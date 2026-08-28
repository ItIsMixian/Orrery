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
from typing import Any, Iterable, Mapping, Sequence


RELATION_SCHEMA_VERSION = 1
RELATION_TYPES = ("absorbs", "depends_on", "derived_from")
RELATION_LIFECYCLES = ("active", "cancelled", "completed", "proposed", "stale")
EVIDENCE_STATES = ("confirmed", "not-applicable", "rejected", "stale", "unknown")
HEAD_STATES = ("current", "stale", "unknown")
NODE_STATES = ("active", "cancelled", "completed", "review-pending", "stale", "unknown")
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
        if not isinstance(reference, str) or not reference or len(reference) > 512 or "\0" in reference:
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


def load_legacy_session_projection(project_root: Path) -> dict[str, Any]:
    """Project W5D lineage sessions read-only; never writes relation storage or sessions."""
    from .collaboration import inspect_worktree_status

    sessions: dict[str, tuple[dict[str, Any], str]] = {}
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
            sessions[record["workstream_id"]] = (record, str(session.get("state", "stale")))
    nodes = [_node_from_session(record, state) for record, state in sessions.values()]
    relations: list[dict[str, Any]] = []
    for record, state in sessions.values():
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


def _node_from_session(session: Mapping[str, Any], session_state: str) -> dict[str, Any]:
    lifecycle = str(session.get("lifecycle_phase", ""))
    runtime = str(session.get("runtime_condition", ""))
    if session_state != "current":
        status = "stale"
        evidence_status = "stale"
    elif lifecycle in {"integrated", "closed"}:
        status = "completed"
        evidence_status = "current"
    elif lifecycle == "review-ready":
        status = "review-pending"
        evidence_status = "current"
    elif runtime in {"stale-unknown", "offline"}:
        status = "unknown"
        evidence_status = "unknown"
    else:
        status = "active"
        evidence_status = "current"
    return {
        "workstream_id": str(session["workstream_id"]),
        "status": status,
        "evidence_status": evidence_status,
        "head_oid": session.get("head"),
        "scope_status": "current" if session_state == "current" else "stale",
        "source_links": [{"kind": "workstream-session", "ref": f"git-private:{session['workstream_id']}"}],
        "origin": "legacy-session-projection",
    }


def _normalize_node(node: Mapping[str, Any]) -> dict[str, Any]:
    workstream_id = _validate_identifier(node.get("workstream_id"), "node workstream_id")
    status = node.get("status", "unknown")
    evidence_status = node.get("evidence_status", "unknown")
    scope_status = node.get("scope_status", "unknown")
    if status not in NODE_STATES or evidence_status not in HEAD_STATES or scope_status not in HEAD_STATES:
        raise ValueError("node status fields do not match the v1 graph contract")
    head = _validate_oid(node.get("head_oid"), "node head_oid")
    origin = node.get("origin", "relation-only")
    if origin not in {"native", "legacy-session-projection", "relation-only", "discovery"}:
        raise ValueError("unsupported node origin")
    return {
        "workstream_id": workstream_id,
        "status": status,
        "evidence_status": evidence_status,
        "head_oid": head,
        "scope_status": scope_status,
        "source_links": _normalize_source_links(node.get("source_links", [])),
        "origin": origin,
    }


