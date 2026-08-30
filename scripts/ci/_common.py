from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
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
ACCEPTANCE_POLICY_VERSION = 1
ACCEPTANCE_GATE_KINDS = {
    "human_experience",
    "contract",
    "measurement",
    "operation_authorization",
    "platform_matrix",
}
ACCEPTANCE_GATE_STATUSES = {
    "proposed", "ready", "accepted", "rejected", "stale", "unknown",
}
HUMAN_ONLY_GATE_KINDS = {"human_experience", "operation_authorization"}
PREDICTIVE_LIMITS = {
    "fast": {"selected_count": 20, "total_p95_seconds": 10.0},
    "checkpoint": {"single_p95_seconds": 30.0, "total_p95_seconds": 60.0},
    "iterating": {
        "selected_count": 20,
        "run_seconds": 20.0,
        "cumulative_seconds_per_scope_revision": 120.0,
    },
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


def git_private_ci_path(name: str, root: Path = ROOT) -> Path:
    """Resolve one CI-private record without projecting evidence into the repository."""
    raw = str(git_output(["rev-parse", "--path-format=absolute", "--git-path", "orrery/ci-validation"], root)).strip()
    return Path(raw) / name


def _safe_repository_path(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or value.startswith(("/", "\\")):
        raise CIValidationError(f"{field} must be a non-empty repository-relative path")
    normalized = value.replace("\\", "/")
    if ".." in Path(normalized).parts:
        raise CIValidationError(f"{field} escapes the repository")
    return normalized


def validate_contract_ref(value: Any, root: Path = ROOT) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "blob_oid"}:
        raise CIValidationError("acceptance gate contract_ref must contain exact path and blob_oid")
    path = _safe_repository_path(value["path"], field="contract_ref.path")
    blob = value["blob_oid"]
    if not isinstance(blob, str) or not re.fullmatch(r"[0-9a-f]{40}", blob):
        raise CIValidationError("acceptance gate contract_ref blob_oid must be a full lowercase Git OID")
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{blob}^{{blob}}"], cwd=root,
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise CIValidationError("acceptance gate contract_ref blob_oid is missing or forged")
    return {"path": path, "blob_oid": blob}


def validate_acceptance_policy(policy: dict[str, Any], *, session: dict[str, Any] | None = None) -> dict[str, Any]:
    required = {
        "schema_version", "contract_type", "rollout_mode", "workstream_id",
        "scope_revision", "composition", "acceptance_gates",
    }
    if set(policy) != required:
        raise CIValidationError(f"acceptance_policy fields differ from v1: {sorted(set(policy) ^ required)}")
    if policy["schema_version"] != ACCEPTANCE_POLICY_VERSION or policy["contract_type"] != "orrery-acceptance-policy-v1":
        raise CIValidationError("unsupported acceptance_policy schema or contract type")
    if policy["rollout_mode"] not in {"shadow", "new-workstreams-enforced", "explicit-legacy-adoption"}:
        raise CIValidationError("unknown acceptance_policy rollout_mode")
    if policy["composition"] != "all_of":
        raise CIValidationError("acceptance_policy v1 supports all_of only")
    if not isinstance(policy["workstream_id"], str) or not policy["workstream_id"]:
        raise CIValidationError("acceptance_policy requires a stable workstream_id")
    if not isinstance(policy["scope_revision"], int) or isinstance(policy["scope_revision"], bool) or policy["scope_revision"] < 1:
        raise CIValidationError("acceptance_policy scope_revision must be a positive integer")
    if session is not None:
        if policy["workstream_id"] != session.get("workstream_id"):
            raise CIValidationError("acceptance_policy workstream binding mismatch")
        if policy["scope_revision"] != session.get("scope_revision"):
            raise CIValidationError("acceptance_policy scope revision is stale")
    gates = policy["acceptance_gates"]
    if not isinstance(gates, list) or not gates:
        raise CIValidationError("opt-in acceptance_policy requires at least one gate")
    ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    gate_fields = {
        "id", "kind", "required_before", "authority_role", "contract_ref",
        "surface_ids", "status", "evidence_requirements", "receipt_ref",
    }
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != gate_fields:
            raise CIValidationError("each acceptance gate must contain the exact v1 fields")
        gate_id = gate["id"]
        if not isinstance(gate_id, str) or not SHARD_ID_RE.fullmatch(gate_id) or gate_id in ids:
            raise CIValidationError("acceptance gate ids must be stable, unique kebab-case ids")
        ids.add(gate_id)
        if gate["required_before"] not in {"focused", "fast", "checkpoint", "candidate", "promotion"}:
            raise CIValidationError("acceptance gate required_before names an unknown stage")
        if not isinstance(gate["authority_role"], str) or not gate["authority_role"]:
            raise CIValidationError("acceptance gate authority_role is required")
        if not isinstance(gate["surface_ids"], list) or not gate["surface_ids"] or any(
            not isinstance(item, str) or not item for item in gate["surface_ids"]
        ) or len(set(gate["surface_ids"])) != len(gate["surface_ids"]):
            raise CIValidationError("acceptance gate surface_ids must be unique non-empty strings")
        if not isinstance(gate["evidence_requirements"], list) or not gate["evidence_requirements"] or any(
            not isinstance(item, str) or not item for item in gate["evidence_requirements"]
        ):
            raise CIValidationError("acceptance gate evidence_requirements must be non-empty strings")
        if gate["receipt_ref"] is not None and not isinstance(gate["receipt_ref"], dict):
            raise CIValidationError("acceptance gate receipt_ref must be null or a reference object")
        item = dict(gate)
        item["contract_ref"] = validate_contract_ref(gate["contract_ref"])
        item["surface_ids"] = sorted(gate["surface_ids"])
        item["recognized_kind"] = gate["kind"] in ACCEPTANCE_GATE_KINDS
        item["recognized_status"] = gate["status"] in ACCEPTANCE_GATE_STATUSES
        normalized.append(item)
    if policy["rollout_mode"] == "explicit-legacy-adoption" and not any(
        gate["kind"] in HUMAN_ONLY_GATE_KINDS and gate["status"] == "accepted"
        for gate in normalized
    ):
        raise CIValidationError("explicit legacy adoption requires a human-reviewed accepted mapping gate")
    return {**policy, "acceptance_gates": normalized}


def _load_receipt_reference(reference: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    if set(reference) != {"path", "sha256"}:
        raise CIValidationError("acceptance receipt_ref must contain exact path and sha256")
    path = Path(str(reference["path"])).expanduser()
    if not path.is_absolute():
        path = root / _safe_repository_path(str(reference["path"]), field="receipt_ref.path")
    if not path.is_file():
        raise CIValidationError("acceptance receipt_ref is missing")
    raw = path.read_bytes()
    expected = reference["sha256"]
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise CIValidationError("acceptance receipt_ref sha256 is invalid")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise CIValidationError("acceptance receipt_ref hash mismatch")
    return load_json(path)


def acceptance_surface_fingerprint(
    *, policy: dict[str, Any], mapping_registry_sha256: str,
    relevant_paths: list[str], root: Path = ROOT,
) -> str:
    normalized = validate_acceptance_policy(policy)
    path_bindings: list[dict[str, str]] = []
    for relative in sorted(set(relevant_paths)):
        value = _safe_repository_path(relative, field="relevant surface path")
        path = root / value
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
        path_bindings.append({"path": value, "sha256": digest})
    contracts = sorted(
        (gate["contract_ref"] for gate in normalized["acceptance_gates"]),
        key=lambda item: (item["path"], item["blob_oid"]),
    )
    return sha256_json({
        "schema_version": 1,
        "contract_refs": contracts,
        "mapping_registry_sha256": mapping_registry_sha256,
        "relevant_paths": path_bindings,
    })


def evaluate_acceptance_policy(
    policy: dict[str, Any] | None, *, requested_stage: str,
    session: dict[str, Any] | None, surface_fingerprint: str | None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if policy is None:
        return {
            "schema_version": 1, "classification": "legacy-unclassified",
            "rollout_mode": "shadow", "decision": "shadow-allow",
            "requested_stage": requested_stage, "gate_results": [],
            "human_authority_required": False,
        }
    normalized = validate_acceptance_policy(policy, session=session)
    stage_order = {"focused": 0, "fast": 1, "checkpoint": 2, "candidate": 3, "promotion": 4}
    if requested_stage not in stage_order:
        raise CIValidationError("acceptance evaluation requested an unknown stage")
    results: list[dict[str, Any]] = []
    for gate in normalized["acceptance_gates"]:
        if stage_order[gate["required_before"]] > stage_order[requested_stage]:
            continue
        result = {"id": gate["id"], "kind": gate["kind"], "status": "unknown", "satisfied": False}
        if not gate["recognized_kind"] or not gate["recognized_status"]:
            result["reason"] = "unknown-kind-or-status"
        elif gate["status"] != "accepted":
            result.update({"status": gate["status"], "reason": "gate-not-accepted"})
        elif gate["receipt_ref"] is None:
            result["reason"] = "accepted-gate-missing-receipt"
        else:
            receipt = _load_receipt_reference(gate["receipt_ref"], root)
            binding_ok = (
                receipt.get("workstream_id") == normalized["workstream_id"]
                and receipt.get("scope_revision") == normalized["scope_revision"]
                and receipt.get("gate_id") == gate["id"]
                and receipt.get("contract_ref") == gate["contract_ref"]
                and receipt.get("authority_role") == gate["authority_role"]
                and receipt.get("decision") == "accepted"
                and isinstance(receipt.get("actor_id"), str)
                and isinstance(receipt.get("revision"), int)
                and receipt.get("revision", 0) > 0
                and receipt.get("expected_scope_revision") == normalized["scope_revision"]
            )
            fingerprint_ok = receipt.get("surface_fingerprint") == surface_fingerprint
            if gate["kind"] in HUMAN_ONLY_GATE_KINDS:
                authority_ok = receipt.get("actor_type") == "human"
                if gate["kind"] == "operation_authorization":
                    authority_ok = authority_ok and receipt.get("action_time_authorized") is True
            else:
                approval = receipt.get("contract_approval")
                authority_ok = (
                    receipt.get("actor_type") == "mechanical"
                    and isinstance(approval, dict)
                    and approval.get("actor_type") == "human"
                    and approval.get("decision") == "accepted"
                    and approval.get("contract_ref") == gate["contract_ref"]
                )
                if gate["kind"] == "contract":
                    authority_ok = authority_ok and receipt.get("contract_result") == "pass"
                elif gate["kind"] == "measurement":
                    authority_ok = authority_ok and receipt.get("threshold_result") == "pass"
                elif gate["kind"] == "platform_matrix":
                    authority_ok = authority_ok and receipt.get("platform_results") == {
                        "windows-latest": "pass", "ubuntu-latest": "pass",
                    }
            if binding_ok and fingerprint_ok and authority_ok:
                result.update({"status": "accepted", "satisfied": True, "reason": "receipt-verified"})
            else:
                result["reason"] = "receipt-authority-binding-or-fingerprint-mismatch"
        results.append(result)
    satisfied = all(item["satisfied"] for item in results)
    decision = "allow" if satisfied else "refuse"
    return {
        "schema_version": 1,
        "classification": "declared-policy",
        "rollout_mode": normalized["rollout_mode"],
        "decision": decision,
        "requested_stage": requested_stage,
        "gate_results": results,
        "human_authority_required": any(
            gate["kind"] in HUMAN_ONLY_GATE_KINDS
            and stage_order[gate["required_before"]] <= stage_order[requested_stage]
            for gate in normalized["acceptance_gates"]
        ),
    }


def enforce_acceptance_rollout(
    policy: dict[str, Any] | None, *, session: dict[str, Any] | None,
    enforcement: dict[str, Any] | None,
) -> str:
    """Classify shadow/new-task/explicit-adoption without rewriting legacy session bytes."""
    if enforcement is None:
        return "legacy-shadow"
    if (
        enforcement.get("schema_version") != 1
        or enforcement.get("contract_type") != "orrery-acceptance-enforcement-v1"
        or enforcement.get("mode") not in {"shadow", "new-workstreams-enforced", "explicit-legacy-adoption"}
        or not isinstance(enforcement.get("activated_at"), str)
        or enforcement.get("human_decision") != "accepted"
    ):
        raise CIValidationError("acceptance enforcement record is missing human authority or has an unknown mode")
    mode = enforcement["mode"]
    if mode == "shadow":
        return "legacy-shadow" if policy is None else "declared-shadow"
    captured = session.get("captured_at") if isinstance(session, dict) else None
    is_new = isinstance(captured, str) and captured >= enforcement["activated_at"]
    if mode == "new-workstreams-enforced" and is_new and policy is None:
        raise CIValidationError("new Workstream created after opt-in enforcement must declare acceptance gates")
    if mode == "explicit-legacy-adoption" and not is_new:
        if policy is None or policy.get("rollout_mode") != "explicit-legacy-adoption":
            raise CIValidationError("legacy Workstream adoption requires a human-reviewed explicit mapping")
    return "enforced" if policy is not None else "legacy-shadow"


def project_team_acceptance_metadata(policy: dict[str, Any] | None) -> dict[str, Any]:
    """Project bounded request-only metadata; never evidence bodies or source/diff content."""
    if policy is None:
        return {"schema_version": 1, "classification": "legacy-unclassified", "gates": []}
    normalized = validate_acceptance_policy(policy)
    return {
        "schema_version": 1,
        "classification": "declared-policy",
        "composition": "all_of",
        "gates": [{
            "id": gate["id"], "kind": gate["kind"],
            "required_before": gate["required_before"],
            "authority_role": gate["authority_role"],
            "surface_ids": gate["surface_ids"], "status": gate["status"],
        } for gate in normalized["acceptance_gates"]],
        "execution_capability": "request-only",
        "network_default": "personal-zero-network",
    }


def validate_review_package(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "contract_type", "purpose", "invariants", "representative_cases",
        "negative_cases", "known_gaps", "contract_ref", "surface_fingerprint", "reproduction_ref",
    }
    if set(value) != required or value.get("schema_version") != 1 or value.get("contract_type") != "orrery-acceptance-review-package-v1":
        raise CIValidationError("review package differs from bounded v1 contract")
    cases = value["representative_cases"]
    if not isinstance(value["purpose"], str) or not value["purpose"]:
        raise CIValidationError("review package purpose is required")
    if not isinstance(value["invariants"], list) or not value["invariants"]:
        raise CIValidationError("review package invariants are required")
    if not isinstance(cases, list) or not 3 <= len(cases) <= 5:
        raise CIValidationError("review package requires 3-5 representative cases")
    if not isinstance(value["negative_cases"], list) or not value["negative_cases"]:
        raise CIValidationError("review package requires negative cases")
    if not isinstance(value["known_gaps"], list):
        raise CIValidationError("review package known_gaps must be a list")
    if not isinstance(value["reproduction_ref"], str) or not value["reproduction_ref"]:
        raise CIValidationError("review package reproduction_ref is required")
    validate_contract_ref(value["contract_ref"])
    if not isinstance(value["surface_fingerprint"], str) or not re.fullmatch(r"[0-9a-f]{64}", value["surface_fingerprint"]):
        raise CIValidationError("review package surface_fingerprint is invalid")
    return value


def timing_prediction(
    test_ids: list[str], *, stage: str, environment_key: str,
    router_setup_p95_seconds: float = 0.0, history: dict[str, Any] | None = None,
) -> dict[str, Any]:
    history = history or {"tests": {}}
    durations: list[float] = []
    unknown: list[str] = []
    for test_id in test_ids:
        item = history.get("tests", {}).get(f"{environment_key}:{test_id}")
        if not isinstance(item, dict) or not isinstance(item.get("p95_seconds"), (int, float)):
            unknown.append(test_id)
        else:
            durations.append(float(item["p95_seconds"]))
    predicted = round(router_setup_p95_seconds + sum(durations), 6) if not unknown else "Unknown"
    single = round(max(durations), 6) if durations and not unknown else "Unknown"
    reasons: list[str] = []
    if stage == "fast":
        if len(test_ids) > PREDICTIVE_LIMITS["fast"]["selected_count"]:
            reasons.append("fast-selected-count-exceeds-20")
        if predicted == "Unknown":
            reasons.append("timing-history-unknown-conservative-refusal")
        elif predicted > PREDICTIVE_LIMITS["fast"]["total_p95_seconds"]:
            reasons.append("fast-predicted-p95-exceeds-10-seconds")
    elif stage == "checkpoint":
        if predicted == "Unknown":
            reasons.append("timing-history-unknown-conservative-refusal")
        else:
            if single > PREDICTIVE_LIMITS["checkpoint"]["single_p95_seconds"]:
                reasons.append("checkpoint-single-test-p95-exceeds-30-seconds")
            if predicted > PREDICTIVE_LIMITS["checkpoint"]["total_p95_seconds"]:
                reasons.append("checkpoint-total-p95-exceeds-60-seconds")
    return {
        "schema_version": 1, "environment_key": environment_key,
        "selected_count": len(test_ids), "predicted_total_p95_seconds": predicted,
        "predicted_single_test_p95_seconds": single, "unknown_test_ids": unknown,
        "router_setup_p95_seconds": router_setup_p95_seconds,
        "setup_build_p95_seconds": router_setup_p95_seconds,
        "decision": "refuse" if reasons else "allow", "reasons": reasons,
    }


def update_timing_summary(
    receipt: dict[str, Any], *, environment_key: str, root: Path = ROOT,
) -> dict[str, Any]:
    if receipt.get("successful") is not True or receipt.get("evidence_eligible") is not True:
        raise CIValidationError("only valid successful receipts may update timing summaries")
    path = git_private_ci_path("timing-summaries-v1.json", root)
    value: dict[str, Any] = {
        "schema_version": 1, "contract_type": "orrery-local-timing-summaries-v1", "tests": {},
        "router_setup_p95_seconds": {},
    }
    if path.is_file():
        value = load_json(path)
        if value.get("contract_type") != "orrery-local-timing-summaries-v1" or value.get("schema_version") != 1:
            raise CIValidationError("unsupported local timing summary")
    for record in receipt.get("records", []):
        if not isinstance(record, dict) or not isinstance(record.get("duration_seconds"), (int, float)):
            continue
        key = f"{environment_key}:{record['test_id']}"
        samples = list(value["tests"].get(key, {}).get("samples", []))[-19:]
        samples.append(float(record["duration_seconds"]))
        ordered = sorted(samples)
        index = max(0, math.ceil(0.95 * len(ordered)) - 1)
        value["tests"][key] = {"samples": samples, "p95_seconds": round(ordered[index], 6)}
    setup = receipt.get("cost_diagnostics", {}).get(
        "total_setup_build_wall_seconds",
        receipt.get("cost_diagnostics", {}).get("router_setup_wall_seconds"),
    )
    if isinstance(setup, (int, float)):
        samples = list(value["router_setup_p95_seconds"].get(environment_key, {}).get("samples", []))[-19:]
        samples.append(float(setup))
        ordered = sorted(samples)
        value["router_setup_p95_seconds"][environment_key] = {
            "samples": samples, "p95_seconds": round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 6),
        }
    atomic_write_json(path, value)
    return value


def _lease_ledger(root: Path = ROOT) -> tuple[Path, dict[str, Any]]:
    path = git_private_ci_path("validation-leases-v1.json", root)
    value: dict[str, Any] = {
        "schema_version": 1,
        "contract_type": "orrery-validation-lease-ledger-v1",
        "leases": {},
        "iteration_cost_seconds": {},
    }
    if path.is_file():
        value = load_json(path)
        if value.get("schema_version") != 1 or value.get("contract_type") != "orrery-validation-lease-ledger-v1":
            raise CIValidationError("unsupported validation lease ledger")
    return path, value


def _validate_human_override(value: dict[str, Any] | None, *, request_key: str) -> bool:
    if value is None:
        return False
    return (
        set(value) == {
            "schema_version", "contract_type", "actor_type", "actor_id", "authority_role",
            "decision", "request_key", "expected_lease_status", "revision",
            "previous_receipt_sha256",
        }
        and
        value.get("schema_version") == 1
        and value.get("contract_type") == "orrery-validation-rerun-override-v1"
        and value.get("actor_type") == "human"
        and value.get("authority_role") == "maintainer"
        and isinstance(value.get("actor_id"), str) and bool(value.get("actor_id"))
        and value.get("decision") == "authorized"
        and value.get("request_key") == request_key
        and value.get("expected_lease_status") == "validation-cost-blocked"
        and isinstance(value.get("revision"), int) and value.get("revision") > 0
        and isinstance(value.get("previous_receipt_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", value.get("previous_receipt_sha256", "")))
    )


def issue_validation_lease(
    plan: dict[str, Any], *, acceptance: dict[str, Any], prediction: dict[str, Any],
    scope_revision: int, surface_fingerprint: str, receipt_inputs: list[str],
    human_override: dict[str, Any] | None = None, task_phase: str = "validating",
    root: Path = ROOT,
) -> dict[str, Any]:
    if acceptance.get("decision") not in {"allow", "shadow-allow"}:
        raise CIValidationError("required acceptance gates are not satisfied for the requested stage")
    shadow = acceptance.get("decision") == "shadow-allow"
    if prediction.get("decision") != "allow" and not shadow:
        raise CIValidationError("predictive budget refusal: " + ", ".join(prediction.get("reasons", [])))
    workstream_id = plan.get("workstream", {}).get("workstream_id")
    if not isinstance(workstream_id, str) or not workstream_id:
        raise CIValidationError("validation lease requires a Git-private Workstream identity")
    identity = {
        "workstream_id": workstream_id, "scope_revision": scope_revision,
        "stage": plan["stage"], "surface_fingerprint": surface_fingerprint,
    }
    request_key = sha256_json(identity)
    path, ledger = _lease_ledger(root)
    previous = ledger["leases"].get(request_key)
    if isinstance(previous, dict) and not shadow:
        if previous.get("status") == "completed" and previous.get("receipt"):
            return {"decision": "reuse-prior-receipt", "request_key": request_key, "prior_receipt": previous["receipt"]}
        if previous.get("status") == "validation-cost-blocked" and not _validate_human_override(human_override, request_key=request_key):
            raise CIValidationError("validation-cost-blocked; unchanged-source rerun requires a human override receipt")
        if previous.get("status") in {"issued", "consumed"}:
            raise CIValidationError("duplicate formal validation request already has an active one-run lease")
    if plan["stage"] == "focused" and task_phase != "iterating":
        raise CIValidationError("focused validation is debug-only and requires the iterating phase")
    if task_phase == "iterating":
        if plan["stage"] != "focused":
            raise CIValidationError("iterating permits focused validation only; Fast/Checkpoint remain locked")
        iteration_key = f"{workstream_id}:{scope_revision}"
        cumulative = float(ledger["iteration_cost_seconds"].get(iteration_key, 0.0))
        if len(plan["selected_test_ids"]) > 20 or prediction["predicted_total_p95_seconds"] == "Unknown" or float(prediction["predicted_total_p95_seconds"]) > 20:
            raise CIValidationError("iterating focused validation exceeds 20 tests or 20 seconds")
        if cumulative + float(prediction["predicted_total_p95_seconds"]) > 120:
            raise CIValidationError("iterating cumulative validation exceeds 120 seconds for this scope revision")
    run_identity = sha256_json({**identity, "selected_test_ids": plan["selected_test_ids"], "prediction": prediction})
    lease = {
        "schema_version": 1,
        "contract_type": "orrery-validation-lease-v1",
        **identity,
        "request_key": request_key,
        "run_identity": run_identity,
        "allowed_test_ids": plan["selected_test_ids"],
        "selected_count": len(plan["selected_test_ids"]),
        "predicted_p95": prediction,
        "budget_seconds": plan["budget_seconds"],
        "receipt_inputs": receipt_inputs,
        "acceptance_decision": acceptance["decision"],
        "enforcement": "shadow" if shadow else "enforced",
        "task_phase": task_phase,
        "override_authorized": _validate_human_override(human_override, request_key=request_key),
        "issued_at_epoch": time.time(),
        "expires_at_epoch": time.time() + 900.0,
    }
    lease["lease_id"] = sha256_json(lease)
    if not shadow:
        ledger["leases"][request_key] = {"status": "issued", "lease": lease}
        atomic_write_json(path, ledger)
    return {"decision": "issued", "request_key": request_key, "lease": lease}


def consume_validation_lease(plan: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    lease = plan.get("validation_lease")
    if not isinstance(lease, dict) or lease.get("contract_type") != "orrery-validation-lease-v1":
        raise CIValidationError("formal selection plan is missing a validation lease")
    expected_id = lease.get("lease_id")
    unsigned = {key: value for key, value in lease.items() if key != "lease_id"}
    if not isinstance(expected_id, str) or expected_id != sha256_json(unsigned):
        raise CIValidationError("validation lease is forged")
    if lease.get("stage") != plan.get("stage") or lease.get("allowed_test_ids") != plan.get("selected_test_ids"):
        raise CIValidationError("validation lease stage or allowed test IDs mismatch")
    if lease.get("surface_fingerprint") != plan.get("surface_fingerprint"):
        raise CIValidationError("validation lease surface fingerprint is stale")
    if lease.get("budget_seconds") != plan.get("budget_seconds"):
        raise CIValidationError("validation lease budget mismatch")
    if not isinstance(lease.get("expires_at_epoch"), (int, float)) or time.time() > float(lease["expires_at_epoch"]):
        raise CIValidationError("validation lease is expired")
    if lease.get("enforcement") == "shadow":
        return lease
    path, ledger = _lease_ledger(root)
    entry = ledger["leases"].get(lease.get("request_key"))
    if not isinstance(entry, dict) or entry.get("status") != "issued" or entry.get("lease") != lease:
        raise CIValidationError("validation lease is missing, expired, consumed, or superseded")
    entry["status"] = "consumed"
    atomic_write_json(path, ledger)
    return lease


def finalize_validation_lease(
    lease: dict[str, Any], receipt: dict[str, Any], *, root: Path = ROOT,
) -> None:
    if lease.get("enforcement") == "shadow":
        return
    path, ledger = _lease_ledger(root)
    entry = ledger["leases"].get(lease.get("request_key"))
    if not isinstance(entry, dict) or entry.get("status") != "consumed" or entry.get("lease") != lease:
        raise CIValidationError("cannot finalize a missing or unconsumed validation lease")
    successful = receipt.get("successful") is True and (
        receipt.get("evidence_eligible") is True
        or (lease.get("task_phase") == "iterating" and lease.get("stage") == "focused")
    )
    entry["status"] = "completed" if successful else "validation-cost-blocked"
    entry["receipt"] = {**receipt, "validation_lease_id": lease.get("lease_id")}
    if lease.get("task_phase") == "iterating":
        key = f"{lease['workstream_id']}:{lease['scope_revision']}"
        ledger["iteration_cost_seconds"][key] = round(
            float(ledger["iteration_cost_seconds"].get(key, 0.0))
            + float(receipt.get("duration_seconds", 0.0))
            + float(receipt.get("cost_diagnostics", {}).get(
                "total_setup_build_wall_seconds",
                receipt.get("cost_diagnostics", {}).get("router_setup_wall_seconds", 0.0),
            )), 6,
        )
    atomic_write_json(path, ledger)


def block_validation_lease(
    lease: dict[str, Any], receipt: dict[str, Any], *, root: Path = ROOT,
) -> None:
    if lease.get("enforcement") == "shadow":
        return
    path, ledger = _lease_ledger(root)
    entry = ledger["leases"].get(lease.get("request_key"))
    if (
        not isinstance(entry, dict)
        or entry.get("status") not in {"issued", "consumed"}
        or entry.get("lease") != lease
    ):
        raise CIValidationError("cannot block a missing, completed, or superseded validation lease")
    entry["status"] = "validation-cost-blocked"
    entry["receipt"] = {**receipt, "validation_lease_id": lease.get("lease_id")}
    atomic_write_json(path, ledger)
