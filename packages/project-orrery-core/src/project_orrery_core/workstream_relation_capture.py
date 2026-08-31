"""W7.3 Workstream relation proposal, confirmation, and role control plane.

The capture store is append-only and Git-common-private.  It records only
bounded metadata and hashes; it never stores prompts, answers, transcripts,
source/diff bodies, credentials, shell commands, or executable paths/URLs.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .workstream_relations import (
    append_relation_event,
    build_relation_graph,
    build_relation_record,
    default_relation_evidence,
    load_relation_history,
)


CAPTURE_SCHEMA_VERSION = 2
DEPENDENCY_GATES = ("implementation", "validation", "integration", "release")
PROPOSER_KINDS = ("agent", "conductor", "harness", "human", "tool")
EVIDENCE_CATEGORIES = (
    "closure",
    "git-ancestry",
    "harness",
    "human-or-agent-assertion",
    "plan",
    "scope",
    "validation",
    "workstream-session",
)
PROPOSAL_EVENT_KINDS = (
    "accepted",
    "deferred",
    "evidence-updated",
    "gate-changed",
    "rejected",
    "suggested",
    "superseded",
)
PROPOSAL_STATUSES = (
    "accepted",
    "deferred-unknown",
    "proposed",
    "rejected",
    "superseded",
)
FACT_SCOPES = ("canonical", "candidate", "worktree", "local-only", "historical", "unknown")
ROLE_STATUSES = ("granted", "revoked")
CAPTURE_MAX_FILE_BYTES = 256 * 1024
CAPTURE_MAX_FILES = 1024
CAPTURE_MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_EVIDENCE_ITEMS = 32
MAX_UNFINISHED_RESPONSIBILITIES = 32
MAX_SERIES_ORDER = 1000000

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_OID = re.compile(r"^[0-9a-f]{40}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_EVENT_FILE = re.compile(r"^([1-9][0-9]{0,8})-([A-Za-z0-9][A-Za-z0-9._-]{0,127})\.json$")
_FORBIDDEN_FIELDS = {
    "answer", "args", "command", "credential", "diff", "diff_body", "password",
    "prompt", "secret", "shell", "source", "source_body", "token", "transcript", "url",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _event_hash(value: Mapping[str, Any]) -> str:
    body = dict(value)
    body.pop("event_hash", None)
    return _digest(body)


def _timestamp(value: str | None = None) -> str:
    candidate = value or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if not isinstance(candidate, str) or len(candidate) > 64:
        raise ValueError("timestamp must be a bounded RFC 3339 value")
    try:
        parsed = dt.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be an RFC 3339 value") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return candidate


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a filesystem-safe identifier")
    return value


def _bounded_text(value: Any, label: str, *, maximum: int = 2048) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(character in value for character in "\r\n\0")
    ):
        raise ValueError(f"{label} must be non-empty, single-line, and bounded")
    return value.strip()


def _optional_oid(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _OID.fullmatch(value):
        raise ValueError(f"{label} must be null or an exact lowercase commit OID")
    return value


def _optional_hash(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ValueError(f"{label} must be null or a lowercase SHA-256 hash")
    return value


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN_FIELDS:
                raise ValueError(f"capture payload contains forbidden field: {key}")
            _reject_forbidden_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_fields(child)


def _safe_reference(value: Any) -> str:
    reference = _bounded_text(value, "evidence ref", maximum=512).replace("\\", "/")
    if "://" in reference or reference.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", reference):
        raise ValueError("evidence ref cannot be an absolute path or URL")
    parts = reference.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("evidence ref must be a normalized relative or opaque reference")
    return reference


def _normalize_evidence(items: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    if len(items) > MAX_EVIDENCE_ITEMS:
        raise ValueError("proposal evidence count exceeds the bounded limit")
    normalized: list[dict[str, str]] = []
    for item in items:
        if set(item) != {"category", "ref", "hash", "fact_scope"}:
            raise ValueError("evidence item fields do not match capture schema v2")
        category = item.get("category")
        fact_scope = item.get("fact_scope")
        if category not in EVIDENCE_CATEGORIES or fact_scope not in FACT_SCOPES:
            raise ValueError("evidence category or fact scope is unsupported")
        value_hash = item.get("hash")
        if not isinstance(value_hash, str) or not _HASH.fullmatch(value_hash):
            raise ValueError("evidence hash must be a lowercase SHA-256 value")
        normalized.append({
            "category": str(category),
            "ref": _safe_reference(item.get("ref")),
            "hash": value_hash,
            "fact_scope": str(fact_scope),
        })
    normalized.sort(key=lambda item: (item["category"], item["ref"], item["hash"], item["fact_scope"]))
    if len({_canonical_bytes(item) for item in normalized}) != len(normalized):
        raise ValueError("proposal evidence contains duplicate items")
    return normalized


def evidence_reference(*, category: str, reference: str, fact_scope: str, digest: str | None = None) -> dict[str, str]:
    """Build one safe evidence reference without retaining evidence body text."""
    return _normalize_evidence([{
        "category": category,
        "ref": reference,
        "hash": digest or hashlib.sha256(reference.encode("utf-8")).hexdigest(),
        "fact_scope": fact_scope,
    }])[0]


def _normalize_absorbs_context(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    allowed = {"target_closure", "validation_refs", "scope_refs", "unfinished_responsibilities"}
    if set(value) != allowed:
        raise ValueError("absorbs context fields do not match capture schema v2")
    closure = value.get("target_closure")
    if closure not in {"closed", "integrated", "open", "unknown"}:
        raise ValueError("absorbs target closure is unsupported")
    result: dict[str, Any] = {"target_closure": closure}
    for key in ("validation_refs", "scope_refs", "unfinished_responsibilities"):
        items = value.get(key)
        if not isinstance(items, list) or len(items) > MAX_UNFINISHED_RESPONSIBILITIES:
            raise ValueError(f"absorbs {key} must be a bounded list")
        if key.endswith("_refs"):
            result[key] = sorted({_safe_reference(item) for item in items})
        else:
            result[key] = sorted({_bounded_text(item, "unfinished responsibility", maximum=512) for item in items})
    return result


def capture_storage_root(project_root: Path) -> Path:
    root = Path(project_root).expanduser().absolute()
    import subprocess

    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode:
        raise ValueError("relation capture requires a local Git repository")
    common = Path(completed.stdout.strip())
    if not common.is_absolute():
        common = root / common
    return Path(os.path.realpath(common)) / "orrery" / "workstream-relation-capture-v2"


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _validate_root(root: Path) -> None:
    common = root.parent.parent
    if root != common / "orrery" / "workstream-relation-capture-v2":
        raise ValueError("capture storage escaped the Git common private boundary")
    for candidate in (common / "orrery", root):
        if os.path.lexists(candidate) and (not candidate.is_dir() or _is_link_or_reparse(candidate)):
            raise ValueError("capture storage ancestors must be real directories")


def _read_regular_json(path: Path) -> dict[str, Any]:
    if _is_link_or_reparse(path):
        raise ValueError("capture event must not be a symlink or reparse point")
    try:
        before = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot inspect capture event: {exc}") from exc
    if not stat.S_ISREG(before.st_mode) or before.st_size > CAPTURE_MAX_FILE_BYTES:
        raise ValueError("capture event must be a bounded regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_size > CAPTURE_MAX_FILE_BYTES:
            raise ValueError("capture event changed or exceeded the size limit")
        content = os.read(descriptor, CAPTURE_MAX_FILE_BYTES + 1)
    except OSError as exc:
        raise ValueError(f"cannot read capture event: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(content) > CAPTURE_MAX_FILE_BYTES:
        raise ValueError("capture event exceeds the size limit")
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"capture event is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("capture event root must be an object")
    return value


def _event_files(root: Path, category: str, identifier: str | None = None) -> list[Path]:
    _validate_root(root)
    base = root / category
    if identifier is not None:
        base = base / _identifier(identifier, f"{category} identifier")
    if not os.path.lexists(base):
        return []
    if not base.is_dir() or _is_link_or_reparse(base):
        raise ValueError("capture event directory must be a real directory")
    result: list[Path] = []
    stack = [base]
    total = 0
    while stack:
        current = stack.pop()
        with os.scandir(current) as iterator:
            entries = sorted(list(iterator), key=lambda item: item.name)
        for entry in entries:
            candidate = Path(entry.path)
            if entry.is_symlink():
                raise ValueError("capture storage cannot contain symlinks")
            if entry.is_dir(follow_symlinks=False):
                if identifier is not None:
                    raise ValueError("capture identifier directory cannot contain nested directories")
                _identifier(entry.name, "capture identifier directory")
                stack.append(candidate)
                continue
            if not entry.is_file(follow_symlinks=False) or not _EVENT_FILE.fullmatch(entry.name):
                raise ValueError("capture storage contains an invalid event entry")
            size = entry.stat(follow_symlinks=False).st_size
            if size > CAPTURE_MAX_FILE_BYTES:
                raise ValueError("capture event exceeds the size limit")
            total += size
            result.append(candidate)
            if len(result) > CAPTURE_MAX_FILES or total > CAPTURE_MAX_TOTAL_BYTES:
                raise ValueError("capture storage exceeds count or total-size limits")
    return sorted(result, key=lambda path: (str(path.parent), path.name))


def _append_json(root: Path, category: str, identifier: str, revision: int, event_id: str, value: Mapping[str, Any]) -> Path:
    _validate_root(root)
    _identifier(identifier, f"{category} identifier")
    _identifier(event_id, "event_id")
    payload = json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if len(payload) > CAPTURE_MAX_FILE_BYTES:
        raise ValueError("capture event exceeds the write size limit")
    base = root / category / identifier
    for ancestor in (root.parent, root, root / category, base):
        if os.path.lexists(ancestor) and (not ancestor.is_dir() or _is_link_or_reparse(ancestor)):
            raise ValueError("capture write target has an unsafe ancestor")
        ancestor.mkdir(parents=True, exist_ok=True)
    destination = base / f"{revision}-{event_id}.json"
    if os.path.lexists(destination):
        raise ValueError("capture event already exists")
    descriptor: int | None = None
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        os.write(descriptor, payload)
        os.fsync(descriptor)
    except OSError as exc:
        raise ValueError(f"cannot append capture event: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return destination


def _proposal_keys() -> set[str]:
    return {
        "schema_version", "contract_type", "event_id", "event_hash", "proposal_id", "relation_id",
        "revision", "event_kind", "status", "relation_type", "source_workstream_id",
        "target_workstream_id", "required_for", "rationale", "consequence", "fact_scope",
        "proposer", "evidence", "source_head_oid", "target_head_oid", "absorbs_context",
        "recorded_at", "prior_event_hash", "writes_performed",
    }


def validate_proposal_event(value: Mapping[str, Any]) -> None:
    if set(value) != _proposal_keys():
        raise ValueError("proposal event fields do not match capture schema v2")
    _reject_forbidden_fields(value)
    if value.get("schema_version") != CAPTURE_SCHEMA_VERSION or value.get("contract_type") != "workstream-relation-proposal-event":
        raise ValueError("unsupported relation proposal contract")
    for field in ("event_id", "proposal_id", "relation_id", "source_workstream_id", "target_workstream_id"):
        _identifier(value.get(field), field)
    if value["source_workstream_id"] == value["target_workstream_id"]:
        raise ValueError("relation proposal cannot reference itself")
    revision = value.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValueError("proposal revision must be a positive integer")
    if value.get("event_kind") not in PROPOSAL_EVENT_KINDS or value.get("status") not in PROPOSAL_STATUSES:
        raise ValueError("proposal lifecycle value is unsupported")
    kind_status = {
        "accepted": "accepted", "deferred": "deferred-unknown", "rejected": "rejected",
        "superseded": "superseded",
    }
    if value["event_kind"] in kind_status and value["status"] != kind_status[value["event_kind"]]:
        raise ValueError("proposal event kind and status conflict")
    if value["event_kind"] in {"suggested", "evidence-updated", "gate-changed"} and value["status"] != "proposed":
        raise ValueError("open proposal event must remain proposed")
    relation_type = value.get("relation_type")
    if relation_type not in {"derived_from", "depends_on", "absorbs"}:
        raise ValueError("proposal relation type is unsupported")
    gate = value.get("required_for")
    if relation_type == "depends_on":
        if gate not in DEPENDENCY_GATES:
            raise ValueError("depends_on proposal requires an explicit gate")
    elif gate is not None:
        raise ValueError("only depends_on may carry required_for")
    _bounded_text(value.get("rationale"), "proposal rationale")
    _bounded_text(value.get("consequence"), "proposal consequence")
    if value.get("fact_scope") not in FACT_SCOPES:
        raise ValueError("proposal fact scope is unsupported")
    proposer = value.get("proposer")
    if not isinstance(proposer, Mapping) or set(proposer) != {"kind", "id", "platform_session_id"}:
        raise ValueError("proposal proposer fields do not match capture schema v2")
    if proposer.get("kind") not in PROPOSER_KINDS:
        raise ValueError("proposal proposer kind is unsupported")
    _identifier(proposer.get("id"), "proposer id")
    if proposer.get("platform_session_id") is not None:
        _identifier(proposer.get("platform_session_id"), "platform_session_id")
    evidence = value.get("evidence")
    if not isinstance(evidence, list) or evidence != _normalize_evidence(evidence):
        raise ValueError("proposal evidence is not normalized")
    _optional_oid(value.get("source_head_oid"), "source_head_oid")
    _optional_oid(value.get("target_head_oid"), "target_head_oid")
    context = _normalize_absorbs_context(value.get("absorbs_context"))
    if relation_type == "absorbs" and context is None:
        raise ValueError("absorbs proposal requires closure, Validation, scope, and responsibility context")
    if relation_type != "absorbs" and context is not None:
        raise ValueError("only absorbs may carry absorbs_context")
    _timestamp(value.get("recorded_at"))
    prior = _optional_hash(value.get("prior_event_hash"), "prior_event_hash")
    if revision == 1 and prior is not None or revision > 1 and prior is None:
        raise ValueError("proposal prior hash does not match its revision")
    if not isinstance(value.get("writes_performed"), bool):
        raise ValueError("proposal writes_performed must be boolean")
    if value.get("event_hash") != _event_hash(value):
        raise ValueError("proposal event hash does not match canonical bytes")


def build_proposal_event(
    *, proposal_id: str, relation_id: str, revision: int, event_kind: str, status: str,
    relation_type: str, source_workstream_id: str, target_workstream_id: str,
    required_for: str | None, rationale: str, consequence: str, fact_scope: str,
    proposer_kind: str, proposer_id: str, platform_session_id: str | None,
    evidence: Sequence[Mapping[str, Any]], source_head_oid: str | None,
    target_head_oid: str | None, absorbs_context: Mapping[str, Any] | None,
    recorded_at: str, prior_event_hash: str | None, writes_performed: bool,
) -> dict[str, Any]:
    seed = {
        "proposal_id": proposal_id, "revision": revision, "event_kind": event_kind,
        "recorded_at": recorded_at, "prior_event_hash": prior_event_hash,
    }
    value: dict[str, Any] = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "workstream-relation-proposal-event",
        "event_id": f"proposal-{_digest(seed)[:24]}",
        "event_hash": "0" * 64,
        "proposal_id": proposal_id,
        "relation_id": relation_id,
        "revision": revision,
        "event_kind": event_kind,
        "status": status,
        "relation_type": relation_type,
        "source_workstream_id": source_workstream_id,
        "target_workstream_id": target_workstream_id,
        "required_for": required_for,
        "rationale": rationale,
        "consequence": consequence,
        "fact_scope": fact_scope,
        "proposer": {"kind": proposer_kind, "id": proposer_id, "platform_session_id": platform_session_id},
        "evidence": _normalize_evidence(evidence),
        "source_head_oid": source_head_oid,
        "target_head_oid": target_head_oid,
        "absorbs_context": _normalize_absorbs_context(absorbs_context),
        "recorded_at": recorded_at,
        "prior_event_hash": prior_event_hash,
        "writes_performed": writes_performed,
    }
    value["event_hash"] = _event_hash(value)
    validate_proposal_event(value)
    return value


def _load_proposal_history(project_root: Path, proposal_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    root = capture_storage_root(project_root)
    histories: dict[str, list[dict[str, Any]]] = {}
    for path in _event_files(root, "proposals", proposal_id):
        value = _read_regular_json(path)
        validate_proposal_event(value)
        file_match = _EVENT_FILE.fullmatch(path.name)
        assert file_match is not None
        if int(file_match.group(1)) != value["revision"] or file_match.group(2) != value["event_id"]:
            raise ValueError("proposal event filename does not match event identity")
        histories.setdefault(value["proposal_id"], []).append(value)
    for identifier, events in histories.items():
        events.sort(key=lambda item: item["revision"])
        if [item["revision"] for item in events] != list(range(1, len(events) + 1)):
            raise ValueError(f"proposal revision history has a gap: {identifier}")
        for index, event in enumerate(events):
            expected_prior = None if index == 0 else events[index - 1]["event_hash"]
            if event["prior_event_hash"] != expected_prior:
                raise ValueError(f"proposal event hash chain is broken: {identifier}")
    return histories


def _append_proposal(project_root: Path, value: Mapping[str, Any], *, expected_revision: int) -> dict[str, Any]:
    validate_proposal_event(value)
    histories = _load_proposal_history(project_root, str(value["proposal_id"]))
    current = histories.get(str(value["proposal_id"]), [])
    if len(current) != expected_revision or value["revision"] != expected_revision + 1:
        raise ValueError("proposal revision changed; refresh and retry with current CAS revision")
    expected_prior = None if not current else current[-1]["event_hash"]
    if value["prior_event_hash"] != expected_prior:
        raise ValueError("proposal prior hash changed; refresh and retry")
    path = _append_json(
        capture_storage_root(project_root), "proposals", str(value["proposal_id"]),
        int(value["revision"]), str(value["event_id"]), value,
    )
    return {"event": dict(value), "event_path": str(path), "writes_performed": True, "network_performed": False}


def _validate_series_event(value: Mapping[str, Any]) -> None:
    expected = {
        "schema_version", "contract_type", "event_id", "event_hash", "revision",
        "workstream_id", "series_id", "task_code", "series_order",
        "series_predecessor_workstream_id", "suggested_required_for", "actor",
        "recorded_at", "prior_event_hash", "writes_performed",
    }
    if set(value) != expected:
        raise ValueError("task series event fields do not match capture schema v2")
    _reject_forbidden_fields(value)
    if value.get("schema_version") != CAPTURE_SCHEMA_VERSION or value.get("contract_type") != "workstream-task-series-event":
        raise ValueError("unsupported task series contract")
    for field in ("event_id", "workstream_id", "series_id", "task_code", "actor"):
        _identifier(value.get(field), field)
    revision = value.get("revision")
    order = value.get("series_order")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValueError("task series revision must be positive")
    if not isinstance(order, int) or isinstance(order, bool) or not 0 <= order <= MAX_SERIES_ORDER:
        raise ValueError("series_order must be a bounded non-negative integer")
    predecessor = value.get("series_predecessor_workstream_id")
    if predecessor is not None:
        _identifier(predecessor, "series_predecessor_workstream_id")
        if predecessor == value["workstream_id"]:
            raise ValueError("task series predecessor cannot reference itself")
    gate = value.get("suggested_required_for")
    if predecessor is None and gate is not None:
        raise ValueError("series gate requires an explicit predecessor")
    if predecessor is not None and gate not in DEPENDENCY_GATES:
        raise ValueError("explicit series predecessor requires a suggested gate")
    prior = _optional_hash(value.get("prior_event_hash"), "prior_event_hash")
    if revision == 1 and prior is not None or revision > 1 and prior is None:
        raise ValueError("task series prior hash does not match revision")
    _timestamp(value.get("recorded_at"))
    if value.get("writes_performed") is not True or value.get("event_hash") != _event_hash(value):
        raise ValueError("task series event hash/write marker is invalid")


def _series_history(project_root: Path, workstream_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    histories: dict[str, list[dict[str, Any]]] = {}
    for path in _event_files(capture_storage_root(project_root), "series", workstream_id):
        value = _read_regular_json(path)
        _validate_series_event(value)
        histories.setdefault(str(value["workstream_id"]), []).append(value)
    for identifier, events in histories.items():
        events.sort(key=lambda item: item["revision"])
        if [item["revision"] for item in events] != list(range(1, len(events) + 1)):
            raise ValueError(f"task series revision history has a gap: {identifier}")
        for index, event in enumerate(events):
            expected_prior = None if index == 0 else events[index - 1]["event_hash"]
            if event["prior_event_hash"] != expected_prior:
                raise ValueError(f"task series hash chain is broken: {identifier}")
    return histories


def register_task_series(
    project_root: Path, *, workstream_id: str, series_id: str, task_code: str,
    series_order: int, series_predecessor_workstream_id: str | None = None,
    suggested_required_for: str | None = None, actor: str = "workstream-registration",
    recorded_at: str | None = None,
    proposal_observed_head_oids: tuple[str | None, str | None] | None = None,
) -> dict[str, Any]:
    """Append explicit display grouping and optionally suggest, never infer, a predecessor edge."""
    identifier = _identifier(workstream_id, "workstream_id")
    histories = _series_history(project_root, identifier)
    current = histories.get(identifier, [])
    semantic = {
        "series_id": series_id, "task_code": task_code, "series_order": series_order,
        "series_predecessor_workstream_id": series_predecessor_workstream_id,
        "suggested_required_for": suggested_required_for,
    }
    if current and all(current[-1].get(key) == value for key, value in semantic.items()):
        event = current[-1]
        series_written = False
    else:
        revision = len(current) + 1
        event = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "contract_type": "workstream-task-series-event",
            "event_id": f"series-{_digest({'workstream': identifier, 'revision': revision, **semantic})[:24]}",
            "event_hash": "0" * 64,
            "revision": revision,
            "workstream_id": identifier,
            **semantic,
            "actor": actor,
            "recorded_at": _timestamp(recorded_at),
            "prior_event_hash": None if not current else current[-1]["event_hash"],
            "writes_performed": True,
        }
        event["event_hash"] = _event_hash(event)
        _validate_series_event(event)
        _append_json(capture_storage_root(project_root), "series", identifier, revision, event["event_id"], event)
        series_written = True
    proposal: dict[str, Any] | None = None
    predecessor = event["series_predecessor_workstream_id"]
    if predecessor is not None:
        proposal_id = f"series-predecessor-{_digest({'source': identifier, 'target': predecessor})[:24]}"
        existing = _load_proposal_history(project_root, proposal_id).get(proposal_id, [])
        if existing:
            proposal = {"event": existing[-1], "writes_performed": False, "idempotent": True}
        else:
            proposal = suggest_relation(
                project_root, proposal_id=proposal_id, relation_type="depends_on",
                source_workstream_id=identifier, target_workstream_id=str(predecessor),
                required_for=str(event["suggested_required_for"]),
                rationale="explicit task-series predecessor supplied by registration",
                consequence="同系列前序只是一条待确认建议；确认前不形成依赖或阻塞",
                proposer_kind="tool", proposer_id=actor,
                evidence=[evidence_reference(
                    category="workstream-session", reference=f"git-private-series:{identifier}", fact_scope="local-only"
                )], recorded_at=recorded_at, observed_head_oids=proposal_observed_head_oids,
            )
    return {
        "series": dict(event), "proposal": proposal,
        "writes_performed": series_written or bool(proposal and proposal.get("writes_performed")),
        "effective_relation_created": False, "name_inference_performed": False,
    }


def inspect_task_series(project_root: Path) -> dict[str, Any]:
    histories = _series_history(project_root)
    items = [dict(events[-1]) for _, events in sorted(histories.items())]
    return {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "workstream-task-series-inspection",
        "items": items,
        "series": sorted({item["series_id"] for item in items}),
        "read_only": True, "writes_performed": False, "name_inference_performed": False,
    }


def _session_index(project_root: Path) -> dict[str, dict[str, Any]]:
    from .collaboration import _read_workstream_session, _status_snapshot, _worktree_records, worktree_session_path

    result: dict[str, dict[str, Any]] = {}
    for record in _worktree_records(Path(project_root)):
        path = Path(str(record.get("worktree", "")))
        if not path.is_dir():
            continue
        try:
            session = _read_workstream_session(worktree_session_path(path))
        except (OSError, ValueError):
            continue
        if not isinstance(session, Mapping) or not isinstance(session.get("workstream_id"), str):
            continue
        identifier = str(session["workstream_id"])
        if identifier in result:
            raise ValueError("multiple current Workstream sessions share one ID")
        reported_head = str(record.get("HEAD") or "").lower()
        reported_branch = record.get("branch")
        try:
            dirty_fingerprint = _status_snapshot(path)["dirty_fingerprint"]
        except ValueError:
            dirty_fingerprint = None
        current = (
            session.get("head") == reported_head
            and session.get("branch") == reported_branch
            and session.get("dirty_fingerprint") == dirty_fingerprint
        )
        result[identifier] = {
            "record": dict(session),
            "state": "current" if current else "stale",
            "evidence_freshness": session.get("evidence_freshness", "unknown"),
        }
    return result


def _endpoint_heads(project_root: Path, source: str, target: str) -> tuple[str | None, str | None]:
    sessions = _session_index(project_root)
    source_snapshot = sessions.get(source, {})
    target_snapshot = sessions.get(target, {})
    source_session = source_snapshot.get("record", {})
    target_session = target_snapshot.get("record", {})
    source_head = source_session.get("head") if isinstance(source_session, Mapping) else None
    target_head = target_session.get("head") if isinstance(target_session, Mapping) else None
    return (
        source_head if source_snapshot.get("state") == "current" and isinstance(source_head, str) and _OID.fullmatch(source_head) else None,
        target_head if target_snapshot.get("state") == "current" and isinstance(target_head, str) and _OID.fullmatch(target_head) else None,
    )


def suggest_relation(
    project_root: Path, *, proposal_id: str, relation_type: str,
    source_workstream_id: str, target_workstream_id: str, required_for: str | None,
    rationale: str, consequence: str, proposer_kind: str, proposer_id: str,
    fact_scope: str = "worktree", platform_session_id: str | None = None,
    evidence: Sequence[Mapping[str, Any]] = (), absorbs_context: Mapping[str, Any] | None = None,
    recorded_at: str | None = None,
    observed_head_oids: tuple[str | None, str | None] | None = None,
) -> dict[str, Any]:
    """Append a human/tool/Agent suggestion.  Suggestions never gain authority."""
    identifier = _identifier(proposal_id, "proposal_id")
    _identifier(proposer_id, "proposer_id")
    if proposer_kind not in PROPOSER_KINDS:
        raise ValueError("unsupported proposer kind")
    if observed_head_oids is None:
        source_head, target_head = _endpoint_heads(project_root, source_workstream_id, target_workstream_id)
    else:
        if len(observed_head_oids) != 2:
            raise ValueError("observed proposal head evidence must contain source and target OIDs")
        source_head = _optional_oid(observed_head_oids[0], "observed source head OID")
        target_head = _optional_oid(observed_head_oids[1], "observed target head OID")
    relation_id = f"relation-{_digest({'proposal_id': identifier, 'source': source_workstream_id, 'target': target_workstream_id})[:24]}"
    value = build_proposal_event(
        proposal_id=identifier, relation_id=relation_id, revision=1, event_kind="suggested",
        status="proposed", relation_type=relation_type, source_workstream_id=source_workstream_id,
        target_workstream_id=target_workstream_id, required_for=required_for,
        rationale=rationale, consequence=consequence, fact_scope=fact_scope,
        proposer_kind=proposer_kind, proposer_id=proposer_id,
        platform_session_id=platform_session_id, evidence=evidence,
        source_head_oid=source_head, target_head_oid=target_head,
        absorbs_context=absorbs_context, recorded_at=_timestamp(recorded_at),
        prior_event_hash=None, writes_performed=True,
    )
    result = _append_proposal(project_root, value, expected_revision=0)
    result["authority_granted"] = False
    result["effective_relation_created"] = False
    return result


def _next_proposal_event(
    project_root: Path, proposal_id: str, *, expected_revision: int, event_kind: str,
    status: str, required_for: str | None = None, reason: str,
    actor_kind: str, actor_id: str, recorded_at: str | None = None,
) -> dict[str, Any]:
    histories = _load_proposal_history(project_root, proposal_id)
    events = histories.get(proposal_id)
    if not events:
        raise ValueError("proposal does not exist")
    current = events[-1]
    if current["revision"] != expected_revision:
        raise ValueError("proposal revision changed; refresh and retry")
    if current["status"] != "proposed":
        raise ValueError("only a current proposed relation can be decided")
    gate = current["required_for"] if required_for is None else required_for
    value = build_proposal_event(
        proposal_id=proposal_id, relation_id=current["relation_id"], revision=expected_revision + 1,
        event_kind=event_kind, status=status, relation_type=current["relation_type"],
        source_workstream_id=current["source_workstream_id"], target_workstream_id=current["target_workstream_id"],
        required_for=gate, rationale=reason, consequence=current["consequence"],
        fact_scope=current["fact_scope"], proposer_kind=actor_kind, proposer_id=actor_id,
        platform_session_id=None, evidence=current["evidence"], source_head_oid=current["source_head_oid"],
        target_head_oid=current["target_head_oid"], absorbs_context=current["absorbs_context"],
        recorded_at=_timestamp(recorded_at), prior_event_hash=current["event_hash"], writes_performed=True,
    )
    return _append_proposal(project_root, value, expected_revision=expected_revision)


def _require_local_human_decision(caller_kind: str, caller_context: str, local_confirmation: bool) -> None:
    if caller_kind != "human" or caller_context != "local" or local_confirmation is not True:
        raise PermissionError("proposal decisions require a local human confirmation")


def change_proposal_gate(project_root: Path, proposal_id: str, *, expected_revision: int, required_for: str, actor_id: str, reason: str, caller_kind: str = "human", caller_context: str = "local", local_confirmation: bool = True, recorded_at: str | None = None) -> dict[str, Any]:
    _require_local_human_decision(caller_kind, caller_context, local_confirmation)
    return _next_proposal_event(
        project_root, proposal_id, expected_revision=expected_revision, event_kind="gate-changed",
        status="proposed", required_for=required_for, reason=reason, actor_kind="human",
        actor_id=actor_id, recorded_at=recorded_at,
    )


def defer_proposal(project_root: Path, proposal_id: str, *, expected_revision: int, actor_id: str, reason: str, caller_kind: str = "human", caller_context: str = "local", local_confirmation: bool = True, recorded_at: str | None = None) -> dict[str, Any]:
    _require_local_human_decision(caller_kind, caller_context, local_confirmation)
    return _next_proposal_event(
        project_root, proposal_id, expected_revision=expected_revision, event_kind="deferred",
        status="deferred-unknown", reason=reason, actor_kind="human", actor_id=actor_id,
        recorded_at=recorded_at,
    )


def reject_proposal(project_root: Path, proposal_id: str, *, expected_revision: int, actor_id: str, reason: str, caller_kind: str = "human", caller_context: str = "local", local_confirmation: bool = True, recorded_at: str | None = None) -> dict[str, Any]:
    _require_local_human_decision(caller_kind, caller_context, local_confirmation)
    return _next_proposal_event(
        project_root, proposal_id, expected_revision=expected_revision, event_kind="rejected",
        status="rejected", reason=reason, actor_kind="human", actor_id=actor_id,
        recorded_at=recorded_at,
    )


def _project_identity(project_root: Path) -> tuple[str, str, str, str]:
    from .collaboration import inspect_worktree_status

    status = inspect_worktree_status(Path(project_root))
    session = status["session"].get("record") or {}
    project_mode = str(session.get("project_mode") or "personal")
    owner_id = str(session.get("member_id") or "local-owner")
    host_id = str(session.get("host_id") or "local-host")
    try:
        from .team import load_team_config, project_fingerprint

        project_id = project_fingerprint(Path(project_root))
        team = load_team_config(Path(project_root))
        if team.get("enabled"):
            project_mode = "team"
            owner_id = str(team.get("member_id") or owner_id)
            host_id = str(team.get("host_id") or host_id)
    except (ImportError, OSError, ValueError):
        project_id = _digest({"git_common_private": str(capture_storage_root(project_root).parent.parent), "owner": owner_id})
    return project_id, project_mode, owner_id, host_id


def _role_keys() -> set[str]:
    return {
        "schema_version", "contract_type", "event_id", "event_hash", "revision", "member_id",
        "role", "status", "project_id", "project_mode", "actor", "recorded_at",
        "prior_event_hash", "writes_performed",
    }


def validate_role_event(value: Mapping[str, Any]) -> None:
    if set(value) != _role_keys():
        raise ValueError("role event fields do not match capture schema v2")
    _reject_forbidden_fields(value)
    if value.get("schema_version") != CAPTURE_SCHEMA_VERSION or value.get("contract_type") != "human-integrator-role-event":
        raise ValueError("unsupported integrator role contract")
    _identifier(value.get("event_id"), "event_id")
    _identifier(value.get("member_id"), "member_id")
    revision = value.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValueError("role revision must be positive")
    if value.get("role") != "integrator" or value.get("status") not in ROLE_STATUSES:
        raise ValueError("unsupported human role event")
    if not isinstance(value.get("project_id"), str) or not _HASH.fullmatch(value["project_id"]):
        raise ValueError("role event project_id must be a project fingerprint")
    if value.get("project_mode") != "team":
        raise ValueError("explicit integrator grants/revokes are Team-only")
    actor = value.get("actor")
    if not isinstance(actor, Mapping) or set(actor) != {"kind", "member_id", "host_id", "local"}:
        raise ValueError("role actor fields do not match capture schema v2")
    if actor.get("kind") != "human" or actor.get("local") is not True:
        raise ValueError("only a local human owner may change integrator roles")
    _identifier(actor.get("member_id"), "role actor member_id")
    _identifier(actor.get("host_id"), "role actor host_id")
    _timestamp(value.get("recorded_at"))
    prior = _optional_hash(value.get("prior_event_hash"), "prior_event_hash")
    if revision == 1 and prior is not None or revision > 1 and prior is None:
        raise ValueError("role prior hash does not match revision")
    if value.get("event_hash") != _event_hash(value):
        raise ValueError("role event hash does not match canonical bytes")
    if value.get("writes_performed") is not True:
        raise ValueError("persisted role event must declare its write")


def _load_roles(project_root: Path) -> list[dict[str, Any]]:
    root = capture_storage_root(project_root)
    events: list[dict[str, Any]] = []
    for path in _event_files(root, "roles", "registry"):
        value = _read_regular_json(path)
        validate_role_event(value)
        events.append(value)
    events.sort(key=lambda item: item["revision"])
    if [item["revision"] for item in events] != list(range(1, len(events) + 1)):
        raise ValueError("integrator role revision history has a gap")
    for index, event in enumerate(events):
        expected = None if index == 0 else events[index - 1]["event_hash"]
        if event["prior_event_hash"] != expected:
            raise ValueError("integrator role hash chain is broken")
    return events


def inspect_integrator_roles(project_root: Path) -> dict[str, Any]:
    project_id, mode, owner_id, host_id = _project_identity(project_root)
    events = _load_roles(project_root)
    integrators = {owner_id}
    for event in events:
        if event["project_id"] != project_id:
            raise ValueError("integrator role event belongs to another project identity")
        if event["status"] == "granted":
            integrators.add(event["member_id"])
        else:
            integrators.discard(event["member_id"])
    if owner_id not in integrators:
        raise ValueError("project owner cannot be removed from the integrator registry")
    return {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "human-integrator-role-projection",
        "project_id": project_id,
        "project_mode": mode,
        "owner_id": owner_id,
        "host_id": host_id,
        "revision": len(events),
        "integrator_member_ids": sorted(integrators),
        "events": events,
        "sole_integrator": len(integrators) == 1,
        "read_only": True,
        "writes_performed": False,
    }


def change_integrator_role(
    project_root: Path, *, member_id: str, action: str, actor_id: str,
    expected_revision: int, caller_kind: str = "human", caller_context: str = "local",
    recorded_at: str | None = None,
) -> dict[str, Any]:
    roles = inspect_integrator_roles(project_root)
    if roles["project_mode"] != "team":
        raise ValueError("explicit integrator role changes require Team Mode")
    if caller_kind != "human" or caller_context != "local" or actor_id != roles["owner_id"]:
        raise PermissionError("only the local human project owner may change integrator roles")
    if roles["revision"] != expected_revision:
        raise ValueError("integrator role revision changed; refresh and retry")
    target = _identifier(member_id, "integrator member_id")
    if target == roles["owner_id"] and action == "revoke":
        raise ValueError("the project owner must remain an integrator")
    if action not in {"grant", "revoke"}:
        raise ValueError("integrator role action must be grant or revoke")
    before = set(roles["integrator_member_ids"])
    if action == "grant" and target != roles["owner_id"]:
        from .team import _coordinator_path, _read_json

        coordinator = _read_json(_coordinator_path(Path(project_root)), required=False)
        member = coordinator.get("members", {}).get(target) if isinstance(coordinator.get("members"), Mapping) else None
        if (
            not isinstance(member, Mapping)
            or member.get("member_kind") != "human"
            or member.get("status") != "active"
            or member.get("credential_state") != "active"
        ):
            raise PermissionError("integrator grant requires a verified active human project member")
    if action == "grant" and target in before or action == "revoke" and target not in before:
        return {"roles": roles, "writes_performed": False, "network_performed": False, "idempotent": True}
    revision = expected_revision + 1
    value: dict[str, Any] = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "human-integrator-role-event",
        "event_id": f"role-{_digest({'member': target, 'action': action, 'revision': revision})[:24]}",
        "event_hash": "0" * 64,
        "revision": revision,
        "member_id": target,
        "role": "integrator",
        "status": "granted" if action == "grant" else "revoked",
        "project_id": roles["project_id"],
        "project_mode": "team",
        "actor": {"kind": "human", "member_id": actor_id, "host_id": roles["host_id"], "local": True},
        "recorded_at": _timestamp(recorded_at),
        "prior_event_hash": None if not roles["events"] else roles["events"][-1]["event_hash"],
        "writes_performed": True,
    }
    value["event_hash"] = _event_hash(value)
    validate_role_event(value)
    path = _append_json(capture_storage_root(project_root), "roles", "registry", revision, value["event_id"], value)
    current = inspect_integrator_roles(project_root)
    if not current["integrator_member_ids"]:
        raise ValueError("integrator registry cannot become empty")
    return {"event": value, "event_path": str(path), "roles": current, "writes_performed": True, "network_performed": False}


def _confirmation_keys() -> set[str]:
    return {
        "schema_version", "contract_type", "confirmation_id", "event_hash", "proposal_id",
        "proposal_revision", "proposal_event_hash", "decision", "relation_type", "required_for",
        "confirmer", "evidence_snapshot_hash", "effective_relation_id", "effective_relation_event_id",
        "effective_relation_hash", "confirmed_at", "writes_performed",
    }


def validate_confirmation_event(value: Mapping[str, Any]) -> None:
    if set(value) != _confirmation_keys():
        raise ValueError("confirmation fields do not match capture schema v2")
    _reject_forbidden_fields(value)
    if value.get("schema_version") != CAPTURE_SCHEMA_VERSION or value.get("contract_type") != "workstream-relation-confirmation-event":
        raise ValueError("unsupported relation confirmation contract")
    for field in ("confirmation_id", "proposal_id", "effective_relation_id", "effective_relation_event_id"):
        _identifier(value.get(field), field)
    if not isinstance(value.get("proposal_revision"), int) or value["proposal_revision"] < 1:
        raise ValueError("confirmation proposal revision must be positive")
    for field in ("proposal_event_hash", "evidence_snapshot_hash", "effective_relation_hash", "event_hash"):
        if not isinstance(value.get(field), str) or not _HASH.fullmatch(value[field]):
            raise ValueError(f"confirmation {field} must be a SHA-256 hash")
    if value.get("decision") != "accept" or value.get("relation_type") not in {"derived_from", "depends_on", "absorbs"}:
        raise ValueError("confirmation decision or relation type is unsupported")
    gate = value.get("required_for")
    if value["relation_type"] == "depends_on":
        if gate not in DEPENDENCY_GATES:
            raise ValueError("confirmed dependency requires a gate")
    elif gate is not None:
        raise ValueError("only dependency confirmation may carry required_for")
    confirmer = value.get("confirmer")
    if not isinstance(confirmer, Mapping) or set(confirmer) != {
        "kind", "member_id", "role", "host_id", "project_id", "authority_revision", "local"
    }:
        raise ValueError("confirmation actor fields do not match capture schema v2")
    if confirmer.get("kind") != "human" or confirmer.get("local") is not True:
        raise ValueError("only a local human may confirm a relation")
    for field in ("member_id", "host_id"):
        _identifier(confirmer.get(field), f"confirmer {field}")
    if confirmer.get("role") not in {"task-owner", "integrator"}:
        raise ValueError("confirmation role is unsupported")
    if not isinstance(confirmer.get("project_id"), str) or not _HASH.fullmatch(confirmer["project_id"]):
        raise ValueError("confirmation project identity is invalid")
    if not isinstance(confirmer.get("authority_revision"), int) or confirmer["authority_revision"] < 0:
        raise ValueError("confirmation authority revision must be non-negative")
    _timestamp(value.get("confirmed_at"))
    if value.get("writes_performed") is not True:
        raise ValueError("persisted confirmation must declare its write")
    if value.get("event_hash") != _event_hash(value):
        raise ValueError("confirmation event hash does not match canonical bytes")


def _confirmation_history(project_root: Path, proposal_id: str | None = None) -> list[dict[str, Any]]:
    root = capture_storage_root(project_root)
    result: list[dict[str, Any]] = []
    for path in _event_files(root, "confirmations", proposal_id):
        value = _read_regular_json(path)
        validate_confirmation_event(value)
        result.append(value)
    result.sort(key=lambda item: (item["proposal_id"], item["proposal_revision"], item["confirmation_id"]))
    return result


def _authority_for_proposal(project_root: Path, proposal: Mapping[str, Any], member_id: str, claimed_role: str) -> dict[str, Any]:
    roles = inspect_integrator_roles(project_root)
    sessions = _session_index(project_root)
    source = sessions.get(str(proposal["source_workstream_id"]), {}).get("record", {})
    owner_id = source.get("member_id") if isinstance(source, Mapping) else None
    gate = proposal.get("required_for")
    needs_integrator = proposal["relation_type"] == "absorbs" or gate in {"integration", "release"}
    required_role = "integrator" if needs_integrator else "task-owner"
    if claimed_role != required_role:
        raise PermissionError(f"relation confirmation requires the {required_role} role")
    if required_role == "integrator":
        if not roles["integrator_member_ids"]:
            raise PermissionError("no current human integrator is available")
        if member_id not in roles["integrator_member_ids"]:
            raise PermissionError("confirmer is not a current human integrator")
    elif owner_id != member_id:
        raise PermissionError("implementation/validation dependency requires the source task owner")
    return roles


def _effective_relation_for_proposal(project_root: Path, proposal: Mapping[str, Any], actor_id: str, recorded_at: str) -> dict[str, Any]:
    sessions = _session_index(project_root)
    for endpoint in (str(proposal["source_workstream_id"]), str(proposal["target_workstream_id"])):
        if sessions.get(endpoint, {}).get("evidence_freshness") != "current":
            raise ValueError("relation endpoints require current evidence freshness before acceptance")
    source_head, target_head = _endpoint_heads(
        project_root, str(proposal["source_workstream_id"]), str(proposal["target_workstream_id"])
    )
    if source_head is None or target_head is None:
        raise ValueError("relation endpoints must have current local session evidence before acceptance")
    if source_head != proposal["source_head_oid"] or target_head != proposal["target_head_oid"]:
        raise ValueError("proposal endpoint evidence drifted; supersede and suggest a fresh proposal")
    relation_type = str(proposal["relation_type"])
    evidence = default_relation_evidence(
        status="confirmed",
        source_head_oid=source_head,
        target_head_oid=target_head,
        source_head_status="current",
        target_head_status="current",
        scope_status="current",
        ancestry_status="not-applicable",
        dependency_status="confirmed" if relation_type == "depends_on" else "not-applicable",
        ownership_transfer_status="not-applicable",
    )
    if relation_type == "derived_from":
        evidence.update({
            "task_base_oid": target_head,
            "ancestry_status": "confirmed",
            "target_unique_commits_after_base": 0,
        })
    if relation_type == "absorbs":
        context = proposal.get("absorbs_context") or {}
        if context.get("target_closure") not in {"closed", "integrated"}:
            sessions = _session_index(project_root)
            target = sessions.get(str(proposal["target_workstream_id"]), {}).get("record", {})
            if target.get("runtime_condition") != "paused":
                raise ValueError("absorbs requires a closed/integrated target or an explicitly paused takeover target")
        evidence.update({
            "ownership_transfer_oid": target_head,
            "ownership_transfer_status": "confirmed",
            "target_unique_commits_after_base": 0,
        })
    event_id = f"effective-{_digest({'proposal': proposal['event_hash'], 'recorded_at': recorded_at})[:24]}"
    return build_relation_record(
        relation_id=str(proposal["relation_id"]), event_id=event_id, revision=1,
        relation_type=relation_type, source_workstream_id=str(proposal["source_workstream_id"]),
        target_workstream_id=str(proposal["target_workstream_id"]), lifecycle="active",
        recorded_at=recorded_at, actor_kind="human", actor_id=actor_id, origin="native",
        reason=str(proposal["rationale"]), evidence=evidence,
        source_links=[{"kind": "relation", "ref": f"capture-v2:{proposal['proposal_id']}:{proposal['revision']}"}],
        writes_performed=True,
    )


def accept_proposal(
    project_root: Path, proposal_id: str, *, expected_revision: int, confirmer_id: str,
    confirmer_role: str, caller_kind: str = "human", caller_context: str = "local",
    local_confirmation: bool = True, recorded_at: str | None = None,
) -> dict[str, Any]:
    if caller_kind != "human" or caller_context != "local" or local_confirmation is not True:
        raise PermissionError("Agent/session/remote request-only callers cannot confirm relations")
    histories = _load_proposal_history(project_root, proposal_id)
    events = histories.get(proposal_id)
    if not events:
        raise ValueError("proposal does not exist")
    proposal = events[-1]
    if proposal["revision"] != expected_revision:
        raise ValueError("proposal revision changed; refresh and retry")
    if proposal["status"] != "proposed":
        raise ValueError("only a current proposed relation can be accepted")
    roles = _authority_for_proposal(project_root, proposal, confirmer_id, confirmer_role)
    timestamp = _timestamp(recorded_at)
    effective = _effective_relation_for_proposal(project_root, proposal, confirmer_id, timestamp)
    existing = load_relation_history(Path(project_root))["current_records"]
    candidate_graph = build_relation_graph([*existing, effective])
    if not candidate_graph["validation"]["valid"]:
        codes = ",".join(item["code"] for item in candidate_graph["validation"]["errors"])
        raise ValueError(f"accepted relation would violate the Core DAG: {codes}")
    accepted = build_proposal_event(
        proposal_id=proposal_id, relation_id=proposal["relation_id"], revision=expected_revision + 1,
        event_kind="accepted", status="accepted", relation_type=proposal["relation_type"],
        source_workstream_id=proposal["source_workstream_id"], target_workstream_id=proposal["target_workstream_id"],
        required_for=proposal["required_for"], rationale=proposal["rationale"], consequence=proposal["consequence"],
        fact_scope=proposal["fact_scope"], proposer_kind="human", proposer_id=confirmer_id,
        platform_session_id=None, evidence=proposal["evidence"], source_head_oid=proposal["source_head_oid"],
        target_head_oid=proposal["target_head_oid"], absorbs_context=proposal["absorbs_context"],
        recorded_at=timestamp, prior_event_hash=proposal["event_hash"], writes_performed=True,
    )
    # Proposal CAS is the serialization point.  A competing confirmer with the
    # old revision is rejected before any effective relation write.
    accepted_result = _append_proposal(project_root, accepted, expected_revision=expected_revision)
    relation_result = append_relation_event(Path(project_root), effective)
    evidence_snapshot_hash = _digest({
        "proposal_event_hash": proposal["event_hash"],
        "evidence": proposal["evidence"],
        "source_head_oid": proposal["source_head_oid"],
        "target_head_oid": proposal["target_head_oid"],
    })
    confirmation: dict[str, Any] = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "workstream-relation-confirmation-event",
        "confirmation_id": f"confirm-{_digest({'proposal': proposal_id, 'revision': expected_revision, 'actor': confirmer_id})[:24]}",
        "event_hash": "0" * 64,
        "proposal_id": proposal_id,
        "proposal_revision": expected_revision,
        "proposal_event_hash": proposal["event_hash"],
        "decision": "accept",
        "relation_type": proposal["relation_type"],
        "required_for": proposal["required_for"],
        "confirmer": {
            "kind": "human", "member_id": confirmer_id, "role": confirmer_role,
            "host_id": roles["host_id"], "project_id": roles["project_id"],
            "authority_revision": roles["revision"], "local": True,
        },
        "evidence_snapshot_hash": evidence_snapshot_hash,
        "effective_relation_id": effective["relation_id"],
        "effective_relation_event_id": effective["event_id"],
        "effective_relation_hash": _digest(effective),
        "confirmed_at": timestamp,
        "writes_performed": True,
    }
    confirmation["event_hash"] = _event_hash(confirmation)
    validate_confirmation_event(confirmation)
    confirmation_path = _append_json(
        capture_storage_root(project_root), "confirmations", proposal_id,
        expected_revision, confirmation["confirmation_id"], confirmation,
    )
    return {
        "proposal": accepted_result["event"],
        "confirmation": confirmation,
        "confirmation_path": str(confirmation_path),
        "effective_relation": relation_result["record"],
        "writes_performed": True,
        "network_performed": False,
        "author_documents_changed": False,
    }


def _proposal_fresh(proposal: Mapping[str, Any], sessions: Mapping[str, Mapping[str, Any]]) -> tuple[bool, list[str]]:
    source_snapshot = sessions.get(str(proposal["source_workstream_id"]), {})
    target_snapshot = sessions.get(str(proposal["target_workstream_id"]), {})
    source_record = source_snapshot.get("record", {})
    target_record = target_snapshot.get("record", {})
    source_head = source_record.get("head") if source_snapshot.get("state") == "current" and isinstance(source_record, Mapping) else None
    target_head = target_record.get("head") if target_snapshot.get("state") == "current" and isinstance(target_record, Mapping) else None
    reasons: list[str] = []
    if source_head is None or target_head is None:
        reasons.append("endpoint-session-unavailable")
    for endpoint, label in (
        (str(proposal["source_workstream_id"]), "source"),
        (str(proposal["target_workstream_id"]), "target"),
    ):
        if sessions.get(endpoint, {}).get("evidence_freshness") != "current":
            reasons.append(f"{label}-evidence-not-current")
    if source_head != proposal.get("source_head_oid"):
        reasons.append("source-head-drift")
    if target_head != proposal.get("target_head_oid"):
        reasons.append("target-head-drift")
    return not reasons, reasons


def inspect_relation_capture(project_root: Path, *, proposal_id: str | None = None) -> dict[str, Any]:
    histories = _load_proposal_history(project_root, proposal_id)
    confirmations = _confirmation_history(project_root, proposal_id)
    confirmation_by_proposal = {item["proposal_id"]: item for item in confirmations}
    roles = inspect_integrator_roles(project_root)
    sessions = _session_index(project_root) if histories else {}
    proposals: list[dict[str, Any]] = []
    effective: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for identifier, events in sorted(histories.items()):
        current = dict(events[-1])
        fresh, freshness_reasons = _proposal_fresh(current, sessions)
        confirmation = confirmation_by_proposal.get(identifier)
        status = current["status"]
        effective_current = status == "accepted" and confirmation is not None and fresh
        projection = {
            "proposal_id": identifier,
            "current": current,
            "history_count": len(events),
            "confirmation": confirmation,
            "fresh": fresh,
            "freshness_reason_codes": freshness_reasons,
            "effective_current_relation": effective_current,
            "display_status": "stale" if status == "accepted" and not fresh else status,
            "local_confirmation": _capability_for_proposal(current, roles, sessions),
        }
        proposals.append(projection)
        if effective_current:
            effective.append(projection)
        elif status == "proposed":
            pending.append(projection)
    legacy_unknown: list[dict[str, Any]] = []
    for record in load_relation_history(Path(project_root))["current_records"]:
        if record["relation_type"] == "depends_on" and not any(
            item["current"]["relation_id"] == record["relation_id"] for item in proposals
        ):
            legacy_unknown.append({
                "relation_id": record["relation_id"],
                "source_workstream_id": record["source_workstream_id"],
                "target_workstream_id": record["target_workstream_id"],
                "required_for": "unknown/unspecified",
                "effective": False,
                "reason_code": "legacy-dependency-gate-unspecified",
            })
    body = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "workstream-relation-capture-inspection",
        "proposals": proposals,
        "pending_proposals": pending,
        "effective_relations": effective,
        "legacy_unknown_dependencies": legacy_unknown,
        "roles": roles,
        "task_series": inspect_task_series(project_root),
        "counts": {
            "proposals": len(proposals), "pending": len(pending), "effective": len(effective),
            "stale": sum(item["display_status"] == "stale" for item in proposals),
            "legacy_unknown": len(legacy_unknown),
        },
        "read_only": True,
        "writes_performed": False,
        "network_performed": False,
        "privacy": {
            "prompt": False, "answer": False, "transcript": False, "source_body": False,
            "diff_body": False, "credentials": False,
        },
    }
    body["inspection_hash"] = _digest(body)
    return body


def local_confirmation_capability(project_root: Path, proposal_id: str) -> dict[str, Any]:
    """Return bounded host-local authority for UI routing; it does not decide the proposal."""
    histories = _load_proposal_history(project_root, proposal_id)
    events = histories.get(proposal_id)
    if not events:
        raise ValueError("proposal does not exist")
    proposal = events[-1]
    roles = inspect_integrator_roles(project_root)
    sessions = _session_index(project_root)
    return _capability_for_proposal(proposal, roles, sessions)


def _capability_for_proposal(
    proposal: Mapping[str, Any], roles: Mapping[str, Any],
    sessions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    source = sessions.get(str(proposal["source_workstream_id"]), {}).get("record", {})
    source_owner = source.get("member_id") if isinstance(source, Mapping) else None
    needs_integrator = proposal["relation_type"] == "absorbs" or proposal.get("required_for") in {"integration", "release"}
    required_role = "integrator" if needs_integrator else "task-owner"
    local_member_id = str(roles["owner_id"])
    allowed = (
        proposal["status"] == "proposed"
        and (
            local_member_id in roles["integrator_member_ids"]
            if needs_integrator else source_owner == local_member_id
        )
    )
    return {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "local-relation-confirmation-capability",
        "proposal_id": proposal["proposal_id"],
        "proposal_revision": proposal["revision"],
        "member_id": local_member_id,
        "required_role": required_role,
        "allowed": allowed,
        "reason_code": "local-human-authority-current" if allowed else "local-human-authority-unavailable",
        "central_request_only": False,
        "read_only": True,
        "writes_performed": False,
    }


def relation_gate_eligibility(project_root: Path, *, source_workstream_id: str, required_for: str) -> dict[str, Any]:
    if required_for not in DEPENDENCY_GATES:
        raise ValueError("required_for gate is unsupported")
    inspection = inspect_relation_capture(project_root)
    sessions = _session_index(project_root)
    blockers: list[dict[str, Any]] = []
    considered: list[str] = []
    for item in inspection["effective_relations"]:
        current = item["current"]
        if (
            current["relation_type"] != "depends_on"
            or current["source_workstream_id"] != source_workstream_id
            or current["required_for"] != required_for
        ):
            continue
        considered.append(current["relation_id"])
        target = sessions.get(current["target_workstream_id"])
        target_record = target.get("record", {}) if target else {}
        satisfied = (
            target is not None
            and target.get("state") == "current"
            and target_record.get("lifecycle_phase") in {"integrated", "closed"}
        )
        if not satisfied:
            blockers.append({
                "relation_id": current["relation_id"],
                "proposal_id": current["proposal_id"],
                "target_workstream_id": current["target_workstream_id"],
                "target_lifecycle_phase": target_record.get("lifecycle_phase", "unknown"),
                "reason_code": "effective-dependency-target-not-complete",
            })
    return {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "contract_type": "workstream-relation-gate-eligibility",
        "source_workstream_id": source_workstream_id,
        "required_for": required_for,
        "eligible": not blockers,
        "blocking_relations": blockers,
        "considered_effective_relation_ids": sorted(considered),
        "proposed_deferred_unknown_block": False,
        "stale_confirmation_block": False,
        "legacy_unspecified_block": False,
        "read_only": True,
        "writes_performed": False,
    }


def auto_capture_derived_from(project_root: Path, session: Mapping[str, Any], *, recorded_at: str | None = None) -> dict[str, Any]:
    """Idempotently append an exact mechanical derived_from relation on registration/rebind."""
    lineage = session.get("lineage")
    if not isinstance(lineage, Mapping) or lineage.get("base_workstream_id") is None:
        return {
            "status": "unknown", "reason_codes": ["explicit-base-workstream-and-task-base-required"],
            "writes_performed": False, "effective_relation_created": False,
        }
    source = _identifier(session.get("workstream_id"), "source workstream_id")
    target = _identifier(lineage.get("base_workstream_id"), "base workstream_id")
    task_base = _optional_oid(lineage.get("task_base_oid"), "task_base_oid")
    source_head = _optional_oid(session.get("head"), "source head")
    sessions = _session_index(project_root)
    target_session = sessions.get(target)
    target_record = target_session.get("record", {}) if target_session else {}
    target_head = target_record.get("head") if isinstance(target_record, Mapping) else None
    relation_id = f"auto-derived-{_digest({'source': source, 'target': target, 'task_base_oid': task_base})[:24]}"
    existing = load_relation_history(Path(project_root))["current_records"]
    exact = next((item for item in existing if item["relation_id"] == relation_id), None)
    if exact is not None:
        return {
            "status": "effective", "reason_codes": ["idempotent-existing-mechanical-relation"],
            "relation": exact, "writes_performed": False, "effective_relation_created": False,
        }
    changed = [
        item for item in existing
        if item["relation_type"] == "derived_from" and item["source_workstream_id"] == source
        and item["lifecycle"] not in {"cancelled", "stale"}
    ]
    if changed:
        return {
            "status": "unknown", "reason_codes": ["derived-base-changed-explicit-rebind-required"],
            "existing_relation_ids": sorted(item["relation_id"] for item in changed),
            "writes_performed": False, "effective_relation_created": False,
        }
    if (
        lineage.get("status") != "current" or task_base is None or source_head is None
        or target_session is None or target_session.get("state") != "current" or target_head != task_base
    ):
        proposal_id = f"auto-derived-unknown-{_digest({'source': source, 'target': target, 'base': task_base})[:20]}"
        try:
            proposal = suggest_relation(
                project_root, proposal_id=proposal_id, relation_type="derived_from",
                source_workstream_id=source, target_workstream_id=target, required_for=None,
                rationale="mechanical lineage could not be verified exactly",
                consequence="Git来源关系保持Unknown；不会从分支名或标题猜测",
                proposer_kind="tool", proposer_id="workstream-registration",
                evidence=[evidence_reference(
                    category="workstream-session", reference=f"git-private:{source}", fact_scope="local-only"
                )], recorded_at=recorded_at,
            )
        except ValueError as exc:
            if "proposal" not in str(exc) and "already exists" not in str(exc):
                raise
            proposal = {"writes_performed": False}
        return {
            "status": "unknown", "reason_codes": ["same-project-exact-base-or-ancestry-unverified"],
            "proposal": proposal, "writes_performed": bool(proposal.get("writes_performed")),
            "effective_relation_created": False,
        }
    from .workstream_relations import _is_ancestor

    if not _is_ancestor(Path(project_root), task_base, source_head):
        return {
            "status": "unknown", "reason_codes": ["task-base-not-ancestor"],
            "writes_performed": False, "effective_relation_created": False,
        }
    timestamp = _timestamp(recorded_at)
    relation = build_relation_record(
        relation_id=relation_id,
        event_id=f"mechanical-{_digest({'relation_id': relation_id, 'head': source_head})[:24]}",
        revision=1, relation_type="derived_from", source_workstream_id=source,
        target_workstream_id=target, lifecycle="active", recorded_at=timestamp,
        actor_kind="tool", actor_id="workstream-registration", origin="native",
        reason="same-project exact task base and local Git ancestry verified",
        evidence=default_relation_evidence(
            status="confirmed", source_head_oid=source_head, target_head_oid=target_head,
            task_base_oid=task_base, source_head_status="current", target_head_status="current",
            scope_status="current", ancestry_status="confirmed", dependency_status="not-applicable",
            ownership_transfer_status="not-applicable", target_unique_commits_after_base=0,
        ),
        source_links=[{"kind": "workstream-session", "ref": f"git-private:{source}"}],
        writes_performed=True,
    )
    graph = build_relation_graph([*existing, relation])
    if not graph["validation"]["valid"]:
        return {
            "status": "unknown", "reason_codes": [item["code"] for item in graph["validation"]["errors"]],
            "writes_performed": False, "effective_relation_created": False,
        }
    appended = append_relation_event(Path(project_root), relation)
    return {
        "status": "effective", "reason_codes": ["same-project-exact-base-and-ancestry-confirmed"],
        "relation": appended["record"], "writes_performed": True, "effective_relation_created": True,
    }


__all__ = [
    "CAPTURE_MAX_FILE_BYTES", "CAPTURE_MAX_FILES", "CAPTURE_MAX_TOTAL_BYTES",
    "CAPTURE_SCHEMA_VERSION", "DEPENDENCY_GATES", "EVIDENCE_CATEGORIES",
    "accept_proposal", "auto_capture_derived_from", "build_proposal_event",
    "capture_storage_root", "change_integrator_role", "change_proposal_gate",
    "defer_proposal", "evidence_reference", "inspect_integrator_roles",
    "inspect_relation_capture", "relation_gate_eligibility", "reject_proposal",
    "suggest_relation", "validate_confirmation_event", "validate_proposal_event",
    "validate_role_event",
]
