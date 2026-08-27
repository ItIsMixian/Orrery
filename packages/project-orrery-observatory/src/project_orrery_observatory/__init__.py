"""Project Orrery Observatory component inventory."""

from .inventory import (
    MANAGED_TOOLS,
    iter_observatory_assets,
    observatory_asset_root,
    projected_bytes,
    read_component_manifest,
)

__version__ = "0.1.4"

__all__ = [
    "MANAGED_TOOLS",
    "iter_observatory_assets",
    "observatory_asset_root",
    "projected_bytes",
    "read_component_manifest",
]
