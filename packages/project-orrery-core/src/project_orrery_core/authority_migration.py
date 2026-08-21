"""Pure planning for explicit Authority Model adoption and exact restore.

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


def materialize_authority_model_migration(
    manifest: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    """Return proposed manifest content for one allowed plan without mutating input."""

    if not isinstance(manifest, Mapping) or not isinstance(plan, Mapping):
        raise AuthorityModelMigrationPlanError("manifest and plan must be objects")
    if not plan.get("allowed"):
        raise AuthorityModelMigrationPlanError("cannot materialize a blocked plan")

    proposed = dict(manifest)
    for change in plan.get("changes", ()):
        if not isinstance(change, Mapping):
            raise AuthorityModelMigrationPlanError("plan change must be an object")
        after = change.get("after")
        if (
            change.get("path") != ".project-orrery.json"
            or change.get("operation") != "set"
            or change.get("field") != AUTHORITY_MODEL_FIELD
            or not isinstance(after, Mapping)
            or after.get("present") is not True
        ):
            raise AuthorityModelMigrationPlanError(
                "plan contains an unsupported manifest operation"
            )
        value = after.get("value")
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise AuthorityModelMigrationPlanError(
                "plan contains an invalid Authority Model version"
            )
        proposed[AUTHORITY_MODEL_FIELD] = value
    return proposed


def plan_authority_model_restore(
    current_manifest: Mapping[str, Any],
    backup_manifest: Mapping[str, Any],
    *,
    supported_versions: Sequence[int] = DEFAULT_SUPPORTED_AUTHORITY_MODEL_VERSIONS,
    known_versions: Sequence[int] = DEFAULT_KNOWN_AUTHORITY_MODEL_VERSIONS,
) -> dict[str, Any]:
    """Judge whether one exact migration backup may replace the current manifest.

    Restore is intentionally narrower than general migration.  It accepts only a
    currently supported project and a backup that differs solely in the public
    Authority Model selector.  This prevents an old or foreign backup from
    silently rolling back unrelated project metadata.
    """

    if not isinstance(current_manifest, Mapping) or not isinstance(
        backup_manifest, Mapping
    ):
        raise AuthorityModelMigrationPlanError(
            "current manifest and backup manifest must be objects"
        )

    current = judge_project_authority_model(
        current_manifest,
        supported_versions=supported_versions,
        known_versions=known_versions,
    )
    backup = judge_project_authority_model(
        backup_manifest,
        supported_versions=supported_versions,
        known_versions=known_versions,
    )

    dimensions: dict[str, dict[str, Any]] = {}
    for field, supported_value in (
        ("manifest_format", PROJECT_MANIFEST_FORMAT),
        ("document_schema", DOCUMENT_SCHEMA),
    ):
        current_value = _field_value(current_manifest, field)
        backup_value = _field_value(backup_manifest, field)
        dimensions[field] = {
            "current": current_value,
            "backup": backup_value,
            "supported_value": supported_value,
            "compatible": (
                current_value["present"]
                and backup_value["present"]
                and current_value["value"] == supported_value
                and backup_value["value"] == supported_value
            ),
            "preserved": current_value == backup_value,
        }

    current_without_selector = dict(current_manifest)
    current_without_selector.pop(AUTHORITY_MODEL_FIELD, None)
    backup_without_selector = dict(backup_manifest)
    backup_without_selector.pop(AUTHORITY_MODEL_FIELD, None)
    unrelated_fields_match = current_without_selector == backup_without_selector

    allowed = False
    reason_code: str
    required_action: str
    if not all(value["compatible"] for value in dimensions.values()):
        reason_code = "orthogonal-version-incompatible"
        required_action = "repair-project-format-or-document-schema"
    elif current["status"] != "supported":
        reason_code = "current-model-not-supported"
        required_action = "use-tool-supporting-current-model"
    elif backup["status"] == "invalid":
        reason_code = "backup-model-invalid"
        required_action = "select-valid-migration-backup"
    elif backup["status"] not in {"legacy-unversioned", "supported"}:
        reason_code = "backup-model-unsupported"
        required_action = "use-tool-supporting-backup-model"
    elif (
        backup["status"] == "supported"
        and backup["selected_version"] != current["selected_version"]
    ):
        reason_code = "reverse-migration-path-unavailable"
        required_action = "explicit-versioned-migration-path"
    elif not unrelated_fields_match:
        reason_code = "backup-unrelated-fields-differ"
        required_action = "review-and-merge-manifest-manually"
    else:
        allowed = True
        reason_code = "ready"
        required_action = "explicit-restore-with-receipt-and-undo-backup"

    changed = allowed and dict(current_manifest) != dict(backup_manifest)
    return {
        "mode": "dry-run",
        "allowed": allowed,
        "changed": changed,
        "reason_code": reason_code,
        "current": current,
        "backup": backup,
        "writes_performed": False,
        "undo_backup_required": changed,
        "preserved_dimensions": dimensions,
        "unrelated_fields_match": unrelated_fields_match,
        "required_action": required_action,
    }
