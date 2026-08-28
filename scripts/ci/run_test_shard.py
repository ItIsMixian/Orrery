from __future__ import annotations

import argparse
import os
import platform
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
    expand_profile,
    flatten_suite,
    git_sha,
    load_json,
    repository_import_path,
    sha256_json,
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
    *, manifest_path: Path, shard: str | None, profile: str | None, output: Path
) -> tuple[dict[str, object], bool]:
    manifest = load_json(manifest_path)
    all_ids, assignments, _ = validate_and_expand_manifest(manifest)
    if (shard is None) == (profile is None):
        raise CIValidationError("select exactly one of --shard or --profile")
    if profile is not None:
        selected_ids = expand_profile(manifest, profile, all_ids)
        shard_id = profile
        role = str(manifest[profile]["role"])
        budget_seconds: float | None = float(manifest[profile]["budget_seconds"])
    else:
        if shard not in assignments:
            raise CIValidationError(f"unknown shard: {shard}")
        selected_ids = assignments[shard]
        shard_id = str(shard)
        role = "promotion-shard"
        shard_config = next(item for item in manifest["shards"] if item["id"] == shard)
        budget_seconds = (
            float(shard_config["budget_seconds"])
            if "budget_seconds" in shard_config
            else None
        )
    suite = _load_selected_tests(selected_ids)
    started = time.perf_counter()
    with repository_import_path(ROOT):
        result = unittest.TextTestRunner(verbosity=2, resultclass=TimedTextResult).run(suite)
    duration = max(0.0, time.perf_counter() - started)
    sha = git_sha()
    runner_os = os.environ.get("RUNNER_OS", platform.system())
    python_version = platform.python_version()
    records = sorted(result.records, key=lambda item: str(item["test_id"]))
    for record in records:
        record.update({"sha": sha, "os": runner_os, "python": python_version, "shard": shard_id})
    record_ids = [str(item["test_id"]) for item in records]
    budget_exceeded = budget_seconds is not None and duration > budget_seconds
    successful = result.wasSuccessful() and record_ids == selected_ids and not budget_exceeded
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_type": "orrery-test-shard-result-v1",
        "role": role,
        "sha": sha,
        "os": runner_os,
        "python": python_version,
        "shard": shard_id,
        "manifest_sha256": sha256_json(manifest),
        "inventory_sha256": sha256_json(all_ids),
        "orrery_test_build": os.environ.get("ORRERY_TEST_BUILD"),
        "selected_test_count": len(selected_ids),
        "selected_test_ids": selected_ids,
        "records": records,
        "tests_run": result.testsRun,
        "successful": successful,
        "completed": True,
        "duration_seconds": round(duration, 6),
        "budget_seconds": budget_seconds,
        "budget_exceeded": budget_exceeded,
        "runner_errors": [test.id() for test, _ in result.errors if test.id() not in selected_ids],
    }
    atomic_write_json(output, payload)
    return payload, successful


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an exact unittest shard and emit timing JSON")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--shard")
    group.add_argument("--profile", choices=("fast", "checkpoint"))
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        payload, successful = run_selected(
            manifest_path=arguments.manifest.resolve(),
            shard=arguments.shard,
            profile=arguments.profile,
            output=arguments.output.resolve(),
        )
        print(
            f"{'PASS' if successful else 'FAIL'} {payload['role']} {payload['shard']}: "
            f"{payload['tests_run']}/{payload['selected_test_count']} tests in {payload['duration_seconds']}s"
        )
        return 0 if successful else 1
    except CIValidationError as exc:
        print(f"FAIL shard runner: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
