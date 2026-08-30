"""Read-only projection for the existing Authority navigation surface.

The Core operating-rules projection remains the semantic owner.  This module
only pairs that projection with explicitly sourced target-project Seed text so
the two layers can be displayed without being merged.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


FACT_RULES_PROJECTION = "authority-facts-and-rules-projection-v1"
_PRINCIPLE = re.compile(r"(?m)^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*(.*)$")


def project_project_principles(path: Path) -> dict[str, Any]:
    """Project numbered Seed principles without interpreting their authority."""

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "schema_version": 1,
            "contract_type": "target-project-seed-projection-v1",
            "status": "unavailable",
            "read_only": True,
            "source": "docs/core/principles.md",
            "items": [],
            "reason": str(exc)[:240],
        }
    items = [
        {
            "ordinal": int(match.group(1)),
            "title": match.group(2).strip(),
            "summary": match.group(3).strip(),
        }
        for match in _PRINCIPLE.finditer(text)
    ]
    return {
        "schema_version": 1,
        "contract_type": "target-project-seed-projection-v1",
        "status": "available" if items else "unavailable",
        "read_only": True,
        "source": "docs/core/principles.md",
        "items": items,
        "reason": None if items else "numbered Seed principles were not found",
    }


def build_fact_rules_projection(
    *,
    project_principles: Mapping[str, Any],
    operating_rules_capability: Mapping[str, Any],
) -> dict[str, Any]:
    """Keep project Seed and tool rules as separately sourced read-only layers."""

    inventory = operating_rules_capability.get("inventory")
    rules = inventory.get("rules", []) if isinstance(inventory, Mapping) else []
    tool_layer = {
        "status": "available" if isinstance(inventory, Mapping) else "unavailable",
        "inventory_id": inventory.get("inventory_id") if isinstance(inventory, Mapping) else None,
        "inventory_version": inventory.get("inventory_version") if isinstance(inventory, Mapping) else None,
        "authority_model_version": inventory.get("authority_model_version") if isinstance(inventory, Mapping) else None,
        "inventory_sha256": inventory.get("inventory_sha256") if isinstance(inventory, Mapping) else None,
        "source": "project-orrery-core",
        "read_only": True,
        "rules": list(rules) if isinstance(rules, list) else [],
        "reason": operating_rules_capability.get("reason"),
    }
    return {
        "schema_version": 1,
        "contract_type": FACT_RULES_PROJECTION,
        "read_only": True,
        "creates_project_facts": False,
        "writes_target_project": False,
        "project_principles": dict(project_principles),
        "orrery_operating_rules": tool_layer,
        "layer_boundary": {
            "merged": False,
            "project_seed_source": "target-project-docs",
            "operating_rules_source": "versioned-tool-contract",
            "text_similarity_does_not_promote_authority": True,
        },
    }


__all__ = [
    "FACT_RULES_PROJECTION",
    "build_fact_rules_projection",
    "project_project_principles",
]
