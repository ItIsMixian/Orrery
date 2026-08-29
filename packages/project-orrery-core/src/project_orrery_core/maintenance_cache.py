"""Git-private incremental cache for local workspace maintenance.

The cache is an acceleration layer only.  Every destructive decision is made
from a fresh target-scoped W3 cleanup evaluation, never from this projection.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from . import __version__ as CORE_TOOL_VERSION
from .review import _atomic_json, _git, _private_area, _read_regular_json, _repository_root


CACHE_SCHEMA_VERSION = 1
CACHE_DIRECTORY_NAME = "cache-v1"
CACHE_CONTRACT = "maintenance-cache-entry"
CACHE_SUMMARY_CONTRACT = "maintenance-cache-registry-summary"
_WORKSPACE_ID = re.compile(r"^workspace-[0-9a-f]{24}$")
_ENTRY_FIELDS = {
    "cache_schema_version", "contract_type", "repository_identity", "workspace_id",
    "worktree_identity", "registered_path", "resolved_path", "git_dir", "head", "branch",
    "fingerprint", "session_hash", "closure_hash", "review_hash", "integration_ref",
    "integration_oid", "policy_hash", "maintenance_schema_version", "cleanup_schema_version",
    "tool_version", "scanned_at", "refresh_reason", "integration_sensitive", "cleanup",
}
_SUMMARY_FIELDS = {
    "cache_schema_version", "contract_type", "repository_identity", "integration_ref",
    "integration_oid", "policy_hash", "maintenance_schema_version", "cleanup_schema_version",
    "tool_version", "generated_at", "registry_hash", "status", "entries", "metrics",
}


def _hash(domain: bytes, value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(domain + raw).hexdigest()


def policy_hash(policy: Mapping[str, Any]) -> str:
    return _hash(b"project-orrery-maintenance-cache-policy-v1\0", dict(policy))


def _common_and_repository_identity(root: Path) -> tuple[Path, str]:
    common = Path(str(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout).strip())
    identity = hashlib.sha256(os.path.normcase(os.path.realpath(common)).encode("utf-8")).hexdigest()
    return common, identity


def repository_identity(root: Path) -> str:
    return _common_and_repository_identity(root)[1]


def cache_root(project_root: Path, *, create: bool = False) -> Path:
    return _private_area(_repository_root(project_root), "maintenance", CACHE_DIRECTORY_NAME, create=create)


def _entry_path(root: Path, workspace_id: str) -> Path:
    return cache_root(root) / "entries" / f"{workspace_id}.json"


def _last_known_path(root: Path, workspace_id: str) -> Path:
    return cache_root(root) / "last-known" / f"{workspace_id}.json"


def _summary_path(root: Path) -> Path:
    return cache_root(root) / "registry-summary.json"


def _summary_backup_path(root: Path) -> Path:
    return cache_root(root) / "last-known-registry-summary.json"


def _workspace_id(path: Path) -> str:
    normalized = os.path.normcase(os.path.realpath(os.path.abspath(path)))
    return "workspace-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def registered_worktrees(project_root: Path, *, _root_is_resolved: bool = False) -> list[dict[str, Any]]:
    """Read only Git's bounded registry; paths are never caller supplied."""
    root = Path(project_root) if _root_is_resolved else _repository_root(project_root)
    raw = str(_git(root, "worktree", "list", "--porcelain").stdout)
    records: list[dict[str, Any]] = []
    for index, block in enumerate(value for value in raw.split("\n\n") if value.strip()):
        record: dict[str, Any] = {"is_primary": index == 0, "locked": False}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                path = Path(os.path.abspath(value))
                record.update(
                    path=str(path),
                    resolved_path=os.path.realpath(path),
                    workspace_id=_workspace_id(path),
                )
            elif key == "HEAD":
                record["head"] = value.lower()
            elif key == "branch":
                record["branch"] = value
            elif key == "locked":
                record["locked"] = True
                record["lock_reason"] = value or None
            elif key in {"detached", "prunable", "bare"}:
                record[key] = value or True
        if record.get("path"):
            records.append(record)
    ids = [str(item["workspace_id"]) for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Git worktree registry contains an identity collision")
    return records


def select_registered_worktree(project_root: Path, workspace_id: str, *, _root_is_resolved: bool = False) -> dict[str, Any]:
    if not _WORKSPACE_ID.fullmatch(workspace_id):
        raise ValueError("invalid registered workspace ID")
    matches = [
        item
        for item in registered_worktrees(project_root, _root_is_resolved=_root_is_resolved)
        if item["workspace_id"] == workspace_id
    ]
    if len(matches) != 1:
        raise ValueError("registered workspace ID is unavailable")
    return matches[0]


def _regular_file_hash(path: Path) -> str | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"cache fingerprint source is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"cache fingerprint source is not a safe directory: {path}")
    material: list[dict[str, Any]] = []
    for candidate in sorted(path.rglob("*"), key=lambda item: str(item).lower()):
        metadata = candidate.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"cache fingerprint source contains a link: {candidate}")
        if stat.S_ISREG(metadata.st_mode):
            material.append({"path": candidate.relative_to(path).as_posix(), "hash": _regular_file_hash(candidate)})
    return _hash(b"project-orrery-maintenance-cache-tree-v1\0", material)


