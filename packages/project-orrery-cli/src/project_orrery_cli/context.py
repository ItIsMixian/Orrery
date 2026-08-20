"""Explicit source contexts keep Core/CLI independent from platform discovery files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_orrery_core import ReleaseContract, authority_template_root, default_release_contract


@dataclass(frozen=True)
class CliContext:
    release: ReleaseContract
    authority_root: Path
    observatory_root: Path


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "component-versions.json").is_file() and (parent / "scripts" / "docsite").is_dir():
            return parent
    raise RuntimeError("cannot locate Project Orrery source repository for Observatory assets")


def repository_context() -> CliContext:
    return CliContext(
        release=default_release_contract(),
        authority_root=authority_template_root(),
        observatory_root=_repository_root(),
    )


def skill_context(skill_root: Path) -> CliContext:
    """Bridge an existing Skill manifest and Observatory projection into the neutral CLI."""
    root = skill_root.expanduser().resolve()
    return CliContext(
        release=ReleaseContract.from_path(root / "release-manifest.json"),
        authority_root=authority_template_root(),
        observatory_root=root / "assets" / "project-template",
    )
