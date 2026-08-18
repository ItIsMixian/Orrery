#!/usr/bin/env python3
"""Prepare, run, independently audit, and seal Pilot 005 B/H2 pairs."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


PILOT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PILOT_DIR.parents[3]
HARNESS = REPOSITORY_ROOT / "experiments" / "context-routing" / "harness"
ORACLE = PILOT_DIR / "operator" / "acceptance.py"
CONFIG_PATH = PILOT_DIR / "pilot-config.json"
RETENTION_POLICY = HARNESS / "raw-evidence-retention-policy.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_command(arguments: list[str], *, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )


def control_hashes(config: dict[str, Any]) -> dict[str, str]:
    paths = [
        CONFIG_PATH,
        PILOT_DIR / "common-protocol.zh-CN.md",
        PILOT_DIR / "TASK-DESIGN.zh-CN.md",
        PILOT_DIR / "variants" / "B.zh-CN.md",
        PILOT_DIR / "variants" / "H2.zh-CN.md",
        PILOT_DIR / "run_pilot.py",
        ORACLE,
        HARNESS / "context_read_proxy.py",
        HARNESS / "_common.py",
        HARNESS / "validate_cli_events.py",
        HARNESS / "hook_audit.py",
        HARNESS / "seal_raw_evidence.py",
        RETENTION_POLICY,
    ]
    paths.extend(PILOT_DIR / task["task_file"] for task in config["tasks"])
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): sha256(path) for path in paths}


def build_prompt(config: dict[str, Any], task: dict[str, Any], variant: str) -> str:
    writes = "\n".join(f"- `{path}`" for path in task["expected_product_write_paths"])
    validation = "\n".join(f"- `{command}`" for command in task["validation_commands"])
    contract = f"""<!-- pilot_id: {config['pilot_id']} -->
<!-- prompt_revision: {config['prompt_revision']} -->
<!-- task_id: {task['task_id']} -->
<!-- variant: {variant} -->

# RUN CONTRACT

- pilot: `{config['pilot_id']}`
- prompt revision: `{config['prompt_revision']}`
- task: `{task['task_id']}`
- variant: `{variant}`
- evidence mode: `{config['evidence_mode']}`
- model/reasoning are fixed by the Harness; do not change them

## 允许的产品写入

{writes}

## 允许的快速反馈命令

