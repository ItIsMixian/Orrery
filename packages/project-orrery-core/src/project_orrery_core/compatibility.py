"""Compatibility and migration judgments shared across entry points."""
from __future__ import annotations

import re
import sys
from typing import Any, Mapping


SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value.strip())
    if not match:
        raise ValueError(f"unsupported semantic version: {value!r}")
    return tuple(int(part) for part in match.groups())


def in_integer_range(value: int | None, rule: Any) -> bool:
    if value is None or not isinstance(rule, Mapping):
        return False
    minimum = rule.get("minimum")
    maximum = rule.get("maximum")
    return isinstance(minimum, int) and isinstance(maximum, int) and minimum <= value <= maximum


def direct_upgrade_supported(current: str, rule: Any) -> bool:
    if not isinstance(rule, Mapping):
        return False
    try:
        value = parse_version(current)
        minimum = parse_version(str(rule["minimum"]))
        maximum = parse_version(str(rule["maximum_exclusive"]))
    except (KeyError, ValueError):
        return False
    return minimum <= value < maximum


def target_dimensions(target: Mapping[str, Any] | None) -> tuple[Any, Any, Any]:
    if not target:
        return None, None, None
    legacy = target.get("name") == "project-orrery" and "manifest_format" not in target
    project_format = target.get("manifest_format", 1 if legacy else None)
    document_schema = target.get("document_schema", 1 if legacy else None)
    toolchain = target.get("toolchain_version") or target.get("version")
    return project_format, document_schema, toolchain


def compatibility_with_environment(
    release: Mapping[str, Any],
    target: Mapping[str, Any] | None,
    *,
    python_version: tuple[int, int] | None = None,
) -> tuple[bool, list[str]]:
    compatibility = release.get("compatibility", {})
    reasons: list[str] = []
    runtime = python_version or sys.version_info[:2]
    python_rule = compatibility.get("python", {}) if isinstance(compatibility, Mapping) else {}
    try:
        minimum_python = tuple(int(part) for part in str(python_rule["minimum"]).split(".")[:2])
    except (KeyError, TypeError, ValueError):
        reasons.append("release has no valid minimum Python version")
    else:
        if runtime < minimum_python:
            reasons.append(
                f"Python {runtime[0]}.{runtime[1]} is older than required "
                f"{minimum_python[0]}.{minimum_python[1]}"
            )
    if target is None:
        return not reasons, reasons
    project_format, document_schema, _ = target_dimensions(target)
    if not in_integer_range(project_format, compatibility.get("project_manifest_format")):
        reasons.append(f"project manifest format {project_format!r} is outside the supported range")
    if not in_integer_range(document_schema, compatibility.get("document_schema")):
        reasons.append(f"document schema {document_schema!r} is outside the supported range")
    return not reasons, reasons
