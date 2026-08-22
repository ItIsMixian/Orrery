"""Read-only Phase 1 contracts for documentation governance findings.

This module validates observations that another future audit runtime may produce.
It does not scan repositories, choose thresholds, write author documents, change
Authority state, or expose a CLI.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from importlib.resources import files
from pathlib import PurePosixPath
from typing import Any, Mapping

from .schema import DOCUMENTATION_GOVERNANCE_FINDING_SCHEMA


DOCUMENTATION_FINDING_SCHEMA_VERSION = 1
DOCUMENTATION_FINDING_CONTRACT_ID = "documentation-governance-finding-v1"
DOCUMENTATION_RULE_REGISTRY_ID = "documentation-governance-rules-v1"
REQUIRED_MUST_NOT_INFER = frozenset(
    {
        "authority-change",
        "document-invalid",
        "automatic-author-document-write",
        "validation-success",
        "automatic-finding-closure",
    }
)


class DocumentationGovernanceContractError(ValueError):
    """Raised when a finding or rule registry violates the frozen v1 contract."""


def _read_rule_registry() -> dict[str, Any]:
    resource = files("project_orrery_core").joinpath(
        "data", "documentation-governance-rules-v1.json"
    )
    try:
        payload = json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentationGovernanceContractError(
            "cannot read documentation governance rule registry"
        ) from exc
    if not isinstance(payload, dict):
        raise DocumentationGovernanceContractError(
            "documentation governance rule registry must be an object"
        )
    return payload


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _validate_schema_value(value: Any, schema: Mapping[str, Any], path: str) -> None:
    if "const" in schema and value != schema["const"]:
        raise DocumentationGovernanceContractError(
            f"{path} must equal {schema['const']!r}"
        )
    allowed = schema.get("enum")
    if isinstance(allowed, list) and value not in allowed:
        raise DocumentationGovernanceContractError(f"{path} is not an allowed value")
    expected = schema.get("type")
    if isinstance(expected, str) and not _schema_type_matches(value, expected):
        raise DocumentationGovernanceContractError(f"{path} must be {expected}")
    if isinstance(expected, list) and not any(
        _schema_type_matches(value, item) for item in expected
    ):
        raise DocumentationGovernanceContractError(f"{path} has an invalid type")
    if value is None:
        return
    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            raise DocumentationGovernanceContractError(
                f"{path} is missing required field {missing[0]}"
            )
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise DocumentationGovernanceContractError(
                    f"{path} contains forbidden field {sorted(unknown)[0]}"
                )
        for name, item in value.items():
            item_schema = properties.get(name)
            if isinstance(item_schema, Mapping):
                _validate_schema_value(item, item_schema, f"{path}.{name}")
    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise DocumentationGovernanceContractError(f"{path} has too few items")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True) for item in value]
            if len(canonical) != len(set(canonical)):
                raise DocumentationGovernanceContractError(
                    f"{path} must contain unique items"
                )
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_schema, f"{path}[{index}]")
    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        pattern = schema.get("pattern")
        if isinstance(minimum_length, int) and len(value) < minimum_length:
            raise DocumentationGovernanceContractError(f"{path} is too short")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            raise DocumentationGovernanceContractError(
                f"{path} does not match the required pattern"
            )
        if schema.get("format") == "date-time":
            try:
                timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise DocumentationGovernanceContractError(
                    f"{path} must be an ISO 8601 date-time"
                ) from exc
            if "T" not in value or timestamp.tzinfo is None:
                raise DocumentationGovernanceContractError(
                    f"{path} must include a time and UTC offset"
                )
    if isinstance(value, int) and not isinstance(value, bool):
        minimum_value = schema.get("minimum")
        if isinstance(minimum_value, int) and value < minimum_value:
            raise DocumentationGovernanceContractError(
                f"{path} is below the minimum"
            )


def _validate_relative_document_path(value: str, path: str) -> None:
    if "\\" in value:
        raise DocumentationGovernanceContractError(f"{path} must use forward slashes")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise DocumentationGovernanceContractError(
            f"{path} must be a normalized repository-relative path"
        )


def validate_documentation_rule_registry(payload: Mapping[str, Any]) -> None:
    """Validate the versioned Phase 1 registry without selecting project budgets."""
    expected_top_level = {
        "registry_id",
        "registry_version",
        "finding_contract_id",
        "status",
        "execution_constraints",
        "advisory_configuration",
        "rules",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_top_level:
        raise DocumentationGovernanceContractError(
            "documentation governance rule registry has an invalid shape"
        )
    if payload["registry_id"] != DOCUMENTATION_RULE_REGISTRY_ID:
        raise DocumentationGovernanceContractError("unsupported rule registry ID")
    if payload["registry_version"] != 1:
        raise DocumentationGovernanceContractError("unsupported rule registry version")
    if payload["finding_contract_id"] != DOCUMENTATION_FINDING_CONTRACT_ID:
        raise DocumentationGovernanceContractError("rule registry targets another contract")
    if payload["status"] != "candidate":
        raise DocumentationGovernanceContractError("Phase 1 rule registry must remain candidate")
    constraints = payload["execution_constraints"]
    if not isinstance(constraints, Mapping) or constraints != {
        "network_access": False,
        "author_document_writes": False,
        "authority_mutation": False,
        "automatic_finding_closure": False,
    }:
        raise DocumentationGovernanceContractError(
            "rule registry execution constraints must remain read-only and offline"
        )
    advisory = payload["advisory_configuration"]
    if not isinstance(advisory, Mapping) or advisory != {
        "location": "unselected",
        "default_when_absent": "disabled",
        "thresholds_are_authority": False,
        "thresholds_are_project_local": True,
    }:
        raise DocumentationGovernanceContractError(
            "advisory configuration must not choose a global threshold or authority effect"
        )
    rules = payload["rules"]
    if not isinstance(rules, list) or not rules:
        raise DocumentationGovernanceContractError("rule registry must contain rules")
    expected_rule_fields = {
        "rule_id",
        "category",
        "severity",
        "document_roles",
        "review_class",
        "threshold_key",
        "program_gate",
        "default_exit_code",
        "authority_effect",
        "author_document_effect",
    }
    seen: set[str] = set()
    for rule in rules:
        if not isinstance(rule, Mapping) or set(rule) != expected_rule_fields:
            raise DocumentationGovernanceContractError("rule has an invalid shape")
        rule_id = rule["rule_id"]
        if not isinstance(rule_id, str) or rule_id in seen:
            raise DocumentationGovernanceContractError("rule IDs must be unique strings")
        seen.add(rule_id)
        if rule["authority_effect"] != "none" or rule["author_document_effect"] != "none":
            raise DocumentationGovernanceContractError(
                "documentation rules cannot mutate authority or author documents"
            )
        if rule["program_gate"] not in {"advisory", "eligible-not-enabled"}:
            raise DocumentationGovernanceContractError("rule program gate is invalid")
        if rule["default_exit_code"] != 0:
            raise DocumentationGovernanceContractError(
                "Phase 1 findings cannot enable a failing program exit"
            )
        if rule["review_class"] == "soft-budget":
            if not rule["threshold_key"] or rule["program_gate"] != "advisory":
                raise DocumentationGovernanceContractError(
                    "soft review budgets require a project threshold and advisory program effect"
                )
        elif rule["threshold_key"] is not None:
            raise DocumentationGovernanceContractError(
                "non-budget rules cannot select a soft threshold"
            )


_RULE_REGISTRY = _read_rule_registry()
validate_documentation_rule_registry(_RULE_REGISTRY)
_RULES_BY_ID = {rule["rule_id"]: rule for rule in _RULE_REGISTRY["rules"]}


def load_documentation_rule_registry() -> dict[str, Any]:
    """Return a detached copy of the frozen provider-neutral rule registry."""
    return deepcopy(_RULE_REGISTRY)


def validate_documentation_finding(payload: Mapping[str, Any]) -> None:
    """Validate one non-authoritative v1 finding and its review-only semantics."""
    if not isinstance(payload, Mapping):
        raise DocumentationGovernanceContractError("documentation finding must be an object")
    _validate_schema_value(payload, DOCUMENTATION_GOVERNANCE_FINDING_SCHEMA, "finding")

    rule = _RULES_BY_ID.get(payload["rule_id"])
    if rule is None:
        raise DocumentationGovernanceContractError("finding references an unknown rule")
    source = payload["source"]
    review = payload["review"]
    for field in ("category", "severity"):
        if payload[field] != rule[field]:
            raise DocumentationGovernanceContractError(
                f"finding {field} does not match the rule registry"
            )
    if source["document_role"] not in rule["document_roles"]:
        raise DocumentationGovernanceContractError(
            "finding document role is outside the rule registry"
        )
    for field in ("review_class", "program_gate", "authority_effect", "author_document_effect"):
        if review[field] != rule[field]:
            raise DocumentationGovernanceContractError(
                f"finding review {field} does not match the rule registry"
            )
    _validate_relative_document_path(source["document"], "finding.source.document")
    for index, evidence in enumerate(payload["source_evidence"]):
        _validate_relative_document_path(
            evidence["path"], f"finding.source_evidence[{index}].path"
        )
        if evidence["path"] != source["document"]:
            raise DocumentationGovernanceContractError(
                "source evidence must refer to the finding document"
            )
        if evidence["line_end"] < evidence["line_start"]:
            raise DocumentationGovernanceContractError(
                "source evidence line range is reversed"
            )
    uncertainty = payload["uncertainty"]
    if uncertainty["status"] == "known" and uncertainty["reason"] is not None:
        raise DocumentationGovernanceContractError(
            "known observations cannot carry an uncertainty reason"
        )
    if uncertainty["status"] == "unknown" and not uncertainty["reason"]:
        raise DocumentationGovernanceContractError(
            "unknown observations require an uncertainty reason"
        )
    acknowledgement = review["acknowledgement"]
    status = review["status"]
    expected_disposition = {
        "acknowledged": "acknowledge",
        "deferred": "defer",
        "resolved": "resolve",
    }
    if status == "open" and acknowledgement is not None:
        raise DocumentationGovernanceContractError(
            "open findings cannot have an acknowledgement"
        )
    if status != "open":
        if not isinstance(acknowledgement, Mapping):
            raise DocumentationGovernanceContractError(
                "non-open findings require an acknowledgement record"
            )
        if acknowledgement["disposition"] != expected_disposition[status]:
            raise DocumentationGovernanceContractError(
                "acknowledgement disposition does not match finding status"
            )
        if status == "deferred" and acknowledgement["review_after"] is None:
            raise DocumentationGovernanceContractError(
                "deferred findings require a review_after date"
            )
        if status != "deferred" and acknowledgement["review_after"] is not None:
            raise DocumentationGovernanceContractError(
                "only deferred findings may set review_after"
            )
    if set(payload["must_not_infer"]) != REQUIRED_MUST_NOT_INFER:
        raise DocumentationGovernanceContractError(
            "finding must freeze every non-escalation prohibition"
        )


def canonical_documentation_finding_json(payload: Mapping[str, Any]) -> str:
    """Return deterministic JSON after validation; this function performs no writes."""
    validate_documentation_finding(payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