{validation}
"""
    pieces = [
        contract,
        (PILOT_DIR / "common-protocol.zh-CN.md").read_text(encoding="utf-8"),
        (PILOT_DIR / task["task_file"]).read_text(encoding="utf-8"),
        (PILOT_DIR / "variants" / f"{variant}.zh-CN.md").read_text(encoding="utf-8"),
    ]
    return "\n\n---\n\n".join(piece.strip() for piece in pieces) + "\n"


def export_baseline(destination: Path, commit: str) -> None:
    archive = destination.parent / (destination.name + ".zip")
    result = run_command(
        ["git", "archive", "--format=zip", f"--output={archive}", commit],
        cwd=REPOSITORY_ROOT,
    )
    if result.returncode or not archive.is_file():
        raise RuntimeError("cannot export frozen baseline: " + (result.stdout + result.stderr).strip())
    destination.mkdir(parents=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(destination)
    archive.unlink()


def initialize_repository(repository: Path) -> None:
    commands = (
        ["git", "init", "-b", "benchmark"],
        ["git", "add", "--all"],
        ["git", "-c", "user.name=Project Orrery Benchmark", "-c", "user.email=benchmark@local.invalid", "commit", "-m", "frozen pilot-005 baseline"],
    )
    for command in commands:
        result = run_command(command, cwd=repository)
        if result.returncode:
            raise RuntimeError("isolated Git initialization failed: " + (result.stdout + result.stderr).strip())
    exclude = repository / ".git" / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    exclude.write_text(existing.rstrip() + "\n.benchmark/\n", encoding="utf-8", newline="\n")


def prepare_run(output_root: Path, config: dict[str, Any], task: dict[str, Any], variant: str) -> dict[str, Any]:
    run_id = f"{task['task_id']}-{variant}"
    run_root = output_root / run_id
    if run_root.exists():
        raise RuntimeError(f"refusing to overwrite existing raw run: {run_root}")
    operator = run_root / "_operator"
    repository = run_root / "repository"
    operator.mkdir(parents=True)
    export_baseline(repository, config["baseline_commit"])
    initialize_repository(repository)
    benchmark = repository / ".benchmark"
    benchmark.mkdir()
    shutil.copy2(HARNESS / "context_read_proxy.py", benchmark / "context_read_proxy.py")
    shutil.copy2(HARNESS / "_common.py", benchmark / "_common.py")
    write_json(benchmark / "access-state.json", {"schema_version": 1, "phase": "prewrite", "read_ranges": {}})
    (benchmark / "proxy-audit.jsonl").write_text("", encoding="utf-8")
    policy = {
        "schema_version": 1,
        "proxy_script": ".benchmark/context_read_proxy.py",
        "allowed_non_content_tools": ["update_plan"],
        "postwrite_commands": task["validation_commands"],
        "expected_write_paths": task["expected_product_write_paths"],
        "minimum_content_reads": 1,
    }
    write_json(operator / "access-policy.json", policy)
    prompt = build_prompt(config, task, variant)
    (operator / "prompt.zh-CN.md").write_text(prompt, encoding="utf-8", newline="\n")
    metadata = {
        "schema_version": 1,
        "pilot_id": config["pilot_id"],
        "prompt_revision": config["prompt_revision"],
        "run_id": run_id,
        "task_id": task["task_id"],
        "variant": variant,
        "baseline_commit": config["baseline_commit"],
        "model": config["model"],
        "reasoning_effort": config["reasoning_effort"],
        "evidence_mode": config["evidence_mode"],
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "expected_product_write_paths": task["expected_product_write_paths"],
        "validation_commands": task["validation_commands"],
    }
    write_json(operator / "run-metadata.json", metadata)
    return {"run_id": run_id, "run_root": run_root, "operator": operator, "repository": repository, "prompt": prompt, "task": task, "variant": variant}


def parse_events(path: Path) -> tuple[dict[str, int], int, int, list[dict[str, Any]]]:
    usage: dict[str, int] = {}
    events: list[dict[str, Any]] = []
    malformed = 0
    if not path.is_file():
        return usage, 0, 0, events
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        events.append(event)
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = {str(key): int(value) for key, value in event["usage"].items() if isinstance(value, int) and not isinstance(value, bool)}
    return usage, len(events), malformed, events


def protocol_check(events: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    messages: list[tuple[int, str]] = []
    first_content_read = None
    for index, event in enumerate(events):
        item = event.get("item")
        if not isinstance(item, dict) or event.get("type") != "item.completed":
            continue
        if item.get("type") == "agent_message":
            text = item.get("text") or item.get("content") or ""
            messages.append((index, str(text)))
        elif item.get("type") == "command_execution" and first_content_read is None:
            command = str(item.get("command", "")).replace("\\", "/")
            if "context_read_proxy.py read" in command:
                first_content_read = index
    joined = "\n".join(text for _, text in messages)
    before = "\n".join(text for index, text in messages if first_content_read is None or index < first_content_read)
    failures: list[str] = []
    if variant == "B":
        if "CONTEXT MANIFEST" not in before:
            failures.append("B did not emit Context Manifest before its first command")
        if "ACCESS SUMMARY" not in joined:
            failures.append("B did not emit final Access Summary")
    else:
        for forbidden in ("CONTEXT MANIFEST", "SELECTED EVIDENCE", "ACCESS SUMMARY", "SCOPE EXPANSION"):
            if forbidden in joined:
                failures.append(f"H2 emitted forbidden protocol prose: {forbidden}")
    return {"passed": not failures, "failures": failures}


def changed_paths(repository: Path) -> list[str]:
    result = run_command(["git", "status", "--porcelain=v1", "-z"], cwd=repository)
    if result.returncode:
        return ["<git-status-failed>"]
    paths: list[str] = []
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        value = entry[3:] if len(entry) > 3 else entry
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        if not value.startswith(".benchmark/"):
            paths.append(value.replace("\\", "/"))
    return sorted(set(paths))


def execute_validation(repository: Path, commands: list[str], output: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for command in commands:
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=repository,
            shell=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=180,
        )
        rows.append({
            "command": command,
            "exit_code": completed.returncode,
            "seconds": round(time.perf_counter() - started, 3),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
    result = {"passed": all(row["exit_code"] == 0 for row in rows), "commands": rows}
    write_json(output, result)
    return result


def execute_agent(run: dict[str, Any], config: dict[str, Any], codex: Path) -> dict[str, Any]:
    operator: Path = run["operator"]
    repository: Path = run["repository"]
    events_path = operator / "events.jsonl"
    stderr_path = operator / "stderr.log"
    final_path = operator / "final-message.txt"
    command = [
        str(codex), "exec", "--ephemeral", "--json", "--ignore-user-config", "--ignore-rules",
        "--approve-for-me", "--model", config["model"], "-c", f'model_reasoning_effort="{config["reasoning_effort"]}"',
        "-c", "sandbox_workspace_write.network_access=false", "-C", str(repository), "-o", str(final_path), "-",
    ]
    environment = os.environ.copy()
    environment.update({
        "ORRERY_BENCHMARK_REPO_ROOT": str(repository),
        "ORRERY_PROXY_AUDIT_LOG": str(repository / ".benchmark" / "proxy-audit.jsonl"),
        "ORRERY_ACCESS_STATE": str(repository / ".benchmark" / "access-state.json"),
        "PYTHONUTF8": "1",
    })
    started_at = now_iso()
    started = time.perf_counter()
    timed_out = False
    exit_code: int | None = None
    spawn_error: str | None = None
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with events_path.open("w", encoding="utf-8", newline="\n") as stdout_handle, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr_handle:
        try:
            process = subprocess.Popen(
                command,
                cwd=repository,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
            )
            try:
                process.communicate(run["prompt"], timeout=int(config["timeout_minutes"]) * 60)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False) if os.name == "nt" else process.kill()
                process.communicate()
                exit_code = process.returncode
        except OSError as exc:
            spawn_error = f"{type(exc).__name__}: {exc}"
    ended_at = now_iso()
    usage, event_count, malformed, events = parse_events(events_path)
    result = {
        "started_at": started_at,
        "ended_at": ended_at,
        "agent_seconds": round(time.perf_counter() - started, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "spawn_error": spawn_error,
        "usage": usage,
        "event_count": event_count,
        "malformed_event_count": malformed,
    }
    write_json(operator / "agent-result.json", result)
    write_json(operator / "protocol-check.json", protocol_check(events, run["variant"]))
    return result


def finish_run(run: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    operator: Path = run["operator"]
    repository: Path = run["repository"]
    agent = load_json(operator / "agent-result.json")
    audit_path = operator / "access-audit.json"
    audit = run_command(
        [
            sys.executable, "-X", "utf8", str(HARNESS / "validate_cli_events.py"),
            "--events", str(operator / "events.jsonl"),
            "--proxy-log", str(repository / ".benchmark" / "proxy-audit.jsonl"),
            "--policy", str(operator / "access-policy.json"),
            "--output", str(audit_path),
        ],
        cwd=REPOSITORY_ROOT,
    )
    access = load_json(audit_path) if audit_path.is_file() else {"apparatus_valid": False, "validator_error": audit.stdout + audit.stderr}
    acceptance_path = operator / "acceptance.json"
    acceptance_run = run_command(
        [sys.executable, "-X", "utf8", str(ORACLE), "--repository", str(repository), "--task-id", run["task"]["task_id"], "--output", str(acceptance_path)],
        cwd=REPOSITORY_ROOT,
        timeout=240,
    )
    acceptance = load_json(acceptance_path) if acceptance_path.is_file() else {"passed": False, "apparatus_errors": [acceptance_run.stdout + acceptance_run.stderr]}
    validation = execute_validation(repository, run["task"]["validation_commands"], operator / "formal-validation.json")
    protocol = load_json(operator / "protocol-check.json")
    paths = changed_paths(repository)
    expected = set(run["task"]["expected_product_write_paths"])
    unexpected = sorted(set(paths) - expected)
    apparatus_valid = bool(access.get("apparatus_valid")) and not acceptance.get("apparatus_errors") and not agent.get("spawn_error") and not agent.get("timed_out") and agent.get("exit_code") == 0 and not unexpected and agent.get("malformed_event_count") == 0
    proxy_events = []
    proxy_path = repository / ".benchmark" / "proxy-audit.jsonl"
    for line in proxy_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            try: proxy_events.append(json.loads(line))
            except json.JSONDecodeError: pass
    reads = [event for event in proxy_events if event.get("operation") == "read"]
    summary = {
        "run_id": run["run_id"],
        "task_id": run["task"]["task_id"],
        "variant": run["variant"],
        "classification": "decision_supporting" if apparatus_valid else "contaminated",
        "apparatus_valid": apparatus_valid,
        "candidate_passed": bool(acceptance.get("passed")) and validation["passed"] and protocol["passed"],
        "operator_acceptance_passed": bool(acceptance.get("passed")),
        "formal_validation_passed": validation["passed"],
        "protocol_passed": protocol["passed"],
        "changed_paths": paths,
        "unexpected_changed_paths": unexpected,
        "content_reads": len(reads),
        "unique_content_paths": len({event.get("path") for event in reads}),
        "expansion_reads": sum(bool(event.get("expansion")) for event in reads),
        "proxy_returned_bytes": sum(int(event.get("returned_bytes", 0)) for event in reads),
        "prompt_bytes": load_json(operator / "run-metadata.json")["prompt_bytes"],
        "usage": agent.get("usage", {}),
        "agent_seconds": agent.get("agent_seconds"),
        "access_audit": access,
        "acceptance": acceptance,
        "protocol": protocol,
    }
    usage = summary["usage"]
    summary["non_cached_input_tokens"] = max(0, int(usage.get("input_tokens", 0)) - int(usage.get("cached_input_tokens", 0)))
    write_json(operator / "run-summary.json", summary)
    seal = run_command(
        [
            sys.executable, "-X", "utf8", str(HARNESS / "seal_raw_evidence.py"), "seal",
            "--run-root", str(run["run_root"]), "--policy", str(RETENTION_POLICY),
            "--pilot-id", config["pilot_id"], "--run-id", run["run_id"],
            "--classification", summary["classification"], "--source-commit", config["baseline_commit"],
            "--apparatus-version", config["prompt_revision"], "--created-at", agent["started_at"],
        ],
        cwd=REPOSITORY_ROOT,
        timeout=240,
    )
    if seal.returncode:
        raise RuntimeError(f"failed to seal {run['run_id']}: " + (seal.stdout + seal.stderr).strip())
    return summary


def summarize(config: dict[str, Any], rows: list[dict[str, Any]], output_root: Path, hashes: dict[str, str]) -> None:
    variants: dict[str, Any] = {}
    for variant in config["variants"]:
        selected = [row for row in rows if row["variant"] == variant]
        token_keys = sorted({key for row in selected for key in row["usage"]})
        variants[variant] = {
            "runs": len(selected),
            "apparatus_valid": sum(row["apparatus_valid"] for row in selected),
            "candidate_passed": sum(row["candidate_passed"] for row in selected),
            "usage_totals": {key: sum(int(row["usage"].get(key, 0)) for row in selected) for key in token_keys},
            "non_cached_input_tokens_total": sum(row["non_cached_input_tokens"] for row in selected),
            "proxy_returned_bytes_total": sum(row["proxy_returned_bytes"] for row in selected),
            "prompt_bytes_total": sum(row["prompt_bytes"] for row in selected),
            "agent_seconds_total": round(sum(float(row["agent_seconds"] or 0) for row in selected), 3),
            "content_reads_total": sum(row["content_reads"] for row in selected),
            "unique_content_paths_total": sum(row["unique_content_paths"] for row in selected),
            "expansion_reads_total": sum(row["expansion_reads"] for row in selected),
        }
    summary = {
        "schema_version": 1,
        "pilot_id": config["pilot_id"],
        "prompt_revision": config["prompt_revision"],
        "generated_at": now_iso(),
        "baseline_commit": config["baseline_commit"],
        "model": config["model"],
        "reasoning_effort": config["reasoning_effort"],
        "control_hashes": hashes,
        "variants": variants,
        "runs": rows,
    }
    write_json(output_root / "pilot-summary.json", summary)
    lines = [
        "# Pilot 005 B/H2 raw comparison", "",
        f"> Generated: `{summary['generated_at']}`  ",
        f"> Model: `{config['model']}` / `{config['reasoning_effort']}`  ",
        "> This raw view is not an ADR or product policy.", "",
        "| Variant | Apparatus valid | Candidate pass | Input | Cached input | Non-cached input | Output | Proxy bytes | Agent seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in config["variants"]:
        item = variants[variant]; usage = item["usage_totals"]
        lines.append(
            f"| {variant} | {item['apparatus_valid']}/{item['runs']} | {item['candidate_passed']}/{item['runs']} | "
            f"{usage.get('input_tokens', 0)} | {usage.get('cached_input_tokens', 0)} | {item['non_cached_input_tokens_total']} | "
            f"{usage.get('output_tokens', 0)} | {item['proxy_returned_bytes_total']} | {item['agent_seconds_total']} |"
        )
    lines.extend(["", "## Runs", "", "| Run | Valid | Pass | Reads/unique/expansion | Changed paths |", "|---|---:|---:|---|---|"])
    for row in rows:
        changed = "<br>".join(f"`{path}`" for path in row["changed_paths"]) or "—"
        lines.append(f"| {row['run_id']} | {row['apparatus_valid']} | {row['candidate_passed']} | {row['content_reads']}/{row['unique_content_paths']}/{row['expansion_reads']} | {changed} |")
    (output_root / "pilot-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def preflight(config: dict[str, Any]) -> None:
    if config.get("pilot_id") != "pilot-005" or config.get("evidence_mode") != "codex-exec-jsonl-posthoc":
        raise RuntimeError("unexpected Pilot 005 configuration")
    commit = run_command(["git", "cat-file", "-e", f"{config['baseline_commit']}^{{commit}}"], cwd=REPOSITORY_ROOT)
    if commit.returncode:
        raise RuntimeError("frozen baseline commit is unavailable")
    self_test = run_command([sys.executable, "-X", "utf8", str(ORACLE), "--self-test"], cwd=REPOSITORY_ROOT)
    if self_test.returncode:
        raise RuntimeError("operator Oracle self-test failed: " + self_test.stdout + self_test.stderr)
    if config.get("model") != "gpt-5.6-terra" or config.get("reasoning_effort") != "medium":
        raise RuntimeError("execution profile must remain gpt-5.6-terra / medium")


def dry_run(config: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="orrery-p005-preflight-") as temporary:
        root = Path(temporary)
        baseline = root / "baseline"
        export_baseline(baseline, config["baseline_commit"])
        for task in config["tasks"]:
            result = run_command([sys.executable, "-X", "utf8", str(ORACLE), "--repository", str(baseline), "--task-id", task["task_id"]], cwd=REPOSITORY_ROOT, timeout=240)
            if result.returncode != 1:
                raise RuntimeError(f"baseline negative control for {task['task_id']} returned {result.returncode}: {result.stdout}{result.stderr}")
        for task in config["tasks"]:
            for variant in config["variants"]:
                prompt = build_prompt(config, task, variant)
                if task["task_id"] not in prompt or f"variant: `{variant}`" not in prompt:
                    raise RuntimeError("generated Prompt lost its run contract")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--codex", type=Path, default=Path(r"D:\Tools\Codex\npm\codex.cmd"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config = load_json(CONFIG_PATH)
    preflight(config)
    dry_run(config)
    hashes = control_hashes(config)
    if args.dry_run:
        print(json.dumps({"pilot": config["pilot_id"], "dry_run": "passed", "control_hashes": hashes}, ensure_ascii=False, indent=2))
        return 0
    if args.output_root is None:
        parser.error("--output-root is required unless --dry-run is used")
    output_root = args.output_root.expanduser().resolve()
    if output_root.exists():
        raise RuntimeError(f"refusing to overwrite existing output root: {output_root}")
    if not args.codex.is_file():
        raise RuntimeError(f"Codex CLI not found: {args.codex}")
    output_root.mkdir(parents=True)
    write_json(output_root / "frozen-control.json", {"config": config, "control_hashes": hashes, "frozen_at": now_iso()})
    tasks = list(config["tasks"])
    random.Random(int(config["task_order_seed"])).shuffle(tasks)
    rows: list[dict[str, Any]] = []
    for task in tasks:
        prepared = [prepare_run(output_root, config, task, variant) for variant in config["variants"]]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(execute_agent, run, config, args.codex) for run in prepared]
            for future in futures:
                future.result()
        for run in prepared:
            row = finish_run(run, config)
            rows.append(row)
            print(f"{row['run_id']}: apparatus={row['apparatus_valid']} acceptance={row['candidate_passed']} classification={row['classification']}", flush=True)
    rows.sort(key=lambda row: (row["task_id"], config["variants"].index(row["variant"])))
    summarize(config, rows, output_root, hashes)
    print(output_root / "pilot-summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
