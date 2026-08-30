from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    atomic_write_json,
    dirty_fingerprint,
    git_output,
    git_sha,
    load_json,
    load_mapping_registry,
    machine_inventory,
    sha256_json,
    validate_and_expand_manifest,
)


RUNNER = Path(__file__).with_name("run_test_shard.py")
RECEIPT_TYPE = "orrery-local-validation-receipt-v1"
REFUSAL_TYPE = "orrery-local-validation-refusal-v1"
PLAN_TYPE = "orrery-test-selection-plan-v1"
COST_DIAGNOSTICS_VERSION = 1


class SelectionRefused(CIValidationError):
    def __init__(self, message: str, required_metadata: list[str]) -> None:
        super().__init__(message)
        self.required_metadata = required_metadata


def _resolve_commit(value: str) -> str:
    resolved = str(git_output(["rev-parse", "--verify", f"{value}^{{commit}}"])).strip().lower()
    if len(resolved) != 40:
        raise CIValidationError(f"base did not resolve to an exact commit: {value}")
    return resolved


def _private_session() -> tuple[dict[str, Any] | None, str | None]:
    raw = str(git_output(["rev-parse", "--path-format=absolute", "--git-path", "orrery/worktree.json"])).strip()
    path = Path(raw)
    if not path.is_file():
        return None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CIValidationError(f"cannot read Git-private Workstream session: {exc}") from exc
    if not isinstance(value, dict):
        raise CIValidationError("Git-private Workstream session must be a JSON object")
    return value, str(path)


def resolve_base(requested: str | None) -> tuple[str, str, dict[str, Any] | None, str | None]:
    session, session_path = _private_session()
    source = "explicit"
    value = requested
    if value is None and session is not None:
        lineage = session.get("lineage")
        if isinstance(lineage, dict) and isinstance(lineage.get("task_base_oid"), str):
            value = str(lineage["task_base_oid"])
            source = "workstream-lineage-task-base"
        elif isinstance(session.get("merge_base"), str):
            value = str(session["merge_base"])
            source = "workstream-merge-base"
    if value is None:
        value = "main"
        source = "git-main-fallback"
    commit = _resolve_commit(value)
    merge_base = str(git_output(["merge-base", commit, "HEAD"])).strip().lower()
    if len(merge_base) != 40:
        raise CIValidationError("cannot resolve exact validation merge base")
    return merge_base, source, session, session_path


def _nul_paths(arguments: list[str]) -> list[str]:
    raw = git_output(arguments, text=False)
    assert isinstance(raw, bytes)
    return [item.decode("utf-8", errors="surrogateescape").replace("\\", "/") for item in raw.split(b"\0") if item]


def changed_paths(base_sha: str) -> tuple[list[str], bool]:
    values = set(_nul_paths(["diff", "--name-only", "-z", f"{base_sha}...HEAD"]))
    values.update(_nul_paths(["diff", "--name-only", "-z"]))
    values.update(_nul_paths(["diff", "--cached", "--name-only", "-z"]))
    values.update(_nul_paths(["ls-files", "--others", "--exclude-standard", "-z"]))
    dirty = bool(str(git_output(["status", "--porcelain=v1", "--untracked-files=all"])).strip())
    return sorted(values), dirty


