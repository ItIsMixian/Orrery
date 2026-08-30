from __future__ import annotations

import argparse
import hashlib
import math
import os
import platform
import subprocess
import sys
import time
import unittest
from pathlib import Path
from typing import Any

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    atomic_write_json,
    block_validation_lease,
    consume_validation_lease,
    dirty_fingerprint,
    expand_profile,
    finalize_validation_lease,
    flatten_suite,
    git_sha,
    load_json,
    load_mapping_registry,
    machine_inventory,
    repository_import_path,
    sha256_json,
    update_timing_summary,
    validate_and_expand_manifest,
)


class TimedTextResult(unittest.TextTestResult):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._started: dict[str, float] = {}
        self._outcomes: dict[str, tuple[str, str | None]] = {}
        self.records: list[dict[str, object]] = []

    def startTest(self, test: unittest.TestCase) -> None:
        self._started[test.id()] = time.perf_counter()
        super().startTest(test)

    def addSuccess(self, test: unittest.TestCase) -> None:
        self._outcomes[test.id()] = ("success", None)
        super().addSuccess(test)

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:
        self._outcomes[test.id()] = ("failure", self._exc_info_to_string(err, test))
        super().addFailure(test, err)

    def addError(self, test: unittest.TestCase, err: Any) -> None:
        self._outcomes[test.id()] = ("error", self._exc_info_to_string(err, test))
        super().addError(test, err)

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        self._outcomes[test.id()] = ("skipped", reason)
        super().addSkip(test, reason)

    def addExpectedFailure(self, test: unittest.TestCase, err: Any) -> None:
        self._outcomes[test.id()] = ("expected-failure", self._exc_info_to_string(err, test))
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        self._outcomes[test.id()] = ("unexpected-success", None)
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test: unittest.TestCase, subtest: unittest.TestCase, err: Any) -> None:
        if err is not None:
            outcome = "failure" if issubclass(err[0], test.failureException) else "error"
            self._outcomes[test.id()] = (outcome, self._exc_info_to_string(err, subtest))
        super().addSubTest(test, subtest, err)

    def stopTest(self, test: unittest.TestCase) -> None:
        test_id = test.id()
        duration = max(0.0, time.perf_counter() - self._started.pop(test_id, time.perf_counter()))
        outcome, detail = self._outcomes.pop(test_id, ("unknown", "test completed without a unittest outcome"))
        record: dict[str, object] = {
            "test_id": test_id,
            "outcome": outcome,
            "duration_seconds": round(duration, 6),
        }
        if detail:
            record["detail"] = detail
        self.records.append(record)
        super().stopTest(test)


def _cost_inputs(plan: dict[str, Any] | None) -> dict[str, Any]:
    defaults = {
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
    }
    if plan is None:
        return defaults
    forbidden_claims = {"cost_diagnostics", "host_usage", "agent_token_usage", "tool_usage", "gate_effect"}
    pending: list[Any] = [plan]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            found = forbidden_claims & set(item)
            if found:
                raise CIValidationError(
                    f"selection plan contains forged usage/token claims or ROI gate fields: {sorted(found)}"
                )
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    value = plan.get("cost_diagnostic_inputs")
    if not isinstance(value, dict) or set(value) != set(defaults):
        raise CIValidationError(
            "selection plan cost_diagnostic_inputs must contain only the versioned CI7 advisory fields; "
            "host usage/token claims or ROI gate fields are not accepted"
        )
    if value["schema_version"] != 1:
        raise CIValidationError("unsupported cost_diagnostic_inputs schema version")
    volume = value["change_volume"]
    if not isinstance(volume, dict) or set(volume) != set(defaults["change_volume"]):
        raise CIValidationError("selection plan change_volume fields are invalid")
    numeric_fields = ("router_setup_wall_seconds", "rerun_count")
    if any(
        not isinstance(value[field], (int, float)) or isinstance(value[field], bool) or value[field] < 0
        for field in numeric_fields
    ):
        raise CIValidationError("selection plan cost diagnostic counts/times must be non-negative")
    if not isinstance(value["independent_optimization_workstream"], bool):
        raise CIValidationError("independent optimization Workstream diagnostic must be boolean")
    for field in ("expected_future_runs", "baseline_test_runtime_seconds", "optimization_investment_seconds"):
        item = value[field]
        if item is not None and (
            not isinstance(item, (int, float)) or isinstance(item, bool) or item < 0
        ):
            raise CIValidationError(f"selection plan {field} must be non-negative or null")
    return value


