"""Experimental Authority Model capability judgment for Gate B.

The module evaluates one public model selector against explicit, discrete
consumer capabilities. It does not mutate manifests, migrate projects, or
export a stable top-level Core API.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


PUBLIC_AUTHORITY_MODEL_VERSION = 1
AUTHORITY_MODEL_FIXTURE_IDS = {1: "amm-fixture-v1"}
DEFAULT_SUPPORTED_AUTHORITY_MODEL_VERSIONS = (1,)
DEFAULT_KNOWN_AUTHORITY_MODEL_VERSIONS = (1,)
AUTHORITY_MODEL_FIELD = "authority_model_version"
AUTHORITY_MODEL_MISSING = object()
UNAVAILABLE_AUTHORITY_CLAIMS = (
    "effective",
    "current",
    "implemented",
    "validated",
)


class AuthorityModelCompatibilityError(ValueError):
    """Raised when a consumer capability declaration is malformed."""


def _normalize_versions(values: Sequence[int], *, label: str) -> tuple[int, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise AuthorityModelCompatibilityError(f"{label} must be a sequence of positive integers")
    versions = tuple(values)
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in versions):
        raise AuthorityModelCompatibilityError(f"{label} must contain only positive integers")
    if len(set(versions)) != len(versions):
        raise AuthorityModelCompatibilityError(f"{label} must not contain duplicates")
    return tuple(sorted(versions))


def judge_authority_model_version(
    selected_version: Any = AUTHORITY_MODEL_MISSING,
    *,
    supported_versions: Sequence[int] = DEFAULT_SUPPORTED_AUTHORITY_MODEL_VERSIONS,
    known_versions: Sequence[int] = DEFAULT_KNOWN_AUTHORITY_MODEL_VERSIONS,
) -> dict[str, Any]:
    """Return a fail-closed capability judgment without changing project state."""

    supported = _normalize_versions(supported_versions, label="supported_versions")
    known = _normalize_versions(known_versions, label="known_versions")
    if not set(supported).issubset(known):
        raise AuthorityModelCompatibilityError(
            "supported_versions must be a subset of known_versions"
        )

    status: str
    required_action: str
    authority_available = False
    normalized_selection: int | None

    if selected_version is AUTHORITY_MODEL_MISSING:
        status = "legacy-unversioned"
        normalized_selection = None
        required_action = "explicit-semantic-migration"
    elif (
        isinstance(selected_version, bool)
        or not isinstance(selected_version, int)
        or selected_version <= 0
    ):
        status = "invalid"
        normalized_selection = None
        required_action = "repair-invalid-field"
    else:
        normalized_selection = selected_version
        if selected_version in supported:
            status = "supported"
            required_action = "none"
            authority_available = True
        elif selected_version in known:
            status = "unsupported-known"
            required_action = "compatible-tool-or-explicit-migration"
        elif known and selected_version > max(known):
            status = "unsupported-newer"
            required_action = "compatible-tool-or-explicit-migration"
        else:
            status = "unsupported-unknown"
            required_action = "compatible-tool-or-explicit-migration"

    return {
        "status": status,
        "selected_version": normalized_selection,
        "supported_versions": list(supported),
        "known_versions": list(known),
        "authority_evaluation_capability": "available" if authority_available else "unavailable",
        "strict_conformance_eligibility": "eligible" if authority_available else "ineligible",
        "read_only_browsing": "available",
        "required_action": required_action,
        "must_not_infer": [] if authority_available else list(UNAVAILABLE_AUTHORITY_CLAIMS),
    }


def judge_project_authority_model(
    manifest: Mapping[str, Any],
    *,
    supported_versions: Sequence[int] = DEFAULT_SUPPORTED_AUTHORITY_MODEL_VERSIONS,
    known_versions: Sequence[int] = DEFAULT_KNOWN_AUTHORITY_MODEL_VERSIONS,
) -> dict[str, Any]:
    """Judge the selector recorded in a project manifest without mutating it."""

    if not isinstance(manifest, Mapping):
        raise AuthorityModelCompatibilityError("project manifest must be an object")
    selected = manifest.get(AUTHORITY_MODEL_FIELD, AUTHORITY_MODEL_MISSING)
    return judge_authority_model_version(
        selected,
        supported_versions=supported_versions,
        known_versions=known_versions,
    )
