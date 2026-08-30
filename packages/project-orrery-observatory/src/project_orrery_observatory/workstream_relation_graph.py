"""Read-only Observatory consumer for the W7A Workstream relation graph."""
from __future__ import annotations

import html
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from .display_vocabulary import display_status


PROJECTION_SCHEMA_VERSION = 2
PROVIDER_SCHEMA_VERSION = 1
PROVIDER_ID = "project-orrery-core.workstream-relations"
GRAPH_CONTRACT = "workstream-relation-graph"
PLAN_CONTRACT = "workstream-succession-plan"
SAFE_LINK_KINDS = {
    "git-commit", "other", "relation", "scope", "validation", "workstream-session"
}
DOCUMENT_LINK_PREFIXES = {
    "validation": ("docs/validation/",),
    "scope": ("docs/state/",),
    "other": ("docs/decisions/", "docs/design/", "docs/implementation/"),
}
OPAQUE_LINK_PREFIXES = ("git-private:", "git-private-series:", "git-common:", "fixture:", "opaque:")
OID = re.compile(r"^[0-9a-f]{40}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}$")
ACTIVE_NODE_STATUSES = {"active", "review-pending"}
ENDED_PHASES = {"closed", "integrated", "unknown"}
NODE_WIDTH = 248
NODE_HEIGHT = 104
RANK_GAP = 112
ROW_GAP = 34

DISPLAY_WORDS = {
    "active": "当前", "acceptance": "验收", "architecture": "架构", "archived": "归档",
    "authority": "权威", "baseline": "基线", "canonical": "权威", "ci": "持续集成",
    "closeout": "收口", "collaboration": "协作", "consumer": "消费者", "contract": "契约",
    "disclosure": "展开", "front": "前端", "graph": "关系图", "harness": "验证",
    "host": "托管", "incremental": "增量", "integration": "整合", "lan": "局域网",
    "local": "本地", "maintenance": "维护", "managed": "受管", "observatory": "观测台",
    "optimization": "优化", "parallel": "并行", "production": "生产", "progressive": "渐进",
    "promotion": "推广", "quick": "快速", "readability": "可读性", "real": "真实",
    "relation": "关系", "remove": "删除", "router": "路由", "security": "安全",
    "self": "自", "session": "会话", "state": "状态", "team": "团队", "throughput": "吞吐",
    "tiered": "分层", "ui": "界面", "unified": "统一", "ux": "体验", "validation": "验证",
    "workstream": "任务流", "fixes": "修复", "execution": "执行", "dynamic": "动态",
    "succession": "接续", "projection": "投影", "infrastructure": "基础设施",
}