def _over_budget_diagnosis(
    *, budget_exceeded: bool, result: unittest.TestResult, records: list[dict[str, object]],
    budget_seconds: float | None, selection_plan: dict[str, Any] | None,
) -> dict[str, object]:
    if result.failures or result.errors:
        classification = "product-test-failure"
    elif not budget_exceeded:
        classification = "not-over-budget"
    elif selection_plan is not None and selection_plan.get("selection_mode") != "actual-changed-paths":
        classification = "router-over-selection"
    elif budget_seconds and records and max(float(item["duration_seconds"]) for item in records) >= budget_seconds / 2:
        classification = "genuinely-slow-path"
    else:
        classification = "fixture-runtime-variance"
    return {
        "schema_version": 1,
        "classification": classification,
        "feature_task_action": (
            "stop-and-report-to-central-integrator" if classification != "not-over-budget" else "none"
        ),
        "bounded_triage_attempts_allowed": 1,
        "bounded_triage_requested": bool(
            selection_plan and selection_plan.get("bounded_triage", {}).get("requested")
        ),
        "recurrence_finding": "not-evaluated",
    }


def _break_even(inputs: dict[str, Any], runtime: float) -> dict[str, Any]:
    baseline = inputs["baseline_test_runtime_seconds"]
    investment = inputs["optimization_investment_seconds"]
    future_runs = inputs["expected_future_runs"]
    result: dict[str, Any] = {
        "status": "not-requested" if future_runs is None else "insufficient-input",
        "baseline_test_runtime_seconds": baseline if baseline is not None else "Unknown",
        "optimization_investment_seconds": investment if investment is not None else "Unknown",
        "seconds_saved_per_run": "Unknown", "break_even_runs": "Unknown",
        "projected_net_savings_seconds": "Unknown",
    }
    if baseline is not None and investment is not None and baseline > runtime:
        saving = baseline - runtime
        result.update({
            "status": "calculated", "seconds_saved_per_run": round(saving, 6),
            "break_even_runs": int(math.ceil(investment / saving)),
            "projected_net_savings_seconds": (
                round(saving * future_runs - investment, 6) if future_runs is not None else "Unknown"
            ),
        })
    return result


def _load_selected_tests(test_ids: list[str]) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    with repository_import_path(ROOT):
        suite = loader.loadTestsFromNames(test_ids)
    if loader.errors:
        raise CIValidationError("selected test loading errors:\n" + "\n".join(loader.errors))
    loaded_ids = [test.id() for test in flatten_suite(suite)]
    if loaded_ids != test_ids:
        raise CIValidationError(f"selected test IDs changed while loading: expected={test_ids}, loaded={loaded_ids}")
    return suite


