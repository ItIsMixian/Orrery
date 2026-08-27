"""Provider-neutral collaboration contracts and local Git inspection."""
from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .schema import COLLABORATION_SCHEMA


COLLABORATION_SCHEMA_VERSION = 1
COLLABORATION_CONTRACT_ID = "project-orrery-collaboration-v1"
WORKTREE_STATUS_SCHEMA_VERSION = 1
WORKTREE_CREATE_SCHEMA_VERSION = 1
PRIMARY_WRITE_GUARD_SCHEMA_VERSION = 1
SESSION_ROUTE_SCHEMA_VERSION = 1
SCOPE_OBSERVATION_SCHEMA_VERSION = 1
OVERLAP_REPORT_SCHEMA_VERSION = 1
SCOPE_EXPANSION_SCHEMA_VERSION = 1
DEFAULT_INTEGRATION_REF = "refs/heads/main"
INTEGRATION_REF_CONFIG_KEY = "collaboration.integration_ref"
PRIMARY_WORKTREE_CONFIG_KEY = "collaboration.primary_worktree"
PROJECT_MODE_CONFIG_KEY = "collaboration.project_mode"
EXCLUSIVE_RESOURCES_CONFIG_KEY = "collaboration.exclusive_resources"
RESERVED_SUBSYSTEM_IDS = ("unmapped", "project-wide")
CAPABILITIES = ("reviewer", "integrator", "admin")
_COLLABORATION_CONFIG_FIELDS = {
    "integration_ref", "primary_worktree", "project_mode", "exclusive_resources",
    "workspace_inventory", "workspace_maintenance"
}
_SUBSYSTEM_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_DIRTY_FINGERPRINT_DOMAIN = b"project-orrery-dirty-fingerprint-v1\0"
_SCOPE_FINGERPRINT_DOMAIN = b"project-orrery-scope-observation-v1\0"
_FINDING_KEY_DOMAIN = b"project-orrery-overlap-finding-key-v1\0"
_FINDING_FINGERPRINT_DOMAIN = b"project-orrery-overlap-finding-v1\0"
_PATH_SOURCES = ("committed", "staged", "unstaged", "untracked", "expected")
_AUTHORITY_PREFIXES = (
    ("seed", "docs/core/"),
    ("adr", "docs/decisions/"),
    ("design", "docs/design/"),
    ("plan", "docs/implementation/plans/"),
    ("state", "docs/state/"),
    ("validation", "docs/validation/"),
)
_AUTHORITY_EXACT = {
    "AGENTS.md": "agent-index",
    "docs/PROGRESS.md": "progress",
    "docs/HANDOFF.md": "handoff",
    "docs/DEVLOG.md": "devlog",
}
DEFAULT_EXCLUSIVE_RESOURCES = (
    {
        "resource_id": "credentials",
        "path_patterns": [
            "ai-config.json", "**/ai-config.json", ".env", ".env.*", "**/.env", "**/.env.*",
            "**/credentials.json", "**/keyring/**", "**/*.pem", "**/*.key",
        ],
    },
    {
        "resource_id": "release",
        "path_patterns": [
            "skills/project-orrery/release-manifest.json", "packages/component-versions.json",
            "scripts/package_release.py", ".github/workflows/release.yml", "packaging/**",
        ],
    },
    {
        "resource_id": "schema-migration",
        "path_patterns": ["**/schema/**", "**/migrations/**", "**/*schema*.json"],
    },
)
_SESSION_STALE_FIELDS = (
    ("worktree_id", "worktree-id-changed"),
    ("branch", "branch-changed"),
    ("head", "head-changed"),
    ("integration_ref", "integration-ref-changed"),
    ("integration_oid", "integration-oid-changed"),
    ("dirty_fingerprint", "dirty-fingerprint-changed"),
)
LIFECYCLE_PHASES = (
    "created", "investigating", "implementing", "validating", "review-ready", "integrated", "closed"
)
RUNTIME_CONDITIONS = (
    "active", "waiting-for-user", "paused", "blocked-by-conflict", "failed", "offline", "stale-unknown"
)
EVIDENCE_FRESHNESS = ("unknown", "current", "stale")
CLOSURE_REASONS = ("integrated", "abandoned", "superseded", "duplicate")
_LIFECYCLE_TRANSITIONS = {
    "created": {"investigating", "implementing", "closed"},
    "investigating": {"implementing", "closed"},
    "implementing": {"investigating", "validating", "closed"},
    "validating": {"implementing", "review-ready", "closed"},
    "review-ready": {"implementing", "validating", "integrated", "closed"},
    "integrated": {"closed"},
    "closed": set(),
}


