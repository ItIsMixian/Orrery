"""Browser delivery bundle for a cached Workstream Graph projection."""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any, Mapping

from .workstream_relation_graph import (
    WORKSTREAM_GRAPH_CSS,
    WORKSTREAM_GRAPH_JS,
    render_workstream_relation_graph_panel,
)


DELIVERY_ASSET_SCHEMA_VERSION = 1
DELIVERY_ASSET_CONTRACT = "workstream-graph-browser-delivery-v1"
MAX_DELIVERY_BYTES = 8 * 1024 * 1024
_CACHE_LOCK = threading.Lock()
_CACHED_HASH: str | None = None
_CACHED_DELIVERY: dict[str, Any] | None = None
_VENDOR_JS: str | None = None


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def build_browser_delivery(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Render the frozen W7.4 presentation as one bounded browser generation."""
    value = dict(projection)
    if value.get("contract_type") != "workstream-relation-graph-observatory":
        raise ValueError("Graph browser delivery projection contract is incompatible")
    if value.get("status") != "ready":
        raise ValueError("Graph browser delivery requires a complete ready projection")
    projection_hash = hashlib.sha256(_canonical_bytes(value)).hexdigest()
    global _CACHED_HASH, _CACHED_DELIVERY, _VENDOR_JS
    with _CACHE_LOCK:
        if _CACHED_HASH == projection_hash and _CACHED_DELIVERY is not None:
            return dict(_CACHED_DELIVERY)
        if _VENDOR_JS is None:
            vendor_path = Path(__file__).with_name("vendor") / "elk.bundled.js"
            _VENDOR_JS = vendor_path.read_text(encoding="utf-8")
        result = {
            "schema_version": DELIVERY_ASSET_SCHEMA_VERSION,
            "contract_type": DELIVERY_ASSET_CONTRACT,
            "projection_hash": projection_hash,
            "panel_html": render_workstream_relation_graph_panel(value),
            "style_text": WORKSTREAM_GRAPH_CSS,
            "vendor_script": _VENDOR_JS,
            "presentation_script": WORKSTREAM_GRAPH_JS,
            "authority": "derived-read-only",
            "read_only": True,
            "network_performed": False,
            "execution_capability": False,
        }
        if len(_canonical_bytes(result)) > MAX_DELIVERY_BYTES:
            raise ValueError("Graph browser delivery exceeds the bounded size")
        _CACHED_HASH = projection_hash
        _CACHED_DELIVERY = dict(result)
        return result
