from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).with_name("test-shards.json")
DEFAULT_MAPPING_REGISTRY = Path(__file__).with_name("change-mapping.json")
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


def mapping_registry_path(manifest: dict[str, Any], root: Path = ROOT) -> Path:
    value = manifest.get("mapping_registry")
    if value != "scripts/ci/change-mapping.json":
        raise CIValidationError("manifest mapping_registry must name scripts/ci/change-mapping.json")
    return root / value


def load_mapping_registry(manifest: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    return load_json(mapping_registry_path(manifest, root))


def validate_manifest_shape(manifest: dict[str, Any], root: Path = ROOT) -> None:
    if set(manifest) != {
        "schema_version",
        "mapping_registry",
        "discovery",
        "promotion_lanes",
        "shards",
    }:
        raise CIValidationError(
            "manifest must contain only schema_version, mapping_registry, discovery, promotion_lanes, and shards"
        )
    if manifest["schema_version"] != 5:
        raise CIValidationError("unsupported shard manifest schema_version")
    mapping_registry_path(manifest, root)
    discovery = manifest["discovery"]
    if not isinstance(discovery, dict) or set(discovery) != {"start_dir", "pattern"}:
        raise CIValidationError("discovery must contain exactly start_dir and pattern")
    if discovery["start_dir"] != "tests" or discovery["pattern"] != "test_*.py":
        raise CIValidationError("promotion discovery must remain final unittest discovery over tests/test_*.py")
    shards = manifest["shards"]
    if not isinstance(shards, list) or not shards:
        raise CIValidationError("manifest shards must be a non-empty array")
    shard_ids: set[str] = set()
    surfaces: set[str] = set()
    for shard in shards:
        if not isinstance(shard, dict) or set(shard) not in (
            {"id", "surface"}, {"id", "surface", "budget_seconds"},
        ):
            raise CIValidationError(
                "each shard must contain id, surface, and optional budget_seconds"
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
    if len(workspace_shards) < 2:
        raise CIValidationError("Workspace Maintenance must be split by test method across multiple shards")
    _validate_promotion_lanes(manifest["promotion_lanes"], shard_ids)


def validate_mapping_registry(registry: dict[str, Any], shard_surfaces: dict[str, str]) -> None:
    expected = {"schema_version", "contract_type", "runner_version", "stages", "path_mappings", "tests", "reuse"}
    if set(registry) != expected:
        raise CIValidationError(f"mapping registry must contain exactly {sorted(expected)}")
    if registry["schema_version"] != 1 or registry["contract_type"] != "orrery-change-mapping-registry-v1":
        raise CIValidationError("unsupported change mapping registry")
    if registry["runner_version"] != "ci6-v2":
        raise CIValidationError("unsupported generic router version")
    stages = registry["stages"]
    if not isinstance(stages, dict) or set(stages) != {"fast", "checkpoint", "candidate"}:
        raise CIValidationError("registry stages must be exactly fast, checkpoint, and candidate")
    for stage, value in stages.items():
        if not isinstance(value, dict) or set(value) != {"role", "budget_seconds"}:
            raise CIValidationError(f"registry stage {stage} must contain role and budget_seconds")
        if not isinstance(value["role"], str) or not value["role"]:
            raise CIValidationError(f"registry stage {stage} has an invalid role")
        if not isinstance(value["budget_seconds"], (int, float)) or isinstance(value["budget_seconds"], bool) or value["budget_seconds"] <= 0:
            raise CIValidationError(f"registry stage {stage} budget_seconds must be positive")
    mappings = registry["path_mappings"]
    if not isinstance(mappings, list) or not mappings:
        raise CIValidationError("mapping registry path_mappings must be a non-empty array")
    mapping_ids: set[str] = set()
    for mapping in mappings:
        required = {"id", "patterns", "subsystems", "surfaces", "high_risk"}
        if not isinstance(mapping, dict) or set(mapping) != required:
            raise CIValidationError(f"path mapping must contain exactly {sorted(required)}")
        mapping_id = mapping["id"]
        if not isinstance(mapping_id, str) or not SHARD_ID_RE.fullmatch(mapping_id) or mapping_id in mapping_ids:
            raise CIValidationError(f"invalid or duplicate path mapping id: {mapping_id!r}")
        mapping_ids.add(mapping_id)
        for field in ("patterns", "subsystems", "surfaces"):
            values = mapping[field]
            if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
                raise CIValidationError(f"path mapping {mapping_id} has invalid {field}")
        if not isinstance(mapping["high_risk"], bool):
            raise CIValidationError(f"path mapping {mapping_id} high_risk must be boolean")
    entries = registry["tests"]
    if not isinstance(entries, list) or not entries:
        raise CIValidationError("mapping registry tests must be a non-empty exact-ID array")
    registered: set[str] = set()
    required_test = {"test_id", "owner_surface", "owner_shard", "allowed_stages", "cost_class", "budget_seconds", "dependencies", "reason"}
    stage_order = ["fast", "checkpoint", "candidate", "promotion"]
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != required_test:
            raise CIValidationError(f"test registry entry must contain exactly {sorted(required_test)}")
        test_id = entry["test_id"]
        if not isinstance(test_id, str) or not test_id or any(token in test_id for token in ("*", "?", "[")):
            raise CIValidationError(f"test registry requires an exact final ID: {test_id!r}")
        if test_id in registered:
            raise CIValidationError(f"duplicate registered test ID: {test_id}")
        registered.add(test_id)
        shard = entry["owner_shard"]
        if shard not in shard_surfaces or entry["owner_surface"] != shard_surfaces[shard]:
            raise CIValidationError(f"registered test owner shard/surface mismatch: {test_id}")
        allowed = entry["allowed_stages"]
        if not isinstance(allowed, list) or not allowed or allowed != [item for item in stage_order if item in allowed] or len(allowed) != len(set(allowed)) or "promotion" not in allowed:
            raise CIValidationError(f"registered test has invalid allowed_stages: {test_id}")
        cost = entry["cost_class"]
        if cost not in {"low", "medium", "heavy"}:
            raise CIValidationError(f"registered test has invalid cost_class: {test_id}")
        if cost == "heavy" and any(stage in allowed for stage in ("fast", "checkpoint", "candidate")):
            raise CIValidationError(f"heavy registered test entered a local lower stage: {test_id}")
        if not isinstance(entry["budget_seconds"], (int, float)) or isinstance(entry["budget_seconds"], bool) or entry["budget_seconds"] <= 0:
            raise CIValidationError(f"registered test has invalid budget_seconds: {test_id}")
        deps = entry["dependencies"]
        if not isinstance(deps, list) or not deps or len(deps) != len(set(deps)) or any(not isinstance(item, str) or not item for item in deps):
            raise CIValidationError(f"registered test must declare unique dependencies: {test_id}")
        unknown = sorted(set(deps) - mapping_ids)
        if unknown:
            raise CIValidationError(
                f"registered test has Unknown dependencies {unknown}: {test_id}; add path_mappings metadata or correct dependencies"
            )
        if not isinstance(entry["reason"], str) or not entry["reason"]:
            raise CIValidationError(f"registered test requires a dependency reason: {test_id}")
    reuse = registry["reuse"]
    required_reuse = {"schema_version", "mode", "environment_gates", "security_high_risk_mappings"}
    if not isinstance(reuse, dict) or set(reuse) != required_reuse or reuse["schema_version"] != 1 or reuse["mode"] != "contract-refusal":
        raise CIValidationError("registry reuse contract must remain contract-refusal v1")
    if any(item not in mapping_ids for item in reuse["security_high_risk_mappings"]):
        raise CIValidationError("reuse security_high_risk_mappings contains an Unknown mapping")


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


def discover_test_ids(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    validate_manifest_shape(manifest, root)
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


def validate_and_expand_manifest(
    manifest: dict[str, Any], root: Path = ROOT
) -> tuple[list[str], dict[str, list[str]], list[str]]:
    test_ids = discover_test_ids(manifest, root)
    shard_surfaces = {str(shard["id"]): str(shard["surface"]) for shard in manifest["shards"]}
    registry = load_mapping_registry(manifest, root)
    validate_mapping_registry(registry, shard_surfaces)
    registered = {str(entry["test_id"]): entry for entry in registry["tests"]}
    missing = sorted(set(test_ids) - set(registered))
    extra = sorted(set(registered) - set(test_ids))
    if missing or extra:
        raise CIValidationError(
            "exact test registry differs from final discovery; "
            f"unregistered={missing}, stale={extra}. Add one tests entry with owner_surface, owner_shard, "
            "allowed_stages, cost_class, budget_seconds, dependencies, and reason for every new test."
        )
    assignments = {shard_id: [] for shard_id in shard_surfaces}
    for test_id in test_ids:
        assignments[str(registered[test_id]["owner_shard"])].append(test_id)
    empty = sorted(shard_id for shard_id, values in assignments.items() if not values)
    if empty:
        raise CIValidationError(f"Promotion shards lost all exact-ID owners: {empty}")
    fast_ids = sorted(
        test_id for test_id, entry in registered.items() if "fast" in entry["allowed_stages"]
    )
    checkpoint_ids = sorted(
        test_id for test_id, entry in registered.items() if "checkpoint" in entry["allowed_stages"]
    )
    if not set(fast_ids).issubset(checkpoint_ids):
        raise CIValidationError("Checkpoint must include every Fast test")
    return test_ids, assignments, fast_ids


def expand_profile(manifest: dict[str, Any], profile: str, test_ids: list[str]) -> list[str]:
    validate_manifest_shape(manifest)
    if profile not in {"fast", "checkpoint"}:
        raise CIValidationError(f"unsupported profile: {profile}")
    registry = load_mapping_registry(manifest)
    registered = {entry["test_id"]: entry for entry in registry["tests"]}
    return sorted(
        test_id for test_id in test_ids if profile in registered[test_id]["allowed_stages"]
    )


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


def git_output(arguments: list[str], root: Path = ROOT, *, text: bool = True) -> str | bytes:
    result = subprocess.run(["git", *arguments], cwd=root, text=text, capture_output=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() if text else result.stderr.decode("utf-8", errors="replace").strip()
        raise CIValidationError(f"git {' '.join(arguments)} failed: {stderr}")
    return result.stdout


def dirty_fingerprint(root: Path = ROOT) -> str:
    status = git_output(["status", "--porcelain=v2", "-z", "--untracked-files=all"], root, text=False)
    assert isinstance(status, bytes)
    digest = hashlib.sha256(status)
    paths = git_output(
        ["ls-files", "--modified", "--deleted", "--others", "--exclude-standard", "-z"],
        root,
        text=False,
    )
    assert isinstance(paths, bytes)
    for raw in sorted(item for item in paths.split(b"\0") if item):
        digest.update(raw + b"\0")
        path = root / raw.decode("utf-8", errors="surrogateescape")
        if path.is_file():
            try:
                digest.update(path.read_bytes())
            except OSError as exc:
                digest.update(f"unreadable:{exc}".encode("utf-8", errors="replace"))
        else:
            digest.update(b"missing")
    return digest.hexdigest()


def machine_inventory(manifest: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    test_ids, _, _ = validate_and_expand_manifest(manifest, root)
    registry = load_mapping_registry(manifest, root)
    by_id = {entry["test_id"]: entry for entry in registry["tests"]}
    entries = [dict(by_id[test_id]) for test_id in test_ids]
    return {
        "schema_version": 4,
        "contract_type": "orrery-unittest-inventory-v4",
        "manifest_sha256": sha256_json(manifest),
        "mapping_registry_sha256": sha256_json(registry),
        "inventory_sha256": sha256_json(entries),
        "test_count": len(entries),
        "tests": entries,
        "generated_on": {"os": platform.system(), "python": platform.python_version()},
    }
