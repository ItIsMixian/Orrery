from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    git_sha,
    load_json,
    sha256_json,
    validate_and_expand_manifest,
)


def build_inventory(manifest_path: Path) -> dict[str, object]:
    manifest = load_json(manifest_path)
    test_ids, assignments, fast_ids = validate_and_expand_manifest(manifest)
    return {
        "schema_version": 1,
        "contract_type": "orrery-unittest-inventory",
        "sha": git_sha(),
        "python": platform.python_version(),
        "manifest_sha256": sha256_json(manifest),
        "test_count": len(test_ids),
        "test_ids": test_ids,
        "fast_test_count": len(fast_ids),
        "fast_test_ids": fast_ids,
        "shards": [
            {
                "id": shard["id"],
                "surface": shard["surface"],
                "test_count": len(assignments[shard["id"]]),
                "test_ids": assignments[shard["id"]],
            }
            for shard in manifest["shards"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover and validate final unittest shard inventory")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--shard-list", action="store_true", help="print the JSON shard-id array")
    arguments = parser.parse_args()
    try:
        inventory = build_inventory(arguments.manifest.resolve())
        if arguments.output:
            from _common import atomic_write_json

            atomic_write_json(arguments.output.resolve(), inventory)
        if arguments.shard_list:
            print(json.dumps([item["id"] for item in inventory["shards"]], separators=(",", ":")))
        else:
            print(
                f"PASS inventory: {inventory['test_count']} unique test IDs, "
                f"{len(inventory['shards'])} shards, {inventory['fast_test_count']} Fast tests"
            )
        return 0
    except CIValidationError as exc:
        print(f"FAIL inventory: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
