"""Read-only workspace inventory and conservative cleanup eligibility contracts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import datetime as dt
from pathlib import Path
from typing import Any, Mapping, Sequence

from .collaboration import resolve_integration_oid, validate_collaboration_contract
from .review import (
    _common_git_dir,
    _directory_size,
    _git,
    _path_matches,
    _private_area,
    _read_regular_json,
    _repository_root,
    load_review_package,
)


WORKSPACE_INVENTORY_SCHEMA_VERSION = 1
WORKSPACE_CLEANUP_SCHEMA_VERSION = 2
CLEANUP_ACTION_RECEIPT_SCHEMA_VERSION = 1
WORKSPACE_CLASSIFICATIONS = {
    "registered-active": "Registered active",
    "review-integration-pending": "Review/Integration pending",
    "integrated-closed": "Integrated/Closed",
    "legacy-unmanaged": "Legacy unmanaged",
    "generated-disposable": "Generated disposable",
    "evidence-retained": "Evidence/retained",
    "unknown": "Unknown",
}
CLEANUP_ACTIONS = (
    "remove-worktree",
    "delete-local-branch",
    "delete-remote-branch",
    "remove-directory",
)
_RECEIPT_ID = re.compile(r"^cleanup-action-[0-9a-f]{24}$")
_CLOSURE_ID = re.compile(r"^closure-[0-9a-f]{24}$")
_SENSITIVE_LOCAL_NAMES = {
    ".doccache.json",
    ".port",
    "ai-config.json",
    "credentials.json",
    "keyring",
}


def _norm(path: Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def _absolute(project_root: Path, value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return Path(os.path.abspath(path))


def _within(path: Path, root: Path) -> bool:
    try:
        Path(_norm(path)).relative_to(Path(_norm(root)))
    except ValueError:
        return False
    return True


def _has_reparse_or_symlink(path: Path, boundary: Path) -> bool:
    """Inspect the candidate and its path segments without following directory contents."""
    candidate = Path(os.path.abspath(path))
    stop = Path(os.path.abspath(boundary))
    current = candidate
    while True:
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            pass
        except OSError:
            return True
        else:
            attributes = int(getattr(metadata, "st_file_attributes", 0))
            reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
            if stat.S_ISLNK(metadata.st_mode) or attributes & reparse_flag:
                return True
        if os.path.normcase(str(current)) == os.path.normcase(str(stop)):
            return False
        parent = current.parent
        if parent == current:
            return True
        current = parent


def _manifest_policy(project_root: Path) -> dict[str, list[Path]]:
    path = project_root / ".project-orrery.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read Project Orrery workspace policy: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Project Orrery manifest must contain an object")
    collaboration = payload.get("collaboration", {})
    if not isinstance(collaboration, Mapping):
        raise ValueError("manifest collaboration policy must be an object")
    cleanup = collaboration.get("workspace_inventory", {})
    if not isinstance(cleanup, Mapping):
        raise ValueError("manifest workspace inventory policy must be an object")
    result: dict[str, list[Path]] = {}
    for key in ("workspace_roots", "retained_paths", "recovery_paths", "credential_cache_paths"):
        values = cleanup.get(key, [])
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise ValueError(f"manifest workspace inventory {key} must be a string array")
        result[key] = [_absolute(project_root, item) for item in values]
    recovery_refs = cleanup.get("recovery_refs", [])
    if not isinstance(recovery_refs, list) or any(not isinstance(item, str) for item in recovery_refs):
        raise ValueError("manifest workspace inventory recovery_refs must be a string array")
    result["recovery_refs"] = [Path(item) for item in recovery_refs]
    return result


def _worktree_records(repository: Path) -> list[dict[str, Any]]:
    raw = str(_git(repository, "worktree", "list", "--porcelain").stdout)
    records: list[dict[str, Any]] = []
    for index, block in enumerate(item for item in raw.split("\n\n") if item.strip()):
        record: dict[str, Any] = {"source": "git-worktree-metadata", "is_primary": index == 0}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                record["path"] = str(Path(value).absolute())
            elif key == "HEAD":
                record["head"] = value.lower()
            elif key == "branch":
                record["branch"] = value
            elif key in {"bare", "detached", "locked", "prunable"}:
                record[key] = value or True
        if record.get("path"):
            records.append(record)
    return records


def _closure_records(repository: Path) -> list[dict[str, Any]]:
    directory = _private_area(repository, "closures")
    if not directory.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("closure-*.json")):
        value = _read_regular_json(path, description="closure record")
        validate_collaboration_contract(value)
        if value.get("contract_type") != "closure-record":
            raise ValueError("Git-private closure directory contains the wrong contract type")
        value["_git_private_path"] = str(path)
        records.append(value)
    return records


def _classification_value(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "registered": "registered-active",
        "active": "registered-active",
        "review-pending": "review-integration-pending",
        "integration-pending": "review-integration-pending",
        "integrated": "integrated-closed",
        "closed": "integrated-closed",
        "legacy": "legacy-unmanaged",
        "generated": "generated-disposable",
        "disposable": "generated-disposable",
        "retained": "evidence-retained",
        "evidence": "evidence-retained",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in WORKSPACE_CLASSIFICATIONS:
        raise ValueError(f"unsupported workspace classification: {value}")
    return normalized


def _classification_map(project_root: Path, values: Mapping[str, str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for path, classification in (values or {}).items():
        result[_norm(_absolute(project_root, path))] = _classification_value(classification)
    return result


def _git_observation(path: Path, expected_common: Path) -> dict[str, Any]:
    if not path.is_dir():
        return {
            "available": False,
            "same_common_dir": False,
            "toplevel": None,
            "git_dir": None,
            "common_dir": None,
            "head": None,
            "branch": None,
            "tracked_changes": [],
            "untracked_paths": [],
            "ignored_paths": [],
        }
    identity = _git(
        path,
        "rev-parse",
        "--show-toplevel",
        "--path-format=absolute",
        "--git-common-dir",
        "--absolute-git-dir",
        "HEAD",
        "--symbolic-full-name",
        "HEAD",
        check=False,
    )
    identity_lines = str(identity.stdout).splitlines() if not identity.returncode else []
    if len(identity_lines) != 5:
        return {
            "available": False,
            "same_common_dir": False,
            "toplevel": None,
            "git_dir": None,
            "common_dir": None,
            "head": None,
            "branch": None,
            "tracked_changes": [],
            "untracked_paths": [],
            "ignored_paths": [],
        }
    toplevel = Path(identity_lines[0]).absolute()
    status_result = _git(
        path,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
        binary=True,
        check=False,
    )
    status_raw = status_result.stdout if isinstance(status_result.stdout, bytes) else b""
    tracked: list[str] = []
    untracked: list[str] = []
    ignored: list[str] = []
    for item in status_raw.split(b"\0"):
        if not item:
            continue
        decoded = item.decode("utf-8", errors="surrogateescape")
        target = decoded[3:].replace("\\", "/") if len(decoded) >= 3 else decoded
        if decoded.startswith("!! "):
            ignored.append(target)
        elif decoded.startswith("?? "):
            untracked.append(target)
        else:
            tracked.append(target)
    common = Path(identity_lines[1]).absolute()
    git_dir = Path(identity_lines[2]).absolute()
    head = identity_lines[3].strip().lower()
    symbolic_head = identity_lines[4].strip()
    branch = symbolic_head if symbolic_head.startswith("refs/") else None
    return {
        "available": bool(re.fullmatch(r"[0-9a-f]{40}", head)),
        "same_common_dir": _norm(common) == _norm(expected_common),
        "toplevel": str(toplevel),
        "git_dir": str(git_dir) if git_dir is not None else None,
        "common_dir": str(common) if common is not None else None,
        "head": head,
        "branch": branch,
        "tracked_changes": sorted(set(tracked)),
        "untracked_paths": sorted(set(untracked)),
        "ignored_paths": sorted(set(ignored)),
    }


def _entry_id(path: Path) -> str:
    return "workspace-" + hashlib.sha256(_norm(path).encode("utf-8")).hexdigest()[:24]


def inventory_workspaces(
    project_root: Path,
    *,
    workspace_roots: Sequence[str | os.PathLike[str]] = (),
    candidate_paths: Sequence[str | os.PathLike[str]] = (),
    classifications: Mapping[str, str] | None = None,
    retained_paths: Sequence[str | os.PathLike[str]] = (),
    recovery_paths: Sequence[str | os.PathLike[str]] = (),
    selected_workspace_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Inventory only bounded Git/config/user paths; never scan sibling prefixes or a whole disk."""
    root = _repository_root(project_root)
    common = _common_git_dir(root)
    policy = _manifest_policy(root)
    allowed_roots = [root, *policy["workspace_roots"]]
    allowed_roots.extend(_absolute(root, item) for item in workspace_roots)
    retained = [*policy["retained_paths"], *(_absolute(root, item) for item in retained_paths)]
    recovery = [*policy["recovery_paths"], *(_absolute(root, item) for item in recovery_paths)]
    credential_cache = list(policy["credential_cache_paths"])
    explicit_classifications = _classification_map(root, classifications)
    all_worktrees = _worktree_records(root)
    selected_ids = set(selected_workspace_ids)
    if any(not re.fullmatch(r"workspace-[0-9a-f]{24}", item) for item in selected_ids):
        raise ValueError("selected workspace ID is invalid")
    if selected_ids and candidate_paths:
        raise ValueError("selected workspace inventory does not accept arbitrary candidate paths")
    by_id = {_entry_id(Path(str(item["path"]))): item for item in all_worktrees}
    missing_ids = selected_ids - set(by_id)
    if missing_ids:
        raise ValueError("selected workspace ID is not a registered worktree")
    worktrees = [by_id[item] for item in sorted(selected_ids)] if selected_ids else all_worktrees
    closures = _closure_records(root)
    candidates: dict[str, dict[str, Any]] = {}

    def add(path: Path, source: str, **metadata: Any) -> None:
        key = _norm(path)
        entry = candidates.setdefault(
            key,
            {"path": Path(os.path.abspath(path)), "sources": [], "metadata": {}},
        )
        if source not in entry["sources"]:
            entry["sources"].append(source)
        entry["metadata"].update(metadata)

    for record in worktrees:
        path = Path(str(record["path"]))
        add(path, "git-worktree-metadata", worktree=record)
    for value in candidate_paths:
        add(_absolute(root, value), "explicit-user-candidate")
    for closure in closures:
        original = closure.get("original_workspace_path")
        if (
            isinstance(original, str)
            and original
            and (not selected_ids or _entry_id(Path(original)) in selected_ids)
        ):
            add(Path(original), "git-private-closure", closure=closure)

    registered_paths = {_norm(Path(str(item["path"]))) for item in worktrees}
    entries: list[dict[str, Any]] = []
    for key, candidate in sorted(candidates.items(), key=lambda item: item[0]):
        path = candidate["path"]
        metadata = candidate["metadata"]
        worktree = metadata.get("worktree")
        closure = metadata.get("closure")
        matching_roots = [item for item in allowed_roots if _within(path, item)]
        if key in registered_paths:
            matching_roots.append(path)
        allowed = bool(matching_roots)
        resolved = Path(os.path.realpath(path))
        escape = allowed and not any(_within(resolved, item) for item in matching_roots)
        boundary = max(matching_roots, key=lambda item: len(str(item)), default=root)
        reparse = path.exists() and _has_reparse_or_symlink(path, boundary)
        path_safe = allowed and not escape and not reparse
        git = _git_observation(path, common)
        session: dict[str, Any] | None = None
        session_state = "absent"
        if git["available"] and git["same_common_dir"] and path.is_dir():
            try:
                session_path = Path(str(git["git_dir"])) / "orrery" / "worktree.json"
                if session_path.exists():
                    session = _read_regular_json(session_path, description="Git-private Workstream session")
                    validate_collaboration_contract(session)
                    if session.get("contract_type") != "workstream-session":
                        raise ValueError("Git-private Workstream session has the wrong contract type")
                    session_state = "current"
            except (OSError, ValueError):
                session_state = "unreadable"
        if closure is None and session is not None:
            matches = [
                item for item in closures if item.get("workstream_id") == session.get("workstream_id")
            ]
            if matches:
                closure = sorted(matches, key=lambda item: str(item.get("closed_at")))[-1]

        explicit = explicit_classifications.get(key)
        phase = str(session.get("lifecycle_phase")) if session is not None else None
        is_primary = bool(worktree and worktree.get("is_primary"))
        if phase in {"integrated", "closed"} or closure is not None:
            classification, source = "integrated-closed", "git-private-session-or-closure"
        elif phase in {"validating", "review-ready"}:
            classification, source = "review-integration-pending", "git-private-session"
        elif session is not None or is_primary:
            classification, source = "registered-active", "git-private-session-or-primary"
        elif explicit is not None:
            classification, source = explicit, "explicit-user-classification"
        elif worktree is not None or git["available"]:
            classification, source = "legacy-unmanaged", "git-without-orrery-session"
        else:
            classification, source = "unknown", "insufficient-evidence"
        adopted = explicit is not None or session is not None or closure is not None
        protections: list[str] = []
        if is_primary:
            protections.append("primary-worktree")
        if any(_within(path, item) or _within(item, path) for item in retained):
            protections.append("evidence-retention-policy")
        if any(_within(path, item) or _within(item, path) for item in recovery):
            protections.append("recovery-or-immutable-policy")
        if any(_within(path, item) or _within(item, path) for item in credential_cache):
            protections.append("credential-or-cache-boundary")
        if classification == "evidence-retained":
            protections.append("explicit-evidence-retained-classification")
        if phase not in {None, "integrated", "closed"}:
            protections.append("active-or-pending-workstream")
        unknown: list[str] = []
        if not path.exists():
            unknown.append("workspace-path-not-found")
        if not allowed:
            unknown.append("workspace-outside-allowed-roots")
        if escape:
            unknown.append("resolved-path-escapes-allowed-root")
        if reparse:
            unknown.append("symlink-or-reparse-path-boundary")
        if not git["available"]:
            unknown.append("git-identity-unavailable")
        elif not git["same_common_dir"]:
            unknown.append("git-common-dir-does-not-match-project")
        if classification in {"legacy-unmanaged", "unknown"} and not adopted:
            unknown.append("explicit-adoption-or-classification-required")
        if session_state == "unreadable":
            unknown.append("git-private-session-unreadable")
        if protections:
            recommendation = "retain-protected"
        elif classification == "registered-active":
            recommendation = "retain-active"
        elif classification == "review-integration-pending":
            recommendation = "await-review-or-integration"
        elif classification in {"legacy-unmanaged", "unknown"}:
            recommendation = "report-and-request-explicit-adoption"
        elif classification == "evidence-retained":
            recommendation = "retain-evidence"
        else:
            recommendation = "evaluate-cleanup-eligibility"
        estimated = _directory_size(path) if not selected_ids and path_safe and path.is_dir() else None
        entries.append(
            {
                "workspace_id": _entry_id(path),
                "path": str(path),
                "resolved_path": str(resolved),
                "sources": candidate["sources"],
                "classification": classification,
                "classification_label": WORKSPACE_CLASSIFICATIONS[classification],
                "classification_source": source,
                "explicitly_adopted_or_classified": adopted,
                "exists": path.exists(),
                "allowed_root": str(boundary) if allowed else None,
                "path_safe": path_safe,
                "is_symlink_or_reparse": reparse,
                "is_registered_worktree": worktree is not None,
                "is_primary_worktree": is_primary,
                "git": git,
                "session": {
                    "state": session_state,
                    "workstream_id": session.get("workstream_id") if session else None,
                    "lifecycle_phase": phase,
                    "runtime_condition": session.get("runtime_condition") if session else None,
                },
                "closure": {
                    "closure_id": closure.get("closure_id") if closure else None,
                    "closure_reason": closure.get("closure_reason") if closure else None,
                    "final_oid": closure.get("final_oid") if closure else None,
                    "review_package_id": closure.get("review_package_id") if closure else None,
                    "record_path": closure.get("_git_private_path") if closure else None,
                },
                "protections": sorted(set(protections)),
                "unknown": sorted(set(unknown)),
                "estimated_reclaim_bytes": estimated,
                "recommended_action": recommendation,
            }
        )
    material = {
        "project_root": str(root),
        "git_common_dir": str(common),
        "allowed_roots": sorted({_norm(item) for item in allowed_roots}),
        "entries": entries,
    }
    digest = hashlib.sha256(
        b"project-orrery-workspace-inventory-v1\0"
        + json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "inventory_schema_version": WORKSPACE_INVENTORY_SCHEMA_VERSION,
        "inventory_id": f"inventory-{digest[:24]}",
        "content_hash": digest,
        **material,
        "source_contract": {
            "git_worktree_metadata": True,
            "git_private_sessions_and_closures": True,
            "project_config_workspace_roots": [str(item) for item in policy["workspace_roots"]],
            "explicit_workspace_roots": [str(_absolute(root, item)) for item in workspace_roots],
            "explicit_candidate_paths": [str(_absolute(root, item)) for item in candidate_paths],
            "recursive_disk_or_prefix_discovery": False,
            "selected_registered_workspace_ids": sorted(selected_ids),
        },
        "writes_performed": False,
        "network_performed": False,
    }