def _evidence_hashes(root: Path, workstream_id: str | None) -> tuple[str | None, str | None]:
    if not workstream_id:
        return None, None
    closures: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    closure_dir = _private_area(root, "closures")
    if closure_dir.is_dir():
        for path in sorted(closure_dir.glob("closure-*.json")):
            value = _read_regular_json(path, description="maintenance cache closure evidence")
            if value.get("workstream_id") != workstream_id:
                continue
            closures.append({"path": path.name, "hash": _regular_file_hash(path)})
            package_id = value.get("review_package_id")
            if isinstance(package_id, str) and package_id:
                review_path = _private_area(root, "reviews", "packages") / f"{package_id}.json"
                reviews.append({"path": review_path.name, "hash": _regular_file_hash(review_path)})
    return (
        _hash(b"project-orrery-maintenance-cache-closures-v1\0", closures),
        _hash(b"project-orrery-maintenance-cache-reviews-v1\0", reviews),
    )


def fingerprint_registered_worktree(
    project_root: Path,
    record: Mapping[str, Any],
    *,
    _root_is_resolved: bool = False,
    _common: Path | None = None,
    _repository_identity_value: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root) if _root_is_resolved else _repository_root(project_root)
    path = Path(str(record["path"]))
    if _workspace_id(path) != record.get("workspace_id"):
        raise ValueError("registered workspace identity drifted")
    metadata = path.lstat()
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    if stat.S_ISLNK(metadata.st_mode) or (reparse_flag and attributes & reparse_flag):
        raise ValueError("registered workspace path is a symlink or reparse point")
    git_dir_result = _git(path, "rev-parse", "--path-format=absolute", "--absolute-git-dir", check=False)
    if git_dir_result.returncode:
        raise ValueError("registered worktree Git directory is unavailable")
    git_dir = Path(str(git_dir_result.stdout).strip())
    common = _common or Path(str(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout).strip())
    try:
        git_dir.resolve(strict=True).relative_to(common.resolve(strict=True))
    except (OSError, ValueError) as exc:
        if git_dir.resolve(strict=False) != common.resolve(strict=False):
            raise ValueError("registered worktree Git directory escapes the repository") from exc
    status = _git(
        path,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
        binary=True,
        check=False,
    )
    if status.returncode:
        raise ValueError("registered worktree status fingerprint is unavailable")
    status_raw = status.stdout if isinstance(status.stdout, bytes) else b""
    tracked: list[str] = []
    untracked: list[str] = []
    ignored_paths: list[str] = []
    dirty_items: list[str] = []
    for item in status_raw.split(b"\0"):
        if not item:
            continue
        decoded = item.decode("utf-8", errors="surrogateescape")
        target = decoded[3:].replace("\\", "/") if len(decoded) >= 3 else decoded
        if decoded.startswith("!! "):
            ignored_paths.append(target)
        elif decoded.startswith("?? "):
            untracked.append(target)
            dirty_items.append(decoded)
        else:
            tracked.append(target)
            dirty_items.append(decoded)
    ignored_paths = sorted(set(ignored_paths))
    session_path = git_dir / "orrery" / "worktree.json"
    session_hash = _regular_file_hash(session_path)
    workstream_id: str | None = None
    if session_hash:
        session = _read_regular_json(session_path, description="maintenance cache Workstream session")
        value = session.get("workstream_id")
        workstream_id = str(value) if isinstance(value, str) and value else None
    closure_hash, review_hash = _evidence_hashes(root, workstream_id)
    fingerprint = {
        "fingerprint_version": 1,
        "head": record.get("head"),
        "branch": record.get("branch"),
        "index_hash": _regular_file_hash(git_dir / "index"),
        "dirty": bool(dirty_items),
        "tracked_hash": _hash(b"project-orrery-maintenance-cache-tracked-v1\0", sorted(set(tracked))),
        "untracked_hash": _hash(b"project-orrery-maintenance-cache-untracked-v1\0", sorted(set(untracked))),
        "ignored_hash": _hash(b"project-orrery-maintenance-cache-ignored-v1\0", ignored_paths),
        "session_hash": session_hash,
        "closure_hash": closure_hash,
        "review_hash": review_hash,
        "locked": bool(record.get("locked")),
    }
    fingerprint["fingerprint_hash"] = _hash(b"project-orrery-maintenance-cache-fingerprint-v1\0", fingerprint)
    return {
        "record": dict(record),
        "git_dir": str(git_dir),
        "worktree_identity": _hash(
            b"project-orrery-maintenance-cache-worktree-identity-v1\0",
            {
                "repository_identity": _repository_identity_value or repository_identity(root),
                "path": os.path.normcase(os.path.realpath(path)),
                "git_dir": os.path.normcase(os.path.realpath(git_dir)),
            },
        ),
        "workstream_id": workstream_id,
        "fingerprint": fingerprint,
        "session_hash": session_hash,
        "closure_hash": closure_hash,
        "review_hash": review_hash,
    }


