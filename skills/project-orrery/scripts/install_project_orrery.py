#!/usr/bin/env python3
"""Compatibility entry for the platform-neutral Project Orrery CLI."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve()
SKILL_ROOT = SCRIPT.parents[1]


def source_cli_available() -> bool:
    for parent in SCRIPT.parents:
        sources = [
            parent / "packages" / "project-orrery-core" / "src",
            parent / "packages" / "project-orrery-observatory" / "src",
            parent / "packages" / "project-orrery-cli" / "src",
        ]
        if all(source.is_dir() for source in sources):
            sys.path[:0] = [str(source) for source in sources]
            return True
    return False


def main() -> int:
    if source_cli_available():
        from project_orrery_cli.context import skill_context
        from project_orrery_cli.scaffold import main as scaffold_main

        return scaffold_main(context=skill_context(SKILL_ROOT))
    runpy.run_path(str(SCRIPT.with_name("_legacy_install_project_orrery.py")), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