def _hash_working_paths(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        digest.update(relative.encode("utf-8", errors="surrogateescape") + b"\0")
        path = ROOT / relative
        if path.is_file():
            try:
                digest.update(path.read_bytes())
            except OSError as exc:
                digest.update(f"unreadable:{exc}".encode())
        else:
            digest.update(b"missing")
    return digest.hexdigest()


def _test_source_hash(test_ids: list[str]) -> str:
    modules = sorted({test_id.split(".", 1)[0] for test_id in test_ids})
    paths = [f"tests/{module}.py" for module in modules]
    paths.extend(["scripts/ci/_common.py", "scripts/ci/run_test_shard.py", "scripts/ci/validate_change.py"])
    return _hash_working_paths(paths)


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _validate_expected_writes(expected_writes: list[str]) -> None:
    broad: list[str] = []
    invalid: list[str] = []
    for value in expected_writes:
        path = value.replace("\\", "/")
        if not path or path.startswith("/") or path.endswith("/") or ".." in Path(path).parts:
            invalid.append(value)
            continue
        if "**" in path or path.count("*") + path.count("?") + path.count("[") > 1:
            broad.append(value)
            continue
        if any(token in path for token in ("*", "?", "[")):
            parent, _, leaf = path.rpartition("/")
            if not parent or leaf in {"*", "*.*"}:
                broad.append(value)
    if invalid or broad:
        raise SelectionRefused(
            f"expected-write scope is invalid or directory-wide: invalid={invalid}, broad={broad}",
            [
                "Replace every broad expected write with an exact repository file or one supported single-basename narrow glob.",
                "Actual Git changed paths remain the primary routing input; expected writes may not widen formal selection.",
            ],
        )


def _mapping_matches(value: str, mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [mapping for mapping in mappings if _matches(value, mapping["patterns"])]


def _change_volume(base_sha: str, paths: list[str]) -> dict[str, int]:
    counts = {path: [0, 0] for path in paths}
    commands = (
        ["diff", "--numstat", f"{base_sha}...HEAD"],
        ["diff", "--numstat"],
        ["diff", "--cached", "--numstat"],
    )
    for command in commands:
        raw = str(git_output(command))
        for line in raw.splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            added, deleted, path = parts
            path = path.replace("\\", "/")
            if path not in counts:
                continue
            if added.isdigit():
                counts[path][0] += int(added)
            if deleted.isdigit():
                counts[path][1] += int(deleted)
    for path in paths:
        absolute = ROOT / path
        if counts[path] == [0, 0] and absolute.is_file() and path in _nul_paths(
            ["ls-files", "--others", "--exclude-standard", "-z"]
        ):
            try:
                counts[path][0] = len(absolute.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeDecodeError):
                pass
    test_paths = {path for path in paths if path.startswith("tests/")}
    ci_paths = {
        path for path in paths
        if path.startswith("scripts/ci/") or path.startswith(".github/workflows/")
    }
    return {
        "test_changed_files": len(test_paths),
        "test_changed_lines": sum(sum(counts[path]) for path in test_paths),
        "ci_changed_files": len(ci_paths),
        "ci_changed_lines": sum(sum(counts[path]) for path in ci_paths),
    }


def _cost_diagnostics(
    plan: dict[str, Any], *, test_runtime: float | str, slow_ids: list[str],
) -> dict[str, Any]:
    inputs = plan["cost_diagnostic_inputs"]
    baseline = inputs["baseline_test_runtime_seconds"]
    investment = inputs["optimization_investment_seconds"]
    future_runs = inputs["expected_future_runs"]
    break_even: dict[str, Any] = {
        "status": "not-requested" if future_runs is None else "insufficient-input",
        "baseline_test_runtime_seconds": baseline if baseline is not None else "Unknown",
        "optimization_investment_seconds": investment if investment is not None else "Unknown",
        "seconds_saved_per_run": "Unknown",
        "break_even_runs": "Unknown",
        "projected_net_savings_seconds": "Unknown",
    }
    if (
        isinstance(test_runtime, (int, float)) and baseline is not None and investment is not None
        and baseline > float(test_runtime)
    ):
        saving = baseline - float(test_runtime)
        break_even.update({
            "status": "calculated",
            "seconds_saved_per_run": round(saving, 6),
            "break_even_runs": int(math.ceil(investment / saving)),
            "projected_net_savings_seconds": (
                round(saving * future_runs - investment, 6) if future_runs is not None else "Unknown"
            ),
        })
    return {
        "schema_version": COST_DIAGNOSTICS_VERSION,
        "authority": "non-authoritative-advisory",
        "selected_test_count": plan["selected_test_count"],
        "test_runtime_seconds": test_runtime,
        "router_setup_wall_seconds": inputs["router_setup_wall_seconds"],
        "rerun_count": inputs["rerun_count"],
        "slow_test_ids": slow_ids,
        "change_volume": inputs["change_volume"],
        "independent_optimization_workstream": inputs["independent_optimization_workstream"],
        "host_usage": {
            "status": "Unknown",
            "agent_token_usage": "Unknown",
            "tool_usage": "Unknown",
        },
        "expected_future_runs": future_runs if future_runs is not None else "Unknown",
        "break_even": break_even,
        "gate_effect": "none",
    }


def _record_recurrence(plan: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any] | str:
    if receipt.get("budget_exceeded") is not True:
        return "not-applicable"
    workstream_id = plan.get("workstream", {}).get("workstream_id")
    if not isinstance(workstream_id, str) or not workstream_id:
        return "workstream-identity-unknown"
    slow_ids = [str(item.get("test_id")) for item in receipt.get("slowest_tests", [])[:3]]
    bottleneck = {
        "mapping_ids": plan.get("mapping_ids", []),
        "slow_test_ids": slow_ids,
        "classification": receipt.get("over_budget_diagnosis", {}).get("classification"),
    }
    bottleneck_id = hashlib.sha256(
        json.dumps(bottleneck, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    common = Path(str(git_output(["rev-parse", "--path-format=absolute", "--git-common-dir"])).strip())
    path = common / "orrery" / "ci-validation" / "routing-recurrence.json"
    data: dict[str, Any] = {
        "schema_version": 1,
        "contract_type": "orrery-ci-routing-recurrence-diagnostic-v1",
        "bottlenecks": {},
    }
    if path.is_file():
        existing = load_json(path)
        if existing.get("schema_version") != 1 or existing.get("contract_type") != data["contract_type"]:
            raise CIValidationError("unsupported Git-private CI routing recurrence diagnostic")
        data = existing
    entry = data["bottlenecks"].setdefault(bottleneck_id, {**bottleneck, "workstream_ids": []})
    if workstream_id not in entry["workstream_ids"]:
        entry["workstream_ids"].append(workstream_id)
        entry["workstream_ids"].sort()
    atomic_write_json(path, data)
    if len(entry["workstream_ids"]) < 2:
        return "first-independent-workstream-observation"
    return {
        "schema_version": 1,
        "finding_type": "advisory-routing-cost-recurrence",
        "authority": "none",
        "bottleneck_id": bottleneck_id,
        "independent_workstream_count": len(entry["workstream_ids"]),
        "workstream_ids": entry["workstream_ids"],
        "automatic_task_created": False,
        "creates_adr_state_or_relation_fact": False,
    }


def _claim_bounded_triage(plan: dict[str, Any]) -> None:
    workstream_id = plan.get("workstream", {}).get("workstream_id")
    if not isinstance(workstream_id, str) or not workstream_id:
        raise SelectionRefused(
            "bounded triage requires a Git-private Workstream identity",
            ["Register or refresh the Git-private Workstream session before the one bounded triage attempt."],
        )
    common = Path(str(git_output(["rev-parse", "--path-format=absolute", "--git-common-dir"])).strip())
    path = common / "orrery" / "ci-validation" / "bounded-triage.json"
    data: dict[str, Any] = {
        "schema_version": 1,
        "contract_type": "orrery-ci-bounded-triage-v1",
        "workstream_attempts": {},
    }
    if path.is_file():
        data = load_json(path)
        if data.get("schema_version") != 1 or data.get("contract_type") != "orrery-ci-bounded-triage-v1":
            raise CIValidationError("unsupported Git-private bounded triage diagnostic")
    attempts = int(data["workstream_attempts"].get(workstream_id, 0))
    if attempts >= 1:
        raise SelectionRefused(
            f"feature Workstream {workstream_id} already used its one bounded triage attempt",
            ["Stop feature-task optimization and report the nonzero receipt and slow IDs to the central integrator."],
        )
    data["workstream_attempts"][workstream_id] = attempts + 1
    atomic_write_json(path, data)


def _record_run_attempt(plan: dict[str, Any]) -> int:
    identity = {
        "workstream_id": plan.get("workstream", {}).get("workstream_id"),
        "head_sha": plan["head_sha"],
        "dirty_fingerprint": plan["dirty_fingerprint"],
        "stage": plan["stage"],
        "mapping_ids": plan["mapping_ids"],
    }
    attempt_id = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    common = Path(str(git_output(["rev-parse", "--path-format=absolute", "--git-common-dir"])).strip())
    path = common / "orrery" / "ci-validation" / "run-attempts.json"
    data: dict[str, Any] = {
        "schema_version": 1,
        "contract_type": "orrery-ci-validation-run-attempts-v1",
        "attempts": {},
    }
    if path.is_file():
        data = load_json(path)
        if data.get("schema_version") != 1 or data.get("contract_type") != "orrery-ci-validation-run-attempts-v1":
            raise CIValidationError("unsupported Git-private validation run-attempt diagnostic")
    previous = int(data["attempts"].get(attempt_id, 0))
    data["attempts"][attempt_id] = previous + 1
    atomic_write_json(path, data)
    return previous


def _session_scope(session: dict[str, Any] | None) -> tuple[set[str], list[str]]:
    if session is None:
        return set(), []
    subsystems = {str(session.get("primary_subsystem_id", ""))}
    affected = session.get("affected_subsystem_ids")
    if isinstance(affected, list):
        subsystems.update(str(item) for item in affected)
    expected = session.get("expected_writes")
    expected_writes = [str(item).replace("\\", "/") for item in expected] if isinstance(expected, list) else []
    return {item for item in subsystems if item}, expected_writes


def build_selection(
    manifest: dict[str, Any], stage: str, base_sha: str, base_source: str,
    session: dict[str, Any] | None, session_path: str | None,
) -> dict[str, Any]:
    all_ids, _, _ = validate_and_expand_manifest(manifest)
    inventory = machine_inventory(manifest)
    metadata = {item["test_id"]: item for item in inventory["tests"]}
    registry = load_mapping_registry(manifest)
    paths, dirty = changed_paths(base_sha)
    subsystems, expected_writes = _session_scope(session)
    _validate_expected_writes(expected_writes)
    mappings = registry["path_mappings"]
    path_scoped_mappings: list[dict[str, Any]] = []
    subsystem_fallback_mappings: list[dict[str, Any]] = []
    path_explain: list[dict[str, Any]] = []
    for value in [*paths, *expected_writes]:
        matches = _mapping_matches(value, mappings)
        if len(matches) > 1:
            raise SelectionRefused(
                f"change scope maps to overlapping path_mappings: {value} -> {[item['id'] for item in matches]}",
                ["Make path_mappings ownership non-overlapping; use exact test dependencies for bounded adjacency."],
            )
    for mapping in mappings:
        matched_paths = [path for path in paths if _matches(path, mapping["patterns"])]
        matched_expected = [] if paths else [
            value for value in expected_writes if _matches(value, mapping["patterns"])
        ]
        matched_subsystems = sorted(subsystems & set(mapping["subsystems"]))
        if matched_paths or matched_expected:
            path_scoped_mappings.append(mapping)
            path_explain.append({
                "mapping_id": mapping["id"], "changed_paths": matched_paths,
                "expected_writes": matched_expected, "subsystems": matched_subsystems,
                "surfaces": mapping["surfaces"], "high_risk": mapping["high_risk"],
            })
        elif matched_subsystems:
            subsystem_fallback_mappings.append(mapping)
    unknown_paths = [path for path in paths if not _mapping_matches(path, mappings)]
    unknown_expected = [value for value in expected_writes if not _mapping_matches(value, mappings)]
    if unknown_paths or unknown_expected:
        raise SelectionRefused(
            f"change scope contains unmapped paths/expected writes: paths={unknown_paths}, expected_writes={unknown_expected}",
            [
                "Add one generic path_mappings entry with id, patterns, subsystems, surfaces, and high_risk.",
                "Then reference that mapping id from exact test dependencies; do not add task-ID branches to the router.",
            ],
        )
    selected_mappings = path_scoped_mappings or subsystem_fallback_mappings
    selection_mode = (
        "actual-changed-paths" if paths else
        "narrow-expected-writes" if expected_writes else
        "conservative-subsystem-fallback"
    )
    if not path_scoped_mappings:
        path_explain.extend({
            "mapping_id": mapping["id"], "changed_paths": [], "expected_writes": [],
            "subsystems": sorted(subsystems & set(mapping["subsystems"])),
            "surfaces": mapping["surfaces"], "high_risk": mapping["high_risk"],
        } for mapping in subsystem_fallback_mappings)
    mapping_ids = {mapping["id"] for mapping in selected_mappings}
    if not mapping_ids:
        raise SelectionRefused(
            "no generic mapping was derived from Git diff or Workstream scope",
            ["Add or correct path_mappings metadata for the changed path/subsystem/expected-write surface."],
        )
    selected_ids = sorted(
        test_id for test_id, entry in metadata.items()
        if stage in entry["allowed_stages"] and mapping_ids.intersection(entry["dependencies"])
    )
    if not selected_ids:
        raise SelectionRefused(
            f"no registered {stage} tests depend on mappings {sorted(mapping_ids)}",
            [
                "Register at least one exact test entry with owner_surface, owner_shard, allowed_stages, "
                "cost_class, budget_seconds, dependencies, and reason."
            ],
        )
    head = git_sha()
    fingerprint = dirty_fingerprint()
    budget = float(registry["stages"][stage]["budget_seconds"])
    relevant_hash = _hash_working_paths(paths)
    dependency_hash = sha256_json({
        "mappings": path_explain, "selected_test_ids": selected_ids,
        "registry_sha256": sha256_json(registry), "session_subsystems": sorted(subsystems),
    })
    environment = {
        name: os.environ.get(name)
        for name in registry["reuse"]["environment_gates"]
    }
    security_mappings = set(registry["reuse"]["security_high_risk_mappings"])
    high_risk = bool(mapping_ids & security_mappings)
    reuse_reasons: list[str] = []
    if stage not in {"fast", "checkpoint"}:
        reuse_reasons.append("reuse-is-limited-to-fast-and-checkpoint")
    if dirty:
        reuse_reasons.append("working-tree-is-dirty")
    if high_risk:
        reuse_reasons.append("security-high-risk-surface")
    reuse_reasons.append("reuse-execution-not-enabled-by-contract-v1")
    reuse_key = {
        "test_source_sha256": _test_source_hash(selected_ids),
        "selector_dependency_sha256": dependency_hash,
        "relevant_tree_sha256": relevant_hash,
        "python": platform.python_version(), "os": platform.system(),
        "runner_version": registry["runner_version"],
        "receipt_schema_version": 1, "manifest_sha256": sha256_json(manifest),
        "mapping_registry_sha256": sha256_json(registry),
        "inventory_sha256": inventory["inventory_sha256"], "environment_gates": environment,
    }
    return {
        "schema_version": 1, "contract_type": PLAN_TYPE, "stage": stage,
        "role": registry["stages"][stage]["role"],
        "head_sha": head, "base_sha": base_sha, "base_source": base_source,
        "dirty": dirty, "dirty_fingerprint": fingerprint,
        "manifest_sha256": sha256_json(manifest),
        "mapping_registry_sha256": sha256_json(registry),
        "inventory_sha256": inventory["inventory_sha256"],
        "selected_test_ids": selected_ids, "selected_test_count": len(selected_ids),
        "budget_seconds": budget, "changed_paths": paths, "unknown_paths": unknown_paths,
        "selection_mode": selection_mode,
        "mapping_ids": sorted(mapping_ids), "path_explain": path_explain,
        "selected_tests": [metadata[test_id] for test_id in selected_ids],
        "workstream": {
            "session_path": session_path,
            "workstream_id": session.get("workstream_id") if session else None,
            "primary_subsystem_id": session.get("primary_subsystem_id") if session else None,
            "affected_subsystem_ids": session.get("affected_subsystem_ids", []) if session else [],
            "expected_writes": expected_writes,
        },
        "reuse": {
            "schema_version": registry["reuse"]["schema_version"],
            "mode": registry["reuse"]["mode"], "decision": "refused",
            "eligible_inputs": not reuse_reasons[:-1], "reasons": reuse_reasons, "key": reuse_key,
        },
        "cost_diagnostic_inputs": {
            "schema_version": 1,
            "router_setup_wall_seconds": 0.0,
            "rerun_count": 0,
            "change_volume": {
                "test_changed_files": 0, "test_changed_lines": 0,
                "ci_changed_files": 0, "ci_changed_lines": 0,
            },
            "independent_optimization_workstream": False,
            "expected_future_runs": None,
            "baseline_test_runtime_seconds": None,
            "optimization_investment_seconds": None,
        },
    }


def _default_output(stage: str) -> Path:
    raw = str(git_output(["rev-parse", "--path-format=absolute", "--git-path", "orrery/ci-validation/receipts"])).strip()
    return Path(raw) / f"latest-{stage}.json"


def _dry_receipt(plan: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        **plan,
        "contract_type": RECEIPT_TYPE,
        "outcome": "dry-run", "successful": False, "completed": True,
        "evidence_eligible": False, "duration_seconds": 0.0,
        "timed_out": False, "interrupted": False, "runner_errors": [],
        "os": platform.system(), "python": platform.python_version(),
    }
    receipt["cost_diagnostics"] = _cost_diagnostics(plan, test_runtime="Unknown", slow_ids=[])
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a local change to the only tier-evidence runner")
    parser.add_argument("--stage", choices=("fast", "checkpoint", "candidate"), required=True)
    parser.add_argument("--base", help="base SHA/ref; defaults to the Git-private Workstream task base")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--reuse", action="store_true", help="evaluate the conservative reuse contract")
    parser.add_argument("--expected-future-runs", type=int)
    parser.add_argument("--baseline-test-runtime-seconds", type=float)
    parser.add_argument("--optimization-investment-seconds", type=float)
    parser.add_argument("--independent-optimization-workstream", action="store_true")
    parser.add_argument(
        "--bounded-triage", action="store_true",
        help="mark this as the one permitted feature-task localization attempt",
    )
    arguments = parser.parse_args()
    if arguments.expected_future_runs is not None and arguments.expected_future_runs <= 0:
        parser.error("--expected-future-runs must be positive")
    for name in ("baseline_test_runtime_seconds", "optimization_investment_seconds"):
        value = getattr(arguments, name)
        if value is not None and value < 0:
            parser.error(f"--{name.replace('_', '-')} must be non-negative")
    started = time.perf_counter()
    output = arguments.output.resolve() if arguments.output else _default_output(arguments.stage)
    base_sha: str | None = None
    base_source: str | None = None
    try:
        manifest_path = arguments.manifest.resolve()
        manifest = load_json(manifest_path)
        base_sha, base_source, session, session_path = resolve_base(arguments.base)
        plan = build_selection(manifest, arguments.stage, base_sha, base_source, session, session_path)
        plan["cost_diagnostic_inputs"] = {
            **plan["cost_diagnostic_inputs"],
            "router_setup_wall_seconds": round(time.perf_counter() - started, 6),
            "rerun_count": 0,
            "change_volume": _change_volume(base_sha, plan["changed_paths"]),
            "independent_optimization_workstream": arguments.independent_optimization_workstream,
            "expected_future_runs": arguments.expected_future_runs,
            "baseline_test_runtime_seconds": arguments.baseline_test_runtime_seconds,
            "optimization_investment_seconds": arguments.optimization_investment_seconds,
        }
        plan["bounded_triage"] = {
            "requested": arguments.bounded_triage,
            "maximum_feature_task_attempts": 1,
        }
        if arguments.bounded_triage and not arguments.dry_run:
            _claim_bounded_triage(plan)
        if arguments.dry_run:
            receipt = _dry_receipt(plan)
            atomic_write_json(output, receipt)
            if arguments.explain:
                print(json.dumps(receipt, ensure_ascii=False, indent=2))
            else:
                print(
                    f"DRY-RUN {arguments.stage}: {plan['selected_test_count']} tests, "
                    f"budget {plan['budget_seconds']}s, receipt {output}"
                )
            return 0
        plan["cost_diagnostic_inputs"]["rerun_count"] = _record_run_attempt(plan)
        plan_path = output.with_suffix(output.suffix + ".plan.json")
        atomic_write_json(plan_path, plan)
        command = [
            sys.executable, "-X", "utf8", str(RUNNER), "--manifest", str(manifest_path),
            "--selection-plan", str(plan_path), "--output", str(output),
        ]
        try:
            completed = subprocess.run(
                command, cwd=ROOT, check=False, timeout=float(plan["budget_seconds"])
            )
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            receipt = {
                **plan, "contract_type": RECEIPT_TYPE, "outcome": "timeout",
                "successful": False, "completed": False, "evidence_eligible": False,
                "duration_seconds": round(time.perf_counter() - started, 6),
                "timed_out": True, "interrupted": False,
                "runner_errors": ["validation runner exceeded the stage budget and was terminated"],
                "os": platform.system(), "python": platform.python_version(),
            }
            receipt["cost_diagnostics"] = _cost_diagnostics(
                plan, test_runtime="Unknown", slow_ids=[]
            )
            receipt["over_budget_diagnosis"] = {
                "schema_version": 1,
                "classification": "router-or-setup-timeout",
                "feature_task_action": "stop-and-report-to-central-integrator",
                "bounded_triage_attempts_allowed": 1,
                "bounded_triage_requested": arguments.bounded_triage,
                "recurrence_finding": "not-evaluated",
            }
            atomic_write_json(output, receipt)
            print(f"FAIL {arguments.stage}: timed out at {plan['budget_seconds']}s", file=sys.stderr)
            return 1
        if not output.is_file():
            raise CIValidationError("runner returned without a versioned receipt")
        receipt = load_json(output)
        receipt["runner_contract_type"] = receipt.get("contract_type")
        receipt["contract_type"] = RECEIPT_TYPE
        receipt["schema_version"] = 1
        receipt["router_explain"] = plan["path_explain"]
        receipt["reuse"] = plan["reuse"]
        receipt["invoked_by"] = "validate_change.py"
        receipt["evidence_eligible"] = return_code == 0 and receipt.get("successful") is True
        receipt["cost_diagnostics"] = _cost_diagnostics(
            plan,
            test_runtime=float(receipt.get("duration_seconds", 0.0)),
            slow_ids=[str(item.get("test_id")) for item in receipt.get("slowest_tests", [])],
        )
        if isinstance(receipt.get("over_budget_diagnosis"), dict):
            receipt["over_budget_diagnosis"]["recurrence_finding"] = _record_recurrence(
                plan, receipt
            )
        atomic_write_json(output, receipt)
        if arguments.explain:
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0 if receipt["evidence_eligible"] else 1
    except KeyboardInterrupt:
        interruption = {
            "schema_version": 1,
            "contract_type": REFUSAL_TYPE,
            "stage": arguments.stage,
            "head_sha": git_sha(),
            "base_sha": base_sha,
            "base_source": base_source,
            "dirty_fingerprint": dirty_fingerprint(),
            "outcome": "interrupted",
            "successful": False,
            "completed": False,
            "evidence_eligible": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "runner_errors": ["validation router was interrupted; no tier evidence is valid"],
            "required_metadata": [],
            "os": platform.system(),
            "python": platform.python_version(),
        }
        interruption["cost_diagnostics"] = {
            "schema_version": 1, "authority": "non-authoritative-advisory",
            "selected_test_count": "Unknown", "test_runtime_seconds": "Unknown",
            "router_setup_wall_seconds": round(time.perf_counter() - started, 6),
            "rerun_count": "Unknown", "slow_test_ids": [],
            "change_volume": "Unknown", "independent_optimization_workstream": arguments.independent_optimization_workstream,
            "host_usage": {"status": "Unknown", "agent_token_usage": "Unknown", "tool_usage": "Unknown"},
            "expected_future_runs": arguments.expected_future_runs or "Unknown",
            "break_even": {"status": "insufficient-input"}, "gate_effect": "none",
        }
        atomic_write_json(output, interruption)
        print("FAIL validation router: interrupted; no tier evidence is valid", file=sys.stderr)
        return 130
    except SelectionRefused as exc:
        refusal = {
            "schema_version": 1,
            "contract_type": REFUSAL_TYPE,
            "stage": arguments.stage,
            "head_sha": git_sha(),
            "base_sha": base_sha,
            "base_source": base_source,
            "dirty_fingerprint": dirty_fingerprint(),
            "outcome": "refused",
            "successful": False,
            "completed": True,
            "evidence_eligible": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "runner_errors": [str(exc)],
            "required_metadata": exc.required_metadata,
            "os": platform.system(),
            "python": platform.python_version(),
        }
        refusal["cost_diagnostics"] = {
            "schema_version": 1, "authority": "non-authoritative-advisory",
            "selected_test_count": "Unknown", "test_runtime_seconds": "Unknown",
            "router_setup_wall_seconds": round(time.perf_counter() - started, 6),
            "rerun_count": "Unknown", "slow_test_ids": [],
            "change_volume": "Unknown", "independent_optimization_workstream": arguments.independent_optimization_workstream,
            "host_usage": {"status": "Unknown", "agent_token_usage": "Unknown", "tool_usage": "Unknown"},
            "expected_future_runs": arguments.expected_future_runs or "Unknown",
            "break_even": {"status": "insufficient-input"}, "gate_effect": "none",
        }
        atomic_write_json(output, refusal)
        print(f"REFUSED {arguments.stage}: {exc}", file=sys.stderr)
        for item in exc.required_metadata:
            print(f"- required metadata: {item}", file=sys.stderr)
        return 2
    except (CIValidationError, OSError) as exc:
        message = str(exc)
        required = ["Repair the manifest/registry contract reported by runner_errors before requesting tier evidence."]
        if "unregistered=" in message:
            required = [
                "Add one exact tests entry with owner_surface, owner_shard, allowed_stages, cost_class, "
                "budget_seconds, dependencies, and reason."
            ]
        elif "Unknown dependencies" in message:
            required = [
                "Add the missing generic path_mappings entry or correct the exact test dependencies list."
            ]
        refusal = {
            "schema_version": 1, "contract_type": REFUSAL_TYPE, "stage": arguments.stage,
            "head_sha": git_sha(), "base_sha": base_sha, "base_source": base_source,
            "dirty_fingerprint": dirty_fingerprint(), "outcome": "refused",
            "successful": False, "completed": True, "evidence_eligible": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "runner_errors": [message], "required_metadata": required,
            "os": platform.system(), "python": platform.python_version(),
        }
        refusal["cost_diagnostics"] = {
            "schema_version": 1, "authority": "non-authoritative-advisory",
            "selected_test_count": "Unknown", "test_runtime_seconds": "Unknown",
            "router_setup_wall_seconds": round(time.perf_counter() - started, 6),
            "rerun_count": "Unknown", "slow_test_ids": [],
            "change_volume": "Unknown", "independent_optimization_workstream": arguments.independent_optimization_workstream,
            "host_usage": {"status": "Unknown", "agent_token_usage": "Unknown", "tool_usage": "Unknown"},
            "expected_future_runs": arguments.expected_future_runs or "Unknown",
            "break_even": {"status": "insufficient-input"}, "gate_effect": "none",
        }
        atomic_write_json(output, refusal)
        print(f"FAIL validation router: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
