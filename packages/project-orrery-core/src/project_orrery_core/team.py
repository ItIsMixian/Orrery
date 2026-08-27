"""Opt-in, metadata-only Team Mode foundation.

The module intentionally uses only the Python standard library.  Personal Mode
does not import or start this runtime.  Team state and credentials live below
the repository's private Git directory and never enter the author worktree.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import stat
import subprocess
import tempfile
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .collaboration import (
    CAPABILITIES,
    apply_capability_change,
    bootstrap_maintainer,
    inspect_worktree_status,
)


TEAM_SCHEMA_VERSION = 1
TEAM_CONTRACT_ID = "project-orrery-team-v1"
TEAM_ENVELOPE_MAX_BYTES = 64 * 1024
TEAM_REQUEST_MAX_BYTES = 16 * 1024
DEFAULT_DEBOUNCE_MILLISECONDS = 750
DEFAULT_TTL_SECONDS = 300
DEFAULT_HEARTBEAT_SECONDS = 60
FORBIDDEN_FIELD_FRAGMENTS = (
    "prompt", "answer", "response_text", "reasoning", "transcript", "conversation",
    "source_code", "source_text", "file_content", "file_contents", "diff", "patch",
    "credential", "password", "secret", "token", "api_key", "private_key",
)
REQUEST_KINDS = (
    "create-workstream", "pause-workstream", "resume-workstream", "stop-workstream",
    "expand-scope", "run-validation", "request-review", "prepare-integration", "cleanup",
)
REQUEST_CAPABILITIES = {
    "request-review": "reviewer",
    "prepare-integration": "integrator",
    "cleanup": "integrator",
}
_DOMAIN = b"project-orrery-team-v1\0"
_STATE_LOCK = threading.RLock()


def _timestamp(value: str | None = None) -> str:
    return value or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp must be RFC 3339") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(_DOMAIN + value.encode("utf-8")).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _git(project_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project_root), *arguments], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode:
        raise ValueError(f"cannot inspect Git team identity: {completed.stderr.strip() or completed.stdout.strip()}")
    return completed.stdout.strip()


def team_private_dir(project_root: Path) -> Path:
    root = Path(project_root).expanduser().absolute()
    common = Path(_git(root, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    return common.resolve() / "orrery" / "team"


def _atomic_json(path: Path, payload: Mapping[str, Any], *, private: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"private Team path is not a regular file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if private:
            os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists() and not required:
        return {}
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise OSError("not a regular file")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read private Team state {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"private Team state must be an object: {path}")
    return value


def project_fingerprint(project_root: Path) -> str:
    root = Path(project_root).expanduser().absolute()
    try:
        manifest = json.loads((root / ".project-orrery.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read project identity: {exc}") from exc
    roots = sorted(filter(None, _git(root, "rev-list", "--max-parents=0", "HEAD").splitlines()))
    material = {"name": manifest.get("name"), "manifest_format": manifest.get("manifest_format"), "roots": roots}
    return hashlib.sha256(_DOMAIN + _json_bytes(material)).hexdigest()


def _team_config_path(project_root: Path) -> Path:
    return team_private_dir(project_root) / "config.json"


def load_team_config(project_root: Path) -> dict[str, Any]:
    path = _team_config_path(project_root)
    value = _read_json(path, required=False)
    if not value:
        return {
            "schema_version": TEAM_SCHEMA_VERSION, "contract_type": "team-config",
            "enabled": False, "runtime_status": "personal-zero-network",
            "network_features": [], "heartbeat": {"enabled": False},
        }
    _validate_team_config(value)
    return value


def _validate_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise ValueError(f"{label} must be a non-empty string up to 128 characters")
    if any(character.isspace() for character in value):
        raise ValueError(f"{label} must not contain whitespace")
    return value


def _validate_team_config(value: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "contract_type", "enabled", "runtime_status", "project_fingerprint",
        "member_id", "device_id", "host_id", "active_host_id", "allow_lan_bind", "sharing_enabled",
        "debounce_milliseconds", "ttl_seconds", "heartbeat", "revision", "network_features", "updated_at",
    }
    if set(value) != required:
        raise ValueError("Team config has missing or unknown fields")
    if value["schema_version"] != 1 or value["contract_type"] != "team-config":
        raise ValueError("unsupported Team config contract")
    for key in ("member_id", "device_id", "host_id", "active_host_id"):
        _validate_id(value[key], key)
    if not isinstance(value["enabled"], bool) or not isinstance(value["allow_lan_bind"], bool):
        raise ValueError("Team config enable and LAN flags must be booleans")
    if not isinstance(value["sharing_enabled"], bool):
        raise ValueError("Team sharing flag must be boolean")
    if value["runtime_status"] not in {"team-enabled-stopped", "team-runtime-active"}:
        raise ValueError("invalid Team runtime status")
    if not isinstance(value["revision"], int) or isinstance(value["revision"], bool) or value["revision"] < 0:
        raise ValueError("Team revision must be a non-negative integer")
    if not 0 <= value["debounce_milliseconds"] <= 60_000:
        raise ValueError("Team debounce must be between 0 and 60000 milliseconds")
    if not 5 <= value["ttl_seconds"] <= 86_400:
        raise ValueError("Team TTL must be between 5 and 86400 seconds")
    heartbeat = value["heartbeat"]
    if not isinstance(heartbeat, Mapping) or set(heartbeat) != {"enabled", "interval_seconds"}:
        raise ValueError("Team heartbeat config is invalid")
    if not isinstance(heartbeat["enabled"], bool) or not 5 <= heartbeat["interval_seconds"] <= 86_400:
        raise ValueError("Team heartbeat interval must be between 5 and 86400 seconds")
    if not isinstance(value["network_features"], list):
        raise ValueError("Team network features must be an array")
    _parse_timestamp(value["updated_at"])


def _credential_path(project_root: Path) -> Path:
    return team_private_dir(project_root) / "credential.json"


def _coordinator_path(project_root: Path) -> Path:
    return team_private_dir(project_root) / "coordinator.json"


def _runtime_path(project_root: Path) -> Path:
    return team_private_dir(project_root) / "runtime.json"


def enable_team(
    project_root: Path, *, member_id: str, device_id: str, host_id: str,
    allow_lan_bind: bool = False, ttl_seconds: int = DEFAULT_TTL_SECONDS,
    debounce_milliseconds: int = DEFAULT_DEBOUNCE_MILLISECONDS,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    """Explicitly enable Team Mode without opening any socket."""
    root = Path(project_root).expanduser().absolute()
    for value, label in ((member_id, "member_id"), (device_id, "device_id"), (host_id, "host_id")):
        _validate_id(value, label)
    timestamp = _timestamp(occurred_at)
    _parse_timestamp(timestamp)
    existing = load_team_config(root)
    revision = int(existing.get("revision", 0))
    config = {
        "schema_version": 1, "contract_type": "team-config", "enabled": True,
        "runtime_status": "team-enabled-stopped", "project_fingerprint": project_fingerprint(root),
        "member_id": member_id, "device_id": device_id, "host_id": host_id,
        "active_host_id": host_id, "allow_lan_bind": bool(allow_lan_bind),
        "sharing_enabled": True, "debounce_milliseconds": debounce_milliseconds,
        "ttl_seconds": ttl_seconds,
        "heartbeat": {"enabled": False, "interval_seconds": DEFAULT_HEARTBEAT_SECONDS},
        "revision": revision, "network_features": [], "updated_at": timestamp,
    }
    _validate_team_config(config)
    token = secrets.token_urlsafe(32)
    member = bootstrap_maintainer(member_id)
    coordinator = {
        "schema_version": 1, "contract_type": "coordinator-state",
        "project_fingerprint": config["project_fingerprint"], "coordinator_host_id": host_id,
        "members": {member_id: member},
        "credentials": {_hash(token): {"member_id": member_id, "credential_epoch": 1}},
        "active_hosts": {member_id: {"host_id": host_id, "device_id": device_id, "switched_at": timestamp}},
        "snapshots": {}, "invites": {}, "join_requests": {}, "requests": {}, "updated_at": timestamp,
    }
    with _STATE_LOCK:
        _atomic_json(_team_config_path(root), config)
        if _coordinator_path(root).exists():
            coordinator = _read_json(_coordinator_path(root))
            if not hmac.compare_digest(
                str(coordinator.get("project_fingerprint")), str(config["project_fingerprint"])
            ):
                raise ValueError("existing private Coordinator belongs to another project identity")
            current_member = coordinator.setdefault("members", {}).get(member_id)
            if current_member is None:
                coordinator["members"][member_id] = member
                current_member = member
            if current_member.get("status") != "active":
                raise ValueError("removed member cannot re-enable Team Mode")
            coordinator["credentials"] = {
                key: item for key, item in coordinator.get("credentials", {}).items()
                if item.get("member_id") != member_id
            }
            coordinator["credentials"][_hash(token)] = {
                "member_id": member_id, "credential_epoch": current_member["credential_epoch"],
            }
            coordinator.setdefault("active_hosts", {})[member_id] = {
                "host_id": host_id, "device_id": device_id, "switched_at": timestamp,
            }
            coordinator["updated_at"] = timestamp
        _atomic_json(_coordinator_path(root), coordinator)
        _atomic_json(_credential_path(root), {
            "schema_version": 1, "member_id": member_id, "credential_epoch": 1, "token": token,
        })
    return {"config": _redacted_config(config), "writes_performed": True, "network_performed": False}


def _redacted_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return dict(config)


def configure_heartbeat(
    project_root: Path, *, enabled: bool, interval_seconds: int = DEFAULT_HEARTBEAT_SECONDS,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be explicitly enabled before configuring heartbeat")
    if not 5 <= interval_seconds <= 86_400:
        raise ValueError("heartbeat interval must be between 5 and 86400 seconds")
    config["heartbeat"] = {"enabled": bool(enabled), "interval_seconds": interval_seconds}
    config["updated_at"] = _timestamp(occurred_at)
    _validate_team_config(config)
    _atomic_json(_team_config_path(project_root), config)
    return {"heartbeat": dict(config["heartbeat"]), "network_performed": False}


def set_sharing(project_root: Path, *, enabled: bool, occurred_at: str | None = None) -> dict[str, Any]:
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be explicitly enabled before changing sharing")
    config["sharing_enabled"] = bool(enabled)
    config["updated_at"] = _timestamp(occurred_at)
    _validate_team_config(config)
    _atomic_json(_team_config_path(project_root), config)
    return {"sharing_enabled": config["sharing_enabled"], "network_performed": False}


def switch_active_host(
    project_root: Path, *, host_id: str, device_id: str, occurred_at: str | None = None,
) -> dict[str, Any]:
    """Manually switch this member's one active Host; no election is attempted."""
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be enabled before switching Host")
    _validate_id(host_id, "host_id")
    _validate_id(device_id, "device_id")
    config.update({"host_id": host_id, "device_id": device_id, "active_host_id": host_id})
    config["revision"] = int(config["revision"]) + 1
    config["updated_at"] = _timestamp(occurred_at)
    _validate_team_config(config)
    _atomic_json(_team_config_path(project_root), config)
    return {"active_host_id": host_id, "revision": config["revision"], "network_performed": False}


