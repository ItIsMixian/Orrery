#!/usr/bin/env python3
"""Prepare and preflight Pilot 009 P/S Scope Acquisition comparisons."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


PILOT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PILOT_DIR.parents[3]
BASE_RUNNER_PATH = PILOT_DIR.parent / "pilot-005" / "run_pilot.py"
ORACLE_PATH = PILOT_DIR / "operator" / "acceptance.py"
FIXTURE_SOURCE = PILOT_DIR / "fixture-source"
S_AGENT_PATH = PILOT_DIR / "variants" / "S-AGENTS.md"
SCOPE_ANALYZER_PATH = REPOSITORY_ROOT / "experiments/context-routing/harness/analyze_scope_acquisition.py"
SCOPE_SMOKE_PATH = REPOSITORY_ROOT / "experiments/context-routing/harness/smoke_app_server_scope_ordering.py"
APP_SERVER_VALIDATOR_PATH = REPOSITORY_ROOT / "experiments/context-routing/harness/validate_app_server_events.py"
DESIGN_PATH = REPOSITORY_ROOT / "experiments/context-routing/designs/scope-acquisition-router-v0.1.zh-CN.md"

spec = importlib.util.spec_from_file_location("orrery_pilot_005_runner_for_009", BASE_RUNNER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load frozen Pilot 005 runner")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

runtime_spec = importlib.util.spec_from_file_location("orrery_app_server_runtime_for_009", SCOPE_SMOKE_PATH)
if runtime_spec is None or runtime_spec.loader is None:
    raise RuntimeError("cannot load app-server runtime helper")
runtime = importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime)


def _git(arguments: list[str], repository: Path, *, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        env=environment,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )


def initialize_fixture_repository(repository: Path) -> str:
    if (repository / ".git").is_dir():
        result = _git(["rev-parse", "HEAD"], repository)
        if result.returncode:
            raise RuntimeError("cannot inspect existing fixture repository")
        return result.stdout.strip()
    commands = (
        ["init", "-b", "pilot-009-fixture"],
        ["config", "core.autocrlf", "false"],
        ["config", "core.filemode", "false"],
        ["add", "--all"],
    )
    for command in commands:
        result = _git(command, repository)
        if result.returncode:
            raise RuntimeError("cannot initialize fixture repository: " + result.stdout + result.stderr)
    environment = os.environ.copy()
    environment.update({
        "GIT_AUTHOR_DATE": "2026-08-19T00:00:00+08:00",
        "GIT_COMMITTER_DATE": "2026-08-19T00:00:00+08:00",
    })
    committed = _git(
        [
            "-c", "user.name=Project Orrery Benchmark",
            "-c", "user.email=benchmark@local.invalid",
            "-c", "commit.gpgsign=false",
            "commit", "-m", "pilot-009 synthetic real-development baseline",
        ],
        repository,
        environment=environment,
    )
    if committed.returncode:
        raise RuntimeError("cannot commit fixture baseline: " + committed.stdout + committed.stderr)
    head = _git(["rev-parse", "HEAD"], repository)
    if head.returncode:
        raise RuntimeError("cannot resolve fixture baseline commit")
    return head.stdout.strip()


def export_baseline(destination: Path, commit: str) -> None:
    shutil.copytree(FIXTURE_SOURCE, destination)
    actual = initialize_fixture_repository(destination)
    if actual != commit:
        raise RuntimeError(f"fixture baseline hash mismatch: config={commit} actual={actual}")


def initialize_repository(repository: Path) -> None:
    actual = initialize_fixture_repository(repository)
    branch = _git(["branch", "--show-current"], repository)
    if branch.returncode or branch.stdout.strip() != "pilot-009-fixture":
        raise RuntimeError("fixture repository is not on the isolated pilot-009-fixture branch")
    if not actual:
        raise RuntimeError("fixture repository has no baseline commit")
    exclude = repository / ".git" / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    if ".benchmark/" not in existing:
        exclude.write_text(existing.rstrip() + "\n.benchmark/\n", encoding="utf-8", newline="\n")


def skill_path(config: dict[str, Any], variant: str) -> Path:
    if variant not in config["variants"]:
        raise RuntimeError(f"unknown Pilot 009 variant: {variant}")
    return REPOSITORY_ROOT / config["shared_skill_path"]


def agent_entry_path(config: dict[str, Any], variant: str) -> Path:
    key = "p_agent_entry_path" if variant == "P" else "s_agent_entry_path"
    return REPOSITORY_ROOT / config[key]


def apply_variant_entry(repository: Path, config: dict[str, Any], variant: str) -> str:
    source = agent_entry_path(config, variant)
    target = repository / "AGENTS.md"
    if variant == "P":
        if base.sha256(target) != config["p_agent_entry_sha256"]:
            raise RuntimeError("P fixture AGENTS entry changed before treatment")
    elif variant == "S":
        target.write_bytes(source.read_bytes())
        added = _git(["add", "AGENTS.md"], repository)
        if added.returncode:
            raise RuntimeError("cannot stage S Agent-entry treatment: " + added.stdout + added.stderr)
        environment = os.environ.copy()
        environment.update({
            "GIT_AUTHOR_DATE": "2026-08-19T00:01:00+08:00",
            "GIT_COMMITTER_DATE": "2026-08-19T00:01:00+08:00",
        })
        committed = _git(
            [
                "-c", "user.name=Project Orrery Benchmark",
                "-c", "user.email=benchmark@local.invalid",
                "-c", "commit.gpgsign=false",
                "commit", "-m", "apply Pilot 009 task-first Agent entry",
            ],
            repository,
            environment=environment,
        )
        if committed.returncode:
            raise RuntimeError("cannot commit S Agent-entry treatment: " + committed.stdout + committed.stderr)
    else:
        raise RuntimeError(f"unknown Pilot 009 variant: {variant}")
    status = _git(["status", "--porcelain"], repository)
    if status.returncode or status.stdout.strip():
        raise RuntimeError(f"{variant} treatment repository is not clean before Harness files")
    head = _git(["rev-parse", "HEAD"], repository)
    if head.returncode:
        raise RuntimeError(f"cannot resolve {variant} treatment commit")
    return head.stdout.strip()


def build_prompt(config: dict[str, Any], task: dict[str, Any], variant: str) -> str:
    prompt = original_build_prompt(config, task, variant)
    skill = skill_path(config, variant).read_text(encoding="utf-8")
    return (
        prompt
        + "\n---\n\n# COMMON FROZEN OPERATING INSTRUCTIONS\n\n"
        + skill.strip()
        + "\n"
    )


def prepare_run(output_root: Path, config: dict[str, Any], task: dict[str, Any], variant: str) -> dict[str, Any]:
    run = original_prepare_run(output_root, config, task, variant)
    treatment_commit = apply_variant_entry(run["repository"], config, variant)
    state_path = run["repository"] / ".benchmark" / "access-state.json"
    state = base.load_json(state_path)
    state["require_expansion_reason"] = False
    base.write_json(state_path, state)
    policy_path = run["operator"] / "access-policy.json"
    policy = base.load_json(policy_path)
    policy["repository_root"] = str(run["repository"])
    policy["minimum_prewrite_content_reads"] = 1
    policy["scope_usage_ordering_verified"] = bool(config["scope_usage_ordering_verified"])
    base.write_json(policy_path, policy)
    metadata_path = run["operator"] / "run-metadata.json"
    metadata = base.load_json(metadata_path)
    metadata.update({
        "treatment_commit": treatment_commit,
        "agent_entry_sha256": base.sha256(agent_entry_path(config, variant)),
        "scope_usage_ordering_verified": bool(config["scope_usage_ordering_verified"]),
    })
    base.write_json(metadata_path, metadata)
    return run


def _agent_messages(events: list[dict[str, Any]]) -> str:
    messages: list[str] = []
    for event in events:
        item = event.get("item")
        if event.get("type") == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            messages.append(str(item.get("text") or item.get("content") or ""))
            continue
        params = event.get("params")
        item = params.get("item") if isinstance(params, dict) else None
        if event.get("method") == "item/completed" and isinstance(item, dict) and item.get("type") == "agentMessage":
            messages.append(str(item.get("text") or ""))
    return "\n".join(messages)


def protocol_check(events: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    failures: list[str] = []
    if variant not in ("P", "S"):
        failures.append(f"unknown variant: {variant}")
    joined = _agent_messages(events)
    for forbidden in (
        "CONTEXT MANIFEST",
        "SCOPE EXPANSION",
        "SELECTED EVIDENCE",
        "ACCESS SUMMARY",
        "ACCESS RECEIPT",
    ):
        if forbidden in joined:
            failures.append(f"{variant} emitted forbidden protocol prose: {forbidden}")
    return {"passed": not failures, "failures": failures}


def protocol_self_test() -> None:
    message = {"type": "item.completed", "item": {"type": "agent_message", "text": "implemented and tested"}}
    if not protocol_check([message], "P")["passed"] or not protocol_check([message], "S")["passed"]:
        raise RuntimeError("protocol self-test rejected a normal completion")
    forbidden = {"type": "item.completed", "item": {"type": "agent_message", "text": "CONTEXT MANIFEST"}}
    if protocol_check([forbidden], "S")["passed"]:
        raise RuntimeError("protocol self-test accepted forbidden Manifest prose")
    app_server_forbidden = {
        "method": "item/completed",
        "params": {"item": {"type": "agentMessage", "text": "ACCESS RECEIPT"}},
    }
    if protocol_check([app_server_forbidden], "P")["passed"]:
        raise RuntimeError("protocol self-test accepted forbidden app-server Receipt prose")


def nested_preflight(config: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="orrery-p009-nested-") as temporary:
        outer = Path(temporary) / "outer"
        outer.mkdir()
        initialized = _git(["init", "-b", "pilot-009-outer"], outer)
        if initialized.returncode:
            raise RuntimeError("cannot create outer preflight repository")
        for variant in config["variants"]:
            nested = outer / "runs" / f"PO-CR-033-{variant}" / "repository"
            nested.parent.mkdir(parents=True)
            export_baseline(nested, config["baseline_commit"])
            apply_variant_entry(nested, config, variant)
            branch = _git(["branch", "--show-current"], nested)
            if branch.returncode or branch.stdout.strip() != "pilot-009-fixture":
                raise RuntimeError("nested preflight did not preserve the inner fixture branch")
            for task in config["tasks"]:
                result = base.run_command(
                    [sys.executable, "-X", "utf8", str(ORACLE_PATH), "--repository", str(nested), "--task-id", task["task_id"]],
                    cwd=REPOSITORY_ROOT,
                    timeout=120,
                )
                if result.returncode != 1:
                    raise RuntimeError(
                        f"nested {variant} negative control for {task['task_id']} returned {result.returncode}: "
                        + result.stdout
                        + result.stderr
                    )


def preflight(config: dict[str, Any]) -> None:
    if config.get("pilot_id") != "pilot-009" or config.get("variants") != ["P", "S"]:
        raise RuntimeError("unexpected Pilot 009 configuration")
    if config.get("evidence_mode") != "codex-app-server-jsonrpc-scope-lock-v1":
        raise RuntimeError("Pilot 009 requires app-server Scope Lock evidence")
    if config.get("scope_usage_ordering_verified"):
        evidence = config.get("scope_usage_ordering_evidence")
        if not isinstance(evidence, str) or not evidence:
            raise RuntimeError("verified app-server ordering requires a Validation evidence path")
        if not (REPOSITORY_ROOT / evidence).is_file():
            raise RuntimeError("app-server ordering Validation evidence is missing")
    frozen = (
        (skill_path(config, "P"), "shared_skill_sha256"),
        (agent_entry_path(config, "P"), "p_agent_entry_sha256"),
        (agent_entry_path(config, "S"), "s_agent_entry_sha256"),
    )
    for path, hash_key in frozen:
        actual = base.sha256(path)
        if actual != config.get(hash_key):
            raise RuntimeError(f"frozen input changed: {path} config={config.get(hash_key)} actual={actual}")
    for task in config["tasks"]:
        p_prompt = build_prompt(config, task, "P").encode("utf-8")
        s_prompt = build_prompt(config, task, "S").encode("utf-8")
        if len(p_prompt) != len(s_prompt):
            raise RuntimeError(f"P/S Prompt byte mismatch for {task['task_id']}: {len(p_prompt)} != {len(s_prompt)}")
    self_test = base.run_command([sys.executable, "-X", "utf8", str(ORACLE_PATH), "--self-test"], cwd=REPOSITORY_ROOT, timeout=180)
    if self_test.returncode:
        raise RuntimeError("Pilot 009 Oracle self-test failed: " + self_test.stdout + self_test.stderr)
    scope_test = base.run_command([sys.executable, "-X", "utf8", str(SCOPE_ANALYZER_PATH), "--self-test"], cwd=REPOSITORY_ROOT, timeout=180)
    if scope_test.returncode:
        raise RuntimeError("Pilot 009 Scope analyzer self-test failed: " + scope_test.stdout + scope_test.stderr)
    event_test = base.run_command([sys.executable, "-X", "utf8", str(APP_SERVER_VALIDATOR_PATH), "--self-test"], cwd=REPOSITORY_ROOT, timeout=180)
    if event_test.returncode:
        raise RuntimeError("Pilot 009 app-server validator self-test failed: " + event_test.stdout + event_test.stderr)
    protocol_self_test()
    nested_preflight(config)
    if config.get("model") != "gpt-5.6-terra" or config.get("reasoning_effort") != "medium":
        raise RuntimeError("execution profile must remain gpt-5.6-terra / medium")


def control_hashes(config: dict[str, Any]) -> dict[str, str]:
    paths = [
        PILOT_DIR / "pilot-config.json",
        PILOT_DIR / "common-protocol.zh-CN.md",
        PILOT_DIR / "TASK-DESIGN.zh-CN.md",
        PILOT_DIR / "variants/P.zh-CN.md",
        PILOT_DIR / "variants/S.zh-CN.md",
        S_AGENT_PATH,
        PILOT_DIR / "run_pilot.py",
        ORACLE_PATH,
        DESIGN_PATH,
        BASE_RUNNER_PATH,
        base.HARNESS / "context_read_proxy.py",
        base.HARNESS / "_common.py",
        base.HARNESS / "validate_cli_events.py",
        SCOPE_ANALYZER_PATH,
        SCOPE_SMOKE_PATH,
        APP_SERVER_VALIDATOR_PATH,
        base.HARNESS / "seal_raw_evidence.py",
        base.RETENTION_POLICY,
    ]
    paths.extend(path for path in sorted((PILOT_DIR / "controls").rglob("*")) if path.is_file())
    paths.extend(path for path in sorted(FIXTURE_SOURCE.rglob("*")) if path.is_file())
    paths.extend(PILOT_DIR / task["task_file"] for task in config["tasks"])
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): base.sha256(path) for path in paths}


def _ratio(numerator: float, denominator: float) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def runtime_identity(codex: Path, config: dict[str, Any]) -> dict[str, Any]:
    executable = codex.resolve(strict=True)
    version = base.run_command([str(executable), "--version"], cwd=REPOSITORY_ROOT)
    if version.returncode:
        raise RuntimeError("cannot read Codex runtime version: " + version.stdout + version.stderr)
    actual_version = version.stdout.strip()
    expected_version = str(config.get("scope_usage_ordering_codex_version", ""))
    if actual_version != expected_version:
        raise RuntimeError(f"Codex runtime changed: expected {expected_version!r}, got {actual_version!r}")
    siblings: dict[str, str] = {}
    if os.name == "nt":
        for name in runtime.REQUIRED_RUNTIME_FILES:
            sibling = executable.parent / name
            if not sibling.is_file():
                raise RuntimeError(f"required Codex runtime sibling is missing: {sibling}")
            siblings[name] = runtime._hash_file(sibling)
    return {
        "codex_version": actual_version,
        "codex_executable_sha256": runtime._hash_file(executable),
        "codex_runtime_sibling_sha256": siblings,
    }


def runtime_handshake(codex: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="orrery-p009-appserver-handshake-") as temporary:
        root = Path(temporary)
        client = runtime.AppServerClient(
            codex.resolve(strict=True),
            REPOSITORY_ROOT,
            root,
            environment=os.environ.copy(),
            config_overrides=(
                "mcp_servers={}",
                "features.skill_search=false",
                "sandbox_workspace_write.network_access=false",
                "shell_environment_policy.inherit=all",
            ),
        )
        try:
            deadline = time.monotonic() + 30
            client.send(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {"name": "project-orrery-pilot-009-preflight", "version": "0.1.0"},
                        "capabilities": {"experimentalApi": True},
                    },
                }
            )
            client.wait_for_response(1, deadline)
            client.send({"jsonrpc": "2.0", "method": "initialized"})
        finally:
            client.close()


def _last_usage(events: list[dict[str, Any]], thread_id: str, turn_id: str) -> dict[str, int]:
    latest: dict[str, int] = {}
    for event in events:
        if event.get("method") != "thread/tokenUsage/updated":
            continue
        params = event.get("params")
        if not isinstance(params, dict):
            continue
        if str(params.get("threadId", "")) != thread_id or str(params.get("turnId", "")) != turn_id:
            continue
        token_usage = params.get("tokenUsage")
        total = token_usage.get("total") if isinstance(token_usage, dict) else None
        if not isinstance(total, dict):
            continue
        mapping = {
            "inputTokens": "input_tokens",
            "cachedInputTokens": "cached_input_tokens",
            "cacheWriteInputTokens": "cache_write_input_tokens",
            "outputTokens": "output_tokens",
            "reasoningOutputTokens": "reasoning_output_tokens",
            "totalTokens": "total_tokens",
        }
        if all(isinstance(total.get(source), int) for source in mapping):
            latest = {target: int(total[source]) for source, target in mapping.items()}
    return latest


def _final_message(events: list[dict[str, Any]]) -> str:
    messages: list[str] = []
    for event in events:
        if event.get("method") != "item/completed":
            continue
        params = event.get("params")
        item = params.get("item") if isinstance(params, dict) else None
        if isinstance(item, dict) and item.get("type") == "agentMessage" and item.get("phase") == "final_answer":
            messages.append(str(item.get("text") or ""))
    return "\n".join(messages)


def execute_agent(run: dict[str, Any], config: dict[str, Any], codex: Path) -> dict[str, Any]:
    operator: Path = run["operator"]
    repository: Path = run["repository"]
    identity = runtime_identity(codex, config)
    environment = os.environ.copy()
    environment.update(
        {
            "ORRERY_BENCHMARK_REPO_ROOT": str(repository),
            "ORRERY_PROXY_AUDIT_LOG": str(repository / ".benchmark" / "proxy-audit.jsonl"),
            "ORRERY_ACCESS_STATE": str(repository / ".benchmark" / "access-state.json"),
            "ORRERY_ACCESS_POLICY": str(operator / "access-policy.json"),
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    metadata_path = operator / "run-metadata.json"
    metadata = base.load_json(metadata_path)
    metadata.update(identity)
    metadata["transport"] = "codex-app-server-jsonrpc-scope-lock-v1"
    metadata["app_server_config_overrides"] = [
        "mcp_servers={}",
        "features.skill_search=false",
        "sandbox_workspace_write.network_access=false",
        "shell_environment_policy.inherit=all",
    ]
    base.write_json(metadata_path, metadata)

    started_at = base.now_iso()
    started = time.perf_counter()
    client = None
    thread_id = ""
    turn_id = ""
    turn_status: str | None = None
    turn_error: Any = None
    timed_out = False
    spawn_error: str | None = None
    try:
        deadline = time.monotonic() + int(config["timeout_minutes"]) * 60
        client = runtime.AppServerClient(
            codex.resolve(strict=True),
            repository,
            operator,
            environment=environment,
            config_overrides=(
                "mcp_servers={}",
                "features.skill_search=false",
                "sandbox_workspace_write.network_access=false",
                "shell_environment_policy.inherit=all",
            ),
        )
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "project-orrery-pilot-009", "version": "0.1.0"},
                    "capabilities": {"experimentalApi": True},
                },
            }
        )
        client.wait_for_response(1, deadline)
        client.send({"jsonrpc": "2.0", "method": "initialized"})
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "thread/start",
                "params": {
                    "cwd": str(repository),
                    "model": config["model"],
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "ephemeral": True,
                    "dynamicTools": [],
                },
            }
        )
        thread_response = client.wait_for_response(2, deadline)
        thread = thread_response.get("result", {}).get("thread", {})
        thread_id = str(thread.get("id", ""))
        if not thread_id:
            raise RuntimeError("thread/start response has no thread id")
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "turn/start",
                "params": {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": run["prompt"]}],
                    "cwd": str(repository),
                    "model": config["model"],
                    "effort": config["reasoning_effort"],
                    "approvalPolicy": "never",
                },
            }
        )
        turn_response = client.wait_for_response(3, deadline)
        turn = turn_response.get("result", {}).get("turn", {})
        turn_id = str(turn.get("id", ""))
        if not turn_id:
            raise RuntimeError("turn/start response has no turn id")
        completed = client.wait_for(
            lambda value: value.get("method") == "turn/completed"
            and isinstance(value.get("params"), dict)
            and str(value["params"].get("threadId", "")) == thread_id
            and isinstance(value["params"].get("turn"), dict)
            and str(value["params"]["turn"].get("id", "")) == turn_id,
            deadline,
        )
        completed_turn = completed.get("params", {}).get("turn", {})
        turn_status = str(completed_turn.get("status", ""))
        turn_error = completed_turn.get("error")
        time.sleep(0.1)
    except TimeoutError as exc:
        timed_out = True
        spawn_error = f"{type(exc).__name__}: {exc}"
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        spawn_error = f"{type(exc).__name__}: {exc}"
    finally:
        if client is not None:
            client.close()

    events = client.messages if client is not None else []
    for name in ("server-events.jsonl", "server-stderr.log", "client-requests.jsonl"):
        path = operator / name
        if not path.exists():
            path.write_text("", encoding="utf-8", newline="\n")
    (operator / "final-message.txt").write_text(_final_message(events), encoding="utf-8", newline="\n")
    usage = _last_usage(events, thread_id, turn_id)
    result = {
        "started_at": started_at,
        "ended_at": base.now_iso(),
        "agent_seconds": round(time.perf_counter() - started, 3),
        "exit_code": 0 if turn_status == "completed" and turn_error is None and spawn_error is None else 1,
        "timed_out": timed_out,
        "spawn_error": spawn_error,
        "thread_id": thread_id or None,
        "turn_id": turn_id or None,
        "turn_status": turn_status,
        "turn_error": turn_error,
        "usage": usage,
        "event_count": len(events),
        "malformed_event_count": 0,
    }
    base.write_json(operator / "agent-result.json", result)
    base.write_json(operator / "protocol-check.json", protocol_check(events, run["variant"]))
    return result


def finish_run(run: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    operator: Path = run["operator"]
    repository: Path = run["repository"]
    agent = base.load_json(operator / "agent-result.json")
    proxy_path = repository / ".benchmark" / "proxy-audit.jsonl"
    events_path = operator / "server-events.jsonl"

    scope_path = operator / "scope-analysis.json"
    scope_run = base.run_command(
        [sys.executable, "-X", "utf8", str(SCOPE_ANALYZER_PATH), "--events", str(events_path),
         "--proxy-log", str(proxy_path), "--policy", str(operator / "access-policy.json"),
         "--output", str(scope_path)],
        cwd=REPOSITORY_ROOT,
    )
    scope = base.load_json(scope_path) if scope_path.is_file() else {
        "measurement_valid": False,
        "unavailable_reasons": [scope_run.stdout + scope_run.stderr],
    }

    audit_path = operator / "access-audit.json"
    audit_run = base.run_command(
        [sys.executable, "-X", "utf8", str(APP_SERVER_VALIDATOR_PATH), "--events", str(events_path),
         "--proxy-log", str(proxy_path), "--policy", str(operator / "access-policy.json"),
         "--output", str(audit_path)],
        cwd=REPOSITORY_ROOT,
    )
    access = base.load_json(audit_path) if audit_path.is_file() else {
        "apparatus_valid": False,
        "validator_error": audit_run.stdout + audit_run.stderr,
    }
    acceptance_path = operator / "acceptance.json"
    acceptance_run = base.run_command(
        [sys.executable, "-X", "utf8", str(ORACLE_PATH), "--repository", str(repository),
         "--task-id", run["task"]["task_id"], "--output", str(acceptance_path)],
        cwd=REPOSITORY_ROOT,
        timeout=240,
    )
    acceptance = base.load_json(acceptance_path) if acceptance_path.is_file() else {
        "passed": False,
        "apparatus_errors": [acceptance_run.stdout + acceptance_run.stderr],
    }
    validation = base.execute_validation(repository, run["task"]["validation_commands"], operator / "formal-validation.json")
    protocol = base.load_json(operator / "protocol-check.json")
    paths = base.changed_paths(repository)
    expected = set(run["task"]["expected_product_write_paths"])
    unexpected = sorted(set(paths) - expected)
    apparatus_valid = bool(
        access.get("apparatus_valid")
        and scope.get("measurement_valid")
        and not acceptance.get("apparatus_errors")
        and not agent.get("spawn_error")
        and not agent.get("timed_out")
        and agent.get("exit_code") == 0
        and not unexpected
        and agent.get("malformed_event_count") == 0
    )
    proxy_events: list[dict[str, Any]] = []
    for line in proxy_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            try:
                proxy_events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    reads = [event for event in proxy_events if event.get("operation") == "read"]
    final_usage = scope.get("final_usage") or agent.get("usage", {})
    prewrite_usage = scope.get("prewrite_usage") or {}
    summary = {
        "run_id": run["run_id"],
        "task_id": run["task"]["task_id"],
        "variant": run["variant"],
        "classification": "decision_supporting" if apparatus_valid else "contaminated",
        "apparatus_valid": apparatus_valid,
        "scope_measurement_valid": bool(scope.get("measurement_valid")),
        "candidate_passed": bool(acceptance.get("passed")) and validation["passed"] and protocol["passed"],
        "operator_acceptance_passed": bool(acceptance.get("passed")),
        "formal_validation_passed": validation["passed"],
        "protocol_passed": protocol["passed"],
        "changed_paths": paths,
        "unexpected_changed_paths": unexpected,
        "first_write_paths": scope.get("scope_lock", {}).get("paths", []),
        "content_reads": len(reads),
        "unique_content_paths": len({event.get("path") for event in reads}),
        "expansion_reads": sum(bool(event.get("expansion")) for event in reads),
        "proxy_returned_bytes": sum(int(event.get("returned_bytes", 0)) for event in reads),
        "prewrite_content_reads": int(scope.get("prewrite_evidence", {}).get("content_reads_proved", 0)),
        "prewrite_unique_content_paths": int(scope.get("prewrite_evidence", {}).get("unique_content_paths", 0)),
        "prewrite_unique_slice_bytes": int(scope.get("prewrite_evidence", {}).get("unique_slice_bytes", 0)),
        "prewrite_input_tokens": prewrite_usage.get("input_tokens"),
        "prewrite_cached_input_tokens": prewrite_usage.get("cached_input_tokens"),
        "prewrite_non_cached_input_tokens": scope.get("prewrite_non_cached_input_tokens"),
        "prewrite_output_tokens": prewrite_usage.get("output_tokens"),
        "prompt_bytes": base.load_json(operator / "run-metadata.json")["prompt_bytes"],
        "usage": final_usage,
        "non_cached_input_tokens": max(0, int(final_usage.get("input_tokens", 0)) - int(final_usage.get("cached_input_tokens", 0))),
        "agent_seconds": agent.get("agent_seconds"),
        "access_audit": access,
        "scope_analysis": scope,
        "acceptance": acceptance,
        "protocol": protocol,
    }
    base.write_json(operator / "run-summary.json", summary)
    seal = base.run_command(
        [sys.executable, "-X", "utf8", str(base.HARNESS / "seal_raw_evidence.py"), "seal",
         "--run-root", str(run["run_root"]), "--policy", str(base.RETENTION_POLICY),
         "--pilot-id", config["pilot_id"], "--run-id", run["run_id"],
         "--classification", summary["classification"], "--source-commit", config["baseline_commit"],
         "--apparatus-version", config["prompt_revision"], "--created-at", agent["started_at"]],
        cwd=REPOSITORY_ROOT,
        timeout=240,
    )
    if seal.returncode:
        raise RuntimeError(f"failed to seal {run['run_id']}: " + (seal.stdout + seal.stderr).strip())
    return summary


def formal_pipeline_self_test(config: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="orrery-p009-formal-pipeline-") as temporary:
        output_root = Path(temporary) / "raw"
        output_root.mkdir()
        task = config["tasks"][0]
        run = prepare_run(output_root, config, task, "P")
        repository: Path = run["repository"]
        operator: Path = run["operator"]
        environment = os.environ.copy()
        environment.update(
            {
                "ORRERY_BENCHMARK_REPO_ROOT": str(repository),
                "ORRERY_PROXY_AUDIT_LOG": str(repository / ".benchmark" / "proxy-audit.jsonl"),
                "ORRERY_ACCESS_STATE": str(repository / ".benchmark" / "access-state.json"),
                "PYTHONUTF8": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        proxy_command = "python .benchmark/context_read_proxy.py read --path docs/state/application.md --start 1 --end 4"
        proxy = subprocess.run(
            [sys.executable, ".benchmark/context_read_proxy.py", "read", "--path", "docs/state/application.md", "--start", "1", "--end", "4"],
            cwd=repository,
            env=environment,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
        if proxy.returncode:
            raise RuntimeError("formal pipeline proxy self-test failed: " + proxy.stdout + proxy.stderr)
        thread_id, turn_id = "thread-self-test", "turn-self-test"

        def item(method: str, value: dict[str, Any]) -> dict[str, Any]:
            return {"method": method, "params": {"threadId": thread_id, "turnId": turn_id, "item": value}}

        total_before = {
            "totalTokens": 110,
            "inputTokens": 100,
            "cachedInputTokens": 40,
            "cacheWriteInputTokens": 0,
            "outputTokens": 10,
            "reasoningOutputTokens": 0,
        }
        total_after = {
            "totalTokens": 220,
            "inputTokens": 200,
            "cachedInputTokens": 80,
            "cacheWriteInputTokens": 0,
            "outputTokens": 20,
            "reasoningOutputTokens": 0,
        }
        write_path = repository / task["expected_product_write_paths"][0]
        events = [
            item("item/started", {"id": "read", "type": "commandExecution"}),
            item(
                "item/completed",
                {
                    "id": "read",
                    "type": "commandExecution",
                    "command": proxy_command,
                    "status": "completed",
                    "exitCode": 0,
                    "aggregatedOutput": proxy.stdout,
                },
            ),
            {"method": "thread/tokenUsage/updated", "params": {"threadId": thread_id, "turnId": turn_id, "tokenUsage": {"total": total_before}}},
            item("item/started", {"id": "write", "type": "fileChange", "changes": [{"path": str(write_path)}]}),
            item("item/completed", {"id": "write", "type": "fileChange", "status": "completed", "changes": [{"path": str(write_path)}]}),
            {"method": "thread/tokenUsage/updated", "params": {"threadId": thread_id, "turnId": turn_id, "tokenUsage": {"total": total_after}}},
            item("item/completed", {"id": "message", "type": "agentMessage", "phase": "final_answer", "text": "done"}),
            {"method": "turn/completed", "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed", "error": None}}},
        ]
        (operator / "server-events.jsonl").write_text(
            "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
            encoding="utf-8",
            newline="\n",
        )
        (operator / "server-stderr.log").write_text("", encoding="utf-8")
        (operator / "client-requests.jsonl").write_text("", encoding="utf-8")
        (operator / "final-message.txt").write_text("done\n", encoding="utf-8", newline="\n")
        base.write_json(
            operator / "agent-result.json",
            {
                "started_at": base.now_iso(),
                "ended_at": base.now_iso(),
                "agent_seconds": 0.1,
                "exit_code": 0,
                "timed_out": False,
                "spawn_error": None,
                "thread_id": thread_id,
                "turn_id": turn_id,
                "turn_status": "completed",
                "turn_error": None,
                "usage": _last_usage(events, thread_id, turn_id),
                "event_count": len(events),
                "malformed_event_count": 0,
            },
        )
        base.write_json(operator / "protocol-check.json", protocol_check(events, "P"))
        summary = finish_run(run, config)
        if not summary["apparatus_valid"] or not summary["scope_measurement_valid"]:
            raise RuntimeError("formal pipeline self-test rejected valid synthetic evidence")
        verify = base.run_command(
            [sys.executable, "-X", "utf8", str(base.HARNESS / "seal_raw_evidence.py"), "verify", "--manifest", str(run["run_root"] / "raw-evidence-manifest.json")],
            cwd=REPOSITORY_ROOT,
        )
        if verify.returncode:
            raise RuntimeError("formal pipeline self-test manifest verification failed: " + verify.stdout + verify.stderr)


def summarize(config: dict[str, Any], rows: list[dict[str, Any]], output_root: Path, hashes: dict[str, str]) -> None:
    variants: dict[str, Any] = {}
    for variant in config["variants"]:
        selected = [row for row in rows if row["variant"] == variant]
        usage_keys = sorted({key for row in selected for key in row["usage"]})
        variants[variant] = {
            "runs": len(selected),
            "apparatus_valid": sum(bool(row["apparatus_valid"]) for row in selected),
            "scope_measurement_valid": sum(bool(row["scope_measurement_valid"]) for row in selected),
            "candidate_passed": sum(bool(row["candidate_passed"]) for row in selected),
            "prewrite_input_tokens_total": sum(int(row["prewrite_input_tokens"] or 0) for row in selected),
            "prewrite_cached_input_tokens_total": sum(int(row["prewrite_cached_input_tokens"] or 0) for row in selected),
            "prewrite_non_cached_input_tokens_total": sum(int(row["prewrite_non_cached_input_tokens"] or 0) for row in selected),
            "prewrite_output_tokens_total": sum(int(row["prewrite_output_tokens"] or 0) for row in selected),
            "prewrite_unique_slice_bytes_total": sum(int(row["prewrite_unique_slice_bytes"] or 0) for row in selected),
            "usage_totals": {key: sum(int(row["usage"].get(key, 0)) for row in selected) for key in usage_keys},
            "non_cached_input_tokens_total": sum(int(row["non_cached_input_tokens"] or 0) for row in selected),
            "proxy_returned_bytes_total": sum(int(row["proxy_returned_bytes"] or 0) for row in selected),
            "prompt_bytes_total": sum(int(row["prompt_bytes"] or 0) for row in selected),
            "agent_seconds_total": round(sum(float(row["agent_seconds"] or 0) for row in selected), 3),
            "content_reads_total": sum(int(row["content_reads"] or 0) for row in selected),
            "prewrite_content_reads_total": sum(int(row["prewrite_content_reads"] or 0) for row in selected),
        }

    all_apparatus_valid = all(row["apparatus_valid"] for row in rows) and len(rows) == 6
    p, s = variants["P"], variants["S"]
    ratios = {
        "prewrite_input_s_over_p": _ratio(s["prewrite_input_tokens_total"], p["prewrite_input_tokens_total"]),
        "prewrite_non_cached_input_s_over_p": _ratio(s["prewrite_non_cached_input_tokens_total"], p["prewrite_non_cached_input_tokens_total"]),
        "prewrite_unique_slice_bytes_s_over_p": _ratio(s["prewrite_unique_slice_bytes_total"], p["prewrite_unique_slice_bytes_total"]),
        "total_input_s_over_p": _ratio(s["usage_totals"].get("input_tokens", 0), p["usage_totals"].get("input_tokens", 0)),
        "output_s_over_p": _ratio(s["usage_totals"].get("output_tokens", 0), p["usage_totals"].get("output_tokens", 0)),
        "agent_seconds_s_over_p": _ratio(s["agent_seconds_total"], p["agent_seconds_total"]),
        "proxy_bytes_s_over_p": _ratio(s["proxy_returned_bytes_total"], p["proxy_returned_bytes_total"]),
    }
    task_by_id = {task["task_id"]: task for task in config["tasks"]}
    pairs: dict[str, Any] = {}
    p_only_high_risk_success = False
    for task_id, task in task_by_id.items():
        pair = {row["variant"]: row for row in rows if row["task_id"] == task_id}
        p_row, s_row = pair["P"], pair["S"]
        pair_ratio = _ratio(float(s_row["prewrite_input_tokens"] or 0), float(p_row["prewrite_input_tokens"] or 0))
        pairs[task_id] = {
            "risk": task["risk"],
            "p_candidate_passed": p_row["candidate_passed"],
            "s_candidate_passed": s_row["candidate_passed"],
            "p_prewrite_input_tokens": p_row["prewrite_input_tokens"],
            "s_prewrite_input_tokens": s_row["prewrite_input_tokens"],
            "s_over_p_prewrite_input": pair_ratio,
        }
        if task["risk"] == "high" and p_row["candidate_passed"] and not s_row["candidate_passed"]:
            p_only_high_risk_success = True

    gate = config["adoption_gate"]
    high_risk_cost_ok = all(
        pair["risk"] != "high"
        or pair["s_over_p_prewrite_input"] is not None
        and pair["s_over_p_prewrite_input"] <= float(gate["s_high_risk_pair_prewrite_input_ratio_max"])
        for pair in pairs.values()
    )
    cost_gate = bool(
        all_apparatus_valid
        and ratios["prewrite_input_s_over_p"] is not None
        and ratios["prewrite_input_s_over_p"] <= float(gate["s_prewrite_input_ratio_max"])
        and ratios["prewrite_non_cached_input_s_over_p"] is not None
        and ratios["prewrite_non_cached_input_s_over_p"] <= float(gate["s_prewrite_non_cached_input_ratio_max"])
        and ratios["prewrite_unique_slice_bytes_s_over_p"] is not None
        and ratios["prewrite_unique_slice_bytes_s_over_p"] <= float(gate["s_prewrite_unique_slice_bytes_ratio_max"])
        and ratios["total_input_s_over_p"] is not None
        and ratios["total_input_s_over_p"] <= float(gate["s_total_input_ratio_max"])
        and ratios["output_s_over_p"] is not None
        and ratios["output_s_over_p"] <= float(gate["s_output_ratio_max"])
        and ratios["agent_seconds_s_over_p"] is not None
        and ratios["agent_seconds_s_over_p"] <= float(gate["s_agent_seconds_ratio_max"])
        and ratios["proxy_bytes_s_over_p"] is not None
        and ratios["proxy_bytes_s_over_p"] <= float(gate["s_proxy_bytes_ratio_max"])
        and high_risk_cost_ok
    )
    quality_gate = bool(
        s["candidate_passed"] == int(gate["s_required_passes"])
        and s["candidate_passed"] >= p["candidate_passed"]
        and not p_only_high_risk_success
    )
    summary = {
        "schema_version": 1,
        "pilot_id": config["pilot_id"],
        "prompt_revision": config["prompt_revision"],
        "generated_at": base.now_iso(),
        "baseline_commit": config["baseline_commit"],
        "model": config["model"],
        "reasoning_effort": config["reasoning_effort"],
        "control_hashes": hashes,
        "variants": variants,
        "ratios": ratios if all_apparatus_valid else {key: None for key in ratios},
        "pairs": pairs,
        "gate": {
            "all_apparatus_valid": all_apparatus_valid,
            "quality_gate_passed": quality_gate,
            "cost_gate_passed": cost_gate,
            "automatic_gate_passed": all_apparatus_valid and quality_gate and cost_gate,
            "product_adoption": False,
            "reason": "automatic evidence gate does not itself authorize product adoption; R2 and maintainer acceptance are required",
        },
        "runs": rows,
    }
    base.write_json(output_root / "pilot-summary.json", summary)
    lines = [
        "# Pilot 009 P/S Scope Acquisition raw comparison", "",
        f"> Generated: `{summary['generated_at']}`  ",
        f"> Model: `{config['model']}` / `{config['reasoning_effort']}`  ",
        "> R0-derived comparison; not an ADR or product policy.", "",
        "| Variant | Apparatus | Candidate pass | Pre-write input | Pre-write non-cached | Pre-write slice bytes | Total input | Output | Agent seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in config["variants"]:
        item = variants[variant]
        usage = item["usage_totals"]
        lines.append(
            f"| {variant} | {item['apparatus_valid']}/{item['runs']} | {item['candidate_passed']}/{item['runs']} | "
            f"{item['prewrite_input_tokens_total']} | {item['prewrite_non_cached_input_tokens_total']} | "
            f"{item['prewrite_unique_slice_bytes_total']} | {usage.get('input_tokens', 0)} | "
            f"{usage.get('output_tokens', 0)} | {item['agent_seconds_total']} |"
        )
    lines.extend(["", "## Runs", "", "| Run | Valid | Pass | Pre-write input | Reads before/all | First write |", "|---|---:|---:|---:|---:|---|"])
    for row in rows:
        first_write = "<br>".join(f"`{path}`" for path in row["first_write_paths"]) or "—"
        lines.append(
            f"| {row['run_id']} | {row['apparatus_valid']} | {row['candidate_passed']} | "
            f"{row['prewrite_input_tokens']} | {row['prewrite_content_reads']}/{row['content_reads']} | {first_write} |"
        )
    lines.extend(["", f"Automatic evidence gate: **{summary['gate']['automatic_gate_passed']}**. ", "Product adoption remains false until a reviewed R2 is explicitly accepted."])
    (output_root / "pilot-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


original_dry_run = base.dry_run


def dry_run(config: dict[str, Any]) -> None:
    original_dry_run(config)
    formal_pipeline_self_test(config)


base.PILOT_DIR = PILOT_DIR
base.CONFIG_PATH = PILOT_DIR / "pilot-config.json"
base.ORACLE = ORACLE_PATH
base.export_baseline = export_baseline
base.initialize_repository = initialize_repository
base.preflight = preflight
base.protocol_check = protocol_check
original_build_prompt = base.build_prompt
base.build_prompt = build_prompt
original_prepare_run = base.prepare_run
base.prepare_run = prepare_run
base.control_hashes = control_hashes
base.dry_run = dry_run
base.execute_agent = execute_agent
base.finish_run = finish_run
base.summarize = summarize


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--dry-run" in arguments:
        return base.main(arguments)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--codex", type=Path, default=Path(r"D:\Tools\Codex\npm\codex.cmd"))
    args = parser.parse_args(arguments)
    config = base.load_json(base.CONFIG_PATH)
    if not config.get("scope_usage_ordering_verified"):
        print(
            "Pilot 009 formal execution is disabled until the app-server usage/fileChange ordering smoke passes.",
            file=sys.stderr,
        )
        return 2
    try:
        runtime_identity(args.codex, config)
        runtime_handshake(args.codex)
        preflight(config)
        dry_run(config)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Pilot 009 runtime preflight failed: {exc}", file=sys.stderr)
        return 2

    output_root = args.output_root.expanduser().resolve()
    if output_root.exists():
        raise RuntimeError(f"refusing to overwrite existing output root: {output_root}")
    output_root.mkdir(parents=True)
    hashes = control_hashes(config)
    base.write_json(
        output_root / "frozen-control.json",
        {"config": config, "control_hashes": hashes, "frozen_at": base.now_iso()},
    )
    tasks = list(config["tasks"])
    base.random.Random(int(config["task_order_seed"])).shuffle(tasks)
    rows: list[dict[str, Any]] = []
    for task in tasks:
        prepared = [prepare_run(output_root, config, task, variant) for variant in config["variants"]]
        with base.concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(execute_agent, run, config, args.codex) for run in prepared]
            for future in futures:
                future.result()
        pair_rows: list[dict[str, Any]] = []
        for run in prepared:
            row = finish_run(run, config)
            rows.append(row)
            pair_rows.append(row)
            print(
                f"{row['run_id']}: apparatus={row['apparatus_valid']} "
                f"scope={row['scope_measurement_valid']} acceptance={row['candidate_passed']} "
                f"classification={row['classification']}",
                flush=True,
            )
        if not all(row["apparatus_valid"] for row in pair_rows):
            base.write_json(
                output_root / "apparatus-stop.json",
                {
                    "schema_version": 1,
                    "pilot_id": config["pilot_id"],
                    "stopped_after_task": task["task_id"],
                    "reason": "at least one paired run failed the frozen apparatus gate; later model samples were not started",
                    "runs": rows,
                    "control_hashes": hashes,
                },
            )
            print("Pilot 009 stopped after the first invalid apparatus pair; later samples were not started.", file=sys.stderr)
            return 3
    rows.sort(key=lambda row: (row["task_id"], config["variants"].index(row["variant"])))
    summarize(config, rows, output_root, hashes)
    print(output_root / "pilot-summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
