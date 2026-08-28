"""Local-only execution for exact Workstream succession plans.

The W7A graph remains the semantic owner.  This module adds one-time local
confirmation, write-ahead journals, append-only apply/undo, and recovery.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import secrets
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .collaboration import validate_collaboration_contract
from .workstream_relations import (
    RELATION_LIFECYCLES,
    RELATION_RECORD_KEYS,
    _canonical_bytes,
    _digest,
    _is_ancestor,
    _revision_count,
    _run_git,
    _validate_identifier,
    append_relation_event,
    build_apply_plan,
    build_discovery_plan,
    build_relation_graph,
    build_relation_record,
    build_undo_plan,
    default_relation_evidence,
    load_legacy_session_projection,
    load_relation_graph,
    load_relation_history,
    relation_storage_root,
    project_legacy_session_relation,
    _node_from_session,
    validate_apply_receipt,
    validate_relation_record,
)


EXECUTION_SCHEMA_VERSION = 1
_MAX_CONTROL_BYTES = 2 * 1024 * 1024
_TERMINAL_JOURNAL_STATES = {"committed", "rolled-back", "undo-committed"}
_EXECUTION_PLAN_KEYS = {
    "actor", "apply_plan", "candidate_bindings", "confirmation_required",
    "contract_type", "destructive_actions", "discovery_plan_hash", "expires_at",
    "execution_supported", "graph_hash", "issued_at", "plan_hash", "plan_id",
    "project_hash", "schema_version", "writes_performed",
}


class RecoveryRequiredError(ValueError):
    """Raised after a journal exists and the transaction cannot finish."""


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str, label: str) -> dt.datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError(f"{label} must be a bounded RFC 3339 timestamp")
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an RFC 3339 timestamp") from exc
    if result.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return result


def _pretty_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_common_dir(project_root: Path) -> Path:
    root = Path(project_root).expanduser().absolute()
    value = _run_git(root, "rev-parse", "--git-common-dir").stdout.strip()
    common = Path(value)
    if not common.is_absolute():
        common = root / common
    return Path(os.path.realpath(common))


def transaction_storage_root(project_root: Path) -> Path:
    return _git_common_dir(project_root) / "orrery" / "workstream-relation-transactions"


def project_execution_hash(project_root: Path) -> str:
    root = Path(project_root).expanduser().absolute()
    first = _run_git(root, "rev-list", "--max-parents=0", "HEAD").stdout.splitlines()
    if not first:
        raise ValueError("project repository has no root commit")
    return _digest({
        "git_common_dir": os.path.normcase(os.path.realpath(_git_common_dir(root))),
        "root_commits": sorted(first),
    })


def _validate_control_root(root: Path) -> None:
    common = root.parent.parent
    if root != common / "orrery" / "workstream-relation-transactions":
        raise ValueError("relation transaction storage escaped Git common private state")
    for path in (common / "orrery", root):
        if os.path.lexists(path):
            metadata = path.lstat()
            if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
                raise ValueError("relation transaction storage must use real directories")


def _safe_control_path(project_root: Path, category: str, identifier: str) -> Path:
    if category not in {"confirmations", "journals", "receipts"}:
        raise ValueError("unsupported transaction control category")
    _validate_identifier(identifier, "control identifier", filesystem_safe=True)
    root = transaction_storage_root(project_root)
    _validate_control_root(root)
    category_path = root / category
    if os.path.lexists(category_path):
        metadata = category_path.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or category_path.is_symlink():
            raise ValueError("transaction control category must be a real directory")
    return category_path / f"{identifier}.json"


def _atomic_write_json(path: Path, value: Mapping[str, Any], *, create_only: bool = False) -> None:
    data = _pretty_bytes(value)
    if len(data) > _MAX_CONTROL_BYTES:
        raise ValueError("transaction control record exceeds the size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    if create_only and os.path.lexists(path):
        raise ValueError(f"transaction control record already exists: {path.stem}")
    descriptor, name = tempfile.mkstemp(prefix=f"{path.stem}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        if create_only and os.path.lexists(path):
            raise ValueError(f"transaction control record already exists: {path.stem}")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise ValueError(f"{label} does not exist") from exc
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink() or metadata.st_size > _MAX_CONTROL_BYTES:
        raise ValueError(f"{label} must be a bounded regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def _scope_hash(session: Mapping[str, Any]) -> str:
    return _digest({
        key: session.get(key)
        for key in (
            "scope_revision", "primary_subsystem_id", "affected_subsystem_ids",
            "expected_writes", "governing_docs", "validation_surfaces", "findings",
            "last_scope_expansion",
        )
    })


def _worktree_entries(project_root: Path) -> list[dict[str, Any]]:
    result = _run_git(Path(project_root), "worktree", "list", "--porcelain")
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current is not None:
                entries.append(current)
            current = {"path": Path(line[9:]), "head": None, "branch": None}
        elif current is not None and line.startswith("HEAD "):
            current["head"] = line[5:]
        elif current is not None and line.startswith("branch "):
            current["branch"] = line[7:]
    if current is not None:
        entries.append(current)
    return sorted(entries, key=lambda item: os.path.normcase(os.path.realpath(item["path"])))


def _session_path_from_worktree(worktree: Path) -> Path:
    marker = worktree / ".git"
    if marker.is_dir():
        git_dir = marker
    elif marker.is_file() and not marker.is_symlink():
        text = marker.read_text(encoding="utf-8").strip()
        prefix = "gitdir: "
        if not text.startswith(prefix):
            raise ValueError("linked worktree .git file is malformed")
        git_dir = Path(text[len(prefix):])
        if not git_dir.is_absolute():
            git_dir = worktree / git_dir
    else:
        raise ValueError("worktree Git directory is unavailable")
    return Path(os.path.realpath(git_dir)) / "orrery" / "worktree.json"


def _session_index(project_root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    integration_oids: dict[str, str | None] = {}
    for entry in _worktree_entries(project_root):
        worktree = entry["path"]
        if not worktree.is_dir():
            continue
        try:
            path = _session_path_from_worktree(worktree)
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or path.is_symlink() or metadata.st_size > _MAX_CONTROL_BYTES:
                continue
            raw = path.read_bytes()
            record = json.loads(raw.decode("utf-8"))
            if not isinstance(record, dict):
                continue
            validate_collaboration_contract(record)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        workstream_id = record.get("workstream_id")
        if not isinstance(workstream_id, str):
            continue
        if workstream_id in result:
            raise ValueError(f"multiple local Sessions claim Workstream {workstream_id}")
        integration_ref = str(record.get("integration_ref", ""))
        if integration_ref not in integration_oids:
            integration_result = _run_git(Path(project_root), "rev-parse", "--verify", integration_ref, check=False)
            integration_oids[integration_ref] = integration_result.stdout.strip() if integration_result.returncode == 0 else None
        integration_oid = integration_oids[integration_ref]
        lineage = record.get("lineage")
        current = (
            record.get("head") == entry.get("head")
            and record.get("branch") == entry.get("branch")
            and (integration_oid is None or record.get("integration_oid") == integration_oid)
            and (
                not isinstance(lineage, Mapping)
                or lineage.get("validated_head") == record.get("head")
            )
        )
        result[workstream_id] = {
            "workstream_id": workstream_id,
            "worktree": str(worktree),
            "path": str(path),
            "raw": raw,
            "session_hash": _sha256_bytes(raw),
            "scope_hash": _scope_hash(record),
            "state": "current" if current else "stale",
            "record": dict(record),
        }
    return result


def _graph_from_session_index(project_root: Path, sessions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    native = load_relation_history(project_root)
    legacy_records: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    for snapshot in sessions.values():
        nodes.append(_node_from_session(snapshot["record"], snapshot["state"]))
    for snapshot in sessions.values():
        record = snapshot["record"]
        lineage = record.get("lineage")
        if not isinstance(lineage, Mapping) or lineage.get("base_workstream_id") is None:
            continue
        parent = sessions.get(str(lineage["base_workstream_id"]))
        legacy_records.append(project_legacy_session_relation(
            record,
            session_state=snapshot["state"],
            parent_session=parent["record"] if parent is not None else None,
            parent_state=parent["state"] if parent is not None else "unknown",
            project_root=Path(project_root),
        ))
    native_triples = {
        (record["relation_type"], record["source_workstream_id"], record["target_workstream_id"])
        for record in native["current_records"]
    }
    records = list(native["current_records"])
    records.extend(
        record for record in legacy_records
        if (record["relation_type"], record["source_workstream_id"], record["target_workstream_id"])
        not in native_triples
    )
    graph = build_relation_graph(records, nodes=nodes)
    graph["storage"] = native["storage"]
    graph["storage_ref"] = native["storage_ref"]
    graph["legacy_projection_included"] = True
    graph["graph_hash"] = _digest({key: value for key, value in graph.items() if key != "graph_hash"})
    return graph


def _graph_and_sessions(project_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    assert_no_incomplete_transactions(project_root)
    sessions = _session_index(project_root)
    return _graph_from_session_index(project_root, sessions), sessions


def _snapshot_binding(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    session = snapshot["record"]
    state = snapshot["state"]
    return {
        "workstream_id": session["workstream_id"],
        "session_hash": snapshot["session_hash"],
        "scope_hash": snapshot["scope_hash"],
        "session_state": state,
        "head_oid": session["head"],
        "lifecycle_phase": session["lifecycle_phase"],
        "runtime_condition": session["runtime_condition"],
        "evidence_freshness": "stale" if state == "stale" else session.get("evidence_freshness", "unknown"),
        "scope_status": "current" if state == "current" else "stale",
        "closure_reason": session.get("closure_reason"),
    }


def _candidate_from_explicit(
    project_root: Path,
    spec: Mapping[str, Any],
    sessions: Mapping[str, Mapping[str, Any]],
    recorded_at: str,
) -> tuple[dict[str, Any], list[str]]:
    allowed = {
        "relation_id", "relation_type", "source_workstream_id", "target_workstream_id",
        "reason", "task_base_oid", "ownership_transfer_oid", "source_links",
    }
    if not isinstance(spec, Mapping) or not set(spec).issubset(allowed):
        raise ValueError("explicit relation spec contains unsupported fields")
    relation_id = _validate_identifier(spec.get("relation_id"), "relation_id", filesystem_safe=True)
    relation_type = spec.get("relation_type")
    if relation_type not in {"derived_from", "depends_on", "absorbs"}:
        raise ValueError("explicit relation spec has an unsupported type")
    source_id = _validate_identifier(spec.get("source_workstream_id"), "source_workstream_id")
    target_id = _validate_identifier(spec.get("target_workstream_id"), "target_workstream_id")
    source = sessions.get(source_id)
    target = sessions.get(target_id)
    reasons: list[str] = []
    evidence = default_relation_evidence(
        ancestry_status="not-applicable" if relation_type != "derived_from" else "unknown",
        dependency_status="unknown" if relation_type == "depends_on" else "not-applicable",
        ownership_transfer_status="unknown" if relation_type == "absorbs" else "not-applicable",
    )
    if source is None or target is None:
        reasons.append("local-session-endpoint-unavailable")
    else:
        source_binding = _snapshot_binding(source)
        target_binding = _snapshot_binding(target)
        evidence.update({
            "source_head_oid": source_binding["head_oid"],
            "target_head_oid": target_binding["head_oid"],
            "source_head_status": "current" if source_binding["session_state"] == "current" else "stale",
            "target_head_status": "current" if target_binding["session_state"] == "current" else "stale",
            "scope_status": "current" if source_binding["scope_status"] == target_binding["scope_status"] == "current" else "stale",
        })
        if evidence["scope_status"] != "current":
            reasons.append("session-or-scope-drift")
        if relation_type == "derived_from":
            lineage = source["record"].get("lineage")
            requested = spec.get("task_base_oid")
            task_base = requested or (lineage.get("task_base_oid") if isinstance(lineage, Mapping) else None)
            evidence["task_base_oid"] = task_base
            if (
                not isinstance(lineage, Mapping)
                or lineage.get("base_workstream_id") != target_id
                or lineage.get("status") != "current"
            ):
                reasons.append("explicit-lineage-not-current")
            elif task_base != target_binding["head_oid"]:
                reasons.append("task-base-target-head-mismatch")
            elif not _is_ancestor(Path(project_root), task_base, source_binding["head_oid"]):
                evidence["ancestry_status"] = "rejected"
                reasons.append("task-base-not-ancestor")
            else:
                evidence["ancestry_status"] = "confirmed"
                evidence["target_unique_commits_after_base"] = 0
        elif relation_type == "depends_on":
            reasons.append("dependency-requires-local-confirmation")
        else:
            transfer = spec.get("ownership_transfer_oid")
            evidence["ownership_transfer_oid"] = transfer
            if not isinstance(transfer, str) or transfer != target_binding["head_oid"]:
                reasons.append("ownership-transfer-evidence-unconfirmed")
            elif not _is_ancestor(Path(project_root), transfer, source_binding["head_oid"]):
                evidence["ownership_transfer_status"] = "rejected"
                reasons.append("ownership-transfer-not-ancestor")
            else:
                evidence["ownership_transfer_status"] = "confirmed"
                evidence["target_unique_commits_after_base"] = 0
    evidence["status"] = "confirmed" if not reasons or reasons == ["dependency-requires-local-confirmation"] else "unknown"
    record = build_relation_record(
        relation_id=relation_id,
        event_id=f"event-{_digest({'relation_id': relation_id, 'recorded_at': recorded_at})[:24]}",
        revision=1,
        relation_type=relation_type,
        source_workstream_id=source_id,
        target_workstream_id=target_id,
        lifecycle="proposed",
        recorded_at=recorded_at,
        actor_kind="tool",
        actor_id="local-discovery",
        origin="discovery",
        reason=str(spec.get("reason") or "exact local relation candidate"),
        evidence=evidence,
        source_links=spec.get("source_links") or [],
        writes_performed=False,
    )
    return record, sorted(set(reasons or ["exact-local-evidence-proposed"]))


def discover_execution_candidates(
    project_root: Path,
    *,
    explicit_relations: Sequence[Mapping[str, Any]] = (),
    similarity_hints: Sequence[Mapping[str, Any]] = (),
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Return proposed/Unknown candidates using only exact local evidence."""
    root = Path(project_root).expanduser().absolute()
    timestamp = recorded_at or _utc_now()
    _parse_time(timestamp, "recorded_at")
    graph, sessions = _graph_and_sessions(root)
    candidates: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    native_triples = {
        (item["relation_type"], item["source_workstream_id"], item["target_workstream_id"])
        for item in load_relation_history(root)["current_records"]
    }
    legacy_records = [
        {key: edge[key] for key in RELATION_RECORD_KEYS}
        for edge in graph["edges"] if edge.get("origin") == "legacy-session-projection"
    ]
    for projected in legacy_records:
        triple = (projected["relation_type"], projected["source_workstream_id"], projected["target_workstream_id"])
        if triple in native_triples:
            continue
        record = dict(projected)
        record["relation_id"] = f"materialized-{_digest(triple)[:24]}"
        record["event_id"] = f"event-{_digest({'triple': triple, 'recorded_at': timestamp})[:24]}"
        record["recorded_at"] = timestamp
        record["lifecycle"] = "proposed"
        record["origin"] = "discovery"
        record["actor"] = {"kind": "tool", "actor_id": "legacy-inference"}
        record["writes_performed"] = False
        validate_relation_record(record, project_root=root)
        reasons = ["exact-legacy-lineage-proposed"]
        if record["evidence"]["status"] != "confirmed":
            reasons.append("legacy-lineage-evidence-unknown")
        candidates.append({"record": record, "status": "proposed", "reason_codes": reasons})
    for spec in explicit_relations:
        record, reasons = _candidate_from_explicit(root, spec, sessions, timestamp)
        if any(item["record"]["relation_id"] == record["relation_id"] for item in candidates):
            raise ValueError("duplicate discovery relation_id")
        candidates.append({"record": record, "status": "proposed", "reason_codes": reasons})
    lineage_sources = {item["source_workstream_id"] for item in legacy_records}
    for workstream_id, snapshot in sorted(sessions.items()):
        session = snapshot["record"]
        lineage = session.get("lineage")
        if workstream_id not in lineage_sources and (
            not isinstance(lineage, Mapping) or lineage.get("base_workstream_id") is None
        ):
            unknown.append({
                "source_workstream_id": workstream_id,
                "target_workstream_id": None,
                "status": "unknown",
                "reason_codes": ["legacy-no-lineage-evidence"],
            })
    rejected: list[dict[str, Any]] = []
    for hint in similarity_hints:
        source = _validate_identifier(hint.get("source_workstream_id"), "hint source")
        target = _validate_identifier(hint.get("target_workstream_id"), "hint target")
        rejected.append({
            "source_workstream_id": source,
            "target_workstream_id": target,
            "status": "unknown",
            "reason_code": "branch-or-path-similarity-insufficient-evidence",
        })
    candidates.sort(key=lambda item: item["record"]["relation_id"])
    records = [item["record"] for item in candidates]
    w7a = build_discovery_plan(records, graph_hash=graph["graph_hash"], rejected_hints=rejected)
    body = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-execution-discovery",
        "project_hash": project_execution_hash(root),
        "graph_hash": graph["graph_hash"],
        "candidates": candidates,
        "unknown_candidates": unknown,
        "rejected_hints": rejected,
        "w7a_discovery_plan": w7a,
        "inference_sources": ["exact-local-session", "task-base-oid", "head", "git-ancestry", "scope", "lineage"],
        "similarity_inference_permitted": False,
        "read_only": True,
        "writes_performed": False,
        "destructive_actions": [],
    }
    body["discovery_hash"] = _digest(body)
    body["discovery_id"] = f"execution-discovery-{body['discovery_hash'][:24]}"
    return body


