"""Versioned, Git-private Workstream relation contracts.

The module is dependency-free, performs no network I/O, and keeps relation
semantics separate from scheduling, UI layout, integration, and cleanup.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
import subprocess
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping, Sequence

from .subprocess_policy import no_window_options


RELATION_SCHEMA_VERSION = 1
ARCHIVE_LAYOUT_VERSION = 1
ARCHIVE_MAX_FILES = 128
ARCHIVE_MAX_FILE_BYTES = 64 * 1024
ARCHIVE_MAX_TOTAL_BYTES = 4 * 1024 * 1024
RELATION_TYPES = ("absorbs", "depends_on", "derived_from")
RELATION_LIFECYCLES = ("active", "cancelled", "completed", "proposed", "stale")
EVIDENCE_STATES = ("confirmed", "not-applicable", "rejected", "stale", "unknown")
HEAD_STATES = ("current", "stale", "unknown")
NODE_STATES = (
    "active", "blocked", "cancelled", "completed", "failed", "inactive",
    "review-pending", "stale", "unknown",
)
NODE_LIFECYCLE_PHASES = (
    "closed", "created", "implementing", "integrated", "investigating",
    "review-ready", "unknown", "validating",
)
NODE_RUNTIME_CONDITIONS = (
    "active", "blocked-by-conflict", "failed", "offline", "paused",
    "stale-unknown", "unknown", "waiting-for-user",
)
NODE_CLOSURE_REASONS = ("abandoned", "duplicate", "integrated", "superseded")
SOURCE_LINK_KINDS = ("git-commit", "other", "relation", "scope", "validation", "workstream-session")
RELATION_RECORD_KEYS = {
    "actor",
    "contract_type",
    "event_id",
    "evidence",
    "lifecycle",
    "origin",
    "reason",
    "recorded_at",
    "relation_id",
    "relation_type",
    "revision",
    "schema_version",
    "source_links",
    "source_workstream_id",
    "target_workstream_id",
    "writes_performed",
}
EVIDENCE_KEYS = {
    "ancestry_status",
    "dependency_status",
    "ownership_transfer_oid",
    "ownership_transfer_status",
    "scope_status",
    "source_head_oid",
    "source_head_status",
    "status",
    "target_head_oid",
    "target_head_status",
    "target_unique_commits_after_base",
    "task_base_oid",
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_OID = re.compile(r"^[0-9a-f]{40}$")
_ARCHIVE_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_ARCHIVE_ENTRY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}-[0-9a-f]{8,40}$")
_MAX_EVENT_BYTES = 256 * 1024
_FORBIDDEN_FIELD_NAMES = {
    "answer",
    "command",
    "credential",
    "diff_body",
    "password",
    "prompt",
    "secret",
    "shell",
    "source_body",
    "token",
    "transcript",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _run_git(repository: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
        **no_window_options(),
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return result


def _exact_commit(repository: Path, oid: str | None) -> bool:
    if oid is None or not _OID.fullmatch(oid):
        return False
    result = _run_git(repository, "rev-parse", "--verify", "--end-of-options", f"{oid}^{{commit}}", check=False)
    return result.returncode == 0 and result.stdout.strip().lower() == oid


def _is_ancestor(repository: Path, ancestor: str, descendant: str) -> bool:
    return _run_git(repository, "merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0


def _revision_count(repository: Path, base: str, head: str) -> int | None:
    result = _run_git(repository, "rev-list", "--count", f"{base}..{head}", check=False)
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def _validate_identifier(value: Any, label: str, *, filesystem_safe: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value) > 256 or any(ch in value for ch in "\r\n\0"):
        raise ValueError(f"{label} must be a non-empty bounded identifier")
    if filesystem_safe and not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must be filesystem-safe")
    return value


def _validate_oid(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _OID.fullmatch(value):
        raise ValueError(f"{label} must be null or an exact lowercase 40-character commit OID")
    return value


def _parse_timestamp(value: Any) -> None:
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("recorded_at must be a bounded RFC 3339 timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("recorded_at must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("recorded_at must include a timezone")


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN_FIELD_NAMES:
                raise ValueError(f"relation payload contains forbidden field: {key}")
            _reject_forbidden_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_fields(child)


def default_relation_evidence(**overrides: Any) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "status": "unknown",
        "source_head_oid": None,
        "target_head_oid": None,
        "task_base_oid": None,
        "ownership_transfer_oid": None,
        "source_head_status": "unknown",
        "target_head_status": "unknown",
        "scope_status": "unknown",
        "ancestry_status": "unknown",
        "dependency_status": "not-applicable",
        "ownership_transfer_status": "not-applicable",
        "target_unique_commits_after_base": None,
    }
    evidence.update(overrides)
    return evidence


def _normalize_source_links(source_links: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in source_links:
        if set(item) != {"kind", "ref"}:
            raise ValueError("source link must contain only kind and ref")
        kind = item.get("kind")
        reference = item.get("ref")
        if kind not in SOURCE_LINK_KINDS:
            raise ValueError(f"unsupported source link kind: {kind}")
        if (
            not isinstance(reference, str)
            or not reference
            or len(reference) > 512
            or any(character in reference for character in "\r\n\0")
        ):
            raise ValueError("source link ref must be non-empty and bounded")
        normalized.append({"kind": str(kind), "ref": reference})
    if len(normalized) > 64:
        raise ValueError("source link count exceeds 64")
    return sorted(normalized, key=lambda item: (item["kind"], item["ref"]))


def build_relation_record(
    *,
    relation_id: str,
    event_id: str,
    revision: int,
    relation_type: str,
    source_workstream_id: str,
    target_workstream_id: str,
    lifecycle: str,
    recorded_at: str,
    actor_kind: str,
    actor_id: str | None,
    origin: str,
    reason: str,
    evidence: Mapping[str, Any] | None = None,
    source_links: Sequence[Mapping[str, Any]] = (),
    writes_performed: bool = False,
) -> dict[str, Any]:
    record = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-record",
        "event_id": event_id,
        "relation_id": relation_id,
        "revision": revision,
        "relation_type": relation_type,
        "source_workstream_id": source_workstream_id,
        "target_workstream_id": target_workstream_id,
        "lifecycle": lifecycle,
        "recorded_at": recorded_at,
        "actor": {"kind": actor_kind, "actor_id": actor_id},
        "origin": origin,
        "reason": reason,
        "evidence": dict(evidence or default_relation_evidence()),
        "source_links": _normalize_source_links(source_links),
        "writes_performed": writes_performed,
    }
    validate_relation_record(record)
    return record


def validate_relation_record(record: Mapping[str, Any], *, project_root: Path | None = None) -> None:
    """Validate one relation event, optionally checking exact local Git evidence."""
    if set(record) != RELATION_RECORD_KEYS:
        raise ValueError("relation record fields do not match the v1 contract")
    _reject_forbidden_fields(record)
    if record.get("schema_version") != RELATION_SCHEMA_VERSION or record.get("contract_type") != "workstream-relation-record":
        raise ValueError("unsupported relation record contract")
    _validate_identifier(record.get("relation_id"), "relation_id", filesystem_safe=True)
    _validate_identifier(record.get("event_id"), "event_id", filesystem_safe=True)
    if not isinstance(record.get("revision"), int) or isinstance(record.get("revision"), bool) or record["revision"] < 1:
        raise ValueError("relation revision must be a positive integer")
    if record.get("relation_type") not in RELATION_TYPES:
        raise ValueError("unsupported relation type")
    source = _validate_identifier(record.get("source_workstream_id"), "source_workstream_id")
    target = _validate_identifier(record.get("target_workstream_id"), "target_workstream_id")
    if source == target:
        raise ValueError("Workstream relation cannot reference itself")
    if record.get("lifecycle") not in RELATION_LIFECYCLES:
        raise ValueError("unsupported relation lifecycle")
    _parse_timestamp(record.get("recorded_at"))
    actor = record.get("actor")
    if not isinstance(actor, Mapping) or set(actor) != {"kind", "actor_id"} or actor.get("kind") not in {"human", "tool", "import"}:
        raise ValueError("actor must match the v1 relation contract")
    if actor.get("actor_id") is not None:
        _validate_identifier(actor.get("actor_id"), "actor_id")
    if record.get("origin") not in {"native", "legacy-session-projection", "discovery"}:
        raise ValueError("unsupported relation origin")
    reason = record.get("reason")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2048:
        raise ValueError("relation reason must be non-empty and bounded")
    if not isinstance(record.get("writes_performed"), bool):
        raise ValueError("writes_performed must be boolean")
    links = record.get("source_links")
    if not isinstance(links, list) or links != _normalize_source_links(links):
        raise ValueError("source links must be a deterministically sorted list")
    evidence = record.get("evidence")
    if not isinstance(evidence, Mapping) or set(evidence) != EVIDENCE_KEYS:
        raise ValueError("relation evidence fields do not match the v1 contract")
    for key in ("status", "ancestry_status", "dependency_status", "ownership_transfer_status"):
        if evidence.get(key) not in EVIDENCE_STATES:
            raise ValueError(f"unsupported evidence state for {key}")
    for key in ("source_head_status", "target_head_status", "scope_status"):
        if evidence.get(key) not in HEAD_STATES:
            raise ValueError(f"unsupported head/scope state for {key}")
    for key in ("source_head_oid", "target_head_oid", "task_base_oid", "ownership_transfer_oid"):
        _validate_oid(evidence.get(key), key)
    count = evidence.get("target_unique_commits_after_base")
    if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count < 0):
        raise ValueError("target_unique_commits_after_base must be null or a non-negative integer")
    relation_type = record["relation_type"]
    if relation_type == "derived_from" and evidence.get("dependency_status") != "not-applicable":
        raise ValueError("derived_from cannot carry dependency evidence")
    if relation_type != "absorbs" and evidence.get("ownership_transfer_status") != "not-applicable":
        raise ValueError("only absorbs can carry ownership-transfer evidence")
    if relation_type != "absorbs" and evidence.get("ownership_transfer_oid") is not None:
        raise ValueError("only absorbs can carry an ownership-transfer OID")
    if relation_type != "derived_from" and evidence.get("task_base_oid") is not None:
        raise ValueError("only derived_from can carry a Git task-base OID")
    if relation_type != "derived_from" and evidence.get("ancestry_status") != "not-applicable":
        raise ValueError("only derived_from can carry Git ancestry evidence")
    if project_root is not None:
        repository = Path(project_root).expanduser().absolute()
        supplied = [
            evidence.get(key)
            for key in ("source_head_oid", "target_head_oid", "task_base_oid", "ownership_transfer_oid")
        ]
        for oid in supplied:
            if oid is not None and not _exact_commit(repository, oid):
                raise ValueError(f"relation evidence OID does not resolve exactly: {oid}")
        if relation_type == "derived_from" and evidence.get("ancestry_status") == "confirmed":
            base = evidence.get("task_base_oid")
            source_head = evidence.get("source_head_oid")
            if base is None or source_head is None or not _is_ancestor(repository, base, source_head):
                raise ValueError("confirmed derived_from ancestry is not supported by local Git")
            target_head = evidence.get("target_head_oid")
            target_count = evidence.get("target_unique_commits_after_base")
            if target_head is not None and target_count is not None:
                actual = _revision_count(repository, base, target_head)
                if actual is None or not _is_ancestor(repository, base, target_head) or actual != target_count:
                    raise ValueError("derived_from parent drift count is not supported by local Git")
        if relation_type == "absorbs" and evidence.get("ownership_transfer_status") == "confirmed":
            transfer = evidence.get("ownership_transfer_oid")
            target_head = evidence.get("target_head_oid")
            target_count = evidence.get("target_unique_commits_after_base")
            if transfer is None or target_head is None or target_count is None:
                raise ValueError("confirmed absorbs evidence requires an exact transfer point and drift count")
            actual = _revision_count(repository, transfer, target_head)
            if actual is None or not _is_ancestor(repository, transfer, target_head) or actual != target_count:
                raise ValueError("absorbs transfer drift count is not supported by local Git")


def relation_storage_root(project_root: Path) -> Path:
    root = Path(project_root).expanduser().absolute()
    result = _run_git(root, "rev-parse", "--git-common-dir")
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = root / common
    return Path(os.path.realpath(common)) / "orrery" / "workstream-relations"


def retired_session_archive_root(project_root: Path) -> Path:
    """Return the one allowed Git-common-private retired-session archive root."""
    root = Path(project_root).expanduser().absolute()
    result = _run_git(root, "rev-parse", "--git-common-dir")
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = root / common
    return Path(os.path.realpath(common)) / "orrery" / "retired-worktree-sessions"


def _is_reparse_or_symlink(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _validate_private_storage_ancestors(storage_root: Path) -> None:
    common_root = storage_root.parent.parent
    if storage_root != common_root / "orrery" / "workstream-relations":
        raise ValueError("relation storage escaped the Git common private boundary")
    for path in (common_root / "orrery", storage_root):
        if os.path.lexists(path) and (not path.is_dir() or _is_reparse_or_symlink(path)):
            raise ValueError("relation storage ancestors must be real directories")


def _validate_archive_storage_ancestors(archive_root: Path) -> None:
    common_root = archive_root.parent.parent
    if archive_root != common_root / "orrery" / "retired-worktree-sessions":
        raise ValueError("retired-session archive escaped the Git common private boundary")
    for path in (common_root / "orrery", archive_root):
        if os.path.lexists(path) and (not path.is_dir() or _is_reparse_or_symlink(path)):
            raise ValueError("retired-session archive ancestors must be real directories without symlink or reparse")


def _archive_directory_entries(path: Path, *, label: str) -> list[os.DirEntry[str]]:
    if not path.is_dir() or _is_reparse_or_symlink(path):
        raise ValueError(f"{label} must be a real directory without symlink or reparse")
    try:
        with os.scandir(path) as iterator:
            entries = sorted(list(iterator), key=lambda item: item.name)
    except OSError as exc:
        raise ValueError(f"cannot inspect {label}: {exc}") from exc
    if len(entries) > ARCHIVE_MAX_FILES * 4:
        raise ValueError("retired-session archive directory count limit exceeded")
    return entries


def _read_archive_regular_file(path: Path) -> bytes:
    if _is_reparse_or_symlink(path):
        raise ValueError("archive worktree.json must not be a symlink or reparse point")
    try:
        before = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot inspect archive worktree.json: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("archive worktree.json must be a regular file")
    if before.st_size > ARCHIVE_MAX_FILE_BYTES:
        raise ValueError("archive worktree.json exceeds the size limit")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("archive worktree.json must be a regular file")
        if opened.st_size > ARCHIVE_MAX_FILE_BYTES:
            raise ValueError("archive worktree.json exceeds the size limit")
        chunks: list[bytes] = []
        remaining = ARCHIVE_MAX_FILE_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > ARCHIVE_MAX_FILE_BYTES:
            raise ValueError("archive worktree.json exceeds the size limit")
        after = path.lstat()
        if (
            not stat.S_ISREG(after.st_mode)
            or after.st_size != opened.st_size
            or getattr(after, "st_ino", 0) != getattr(before, "st_ino", 0)
            or getattr(after, "st_dev", 0) != getattr(before, "st_dev", 0)
        ):
            raise ValueError("archive worktree.json changed while being read")
        return content
    except OSError as exc:
        raise ValueError(f"cannot read archive worktree.json safely: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _archive_session_files(project_root: Path) -> list[tuple[str, str, Path, bytes]]:
    archive_root = retired_session_archive_root(project_root)
    _validate_archive_storage_ancestors(archive_root)
    if not archive_root.exists():
        return []
    files: list[tuple[str, str, Path, bytes]] = []
    total_bytes = 0
    directory_count = 0
    for date_entry in _archive_directory_entries(archive_root, label="retired-session archive root"):
        date_path = Path(date_entry.path)
        if date_entry.is_symlink() or _is_reparse_or_symlink(date_path):
            raise ValueError("archive date entry must not be a symlink or reparse point")
        if not date_entry.is_dir(follow_symlinks=False) or not _ARCHIVE_DATE.fullmatch(date_entry.name):
            raise ValueError("retired-session archive contains an unsafe dated layout entry")
        try:
            dt.date.fromisoformat(date_entry.name)
        except ValueError as exc:
            raise ValueError("retired-session archive date entry is invalid") from exc
        directory_count += 1
        for session_entry in _archive_directory_entries(date_path, label="archive date directory"):
            session_path = Path(session_entry.path)
            if session_entry.is_symlink() or _is_reparse_or_symlink(session_path):
                raise ValueError("archive session entry must not be a symlink or reparse point")
            if (
                not session_entry.is_dir(follow_symlinks=False)
                or not _ARCHIVE_ENTRY.fullmatch(session_entry.name)
            ):
                raise ValueError("retired-session archive contains an unsafe archive entry")
            directory_count += 1
            children = _archive_directory_entries(session_path, label="archive session directory")
            if len(children) != 1 or children[0].name != "worktree.json":
                raise ValueError("archive session directory must contain exactly one worktree.json regular file")
            worktree_entry = children[0]
            worktree_path = Path(worktree_entry.path)
            if worktree_entry.is_symlink() or _is_reparse_or_symlink(worktree_path):
                raise ValueError("archive worktree.json must not be a symlink or reparse point")
            if not worktree_entry.is_file(follow_symlinks=False):
                raise ValueError("archive worktree.json must be a regular file")
            if len(files) >= ARCHIVE_MAX_FILES:
                raise ValueError("retired-session archive file count limit exceeded")
            content = _read_archive_regular_file(worktree_path)
            total_bytes += len(content)
            if total_bytes > ARCHIVE_MAX_TOTAL_BYTES:
                raise ValueError("retired-session archive aggregate size limit exceeded")
            files.append((date_entry.name, session_entry.name, worktree_path, content))
            if directory_count > ARCHIVE_MAX_FILES * 3:
                raise ValueError("retired-session archive directory count limit exceeded")
    return files


def _archive_branch_slug(branch_ref: str, *, separator: str) -> str:
    short = branch_ref.removeprefix("refs/heads/")
    return short.replace("/", separator)


def _decode_archive_session(content: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot decode archive session JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("archive session JSON must contain an object")
    if payload.get("schema_version") != 1 or payload.get("contract_type") != "workstream-session":
        raise ValueError("unsupported archived Workstream session schema or contract")
    try:
        from .collaboration import validate_collaboration_contract

        validate_collaboration_contract(payload)
    except (ImportError, ValueError) as exc:
        raise ValueError(f"malformed archived Workstream session: {exc}") from exc
    return payload


def _parse_archive_session(
    project_root: Path,
    *,
    entry_name: str,
    content: bytes,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(payload) if payload is not None else _decode_archive_session(content)
    workstream_id = _validate_identifier(payload.get("workstream_id"), "archived workstream_id")
    head = _validate_oid(payload.get("head"), "archived session HEAD")
    if head is None or not _exact_commit(project_root, head):
        raise ValueError("archived session HEAD does not resolve to an exact local commit")
    branch_ref = payload.get("branch")
    if (
        not isinstance(branch_ref, str)
        or not branch_ref.startswith("refs/heads/")
        or len(branch_ref) > 512
        or any(character in branch_ref for character in "\r\n\0")
    ):
        raise ValueError("archive branch must be a bounded local branch ref")
    branch_result = _run_git(
        project_root,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{branch_ref}^{{commit}}",
        check=False,
    )
    if branch_result.returncode != 0 or branch_result.stdout.strip().lower() != head:
        raise ValueError("archive branch does not resolve to the archived session HEAD")
    entry_slug, separator, head_prefix = entry_name.rpartition("-")
    if (
        not separator
        or len(head_prefix) < 8
        or len(head_prefix) > 40
        or not head.startswith(head_prefix)
        or entry_slug not in {
            _archive_branch_slug(branch_ref, separator="-"),
            _archive_branch_slug(branch_ref, separator="_"),
        }
    ):
        raise ValueError("archive entry identity does not match the archived branch and HEAD")
    lineage = payload.get("lineage")
    if isinstance(lineage, Mapping) and lineage.get("status") != "legacy-unknown":
        if lineage.get("validated_head") != head:
            raise ValueError("archived Workstream lineage HEAD is inconsistent with the session HEAD")
    semantic_hash = _digest(payload)
    eligible = (
        payload.get("lifecycle_phase") == "closed"
        and payload.get("runtime_condition") == "offline"
        and payload.get("evidence_freshness") == "current"
        and payload.get("closure_reason") == "superseded"
    )
    return {
        "workstream_id": workstream_id,
        "session": payload,
        "semantic_hash": semantic_hash,
        "byte_hash": hashlib.sha256(content).hexdigest(),
        "evidence_id": f"retired-session-archive:sha256:{semantic_hash}",
        "eligible": eligible,
    }


def load_archived_session_index(
    project_root: Path,
    *,
    referenced_workstream_ids: Sequence[str],
) -> dict[str, Any]:
    """Resolve only referenced, live-missing retired sessions without writing or networking."""
    repository = Path(project_root).expanduser().absolute()
    referenced = sorted({
        _validate_identifier(item, "referenced archived workstream_id")
        for item in referenced_workstream_ids
    })
    referenced_set = set(referenced)
    candidates: dict[str, list[dict[str, Any]]] = {}
    unreferenced_archive_count = 0
    for _date_name, _entry_name, _path, content in _archive_session_files(repository):
        candidate_header = _decode_archive_session(content)
        candidate_workstream_id = _validate_identifier(
            candidate_header.get("workstream_id"),
            "archived workstream_id",
        )
        if candidate_workstream_id not in referenced_set:
            unreferenced_archive_count += 1
            continue
        parsed = _parse_archive_session(
            repository,
            entry_name=_entry_name,
            content=content,
            payload=candidate_header,
        )
        candidates.setdefault(parsed["workstream_id"], []).append(parsed)
    resolved: list[dict[str, Any]] = []
    conflicts: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    for workstream_id in referenced:
        entries = candidates.get(workstream_id, [])
        if not entries:
            continue
        eligible = [entry for entry in entries if entry["eligible"]]
        semantic_hashes = sorted({entry["semantic_hash"] for entry in entries})
        if len(semantic_hashes) == 1 and eligible:
            selected = min(
                (entry for entry in eligible if entry["semantic_hash"] == semantic_hashes[0]),
                key=lambda item: (item["byte_hash"], item["evidence_id"]),
            )
            resolved.append({
                "workstream_id": workstream_id,
                "session": dict(selected["session"]),
                "origin": "retired-session-archive",
                "visibility": "git-private-local-only",
                "observability": "retired-archive-local",
                "evidence_id": selected["evidence_id"],
                "evidence_hash": selected["semantic_hash"],
                "equivalent_copy_count": len(eligible),
            })
            continue
        evidence_hash = _digest({
            "workstream_id": workstream_id,
            "semantic_hashes": semantic_hashes,
        })
        evidence_id = (
            f"retired-session-archive-conflict:sha256:{evidence_hash}"
            if len(semantic_hashes) > 1
            else f"retired-session-archive-unresolved:sha256:{evidence_hash}"
        )
        target = conflicts if len(semantic_hashes) > 1 else unresolved
        target.append({
            "workstream_id": workstream_id,
            "evidence_id": evidence_id,
            "evidence_hash": evidence_hash,
        })
    return {
        "schema_version": ARCHIVE_LAYOUT_VERSION,
        "contract_type": "retired-workstream-session-index",
        "storage": "git-common-private-read-only",
        "storage_ref": "git-common:orrery/retired-worktree-sessions:dated-entry-v1",
        "referenced_workstream_ids": referenced,
        "resolved_workstream_ids": [item["workstream_id"] for item in resolved],
        "conflicting_workstream_ids": [item["workstream_id"] for item in conflicts],
        "unresolved_workstream_ids": [item["workstream_id"] for item in unresolved],
        "resolved_sessions": resolved,
        "conflicts": conflicts,
        "unresolved": unresolved,
        "unreferenced_archive_count": unreferenced_archive_count,
        "read_only": True,
        "writes_performed": False,
        "network_performed": False,
        "execution_supported": False,
        "destructive_actions": [],
    }


def load_relation_history(project_root: Path) -> dict[str, Any]:
    """Read append-only native events without creating any path."""
    storage_root = relation_storage_root(project_root)
    _validate_private_storage_ancestors(storage_root)
    if not storage_root.exists():
        return {
            "storage": "git-common-private-append-only",
            "storage_ref": "git-common:orrery/workstream-relations",
            "histories": [],
            "current_records": [],
            "writes_performed": False,
        }
    if not storage_root.is_dir() or _is_reparse_or_symlink(storage_root):
        raise ValueError("relation storage root must be a real directory")
    histories: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    seen_events: set[str] = set()
    for relation_dir in sorted(storage_root.iterdir(), key=lambda path: path.name):
        if not relation_dir.is_dir() or _is_reparse_or_symlink(relation_dir) or not _SAFE_ID.fullmatch(relation_dir.name):
            raise ValueError("relation storage contains an unsafe relation directory")
        events: list[dict[str, Any]] = []
        for event_path in sorted(relation_dir.iterdir(), key=lambda path: path.name):
            if event_path.suffix != ".json" or not event_path.is_file() or _is_reparse_or_symlink(event_path):
                raise ValueError("relation storage contains a non-regular event")
            if event_path.stat().st_size > _MAX_EVENT_BYTES:
                raise ValueError("relation event exceeds the size limit")
            try:
                payload = json.loads(event_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"cannot read relation event {event_path.name}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError("relation event must contain a JSON object")
            validate_relation_record(payload, project_root=Path(project_root))
            if payload["relation_id"] != relation_dir.name:
                raise ValueError("relation event ID does not match its storage directory")
            if payload["event_id"] in seen_events:
                raise ValueError("duplicate relation event_id")
            seen_events.add(payload["event_id"])
            expected_name = f"{payload['revision']:08d}-{payload['event_id']}.json"
            if event_path.name != expected_name:
                raise ValueError("relation event filename does not match revision and event_id")
            events.append(payload)
        revisions = [event["revision"] for event in events]
        if revisions != list(range(1, len(events) + 1)):
            raise ValueError("relation history revisions must be contiguous from 1")
        if events:
            histories.append({"relation_id": relation_dir.name, "events": events})
            current.append(events[-1])
    return {
        "storage": "git-common-private-append-only",
        "storage_ref": "git-common:orrery/workstream-relations",
        "histories": histories,
        "current_records": sorted(current, key=_record_sort_key),
        "writes_performed": False,
    }


def append_proposed_relation(
    project_root: Path,
    *,
    relation_id: str,
    relation_type: str,
    source_workstream_id: str,
    target_workstream_id: str,
    reason: str,
    actor_id: str,
    recorded_at: str | None = None,
    evidence: Mapping[str, Any] | None = None,
    source_links: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Append revision 1 of one explicitly proposed native relation."""
    _validate_identifier(relation_id, "relation_id", filesystem_safe=True)
    timestamp = recorded_at or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    event_seed = {
        "relation_id": relation_id,
        "relation_type": relation_type,
        "source": source_workstream_id,
        "target": target_workstream_id,
        "recorded_at": timestamp,
    }
    event_id = f"event-{_digest(event_seed)[:24]}"
    record = build_relation_record(
        relation_id=relation_id,
        event_id=event_id,
        revision=1,
        relation_type=relation_type,
        source_workstream_id=source_workstream_id,
        target_workstream_id=target_workstream_id,
        lifecycle="proposed",
        recorded_at=timestamp,
        actor_kind="human",
        actor_id=actor_id,
        origin="native",
        reason=reason,
        evidence=evidence or default_relation_evidence(
            ancestry_status="unknown" if relation_type == "derived_from" else "not-applicable",
            dependency_status="unknown" if relation_type == "depends_on" else "not-applicable",
            ownership_transfer_status="unknown" if relation_type == "absorbs" else "not-applicable",
        ),
        source_links=source_links,
        writes_performed=True,
    )
    validate_relation_record(record, project_root=Path(project_root))
    storage_root = relation_storage_root(project_root)
    _validate_private_storage_ancestors(storage_root)
    relation_dir = storage_root / relation_id
    if os.path.lexists(relation_dir):
        raise ValueError("relation_id already has append-only history")
    relation_dir.mkdir(parents=True, exist_ok=False)
    event_path = relation_dir / f"00000001-{event_id}.json"
    descriptor: int | None = None
    try:
        descriptor = os.open(event_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = None
            json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        event_path.unlink(missing_ok=True)
        try:
            relation_dir.rmdir()
        except OSError:
            pass
        raise ValueError(f"cannot append proposed relation: {exc}") from exc
    return {
        "record": record,
        "storage": "git-common-private-append-only",
        "storage_ref": "git-common:orrery/workstream-relations",
        "writes_performed": True,
        "destructive_actions": [],
    }


def append_relation_event(project_root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    """Append one exact full-state revision without replacing relation history."""
    payload = dict(record)
    validate_relation_record(payload, project_root=Path(project_root))
    if payload.get("writes_performed") is not True:
        raise ValueError("appended relation event must declare writes_performed=true")
    storage_root = relation_storage_root(project_root)
    _validate_private_storage_ancestors(storage_root)
    relation_dir = storage_root / payload["relation_id"]
    created_relation_dir = False
    if relation_dir.exists():
        if not relation_dir.is_dir() or _is_reparse_or_symlink(relation_dir):
            raise ValueError("relation history directory must be a real directory")
        history = next(
            (item for item in load_relation_history(project_root)["histories"]
             if item["relation_id"] == payload["relation_id"]),
            None,
        )
        if history is None or not history["events"]:
            raise ValueError("existing relation history is unreadable")
        previous = history["events"][-1]
        if payload["revision"] != previous["revision"] + 1:
            raise ValueError("relation event revision does not continue exact history")
        for key in ("relation_type", "source_workstream_id", "target_workstream_id"):
            if payload[key] != previous[key]:
                raise ValueError("relation event cannot change the immutable edge identity")
    else:
        if payload["revision"] != 1:
            raise ValueError("new relation history must begin at revision 1")
        relation_dir.mkdir(parents=True, exist_ok=False)
        created_relation_dir = True
    event_path = relation_dir / f"{payload['revision']:08d}-{payload['event_id']}.json"
    descriptor: int | None = None
    try:
        descriptor = os.open(event_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = None
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        if created_relation_dir:
            try:
                relation_dir.rmdir()
            except OSError:
                pass
        raise ValueError(f"cannot append relation event: {exc}") from exc
    return {
        "record": payload,
        "event_path": str(event_path),
        "storage": "git-common-private-append-only",
        "writes_performed": True,
        "destructive_actions": [],
    }


def _record_sort_key(record: Mapping[str, Any]) -> tuple[str, str, str, str, int]:
    return (
        str(record.get("source_workstream_id", "")),
        str(record.get("target_workstream_id", "")),
        str(record.get("relation_type", "")),
        str(record.get("relation_id", "")),
        int(record.get("revision", 0)),
    )


def _worktree_paths(project_root: Path) -> list[Path]:
    result = _run_git(Path(project_root), "worktree", "list", "--porcelain")
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line.removeprefix("worktree ")))
    return sorted(paths, key=lambda path: os.path.normcase(os.path.realpath(path)))


def _archived_node_from_session(session: Mapping[str, Any], evidence_id: str) -> dict[str, Any]:
    node = _node_from_session(session, "current")
    node.update({
        "visibility": "git-private-local-only",
        "observability": "retired-archive-local",
        "source_links": [{"kind": "workstream-session", "ref": evidence_id}],
        "origin": "legacy-session-projection",
    })
    return node


def _unresolved_archive_node(workstream_id: str, evidence_id: str) -> dict[str, Any]:
    return {
        "workstream_id": workstream_id,
        "status": "unknown",
        "session_state": "unknown",
        "lifecycle_phase": "unknown",
        "runtime_condition": "unknown",
        "evidence_freshness": "unknown",
        "head_oid": None,
        "scope_status": "unknown",
        "closure_reason": None,
        "primary_subsystem_id": "unknown",
        "affected_subsystem_ids": [],
        "visibility": "git-private-local-only",
        "observability": "retired-archive-conflict-unknown",
        "source_links": [{"kind": "other", "ref": evidence_id}],
        "origin": "relation-only",
    }


def load_legacy_session_projection(
    project_root: Path,
    *,
    additional_referenced_workstream_ids: Sequence[str] = (),
    include_archived: bool = True,
) -> dict[str, Any]:
    """Project W5D lineage sessions read-only; never writes relation storage or sessions."""
    from .collaboration import inspect_worktree_status

    live_sessions: dict[str, tuple[dict[str, Any], str]] = {}
    for worktree in _worktree_paths(project_root):
        if not worktree.is_dir():
            continue
        try:
            status = inspect_worktree_status(worktree)
        except ValueError:
            continue
        session = status.get("session", {})
        record = session.get("record")
        if isinstance(record, dict) and isinstance(record.get("workstream_id"), str):
            live_sessions[record["workstream_id"]] = (record, str(session.get("state", "stale")))
    referenced = {
        _validate_identifier(item, "additional referenced workstream_id")
        for item in additional_referenced_workstream_ids
    }
    for record, _state in live_sessions.values():
        lineage = record.get("lineage")
        if isinstance(lineage, Mapping) and lineage.get("base_workstream_id") is not None:
            referenced.add(_validate_identifier(lineage["base_workstream_id"], "legacy parent workstream"))
    missing_referenced = sorted(referenced - set(live_sessions))
    sessions = dict(live_sessions)
    archived_node_map: dict[str, dict[str, Any]] = {}
    archive_resolution: dict[str, Any] | None = None
    if include_archived and missing_referenced:
        archive_resolution = load_archived_session_index(
            project_root,
            referenced_workstream_ids=missing_referenced,
        )
        for item in archive_resolution["resolved_sessions"]:
            session_record = dict(item["session"])
            workstream_id = str(item["workstream_id"])
            sessions[workstream_id] = (session_record, "current")
            archived_node_map[workstream_id] = _archived_node_from_session(
                session_record,
                str(item["evidence_id"]),
            )
        for item in [*archive_resolution["conflicts"], *archive_resolution["unresolved"]]:
            archived_node_map[str(item["workstream_id"])] = _unresolved_archive_node(
                str(item["workstream_id"]),
                str(item["evidence_id"]),
            )
    nodes = [
        archived_node_map.get(workstream_id, _node_from_session(record, state))
        for workstream_id, (record, state) in sessions.items()
    ]
    for workstream_id, node in archived_node_map.items():
        if workstream_id not in sessions:
            nodes.append(node)
    relations: list[dict[str, Any]] = []
    for record, state in live_sessions.values():
        lineage = record.get("lineage")
        if not isinstance(lineage, Mapping) or lineage.get("base_workstream_id") is None:
            continue
        parent = sessions.get(str(lineage["base_workstream_id"]))
        relations.append(
            project_legacy_session_relation(
                record,
                session_state=state,
                parent_session=parent[0] if parent is not None else None,
                parent_state=parent[1] if parent is not None else "unknown",
                project_root=Path(project_root),
            )
        )
    return {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-legacy-relation-projection",
        "records": sorted(relations, key=_record_sort_key),
        "nodes": sorted(nodes, key=lambda item: item["workstream_id"]),
        "writes_performed": False,
        "storage_writes_performed": False,
    }


def project_legacy_session_relation(
    session: Mapping[str, Any],
    *,
    session_state: str,
    parent_session: Mapping[str, Any] | None,
    parent_state: str,
    project_root: Path,
) -> dict[str, Any]:
    lineage = session.get("lineage")
    if not isinstance(lineage, Mapping):
        raise ValueError("legacy session does not contain lineage")
    source = _validate_identifier(session.get("workstream_id"), "legacy source workstream")
    target = _validate_identifier(lineage.get("base_workstream_id"), "legacy parent workstream")
    base = _validate_oid(lineage.get("task_base_oid"), "legacy task_base_oid")
    source_head = _validate_oid(session.get("head"), "legacy source HEAD")
    parent_head = None if parent_session is None else _validate_oid(parent_session.get("head"), "legacy parent HEAD")
    exact_source = _exact_commit(project_root, source_head)
    exact_base = _exact_commit(project_root, base)
    ancestry = exact_source and exact_base and _is_ancestor(project_root, str(base), str(source_head))
    source_current = session_state == "current" and lineage.get("validated_head") == source_head
    target_current = parent_session is not None and parent_state == "current" and parent_head == base
    target_count = None
    if parent_head is not None and base is not None and _exact_commit(project_root, parent_head) and exact_base:
        target_count = _revision_count(project_root, base, parent_head)
    if not source_current or (parent_session is not None and not target_current):
        lifecycle = "stale"
        evidence_status = "stale"
    elif ancestry and target_current:
        lifecycle = "active"
        evidence_status = "confirmed"
    else:
        lifecycle = "proposed"
        evidence_status = "unknown"
    relation_hash = _digest({"source": source, "target": target, "base": base})[:24]
    return build_relation_record(
        relation_id=f"legacy-{relation_hash}",
        event_id=f"legacy-{relation_hash}",
        revision=1,
        relation_type="derived_from",
        source_workstream_id=source,
        target_workstream_id=target,
        lifecycle=lifecycle,
        recorded_at=str(session.get("captured_at", "1970-01-01T00:00:00Z")),
        actor_kind="import",
        actor_id=None,
        origin="legacy-session-projection",
        reason="read-only projection of explicit legacy stacked lineage",
        evidence=default_relation_evidence(
            status=evidence_status,
            source_head_oid=source_head,
            target_head_oid=parent_head or base,
            task_base_oid=base,
            source_head_status="current" if source_current else "stale",
            target_head_status=("current" if target_current else "stale" if parent_session is not None else "unknown"),
            scope_status="current" if session_state == "current" else "stale",
            ancestry_status="confirmed" if ancestry else "unknown",
            target_unique_commits_after_base=target_count,
        ),
        source_links=[{"kind": "workstream-session", "ref": f"git-private:{source}"}],
        writes_performed=False,
    )


def _derive_node_status(
    *,
    session_state: str,
    lifecycle_phase: str,
    runtime_condition: str,
    evidence_freshness: str,
    scope_status: str,
    closure_reason: str | None,
) -> str:
    if session_state != "current":
        return "stale" if session_state == "stale" else "unknown"
    if lifecycle_phase == "integrated":
        return "completed"
    if lifecycle_phase == "closed":
        return "cancelled" if closure_reason in {"abandoned", "duplicate"} else "completed"
    if runtime_condition == "blocked-by-conflict":
        return "blocked"
    if runtime_condition == "failed":
        return "failed"
    if runtime_condition in {"waiting-for-user", "paused"}:
        return "inactive"
    if runtime_condition in {"stale-unknown", "offline", "unknown"}:
        return "unknown"
    if evidence_freshness != "current" or scope_status != "current":
        return "stale" if "stale" in {evidence_freshness, scope_status} else "unknown"
    if lifecycle_phase == "review-ready" and runtime_condition == "active":
        return "review-pending"
    if lifecycle_phase == "unknown":
        return "unknown"
    return "active"


def _node_from_session(session: Mapping[str, Any], session_state: str) -> dict[str, Any]:
    lifecycle = str(session.get("lifecycle_phase", "unknown"))
    if lifecycle not in NODE_LIFECYCLE_PHASES:
        lifecycle = "unknown"
    runtime = str(session.get("runtime_condition", "unknown"))
    if runtime not in NODE_RUNTIME_CONDITIONS:
        runtime = "unknown"
    evidence_freshness = str(session.get("evidence_freshness", "unknown"))
    if evidence_freshness not in HEAD_STATES:
        evidence_freshness = "unknown"
    normalized_session_state = session_state if session_state in HEAD_STATES else "unknown"
    scope_status = "current" if normalized_session_state == "current" else normalized_session_state
    closure_reason = session.get("closure_reason")
    if closure_reason not in (*NODE_CLOSURE_REASONS, None):
        closure_reason = None
    primary_subsystem = session.get("primary_subsystem_id", "unknown")
    if not isinstance(primary_subsystem, str) or not primary_subsystem:
        primary_subsystem = "unknown"
    affected = session.get("affected_subsystem_ids", [])
    if not isinstance(affected, list):
        affected = []
    status = _derive_node_status(
        session_state=normalized_session_state,
        lifecycle_phase=lifecycle,
        runtime_condition=runtime,
        evidence_freshness=evidence_freshness,
        scope_status=scope_status,
        closure_reason=closure_reason,
    )
    return {
        "workstream_id": str(session["workstream_id"]),
        "status": status,
        "session_state": normalized_session_state,
        "lifecycle_phase": lifecycle,
        "runtime_condition": runtime,
        "evidence_freshness": evidence_freshness,
        "head_oid": session.get("head"),
        "scope_status": scope_status,
        "closure_reason": closure_reason,
        "primary_subsystem_id": primary_subsystem,
        "affected_subsystem_ids": sorted(set(str(item) for item in affected)),
        "visibility": str(session.get("visibility", "unknown")),
        "observability": str(session.get("observability", "unknown")),
        "source_links": [{"kind": "workstream-session", "ref": f"git-private:{session['workstream_id']}"}],
        "origin": "legacy-session-projection",
    }


def _normalize_node(node: Mapping[str, Any]) -> dict[str, Any]:
    workstream_id = _validate_identifier(node.get("workstream_id"), "node workstream_id")
    session_state = node.get("session_state", "unknown")
    lifecycle_phase = node.get("lifecycle_phase", "unknown")
    runtime_condition = node.get("runtime_condition", "unknown")
    evidence_freshness = node.get("evidence_freshness", "unknown")
    scope_status = node.get("scope_status", "unknown")
    if (
        session_state not in HEAD_STATES
        or lifecycle_phase not in NODE_LIFECYCLE_PHASES
        or runtime_condition not in NODE_RUNTIME_CONDITIONS
        or evidence_freshness not in HEAD_STATES
        or scope_status not in HEAD_STATES
    ):
        raise ValueError("node status fields do not match the v1 graph contract")
    head = _validate_oid(node.get("head_oid"), "node head_oid")
    closure_reason = node.get("closure_reason")
    if closure_reason not in (*NODE_CLOSURE_REASONS, None):
        raise ValueError("node closure_reason does not match the v1 graph contract")
    if (lifecycle_phase == "closed") != (closure_reason is not None):
        raise ValueError("node closed lifecycle and closure_reason disagree")
    status = _derive_node_status(
        session_state=session_state,
        lifecycle_phase=lifecycle_phase,
        runtime_condition=runtime_condition,
        evidence_freshness=evidence_freshness,
        scope_status=scope_status,
        closure_reason=closure_reason,
    )
    if node.get("status", status) != status:
        raise ValueError("node status does not match its independent state axes")
    primary_subsystem_id = _validate_identifier(
        node.get("primary_subsystem_id", "unknown"), "node primary_subsystem_id", filesystem_safe=True
    )
    affected = node.get("affected_subsystem_ids", [])
    if not isinstance(affected, list):
        raise ValueError("node affected_subsystem_ids must be a list")
    affected_subsystem_ids = sorted({
        _validate_identifier(item, "node affected_subsystem_id", filesystem_safe=True) for item in affected
    })
    visibility = _validate_identifier(node.get("visibility", "unknown"), "node visibility", filesystem_safe=True)
    observability = _validate_identifier(node.get("observability", "unknown"), "node observability", filesystem_safe=True)
    origin = node.get("origin", "relation-only")
    if origin not in {"native", "legacy-session-projection", "relation-only", "discovery"}:
        raise ValueError("unsupported node origin")
    normalized = {
        "workstream_id": workstream_id,
        "status": status,
        "session_state": session_state,
        "lifecycle_phase": lifecycle_phase,
        "runtime_condition": runtime_condition,
        "evidence_freshness": evidence_freshness,
        "head_oid": head,
        "scope_status": scope_status,
        "closure_reason": closure_reason,
        "primary_subsystem_id": primary_subsystem_id,
        "affected_subsystem_ids": affected_subsystem_ids,
        "visibility": visibility,
        "observability": observability,
        "source_links": _normalize_source_links(node.get("source_links", [])),
        "origin": origin,
    }
    return normalized


def _graph_diagnostics(
    records: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    effective = [record for record in records if record["lifecycle"] not in {"cancelled", "stale"}]
    triples: dict[tuple[str, str, str], list[str]] = {}
    parents: dict[str, list[str]] = {}
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for record in effective:
        triple = (record["relation_type"], record["source_workstream_id"], record["target_workstream_id"])
        triples.setdefault(triple, []).append(record["relation_id"])
        if record["relation_type"] == "derived_from":
            parents.setdefault(record["source_workstream_id"], []).append(record["relation_id"])
        adjacency.setdefault(record["source_workstream_id"], []).append(
            (record["target_workstream_id"], record["relation_id"])
        )
    for triple, relation_ids in sorted(triples.items()):
        if len(relation_ids) > 1:
            errors.append({"code": "duplicate-edge", "edge": list(triple), "relation_ids": sorted(relation_ids)})
    for source, relation_ids in sorted(parents.items()):
        if len(relation_ids) > 1:
            errors.append({"code": "multiple-primary-git-parents", "workstream_id": source, "relation_ids": sorted(relation_ids)})
    visited: set[str] = set()
    active: set[str] = set()
    stack_nodes: list[str] = []
    stack_edges: list[str] = []

    def visit(node: str) -> None:
        if node in active:
            start = stack_nodes.index(node)
            errors.append({
                "code": "relation-cycle",
                "workstream_ids": stack_nodes[start:] + [node],
                "relation_ids": stack_edges[start:],
            })
            return
        if node in visited:
            return
        active.add(node)
        stack_nodes.append(node)
        for target, relation_id in sorted(adjacency.get(node, [])):
            stack_edges.append(relation_id)
            visit(target)
            stack_edges.pop()
        stack_nodes.pop()
        active.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)
    for record in records:
        if record["relation_type"] in {"derived_from", "absorbs"} and record["lifecycle"] == "completed":
            predecessor = nodes.get(record["target_workstream_id"])
            if (
                predecessor is None
                or predecessor.get("lifecycle_phase") != "closed"
                or predecessor.get("closure_reason") != "superseded"
            ):
                errors.append({
                    "code": "completed-takeover-predecessor-not-closed-superseded",
                    "relation_id": record["relation_id"],
                    "predecessor_workstream_id": record["target_workstream_id"],
                })
        if (
            record["relation_type"] in {"derived_from", "absorbs"}
            and record["lifecycle"] == "active"
            and not _relation_is_effective(record, None)[0]
        ):
            warnings.append({"code": "active-relation-evidence-insufficient", "relation_id": record["relation_id"]})
    errors.sort(key=_canonical_bytes)
    warnings.sort(key=_canonical_bytes)
    return errors, warnings


def _node_is_active(node: Mapping[str, Any]) -> bool:
    return (
        node.get("status") in {"active", "review-pending"}
        and node.get("session_state") == "current"
        and node.get("runtime_condition") == "active"
        and node.get("evidence_freshness") == "current"
        and node.get("scope_status") == "current"
        and node.get("lifecycle_phase") not in {"integrated", "closed", "unknown"}
    )


def _relation_is_effective(record: Mapping[str, Any], nodes: Mapping[str, Mapping[str, Any]] | None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if record["lifecycle"] != "active":
        reasons.append("relation-not-active")
    if record["relation_type"] not in {"derived_from", "absorbs"}:
        reasons.append("not-a-succession-relation")
    evidence = record["evidence"]
    if evidence["status"] != "confirmed":
        reasons.append("evidence-not-confirmed")
    if evidence["source_head_status"] != "current" or evidence["target_head_status"] != "current":
        reasons.append("head-stale-or-unknown")
    if evidence["scope_status"] != "current":
        reasons.append("scope-stale-or-unknown")
    if evidence["target_unique_commits_after_base"] != 0:
        reasons.append("target-unique-commits-or-unknown")
    if record["relation_type"] == "derived_from":
        if evidence["ancestry_status"] != "confirmed":
            reasons.append("ancestry-not-confirmed")
        if evidence["task_base_oid"] is None or evidence["target_head_oid"] != evidence["task_base_oid"]:
            reasons.append("task-base-target-mismatch")
    if record["relation_type"] == "absorbs" and evidence["ownership_transfer_status"] != "confirmed":
        reasons.append("ownership-transfer-not-confirmed")
    if record["relation_type"] == "absorbs":
        if evidence["ownership_transfer_oid"] is None or evidence["target_head_oid"] != evidence["ownership_transfer_oid"]:
            reasons.append("ownership-transfer-target-mismatch")
    if nodes is not None:
        source = nodes.get(record["source_workstream_id"])
        target = nodes.get(record["target_workstream_id"])
        endpoints = (source, target)
        if source is None or target is None or any(
            node.get("session_state") != "current"
            or node.get("evidence_freshness") != "current"
            or node.get("scope_status") != "current"
            for node in endpoints if node is not None
        ):
            reasons.append("endpoint-not-current")
        else:
            if evidence["source_head_oid"] != source.get("head_oid") or evidence["target_head_oid"] != target.get("head_oid"):
                reasons.append("endpoint-head-drift")
            if target.get("runtime_condition") != "paused":
                reasons.append("predecessor-not-marked-inactive")
            if target.get("lifecycle_phase") in {"integrated", "closed", "unknown"}:
                reasons.append("predecessor-lifecycle-not-active-takeover")
    return not reasons, sorted(set(reasons))


def build_relation_graph(
    records: Sequence[Mapping[str, Any]],
    *,
    nodes: Sequence[Mapping[str, Any]] = (),
    pair_constraints: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    def unknown_node(workstream_id: str) -> dict[str, Any]:
        return _normalize_node({"workstream_id": workstream_id})

    normalized_records: list[dict[str, Any]] = []
    for record in records:
        validate_relation_record(record)
        normalized_records.append(dict(record))
    normalized_records.sort(key=_record_sort_key)
    node_map = {node["workstream_id"]: node for node in (_normalize_node(item) for item in nodes)}
    for record in normalized_records:
        for workstream_id in (record["source_workstream_id"], record["target_workstream_id"]):
            node_map.setdefault(workstream_id, unknown_node(workstream_id))
    normalized_constraints: list[dict[str, Any]] = []
    for item in pair_constraints:
        left = _validate_identifier(item.get("left_workstream_id"), "constraint left workstream")
        right = _validate_identifier(item.get("right_workstream_id"), "constraint right workstream")
        if left == right:
            raise ValueError("pair constraint cannot reference the same Workstream")
        reasons = item.get("reasons")
        if not isinstance(reasons, list) or not reasons or any(not isinstance(reason, str) or not reason for reason in reasons):
            raise ValueError("pair constraint reasons must be a non-empty string list")
        ordered = sorted((left, right))
        for workstream_id in ordered:
            node_map.setdefault(workstream_id, unknown_node(workstream_id))
        normalized_constraints.append({"left_workstream_id": ordered[0], "right_workstream_id": ordered[1], "reasons": sorted(set(reasons))})
    normalized_constraints.sort(key=lambda item: (item["left_workstream_id"], item["right_workstream_id"], item["reasons"]))
    errors, warnings = _graph_diagnostics(normalized_records, node_map)
    edges: list[dict[str, Any]] = []
    for record in normalized_records:
        effective, reasons = _relation_is_effective(record, node_map)
        edge = dict(record)
        edge["effective_active_succession"] = effective and not errors
        edge["evidence_reason_codes"] = reasons
        edges.append(edge)
    taken_over = {
        edge["target_workstream_id"] for edge in edges if edge["effective_active_succession"]
    }
    active_tips = sorted(
        workstream_id for workstream_id, node in node_map.items() if _node_is_active(node) and workstream_id not in taken_over
    )
    unknown = sorted(
        workstream_id for workstream_id, node in node_map.items()
        if (
            node["status"] in {"unknown", "stale"}
            or node["session_state"] in {"unknown", "stale"}
            or node["evidence_freshness"] in {"unknown", "stale"}
            or node["scope_status"] in {"unknown", "stale"}
        )
    )
    body = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-graph",
        "nodes": sorted(node_map.values(), key=lambda item: item["workstream_id"]),
        "edges": edges,
        "pair_constraints": normalized_constraints,
        "active_tip_workstream_ids": active_tips,
        "unknown_workstream_ids": unknown,
        "validation": {"valid": not errors, "errors": errors, "warnings": warnings},
        "read_only": True,
        "writes_performed": False,
    }
    body["graph_hash"] = _digest(body)
    return body


def load_relation_graph(
    project_root: Path,
    *,
    include_legacy: bool = True,
    allow_incomplete_transactions: bool = False,
) -> dict[str, Any]:
    if not allow_incomplete_transactions:
        try:
            from .workstream_relation_execution import assert_no_incomplete_transactions
        except ImportError:
            assert_no_incomplete_transactions = None
        if assert_no_incomplete_transactions is not None:
            assert_no_incomplete_transactions(Path(project_root))
    native = load_relation_history(project_root)
    records = list(native["current_records"])
    nodes: list[dict[str, Any]] = []
    if include_legacy:
        native_endpoints = sorted({
            workstream_id
            for record in records
            for workstream_id in (record["source_workstream_id"], record["target_workstream_id"])
        })
        legacy = load_legacy_session_projection(
            project_root,
            additional_referenced_workstream_ids=native_endpoints,
            include_archived=True,
        )
        native_triples = {
            (record["relation_type"], record["source_workstream_id"], record["target_workstream_id"])
            for record in records
        }
        records.extend(
            record for record in legacy["records"]
            if (record["relation_type"], record["source_workstream_id"], record["target_workstream_id"]) not in native_triples
        )
        nodes.extend(legacy["nodes"])
    graph = build_relation_graph(records, nodes=nodes)
    graph["storage"] = native["storage"]
    graph["storage_ref"] = native["storage_ref"]
    graph["legacy_projection_included"] = include_legacy
    graph["graph_hash"] = _digest({key: value for key, value in graph.items() if key != "graph_hash"})
    return graph


def build_succession_plan(graph: Mapping[str, Any]) -> dict[str, Any]:
    if graph.get("contract_type") != "workstream-relation-graph":
        raise ValueError("succession plan requires a v1 relation graph")
    nodes = {node["workstream_id"]: node for node in graph.get("nodes", [])}
    candidate_ids = sorted(
        workstream_id for workstream_id, node in nodes.items() if node.get("status") not in {"cancelled", "completed"}
    )
    active_tip_ids = sorted(set(graph.get("active_tip_workstream_ids", [])) & set(candidate_ids))
    effective_edges = [edge for edge in graph.get("edges", []) if edge.get("effective_active_succession")]
    adjacency: dict[str, set[str]] = {}
    parents_by_target: dict[str, set[str]] = {}
    for edge in effective_edges:
        adjacency.setdefault(edge["source_workstream_id"], set()).add(edge["target_workstream_id"])
        parents_by_target.setdefault(edge["target_workstream_id"], set()).add(edge["source_workstream_id"])
    constraints = {
        tuple(sorted((item["left_workstream_id"], item["right_workstream_id"]))): item["reasons"]
        for item in graph.get("pair_constraints", [])
    }

    def path_exists(source: str, target: str) -> bool:
        pending = [source]
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current == target:
                return True
            if current in seen:
                continue
            seen.add(current)
            pending.extend(sorted(adjacency.get(current, set()), reverse=True))
        return False

    relevant_pairs = {tuple(pair) for pair in combinations(active_tip_ids, 2)}
    for pair in constraints:
        if pair[0] in nodes and pair[1] in nodes:
            relevant_pairs.add(pair)
    for edge in graph.get("edges", []):
        pair = tuple(sorted((edge["source_workstream_id"], edge["target_workstream_id"])))
        if pair[0] not in nodes or pair[1] not in nodes:
            continue
        endpoints = (nodes[pair[0]], nodes[pair[1]])
        endpoint_unknown = any(
            node.get("status") in {"stale", "unknown"}
            or node.get("session_state") in {"stale", "unknown"}
            or node.get("evidence_freshness") in {"stale", "unknown"}
            or node.get("scope_status") in {"stale", "unknown"}
            for node in endpoints
        )
        dependency_visible = edge["relation_type"] == "depends_on" and edge["lifecycle"] in {"proposed", "active", "stale"}
        uncertain_succession = (
            edge["relation_type"] in {"derived_from", "absorbs"}
            and edge["lifecycle"] not in {"cancelled", "completed"}
            and not edge.get("effective_active_succession")
        )
        invalid_completed_takeover = (
            edge["relation_type"] in {"derived_from", "absorbs"}
            and edge["lifecycle"] == "completed"
            and any(
                item.get("code") == "completed-takeover-predecessor-not-closed-superseded"
                and item.get("relation_id") == edge["relation_id"]
                for item in graph.get("validation", {}).get("errors", [])
            )
        )
        if endpoint_unknown or dependency_visible or uncertain_succession or invalid_completed_takeover:
            relevant_pairs.add(pair)

    compare_pairs: list[dict[str, Any]] = []
    suppress_pairs: list[dict[str, Any]] = []
    for left, right in combinations(candidate_ids, 2):
        pair = (left, right)
        constraint_reasons = list(constraints.get(pair, []))
        connected = path_exists(left, right) or path_exists(right, left)
        if connected and pair not in relevant_pairs and graph.get("validation", {}).get("valid"):
            suppress_pairs.append({
                "left_workstream_id": left,
                "right_workstream_id": right,
                "reason_codes": ["confirmed-active-succession-ancestor-pair"],
            })
            continue
        if pair not in relevant_pairs:
            continue
        reasons = constraint_reasons
        if not reasons:
            if any(
                nodes[workstream_id].get("status") in {"stale", "unknown"}
                or nodes[workstream_id].get("session_state") in {"stale", "unknown"}
                or nodes[workstream_id].get("evidence_freshness") in {"stale", "unknown"}
                or nodes[workstream_id].get("scope_status") in {"stale", "unknown"}
                for workstream_id in pair
            ):
                reasons.append("stale-or-unknown-endpoint")
            sibling = any({left, right}.issubset(children) for children in parents_by_target.values())
            if sibling:
                reasons.append("sibling-successors")
            direct_edges = [
                edge for edge in graph.get("edges", [])
                if {edge["source_workstream_id"], edge["target_workstream_id"]} == {left, right}
            ]
            if any(edge["relation_type"] == "depends_on" for edge in direct_edges):
                reasons.append("execution-dependency-does-not-suppress")
            if any(
                edge["relation_type"] in {"derived_from", "absorbs"}
                and edge["lifecycle"] in {"proposed", "stale"}
                for edge in direct_edges
            ):
                reasons.append("succession-stale-or-unconfirmed")
            if any(
                edge["relation_type"] in {"derived_from", "absorbs"}
                and "target-unique-commits-or-unknown" in edge.get("evidence_reason_codes", [])
                for edge in direct_edges
            ):
                reasons.append("parent-post-fork-or-unknown-commits")
            if any(
                edge["relation_type"] in {"derived_from", "absorbs"}
                and edge["lifecycle"] == "completed"
                and any(
                    item.get("code") == "completed-takeover-predecessor-not-closed-superseded"
                    and item.get("relation_id") == edge["relation_id"]
                    for item in graph.get("validation", {}).get("errors", [])
                )
                for edge in direct_edges
            ):
                reasons.append("completed-takeover-predecessor-not-closed-superseded")
            if not reasons:
                reasons.append("independent-or-unproven-pair")
        compare_pairs.append({
            "left_workstream_id": left,
            "right_workstream_id": right,
            "reason_codes": sorted(set(reasons)),
        })
    blocking_dependencies = sorted(
        [
            {
                "relation_id": edge["relation_id"],
                "source_workstream_id": edge["source_workstream_id"],
                "target_workstream_id": edge["target_workstream_id"],
                "evidence_status": edge["evidence"]["dependency_status"],
            }
            for edge in graph.get("edges", [])
            if edge["relation_type"] == "depends_on" and edge["lifecycle"] in {"proposed", "active"}
        ],
        key=lambda item: (item["source_workstream_id"], item["target_workstream_id"], item["relation_id"]),
    )
    return {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-succession-plan",
        "graph_hash": graph.get("graph_hash"),
        "active_tip_workstream_ids": active_tip_ids,
        "compare_pairs": compare_pairs,
        "suppress_direct_pairs": suppress_pairs,
        "blocking_dependencies": blocking_dependencies,
        "unknown_workstream_ids": list(graph.get("unknown_workstream_ids", [])),
        "pair_policy": "active-tips-v1",
        "read_only": True,
        "writes_performed": False,
        "destructive_actions": [],
    }


def build_discovery_plan(
    candidate_records: Sequence[Mapping[str, Any]],
    *,
    graph_hash: str,
    rejected_hints: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for record in candidate_records:
        validate_relation_record(record)
        candidate = dict(record)
        candidate["lifecycle"] = "proposed"
        candidate["writes_performed"] = False
        candidates.append(candidate)
    candidates.sort(key=_record_sort_key)
    body = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-discovery-plan",
        "graph_hash": graph_hash,
        "candidates": candidates,
        "rejected_hints": sorted(
            [dict(item) for item in rejected_hints],
            key=lambda item: (str(item.get("source_workstream_id", "")), str(item.get("target_workstream_id", ""))),
        ),
        "similarity_inference_permitted": False,
        "confirmation_required": True,
        "confirmation_scope": "one-local-confirmation-per-exact-plan",
        "silence_policy": "no-permanent-suppression",
        "writes_performed": False,
        "destructive_actions": [],
    }
    body["plan_id"] = f"discovery-{_digest(body)[:24]}"
    return body


def discover_relation_candidates(
    project_root: Path,
    *,
    similarity_hints: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Discover only explicit legacy lineage; similarity hints remain rejected Unknown."""
    legacy = load_legacy_session_projection(project_root, include_archived=False)
    graph = build_relation_graph(legacy["records"], nodes=legacy["nodes"])
    rejected: list[dict[str, Any]] = []
    for hint in similarity_hints:
        source = _validate_identifier(hint.get("source_workstream_id"), "hint source workstream")
        target = _validate_identifier(hint.get("target_workstream_id"), "hint target workstream")
        if source == target:
            raise ValueError("similarity hint cannot reference the same Workstream")
        rejected.append({
            "source_workstream_id": source,
            "target_workstream_id": target,
            "status": "unknown",
            "reason_code": "branch-or-path-similarity-insufficient-evidence",
        })
    return build_discovery_plan(legacy["records"], graph_hash=graph["graph_hash"], rejected_hints=rejected)


_SESSION_BINDING_KEYS = {
    "closure_reason", "evidence_freshness", "head_oid", "lifecycle_phase",
    "runtime_condition", "scope_status", "session_hash", "session_state",
    "workstream_id",
}
_SESSION_TRANSITION_KEYS = {
    "closure_reason", "evidence_freshness", "lifecycle_phase", "runtime_condition",
}
_APPLY_RECEIPT_KEYS = {
    "confirmed_locally", "contract_type", "graph_hash", "plan_hash", "plan_id",
    "predecessor_transitions", "receipt_id", "relation_events", "schema_version",
    "writes_performed",
}
_RELATION_EVENT_RECEIPT_KEYS = {
    "event_hash", "event_id", "prior_lifecycle", "relation_id", "resulting_lifecycle",
}
_SESSION_TRANSITION_RECEIPT_KEYS = {
    "original_closure_reason", "original_evidence_freshness", "original_head_oid",
    "original_lifecycle_phase", "original_runtime_condition", "original_scope_status",
    "original_session_hash", "relation_id", "resulting_closure_reason",
    "resulting_evidence_freshness", "resulting_head_oid", "resulting_lifecycle_phase",
    "resulting_runtime_condition", "resulting_scope_status", "resulting_session_hash",
    "workstream_id",
}


def _validate_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be an exact lowercase SHA-256 digest")
    return value


def _normalize_session_binding(value: Any, *, predecessor_id: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _SESSION_BINDING_KEYS:
        raise ValueError("predecessor_session fields do not match the v1 apply contract")
    workstream_id = _validate_identifier(value.get("workstream_id"), "predecessor workstream_id")
    if workstream_id != predecessor_id:
        raise ValueError("predecessor_session does not match the relation target")
    session_state = value.get("session_state")
    evidence_freshness = value.get("evidence_freshness")
    scope_status = value.get("scope_status")
    if session_state != "current" or evidence_freshness != "current" or scope_status != "current":
        raise ValueError("takeover requires current predecessor session, evidence, and scope")
    lifecycle_phase = value.get("lifecycle_phase")
    runtime_condition = value.get("runtime_condition")
    closure_reason = value.get("closure_reason")
    if lifecycle_phase not in NODE_LIFECYCLE_PHASES or lifecycle_phase == "unknown":
        raise ValueError("predecessor lifecycle_phase is not executable")
    if runtime_condition not in NODE_RUNTIME_CONDITIONS or runtime_condition == "unknown":
        raise ValueError("predecessor runtime_condition is not executable")
    if closure_reason not in (*NODE_CLOSURE_REASONS, None):
        raise ValueError("predecessor closure_reason is invalid")
    if (lifecycle_phase == "closed") != (closure_reason is not None):
        raise ValueError("predecessor closed lifecycle and closure_reason disagree")
    head_oid = _validate_oid(value.get("head_oid"), "predecessor head_oid")
    if head_oid is None:
        raise ValueError("takeover requires an exact predecessor HEAD")
    return {
        "workstream_id": workstream_id,
        "session_hash": _validate_hash(value.get("session_hash"), "predecessor session_hash"),
        "session_state": session_state,
        "head_oid": head_oid,
        "lifecycle_phase": lifecycle_phase,
        "runtime_condition": runtime_condition,
        "evidence_freshness": evidence_freshness,
        "scope_status": scope_status,
        "closure_reason": closure_reason,
    }


def _normalize_session_transition(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _SESSION_TRANSITION_KEYS:
        raise ValueError("predecessor transition fields do not match the v1 apply contract")
    lifecycle_phase = value.get("lifecycle_phase")
    runtime_condition = value.get("runtime_condition")
    evidence_freshness = value.get("evidence_freshness")
    closure_reason = value.get("closure_reason")
    if lifecycle_phase not in NODE_LIFECYCLE_PHASES or lifecycle_phase == "unknown":
        raise ValueError("target predecessor lifecycle_phase is invalid")
    if runtime_condition not in NODE_RUNTIME_CONDITIONS or runtime_condition == "unknown":
        raise ValueError("target predecessor runtime_condition is invalid")
    if evidence_freshness not in HEAD_STATES:
        raise ValueError("target predecessor evidence_freshness is invalid")
    if closure_reason not in (*NODE_CLOSURE_REASONS, None):
        raise ValueError("target predecessor closure_reason is invalid")
    if (lifecycle_phase == "closed") != (closure_reason is not None):
        raise ValueError("target predecessor closed lifecycle and closure_reason disagree")
    return {
        "lifecycle_phase": lifecycle_phase,
        "runtime_condition": runtime_condition,
        "evidence_freshness": evidence_freshness,
        "closure_reason": closure_reason,
    }


def build_apply_plan(
    discovery_plan: Mapping[str, Any],
    *,
    takeover_requests: Sequence[Mapping[str, Any]] = (),
    relation_lifecycle_requests: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if discovery_plan.get("contract_type") != "workstream-relation-discovery-plan":
        raise ValueError("apply plan requires a discovery plan")
    graph_hash = _validate_hash(discovery_plan.get("graph_hash"), "discovery graph_hash")
    discovery_plan_id = _validate_identifier(
        discovery_plan.get("plan_id"), "discovery plan_id", filesystem_safe=True
    )
    discovery_body = dict(discovery_plan)
    discovery_body.pop("plan_id", None)
    if discovery_plan_id != f"discovery-{_digest(discovery_body)[:24]}":
        raise ValueError("discovery plan_id does not bind its exact content")
    candidates = sorted((dict(item) for item in discovery_plan.get("candidates", [])), key=_record_sort_key)
    for candidate in candidates:
        validate_relation_record(candidate)
        if candidate["lifecycle"] != "proposed" or candidate["writes_performed"]:
            raise ValueError("discovery candidate must be a read-only proposed relation")
    request_map: dict[str, Mapping[str, Any]] = {}
    for request in takeover_requests:
        if not isinstance(request, Mapping) or set(request) != {
            "relation_id", "target_lifecycle", "predecessor_session", "transition"
        }:
            raise ValueError("takeover request fields do not match the v1 apply contract")
        relation_id = _validate_identifier(request.get("relation_id"), "takeover relation_id", filesystem_safe=True)
        if relation_id in request_map:
            raise ValueError("duplicate takeover request")
        request_map[relation_id] = request
    operations: list[dict[str, Any]] = []
    session_bindings: list[dict[str, Any]] = []
    candidate_ids = {record["relation_id"] for record in candidates}
    lifecycle_requests = dict(relation_lifecycle_requests or {})
    unknown_lifecycle_requests = sorted(set(lifecycle_requests) - candidate_ids)
    if unknown_lifecycle_requests:
        raise ValueError(
            f"relation lifecycle request does not match a discovery candidate: {unknown_lifecycle_requests[0]}"
        )
    for relation_id, lifecycle in lifecycle_requests.items():
        _validate_identifier(relation_id, "relation lifecycle relation_id", filesystem_safe=True)
        if lifecycle not in {"proposed", "active", "completed"}:
            raise ValueError("relation lifecycle request must be proposed, active, or completed")
    unknown_requests = sorted(set(request_map) - candidate_ids)
    if unknown_requests:
        raise ValueError(f"takeover request does not match a discovery candidate: {unknown_requests[0]}")
    for record in candidates:
        request = request_map.get(record["relation_id"])
        target_lifecycle = lifecycle_requests.get(record["relation_id"], "proposed")
        if request is not None:
            if record["relation_type"] not in {"derived_from", "absorbs"}:
                raise ValueError("only succession relations can transition predecessor sessions")
            target_lifecycle = str(request.get("target_lifecycle"))
            if target_lifecycle not in {"active", "completed"}:
                raise ValueError("takeover target_lifecycle must be active or completed")
        elif target_lifecycle in {"active", "completed"} and record["relation_type"] in {"derived_from", "absorbs"}:
            raise ValueError("succession lifecycle activation requires an exact takeover request")
        event = dict(record)
        event["lifecycle"] = target_lifecycle
        operations.append({
            "action": "append-relation-event",
            "relation_id": record["relation_id"],
            "target_lifecycle": target_lifecycle,
            "event_hash": _digest(event),
        })
        if request is None:
            continue
        binding = _normalize_session_binding(
            request.get("predecessor_session"), predecessor_id=record["target_workstream_id"]
        )
        transition_value = request.get("transition")
        transition = None if transition_value is None else _normalize_session_transition(transition_value)
        if target_lifecycle == "active":
            if transition is None:
                raise ValueError("active takeover requires an atomic predecessor inactive transition")
            if binding["runtime_condition"] != "active":
                raise ValueError("active takeover predecessor must be runtime active before the transition")
            if (
                transition["lifecycle_phase"] != binding["lifecycle_phase"]
                or transition["runtime_condition"] != "paused"
                or transition["evidence_freshness"] != "current"
                or transition["closure_reason"] != binding["closure_reason"]
            ):
                raise ValueError("active takeover transition must preserve lifecycle and mark runtime paused")
        elif binding["lifecycle_phase"] == "closed" and binding["closure_reason"] == "superseded":
            if transition is not None:
                raise ValueError("already superseded predecessor must not be transitioned again")
        else:
            if transition is None:
                raise ValueError("completed takeover requires closed/superseded predecessor or atomic transition")
            if (
                transition["lifecycle_phase"] != "closed"
                or transition["runtime_condition"] != "paused"
                or transition["evidence_freshness"] != "current"
                or transition["closure_reason"] != "superseded"
            ):
                raise ValueError("completed takeover transition must close predecessor as superseded")
        session_bindings.append({
            "relation_id": record["relation_id"],
            "target_lifecycle": target_lifecycle,
            "predecessor_session": binding,
            "transition": transition,
        })
        if transition is None:
            operations.append({
                "action": "assert-predecessor-closed-superseded",
                "relation_id": record["relation_id"],
                "workstream_id": binding["workstream_id"],
                "expected_session_hash": binding["session_hash"],
                "expected_head_oid": binding["head_oid"],
            })
        else:
            operations.append({
                "action": "transition-predecessor-session",
                "relation_id": record["relation_id"],
                "workstream_id": binding["workstream_id"],
                "expected_session_hash": binding["session_hash"],
                "expected_head_oid": binding["head_oid"],
                "expected_lifecycle_phase": binding["lifecycle_phase"],
                "expected_runtime_condition": binding["runtime_condition"],
                "expected_evidence_freshness": binding["evidence_freshness"],
                "expected_scope_status": binding["scope_status"],
                "expected_closure_reason": binding["closure_reason"],
                "target_lifecycle_phase": transition["lifecycle_phase"],
                "target_runtime_condition": transition["runtime_condition"],
                "target_evidence_freshness": transition["evidence_freshness"],
                "target_closure_reason": transition["closure_reason"],
                "transition_reason": f"succession-takeover:{record['relation_id']}:{target_lifecycle}",
                "restore_receipt_required": True,
            })
    body = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-apply-plan",
        "discovery_plan_id": discovery_plan_id,
        "graph_hash": graph_hash,
        "operations": operations,
        "session_bindings": sorted(session_bindings, key=lambda item: item["relation_id"]),
        "atomicity": "all-operations-or-none",
        "no_drift_policy": "exact-graph-session-and-head-or-fail",
        "confirmation_required": True,
        "confirmation_scope": "one-local-confirmation-per-exact-plan",
        "output_contract": {
            "contract_type": "workstream-relation-apply-receipt",
            "required_fields": [
                "schema_version", "contract_type", "receipt_id", "plan_id", "plan_hash",
                "graph_hash", "confirmed_locally", "relation_events",
                "predecessor_transitions", "writes_performed",
            ],
        },
        "preservation_contract": {
            "worktrees": True,
            "branches": True,
            "commits": True,
            "validations": True,
            "author_documents": True,
            "relation_history": True,
        },
        "writes_performed": False,
        "execution_supported": False,
        "destructive_actions": [],
    }
    body["plan_hash"] = _digest(body)
    body["plan_id"] = f"apply-{body['plan_hash'][:24]}"
    return body


def validate_apply_receipt(
    receipt: Mapping[str, Any],
    *,
    apply_plan: Mapping[str, Any] | None = None,
) -> None:
    if set(receipt) != _APPLY_RECEIPT_KEYS:
        raise ValueError("apply receipt fields do not match the v1 contract")
    if receipt.get("schema_version") != RELATION_SCHEMA_VERSION or receipt.get("contract_type") != "workstream-relation-apply-receipt":
        raise ValueError("unsupported apply receipt contract")
    _validate_identifier(receipt.get("receipt_id"), "apply receipt_id", filesystem_safe=True)
    _validate_identifier(receipt.get("plan_id"), "apply receipt plan_id", filesystem_safe=True)
    _validate_hash(receipt.get("plan_hash"), "apply receipt plan_hash")
    _validate_hash(receipt.get("graph_hash"), "apply receipt graph_hash")
    if receipt.get("confirmed_locally") is not True or receipt.get("writes_performed") is not True:
        raise ValueError("apply receipt requires confirmed local writes")
    relation_events = receipt.get("relation_events")
    transitions = receipt.get("predecessor_transitions")
    if not isinstance(relation_events, list) or not isinstance(transitions, list):
        raise ValueError("apply receipt events and transitions must be lists")
    for event in relation_events:
        if not isinstance(event, Mapping) or set(event) != _RELATION_EVENT_RECEIPT_KEYS:
            raise ValueError("apply receipt relation event fields do not match the v1 contract")
        _validate_identifier(event.get("relation_id"), "receipt relation_id", filesystem_safe=True)
        _validate_identifier(event.get("event_id"), "receipt event_id", filesystem_safe=True)
        _validate_hash(event.get("event_hash"), "receipt event_hash")
        if event.get("prior_lifecycle") not in (*RELATION_LIFECYCLES, None):
            raise ValueError("receipt prior_lifecycle is invalid")
        if event.get("resulting_lifecycle") not in RELATION_LIFECYCLES:
            raise ValueError("receipt resulting_lifecycle is invalid")
    if relation_events != sorted(relation_events, key=lambda item: item["relation_id"]):
        raise ValueError("apply receipt relation events must be deterministically sorted")
    for transition in transitions:
        if not isinstance(transition, Mapping) or set(transition) != _SESSION_TRANSITION_RECEIPT_KEYS:
            raise ValueError("apply receipt predecessor transition fields do not match the v1 contract")
        _validate_identifier(transition.get("relation_id"), "transition relation_id", filesystem_safe=True)
        _validate_identifier(transition.get("workstream_id"), "transition workstream_id")
        for key in ("original_session_hash", "resulting_session_hash"):
            _validate_hash(transition.get(key), f"transition {key}")
        if transition["original_session_hash"] == transition["resulting_session_hash"]:
            raise ValueError("predecessor transition receipt must bind changed session content")
        for key in ("original_head_oid", "resulting_head_oid"):
            if _validate_oid(transition.get(key), f"transition {key}") is None:
                raise ValueError("predecessor transition receipt requires exact HEADs")
        if transition["original_head_oid"] != transition["resulting_head_oid"]:
            raise ValueError("succession session transition must not move predecessor HEAD")
        for prefix in ("original", "resulting"):
            if transition.get(f"{prefix}_lifecycle_phase") not in NODE_LIFECYCLE_PHASES:
                raise ValueError("transition lifecycle phase is invalid")
            if transition.get(f"{prefix}_runtime_condition") not in NODE_RUNTIME_CONDITIONS:
                raise ValueError("transition runtime condition is invalid")
            if transition.get(f"{prefix}_evidence_freshness") not in HEAD_STATES:
                raise ValueError("transition evidence freshness is invalid")
            if transition.get(f"{prefix}_scope_status") not in HEAD_STATES:
                raise ValueError("transition scope status is invalid")
            if transition.get(f"{prefix}_closure_reason") not in (*NODE_CLOSURE_REASONS, None):
                raise ValueError("transition closure reason is invalid")
    if transitions != sorted(transitions, key=lambda item: (item["relation_id"], item["workstream_id"])):
        raise ValueError("apply receipt transitions must be deterministically sorted")
    if apply_plan is not None:
        if apply_plan.get("contract_type") != "workstream-relation-apply-plan":
            raise ValueError("apply receipt binding requires an apply plan")
        apply_body = dict(apply_plan)
        apply_body.pop("plan_id", None)
        apply_body.pop("plan_hash", None)
        expected_plan_hash = _digest(apply_body)
        if (
            apply_plan.get("plan_hash") != expected_plan_hash
            or apply_plan.get("plan_id") != f"apply-{expected_plan_hash[:24]}"
        ):
            raise ValueError("apply plan hash does not bind its exact content")
        for receipt_key, plan_key in (("plan_id", "plan_id"), ("plan_hash", "plan_hash"), ("graph_hash", "graph_hash")):
            if receipt.get(receipt_key) != apply_plan.get(plan_key):
                raise ValueError(f"apply receipt {receipt_key} does not match the exact apply plan")
        expected_relations = sorted(
            operation["relation_id"] for operation in apply_plan.get("operations", [])
            if operation.get("action") == "append-relation-event"
        )
        if [item["relation_id"] for item in relation_events] != expected_relations:
            raise ValueError("apply receipt relation events do not match the exact apply plan")
        append_operations = {
            operation["relation_id"]: operation for operation in apply_plan.get("operations", [])
            if operation.get("action") == "append-relation-event"
        }
        for event in relation_events:
            operation = append_operations[event["relation_id"]]
            if (
                event["event_hash"] != operation["event_hash"]
                or event["resulting_lifecycle"] != operation["target_lifecycle"]
            ):
                raise ValueError("apply receipt event evidence does not match the exact apply operation")
        expected_transitions = sorted(
            (operation["relation_id"], operation["workstream_id"])
            for operation in apply_plan.get("operations", [])
            if operation.get("action") == "transition-predecessor-session"
        )
        actual_transitions = [(item["relation_id"], item["workstream_id"]) for item in transitions]
        if actual_transitions != expected_transitions:
            raise ValueError("apply receipt predecessor transitions do not match the exact apply plan")
        transition_operations = {
            (operation["relation_id"], operation["workstream_id"]): operation
            for operation in apply_plan.get("operations", [])
            if operation.get("action") == "transition-predecessor-session"
        }
        for transition in transitions:
            operation = transition_operations[(transition["relation_id"], transition["workstream_id"])]
            field_pairs = (
                ("original_session_hash", "expected_session_hash"),
                ("original_head_oid", "expected_head_oid"),
                ("original_lifecycle_phase", "expected_lifecycle_phase"),
                ("original_runtime_condition", "expected_runtime_condition"),
                ("original_evidence_freshness", "expected_evidence_freshness"),
                ("original_scope_status", "expected_scope_status"),
                ("original_closure_reason", "expected_closure_reason"),
                ("resulting_lifecycle_phase", "target_lifecycle_phase"),
                ("resulting_runtime_condition", "target_runtime_condition"),
                ("resulting_evidence_freshness", "target_evidence_freshness"),
                ("resulting_closure_reason", "target_closure_reason"),
            )
            if any(transition[receipt_key] != operation[operation_key] for receipt_key, operation_key in field_pairs):
                raise ValueError("apply receipt session evidence does not match the exact transition operation")


def build_undo_plan(*, apply_receipt: Mapping[str, Any]) -> dict[str, Any]:
    validate_apply_receipt(apply_receipt)
    receipt_hash = _digest(apply_receipt)
    operations: list[dict[str, Any]] = []
    for event in apply_receipt["relation_events"]:
        operations.append({
            "action": "append-compensating-event",
            "relation_id": event["relation_id"],
            "expected_event_id": event["event_id"],
            "expected_event_hash": event["event_hash"],
            "target_lifecycle": event["prior_lifecycle"] or "cancelled",
        })
    for transition in apply_receipt["predecessor_transitions"]:
        operations.append({
            "action": "restore-predecessor-session",
            "relation_id": transition["relation_id"],
            "workstream_id": transition["workstream_id"],
            "expected_session_hash": transition["resulting_session_hash"],
            "expected_head_oid": transition["resulting_head_oid"],
            "expected_lifecycle_phase": transition["resulting_lifecycle_phase"],
            "expected_runtime_condition": transition["resulting_runtime_condition"],
            "expected_evidence_freshness": transition["resulting_evidence_freshness"],
            "expected_scope_status": transition["resulting_scope_status"],
            "expected_closure_reason": transition["resulting_closure_reason"],
            "restore_session_hash": transition["original_session_hash"],
            "restore_head_oid": transition["original_head_oid"],
            "restore_lifecycle_phase": transition["original_lifecycle_phase"],
            "restore_runtime_condition": transition["original_runtime_condition"],
            "restore_evidence_freshness": transition["original_evidence_freshness"],
            "restore_scope_status": transition["original_scope_status"],
            "restore_closure_reason": transition["original_closure_reason"],
        })
    body = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-undo-plan",
        "apply_receipt_id": apply_receipt["receipt_id"],
        "apply_receipt_hash": receipt_hash,
        "apply_plan_hash": apply_receipt["plan_hash"],
        "graph_hash": apply_receipt["graph_hash"],
        "operations": operations,
        "atomicity": "all-operations-or-none",
        "no_drift_policy": "exact-receipt-session-and-head-or-fail",
        "confirmation_required": True,
        "confirmation_scope": "one-local-confirmation-per-exact-plan",
        "output_contract": {
            "contract_type": "workstream-relation-undo-receipt",
            "required_fields": [
                "schema_version", "contract_type", "receipt_id", "plan_id", "plan_hash",
                "apply_receipt_id", "apply_receipt_hash", "confirmed_locally",
                "appended_compensating_event_ids", "restored_sessions", "writes_performed",
            ],
        },
        "preservation_contract": {
            "worktrees": True,
            "branches": True,
            "commits": True,
            "validations": True,
            "author_documents": True,
            "relation_history": True,
        },
        "writes_performed": False,
        "execution_supported": False,
        "deletes_history": False,
        "destructive_actions": [],
    }
    body["plan_hash"] = _digest(body)
    body["plan_id"] = f"undo-{body['plan_hash'][:24]}"
    return body


__all__ = [
    "ARCHIVE_LAYOUT_VERSION",
    "ARCHIVE_MAX_FILE_BYTES",
    "ARCHIVE_MAX_FILES",
    "ARCHIVE_MAX_TOTAL_BYTES",
    "RELATION_SCHEMA_VERSION",
    "RELATION_LIFECYCLES",
    "RELATION_TYPES",
    "append_proposed_relation",
    "append_relation_event",
    "build_apply_plan",
    "build_discovery_plan",
    "build_relation_graph",
    "build_relation_record",
    "build_succession_plan",
    "build_undo_plan",
    "default_relation_evidence",
    "discover_relation_candidates",
    "load_archived_session_index",
    "load_legacy_session_projection",
    "load_relation_graph",
    "load_relation_history",
    "project_legacy_session_relation",
    "relation_storage_root",
    "retired_session_archive_root",
    "validate_apply_receipt",
    "validate_relation_record",
]
