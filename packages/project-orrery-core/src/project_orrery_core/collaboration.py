"""Provider-neutral Phase 0 collaboration contracts and local Git inspection."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .schema import COLLABORATION_SCHEMA


COLLABORATION_SCHEMA_VERSION = 1
COLLABORATION_CONTRACT_ID = "project-orrery-collaboration-v1"
DEFAULT_INTEGRATION_REF = "refs/heads/main"
INTEGRATION_REF_CONFIG_KEY = "collaboration.integration_ref"
PRIMARY_WORKTREE_CONFIG_KEY = "collaboration.primary_worktree"
PROJECT_MODE_CONFIG_KEY = "collaboration.project_mode"
RESERVED_SUBSYSTEM_IDS = ("unmapped", "project-wide")
CAPABILITIES = ("reviewer", "integrator", "admin")
_COLLABORATION_CONFIG_FIELDS = {"integration_ref", "primary_worktree", "project_mode"}
_SUBSYSTEM_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


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
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _absolute_git_path(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return Path(os.path.abspath(os.fspath(path)))


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
    dirty = bool(_run_git(root, "status", "--porcelain=v1", "-z", binary=True))
    integration_oid = resolve_integration_oid(root, config.integration_ref)
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
        "is_primary": is_primary,
        "primary_worktree_path": str(Path(str(primary["worktree"])).absolute()),
        "primary_worktree_source": primary_source,
        "integration_ref": config.integration_ref,
        "integration_oid": integration_oid,
        "fact_scope": fact_scope,
        "member_id": member_id,
        "host_id": host_id,
        "visibility": "worktree-local",
        "observability": "local",
    }
    validate_collaboration_contract(contract)
    return contract


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