def _normalize_scope_path(value: str, *, allow_pattern: bool = False) -> str:
    """Normalize one repository-relative path or glob without touching the filesystem."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("scope paths must be non-empty strings")
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if allow_pattern and normalized.endswith("/"):
        normalized = f"{normalized}**"
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise ValueError("scope paths must be repository-relative")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("scope paths must not contain empty, dot, or parent segments")
    if not allow_pattern and any(character in normalized for character in "*?["):
        raise ValueError("observed Git paths must not contain glob syntax")
    return normalized


def _utc_timestamp(value: str | None = None) -> str:
    return value or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json_hash(domain: bytes, payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(domain + encoded).hexdigest()


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _validate_schema_value(value: Any, schema: Mapping[str, Any], path: str) -> None:
    reference = schema.get("$ref")
    if isinstance(reference, str):
        prefix = "#/$defs/"
        if not reference.startswith(prefix):
            raise ValueError(f"unsupported collaboration schema reference at {path}")
        target = COLLABORATION_SCHEMA["$defs"].get(reference[len(prefix) :])
        if not isinstance(target, Mapping):
            raise ValueError(f"missing collaboration schema reference at {path}")
        _validate_schema_value(value, target, path)
        return
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path} must equal {schema['const']!r}")
    allowed = schema.get("enum")
    if isinstance(allowed, list) and value not in allowed:
        raise ValueError(f"{path} is not an allowed value")
    expected = schema.get("type")
    if isinstance(expected, str) and not _schema_type_matches(value, expected):
        raise ValueError(f"{path} must be {expected}")
    if isinstance(expected, list) and not any(_schema_type_matches(value, item) for item in expected):
        raise ValueError(f"{path} has an invalid type")
    if value is None:
        return
    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            raise ValueError(f"{path} is missing required field {missing[0]}")
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise ValueError(f"{path} contains forbidden field {sorted(unknown)[0]}")
        for name, item in value.items():
            item_schema = properties.get(name)
            if isinstance(item_schema, Mapping):
                _validate_schema_value(item, item_schema, f"{path}.{name}")
    if isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ValueError(f"{path} has too few items")
        if isinstance(maximum, int) and len(value) > maximum:
            raise ValueError(f"{path} has too many items")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise ValueError(f"{path} must contain unique items")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_schema, f"{path}[{index}]")
    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        pattern = schema.get("pattern")
        if isinstance(minimum_length, int) and len(value) < minimum_length:
            raise ValueError(f"{path} is too short")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            raise ValueError(f"{path} does not match the required pattern")
    if isinstance(value, int) and not isinstance(value, bool):
        minimum_value = schema.get("minimum")
        if isinstance(minimum_value, int) and value < minimum_value:
            raise ValueError(f"{path} is below the minimum")


def validate_collaboration_contract(payload: Mapping[str, Any]) -> None:
    """Validate one v1 contract against the bundled dependency-free schema subset."""
    if not isinstance(payload, Mapping):
        raise ValueError("collaboration contract must be an object")
    contract_type = payload.get("contract_type")
    definitions = COLLABORATION_SCHEMA["$defs"]
    selected: Mapping[str, Any] | None = None
    for definition in definitions.values():
        if not isinstance(definition, Mapping):
            continue
        properties = definition.get("properties", {})
        type_schema = properties.get("contract_type", {}) if isinstance(properties, Mapping) else {}
        if isinstance(type_schema, Mapping) and type_schema.get("const") == contract_type:
            selected = definition
            break
    if selected is None:
        raise ValueError(f"unknown collaboration contract type: {contract_type}")
    _validate_schema_value(payload, selected, "contract")


@dataclass(frozen=True)
class CollaborationConfig:
    """Validated project-local collaboration configuration."""

    integration_ref: str = DEFAULT_INTEGRATION_REF
    primary_worktree: Path | None = None
    project_mode: str = "personal"
    exclusive_resources: tuple[dict[str, Any], ...] = tuple(
        {"resource_id": item["resource_id"], "path_patterns": list(item["path_patterns"])}
        for item in DEFAULT_EXCLUSIVE_RESOURCES
    )
    workspace_maintenance: Mapping[str, Any] | None = None

    @classmethod
    def from_manifest(cls, manifest: Mapping[str, Any]) -> "CollaborationConfig":
        raw = manifest.get("collaboration", {})
        if not isinstance(raw, Mapping):
            raise ValueError("project collaboration config must be an object")
        unknown = set(raw) - _COLLABORATION_CONFIG_FIELDS
        if unknown:
            raise ValueError(f"unknown project collaboration config field: {sorted(unknown)[0]}")
        integration_ref = raw.get("integration_ref", DEFAULT_INTEGRATION_REF)
        if not isinstance(integration_ref, str) or not integration_ref.startswith("refs/heads/"):
            raise ValueError("collaboration.integration_ref must be a local branch ref under refs/heads/")
        if integration_ref == "refs/heads/" or integration_ref.endswith("/"):
            raise ValueError("collaboration.integration_ref must name a local branch ref")
        primary_value = raw.get("primary_worktree")
        primary_worktree: Path | None = None
        if primary_value is not None:
            if not isinstance(primary_value, str) or not primary_value:
                raise ValueError("collaboration.primary_worktree must be an absolute path")
            primary_worktree = Path(primary_value).expanduser()
            if not primary_worktree.is_absolute():
                raise ValueError("collaboration.primary_worktree must be an absolute path")
        project_mode = raw.get("project_mode", "personal")
        if project_mode not in {"personal", "team"}:
            raise ValueError("collaboration.project_mode must be personal or team")
        exclusive_raw = raw.get("exclusive_resources", DEFAULT_EXCLUSIVE_RESOURCES)
        if not isinstance(exclusive_raw, Sequence) or isinstance(exclusive_raw, (str, bytes)):
            raise ValueError("collaboration.exclusive_resources must be an array")
        exclusive_resources: list[dict[str, Any]] = []
        seen_resources: set[str] = set()
        for item in exclusive_raw:
            if not isinstance(item, Mapping) or set(item) != {"resource_id", "path_patterns"}:
                raise ValueError("each exclusive resource requires only resource_id and path_patterns")
            resource_id = item.get("resource_id")
            patterns = item.get("path_patterns")
            if (
                not isinstance(resource_id, str)
                or not _SUBSYSTEM_ID.fullmatch(resource_id)
                or resource_id in seen_resources
            ):
                raise ValueError("exclusive resource IDs must be unique stable IDs")
            if (
                not isinstance(patterns, Sequence)
                or isinstance(patterns, (str, bytes))
                or not patterns
                or any(not isinstance(pattern, str) or not pattern.strip() for pattern in patterns)
            ):
                raise ValueError("exclusive resource path_patterns must be a non-empty string array")
            normalized_patterns = [_normalize_scope_path(pattern, allow_pattern=True) for pattern in patterns]
            exclusive_resources.append(
                {"resource_id": resource_id, "path_patterns": list(dict.fromkeys(normalized_patterns))}
            )
            seen_resources.add(resource_id)
        inventory = raw.get("workspace_inventory", {})
        if not isinstance(inventory, Mapping):
            raise ValueError("collaboration.workspace_inventory must be an object")
        maintenance = raw.get("workspace_maintenance")
        if maintenance is not None:
            from .maintenance import validate_maintenance_policy

            maintenance = validate_maintenance_policy(maintenance)
        return cls(
            integration_ref=integration_ref,
            primary_worktree=primary_worktree,
            project_mode=str(project_mode),
            exclusive_resources=tuple(exclusive_resources),
            workspace_maintenance=maintenance,
        )


def load_collaboration_config(project_root: Path) -> CollaborationConfig:
    path = Path(project_root) / ".project-orrery.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read Project Orrery manifest {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Project Orrery manifest must be an object")
    return CollaborationConfig.from_manifest(payload)


def _run_git(repository: Path, *arguments: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode:
        raise ValueError(f"Git inspection failed for {' '.join(arguments)}")
    return completed.stdout


def _run_git_mutation(repository: Path, *arguments: str) -> None:
    """Run one bounded local Git mutation without prompts or network fallback."""
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        suffix = f": {detail}" if detail else ""
        raise ValueError(f"Git operation failed for {' '.join(arguments)}{suffix}")


def _git_succeeds(repository: Path, *arguments: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    return completed.returncode == 0


def resolve_integration_oid(repository: Path, integration_ref: str) -> str:
    """Resolve one configured local branch without fetch, fallback, or mutation."""
    if not integration_ref.startswith("refs/heads/") or integration_ref.endswith("/"):
        raise ValueError("integration ref must be a local branch ref under refs/heads/")
    try:
        output = _run_git(
            Path(repository), "rev-parse", "--verify", "--end-of-options", f"{integration_ref}^{{commit}}"
        )
    except ValueError as exc:
        raise ValueError(f"cannot resolve integration ref {integration_ref} to a commit OID") from exc
    oid = str(output).strip().lower()
    if not _OID.fullmatch(oid):
        raise ValueError(f"integration ref {integration_ref} did not resolve to a full commit OID")
    return oid


def _normalized_path(path: Path) -> str:
    # Git can report the long Windows spelling of a worktree even when TEMP or
    # the caller supplied the equivalent 8.3 path (for example RUNNER~1).
    # realpath expands those aliases before the case-insensitive comparison.
    return os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(path))))


def _absolute_git_path(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return Path(os.path.abspath(os.fspath(path)))


def _status_snapshot(repository: Path) -> dict[str, Any]:
    raw = _run_git(
        repository,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        binary=True,
    )
    assert isinstance(raw, bytes)
    staged_count = 0
    unstaged_count = 0
    untracked_count = 0
    entry_count = 0
    records = raw.split(b"\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 3:
            raise ValueError("Git returned an invalid porcelain status record")
        code = record[:2]
        entry_count += 1
        if code == b"??":
            untracked_count += 1
            continue
        if code == b"!!":
            continue
        if code[:1] != b" ":
            staged_count += 1
        if code[1:2] != b" ":
            unstaged_count += 1
        if code[:1] in {b"R", b"C"} or code[1:2] in {b"R", b"C"}:
            # Porcelain v1 -z emits the original path as the following NUL field.
            index += 1
    return {
        "dirty": bool(raw),
        "dirty_fingerprint": hashlib.sha256(_DIRTY_FINGERPRINT_DOMAIN + raw).hexdigest(),
        "dirty_entry_count": entry_count,
        "staged_count": staged_count,
        "unstaged_count": unstaged_count,
        "untracked_count": untracked_count,
    }


def _merge_base(repository: Path, head: str, integration_oid: str) -> str:
    value = str(_run_git(repository, "merge-base", head, integration_oid)).strip().lower()
    if not _OID.fullmatch(value):
        raise ValueError("HEAD and integration ref do not have a valid merge base")
    return value


def _ahead_behind(repository: Path, head: str, integration_oid: str) -> tuple[int, int]:
    value = str(
        _run_git(repository, "rev-list", "--left-right", "--count", f"{integration_oid}...{head}")
    ).strip()
    parts = value.split()
    if len(parts) != 2 or any(not part.isdigit() for part in parts):
        raise ValueError("Git returned invalid ahead/behind counts")
    behind, ahead = (int(part) for part in parts)
    return ahead, behind


def _worktree_records(repository: Path) -> list[dict[str, Any]]:
    raw = _run_git(repository, "worktree", "list", "--porcelain", "-z", binary=True)
    assert isinstance(raw, bytes)
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for encoded in raw.split(b"\0"):
        if not encoded:
            continue
        field = encoded.decode("utf-8", errors="surrogateescape")
        key, _, value = field.partition(" ")
        if key == "worktree":
            if current is not None:
                records.append(current)
            current = {"worktree": value}
        elif current is not None:
            current[key] = value if value else True
    if current is not None:
        records.append(current)
    if not records:
        raise ValueError("Git did not report any worktree")
    return records


def inspect_worktree_identity(
    repository: Path,
    config: CollaborationConfig,
    *,
    member_id: str = "local-owner",
    host_id: str = "local-host",
) -> dict[str, Any]:
    root_text = str(_run_git(repository, "rev-parse", "--show-toplevel")).strip()
    root = Path(os.path.abspath(root_text))
    git_dir_text = str(_run_git(root, "rev-parse", "--absolute-git-dir")).strip()
    common_text = str(_run_git(root, "rev-parse", "--git-common-dir")).strip()
    git_dir = _absolute_git_path(root, git_dir_text)
    git_common_dir = _absolute_git_path(root, common_text)
    records = _worktree_records(root)
    current = next(
        (record for record in records if _normalized_path(Path(str(record["worktree"]))) == _normalized_path(root)),
        None,
    )
    if current is None:
        raise ValueError("current repository root is not a listed Git worktree")

    primary_source = "git-main-worktree"
    primary = records[0]
    if config.primary_worktree is not None:
        expected = _normalized_path(config.primary_worktree)
        override = next(
            (record for record in records if _normalized_path(Path(str(record["worktree"]))) == expected),
            None,
        )
        if override is None:
            raise ValueError("collaboration.primary_worktree must identify a listed Git worktree")
        primary = override
        primary_source = "maintainer-override"

    head = str(_run_git(root, "rev-parse", "HEAD")).strip().lower()
    if not _OID.fullmatch(head):
        raise ValueError("HEAD did not resolve to a full commit OID")
    branch_result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "-q", "HEAD"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    if branch_result.returncode not in {0, 1}:
        raise ValueError("Git inspection failed for symbolic-ref HEAD")
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    status = _status_snapshot(root)
    dirty = bool(status["dirty"])
    integration_oid = resolve_integration_oid(root, config.integration_ref)
    merge_base = _merge_base(root, head, integration_oid)
    ahead, behind = _ahead_behind(root, head, integration_oid)
    is_primary = _normalized_path(root) == _normalized_path(Path(str(primary["worktree"])))
    if dirty:
        fact_scope = "worktree"
    elif branch == config.integration_ref and head == integration_oid:
        fact_scope = "canonical"
    else:
        fact_scope = "candidate"
    worktree_digest = hashlib.sha256(_normalized_path(git_dir).encode("utf-8")).hexdigest()[:24]
    contract = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "worktree-identity",
        "worktree_id": f"local-{worktree_digest}",
        "worktree_path": str(root),
        "git_dir": str(git_dir),
        "git_common_dir": str(git_common_dir),
        "branch": branch,
        "head": head,
        "dirty": dirty,
        "dirty_fingerprint": status["dirty_fingerprint"],
        "dirty_entry_count": status["dirty_entry_count"],
        "staged_count": status["staged_count"],
        "unstaged_count": status["unstaged_count"],
        "untracked_count": status["untracked_count"],
        "is_primary": is_primary,
        "primary_worktree_path": str(Path(str(primary["worktree"])).absolute()),
        "primary_worktree_source": primary_source,
        "integration_ref": config.integration_ref,
        "integration_oid": integration_oid,
        "merge_base": merge_base,
        "ahead": ahead,
        "behind": behind,
        "fact_scope": fact_scope,
        "member_id": member_id,
        "host_id": host_id,
        "visibility": "worktree-local",
        "observability": "local",
    }
    validate_collaboration_contract(contract)
    return contract


def worktree_session_path(repository: Path) -> Path:
    """Resolve the per-worktree private session path selected by Git."""
    root_text = str(_run_git(repository, "rev-parse", "--show-toplevel")).strip()
    root = Path(os.path.abspath(root_text))
    value = str(_run_git(root, "rev-parse", "--git-path", "orrery/worktree.json")).strip()
    path = _absolute_git_path(root, value)
    git_dir = _absolute_git_path(
        root, str(_run_git(root, "rev-parse", "--absolute-git-dir")).strip()
    )
    try:
        path.resolve(strict=False).relative_to(git_dir.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValueError("Git private session path is outside the current worktree Git directory") from exc
    return path


def _read_workstream_session(path: Path) -> dict[str, Any] | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError(f"cannot inspect private Workstream session: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("private Workstream session must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read private Workstream session: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValueError("private Workstream session must contain a JSON object")
    session = dict(value)
    validate_collaboration_contract(session)
    if session.get("contract_type") != "workstream-session":
        raise ValueError("private Workstream session has the wrong contract type")
    return session


def _session_lifecycle_projection(
    session: Mapping[str, Any] | None, stale_reasons: Sequence[str]
) -> dict[str, Any] | None:
    if session is None:
        return None
    declared_phase = str(session["lifecycle_phase"])
    declared_freshness = str(session.get("evidence_freshness", "unknown"))
    reasons = list(stale_reasons)
    if declared_phase == "review-ready" and declared_freshness != "current":
        reasons.append("review-evidence-not-current")
    scope_gate = _session_scope_gate(session)
    if declared_phase == "review-ready" and not scope_gate["allowed"]:
        reasons.append(scope_gate["reason"])
    reasons = list(dict.fromkeys(reasons))
    review_ready_revoked = declared_phase == "review-ready" and bool(reasons)
    return {
        "declared_phase": declared_phase,
        "effective_phase": "validating" if review_ready_revoked else declared_phase,
        "runtime_condition": session["runtime_condition"],
        "evidence_freshness": "stale" if stale_reasons else declared_freshness,
        "closure_reason": session.get("closure_reason"),
        "lifecycle_revision": session.get("lifecycle_revision", 1),
        "review_ready_revoked": review_ready_revoked,
        "revocation_reasons": reasons if review_ready_revoked else [],
    }


def _session_scope_gate(session: Mapping[str, Any]) -> dict[str, Any]:
    expansion = session.get("last_scope_expansion")
    if isinstance(expansion, Mapping) and expansion.get("decision") == "blocked":
        level = expansion.get("level")
        return {
            "allowed": False,
            "reason": (
                "scope-expansion-l3-blocked"
                if level == "l3"
                else "scope-expansion-l2-confirmation-required"
            ),
        }
    member_id = session.get("member_id")
    for finding in session.get("findings", []):
        if not isinstance(finding, Mapping) or finding.get("disposition") not in {
            "open", "acknowledged"
        }:
            continue
        if finding.get("kind") == "direct" or finding.get("severity") == "l3":
            return {"allowed": False, "reason": "direct-or-l3-finding-blocked"}
        if finding.get("severity") == "l2" and not any(
            isinstance(ack, Mapping) and ack.get("member_id") == member_id
            for ack in finding.get("acknowledgements", [])
        ):
            return {"allowed": False, "reason": "local-l2-acknowledgement-required"}
    return {"allowed": True, "reason": "scope-gate-clear"}


def inspect_worktree_status(project_root: Path) -> dict[str, Any]:
    """Return a stable read-only status projection for one worktree or clone."""
    root = Path(project_root).expanduser().absolute()
    config = load_collaboration_config(root)
    identity = inspect_worktree_identity(root, config)
    session_path = worktree_session_path(root)
    session = _read_workstream_session(session_path)
    stale_reasons = (
        [reason for field, reason in _SESSION_STALE_FIELDS if session.get(field) != identity.get(field)]
        if session is not None
        else []
    )
    return {
        "status_schema_version": WORKTREE_STATUS_SCHEMA_VERSION,
        "identity": identity,
        "session": {
            "path": str(session_path),
            "storage": "git-private-worktree",
            "exists": session is not None,
            "state": "absent" if session is None else ("stale" if stale_reasons else "current"),
            "stale_reasons": stale_reasons,
            "lifecycle": _session_lifecycle_projection(session, stale_reasons),
            "record": session,
        },
        "writes_performed": False,
    }


def inspect_primary_write_guard(project_root: Path) -> dict[str, Any]:
    """Fail closed before a product write from the configured primary worktree."""
    root = Path(project_root).expanduser().absolute()
    config = load_collaboration_config(root)
    identity = inspect_worktree_identity(root, config)
    if not identity["is_primary"]:
        decision = "allow"
        reason = "isolated-worktree"
        recovery = "none"
    elif identity["dirty"]:
        decision = "block"
        reason = "primary-worktree-dirty-recovery-required"
        recovery = "review-and-selectively-transfer-existing-changes"
    else:
        decision = "block"
        reason = "primary-worktree-write-prohibited"
        recovery = "create-or-connect-isolated-workstream"
    return {
        "guard_schema_version": PRIMARY_WRITE_GUARD_SCHEMA_VERSION,
        "intent": "product-write",
        "decision": decision,
        "allowed": decision == "allow",
        "reason": reason,
        "recovery": recovery,
        "identity": identity,
        "writes_performed": False,
    }


def build_workstream_session(
    project_root: Path,
    *,
    workstream_id: str,
    primary_subsystem_id: str,
    affected_subsystem_ids: Sequence[str] = (),
    expected_writes: Sequence[str] = (),
    governing_docs: Sequence[str] = (),
    validation_surfaces: Sequence[str] = (),
    scope_revision: int = 1,
    lifecycle_phase: str = "implementing",
    runtime_condition: str = "active",
    evidence_freshness: str = "unknown",
    closure_reason: str | None = None,
    lifecycle_revision: int = 1,
    last_transition: Mapping[str, Any] | None = None,
    platform_session: Mapping[str, str] | None = None,
    member_id: str = "local-owner",
    host_id: str = "local-host",
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Build a session bound to current Git facts without writing it."""
    root = Path(project_root).expanduser().absolute()
    config = load_collaboration_config(root)
    identity = inspect_worktree_identity(root, config, member_id=member_id, host_id=host_id)
    registry = load_subsystem_registry(root)
    scope = build_scope_contract(
        workstream_id=workstream_id,
        revision=scope_revision,
        primary_subsystem_id=primary_subsystem_id,
        affected_subsystem_ids=affected_subsystem_ids,
        registry=registry,
        expected_writes=expected_writes,
        governing_docs=governing_docs,
        validation_surfaces=validation_surfaces,
        member_id=member_id,
        host_id=host_id,
    )
    timestamp = captured_at or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    session = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "workstream-session",
        "project_mode": config.project_mode,
        "workstream_id": workstream_id,
        "worktree_id": identity["worktree_id"],
        "member_id": member_id,
        "host_id": host_id,
        "active_host_id": host_id,
        "platform_session": dict(platform_session) if platform_session is not None else None,
        "branch": identity["branch"],
        "head": identity["head"],
        "integration_ref": identity["integration_ref"],
        "integration_oid": identity["integration_oid"],
        "merge_base": identity["merge_base"],
        "dirty_fingerprint": identity["dirty_fingerprint"],
        "lifecycle_phase": lifecycle_phase,
        "runtime_condition": runtime_condition,
        "evidence_freshness": evidence_freshness,
        "closure_reason": closure_reason,
        "lifecycle_revision": lifecycle_revision,
        "last_transition": dict(last_transition) if last_transition is not None else None,
        "scope_revision": scope_revision,
        "primary_subsystem_id": scope["primary_subsystem_id"],
        "affected_subsystem_ids": scope["affected_subsystem_ids"],
        "expected_writes": scope["expected_writes"],
        "governing_docs": scope["governing_docs"],
        "validation_surfaces": scope["validation_surfaces"],
        "visibility": "worktree-local",
        "observability": "local",
        "captured_at": timestamp,
    }
    validate_collaboration_contract(session)
    _validate_lifecycle_semantics(session)
    return session


