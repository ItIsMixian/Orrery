"""Local-only workspace maintenance planning, authorization, and execution.

This module deliberately reuses the W3 workspace inventory and cleanup gate.
It never accepts an arbitrary command, URL, or execution path, and the only
implemented destructive action is removal of one already-registered linked
worktree after a fresh evidence check.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import queue as queue_module
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .collaboration import load_collaboration_config, resolve_integration_oid
from .review import _atomic_json, _common_git_dir, _git, _private_area, _read_regular_json, _repository_root
from .workspace_cleanup import compute_workspace_cleanup_eligibility, inventory_workspaces
from .maintenance_cache import (
    CACHE_DIRECTORY_NAME,
    CACHE_SCHEMA_VERSION,
    cache_status,
    fingerprint_registered_worktree,
    invalidate_cache_after_remove,
    policy_hash as maintenance_policy_hash,
    refresh_incremental_cache,
    registered_worktrees,
    select_registered_worktree,
    validate_cached_target,
)


MAINTENANCE_SCHEMA_VERSION = 2
MAINTENANCE_POLICY_VERSION = 1
MAINTENANCE_TRIGGERS = (
    "integration-event",
    "closure-event",
    "observatory-catch-up",
    "manual",
)
DEFAULT_POLICY: dict[str, Any] = {
    "policy_version": 1,
    "scan_on_observatory_start": True,
    "catch_up_after_hours": 24,
    "worktree_count_threshold": 8,
    "reclaim_threshold_mb": 500,
    "integrated_grace_days": 7,
    "local_branch_reminder_days": 30,
    "auto_remove_eligible_worktrees": False,
    "ignored_allowlist": ["**/__pycache__/**", "docs/_site/**"],
}
DEFAULT_HOST_PREFERENCES: dict[str, Any] = {
    "preference_version": 1,
    "catch_up_enabled": True,
    "notifications_enabled": True,
    "scheduler": {"status": "unsupported-phase-4", "installed": False},
}
_POLICY_FIELDS = set(DEFAULT_POLICY)
_HOST_FIELDS = set(DEFAULT_HOST_PREFERENCES)
_ITEM_ID = re.compile(r"^maintenance-item-[0-9a-f]{24}$")
_AUTH_ID = re.compile(r"^maintenance-authorization-[0-9a-f]{24}$")
_RECEIPT_ID = re.compile(r"^maintenance-receipt-[0-9a-f]{24}$")
_SCAN_ID = re.compile(r"^maintenance-scan-[0-9a-f]{24}$")
_WORKSPACE_ID = re.compile(r"^workspace-[0-9a-f]{24}$")
_EXPIRATION_CONDITIONS = [
    "workspace-path-or-identity-changed",
    "workspace-head-or-branch-changed",
    "integration-oid-changed",
    "closure-review-or-validation-changed",
    "dirty-untracked-or-ignored-set-changed",
    "eligibility-or-protection-changed",
]
_CONTRACT_FIELDS = {
    "maintenance-scan": {
        "schema_version", "contract_type", "scan_id", "repository_identity",
        "integration_ref", "integration_oid", "inventory_schema_version",
        "inventory_content_hash", "trigger_reason", "started_at", "finished_at",
        "status", "error_category", "counts", "writes_performed", "network_performed",
    },
    "maintenance-queue-item": {
        "schema_version", "contract_type", "item_id", "lifecycle", "action",
        "workspace_id", "workspace_path", "binding", "eligible", "reasons", "unknown",
        "created_at", "earliest_execute_at", "expiration_conditions", "authority",
    },
    "maintenance-authorization": {
        "schema_version", "contract_type", "authorization_id", "item_id", "action",
        "actor_id", "actor_kind", "authorized_at", "evidence_hash", "status",
        "execution_performed",
    },
    "maintenance-receipt": {
        "schema_version", "contract_type", "receipt_id", "authorization_id", "item_id",
        "action", "started_at", "finished_at", "outcome", "preflight", "postflight",
        "execution_performed", "branch_deleted", "remote_branch_deleted", "network_performed",
    },
}
_QUEUE_OPTIONAL_FIELDS = {"stale_reason", "stale_scan_id"}
_BINDING_FIELDS = {
    "workspace_id", "worktree_identity", "resolved_path", "git_dir", "head", "branch",
    "dirty_fingerprint", "workstream_id", "session_phase",
    "integration_oid", "inventory_content_hash", "closure_id", "review_package_id",
    "review_package_content_hash", "validation_refs_hash", "candidate_head",
    "tracked_changes", "untracked_paths", "ignored_paths_hash", "allowlisted_ignored_paths",
    "unique_commits", "evidence_hash",
}
_PATH_CONTEXT = threading.local()


def _timestamp(value: str | None = None) -> str:
    return value or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("maintenance timestamp must be RFC 3339") from exc
    if parsed.tzinfo is None:
        raise ValueError("maintenance timestamp must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _hash(domain: bytes, value: Mapping[str, Any] | Sequence[Any] | str) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(domain + encoded).hexdigest()


def _maintenance_root(project_root: Path) -> Path:
    context = getattr(_PATH_CONTEXT, "value", None)
    candidate = Path(project_root).expanduser().absolute()
    if context and os.path.normcase(os.path.abspath(candidate)) == context["root_key"]:
        return context["root"]
    return _repository_root(candidate)


def _maintenance_dir(project_root: Path, *parts: str, create: bool = False) -> Path:
    root = _maintenance_root(project_root)
    context = getattr(_PATH_CONTEXT, "value", None)
    common = context["common"] if context and root == context["root"] else _common_git_dir(root)
    path = common / "orrery" / "maintenance" / Path(*parts)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _manifest(project_root: Path) -> dict[str, Any]:
    path = _maintenance_root(project_root) / ".project-orrery.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read Project Orrery maintenance policy: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Project Orrery manifest must contain an object")
    return value


def validate_maintenance_policy(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("workspace maintenance policy must be an object")
    unknown = set(value) - _POLICY_FIELDS
    missing = _POLICY_FIELDS - set(value)
    if unknown:
        raise ValueError(f"unknown workspace maintenance policy field: {sorted(unknown)[0]}")
    if missing:
        raise ValueError(f"workspace maintenance policy is missing field: {sorted(missing)[0]}")
    result = dict(value)
    if result["policy_version"] != MAINTENANCE_POLICY_VERSION:
        raise ValueError("unsupported workspace maintenance policy version")
    for key in ("scan_on_observatory_start", "auto_remove_eligible_worktrees"):
        if not isinstance(result[key], bool):
            raise ValueError(f"workspace maintenance {key} must be boolean")
    if result["auto_remove_eligible_worktrees"]:
        raise ValueError("automatic worktree removal is unsupported in Phase 0-2")
    for key, minimum in (
        ("catch_up_after_hours", 1),
        ("worktree_count_threshold", 1),
        ("reclaim_threshold_mb", 1),
        ("integrated_grace_days", 0),
        ("local_branch_reminder_days", 1),
    ):
        item = result[key]
        if not isinstance(item, int) or isinstance(item, bool) or item < minimum:
            raise ValueError(f"workspace maintenance {key} must be an integer >= {minimum}")
    allowlist = result["ignored_allowlist"]
    if not isinstance(allowlist, list) or any(not isinstance(item, str) or not item.strip() for item in allowlist):
        raise ValueError("workspace maintenance ignored_allowlist must be a string array")
    if len(set(allowlist)) != len(allowlist):
        raise ValueError("workspace maintenance ignored_allowlist must be unique")
    return result


def validate_maintenance_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed on incompatible persisted maintenance contract fields."""
    if not isinstance(value, Mapping):
        raise ValueError("maintenance contract must be an object")
    contract_type = value.get("contract_type")
    expected = _CONTRACT_FIELDS.get(str(contract_type))
    if expected is None:
        raise ValueError("unsupported maintenance contract type")
    optional = _QUEUE_OPTIONAL_FIELDS if contract_type == "maintenance-queue-item" else set()
    unknown = set(value) - expected - optional
    missing = expected - set(value)
    if unknown or missing:
        field = sorted(unknown or missing)[0]
        raise ValueError(f"maintenance {contract_type} has incompatible field: {field}")
    if value.get("schema_version") != MAINTENANCE_SCHEMA_VERSION:
        raise ValueError("unsupported maintenance contract schema version")
    if contract_type == "maintenance-scan":
        if not _SCAN_ID.fullmatch(str(value.get("scan_id", ""))):
            raise ValueError("invalid maintenance scan ID")
        if value.get("writes_performed") is not False or value.get("network_performed") is not False:
            raise ValueError("maintenance scan must remain workspace-read-only and zero-network")
    elif contract_type == "maintenance-queue-item":
        if not _ITEM_ID.fullmatch(str(value.get("item_id", ""))) or value.get("action") != "remove-worktree":
            raise ValueError("invalid maintenance queue item")
        binding = value.get("binding")
        if not isinstance(binding, Mapping) or set(binding) != _BINDING_FIELDS:
            raise ValueError("maintenance queue binding fields are incompatible")
        if not re.fullmatch(r"[0-9a-f]{64}", str(binding.get("evidence_hash", ""))):
            raise ValueError("maintenance queue evidence hash is invalid")
    elif contract_type == "maintenance-authorization":
        if not _AUTH_ID.fullmatch(str(value.get("authorization_id", ""))) or value.get("action") != "remove-worktree":
            raise ValueError("invalid maintenance authorization")
        if value.get("actor_kind") != "human":
            raise ValueError("maintenance authorization must come from a local human")
    elif contract_type == "maintenance-receipt":
        if not _RECEIPT_ID.fullmatch(str(value.get("receipt_id", ""))) or value.get("action") != "remove-worktree":
            raise ValueError("invalid maintenance receipt")
        if value.get("branch_deleted") is not False or value.get("remote_branch_deleted") is not False or value.get("network_performed") is not False:
            raise ValueError("maintenance receipt crosses the Phase 2 action boundary")
    return dict(value)


