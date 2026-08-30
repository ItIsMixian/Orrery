"""Provider-neutral Authority Route Preflight and novelty/absence gate.

Core consumes normalized concept/source observations.  Repository Markdown,
Git, release manifests, and host hooks are collected by adapters outside this
module.  The receipt selects evidence and preserves claim dimensions; it never
creates the selected project facts.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


AUTHORITY_ROUTE_CONTRACT = "authority-route-preflight-v1"
AUTHORITY_ROUTE_SCHEMA_VERSION = 1
SUPPORTED_QUERY_CLASSES = {
    "existence",
    "implementation",
    "validation",
    "distribution",
    "release",
    "visibility",
    "novelty-absence",
    "general-fact",
}
CLAIM_AXES = (
    "semantic_decision",
    "implementation",
    "distribution_consumer",
    "public_default_release",
)
FACT_SCOPES = {"canonical", "candidate", "worktree", "local-only", "historical", "unknown"}
SOURCE_ROLES = {
    "index", "state", "adr", "design", "implementation", "validation",
    "distribution", "consumer", "release", "template", "readme", "agent-assertion",
}
LOWER_AUTHORITY_ROLES = {"template", "readme", "agent-assertion"}
AXIS_ROLES = {
    "semantic_decision": {"index", "state", "adr", "design"},
    "implementation": {"state", "implementation", "validation"},
    "distribution_consumer": {"state", "distribution", "consumer"},
    "public_default_release": {"state", "release"},
}
_CONCEPT_ID = re.compile(r"^[a-z][a-z0-9-]+$")
_SOURCE_ID = re.compile(r"^[a-z][a-z0-9_.:-]+$")


class AuthorityRouteError(ValueError):
    """Raised for malformed normalized route inputs."""


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuthorityRouteError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise AuthorityRouteError(f"{label} must be an array")
    return list(value)


def _normalize_text(value: str) -> str:
    return " ".join(re.sub(r"[^0-9a-z\u3400-\u9fff]+", " ", value.lower()).split())


def _bigrams(value: str) -> set[str]:
    compact = value.replace(" ", "")
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[index : index + 2] for index in range(len(compact) - 1)}


def _alias_score(query: str, alias: str) -> float:
    normalized_query = _normalize_text(query)
    normalized_alias = _normalize_text(alias)
    if not normalized_alias:
        return 0.0
    if normalized_alias in normalized_query:
        return 2.0 + min(len(normalized_alias), 160) / 160
    query_tokens = set(normalized_query.split())
    alias_tokens = set(normalized_alias.split())
    token_score = len(query_tokens & alias_tokens) / len(alias_tokens) if alias_tokens else 0.0
    alias_bigrams = _bigrams(normalized_alias)
    query_bigrams = _bigrams(normalized_query)
    bigram_score = len(alias_bigrams & query_bigrams) / len(alias_bigrams) if alias_bigrams else 0.0
    return max(token_score, bigram_score)


def classify_query(query: str) -> str:
    normalized = _normalize_text(query)
    patterns = (
        ("novelty-absence", ("new layer", "not exist", "does not exist", "尚未建立", "不存在", "全新的", "新层")),
        ("visibility", ("看不到", "为什么用户", "why users cannot see", "why skill", "where is", "没有出现在", "delivered")),
        ("release", ("released", "release", "public", "default", "发布", "公开", "默认")),
        ("distribution", ("distributed", "consumer wiring", "skill", "adapter", "分发", "消费接线", "用户入口")),
        ("validation", ("validated", "verified", "evidence", "验证", "证据")),
        ("implementation", ("implemented", "implementation", "代码", "实现")),
        ("existence", ("exists", "existence", "是否存在", "有没有", "已建立")),
    )
    for query_class, aliases in patterns:
        if any(_normalize_text(alias) in normalized for alias in aliases):
            return query_class
    return "general-fact"


def _validate_registry(registry: object) -> dict[str, Any]:
    value = _mapping(registry, "registry")
    required = {"schema_version", "registry_id", "registry_version", "index_source", "concepts"}
    if set(value) != required:
        raise AuthorityRouteError("registry fields do not match authority-route-registry-v1")
    if value["schema_version"] != 1 or value["registry_version"] != 1:
        raise AuthorityRouteError("unsupported authority route registry schema/version")
    for key in ("registry_id", "index_source"):
        if not isinstance(value[key], str) or not value[key]:
            raise AuthorityRouteError(f"registry.{key} must be a non-empty string")
    concepts: list[dict[str, Any]] = []
    concept_ids: set[str] = set()
    source_ids: set[str] = set()
    for index, raw_concept in enumerate(_sequence(value["concepts"], "registry.concepts")):
        label = f"registry.concepts[{index}]"
        concept = _mapping(raw_concept, label)
        if set(concept) != {"concept_id", "subsystem_id", "aliases", "sources"}:
            raise AuthorityRouteError(f"{label} fields are invalid")
        concept_id = concept["concept_id"]
        if not isinstance(concept_id, str) or not _CONCEPT_ID.fullmatch(concept_id):
            raise AuthorityRouteError(f"{label}.concept_id is invalid")
        if concept_id in concept_ids:
            raise AuthorityRouteError("registry concept IDs must be unique")
        concept_ids.add(concept_id)
        if not isinstance(concept["subsystem_id"], str) or not concept["subsystem_id"]:
            raise AuthorityRouteError(f"{label}.subsystem_id must be a non-empty string")
        aliases = _sequence(concept["aliases"], f"{label}.aliases")
        if len(aliases) < 2 or any(not isinstance(item, str) or not item.strip() for item in aliases):
            raise AuthorityRouteError(f"{label}.aliases must contain at least two strings")
        sources: list[dict[str, Any]] = []
        for source_index, raw_source in enumerate(_sequence(concept["sources"], f"{label}.sources")):
            source_label = f"{label}.sources[{source_index}]"
            source = _mapping(raw_source, source_label)
            required_source = {"source_id", "path", "role", "authority_rank"}
            optional_source = {"lower_authority", "required_for_axes"}
            if not required_source.issubset(source) or set(source) - required_source - optional_source:
                raise AuthorityRouteError(f"{source_label} fields are invalid")
            source_id = source["source_id"]
            if not isinstance(source_id, str) or not _SOURCE_ID.fullmatch(source_id):
                raise AuthorityRouteError(f"{source_label}.source_id is invalid")
            if source_id in source_ids:
                raise AuthorityRouteError("registry source IDs must be globally unique")
            source_ids.add(source_id)
            if not isinstance(source["path"], str) or not source["path"]:
                raise AuthorityRouteError(f"{source_label}.path must be a non-empty string")
            if source["role"] not in SOURCE_ROLES:
                raise AuthorityRouteError(f"{source_label}.role is unsupported")
            rank = source["authority_rank"]
            if isinstance(rank, bool) or not isinstance(rank, int) or rank < 0:
                raise AuthorityRouteError(f"{source_label}.authority_rank must be a non-negative integer")
            required_for_axes = _sequence(
                source.get("required_for_axes", []),
                f"{source_label}.required_for_axes",
            )
            if any(axis not in CLAIM_AXES for axis in required_for_axes):
                raise AuthorityRouteError(f"{source_label}.required_for_axes is invalid")
            sources.append({
                "source_id": source_id,
                "path": source["path"],
                "role": source["role"],
                "authority_rank": rank,
                "lower_authority": bool(source.get("lower_authority", source["role"] in LOWER_AUTHORITY_ROLES)),
                "required_for_axes": list(dict.fromkeys(required_for_axes)),
                "concept_id": concept_id,
            })
        if not sources:
            raise AuthorityRouteError(f"{label}.sources must not be empty")
        concepts.append({
            "concept_id": concept_id,
            "subsystem_id": concept["subsystem_id"],
            "aliases": list(dict.fromkeys(str(item) for item in aliases)),
            "sources": sources,
        })
    if not concepts:
        raise AuthorityRouteError("registry must contain at least one concept")
    return {
        "schema_version": 1,
        "registry_id": value["registry_id"],
        "registry_version": 1,
        "index_source": value["index_source"],
        "concepts": concepts,
    }


def _validate_observations(observations: object, valid_source_ids: set[str]) -> dict[str, dict[str, Any]]:
    value = _mapping(observations, "observations")
    unknown = set(value) - valid_source_ids
    if unknown:
        raise AuthorityRouteError(f"observations contain unknown source IDs: {sorted(unknown)}")
    result: dict[str, dict[str, Any]] = {}
    for source_id, raw_observation in value.items():
        observation = _mapping(raw_observation, f"observations.{source_id}")
        allowed = {"exists", "link_valid", "current", "claims", "assertion_kind"}
        if set(observation) - allowed:
            raise AuthorityRouteError(f"observations.{source_id} has unknown fields")
        for key in ("exists", "link_valid", "current"):
            if key not in observation or not isinstance(observation[key], bool):
                raise AuthorityRouteError(f"observations.{source_id}.{key} must be boolean")
        claims_raw = _mapping(observation.get("claims", {}), f"observations.{source_id}.claims")
        if set(claims_raw) - set(CLAIM_AXES):
            raise AuthorityRouteError(f"observations.{source_id}.claims has unknown axes")
        claims: dict[str, dict[str, Any]] = {}
        for axis, raw_claim in claims_raw.items():
            claim = _mapping(raw_claim, f"observations.{source_id}.claims.{axis}")
            allowed_claim = {
                "status", "fact_scope", "reason_codes", "negative_evidence", "validation_status",
                "public_status", "default_status", "release_status",
            }
            if not {"status", "fact_scope"}.issubset(claim) or set(claim) - allowed_claim:
                raise AuthorityRouteError(f"observations.{source_id}.claims.{axis} fields are invalid")
            if claim["status"] not in {"present", "absent", "unknown"}:
                raise AuthorityRouteError(f"observations.{source_id}.claims.{axis}.status is invalid")
            if claim["fact_scope"] not in FACT_SCOPES:
                raise AuthorityRouteError(f"observations.{source_id}.claims.{axis}.fact_scope is invalid")
            reasons = _sequence(claim.get("reason_codes", []), f"observations.{source_id}.claims.{axis}.reason_codes")
            if any(not isinstance(item, str) or not item for item in reasons):
                raise AuthorityRouteError(f"observations.{source_id}.claims.{axis}.reason_codes is invalid")
            normalized = {
                "status": claim["status"],
                "fact_scope": claim["fact_scope"],
                "reason_codes": list(dict.fromkeys(reasons)),
                "negative_evidence": bool(claim.get("negative_evidence", False)),
            }
            for key in ("validation_status", "public_status", "default_status", "release_status"):
                if key in claim:
                    if claim[key] not in {"present", "absent", "unknown"}:
                        raise AuthorityRouteError(f"observations.{source_id}.claims.{axis}.{key} is invalid")
                    normalized[key] = claim[key]
            claims[axis] = normalized
        assertion_kind = observation.get("assertion_kind")
        if assertion_kind is not None and assertion_kind not in {"mechanical", "human", "agent", "derived"}:
            raise AuthorityRouteError(f"observations.{source_id}.assertion_kind is invalid")
        result[source_id] = {
            "exists": observation["exists"],
            "link_valid": observation["link_valid"],
            "current": observation["current"],
            "claims": claims,
            "assertion_kind": assertion_kind or "mechanical",
        }
    return result


def _selected_concepts(query: str, concepts: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[tuple[float, Mapping[str, Any]]] = []
    for concept in concepts:
        score = max((_alias_score(query, alias) for alias in concept["aliases"]), default=0.0)
        scored.append((score, concept))
    maximum = max((score for score, _concept in scored), default=0.0)
    if maximum < 0.44:
        return [], [{"concept_id": concept["concept_id"], "score": round(score, 6)} for score, concept in scored]
    threshold = max(0.44, maximum * 0.82)
    selected = [
        {"concept_id": concept["concept_id"], "subsystem_id": concept["subsystem_id"], "score": round(score, 6)}
        for score, concept in sorted(scored, key=lambda item: (-item[0], item[1]["concept_id"]))
        if score >= threshold
    ][:4]
    rejected = [
        {"concept_id": concept["concept_id"], "score": round(score, 6)}
        for score, concept in sorted(scored, key=lambda item: (-item[0], item[1]["concept_id"]))
        if concept["concept_id"] not in {item["concept_id"] for item in selected}
    ]
    return selected, rejected


def _needed_roles(query_class: str) -> set[str]:
    # Lower-authority material is deliberately collected so the receipt can
    # show why it was excluded instead of silently stopping at a template,
    # README, or Agent assertion.
    baseline = {
        "index", "state", "adr", "design", "template", "readme",
        "agent-assertion",
    }
    # Every fact judgment produces all four axes.  Query class controls the
    # minimal displayed selection, not which normalized observations Core
    # evaluates.
    return baseline | {"implementation", "validation", "distribution", "consumer", "release"}


def _receipt_roles(query_class: str) -> set[str]:
    roles = {"state", "adr"}
    if query_class in {"implementation", "validation", "distribution", "release", "visibility"}:
        roles.add("implementation")
    if query_class in {"validation", "visibility"}:
        roles.add("validation")
    if query_class in {"distribution", "release", "visibility"}:
        roles.update({"distribution", "consumer"})
    if query_class in {"release", "visibility"}:
        roles.add("release")
    return roles


def _minimal_selected_sources(
    sources: Sequence[Mapping[str, Any]], query_class: str
) -> list[dict[str, Any]]:
    wanted = _receipt_roles(query_class)
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        role = source["role"]
        if role not in wanted:
            continue
        family = "distribution" if role in {"distribution", "consumer"} else role
        key = (source["concept_id"], family)
        required = bool(source.get("required_for_axes"))
        if key in seen and not required:
            continue
        seen.add(key)
        selected.append({
            "source_id": source["source_id"],
            "path": source["path"],
            "role": role,
            "authority_rank": source["authority_rank"],
            "concept_id": source["concept_id"],
        })
    return selected


def _unknown_claim(*reason_codes: str) -> dict[str, Any]:
    return {
        "status": "unknown",
        "reason_codes": list(dict.fromkeys(reason_codes or ("insufficient-governing-evidence",))),
        "source_ids": [],
        "fact_scope": "unknown",
    }


def _aggregate_axis(
    axis: str,
    sources: Sequence[Mapping[str, Any]],
    observations: Mapping[str, Mapping[str, Any]],
    unresolved: Sequence[str],
) -> dict[str, Any]:
    candidates: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for source in sources:
        if source["role"] not in AXIS_ROLES[axis]:
            continue
        observation = observations.get(source["source_id"])
        if not observation or not observation["exists"] or not observation["link_valid"] or not observation["current"]:
            continue
        claim = observation["claims"].get(axis)
        if claim is not None:
            candidates.append((source, claim))
    if axis == "semantic_decision" and not candidates:
        governing = [
            source for source in sources
            if source["role"] in {"state", "adr", "design"}
            and (observation := observations.get(source["source_id"]))
            and observation["exists"] and observation["link_valid"] and observation["current"]
            and observation["assertion_kind"] not in {"agent", "derived"}
        ]
        if governing:
            scopes = {
                claim["fact_scope"]
                for source in governing
                for claim in observations[source["source_id"]]["claims"].values()
                if claim.get("fact_scope") in FACT_SCOPES
            }
            return {
                "status": "present",
                "reason_codes": ["indexed-governing-source-present"],
                "source_ids": [source["source_id"] for source in governing],
                "fact_scope": scopes.pop() if len(scopes) == 1 else "unknown",
            }
    if not candidates:
        return _unknown_claim("no-current-authoritative-observation")
    statuses = {claim["status"] for _source, claim in candidates if claim["status"] != "unknown"}
    sources_used = [source["source_id"] for source, _claim in candidates]
    reasons = list(dict.fromkeys(
        reason for _source, claim in candidates for reason in claim.get("reason_codes", [])
    ))
    scopes = {claim["fact_scope"] for _source, claim in candidates}
    fact_scope = scopes.pop() if len(scopes) == 1 else "unknown"
    if unresolved:
        status = "unknown"
        reasons.append("required-authority-observation-unresolved")
    elif len(statuses) > 1:
        status = "unknown"
        reasons.append("conflicting-authority-observations")
    elif statuses == {"present"}:
        status = "present"
    elif statuses == {"absent"}:
        complete_negative = all(claim.get("negative_evidence") is True for _source, claim in candidates)
        if complete_negative and not unresolved:
            status = "absent"
        else:
            status = "unknown"
            reasons.append("absence-evidence-incomplete")
    else:
        status = "unknown"
        reasons.append("authoritative-observation-unknown")
    result: dict[str, Any] = {
        "status": status,
        "reason_codes": list(dict.fromkeys(reasons or ["authoritative-observation-selected"])),
        "source_ids": sources_used,
        "fact_scope": fact_scope,
    }
    extras = (
        ("validation_status",)
        if axis == "implementation"
        else ("public_status", "default_status", "release_status")
        if axis == "public_default_release"
        else ()
    )
    for key in extras:
        values = {claim.get(key, "unknown") for _source, claim in candidates}
        known_values = values - {"unknown"}
        # A source that does not judge a sub-dimension must not erase a
        # current authoritative observation that does.  Conflicting known
        # values still fail closed to Unknown.
        result[key] = known_values.pop() if len(known_values) == 1 else "unknown"
    return result


def evaluate_authority_route(
    *,
    query: str,
    registry: Mapping[str, Any],
    observations: Mapping[str, Any],
    query_class: str | None = None,
) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise AuthorityRouteError("query must contain 1..1000 characters")
    normalized_registry = _validate_registry(registry)
    sources_by_id = {
        source["source_id"]: source
        for concept in normalized_registry["concepts"]
        for source in concept["sources"]
    }
    normalized_observations = _validate_observations(observations, set(sources_by_id))
    selected_class = query_class or classify_query(query)
    if selected_class not in SUPPORTED_QUERY_CLASSES:
        raise AuthorityRouteError(f"unsupported query class: {selected_class!r}")
    selected_concepts, rejected_concepts = _selected_concepts(query, normalized_registry["concepts"])
    selected_ids = {item["concept_id"] for item in selected_concepts}
    candidate_sources = [
        source
        for concept in normalized_registry["concepts"]
        if concept["concept_id"] in selected_ids
        for source in concept["sources"]
        if source["role"] in _needed_roles(selected_class)
    ]
    candidate_sources.sort(key=lambda item: (item["authority_rank"], item["source_id"]))
    available_sources: list[dict[str, Any]] = []
    excluded_sources: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for source in candidate_sources:
        observation = normalized_observations.get(source["source_id"])
        if source["lower_authority"] or source["role"] in LOWER_AUTHORITY_ROLES:
            excluded_sources.append({
                "source_id": source["source_id"], "path": source["path"], "role": source["role"],
                "reason": "lower-authority-source-cannot-establish-project-wide-claim",
            })
            continue
        if observation is None:
            unresolved.append(f"{source['source_id']}:observation-missing")
            continue
        if not observation["exists"]:
            unresolved.append(f"{source['source_id']}:source-missing")
            continue
        if not observation["link_valid"]:
            unresolved.append(f"{source['source_id']}:authority-link-broken")
            continue
        if not observation["current"]:
            unresolved.append(f"{source['source_id']}:source-stale")
            continue
        if observation["assertion_kind"] in {"agent", "derived"}:
            excluded_sources.append({
                "source_id": source["source_id"], "path": source["path"], "role": source["role"],
                "reason": "assertion-or-derived-view-is-not-governing-evidence",
            })
            continue
        available_sources.append(source)
    selected_sources = _minimal_selected_sources(available_sources, selected_class)
    claims = {}
    for axis in CLAIM_AXES:
        axis_source_ids = {
            source["source_id"] for source in candidate_sources
            if source["role"] in AXIS_ROLES[axis]
        }
        axis_unresolved = [
            target for target in unresolved
            if any(
                target.startswith(source["source_id"] + ":")
                for source in candidate_sources
                if source["source_id"] in axis_source_ids
                and axis in source.get("required_for_axes", [])
            )
        ]
        claims[axis] = _aggregate_axis(
            axis, candidate_sources, normalized_observations, axis_unresolved
        )
    if not selected_concepts:
        claims = {axis: _unknown_claim("concept-unindexed-or-ambiguous") for axis in CLAIM_AXES}
        unresolved.append("concept-registry:no-confident-match")
    negative_complete = bool(selected_concepts) and not unresolved and any(
        source["role"] in {"state", "adr"} for source in selected_sources
    )
    semantic_status = claims["semantic_decision"]["status"]
    if semantic_status == "present":
        gate_status = "rejected"
        gate_reason = "indexed-governing-source-exists"
    elif semantic_status == "absent" and negative_complete:
        gate_status = "allowed"
        gate_reason = "bounded-authoritative-search-supports-absence"
    else:
        gate_status = "unknown"
        gate_reason = "negative-evidence-incomplete"
    body: dict[str, Any] = {
        "schema_version": AUTHORITY_ROUTE_SCHEMA_VERSION,
        "contract_type": AUTHORITY_ROUTE_CONTRACT,
        "registry": {
            "registry_id": normalized_registry["registry_id"],
            "registry_version": normalized_registry["registry_version"],
            "index_source": normalized_registry["index_source"],
        },
        "query": {
            "query_class": selected_class,
            "normalized": _normalize_text(query),
            "raw_length": len(query),
        },
        "selection": {
            "concept_ids": [item["concept_id"] for item in selected_concepts],
            "subsystem_ids": list(dict.fromkeys(item["subsystem_id"] for item in selected_concepts)),
            "fan_out": len(selected_concepts) > 1,
            "ambiguous": not selected_concepts or len(selected_concepts) > 1,
            "scores": selected_concepts,
            "rejected_candidates": rejected_concepts,
        },
        "selected_governing_sources": selected_sources,
        "excluded_lower_authority_sources": excluded_sources,
        "claim_dimensions": claims,
        "negative_evidence": {
            "complete": negative_complete,
            "registry_version": normalized_registry["registry_version"],
            "concept_ids": [item["concept_id"] for item in selected_concepts],
            "searched_source_ids": [source["source_id"] for source in candidate_sources],
            "unresolved_targets": list(dict.fromkeys(unresolved)),
        },
        "novelty_absence_gate": {
            "status": gate_status,
            "reason": gate_reason,
            "absence_claim_allowed": gate_status == "allowed",
        },
        "guarantees": {
            "deterministic_owner": "project-orrery-core",
            "writes_target_project": False,
            "creates_or_promotes_authority": False,
            "changes_release_status": False,
            "skill_enforcement": "advisory-without-host-hook",
        },
    }
    return {**body, "receipt_hash": _canonical_hash(body)}


def unavailable_route_receipt(query: str, reason: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": AUTHORITY_ROUTE_SCHEMA_VERSION,
        "contract_type": AUTHORITY_ROUTE_CONTRACT,
        "registry": {"registry_id": "unavailable", "registry_version": 0, "index_source": "unavailable"},
        "query": {"query_class": classify_query(query), "normalized": _normalize_text(query), "raw_length": len(query)},
        "selection": {"concept_ids": [], "subsystem_ids": [], "fan_out": False, "ambiguous": True, "scores": [], "rejected_candidates": []},
        "selected_governing_sources": [],
        "excluded_lower_authority_sources": [],
        "claim_dimensions": {axis: _unknown_claim("route-preflight-unavailable") for axis in CLAIM_AXES},
        "negative_evidence": {"complete": False, "registry_version": 0, "concept_ids": [], "searched_source_ids": [], "unresolved_targets": [reason]},
        "novelty_absence_gate": {"status": "unknown", "reason": "negative-evidence-incomplete", "absence_claim_allowed": False},
        "guarantees": {
            "deterministic_owner": "project-orrery-core",
            "writes_target_project": False,
            "creates_or_promotes_authority": False,
            "changes_release_status": False,
            "skill_enforcement": "advisory-without-host-hook",
        },
    }
    return {**body, "receipt_hash": _canonical_hash(body)}


__all__ = [
    "AUTHORITY_ROUTE_CONTRACT",
    "AUTHORITY_ROUTE_SCHEMA_VERSION",
    "AuthorityRouteError",
    "CLAIM_AXES",
    "classify_query",
    "evaluate_authority_route",
    "unavailable_route_receipt",
]
