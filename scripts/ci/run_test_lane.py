from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from collections.abc import Callable

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    atomic_write_json,
    git_sha,
    load_json,
    promotion_lane_assignments,
    sha256_json,
    validate_and_expand_manifest,
)


SHARD_RUNNER = Path(__file__).with_name("run_test_shard.py")


def run_lane(
    *,
    manifest_path: Path,
    lane: str,
    output_dir: Path,
    runner_script: Path = SHARD_RUNNER,
    executor: Callable[[list[str]], int] | None = None,
) -> tuple[dict[str, object], bool]:
    manifest = load_json(manifest_path)
    validate_and_expand_manifest(manifest)
    lanes = promotion_lane_assignments(manifest)
    if lane not in lanes:
        raise CIValidationError(f"unknown Promotion lane: {lane}")
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    records: list[dict[str, object]] = []
    all_successful = True
    for shard in lanes[lane]:
        result_path = output_dir / f"result-{shard}.json"
        command = [
            sys.executable,
            str(runner_script),
            "--manifest",
            str(manifest_path),
            "--shard",
            shard,
            "--output",
            str(result_path),
        ]
        error: str | None = None
        try:
            return_code: int | None = (
                executor(command)
                if executor is not None
                else subprocess.run(command, cwd=ROOT, check=False).returncode
            )
        except OSError as exc:
            return_code = None
            error = str(exc)
        result_present = result_path.is_file()
        shard_successful = False
        if result_present:
            try:
                shard_payload = load_json(result_path)
                shard_successful = (
                    return_code == 0
                    and shard_payload.get("contract_type")
                    == "orrery-test-shard-result-v2"
                    and shard_payload.get("shard") == shard
                    and shard_payload.get("successful") is True
                    and shard_payload.get("completed") is True
                )
            except CIValidationError as exc:
                error = str(exc)
        if not shard_successful:
            all_successful = False
        record: dict[str, object] = {
            "shard": shard,
            "return_code": return_code,
            "result_file": result_path.name,
            "result_present": result_present,
            "successful": shard_successful,
        }
        if error:
            record["error"] = error
        records.append(record)
    duration = max(0.0, time.perf_counter() - started)
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_type": "orrery-test-lane-result-v1",
        "sha": git_sha(),
        "os": os.environ.get("RUNNER_OS", platform.system()),
        "python": platform.python_version(),
        "lane": lane,
        "manifest_sha256": sha256_json(manifest),
        "shards": lanes[lane],
        "records": records,
        "successful": all_successful,
        "completed": True,
        "duration_seconds": round(duration, 6),
    }
    atomic_write_json(output_dir / "lane-result.json", payload)
    return payload, all_successful


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one physical Promotion lane while preserving logical shard evidence"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        payload, successful = run_lane(
            manifest_path=arguments.manifest.resolve(),
            lane=arguments.lane,
            output_dir=arguments.output_dir.resolve(),
        )
        print(
            f"{'PASS' if successful else 'FAIL'} Promotion lane {payload['lane']}: "
            f"{len(payload['records'])} logical shards in {payload['duration_seconds']}s"
        )
        return 0 if successful else 1
    except CIValidationError as exc:
        print(f"FAIL Promotion lane: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