def _validate_discovery(discovery: Mapping[str, Any], project_root: Path) -> None:
    if discovery.get("contract_type") != "workstream-relation-execution-discovery":
        raise ValueError("execution plan requires an execution discovery")
    body = dict(discovery)
    discovery_id = body.pop("discovery_id", None)
    discovery_hash = body.pop("discovery_hash", None)
    expected = _digest(body)
    if discovery_hash != expected or discovery_id != f"execution-discovery-{expected[:24]}":
        raise ValueError("execution discovery hash does not bind its exact content")
    if discovery.get("project_hash") != project_execution_hash(project_root):
        raise ValueError("execution discovery belongs to another local project")


def build_execution_plan(
    project_root: Path,
    discovery: Mapping[str, Any],
    *,
    target_lifecycles: Mapping[str, str],
    actor_id: str,
    issued_at: str | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    _validate_discovery(discovery, root)
    actor = _validate_identifier(actor_id, "actor_id")
    current_graph, sessions = _graph_and_sessions(root)
    if current_graph["graph_hash"] != discovery["graph_hash"]:
        raise ValueError("relation graph drifted after discovery")
    issued = issued_at or _utc_now()
    issued_time = _parse_time(issued, "issued_at")
    expiry = expires_at or (issued_time + dt.timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
    if _parse_time(expiry, "expires_at") <= issued_time:
        raise ValueError("execution plan expiry must be after issuance")
    records = {item["record"]["relation_id"]: item["record"] for item in discovery["candidates"]}
    if set(target_lifecycles) != set(records):
        raise ValueError("target lifecycles must cover every discovery candidate exactly")
    takeovers: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    for relation_id in sorted(records):
        record = records[relation_id]
        lifecycle = target_lifecycles[relation_id]
        if lifecycle not in RELATION_LIFECYCLES or lifecycle in {"cancelled", "stale"}:
            raise ValueError("apply target lifecycle must be proposed, active, or completed")
        source = sessions.get(record["source_workstream_id"])
        target = sessions.get(record["target_workstream_id"])
        if source is None:
            raise ValueError(f"source Session unavailable for {relation_id}")
        source_binding = _snapshot_binding(source)
        if source_binding["session_state"] != "current" or source_binding["scope_status"] != "current":
            raise ValueError(f"source Session/Scope is not current for {relation_id}")
        binding = {
            "relation_id": relation_id,
            "record": record,
            "source": source_binding,
            "target": None if target is None else _snapshot_binding(target),
            "target_lifecycle": lifecycle,
        }
        bindings.append(binding)
        if lifecycle in {"active", "completed"}:
            if source_binding["evidence_freshness"] != "current":
                raise ValueError(f"source evidence is not current for {relation_id}")
            if target is None:
                raise ValueError(f"target Session unavailable for active/completed relation {relation_id}")
            target_binding = _snapshot_binding(target)
            if (
                target_binding["session_state"] != "current"
                or target_binding["scope_status"] != "current"
                or target_binding["evidence_freshness"] != "current"
            ):
                raise ValueError(f"target Session/evidence/Scope is not current for {relation_id}")
        if lifecycle in {"active", "completed"} and record["relation_type"] in {"derived_from", "absorbs"}:
            if target is None:
                raise ValueError(f"predecessor Session unavailable for {relation_id}")
            predecessor = _snapshot_binding(target)
            if lifecycle == "active" and predecessor["lifecycle_phase"] in {"closed", "integrated"}:
                raise ValueError("active takeover predecessor lifecycle is already ended")
            w7a_predecessor = {key: predecessor[key] for key in (
                "workstream_id", "session_hash", "session_state", "head_oid", "lifecycle_phase",
                "runtime_condition", "evidence_freshness", "scope_status", "closure_reason",
            )}
            transition = None
            if lifecycle == "active":
                transition = {
                    "lifecycle_phase": predecessor["lifecycle_phase"],
                    "runtime_condition": "paused",
                    "evidence_freshness": "current",
                    "closure_reason": predecessor["closure_reason"],
                }
            elif not (
                predecessor["lifecycle_phase"] == "closed"
                and predecessor["closure_reason"] == "superseded"
            ):
                transition = {
                    "lifecycle_phase": "closed",
                    "runtime_condition": "paused",
                    "evidence_freshness": "current",
                    "closure_reason": "superseded",
                }
            takeovers.append({
                "relation_id": relation_id,
                "target_lifecycle": lifecycle,
                "predecessor_session": w7a_predecessor,
                "transition": transition,
            })
    w7a = build_apply_plan(
        discovery["w7a_discovery_plan"],
        takeover_requests=takeovers,
        relation_lifecycle_requests=target_lifecycles,
    )
    body = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-execution-plan",
        "project_hash": project_execution_hash(root),
        "discovery_plan_hash": discovery["discovery_hash"],
        "graph_hash": discovery["graph_hash"],
        "candidate_bindings": bindings,
        "apply_plan": w7a,
        "actor": {"kind": "human-local", "actor_id": actor},
        "issued_at": issued,
        "expires_at": expiry,
        "confirmation_required": True,
        "execution_supported": True,
        "writes_performed": False,
        "destructive_actions": [],
    }
    body["plan_hash"] = _digest(body)
    body["plan_id"] = f"execute-{body['plan_hash'][:24]}"
    return body


def _validate_execution_plan(plan: Mapping[str, Any], project_root: Path, actor_id: str) -> None:
    if not isinstance(plan, Mapping) or set(plan) != _EXECUTION_PLAN_KEYS:
        raise ValueError("execution plan fields do not match the v1 contract")
    if plan.get("contract_type") != "workstream-relation-execution-plan":
        raise ValueError("unsupported execution plan")
    body = dict(plan)
    plan_id = body.pop("plan_id")
    plan_hash = body.pop("plan_hash")
    expected = _digest(body)
    if plan_hash != expected or plan_id != f"execute-{expected[:24]}":
        raise ValueError("execution plan hash does not bind its exact content")
    if plan.get("project_hash") != project_execution_hash(project_root):
        raise ValueError("execution plan belongs to another local project")
    if plan.get("actor") != {"kind": "human-local", "actor_id": actor_id}:
        raise ValueError("execution actor does not match the exact plan")
    if _parse_time(plan["expires_at"], "expires_at") <= dt.datetime.now(dt.timezone.utc):
        raise ValueError("execution plan has expired")
    if plan.get("execution_supported") is not True or plan.get("destructive_actions") != []:
        raise ValueError("execution plan is not locally executable")


def issue_local_confirmation(
    project_root: Path,
    plan: Mapping[str, Any],
    *,
    actor_id: str,
    issued_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    _validate_execution_plan(plan, root, actor_id)
    timestamp = issued_at or _utc_now()
    _parse_time(timestamp, "confirmation issued_at")
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    confirmation_id = f"confirmation-{_digest({'plan_hash': plan['plan_hash'], 'actor_id': actor_id, 'token_hash': token_hash})[:24]}"
    record = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-local-confirmation",
        "confirmation_id": confirmation_id,
        "project_hash": plan["project_hash"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "actor": {"kind": "human-local", "actor_id": actor_id},
        "token_hash": token_hash,
        "issued_at": timestamp,
        "expires_at": plan["expires_at"],
        "status": "issued",
        "consumed_by": None,
    }
    _atomic_write_json(_safe_control_path(root, "confirmations", confirmation_id), record, create_only=True)
    return {
        "confirmation_id": confirmation_id,
        "confirmation_token": token,
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "actor_id": actor_id,
        "expires_at": plan["expires_at"],
        "writes_performed": True,
        "storage": "git-common-private",
    }


def _verify_confirmation(
    project_root: Path,
    plan: Mapping[str, Any],
    *,
    confirmation_id: str,
    confirmation_token: str,
    actor_id: str,
) -> dict[str, Any]:
    path = _safe_control_path(project_root, "confirmations", confirmation_id)
    record = _read_json(path, "local confirmation")
    expected_token_hash = hashlib.sha256(confirmation_token.encode("utf-8")).hexdigest()
    if (
        record.get("status") != "issued"
        or record.get("project_hash") != plan["project_hash"]
        or record.get("plan_id") != plan["plan_id"]
        or record.get("plan_hash") != plan["plan_hash"]
        or record.get("actor") != {"kind": "human-local", "actor_id": actor_id}
        or not secrets.compare_digest(str(record.get("token_hash", "")), expected_token_hash)
    ):
        raise ValueError("confirmation is forged, replayed, cross-project, or not exact")
    if _parse_time(record["expires_at"], "confirmation expires_at") <= dt.datetime.now(dt.timezone.utc):
        raise ValueError("local confirmation has expired")
    return record


def _consume_confirmation(
    project_root: Path,
    plan: Mapping[str, Any],
    *,
    confirmation_id: str,
    confirmation_token: str,
    actor_id: str,
    transaction_id: str,
) -> dict[str, Any]:
    record = _verify_confirmation(
        project_root, plan, confirmation_id=confirmation_id,
        confirmation_token=confirmation_token, actor_id=actor_id,
    )
    path = _safe_control_path(project_root, "confirmations", confirmation_id)
    record["status"] = "consumed"
    record["consumed_by"] = transaction_id
    _atomic_write_json(path, record)
    return record


def _list_journals(project_root: Path) -> list[dict[str, Any]]:
    root = transaction_storage_root(project_root)
    _validate_control_root(root)
    directory = root / "journals"
    if not directory.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        result.append(_read_json(path, "transaction journal"))
    return result


def assert_no_incomplete_transactions(project_root: Path) -> None:
    incomplete = [item.get("transaction_id") for item in _list_journals(project_root) if item.get("status") not in _TERMINAL_JOURNAL_STATES]
    if incomplete:
        raise RecoveryRequiredError(f"relation transaction recovery required: {incomplete[0]}")


def _write_session_bytes(path: Path, value: bytes) -> None:
    if len(value) > _MAX_CONTROL_BYTES:
        raise ValueError("private Session exceeds the transaction size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="worktree.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _resulting_session(
    original: Mapping[str, Any],
    operation: Mapping[str, Any],
    occurred_at: str,
) -> dict[str, Any]:
    result = dict(original)
    result.update({
        "lifecycle_phase": operation["target_lifecycle_phase"],
        "runtime_condition": operation["target_runtime_condition"],
        "evidence_freshness": operation["target_evidence_freshness"],
        "closure_reason": operation["target_closure_reason"],
        "lifecycle_revision": int(original.get("lifecycle_revision", 1)) + 1,
        "last_transition": {
            "from_phase": original["lifecycle_phase"],
            "to_phase": operation["target_lifecycle_phase"],
            "reason": operation["transition_reason"],
            "occurred_at": occurred_at,
        },
    })
    return result


def _event_for_operation(
    record: Mapping[str, Any], operation: Mapping[str, Any], actor_id: str, occurred_at: str
) -> dict[str, Any]:
    event = dict(record)
    event["lifecycle"] = operation["target_lifecycle"]
    event["recorded_at"] = occurred_at
    event["actor"] = {"kind": "human", "actor_id": actor_id}
    event["origin"] = "native"
    event["writes_performed"] = True
    event["event_id"] = f"event-{_digest({'plan_event_hash': operation['event_hash'], 'recorded_at': occurred_at, 'actor_id': actor_id})[:24]}"
    validate_relation_record(event)
    return event


def execute_apply_plan(
    project_root: Path,
    plan: Mapping[str, Any],
    *,
    plan_id: str,
    plan_hash: str,
    confirmation_id: str,
    confirmation_token: str,
    actor_id: str,
    occurred_at: str | None = None,
    failure_injection: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    if plan.get("plan_id") != plan_id or plan.get("plan_hash") != plan_hash:
        raise ValueError("provided plan ID/hash do not match the exact plan")
    _validate_execution_plan(plan, root, actor_id)
    assert_no_incomplete_transactions(root)
    timestamp = occurred_at or _utc_now()
    _parse_time(timestamp, "occurred_at")
    current_graph, sessions = _graph_and_sessions(root)
    if current_graph["graph_hash"] != plan["graph_hash"]:
        raise ValueError("relation graph drifted before apply")
    transition_operations = {
        (item["relation_id"], item["workstream_id"]): item
        for item in plan["apply_plan"]["operations"]
        if item["action"] == "transition-predecessor-session"
    }
    candidate_records = {
        item["record"]["relation_id"]: item["record"]
        for item in []
    }
    # Candidate records are recoverable from the W7A discovery event hashes only through the
    # execution bindings, so the plan stores their exact records in each binding.
    for binding in plan["candidate_bindings"]:
        if "record" in binding:
            candidate_records[binding["relation_id"]] = binding["record"]
    if not candidate_records:
        raise ValueError("execution plan does not embed exact candidate records")
    prepared_sessions: list[dict[str, Any]] = []
    for binding in plan["candidate_bindings"]:
        target = binding.get("target")
        if target is None:
            continue
        operation = transition_operations.get((binding["relation_id"], target["workstream_id"]))
        if operation is None:
            continue
        current = sessions.get(target["workstream_id"])
        if current is None:
            raise ValueError("predecessor Session disappeared before apply")
        current_binding = _snapshot_binding(current)
        for key in (
            "session_hash", "scope_hash", "session_state", "head_oid", "lifecycle_phase",
            "runtime_condition", "evidence_freshness", "scope_status", "closure_reason",
        ):
            if current_binding.get(key) != target.get(key):
                raise ValueError(f"predecessor Session/HEAD/Scope drifted before apply: {target['workstream_id']}")
        resulting = _resulting_session(current["record"], operation, timestamp)
        validate_collaboration_contract(resulting)
        resulting_raw = _pretty_bytes(resulting)
        prepared_sessions.append({
            "relation_id": binding["relation_id"],
            "workstream_id": target["workstream_id"],
            "path": current["path"],
            "original_b64": base64.b64encode(current["raw"]).decode("ascii"),
            "resulting_b64": base64.b64encode(resulting_raw).decode("ascii"),
            "original_hash": current["session_hash"],
            "resulting_hash": _sha256_bytes(resulting_raw),
            "original_binding": current_binding,
            "resulting_binding": {
                **current_binding,
                "session_hash": _sha256_bytes(resulting_raw),
                "lifecycle_phase": resulting["lifecycle_phase"],
                "runtime_condition": resulting["runtime_condition"],
                "evidence_freshness": resulting["evidence_freshness"],
                "closure_reason": resulting.get("closure_reason"),
            },
        })
    append_operations = [item for item in plan["apply_plan"]["operations"] if item["action"] == "append-relation-event"]
    prepared_events = [
        _event_for_operation(candidate_records[item["relation_id"]], item, actor_id, timestamp)
        for item in append_operations
    ]
    for event in prepared_events:
        validate_relation_record(event, project_root=root)
    history_ids = {item["relation_id"] for item in load_relation_history(root)["histories"]}
    if any(event["relation_id"] in history_ids for event in prepared_events):
        raise ValueError("apply would replay an existing relation history")
    transaction_id = f"apply-tx-{_digest({'plan_hash': plan_hash, 'confirmation_id': confirmation_id})[:24]}"
    _verify_confirmation(
        root, plan, confirmation_id=confirmation_id,
        confirmation_token=confirmation_token, actor_id=actor_id,
    )
    journal_path = _safe_control_path(root, "journals", transaction_id)
    journal = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-transaction-journal",
        "transaction_id": transaction_id,
        "operation": "apply",
        "status": "prepared",
        "project_hash": plan["project_hash"],
        "plan_id": plan_id,
        "plan_hash": plan_hash,
        "confirmation_id": confirmation_id,
        "actor_id": actor_id,
        "occurred_at": timestamp,
        "sessions": prepared_sessions,
        "events": prepared_events,
        "completed_session_writes": [],
        "completed_event_ids": [],
        "error": None,
    }
    _atomic_write_json(journal_path, journal, create_only=True)
    try:
        _consume_confirmation(
            root, plan, confirmation_id=confirmation_id, confirmation_token=confirmation_token,
            actor_id=actor_id, transaction_id=transaction_id,
        )
        journal["status"] = "applying"
        _atomic_write_json(journal_path, journal)
        for index, session in enumerate(prepared_sessions, start=1):
            _write_session_bytes(Path(session["path"]), base64.b64decode(session["resulting_b64"]))
            journal["completed_session_writes"].append(session["workstream_id"])
            _atomic_write_json(journal_path, journal)
            if failure_injection == f"after-session-write:{index}":
                raise OSError("injected failure after Session write")
        relation_receipts: list[dict[str, Any]] = []
        for index, event in enumerate(prepared_events, start=1):
            append_relation_event(root, event)
            journal["completed_event_ids"].append(event["event_id"])
            _atomic_write_json(journal_path, journal)
            operation = next(item for item in append_operations if item["relation_id"] == event["relation_id"])
            relation_receipts.append({
                "relation_id": event["relation_id"],
                "event_id": event["event_id"],
                "event_hash": operation["event_hash"],
                "prior_lifecycle": None,
                "resulting_lifecycle": event["lifecycle"],
            })
            if failure_injection == f"after-event-write:{index}":
                raise OSError("injected failure after relation event write")
        transition_receipts = []
        for item in prepared_sessions:
            original = item["original_binding"]
            resulting = item["resulting_binding"]
            transition_receipts.append({
                "relation_id": item["relation_id"],
                "workstream_id": item["workstream_id"],
                "original_session_hash": original["session_hash"],
                "resulting_session_hash": resulting["session_hash"],
                "original_head_oid": original["head_oid"],
                "resulting_head_oid": resulting["head_oid"],
                "original_lifecycle_phase": original["lifecycle_phase"],
                "resulting_lifecycle_phase": resulting["lifecycle_phase"],
                "original_runtime_condition": original["runtime_condition"],
                "resulting_runtime_condition": resulting["runtime_condition"],
                "original_evidence_freshness": original["evidence_freshness"],
                "resulting_evidence_freshness": resulting["evidence_freshness"],
                "original_scope_status": original["scope_status"],
                "resulting_scope_status": resulting["scope_status"],
                "original_closure_reason": original["closure_reason"],
                "resulting_closure_reason": resulting["closure_reason"],
            })
        w7a_receipt = {
            "schema_version": 1,
            "contract_type": "workstream-relation-apply-receipt",
            "receipt_id": f"apply-receipt-{_digest({'transaction_id': transaction_id})[:24]}",
            "plan_id": plan["apply_plan"]["plan_id"],
            "plan_hash": plan["apply_plan"]["plan_hash"],
            "graph_hash": plan["graph_hash"],
            "confirmed_locally": True,
            "relation_events": sorted(relation_receipts, key=lambda item: item["relation_id"]),
            "predecessor_transitions": sorted(transition_receipts, key=lambda item: (item["relation_id"], item["workstream_id"])),
            "writes_performed": True,
        }
        validate_apply_receipt(w7a_receipt, apply_plan=plan["apply_plan"])
        resulting_sessions = _session_index(root)
        resulting_graph_hash = _graph_from_session_index(root, resulting_sessions)["graph_hash"]
        receipt_body = {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "contract_type": "workstream-relation-transaction-receipt",
            "operation": "apply",
            "transaction_id": transaction_id,
            "project_hash": plan["project_hash"],
            "execution_plan_id": plan_id,
            "execution_plan_hash": plan_hash,
            "confirmation_id": confirmation_id,
            "actor": {"kind": "human-local", "actor_id": actor_id},
            "occurred_at": timestamp,
            "resulting_graph_hash": resulting_graph_hash,
            "w7a_apply_receipt": w7a_receipt,
            "relation_event_records": sorted(
                [
                    {
                        "relation_id": event["relation_id"],
                        "event_id": event["event_id"],
                        "revision": event["revision"],
                        "lifecycle": event["lifecycle"],
                        "event_hash": _digest(event),
                    }
                    for event in prepared_events
                ],
                key=lambda item: item["relation_id"],
            ),
            "status": "committed",
            "writes_performed": True,
            "destructive_actions": [],
        }
        receipt_hash = _digest(receipt_body)
        receipt = {**receipt_body, "receipt_hash": receipt_hash, "receipt_id": f"receipt-{receipt_hash[:24]}"}
        _atomic_write_json(_safe_control_path(root, "receipts", receipt["receipt_id"]), receipt, create_only=True)
        journal["status"] = "committed"
        journal["receipt_id"] = receipt["receipt_id"]
        journal["error"] = None
        _atomic_write_json(journal_path, journal)
        return receipt
    except Exception as exc:
        journal["status"] = "recovery-required"
        journal["error"] = {"type": type(exc).__name__, "message": str(exc)[:512]}
        _atomic_write_json(journal_path, journal)
        raise RecoveryRequiredError(f"apply transaction requires recovery: {transaction_id}") from exc


def _current_relation_event(project_root: Path, relation_id: str) -> dict[str, Any] | None:
    history = load_relation_history(project_root)
    for item in history["histories"]:
        if item["relation_id"] == relation_id:
            return item["events"][-1]
    return None


def recover_transaction(project_root: Path, transaction_id: str, *, actor_id: str, occurred_at: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    timestamp = occurred_at or _utc_now()
    journal_path = _safe_control_path(root, "journals", transaction_id)
    journal = _read_json(journal_path, "transaction journal")
    if journal.get("status") in _TERMINAL_JOURNAL_STATES:
        return {"transaction_id": transaction_id, "status": journal["status"], "writes_performed": False}
    if journal.get("actor_id") != actor_id or journal.get("project_hash") != project_execution_hash(root):
        raise ValueError("recovery actor/project does not match the exact journal")
    operation = journal.get("operation")
    for session in journal.get("sessions", []):
        path = Path(session["path"])
        current_hash = _sha256_bytes(path.read_bytes())
        if current_hash == session["resulting_hash"]:
            _write_session_bytes(path, base64.b64decode(session["original_b64"]))
        elif current_hash != session["original_hash"]:
            raise RecoveryRequiredError("Session drift prevents journal recovery")
    compensations: list[str] = []
    for event in journal.get("events", []):
        current = _current_relation_event(root, event["relation_id"])
        if current is None:
            continue
        if current["event_id"] == event["event_id"]:
            compensation = dict(current)
            compensation["revision"] = current["revision"] + 1
            compensation["lifecycle"] = "stale" if current["lifecycle"] == "completed" else "cancelled"
            compensation["event_id"] = f"event-{_digest({'recovery': transaction_id, 'relation_id': current['relation_id'], 'recorded_at': timestamp})[:24]}"
            compensation["recorded_at"] = timestamp
            compensation["actor"] = {"kind": "human", "actor_id": actor_id}
            compensation["reason"] = f"transaction-recovery:{transaction_id}"
            compensation["writes_performed"] = True
            append_relation_event(root, compensation)
            compensations.append(compensation["event_id"])
        elif (
            current["reason"] != f"transaction-recovery:{transaction_id}"
            and not (operation == "undo" and current["reason"].startswith("undo-apply-receipt:"))
        ):
            raise RecoveryRequiredError("relation history drift prevents journal recovery")
    journal["status"] = "undo-committed" if operation == "undo" else "rolled-back"
    journal["recovered_at"] = timestamp
    journal["recovery_actor_id"] = actor_id
    journal["compensating_event_ids"] = sorted(compensations)
    _atomic_write_json(journal_path, journal)
    return {
        "transaction_id": transaction_id,
        "status": journal["status"],
        "compensating_event_ids": sorted(compensations),
        "writes_performed": True,
        "history_deleted": False,
        "destructive_actions": [],
    }


def load_execution_receipt(project_root: Path, receipt_id: str) -> dict[str, Any]:
    receipt = _read_json(_safe_control_path(project_root, "receipts", receipt_id), "execution receipt")
    body = dict(receipt)
    actual_id = body.pop("receipt_id", None)
    actual_hash = body.pop("receipt_hash", None)
    expected = _digest(body)
    if actual_hash != expected or actual_id != f"receipt-{expected[:24]}":
        raise ValueError("execution receipt hash does not bind its exact content")
    if receipt.get("project_hash") != project_execution_hash(project_root):
        raise ValueError("execution receipt belongs to another local project")
    return receipt


def build_execution_undo_plan(project_root: Path, apply_receipt: Mapping[str, Any], *, actor_id: str, issued_at: str | None = None, expires_at: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    actor = _validate_identifier(actor_id, "actor_id")
    if apply_receipt.get("operation") != "apply" or apply_receipt.get("status") != "committed":
        raise ValueError("undo requires a committed apply receipt")
    stored = load_execution_receipt(root, apply_receipt["receipt_id"])
    if stored != dict(apply_receipt):
        raise ValueError("undo receipt input does not equal the stored exact receipt")
    assert_no_incomplete_transactions(root)
    graph, sessions = _graph_and_sessions(root)
    if graph["graph_hash"] != apply_receipt["resulting_graph_hash"]:
        raise ValueError("relation graph drift prevents undo")
    journal = _read_json(_safe_control_path(root, "journals", apply_receipt["transaction_id"]), "apply journal")
    bindings: list[dict[str, Any]] = []
    for item in journal.get("sessions", []):
        current = sessions.get(item["workstream_id"])
        if current is None or current["session_hash"] != item["resulting_hash"]:
            raise ValueError("predecessor Session drift prevents undo")
        bindings.append({
            "relation_id": item["relation_id"],
            "workstream_id": item["workstream_id"],
            "current_session_hash": item["resulting_hash"],
            "restore_session_hash": item["original_hash"],
            "head_oid": current["record"]["head"],
            "scope_hash": current["scope_hash"],
        })
    issued = issued_at or _utc_now()
    issued_time = _parse_time(issued, "issued_at")
    expiry = expires_at or (issued_time + dt.timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
    w7a = build_undo_plan(apply_receipt=apply_receipt["w7a_apply_receipt"])
    body = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-execution-undo-plan",
        "project_hash": apply_receipt["project_hash"],
        "apply_receipt_id": apply_receipt["receipt_id"],
        "apply_receipt_hash": apply_receipt["receipt_hash"],
        "graph_hash": graph["graph_hash"],
        "session_bindings": bindings,
        "w7a_undo_plan": w7a,
        "actor": {"kind": "human-local", "actor_id": actor},
        "issued_at": issued,
        "expires_at": expiry,
        "confirmation_required": True,
        "execution_supported": True,
        "writes_performed": False,
        "deletes_history": False,
        "destructive_actions": [],
    }
    body["plan_hash"] = _digest(body)
    body["plan_id"] = f"undo-execute-{body['plan_hash'][:24]}"
    return body


def _validate_undo_execution_plan(plan: Mapping[str, Any], project_root: Path, actor_id: str) -> None:
    if plan.get("contract_type") != "workstream-relation-execution-undo-plan":
        raise ValueError("unsupported undo execution plan")
    body = dict(plan)
    plan_id = body.pop("plan_id", None)
    plan_hash = body.pop("plan_hash", None)
    expected = _digest(body)
    if plan_hash != expected or plan_id != f"undo-execute-{expected[:24]}":
        raise ValueError("undo plan hash does not bind its exact content")
    if plan.get("project_hash") != project_execution_hash(project_root):
        raise ValueError("undo plan belongs to another local project")
    if plan.get("actor") != {"kind": "human-local", "actor_id": actor_id}:
        raise ValueError("undo actor does not match the exact plan")
    if _parse_time(plan["expires_at"], "expires_at") <= dt.datetime.now(dt.timezone.utc):
        raise ValueError("undo plan has expired")


def issue_local_undo_confirmation(project_root: Path, plan: Mapping[str, Any], *, actor_id: str, issued_at: str | None = None) -> dict[str, Any]:
    _validate_undo_execution_plan(plan, Path(project_root), actor_id)
    # The confirmation storage contract is plan-type neutral.
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    confirmation_id = f"confirmation-{_digest({'plan_hash': plan['plan_hash'], 'actor_id': actor_id, 'token_hash': token_hash})[:24]}"
    record = {
        "schema_version": 1,
        "contract_type": "workstream-relation-local-confirmation",
        "confirmation_id": confirmation_id,
        "project_hash": plan["project_hash"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "actor": {"kind": "human-local", "actor_id": actor_id},
        "token_hash": token_hash,
        "issued_at": issued_at or _utc_now(),
        "expires_at": plan["expires_at"],
        "status": "issued",
        "consumed_by": None,
    }
    _atomic_write_json(_safe_control_path(project_root, "confirmations", confirmation_id), record, create_only=True)
    return {"confirmation_id": confirmation_id, "confirmation_token": token, "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "actor_id": actor_id, "expires_at": plan["expires_at"], "writes_performed": True}


def execute_undo_plan(project_root: Path, plan: Mapping[str, Any], *, plan_id: str, plan_hash: str, confirmation_id: str, confirmation_token: str, actor_id: str, occurred_at: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    if plan.get("plan_id") != plan_id or plan.get("plan_hash") != plan_hash:
        raise ValueError("provided undo plan ID/hash do not match the exact plan")
    _validate_undo_execution_plan(plan, root, actor_id)
    assert_no_incomplete_transactions(root)
    apply_receipt = load_execution_receipt(root, plan["apply_receipt_id"])
    if apply_receipt["receipt_hash"] != plan["apply_receipt_hash"]:
        raise ValueError("undo plan does not bind the exact apply receipt")
    current_graph, current_sessions = _graph_and_sessions(root)
    if current_graph["graph_hash"] != plan["graph_hash"]:
        raise ValueError("relation graph drift prevents undo execution")
    apply_journal = _read_json(_safe_control_path(root, "journals", apply_receipt["transaction_id"]), "apply journal")
    for applied in apply_journal.get("events", []):
        current = _current_relation_event(root, applied["relation_id"])
        if current is None or current["event_id"] != applied["event_id"]:
            raise ValueError("relation history drift prevents undo execution")
    timestamp = occurred_at or _utc_now()
    transaction_id = f"undo-tx-{_digest({'plan_hash': plan_hash, 'confirmation_id': confirmation_id})[:24]}"
    _verify_confirmation(
        root, plan, confirmation_id=confirmation_id,
        confirmation_token=confirmation_token, actor_id=actor_id,
    )
    journal_path = _safe_control_path(root, "journals", transaction_id)
    journal = {
        "schema_version": 1,
        "contract_type": "workstream-relation-transaction-journal",
        "transaction_id": transaction_id,
        "operation": "undo",
        "status": "prepared",
        "project_hash": plan["project_hash"],
        "plan_id": plan_id,
        "plan_hash": plan_hash,
        "confirmation_id": confirmation_id,
        "actor_id": actor_id,
        "occurred_at": timestamp,
        "apply_receipt_id": apply_receipt["receipt_id"],
        "sessions": apply_journal.get("sessions", []),
        "events": apply_journal.get("events", []),
        "completed_session_writes": [],
        "completed_event_ids": [],
        "error": None,
    }
    _atomic_write_json(journal_path, journal, create_only=True)
    try:
        _consume_confirmation(root, plan, confirmation_id=confirmation_id, confirmation_token=confirmation_token, actor_id=actor_id, transaction_id=transaction_id)
        journal["status"] = "applying"
        _atomic_write_json(journal_path, journal)
        sessions = current_sessions
        restored: list[dict[str, Any]] = []
        for item in journal["sessions"]:
            current = sessions.get(item["workstream_id"])
            if current is None or current["session_hash"] != item["resulting_hash"]:
                raise ValueError("Session drift prevents undo")
            original_raw = base64.b64decode(item["original_b64"])
            _write_session_bytes(Path(item["path"]), original_raw)
            journal["completed_session_writes"].append(item["workstream_id"])
            _atomic_write_json(journal_path, journal)
            restored.append({"workstream_id": item["workstream_id"], "restored_session_hash": item["original_hash"], "head_oid": item["original_binding"]["head_oid"]})
        compensation_ids: list[str] = []
        for applied in journal["events"]:
            current = _current_relation_event(root, applied["relation_id"])
            if current is None or current["event_id"] != applied["event_id"]:
                raise ValueError("relation history drift prevents undo")
            compensation = dict(current)
            compensation["revision"] = current["revision"] + 1
            compensation["lifecycle"] = "stale" if current["lifecycle"] == "completed" else "cancelled"
            compensation["event_id"] = f"event-{_digest({'undo': transaction_id, 'relation_id': current['relation_id'], 'recorded_at': timestamp})[:24]}"
            compensation["recorded_at"] = timestamp
            compensation["actor"] = {"kind": "human", "actor_id": actor_id}
            compensation["reason"] = f"undo-apply-receipt:{apply_receipt['receipt_id']}"
            compensation["writes_performed"] = True
            append_relation_event(root, compensation)
            compensation_ids.append(compensation["event_id"])
            journal["completed_event_ids"].append(compensation["event_id"])
            _atomic_write_json(journal_path, journal)
        receipt_body = {
            "schema_version": 1,
            "contract_type": "workstream-relation-transaction-receipt",
            "operation": "undo",
            "transaction_id": transaction_id,
            "project_hash": plan["project_hash"],
            "execution_plan_id": plan_id,
            "execution_plan_hash": plan_hash,
            "confirmation_id": confirmation_id,
            "actor": {"kind": "human-local", "actor_id": actor_id},
            "occurred_at": timestamp,
            "apply_receipt_id": apply_receipt["receipt_id"],
            "apply_receipt_hash": apply_receipt["receipt_hash"],
            "appended_compensating_event_ids": sorted(compensation_ids),
            "restored_sessions": sorted(restored, key=lambda item: item["workstream_id"]),
            "resulting_graph_hash": _graph_from_session_index(root, _session_index(root))["graph_hash"],
            "status": "committed",
            "writes_performed": True,
            "history_deleted": False,
            "destructive_actions": [],
        }
        receipt_hash = _digest(receipt_body)
        receipt = {**receipt_body, "receipt_hash": receipt_hash, "receipt_id": f"receipt-{receipt_hash[:24]}"}
        _atomic_write_json(_safe_control_path(root, "receipts", receipt["receipt_id"]), receipt, create_only=True)
        journal["status"] = "undo-committed"
        journal["receipt_id"] = receipt["receipt_id"]
        _atomic_write_json(journal_path, journal)
        return receipt
    except Exception as exc:
        journal["status"] = "recovery-required"
        journal["error"] = {"type": type(exc).__name__, "message": str(exc)[:512]}
        _atomic_write_json(journal_path, journal)
        raise RecoveryRequiredError(f"undo transaction requires recovery: {transaction_id}") from exc


def inspect_execution_state(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().absolute()
    journals = _list_journals(root)
    storage = transaction_storage_root(root)
    receipt_dir = storage / "receipts"
    receipt_ids = sorted(path.stem for path in receipt_dir.glob("*.json")) if receipt_dir.exists() else []
    pending = sorted(item["transaction_id"] for item in journals if item.get("status") not in _TERMINAL_JOURNAL_STATES)
    graph_error = None
    graph_hash = None
    try:
        graph_hash = load_relation_graph(root)["graph_hash"]
    except ValueError as exc:
        graph_error = str(exc)
    return {
        "schema_version": 1,
        "contract_type": "workstream-relation-execution-inspection",
        "project_hash": project_execution_hash(root),
        "graph_hash": graph_hash,
        "graph_status": "blocked" if pending or graph_error else "current",
        "pending_recovery_transaction_ids": pending,
        "journal_statuses": sorted(
            [{"transaction_id": item["transaction_id"], "operation": item["operation"], "status": item["status"]} for item in journals],
            key=lambda item: item["transaction_id"],
        ),
        "receipt_ids": receipt_ids,
        "apply_eligible": not pending and graph_error is None,
        "undo_eligible": not pending and graph_error is None,
        "projection_role": "derived-read-only",
        "read_only": True,
        "writes_performed": False,
        "network_performed": False,
        "destructive_actions": [],
    }


__all__ = [
    "RecoveryRequiredError",
    "assert_no_incomplete_transactions",
    "build_execution_plan",
    "build_execution_undo_plan",
    "discover_execution_candidates",
    "execute_apply_plan",
    "execute_undo_plan",
    "inspect_execution_state",
    "issue_local_confirmation",
    "issue_local_undo_confirmation",
    "load_execution_receipt",
    "project_execution_hash",
    "recover_transaction",
    "transaction_storage_root",
]
