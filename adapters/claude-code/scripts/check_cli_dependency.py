#!/usr/bin/env python3
"""Fail closed unless the Claude Code adapter's declared CLI is usable."""
from __future__ import annotations

import json
import re
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


ADAPTER_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ADAPTER_ROOT / "adapter-manifest.json"
VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"unsupported version format: {value!r}")
    return tuple(int(part) for part in match.groups())


def load_requirement() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        requirement = manifest["requires"]["cli"]
        values = (
            requirement["distribution"],
            requirement["entrypoint"],
            requirement["minimum"],
            requirement["maximum_exclusive"],
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"invalid adapter CLI requirement in {MANIFEST_PATH}: {error}") from error
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"invalid adapter CLI requirement in {MANIFEST_PATH}: expected non-empty strings")
    parse_version(requirement["minimum"])
    parse_version(requirement["maximum_exclusive"])
    return requirement


def main() -> int:
    try:
        requirement = load_requirement()
    except ValueError as error:
        print(f"ERROR code=adapter_manifest_invalid detail={error}", file=sys.stderr)
        return 2

    distribution = requirement["distribution"]
    entrypoint = requirement["entrypoint"]
    try:
        installed = version(distribution)
    except PackageNotFoundError:
        print(f"ERROR code=cli_distribution_missing distribution={distribution}", file=sys.stderr)
        return 3

    try:
        installed_tuple = parse_version(installed)
    except ValueError as error:
        print(f"ERROR code=cli_version_unparseable distribution={distribution} detail={error}", file=sys.stderr)
        return 4
    minimum = requirement["minimum"]
    maximum_exclusive = requirement["maximum_exclusive"]
    if not (parse_version(minimum) <= installed_tuple < parse_version(maximum_exclusive)):
        print(
            "ERROR code=cli_version_incompatible "
            f"distribution={distribution} installed={installed} required=>={minimum},<{maximum_exclusive}",
            file=sys.stderr,
        )
        return 4

    executable = shutil.which(entrypoint)
    if executable is None:
        print(f"ERROR code=cli_entrypoint_missing entrypoint={entrypoint}", file=sys.stderr)
        return 3

    print(f"OK distribution={distribution} version={installed} entrypoint={executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
