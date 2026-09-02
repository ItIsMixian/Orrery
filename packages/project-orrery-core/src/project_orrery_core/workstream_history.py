"""Strict, append-only, Git-common-private Workstream history.

An earlier W7.4 draft wrote every retired archive as a closed summary.  Those
bytes remain untouched under ``records/``.  Corrected records follow the
integrator-owned strict schema and are appended under ``strict-records/``.
Only the strict projection is exposed to consumers.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .subprocess_policy import no_window_options


HISTORY_SCHEMA_VERSION = 1
HISTORY_CONTRACT = "workstream-history-summary"
MAX_RECORD_BYTES = 256 * 1024
MAX_RECORDS = 2048
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_OID = re.compile(r"^[0-9a-f]{40}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_BRANCH = re.compile(r"^refs/heads/[A-Za-z0-9._/-]+$")
_STRICT_RECORD_FILE = re.compile(r"^([1-9][0-9]{0,8})-([0-9a-f]{64})\.json$")
_LIFECYCLES = {"created", "investigating", "implementing", "validating", "review-ready", "integrated", "closed"}
_RUNTIMES = {"active", "waiting-for-user", "paused", "blocked-by-conflict", "failed", "offline", "stale-unknown"}
_CLOSURE_REASONS = {"integrated", "abandoned", "superseded", "duplicate"}
_LINEAGE_STATUSES = {"current", "legacy-unknown", "parent-unverified-unknown"}
_FORBIDDEN_KEYS = {
    "answer", "command", "credential", "diff", "diff_body", "password", "path",
    "prompt", "secret", "shell", "source", "source_body", "token", "transcript",
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _identifier(value: Any, label: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a filesystem-safe identifier")
    return value


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise ValueError(f"{label} must be a bounded timestamp")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return value


def _safe_ref(value: Any, label: str) -> str:
    if (
        not isinstance(value, str) or not value or len(value) > 400
        or any(character in value for character in "\r\n\0")
        or value.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:", value)
    ):
        raise ValueError(f"{label} must be a bounded relative or opaque reference")
    normalized = value.replace("\\", "/")
    if "://" in normalized or any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ValueError(f"{label} escapes the safe evidence boundary")
    return normalized


def _unsafe(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        return True


def history_storage_root(project_root: Path) -> Path:
    root = Path(project_root).resolve()
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
        **no_window_options(),
    )
    if completed.returncode:
        raise ValueError("Workstream history requires a local Git repository")
    common = Path(completed.stdout.strip())
    if not common.is_absolute():
        common = root / common
    return Path(os.path.realpath(common)) / "orrery" / "workstream-history-index-v1"


def _validate_storage_boundary(root: Path) -> None:
    common = root.parent.parent
    if root != common / "orrery" / "workstream-history-index-v1":
        raise ValueError("Workstream history escaped the Git common private boundary")
    for path in (common / "orrery", root):
        if os.path.lexists(path) and (not path.is_dir() or _unsafe(path)):
            raise ValueError("Workstream history ancestors must be real directories")


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in _FORBIDDEN_KEYS or (lowered.endswith("_path") and lowered != "program_path") or lowered.endswith("_body"):
                raise ValueError(f"Workstream history forbids field {key}")
            _reject_forbidden_fields(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_forbidden_fields(child)


def _strict_schema() -> tuple[dict[str, Any], str]:
    path = Path(__file__).with_name("schema") / "workstream-history-index-v1.json"
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    required = {
        "schema_version", "contract_type", "workstream_id", "display", "classification",
        "historical_state", "git", "lineage", "references", "visibility", "revision",
    }
    if (
        not isinstance(value, dict) or set(value.get("required", [])) != required
        or value.get("additionalProperties") is not False
        or value.get("properties", {}).get("contract_type", {}).get("const") != HISTORY_CONTRACT
    ):
        raise ValueError("integrator-owned Workstream history schema is not the strict v1 contract")
    return value, hashlib.sha256(raw).hexdigest()


def _bounded_text(value: Any, label: str, *, nullable: bool = False, maximum: int = 200) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum or any(c in value for c in "\r\n\0"):
        raise ValueError(f"{label} must be bounded single-line text")
    return value


def validate_history_record(value: Mapping[str, Any]) -> None:
    """Validate one record against the strict central schema shape."""
    schema, _schema_hash = _strict_schema()
    if set(value) != set(schema["required"]) or value.get("schema_version") != 1 or value.get("contract_type") != HISTORY_CONTRACT:
        raise ValueError("Workstream history fields do not match the strict schema v1")
    _reject_forbidden_fields(value)
    _identifier(value.get("workstream_id"), "history workstream_id")
    revision = value.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValueError("history revision must be a positive integer")

    display = value.get("display")
    if not isinstance(display, Mapping) or set(display) != {"task_code", "label"}:
        raise ValueError("history display identity is invalid")
    _bounded_text(display.get("task_code"), "history task_code", nullable=True, maximum=64)
    _bounded_text(display.get("label"), "history label")

    classification = value.get("classification")
    if not isinstance(classification, Mapping) or set(classification) != {"primary_subsystem_id", "program_path", "series_id", "series_order"}:
        raise ValueError("history classification is invalid")
    _identifier(classification.get("primary_subsystem_id"), "history primary subsystem", nullable=True)
    program_path = classification.get("program_path")
    if (
        not isinstance(program_path, list) or len(program_path) > 2 or len(program_path) != len(set(program_path))
        or any(_identifier(item, "history program path") != item for item in program_path)
    ):
        raise ValueError("history program path is invalid")
    _identifier(classification.get("series_id"), "history series_id", nullable=True)
    order = classification.get("series_order")
    if order is not None and (not isinstance(order, int) or isinstance(order, bool) or order < 0):
        raise ValueError("history series_order must be a non-negative integer or null")

    historical = value.get("historical_state")
    if not isinstance(historical, Mapping) or set(historical) != {"record_kind", "observed_lifecycle_phase", "runtime_condition", "closure_reason", "captured_at"}:
        raise ValueError("history state is invalid")
    lifecycle, runtime, reason = historical.get("observed_lifecycle_phase"), historical.get("runtime_condition"), historical.get("closure_reason")
    if lifecycle not in _LIFECYCLES or runtime not in _RUNTIMES:
        raise ValueError("history lifecycle/runtime is invalid")
    if lifecycle == "closed":
        if historical.get("record_kind") != "closed-workstream" or reason not in _CLOSURE_REASONS:
            raise ValueError("closed history requires closed-workstream kind and verified reason")
    elif historical.get("record_kind") != "retired-session" or reason is not None:
        raise ValueError("non-closed history must remain a retired-session without closure reason")
    _timestamp(historical.get("captured_at"), "history captured_at")

    git_identity = value.get("git")
    if not isinstance(git_identity, Mapping) or set(git_identity) != {"final_head_oid", "branch_ref"}:
        raise ValueError("history Git identity is invalid")
    if not _OID.fullmatch(str(git_identity.get("final_head_oid"))) or not _BRANCH.fullmatch(str(git_identity.get("branch_ref"))):
        raise ValueError("history Git identity is invalid")

    lineage = value.get("lineage")
    if lineage is not None:
        if not isinstance(lineage, Mapping) or set(lineage) != {"status", "base_workstream_id", "task_base_oid", "validated_head"} or lineage.get("status") not in _LINEAGE_STATUSES:
            raise ValueError("history lineage is invalid")
        base, task_base, validated_head = lineage.get("base_workstream_id"), lineage.get("task_base_oid"), lineage.get("validated_head")
        _identifier(base, "history lineage base", nullable=True)
        for candidate, label in ((task_base, "task base"), (validated_head, "validated head")):
            if candidate is not None and not _OID.fullmatch(str(candidate)):
                raise ValueError(f"history lineage {label} is invalid")
        if lineage.get("status") == "current" and (base is None or not _OID.fullmatch(str(task_base)) or not _OID.fullmatch(str(validated_head))):
            raise ValueError("current history lineage requires exact identities and OIDs")

    references = value.get("references")
    if not isinstance(references, Mapping) or set(references) != {"validation_refs", "relation_ids", "source_evidence_ids"}:
        raise ValueError("history references are invalid")
    for key in references:
        items = references[key]
        if not isinstance(items, list) or len(items) > 128 or items != sorted(set(items)):
            raise ValueError("history reference lists must be bounded, sorted and unique")
        for item in items:
            _safe_ref(item, f"history {key}")
    if value.get("visibility") != "git-private-local-only":
        raise ValueError("history visibility is invalid")


def _legacy_draft_inventory(root: Path) -> dict[str, Any]:
    """Hash rejected draft bytes without accepting them as strict records."""
    records_root = root / "records"
    files = sorted(records_root.glob("*/*.json")) if records_root.exists() else []
    digest = hashlib.sha256()
    for path in files:
        if _unsafe(path) or not path.is_file() or path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("legacy Workstream history draft contains an unsafe record")
        relative, payload = path.relative_to(root).as_posix().encode("utf-8"), path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big")); digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big")); digest.update(payload)
    return {
        "record_count": len(files), "aggregate_sha256": digest.hexdigest(),
        "storage_ref": "git-common:orrery/workstream-history-index-v1/records", "accepted_as_strict": False,
    }


def _read_history(root: Path) -> dict[str, list[dict[str, Any]]]:
    _validate_storage_boundary(root)
    strict_root = root / "strict-records"
    if not strict_root.exists():
        return {}
    if _unsafe(strict_root) or not strict_root.is_dir():
        raise ValueError("strict Workstream history root must be a real directory")
    files = sorted(strict_root.glob("*/*.json"))
    if len(files) > MAX_RECORDS:
        raise ValueError("Workstream history record count exceeds limit")
    result: dict[str, list[dict[str, Any]]] = {}
    for path in files:
        match = _STRICT_RECORD_FILE.fullmatch(path.name)
        if not match or _unsafe(path) or not path.is_file() or path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("Workstream history contains an unsafe strict record")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Workstream history record root must be an object")
        validate_history_record(value)
        identifier = str(value["workstream_id"])
        if path.parent.name != identifier or int(match.group(1)) != int(value["revision"]) or match.group(2) != _digest(value):
            raise ValueError("strict Workstream history filename binding is invalid")
        result.setdefault(identifier, []).append(value)
    for values in result.values():
        values.sort(key=lambda item: int(item["revision"]))
        if [item["revision"] for item in values] != list(range(1, len(values) + 1)):
            raise ValueError("Workstream history revision chain is invalid")
    return result


def inspect_workstream_history(project_root: Path) -> dict[str, Any]:
    root = history_storage_root(project_root)
    histories = _read_history(root)
    records = [dict(values[-1]) for _, values in sorted(histories.items())]
    _schema, schema_hash = _strict_schema()
    kinds = Counter(item["historical_state"]["record_kind"] for item in records)
    lifecycles = Counter(item["historical_state"]["observed_lifecycle_phase"] for item in records)
    legacy = _legacy_draft_inventory(root) if root.exists() else {
        "record_count": 0, "aggregate_sha256": hashlib.sha256().hexdigest(),
        "storage_ref": "git-common:orrery/workstream-history-index-v1/records", "accepted_as_strict": False,
    }
    return {
        "schema_version": 1, "contract_type": "workstream-history-index-inspection",
        "status": "ready" if histories else "unavailable", "records": records,
        "counts": {
            "records": len(records), "revisions": sum(len(values) for values in histories.values()),
            "closed_workstreams": kinds["closed-workstream"], "retired_sessions": kinds["retired-session"],
            "observed_lifecycle": dict(sorted(lifecycles.items())),
        },
        "schema_ref": "project_orrery_core/schema/workstream-history-index-v1.json", "schema_sha256": schema_hash,
        "legacy_draft": legacy, "storage": "git-common-private-append-only-strict",
        "storage_ref": "git-common:orrery/workstream-history-index-v1/strict-records",
        "read_only": True, "writes_performed": False, "network_performed": False, "execution_capability": False,
    }


def _accepted_classification(project_root: Path, workstream_id: str, session: Mapping[str, Any], context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if context is None:
        from .workstream_program_hierarchy import inspect_program_hierarchy
        from .workstream_relation_capture import inspect_task_series
        memberships = {str(item["workstream_id"]): item for item in inspect_program_hierarchy(project_root)["memberships"]}
        series_items = {str(item["workstream_id"]): item for item in inspect_task_series(project_root)["items"]}
    else:
        memberships, series_items = context["memberships"], context["series"]
    membership, series = memberships.get(workstream_id), series_items.get(workstream_id)
    primary = session.get("primary_subsystem_id")
    if not isinstance(primary, str) or not _SAFE_ID.fullmatch(primary):
        primary = None
    return {
        "primary_subsystem_id": primary,
        "program_path": list(membership["group_path"]) if membership else [],
        "series_id": str(series["series_id"]) if series else None,
        "series_order": int(series["series_order"]) if series else None,
    }


def _legacy_archive_envelope(project_root: Path, *, archive_date: str, entry_name: str, session: Mapping[str, Any]) -> dict[str, str]:
    try:
        dt.date.fromisoformat(archive_date)
    except ValueError as exc:
        raise ValueError("legacy archive date is invalid") from exc
    branch_ref = session.get("branch")
    if not isinstance(branch_ref, str) or not _BRANCH.fullmatch(branch_ref):
        raise ValueError("legacy archive branch ref is invalid")
    entry_slug, separator, head_prefix = entry_name.rpartition("-")
    expected_slugs = {branch_ref.removeprefix("refs/heads/").replace("/", "-"), branch_ref.removeprefix("refs/heads/").replace("/", "_")}
    if not separator or entry_slug not in expected_slugs or not (8 <= len(head_prefix) <= 40):
        raise ValueError("legacy archive entry does not bind its branch identity")
    completed = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--verify", f"{head_prefix}^{{commit}}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}, **no_window_options(),
    )
    final_head = completed.stdout.strip().lower()
    if completed.returncode or not _OID.fullmatch(final_head) or not final_head.startswith(head_prefix.lower()):
        raise ValueError("legacy archive retirement HEAD is not an exact local commit")
    return {"branch_ref": branch_ref, "final_head_oid": final_head, "archive_day": f"{archive_date}T00:00:00Z"}


def _captured_at(session: Mapping[str, Any], archive_day: str) -> str:
    transition = session.get("last_transition")
    candidate = transition.get("occurred_at") if isinstance(transition, Mapping) else None
    try:
        return _timestamp(candidate, "history captured_at")
    except (TypeError, ValueError):
        return archive_day


def _lineage_summary(session: Mapping[str, Any]) -> dict[str, Any] | None:
    lineage = session.get("lineage")
    if not isinstance(lineage, Mapping):
        return None
    if lineage.get("status") not in _LINEAGE_STATUSES:
        raise ValueError("legacy archive lineage status is invalid")
    return {key: lineage.get(key) for key in ("status", "base_workstream_id", "task_base_oid", "validated_head")}


def _summary_from_archive(project_root: Path, parsed: Mapping[str, Any], *, archive_date: str, entry_name: str, migration_context: Mapping[str, Any], revision: int) -> dict[str, Any]:
    session, workstream_id = parsed["session"], str(parsed["workstream_id"])
    _identifier(workstream_id, "legacy archive workstream_id")
    envelope = _legacy_archive_envelope(project_root, archive_date=archive_date, entry_name=entry_name, session=session)
    lifecycle, runtime, reason = session.get("lifecycle_phase"), session.get("runtime_condition"), session.get("closure_reason")
    if lifecycle not in _LIFECYCLES or runtime not in _RUNTIMES:
        raise ValueError("legacy archive lifecycle/runtime is outside strict schema")
    if lifecycle == "closed" and reason not in _CLOSURE_REASONS:
        raise ValueError("closed legacy archive lacks a valid closure reason")
    if lifecycle != "closed":
        reason = None
    classification = _accepted_classification(project_root, workstream_id, session, migration_context)
    series_item = migration_context["series"].get(workstream_id)
    validation_refs = sorted({
        str(item).replace("\\", "/") for item in session.get("governing_docs", [])
        if isinstance(item, str) and item.replace("\\", "/").startswith("docs/validation/")
    })
    archive_evidence_hash = _digest({"archive_date": archive_date, "entry_name": entry_name, "session_semantic_hash": parsed["semantic_hash"]})
    record = {
        "schema_version": 1, "contract_type": HISTORY_CONTRACT, "workstream_id": workstream_id,
        "display": {"task_code": str(series_item["task_code"]) if series_item else None, "label": workstream_id},
        "classification": classification,
        "historical_state": {
            "record_kind": "closed-workstream" if lifecycle == "closed" else "retired-session",
            "observed_lifecycle_phase": lifecycle, "runtime_condition": runtime, "closure_reason": reason,
            "captured_at": _captured_at(session, envelope["archive_day"]),
        },
        "git": {"final_head_oid": envelope["final_head_oid"], "branch_ref": envelope["branch_ref"]},
        "lineage": _lineage_summary(session),
        "references": {
            "validation_refs": validation_refs,
            "relation_ids": list(migration_context["relation_ids"].get(workstream_id, [])),
            "source_evidence_ids": [f"retired-session-archive:sha256:{archive_evidence_hash}"],
        },
        "visibility": "git-private-local-only", "revision": revision,
    }
    validate_history_record(record)
    return record


def _migration_context(project_root: Path) -> dict[str, Any]:
    from .workstream_program_hierarchy import inspect_program_hierarchy
    from .workstream_relation_capture import inspect_task_series
    from .workstream_relations import load_relation_history
    relation_ids: dict[str, set[str]] = {}
    for item in load_relation_history(project_root)["current_records"]:
        for endpoint in (item["source_workstream_id"], item["target_workstream_id"]):
            relation_ids.setdefault(str(endpoint), set()).add(str(item["relation_id"]))
    return {
        "relation_ids": {key: sorted(value) for key, value in relation_ids.items()},
        "memberships": {str(item["workstream_id"]): item for item in inspect_program_hierarchy(project_root)["memberships"]},
        "series": {str(item["workstream_id"]): item for item in inspect_task_series(project_root)["items"]},
    }


def preview_legacy_history_migration(project_root: Path) -> dict[str, Any]:
    """Recompute a zero-write strict repair preview from preserved archives."""
    from . import workstream_relations as relations
    root, storage = Path(project_root).resolve(), history_storage_root(project_root)
    existing, context = _read_history(storage), _migration_context(root)
    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    accounted: list[dict[str, str]] = []
    seen: set[str] = set()
    lifecycle_counts: Counter[str] = Counter(); kind_counts: Counter[str] = Counter()
    inventory_records = valid_records = 0
    for archive_date, entry_name, _path, content in relations._archive_session_files(root):
        inventory_records += 1; workstream_id = "unknown"
        try:
            session = relations._decode_archive_session(content)
            workstream_id = str(session.get("workstream_id", "unknown")); prior = existing.get(workstream_id, [])
            record = _summary_from_archive(
                root, {"workstream_id": workstream_id, "session": session, "semantic_hash": _digest(session)},
                archive_date=archive_date, entry_name=entry_name, migration_context=context, revision=len(prior) + 1,
            )
        except ValueError as exc:
            excluded.append({"archive_ref": f"retired-session:{archive_date}:{hashlib.sha256(entry_name.encode()).hexdigest()[:16]}", "workstream_id": workstream_id, "reason_code": str(exc)})
            continue
        valid_records += 1
        if workstream_id in seen:
            excluded.append({"archive_ref": f"retired-session:{archive_date}:{hashlib.sha256(entry_name.encode()).hexdigest()[:16]}", "workstream_id": workstream_id, "reason_code": "duplicate-workstream-identity"})
            continue
        seen.add(workstream_id)
        lifecycle_counts[record["historical_state"]["observed_lifecycle_phase"]] += 1
        kind_counts[record["historical_state"]["record_kind"]] += 1
        if prior and {k: v for k, v in prior[-1].items() if k != "revision"} == {k: v for k, v in record.items() if k != "revision"}:
            accounted.append({"workstream_id": workstream_id, "reason_code": "strict-record-current"}); continue
        candidates.append(record)
    candidates.sort(key=lambda item: (item["historical_state"]["captured_at"], item["workstream_id"]))
    excluded.sort(key=lambda item: (item["workstream_id"], item["archive_ref"], item["reason_code"])); accounted.sort(key=lambda item: item["workstream_id"])
    _schema, schema_hash = _strict_schema()
    legacy = _legacy_draft_inventory(storage) if storage.exists() else {"record_count": 0, "aggregate_sha256": hashlib.sha256().hexdigest(), "storage_ref": "git-common:orrery/workstream-history-index-v1/records", "accepted_as_strict": False}
    return {
        "schema_version": 1, "contract_type": "workstream-history-strict-repair-preview", "schema_sha256": schema_hash,
        "candidates": candidates, "excluded_records": excluded, "accounted_records": accounted, "legacy_draft": legacy,
        "counts": {
            "archive_records": inventory_records, "valid_archive_records": valid_records, "unique_archive_workstreams": len(seen),
            "already_strict": len(accounted), "candidates": len(candidates), "excluded": len(excluded),
            "record_kind": dict(sorted(kind_counts.items())), "observed_lifecycle": dict(sorted(lifecycle_counts.items())),
        },
        "read_only": True, "writes_performed": False, "network_performed": False,
        "archives_changed": False, "relations_changed": False, "legacy_draft_changed": False,
    }


def _ensure_real_directory(path: Path) -> None:
    if path.exists() and (_unsafe(path) or not path.is_dir()):
        raise ValueError("Workstream history write target is unsafe")
    path.mkdir(parents=True, exist_ok=True)


def _exclusive_write(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    try:
        os.write(descriptor, payload); os.fsync(descriptor)
    finally:
        os.close(descriptor)


def apply_legacy_history_migration(project_root: Path, *, expected_preview_hash: str) -> dict[str, Any]:
    """Append one hash-bound strict repair without touching draft/archive bytes."""
    root = Path(project_root).resolve(); preview = preview_legacy_history_migration(root); preview_hash = _digest(preview)
    if expected_preview_hash != preview_hash:
        raise ValueError("Workstream history strict repair preview hash drifted")
    storage = history_storage_root(root); _validate_storage_boundary(storage)
    legacy_before = _legacy_draft_inventory(storage) if storage.exists() else preview["legacy_draft"]
    strict_root = storage / "strict-records"
    for ancestor in (storage.parent, storage, strict_root):
        _ensure_real_directory(ancestor)
    written: list[dict[str, str]] = []
    for record in preview["candidates"]:
        destination_dir = strict_root / record["workstream_id"]; _ensure_real_directory(destination_dir)
        record_hash = _digest(record); destination = destination_dir / f"{record['revision']}-{record_hash}.json"
        payload = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        if len(payload) > MAX_RECORD_BYTES:
            raise ValueError("Workstream history record exceeds size limit")
        _exclusive_write(destination, payload)
        written.append({"workstream_id": record["workstream_id"], "record_sha256": record_hash, "storage_ref": f"strict-records/{record['workstream_id']}/{destination.name}"})
    legacy_after = _legacy_draft_inventory(storage)
    if legacy_after != legacy_before:
        raise ValueError("legacy Workstream history draft bytes changed during strict repair")
    inspection = inspect_workstream_history(root)
    receipt = {
        "schema_version": 1, "contract_type": "workstream-history-strict-repair-receipt",
        "preview_hash": preview_hash, "schema_sha256": preview["schema_sha256"], "written_records": written,
        "legacy_draft_before": legacy_before, "legacy_draft_after": legacy_after,
        "history_snapshot_ready": preview["counts"]["excluded"] == 0 and inspection["counts"]["records"] >= preview["counts"]["unique_archive_workstreams"],
        "classification_counts": {"record_kind": preview["counts"]["record_kind"], "observed_lifecycle": preview["counts"]["observed_lifecycle"]},
        "rollback": {
            "strategy": "remove-only-repair-created-strict-records-after-hash-verification",
            "created_storage_refs": [item["storage_ref"] for item in written], "legacy_draft_remains_preserved": True,
        },
        "archives_changed": False, "relations_changed": False, "legacy_draft_changed": False,
        "writes_performed": bool(written), "inspection_hash": _digest(inspection),
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    receipts = storage / "repair-receipts"; _ensure_real_directory(receipts)
    _exclusive_write(receipts / f"strict-schema-{preview_hash}.json", json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return receipt


def build_verified_closure_snapshot(
    project_root: Path, *, session: Mapping[str, Any], source_evidence_id: str,
    source_evidence_hash: str, closed_at: str, validation_refs: Sequence[str] = (), relation_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Build, but do not write, the strict result required before cleanup."""
    if (
        session.get("lifecycle_phase") != "closed" or session.get("runtime_condition") != "offline"
        or session.get("evidence_freshness") != "current" or session.get("closure_reason") not in _CLOSURE_REASONS
    ):
        raise ValueError("history snapshot requires verified closed/offline/current session evidence")
    if not _HASH.fullmatch(str(source_evidence_hash)):
        raise ValueError("history source evidence hash is invalid")
    workstream_id = str(_identifier(session.get("workstream_id"), "history workstream_id"))
    record = {
        "schema_version": 1, "contract_type": HISTORY_CONTRACT, "workstream_id": workstream_id,
        "display": {"task_code": None, "label": workstream_id},
        "classification": _accepted_classification(Path(project_root), workstream_id, session),
        "historical_state": {
            "record_kind": "closed-workstream", "observed_lifecycle_phase": "closed", "runtime_condition": "offline",
            "closure_reason": session["closure_reason"], "captured_at": _timestamp(closed_at, "history closed_at"),
        },
        "git": {"final_head_oid": session["head"], "branch_ref": session["branch"]},
        "lineage": _lineage_summary(session) if isinstance(session.get("lineage"), Mapping) else None,
        "references": {
            "validation_refs": sorted({_safe_ref(item, "validation ref") for item in validation_refs}),
            "relation_ids": sorted({_safe_ref(item, "relation id") for item in relation_ids}),
            "source_evidence_ids": [_safe_ref(source_evidence_id, "source evidence id")],
        },
        "visibility": "git-private-local-only", "revision": 1,
    }
    validate_history_record(record)
    return {"schema_version": 1, "contract_type": "workstream-history-snapshot-readiness", "history_snapshot_ready": True, "record": record, "record_hash": _digest(record), "read_only": True, "writes_performed": False}