def load_maintenance_policy(project_root: Path) -> dict[str, Any]:
    manifest = _manifest(project_root)
    collaboration = manifest.get("collaboration", {})
    if not isinstance(collaboration, Mapping):
        raise ValueError("project collaboration config must be an object")
    value = collaboration.get("workspace_maintenance")
    return validate_maintenance_policy(DEFAULT_POLICY if value is None else value)


def validate_host_preferences(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("maintenance host preferences must be an object")
    unknown = set(value) - _HOST_FIELDS
    missing = _HOST_FIELDS - set(value)
    if unknown or missing:
        field = sorted(unknown or missing)[0]
        raise ValueError(f"maintenance host preferences have incompatible field: {field}")
    if value.get("preference_version") != 1:
        raise ValueError("unsupported maintenance host preference version")
    if not isinstance(value.get("catch_up_enabled"), bool) or not isinstance(value.get("notifications_enabled"), bool):
        raise ValueError("maintenance host switches must be boolean")
    scheduler = value.get("scheduler")
    if scheduler != {"status": "unsupported-phase-4", "installed": False}:
        raise ValueError("OS scheduler installation is unsupported in Phase 0-2")
    return dict(value)


def load_host_preferences(project_root: Path) -> dict[str, Any]:
    path = _maintenance_dir(project_root) / "host.json"
    if not path.exists():
        return validate_host_preferences(DEFAULT_HOST_PREFERENCES)
    return validate_host_preferences(_read_regular_json(path, description="maintenance host preferences"))


def _repository_identity(root: Path) -> str:
    context = getattr(_PATH_CONTEXT, "value", None)
    common = context["common"] if context and Path(root) == context["root"] else _common_git_dir(root)
    return hashlib.sha256(os.path.normcase(os.path.realpath(common)).encode("utf-8")).hexdigest()


def _scan_path(root: Path, scan_id: str) -> Path:
    return _maintenance_dir(root, "runs", create=True) / f"{scan_id}.json"


def _last_run_path(root: Path) -> Path:
    return _maintenance_dir(root, create=True) / "last-run-v2.json"


def _legacy_last_run_path(root: Path) -> Path:
    """Return the pre-U2.1 evidence path without creating or rewriting it."""
    return _maintenance_dir(root) / "last-run.json"


def _read_optional(path: Path, description: str) -> dict[str, Any] | None:
    return _read_regular_json(path, description=description) if path.exists() else None


def _read_compatible_last_run(
    root: Path,
) -> tuple[dict[str, Any] | None, str | None, list[dict[str, Any]]]:
    """Read current evidence first and preserve incompatible history as warnings.

    The old ``last-run.json`` path is never migrated, deleted or overwritten.
    A new scan writes ``last-run-v2.json`` and keeps eligibility based only on
    current provider/cache evidence.
    """
    warnings: list[dict[str, Any]] = []
    candidates = (
        (_maintenance_dir(root) / "last-run-v2.json", "current-last-run", False),
        (_legacy_last_run_path(root), "legacy-last-run", True),
    )
    selected: dict[str, Any] | None = None
    selected_source: str | None = None
    for path, source, historical in candidates:
        if not path.exists():
            continue
        try:
            raw = _read_regular_json(path, description="maintenance last run")
            value = validate_maintenance_contract(raw)
        except ValueError as exc:
            warnings.append({
                "source": source,
                "error_type": type(exc).__name__,
                "message": str(exc),
                "evidence_scope": "historical" if historical else "current-file",
                "display_state": "historical-unknown",
                "affects_current_refresh": False,
                "affects_current_eligibility": False,
            })
            continue
        if selected is None:
            selected = value
            selected_source = source
    return selected, selected_source, warnings


def _bounded_call(call: Callable[..., Any], *arguments: Any, timeout_seconds: float) -> Any:
    result: queue_module.Queue[tuple[bool, Any]] = queue_module.Queue(maxsize=1)

    def invoke() -> None:
        try:
            result.put((True, call(*arguments)))
        except BaseException as error:
            result.put((False, error))

    worker = threading.Thread(target=invoke, daemon=True, name="orrery-maintenance-read")
    worker.start()
    worker.join(timeout_seconds)
    if worker.is_alive():
        raise TimeoutError("workspace maintenance read timed out")
    succeeded, value = result.get_nowait()
    if not succeeded:
        raise value
    return value


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _scan_contract(
    root: Path,
    *,
    reason: str,
    started_at: str,
    status: str,
    inventory: Mapping[str, Any] | None = None,
    finished_at: str | None = None,
    error_category: str | None = None,
    counts: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    config = load_collaboration_config(root)
    integration_oid = resolve_integration_oid(root, config.integration_ref)
    material = {"repository": _repository_identity(root), "reason": reason, "started_at": started_at}
    scan = {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "contract_type": "maintenance-scan",
        "scan_id": "maintenance-scan-" + _hash(b"project-orrery-maintenance-scan-v1\0", material)[:24],
        "repository_identity": material["repository"],
        "integration_ref": config.integration_ref,
        "integration_oid": integration_oid,
        "inventory_schema_version": int((inventory or {}).get("inventory_schema_version", 1)),
        "inventory_content_hash": str((inventory or {}).get("content_hash", "0" * 64)),
        "trigger_reason": reason,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "error_category": error_category,
        "counts": dict(counts or {}),
        "writes_performed": False,
        "network_performed": False,
    }
    if not _SCAN_ID.fullmatch(scan["scan_id"]):
        raise AssertionError("maintenance scan ID generation failed")
    return scan


def _queue_files(root: Path, *, directory: Path | None = None) -> list[Path]:
    directory = directory or _maintenance_dir(root, "queue")
    return sorted(directory.glob("maintenance-item-*.json")) if directory.is_dir() else []


def _binding(cleanup: Mapping[str, Any]) -> dict[str, Any]:
    workspace = cleanup["workspace"]
    git = workspace["git"]
    closure = workspace["closure"]
    closure_contract: Mapping[str, Any] = {}
    closure_record = cleanup.get("closure_record")
    if closure_record:
        closure_contract = _read_regular_json(Path(str(closure_record)), description="maintenance closure record")
    resolved_path = str(workspace["resolved_path"])
    git_dir = git.get("git_dir")
    worktree_identity = _hash(
        b"project-orrery-maintenance-worktree-identity-v1\0",
        {
            "repository_identity": _repository_identity(Path(str(workspace["path"]))),
            "resolved_path": os.path.normcase(os.path.realpath(resolved_path)),
            "git_dir": os.path.normcase(os.path.realpath(str(git_dir or ""))),
        },
    )
    dirty_fingerprint = _hash(
        b"project-orrery-maintenance-target-dirty-v1\0",
        {
            "tracked": list(git.get("tracked_changes", [])),
            "untracked": list(git.get("untracked_paths", [])),
            "ignored": list(git.get("ignored_paths", [])),
        },
    )
    material = {
        "workspace_id": workspace["workspace_id"],
        "worktree_identity": worktree_identity,
        "resolved_path": resolved_path,
        "git_dir": git_dir,
        "head": git.get("head"),
        "branch": git.get("branch"),
        "dirty_fingerprint": dirty_fingerprint,
        "workstream_id": cleanup.get("workstream_id"),
        "session_phase": workspace.get("session", {}).get("lifecycle_phase"),
        "integration_oid": cleanup.get("final_oid"),
        "inventory_content_hash": cleanup["inventory_content_hash"],
        "closure_id": closure.get("closure_id"),
        "review_package_id": closure.get("review_package_id"),
        "review_package_content_hash": closure_contract.get("review_package_content_hash"),
        "validation_refs_hash": _hash(
            b"project-orrery-maintenance-validation-refs-v1\0",
            list(closure_contract.get("validation_refs", [])),
        ),
        "candidate_head": cleanup.get("candidate_head"),
        "tracked_changes": list(git.get("tracked_changes", [])),
        "untracked_paths": list(git.get("untracked_paths", [])),
        "ignored_paths_hash": _hash(b"project-orrery-maintenance-ignored-v1\0", list(git.get("ignored_paths", []))),
        "allowlisted_ignored_paths": list(cleanup.get("allowlisted_ignored_paths", [])),
        "unique_commits": list(cleanup.get("unique_commits", [])),
    }
    # The W3 inventory hash includes estimates for every workspace.  Git-private
    # maintenance records live under the primary worktree's .git directory, so
    # persisting a scan can legitimately change that global size estimate.  Bind
    # authorization to the selected workspace facts while retaining the source
    # inventory hash as provenance, avoiding self-invalidating suggestions.
    evidence = {key: value for key, value in material.items() if key != "inventory_content_hash"}
    material["evidence_hash"] = _hash(b"project-orrery-maintenance-binding-v1\0", evidence)
    return material


def _closed_at(root: Path, cleanup: Mapping[str, Any]) -> dt.datetime:
    record = cleanup.get("closure_record")
    if not record:
        raise ValueError("maintenance suggestion requires a closure record")
    closure = _read_regular_json(Path(str(record)), description="maintenance closure record")
    return _parse_timestamp(str(closure["closed_at"]))


def _queue_item(root: Path, cleanup: Mapping[str, Any], *, now: dt.datetime, policy: Mapping[str, Any]) -> dict[str, Any] | None:
    action = cleanup["actions"]["remove-worktree"]
    if not cleanup.get("eligible") or not action.get("eligible"):
        return None
    earliest = _closed_at(root, cleanup) + dt.timedelta(days=int(policy["integrated_grace_days"]))
    if now < earliest:
        return None
    binding = _binding(cleanup)
    item_id = "maintenance-item-" + _hash(
        b"project-orrery-maintenance-item-v1\0",
        {"action": "remove-worktree", "evidence_hash": binding["evidence_hash"]},
    )[:24]
    return {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "contract_type": "maintenance-queue-item",
        "item_id": item_id,
        "lifecycle": "suggested",
        "action": "remove-worktree",
        "workspace_id": cleanup["workspace"]["workspace_id"],
        "workspace_path": cleanup["workspace"]["path"],
        "binding": binding,
        "eligible": True,
        "reasons": [],
        "unknown": list(cleanup.get("unknown", [])),
        "created_at": _timestamp(now.isoformat().replace("+00:00", "Z")),
        "earliest_execute_at": earliest.isoformat().replace("+00:00", "Z"),
        "expiration_conditions": list(_EXPIRATION_CONDITIONS),
        "authority": "git-private-suggestion",
    }


def _persist_queue(root: Path, suggestions: Sequence[Mapping[str, Any]], *, scan_id: str) -> tuple[list[dict[str, Any]], int]:
    directory = _maintenance_dir(root, "queue", create=True)
    current_ids = {str(item["item_id"]) for item in suggestions}
    stale_count = 0
    for path in _queue_files(root):
        try:
            existing = validate_maintenance_contract(_read_regular_json(path, description="maintenance queue item"))
        except ValueError:
            stale_count += 1
            continue
        if existing.get("item_id") not in current_ids and existing.get("lifecycle") in {"suggested", "authorized"}:
            existing["lifecycle"] = "stale"
            existing["stale_reason"] = "not-produced-by-latest-scan"
            existing["stale_scan_id"] = scan_id
            _atomic_json(path, existing)
            stale_count += 1
    written: list[dict[str, Any]] = []
    for suggestion in suggestions:
        path = directory / f"{suggestion['item_id']}.json"
        existing = _read_optional(path, "maintenance queue item")
        if existing is not None:
            existing = validate_maintenance_contract(existing)
        value = dict(suggestion)
        if existing and existing.get("binding", {}).get("evidence_hash") == value["binding"]["evidence_hash"]:
            value["created_at"] = existing.get("created_at", value["created_at"])
            if existing.get("lifecycle") in {"authorized", "executing", "verified", "failed"}:
                value["lifecycle"] = existing["lifecycle"]
        _atomic_json(path, value)
        written.append(value)
    return written, stale_count


def run_maintenance_scan(
    project_root: Path,
    *,
    reason: str = "manual",
    now: str | None = None,
    timeout_seconds: float = 120.0,
    debounce_seconds: float = 2.0,
    inventory_provider: Callable[..., dict[str, Any]] = inventory_workspaces,
    eligibility_provider: Callable[..., dict[str, Any]] = compute_workspace_cleanup_eligibility,
) -> dict[str, Any]:
    """Run one bounded scan and persist only Git-private maintenance metadata."""
    if reason not in MAINTENANCE_TRIGGERS:
        raise ValueError("unsupported maintenance scan trigger")
    if timeout_seconds <= 0:
        raise ValueError("maintenance scan timeout must be positive")
    root = _maintenance_root(project_root)
    policy = load_maintenance_policy(root)
    started = _timestamp(now)
    now_dt = _parse_timestamp(started)
    last_path = _last_run_path(root)
    last, _last_source, _historical_warnings = _read_compatible_last_run(root)
    if reason in {"integration-event", "closure-event"} and last and last.get("status") == "succeeded":
        finished = _parse_timestamp(str(last["finished_at"]))
        if (now_dt - finished).total_seconds() < debounce_seconds:
            scan = _scan_contract(root, reason=reason, started_at=started, status="debounced", finished_at=started)
            return {"scan": scan, "queue": list_maintenance_queue(root)["items"], "private_writes_performed": False}

    directory = _maintenance_dir(root, create=True)
    lock_path = directory / "scan.lock"
    descriptor: int | None = None
    for attempt in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            stale = False
            try:
                lock_value = json.loads(lock_path.read_text(encoding="utf-8"))
                stale = isinstance(lock_value, dict) and not _process_is_alive(int(lock_value.get("pid", 0)))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                stale = False
            if attempt == 0 and stale:
                lock_path.unlink(missing_ok=True)
                continue
            scan = _scan_contract(root, reason=reason, started_at=started, status="single-flight", finished_at=started)
            return {"scan": scan, "queue": list_maintenance_queue(root)["items"], "private_writes_performed": False}
    if descriptor is None:
        raise RuntimeError("maintenance scan lock acquisition failed")
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "started_at": started}, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if last and last.get("status") == "running":
            interrupted = dict(last)
            interrupted["status"] = "interrupted"
            interrupted["finished_at"] = started
            interrupted["error_category"] = "previous-process-interrupted"
            _atomic_json(_scan_path(root, str(interrupted["scan_id"])), interrupted)
            _atomic_json(last_path, interrupted)
            last = interrupted
        monotonic_start = time.monotonic()
        running = _scan_contract(root, reason=reason, started_at=started, status="running")
        _atomic_json(_scan_path(root, running["scan_id"]), running)
        _atomic_json(last_path, running)
    except BaseException:
        lock_path.unlink(missing_ok=True)
        raise
    try:
        suggestions: list[dict[str, Any]] = []
        protected: dict[str, int] = {}
        reclaim = 0
        cache_refresh: dict[str, Any] | None = None
        if inventory_provider is inventory_workspaces:
            config = load_collaboration_config(root)
            integration_oid = resolve_integration_oid(root, config.integration_ref)
            cache_refresh = _bounded_call(
                lambda: refresh_incremental_cache(
                    root,
                    integration_ref=config.integration_ref,
                    integration_oid=integration_oid,
                    policy=policy,
                    maintenance_schema_version=MAINTENANCE_SCHEMA_VERSION,
                    scanned_at=started,
                    eligibility_provider=eligibility_provider,
                ),
                timeout_seconds=timeout_seconds,
            )
            inventory = {
                "inventory_schema_version": 1,
                "content_hash": _hash(
                    b"project-orrery-maintenance-incremental-inventory-v1\0",
                    cache_refresh["projections"],
                ),
                "entries": [
                    value["cleanup"]["workspace"]
                    for value in cache_refresh["entries"]
                    if isinstance(value.get("cleanup"), Mapping)
                ],
            }
            for cache_entry in cache_refresh["entries"]:
                cleanup = cache_entry["cleanup"]
                item = _queue_item(root, cleanup, now=now_dt, policy=policy)
                if item is not None:
                    suggestions.append(item)
                    reclaim += int(cleanup.get("estimated_reclaim_bytes") or 0)
                else:
                    reasons = cleanup.get("reasons") or ["integrated-grace-period-active"]
                    for reason_value in reasons:
                        protected[str(reason_value)] = protected.get(str(reason_value), 0) + 1
            for error in cache_refresh["errors"]:
                protected["target-refresh-failed"] = protected.get("target-refresh-failed", 0) + 1
        else:
            inventory = _bounded_call(inventory_provider, root, timeout_seconds=timeout_seconds)
            if time.monotonic() - monotonic_start > timeout_seconds:
                raise TimeoutError("workspace maintenance inventory timed out")
            for entry in inventory["entries"]:
                if entry.get("recommended_action") != "evaluate-cleanup-eligibility":
                    for reason_value in entry.get("protections") or entry.get("unknown") or [entry.get("recommended_action", "unknown")]:
                        protected[str(reason_value)] = protected.get(str(reason_value), 0) + 1
                    continue
                remaining = timeout_seconds - (time.monotonic() - monotonic_start)
                if remaining <= 0:
                    raise TimeoutError("workspace maintenance eligibility scan timed out")
                cleanup = _bounded_call(
                    lambda selected: eligibility_provider(
                        root,
                        workspace_path=selected,
                        ignored_allowlist=policy["ignored_allowlist"],
                    ),
                    entry["path"],
                    timeout_seconds=remaining,
                )
                if time.monotonic() - monotonic_start > timeout_seconds:
                    raise TimeoutError("workspace maintenance eligibility scan timed out")
                item = _queue_item(root, cleanup, now=now_dt, policy=policy)
                if item is not None:
                    suggestions.append(item)
                    reclaim += int(cleanup.get("estimated_reclaim_bytes") or 0)
                else:
                    reasons = cleanup.get("reasons") or ["integrated-grace-period-active"]
                    for reason_value in reasons:
                        protected[str(reason_value)] = protected.get(str(reason_value), 0) + 1
        queue, stale_count = _persist_queue(root, suggestions, scan_id=running["scan_id"])
        counts = {
            "worktrees": int(cache_refresh["metrics"]["registered"]) if cache_refresh is not None else len(inventory["entries"]),
            "suggested": len(suggestions),
            "stale": stale_count,
            "unknown": sum(len(item.get("unknown", [])) for item in inventory["entries"]),
            "estimated_reclaim_bytes": reclaim,
        }
        if cache_refresh is not None:
            counts.update(
                {
                    "cache_hits": int(cache_refresh["metrics"]["cache_hits"]),
                    "target_provider_scans": int(cache_refresh["metrics"]["target_provider_scans"]),
                    "fingerprint_changes": int(cache_refresh["metrics"]["fingerprint_changes"]),
                    "removed_cache_entries": int(cache_refresh["metrics"]["removed"]),
                    "integration_only_updates": int(cache_refresh["metrics"]["integration_only_updates"]),
                    "duration_ms": cache_refresh["metrics"]["duration_ms"],
                }
            )
        finished = _timestamp(now if now is not None else None)
        scan = _scan_contract(
            root,
            reason=reason,
            started_at=started,
            status="succeeded",
            inventory=inventory,
            finished_at=finished,
            counts=counts,
        )
        scan["counts"]["protected_reason_groups"] = len(protected)
        _atomic_json(_scan_path(root, scan["scan_id"]), scan)
        _atomic_json(last_path, scan)
        _atomic_json(directory / "latest-protected.json", {"schema_version": 1, "scan_id": scan["scan_id"], "reasons": protected})
        return {
            "scan": scan,
            "queue": queue,
            "protected_reasons": protected,
            "policy": policy,
            "private_writes_performed": True,
            "workspace_writes_performed": False,
            "destructive_action_performed": False,
            "network_performed": False,
        }
    except Exception as exc:
        status = "timed-out" if isinstance(exc, TimeoutError) else "failed"
        failed = _scan_contract(
            root,
            reason=reason,
            started_at=started,
            status=status,
            finished_at=_timestamp(now if now is not None else None),
            error_category=type(exc).__name__,
        )
        _atomic_json(_scan_path(root, failed["scan_id"]), failed)
        _atomic_json(last_path, failed)
        return {
            "scan": failed,
            "queue": list_maintenance_queue(root)["items"],
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "private_writes_performed": True,
            "workspace_writes_performed": False,
            "destructive_action_performed": False,
            "network_performed": False,
        }
    finally:
        lock_path.unlink(missing_ok=True)


_BACKGROUND_LOCK = threading.RLock()
_BACKGROUND_REFRESH: dict[str, dict[str, Any]] = {}


def background_maintenance_status(project_root: Path) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    key = _repository_identity(root)
    with _BACKGROUND_LOCK:
        state = dict(_BACKGROUND_REFRESH.get(key, {}))
    if not state:
        state = {
            "status": "idle",
            "reason": None,
            "started_at": None,
            "finished_at": None,
            "error_type": None,
        }
    return {**state, "request_thread_blocked": False, "network_performed": False}


def request_background_maintenance_refresh(
    project_root: Path,
    *,
    reason: str = "manual",
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    """Schedule a single-flight refresh and return without waiting for its scan."""
    if reason not in MAINTENANCE_TRIGGERS:
        raise ValueError("unsupported maintenance scan trigger")
    root = _maintenance_root(project_root)
    key = _repository_identity(root)
    with _BACKGROUND_LOCK:
        current = _BACKGROUND_REFRESH.get(key)
        if current and current.get("status") in {"pending", "running"}:
            return {**current, "scheduled": False, "request_thread_blocked": False, "network_performed": False}
        state = {
            "status": "pending",
            "reason": reason,
            "started_at": _timestamp(),
            "finished_at": None,
            "error_type": None,
        }
        _BACKGROUND_REFRESH[key] = state

    def refresh() -> None:
        with _BACKGROUND_LOCK:
            _BACKGROUND_REFRESH[key] = {**state, "status": "running"}
        try:
            result = run_maintenance_scan(root, reason=reason, timeout_seconds=timeout_seconds)
            final = {
                **state,
                "status": "succeeded" if result["scan"]["status"] in {"succeeded", "debounced", "single-flight"} else result["scan"]["status"],
                "finished_at": _timestamp(),
                "scan_id": result["scan"].get("scan_id"),
                "error_type": (result.get("error") or {}).get("type"),
            }
        except BaseException as exc:
            final = {
                **state,
                "status": "failed",
                "finished_at": _timestamp(),
                "error_type": type(exc).__name__,
            }
        with _BACKGROUND_LOCK:
            _BACKGROUND_REFRESH[key] = final

    threading.Thread(
        target=refresh,
        daemon=True,
        name="orrery-maintenance-incremental-refresh",
    ).start()
    return {**state, "scheduled": True, "request_thread_blocked": False, "network_performed": False}


def request_background_catch_up(project_root: Path, *, now: str | None = None) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    policy = load_maintenance_policy(root)
    host = load_host_preferences(root)
    if not policy["scan_on_observatory_start"] or not host["catch_up_enabled"]:
        return {"status": "disabled", "scheduled": False, "request_thread_blocked": False, "network_performed": False}
    current = _parse_timestamp(_timestamp(now))
    last, _last_source, _historical_warnings = _read_compatible_last_run(root)
    if last and last.get("status") == "succeeded" and last.get("finished_at"):
        if current - _parse_timestamp(str(last["finished_at"])) < dt.timedelta(hours=int(policy["catch_up_after_hours"])):
            return {"status": "fresh", "scheduled": False, "last_run": last, "request_thread_blocked": False, "network_performed": False}
    return request_background_maintenance_refresh(root, reason="observatory-catch-up")


def catch_up_maintenance_scan(project_root: Path, *, now: str | None = None) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    policy = load_maintenance_policy(root)
    host = load_host_preferences(root)
    if not policy["scan_on_observatory_start"] or not host["catch_up_enabled"]:
        return {"status": "disabled", "scan_performed": False, "network_performed": False}
    current = _parse_timestamp(_timestamp(now))
    last, _last_source, _historical_warnings = _read_compatible_last_run(root)
    if last and last.get("status") == "succeeded" and last.get("finished_at"):
        age = current - _parse_timestamp(str(last["finished_at"]))
        if age < dt.timedelta(hours=int(policy["catch_up_after_hours"])):
            return {"status": "fresh", "scan_performed": False, "last_run": last, "network_performed": False}
    result = run_maintenance_scan(root, reason="observatory-catch-up", now=now)
    return {"status": result["scan"]["status"], "scan_performed": result["scan"]["status"] == "succeeded", **result}


def record_maintenance_event(project_root: Path, *, reason: str, occurred_at: str | None = None) -> dict[str, Any]:
    if reason not in {"integration-event", "closure-event"}:
        raise ValueError("maintenance event must be integration-event or closure-event")
    root = _maintenance_root(project_root)
    event = {"schema_version": 1, "reason": reason, "occurred_at": _timestamp(occurred_at)}
    event["event_id"] = "maintenance-event-" + _hash(b"project-orrery-maintenance-event-v1\0", event)[:24]
    _atomic_json(_maintenance_dir(root, "events", create=True) / f"{event['event_id']}.json", event)
    scan = run_maintenance_scan(root, reason=reason, now=occurred_at)
    return {"event": event, "scan": scan["scan"], "execution_performed": False, "network_performed": False}


def list_maintenance_queue(project_root: Path) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in _queue_files(root):
        try:
            items.append(validate_maintenance_contract(_read_regular_json(path, description="maintenance queue item")))
        except ValueError as exc:
            errors.append({"file": path.name, "type": type(exc).__name__, "state": "stale-unknown"})
    items.sort(key=lambda item: (str(item.get("lifecycle")), str(item.get("created_at")), str(item.get("item_id"))))
    return {"schema_version": 1, "items": items, "errors": errors, "writes_performed": False, "network_performed": False}


def _safe_queue_value(path: Path) -> dict[str, Any] | None:
    try:
        return validate_maintenance_contract(_read_regular_json(path, description="maintenance queue item"))
    except ValueError:
        return None


def inspect_maintenance_item(project_root: Path, item_id: str) -> dict[str, Any]:
    if not _ITEM_ID.fullmatch(item_id):
        raise ValueError("invalid maintenance item ID")
    path = _maintenance_dir(project_root, "queue") / f"{item_id}.json"
    item = validate_maintenance_contract(_read_regular_json(path, description="maintenance queue item"))
    if item.get("item_id") != item_id:
        raise ValueError("maintenance queue item ID does not match its file")
    return item


def quick_remove_preflight(
    project_root: Path,
    *,
    target_id: str,
    inspected_at: str | None = None,
) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    previous_context = getattr(_PATH_CONTEXT, "value", None)
    _PATH_CONTEXT.value = {
        "root": root,
        "root_key": os.path.normcase(os.path.abspath(root)),
        "common": _common_git_dir(root),
    }
    try:
        return _quick_remove_preflight(root, target_id=target_id, inspected_at=inspected_at)
    finally:
        if previous_context is None:
            delattr(_PATH_CONTEXT, "value")
        else:
            _PATH_CONTEXT.value = previous_context


def _quick_remove_preflight(
    project_root: Path,
    *,
    target_id: str,
    inspected_at: str | None = None,
) -> dict[str, Any]:
    """Refresh one registered target without scanning unrelated worktrees."""
    root = _maintenance_root(project_root)
    previous_item: dict[str, Any] | None = None
    if _ITEM_ID.fullmatch(target_id):
        previous_item = inspect_maintenance_item(root, target_id)
        workspace_id = str(previous_item["workspace_id"])
    elif _WORKSPACE_ID.fullmatch(target_id):
        workspace_id = target_id
    else:
        raise ValueError("Quick Remove requires a versioned item or registered workspace ID")
    policy = load_maintenance_policy(root)
    config = load_collaboration_config(root)
    integration_oid = resolve_integration_oid(root, config.integration_ref)
    timestamp = _timestamp(inspected_at)
    refreshed = refresh_incremental_cache(
        root,
        integration_ref=config.integration_ref,
        integration_oid=integration_oid,
        policy=policy,
        maintenance_schema_version=MAINTENANCE_SCHEMA_VERSION,
        scanned_at=timestamp,
        eligibility_provider=compute_workspace_cleanup_eligibility,
        target_workspace_id=workspace_id,
    )
    if len(refreshed["entries"]) != 1:
        error = refreshed["errors"][0] if refreshed["errors"] else {"type": "Unknown", "message": "target refresh unavailable"}
        projection = next(
            (item for item in refreshed["projections"] if item.get("workspace_id") == workspace_id),
            {},
        )
        return {
            "status": "unknown",
            "target_id": target_id,
            "workspace_id": workspace_id,
            "registered_path": projection.get("registered_path"),
            "eligible": False,
            "reasons": ["target-refresh-failed"],
            "unknown": [str(error.get("type"))],
            "item": None,
            "cache": refreshed["projections"],
            "workspace_writes_performed": False,
            "network_performed": False,
        }
    cleanup = refreshed["entries"][0]["cleanup"]
    record = refreshed["entries"][0]
    item = _queue_item(root, cleanup, now=_parse_timestamp(timestamp), policy=policy)
    if item is not None:
        item_path = _maintenance_dir(root, "queue", create=True) / f"{item['item_id']}.json"
        existing = _read_optional(item_path, "maintenance queue item")
        if existing is not None:
            existing = validate_maintenance_contract(existing)
            if existing.get("binding", {}).get("evidence_hash") == item["binding"]["evidence_hash"]:
                item["created_at"] = existing.get("created_at", item["created_at"])
        _atomic_json(item_path, item)
    if previous_item is not None and (item is None or previous_item["item_id"] != item["item_id"]):
        previous_item["lifecycle"] = "stale"
        previous_item["stale_reason"] = "quick-preflight-evidence-drifted"
        previous_item.pop("stale_scan_id", None)
        _atomic_json(_maintenance_dir(root, "queue") / f"{previous_item['item_id']}.json", previous_item)
    reasons = list(cleanup.get("reasons", []))
    if cleanup.get("eligible") and item is None:
        reasons.append("integrated-grace-period-active")
    return {
        "status": "eligible" if item is not None else "protected",
        "target_id": target_id,
        "workspace_id": workspace_id,
        "registered_path": record["registered_path"],
        "head": record.get("head"),
        "branch": record.get("branch"),
        "eligible": item is not None,
        "reasons": list(dict.fromkeys(reasons)),
        "unknown": list(cleanup.get("unknown", [])),
        "item": item,
        "cache_metrics": refreshed["metrics"],
        "workspace_writes_performed": False,
        "network_performed": False,
    }


def _fresh_target(root: Path, item: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = load_maintenance_policy(root)
    config = load_collaboration_config(root)
    validated = validate_cached_target(
        root,
        workspace_id=str(item["workspace_id"]),
        integration_ref=config.integration_ref,
        integration_oid=resolve_integration_oid(root, config.integration_ref),
        policy=policy,
        maintenance_schema_version=MAINTENANCE_SCHEMA_VERSION,
    )
    cleanup = validated["entry"].get("cleanup")
    if not isinstance(cleanup, Mapping):
        raise ValueError("cached target cleanup evidence is unavailable")
    return dict(cleanup), dict(validated["record"])


def authorize_maintenance_item(
    project_root: Path,
    *,
    item_id: str,
    action: str,
    actor_id: str,
    actor_kind: str = "human",
    authorized_at: str | None = None,
    _prevalidated_target: tuple[dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    if action != "remove-worktree":
        raise ValueError("Phase 2 only authorizes the remove-worktree action")
    if actor_kind != "human" or not actor_id.strip():
        raise ValueError("maintenance authorization requires a local human actor")
    item = inspect_maintenance_item(root, item_id)
    if item.get("lifecycle") != "suggested":
        raise ValueError("maintenance item is not awaiting local confirmation")
    try:
        fresh, _ = _prevalidated_target or _fresh_target(root, item)
    except ValueError:
        item["lifecycle"] = "stale"
        item["reasons"] = list(dict.fromkeys([*item.get("reasons", []), "authorization-evidence-drifted"]))
        _atomic_json(_maintenance_dir(root, "queue") / f"{item_id}.json", item)
        raise ValueError("maintenance item evidence drifted; rescan before authorization") from None
    fresh_binding = _binding(fresh)
    if not fresh.get("eligible") or not fresh["actions"]["remove-worktree"]["eligible"] or fresh_binding["evidence_hash"] != item["binding"]["evidence_hash"]:
        item["lifecycle"] = "stale"
        item["reasons"] = list(dict.fromkeys([*fresh.get("reasons", []), "authorization-evidence-drifted"]))
        _atomic_json(_maintenance_dir(root, "queue") / f"{item_id}.json", item)
        raise ValueError("maintenance item evidence drifted; rescan before authorization")
    timestamp = _timestamp(authorized_at)
    material = {"item_id": item_id, "action": action, "actor_id": actor_id.strip(), "authorized_at": timestamp, "evidence_hash": fresh_binding["evidence_hash"]}
    authorization = {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "contract_type": "maintenance-authorization",
        "authorization_id": "maintenance-authorization-" + _hash(b"project-orrery-maintenance-authorization-v1\0", material)[:24],
        "item_id": item_id,
        "action": action,
        "actor_id": actor_id.strip(),
        "actor_kind": "human",
        "authorized_at": timestamp,
        "evidence_hash": fresh_binding["evidence_hash"],
        "status": "authorized",
        "execution_performed": False,
    }
    _atomic_json(_maintenance_dir(root, "authorizations", create=True) / f"{authorization['authorization_id']}.json", authorization)
    item["lifecycle"] = "authorized"
    _atomic_json(_maintenance_dir(root, "queue") / f"{item_id}.json", item)
    return {"authorization": authorization, "item": item, "workspace_writes_performed": False, "network_performed": False}


def _authorization(root: Path, authorization_id: str) -> tuple[dict[str, Any], Path]:
    if not _AUTH_ID.fullmatch(authorization_id):
        raise ValueError("invalid maintenance authorization ID")
    path = _maintenance_dir(root, "authorizations") / f"{authorization_id}.json"
    value = validate_maintenance_contract(_read_regular_json(path, description="maintenance authorization"))
    if value.get("authorization_id") != authorization_id:
        raise ValueError("maintenance authorization ID does not match its file")
    return value, path


def _registered(root: Path, selected: Path) -> tuple[bool, bool]:
    raw = str(_git(root, "worktree", "list", "--porcelain").stdout)
    selected_norm = os.path.normcase(os.path.realpath(os.path.abspath(selected)))
    registered = False
    locked = False
    for block in raw.split("\n\n"):
        lines = block.splitlines()
        path_line = next((line for line in lines if line.startswith("worktree ")), None)
        if path_line and os.path.normcase(os.path.realpath(os.path.abspath(path_line[9:]))) == selected_norm:
            registered = True
            locked = any(line.startswith("locked") for line in lines)
    return registered, locked


def _receipt_path(root: Path, receipt_id: str) -> Path:
    return _maintenance_dir(root, "receipts", create=True) / f"{receipt_id}.json"


def _receipt(
    *,
    authorization: Mapping[str, Any],
    started_at: str,
    outcome: str,
    preflight: Mapping[str, Any],
    postflight: Mapping[str, Any],
    finished_at: str | None,
    execution_performed: bool,
) -> dict[str, Any]:
    material = {"authorization_id": authorization["authorization_id"], "started_at": started_at}
    return {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "contract_type": "maintenance-receipt",
        "receipt_id": "maintenance-receipt-" + _hash(b"project-orrery-maintenance-receipt-v1\0", material)[:24],
        "authorization_id": authorization["authorization_id"],
        "item_id": authorization["item_id"],
        "action": "remove-worktree",
        "started_at": started_at,
        "finished_at": finished_at,
        "outcome": outcome,
        "preflight": dict(preflight),
        "postflight": dict(postflight),
        "execution_performed": execution_performed,
        "branch_deleted": False,
        "remote_branch_deleted": False,
        "network_performed": False,
    }


def _run_worktree_remove(arguments: Sequence[str], *, timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout_seconds,
    )


def _private_tree_hash(path: Path) -> str:
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Git-private session archive source must be a real directory")
    material: list[dict[str, str]] = []
    for candidate in sorted(path.rglob("*"), key=lambda value: str(value).lower()):
        if candidate.is_symlink():
            raise ValueError("Git-private session archive cannot contain links")
        if not candidate.is_file():
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        material.append({"path": candidate.relative_to(path).as_posix(), "sha256": digest})
    if not material or not any(item["path"] == "worktree.json" for item in material):
        raise ValueError("Git-private Workstream session is unavailable for archival")
    return _hash(b"project-orrery-maintenance-session-archive-v1\0", material)


def _archive_target_session(
    root: Path,
    *,
    item: Mapping[str, Any],
    authorization_id: str,
) -> dict[str, Any]:
    git_dir = Path(str(item["binding"].get("git_dir") or ""))
    source = git_dir / "orrery"
    try:
        source.resolve(strict=True).relative_to(git_dir.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValueError("Git-private Workstream session archive path escaped") from exc
    source_hash = _private_tree_hash(source)
    parent = _maintenance_dir(root, "archives", str(item["workspace_id"]), create=True)
    destination = parent / authorization_id
    if destination.exists():
        archived_hash = _private_tree_hash(destination)
        if archived_hash != source_hash:
            raise ValueError("existing Git-private session archive hash does not match")
    else:
        shutil.copytree(source, destination, copy_function=shutil.copy2)
        archived_hash = _private_tree_hash(destination)
        if archived_hash != source_hash:
            raise ValueError("Git-private session archive verification failed")
    return {
        "source": str(source),
        "archive": str(destination),
        "sha256": source_hash,
        "verified": True,
    }


def execute_maintenance_authorization(
    project_root: Path,
    *,
    authorization_id: str,
    started_at: str | None = None,
    execution_timeout_seconds: float = 120.0,
    _prevalidated_target: tuple[dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    authorization, authorization_path = _authorization(root, authorization_id)
    if authorization.get("status") != "authorized" or authorization.get("action") != "remove-worktree":
        raise ValueError("maintenance authorization is not executable")
    item = inspect_maintenance_item(root, str(authorization["item_id"]))
    selected = Path(str(item["workspace_path"]))
    start = _timestamp(started_at)
    try:
        fresh, registered_record = _prevalidated_target or _fresh_target(root, item)
    except ValueError:
        try:
            registered_record = select_registered_worktree(root, str(item["workspace_id"]))
        except ValueError:
            registered_record = {}
        registered = bool(registered_record)
        locked = bool(registered_record.get("locked"))
        exact_registered_path = bool(
            registered
            and os.path.normcase(os.path.abspath(str(registered_record.get("path"))))
            == os.path.normcase(os.path.abspath(str(item["workspace_path"])))
        )
        authorization["status"] = "stale"
        item["lifecycle"] = "stale"
        preflight = {
            "evidence_hash": str(item.get("binding", {}).get("evidence_hash", "0" * 64)),
            "eligible": False,
            "registered": registered,
            "locked_or_process_use": locked,
            "path_exists": selected.exists(),
            "exact_registered_path": exact_registered_path,
            "branch": registered_record.get("branch", item.get("binding", {}).get("branch")),
            "head": registered_record.get("head", item.get("binding", {}).get("head")),
            "reasons": ["cached-target-evidence-drifted"],
        }
        receipt = _receipt(
            authorization=authorization,
            started_at=start,
            outcome="stale",
            preflight=preflight,
            postflight={},
            finished_at=start,
            execution_performed=False,
        )
        _atomic_json(authorization_path, authorization)
        _atomic_json(_maintenance_dir(root, "queue") / f"{item['item_id']}.json", item)
        _atomic_json(_receipt_path(root, receipt["receipt_id"]), receipt)
        return {
            "receipt": receipt,
            "authorization": authorization,
            "item": item,
            "destructive_action_performed": False,
            "network_performed": False,
        }
    binding = _binding(fresh)
    registered = True
    locked = bool(registered_record.get("locked"))
    exact_registered_path = (
        os.path.normcase(os.path.abspath(str(registered_record["path"])))
        == os.path.normcase(os.path.abspath(str(item["workspace_path"])))
    )
    drift = (
        not fresh.get("eligible")
        or not fresh["actions"]["remove-worktree"]["eligible"]
        or binding["evidence_hash"] != authorization["evidence_hash"]
        or binding["evidence_hash"] != item["binding"]["evidence_hash"]
        or not registered
        or locked
        or not exact_registered_path
        or os.path.normcase(os.path.realpath(root)) == os.path.normcase(os.path.realpath(selected))
    )
    preflight = {
        "evidence_hash": binding["evidence_hash"],
        "eligible": bool(fresh.get("eligible")),
        "registered": registered,
        "locked_or_process_use": locked,
        "path_exists": selected.exists(),
        "exact_registered_path": exact_registered_path,
        "branch": fresh["workspace"]["git"].get("branch"),
        "head": fresh["workspace"]["git"].get("head"),
        "reasons": list(fresh.get("reasons", [])),
    }
    if drift:
        authorization["status"] = "stale"
        item["lifecycle"] = "stale"
        receipt = _receipt(authorization=authorization, started_at=start, outcome="stale", preflight=preflight, postflight={}, finished_at=start, execution_performed=False)
        _atomic_json(authorization_path, authorization)
        _atomic_json(_maintenance_dir(root, "queue") / f"{item['item_id']}.json", item)
        _atomic_json(_receipt_path(root, receipt["receipt_id"]), receipt)
        return {"receipt": receipt, "authorization": authorization, "item": item, "destructive_action_performed": False}

    try:
        session_archive = _archive_target_session(
            root,
            item=item,
            authorization_id=authorization_id,
        )
    except (OSError, ValueError) as exc:
        authorization["status"] = "failed"
        item["lifecycle"] = "failed"
        preflight["session_archive"] = {"verified": False, "error": type(exc).__name__}
        receipt = _receipt(
            authorization=authorization,
            started_at=start,
            outcome="failed",
            preflight=preflight,
            postflight={},
            finished_at=start,
            execution_performed=False,
        )
        _atomic_json(authorization_path, authorization)
        _atomic_json(_maintenance_dir(root, "queue") / f"{item['item_id']}.json", item)
        _atomic_json(_receipt_path(root, receipt["receipt_id"]), receipt)
        return {
            "receipt": receipt,
            "authorization": authorization,
            "item": item,
            "destructive_action_performed": False,
            "network_performed": False,
        }
    preflight["session_archive"] = session_archive

    authorization["status"] = "executing"
    item["lifecycle"] = "executing"
    in_progress = _receipt(authorization=authorization, started_at=start, outcome="executing", preflight=preflight, postflight={}, finished_at=None, execution_performed=False)
    receipt_path = _receipt_path(root, in_progress["receipt_id"])
    _atomic_json(authorization_path, authorization)
    _atomic_json(_maintenance_dir(root, "queue") / f"{item['item_id']}.json", item)
    _atomic_json(receipt_path, in_progress)
    arguments = ["git", "-C", str(root), "worktree", "remove"]
    if fresh.get("allowlisted_ignored_paths"):
        arguments.append("--force")
    arguments.extend(["--", str(selected)])
    try:
        completed = _run_worktree_remove(arguments, timeout_seconds=execution_timeout_seconds)
    except BaseException as exc:
        interrupted = isinstance(exc, (KeyboardInterrupt, SystemExit))
        outcome = "interrupted" if interrupted else "unknown"
        authorization["status"] = outcome
        item["lifecycle"] = "failed"
        postflight = {
            "git_exit_code": None,
            "path_absent": not selected.exists(),
            "registry_absent": not _registered(root, selected)[0],
            "branch_retained": bool(
                fresh["workspace"]["git"].get("branch")
                and not _git(root, "show-ref", "--verify", str(fresh["workspace"]["git"].get("branch")), check=False).returncode
            ),
            "commit_retained": bool(
                fresh["workspace"]["git"].get("head")
                and not _git(root, "cat-file", "-e", f"{fresh['workspace']['git'].get('head')}^{{commit}}", check=False).returncode
            ),
            "stderr_category": "execution-interrupted" if interrupted else type(exc).__name__,
        }
        receipt = _receipt(
            authorization=authorization,
            started_at=start,
            outcome=outcome,
            preflight=preflight,
            postflight=postflight,
            finished_at=_timestamp(),
            execution_performed=False,
        )
        _atomic_json(authorization_path, authorization)
        _atomic_json(_maintenance_dir(root, "queue") / f"{item['item_id']}.json", item)
        _atomic_json(receipt_path, receipt)
        if interrupted:
            raise
        return {
            "receipt": receipt,
            "authorization": authorization,
            "item": item,
            "destructive_action_performed": False,
            "branch_deleted": False,
            "remote_branch_deleted": False,
            "network_performed": False,
        }
    registered_after, _ = _registered(root, selected)
    branch = fresh["workspace"]["git"].get("branch")
    head = fresh["workspace"]["git"].get("head")
    retained = _git(root, "rev-parse", "--verify", "--end-of-options", str(branch), check=False) if branch else None
    retained_oid = str(retained.stdout).strip().lower() if retained is not None and not retained.returncode else None
    branch_retained = bool(branch and retained_oid)
    commit_retained = bool(head and retained_oid == str(head).lower())
    postflight = {
        "git_exit_code": completed.returncode,
        "path_absent": not selected.exists(),
        "registry_absent": not registered_after,
        "branch_retained": branch_retained,
        "commit_retained": commit_retained,
        "stderr_category": "none" if completed.returncode == 0 else "git-worktree-remove-failed",
    }
    verified = completed.returncode == 0 and all((postflight["path_absent"], postflight["registry_absent"], branch_retained, commit_retained))
    outcome = "verified" if verified else "failed"
    authorization["status"] = outcome
    authorization["execution_performed"] = completed.returncode == 0
    item["lifecycle"] = outcome
    receipt = _receipt(
        authorization=authorization,
        started_at=start,
        outcome=outcome,
        preflight=preflight,
        postflight=postflight,
        finished_at=_timestamp(),
        execution_performed=completed.returncode == 0,
    )
    _atomic_json(authorization_path, authorization)
    _atomic_json(_maintenance_dir(root, "queue") / f"{item['item_id']}.json", item)
    _atomic_json(receipt_path, receipt)
    invalidation = None
    background = None
    if verified:
        context = getattr(_PATH_CONTEXT, "value", None)
        invalidation = invalidate_cache_after_remove(
            root,
            str(item["workspace_id"]),
            _directory=(context["common"] / "orrery" / "maintenance" / CACHE_DIRECTORY_NAME) if context else None,
            _root_is_resolved=bool(context),
        )
        background = request_background_maintenance_refresh(root, reason="manual")
    return {
        "receipt": receipt,
        "receipt_path": str(receipt_path),
        "authorization": authorization,
        "item": item,
        "destructive_action_performed": completed.returncode == 0,
        "branch_deleted": False,
        "remote_branch_deleted": False,
        "network_performed": False,
        "cache_invalidation": invalidation,
        "background_refresh": background,
    }


def execute_quick_remove_item(
    project_root: Path,
    *,
    item_id: str,
    actor_id: str,
    confirmed_at: str | None = None,
    execution_timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    """Authorize and remove one preflighted item with one immediate fresh evidence read."""
    root = _maintenance_root(project_root)
    previous_context = getattr(_PATH_CONTEXT, "value", None)
    _PATH_CONTEXT.value = {
        "root": root,
        "root_key": os.path.normcase(os.path.abspath(root)),
        "common": _common_git_dir(root),
    }
    try:
        item = inspect_maintenance_item(root, item_id)
        if item.get("lifecycle") != "suggested":
            raise ValueError("maintenance item is not awaiting local confirmation")
        prevalidated = _fresh_target(root, item)
        authorization = authorize_maintenance_item(
            root,
            item_id=item_id,
            action="remove-worktree",
            actor_id=actor_id,
            authorized_at=confirmed_at,
            _prevalidated_target=prevalidated,
        )["authorization"]
        return execute_maintenance_authorization(
            root,
            authorization_id=str(authorization["authorization_id"]),
            started_at=confirmed_at,
            execution_timeout_seconds=execution_timeout_seconds,
            _prevalidated_target=prevalidated,
        )
    finally:
        if previous_context is None:
            delattr(_PATH_CONTEXT, "value")
        else:
            _PATH_CONTEXT.value = previous_context


def read_maintenance_receipt(project_root: Path, receipt_id: str) -> dict[str, Any]:
    if not _RECEIPT_ID.fullmatch(receipt_id):
        raise ValueError("invalid maintenance receipt ID")
    value = validate_maintenance_contract(
        _read_regular_json(_maintenance_dir(project_root, "receipts") / f"{receipt_id}.json", description="maintenance receipt")
    )
    if value.get("receipt_id") != receipt_id:
        raise ValueError("maintenance receipt ID does not match its file")
    return value


def maintenance_status(project_root: Path) -> dict[str, Any]:
    root = _maintenance_root(project_root)
    common = _common_git_dir(root)
    directory = common / "orrery" / "maintenance"
    policy = load_maintenance_policy(root)
    contract_errors: list[dict[str, str]] = []
    last, last_run_source, last_run_warnings = _read_compatible_last_run(root)
    contract_errors.extend(last_run_warnings)
    protected = _read_optional(directory / "latest-protected.json", "maintenance protected summary")
    receipts_dir = directory / "receipts"
    def compatible_contracts(paths: Sequence[Path], description: str) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        for path in paths:
            try:
                values.append(validate_maintenance_contract(_read_regular_json(path, description=description)))
            except ValueError as exc:
                contract_errors.append({"source": path.name, "error_type": type(exc).__name__, "message": str(exc)})
        return values

    receipts = []
    if receipts_dir.is_dir():
        receipts = compatible_contracts(sorted(receipts_dir.glob("maintenance-receipt-*.json")), "maintenance receipt")
        receipts.sort(key=lambda value: (str(value.get("started_at")), str(value.get("receipt_id"))))
    authorizations_dir = directory / "authorizations"
    authorizations = []
    if authorizations_dir.is_dir():
        authorizations = compatible_contracts(
            sorted(authorizations_dir.glob("maintenance-authorization-*.json")), "maintenance authorization"
        )
        authorizations.sort(key=lambda value: (str(value.get("authorized_at")), str(value.get("authorization_id"))))
    counts = last.get("counts", {}) if isinstance(last, Mapping) and isinstance(last.get("counts"), Mapping) else {}
    threshold_reasons = []
    if int(counts.get("worktrees", 0)) >= int(policy["worktree_count_threshold"]):
        threshold_reasons.append("worktree-count-threshold-reached")
    if int(counts.get("estimated_reclaim_bytes", 0)) >= int(policy["reclaim_threshold_mb"]) * 1024 * 1024:
        threshold_reasons.append("reclaim-threshold-reached")
    current = dt.datetime.now(dt.timezone.utc)
    cached = cache_status(root, directory=directory / CACHE_DIRECTORY_NAME)
    host_path = directory / "host.json"
    host_preferences = (
        validate_host_preferences(_read_regular_json(host_path, description="maintenance host preferences"))
        if host_path.exists()
        else validate_host_preferences(DEFAULT_HOST_PREFERENCES)
    )
    background_key = hashlib.sha256(os.path.normcase(os.path.realpath(common)).encode("utf-8")).hexdigest()
    with _BACKGROUND_LOCK:
        background = dict(_BACKGROUND_REFRESH.get(background_key, {}))
    if not background:
        background = {"status": "idle", "reason": None, "started_at": None, "finished_at": None, "error_type": None}
    background.update({"request_thread_blocked": False, "network_performed": False})
    branch_reminders = []
    for receipt in receipts:
        if receipt.get("outcome") != "verified" or not receipt.get("preflight", {}).get("branch"):
            continue
        remind_at = _parse_timestamp(str(receipt["finished_at"])) + dt.timedelta(days=int(policy["local_branch_reminder_days"]))
        if current >= remind_at:
            branch_reminders.append(
                {
                    "branch": receipt["preflight"]["branch"],
                    "source_receipt_id": receipt["receipt_id"],
                    "remind_at": remind_at.isoformat().replace("+00:00", "Z"),
                    "action": "reminder-only",
                    "execution_performed": False,
                }
            )
    return {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "status": "ready",
        "policy": policy,
        "host_preferences": host_preferences,
        "last_run": last,
        "last_run_source": last_run_source,
        "historical_evidence_warnings": last_run_warnings,
        "queue": [
            value
            for path in _queue_files(root, directory=directory / "queue")
            for value in (
                _safe_queue_value(path),
            )
            if value is not None
        ],
        "authorizations": authorizations[-50:],
        "protected_reasons": (protected or {}).get("reasons", {}),
        "receipts": receipts[-20:],
        "scheduler": {"supported": False, "installed": False, "status": "unsupported-phase-4"},
        "attention_required": bool(threshold_reasons),
        "attention_reasons": threshold_reasons,
        "local_branch_reminders": branch_reminders,
        "remote_branch_status": "unobserved-zero-network",
        "cache": cached,
        "background_refresh": background,
        "contract_errors": contract_errors,
        "automatic_deletion": False,
        "workspace_writes_performed": False,
        "network_performed": False,
    }
