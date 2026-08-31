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


def _extracted_release_asset_root(root: Path) -> Path | None:
    release_path = root / "release-manifest.json"
    versions_path = root / "packages" / "component-versions.json"
    asset_root = root / "assets" / "project-template"
    if not release_path.is_file() or not versions_path.is_file() or not _complete_asset_root(asset_root):
        return None
    try:
        release = json.loads(release_path.read_text(encoding="utf-8"))
        versions = json.loads(versions_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(release, dict) or not isinstance(versions, dict):
        return None

    component = read_component_manifest()
    release_components = release.get("components")
    inventory_components = versions.get("components")
    distribution = release.get("distribution")
    if (
        not isinstance(release_components, dict)
        or not isinstance(inventory_components, dict)
        or not isinstance(distribution, dict)
    ):
        return None
    release_component = release_components.get("observatory", {})
    inventory_component = inventory_components.get("observatory", {})
    if not isinstance(release_component, dict) or not isinstance(inventory_component, dict):
        return None
    archive_paths = distribution.get("archive_paths", ())
    if (
        release.get("name") != "project-orrery"
        or release_component.get("distribution") != component.get("name")
        or inventory_component.get("distribution") != component.get("name")
        or release_component.get("version") != component.get("version")
        or inventory_component.get("version") != component.get("version")
        or distribution.get("archive_root") != f"{root.name}/"
        or not isinstance(archive_paths, list)
        or any(not isinstance(value, str) for value in archive_paths)
    ):
        return None
    expected_assets = {
        f"{root.name}/assets/project-template/{relative.as_posix()}"
        for relative in MANAGED_TOOLS
    }
    if not expected_assets.issubset(set(archive_paths)):
        return None
    return asset_root


def observatory_asset_root() -> Path:
    """Return wheel, source-checkout, or strictly bound release assets."""
    packaged = Path(__file__).resolve().parent / "assets"
    if _complete_asset_root(packaged):
        return packaged
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "component-versions.json").is_file() and _complete_asset_root(parent):
            return parent
        extracted = _extracted_release_asset_root(parent)
        if extracted is not None:
            return extracted
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
