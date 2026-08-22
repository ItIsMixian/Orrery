"""Versioned schema facts owned by Project Orrery Core."""
from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


PROJECT_MANIFEST_FORMAT = 1
DOCUMENT_SCHEMA = 1


def _read_schema(name: str) -> dict[str, Any]:
    resource = files("project_orrery_core").joinpath("schema", name)
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid Core schema resource: {name}")
    return payload


AUTHORITY_SCHEMA = _read_schema("authority-v1.json")
PROJECT_MANIFEST_SCHEMA = _read_schema("project-manifest-v1.json")
COLLABORATION_SCHEMA = _read_schema("collaboration-v1.json")
TEAM_SCHEMA = _read_schema("team-v1.json")
DOCUMENTATION_GOVERNANCE_FINDING_SCHEMA = _read_schema("documentation-governance-finding-v1.json")
REQUIRED_SCAFFOLD_FILES = tuple(AUTHORITY_SCHEMA["required_scaffold_files"])
