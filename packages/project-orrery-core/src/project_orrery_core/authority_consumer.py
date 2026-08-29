"""Versioned managed Authority consumer selection and rollback contract.

This internal A3 boundary evaluates provider-neutral health observations.  It
does not collect repository content, render a page, mutate project files, or
select a release.  The normalized M2.1 observation bundle deliberately stays
outside this contract.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .authority import EVIDENCE_CAPABILITIES


MANAGED_CONSUMER_CONTRACT = "authority-managed-consumer-v1"
MANAGED_CONSUMER_SCHEMA_VERSION = 1
MANAGED_EVALUATOR_VERSION = "core-authority-evaluator-v1"
MANAGED_COLLECTOR_VERSION = "cli-authority-observations-v1"
MANAGED_PROJECTION_VERSION = "observatory-authority-projection-v1"
REQUESTABLE_SELECTIONS = (
    "legacy",
    "shadow",
    "candidate-projection",
    "enabled",
    "rollback",
)
MANAGED_COMPONENTS = ("collector", "evaluator", "projection")
COMPONENT_STATUSES = ("ready", "failed", "unavailable")
RENDER_STATUSES = ("complete", "partial", "failed", "unavailable")
UPGRADE_SCOPES = {
    "candidate-projection": {"canonical", "candidate", "worktree"},
    "enabled": {"canonical"},
}
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ManagedAuthorityConsumerError(ValueError):
    """Raised when an A3 observation is malformed rather than merely blocked."""


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManagedAuthorityConsumerError(f"{label} must be an object")
    return value


def _versions(value: object, label: str) -> dict[str, str]:
    mapping = _mapping(value, label)
    if set(mapping) != set(MANAGED_COMPONENTS):
        raise ManagedAuthorityConsumerError(
            f"{label} must contain exactly: {', '.join(MANAGED_COMPONENTS)}"
        )
    result = {component: mapping[component] for component in MANAGED_COMPONENTS}
    if not all(isinstance(item, str) and item for item in result.values()):
        raise ManagedAuthorityConsumerError(f"{label} values must be non-empty strings")
    return result


def _component_health(value: object) -> dict[str, str]:
    mapping = _mapping(value, "component_health")
    if set(mapping) != set(MANAGED_COMPONENTS):
        raise ManagedAuthorityConsumerError(
            "component_health must contain exactly: " + ", ".join(MANAGED_COMPONENTS)
        )
    result = {component: mapping[component] for component in MANAGED_COMPONENTS}
    if any(status not in COMPONENT_STATUSES for status in result.values()):
        raise ManagedAuthorityConsumerError(
            "component_health contains an unsupported status"
        )
    return result


def _hash_pair(value: object, label: str) -> dict[str, str | None]:
    mapping = _mapping(value, label)
    if set(mapping) != {"expected", "observed"}:
        raise ManagedAuthorityConsumerError(
            f"{label} must contain exactly expected and observed"
        )
    pair: dict[str, str | None] = {}
    for key in ("expected", "observed"):
        item = mapping[key]
        if item is not None and (not isinstance(item, str) or not HASH_RE.fullmatch(item)):
            raise ManagedAuthorityConsumerError(
                f"{label}.{key} must be null or a sha256 digest"
            )
        pair[key] = item
    return pair


def _safety(value: object) -> dict[str, bool]:
    required = (
        "unknown_preserved",
        "local_only_preserved",
        "ai_non_escalation",
        "coordinator_cannot_select",
        "partial_claims_exposed",
    )
    mapping = _mapping(value, "safety")
    if set(mapping) != set(required) or any(
        not isinstance(mapping[key], bool) for key in required
    ):
        raise ManagedAuthorityConsumerError(
            "safety must contain exactly the five boolean A3 invariants"
        )
    return {key: mapping[key] for key in required}


def _blocker(code: str, category: str, component: str, detail: str) -> dict[str, str]:
    return {
        "code": code,
        "category": category,
        "component": component,
        "detail": detail,
    }


def _plan(kind: str, selection: str, binding_hash: str) -> dict[str, Any]:
    if kind == "rollout":
        if selection == "legacy":
            steps = ["retain-legacy-consumer"]
        elif selection == "shadow":
            steps = [
                "collect-and-evaluate-without-claim-page",
                "record-hash-bound-comparison",
                "retain-legacy-consumer",
            ]
        elif selection == "candidate-projection":
            steps = [
                "retain-legacy-bytes",
                "stage-complete-candidate-projection",
                "verify-exact-binding-and-no-partial-claims",
                "publish-opt-in-projection-atomically",
                "retain-legacy-default",
            ]
        elif selection == "enabled":
            steps = [
                "retain-legacy-bytes",
                "stage-complete-managed-projection",
                "verify-exact-binding-and-no-partial-claims",
                "atomically-switch-only-after-complete-render",
                "restore-legacy-on-any-failure",
            ]
        else:
            steps = ["do-not-stage-managed-projection", "retain-legacy-consumer"]
    else:
        steps = [
            "discard-uncommitted-managed-output",
            "atomically-restore-retained-legacy-bytes",
            "verify-no-managed-claim-fragment-is-visible",
        ]
    body: dict[str, Any] = {
        "contract": MANAGED_CONSUMER_CONTRACT,
        "kind": kind,
        "selection": selection,
        "binding_hash": binding_hash,
        "steps": steps,
        "atomicity": "complete-page-or-legacy",
        "failure_consumer": "legacy",
        "writes_author_documents": False,
        "network_required": False,
        "modifies_release": False,
    }
    plan_hash = _canonical_hash(body)
    return {
        **body,
        "plan_hash": plan_hash,
        "plan_id": f"authority-{kind}-{plan_hash.removeprefix('sha256:')[:24]}",
    }


def evaluate_managed_authority_consumer(
    *,
    requested_selection: str,
    selection_authority: str,
    authority_model_version: int | None,
    evaluator_model_id: str | None,
    model_status: str,
    repository_snapshot: str,
    fact_scope: str,
    evidence_visibility: Sequence[str],
    expected_versions: Mapping[str, str],
    observed_versions: Mapping[str, str],
    component_health: Mapping[str, str],
    source_hashes: Mapping[str, str | None],
    reconciliation_hashes: Mapping[str, str | None],
    render_status: str,
    safety: Mapping[str, bool],
) -> dict[str, Any]:
    """Return a deterministic selection, readiness, rollout and rollback contract."""

    if requested_selection not in REQUESTABLE_SELECTIONS:
        raise ManagedAuthorityConsumerError(
            f"unsupported requested selection: {requested_selection!r}"
        )
    if not isinstance(selection_authority, str) or not selection_authority:
        raise ManagedAuthorityConsumerError("selection_authority must be a non-empty string")
    if authority_model_version is not None and (
        isinstance(authority_model_version, bool)
        or not isinstance(authority_model_version, int)
        or authority_model_version <= 0
    ):
        raise ManagedAuthorityConsumerError(
            "authority_model_version must be null or a positive integer"
        )
    if evaluator_model_id is not None and (
        not isinstance(evaluator_model_id, str) or not evaluator_model_id
    ):
        raise ManagedAuthorityConsumerError(
            "evaluator_model_id must be null or a non-empty string"
        )
    if not isinstance(repository_snapshot, str) or not repository_snapshot:
        raise ManagedAuthorityConsumerError(
            "repository_snapshot must be a non-empty string"
        )
    if fact_scope not in {
        "canonical",
        "candidate",
        "worktree",
        "local-only",
        "historical",
        "unknown",
    }:
        raise ManagedAuthorityConsumerError(f"unsupported fact scope: {fact_scope!r}")
    if not isinstance(evidence_visibility, Sequence) or isinstance(
        evidence_visibility, (str, bytes)
    ):
        raise ManagedAuthorityConsumerError("evidence_visibility must be a sequence")
    visibility = list(evidence_visibility)
    if (
        len(set(visibility)) != len(visibility)
        or any(item not in EVIDENCE_CAPABILITIES for item in visibility)
    ):
        raise ManagedAuthorityConsumerError(
            "evidence_visibility must contain unique supported categories"
        )
    expected = _versions(expected_versions, "expected_versions")
    observed = _versions(observed_versions, "observed_versions")
    health = _component_health(component_health)
    source = _hash_pair(source_hashes, "source_hashes")
    reconciliation = _hash_pair(reconciliation_hashes, "reconciliation_hashes")
    if render_status not in RENDER_STATUSES:
        raise ManagedAuthorityConsumerError(
            f"unsupported render status: {render_status!r}"
        )
    invariants = _safety(safety)

    blockers: list[dict[str, str]] = []
    allowed_authority = (
        (requested_selection == "legacy" and selection_authority == "system-default")
        or selection_authority == "maintainer-explicit"
        or (
            requested_selection == "rollback"
            and selection_authority == "runtime-failure"
        )
    )
    if not allowed_authority:
        blockers.append(
            _blocker(
                "selection-authority-forbidden",
                "unavailable",
                "selection",
                "only system default, explicit maintainer choice, or runtime rollback may select a consumer",
            )
        )
    if (
        model_status != "supported"
        or authority_model_version != 1
        or evaluator_model_id != "amm-fixture-v1"
    ):
        blockers.append(
            _blocker(
                "authority-model-unavailable",
                "unavailable",
                "authority-model",
                "the selected public model and exact evaluator model are not supported",
            )
        )
    allowed_scopes = UPGRADE_SCOPES.get(requested_selection)
    if allowed_scopes is not None and fact_scope not in allowed_scopes:
        blockers.append(
            _blocker(
                "fact-scope-not-enablable",
                "unavailable",
                "conformance-input",
                f"{fact_scope} cannot be upgraded to {requested_selection}",
            )
        )
    for component in MANAGED_COMPONENTS:
        if health[component] != "ready":
            blockers.append(
                _blocker(
                    f"{component}-unavailable",
                    "runtime-failure",
                    component,
                    f"component status is {health[component]}",
                )
            )
        if observed[component] != expected[component]:
            blockers.append(
                _blocker(
                    f"{component}-version-drift",
                    "runtime-failure",
                    component,
                    f"expected {expected[component]}, observed {observed[component]}",
                )
            )
    if source["expected"] is None or source["observed"] is None:
        blockers.append(
            _blocker(
                "source-hash-unavailable",
                "runtime-failure",
                "collector",
                "exact source-set hashes are required",
            )
        )
    elif source["expected"] != source["observed"]:
        blockers.append(
            _blocker(
                "source-drift",
                "runtime-failure",
                "collector",
                "observed source-set hash differs from the requested snapshot",
            )
        )
    if reconciliation["expected"] is None or reconciliation["observed"] is None:
        blockers.append(
            _blocker(
                "reconciliation-hash-unavailable",
                "runtime-failure",
                "projection",
                "exact reconciliation hashes are required",
            )
        )
    elif reconciliation["expected"] != reconciliation["observed"]:
        blockers.append(
            _blocker(
                "reconciliation-drift",
                "runtime-failure",
                "projection",
                "projected bundle differs from the collected bundle",
            )
        )
    if render_status != "complete":
        blockers.append(
            _blocker(
                "partial-render" if render_status == "partial" else "render-unavailable",
                "runtime-failure",
                "projection",
                f"render status is {render_status}",
            )
        )
    for key, code in (
        ("unknown_preserved", "unknown-escalation"),
        ("local_only_preserved", "local-only-escalation"),
        ("ai_non_escalation", "ai-escalation"),
        ("coordinator_cannot_select", "coordinator-selection-escalation"),
    ):
        if not invariants[key]:
            blockers.append(
                _blocker(
                    code,
                    "unavailable",
                    "authority-boundary",
                    f"required invariant {key} is not preserved",
                )
            )
    if invariants["partial_claims_exposed"]:
        blockers.append(
            _blocker(
                "partial-claims-exposed",
                "runtime-failure",
                "projection",
                "a partial managed claim page must never be committed",
            )
        )

    readiness = (
        "ready"
        if not blockers
        else "unavailable"
        if any(item["category"] == "unavailable" for item in blockers)
        else "blocked"
    )
    if requested_selection == "legacy":
        effective_selection = "legacy"
    elif requested_selection == "rollback":
        effective_selection = "rollback"
    elif not blockers:
        effective_selection = requested_selection
    elif readiness == "unavailable":
        effective_selection = "unavailable"
    else:
        effective_selection = "rollback"
    target_consumer = "managed-authority-projection" if effective_selection == "enabled" else "legacy"
    # A3 is an inspect/readiness contract, not an executor.  Until a later
    # maintainer-owned apply receipt exists, the actual active consumer stays
    # legacy even when the enabled rollout target is ready.
    active_consumer = "legacy"
    rollout_ready = effective_selection == "enabled" and not blockers

    binding = {
        "authority_model_version": authority_model_version,
        "evaluator_model_id": evaluator_model_id,
        "repository_snapshot": repository_snapshot,
        "fact_scope": fact_scope,
        "evidence_visibility": visibility,
        "versions": {"expected": expected, "observed": observed},
        "source_hashes": source,
        "reconciliation_hashes": reconciliation,
    }
    binding_hash = _canonical_hash(binding)
    rollout = _plan("rollout", effective_selection, binding_hash)
    rollback = _plan("rollback", effective_selection, binding_hash)
    body: dict[str, Any] = {
        "schema_version": MANAGED_CONSUMER_SCHEMA_VERSION,
        "contract_type": MANAGED_CONSUMER_CONTRACT,
        "selection": {
            "current": "legacy",
            "requested": requested_selection,
            "authority": selection_authority,
            "effective": effective_selection,
            "active_consumer": active_consumer,
            "target_consumer": target_consumer,
            "rollout_ready": rollout_ready,
            "switch_authorized": False,
            "maintainer_enable_decision": "pending",
            "default_selection": "legacy",
            "production_behavior_switched": False,
        },
        "readiness": {
            "status": readiness,
            "ready": not blockers,
            "blockers": blockers,
        },
        "binding": binding,
        "binding_hash": binding_hash,
        "component_health": health,
        "render_status": render_status,
        "safety": invariants,
        "rollout_plan": rollout,
        "rollback_plan": rollback,
        "guarantees": {
            "atomic_page_transition": True,
            "partial_claim_page_allowed": False,
            "fallback_consumer": "legacy",
            "writes_author_documents": False,
            "network_required": False,
            "modifies_release": False,
            "ai_may_select": False,
            "coordinator_may_select": False,
        },
    }
    return {**body, "contract_hash": _canonical_hash(body)}
