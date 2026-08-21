"""Stable machine-readable response contract for the unreleased neutral CLI."""
from __future__ import annotations

import json
from enum import IntEnum
from typing import Any, Iterable, Mapping

from project_orrery_core import CORE_API_VERSION
from project_orrery_core import __version__ as CORE_VERSION

from . import __version__ as CLI_VERSION


JSON_SCHEMA_VERSION = 1


class JsonExitCode(IntEnum):
    """Process exit codes reserved for opt-in JSON and Harness execution."""

    OK = 0
    INVALID_REQUEST = 2
    OPERATION_FAILED = 3
    VALIDATION_FAILED = 4
    COMPATIBILITY_FAILED = 5
    UPDATE_UNAVAILABLE = 6
    TIMEOUT = 7


def issue(code: str, message: str, **details: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"code": code, "message": message}
    if details:
        value["details"] = details
    return value


def response(
    command: str,
    *,
    status: str,
    exit_code: int | JsonExitCode,
    data: Mapping[str, Any] | None = None,
    warnings: Iterable[Mapping[str, Any]] = (),
    errors: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    if status not in {"ok", "warning", "error"}:
        raise ValueError(f"unsupported JSON response status: {status}")
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "command": command,
        "status": status,
        "exit_code": int(exit_code),
        "versions": {
            "core": CORE_VERSION,
            "core_api": CORE_API_VERSION,
            "cli": CLI_VERSION,
        },
        "data": dict(data or {}),
        "warnings": [dict(item) for item in warnings],
        "errors": [dict(item) for item in errors],
    }


def emit(payload: Mapping[str, Any]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True))
