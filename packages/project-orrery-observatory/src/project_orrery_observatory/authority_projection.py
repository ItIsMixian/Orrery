"""Internal M2.2 projection of a pre-built M2.1 Authority bundle.

The Observatory package deliberately does not import ``project_orrery_cli``.
The CLI already depends on Observatory, so the managed integration layer owns
collection and passes an immutable-by-convention bundle into this module.
This module validates and projects Core-owned claims; it never parses Markdown
or infers claims from legacy viewer prose.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any


PROJECTION_SCHEMA = "observatory-authority-projection-v1"
M2_1_CONTRACT_VERSION = "cli-authority-observations-v1"
ALLOWED_ROLES = (
    "seed",
    "adr",
    "design",
    "plan",
    "state",
    "validation",
    "snapshot",
)
SOURCE_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class AuthorityProjectionError(ValueError):
    """Raised when a Candidate bundle cannot be projected safely."""


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _safe_source(source: object) -> str:
    if not isinstance(source, str) or not source:
        raise AuthorityProjectionError("document source must be a non-empty string")
    if "\\" in source:
        raise AuthorityProjectionError(f"unsafe repository source: {source!r}")
    path = PurePosixPath(source)
    if path.is_absolute() or ".." in path.parts or path.parts[0] != "docs":
        raise AuthorityProjectionError(f"unsafe repository source: {source!r}")
    return source


def source_anchor(role: str, source: str, subject: str) -> str:
    """Return an existing legacy-reader anchor for an authored source."""

    if role == "adr":
        number = subject.removeprefix("ADR-").lower()
        if not re.fullmatch(r"\d{4}(?:\.\d+)?", number):
            raise AuthorityProjectionError(f"invalid ADR subject: {subject!r}")
        return "#adr-" + number
    name = PurePosixPath(source).name
    if role == "state":
        return "#state-" + PurePosixPath(name).stem
    if role == "snapshot":
        return "#snap-" + name
    if role == "seed":
        return "#lib-principles"
    return "#lib-" + PurePosixPath(name).stem


def _validate_conformance_input(
    bundle: Mapping[str, Any],
    *,
    authority_model_version: str,
    repository_snapshot: str,
    fact_scope: str,
    evidence_visibility: Sequence[str],
) -> dict[str, Any]:
    actual = bundle.get("conformance_input")
    if not isinstance(actual, Mapping):
        raise AuthorityProjectionError("M2.1 bundle has no conformance input")
    expected = {
        "authority_model_version": authority_model_version,
        "repository_snapshot": repository_snapshot,
        "fact_scope": fact_scope,
        "evidence_visibility": list(evidence_visibility),
    }
    normalized = {
        "authority_model_version": actual.get("authority_model_version"),
        "repository_snapshot": actual.get("repository_snapshot"),
        "fact_scope": actual.get("fact_scope"),
        "evidence_visibility": actual.get("evidence_visibility"),
    }
    if normalized != expected:
        raise AuthorityProjectionError(
            "M2.1 bundle conformance input does not match the Observatory request"
        )
    return expected


def _project_document(document: Mapping[str, Any]) -> dict[str, Any]:
    role = document.get("role")
    if role not in ALLOWED_ROLES:
        raise AuthorityProjectionError(f"unsupported Authority role: {role!r}")
    source = _safe_source(document.get("source"))
    source_hash = document.get("source_sha256")
    if not isinstance(source_hash, str) or not SOURCE_HASH_RE.fullmatch(source_hash):
        raise AuthorityProjectionError(f"invalid source hash for {source}")
    subject = document.get("subject")
    if not isinstance(subject, str) or not subject:
        raise AuthorityProjectionError(f"invalid subject for {source}")
    claims = document.get("claims")
    relations = document.get("relations")
    must_not_infer = document.get("must_not_infer")
    evidence = document.get("evidence_provenance")
    if not isinstance(claims, Mapping) or not isinstance(relations, Mapping):
        raise AuthorityProjectionError(f"missing Core claims/relations for {source}")
    if not isinstance(must_not_infer, list) or not all(
        isinstance(item, str) for item in must_not_infer
    ):
        raise AuthorityProjectionError(f"invalid must_not_infer for {source}")
    if not isinstance(evidence, list) or not all(
        isinstance(item, Mapping) for item in evidence
    ):
        raise AuthorityProjectionError(f"invalid evidence provenance for {source}")
    for item in evidence:
        if item.get("source") != source or item.get("source_sha256") != source_hash:
            raise AuthorityProjectionError(f"evidence/source mismatch for {source}")

    return {
        "role": role,
        "subject": subject,
        "source": source,
        "source_sha256": source_hash,
        "source_href": source_anchor(str(role), source, subject),
        "claims": dict(claims),
        "relations": dict(relations),
        "must_not_infer": list(must_not_infer),
        "evidence_provenance": [dict(item) for item in evidence],
    }


def build_authority_projection(
    bundle: Mapping[str, Any],
    *,
    authority_model_version: str,
    repository_snapshot: str,
    fact_scope: str,
    evidence_visibility: Sequence[str],
) -> dict[str, Any]:
    """Validate and project one exact M2.1 bundle.

    Collection is intentionally a caller responsibility.  A mismatch in any
    conformance input, document provenance or decision graph fails closed.
    """

    if bundle.get("contract_version") != M2_1_CONTRACT_VERSION:
        raise AuthorityProjectionError("unsupported M2.1 Authority bundle")
    if bundle.get("production_behavior_switched") is not False:
        raise AuthorityProjectionError("bundle is not a Candidate shadow contract")

    conformance_input = _validate_conformance_input(
        bundle,
        authority_model_version=authority_model_version,
        repository_snapshot=repository_snapshot,
        fact_scope=fact_scope,
        evidence_visibility=evidence_visibility,
    )
    documents = bundle.get("documents")
    if not isinstance(documents, list):
        raise AuthorityProjectionError("M2.1 bundle documents are unavailable")
    projected = [_project_document(document) for document in documents]
    sources = [document["source"] for document in projected]
    if len(sources) != len(set(sources)):
        raise AuthorityProjectionError("duplicate Authority source in M2.1 bundle")
    projected.sort(
        key=lambda document: (ALLOWED_ROLES.index(document["role"]), document["source"])
    )

    decision_graph = bundle.get("decision_graph")
    if not isinstance(decision_graph, Mapping):
        raise AuthorityProjectionError("M2.1 decision graph is unavailable")
    graph_status = decision_graph.get("status")
    if graph_status not in {"evaluated", "unknown"}:
        raise AuthorityProjectionError("invalid M2.1 decision graph status")
    graph_result = decision_graph.get("result")
    if graph_status == "evaluated":
        if not isinstance(graph_result, Mapping):
            raise AuthorityProjectionError(
                "evaluated decision graph has no Core result"
            )
        if {
            "authority_model_version": graph_result.get("authority_model_version"),
            "repository_snapshot": graph_result.get("repository_snapshot"),
            "fact_scope": graph_result.get("fact_scope"),
            "evidence_visibility": graph_result.get("evidence_visibility"),
        } != conformance_input:
            raise AuthorityProjectionError("decision graph conformance input drift")
        graph_claims = graph_result.get("claims", {})
        graph_relations = graph_result.get("relations", {})
        if not isinstance(graph_claims, Mapping) or not isinstance(
            graph_relations, Mapping
        ):
            raise AuthorityProjectionError("invalid Core decision graph output")
        raw_effective = graph_claims.get("effective_decisions", [])
        if not isinstance(raw_effective, list) or not all(
            isinstance(item, str) for item in raw_effective
        ):
            raise AuthorityProjectionError("invalid effective decision claims")
        effective_decisions: list[str] | None = list(raw_effective)
        relations: dict[str, Any] | None = dict(graph_relations)
        raw_graph_limits = graph_result.get("must_not_infer", [])
        if not isinstance(raw_graph_limits, list) or not all(
            isinstance(item, str) for item in raw_graph_limits
        ):
            raise AuthorityProjectionError("invalid decision graph limits")
        graph_must_not_infer = list(raw_graph_limits)
    else:
        effective_decisions = None
        relations = None
        graph_must_not_infer = ["effective-decision"]

    unresolved = bundle.get("unresolved_relations")
    if not isinstance(unresolved, list) or not all(
        isinstance(item, Mapping) for item in unresolved
    ):
        raise AuthorityProjectionError("invalid unresolved relation list")
    by_role = {
        role: [document for document in projected if document["role"] == role]
        for role in ALLOWED_ROLES
    }
    digest = _canonical_sha256(bundle)
    return {
        "projection_schema": PROJECTION_SCHEMA,
        "status": "ready",
        "mode": "candidate-opt-in",
        "authoritative_source": "core-owned-semantics-via-m2.1-bundle",
        "creates_project_facts": False,
        "production_behavior_switched": False,
        "conformance_input": conformance_input,
        "reconciliation": {
            "status": "match",
            "source_contract": M2_1_CONTRACT_VERSION,
            "bundle_sha256": digest,
        },
        "decision_graph": {
            "status": graph_status,
            "effective_decisions": effective_decisions,
            "relations": relations,
            "unresolved_relations": [dict(item) for item in unresolved],
            "must_not_infer": graph_must_not_infer,
        },
        "roles": by_role,
        "role_counts": {role: len(items) for role, items in by_role.items()},
    }


def unavailable_projection(
    *,
    authority_model_version: object,
    fact_scope: object,
    error: Exception,
) -> dict[str, Any]:
    """Return a bounded failure projection without claims or source payloads."""

    return {
        "projection_schema": PROJECTION_SCHEMA,
        "status": "unavailable",
        "mode": "candidate-opt-in",
        "creates_project_facts": False,
        "production_behavior_switched": False,
        "authority_model_version": authority_model_version,
        "fact_scope": fact_scope,
        "error": {"type": type(error).__name__, "message": str(error)},
    }