def _validate_lifecycle_semantics(session: Mapping[str, Any]) -> None:
    phase = session["lifecycle_phase"]
    closure_reason = session.get("closure_reason")
    if phase == "closed" and closure_reason is None:
        raise ValueError("closed Workstream session requires a closure reason")
    if phase != "closed" and closure_reason is not None:
        raise ValueError("closure reason is only valid for a closed Workstream session")
    if closure_reason == "integrated" and phase != "closed":
        raise ValueError("integrated closure reason requires a closed Workstream session")


def _write_private_session(root: Path, session: Mapping[str, Any]) -> dict[str, Any]:
    validate_collaboration_contract(session)
    _validate_lifecycle_semantics(session)
    path = worktree_session_path(root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not stat.S_ISREG(path.lstat().st_mode):
            raise OSError("existing private Workstream session is not a regular file")
        descriptor, temporary_name = tempfile.mkstemp(prefix="worktree.", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(session, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    except OSError as exc:
        raise ValueError(f"cannot write private Workstream session: {exc}") from exc
    return {
        "session_path": str(path),
        "storage": "git-private-worktree",
        "session": dict(session),
        "writes_performed": True,
    }


def write_workstream_session(project_root: Path, **session_fields: Any) -> dict[str, Any]:
    """Atomically persist one reconstructable session under the private Git path."""
    root = Path(project_root).expanduser().absolute()
    session = build_workstream_session(root, **session_fields)
    return _write_private_session(root, session)


def transition_workstream_session(
    project_root: Path,
    *,
    reason: str,
    lifecycle_phase: str | None = None,
    runtime_condition: str | None = None,
    evidence_freshness: str | None = None,
    closure_reason: str | None = None,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    """Apply one legal lifecycle transition to a current private session."""
    if not reason.strip():
        raise ValueError("lifecycle transition reason must not be empty")
    root = Path(project_root).expanduser().absolute()
    status = inspect_worktree_status(root)
    if status["session"]["state"] != "current":
        raise ValueError("lifecycle transition requires a current Workstream session")
    session = dict(status["session"]["record"])
    old_phase = str(session["lifecycle_phase"])
    new_phase = lifecycle_phase or old_phase
    if new_phase not in LIFECYCLE_PHASES:
        raise ValueError("unknown Workstream lifecycle phase")
    if new_phase != old_phase and new_phase not in _LIFECYCLE_TRANSITIONS[old_phase]:
        raise ValueError(f"illegal Workstream lifecycle transition: {old_phase} -> {new_phase}")
    if new_phase == "review-ready" and old_phase != "review-ready":
        raise ValueError("review-ready transition requires the future executable review gate")
    if new_phase == "integrated" and old_phase != "integrated":
        raise ValueError("integrated transition requires the future integration command")
    new_runtime = runtime_condition or str(session["runtime_condition"])
    if new_runtime not in RUNTIME_CONDITIONS:
        raise ValueError("unknown Workstream runtime condition")
    new_freshness = evidence_freshness or str(session.get("evidence_freshness", "unknown"))
    if new_freshness not in EVIDENCE_FRESHNESS:
        raise ValueError("unknown Workstream evidence freshness")
    if old_phase == "review-ready" and new_phase == "review-ready" and (
        new_freshness != "current" or new_runtime != "active"
    ):
        new_phase = "validating"
    if new_phase == "closed":
        if closure_reason not in CLOSURE_REASONS:
            raise ValueError("closing a Workstream requires an explicit closure reason")
        if closure_reason == "integrated" and old_phase != "integrated":
            raise ValueError("integrated closure is only legal after the integrated phase")
        if old_phase == "integrated" and closure_reason != "integrated":
            raise ValueError("an integrated Workstream must close with reason integrated")
    elif closure_reason is not None:
        raise ValueError("closure reason is only valid when closing a Workstream")
    timestamp = occurred_at or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    session.update(
        {
            "lifecycle_phase": new_phase,
            "runtime_condition": new_runtime,
            "evidence_freshness": new_freshness,
            "closure_reason": closure_reason if new_phase == "closed" else None,
            "lifecycle_revision": int(session.get("lifecycle_revision", 1)) + 1,
            "last_transition": {
                "from_phase": old_phase,
                "to_phase": new_phase,
                "reason": reason.strip(),
                "occurred_at": timestamp,
            },
        }
    )
    result = _write_private_session(root, session)
    if new_phase == "closed":
        try:
            from .maintenance import record_maintenance_event

            result["maintenance_event"] = record_maintenance_event(
                root, reason="closure-event", occurred_at=timestamp
            )
        except Exception as error:
            result["maintenance_event"] = {
                "status": "unavailable",
                "error_type": type(error).__name__,
                "lifecycle_transition_affected": False,
            }
    return result


def load_adapter_capabilities(manifest_path: Path) -> dict[str, Any]:
    """Load the provider-neutral capability declaration embedded in an Adapter manifest."""
    path = Path(manifest_path).expanduser().absolute()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read Adapter manifest {path}: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise ValueError("Adapter manifest must contain a JSON object")
    value = manifest.get("workstream_capabilities")
    if not isinstance(value, Mapping):
        raise ValueError("Adapter manifest does not declare workstream_capabilities")
    capabilities = dict(value)
    validate_collaboration_contract(capabilities)
    if capabilities.get("contract_type") != "adapter-capabilities":
        raise ValueError("Adapter capability declaration has the wrong contract type")
    if capabilities["rebind"] and not capabilities["attach"]:
        raise ValueError("Adapter rebind capability requires attach capability")
    if capabilities["session_identity_source"] == "unavailable" and (
        capabilities["attach"] or capabilities["rebind"]
    ):
        raise ValueError("Adapter without a session identity source cannot attach or rebind")
    return capabilities


def _continuation_brief(
    identity: Mapping[str, Any], session: Mapping[str, Any] | None, action: str
) -> dict[str, Any]:
    """Return only reconstructable routing facts; never include prompts or source content."""
    return {
        "action": action,
        "worktree_path": identity["worktree_path"],
        "branch": identity["branch"],
        "head": identity["head"],
        "integration_ref": identity["integration_ref"],
        "integration_oid": identity["integration_oid"],
        "workstream_id": session.get("workstream_id") if session else None,
    }


def plan_adapter_session_route(
    project_root: Path,
    *,
    adapter_manifest: Path,
    platform_session_id: str | None = None,
) -> dict[str, Any]:
    """Plan an Orrery-first or Agent-first local session route without writing."""
    root = Path(project_root).expanduser().absolute()
    capabilities = load_adapter_capabilities(adapter_manifest)
    status = inspect_worktree_status(root)
    identity = status["identity"]
    session_record = status["session"]["record"]
    decision = "block"
    reason: str
    next_action: str
    if identity["is_primary"]:
        reason = (
            "primary-worktree-dirty-recovery-required"
            if identity["dirty"]
            else "primary-worktree-write-prohibited"
        )
        next_action = (
            "review-and-selectively-transfer-existing-changes"
            if identity["dirty"]
            else "create-or-open-isolated-workstream"
        )
    elif status["session"]["state"] == "absent":
        reason = "workstream-session-required"
        next_action = "register-private-workstream-session"
    elif status["session"]["state"] == "stale":
        reason = "stale-workstream-session"
        next_action = "explicitly-recreate-or-refresh-session"
    else:
        assert isinstance(session_record, Mapping)
        attached = session_record.get("platform_session")
        same_session = (
            isinstance(attached, Mapping)
            and attached.get("adapter") == capabilities["adapter_id"]
            and attached.get("session_id") == platform_session_id
        )
        scope_gate = _session_scope_gate(session_record)
        if not scope_gate["allowed"]:
            reason = scope_gate["reason"]
            next_action = "refresh-scope-and-resolve-local-finding"
        elif platform_session_id and same_session:
            decision = "allow"
            reason = "platform-session-attached"
            next_action = "continue-in-current-worktree"
        elif not platform_session_id:
            reason = "platform-session-id-required"
            next_action = (
                "supply-platform-session-id"
                if capabilities["session_identity_source"] != "unavailable"
                else "manual-open-with-continuation-brief"
            )
        elif attached is None and capabilities["attach"]:
            reason = "platform-session-attach-required"
            next_action = "attach-platform-session"
        elif isinstance(attached, Mapping) and capabilities["rebind"]:
            reason = "platform-session-rebind-required"
            next_action = "explicitly-rebind-platform-session"
        elif isinstance(attached, Mapping):
            reason = "adapter-rebind-unavailable"
            next_action = "create-new-workstream-and-open-new-platform-session"
        elif capabilities["launch"]:
            reason = "platform-session-launch-required"
            next_action = "launch-platform-session-in-current-worktree"
        else:
            reason = "adapter-attach-unavailable"
            next_action = "manual-open-with-continuation-brief"
    return {
        "route_schema_version": SESSION_ROUTE_SCHEMA_VERSION,
        "decision": decision,
        "allowed": decision == "allow",
        "reason": reason,
        "next_action": next_action,
        "capabilities": capabilities,
        "status": status,
        "continuation_brief": _continuation_brief(identity, session_record, next_action),
        "writes_performed": False,
        "network_performed": False,
    }


def attach_platform_session(
    project_root: Path,
    *,
    adapter_manifest: Path,
    platform_session_id: str,
    rebind: bool = False,
) -> dict[str, Any]:
    """Attach a runtime session to a current Workstream using Git-private storage only."""
    if not platform_session_id.strip():
        raise ValueError("platform session ID must not be empty")
    root = Path(project_root).expanduser().absolute()
    capabilities = load_adapter_capabilities(adapter_manifest)
    if not capabilities["attach"]:
        raise ValueError("Adapter does not support platform-session attach")
    status = inspect_worktree_status(root)
    if status["identity"]["is_primary"]:
        raise ValueError("platform-session attach is prohibited in the primary worktree")
    if status["session"]["state"] != "current":
        raise ValueError("platform-session attach requires a current Workstream session")
    session = dict(status["session"]["record"])
    if session["lifecycle_phase"] in {"integrated", "closed"}:
        raise ValueError("platform-session attach is not legal for a finished Workstream")
    requested = {
        "adapter": capabilities["adapter_id"],
        "session_id": platform_session_id.strip(),
    }
    existing = session.get("platform_session")
    if existing == requested:
        return {
            "session_path": status["session"]["path"],
            "storage": "git-private-worktree",
            "session": session,
            "writes_performed": False,
        }
    if existing is not None:
        if not rebind:
            raise ValueError("Workstream is already attached; explicit --rebind is required")
        if not capabilities["rebind"]:
            raise ValueError("Adapter does not support platform-session rebind")
    old_phase = str(session["lifecycle_phase"])
    new_phase = "investigating" if old_phase == "created" else old_phase
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    session.update(
        {
            "platform_session": requested,
            "lifecycle_phase": new_phase,
            "runtime_condition": "active",
            "evidence_freshness": str(session.get("evidence_freshness", "unknown")),
            "closure_reason": None,
            "lifecycle_revision": int(session.get("lifecycle_revision", 1)) + 1,
            "last_transition": {
                "from_phase": old_phase,
                "to_phase": new_phase,
                "reason": "platform-session-rebound" if existing is not None else "platform-session-attached",
                "occurred_at": timestamp,
            },
        }
    )
    return _write_private_session(root, session)


def _default_worktree_path(source_root: Path, workstream_id: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", workstream_id.lower()).strip("-")
    if not slug:
        raise ValueError("workstream ID must contain at least one letter or number")
    return source_root.parent / f"{source_root.name}-{slug}"


def _validate_new_branch(repository: Path, branch: str) -> str:
    if not branch or branch.startswith("refs/"):
        raise ValueError("branch must be a short local branch name")
    completed = subprocess.run(
        ["git", "-C", str(repository), "check-ref-format", "--branch", branch],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode:
        raise ValueError("branch is not a valid short local branch name")
    branch_ref = f"refs/heads/{branch}"
    if _git_succeeds(repository, "show-ref", "--verify", "--quiet", branch_ref):
        raise ValueError(f"branch already exists: {branch_ref}")
    return branch_ref


def _rollback_created_worktree(repository: Path, path: Path, branch: str) -> list[str]:
    failures: list[str] = []
    if os.path.lexists(path):
        try:
            _run_git_mutation(repository, "worktree", "remove", str(path))
        except ValueError as exc:
            failures.append(str(exc))
    branch_ref = f"refs/heads/{branch}"
    if _git_succeeds(repository, "show-ref", "--verify", "--quiet", branch_ref):
        try:
            _run_git_mutation(repository, "branch", "-d", "--", branch)
        except ValueError as exc:
            failures.append(str(exc))
    return failures


def create_worktree(
    project_root: Path,
    *,
    workstream_id: str,
    branch: str,
    primary_subsystem_id: str,
    path: Path | None = None,
    integration_ref: str | None = None,
    affected_subsystem_ids: Sequence[str] = (),
    expected_writes: Sequence[str] = (),
    governing_docs: Sequence[str] = (),
    validation_surfaces: Sequence[str] = (),
    member_id: str = "local-owner",
    host_id: str = "local-host",
) -> dict[str, Any]:
    """Create one linked worktree at an exact local integration OID and initialize its session."""
    source_text = str(_run_git(Path(project_root), "rev-parse", "--show-toplevel")).strip()
    source_root = Path(os.path.abspath(source_text))
    config = load_collaboration_config(source_root)
    selected_ref = integration_ref or config.integration_ref
    if selected_ref != config.integration_ref:
        raise ValueError(
            "--from must match collaboration.integration_ref so status and session use one baseline"
        )
    source_identity = inspect_worktree_identity(
        source_root, config, member_id=member_id, host_id=host_id
    )
    integration_oid = source_identity["integration_oid"]
    branch_ref = _validate_new_branch(source_root, branch)
    target = Path(path).expanduser().absolute() if path is not None else _default_worktree_path(
        source_root, workstream_id
    ).absolute()
    if os.path.lexists(target):
        raise ValueError(f"worktree path already exists: {target}")
    if not target.parent.is_dir():
        raise ValueError(f"worktree parent directory does not exist: {target.parent}")
    build_scope_contract(
        workstream_id=workstream_id,
        revision=1,
        primary_subsystem_id=primary_subsystem_id,
        affected_subsystem_ids=affected_subsystem_ids,
        registry=load_subsystem_registry(source_root),
        expected_writes=expected_writes,
        governing_docs=governing_docs,
        validation_surfaces=validation_surfaces,
        member_id=member_id,
        host_id=host_id,
    )

    created = False
    try:
        _run_git_mutation(
            source_root,
            "worktree",
            "add",
            "-b",
            branch,
            str(target),
            integration_oid,
        )
        created = True
        session_result = write_workstream_session(
            target,
            workstream_id=workstream_id,
            primary_subsystem_id=primary_subsystem_id,
            affected_subsystem_ids=affected_subsystem_ids,
            expected_writes=expected_writes,
            governing_docs=governing_docs,
            validation_surfaces=validation_surfaces,
            lifecycle_phase="created",
            member_id=member_id,
            host_id=host_id,
        )
        if session_result["session"]["integration_oid"] != integration_oid:
            raise ValueError("integration ref changed while the worktree was being created")
        status = inspect_worktree_status(target)
    except (OSError, ValueError) as exc:
        failures = _rollback_created_worktree(source_root, target, branch) if created else []
        if failures:
            raise ValueError(
                f"worktree creation failed: {exc}; rollback incomplete: {'; '.join(failures)}"
            ) from exc
        raise ValueError(f"worktree creation failed and was rolled back: {exc}") from exc

    return {
        "create_schema_version": WORKTREE_CREATE_SCHEMA_VERSION,
        "workstream_id": workstream_id,
        "source": {
            "worktree_path": source_identity["worktree_path"],
            "dirty": source_identity["dirty"],
            "integration_ref": selected_ref,
            "integration_oid": integration_oid,
        },
        "branch": branch_ref,
        "worktree_path": str(target),
        "status": status,
        "session_path": session_result["session_path"],
        "write_targets": ["local-branch", "linked-worktree", "git-private-worktree-session"],
        "writes_performed": True,
    }


def _registry_path_patterns(body: str, state_docs: Sequence[str], authority_docs: Sequence[str]) -> list[str]:
    patterns: list[str] = []
    truth_match = re.search(r"(?m)^\*\*Truth\*\*:\s*(.+)$", body)
    tokens = re.findall(r"`([^`]+)`", truth_match.group(1)) if truth_match else []
    for token in tokens:
        candidate = token.strip().replace("\\", "/")
        if (
            not candidate
            or "://" in candidate
            or candidate.startswith("$")
            or not ("/" in candidate or "." in Path(candidate).name or candidate == "AGENTS.md")
        ):
            continue
        if candidate.endswith("/"):
            candidate = f"{candidate}**"
        try:
            patterns.append(_normalize_scope_path(candidate, allow_pattern=True))
        except ValueError:
            continue
    for path in (*state_docs, *authority_docs):
        if path.startswith("docs/") or path == "AGENTS.md":
            try:
                patterns.append(_normalize_scope_path(path, allow_pattern=True))
            except ValueError:
                continue
    return list(dict.fromkeys(patterns))


def load_subsystem_registry(project_root: Path) -> dict[str, Any]:
    """Project explicit subsystem IDs from AGENTS.md and existing State Docs."""
    root = Path(project_root)
    agents_path = root / "AGENTS.md"
    try:
        content = agents_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read subsystem index {agents_path}: {exc}") from exc
    headings = list(re.finditer(r"(?m)^## ([^\r\n]+)\r?$", content))
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        body = content[start:end]
        id_match = re.search(r"(?m)^\*\*ID\*\*:\s*`([^`]+)`\s*$", body)
        if id_match is None:
            continue
        subsystem_id = id_match.group(1)
        if not _SUBSYSTEM_ID.fullmatch(subsystem_id) or subsystem_id in RESERVED_SUBSYSTEM_IDS:
            raise ValueError(f"invalid or reserved subsystem ID in AGENTS.md: {subsystem_id}")
        if subsystem_id in seen:
            raise ValueError(f"duplicate subsystem ID in AGENTS.md: {subsystem_id}")
        state_docs = list(dict.fromkeys(re.findall(r"\((docs/state/[^)#]+\.md)(?:#[^)]*)?\)", body)))
        if not state_docs or any(not (root / path).is_file() for path in state_docs):
            raise ValueError(f"subsystem {subsystem_id} must project at least one existing State Doc")
        linked_docs = list(
            dict.fromkeys(
                path
                for path in re.findall(r"\(([^)#]+\.md)(?:#[^)]*)?\)", body)
                if not re.match(r"^[a-z]+://", path)
            )
        )
        entries.append(
            {
                "subsystem_id": subsystem_id,
                "display_name": heading.group(1).strip(),
                "state_docs": state_docs,
                "authority_docs": linked_docs,
                "path_patterns": _registry_path_patterns(body, state_docs, linked_docs),
            }
        )
        seen.add(subsystem_id)
    if not entries:
        raise ValueError("AGENTS.md does not define an explicit subsystem registry")
    contract = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "subsystem-registry",
        "source": "AGENTS.md",
        "reserved_scope_ids": list(RESERVED_SUBSYSTEM_IDS),
        "entries": entries,
    }
    validate_collaboration_contract(contract)
    return contract


def build_scope_contract(
    *,
    workstream_id: str,
    revision: int,
    primary_subsystem_id: str,
    affected_subsystem_ids: Sequence[str],
    registry: Mapping[str, Any],
    expected_writes: Sequence[str] = (),
    governing_docs: Sequence[str] = (),
    validation_surfaces: Sequence[str] = (),
    member_id: str = "local-owner",
    host_id: str = "local-host",
    visibility: str = "worktree-local",
    observability: str = "local",
) -> dict[str, Any]:
    if not workstream_id or isinstance(revision, bool) or revision < 1:
        raise ValueError("scope requires a workstream ID and positive revision")
    entries = registry.get("entries")
    if not isinstance(entries, Sequence):
        raise ValueError("invalid subsystem registry")
    known = {
        entry.get("subsystem_id")
        for entry in entries
        if isinstance(entry, Mapping) and isinstance(entry.get("subsystem_id"), str)
    }
    allowed_primary = known | set(RESERVED_SUBSYSTEM_IDS)
    if primary_subsystem_id not in allowed_primary:
        raise ValueError(f"unknown subsystem ID: {primary_subsystem_id}")
    affected = list(affected_subsystem_ids)
    if len(set(affected)) != len(affected) or any(value not in known for value in affected):
        raise ValueError("affected_subsystem_ids contains an unknown subsystem or duplicate")
    if primary_subsystem_id in affected:
        raise ValueError("primary subsystem must not be repeated in affected_subsystem_ids")
    scope_kind = primary_subsystem_id if primary_subsystem_id in RESERVED_SUBSYSTEM_IDS else "mapped"
    contract = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "scope",
        "workstream_id": workstream_id,
        "revision": revision,
        "scope_kind": scope_kind,
        "primary_subsystem_id": primary_subsystem_id,
        "affected_subsystem_ids": affected,
        "expected_writes": list(dict.fromkeys(expected_writes)),
        "governing_docs": list(dict.fromkeys(governing_docs)),
        "validation_surfaces": list(dict.fromkeys(validation_surfaces)),
        "member_id": member_id,
        "host_id": host_id,
        "visibility": visibility,
        "observability": observability,
    }
    validate_collaboration_contract(contract)
    return contract


def _path_matches_pattern(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatch.fnmatchcase(path, pattern)


def _path_specs_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_path = str(left["path"])
    right_path = str(right["path"])
    left_pattern = bool(left.get("is_pattern"))
    right_pattern = bool(right.get("is_pattern"))
    if not left_pattern and not right_pattern:
        return left_path == right_path
    if left_pattern and not right_pattern:
        return _path_matches_pattern(right_path, left_path)
    if right_pattern and not left_pattern:
        return _path_matches_pattern(left_path, right_path)
    if left_path == right_path:
        return True
    def literal_prefix(value: str) -> str:
        positions = [value.find(character) for character in "*?[" if character in value]
        return value[: min(positions) if positions else len(value)].rstrip("/")

    left_prefix = literal_prefix(left_path)
    right_prefix = literal_prefix(right_path)
    return bool(left_prefix and right_prefix) and (
        left_prefix == right_prefix
        or left_prefix.startswith(f"{right_prefix}/")
        or right_prefix.startswith(f"{left_prefix}/")
    )


def _authority_surfaces(path: str, *, is_pattern: bool) -> list[str]:
    surfaces: list[str] = []
    for exact, kind in _AUTHORITY_EXACT.items():
        if (not is_pattern and path == exact) or (is_pattern and _path_matches_pattern(exact, path)):
            surfaces.append(f"{kind}:{exact}")
    for kind, prefix in _AUTHORITY_PREFIXES:
        if path.startswith(prefix):
            surfaces.append(f"{kind}:{path}")
        elif is_pattern and _path_matches_pattern(f"{prefix}__authority_probe__.md", path):
            surfaces.append(f"{kind}:{path}")
    return list(dict.fromkeys(surfaces))


def _subsystems_for_path(
    path: str, *, is_pattern: bool, registry: Mapping[str, Any]
) -> list[str]:
    matched: list[str] = []
    for entry in registry.get("entries", []):
        if not isinstance(entry, Mapping):
            continue
        subsystem_id = entry.get("subsystem_id")
        if not isinstance(subsystem_id, str):
            continue
        for raw_pattern in entry.get("path_patterns", []):
            if not isinstance(raw_pattern, str):
                continue
            registry_spec = {
                "path": raw_pattern,
                "is_pattern": any(character in raw_pattern for character in "*?[")
                or raw_pattern.endswith("/"),
            }
            current_spec = {"path": path, "is_pattern": is_pattern}
            if _path_specs_overlap(current_spec, registry_spec):
                matched.append(subsystem_id)
                break
    return list(dict.fromkeys(matched))


def _exclusive_resources_for_path(
    path: str, *, is_pattern: bool, config: CollaborationConfig
) -> list[str]:
    matched: list[str] = []
    current = {"path": path, "is_pattern": is_pattern}
    for resource in config.exclusive_resources:
        for pattern in resource["path_patterns"]:
            configured = {
                "path": pattern,
                "is_pattern": any(character in pattern for character in "*?[")
                or pattern.endswith("/"),
            }
            if _path_specs_overlap(current, configured):
                matched.append(str(resource["resource_id"]))
                break
    return matched


def _parse_name_status(raw: bytes) -> list[str]:
    records = raw.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        status_raw = records[index]
        index += 1
        if not status_raw:
            continue
        status = status_raw.decode("ascii", errors="replace")
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(records):
            raise ValueError("Git returned an invalid name-status record")
        for _ in range(path_count):
            encoded = records[index]
            index += 1
            if not encoded:
                raise ValueError("Git returned an empty changed path")
            decoded = encoded.decode("utf-8", errors="surrogateescape")
            paths.append(_normalize_scope_path(decoded))
    return list(dict.fromkeys(paths))


def _git_changed_paths(repository: Path, *arguments: str) -> list[str]:
    raw = _run_git(repository, *arguments, "--name-status", "-z", binary=True)
    assert isinstance(raw, bytes)
    return _parse_name_status(raw)


def _git_untracked_paths(repository: Path) -> list[str]:
    raw = _run_git(repository, "ls-files", "--others", "--exclude-standard", "-z", binary=True)
    assert isinstance(raw, bytes)
    return [
        _normalize_scope_path(item.decode("utf-8", errors="surrogateescape"))
        for item in raw.split(b"\0")
        if item
    ]


def collect_scope_observation(
    project_root: Path,
    *,
    session: Mapping[str, Any] | None = None,
    scope_revision: int | None = None,
    affected_subsystem_ids: Sequence[str] | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Collect actual and expected path scope while preserving every Git/session source."""
    root = Path(project_root).expanduser().absolute()
    config = load_collaboration_config(root)
    status = inspect_worktree_status(root)
    record = dict(session) if session is not None else status["session"]["record"]
    if not isinstance(record, Mapping):
        raise ValueError("scope collection requires a private Workstream session")
    registry = load_subsystem_registry(root)
    identity = status["identity"]
    sources: dict[str, set[str]] = {}

    def add_paths(values: Sequence[str], source: str, *, patterns: bool = False) -> None:
        for value in values:
            normalized = _normalize_scope_path(value, allow_pattern=patterns)
            sources.setdefault(normalized, set()).add(source)

    add_paths(
        _git_changed_paths(root, "diff", f"{identity['merge_base']}..{identity['head']}"),
        "committed",
    )
    add_paths(_git_changed_paths(root, "diff", "--cached"), "staged")
    add_paths(_git_changed_paths(root, "diff"), "unstaged")
    add_paths(_git_untracked_paths(root), "untracked")
    add_paths(list(record.get("expected_writes", [])), "expected", patterns=True)

    entries: list[dict[str, Any]] = []
    derived_subsystems: list[str] = []
    for path in sorted(sources):
        is_pattern = "expected" in sources[path] and any(character in path for character in "*?[")
        subsystem_ids = _subsystems_for_path(path, is_pattern=is_pattern, registry=registry)
        derived_subsystems.extend(subsystem_ids)
        entries.append(
            {
                "path": path,
                "is_pattern": is_pattern,
                "sources": [source for source in _PATH_SOURCES if source in sources[path]],
                "authority_surfaces": _authority_surfaces(path, is_pattern=is_pattern),
                "subsystem_ids": subsystem_ids,
                "exclusive_resource_ids": _exclusive_resources_for_path(
                    path, is_pattern=is_pattern, config=config
                ),
            }
        )
    selected_affected = list(
        record.get("affected_subsystem_ids", [])
        if affected_subsystem_ids is None
        else affected_subsystem_ids
    )
    declared = list(
        dict.fromkeys([str(record["primary_subsystem_id"]), *selected_affected])
    )
    observation = {
        "schema_version": SCOPE_OBSERVATION_SCHEMA_VERSION,
        "contract_type": "scope-observation",
        "workstream_id": str(record["workstream_id"]),
        "worktree_id": identity["worktree_id"],
        "member_id": str(record["member_id"]),
        "host_id": str(record["host_id"]),
        "branch": identity["branch"],
        "head": identity["head"],
        "integration_ref": identity["integration_ref"],
        "integration_oid": identity["integration_oid"],
        "merge_base": identity["merge_base"],
        "scope_revision": int(scope_revision or record["scope_revision"]),
        "declared_subsystem_ids": declared,
        "derived_subsystem_ids": list(dict.fromkeys(derived_subsystems)),
        "path_entries": entries,
        "governing_docs": list(dict.fromkeys(record.get("governing_docs", []))),
        "validation_surfaces": list(dict.fromkeys(record.get("validation_surfaces", []))),
        "scope_fingerprint": "0" * 64,
        "visibility": str(record.get("visibility", "worktree-local")),
        "observability": str(record.get("observability", "local")),
        "captured_at": _utc_timestamp(captured_at),
    }
    fingerprint_input = dict(observation)
    fingerprint_input.pop("scope_fingerprint")
    fingerprint_input.pop("captured_at")
    observation["scope_fingerprint"] = _canonical_json_hash(
        _SCOPE_FINGERPRINT_DOMAIN, fingerprint_input
    )
    validate_collaboration_contract(observation)
    return observation


def _finding_material(
    kind: str,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    path_evidence: Sequence[str] = (),
    authority_surfaces: Sequence[str] = (),
    validation_surfaces: Sequence[str] = (),
    exclusive_resource_ids: Sequence[str] = (),
) -> dict[str, Any]:
    workstreams = sorted({str(left["workstream_id"]), str(right["workstream_id"])})
    members = sorted({str(left["member_id"]), str(right["member_id"])})
    key_input = {
        "kind": kind,
        "workstream_ids": workstreams,
        "path_evidence": sorted(set(path_evidence)),
        "authority_surfaces": sorted(set(authority_surfaces)),
        "validation_surfaces": sorted(set(validation_surfaces)),
        "exclusive_resource_ids": sorted(set(exclusive_resource_ids)),
    }
    finding_key = _canonical_json_hash(_FINDING_KEY_DOMAIN, key_input)
    bindings = sorted(
        [
            {
                "workstream_id": str(scope["workstream_id"]),
                "scope_revision": int(scope["scope_revision"]),
                "scope_fingerprint": str(scope["scope_fingerprint"]),
            }
            for scope in (left, right)
        ],
        key=lambda item: item["workstream_id"],
    )
    fingerprint = _canonical_json_hash(
        _FINDING_FINGERPRINT_DOMAIN, {"finding_key": finding_key, "scope_bindings": bindings}
    )
    severity = "l3" if kind == "direct" or exclusive_resource_ids else "l2"
    return {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "overlap-finding",
        "finding_id": f"finding-{finding_key[:20]}",
        "kind": kind,
        "disposition": "open",
        "severity": severity,
        "workstream_ids": workstreams,
        "path_evidence": sorted(set(path_evidence)),
        "authority_surfaces": sorted(set(authority_surfaces)),
        "validation_surfaces": sorted(set(validation_surfaces)),
        "required_member_ids": members,
        "acknowledgements": [],
        "member_id": str(left["member_id"]),
        "host_id": str(left["host_id"]),
        "visibility": "worktree-local",
        "observability": "local",
        "created_at": _utc_timestamp(),
        "finding_key": finding_key,
        "finding_fingerprint": fingerprint,
        "finding_revision": 1,
        "scope_bindings": bindings,
        "path_provenance": [],
        "exclusive_resource_ids": sorted(set(exclusive_resource_ids)),
        "blocking": True,
        "acknowledgement_complete": False,
        "acknowledgement_progress": f"0/{len(members)}",
        "review_ready_blocked": True,
        "resolution_reason": None,
    }


def _add_path_provenance(
    finding: dict[str, Any], left: Mapping[str, Any], right: Mapping[str, Any]
) -> None:
    finding["path_provenance"] = [
        {
            "workstream_id": str(scope["workstream_id"]),
            "path": str(entry["path"]),
            "sources": list(entry["sources"]),
        }
        for scope, entry in (left, right)
    ]


def compute_overlap_findings(
    scopes: Sequence[Mapping[str, Any]],
    *,
    unavailable_peers: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    """Compute local/metadata findings without network access or semantic overclaiming."""
    validated_scopes: list[dict[str, Any]] = []
    for raw in scopes:
        scope = dict(raw)
        validate_collaboration_contract(scope)
        if scope.get("contract_type") != "scope-observation":
            raise ValueError("overlap inputs must be scope-observation contracts")
        validated_scopes.append(scope)
    findings: list[dict[str, Any]] = []
    semantic_priorities: list[dict[str, Any]] = []
    for left_index, left in enumerate(validated_scopes):
        for right in validated_scopes[left_index + 1 :]:
            if left["workstream_id"] == right["workstream_id"]:
                continue
            shared_subsystems = sorted(
                set(left["derived_subsystem_ids"]) & set(right["derived_subsystem_ids"])
            )
            if shared_subsystems:
                semantic_priorities.append(
                    {
                        "workstream_ids": sorted([left["workstream_id"], right["workstream_id"]]),
                        "shared_subsystem_ids": shared_subsystems,
                        "finding_created": False,
                        "reason": "shared-subsystem-priority-is-not-alone-proof-of-conflict",
                    }
                )
            for left_entry in left["path_entries"]:
                for right_entry in right["path_entries"]:
                    if not _path_specs_overlap(left_entry, right_entry):
                        continue
                    evidence = sorted({left_entry["path"], right_entry["path"]})
                    direct = _finding_material("direct", left, right, path_evidence=evidence)
                    _add_path_provenance(direct, (left, left_entry), (right, right_entry))
                    findings.append(direct)
                    shared_authority = sorted(
                        set(left_entry["authority_surfaces"])
                        & set(right_entry["authority_surfaces"])
                    )
                    if shared_authority:
                        authority = _finding_material(
                            "authority",
                            left,
                            right,
                            path_evidence=evidence,
                            authority_surfaces=shared_authority,
                        )
                        _add_path_provenance(authority, (left, left_entry), (right, right_entry))
                        findings.append(authority)
            shared_validations = sorted(
                set(left["validation_surfaces"]) & set(right["validation_surfaces"])
            )
            if shared_validations:
                findings.append(
                    _finding_material(
                        "semantic", left, right, validation_surfaces=shared_validations
                    )
                )
            left_resources = {
                resource
                for entry in left["path_entries"]
                for resource in entry["exclusive_resource_ids"]
            }
            right_resources = {
                resource
                for entry in right["path_entries"]
                for resource in entry["exclusive_resource_ids"]
            }
            shared_resources = sorted(left_resources & right_resources)
            if shared_resources:
                findings.append(
                    _finding_material(
                        "semantic", left, right, exclusive_resource_ids=shared_resources
                    )
                )
    if validated_scopes:
        local = validated_scopes[0]
        for peer in unavailable_peers:
            peer_workstream = peer.get("workstream_id", "unknown-peer")
            synthetic = {
                **local,
                "workstream_id": peer_workstream,
                "member_id": peer.get("member_id", "unknown-member"),
                "host_id": peer.get("host_id", "unknown-host"),
                "scope_fingerprint": "0" * 64,
                "scope_revision": 1,
            }
            unknown = _finding_material("unknown", local, synthetic)
            unknown.update(
                {
                    "visibility": "unknown",
                    "observability": "unavailable",
                    "resolution_reason": peer.get("reason", "peer-scope-unavailable"),
                }
            )
            findings.append(unknown)
    deduplicated: dict[str, dict[str, Any]] = {}
    for finding in findings:
        validate_collaboration_contract(finding)
        deduplicated[finding["finding_id"]] = finding
    return {
        "report_schema_version": OVERLAP_REPORT_SCHEMA_VERSION,
        "scopes": validated_scopes,
        "findings": [deduplicated[key] for key in sorted(deduplicated)],
        "semantic_priorities": semantic_priorities,
        "writes_performed": False,
        "network_performed": False,
    }


def _with_ack_progress(finding: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(finding)
    required = list(value.get("required_member_ids", []))
    acknowledgements = [dict(item) for item in value.get("acknowledgements", [])]
    acknowledged = {item["member_id"] for item in acknowledgements}
    count = len(acknowledged & set(required))
    complete = bool(required) and count == len(required)
    value.update(
        {
            "acknowledgements": acknowledgements,
            "acknowledgement_complete": complete,
            "acknowledgement_progress": f"{count}/{len(required)}",
            "disposition": "acknowledged" if count else "open",
            "blocking": not complete,
            "review_ready_blocked": not complete,
        }
    )
    return value


def acknowledge_overlap_finding(
    finding: Mapping[str, Any],
    *,
    member_id: str,
    reason: str,
    scope_revision: int,
    acknowledged_at: str | None = None,
    source: str = "member-local",
) -> dict[str, Any]:
    """Record a local human acknowledgement; Direct/L3 and remote/Agent sources fail closed."""
    value = dict(finding)
    validate_collaboration_contract(value)
    if source != "member-local":
        raise ValueError("finding acknowledgement must be confirmed by a member locally")
    if value["kind"] == "direct" or value["severity"] == "l3":
        raise ValueError("Direct and L3 findings cannot be acknowledged or waived")
    if value["disposition"] in {"resolved", "stale"}:
        raise ValueError("resolved or stale findings cannot be acknowledged")
    if member_id not in value["required_member_ids"]:
        raise ValueError("acknowledging member is not required by this finding")
    if not reason.strip():
        raise ValueError("finding acknowledgement requires a non-empty reason")
    binding = next(
        (item for item in value.get("scope_bindings", []) if item["workstream_id"] in value["workstream_ids"]),
        None,
    )
    if binding is not None and scope_revision not in {
        item["scope_revision"] for item in value["scope_bindings"]
    }:
        raise ValueError("finding acknowledgement scope revision does not match the finding")
    acknowledgements = [
        dict(item) for item in value.get("acknowledgements", []) if item["member_id"] != member_id
    ]
    acknowledgements.append(
        {
            "member_id": member_id,
            "reason": reason.strip(),
            "scope_revision": scope_revision,
            "acknowledged_at": _utc_timestamp(acknowledged_at),
            "finding_fingerprint": value["finding_fingerprint"],
        }
    )
    value["acknowledgements"] = sorted(acknowledgements, key=lambda item: item["member_id"])
    value = _with_ack_progress(value)
    validate_collaboration_contract(value)
    return value


def reconcile_overlap_findings(
    current: Sequence[Mapping[str, Any]], previous: Sequence[Mapping[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Carry current acknowledgements, stale changed bindings, and resolve disappeared findings."""
    previous_by_id = {str(item["finding_id"]): dict(item) for item in previous}
    active: list[dict[str, Any]] = []
    retired: list[dict[str, Any]] = []
    current_ids: set[str] = set()
    for raw in current:
        value = dict(raw)
        current_ids.add(value["finding_id"])
        old = previous_by_id.get(value["finding_id"])
        if old is not None and old.get("finding_fingerprint") == value.get("finding_fingerprint"):
            value["acknowledgements"] = [dict(item) for item in old.get("acknowledgements", [])]
            value["finding_revision"] = int(old.get("finding_revision", 1))
            value = _with_ack_progress(value)
        elif old is not None:
            stale = dict(old)
            stale.update(
                {
                    "disposition": "stale",
                    "blocking": False,
                    "review_ready_blocked": False,
                    "resolution_reason": "scope-or-baseline-binding-changed",
                }
            )
            retired.append(stale)
            value["finding_revision"] = int(old.get("finding_revision", 1)) + 1
        validate_collaboration_contract(value)
        active.append(value)
    for finding_id, old in previous_by_id.items():
        if finding_id in current_ids or old.get("disposition") in {"resolved", "stale"}:
            continue
        resolved = dict(old)
        resolved.update(
            {
                "disposition": "resolved",
                "blocking": False,
                "review_ready_blocked": False,
                "resolution_reason": "overlap-condition-no-longer-present",
            }
        )
        validate_collaboration_contract(resolved)
        retired.append(resolved)
    return {"active": active, "retired": retired}


def evaluate_scope_expansion(
    observation: Mapping[str, Any],
    session: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    active = [item for item in findings if item.get("disposition") in {"open", "acknowledged"}]
    exclusive = any(entry["exclusive_resource_ids"] for entry in observation["path_entries"])
    if exclusive or any(
        item.get("kind") == "direct" or item.get("severity") == "l3" for item in active
    ):
        level, allowed, reason = "l3", False, "direct-or-exclusive-resource-hard-gate"
    else:
        declared = set(observation["declared_subsystem_ids"])
        derived = set(observation["derived_subsystem_ids"])
        authority = any(entry["authority_surfaces"] for entry in observation["path_entries"])
        l2_findings = [item for item in active if item.get("severity") == "l2"]
        local_member = session.get("member_id")
        locally_acknowledged = all(
            any(ack.get("member_id") == local_member for ack in item.get("acknowledgements", []))
            for item in l2_findings
        )
        if (
            session.get("scope_fingerprint") == observation["scope_fingerprint"]
            and locally_acknowledged
        ):
            level, allowed, reason = "l0", True, "scope-unchanged"
        elif derived - declared or authority or l2_findings:
            level, allowed, reason = "l2", False, "local-member-confirmation-required"
        elif session.get("scope_fingerprint") != observation["scope_fingerprint"]:
            level, allowed, reason = "l1", True, "same-subsystem-safe-expansion"
        else:
            level, allowed, reason = "l0", True, "scope-unchanged"
    return {
        "expansion_schema_version": SCOPE_EXPANSION_SCHEMA_VERSION,
        "level": level,
        "allowed": allowed,
        "reason": reason,
        "local_confirmation_required": level == "l2",
        "hard_block": level == "l3",
        "central_override_allowed": False,
    }


def inspect_worktree_overlap(
    project_root: Path,
    *,
    peer_scopes: Sequence[Mapping[str, Any]] = (),
    include_local_worktrees: bool = True,
) -> dict[str, Any]:
    """Inspect current and explicitly visible peer scope without any network transport."""
    root = Path(project_root).expanduser().absolute()
    status = inspect_worktree_status(root)
    session = status["session"]["record"]
    if not isinstance(session, Mapping):
        raise ValueError("overlap inspection requires a private Workstream session")
    current = collect_scope_observation(root, session=session)
    scopes = [current]
    unavailable: list[dict[str, str]] = []
    if include_local_worktrees:
        config = load_collaboration_config(root)
        identity = status["identity"]
        primary = _normalized_path(Path(identity["primary_worktree_path"]))
        for record in _worktree_records(root):
            candidate = Path(str(record["worktree"]))
            normalized = _normalized_path(candidate)
            if normalized in {_normalized_path(root), primary}:
                continue
            peer_hint = f"local-{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]}"
            if not candidate.is_dir():
                unavailable.append(
                    {"workstream_id": peer_hint, "reason": "local-worktree-unavailable"}
                )
                continue
            try:
                peer_status = inspect_worktree_status(candidate)
                peer_session = peer_status["session"]["record"]
                if not isinstance(peer_session, Mapping):
                    unavailable.append(
                        {"workstream_id": peer_hint, "reason": "local-worktree-session-unavailable"}
                    )
                    continue
                scopes.append(collect_scope_observation(candidate, session=peer_session))
            except ValueError:
                unavailable.append(
                    {"workstream_id": peer_hint, "reason": "local-worktree-scope-unavailable"}
                )
    for peer in peer_scopes:
        value = dict(peer)
        validate_collaboration_contract(value)
        if value.get("contract_type") != "scope-observation":
            raise ValueError("peer scope file must contain a scope-observation contract")
        scopes.append(value)
    computed = compute_overlap_findings(scopes, unavailable_peers=unavailable)
    previous = session.get("findings", [])
    reconciled = reconcile_overlap_findings(computed["findings"], previous)
    review_ready_blocked = any(
        finding.get("review_ready_blocked", False) for finding in reconciled["active"]
    )
    return {
        **computed,
        "current_scope": current,
        "findings": reconciled["active"],
        "retired_findings": reconciled["retired"],
        "unavailable_peers": unavailable,
        "review_ready_blocked": review_ready_blocked,
        "writes_performed": False,
        "network_performed": False,
    }


def _accepted_affected_subsystems(
    session: Mapping[str, Any], observation: Mapping[str, Any]
) -> list[str]:
    primary = str(session["primary_subsystem_id"])
    affected = list(session.get("affected_subsystem_ids", []))
    for subsystem_id in observation["derived_subsystem_ids"]:
        if subsystem_id != primary and subsystem_id not in RESERVED_SUBSYSTEM_IDS:
            affected.append(subsystem_id)
    return list(dict.fromkeys(affected))


def refresh_workstream_scope(
    project_root: Path,
    *,
    peer_scopes: Sequence[Mapping[str, Any]] = (),
    include_local_worktrees: bool = True,
    confirm_l2: bool = False,
    reason: str | None = None,
    confirmation_source: str = "member-local",
    occurred_at: str | None = None,
) -> dict[str, Any]:
    """Apply Scope Expansion B to Git-private control metadata only."""
    root = Path(project_root).expanduser().absolute()
    status = inspect_worktree_status(root)
    if status["identity"]["is_primary"]:
        raise ValueError("scope refresh is prohibited in the primary worktree")
    raw_session = status["session"]["record"]
    if not isinstance(raw_session, Mapping):
        raise ValueError("scope refresh requires a private Workstream session")
    session = dict(raw_session)
    overlap = inspect_worktree_overlap(
        root, peer_scopes=peer_scopes, include_local_worktrees=include_local_worktrees
    )
    observation = overlap["current_scope"]
    decision = evaluate_scope_expansion(observation, session, overlap["findings"])
    timestamp = _utc_timestamp(occurred_at)
    if confirm_l2 and decision["level"] != "l2":
        raise ValueError("--confirm-l2 is valid only for an L2 scope expansion")
    if confirm_l2 and (confirmation_source != "member-local" or not reason or not reason.strip()):
        raise ValueError("L2 expansion requires a local member confirmation and reason")

    accepted = decision["level"] in {"l0", "l1"} or (decision["level"] == "l2" and confirm_l2)
    new_revision = int(session["scope_revision"])
    affected = list(session.get("affected_subsystem_ids", []))
    if decision["level"] in {"l1", "l2"} and accepted:
        new_revision += 1
        affected = _accepted_affected_subsystems(session, observation)
        observation = collect_scope_observation(
            root,
            session=session,
            scope_revision=new_revision,
            affected_subsystem_ids=affected,
            captured_at=timestamp,
        )
        scopes = [observation, *[scope for scope in overlap["scopes"] if scope is not overlap["current_scope"]]]
        recomputed = compute_overlap_findings(scopes, unavailable_peers=overlap["unavailable_peers"])
        reconciled = reconcile_overlap_findings(recomputed["findings"], session.get("findings", []))
        overlap["findings"] = reconciled["active"]
        overlap["retired_findings"] = reconciled["retired"]
        overlap["current_scope"] = observation

    if decision["level"] == "l2" and confirm_l2:
        confirmed: list[dict[str, Any]] = []
        for finding in overlap["findings"]:
            if finding["severity"] == "l2" and session["member_id"] in finding["required_member_ids"]:
                finding = acknowledge_overlap_finding(
                    finding,
                    member_id=str(session["member_id"]),
                    reason=str(reason),
                    scope_revision=new_revision,
                    acknowledged_at=timestamp,
                    source=confirmation_source,
                )
            confirmed.append(finding)
        overlap["findings"] = confirmed

    identity = inspect_worktree_identity(root, load_collaboration_config(root))
    session.update(
        {
            "worktree_id": identity["worktree_id"],
            "branch": identity["branch"],
            "head": identity["head"],
            "integration_ref": identity["integration_ref"],
            "integration_oid": identity["integration_oid"],
            "merge_base": identity["merge_base"],
            "dirty_fingerprint": identity["dirty_fingerprint"],
            "scope_revision": new_revision,
            "affected_subsystem_ids": affected,
            "scope_observation": observation,
            "findings": overlap["findings"],
            "finding_history": [
                *[dict(item) for item in session.get("finding_history", [])],
                *overlap["retired_findings"],
            ],
            "last_scope_expansion": {
                "level": decision["level"],
                "decision": (
                    "blocked"
                    if not accepted
                    else "confirmed-local"
                    if decision["level"] == "l2"
                    else "auto-revised"
                    if decision["level"] == "l1"
                    else "recorded"
                ),
                "reason": str(reason).strip() if confirm_l2 else decision["reason"],
                "member_id": str(session["member_id"]),
                "occurred_at": timestamp,
            },
            "captured_at": timestamp,
        }
    )
    if accepted:
        session["scope_fingerprint"] = observation["scope_fingerprint"]
    if accepted and session.get("runtime_condition") == "blocked-by-conflict":
        session["runtime_condition"] = "active"
    elif not accepted:
        session["runtime_condition"] = "blocked-by-conflict"
    write_result = _write_private_session(root, session)
    local_acknowledged = all(
        finding["severity"] != "l2"
        or any(ack["member_id"] == session["member_id"] for ack in finding["acknowledgements"])
        for finding in overlap["findings"]
    )
    review_ready_blocked = any(
        finding["severity"] == "l3"
        or finding["kind"] == "direct"
        or not finding.get("acknowledgement_complete", False)
        for finding in overlap["findings"]
    )
    return {
        "expansion": {**decision, "allowed": accepted},
        "scope": observation,
        "findings": overlap["findings"],
        "retired_findings": overlap["retired_findings"],
        "local_work_allowed": accepted and local_acknowledged,
        "review_ready_blocked": review_ready_blocked,
        "session": write_result["session"],
        "session_path": write_result["session_path"],
        "writes_performed": True,
        "network_performed": False,
    }


def acknowledge_workstream_finding(
    project_root: Path,
    *,
    finding_id: str,
    reason: str,
    source: str = "member-local",
    acknowledged_at: str | None = None,
) -> dict[str, Any]:
    """Acknowledge one stored L2 finding for the local owning Member."""
    root = Path(project_root).expanduser().absolute()
    status = inspect_worktree_status(root)
    session_record = status["session"]["record"]
    if not isinstance(session_record, Mapping):
        raise ValueError("finding acknowledgement requires a private Workstream session")
    session = dict(session_record)
    findings = [dict(item) for item in session.get("findings", [])]
    target_index = next(
        (index for index, item in enumerate(findings) if item["finding_id"] == finding_id), None
    )
    if target_index is None:
        raise ValueError("finding is not present in the current Workstream session")
    findings[target_index] = acknowledge_overlap_finding(
        findings[target_index],
        member_id=str(session["member_id"]),
        reason=reason,
        scope_revision=int(session["scope_revision"]),
        acknowledged_at=acknowledged_at,
        source=source,
    )
    session["findings"] = findings
    expansion_blocked = (
        isinstance(session.get("last_scope_expansion"), Mapping)
        and session["last_scope_expansion"].get("decision") == "blocked"
    )
    if not expansion_blocked and all(
        finding["severity"] != "l2"
        or any(ack["member_id"] == session["member_id"] for ack in finding["acknowledgements"])
        for finding in findings
    ) and not any(finding["severity"] == "l3" for finding in findings):
        session["runtime_condition"] = "active"
    result = _write_private_session(root, session)
    return {
        "finding": findings[target_index],
        "session_path": result["session_path"],
        "writes_performed": result["writes_performed"],
        "network_performed": False,
    }


def bootstrap_maintainer(member_id: str = "local-owner") -> dict[str, Any]:
    if not member_id:
        raise ValueError("bootstrap maintainer requires a member ID")
    contract = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "member",
        "member_id": member_id,
        "member_kind": "human",
        "base_role": "member",
        "status": "active",
        "capabilities": list(CAPABILITIES),
        "credential_epoch": 1,
        "credential_state": "active",
        "audit": [],
    }
    validate_collaboration_contract(contract)
    return contract


def _validated_member(member: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(member)
    if value.get("member_kind") != "human" or value.get("base_role") != "member":
        raise ValueError("governance capabilities belong only to human Member identities")
    capabilities = value.get("capabilities")
    if not isinstance(capabilities, list) or any(item not in CAPABILITIES for item in capabilities):
        raise ValueError("invalid member capability set")
    if len(set(capabilities)) != len(capabilities):
        raise ValueError("member capability set contains duplicates")
    if value.get("status") != "active":
        raise ValueError("removed members cannot change capabilities")
    validate_collaboration_contract(value)
    return value


def apply_capability_change(
    member: Mapping[str, Any],
    *,
    actor_id: str,
    action: str,
    capability: str,
    occurred_at: str,
) -> dict[str, Any]:
    value = _validated_member(member)
    if not actor_id or not occurred_at:
        raise ValueError("capability changes require actor and timestamp")
    if action not in {"grant", "revoke"} or capability not in CAPABILITIES:
        raise ValueError("unsupported capability change")
    before = list(value["capabilities"])
    present = capability in before
    if (action == "grant" and present) or (action == "revoke" and not present):
        raise ValueError("capability change must alter the member capability set")
    after = list(before)
    if action == "grant":
        after.append(capability)
        after.sort(key=CAPABILITIES.index)
    else:
        after.remove(capability)
    epoch = int(value.get("credential_epoch", 0)) + 1
    audit = [dict(item) for item in value.get("audit", [])]
    audit.append(
        {
            "actor_id": actor_id,
            "action": action,
            "capability": capability,
            "before": before,
            "after": after,
            "credential_epoch": epoch,
            "occurred_at": occurred_at,
        }
    )
    value.update({"capabilities": after, "credential_epoch": epoch, "audit": audit})
    validate_collaboration_contract(value)
    return value


def remove_member(member: Mapping[str, Any], *, actor_id: str, occurred_at: str) -> dict[str, Any]:
    value = _validated_member(member)
    before = list(value["capabilities"])
    epoch = int(value.get("credential_epoch", 0)) + 1
    audit = [dict(item) for item in value.get("audit", [])]
    audit.append(
        {
            "actor_id": actor_id,
            "action": "remove-member",
            "capability": None,
            "before": before,
            "after": [],
            "credential_epoch": epoch,
            "occurred_at": occurred_at,
        }
    )
    value.update(
        {
            "status": "removed",
            "capabilities": [],
            "credential_epoch": epoch,
            "credential_state": "revoked",
            "audit": audit,
        }
    )
    validate_collaboration_contract(value)
    return value


def credential_is_current(member: Mapping[str, Any], credential_epoch: int) -> bool:
    return (
        isinstance(credential_epoch, int)
        and not isinstance(credential_epoch, bool)
        and member.get("status") == "active"
        and member.get("credential_state") == "active"
        and member.get("credential_epoch") == credential_epoch
    )


def build_project_mode_contract(config: CollaborationConfig) -> dict[str, Any]:
    personal = config.project_mode == "personal"
    contract = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "project-mode",
        "project_mode": config.project_mode,
        "runtime_status": "personal-local-only" if personal else "contract-only",
        "member_identity": "implicit-local" if personal else "explicit-member-required",
        "active_network_features": [],
        "network_boundaries": {
            "listener": False,
            "discovery": False,
            "coordinator": False,
            "member_authentication": False,
            "team_sync": False,
            "heartbeat": False,
        },
    }
    validate_collaboration_contract(contract)
    return contract


def inspect_collaboration(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    config = load_collaboration_config(root)
    return {
        "contract_id": COLLABORATION_CONTRACT_ID,
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "config_keys": {
            "integration_ref": INTEGRATION_REF_CONFIG_KEY,
            "primary_worktree": PRIMARY_WORKTREE_CONFIG_KEY,
            "project_mode": PROJECT_MODE_CONFIG_KEY,
            "exclusive_resources": EXCLUSIVE_RESOURCES_CONFIG_KEY,
        },
        "identity": inspect_worktree_identity(root, config),
        "mode": build_project_mode_contract(config),
        "bootstrap_maintainer": bootstrap_maintainer(),
        "subsystems": load_subsystem_registry(root),
        "exclusive_resources": [dict(item) for item in config.exclusive_resources],
    }
