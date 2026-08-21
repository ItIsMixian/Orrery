"""Load and resolve the separately versioned Observatory managed-tool inventory."""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterator


def read_component_manifest() -> dict[str, Any]:
    payload = json.loads(files("project_orrery_observatory").joinpath("component.json").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid Observatory component manifest")
    return payload


MANAGED_TOOLS = tuple(Path(value) for value in read_component_manifest()["managed_tools"])
TEMPLATE_PROJECTION = read_component_manifest().get("template_projection", {})


def _complete_asset_root(root: Path) -> bool:
    return all((root / relative).is_file() for relative in MANAGED_TOOLS)


def observatory_asset_root() -> Path:
    """Return packaged wheel assets, or the canonical root in a source checkout."""
    packaged = Path(__file__).resolve().parent / "assets"
    if _complete_asset_root(packaged):
        return packaged
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "component-versions.json").is_file() and _complete_asset_root(parent):
            return parent
    raise RuntimeError("cannot locate packaged or source Observatory managed assets")


def iter_observatory_assets(source_root: Path) -> Iterator[tuple[Path, Path]]:
    """Resolve managed assets from a repository root or compatibility template root."""
    for relative in MANAGED_TOOLS:
        source = source_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"missing Observatory managed tool: {source}")
        yield relative, source


def projected_bytes(relative: Path, source: Path) -> bytes:
    """Turn self-hosted sources into canonical install-template bytes."""
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError:
        return raw
    rules = TEMPLATE_PROJECTION.get(relative.as_posix(), {})
    if isinstance(rules, dict):
        for current, template in rules.items():
            text = text.replace(str(current), str(template))
    return text.encode("utf-8")