class RelationGraphUnavailable(ValueError):
    """A complete, safe graph cannot be projected."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _bounded_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256 or any(ch in value for ch in "\r\n\0"):
        raise RelationGraphUnavailable("invalid-core-payload", f"Core {label} is invalid.")
    return value


def _document_href(kind: str, reference: str) -> str | None:
    prefixes = DOCUMENT_LINK_PREFIXES.get(kind, ())
    if not prefixes or not reference.startswith(prefixes) or not reference.endswith(".md"):
        return None
    path = PurePosixPath(reference)
    if path.is_absolute() or ".." in path.parts or "\\" in reference or ":" in reference:
        return None
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-").lower()
    if not stem:
        return None
    if kind == "scope":
        return "#state-" + stem
    if reference.startswith("docs/decisions/"):
        match = re.match(r"^(\d{4})", stem)
        return "#adr-" + match.group(1) if match else None
    return "#lib-" + stem


def _safe_source_link(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"kind", "ref"}:
        raise RelationGraphUnavailable("dangling-evidence", "Core evidence link shape is invalid.")
    kind = value.get("kind")
    reference = value.get("ref")
    if kind not in SAFE_LINK_KINDS or not isinstance(reference, str) or not SAFE_TOKEN.fullmatch(reference):
        raise RelationGraphUnavailable("unsafe-source-link", "Core evidence link is outside the safe whitelist.")
    lowered = reference.lower()
    if (
        lowered.startswith(("http:", "https:", "javascript:", "data:", "file:", "cmd:", "powershell:"))
        or reference.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:", reference)
        or ".." in PurePosixPath(reference).parts
    ):
        raise RelationGraphUnavailable("unsafe-source-link", "Core evidence link is outside the safe whitelist.")
    href = _document_href(str(kind), reference)
    if href is None:
        archive_prefix = "retired-session-archive:sha256:"
        allowed_archive = reference.startswith(archive_prefix) and bool(
            HASH.fullmatch(reference.removeprefix(archive_prefix))
        )
        allowed_opaque = allowed_archive or reference.startswith(OPAQUE_LINK_PREFIXES) or (
            kind == "git-commit" and OID.fullmatch(reference)
        )
        if not allowed_opaque:
            raise RelationGraphUnavailable("unsafe-source-link", "Core evidence link is outside the safe whitelist.")
    return {"kind": str(kind), "ref": reference, "href": href}


def _safe_links(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RelationGraphUnavailable("dangling-evidence", "Core source_links are unavailable.")
    return [_safe_source_link(item) for item in value]


def _validate_pair(value: Any, node_ids: set[str], *, disposition: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RelationGraphUnavailable("invalid-core-payload", "Core pair plan is invalid.")
    left = _bounded_identifier(value.get("left_workstream_id"), "pair endpoint")
    right = _bounded_identifier(value.get("right_workstream_id"), "pair endpoint")
    if left == right or left not in node_ids or right not in node_ids:
        raise RelationGraphUnavailable("dangling-node", "Core pair references a missing Workstream.")
    reasons = value.get("reason_codes")
    if not isinstance(reasons, list) or not reasons or any(not isinstance(item, str) or not item for item in reasons):
        raise RelationGraphUnavailable("invalid-core-payload", "Core pair reasons are unavailable.")
    return {
        "id": f"{disposition}:{left}:{right}",
        "source_workstream_id": left,
        "target_workstream_id": right,
        "relation_type": "comparison-suggestion",
        "lifecycle": "suppressed" if disposition == "suppress" else "proposed",
        "certainty": "suppressed" if disposition == "suppress" else "review-suggested",
        "reason_codes": sorted(set(reasons)),
        "source_links": [],
        "disposition": disposition,
    }


def _explicit_conflict(pair: Mapping[str, Any]) -> dict[str, Any] | None:
    reasons = [str(item) for item in pair.get("reason_codes", [])]
    conflict_reasons = [
        reason for reason in reasons
        if any(token in reason.lower() for token in (
            "path-overlap", "module-overlap", "exclusive-resource", "contract-incompatibility",
            "confirmed-conflict", "direct-validation-surface",
        ))
    ]
    if not conflict_reasons:
        return None
    result = dict(pair)
    result.update({
        "id": str(pair["id"]).replace("compare:", "conflict:"),
        "relation_type": "conflict-fact",
        "lifecycle": "confirmed",
        "certainty": "confirmed",
        "reason_codes": sorted(set(conflict_reasons)),
        "conflict_evidence": {
            "location": sorted(set(conflict_reasons)),
            "impact": "这些任务共享明确的受约束表面，集成前必须解决不兼容写入或资源占用。",
            "source": "Core succession-plan v1 explicit constraint reason_codes",
        },
        "disposition": "conflict",
    })
    return result


def _plain_state(node: Mapping[str, Any]) -> tuple[str, str]:
    if node.get("runtime_condition") == "waiting-for-user":
        return "等待人工确认", "human-confirmation-pending"
    if node.get("status") in {"unregistered", "candidate-unregistered"}:
        return "未登记", "unregistered"
    if node.get("session_state") in {"missing", "unavailable"}:
        return "缺少任务记录", "session-missing"
    if node.get("lifecycle_phase") in {"closed", "integrated", "historical"} or node.get("status") in {"inactive", "completed", "cancelled"}:
        return "历史任务", "historical"
    if node.get("session_state") == "stale" or node.get("evidence_freshness") == "stale" or node.get("scope_status") == "stale":
        return "状态待刷新／证据过期", "stale-evidence"
    if node.get("evidence_freshness") == "unknown" or node.get("scope_status") == "unknown" or node.get("status") == "unknown":
        return "关系证据不足", "relation-evidence-insufficient"
    if node.get("runtime_condition") == "active":
        return "正在进行", "in-progress"
    return "状态待刷新／证据过期", "state-refresh-required"


def _node_is_active_tip(node: Mapping[str, Any]) -> bool:
    return (
        node.get("status") in ACTIVE_NODE_STATUSES
        and node.get("session_state") == "current"
        and node.get("runtime_condition") == "active"
        and node.get("evidence_freshness") == "current"
        and node.get("scope_status") == "current"
        and node.get("lifecycle_phase") not in ENDED_PHASES
    )


def _display_identity(workstream_id: str) -> tuple[str, str]:
    """Return a short task prefix and Chinese-first display name without changing the fact ID."""
    parts = [part for part in workstream_id.split("-") if part]
    prefix = parts[0] if parts and re.fullmatch(r"[A-Za-z]+[0-9][A-Za-z0-9.]*", parts[0]) else "任务"
    translated = [DISPLAY_WORDS[item.lower()] for item in parts[1:] if item.lower() in DISPLAY_WORDS]
    name = " · ".join(translated[:5]) if translated else "任务记录"
    return prefix, name


def _sanitize_node(value: Any, active_tip_ids: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RelationGraphUnavailable("invalid-core-payload", "Core node is invalid.")
    required = {
        "workstream_id", "status", "session_state", "lifecycle_phase", "runtime_condition",
        "evidence_freshness", "scope_status", "primary_subsystem_id", "affected_subsystem_ids",
        "visibility", "observability", "source_links", "origin",
    }
    if not required.issubset(value):
        raise RelationGraphUnavailable("invalid-core-payload", "Core node axes are incomplete.")
    workstream_id = _bounded_identifier(value.get("workstream_id"), "workstream_id")
    affected = value.get("affected_subsystem_ids")
    if not isinstance(affected, list) or any(not isinstance(item, str) or not item for item in affected):
        raise RelationGraphUnavailable("invalid-core-payload", "Core subsystem axes are invalid.")
    display_prefix, display_name = _display_identity(workstream_id)
    node = {
        "workstream_id": workstream_id,
        "display_prefix": display_prefix,
        "display_name": display_name,
        "status": str(value.get("status")),
        "session_state": str(value.get("session_state")),
        "lifecycle_phase": str(value.get("lifecycle_phase")),
        "runtime_condition": str(value.get("runtime_condition")),
        "evidence_freshness": str(value.get("evidence_freshness")),
        "scope_status": str(value.get("scope_status")),
        "closure_reason": value.get("closure_reason"),
        "head_oid": value.get("head_oid"),
        "primary_subsystem_id": _bounded_identifier(value.get("primary_subsystem_id"), "primary subsystem"),
        "affected_subsystem_ids": sorted(set(affected)),
        "visibility": _bounded_identifier(value.get("visibility"), "visibility"),
        "observability": _bounded_identifier(value.get("observability"), "observability"),
        "source_links": _safe_links(value.get("source_links")),
        "origin": str(value.get("origin")),
        "is_active_tip": workstream_id in active_tip_ids,
    }
    if node["is_active_tip"] and not _node_is_active_tip(node):
        raise RelationGraphUnavailable("contradictory-active-tip", "Core active tip contradicts its state axes.")
    node["plain_status"], node["plain_status_code"] = _plain_state(node)
    return node


def _sanitize_edge(value: Any, node_ids: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RelationGraphUnavailable("invalid-core-payload", "Core edge is invalid.")
    required = {
        "relation_id", "relation_type", "source_workstream_id", "target_workstream_id", "lifecycle",
        "evidence", "source_links", "effective_active_succession", "evidence_reason_codes",
    }
    if not required.issubset(value):
        raise RelationGraphUnavailable("invalid-core-payload", "Core edge fields are incomplete.")
    source = _bounded_identifier(value.get("source_workstream_id"), "edge source")
    target = _bounded_identifier(value.get("target_workstream_id"), "edge target")
    if source == target or source not in node_ids or target not in node_ids:
        raise RelationGraphUnavailable("dangling-node", "Core edge references a missing Workstream.")
    relation_type = value.get("relation_type")
    if relation_type not in {"derived_from", "depends_on", "absorbs"}:
        raise RelationGraphUnavailable("unsupported-relation", "Core relation kind is unsupported.")
    evidence = value.get("evidence")
    reasons = value.get("evidence_reason_codes")
    if not isinstance(evidence, Mapping) or not isinstance(reasons, list) or any(not isinstance(item, str) for item in reasons):
        raise RelationGraphUnavailable("dangling-evidence", "Core edge evidence is incomplete.")
    lifecycle = str(value.get("lifecycle"))
    certainty = "confirmed" if evidence.get("status") == "confirmed" else (
        "stale" if lifecycle == "stale" or evidence.get("status") == "stale" else
        "proposed" if lifecycle == "proposed" else "unknown"
    )
    return {
        "relation_id": _bounded_identifier(value.get("relation_id"), "relation_id"),
        "source_workstream_id": source,
        "target_workstream_id": target,
        "relation_type": relation_type,
        "lifecycle": lifecycle,
        "certainty": certainty,
        "effective_active_succession": bool(value.get("effective_active_succession")),
        "evidence_status": str(evidence.get("status", "unknown")),
        "evidence": dict(evidence),
        "evidence_reason_codes": sorted(set(reasons)),
        "source_links": _safe_links(value.get("source_links")),
        "origin": str(value.get("origin", "unknown")),
        "required_for": value.get("required_for"),
    }


def _capture_proposal_edge(value: Any, node_ids: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("contract_type") != "workstream-relation-proposal-event":
        raise RelationGraphUnavailable("invalid-provider", "Relation capture proposal is malformed.")
    source = _bounded_identifier(value.get("source_workstream_id"), "capture proposal source")
    target = _bounded_identifier(value.get("target_workstream_id"), "capture proposal target")
    if source == target or source not in node_ids or target not in node_ids:
        raise RelationGraphUnavailable("dangling-node", "Relation capture proposal references a missing Workstream.")
    relation_type = value.get("relation_type")
    required_for = value.get("required_for")
    if relation_type not in {"derived_from", "depends_on", "absorbs"}:
        raise RelationGraphUnavailable("unsupported-relation", "Capture proposal relation kind is unsupported.")
    if relation_type == "depends_on" and required_for not in {"implementation", "validation", "integration", "release"}:
        raise RelationGraphUnavailable("invalid-provider", "Capture dependency proposal has no explicit gate.")
    evidence = value.get("evidence")
    if not isinstance(evidence, list):
        raise RelationGraphUnavailable("invalid-provider", "Capture proposal evidence is malformed.")
    return {
        "relation_id": _bounded_identifier(value.get("relation_id"), "capture relation_id"),
        "proposal_id": _bounded_identifier(value.get("proposal_id"), "capture proposal_id"),
        "source_workstream_id": source,
        "target_workstream_id": target,
        "relation_type": relation_type,
        "required_for": required_for,
        "lifecycle": "proposed",
        "certainty": "proposed",
        "effective_active_succession": False,
        "evidence_status": "unknown",
        "evidence": {"status": "unknown", "capture_revision": value.get("revision")},
        "evidence_reason_codes": ["human-confirmation-pending"],
        "source_links": _safe_links([{"kind": item.get("category"), "ref": item.get("ref")} for item in evidence]),
        "origin": "capture-v2-proposal",
        "rationale": str(value.get("rationale", "")),
        "consequence": str(value.get("consequence", "")),
    }


def build_relation_graph_projection(provider_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and map one complete Core provider envelope, or fail closed."""
    if not isinstance(provider_payload, Mapping):
        raise RelationGraphUnavailable("invalid-provider", "Core relation provider is unavailable.")
    if provider_payload.get("provider_schema_version") != PROVIDER_SCHEMA_VERSION:
        raise RelationGraphUnavailable("unsupported-provider-schema", "Core relation provider schema is unsupported.")
    if provider_payload.get("provider_id") != PROVIDER_ID:
        raise RelationGraphUnavailable("invalid-provider", "Core relation provider identity is unsupported.")
    relation_root_present = provider_payload.get("relation_root_present")
    if not isinstance(relation_root_present, bool):
        raise RelationGraphUnavailable("invalid-provider", "Core relation source fact is malformed.")
    graph = provider_payload.get("graph")
    plan = provider_payload.get("succession_plan")
    if not isinstance(graph, Mapping) or not isinstance(plan, Mapping):
        raise RelationGraphUnavailable("invalid-provider", "Core graph or succession plan is unavailable.")
    if graph.get("schema_version") != 1 or graph.get("contract_type") != GRAPH_CONTRACT:
        raise RelationGraphUnavailable("unsupported-graph-schema", "Core relation graph schema is unsupported.")
    if plan.get("schema_version") != 1 or plan.get("contract_type") != PLAN_CONTRACT:
        raise RelationGraphUnavailable("unsupported-plan-schema", "Core succession plan schema is unsupported.")
    validation = graph.get("validation")
    if not isinstance(validation, Mapping) or validation.get("valid") is not True or validation.get("errors"):
        raise RelationGraphUnavailable("core-graph-invalid", "Core relation graph validation failed.")
    if graph.get("read_only") is not True or graph.get("writes_performed") is not False:
        raise RelationGraphUnavailable("unsafe-core-contract", "Core graph is not a read-only projection.")
    if (
        plan.get("read_only") is not True or plan.get("writes_performed") is not False
        or plan.get("destructive_actions") != [] or plan.get("graph_hash") != graph.get("graph_hash")
    ):
        raise RelationGraphUnavailable("unsafe-plan-contract", "Core succession plan binding is invalid.")
    if not HASH.fullmatch(str(graph.get("graph_hash", ""))):
        raise RelationGraphUnavailable("invalid-core-payload", "Core relation graph hash binding is invalid.")
    graph_body = {key: value for key, value in graph.items() if key != "graph_hash"}
    actual_graph_hash = hashlib.sha256(_canonical_json(graph_body).encode("utf-8")).hexdigest()
    if actual_graph_hash != graph.get("graph_hash"):
        raise RelationGraphUnavailable("invalid-core-payload", "Core relation graph content hash does not match.")
    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    active_tip_values = plan.get("active_tip_workstream_ids")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list) or not isinstance(active_tip_values, list):
        raise RelationGraphUnavailable("invalid-core-payload", "Core graph collections are invalid.")
    if not raw_nodes and not raw_edges:
        raise RelationGraphUnavailable(
            "relation-evidence-absent",
            "No native or validated legacy/archive relation evidence is available.",
        )
    active_tip_ids = {_bounded_identifier(item, "active tip") for item in active_tip_values}
    nodes = [_sanitize_node(item, active_tip_ids) for item in raw_nodes]
    node_ids = {item["workstream_id"] for item in nodes}
    if len(node_ids) != len(nodes) or not active_tip_ids.issubset(node_ids):
        raise RelationGraphUnavailable("dangling-node", "Core node identity is duplicate or missing.")
    edges = [_sanitize_edge(item, node_ids) for item in raw_edges]
    capture_payload = provider_payload.get("relation_capture")
    capture_gate_by_relation: dict[str, str | None] = {}
    if capture_payload is not None:
        if not isinstance(capture_payload, Mapping) or capture_payload.get("schema_version") != 2:
            raise RelationGraphUnavailable("invalid-provider", "Relation capture projection is malformed.")
        effective_values = capture_payload.get("effective_relations", [])
        pending_values = capture_payload.get("pending_proposals", [])
        if not isinstance(effective_values, list) or not isinstance(pending_values, list):
            raise RelationGraphUnavailable("invalid-provider", "Relation capture collections are malformed.")
        for item in effective_values:
            if not isinstance(item, Mapping) or not isinstance(item.get("current"), Mapping):
                raise RelationGraphUnavailable("invalid-provider", "Effective capture relation is malformed.")
            current = item["current"]
            capture_gate_by_relation[str(current.get("relation_id"))] = current.get("required_for")
        for edge in edges:
            if edge["relation_id"] in capture_gate_by_relation:
                edge["required_for"] = capture_gate_by_relation[edge["relation_id"]]
        edges.extend(_capture_proposal_edge(item.get("current"), node_ids) for item in pending_values if isinstance(item, Mapping))
    edge_ids = {item["relation_id"] for item in edges}
    if len(edge_ids) != len(edges):
        raise RelationGraphUnavailable("invalid-core-payload", "Core relation identity is duplicated.")
    compare_values = plan.get("compare_pairs")
    suppress_values = plan.get("suppress_direct_pairs")
    if not isinstance(compare_values, list) or not isinstance(suppress_values, list):
        raise RelationGraphUnavailable("invalid-core-payload", "Core pair plan collections are invalid.")
    comparison_suggestions = [_validate_pair(item, node_ids, disposition="compare") for item in compare_values]
    suppressed_pairs = [_validate_pair(item, node_ids, disposition="suppress") for item in suppress_values]
    conflicts = [item for item in (_explicit_conflict(pair) for pair in comparison_suggestions) if item is not None]
    conflict_ids = {item["id"].replace("conflict:", "compare:") for item in conflicts}
    comparison_suggestions = [item for item in comparison_suggestions if item["id"] not in conflict_ids]
    series_payload = provider_payload.get("task_series", {"items": []})
    if not isinstance(series_payload, Mapping) or not isinstance(series_payload.get("items", []), list):
        raise RelationGraphUnavailable("invalid-provider", "Task series metadata is malformed.")
    series_by_workstream: dict[str, Mapping[str, Any]] = {}
    for item in series_payload.get("items", []):
        if not isinstance(item, Mapping) or item.get("workstream_id") not in node_ids:
            continue
        series_by_workstream[str(item["workstream_id"])] = item
    for node in nodes:
        series = series_by_workstream.get(node["workstream_id"])
        node["series_id"] = str(series["series_id"]) if series else None
        node["task_code"] = str(series["task_code"]) if series else None
        node["series_order"] = int(series["series_order"]) if series else None
    unknown_values = plan.get("unknown_workstream_ids")
    if not isinstance(unknown_values, list) or any(item not in node_ids for item in unknown_values):
        raise RelationGraphUnavailable("dangling-node", "Core Unknown node list is invalid.")
    direct_to_tip = {
        endpoint
        for edge in edges
        if edge["source_workstream_id"] in active_tip_ids or edge["target_workstream_id"] in active_tip_ids
        for endpoint in (edge["source_workstream_id"], edge["target_workstream_id"])
    }
    historical = sorted(
        item["workstream_id"] for item in nodes
        if item["workstream_id"] not in active_tip_ids | direct_to_tip
        and item["status"] in {"inactive", "completed", "cancelled"}
    )
    authority = str(provider_payload.get("authority", "derived-read-only"))
    if authority not in {"derived-read-only", "synthetic-non-authoritative"}:
        raise RelationGraphUnavailable("invalid-provider", "Core provider authority marker is unsupported.")
    evidence_origins = sorted({
        str(item.get("origin", "unknown")) for item in [*nodes, *edges]
    })
    if authority == "derived-read-only" and not (
        {"native", "legacy-session-projection"} & set(evidence_origins)
    ):
        raise RelationGraphUnavailable(
            "relation-evidence-absent",
            "The graph has no native or validated legacy/archive evidence.",
        )
    return {
        "projection_schema_version": PROJECTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-graph-observatory",
        "status": "ready",
        "authority": authority,
        "provider_id": PROVIDER_ID,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "graph_contract": GRAPH_CONTRACT,
        "plan_contract": PLAN_CONTRACT,
        "graph_hash": graph.get("graph_hash"),
        "native_relation_root_present": relation_root_present,
        "evidence_origins": evidence_origins,
        "nodes": sorted(nodes, key=lambda item: item["workstream_id"]),
        "edges": sorted(edges, key=lambda item: (item["relation_type"], item["source_workstream_id"], item["target_workstream_id"], item["relation_id"])),
        "conflicts": sorted(conflicts, key=lambda item: item["id"]),
        "comparison_suggestions": sorted(comparison_suggestions, key=lambda item: item["id"]),
        "suppressed_pairs": sorted(suppressed_pairs, key=lambda item: item["id"]),
        "task_series": sorted({str(item["series_id"]) for item in series_by_workstream.values()}),
        "active_tip_workstream_ids": sorted(active_tip_ids),
        "unknown_workstream_ids": sorted(unknown_values),
        "history_candidate_ids": historical,
        "blocking_dependencies": list(plan.get("blocking_dependencies", [])),
        "read_only": True,
        "writes_performed": False,
        "network_performed": False,
        "execution_capability": False,
        "available_actions": [],
    }


