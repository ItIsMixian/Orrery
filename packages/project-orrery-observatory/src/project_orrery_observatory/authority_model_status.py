"""Display-neutral projection of a Core Authority Model capability judgment.

This module does not evaluate project semantics. It only turns an already
computed Core judgment into a read-only Observatory status signal.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def project_authority_model_status(
    capability: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a status signal without creating or upgrading project facts."""

    if capability is None:
        return {
            "level": "unknown",
            "code": "authority-model-not-reported",
            "read_only": True,
            "message": "Authority Model capability was not supplied.",
        }

    status = str(capability.get("status", "invalid"))
    selected = capability.get("selected_version")
    available = capability.get("authority_evaluation_capability") == "available"
    if status == "supported" and available:
        level = "ok"
        code = "authority-model-supported"
        message = (
            f"Authority Model {selected} is supported; strict evaluation is eligible."
        )
        read_only = False
    elif status == "legacy-unversioned":
        level = "warning"
        code = "authority-model-legacy-unversioned"
        message = "No Authority Model version is selected; only raw project knowledge is readable."
        read_only = True
    else:
        level = "error"
        code = "authority-model-unsupported"
        message = f"Authority Model capability is {status}; deterministic claims are unavailable."
        read_only = True

    return {
        "level": level,
        "code": code,
        "status": status,
        "selected_version": selected,
        "read_only": read_only,
        "message": message,
        "required_action": capability.get("required_action"),
    }
