from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).with_name("test-shards.json")
SHARD_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LANE_ID_RE = re.compile(r"^lane-[0-9]{2}$")
REQUIRED_SURFACES = {
    "Authority/Core",
    "W1-W2",
    "W3",
    "Team/LAN",
    "Workspace Maintenance",
    "Context Routing/Harness",
    "Packaging/Adapters/docsite",
    "Release/migration/restore",
}


class CIValidationError(RuntimeError):
    pass


@contextmanager
def repository_import_path(root: Path = ROOT):
    original_cwd = Path.cwd()
    additions = [str(root), str(root / "tests")]
    original_path = list(sys.path)
    os.chdir(root)
    for entry in reversed(additions):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    try:
        yield
    finally:
        os.chdir(original_cwd)
        sys.path[:] = original_path


def flatten_suite(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten_suite(item)
        else:
            yield item


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CIValidationError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CIValidationError(f"JSON root must be an object: {path}")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical_json_bytes(value))
    temporary.replace(path)


def validate_manifest_shape(manifest: dict[str, Any]) -> None:
    if set(manifest) != {
        "schema_version",
        "discovery",
        "fast",
        "checkpoint",
        "promotion_lanes",
        "shards",
    }:
        raise CIValidationError(
            "manifest must contain only schema_version, discovery, fast, checkpoint, "
            "promotion_lanes, and shards"
        )
    if manifest["schema_version"] != 3:
        raise CIValidationError("unsupported shard manifest schema_version")
    discovery = manifest["discovery"]
    if not isinstance(discovery, dict) or set(discovery) != {"start_dir", "pattern"}:
        raise CIValidationError("discovery must contain exactly start_dir and pattern")
    if discovery["start_dir"] != "tests" or discovery["pattern"] != "test_*.py":
        raise CIValidationError("promotion discovery must remain final unittest discovery over tests/test_*.py")
    for profile, expected_role in (
        ("fast", "non-promotion-feedback"),
        ("checkpoint", "non-promotion-checkpoint"),
    ):
        value = manifest[profile]
        if not isinstance(value, dict) or set(value) != {
            "role",
            "budget_seconds",
            "selectors",
        }:
            raise CIValidationError(
                f"{profile} must contain exactly role, budget_seconds, and selectors"
            )
        if value["role"] != expected_role:
            raise CIValidationError(f"{profile} profile has the wrong non-Promotion role")
        if (
            not isinstance(value["budget_seconds"], (int, float))
            or isinstance(value["budget_seconds"], bool)
            or value["budget_seconds"] <= 0
        ):
            raise CIValidationError(f"{profile} budget_seconds must be positive")
        _validate_selectors(value["selectors"], profile)
    shards = manifest["shards"]
    if not isinstance(shards, list) or not shards:
        raise CIValidationError("manifest shards must be a non-empty array")
    shard_ids: set[str] = set()
    surfaces: set[str] = set()
    for shard in shards:
        if not isinstance(shard, dict) or set(shard) not in (
            {"id", "surface", "selectors"},
            {"id", "surface", "selectors", "budget_seconds"},
        ):
            raise CIValidationError(
                "each shard must contain id, surface, selectors, and optional budget_seconds"
            )
        shard_id = shard["id"]
        if not isinstance(shard_id, str) or not SHARD_ID_RE.fullmatch(shard_id):
            raise CIValidationError(f"invalid shard id: {shard_id!r}")
        if shard_id in shard_ids:
            raise CIValidationError(f"duplicate shard id: {shard_id}")
        shard_ids.add(shard_id)
        if not isinstance(shard["surface"], str) or not shard["surface"]:
            raise CIValidationError(f"invalid surface for shard {shard_id}")
        surfaces.add(shard["surface"])
        _validate_selectors(shard["selectors"], f"shard {shard_id}")
        if "budget_seconds" in shard and (
            not isinstance(shard["budget_seconds"], (int, float))
            or isinstance(shard["budget_seconds"], bool)
            or shard["budget_seconds"] <= 0
        ):
            raise CIValidationError(f"shard {shard_id} budget_seconds must be positive")
    missing_surfaces = sorted(REQUIRED_SURFACES - surfaces)
    if missing_surfaces:
        raise CIValidationError(f"required promotion surfaces missing: {missing_surfaces}")
    workspace_shards = [item for item in shards if item["surface"] == "Workspace Maintenance"]
    if len(workspace_shards) < 2 or any("test_workspace_maintenance.*" in item["selectors"] for item in workspace_shards):
        raise CIValidationError("Workspace Maintenance must be split by test method across multiple shards")
    _validate_promotion_lanes(manifest["promotion_lanes"], shard_ids)


