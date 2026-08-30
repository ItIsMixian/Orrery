"""Portable operating-rules inventory owned by the existing Authority Meta Model.

The inventory is a tool contract, not a target-project document.  This module
performs dependency-free validation and never writes, migrates, approves, or
promotes project facts.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


OPERATING_RULES_INVENTORY_ID = "orrery-operating-rules-v1"
OPERATING_RULES_INVENTORY_VERSION = 1
OPERATING_RULES_SCHEMA_VERSION = 1
OPERATING_RULES_PROJECTION = "orrery-operating-rules-projection-v1"
OPERATING_RULES_V1_SHA256 = "f786c4f2365e9b7b0e107d8365aba2ea5c81799b1b0a75a254a6aa06fe9eb7dd"
SUPPORTED_OPERATING_RULES_VERSIONS = (1,)
_RULE_ID = re.compile(r"^ORR-OP-[0-9]{3}$")
_CONCEPT_ID = re.compile(r"^[a-z][a-z0-9-]+$")
_MESSAGE_KEY = re.compile(r"^[a-z][a-z0-9_.-]+$")


class OperatingRulesError(ValueError):
    """Raised when the canonical inventory cannot be trusted."""


def operating_rules_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "orrery-operating-rules-v1.json"


def _canonical_inventory_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def _object(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise OperatingRulesError(f"{label} must be an object")
    return value


def _exact_keys(value: Mapping[str, Any], required: set[str], label: str) -> None:
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        raise OperatingRulesError(f"{label} fields mismatch: missing={missing}, extra={extra}")


def _strings(value: object, label: str, *, minimum: int = 1) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) < minimum
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise OperatingRulesError(f"{label} must contain at least {minimum} non-empty strings")
    items = list(value)
    if len(set(items)) != len(items):
        raise OperatingRulesError(f"{label} must not contain duplicates")
    return items


def _validate_source(value: object, label: str) -> dict[str, str]:
    source = _object(value, label)
    _exact_keys(source, {"path", "authority_role", "locator"}, label)
    roles = {"product-seed", "agent-index", "adr", "approved-design", "skill-contract"}
    if source["authority_role"] not in roles:
        raise OperatingRulesError(f"{label}.authority_role is unsupported")
    for key in ("path", "locator"):
        if not isinstance(source[key], str) or not source[key].strip():
            raise OperatingRulesError(f"{label}.{key} must be a non-empty string")
    return {key: str(source[key]) for key in ("path", "authority_role", "locator")}


def _validate_concept(value: object, label: str) -> dict[str, Any]:
    concept = _object(value, label)
    allowed = {
        "concept_id", "subsystem_id", "aliases", "minimum_governing_sources",
        "conditional_governing_sources", "conclusion_code",
    }
    required = allowed - {"conditional_governing_sources"}
    if not required.issubset(concept) or set(concept) - allowed:
        raise OperatingRulesError(f"{label} has missing or unknown fields")
    concept_id = concept["concept_id"]
    if not isinstance(concept_id, str) or not _CONCEPT_ID.fullmatch(concept_id):
        raise OperatingRulesError(f"{label}.concept_id is invalid")
    for key in ("subsystem_id", "conclusion_code"):
        if not isinstance(concept[key], str) or not concept[key]:
            raise OperatingRulesError(f"{label}.{key} must be a non-empty string")
    aliases = _strings(concept["aliases"], f"{label}.aliases", minimum=2)
    minimum = _strings(
        concept["minimum_governing_sources"],
        f"{label}.minimum_governing_sources",
        minimum=2,
    )
    conditional = _strings(
        concept.get("conditional_governing_sources", []),
        f"{label}.conditional_governing_sources",
        minimum=0,
    )
    return {
        "concept_id": concept_id,
        "subsystem_id": concept["subsystem_id"],
        "aliases": aliases,
        "minimum_governing_sources": minimum,
        "conditional_governing_sources": conditional,
        "conclusion_code": concept["conclusion_code"],
    }


def _validate_rule(value: object, index: int) -> dict[str, Any]:
    label = f"rules[{index}]"
    rule = _object(value, label)
    required = {
        "rule_id", "rule_version", "message_key", "summary", "applies_to", "sources",
        "strength", "mechanical_enforcement", "failure_behavior", "unknown_behavior",
        "project_fact_boundary",
    }
    _exact_keys(rule, required, label)
    if not isinstance(rule["rule_id"], str) or not _RULE_ID.fullmatch(rule["rule_id"]):
        raise OperatingRulesError(f"{label}.rule_id is invalid")
    if rule["rule_version"] != 1:
        raise OperatingRulesError(f"{label}.rule_version is unsupported")
    if not isinstance(rule["message_key"], str) or not _MESSAGE_KEY.fullmatch(rule["message_key"]):
        raise OperatingRulesError(f"{label}.message_key is invalid")
    summary = _object(rule["summary"], f"{label}.summary")
    _exact_keys(summary, {"zh-CN", "en"}, f"{label}.summary")
    if any(not isinstance(summary[key], str) or not summary[key].strip() for key in summary):
        raise OperatingRulesError(f"{label}.summary values must be non-empty")
    applies = _object(rule["applies_to"], f"{label}.applies_to")
    _exact_keys(applies, {"stages", "consumers"}, f"{label}.applies_to")
    stages = _strings(applies["stages"], f"{label}.applies_to.stages")
    consumers = _strings(applies["consumers"], f"{label}.applies_to.consumers")
    if not isinstance(rule["sources"], Sequence) or isinstance(rule["sources"], (str, bytes)):
        raise OperatingRulesError(f"{label}.sources must be an array")
    sources = [_validate_source(item, f"{label}.sources[{i}]") for i, item in enumerate(rule["sources"])]
    if not sources:
        raise OperatingRulesError(f"{label}.sources must not be empty")
    if rule["strength"] not in {"must", "must-not", "should"}:
        raise OperatingRulesError(f"{label}.strength is unsupported")
    if rule["mechanical_enforcement"] not in {"enforceable", "partially-enforceable", "human-judgment"}:
        raise OperatingRulesError(f"{label}.mechanical_enforcement is unsupported")
    if rule["failure_behavior"] not in {"block-write", "fail-closed-read-only", "warn-without-escalation"}:
        raise OperatingRulesError(f"{label}.failure_behavior is unsupported")
    if rule["unknown_behavior"] not in {"preserve-unknown", "read-only-unavailable"}:
        raise OperatingRulesError(f"{label}.unknown_behavior is unsupported")
    if rule["project_fact_boundary"] != "not-target-project-fact-or-seed":
        raise OperatingRulesError(f"{label} crosses the target-project fact boundary")
    return {
        **dict(rule),
        "summary": dict(summary),
        "applies_to": {"stages": stages, "consumers": consumers},
        "sources": sources,
    }


def validate_operating_rules(value: object) -> dict[str, Any]:
    inventory = _object(value, "inventory")
    required = {
        "schema_version", "contract_type", "inventory_id", "inventory_version",
        "authority_model_version", "deterministic_owner", "status", "project_fact_boundary",
        "compatibility", "source_policy", "routing", "rules",
    }
    _exact_keys(inventory, required, "inventory")
    constants = {
        "schema_version": 1,
        "contract_type": "orrery-operating-rules",
        "inventory_id": OPERATING_RULES_INVENTORY_ID,
        "inventory_version": OPERATING_RULES_INVENTORY_VERSION,
        "authority_model_version": 1,
        "deterministic_owner": "project-orrery-core",
        "status": "unreleased-candidate",
    }
    for key, expected in constants.items():
        if inventory[key] != expected:
            raise OperatingRulesError(f"inventory.{key} must equal {expected!r}")
    boundary = _object(inventory["project_fact_boundary"], "project_fact_boundary")
    _exact_keys(
        boundary,
        {"classification", "declares_target_project_facts", "is_target_project_seed"},
        "project_fact_boundary",
    )
    if boundary != {
        "classification": "not-target-project-fact-or-seed",
        "declares_target_project_facts": False,
        "is_target_project_seed": False,
    }:
        raise OperatingRulesError("inventory crosses the target-project fact boundary")
    compatibility = _object(inventory["compatibility"], "compatibility")
    _exact_keys(
        compatibility,
        {"supported_inventory_versions", "missing_inventory", "unknown_version", "tamper"},
        "compatibility",
    )
    if compatibility != {
        "supported_inventory_versions": [1],
        "missing_inventory": "read-only-unknown",
        "unknown_version": "read-only-unknown-no-latest-fallback",
        "tamper": "read-only-unknown",
    }:
        raise OperatingRulesError("inventory compatibility policy is invalid")
    policy = _object(inventory["source_policy"], "source_policy")
    if policy.get("distillation_only") is not True:
        raise OperatingRulesError("source policy must remain distillation-only")
    excluded = _strings(policy.get("excluded_content"), "source_policy.excluded_content")
    if "target-project-facts" not in excluded or "orrery-current-state" not in excluded:
        raise OperatingRulesError("source policy does not exclude project/current facts")
    routing = _object(inventory["routing"], "routing")
    _exact_keys(routing, {"contract", "portable_concepts"}, "routing")
    if routing["contract"] != "authority-route-preflight-v1":
        raise OperatingRulesError("routing contract is unsupported")
    if not isinstance(routing["portable_concepts"], Sequence) or isinstance(routing["portable_concepts"], (str, bytes)):
        raise OperatingRulesError("routing.portable_concepts must be an array")
    concepts = [
        _validate_concept(item, f"routing.portable_concepts[{index}]")
        for index, item in enumerate(routing["portable_concepts"])
    ]
    if len({item["concept_id"] for item in concepts}) != len(concepts):
        raise OperatingRulesError("portable concept IDs must be unique")
    if not isinstance(inventory["rules"], Sequence) or isinstance(inventory["rules"], (str, bytes)):
        raise OperatingRulesError("rules must be an array")
    rules = [_validate_rule(item, index) for index, item in enumerate(inventory["rules"])]
    if not rules:
        raise OperatingRulesError("rules must not be empty")
    if len({item["rule_id"] for item in rules}) != len(rules):
        raise OperatingRulesError("rule IDs must be unique")
    if len({item["message_key"] for item in rules}) != len(rules):
        raise OperatingRulesError("rule message keys must be unique")
    return {
        **dict(inventory),
        "project_fact_boundary": dict(boundary),
        "compatibility": dict(compatibility),
        "source_policy": dict(policy),
        "routing": {"contract": routing["contract"], "portable_concepts": concepts},
        "rules": rules,
    }


def load_operating_rules(
    *,
    version: int = 1,
    path: Path | None = None,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    if isinstance(version, bool) or not isinstance(version, int) or version not in SUPPORTED_OPERATING_RULES_VERSIONS:
        raise OperatingRulesError(f"unsupported operating-rules inventory version: {version!r}")
    source = path or operating_rules_path()
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise OperatingRulesError(f"operating-rules inventory is unavailable: {exc}") from exc
    digest = hashlib.sha256(_canonical_inventory_bytes(raw)).hexdigest()
    expected = expected_sha256 or OPERATING_RULES_V1_SHA256
    if digest != expected:
        raise OperatingRulesError("operating-rules inventory digest does not match the Core-owned v1 contract")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OperatingRulesError(f"operating-rules inventory is invalid JSON: {exc}") from exc
    validated = validate_operating_rules(value)
    validated["inventory_sha256"] = f"sha256:{digest}"
    return validated


def project_operating_rules(inventory: Mapping[str, Any] | None = None) -> dict[str, Any]:
    value = dict(inventory) if inventory is not None else load_operating_rules()
    validated = validate_operating_rules({key: item for key, item in value.items() if key != "inventory_sha256"})
    digest = value.get("inventory_sha256") or f"sha256:{OPERATING_RULES_V1_SHA256}"
    return {
        "schema_version": 1,
        "contract_type": OPERATING_RULES_PROJECTION,
        "inventory_id": validated["inventory_id"],
        "inventory_version": validated["inventory_version"],
        "authority_model_version": validated["authority_model_version"],
        "deterministic_owner": validated["deterministic_owner"],
        "status": "available",
        "read_only": True,
        "inventory_sha256": digest,
        "project_fact_boundary": dict(validated["project_fact_boundary"]),
        "compatibility": dict(validated["compatibility"]),
        "routing": dict(validated["routing"]),
        "rules": list(validated["rules"]),
        "guarantees": {
            "writes_target_project": False,
            "creates_or_promotes_authority": False,
            "changes_release_status": False,
            "selects_latest_on_unknown": False,
        },
    }


def inspect_operating_rules(*, version: int = 1, path: Path | None = None) -> dict[str, Any]:
    try:
        projection = project_operating_rules(load_operating_rules(version=version, path=path))
    except OperatingRulesError as exc:
        return {
            "schema_version": 1,
            "contract_type": "orrery-operating-rules-capability-v1",
            "requested_inventory_version": version,
            "supported_inventory_versions": list(SUPPORTED_OPERATING_RULES_VERSIONS),
            "status": "unavailable",
            "read_only": True,
            "unknown": True,
            "reason": str(exc),
            "inventory": None,
            "guarantees": {
                "writes_target_project": False,
                "creates_or_promotes_authority": False,
                "changes_release_status": False,
                "selects_latest_on_unknown": False,
            },
        }
    return {
        "schema_version": 1,
        "contract_type": "orrery-operating-rules-capability-v1",
        "requested_inventory_version": version,
        "supported_inventory_versions": list(SUPPORTED_OPERATING_RULES_VERSIONS),
        "status": "supported",
        "read_only": True,
        "unknown": False,
        "reason": None,
        "inventory": projection,
        "guarantees": dict(projection["guarantees"]),
    }


__all__ = [
    "OPERATING_RULES_INVENTORY_ID",
    "OPERATING_RULES_INVENTORY_VERSION",
    "OPERATING_RULES_PROJECTION",
    "OPERATING_RULES_V1_SHA256",
    "SUPPORTED_OPERATING_RULES_VERSIONS",
    "OperatingRulesError",
    "inspect_operating_rules",
    "load_operating_rules",
    "operating_rules_path",
    "project_operating_rules",
    "validate_operating_rules",
]