def validate_cache_entry(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _ENTRY_FIELDS:
        raise ValueError("maintenance cache entry fields are incompatible")
    if value.get("cache_schema_version") != CACHE_SCHEMA_VERSION or value.get("contract_type") != CACHE_CONTRACT:
        raise ValueError("unsupported maintenance cache entry version")
    if not _WORKSPACE_ID.fullmatch(str(value.get("workspace_id", ""))):
        raise ValueError("maintenance cache workspace ID is invalid")
    for field in ("repository_identity", "worktree_identity", "policy_hash"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(value.get(field, ""))):
            raise ValueError(f"maintenance cache {field} is invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(value.get("integration_oid", ""))):
        raise ValueError("maintenance cache integration OID is invalid")
    if not all(isinstance(value.get(field), str) and value.get(field) for field in ("registered_path", "resolved_path", "git_dir", "integration_ref", "tool_version", "scanned_at", "refresh_reason")):
        raise ValueError("maintenance cache identity or version field is unavailable")
    if not isinstance(value.get("maintenance_schema_version"), int) or not isinstance(value.get("cleanup_schema_version"), int):
        raise ValueError("maintenance cache schema binding is invalid")
    fingerprint = value.get("fingerprint")
    if not isinstance(fingerprint, Mapping) or fingerprint.get("fingerprint_version") != 1:
        raise ValueError("maintenance cache fingerprint is incompatible")
    if not re.fullmatch(r"[0-9a-f]{64}", str(fingerprint.get("fingerprint_hash", ""))):
        raise ValueError("maintenance cache fingerprint hash is invalid")
    if not isinstance(value.get("cleanup"), Mapping):
        raise ValueError("maintenance cache cleanup projection is unavailable")
    return dict(value)


def validate_cached_target(
    project_root: Path,
    *,
    workspace_id: str,
    integration_ref: str,
    integration_oid: str,
    policy: Mapping[str, Any],
    maintenance_schema_version: int,
    tool_version: str = CORE_TOOL_VERSION,
) -> dict[str, Any]:
    """Revalidate every cached destructive input without rerunning the W3 provider."""
    root = _repository_root(project_root)
    common, repo_id = _common_and_repository_identity(root)
    directory = common / "orrery" / "maintenance" / CACHE_DIRECTORY_NAME
    directory.mkdir(parents=True, exist_ok=True)
    record = select_registered_worktree(root, workspace_id, _root_is_resolved=True)
    cached, state, errors = _load_with_last_known(root, workspace_id, directory=directory)
    if cached is None or state != "current":
        raise ValueError(f"current target cache is unavailable: {','.join(errors)}")
    observation = fingerprint_registered_worktree(
        root,
        record,
        _root_is_resolved=True,
        _common=common,
        _repository_identity_value=repo_id,
    )
    expected = {
        "repository_identity": repo_id,
        "workspace_id": workspace_id,
        "worktree_identity": observation["worktree_identity"],
        "registered_path": record["path"],
        "resolved_path": record["resolved_path"],
        "git_dir": observation["git_dir"],
        "head": record.get("head"),
        "branch": record.get("branch"),
        "integration_ref": integration_ref,
        "integration_oid": integration_oid,
        "policy_hash": policy_hash(policy),
        "maintenance_schema_version": maintenance_schema_version,
        "tool_version": tool_version,
    }
    drifted = [field for field, expected_value in expected.items() if cached.get(field) != expected_value]
    if cached["fingerprint"].get("fingerprint_hash") != observation["fingerprint"].get("fingerprint_hash"):
        drifted.append("fingerprint")
    if drifted:
        raise ValueError(f"cached target evidence drifted: {','.join(sorted(set(drifted)))}")
    return {"entry": cached, "record": record, "observation": observation, "network_performed": False}


def validate_cache_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _SUMMARY_FIELDS:
        raise ValueError("maintenance cache registry summary fields are incompatible")
    if value.get("cache_schema_version") != CACHE_SCHEMA_VERSION or value.get("contract_type") != CACHE_SUMMARY_CONTRACT:
        raise ValueError("unsupported maintenance cache registry summary version")
    if not isinstance(value.get("entries"), list) or not isinstance(value.get("metrics"), Mapping):
        raise ValueError("maintenance cache registry summary is incompatible")
    return dict(value)


def _load_with_last_known(
    root: Path,
    workspace_id: str,
    *,
    directory: Path | None = None,
) -> tuple[dict[str, Any] | None, str, list[str]]:
    errors: list[str] = []
    base = directory or cache_root(root)
    path = base / "entries" / f"{workspace_id}.json"
    if path.exists():
        try:
            return validate_cache_entry(_read_regular_json(path, description="maintenance cache entry")), "current", errors
        except ValueError as exc:
            errors.append(f"current:{type(exc).__name__}")
    else:
        errors.append("current:missing")
    backup = base / "last-known" / f"{workspace_id}.json"
    if backup.exists():
        try:
            return validate_cache_entry(_read_regular_json(backup, description="maintenance last-known cache entry")), "stale", errors
        except ValueError as exc:
            errors.append(f"last-known:{type(exc).__name__}")
    return None, "unknown", errors


def _write_entry(root: Path, entry: Mapping[str, Any], *, directory: Path | None = None) -> None:
    workspace_id = str(entry["workspace_id"])
    base = directory or cache_root(root)
    path = base / "entries" / f"{workspace_id}.json"
    if path.exists():
        try:
            current = validate_cache_entry(_read_regular_json(path, description="maintenance cache entry"))
        except ValueError:
            current = None
        if current is not None:
            _atomic_json(base / "last-known" / f"{workspace_id}.json", current)
    _atomic_json(path, validate_cache_entry(entry))


def _write_summary(root: Path, summary: Mapping[str, Any], *, directory: Path | None = None) -> None:
    base = directory or cache_root(root)
    path = base / "registry-summary.json"
    if path.exists():
        try:
            current = validate_cache_summary(_read_regular_json(path, description="maintenance cache registry summary"))
        except ValueError:
            current = None
        if current is not None:
            _atomic_json(base / "last-known-registry-summary.json", current)
    _atomic_json(path, validate_cache_summary(summary))


def _entry_projection(entry: Mapping[str, Any], *, cache_state: str, errors: Sequence[str] = ()) -> dict[str, Any]:
    cleanup = entry.get("cleanup") if isinstance(entry.get("cleanup"), Mapping) else {}
    workspace = cleanup.get("workspace") if isinstance(cleanup.get("workspace"), Mapping) else {}
    return {
        "workspace_id": entry.get("workspace_id"),
        "registered_path": entry.get("registered_path"),
        "head": entry.get("head"),
        "branch": entry.get("branch"),
        "classification": workspace.get("classification", "unknown"),
        "is_primary_worktree": bool(workspace.get("is_primary_worktree")),
        "eligible": bool(cleanup.get("eligible")),
        "remove_worktree_eligible": bool((cleanup.get("actions") or {}).get("remove-worktree", {}).get("eligible")),
        "reasons": list(cleanup.get("reasons", [])),
        "unknown": list(cleanup.get("unknown", [])),
        "estimated_reclaim_bytes": cleanup.get("estimated_reclaim_bytes"),
        "cache_state": cache_state,
        "cache_errors": list(errors),
        "scanned_at": entry.get("scanned_at"),
        "refresh_reason": entry.get("refresh_reason"),
        "fingerprint_hash": (entry.get("fingerprint") or {}).get("fingerprint_hash"),
    }


def cache_status(project_root: Path, *, directory: Path | None = None) -> dict[str, Any]:
    """Read cache files only; no Git/provider scan is performed."""
    root = _repository_root(project_root)
    directory = directory or cache_root(root)
    ids: set[str] = set()
    for name in ("entries", "last-known"):
        candidate = directory / name
        if candidate.is_dir():
            ids.update(path.stem for path in candidate.glob("workspace-*.json"))
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    for workspace_id in sorted(ids):
        entry, state, entry_errors = _load_with_last_known(root, workspace_id, directory=directory)
        errors.extend(f"{workspace_id}:{item}" for item in entry_errors)
        if entry is not None:
            entries.append(_entry_projection(entry, cache_state=state, errors=entry_errors))
    summary: dict[str, Any] | None = None
    summary_state = "unknown"
    for path, state in ((directory / "registry-summary.json", "current"), (directory / "last-known-registry-summary.json", "stale")):
        if not path.exists():
            continue
        try:
            summary = validate_cache_summary(_read_regular_json(path, description="maintenance cache registry summary"))
            summary_state = state
            break
        except ValueError as exc:
            errors.append(f"registry-summary:{state}:{type(exc).__name__}")
    if summary is not None:
        by_id = {str(item.get("workspace_id")): item for item in entries}
        for projected in summary.get("entries", []):
            workspace_id = str(projected.get("workspace_id"))
            if workspace_id not in by_id:
                value = dict(projected)
                value["cache_state"] = "stale" if summary_state == "stale" else "unknown"
                value["cache_errors"] = ["entry-unavailable"]
                entries.append(value)
    entries.sort(key=lambda item: (str(item.get("registered_path")), str(item.get("workspace_id"))))
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "directory": str(directory),
        "status": "current" if summary_state == "current" and all(item["cache_state"] == "current" for item in entries) else ("stale" if entries else "unknown"),
        "summary_state": summary_state,
        "summary": summary,
        "entries": entries,
        "errors": errors,
        "cache_hit_read": True,
        "git_provider_scans": 0,
        "network_performed": False,
    }


def _build_entry(
    root: Path,
    *,
    observation: Mapping[str, Any],
    cleanup: Mapping[str, Any],
    integration_ref: str,
    integration_oid: str,
    current_policy_hash: str,
    maintenance_schema_version: int,
    tool_version: str,
    scanned_at: str,
    refresh_reason: str,
    repository_identity_value: str | None = None,
) -> dict[str, Any]:
    record = observation["record"]
    entry = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "contract_type": CACHE_CONTRACT,
        "repository_identity": repository_identity_value or repository_identity(root),
        "workspace_id": record["workspace_id"],
        "worktree_identity": observation["worktree_identity"],
        "registered_path": record["path"],
        "resolved_path": record["resolved_path"],
        "git_dir": observation["git_dir"],
        "head": record.get("head"),
        "branch": record.get("branch"),
        "fingerprint": dict(observation["fingerprint"]),
        "session_hash": observation.get("session_hash"),
        "closure_hash": observation.get("closure_hash"),
        "review_hash": observation.get("review_hash"),
        "integration_ref": integration_ref,
        "integration_oid": integration_oid,
        "policy_hash": current_policy_hash,
        "maintenance_schema_version": maintenance_schema_version,
        "cleanup_schema_version": int(cleanup.get("cleanup_schema_version", 0)),
        "tool_version": tool_version,
        "scanned_at": scanned_at,
        "refresh_reason": refresh_reason,
        "integration_sensitive": bool(cleanup.get("final_oid") or (cleanup.get("workspace") or {}).get("classification") == "integrated-closed"),
        "cleanup": dict(cleanup),
    }
    return validate_cache_entry(entry)