def run_selected(
    *, manifest_path: Path, shard: str | None, profile: str | None, output: Path,
    selection_plan_path: Path | None = None,
) -> tuple[dict[str, object], bool]:
    runner_setup_started = time.perf_counter()
    manifest = load_json(manifest_path)
    all_ids, assignments, _ = validate_and_expand_manifest(manifest)
    inventory = machine_inventory(manifest)
    registry = load_mapping_registry(manifest)
    head_before = git_sha()
    dirty_before = dirty_fingerprint()
    selection_plan: dict[str, Any] | None = None
    validation_lease: dict[str, Any] | None = None
    if selection_plan_path is not None:
        if shard is not None or profile is not None:
            raise CIValidationError("selection plan cannot be combined with --shard or --profile")
        selection_plan = load_json(selection_plan_path)
        if selection_plan.get("contract_type") != "orrery-test-selection-plan-v1":
            raise CIValidationError("unsupported local validation selection plan")
        for field, actual in (
            ("head_sha", head_before),
            ("dirty_fingerprint", dirty_before),
            ("manifest_sha256", sha256_json(manifest)),
            ("mapping_registry_sha256", sha256_json(registry)),
            ("inventory_sha256", inventory["inventory_sha256"]),
        ):
            if selection_plan.get(field) != actual:
                raise CIValidationError(f"selection plan {field} drifted before runner start")
        selected_ids = selection_plan.get("selected_test_ids")
        if not isinstance(selected_ids, list) or not selected_ids or any(
            not isinstance(item, str) or item not in all_ids for item in selected_ids
        ):
            raise CIValidationError("selection plan contains invalid or unknown test IDs")
        if selected_ids != sorted(set(selected_ids)):
            raise CIValidationError("selection plan test IDs must be sorted and unique")
        stage = str(selection_plan.get("stage"))
        if stage not in {"focused", "fast", "checkpoint", "candidate"}:
            raise CIValidationError(f"selection plan has invalid stage: {stage}")
        shard_id = stage
        role = str(selection_plan.get("role"))
        budget_seconds = float(selection_plan.get("budget_seconds"))
        base_sha = str(selection_plan.get("base_sha"))
        relevant_tree_hash = str(selection_plan["reuse"]["key"]["relevant_tree_sha256"])
        test_source_hash = str(selection_plan["reuse"]["key"]["test_source_sha256"])
        selector_dependency_hash = str(
            selection_plan["reuse"]["key"]["selector_dependency_sha256"]
        )
        validation_lease = consume_validation_lease(selection_plan)
    elif profile is not None:
        selected_ids = expand_profile(manifest, profile, all_ids)
        shard_id = profile
        stage = profile
        role = str(registry["stages"][profile]["role"])
        budget_seconds: float | None = float(registry["stages"][profile]["budget_seconds"])
    else:
        if shard is None:
            raise CIValidationError("select exactly one of --shard, --profile, or --selection-plan")
        if shard not in assignments:
            raise CIValidationError(f"unknown shard: {shard}")
        selected_ids = assignments[shard]
        shard_id = str(shard)
        stage = "promotion"
        role = "promotion-shard"
        shard_config = next(item for item in manifest["shards"] if item["id"] == shard)
        budget_seconds = (
            float(shard_config["budget_seconds"])
            if "budget_seconds" in shard_config
            else None
        )
    if selection_plan is None:
        main = subprocess.run(
            ["git", "merge-base", "HEAD", "main"], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )
        base_sha = main.stdout.strip().lower() if main.returncode == 0 else head_before
        source_digest = hashlib.sha256()
        for module in sorted({test_id.split(".", 1)[0] for test_id in selected_ids}):
            path = ROOT / "tests" / f"{module}.py"
            source_digest.update(module.encode() + b"\0")
            source_digest.update(path.read_bytes() if path.is_file() else b"missing")
        test_source_hash = source_digest.hexdigest()
        selector_dependency_hash = sha256_json(selected_ids)
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )
        relevant_tree_hash = (
            tree.stdout.strip().lower() if tree.returncode == 0 else sha256_json([head_before, dirty_before])
        )
    diagnostic_inputs = _cost_inputs(selection_plan)
    try:
        suite = _load_selected_tests(selected_ids)
    except (CIValidationError, OSError) as exc:
        if validation_lease is not None:
            block_validation_lease(validation_lease, {
                "schema_version": 2,
                "contract_type": "orrery-test-shard-result-v2",
                "outcome": "runner-error",
                "successful": False,
                "evidence_eligible": False,
                "duration_seconds": 0.0,
                "runner_errors": [str(exc)],
            })
        raise
    runner_setup_wall_seconds = max(0.0, time.perf_counter() - runner_setup_started)
    started = time.perf_counter()
    with repository_import_path(ROOT):
        result = unittest.TextTestRunner(verbosity=2, resultclass=TimedTextResult).run(suite)
    duration = max(0.0, time.perf_counter() - started)
    sha = git_sha()
    dirty_after = dirty_fingerprint()
    runner_os = os.environ.get("RUNNER_OS", platform.system())
    python_version = platform.python_version()
    records = sorted(result.records, key=lambda item: str(item["test_id"]))
    for record in records:
        record.update({"sha": sha, "os": runner_os, "python": python_version, "shard": shard_id})
    record_ids = [str(item["test_id"]) for item in records]
    budget_exceeded = budget_seconds is not None and duration > budget_seconds
    runner_errors = [test.id() for test, _ in result.errors if test.id() not in selected_ids]
    if sha != head_before:
        runner_errors.append("HEAD changed during validation")
    if dirty_after != dirty_before:
        runner_errors.append("dirty fingerprint changed during validation")
    successful = (
        result.wasSuccessful() and record_ids == selected_ids and not budget_exceeded
        and not runner_errors
    )
    slowest = sorted(records, key=lambda item: float(item["duration_seconds"]), reverse=True)[:5]
    outcome = "passed" if successful else ("budget-exceeded" if budget_exceeded else "failed")
    payload: dict[str, object] = {
        "schema_version": 2,
        "contract_type": "orrery-test-shard-result-v2",
        "role": role,
        "stage": stage,
        "sha": sha,
        "head_sha": sha,
        "base_sha": base_sha,
        "dirty_fingerprint": dirty_after,
        "os": runner_os,
        "python": python_version,
        "shard": shard_id,
        "manifest_sha256": sha256_json(manifest),
        "mapping_registry_sha256": sha256_json(registry),
        "inventory_sha256": inventory["inventory_sha256"],
        "test_source_sha256": test_source_hash,
        "selector_dependency_sha256": selector_dependency_hash,
        "relevant_tree_sha256": relevant_tree_hash,
        "runner_version": registry["runner_version"],
        "environment_gates": {
            name: os.environ.get(name)
            for name in registry["reuse"]["environment_gates"]
        },
        "orrery_test_build": os.environ.get("ORRERY_TEST_BUILD"),
        "selected_test_count": len(selected_ids),
        "selected_test_ids": selected_ids,
        "records": records,
        "tests_run": result.testsRun,
        "successful": successful,
        "completed": True,
        "evidence_eligible": successful and stage != "focused",
        "outcome": outcome,
        "duration_seconds": round(duration, 6),
        "budget_seconds": budget_seconds,
        "budget_exceeded": budget_exceeded,
        "timed_out": False,
        "interrupted": False,
        "runner_errors": runner_errors,
        "slowest_tests": [
            {"test_id": item["test_id"], "duration_seconds": item["duration_seconds"]}
            for item in slowest
        ],
        "promotion_only_suggestion": (
            "Move only inventory-declared heavy journeys to Promotion; do not record this over-budget run as tier evidence."
            if budget_exceeded else None
        ),
        "cost_diagnostics": {
            "schema_version": 1,
            "authority": "non-authoritative-advisory",
            "selected_test_count": len(selected_ids),
            "test_runtime_seconds": round(duration, 6),
            "router_setup_wall_seconds": diagnostic_inputs["router_setup_wall_seconds"],
            "runner_setup_build_wall_seconds": round(runner_setup_wall_seconds, 6),
            "total_setup_build_wall_seconds": round(
                diagnostic_inputs["router_setup_wall_seconds"] + runner_setup_wall_seconds, 6
            ),
            "rerun_count": diagnostic_inputs["rerun_count"],
            "slow_test_ids": [str(item["test_id"]) for item in slowest],
            "change_volume": diagnostic_inputs["change_volume"],
            "independent_optimization_workstream": diagnostic_inputs["independent_optimization_workstream"],
            "host_usage": {
                "status": "Unknown", "agent_token_usage": "Unknown", "tool_usage": "Unknown",
            },
            "expected_future_runs": (
                diagnostic_inputs["expected_future_runs"]
                if diagnostic_inputs["expected_future_runs"] is not None else "Unknown"
            ),
            "break_even": _break_even(diagnostic_inputs, duration),
            "gate_effect": "none",
        },
        "over_budget_diagnosis": _over_budget_diagnosis(
            budget_exceeded=budget_exceeded, result=result, records=records,
            budget_seconds=budget_seconds, selection_plan=selection_plan,
        ),
    }
    if selection_plan is not None and validation_lease is not None:
        payload.update({
            "acceptance_policy": selection_plan.get("acceptance_policy"),
            "surface_fingerprint": selection_plan.get("surface_fingerprint"),
            "timing_prediction": selection_plan.get("timing_prediction"),
            "task_phase": selection_plan.get("task_phase"),
            "validation_lease_id": validation_lease["lease_id"],
        })
    atomic_write_json(output, payload)
    if validation_lease is not None:
        finalize_validation_lease(validation_lease, payload)
        if successful and stage != "focused":
            update_timing_summary(
                payload,
                environment_key=f"{platform.system()}:{platform.python_version()}",
            )
    return payload, successful


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an exact unittest shard and emit timing JSON")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--shard")
    group.add_argument("--profile", choices=("fast", "checkpoint"))
    group.add_argument("--selection-plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    def block_plan_lease(failure: dict[str, object]) -> None:
        if arguments.selection_plan is None or not arguments.selection_plan.is_file():
            return
        try:
            plan = load_json(arguments.selection_plan.resolve())
            lease = plan.get("validation_lease")
            if isinstance(lease, dict):
                block_validation_lease(lease, failure)
        except (CIValidationError, OSError):
            return
    try:
        payload, successful = run_selected(
            manifest_path=arguments.manifest.resolve(),
            shard=arguments.shard,
            profile=arguments.profile,
            output=arguments.output.resolve(),
            selection_plan_path=(
                arguments.selection_plan.resolve() if arguments.selection_plan is not None else None
            ),
        )
        print(
            f"{'PASS' if successful else 'FAIL'} {payload['role']} {payload['shard']}: "
            f"{payload['tests_run']}/{payload['selected_test_count']} tests in {payload['duration_seconds']}s"
        )
        if payload["budget_exceeded"]:
            print("Slowest tests:", file=sys.stderr)
            for item in payload["slowest_tests"]:
                print(f"- {item['test_id']}: {item['duration_seconds']}s", file=sys.stderr)
            print(payload["promotion_only_suggestion"], file=sys.stderr)
        return 0 if successful else 1
    except KeyboardInterrupt:
        failure = {
            "schema_version": 2,
            "contract_type": "orrery-test-shard-result-v2",
            "role": "non-evidence-runner-failure",
            "stage": arguments.profile or ("promotion" if arguments.shard else "selection-plan"),
            "sha": git_sha(),
            "head_sha": git_sha(),
            "dirty_fingerprint": dirty_fingerprint(),
            "shard": arguments.shard or arguments.profile or "selection-plan",
            "selected_test_count": 0,
            "selected_test_ids": [],
            "records": [],
            "tests_run": 0,
            "successful": False,
            "completed": False,
            "evidence_eligible": False,
            "outcome": "interrupted",
            "duration_seconds": 0.0,
            "timed_out": False,
            "interrupted": True,
            "runner_errors": ["shard runner was interrupted; no tier evidence is valid"],
            "os": os.environ.get("RUNNER_OS", platform.system()),
            "python": platform.python_version(),
        }
        atomic_write_json(arguments.output.resolve(), failure)
        block_plan_lease(failure)
        print("FAIL shard runner: interrupted; no tier evidence is valid", file=sys.stderr)
        return 130
    except (CIValidationError, OSError) as exc:
        failure = {
            "schema_version": 2,
            "contract_type": "orrery-test-shard-result-v2",
            "role": "non-evidence-runner-failure",
            "stage": arguments.profile or ("promotion" if arguments.shard else "selection-plan"),
            "sha": git_sha(),
            "head_sha": git_sha(),
            "dirty_fingerprint": dirty_fingerprint(),
            "shard": arguments.shard or arguments.profile or "selection-plan",
            "selected_test_count": 0,
            "selected_test_ids": [],
            "records": [],
            "tests_run": 0,
            "successful": False,
            "completed": False,
            "evidence_eligible": False,
            "outcome": "runner-error",
            "duration_seconds": 0.0,
            "timed_out": False,
            "interrupted": False,
            "runner_errors": [str(exc)],
            "os": os.environ.get("RUNNER_OS", platform.system()),
            "python": platform.python_version(),
        }
        atomic_write_json(arguments.output.resolve(), failure)
        block_plan_lease(failure)
        print(f"FAIL shard runner: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