def _validate_promotion_lanes(lanes: Any, shard_ids: set[str]) -> None:
    if not isinstance(lanes, list) or not lanes:
        raise CIValidationError("promotion_lanes must be a non-empty array")
    if len(lanes) > 20:
        raise CIValidationError("promotion_lanes must fit the bounded hosted runner concurrency")
    lane_ids: set[str] = set()
    owner_by_shard: dict[str, str] = {}
    for lane in lanes:
        if not isinstance(lane, dict) or set(lane) != {"id", "shards"}:
            raise CIValidationError("each Promotion lane must contain exactly id and shards")
        lane_id = lane["id"]
        if not isinstance(lane_id, str) or not LANE_ID_RE.fullmatch(lane_id):
            raise CIValidationError(f"invalid Promotion lane id: {lane_id!r}")
        if lane_id in lane_ids:
            raise CIValidationError(f"duplicate Promotion lane id: {lane_id}")
        lane_ids.add(lane_id)
        members = lane["shards"]
        if not isinstance(members, list) or not members:
            raise CIValidationError(f"Promotion lane {lane_id} must contain at least one shard")
        if any(not isinstance(item, str) or not item for item in members):
            raise CIValidationError(f"Promotion lane {lane_id} contains an invalid shard id")
        if len(members) != len(set(members)):
            raise CIValidationError(f"Promotion lane {lane_id} contains duplicate shard ids")
        for shard_id in members:
            if shard_id not in shard_ids:
                raise CIValidationError(
                    f"Promotion lane {lane_id} references unknown shard {shard_id}"
                )
            previous = owner_by_shard.get(shard_id)
            if previous is not None:
                raise CIValidationError(
                    f"Promotion shard {shard_id} belongs to multiple lanes: {previous}, {lane_id}"
                )
            owner_by_shard[shard_id] = lane_id
    missing = sorted(shard_ids - set(owner_by_shard))
    extra = sorted(set(owner_by_shard) - shard_ids)
    if missing or extra:
        raise CIValidationError(
            f"Promotion lane assignment is incomplete; missing={missing}, extra={extra}"
        )
    heavy_lane = owner_by_shard.get("team-relations-execution")
    if heavy_lane is None:
        raise CIValidationError("team-relations-execution must belong to one Promotion lane")
    heavy_members = next(lane["shards"] for lane in lanes if lane["id"] == heavy_lane)
    if heavy_members != ["team-relations-execution"]:
        raise CIValidationError("team-relations-execution must remain isolated in its Promotion lane")


def promotion_lane_assignments(manifest: dict[str, Any]) -> dict[str, list[str]]:
    validate_manifest_shape(manifest)
    return {str(lane["id"]): list(lane["shards"]) for lane in manifest["promotion_lanes"]}


def _validate_selectors(selectors: Any, owner: str) -> None:
    if not isinstance(selectors, list) or not selectors:
        raise CIValidationError(f"{owner} selectors must be a non-empty array")
    if any(not isinstance(item, str) or not item for item in selectors):
        raise CIValidationError(f"{owner} contains an invalid selector")
    if len(selectors) != len(set(selectors)):
        raise CIValidationError(f"{owner} contains duplicate selectors")


def discover_test_ids(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    validate_manifest_shape(manifest)
    loader = unittest.TestLoader()
    with repository_import_path(root):
        suite = loader.discover(
            str(root / manifest["discovery"]["start_dir"]),
            pattern=manifest["discovery"]["pattern"],
        )
        ids = [test.id() for test in flatten_suite(suite)]
    if loader.errors:
        raise CIValidationError("unittest discovery errors:\n" + "\n".join(loader.errors))
    failed = sorted(test_id for test_id in ids if test_id.startswith("unittest.loader._FailedTest"))
    if failed:
        raise CIValidationError(f"unittest discovery produced failed tests: {failed}")
    duplicates = sorted({test_id for test_id in ids if ids.count(test_id) > 1})
    if duplicates:
        raise CIValidationError(f"duplicate discovered test IDs: {duplicates}")
    return sorted(ids)


def expand_selectors(selectors: list[str], test_ids: list[str], owner: str) -> list[str]:
    selected: list[str] = []
    claimed_by: dict[str, str] = {}
    for selector in selectors:
        matches = [test_id for test_id in test_ids if fnmatch.fnmatchcase(test_id, selector)]
        if not matches:
            raise CIValidationError(f"selector matched no final unittest ID ({owner}): {selector}")
        for test_id in matches:
            previous = claimed_by.get(test_id)
            if previous is not None:
                raise CIValidationError(
                    f"test ID selected more than once in {owner}: {test_id} ({previous!r}, {selector!r})"
                )
            claimed_by[test_id] = selector
            selected.append(test_id)
    return sorted(selected)


def validate_and_expand_manifest(
    manifest: dict[str, Any], root: Path = ROOT
) -> tuple[list[str], dict[str, list[str]], list[str]]:
    test_ids = discover_test_ids(manifest, root)
    assignments: dict[str, list[str]] = {}
    owner_by_test: dict[str, str] = {}
    for shard in manifest["shards"]:
        selected = expand_selectors(shard["selectors"], test_ids, f"shard {shard['id']}")
        assignments[shard["id"]] = selected
        for test_id in selected:
            previous = owner_by_test.get(test_id)
            if previous is not None:
                raise CIValidationError(
                    f"promotion test ID assigned to multiple shards: {test_id} ({previous}, {shard['id']})"
                )
            owner_by_test[test_id] = shard["id"]
    missing = sorted(set(test_ids) - set(owner_by_test))
    extra = sorted(set(owner_by_test) - set(test_ids))
    if missing or extra:
        raise CIValidationError(f"promotion assignment is incomplete; missing={missing}, extra={extra}")
    fast_ids = expand_selectors(manifest["fast"]["selectors"], test_ids, "fast profile")
    return test_ids, assignments, fast_ids


def expand_profile(manifest: dict[str, Any], profile: str, test_ids: list[str]) -> list[str]:
    validate_manifest_shape(manifest)
    if profile not in {"fast", "checkpoint"}:
        raise CIValidationError(f"unsupported profile: {profile}")
    return expand_selectors(manifest[profile]["selectors"], test_ids, f"{profile} profile")


def git_sha(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise CIValidationError(f"cannot resolve git HEAD: {result.stderr.strip()}")
    value = result.stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise CIValidationError(f"git HEAD is not a full SHA: {value!r}")
    return value