def _sensitive_ignored(path: str) -> bool:
    parts = {item.lower() for item in Path(path.replace("\\", "/")).parts}
    return bool(parts & _SENSITIVE_LOCAL_NAMES) or any(
        "credential" in item or "keyring" in item for item in parts
    )


def _authorization_id(
    *, workspace_id: str, action: str, closure_id: str | None, target_oid: str | None
) -> str:
    material = f"{workspace_id}\0{action}\0{closure_id or ''}\0{target_oid or ''}".encode("utf-8")
    return "cleanup-authorization-" + hashlib.sha256(material).hexdigest()[:24]


def compute_workspace_cleanup_eligibility(
    project_root: Path,
    *,
    workspace_path: str | os.PathLike[str] | None = None,
    workspace_id: str | None = None,
    package: str | Path | None = None,
    workspace_roots: Sequence[str | os.PathLike[str]] = (),
    classifications: Mapping[str, str] | None = None,
    retained_paths: Sequence[str | os.PathLike[str]] = (),
    recovery_paths: Sequence[str | os.PathLike[str]] = (),
    ignored_allowlist: Sequence[str] = (),
    authorized_actions: Sequence[str] = (),
) -> dict[str, Any]:
    """Compute an advisory contract. Explicit authorizations never execute an action."""
    requested = list(dict.fromkeys(authorized_actions))
    unsupported = [item for item in requested if item not in CLEANUP_ACTIONS]
    if unsupported:
        raise ValueError(f"unsupported cleanup authorization action: {unsupported[0]}")
    root = _repository_root(project_root)
    if (workspace_path is None) == (workspace_id is None):
        raise ValueError("cleanup eligibility requires exactly one workspace path or registered workspace ID")
    if workspace_id is not None:
        inventory = inventory_workspaces(
            root,
            workspace_roots=workspace_roots,
            classifications=classifications,
            retained_paths=retained_paths,
            recovery_paths=recovery_paths,
            selected_workspace_ids=[workspace_id],
        )
        if len(inventory["entries"]) != 1:
            raise ValueError("registered workspace inventory did not produce exactly one selected entry")
        selected_path = Path(str(inventory["entries"][0]["path"]))
    else:
        selected_path = _absolute(root, workspace_path)
        inventory = inventory_workspaces(
            root,
            workspace_roots=workspace_roots,
            candidate_paths=[selected_path],
            classifications=classifications,
            retained_paths=retained_paths,
            recovery_paths=recovery_paths,
        )
    matches = [item for item in inventory["entries"] if _norm(Path(item["path"])) == _norm(selected_path)]
    if len(matches) != 1:
        raise ValueError("workspace inventory did not produce exactly one selected entry")
    entry = matches[0]
    reasons: list[str] = []
    unknown = list(entry["unknown"])
    if not entry["exists"]:
        reasons.append("workspace-path-not-found")
    if not entry["path_safe"]:
        reasons.append("workspace-path-boundary-not-safe")
    if entry["classification"] in {"legacy-unmanaged", "unknown"} and not entry[
        "explicitly_adopted_or_classified"
    ]:
        reasons.append("legacy-or-unknown-workspace-requires-explicit-adoption")
    if entry["classification"] == "registered-active":
        reasons.append("workstream-is-active")
    if entry["classification"] == "review-integration-pending":
        reasons.append("review-or-integration-is-pending")
    if entry["classification"] == "evidence-retained" or entry["protections"]:
        reasons.append("workspace-is-protected-or-retained")
    git = entry["git"]
    if not git["available"] or not git["same_common_dir"]:
        reasons.append("git-identity-or-common-dir-not-verified")
    if git["tracked_changes"]:
        reasons.append("tracked-worktree-changes-present")
    if git["untracked_paths"]:
        reasons.append("unknown-untracked-paths-present")
        unknown.extend(f"untracked:{item}" for item in git["untracked_paths"])
    ignored = list(git["ignored_paths"])
    allowlisted_ignored = [
        item
        for item in ignored
        if any(
            _path_matches(item, pattern)
            or (item.endswith("/") and _path_matches(item + "__orrery_ignored_probe__", pattern))
            for pattern in ignored_allowlist
        )
    ]
    sensitive = [item for item in ignored if _sensitive_ignored(item)]
    unknown_ignored = sorted(set(ignored) - set(allowlisted_ignored) | set(sensitive))
    if unknown_ignored:
        reasons.append("unknown-or-sensitive-ignored-paths-present")
        unknown.extend(f"ignored:{item}" for item in unknown_ignored)

    review: dict[str, Any] | None = None
    closure: dict[str, Any] | None = None
    closure_path: str | None = entry["closure"]["record_path"]
    if package is not None:
        review = load_review_package(root, package)
        closure_dir = _private_area(root, "closures")
        if closure_dir.is_dir():
            for path in closure_dir.glob("closure-*.json"):
                value = _read_regular_json(path, description="closure record")
                validate_collaboration_contract(value)
                if value.get("review_package_id") == review["package_id"] and value.get(
                    "review_package_content_hash"
                ) == review["content_hash"]:
                    closure, closure_path = value, str(path)
    elif entry["closure"]["closure_id"]:
        path = Path(str(entry["closure"]["record_path"]))
        closure = _read_regular_json(path, description="closure record")
        validate_collaboration_contract(closure)
        try:
            review = load_review_package(root, str(closure["review_package_id"]))
        except ValueError:
            review = None
    if closure is None:
        reasons.append("git-private-closure-record-missing")
        final_oid = None
        closure_id = None
    else:
        closure_id = str(closure["closure_id"])
        final_oid = str(closure["final_oid"])
        if closure.get("closure_reason") != "integrated":
            reasons.append("closure-reason-is-not-integrated")
        if closure.get("original_workspace_path") and _norm(
            Path(str(closure["original_workspace_path"]))
        ) != _norm(selected_path):
            reasons.append("closure-workspace-path-does-not-match")
        try:
            current_target = resolve_integration_oid(root, str(closure["target_ref"]))
        except ValueError:
            current_target = None
        if current_target != final_oid:
            reasons.append("final-integration-target-oid-drifted")
        ancestry = _git(
            root,
            "merge-base",
            "--is-ancestor",
            str(closure["candidate_head"]),
            final_oid,
            check=False,
        )
        if ancestry.returncode:
            reasons.append("closure-candidate-is-not-ancestor-of-integration-oid")
    if review is None:
        reasons.append("review-package-evidence-missing")
    else:
        if closure is not None and review["content_hash"] != closure.get("review_package_content_hash"):
            reasons.append("review-package-content-hash-does-not-match-closure")
        if closure is not None and review["binding"]["candidate_head"] != closure.get(
            "candidate_head"
        ):
            reasons.append("review-candidate-head-does-not-match-closure")
        validations = list(review.get("evidence", {}).get("validations", []))
        if not validations or any(item.get("result") != "passed" for item in validations):
            reasons.append("passed-validation-evidence-missing")
        if closure is not None and not closure.get("decision_ids"):
            reasons.append("review-decision-evidence-missing")
        if closure is not None and not closure.get("validation_refs"):
            reasons.append("closure-validation-references-missing")
    candidate_head = (
        str(closure.get("candidate_head")) if closure is not None else str(git.get("head") or "")
    )
    if closure is not None and git.get("head") != candidate_head:
        reasons.append("workspace-head-does-not-match-closure-final-head")
    unique_commits: list[str] = []
    current_workspace_head = str(git.get("head") or "")
    if final_oid and git["available"] and current_workspace_head:
        unique = _git(
            selected_path, "rev-list", current_workspace_head, "--not", final_oid, check=False
        )
        if unique.returncode:
            reasons.append("unique-commit-check-failed")
        else:
            unique_commits = [item for item in str(unique.stdout).splitlines() if item]
            if unique_commits:
                reasons.append("workspace-has-commits-not-reachable-from-integration-oid")
    phase = entry["session"]["lifecycle_phase"]
    if phase not in {"integrated", "closed"}:
        reasons.append("workstream-session-is-not-integrated-or-closed")
    reasons = list(dict.fromkeys(reasons))
    base_eligible = not reasons
    branch = git.get("branch")
    worktree_action = base_eligible and entry["is_registered_worktree"] and not entry[
        "is_primary_worktree"
    ]
    local_branch_action = base_eligible and isinstance(branch, str) and branch.startswith("refs/heads/")
    ordinary_directory_action = base_eligible and not entry["is_registered_worktree"]
    action_eligibility = {
        "remove-worktree": worktree_action,
        "delete-local-branch": local_branch_action,
        "delete-remote-branch": False,
        "remove-directory": ordinary_directory_action,
    }
    action_reasons = {
        "remove-worktree": [] if worktree_action else ["registered-non-primary-worktree-gate-not-met"],
        "delete-local-branch": [] if local_branch_action else ["local-branch-gate-not-met"],
        "delete-remote-branch": ["remote-state-not-observed-network-free"],
        "remove-directory": [] if ordinary_directory_action else ["ordinary-directory-gate-not-met"],
    }
    actions: dict[str, Any] = {}
    for action in CLEANUP_ACTIONS:
        authorization_id = _authorization_id(
            workspace_id=str(entry["workspace_id"]),
            action=action,
            closure_id=closure_id,
            target_oid=final_oid,
        )
        actions[action] = {
            "eligible": action_eligibility[action],
            "authorized": action in requested,
            "authorization_id": authorization_id if action in requested else None,
            "authorization_required": True,
            "performed": False,
            "implies_actions": [],
            "reasons": action_reasons[action],
            "recommendation": (
                "quarantine-or-confirm-separately"
                if action_eligibility[action]
                else "do-not-perform"
            ),
        }
    return {
        "cleanup_schema_version": WORKSPACE_CLEANUP_SCHEMA_VERSION,
        "eligible": base_eligible,
        "reasons": reasons,
        "unknown": sorted(set(unknown)),
        "inventory_id": inventory["inventory_id"],
        "inventory_content_hash": inventory["content_hash"],
        "workspace": entry,
        "workstream_id": entry["session"]["workstream_id"],
        "candidate_head": candidate_head or None,
        "final_oid": final_oid,
        "closure_record": closure_path,
        "estimated_reclaim_bytes": entry["estimated_reclaim_bytes"],
        "unknown_ignored_paths": unknown_ignored,
        "allowlisted_ignored_paths": sorted(set(allowlisted_ignored) - set(sensitive)),
        "unique_commits": unique_commits,
        "actions": actions,
        "recommended_actions": [
            action for action, details in actions.items() if details["eligible"]
        ] or [entry["recommended_action"]],
        "automatic_deletion": False,
        "retention_deadline": None,
        "writes_performed": False,
        "network_performed": False,
    }


