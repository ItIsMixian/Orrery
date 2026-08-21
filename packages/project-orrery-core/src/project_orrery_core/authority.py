"""Experimental deterministic Authority Meta Model evaluator.

This module is the Gate A Core-owned implementation checkpoint. It consumes
pre-normalized observations and does not parse Markdown, alter manifests, or
define a public compatibility contract.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


AUTHORITY_MODEL_VERSION = "amm-fixture-v1"
REQUIRED_INPUT_DIMENSIONS = (
    "authority_model_version",
    "repository_snapshot",
    "fact_scope",
    "evidence_visibility",
)
FACT_SCOPE_LEVELS = {
    "canonical": "authoritative",
    "candidate": "candidate",
    "worktree": "worktree",
    "local-only": "reported",
    "historical": "historical",
    "unknown": "unknown",
}
EVIDENCE_CAPABILITIES = {
    "revision-content": "supports-bytes-at-revision",
    "reproducible-executable-validation": "supports-tested-behavior",
    "tool-runtime-trace": "supports-observed-tool-event",
    "human-or-agent-assertion": "assertion-only",
    "derived-ai-summary": "derived-interpretation-only",
}
SCOPE_PROHIBITIONS = {
    "canonical": (),
    "candidate": ("canonical",),
    "worktree": ("committed", "canonical"),
    "local-only": ("source-code-content", "canonical"),
    "historical": ("current",),
    "unknown": ("canonical", "candidate", "worktree"),
}


class AuthorityEvaluationError(ValueError):
    """Raised when an input cannot be interpreted under the fixture model."""


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuthorityEvaluationError(f"{label} must be an object")
    return value


def evaluate_authority(
    conformance_input: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Evaluate normalized observations under the Candidate fixture model.

    The result is deterministic for identical inputs and observations. Unknown
    versions, scopes, evidence categories, and observation kinds fail closed.
    """

    inputs = _require_mapping(conformance_input, label="conformance input")
    if tuple(inputs) != REQUIRED_INPUT_DIMENSIONS:
        raise AuthorityEvaluationError(
            "conformance input must contain exactly: " + ", ".join(REQUIRED_INPUT_DIMENSIONS)
        )
    if inputs["authority_model_version"] != AUTHORITY_MODEL_VERSION:
        raise AuthorityEvaluationError(
            f"unsupported authority model version: {inputs['authority_model_version']!r}"
        )
    snapshot = inputs["repository_snapshot"]
    if not isinstance(snapshot, str) or not snapshot.strip():
        raise AuthorityEvaluationError("repository_snapshot must be a non-empty identifier")
    scope = inputs["fact_scope"]
    if scope not in FACT_SCOPE_LEVELS:
        raise AuthorityEvaluationError(f"unsupported fact scope: {scope!r}")
    visibility = inputs["evidence_visibility"]
    if not isinstance(visibility, list) or any(item not in EVIDENCE_CAPABILITIES for item in visibility):
        raise AuthorityEvaluationError("evidence_visibility contains an unsupported category")
    if len(set(visibility)) != len(visibility):
        raise AuthorityEvaluationError("evidence_visibility contains duplicates")
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)):
        raise AuthorityEvaluationError("observations must be a sequence of objects")

    claims: dict[str, Any] = {
        "scope": scope,
        "authority_level": FACT_SCOPE_LEVELS[scope],
    }
    relations: dict[str, dict[str, list[str]]] = {}
    coordinator_runtime: dict[str, Any] = {}
    must_not_infer = list(SCOPE_PROHIBITIONS[scope])
    visible_categories = set(visibility)
    decisions: list[Mapping[str, Any]] = []
    hidden_validation = False

    def prohibit(*values: str) -> None:
        for value in values:
            if value not in must_not_infer:
                must_not_infer.append(value)

    for raw_observation in observations:
        observation = _require_mapping(raw_observation, label="observation")
        kind = observation.get("kind")
        evidence_category = observation.get("evidence_category")
        if evidence_category is not None and evidence_category not in EVIDENCE_CAPABILITIES:
            raise AuthorityEvaluationError(
                f"observation {kind!r} uses unsupported evidence category {evidence_category!r}"
            )
        if evidence_category is not None and evidence_category not in visible_categories:
            if kind == "validation":
                hidden_validation = True
            continue

        if kind == "seed":
            claims["seed_present"] = bool(observation.get("present"))
        elif kind == "decision":
            decisions.append(observation)
            if not observation.get("id"):
                claims["decision_status"] = observation.get("status", "unknown")
        elif kind == "implementation":
            time = observation.get("time", "current")
            key = "historical_implementation_claim" if time == "historical" else "implementation_claim"
            claims[key] = observation.get("state", "unknown")
        elif kind == "validation":
            result = observation.get("result", "unknown")
            if (
                result in {"passed", "failed"}
                and evidence_category != "reproducible-executable-validation"
            ):
                claims["validation_assertion"] = result
                claims["validation_evidence"] = "unknown"
                prohibit("validated", "assertion-is-independent-validation")
            else:
                claims["validation_evidence"] = result
        elif kind == "design":
            claims["design_lifecycle"] = observation.get("lifecycle", "unknown")
        elif kind == "plan":
            claims["planned"] = bool(observation.get("planned"))
        elif kind == "state":
            claims["current"] = bool(observation.get("current"))
        elif kind == "snapshot":
            claims["role"] = "snapshot"
            claims["live_state"] = bool(observation.get("live_state"))
        elif kind == "evidence-capabilities":
            claims.update({category: EVIDENCE_CAPABILITIES[category] for category in visibility})
        elif kind == "ai-summary":
            claims["authority_level"] = "derived"
            claims.setdefault("implementation_claim", "unknown")
            prohibit("approved", "implemented", "validated")
        elif kind == "coordinator":
            coordinator_runtime.update(
                {key: observation[key] for key in ("owner", "lock") if key in observation}
            )
            prohibit("owner-is-scope", "lock-confers-authority")
        else:
            raise AuthorityEvaluationError(f"unsupported observation kind: {kind!r}")

    if hidden_validation and "validation_evidence" not in claims:
        claims["validation_evidence"] = "unknown"
        prohibit("validated")

    accepted_ids = [
        str(decision["id"])
        for decision in decisions
        if decision.get("status") == "accepted" and decision.get("id")
    ]
    superseded_ids: set[str] = set()
    has_supersede = False
    has_amend = False
    for decision in decisions:
        decision_id = decision.get("id")
        if not decision_id:
            continue
        relation: dict[str, list[str]] = {}
        for relation_name in ("supersedes", "amends"):
            targets = decision.get(relation_name, [])
            if targets:
                if not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
                    raise AuthorityEvaluationError(f"{relation_name} must be a list of decision ids")
                relation[relation_name] = list(targets)
                if relation_name == "supersedes":
                    has_supersede = True
                    superseded_ids.update(targets)
                else:
                    has_amend = True
        if relation:
            relations[str(decision_id)] = relation

    effective_ids = [decision_id for decision_id in accepted_ids if decision_id not in superseded_ids]
    if has_supersede and len(effective_ids) == 1:
        claims["effective_decision"] = effective_ids[0]
        prohibit(*(f"{decision_id}-is-current-effective" for decision_id in sorted(superseded_ids)))
    elif has_supersede and effective_ids:
        claims["effective_decisions"] = effective_ids
    if has_amend:
        claims["effective_decisions"] = effective_ids
        prohibit("amend-equals-supersede")

    if claims.get("decision_status") == "accepted":
        if claims.get("implementation_claim") in (None, "unknown", "absent"):
            prohibit("implemented")
        if claims.get("validation_evidence") in (None, "unknown", "absent", "failed"):
            prohibit("validated")
    if claims.get("validation_evidence") == "failed":
        prohibit("implementation-absent", "validated")
    if claims.get("historical_implementation_claim") == "present" and claims.get("implementation_claim") == "absent":
        prohibit("historical-is-current")
    if claims.get("design_lifecycle") == "draft":
        prohibit("approved-design", "implemented")
    if claims.get("planned") is True and claims.get("current") is False:
        prohibit("planned-is-current", "implemented")
    if claims.get("role") == "snapshot" and claims.get("live_state") is False:
        prohibit("current-state")
    if "human-or-agent-assertion" in claims:
        prohibit("assertion-is-independent-validation")
    if "derived-ai-summary" in claims:
        prohibit("summary-is-primary-evidence")

    return {
        "authority_model_version": AUTHORITY_MODEL_VERSION,
        "repository_snapshot": snapshot,
        "fact_scope": scope,
        "evidence_visibility": list(visibility),
        "claims": claims,
        "relations": relations,
        "coordinator_runtime": coordinator_runtime,
        "must_not_infer": must_not_infer,
    }