def refresh_incremental_cache(
    project_root: Path,
    *,
    integration_ref: str,
    integration_oid: str,
    policy: Mapping[str, Any],
    maintenance_schema_version: int,
    scanned_at: str,
    eligibility_provider: Callable[..., Mapping[str, Any]],
    fingerprint_provider: Callable[[Path, Mapping[str, Any]], Mapping[str, Any]] = fingerprint_registered_worktree,
    tool_version: str = CORE_TOOL_VERSION,
    target_workspace_id: str | None = None,
) -> dict[str, Any]:
    """Refresh changed registered targets and reuse valid unchanged entries."""
    started = time.perf_counter()
    root = _repository_root(project_root)
    common, repo_id = _common_and_repository_identity(root)
    directory = common / "orrery" / "maintenance" / CACHE_DIRECTORY_NAME
    directory.mkdir(parents=True, exist_ok=True)
    all_records = registered_worktrees(root, _root_is_resolved=True)
    records = all_records
    if target_workspace_id is not None:
        if not _WORKSPACE_ID.fullmatch(target_workspace_id):
            raise ValueError("invalid registered workspace ID")
        records = [item for item in records if item["workspace_id"] == target_workspace_id]
        if len(records) != 1:
            raise ValueError("registered workspace ID is unavailable")
    current_policy_hash = policy_hash(policy)
    metrics = {
        "registered": len(all_records),
        "considered": len(records),
        "cache_hits": 0,
        "fingerprint_changes": 0,
        "target_provider_scans": 0,
        "integration_only_updates": 0,
        "cache_invalidations": 0,
        "removed": 0,
    }
    refreshed: list[dict[str, Any]] = []
    projections: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for record in records:
        workspace_id = str(record["workspace_id"])
        cached, state, cache_errors = _load_with_last_known(root, workspace_id, directory=directory)
        try:
            if fingerprint_provider is fingerprint_registered_worktree:
                observation = fingerprint_provider(
                    root,
                    record,
                    _root_is_resolved=True,
                    _common=common,
                    _repository_identity_value=repo_id,
                )
            else:
                observation = fingerprint_provider(root, record)
            compatible = bool(
                cached
                and state == "current"
                and cached.get("repository_identity") == repo_id
                and cached.get("policy_hash") == current_policy_hash
                and cached.get("maintenance_schema_version") == maintenance_schema_version
                and cached.get("tool_version") == tool_version
                and cached.get("worktree_identity") == observation.get("worktree_identity")
            )
            same_fingerprint = compatible and cached["fingerprint"]["fingerprint_hash"] == observation["fingerprint"]["fingerprint_hash"]
            if target_workspace_id is None and same_fingerprint and cached.get("integration_oid") == integration_oid:
                metrics["cache_hits"] += 1
                entry = cached
            elif target_workspace_id is None and same_fingerprint and not cached.get("integration_sensitive"):
                entry = dict(cached)
                entry["integration_oid"] = integration_oid
                entry["integration_ref"] = integration_ref
                entry["scanned_at"] = scanned_at
                entry["refresh_reason"] = "integration-oid-only"
                _write_entry(root, entry, directory=directory)
                metrics["integration_only_updates"] += 1
            else:
                metrics["fingerprint_changes"] += int(bool(compatible))
                metrics["cache_invalidations"] += int(not compatible)
                cleanup = eligibility_provider(
                    root,
                    workspace_id=workspace_id,
                    ignored_allowlist=policy["ignored_allowlist"],
                )
                metrics["target_provider_scans"] += 1
                reason = "target-preflight" if target_workspace_id is not None else ("fingerprint-changed" if compatible else "cache-miss-or-incompatible")
                if same_fingerprint and cached and cached.get("integration_oid") != integration_oid:
                    reason = "integration-oid-changed"
                entry = _build_entry(
                    root,
                    observation=observation,
                    cleanup=cleanup,
                    integration_ref=integration_ref,
                    integration_oid=integration_oid,
                    current_policy_hash=current_policy_hash,
                    maintenance_schema_version=maintenance_schema_version,
                    tool_version=tool_version,
                    scanned_at=scanned_at,
                    refresh_reason=reason,
                    repository_identity_value=repo_id,
                )
                _write_entry(root, entry, directory=directory)
            refreshed.append(entry)
            projections.append(_entry_projection(entry, cache_state="current"))
        except Exception as exc:
            errors.append({"workspace_id": workspace_id, "type": type(exc).__name__, "message": str(exc)})
            if cached is not None:
                projections.append(_entry_projection(cached, cache_state="stale", errors=[*cache_errors, type(exc).__name__]))
            else:
                projections.append({
                    "workspace_id": workspace_id,
                    "registered_path": record.get("path"),
                    "head": record.get("head"),
                    "branch": record.get("branch"),
                    "classification": "unknown",
                    "eligible": False,
                    "remove_worktree_eligible": False,
                    "reasons": ["target-refresh-failed"],
                    "unknown": [type(exc).__name__],
                    "estimated_reclaim_bytes": None,
                    "cache_state": "unknown",
                    "cache_errors": [type(exc).__name__],
                    "scanned_at": None,
                    "refresh_reason": "refresh-failed",
                    "fingerprint_hash": None,
                })
    if target_workspace_id is None:
        current_ids = {str(item["workspace_id"]) for item in records}
        entry_dir = directory / "entries"
        if entry_dir.is_dir():
            for path in entry_dir.glob("workspace-*.json"):
                if path.stem not in current_ids:
                    path.unlink(missing_ok=True)
                    (directory / "last-known" / f"{path.stem}.json").unlink(missing_ok=True)
                    metrics["removed"] += 1
    else:
        target_projection = projections
        projections = []
        for record in all_records:
            workspace_id = str(record["workspace_id"])
            if workspace_id == target_workspace_id:
                projections.extend(target_projection)
                continue
            cached, state, cache_errors = _load_with_last_known(root, workspace_id, directory=directory)
            compatible = bool(
                cached
                and state == "current"
                and cached.get("repository_identity") == repo_id
                and cached.get("policy_hash") == current_policy_hash
                and cached.get("maintenance_schema_version") == maintenance_schema_version
                and cached.get("tool_version") == tool_version
            )
            if cached is not None:
                projections.append(
                    _entry_projection(
                        cached,
                        cache_state="current" if compatible else "stale",
                        errors=cache_errors if compatible else [*cache_errors, "contract-incompatible"],
                    )
                )
            else:
                projections.append(
                    {
                        "workspace_id": workspace_id,
                        "registered_path": record.get("path"),
                        "head": record.get("head"),
                        "branch": record.get("branch"),
                        "classification": "unknown",
                        "is_primary_worktree": bool(record.get("is_primary")),
                        "eligible": False,
                        "remove_worktree_eligible": False,
                        "reasons": ["cache-entry-unavailable"],
                        "unknown": ["cache-entry-unavailable"],
                        "estimated_reclaim_bytes": None,
                        "cache_state": "unknown",
                        "cache_errors": cache_errors,
                        "scanned_at": None,
                        "refresh_reason": "cache-missing",
                        "fingerprint_hash": None,
                    }
                )
    registry_material = [
        {"workspace_id": item["workspace_id"], "path": item["path"], "head": item.get("head"), "branch": item.get("branch")}
        for item in all_records
    ]
    summary = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "contract_type": CACHE_SUMMARY_CONTRACT,
        "repository_identity": repo_id,
        "integration_ref": integration_ref,
        "integration_oid": integration_oid,
        "policy_hash": current_policy_hash,
        "maintenance_schema_version": maintenance_schema_version,
        "cleanup_schema_version": max((int(item.get("cleanup_schema_version", 0)) for item in refreshed), default=0),
        "tool_version": tool_version,
        "generated_at": scanned_at,
        "registry_hash": _hash(b"project-orrery-maintenance-cache-registry-v1\0", registry_material),
        "status": "current" if not errors and all(item.get("cache_state") == "current" for item in projections) else "stale-unknown",
        "entries": sorted(projections, key=lambda item: (str(item.get("registered_path")), str(item.get("workspace_id")))),
        "metrics": metrics,
    }
    _write_summary(root, summary, directory=directory)
    metrics["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
    summary["metrics"] = metrics
    _atomic_json(directory / "registry-summary.json", summary)
    return {"summary": summary, "entries": refreshed, "projections": projections, "errors": errors, "metrics": metrics}


def invalidate_cache_after_remove(
    project_root: Path,
    workspace_id: str,
    *,
    _directory: Path | None = None,
    _root_is_resolved: bool = False,
) -> dict[str, Any]:
    """Invalidate only the removed target plus the global derived registry summary."""
    if not _WORKSPACE_ID.fullmatch(workspace_id):
        raise ValueError("invalid registered workspace ID")
    root = Path(project_root) if _root_is_resolved else _repository_root(project_root)
    directory = _directory or cache_root(root)
    removed: list[str] = []
    for path in (
        directory / "entries" / f"{workspace_id}.json",
        directory / "last-known" / f"{workspace_id}.json",
        directory / "registry-summary.json",
        directory / "last-known-registry-summary.json",
    ):
        if path.exists():
            path.unlink()
            removed.append(str(path))
    return {"workspace_id": workspace_id, "invalidated": removed, "network_performed": False}
