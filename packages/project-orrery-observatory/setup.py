"""Build the Observatory wheel with a snapshot of the monorepo managed tools."""
from __future__ import annotations

import json
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
COMPONENT_MANIFEST = PACKAGE_ROOT / "src" / "project_orrery_observatory" / "component.json"


class BuildPyWithManagedAssets(build_py):
    """Copy canonical managed tools into build_lib without duplicating source files."""

    def run(self) -> None:
        super().run()
        payload = json.loads(COMPONENT_MANIFEST.read_text(encoding="utf-8"))
        destination_root = Path(self.build_lib) / "project_orrery_observatory" / "assets"
        for raw_relative in payload["managed_tools"]:
            relative = Path(raw_relative)
            source = REPOSITORY_ROOT / relative
            if not source.is_file():
                raise RuntimeError(f"missing canonical Observatory managed tool: {source}")
            destination = destination_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            self.copy_file(str(source), str(destination))


setup(cmdclass={"build_py": BuildPyWithManagedAssets})