def history_nodes(project_root: Path) -> list[dict[str, Any]]:
    """Project strict records into read-only Graph nodes without changing state axes."""
    nodes: list[dict[str, Any]] = []
    for record in inspect_workstream_history(project_root)["records"]:
        historical, references = record["historical_state"], record["references"]
        source_ref = references["source_evidence_ids"][0] if references["source_evidence_ids"] else "history-index:strict"
        nodes.append({
            "workstream_id": record["workstream_id"], "session_state": "current",
            "lifecycle_phase": historical["observed_lifecycle_phase"], "runtime_condition": historical["runtime_condition"],
            "evidence_freshness": "current", "head_oid": record["git"]["final_head_oid"], "scope_status": "current",
            "closure_reason": historical["closure_reason"] if historical["record_kind"] == "closed-workstream" else None,
            "primary_subsystem_id": record["classification"]["primary_subsystem_id"] or "unknown",
            "affected_subsystem_ids": [], "visibility": "git-private-local-only", "observability": "workstream-history-index",
            "source_links": [{"kind": "workstream-session", "ref": source_ref}], "origin": "workstream-history-index",
            "history_closed_at": historical["captured_at"], "history_relation_count": len(references["relation_ids"]),
            "history_record_kind": historical["record_kind"],
            "history_observed_lifecycle_phase": historical["observed_lifecycle_phase"],
            "history_observed_runtime_condition": historical["runtime_condition"],
        })
    return nodes


__all__ = [
    "HISTORY_CONTRACT", "HISTORY_SCHEMA_VERSION", "apply_legacy_history_migration", "build_verified_closure_snapshot",
    "history_nodes", "history_storage_root", "inspect_workstream_history", "preview_legacy_history_migration", "validate_history_record",
]