def record_cleanup_action_receipt(
    project_root: Path,
    *,
    closure_id: str,
    action: str,
    actor_id: str,
    authorization_id: str,
    evidence_refs: Sequence[str],
    occurred_at: str,
) -> dict[str, Any]:
    """Record a caller-attested external action; this function never performs that action."""
    root = _repository_root(project_root)
    if not _CLOSURE_ID.fullmatch(closure_id):
        raise ValueError("cleanup action receipt requires a valid closure ID")
    if action not in CLEANUP_ACTIONS:
        raise ValueError("cleanup action receipt uses an unsupported action")
    if not actor_id.strip() or not authorization_id.startswith("cleanup-authorization-"):
        raise ValueError("cleanup action receipt requires actor and explicit authorization ID")
    if not evidence_refs or any(not str(item).strip() for item in evidence_refs):
        raise ValueError("cleanup action receipt requires external action evidence")
    closure_path = _private_area(root, "closures") / f"{closure_id}.json"
    closure = _read_regular_json(closure_path, description="closure record")
    validate_collaboration_contract(closure)
    original_workspace_path = closure.get("original_workspace_path")
    if not isinstance(original_workspace_path, str) or not original_workspace_path:
        raise ValueError("closure record predates workspace action traceability")
    expected_authorization = _authorization_id(
        workspace_id=_entry_id(Path(original_workspace_path)),
        action=action,
        closure_id=closure_id,
        target_oid=str(closure["final_oid"]),
    )
    if authorization_id != expected_authorization:
        raise ValueError("cleanup action receipt authorization does not match closure and action")
    try:
        dt.datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("cleanup action receipt timestamp must be ISO 8601") from exc
    material = {
        "closure_id": closure_id,
        "original_workspace_path": original_workspace_path,
        "final_head": closure.get("final_head", closure["candidate_head"]),
        "integration_oid": closure.get("integration_oid", closure["final_oid"]),
        "review_package_id": closure["review_package_id"],
        "validation_refs": closure["validation_refs"],
        "workspace_classification": closure.get("workspace_classification", "integrated-closed"),
        "action": action,
        "actor_id": actor_id.strip(),
        "authorization_id": authorization_id,
        "evidence_refs": list(dict.fromkeys(str(item) for item in evidence_refs)),
        "occurred_at": occurred_at,
    }
    digest = hashlib.sha256(
        b"project-orrery-cleanup-action-receipt-v1\0"
        + json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt = {
        "receipt_schema_version": CLEANUP_ACTION_RECEIPT_SCHEMA_VERSION,
        "receipt_id": f"cleanup-action-{digest[:24]}",
        **material,
        "performed": True,
        "verification": "caller-attested-external-action",
        "storage": "git-private-common",
        "network_performed": False,
    }
    if not _RECEIPT_ID.fullmatch(receipt["receipt_id"]):
        raise AssertionError("cleanup action receipt ID generation failed")
    directory = _private_area(root, "closures", "actions", closure_id, create=True)
    path = directory / f"{receipt['receipt_id']}.json"
    from .review import _atomic_json

    _atomic_json(path, receipt)
    return {
        "receipt": receipt,
        "receipt_path": str(path),
        "destructive_action_performed": False,
        "writes_performed": True,
        "write_targets": ["git-private-cleanup-action-receipt"],
        "network_performed": False,
    }
