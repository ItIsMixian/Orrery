#!/usr/bin/env python3
"""Pilot 006 wrapper over the frozen Pilot 005 runner with corrected isolation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PILOT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PILOT_DIR.parents[3]
BASE_RUNNER_PATH = PILOT_DIR.parent / "pilot-005" / "run_pilot.py"
BASE_ORACLE_PATH = PILOT_DIR.parent / "pilot-005" / "operator" / "acceptance.py"

spec = importlib.util.spec_from_file_location("orrery_pilot_005_runner", BASE_RUNNER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load the frozen Pilot 005 runner")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def export_baseline(destination: Path, commit: str) -> None:
    result = base.run_command(
        ["git", "clone", "--no-checkout", "--no-local", str(REPOSITORY_ROOT), str(destination)],
        cwd=REPOSITORY_ROOT,
        timeout=240,
    )
    if result.returncode:
        raise RuntimeError("cannot clone full-history frozen baseline: " + (result.stdout + result.stderr).strip())
    for command in (
        ["git", "checkout", "--detach", commit],
        ["git", "switch", "-c", "benchmark"],
        ["git", "remote", "remove", "origin"],
    ):
        completed = base.run_command(command, cwd=destination)
        if completed.returncode:
            raise RuntimeError("cannot position full-history baseline: " + (completed.stdout + completed.stderr).strip())


def initialize_repository(repository: Path) -> None:
    exclude = repository / ".git" / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    exclude.write_text(existing.rstrip() + "\n.benchmark/\n", encoding="utf-8", newline="\n")


def prepare_run(output_root: Path, config: dict[str, Any], task: dict[str, Any], variant: str) -> dict[str, Any]:
    run = original_prepare_run(output_root, config, task, variant)
    policy_path = run["operator"] / "access-policy.json"
    policy = base.load_json(policy_path)
    policy["repository_root"] = str(run["repository"])
    base.write_json(policy_path, policy)
    return run


def preflight(config: dict[str, Any]) -> None:
    if config.get("pilot_id") != "pilot-006" or config.get("evidence_mode") != "codex-exec-jsonl-posthoc":
        raise RuntimeError("unexpected Pilot 006 configuration")
    commit = base.run_command(["git", "cat-file", "-e", f"{config['baseline_commit']}^{{commit}}"], cwd=REPOSITORY_ROOT)
    if commit.returncode:
        raise RuntimeError("frozen baseline commit is unavailable")
    self_test = base.run_command([sys.executable, "-X", "utf8", str(BASE_ORACLE_PATH), "--self-test"], cwd=REPOSITORY_ROOT)
    if self_test.returncode:
        raise RuntimeError("operator Oracle self-test failed: " + self_test.stdout + self_test.stderr)
    if config.get("model") != "gpt-5.6-terra" or config.get("reasoning_effort") != "medium":
        raise RuntimeError("execution profile must remain gpt-5.6-terra / medium")


def control_hashes(config: dict[str, Any]) -> dict[str, str]:
    hashes = original_control_hashes(config)
    hashes[BASE_RUNNER_PATH.relative_to(REPOSITORY_ROOT).as_posix()] = base.sha256(BASE_RUNNER_PATH)
    return hashes


base.PILOT_DIR = PILOT_DIR
base.CONFIG_PATH = PILOT_DIR / "pilot-config.json"
base.ORACLE = BASE_ORACLE_PATH
base.export_baseline = export_baseline
base.initialize_repository = initialize_repository
base.preflight = preflight
original_prepare_run = base.prepare_run
base.prepare_run = prepare_run
original_control_hashes = base.control_hashes
base.control_hashes = control_hashes


if __name__ == "__main__":
    raise SystemExit(base.main())
