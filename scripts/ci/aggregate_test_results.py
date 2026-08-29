from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    atomic_write_json,
    git_sha,
    load_json,
    promotion_lane_assignments,
    sha256_json,
    validate_and_expand_manifest,
)


PASSING_OUTCOMES = {"success", "skipped", "expected-failure"}


def aggregate(
    *,
    manifest_path: Path,
    results_dir: Path,
    expected_os: str,
    expected_sha: str,
    matrix_result: str,
    gate_result: str,
) -> dict[str, object]:
    errors: list[str] = []
    if matrix_result != "success":
        errors.append(f"shard matrix result is {matrix_result!r}, not 'success'")
    if gate_result != "success":
        errors.append(f"repository gate result is {gate_result!r}, not 'success'")
    current_sha = git_sha()
    expected_sha = expected_sha.lower()
    if current_sha != expected_sha:
        errors.append(f"aggregator HEAD {current_sha} does not equal expected SHA {expected_sha}")
    manifest = load_json(manifest_path)
    all_ids, assignments, _ = validate_and_expand_manifest(manifest)
    lanes = promotion_lane_assignments(manifest)
    expected_manifest_hash = sha256_json(manifest)
    expected_inventory_hash = sha256_json(all_ids)
    payloads: list[dict[str, Any]] = []
    lane_payloads: list[dict[str, Any]] = []
    for path in sorted(results_dir.rglob("*.json")):
        try:
            payload = load_json(path)
        except CIValidationError as exc:
            errors.append(str(exc))
            continue
        if payload.get("contract_type") == "orrery-test-shard-result-v1":
            payload["_path"] = str(path)
            payloads.append(payload)
        elif payload.get("contract_type") == "orrery-test-lane-result-v1":
            payload["_path"] = str(path)
            lane_payloads.append(payload)
    by_lane: dict[str, list[dict[str, Any]]] = {}
    for payload in lane_payloads:
        by_lane.setdefault(str(payload.get("lane")), []).append(payload)
    expected_lanes = set(lanes)
    actual_lanes = set(by_lane)
    missing_lanes = sorted(expected_lanes - actual_lanes)
    extra_lanes = sorted(actual_lanes - expected_lanes)
    if missing_lanes:
        errors.append(f"missing lane artifacts: {missing_lanes}")
    if extra_lanes:
        errors.append(f"unexpected lane artifacts: {extra_lanes}")
    for lane_id, items in sorted(by_lane.items()):
        if len(items) != 1:
            errors.append(f"lane {lane_id} has {len(items)} artifacts; expected exactly one")
            continue
        payload = items[0]
        if payload.get("sha") != expected_sha:
            errors.append(f"lane {lane_id} SHA mismatch: {payload.get('sha')!r}")
        if payload.get("os") != expected_os:
            errors.append(f"lane {lane_id} OS mismatch: {payload.get('os')!r}")
        if payload.get("manifest_sha256") != expected_manifest_hash:
            errors.append(f"lane {lane_id} manifest hash mismatch")
        if payload.get("completed") is not True or payload.get("successful") is not True:
            errors.append(f"lane {lane_id} was incomplete or unsuccessful")
        expected_lane_shards = lanes.get(lane_id, [])
        if payload.get("shards") != expected_lane_shards:
            errors.append(f"lane {lane_id} shard list differs from the current manifest")
        records = payload.get("records")
        record_shards = (
            [item.get("shard") for item in records if isinstance(item, dict)]
            if isinstance(records, list)
            else []
        )
        if record_shards != expected_lane_shards:
            errors.append(f"lane {lane_id} records are missing, duplicated, or reordered")
        elif any(item.get("successful") is not True for item in records):
            errors.append(f"lane {lane_id} records a failed logical shard")
    by_shard: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        by_shard.setdefault(str(payload.get("shard")), []).append(payload)
    expected_shards = set(assignments)
    actual_shards = set(by_shard)
    missing_shards = sorted(expected_shards - actual_shards)
    extra_shards = sorted(actual_shards - expected_shards)
    if missing_shards:
        errors.append(f"missing shard artifacts: {missing_shards}")
    if extra_shards:
        errors.append(f"unexpected shard artifacts: {extra_shards}")
    for shard_id, items in sorted(by_shard.items()):
        if len(items) != 1:
            errors.append(f"shard {shard_id} has {len(items)} artifacts; expected exactly one")
            continue
        payload = items[0]
        if payload.get("role") != "promotion-shard":
            errors.append(f"shard {shard_id} artifact has non-promotion role")
        if payload.get("sha") != expected_sha:
            errors.append(f"shard {shard_id} SHA mismatch: {payload.get('sha')!r}")
        if payload.get("os") != expected_os:
            errors.append(f"shard {shard_id} OS mismatch: {payload.get('os')!r}")
        if payload.get("manifest_sha256") != expected_manifest_hash:
            errors.append(f"shard {shard_id} manifest hash mismatch")
        if payload.get("inventory_sha256") != expected_inventory_hash:
            errors.append(f"shard {shard_id} inventory hash mismatch")
        if payload.get("orrery_test_build") != "1":
            errors.append(f"shard {shard_id} did not run with ORRERY_TEST_BUILD=1")
        if payload.get("completed") is not True or payload.get("successful") is not True:
            errors.append(f"shard {shard_id} was incomplete or unsuccessful")
        expected_ids = assignments.get(shard_id, [])
        selected_ids = payload.get("selected_test_ids")
        if selected_ids != expected_ids:
            errors.append(f"shard {shard_id} selected test IDs differ from current manifest expansion")
        records = payload.get("records")
        if not isinstance(records, list):
            errors.append(f"shard {shard_id} records are missing")
            continue
        record_ids = [item.get("test_id") for item in records if isinstance(item, dict)]
        if record_ids != expected_ids:
            errors.append(f"shard {shard_id} result records are missing, duplicated, or reordered")
        for item in records:
            if not isinstance(item, dict) or item.get("outcome") not in PASSING_OUTCOMES:
                errors.append(f"shard {shard_id} has a non-passing or invalid test outcome")
                break
            if (
                item.get("sha") != expected_sha
                or item.get("os") != expected_os
                or item.get("python") != payload.get("python")
                or item.get("shard") != shard_id
                or not isinstance(item.get("duration_seconds"), (int, float))
                or item.get("duration_seconds", -1) < 0
            ):
                errors.append(f"shard {shard_id} has an invalid per-test timing binding")
                break
    all_record_ids = [
        str(item.get("test_id"))
        for payload in payloads
        for item in payload.get("records", [])
        if isinstance(item, dict)
    ]
    counts = Counter(all_record_ids)
    duplicates = sorted(test_id for test_id, count in counts.items() if count != 1)
    missing_tests = sorted(set(all_ids) - set(counts))
    extra_tests = sorted(set(counts) - set(all_ids))
    if duplicates:
        errors.append(f"test IDs did not execute exactly once: {duplicates}")
    if missing_tests:
        errors.append(f"test IDs missing from Promotion artifacts: {missing_tests}")
    if extra_tests:
        errors.append(f"unknown test IDs in Promotion artifacts: {extra_tests}")
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_type": "orrery-promotion-aggregate-v1",
        "sha": expected_sha,
        "os": expected_os,
        "matrix_result": matrix_result,
        "gate_result": gate_result,
        "manifest_sha256": expected_manifest_hash,
        "inventory_sha256": expected_inventory_hash,
        "expected_shard_count": len(assignments),
        "artifact_shard_count": len(payloads),
        "expected_lane_count": len(lanes),
        "artifact_lane_count": len(lane_payloads),
        "expected_test_count": len(all_ids),
        "recorded_test_count": len(all_record_ids),
        "complete": not errors,
        "errors": errors,
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed aggregation of Promotion shard artifacts")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--expected-os", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--matrix-result", required=True)
    parser.add_argument("--gate-result", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        payload = aggregate(
            manifest_path=arguments.manifest.resolve(),
            results_dir=arguments.results_dir.resolve(),
            expected_os=arguments.expected_os,
            expected_sha=arguments.expected_sha,
            matrix_result=arguments.matrix_result,
            gate_result=arguments.gate_result,
        )
        atomic_write_json(arguments.output.resolve(), payload)
        if payload["complete"]:
            print(
                f"PASS Promotion aggregate {payload['os']}: "
                f"{payload['recorded_test_count']} tests across {payload['artifact_shard_count']} shards"
            )
            return 0
        print("FAIL Promotion aggregate:", file=sys.stderr)
        for error in payload["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1
    except CIValidationError as exc:
        print(f"FAIL Promotion aggregate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
