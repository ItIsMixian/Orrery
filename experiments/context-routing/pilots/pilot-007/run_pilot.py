#!/usr/bin/env python3
"""Prepare, run, audit, and seal the Pilot 007 P/B adoption comparison."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


PILOT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PILOT_DIR.parents[3]
BASE_RUNNER_PATH = PILOT_DIR.parent / "pilot-005" / "run_pilot.py"
ORACLE_PATH = PILOT_DIR / "operator" / "acceptance.py"

spec = importlib.util.spec_from_file_location("orrery_pilot_005_runner_for_007", BASE_RUNNER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load frozen Pilot 005 runner")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def export_baseline(destination: Path, commit: str) -> None:
    result = base.run_command(
        ["git", "clone", "--no-checkout", "--no-local", str(REPOSITORY_ROOT), str(destination)],
        cwd=REPOSITORY_ROOT,
        timeout=240,
    )
    if result.returncode:
        raise RuntimeError("cannot clone frozen baseline: " + (result.stdout + result.stderr).strip())
    for command in (
        ["git", "checkout", "--detach", commit],
        ["git", "switch", "-c", "benchmark"],
        ["git", "remote", "remove", "origin"],
    ):
        completed = base.run_command(command, cwd=destination)
        if completed.returncode:
            raise RuntimeError("cannot position baseline: " + (completed.stdout + completed.stderr).strip())


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


def _agent_messages(events: list[dict[str, Any]]) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for index, event in enumerate(events):
        item = event.get("item")
        if event.get("type") == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            rows.append((index, str(item.get("text") or item.get("content") or "")))
    return rows


def protocol_check(events: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    messages = _agent_messages(events)
    reads: list[tuple[int, str]] = []
    for index, event in enumerate(events):
        item = event.get("item")
        if event.get("type") != "item.completed" or not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        command = str(item.get("command", "")).replace("\\", "/")
        if "context_read_proxy.py read" in command:
            reads.append((index, command))
    joined = "\n".join(text for _, text in messages)
    first_index = reads[0][0] if reads else 10**12
    before = "\n".join(text for index, text in messages if index < first_index)
    failures: list[str] = []
    if variant == "P":
        for forbidden in ("CONTEXT MANIFEST", "SCOPE EXPANSION", "SELECTED EVIDENCE", "ACCESS SUMMARY"):
            if forbidden in joined:
                failures.append(f"P emitted forbidden protocol prose: {forbidden}")
    elif variant == "B":
        if "CONTEXT MANIFEST" not in before:
            failures.append("B did not emit Context Manifest before first content read")
        if not messages or "ACCESS SUMMARY" not in messages[-1][1]:
            failures.append("B final Agent message has no Access Summary")
        for index, command in reads:
            match = re.search(r"--path\s+[\"']?([^\s\"']+)", command)
            path = match.group(1) if match else ""
            prior_messages = [text for message_index, text in messages if message_index < index]
            latest = prior_messages[-1] if prior_messages else ""
            if "--reason" in command:
                if "SCOPE EXPANSION" not in latest or (path and path not in latest.replace("\\", "/")):
                    failures.append(f"B read expansion without matching declaration: {path or command}")
            elif path and path not in before.replace("\\", "/"):
                failures.append(f"B initial read was absent from Context Manifest: {path}")
    else:
        failures.append(f"unknown variant: {variant}")
    return {"passed": not failures, "failures": failures}


def protocol_self_test() -> None:
    def message(text: str) -> dict[str, Any]:
        return {"type": "item.completed", "item": {"type": "agent_message", "text": text}}

    def command(value: str) -> dict[str, Any]:
        return {"type": "item.completed", "item": {"type": "command_execution", "command": value}}

    valid_b = [
        message("CONTEXT MANIFEST\ninitial_reads:\n- README.md — task evidence"),
        command("python .benchmark/context_read_proxy.py read --path README.md --start 1 --end 20"),
        message("SCOPE EXPANSION\npath: tests/test_project_orrery.py\nreason_code: dependency-found\nreason: test contract"),
        command("python .benchmark/context_read_proxy.py read --path tests/test_project_orrery.py --start 1 --end 20 --reason dependency-found"),
        message("implemented\nACCESS SUMMARY\ncontent_reads: README.md; tests/test_project_orrery.py\nscope_expansions: tests/test_project_orrery.py"),
    ]
    if not protocol_check(valid_b, "B")["passed"]:
        raise RuntimeError("protocol self-test rejected a valid B transcript")
    if protocol_check(valid_b[1:], "B")["passed"]:
        raise RuntimeError("protocol self-test accepted B without a pre-read Manifest")
    if not protocol_check([message("implemented")], "P")["passed"]:
        raise RuntimeError("protocol self-test rejected a valid P transcript")
    if protocol_check([message("CONTEXT MANIFEST\nnot allowed")], "P")["passed"]:
        raise RuntimeError("protocol self-test accepted B prose in P")


def preflight(config: dict[str, Any]) -> None:
    if config.get("pilot_id") != "pilot-007" or config.get("variants") != ["P", "B"]:
        raise RuntimeError("unexpected Pilot 007 configuration")
    if config.get("evidence_mode") != "codex-exec-jsonl-posthoc":
        raise RuntimeError("Pilot 007 requires post-hoc complete JSONL evidence")
    commit = base.run_command(["git", "cat-file", "-e", f"{config['baseline_commit']}^{{commit}}"], cwd=REPOSITORY_ROOT)
    if commit.returncode:
        raise RuntimeError("frozen baseline commit is unavailable")
    self_test = base.run_command([sys.executable, "-X", "utf8", str(ORACLE_PATH), "--self-test"], cwd=REPOSITORY_ROOT)
    if self_test.returncode:
        raise RuntimeError("Pilot 007 Oracle self-test failed: " + self_test.stdout + self_test.stderr)
    protocol_self_test()
    if config.get("model") != "gpt-5.6-terra" or config.get("reasoning_effort") != "medium":
        raise RuntimeError("execution profile must remain gpt-5.6-terra / medium")


def control_hashes(config: dict[str, Any]) -> dict[str, str]:
    paths = [
        PILOT_DIR / "pilot-config.json",
        PILOT_DIR / "common-protocol.zh-CN.md",
        PILOT_DIR / "TASK-DESIGN.zh-CN.md",
        PILOT_DIR / "variants/P.zh-CN.md",
        PILOT_DIR / "variants/B.zh-CN.md",
        PILOT_DIR / "run_pilot.py",
        ORACLE_PATH,
        BASE_RUNNER_PATH,
        base.HARNESS / "context_read_proxy.py",
        base.HARNESS / "_common.py",
        base.HARNESS / "validate_cli_events.py",
        base.HARNESS / "seal_raw_evidence.py",
        base.RETENTION_POLICY,
    ]
    paths.extend(PILOT_DIR / task["task_file"] for task in config["tasks"])
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): base.sha256(path) for path in paths}


def _ratio(numerator: float, denominator: float) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def summarize(config: dict[str, Any], rows: list[dict[str, Any]], output_root: Path, hashes: dict[str, str]) -> None:
    original_summarize(config, rows, output_root, hashes)
    path = output_root / "pilot-summary.json"
    summary = base.load_json(path)
    p = summary["variants"]["P"]
    b = summary["variants"]["B"]
    p_usage = p["usage_totals"]; b_usage = b["usage_totals"]
    ratios = {
        "input": _ratio(float(b_usage.get("input_tokens", 0)), float(p_usage.get("input_tokens", 0))),
        "output": _ratio(float(b_usage.get("output_tokens", 0)), float(p_usage.get("output_tokens", 0))),
        "agent_seconds": _ratio(float(b["agent_seconds_total"]), float(p["agent_seconds_total"])),
        "proxy_bytes": _ratio(float(b["proxy_returned_bytes_total"]), float(p["proxy_returned_bytes_total"])),
    }
    gates = config["adoption_gate"]
    p_passes = p["candidate_passed"]
    b_passes = b["candidate_passed"]
    p_only_high_risk = [
        row["task_id"] for row in rows
        if row["variant"] == "P" and row["candidate_passed"]
        and next(task for task in config["tasks"] if task["task_id"] == row["task_id"])["risk"] == "high"
        and not any(other["task_id"] == row["task_id"] and other["variant"] == "B" and other["candidate_passed"] for other in rows)
    ]
    checks = {
        "b_required_passes": b_passes == gates["b_required_passes"],
        "b_not_below_p": b_passes >= p_passes,
        "no_p_only_high_risk_success": not p_only_high_risk,
        "all_b_apparatus_valid": b["apparatus_valid"] == b["runs"],
        "input_cost": ratios["input"] is not None and ratios["input"] <= gates["b_input_ratio_max"],
        "output_cost": ratios["output"] is not None and ratios["output"] <= gates["b_output_ratio_max"],
        "time_cost": ratios["agent_seconds"] is not None and ratios["agent_seconds"] <= gates["b_agent_seconds_ratio_max"],
        "direct_proxy_benefit": ratios["proxy_bytes"] is not None and ratios["proxy_bytes"] <= gates["b_proxy_bytes_ratio_max_for_direct_benefit"],
    }
    summary["adoption_gate_evaluation"] = {
        "ratios": ratios,
        "p_only_high_risk_tasks": p_only_high_risk,
        "checks": checks,
        "automated_gate_passed": all(checks.values()),
        "maintainer_acceptance_required": True,
        "note": "An independently reviewed necessary-dependency recall gain may replace direct_proxy_benefit only in a separate R2 review.",
    }
    base.write_json(path, summary)
    markdown = output_root / "pilot-summary.md"
    text = markdown.read_text(encoding="utf-8")
    text = text.replace("# Pilot 005 B/H2 raw comparison", "# Pilot 007 P/B adoption raw comparison")
    text += "\n## Automated adoption gate\n\n```json\n" + json.dumps(summary["adoption_gate_evaluation"], ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"
    markdown.write_text(text, encoding="utf-8", newline="\n")


base.PILOT_DIR = PILOT_DIR
base.CONFIG_PATH = PILOT_DIR / "pilot-config.json"
base.ORACLE = ORACLE_PATH
base.export_baseline = export_baseline
base.initialize_repository = initialize_repository
base.preflight = preflight
base.protocol_check = protocol_check
original_prepare_run = base.prepare_run
base.prepare_run = prepare_run
base.control_hashes = control_hashes
original_summarize = base.summarize
base.summarize = summarize


if __name__ == "__main__":
    raise SystemExit(base.main())
