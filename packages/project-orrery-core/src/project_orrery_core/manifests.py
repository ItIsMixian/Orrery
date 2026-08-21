"""Manifest models shared by the CLI, Observatory, and future Adapters."""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping, Sequence

from .authority_compatibility import AUTHORITY_MODEL_FIELD


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object and reject arrays or scalar roots."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON manifest {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON manifest is not an object: {path}")
    return payload


@dataclass(frozen=True)
class ReleaseContract:
    """Validated view of the legacy release contract used during migration."""

    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.payload.get("name") != "project-orrery":
            raise ValueError("invalid Project Orrery release manifest")
        default_model = self.authority_model_version
        supported_models = self.supported_authority_model_versions
        if default_model is None and supported_models:
            raise ValueError(
                "Authority Model support requires an explicit release default"
            )
        if default_model is not None and default_model not in supported_models:
            raise ValueError(
                "release Authority Model default must be in the discrete support set"
            )

    @classmethod
    def from_path(cls, path: Path) -> "ReleaseContract":
        payload = read_json_object(path)
        try:
            return cls(payload)
        except ValueError as exc:
            raise ValueError(f"invalid Project Orrery release manifest {path}: {exc}") from exc

    @property
    def version(self) -> str:
        return str(self.payload["version"])

    @property
    def project_manifest_format(self) -> int:
        return int(self.payload["project_manifest_format"])

    @property
    def document_schema(self) -> int:
        return int(self.payload["document_schema"])

    @property
    def authority_model_version(self) -> int | None:
        value = self.payload.get(AUTHORITY_MODEL_FIELD)
        if value is None and AUTHORITY_MODEL_FIELD not in self.payload:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(
                "release authority_model_version must be a positive integer"
            )
        return value

    @property
    def supported_authority_model_versions(self) -> tuple[int, ...]:
        rule = self.compatibility.get("authority_model_versions")
        if rule is None:
            return ()
        if not isinstance(rule, Mapping):
            raise ValueError(
                "release compatibility.authority_model_versions must be an object"
            )
        values = rule.get("supported")
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ValueError(
                "release Authority Model supported set must be an array"
            )
        normalized = tuple(values)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in normalized
        ):
            raise ValueError(
                "release Authority Model supported set must contain positive integers"
            )
        if len(set(normalized)) != len(normalized):
            raise ValueError(
                "release Authority Model supported set must not contain duplicates"
            )
        return tuple(sorted(normalized))

    @property
    def compatibility(self) -> Mapping[str, Any]:
        value = self.payload.get("compatibility", {})
        return value if isinstance(value, Mapping) else {}

    @property
    def channel(self) -> str:
        return str(self.payload.get("channel", "stable"))

    @property
    def latest_manifest_url(self) -> str | None:
        value = self.payload.get("latest_manifest_url")
        return value if isinstance(value, str) else None


def default_release_contract() -> ReleaseContract:
    """Return the immutable v0.2.0 bridge contract used by the unreleased Core."""
    resource = files("project_orrery_core").joinpath("data", "release-v0.2.0.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("name") != "project-orrery":
        raise ValueError("invalid bundled Project Orrery release bridge contract")
    return ReleaseContract(payload)


def build_project_manifest(
    existing: Mapping[str, Any],
    *,
    release: ReleaseContract,
    title: str,
    today: str,
    toolchain_version: str,
    toolchain_status: str,
    managed_tools: list[str],
    expected_tool_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Preserve authored installation metadata while updating managed dimensions."""
    manifest = dict(existing)
    new_project = not existing
    manifest.update(
        {
            "name": "project-orrery",
            "version": release.version,
            "manifest_format": release.project_manifest_format,
            "installed_skill_version": release.version,
            "toolchain_version": toolchain_version,
            "document_schema": existing.get("document_schema", release.document_schema),
            "update_channel": existing.get("update_channel", release.channel),
            "latest_manifest_url": release.latest_manifest_url,
            "title": title,
            "installed": existing.get("installed", today),
            "last_scaffold_run": today,
            "authority_status": existing.get("authority_status", "migration_pending"),
            "toolchain_status": toolchain_status,
            "managed_tools": sorted(managed_tools),
            "expected_tool_hashes": dict(expected_tool_hashes),
        }
    )
    if new_project and release.authority_model_version is not None:
        manifest[AUTHORITY_MODEL_FIELD] = release.authority_model_version
    return manifest