def _forbidden_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(fragment in normalized for fragment in FORBIDDEN_FIELD_FRAGMENTS)


def _reject_forbidden(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or _forbidden_key(key):
                raise ValueError(f"forbidden Team payload field at {path}.{key}")
            _reject_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden(item, f"{path}[{index}]")
    elif isinstance(value, str) and len(value.encode("utf-8")) > 4096:
        raise ValueError(f"Team payload string is too large at {path}")


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        extra = sorted(set(value) - expected)
        missing = sorted(expected - set(value))
        raise ValueError(f"{label} has forbidden fields {extra} or missing fields {missing}")


def validate_metadata_envelope(envelope: Mapping[str, Any], *, raw_size: int | None = None) -> None:
    if not isinstance(envelope, Mapping):
        raise ValueError("Team envelope must be an object")
    size = len(_json_bytes(envelope)) if raw_size is None else raw_size
    if size > TEAM_ENVELOPE_MAX_BYTES:
        raise ValueError("Team envelope exceeds the 64 KiB metadata limit")
    _reject_forbidden(envelope)
    _exact_keys(envelope, {
        "schema_version", "contract_type", "project_fingerprint", "member_id", "device_id", "host_id",
        "workstream_id", "revision", "occurred_at", "ttl_seconds", "heartbeat", "sharing_state",
        "member", "host", "workstream", "git", "scope", "finding", "validation", "review", "last_seen",
    }, "Team envelope")
    if envelope["schema_version"] != 1 or envelope["contract_type"] != "team-metadata-envelope":
        raise ValueError("unsupported Team envelope version")
    if not isinstance(envelope["project_fingerprint"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", envelope["project_fingerprint"]
    ):
        raise ValueError("invalid Team project fingerprint")
    for key in ("member_id", "device_id", "host_id", "workstream_id"):
        _validate_id(envelope[key], key)
    if not isinstance(envelope["revision"], int) or isinstance(envelope["revision"], bool) or envelope["revision"] < 1:
        raise ValueError("Team envelope revision must be a positive integer")
    if envelope["sharing_state"] not in {"sharing", "off", "offline"}:
        raise ValueError("invalid Team sharing state")
    _parse_timestamp(envelope["occurred_at"])
    _parse_timestamp(envelope["last_seen"])
    heartbeat = envelope["heartbeat"]
    _exact_keys(heartbeat, {"enabled", "interval_seconds"}, "heartbeat")
    if (
        not isinstance(heartbeat["enabled"], bool)
        or not isinstance(heartbeat["interval_seconds"], int)
        or isinstance(heartbeat["interval_seconds"], bool)
        or not 5 <= heartbeat["interval_seconds"] <= 86_400
    ):
        raise ValueError("invalid Team heartbeat metadata")
    if not isinstance(envelope["ttl_seconds"], int) or not 5 <= envelope["ttl_seconds"] <= 86_400:
        raise ValueError("invalid Team TTL")
    nested = {
        "member": {"status", "capabilities"},
        "host": {"active", "device_id"},
        "workstream": {"lifecycle_phase", "runtime_condition", "evidence_freshness", "last_activity"},
        "git": {"branch", "head", "integration_ref", "integration_oid", "merge_base", "ahead", "behind", "dirty_count"},
        "scope": {"revision", "primary_subsystem_id", "affected_subsystem_ids", "path_summary", "visibility", "observability"},
        "finding": {"open", "acknowledged", "resolved", "stale", "direct", "authority", "semantic", "unknown"},
        "validation": {"passed", "failed", "skipped", "unknown", "evidence_freshness", "last_completed_at"},
        "review": {"status", "human_approvals", "non_author_required", "last_decision_at"},
    }
    for key, expected in nested.items():
        if not isinstance(envelope[key], Mapping):
            raise ValueError(f"Team {key} metadata must be an object")
        _exact_keys(envelope[key], expected, key)
    member = envelope["member"]
    if member["status"] not in {"active", "removed"}:
        raise ValueError("invalid Team member lifecycle")
    if (
        not isinstance(member["capabilities"], list)
        or len(set(member["capabilities"])) != len(member["capabilities"])
        or any(item not in CAPABILITIES for item in member["capabilities"])
    ):
        raise ValueError("invalid Team member capability metadata")
    host = envelope["host"]
    if not isinstance(host["active"], bool) or host["device_id"] != envelope["device_id"]:
        raise ValueError("invalid Team Host metadata")
    workstream = envelope["workstream"]
    if workstream["lifecycle_phase"] not in {
        "created", "investigating", "implementing", "validating", "review-ready", "integrated", "closed",
    }:
        raise ValueError("invalid Team Workstream lifecycle")
    if workstream["runtime_condition"] not in {
        "active", "waiting-for-user", "paused", "blocked-by-conflict", "failed", "offline", "stale-unknown",
    }:
        raise ValueError("invalid Team Workstream runtime condition")
    if workstream["evidence_freshness"] not in {"unknown", "current", "stale"}:
        raise ValueError("invalid Team evidence freshness")
    _parse_timestamp(workstream["last_activity"])
    git = envelope["git"]
    if git["branch"] is not None and (not isinstance(git["branch"], str) or len(git["branch"]) > 512):
        raise ValueError("invalid Team Git branch metadata")
    for key in ("head", "integration_oid", "merge_base"):
        if not isinstance(git[key], str) or re.fullmatch(r"[0-9a-f]{40}([0-9a-f]{24})?", git[key]) is None:
            raise ValueError(f"invalid Team Git {key} metadata")
    if not isinstance(git["integration_ref"], str) or not git["integration_ref"].startswith("refs/heads/"):
        raise ValueError("invalid Team integration ref")
    for key in ("ahead", "behind", "dirty_count"):
        if not isinstance(git[key], int) or isinstance(git[key], bool) or git[key] < 0:
            raise ValueError(f"invalid Team Git {key} metadata")
    scope = envelope["scope"]
    if not isinstance(scope["revision"], int) or isinstance(scope["revision"], bool) or scope["revision"] < 1:
        raise ValueError("invalid Team Scope revision")
    _validate_id(scope["primary_subsystem_id"], "primary_subsystem_id")
    if (
        not isinstance(scope["affected_subsystem_ids"], list)
        or len(set(scope["affected_subsystem_ids"])) != len(scope["affected_subsystem_ids"])
        or any(not isinstance(item, str) or not item for item in scope["affected_subsystem_ids"])
    ):
        raise ValueError("invalid Team affected subsystem metadata")
    if scope["visibility"] != "local-only" or scope["observability"] != "shared-metadata":
        raise ValueError("Team Scope must remain Local-only shared metadata")
    if len(envelope["scope"]["path_summary"]) > 128:
        raise ValueError("Team scope path summary exceeds 128 entries")
    if not all(isinstance(item, str) and 0 < len(item) <= 512 for item in envelope["scope"]["path_summary"]):
        raise ValueError("Team scope paths must be bounded strings")
    for group in (envelope["finding"], envelope["validation"]):
        for key, value in group.items():
            if key in {"evidence_freshness", "last_completed_at"}:
                continue
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("Team counters must be non-negative integers")
    validation = envelope["validation"]
    if validation["evidence_freshness"] not in {"unknown", "current", "stale"}:
        raise ValueError("invalid Team validation freshness")
    if validation["last_completed_at"] is not None:
        _parse_timestamp(validation["last_completed_at"])
    review = envelope["review"]
    if review["status"] not in {"not-submitted", "pending", "approved", "changes", "held", "rejected"}:
        raise ValueError("invalid Team review status")
    if not isinstance(review["human_approvals"], int) or isinstance(review["human_approvals"], bool) or review["human_approvals"] < 0:
        raise ValueError("invalid Team human approval count")
    if not isinstance(review["non_author_required"], bool):
        raise ValueError("invalid Team reviewer policy metadata")
    if review["last_decision_at"] is not None:
        _parse_timestamp(review["last_decision_at"])


def _count_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    result = {key: 0 for key in ("open", "acknowledged", "resolved", "stale", "direct", "authority", "semantic", "unknown")}
    for finding in findings:
        status = str(finding.get("status", "open")).lower()
        kind = str(finding.get("kind", "unknown")).lower()
        if status in result:
            result[status] += 1
        if kind in {"direct", "authority", "semantic", "unknown"}:
            result[kind] += 1
    return result


def capture_metadata_envelope(project_root: Path, *, occurred_at: str | None = None) -> dict[str, Any]:
    """Mechanically project the existing W1-W3 session into bounded Team metadata."""
    root = Path(project_root).expanduser().absolute()
    config = load_team_config(root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be explicitly enabled before capture")
    status = inspect_worktree_status(root)
    local_state = _read_json(_coordinator_path(root), required=False)
    local_member = local_state.get("members", {}).get(config["member_id"], {})
    identity = status["identity"]
    record = status["session"].get("record") or {}
    timestamp = _timestamp(occurred_at)
    revision = int(config["revision"]) + 1
    config["revision"] = revision
    config["updated_at"] = timestamp
    _atomic_json(_team_config_path(root), config)
    workstream_id = str(record.get("workstream_id") or f"workspace-{identity['worktree_id'][:16]}")
    findings = [item for item in record.get("findings", []) if isinstance(item, Mapping)]
    path_summary: list[str] = []
    scope = record.get("scope_observation")
    if isinstance(scope, Mapping):
        for entry in scope.get("path_entries", []):
            if isinstance(entry, Mapping) and isinstance(entry.get("path"), str):
                path_summary.append(entry["path"])
    if not path_summary:
        path_summary = [str(item) for item in record.get("expected_writes", []) if isinstance(item, str)]
    dirty_count = sum(
        int(identity.get(key, 0))
        for key in ("staged_count", "unstaged_count", "untracked_count")
    )
    envelope = {
        "schema_version": 1, "contract_type": "team-metadata-envelope",
        "project_fingerprint": config["project_fingerprint"], "member_id": config["member_id"],
        "device_id": config["device_id"], "host_id": config["host_id"], "workstream_id": workstream_id,
        "revision": revision, "occurred_at": timestamp, "ttl_seconds": config["ttl_seconds"],
        "heartbeat": dict(config["heartbeat"]),
        "sharing_state": "sharing" if config["sharing_enabled"] else "off",
        "member": {
            "status": local_member.get("status", "active"),
            "capabilities": list(local_member.get("capabilities", CAPABILITIES)),
        },
        "host": {"active": config["host_id"] == config["active_host_id"], "device_id": config["device_id"]},
        "workstream": {
            "lifecycle_phase": record.get("lifecycle_phase", "created"),
            "runtime_condition": record.get("runtime_condition", "stale-unknown"),
            "evidence_freshness": record.get("evidence_freshness", "unknown"),
            "last_activity": record.get("captured_at", timestamp),
        },
        "git": {
            "branch": identity.get("branch"), "head": identity["head"],
            "integration_ref": identity["integration_ref"], "integration_oid": identity["integration_oid"],
            "merge_base": identity["merge_base"], "ahead": identity["ahead"], "behind": identity["behind"],
            "dirty_count": dirty_count,
        },
        "scope": {
            "revision": int(record.get("scope_revision", 1)),
            "primary_subsystem_id": record.get("primary_subsystem_id", "unmapped"),
            "affected_subsystem_ids": list(record.get("affected_subsystem_ids", [])),
            "path_summary": sorted(set(path_summary))[:128], "visibility": "local-only",
            "observability": "shared-metadata",
        },
        "finding": _count_findings(findings),
        "validation": {
            "passed": 0, "failed": 0, "skipped": 0, "unknown": len(record.get("validation_surfaces", [])),
            "evidence_freshness": record.get("evidence_freshness", "unknown"), "last_completed_at": None,
        },
        "review": {"status": "not-submitted", "human_approvals": 0, "non_author_required": False, "last_decision_at": None},
        "last_seen": timestamp,
    }
    validate_metadata_envelope(envelope)
    return envelope


def _outbox_path(project_root: Path) -> Path:
    config = load_team_config(project_root)
    return team_private_dir(project_root) / "hosts" / str(config.get("host_id", "unknown")) / "outbox.json"


def queue_sync_event(
    project_root: Path, envelope: Mapping[str, Any], *, event_kind: str = "workstream-change",
    immediate: bool = False,
) -> dict[str, Any]:
    validate_metadata_envelope(envelope)
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be enabled before queueing sync")
    path = _outbox_path(project_root)
    value = _read_json(path, required=False) or {"schema_version": 1, "events": []}
    events = list(value.get("events", []))
    coalesce_key = f"{envelope['member_id']}:{envelope['workstream_id']}:{event_kind}"
    event = {
        "event_id": f"event-{secrets.token_hex(12)}", "event_kind": event_kind,
        "coalesce_key": coalesce_key, "queued_at": _timestamp(), "immediate": bool(immediate),
        "envelope": dict(envelope),
    }
    events = [item for item in events if item.get("coalesce_key") != coalesce_key]
    events.append(event)
    _atomic_json(path, {"schema_version": 1, "events": events})
    return {"queued": True, "event_count": len(events), "coalesced_by": coalesce_key, "network_performed": False}


def inspect_outbox(project_root: Path) -> dict[str, Any]:
    value = _read_json(_outbox_path(project_root), required=False) or {"schema_version": 1, "events": []}
    return {"events": list(value.get("events", [])), "network_performed": False}


def _validate_endpoint(endpoint: str, *, allow_lan: bool) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.username or parsed.password or parsed.path not in {"", "/"}:
        raise ValueError("Coordinator endpoint must be a bare http://IP:port address")
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as exc:
        raise ValueError("Coordinator endpoint must use an IP literal; DNS names are not allowed") from exc
    if address.is_loopback:
        return endpoint.rstrip("/")
    if not allow_lan or not address.is_private:
        raise ValueError("non-loopback Coordinator endpoints require explicit LAN opt-in and a private IP")
    return endpoint.rstrip("/")


def _load_local_credential(project_root: Path) -> dict[str, Any]:
    value = _read_json(_credential_path(project_root))
    if set(value) != {"schema_version", "member_id", "credential_epoch", "token"}:
        raise ValueError("local Team credential is malformed")
    return value


def _auth_header(credential: Mapping[str, Any]) -> str:
    return f"Bearer {credential['token']}"


def _http_json(
    endpoint: str, path: str, *, method: str = "GET", payload: Mapping[str, Any] | None = None,
    credential: Mapping[str, Any] | None = None, allow_lan: bool = False,
) -> dict[str, Any]:
    base = _validate_endpoint(endpoint, allow_lan=allow_lan)
    data = None if payload is None else _json_bytes(payload)
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if credential is not None:
        headers["Authorization"] = _auth_header(credential)
    request = Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - endpoint is validated IP-only
            raw = response.read(TEAM_ENVELOPE_MAX_BYTES + 1)
    except HTTPError as exc:
        raw = exc.read(TEAM_REQUEST_MAX_BYTES)
        try:
            detail = json.loads(raw.decode("utf-8")).get("error", str(exc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            detail = str(exc)
        raise ValueError(f"Coordinator rejected request: {detail}") from exc
    except URLError as exc:
        raise ValueError(f"Coordinator request failed: {exc.reason}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Coordinator returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("Coordinator response must be an object")
    return value


def sync_now(project_root: Path, *, endpoint: str) -> dict[str, Any]:
    config = load_team_config(project_root)
    if not config.get("enabled") or not config.get("sharing_enabled"):
        raise ValueError("Team Mode and sharing must be enabled before synchronization")
    credential = _load_local_credential(project_root)
    outbox_path = _outbox_path(project_root)
    outbox = _read_json(outbox_path, required=False) or {"schema_version": 1, "events": []}
    events = list(outbox.get("events", []))
    accepted: list[str] = []
    for event in events:
        result = _http_json(
            endpoint, "/v1/sync", method="POST", payload=event["envelope"], credential=credential,
            allow_lan=bool(config["allow_lan_bind"]),
        )
        if result.get("accepted"):
            accepted.append(event["event_id"])
    remaining = [item for item in events if item.get("event_id") not in accepted]
    _atomic_json(outbox_path, {"schema_version": 1, "events": remaining})
    return {"accepted": len(accepted), "remaining": len(remaining), "network_performed": bool(events)}


def create_invite(
    project_root: Path, *, candidate_member_id: str, endpoint: str,
    expires_at: str, actor_id: str | None = None,
) -> dict[str, Any]:
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be enabled before creating invites")
    candidate_member_id = _validate_id(candidate_member_id, "candidate_member_id")
    expiry = _parse_timestamp(expires_at)
    if expiry <= dt.datetime.now(dt.timezone.utc):
        raise ValueError("invite expiry must be in the future")
    endpoint = _validate_endpoint(endpoint, allow_lan=bool(config["allow_lan_bind"]))
    with _STATE_LOCK:
        state = _read_json(_coordinator_path(project_root))
        actor = actor_id or config["member_id"]
        member = state.get("members", {}).get(actor)
        if not isinstance(member, Mapping) or "admin" not in member.get("capabilities", []):
            raise ValueError("creating an invite requires Admin capability")
        invite_id = f"invite-{secrets.token_hex(12)}"
        invite_secret = secrets.token_urlsafe(32)
        state["invites"][invite_id] = {
            "candidate_member_id": candidate_member_id, "secret_hash": _hash(invite_secret),
            "expires_at": expires_at, "created_by": actor, "status": "open",
        }
        state["updated_at"] = _timestamp()
        _atomic_json(_coordinator_path(project_root), state)
    public = {
        "schema_version": 1, "contract_type": "manual-team-invite", "endpoint": endpoint,
        "project_fingerprint": config["project_fingerprint"], "invite_id": invite_id,
        "candidate_member_id": candidate_member_id, "invite_secret": invite_secret,
        "expires_at": expires_at, "discovery": "unsupported-next-phase",
    }
    encoded = base64.urlsafe_b64encode(_json_bytes(public)).decode("ascii").rstrip("=")
    return {"invite": encoded, "invite_id": invite_id, "discovery": "unsupported-next-phase"}


def _decode_invite(encoded: str) -> dict[str, Any]:
    try:
        padding = "=" * (-len(encoded) % 4)
        value = json.loads(base64.urlsafe_b64decode(encoded + padding).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("manual Team invite is malformed") from exc
    expected = {
        "schema_version", "contract_type", "endpoint", "project_fingerprint", "invite_id",
        "candidate_member_id", "invite_secret", "expires_at", "discovery",
    }
    if not isinstance(value, dict) or set(value) != expected or value.get("contract_type") != "manual-team-invite":
        raise ValueError("manual Team invite has an invalid contract")
    _parse_timestamp(value["expires_at"])
    return value


def request_join(project_root: Path, *, invite: str) -> dict[str, Any]:
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be enabled before joining")
    value = _decode_invite(invite)
    if not hmac.compare_digest(value["project_fingerprint"], config["project_fingerprint"]):
        raise ValueError("invite project identity does not match this checkout")
    if value["candidate_member_id"] != config["member_id"]:
        raise ValueError("invite member identity does not match the local member")
    result = _http_json(
        value["endpoint"], "/v1/join/request", method="POST",
        payload={
            "project_fingerprint": config["project_fingerprint"], "invite_id": value["invite_id"],
            "invite_secret": value["invite_secret"], "member_id": config["member_id"],
            "device_id": config["device_id"], "host_id": config["host_id"],
        }, allow_lan=bool(config["allow_lan_bind"]),
    )
    pending = {
        "schema_version": 1, "endpoint": value["endpoint"], "request_id": result["request_id"],
        "join_claim": result["join_claim"], "member_id": config["member_id"],
    }
    _atomic_json(team_private_dir(project_root) / "pending-join.json", pending)
    return {"request_id": result["request_id"], "status": "pending-host-confirmation", "network_performed": True}


def confirm_join(project_root: Path, *, request_id: str, actor_id: str | None = None) -> dict[str, Any]:
    config = load_team_config(project_root)
    with _STATE_LOCK:
        state = _read_json(_coordinator_path(project_root))
        actor = actor_id or config.get("member_id")
        member = state.get("members", {}).get(actor)
        if not isinstance(member, Mapping) or "admin" not in member.get("capabilities", []):
            raise ValueError("confirming a join requires Host-local Admin capability")
        request = state.get("join_requests", {}).get(request_id)
        if not isinstance(request, dict) or request.get("status") != "pending":
            raise ValueError("join request is not pending")
        joined = bootstrap_maintainer(request["member_id"])
        joined["capabilities"] = []
        joined["audit"] = []
        credential_token = secrets.token_urlsafe(32)
        state["members"][request["member_id"]] = joined
        state["credentials"][_hash(credential_token)] = {"member_id": request["member_id"], "credential_epoch": 1}
        state["active_hosts"][request["member_id"]] = {
            "host_id": request["host_id"], "device_id": request["device_id"], "switched_at": _timestamp(),
        }
        request.update({"status": "confirmed", "confirmed_by": actor, "credential_token": credential_token})
        state["updated_at"] = _timestamp()
        _atomic_json(_coordinator_path(project_root), state)
    return {"request_id": request_id, "status": "confirmed", "execution_performed": False}


def finalize_join(project_root: Path) -> dict[str, Any]:
    config = load_team_config(project_root)
    pending_path = team_private_dir(project_root) / "pending-join.json"
    pending = _read_json(pending_path)
    result = _http_json(
        pending["endpoint"], "/v1/join/finalize", method="POST",
        payload={"request_id": pending["request_id"], "join_claim": pending["join_claim"]},
        allow_lan=bool(config["allow_lan_bind"]),
    )
    _atomic_json(_credential_path(project_root), {
        "schema_version": 1, "member_id": config["member_id"],
        "credential_epoch": result["credential_epoch"], "token": result["credential_token"],
    })
    local_state = _read_json(_coordinator_path(project_root), required=False)
    if local_state:
        local_state.setdefault("members", {})[config["member_id"]] = result["member"]
        _atomic_json(_coordinator_path(project_root), local_state)
    pending_path.unlink(missing_ok=True)
    return {"member_id": config["member_id"], "status": "joined", "network_performed": True}


def change_member_capability(
    project_root: Path, *, member_id: str, action: str, capability: str,
    actor_id: str | None = None, occurred_at: str | None = None,
) -> dict[str, Any]:
    config = load_team_config(project_root)
    with _STATE_LOCK:
        state = _read_json(_coordinator_path(project_root))
        actor = actor_id or config.get("member_id")
        actor_member = state.get("members", {}).get(actor)
        if not isinstance(actor_member, Mapping) or "admin" not in actor_member.get("capabilities", []):
            raise ValueError("capability changes require Host-local Admin capability")
        target = state.get("members", {}).get(member_id)
        if not isinstance(target, Mapping):
            raise ValueError("unknown Team member")
        updated = apply_capability_change(
            target, actor_id=actor, action=action, capability=capability, occurred_at=_timestamp(occurred_at),
        )
        state["members"][member_id] = updated
        state["updated_at"] = _timestamp(occurred_at)
        _atomic_json(_coordinator_path(project_root), state)
    return {"member": updated, "old_credentials_revoked": True, "execution_performed": False}


def _authenticate(state: Mapping[str, Any], authorization: str | None) -> tuple[str, dict[str, Any]]:
    if not authorization or not authorization.startswith("Bearer "):
        raise PermissionError("project membership credential required")
    token = authorization[7:]
    credential = state.get("credentials", {}).get(_hash(token))
    if not isinstance(credential, Mapping):
        raise PermissionError("invalid project membership credential")
    member = state.get("members", {}).get(credential.get("member_id"))
    if (
        not isinstance(member, Mapping) or member.get("status") != "active"
        or member.get("credential_state") != "active"
        or member.get("credential_epoch") != credential.get("credential_epoch")
    ):
        raise PermissionError("project membership credential is revoked or stale")
    return str(member["member_id"]), dict(member)


def accept_envelope(state: dict[str, Any], envelope: Mapping[str, Any], *, raw_size: int | None = None) -> dict[str, Any]:
    validate_metadata_envelope(envelope, raw_size=raw_size)
    if not hmac.compare_digest(str(state["project_fingerprint"]), str(envelope["project_fingerprint"])):
        raise ValueError("Team envelope project identity mismatch")
    member_id = envelope["member_id"]
    if member_id not in state.get("members", {}):
        raise PermissionError("non-member cannot publish Team state")
    member = state["members"][member_id]
    if (
        envelope["member"].get("status") != member.get("status")
        or sorted(envelope["member"].get("capabilities", []))
        != sorted(member.get("capabilities", []))
    ):
        raise ValueError("Team envelope member capability metadata is stale or forged")
    active = state.get("active_hosts", {}).get(member_id)
    if not isinstance(active, Mapping) or active.get("host_id") != envelope["host_id"] or active.get("device_id") != envelope["device_id"]:
        raise ValueError("envelope does not come from the member's manually selected active Host")
    key = f"{member_id}:{envelope['workstream_id']}"
    previous = state.get("snapshots", {}).get(key)
    if isinstance(previous, Mapping) and int(envelope["revision"]) <= int(previous.get("revision", 0)):
        raise ValueError("Team envelope revision rollback or duplicate rejected")
    state.setdefault("snapshots", {})[key] = dict(envelope)
    state["updated_at"] = _timestamp()
    return {"accepted": True, "revision": envelope["revision"]}


def switch_coordinator_member_host(
    state: dict[str, Any], *, member_id: str, host_id: str, device_id: str, switched_at: str | None = None,
) -> dict[str, Any]:
    if member_id not in state.get("members", {}):
        raise ValueError("unknown Team member")
    _validate_id(host_id, "host_id")
    _validate_id(device_id, "device_id")
    state.setdefault("active_hosts", {})[member_id] = {
        "host_id": host_id, "device_id": device_id, "switched_at": _timestamp(switched_at),
    }
    state["updated_at"] = _timestamp(switched_at)
    return dict(state["active_hosts"][member_id])


def aggregate_projection(state: Mapping[str, Any], *, now: str | None = None) -> dict[str, Any]:
    current = _parse_timestamp(_timestamp(now))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for snapshot in state.get("snapshots", {}).values():
        if not isinstance(snapshot, Mapping):
            continue
        last_seen = _parse_timestamp(str(snapshot["last_seen"]))
        age = max(0.0, (current - last_seen).total_seconds())
        sharing = snapshot["sharing_state"]
        heartbeat = snapshot["heartbeat"]
        if sharing == "off":
            presence = "unavailable"
        elif sharing == "offline":
            presence = "offline"
        elif age > int(snapshot["ttl_seconds"]):
            presence = "stale-unknown"
        elif heartbeat["enabled"] and age <= max(5, int(heartbeat["interval_seconds"]) * 2):
            presence = "online"
        else:
            presence = "unknown"
        workstream = {
            "workstream_id": snapshot["workstream_id"], "revision": snapshot["revision"],
            "host": {"host_id": snapshot["host_id"], "device_id": snapshot["device_id"]},
            "presence": presence, "snapshot_age_seconds": int(age),
            "reported_workstream": dict(snapshot["workstream"]),
            "git": dict(snapshot["git"]), "scope": dict(snapshot["scope"]),
            "finding": dict(snapshot["finding"]), "validation": dict(snapshot["validation"]),
            "review": dict(snapshot["review"]), "last_seen": snapshot["last_seen"],
            "fact_scope": "Local-only", "semantic_without_code": "Unknown",
        }
        grouped.setdefault(str(snapshot["member_id"]), []).append(workstream)
    members: list[dict[str, Any]] = []
    for member_id, member in sorted(state.get("members", {}).items()):
        if not isinstance(member, Mapping):
            continue
        members.append({
            "member_id": member_id, "status": member.get("status"),
            "capabilities": list(member.get("capabilities", [])),
            "active_host": dict(state.get("active_hosts", {}).get(member_id, {})),
            "workstreams": sorted(grouped.get(member_id, []), key=lambda item: item["workstream_id"]),
        })
    return {
        "schema_version": 1, "contract_type": "team-read-only-projection",
        "project_fingerprint": state["project_fingerprint"],
        "coordinator": {"host_id": state["coordinator_host_id"], "topology": "single-active-manual-no-election"},
        "aggregation": "member-workstream", "members": members, "generated_at": _timestamp(now),
        "authority": "derived-read-only", "execution_capability": False,
    }


def create_request_record(
    state: dict[str, Any], *, requester_id: str, target_member_id: str, workstream_id: str,
    request_kind: str, summary: str, created_at: str | None = None,
) -> dict[str, Any]:
    if request_kind not in REQUEST_KINDS:
        raise ValueError("unsupported Team request kind")
    if target_member_id not in state.get("members", {}):
        raise ValueError("request target must be an active project member")
    if not summary or len(summary.encode("utf-8")) > 1024:
        raise ValueError("request summary must be 1-1024 UTF-8 bytes")
    required = REQUEST_CAPABILITIES.get(request_kind)
    requester = state["members"][requester_id]
    if required and required not in requester.get("capabilities", []):
        raise PermissionError(f"Team request requires {required} capability")
    request_id = f"request-{secrets.token_hex(12)}"
    record = {
        "schema_version": 1, "contract_type": "team-action-request", "request_id": request_id,
        "requester_id": requester_id, "target_member_id": target_member_id,
        "workstream_id": _validate_id(workstream_id, "workstream_id"), "request_kind": request_kind,
        "summary": summary, "status": "pending-local-confirmation", "created_at": _timestamp(created_at),
        "decided_at": None, "decision_reason": None, "execution_performed": False,
    }
    state.setdefault("requests", {})[request_id] = record
    state["updated_at"] = _timestamp(created_at)
    return record


def record_local_request_decision(
    project_root: Path, *, request_record: Mapping[str, Any], decision: str, reason: str,
    decided_at: str | None = None,
) -> dict[str, Any]:
    config = load_team_config(project_root)
    if request_record.get("target_member_id") != config.get("member_id"):
        raise ValueError("only the target member can decide a Team request locally")
    if decision not in {"accept", "reject"} or not reason:
        raise ValueError("local request decision requires accept/reject and a reason")
    receipt = {
        "schema_version": 1, "contract_type": "team-local-request-decision",
        "request_id": request_record["request_id"], "member_id": config["member_id"],
        "decision": decision, "reason": reason, "decided_at": _timestamp(decided_at),
        "execution_performed": False,
    }
    path = team_private_dir(project_root) / "inbox" / f"{request_record['request_id']}.json"
    _atomic_json(path, receipt)
    return receipt


def _safe_public_state(state: Mapping[str, Any]) -> dict[str, Any]:
    return aggregate_projection(state)


class _CoordinatorServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], project_root: Path, control_token: str):
        self.project_root = Path(project_root)
        self.control_token_hash = _hash(control_token)
        super().__init__(address, _CoordinatorHandler)

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        with _STATE_LOCK:
            super().process_request_thread(request, client_address)


class _CoordinatorHandler(BaseHTTPRequestHandler):
    server: _CoordinatorServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send(self, status: int, payload: Mapping[str, Any]) -> None:
        raw = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self, limit: int = TEAM_ENVELOPE_MAX_BYTES) -> tuple[dict[str, Any], int]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length <= 0 or length > limit:
            raise ValueError("request payload is empty or exceeds the bounded metadata limit")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value, len(raw)

    def _state(self) -> dict[str, Any]:
        config = load_team_config(self.server.project_root)
        if not config.get("enabled"):
            raise PermissionError("Team Mode is disabled")
        return _read_json(_coordinator_path(self.server.project_root))

    def _save(self, state: Mapping[str, Any]) -> None:
        _atomic_json(_coordinator_path(self.server.project_root), state)

    def do_GET(self) -> None:  # noqa: N802
        try:
            state = self._state()
            member_id, _member = _authenticate(state, self.headers.get("Authorization"))
            if self.path == "/v1/projection":
                self._send(HTTPStatus.OK, _safe_public_state(state))
                return
            if self.path == "/v1/requests":
                records = [
                    dict(item) for item in state.get("requests", {}).values()
                    if item.get("target_member_id") == member_id
                ]
                self._send(HTTPStatus.OK, {"requests": records, "execution_capability": False})
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except PermissionError as exc:
            self._send(HTTPStatus.FORBIDDEN, {"error": str(exc)})
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/v1/runtime/shutdown":
                body, _ = self._body(TEAM_REQUEST_MAX_BYTES)
                if not hmac.compare_digest(_hash(str(body.get("control"))), self.server.control_token_hash):
                    raise PermissionError("invalid Host-local runtime control")
                self._send(HTTPStatus.OK, {"stopping": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            state = self._state()
            if self.path == "/v1/join/request":
                body, _ = self._body(TEAM_REQUEST_MAX_BYTES)
                expected = {"project_fingerprint", "invite_id", "invite_secret", "member_id", "device_id", "host_id"}
                _exact_keys(body, expected, "join request")
                if not hmac.compare_digest(str(body["project_fingerprint"]), str(state["project_fingerprint"])):
                    raise PermissionError("project identity verification failed")
                invite = state.get("invites", {}).get(body["invite_id"])
                if (
                    not isinstance(invite, dict) or invite.get("status") != "open"
                    or invite.get("candidate_member_id") != body["member_id"]
                    or not hmac.compare_digest(invite.get("secret_hash", ""), _hash(str(body["invite_secret"])))
                    or _parse_timestamp(invite["expires_at"]) <= dt.datetime.now(dt.timezone.utc)
                ):
                    raise PermissionError("invite is invalid, expired, or for another member")
                request_id = f"join-{secrets.token_hex(12)}"
                claim = secrets.token_urlsafe(32)
                state["join_requests"][request_id] = {
                    "member_id": body["member_id"], "device_id": body["device_id"], "host_id": body["host_id"],
                    "invite_id": body["invite_id"], "join_claim_hash": _hash(claim), "status": "pending",
                    "requested_at": _timestamp(),
                }
                invite["status"] = "pending-confirmation"
                self._save(state)
                self._send(HTTPStatus.ACCEPTED, {"request_id": request_id, "join_claim": claim})
                return
            if self.path == "/v1/join/finalize":
                body, _ = self._body(TEAM_REQUEST_MAX_BYTES)
                _exact_keys(body, {"request_id", "join_claim"}, "join finalize")
                pending = state.get("join_requests", {}).get(body["request_id"])
                if (
                    not isinstance(pending, dict) or pending.get("status") != "confirmed"
                    or not hmac.compare_digest(pending.get("join_claim_hash", ""), _hash(str(body["join_claim"])))
                ):
                    raise PermissionError("join is not Host-confirmed")
                response = {
                    "credential_epoch": 1, "credential_token": pending.pop("credential_token"),
                    "member": state["members"][pending["member_id"]],
                }
                pending["status"] = "finalized"
                state["invites"][pending["invite_id"]]["status"] = "consumed"
                self._save(state)
                self._send(HTTPStatus.OK, response)
                return
            member_id, member = _authenticate(state, self.headers.get("Authorization"))
            body, raw_size = self._body()
            if self.path == "/v1/sync":
                if body.get("member_id") != member_id:
                    raise PermissionError("members may publish only their own Team state")
                result = accept_envelope(state, body, raw_size=raw_size)
                self._save(state)
                self._send(HTTPStatus.OK, result)
                return
            if self.path == "/v1/host/switch":
                _exact_keys(body, {"host_id", "device_id"}, "Host switch")
                result = switch_coordinator_member_host(
                    state, member_id=member_id, host_id=body["host_id"], device_id=body["device_id"],
                )
                self._save(state)
                self._send(HTTPStatus.OK, {"active_host": result, "automatic_election": False})
                return
            if self.path == "/v1/requests":
                _exact_keys(body, {"target_member_id", "workstream_id", "request_kind", "summary"}, "Team request")
                record = create_request_record(state, requester_id=member_id, **body)
                self._save(state)
                self._send(HTTPStatus.ACCEPTED, record)
                return
            if self.path.startswith("/v1/requests/") and self.path.endswith("/decision"):
                request_id = self.path.split("/")[3]
                _exact_keys(body, {"decision", "reason", "local_receipt"}, "request decision")
                record = state.get("requests", {}).get(request_id)
                if not isinstance(record, dict) or record.get("target_member_id") != member_id:
                    raise PermissionError("only the target member can decide this request")
                receipt = body["local_receipt"]
                if not isinstance(receipt, Mapping) or receipt.get("request_id") != request_id or receipt.get("execution_performed") is not False:
                    raise ValueError("a matching Host-local no-execution receipt is required")
                if body["decision"] not in {"accept", "reject"}:
                    raise ValueError("request decision must be accept or reject")
                record.update({
                    "status": "accepted-locally" if body["decision"] == "accept" else "rejected-locally",
                    "decided_at": receipt.get("decided_at"), "decision_reason": body["reason"],
                    "execution_performed": False,
                })
                self._save(state)
                self._send(HTTPStatus.OK, record)
                return
            raise ValueError("unsupported Coordinator operation")
        except PermissionError as exc:
            self._send(HTTPStatus.FORBIDDEN, {"error": str(exc)})
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})


def start_coordinator_server(
    project_root: Path, *, bind: str = "127.0.0.1", port: int = 0,
) -> tuple[_CoordinatorServer, dict[str, Any]]:
    """Create (but do not background) one explicitly enabled Coordinator server."""
    config = load_team_config(project_root)
    if not config.get("enabled"):
        raise ValueError("Team Mode must be explicitly enabled before Coordinator start")
    if _runtime_path(project_root).exists():
        raise ValueError("a Coordinator runtime is already registered; disable it before manual Host switch")
    try:
        address = ipaddress.ip_address(bind)
    except ValueError as exc:
        raise ValueError("Coordinator bind must be an IP literal") from exc
    if not address.is_loopback:
        if not config["allow_lan_bind"]:
            raise ValueError("LAN Coordinator bind requires explicit allow_lan_bind")
        if not (address.is_unspecified or address.is_private):
            raise ValueError("LAN Coordinator bind must use a private or wildcard address")
    control = secrets.token_urlsafe(32)
    server = _CoordinatorServer((bind, port), Path(project_root), control)
    host, bound_port = server.server_address[:2]
    endpoint_host = "127.0.0.1" if ipaddress.ip_address(host).is_unspecified else host
    runtime = {
        "schema_version": 1, "endpoint": f"http://{endpoint_host}:{bound_port}",
        "bind": bind, "port": bound_port, "pid": os.getpid(), "control": control,
        "coordinator_host_id": config["host_id"], "started_at": _timestamp(),
    }
    _atomic_json(_runtime_path(project_root), runtime)
    config["runtime_status"] = "team-runtime-active"
    config["network_features"] = ["listener", "coordinator", "member-authentication", "team-sync"]
    config["updated_at"] = _timestamp()
    _atomic_json(_team_config_path(project_root), config)
    return server, {key: value for key, value in runtime.items() if key != "control"}


def stop_owned_coordinator_server(
    project_root: Path, server: _CoordinatorServer, *, occurred_at: str | None = None,
) -> dict[str, Any]:
    """Stop the exact in-process Coordinator owned by a local UI/runtime.

    This does not disable Team Mode or touch Workstream facts.  Possession of
    the server object is the ownership boundary; no PID, URL, path, or shell
    parameter can be supplied by a remote caller.
    """

    root = Path(project_root).expanduser().absolute()
    if Path(server.project_root).resolve() != root.resolve():
        raise ValueError("Coordinator server is owned by another project root")
    server.shutdown()
    server.server_close()
    _runtime_path(root).unlink(missing_ok=True)
    config = load_team_config(root)
    if config.get("enabled"):
        config["runtime_status"] = "team-enabled-stopped"
        config["network_features"] = []
        config["updated_at"] = _timestamp(occurred_at)
        _validate_team_config(config)
        _atomic_json(_team_config_path(root), config)
    return {
        "runtime_status": "team-enabled-stopped",
        "network_features": [],
        "team_enabled": bool(config.get("enabled")),
        "local_facts_preserved": True,
    }


def disable_team(project_root: Path, *, occurred_at: str | None = None) -> dict[str, Any]:
    """Stop a known local runtime, then disable all Team network/sync features."""
    root = Path(project_root).expanduser().absolute()
    config = load_team_config(root)
    runtime = _read_json(_runtime_path(root), required=False)
    shutdown_requested = False
    if runtime:
        try:
            _http_json(
                runtime["endpoint"], "/v1/runtime/shutdown", method="POST",
                payload={"control": runtime["control"]}, allow_lan=bool(config.get("allow_lan_bind")),
            )
            shutdown_requested = True
        except ValueError:
            shutdown_requested = False
    if config.get("enabled"):
        config.update({
            "enabled": False, "runtime_status": "team-enabled-stopped", "network_features": [],
            "sharing_enabled": False, "updated_at": _timestamp(occurred_at),
        })
        _validate_team_config(config)
        _atomic_json(_team_config_path(root), config)
    _runtime_path(root).unlink(missing_ok=True)
    return {
        "enabled": False, "runtime_stopped": shutdown_requested or not runtime,
        "network_features": [], "local_facts_preserved": True,
    }


def fetch_projection(project_root: Path, *, endpoint: str) -> dict[str, Any]:
    config = load_team_config(project_root)
    credential = _load_local_credential(project_root)
    return _http_json(
        endpoint, "/v1/projection", credential=credential,
        allow_lan=bool(config.get("allow_lan_bind")),
    )


def fetch_requests(project_root: Path, *, endpoint: str) -> list[dict[str, Any]]:
    config = load_team_config(project_root)
    credential = _load_local_credential(project_root)
    result = _http_json(
        endpoint, "/v1/requests", credential=credential,
        allow_lan=bool(config.get("allow_lan_bind")),
    )
    return list(result.get("requests", []))


def send_request(
    project_root: Path, *, endpoint: str, target_member_id: str, workstream_id: str,
    request_kind: str, summary: str,
) -> dict[str, Any]:
    config = load_team_config(project_root)
    return _http_json(
        endpoint, "/v1/requests", method="POST",
        payload={
            "target_member_id": target_member_id, "workstream_id": workstream_id,
            "request_kind": request_kind, "summary": summary,
        }, credential=_load_local_credential(project_root), allow_lan=bool(config.get("allow_lan_bind")),
    )


def decide_request(
    project_root: Path, *, endpoint: str, request_record: Mapping[str, Any], decision: str, reason: str,
) -> dict[str, Any]:
    config = load_team_config(project_root)
    receipt = record_local_request_decision(
        project_root, request_record=request_record, decision=decision, reason=reason,
    )
    return _http_json(
        endpoint, f"/v1/requests/{request_record['request_id']}/decision", method="POST",
        payload={"decision": decision, "reason": reason, "local_receipt": receipt},
        credential=_load_local_credential(project_root), allow_lan=bool(config.get("allow_lan_bind")),
    )


def request_host_switch(project_root: Path, *, endpoint: str) -> dict[str, Any]:
    config = load_team_config(project_root)
    return _http_json(
        endpoint, "/v1/host/switch", method="POST",
        payload={"host_id": config["host_id"], "device_id": config["device_id"]},
        credential=_load_local_credential(project_root), allow_lan=bool(config.get("allow_lan_bind")),
    )