def unavailable_relation_graph_projection(error: Exception) -> dict[str, Any]:
    code = error.code if isinstance(error, RelationGraphUnavailable) else "core-provider-failure"
    messages = {
        "relation-store-absent": "当前没有可验证的任务关系证据。",
        "relation-evidence-absent": "当前没有原生或经验证的历史／归档任务关系证据。",
        "legacy-unknown": "历史任务关系证据不足，未生成不完整关系图。",
        "unsafe-source-link": "证据链接未通过安全白名单，未生成不完整关系图。",
        "dangling-node": "关系图包含缺失的任务引用，未生成不完整关系图。",
        "dangling-evidence": "关系图包含缺失证据，未生成不完整关系图。",
        "core-graph-invalid": "核心任务关系验证失败，未生成不完整关系图。",
    }
    return {
        "projection_schema_version": PROJECTION_SCHEMA_VERSION,
        "contract_type": "workstream-relation-graph-observatory",
        "status": "unavailable",
        "authority": "derived-read-only",
        "provider_id": PROVIDER_ID,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "error": {"code": code, "message": messages.get(code, "当前无法读取完整的任务关系，未生成不完整关系图。")},
        "nodes": [], "edges": [], "conflicts": [], "comparison_suggestions": [], "suppressed_pairs": [], "task_series": [], "active_tip_workstream_ids": [],
        "unknown_workstream_ids": [], "history_candidate_ids": [], "blocking_dependencies": [],
        "read_only": True, "writes_performed": False, "network_performed": False,
        "execution_capability": False, "available_actions": [],
    }


