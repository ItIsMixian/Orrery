"""Manifest models shared by the CLI, Observatory, and future Adapters."""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping


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

    @classmethod
    def from_path(cls, path: Path) -> "ReleaseContract":
        payload = read_json_object(path)
        if payload.get("name") != "project-orrery":
            raise ValueError(f"invalid Project Orrery release manifest: {path}")
        return cls(payload)

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
    return manifest
