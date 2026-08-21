"""Read-only planning for explicit Authority Model adoption.

This internal module describes a possible manifest change.  It never writes,
backs up, or mutates the supplied manifest, and it does not expose a stable
top-level Core API.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .authority_compatibility import (
    AUTHORITY_MODEL_FIELD,
    DEFAULT_KNOWN_AUTHORITY_MODEL_VERSIONS,
    DEFAULT_SUPPORTED_AUTHORITY_MODEL_VERSIONS,
    judge_authority_model_version,
    judge_project_authority_model,
)
from .schema import DOCUMENT_SCHEMA, PROJECT_MANIFEST_FORMAT


class AuthorityModelMigrationPlanError(ValueError):
    """Raised when a migration plan request is malformed."""


def _field_value(manifest: Mapping[str, Any], field: str) -> dict[str, Any]:
    present = field in manifest
    return {
        "present": present,
        "value": manifest.get(field) if present else None,
    }


def plan_authority_model_migration(
    manifest: Mapping[str, Any],
    *,
    target_version: int,
    supported_versions: Sequence[int] = DEFAULT_SUPPORTED_AUTHORITY_MODEL_VERSIONS,
    known_versions: Sequence[int] = DEFAULT_KNOWN_AUTHORITY_MODEL_VERSIONS,
) -> dict[str, Any]:
    """Build a deterministic, no-write migration plan for one project manifest."""

    if not isinstance(manifest, Mapping):
        raise AuthorityModelMigrationPlanError("project manifest must be an object")
    if (
        isinstance(target_version, bool)
        or not isinstance(target_version, int)
        or target_version <= 0
    ):
        raise AuthorityModelMigrationPlanError(
            "target_version must be a positive integer"
        )

    source = judge_project_authority_model(
        manifest,
        supported_versions=supported_versions,
        known_versions=known_versions,
    )
    target = judge_authority_model_version(
        target_version,
        supported_versions=supported_versions,
        known_versions=known_versions,
    )

    dimensions = {}
    for field, supported_value in (
        ("manifest_format", PROJECT_MANIFEST_FORMAT),
        ("document_schema", DOCUMENT_SCHEMA),
    ):
        current = _field_value(manifest, field)
        dimensions[field] = {
            "before": current,
            "after": dict(current),
            "supported_value": supported_value,
            "compatible": current["present"] and current["value"] == supported_value,
        }

    allowed = False
    changed = False
    reason_code: str
    required_action: str
    changes: list[dict[str, Any]] = []

    if target["status"] != "supported":
        reason_code = "target-unsupported"
        required_action = "use-tool-supporting-target"
    elif not all(value["compatible"] for value in dimensions.values()):
        reason_code = "orthogonal-version-incompatible"
        required_action = "upgrade-project-format-or-document-schema"
    elif source["status"] == "legacy-unversioned":
        allowed = True
        changed = True
        reason_code = "ready"
        required_action = "explicit-apply-with-backup"
        changes.append(
            {
                "path": ".project-orrery.json",
                "operation": "set",
                "field": AUTHORITY_MODEL_FIELD,
                "before": _field_value(manifest, AUTHORITY_MODEL_FIELD),
                "after": {"present": True, "value": target_version},
            }
        )
    elif source["status"] == "supported" and source["selected_version"] == target_version:
        allowed = True
        reason_code = "already-selected"
        required_action = "none"
    elif source["status"] == "supported":
        reason_code = "migration-path-unavailable"
        required_action = "explicit-versioned-migration-path"
    elif source["status"] == "invalid":
        reason_code = "source-invalid"
        required_action = "repair-invalid-field"
    else:
        reason_code = "source-unsupported"
        required_action = "compatible-tool-or-explicit-versioned-migration"

    return {
        "mode": "dry-run",
        "allowed": allowed,
        "changed": changed,
        "reason_code": reason_code,
        "source": source,
        "target": target,
        "changes": changes,
        "writes_performed": False,
        "backup_required": changed,
        "backup_scope": [".project-orrery.json"] if changed else [],
        "preserved_dimensions": dimensions,
        "required_action": required_action,
    }