def project_core_relation_graph(provider: Callable[[], Mapping[str, Any]]) -> dict[str, Any]:
    try:
        return build_relation_graph_projection(provider())
    except Exception as error:  # the view itself remains reachable
        return unavailable_relation_graph_projection(error)


def _lens_edges(projection: Mapping[str, Any], lens: str) -> list[dict[str, Any]]:
    if lens == "conflict":
        values = projection.get("conflicts", [])
    else:
        allowed = {"derived_from", "absorbs"} if lens == "succession" else {"depends_on"}
        values = [
            item for item in projection.get("edges", [])
            if item.get("relation_type") in allowed and item.get("lifecycle") != "cancelled"
        ]
    result: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        edge = dict(item)
        if lens == "conflict":
            left, right = sorted((str(item["source_workstream_id"]), str(item["target_workstream_id"])))
            edge["display_from_id"], edge["display_to_id"] = left, right
        else:
            # Core records source=successor/dependent and target=predecessor/dependency.
            edge["display_from_id"] = str(item["target_workstream_id"])
            edge["display_to_id"] = str(item["source_workstream_id"])
        edge["display_edge_id"] = str(item.get("relation_id") or item.get("id") or f"edge-{index}")
        result.append(edge)
    return result


def _ordered_ancestors(tip: str, incoming: Mapping[str, set[str]]) -> list[str]:
    """Return a stable oldest-to-newest traversal for one visible tip."""
    found: set[str] = set()
    ordered: list[str] = []

    def visit(workstream_id: str) -> None:
        for item in sorted(incoming.get(workstream_id, set())):
            if item in found:
                continue
            found.add(item)
            visit(item)
            ordered.append(item)

    visit(tip)
    return ordered