def _graph_diagnostics(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
    return node.get("status") in {"active", "review-pending"} and node.get("scope_status") == "current"


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
        if source is None or target is None or not _node_is_active(source) or not _node_is_active(target):
            reasons.append("endpoint-not-current-active")
        else:
            if evidence["source_head_oid"] != source.get("head_oid") or evidence["target_head_oid"] != target.get("head_oid"):
                reasons.append("endpoint-head-drift")
    return not reasons, sorted(set(reasons))


def build_relation_graph(
    records: Sequence[Mapping[str, Any]],
    *,
    nodes: Sequence[Mapping[str, Any]] = (),
    pair_constraints: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_records: list[dict[str, Any]] = []
    for record in records:
        validate_relation_record(record)
        normalized_records.append(dict(record))
    normalized_records.sort(key=_record_sort_key)
    node_map = {node["workstream_id"]: node for node in (_normalize_node(item) for item in nodes)}
    for record in normalized_records:
        for workstream_id in (record["source_workstream_id"], record["target_workstream_id"]):
            node_map.setdefault(workstream_id, {
                "workstream_id": workstream_id,
                "status": "unknown",
                "evidence_status": "unknown",
                "head_oid": None,
                "scope_status": "unknown",
                "source_links": [],
                "origin": "relation-only",
            })
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
            node_map.setdefault(workstream_id, {
                "workstream_id": workstream_id,
                "status": "unknown",
                "evidence_status": "unknown",
                "head_oid": None,
                "scope_status": "unknown",
                "source_links": [],
                "origin": "relation-only",
            })
        normalized_constraints.append({"left_workstream_id": ordered[0], "right_workstream_id": ordered[1], "reasons": sorted(set(reasons))})
    normalized_constraints.sort(key=lambda item: (item["left_workstream_id"], item["right_workstream_id"], item["reasons"]))
    errors, warnings = _graph_diagnostics(normalized_records)
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
        if node["status"] in {"unknown", "stale"} or node["evidence_status"] in {"unknown", "stale"}
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


def load_relation_graph(project_root: Path, *, include_legacy: bool = True) -> dict[str, Any]:
    native = load_relation_history(project_root)
    records = list(native["current_records"])
    nodes: list[dict[str, Any]] = []
    if include_legacy:
        legacy = load_legacy_session_projection(project_root)
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
            or node.get("evidence_status") in {"stale", "unknown"}
            or node.get("scope_status") in {"stale", "unknown"}
            for node in endpoints
        )
        dependency_visible = edge["relation_type"] == "depends_on" and edge["lifecycle"] in {"proposed", "active", "stale"}
        uncertain_succession = (
            edge["relation_type"] in {"derived_from", "absorbs"}
            and edge["lifecycle"] not in {"cancelled", "completed"}
            and not edge.get("effective_active_succession")
        )
        if endpoint_unknown or dependency_visible or uncertain_succession:
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
                or nodes[workstream_id].get("evidence_status") in {"stale", "unknown"}
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
    legacy = load_legacy_session_projection(project_root)
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


def build_apply_plan(discovery_plan: Mapping[str, Any]) -> dict[str, Any]:
    if discovery_plan.get("contract_type") != "workstream-relation-discovery-plan":
        raise ValueError("apply plan requires a discovery plan")
    operations = [
        {"action": "append-relation-event", "relation_id": record["relation_id"], "event_hash": _digest(record)}
        for record in discovery_plan.get("candidates", [])
    ]
    body = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-apply-plan",
        "discovery_plan_id": discovery_plan.get("plan_id"),
        "graph_hash": discovery_plan.get("graph_hash"),
        "operations": operations,
        "confirmation_required": True,
        "confirmation_scope": "one-local-confirmation-per-exact-plan",
        "output_contract": {
            "contract_type": "workstream-relation-apply-receipt",
            "required_fields": [
                "receipt_id", "plan_id", "graph_hash", "confirmed_locally",
                "appended_event_ids", "writes_performed",
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
    body["plan_id"] = f"apply-{_digest(body)[:24]}"
    return body


def build_undo_plan(*, apply_receipt_id: str, relation_ids: Iterable[str]) -> dict[str, Any]:
    _validate_identifier(apply_receipt_id, "apply_receipt_id")
    normalized = sorted({_validate_identifier(value, "relation_id", filesystem_safe=True) for value in relation_ids})
    body = {
        "schema_version": RELATION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-undo-plan",
        "apply_receipt_id": apply_receipt_id,
        "operations": [
            {"action": "append-compensating-event", "relation_id": relation_id, "target_lifecycle": "cancelled"}
            for relation_id in normalized
        ],
        "confirmation_required": True,
        "confirmation_scope": "one-local-confirmation-per-exact-plan",
        "output_contract": {
            "contract_type": "workstream-relation-undo-receipt",
            "required_fields": [
                "receipt_id", "plan_id", "apply_receipt_id", "appended_event_ids", "writes_performed",
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
    body["plan_id"] = f"undo-{_digest(body)[:24]}"
    return body


__all__ = [
    "RELATION_SCHEMA_VERSION",
    "RELATION_LIFECYCLES",
    "RELATION_TYPES",
    "append_proposed_relation",
    "build_apply_plan",
    "build_discovery_plan",
    "build_relation_graph",
    "build_relation_record",
    "build_succession_plan",
    "build_undo_plan",
    "default_relation_evidence",
    "discover_relation_candidates",
    "load_legacy_session_projection",
    "load_relation_graph",
    "load_relation_history",
    "project_legacy_session_relation",
    "relation_storage_root",
    "validate_relation_record",
]
