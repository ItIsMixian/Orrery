"""Provider-neutral collaboration contracts and local Git inspection."""
from __future__ import annotations

import datetime as dt
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
DEFAULT_INTEGRATION_REF = "refs/heads/main"
INTEGRATION_REF_CONFIG_KEY = "collaboration.integration_ref"
PRIMARY_WORKTREE_CONFIG_KEY = "collaboration.primary_worktree"
PROJECT_MODE_CONFIG_KEY = "collaboration.project_mode"
RESERVED_SUBSYSTEM_IDS = ("unmapped", "project-wide")
CAPABILITIES = ("reviewer", "integrator", "admin")
_COLLABORATION_CONFIG_FIELDS = {"integration_ref", "primary_worktree", "project_mode"}
_SUBSYSTEM_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_DIRTY_FINGERPRINT_DOMAIN = b"project-orrery-dirty-fingerprint-v1\0"
_SESSION_STALE_FIELDS = (
    ("worktree_id", "worktree-id-changed"),
    ("branch", "branch-changed"),
    ("head", "head-changed"),
    ("integration_ref", "integration-ref-changed"),
    ("integration_oid", "integration-oid-changed"),
    ("dirty_fingerprint", "dirty-fingerprint-changed"),
)


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
        return cls(
            integration_ref=integration_ref,
            primary_worktree=primary_worktree,
            project_mode=str(project_mode),
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
        "platform_session": None,
        "branch": identity["branch"],
        "head": identity["head"],
        "integration_ref": identity["integration_ref"],
        "integration_oid": identity["integration_oid"],
        "merge_base": identity["merge_base"],
        "dirty_fingerprint": identity["dirty_fingerprint"],
        "lifecycle_phase": lifecycle_phase,
        "runtime_condition": runtime_condition,
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
    return session


def write_workstream_session(project_root: Path, **session_fields: Any) -> dict[str, Any]:
    """Atomically persist one reconstructable session under the private Git path."""
    root = Path(project_root).expanduser().absolute()
    session = build_workstream_session(root, **session_fields)
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
        "session": session,
        "writes_performed": True,
    }


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
        },
        "identity": inspect_worktree_identity(root, config),
        "mode": build_project_mode_contract(config),
        "bootstrap_maintainer": bootstrap_maintainer(),
        "subsystems": load_subsystem_registry(root),
    }
