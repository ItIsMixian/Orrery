from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from contextlib import redirect_stdout
from pathlib import Path

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    expand_profile,
    git_sha,
    load_json,
    machine_inventory,
    promotion_lane_assignments,
    sha256_json,
    validate_and_expand_manifest,
)


def build_inventory(manifest_path: Path) -> dict[str, object]:
    manifest = load_json(manifest_path)
    test_ids, assignments, fast_ids = validate_and_expand_manifest(manifest)
    checkpoint_ids = expand_profile(manifest, "checkpoint", test_ids)
    lanes = promotion_lane_assignments(manifest)
    routed = machine_inventory(manifest)
    return {
        "schema_version": 4,
        "contract_type": "orrery-unittest-inventory-v4",
        "sha": git_sha(),
        "python": platform.python_version(),
        "manifest_sha256": sha256_json(manifest),
        "test_count": len(test_ids),
        "test_ids": test_ids,
        "inventory_sha256": routed["inventory_sha256"],
        "mapping_registry_sha256": routed["mapping_registry_sha256"],
        "tests": routed["tests"],
        "fast_test_count": len(fast_ids),
        "fast_test_ids": fast_ids,
        "checkpoint_test_count": len(checkpoint_ids),
        "checkpoint_test_ids": checkpoint_ids,
        "lanes": [
            {
                "id": lane_id,
                "shards": shard_ids,
                "shard_count": len(shard_ids),
                "test_count": sum(len(assignments[shard_id]) for shard_id in shard_ids),
            }
            for lane_id, shard_ids in lanes.items()
        ],
        "shards": [
            {
                "id": shard["id"],
                "surface": shard["surface"],
                "test_count": len(assignments[shard["id"]]),
                "test_ids": assignments[shard["id"]],
                "budget_seconds": shard.get("budget_seconds"),
            }
            for shard in manifest["shards"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover and validate final unittest shard inventory")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--shard-list", action="store_true", help="print the JSON shard-id array")
    parser.add_argument("--lane-list", action="store_true", help="print the JSON Promotion lane-id array")
    arguments = parser.parse_args()
    if arguments.shard_list and arguments.lane_list:
        parser.error("--shard-list and --lane-list are mutually exclusive")
    os.environ["DOCSITE_AI_ENABLED"] = "0"
    try:
        if arguments.shard_list or arguments.lane_list:
            with redirect_stdout(sys.stderr):
                inventory = build_inventory(arguments.manifest.resolve())
        else:
            inventory = build_inventory(arguments.manifest.resolve())
        if arguments.output:
            from _common import atomic_write_json

            atomic_write_json(arguments.output.resolve(), inventory)
        if arguments.shard_list:
            print(json.dumps([item["id"] for item in inventory["shards"]], separators=(",", ":")))
        elif arguments.lane_list:
            print(json.dumps([item["id"] for item in inventory["lanes"]], separators=(",", ":")))
        else:
            print(
                f"PASS inventory: {inventory['test_count']} unique test IDs, "
                f"{len(inventory['shards'])} shards, {len(inventory['lanes'])} lanes, "
                f"{inventory['fast_test_count']} Fast tests"
                f", {inventory['checkpoint_test_count']} Checkpoint tests"
            )
        return 0
    except CIValidationError as exc:
        print(f"FAIL inventory: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
