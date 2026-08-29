from __future__ import annotations

import fnmatch
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
        "routing",
        "discovery",
        "fast",
        "checkpoint",
        "promotion_lanes",
        "shards",
    }:
        raise CIValidationError(
            "manifest must contain only schema_version, routing, discovery, fast, checkpoint, "
            "promotion_lanes, and shards"
        )
    if manifest["schema_version"] != 4:
        raise CIValidationError("unsupported shard manifest schema_version")
    _validate_routing_shape(manifest["routing"])
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


def _validate_routing_shape(routing: Any) -> None:
    expected = {
        "schema_version", "runner_version", "stages", "path_rules", "claim_sets", "reuse"
    }
    if not isinstance(routing, dict) or set(routing) != expected:
        raise CIValidationError(f"routing must contain exactly {sorted(expected)}")
    if routing["schema_version"] != 1 or routing["runner_version"] != "ci6-v1":
        raise CIValidationError("unsupported validation routing or runner version")
    stages = routing["stages"]
    if not isinstance(stages, dict) or set(stages) != {"fast", "checkpoint", "candidate"}:
        raise CIValidationError("routing stages must be exactly fast, checkpoint, and candidate")
    for stage, value in stages.items():
        if not isinstance(value, dict) or set(value) != {"role", "budget_seconds"}:
            raise CIValidationError(f"routing stage {stage} must contain role and budget_seconds")
        if not isinstance(value["role"], str) or not value["role"]:
            raise CIValidationError(f"routing stage {stage} has an invalid role")
        if (
            not isinstance(value["budget_seconds"], (int, float))
            or isinstance(value["budget_seconds"], bool)
            or value["budget_seconds"] <= 0
        ):
            raise CIValidationError(f"routing stage {stage} budget_seconds must be positive")
    rules = routing["path_rules"]
    if not isinstance(rules, list) or not rules:
        raise CIValidationError("routing path_rules must be a non-empty array")
    rule_ids: set[str] = set()
    for rule in rules:
        required = {"id", "patterns", "subsystems", "surfaces", "selectors", "reason", "high_risk"}
        if not isinstance(rule, dict) or set(rule) != required:
            raise CIValidationError(f"routing path rule must contain exactly {sorted(required)}")
        rule_id = rule["id"]
        if not isinstance(rule_id, str) or not SHARD_ID_RE.fullmatch(rule_id):
            raise CIValidationError(f"invalid routing rule id: {rule_id!r}")
        if rule_id in rule_ids:
            raise CIValidationError(f"duplicate routing rule id: {rule_id}")
        rule_ids.add(rule_id)
        for field in ("patterns", "subsystems", "surfaces"):
            values = rule[field]
            if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
                raise CIValidationError(f"routing rule {rule_id} has invalid {field}")
        selectors = rule["selectors"]
        if not isinstance(selectors, dict) or set(selectors) != {"fast", "checkpoint", "candidate"}:
            raise CIValidationError(f"routing rule {rule_id} selectors must cover all local stages")
        for stage, values in selectors.items():
            _validate_selectors(values, f"routing rule {rule_id} {stage}")
        if not isinstance(rule["reason"], str) or not rule["reason"]:
            raise CIValidationError(f"routing rule {rule_id} requires a dependency/adjacency reason")
        if not isinstance(rule["high_risk"], bool):
            raise CIValidationError(f"routing rule {rule_id} high_risk must be boolean")
    claims = routing["claim_sets"]
    if not isinstance(claims, list) or not claims:
        raise CIValidationError("routing claim_sets must be a non-empty array")
    claim_ids: set[str] = set()
    for claim in claims:
        required = {"id", "selectors", "promotion_only_selectors", "reason"}
        if not isinstance(claim, dict) or set(claim) != required:
            raise CIValidationError(f"routing claim set must contain exactly {sorted(required)}")
        claim_id = claim["id"]
        if not isinstance(claim_id, str) or not SHARD_ID_RE.fullmatch(claim_id) or claim_id in claim_ids:
            raise CIValidationError(f"invalid or duplicate routing claim set id: {claim_id!r}")
        claim_ids.add(claim_id)
        _validate_selectors(claim["selectors"], f"claim set {claim_id}")
        _validate_selectors(claim["promotion_only_selectors"], f"claim set {claim_id} Promotion-only")
        if not isinstance(claim["reason"], str) or not claim["reason"]:
            raise CIValidationError(f"claim set {claim_id} requires a reason")
    reuse = routing["reuse"]
    required_reuse = {"schema_version", "mode", "environment_gates", "security_high_risk_paths"}
    if not isinstance(reuse, dict) or set(reuse) != required_reuse:
        raise CIValidationError(f"routing reuse must contain exactly {sorted(required_reuse)}")
    if reuse["schema_version"] != 1 or reuse["mode"] != "contract-refusal":
        raise CIValidationError("CI6 reuse must remain the versioned contract-refusal mode")
    for field in ("environment_gates", "security_high_risk_paths"):
        if not isinstance(reuse[field], list) or not reuse[field] or any(
            not isinstance(item, str) or not item for item in reuse[field]
        ):
            raise CIValidationError(f"routing reuse {field} must be a non-empty string array")


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
    checkpoint_ids = expand_selectors(
        manifest["checkpoint"]["selectors"], test_ids, "checkpoint profile"
    )
    if not set(fast_ids).issubset(checkpoint_ids):
        raise CIValidationError("Checkpoint must include every Fast test")
    allowed_by_stage = {
        "fast": set(fast_ids),
        "checkpoint": set(checkpoint_ids),
        "candidate": set(checkpoint_ids),
    }
    for rule in manifest["routing"]["path_rules"]:
        for stage, selectors in rule["selectors"].items():
            selected = expand_selectors(selectors, test_ids, f"routing rule {rule['id']} {stage}")
            forbidden = sorted(set(selected) - allowed_by_stage[stage])
            if forbidden:
                raise CIValidationError(
                    f"heavy or disallowed test entered {stage} through routing rule {rule['id']}: {forbidden}"
                )
    lower_ids = set(checkpoint_ids)
    for claim in manifest["routing"]["claim_sets"]:
        claimed = set(expand_selectors(claim["selectors"], test_ids, f"claim set {claim['id']}"))
        promotion_only = set(
            expand_selectors(
                claim["promotion_only_selectors"], test_ids, f"claim set {claim['id']} Promotion-only"
            )
        )
        if not promotion_only.issubset(claimed):
            raise CIValidationError(f"claim set {claim['id']} Promotion-only IDs escape its claim set")
        leaked = sorted(promotion_only & lower_ids)
        if leaked:
            raise CIValidationError(
                f"Promotion-only claim entered Fast/Checkpoint for {claim['id']}: {leaked}"
            )
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
    test_ids, assignments, fast_ids = validate_and_expand_manifest(manifest, root)
    checkpoint_ids = expand_profile(manifest, "checkpoint", test_ids)
    fast = set(fast_ids)
    checkpoint = set(checkpoint_ids)
    owner_by_test = {
        test_id: (shard["id"], shard["surface"], shard.get("budget_seconds"))
        for shard in manifest["shards"]
        for test_id in assignments[shard["id"]]
    }
    reasons_by_test: dict[str, set[str]] = {test_id: set() for test_id in test_ids}
    for rule in manifest["routing"]["path_rules"]:
        for stage, selectors in rule["selectors"].items():
            for test_id in expand_selectors(selectors, test_ids, f"routing rule {rule['id']} {stage}"):
                reasons_by_test[test_id].add(f"{stage}:{rule['id']}:{rule['reason']}")
    promotion_only_claims: set[str] = set()
    for claim in manifest["routing"]["claim_sets"]:
        for test_id in expand_selectors(
            claim["promotion_only_selectors"], test_ids, f"claim set {claim['id']} Promotion-only"
        ):
            promotion_only_claims.add(test_id)
            reasons_by_test[test_id].add(f"promotion:{claim['id']}:{claim['reason']}")
    entries: list[dict[str, Any]] = []
    for test_id in test_ids:
        shard_id, surface, shard_budget = owner_by_test[test_id]
        if test_id in fast:
            allowed_stages = ["fast", "checkpoint", "candidate", "promotion"]
            cost_class = "low"
            budget = float(manifest["fast"]["budget_seconds"])
        elif test_id in checkpoint:
            allowed_stages = ["checkpoint", "candidate", "promotion"]
            cost_class = "medium"
            budget = float(manifest["checkpoint"]["budget_seconds"])
        else:
            allowed_stages = ["promotion"]
            cost_class = "heavy"
            budget = float(shard_budget or 600)
        reasons = sorted(reasons_by_test[test_id]) or [
            f"promotion:{shard_id}:complete final discovery ownership for {surface}"
        ]
        entries.append({
            "test_id": test_id,
            "owner_surface": surface,
            "owner_shard": shard_id,
            "allowed_stages": allowed_stages,
            "cost_class": cost_class,
            "budget_seconds": budget,
            "dependency_reasons": reasons,
            "promotion_only_claim": test_id in promotion_only_claims,
        })
    return {
        "schema_version": 3,
        "contract_type": "orrery-unittest-inventory-v3",
        "manifest_sha256": sha256_json(manifest),
        "inventory_sha256": sha256_json(entries),
        "test_count": len(entries),
        "tests": entries,
        "generated_on": {"os": platform.system(), "python": platform.python_version()},
    }