def build_readability_layout(
    projection: Mapping[str, Any],
    *,
    lens: str = "succession",
    expanded_chain_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a deterministic presentation-only layout for mechanical and browser parity checks."""
    if lens not in {"succession", "dependency", "conflict"}:
        raise ValueError("lens must be succession, dependency, or conflict")
    nodes_by_id = {str(item["workstream_id"]): dict(item) for item in projection.get("nodes", [])}
    edges = _lens_edges(projection, lens)
    endpoint_ids = {
        endpoint for item in edges
        for endpoint in (item["display_from_id"], item["display_to_id"])
    }
    if lens == "succession":
        endpoint_ids.update(str(item) for item in projection.get("active_tip_workstream_ids", []))
    incoming: dict[str, set[str]] = {item: set() for item in endpoint_ids}
    outgoing: dict[str, set[str]] = {item: set() for item in endpoint_ids}
    for item in edges:
        source, target = item["display_from_id"], item["display_to_id"]
        outgoing.setdefault(source, set()).add(target)
        incoming.setdefault(target, set()).add(source)

    expanded = set(expanded_chain_ids)
    visible_ids: set[str] = set()
    chains: list[dict[str, Any]] = []
    claimed_history: set[str] = set()
    if lens == "conflict":
        visible_ids.update(endpoint_ids)
    else:
        tips = sorted(item for item in endpoint_ids if not outgoing.get(item))
        if lens == "succession":
            tips = sorted(set(tips) | set(str(item) for item in projection.get("active_tip_workstream_ids", [])))
        for tip in tips:
            chain_id = "chain:" + tip
            direct = set(incoming.get(tip, set()))
            siblings = {sibling for predecessor in direct for sibling in outgoing.get(predecessor, set())}
            default_ids = {tip, *direct, *siblings}
            older = [
                item for item in _ordered_ancestors(tip, incoming)
                if item not in default_ids and item not in claimed_history
            ]
            claimed_history.update(older)
            visible_ids.update(default_ids)
            if chain_id in expanded:
                visible_ids.update(older)
            chains.append({
                "chain_id": chain_id,
                "tip_id": tip,
                "direct_ids": sorted(direct),
                "history_ids": older,
                "expanded": chain_id in expanded,
            })

    visible_nodes = [nodes_by_id[item] for item in sorted(visible_ids) if item in nodes_by_id]
    for chain in chains:
        if not chain["expanded"] or not chain["history_ids"]:
            continue
        toggle_node = next(
            (
                item for item in visible_nodes
                if item["workstream_id"] == chain["history_ids"][0]
            ),
            None,
        )
        if toggle_node is not None:
            toggle_node["collapse_chain_id"] = chain["chain_id"]
            toggle_node["expanded_history_count"] = len(chain["history_ids"])
    cluster_nodes: list[dict[str, Any]] = []
    cluster_edges: list[dict[str, Any]] = []
    hidden_owner: dict[str, str] = {}
    for chain in chains:
        if chain["expanded"] or not chain["history_ids"]:
            continue
        cluster_id = "history:" + chain["tip_id"]
        for item in chain["history_ids"]:
            hidden_owner[item] = cluster_id
        cluster_nodes.append({
            "workstream_id": cluster_id,
            "display_prefix": f"+{len(chain['history_ids'])}",
            "display_name": "折叠的上游链",
            "status": "inactive",
            "runtime_condition": "collapsed",
            "lifecycle_phase": "historical",
            "evidence_freshness": "historical",
            "scope_status": "historical",
            "primary_subsystem_id": "历史任务",
            "source_links": [],
            "is_cluster": True,
            "chain_id": chain["chain_id"],
            "cluster_ids": list(chain["history_ids"]),
            "cluster_first_id": chain["history_ids"][0],
            "cluster_last_id": chain["history_ids"][-1],
            "cluster_tip_id": chain["tip_id"],
        })
    visible_nodes.extend(cluster_nodes)

    display_edges: list[dict[str, Any]] = []
    seen_clusters: set[tuple[str, str, str]] = set()
    for edge in edges:
        source, target = edge["display_from_id"], edge["display_to_id"]
        mapped_source, mapped_target = hidden_owner.get(source, source), hidden_owner.get(target, target)
        if mapped_source == mapped_target:
            continue
        if mapped_source in {item["workstream_id"] for item in visible_nodes} and mapped_target in {
            item["workstream_id"] for item in visible_nodes
        }:
            key = (mapped_source, mapped_target, str(edge.get("relation_type")))
            if key in seen_clusters:
                continue
            seen_clusters.add(key)
            item = dict(edge)
            item["display_from_id"], item["display_to_id"] = mapped_source, mapped_target
            item["collapsed_history_edge"] = mapped_source != source or mapped_target != target
            display_edges.append(item)

    node_ids = {item["workstream_id"] for item in visible_nodes}
    indegree = {item: 0 for item in node_ids}
    adjacency = {item: set() for item in node_ids}
    for edge in display_edges:
        source, target = edge["display_from_id"], edge["display_to_id"]
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1
    rank = {item: 0 for item in node_ids}
    queue = sorted(item for item, degree in indegree.items() if degree == 0)
    visited: list[str] = []
    while queue:
        item = queue.pop(0)
        visited.append(item)
        for target in sorted(adjacency[item]):
            rank[target] = max(rank[target], rank[item] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    for item in sorted(node_ids - set(visited)):
        rank[item] = 1 if lens == "conflict" else 0

    groups: dict[int, list[dict[str, Any]]] = {}
    for node in visible_nodes:
        groups.setdefault(rank[node["workstream_id"]], []).append(node)
    for values in groups.values():
        values.sort(key=lambda item: (not bool(item.get("is_cluster")), str(item["workstream_id"])))
    # Connected components own horizontal bands.  A simple chain therefore
    # stays on one row and reads like an engineering diagram instead of a set
    # of unrelated cards joined through a label shelf.
    undirected = {item: set() for item in node_ids}
    for edge in display_edges:
        source, target = edge["display_from_id"], edge["display_to_id"]
        undirected[source].add(target)
        undirected[target].add(source)
    components: list[list[str]] = []
    assigned: set[str] = set()
    for seed in sorted(node_ids):
        if seed in assigned:
            continue
        members: list[str] = []
        pending = [seed]
        assigned.add(seed)
        while pending:
            item = pending.pop(0)
            members.append(item)
            for sibling in sorted(undirected[item]):
                if sibling not in assigned:
                    assigned.add(sibling)
                    pending.append(sibling)
        components.append(sorted(members))

    node_top = 112
    positions: dict[str, dict[str, int]] = {}
    row_cursor = 0
    for component_index, members in enumerate(sorted(components, key=lambda item: item[0])):
        member_ids = set(members)
        by_rank = {
            rank_value: [node for node in values if node["workstream_id"] in member_ids]
            for rank_value, values in sorted(groups.items())
        }
        by_rank = {rank_value: values for rank_value, values in by_rank.items() if values}
        component_rows = max((len(values) for values in by_rank.values()), default=1)
        for rank_value, values in by_rank.items():
            for local_row, node in enumerate(values):
                positions[node["workstream_id"]] = {
                    "x": 36 + rank_value * (NODE_WIDTH + RANK_GAP),
                    "y": node_top + (row_cursor + local_row) * (NODE_HEIGHT + ROW_GAP),
                    "width": NODE_WIDTH,
                    "height": NODE_HEIGHT,
                    "rank": rank_value,
                    "row": row_cursor + local_row,
                    "component": component_index,
                }
        row_cursor += component_rows + 1
    max_rows = max(1, row_cursor - 1 if row_cursor else 1)
    routes: list[dict[str, Any]] = []
    for index, edge in enumerate(display_edges):
        source = positions[edge["display_from_id"]]
        target = positions[edge["display_to_id"]]
        start = (source["x"] + source["width"], source["y"] + source["height"] // 2)
        end = (target["x"], target["y"] + target["height"] // 2)
        rank_span = max(1, target["rank"] - source["rank"])
        if start[1] == end[1] and rank_span == 1:
            points = [start, end]
        elif rank_span == 1:
            middle = (start[0] + end[0]) // 2
            points = [start, (middle, start[1]), (middle, end[1]), end]
        else:
            start_channel = start[0] + 22
            end_channel = end[0] - 22
            track_y = max(88, min(source["y"], target["y"]) - 20 - (index % 4) * 8)
            points = [
                start, (start_channel, start[1]), (start_channel, track_y),
                (end_channel, track_y), (end_channel, end[1]), end,
            ]
        routes.append({
            "edge_id": edge["display_edge_id"], "points": points,
            "has_arrow": True, "has_label": False,
            "line_encoding": (
                "dashed" if lens == "dependency" else
                "compound" if lens == "conflict" else "solid"
            ),
        })
    max_rank = max(groups, default=-1)
    lane_titles = []
    for rank_value in range(max_rank + 1):
        values = groups.get(rank_value, [])
        if any(item.get("is_cluster") for item in values):
            title = "更早历史"
        elif any(item.get("is_active_tip") for item in values):
            title = "当前任务"
        elif rank_value == max_rank:
            title = "当前／后续任务"
        else:
            title = "直接前置／依赖"
        lane_titles.append({"rank": rank_value, "title": title})
    return {
        "lens": lens,
        "nodes": visible_nodes,
        "edges": display_edges,
        "chains": chains,
        "positions": positions,
        "routes": routes,
        "lanes": lane_titles,
        "width": (
            72 + (max_rank + 1) * NODE_WIDTH + max_rank * RANK_GAP
            if node_ids else 1
        ),
        "height": node_top + max_rows * (NODE_HEIGHT + ROW_GAP) + 34 if node_ids else 1,
        "visible_fact_ids": sorted(item for item in visible_ids if item in nodes_by_id),
    }


WORKSTREAM_GRAPH_CSS = r"""
.wg-shell{--wg-cyan:#5fcfc7;--wg-amber:#efb759;--wg-red:#f07467;--wg-ink:#d8e1ee;--wg-dim:#8490a3;margin:0 0 24px;border:1px solid var(--line);border-radius:15px;overflow:hidden;background:linear-gradient(180deg,rgba(95,207,199,.055),transparent 210px),var(--bg)}
.wg-shell *{box-sizing:border-box}.wg-mast{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;padding:22px 24px 17px;border-bottom:1px solid var(--line)}.wg-kicker,.wg-panel-index{margin:0;color:var(--wg-cyan);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;letter-spacing:.13em;text-transform:uppercase}.wg-mast h2{margin:4px 0;font-size:26px;letter-spacing:-.025em}.wg-mast p{margin:0;color:var(--mut);font-size:12.5px}.wg-seal{align-self:start;padding:7px 10px;border:1px solid var(--line);border-radius:6px;color:var(--wg-dim);font:700 10px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em}.wg-seal.ready::before{content:"◇ ";color:var(--wg-cyan)}.wg-seal.unavailable::before{content:"? ";color:var(--wg-amber)}
.wg-failure{margin:16px 24px 0;padding:12px 14px;border:1px dashed var(--wg-amber);background:rgba(239,183,89,.06);color:var(--mut);border-radius:8px}.wg-failure b{display:block;color:var(--wg-amber);margin-bottom:3px}.wg-controls{padding:17px 24px;border-bottom:1px solid var(--line)}.wg-lenses{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:9px;overflow:hidden}.wg-lens{min-width:0;border:0;border-radius:0;padding:11px 13px;background:var(--bg2);color:var(--fg);font:inherit;text-align:left;cursor:pointer}.wg-lens span{display:block;color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace}.wg-lens b{display:block;margin-top:3px}.wg-lens[aria-pressed="true"]{box-shadow:inset 0 -3px 0 var(--wg-cyan);background:rgba(95,207,199,.08)}.wg-filterbar{display:grid;grid-template-columns:minmax(150px,1fr) minmax(150px,1fr) auto auto;gap:9px;margin-top:10px}.wg-filterbar label{display:grid;gap:4px;color:var(--mut);font-size:10px}.wg-filterbar select,.wg-button{min-height:38px;border:1px solid var(--line);border-radius:7px;background:var(--bg2);color:var(--fg);font:600 11px/1.2 inherit;padding:0 10px}.wg-button{align-self:end;cursor:pointer}.wg-button:disabled{opacity:.45;cursor:not-allowed}
.wg-grid{display:grid;grid-template-columns:minmax(0,1.8fr) minmax(260px,.72fr);min-height:520px}.wg-graph-panel{min-width:0;padding:18px 20px 20px;border-right:1px solid var(--line)}.wg-panel-head{display:flex;justify-content:space-between;gap:12px;align-items:end}.wg-panel-head h3{margin:3px 0 0;font-size:17px}.wg-legend{display:flex;gap:10px;flex-wrap:wrap;color:var(--mut);font-size:10px}.wg-legend i{display:inline-block;width:18px;border-top:2px solid var(--wg-cyan);vertical-align:middle;margin-right:4px}.wg-legend .broken{border-top-style:dashed;border-color:var(--wg-amber)}.wg-legend .conflict{border-color:var(--wg-red)}.wg-frame{position:relative;margin-top:12px;min-height:420px;border:1px solid var(--line);border-radius:9px;overflow:hidden;background-image:linear-gradient(rgba(132,144,163,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(132,144,163,.07) 1px,transparent 1px);background-size:28px 28px}.wg-frame svg{display:block;width:100%;height:420px}.wg-edge{fill:none;stroke:var(--wg-cyan);stroke-width:2}.wg-edge.proposed,.wg-edge.unknown{stroke:var(--wg-amber);stroke-dasharray:8 6}.wg-edge.stale{stroke:var(--wg-dim);stroke-dasharray:2 6}.wg-edge.confirmed-conflict{stroke:var(--wg-red);stroke-width:4;stroke-dasharray:12 4 2 4}.wg-edge.suppressed{stroke:var(--wg-dim);stroke-dasharray:2 7}.wg-edge-hit{fill:none;stroke:rgba(255,255,255,.001);stroke-width:18;pointer-events:stroke;cursor:pointer}.wg-edge-label{font:700 9px "Cascadia Code",Consolas,monospace;fill:var(--wg-dim);paint-order:stroke;stroke:var(--bg);stroke-width:4px}.wg-node{cursor:pointer}.wg-node rect{fill:var(--bg2);stroke:var(--line);stroke-width:1.5}.wg-node.active-tip rect{stroke:var(--wg-cyan);stroke-width:3}.wg-node.active-tip .wg-tip-ring{fill:none;stroke:var(--wg-cyan);stroke-width:1;stroke-dasharray:3 3}.wg-node.unknown rect,.wg-node.stale rect{stroke:var(--wg-amber);stroke-dasharray:6 4}.wg-node.blocked rect,.wg-node.failed rect{stroke:var(--wg-red)}.wg-node-title{fill:var(--fg);font:700 12px "Cascadia Code",Consolas,monospace}.wg-node-meta{fill:var(--wg-dim);font:10px "Cascadia Code",Consolas,monospace}.wg-node-state{fill:var(--wg-amber);font:700 9px "Cascadia Code",Consolas,monospace}.wg-node.active-tip .wg-node-state{fill:var(--wg-cyan)}.wg-empty{position:absolute;inset:0;display:grid;place-content:center;text-align:center;color:var(--mut)}.wg-empty b{color:var(--wg-amber)}
.wg-inspector{min-width:0;padding:18px;background:rgba(0,0,0,.055)}.wg-inspector-head{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:9px;color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.1em}.wg-inspector h3{margin:14px 0 5px;font-size:17px;overflow-wrap:anywhere}.wg-inspector p{color:var(--mut);font-size:11.5px;overflow-wrap:anywhere}.wg-axis{display:grid;grid-template-columns:1fr auto;gap:8px;padding:7px 0;border-top:1px solid var(--line);font-size:11px}.wg-axis span{color:var(--mut)}.wg-reasons{margin:8px 0;padding-left:17px;color:var(--wg-amber);font:10px/1.6 "Cascadia Code",Consolas,monospace}.wg-evidence{display:grid;gap:6px;margin-top:12px}.wg-evidence a,.wg-evidence span{display:block;max-width:100%;padding:7px 8px;border:1px solid var(--line);border-radius:6px;color:var(--mut);font:10px/1.35 "Cascadia Code",Consolas,monospace;overflow-wrap:anywhere}.wg-evidence a{color:var(--wg-cyan);text-decoration:none}.wg-readonly{margin-top:14px;padding-top:10px;border-top:1px solid var(--line);color:var(--mut);font-size:10px}
.wg-ledger{display:block;padding:18px 20px;border-top:1px solid var(--line)}.wg-ledger h3{margin:0 0 10px}.wg-ledger-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.wg-ledger-item{width:100%;min-width:0;padding:11px;border:1px solid var(--line);border-left:3px solid var(--wg-cyan);border-radius:7px;background:var(--bg2);color:var(--fg);font:inherit;text-align:left}.wg-ledger-item.proposed,.wg-ledger-item.unknown{border-left-style:dashed;border-left-color:var(--wg-amber)}.wg-ledger-item.confirmed-conflict{border-left-color:var(--wg-red)}.wg-ledger-item small{display:block;margin-top:4px;color:var(--mut);overflow-wrap:anywhere}.wg-ledger-empty{padding:14px;border:1px dashed var(--line);color:var(--mut)}
.wg-edge-button{position:absolute;z-index:4;display:block;width:44px;height:44px;padding:0;border:0;border-radius:50%;background:rgba(255,255,255,.001);cursor:pointer}.wg-lens:focus-visible,.wg-button:focus-visible,.wg-filterbar select:focus-visible,.wg-ledger-item:focus-visible,.wg-node:focus-visible,.wg-edge-button:focus-visible,.wg-evidence a:focus-visible{outline:3px solid var(--wg-amber);outline-offset:3px}.wg-sr{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.wg-empty[hidden]{display:none}@media(max-width:900px){.wg-grid{grid-template-columns:1fr}.wg-graph-panel{border-right:0;border-bottom:1px solid var(--line)}.wg-inspector{min-height:260px}}
@media(max-width:640px){header.top{gap:8px;padding:0 12px}.top h1{min-width:0;overflow:hidden;text-overflow:ellipsis}.top .sub,.searchwrap{display:none}.rightgrp{min-width:0;gap:6px}.wg-mast{grid-template-columns:1fr;padding:18px}.wg-seal{justify-self:start}.wg-controls{padding:14px 18px}.wg-lenses{grid-template-columns:1fr}.wg-filterbar{grid-template-columns:minmax(0,1fr)}.wg-filterbar label,.wg-filterbar select,.wg-button{min-width:0;width:100%}.wg-button{width:100%}.wg-grid{min-height:0}.wg-graph-panel{padding:16px 18px}.wg-frame{min-height:116px}.wg-frame svg{height:116px;pointer-events:none;opacity:.28}.wg-frame::after{content:"移动端请使用下方的关系清单。";position:absolute;inset:0;display:grid;place-content:center;padding:20px;text-align:center;color:var(--mut);font:700 10px/1.4 "Cascadia Code",Consolas,monospace}.wg-legend{display:none}.wg-ledger-list{grid-template-columns:1fr}.wg-inspector{padding:18px}.wg-shell{max-width:100%;overflow:hidden}}
@media(prefers-reduced-motion:reduce){.wg-shell *{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
"""


WORKSTREAM_GRAPH_JS = r"""
(()=>{'use strict';const page=document.querySelector('#workstream-relation-graph');if(!page)return;
const data=JSON.parse(page.querySelector('[data-wg-payload]').textContent);const svg=page.querySelector('[data-wg-svg]'),ledger=page.querySelector('[data-wg-ledger]'),inspector=page.querySelector('[data-wg-inspector]'),live=page.querySelector('[data-wg-live]'),subsystem=page.querySelector('[data-wg-subsystem]'),runtime=page.querySelector('[data-wg-runtime]'),history=page.querySelector('[data-wg-history]');
const state={lens:'succession',history:false,subsystem:'all',runtime:'all',selection:null};const NS='http://www.w3.org/2000/svg';
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};const se=(tag,attrs={})=>{const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));return n};
const phaseLabels={created:'已创建',planning:'规划中',implementing:'实现中',validating:'验证中','review-ready':'等待审查',integrated:'已集成',closed:'已关闭',historical:'历史记录',unknown:'待确认'};const runtimeLabels={active:'进行中',paused:'已暂停','waiting-for-user':'等待确认','blocked-by-conflict':'存在冲突',failed:'失败',offline:'离线',collapsed:'已收起',unknown:'待确认'};const evidenceLabels={current:'当前',stale:'历史状态',unknown:'待确认',historical:'历史记录'};const shown=(map,value)=>map[value]||value||'待确认';
const nodeMap=new Map((data.nodes||[]).map(n=>[n.workstream_id,n]));
function lensEdges(){if(state.lens==='conflict')return data.conflicts||[];const types=state.lens==='succession'?new Set(['derived_from','absorbs']):new Set(['depends_on']);return(data.edges||[]).filter(e=>types.has(e.relation_type)&&e.lifecycle!=='cancelled')}
function matches(n){return(state.subsystem==='all'||n.primary_subsystem_id===state.subsystem||(n.affected_subsystem_ids||[]).includes(state.subsystem))&&(state.runtime==='all'||n.runtime_condition===state.runtime)}
function graph(){let edges=lensEdges(),ids=new Set();edges.forEach(e=>{ids.add(e.source_workstream_id);ids.add(e.target_workstream_id)});(data.active_tip_workstream_ids||[]).forEach(id=>ids.add(id));let nodes=(data.nodes||[]).filter(n=>ids.has(n.workstream_id)&&matches(n));let visible=new Set(nodes.map(n=>n.workstream_id));edges=edges.filter(e=>visible.has(e.source_workstream_id)&&visible.has(e.target_workstream_id));if(state.lens==='succession'&&!state.history){const historic=new Set((data.history_candidate_ids||[]).filter(id=>visible.has(id)));if(historic.size>1){nodes=nodes.filter(n=>!historic.has(n.workstream_id));nodes.unshift({workstream_id:'history-cluster',status:'inactive',runtime_condition:'collapsed',lifecycle_phase:'historical',evidence_freshness:'historical',scope_status:'historical',session_state:'historical',primary_subsystem_id:'multi-worktree-collaboration',affected_subsystem_ids:[],visibility:'derived',observability:'local',source_links:[],is_cluster:true,cluster_ids:[...historic].sort()});const seen=new Set();edges=edges.map(e=>({...e,source_workstream_id:historic.has(e.source_workstream_id)?'history-cluster':e.source_workstream_id,target_workstream_id:historic.has(e.target_workstream_id)?'history-cluster':e.target_workstream_id})).filter(e=>{if(e.source_workstream_id===e.target_workstream_id)return false;const k=e.source_workstream_id+'>'+e.target_workstream_id+e.relation_type;if(seen.has(k))return false;seen.add(k);return true})}}return{nodes,edges}}
function certainty(e){if(e.disposition==='suppress')return'suppressed';if(e.relation_type==='conflict-pair'&&e.certainty==='confirmed')return'confirmed-conflict';return e.certainty||'unknown'}function label(e){if(e.disposition==='suppress')return'已抑制';if(e.relation_type==='conflict-pair')return e.certainty==='confirmed'?'已确认直接冲突':'需要比较';if(e.certainty==='unknown')return'关系待确认';if(e.lifecycle==='proposed')return'建议关系';if(e.lifecycle==='stale')return'历史关系';return{derived_from:'继承自',absorbs:'吸收',depends_on:'依赖'}[e.relation_type]||e.relation_type}
function layout(nodes,edges){const levels=new Map(nodes.map(n=>[n.workstream_id,0]));for(let i=0;i<nodes.length;i++)edges.forEach(e=>{const next=Math.max(levels.get(e.source_workstream_id)||0,(levels.get(e.target_workstream_id)||0)+1);levels.set(e.source_workstream_id,Math.min(next,4))});const groups=new Map();nodes.forEach((n,index)=>{const level=state.lens==='conflict'?index%2:(levels.get(n.workstream_id)||0);if(!groups.has(level))groups.set(level,[]);groups.get(level).push(n)});const positions=new Map();let maxRows=1;[...groups.entries()].sort((a,b)=>a[0]-b[0]).forEach(([level,items])=>{items.sort((a,b)=>a.workstream_id.localeCompare(b.workstream_id));maxRows=Math.max(maxRows,items.length);items.forEach((n,row)=>positions.set(n.workstream_id,{x:36+level*224,y:state.lens==='conflict'?28+row*100:34+row*124,w:184,h:86}))});return{positions,width:state.lens==='conflict'?538:Math.max(520,90+(Math.max(0,...levels.values())+1)*224),height:Math.max(250,70+maxRows*(state.lens==='conflict'?100:124))}}
function edgePath(a,b){const sx=a.x+a.w,sy=a.y+a.h/2,tx=b.x,ty=b.y+b.h/2,bend=Math.max(45,(tx-sx)*.42);return{d:`M ${sx} ${sy} C ${sx+bend} ${sy}, ${tx-bend} ${ty}, ${tx} ${ty}`,x:(sx+tx)/2,y:(sy+ty)/2-8}}
function select(kind,item){state.selection={kind,item};renderInspector();live.textContent=(kind==='node'?'已选择任务 ':'已选择关系 ')+(item.workstream_id||item.relation_id||item.id)}
function renderInspector(){inspector.replaceChildren();const selected=state.selection;if(!selected){inspector.append(el('p',null,data.status==='ready'?'选择一个任务或关系以查看完整技术证据。':data.error.message));return}const item=selected.item;inspector.append(el('h3',null,item.workstream_id||item.relation_id||item.id));const axes=selected.kind==='node'?[['lifecycle',item.lifecycle_phase],['runtime',item.runtime_condition],['evidence',item.evidence_freshness],['scope',item.scope_status],['subsystem',item.primary_subsystem_id],['visibility',item.visibility],['observability',item.observability]]:[['relation',item.relation_type],['lifecycle',item.lifecycle],['certainty',item.certainty],['direction',item.source_workstream_id+' → '+item.target_workstream_id],['disposition',item.disposition||'edge']];axes.forEach(([k,v])=>{const row=el('div','wg-axis');row.append(el('span',null,k),el('b',null,v==null?'Unknown':String(v)));inspector.append(row)});const reasons=item.reason_codes||item.evidence_reason_codes||[];if(reasons.length){const ul=el('ul','wg-reasons');reasons.forEach(r=>ul.append(el('li',null,r)));inspector.append(ul)}const links=el('div','wg-evidence');(item.source_links||[]).forEach(link=>{const n=link.href?el('a',null,link.kind+' · '+link.ref):el('span',null,link.kind+' · '+link.ref);if(link.href){n.href=link.href;n.rel='noopener'}links.append(n)});if(!(item.source_links||[]).length)links.append(el('span',null,'没有可跳转的来源链接；证据状态见上方技术字段。'));inspector.append(links)}
function render(){const view=graph();svg.replaceChildren();const l=layout(view.nodes,view.edges);svg.setAttribute('viewBox',`0 0 ${l.width} ${l.height}`);const defs=se('defs');['cyan','amber','red','dim'].forEach((id,i)=>{const m=se('marker',{id:'wg-'+id,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto'});m.append(se('path',{d:'M0 0L10 5L0 10z',fill:['#5fcfc7','#efb759','#f07467','#8490a3'][i]}));defs.append(m)});svg.append(defs);view.edges.forEach(e=>{const a=l.positions.get(e.source_workstream_id),b=l.positions.get(e.target_workstream_id);if(!a||!b)return;const g=se('g'),p=edgePath(a,b),cls=certainty(e),path=se('path',{d:p.d,class:'wg-edge '+cls,'marker-end':`url(#wg-${cls==='confirmed-conflict'?'red':cls==='proposed'||cls==='unknown'?'amber':cls==='suppressed'||cls==='stale'?'dim':'cyan'})`}),hit=se('path',{d:p.d,class:'wg-edge-hit',tabindex:0,role:'button','aria-label':label(e)+' '+e.source_workstream_id+' 到 '+e.target_workstream_id});const text=se('text',{x:p.x,y:p.y,class:'wg-edge-label','text-anchor':'middle'});text.textContent=label(e);hit.addEventListener('click',()=>select('edge',e));hit.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();select('edge',e)}});g.append(path,hit,text);svg.append(g)});view.nodes.forEach(n=>{const p=l.positions.get(n.workstream_id),status=n.is_active_tip?'active-tip':n.status==='blocked'||n.runtime_condition==='blocked-by-conflict'?'blocked':n.status;const g=se('g',{class:'wg-node '+status,tabindex:0,role:'button','aria-label':n.workstream_id+' '+shown(runtimeLabels,n.runtime_condition)});g.append(se('rect',{x:p.x,y:p.y,width:p.w,height:p.h,rx:8}));if(n.is_active_tip)g.append(se('rect',{x:p.x-5,y:p.y-5,width:p.w+10,height:p.h+10,rx:11,class:'wg-tip-ring'}));const title=se('text',{x:p.x+12,y:p.y+23,class:'wg-node-title'});title.textContent=n.is_cluster?'历史记录 · '+n.cluster_ids.length:n.workstream_id;const meta=se('text',{x:p.x+12,y:p.y+45,class:'wg-node-meta'});meta.textContent=n.primary_subsystem_id==='unknown'?'待确认':n.primary_subsystem_id;const stateText=se('text',{x:p.x+12,y:p.y+68,class:'wg-node-state'});stateText.textContent=n.is_active_tip?'当前任务':shown(runtimeLabels,n.runtime_condition);g.append(title,meta,stateText);g.addEventListener('click',()=>select('node',n));g.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();select('node',n)}});svg.append(g)});renderLedger(view);page.querySelector('[data-wg-empty]').hidden=view.nodes.length>0;history.disabled=data.status!=='ready'||!(data.history_candidate_ids||[]).length;history.setAttribute('aria-pressed',String(state.history));history.textContent=state.history?'收起历史记录':'展开历史记录';if(state.selection)renderInspector()}
function keyboardActivate(button,action){button.addEventListener('click',action);button.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();action()}})}
function renderLedger(view){ledger.replaceChildren();if(!view.nodes.length&&!view.edges.length){ledger.append(el('div','wg-ledger-empty',data.status==='ready'?'当前筛选条件下没有关系事实。':'当前没有完整证据，因此未生成不完整关系图。'));return}view.nodes.forEach(n=>{const b=el('button','wg-ledger-item '+(n.is_active_tip?'active-tip':n.status));b.type='button';b.append(el('b',null,n.is_cluster?'已收起历史记录 · '+n.cluster_ids.length:n.workstream_id),el('small',null,shown(phaseLabels,n.lifecycle_phase)+' · '+shown(runtimeLabels,n.runtime_condition)+' · '+shown(evidenceLabels,n.evidence_freshness)));keyboardActivate(b,()=>select('node',n));ledger.append(b)});view.edges.forEach(e=>{const b=el('button','wg-ledger-item '+certainty(e));b.type='button';b.append(el('b',null,label(e)),el('small',null,e.source_workstream_id+' → '+e.target_workstream_id));keyboardActivate(b,()=>select('edge',e));ledger.append(b)})}
function options(select,values,labels={}){[...new Set(values.filter(Boolean))].sort().forEach(v=>{const o=el('option',null,labels[v]||v);o.value=v;select.append(o)})}options(subsystem,(data.nodes||[]).flatMap(n=>[n.primary_subsystem_id,...(n.affected_subsystem_ids||[])]),{unknown:'待确认'});options(runtime,(data.nodes||[]).map(n=>n.runtime_condition),runtimeLabels);page.querySelectorAll('[data-wg-lens]').forEach(b=>b.addEventListener('click',()=>{state.lens=b.dataset.wgLens;page.querySelectorAll('[data-wg-lens]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));state.selection=null;render();renderInspector()}));subsystem.addEventListener('change',()=>{state.subsystem=subsystem.value;render()});runtime.addEventListener('change',()=>{state.runtime=runtime.value;render()});history.addEventListener('click',()=>{state.history=!state.history;render()});page.querySelector('[data-wg-reset]').addEventListener('click',()=>{state.history=false;state.subsystem='all';state.runtime='all';subsystem.value='all';runtime.value='all';render()});render();renderInspector();})();
"""


WORKSTREAM_GRAPH_EDGE_TARGET_JS = r"""
(()=>{'use strict';const svg=document.querySelector('#workstream-relation-graph [data-wg-svg]');if(!svg)return;
function install(){svg.querySelectorAll('.wg-edge-hit').forEach(path=>{path.removeAttribute('role');path.removeAttribute('tabindex');path.setAttribute('aria-hidden','true')})}
let queued=false;const observer=new MutationObserver(()=>{if(queued)return;queued=true;queueMicrotask(()=>{queued=false;observer.disconnect();install();observer.observe(svg,{childList:true,subtree:true})})});install();observer.observe(svg,{childList:true,subtree:true});})();
"""

# W7.2 keeps the previous bytes above only as an internal rollback reference while the shipped
# presentation is owned by a focused module. Core/provider contracts remain untouched.
from .workstream_graph_presentation import (  # noqa: E402
    WORKSTREAM_GRAPH_CSS as _PROGRESSIVE_WORKSTREAM_GRAPH_CSS,
    WORKSTREAM_GRAPH_JS as _PROGRESSIVE_WORKSTREAM_GRAPH_JS,
)

WORKSTREAM_GRAPH_CSS = _PROGRESSIVE_WORKSTREAM_GRAPH_CSS
WORKSTREAM_GRAPH_JS = _PROGRESSIVE_WORKSTREAM_GRAPH_JS


def render_workstream_relation_graph_panel(projection: Mapping[str, Any]) -> str:
    status = str(projection.get("status", "unavailable"))
    authority = str(projection.get("authority", "derived-read-only"))
    error = projection.get("error") if isinstance(projection.get("error"), Mapping) else None
    failure = ""
    if error:
        failure = (
            '<div class="wg-failure" role="status"><b>当前暂不可用</b>%s</div>'
            % html.escape(str(error.get("message", "当前无法读取完整的任务关系。")))
        )
    payload = _canonical_json(dict(projection)).replace("<", "\\u003c")
    series_groups: dict[str, list[Mapping[str, Any]]] = {}
    for node in projection.get("nodes", []):
        if isinstance(node, Mapping) and node.get("series_id"):
            series_groups.setdefault(str(node["series_id"]), []).append(node)
    series_html = "".join(
        '<div class="wg-series-lane"><b>%s 系列</b><span>%s</span></div>' % (
            html.escape(series_id),
            " · ".join(
                html.escape(str(item.get("task_code") or item.get("workstream_id")))
                for item in sorted(values, key=lambda value: (value.get("series_order") is None, value.get("series_order") or 0, value.get("workstream_id")))
            ),
        )
        for series_id, values in sorted(series_groups.items())
    ) or '<div class="wg-series-empty">当前没有显式任务系列元数据；不会从任务名称推断。</div>'
    return (
        '<article class="page wide" id="workstream-relation-graph" data-kind="workstream-relation-graph" '
        'data-title="任务关系" data-authority="%s" data-read-only="true">'
        '<section class="wg-shell"><header class="wg-mast"><div><p class="wg-kicker">任务关系图 · 只读</p>'
        '<h2>任务关系</h2><p>从左到右阅读：更早历史 → 直接前置／依赖 → 当前任务。每条链可独立展开，本页不会执行任何操作。</p></div>'
        '<div class="wg-seal %s">%s · 技术结构版本 2</div></header>%s'
        '<section class="wg-series" aria-label="显式任务系列"><div><h3>任务系列</h3><p>仅作结构化展示分组，不表示因果或依赖边。</p></div><div class="wg-series-lanes">%s</div></section>'
        '<section class="wg-controls" aria-label="任务关系控制"><div class="wg-lenses" role="group" aria-label="关系类型">'
        '<button class="wg-lens" type="button" data-wg-lens="succession" aria-pressed="true"><span>01</span><b>接续关系</b></button>'
        '<button class="wg-lens" type="button" data-wg-lens="dependency" aria-pressed="false"><span>02</span><b>依赖关系</b></button>'
        '<button class="wg-lens" type="button" data-wg-lens="conflict" aria-pressed="false"><span>03</span><b>冲突关系</b></button></div>'
        '<div class="wg-filterbar"><label>项目模块<select data-wg-subsystem><option value="all">全部模块</option></select></label>'
        '<label>运行状态<select data-wg-runtime><option value="all">全部状态</option></select></label>'
        '<button class="wg-button" type="button" data-wg-expand-all>展开全部历史</button>'
        '<button class="wg-button" type="button" data-wg-collapse-all>收起全部历史</button>'
        '<button class="wg-button" type="button" data-wg-reset>重置布局</button></div>'
        '<div class="wg-viewbar" role="toolbar" aria-label="关系图视图工具"><span class="wg-viewbar-note">默认保持 100%% 可读；画布内按住 Ctrl＋滚轮缩放，空白处拖动平移。</span>'
        '<button class="wg-button" type="button" data-wg-zoom-out aria-label="缩小关系图">−</button><span class="wg-zoom-readout" data-wg-zoom-readout>100%%</span>'
        '<button class="wg-button" type="button" data-wg-zoom-in aria-label="放大关系图">＋</button><button class="wg-button" type="button" data-wg-fit>适合窗口</button></div></section>'
        '<section class="wg-grid"><div class="wg-graph-panel"><div class="wg-panel-head"><div><p class="wg-panel-index">关系图 / 已验证核心数据</p><h3>分层关系拓扑</h3></div>'
        '<div class="wg-legend" aria-label="关系图例"><span><i></i>接续：实线青</span><span><i class="dependency"></i>依赖：虚线黄</span><span><i class="conflict"></i>冲突：复合红线</span></div></div>'
        '<div class="wg-frame"><div class="wg-viewport" data-wg-viewport tabindex="0" aria-label="可滚动任务关系画布"><div class="wg-canvas"><svg data-wg-svg role="group" aria-label="从左到右的分层任务关系图"></svg></div></div><div class="wg-empty" data-wg-empty hidden><b>没有匹配的关系事实</b></div>'
        '<aside class="wg-inspector" hidden aria-hidden="true" role="dialog" aria-modal="false" aria-label="任务关系技术详情" data-wg-inspector-shell><div class="wg-inspector-head"><span>技术详情 / 核心证据 · 只读</span><button class="wg-inspector-close" type="button" data-wg-inspector-close aria-label="关闭技术详情">×</button></div><div data-wg-inspector></div><div class="wg-readonly">不提供应用、撤销、关闭、删除、合并或远程执行</div></aside></div></div></section>'
        '<section class="wg-ledger" aria-labelledby="wg-ledger-title"><h3 id="wg-ledger-title">任务关系列表</h3><p class="wg-ledger-intro">按层级与链阅读；每条关系明确显示“从谁 → 到谁”，历史折叠与桌面保持一致。</p><div class="wg-ledger-list" data-wg-ledger></div></section>'
        '<section class="wg-comparisons" aria-labelledby="wg-comparison-title"><h3 id="wg-comparison-title">需要比较／证据待刷新</h3><p>黄色建议不属于冲突事实，不会画成红线。</p><div data-wg-comparisons></div></section>'
        '<p class="wg-sr" aria-live="polite" data-wg-live></p><script type="application/json" data-wg-payload>%s</script>'
        '</section></article>'
        % (html.escape(authority, quote=True), status, html.escape(display_status(status)), failure, series_html, payload)
    )


def inject_workstream_relation_graph(page: str, projection: Mapping[str, Any]) -> str:
    if 'id="workstream-relation-graph"' in page:
        raise ValueError("Workstream relation graph is already present")
    content_marker = '</main><aside class="toc" id="toc">'
    if content_marker not in page or "</style>" not in page or "</body>" not in page:
        raise ValueError("Observatory composition markers are missing")
    nav_candidates = [
        '<a class="nav-item" data-target="team-observatory"><span class="dot proposed"></span><span class="lbl">团队协作</span></a>',
        '<a class="nav-item" data-target="personal-observatory"><span class="dot state"></span><span class="lbl">个人工作台</span></a>',
        '<a class="nav-item" data-target="trends"><span class="dot proposed"></span><span class="lbl">🔭 路线与趋势</span></a>',
    ]
    marker = next((item for item in nav_candidates if item in page), None)
    if marker is None:
        raise ValueError("Observatory navigation marker is missing")
    nav = '<a class="nav-item" data-target="workstream-relation-graph"><span class="dot proposed"></span><span class="lbl">任务关系</span></a>'
    result = page.replace("</style>", WORKSTREAM_GRAPH_CSS + "</style>", 1)
    result = result.replace(marker, marker + nav, 1)
    marker_index = result.index(marker)
    group_index = result.rfind('<div class="nav-group">', 0, marker_index)
    if group_index >= 0:
        result = result[:group_index] + result[group_index:].replace('<div class="nav-group">', '<div class="nav-group expanded">', 1)
    result = result.replace(content_marker, render_workstream_relation_graph_panel(projection) + content_marker, 1)
    scripts = "<script>" + WORKSTREAM_GRAPH_JS + "</script>"
    return result.replace("</body>", scripts + "</body>", 1)


def write_projection_json(path: Path, projection: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


__all__ = [
    "PROJECTION_SCHEMA_VERSION", "PROVIDER_SCHEMA_VERSION", "PROVIDER_ID",
    "RelationGraphUnavailable", "build_relation_graph_projection",
    "project_core_relation_graph", "unavailable_relation_graph_projection",
    "build_readability_layout", "NODE_WIDTH", "NODE_HEIGHT",
    "render_workstream_relation_graph_panel", "inject_workstream_relation_graph",
    "write_projection_json",
]
