#!/usr/bin/env python3
"""Run Project Orrery pilot-004 with one reproducible local command.

The runner prepares the selected isolated repositories and routing variants,
captures Codex JSONL/stdout/stderr, records operator
timing, seals the run, validates all artifacts, and writes a comparison
summary. Interrupted or failed attempts are never silently retried: they are
marked contaminated so benchmark evidence cannot hide retries.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


RUNNER_VERSION = "3"
TERMINAL_STATUSES = {"completed", "contaminated"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _nul_paths(value: str) -> set[str]:
    return {
        item.replace("\\", "/")
        for item in value.split("\0")
        if item
    }


def collect_product_changes(repository: Path) -> dict[str, Any]:
    """Collect tracked and untracked product changes from the Harness side."""
    tracked_result = run_command(
        ["git", "diff", "--name-only", "-z", "HEAD", "--"],
        cwd=repository,
        timeout=120,
    )
    require_success(tracked_result, "tracked product change collection")
    untracked_result = run_command(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repository,
        timeout=120,
    )
    require_success(untracked_result, "untracked product change collection")

    tracked = _nul_paths(tracked_result.stdout)
    untracked = _nul_paths(untracked_result.stdout)
    entries: list[dict[str, Any]] = []
    for relative in sorted(tracked | untracked):
        path = repository / Path(relative)
        exists = path.is_file()
        entries.append(
            {
                "path": relative,
                "kind": "untracked" if relative in untracked else "tracked",
                "exists": exists,
                "bytes": path.stat().st_size if exists else None,
                "sha256": sha256(path) if exists else None,
            }
        )
    return {
        "schema_version": 1,
        "observed_by": "harness",
        "repository_head": run_command(
            ["git", "rev-parse", "HEAD"], cwd=repository, timeout=30
        ).stdout.strip(),
        "entries": entries,
    }


def resolve_command(command: str) -> str:
    candidate = Path(command).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    resolved = shutil.which(command)
    if resolved is None:
        raise RuntimeError(
            f"Agent command is unavailable: {command!r}. Install the standalone Codex CLI "
            "or pass --agent-command explicitly."
        )
    return str(Path(resolved).resolve())


def powershell_command() -> str:
    command = shutil.which("powershell") or shutil.which("pwsh")
    if command is None:
        raise RuntimeError("PowerShell is required by the pilot-004 operator scripts.")
    return command


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()
        raise RuntimeError(f"{label} failed with exit code {result.returncode}:\n{detail}")


def invoke_powershell(script: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    command = [
        powershell_command(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *arguments,
    ]
    return run_command(command, timeout=900)


def command_version(executable: str, prefix_args: list[str]) -> str:
    try:
        result = run_command([executable, *prefix_args, "--version"], timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "The selected Agent command could not be started. The Codex desktop app's bundled "
            "executable may not be callable from PowerShell; install the standalone Codex CLI."
        ) from exc
    require_success(result, "Agent command preflight")
    version = (result.stdout or result.stderr).strip().splitlines()
    if not version:
        raise RuntimeError("Agent command preflight returned no version text.")
    return version[0]


def process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class RunnerLock:
    def __init__(self, path: Path, *, resume: bool) -> None:
        self.path = path
        self.resume = resume
        self.owned = False

    def __enter__(self) -> "RunnerLock":
        if self.path.exists():
            try:
                existing = load_json(self.path)
                existing_pid = int(existing.get("pid", -1))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                existing_pid = -1
            if process_exists(existing_pid):
                raise RuntimeError(f"Another pilot runner is active (PID {existing_pid}).")
            if not self.resume:
                raise RuntimeError("A stale automation lock exists; use --resume to recover it.")
            self.path.unlink()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            payload = json.dumps({"pid": os.getpid(), "acquired_at": now_iso()}, ensure_ascii=False)
            os.write(descriptor, payload.encode("utf-8"))
        finally:
            os.close(descriptor)
        self.owned = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.owned and self.path.exists():
            self.path.unlink()


def parse_jsonl(path: Path) -> dict[str, Any]:
    thread_id: str | None = None
    usage: dict[str, int] = {}
    event_count = 0
    malformed = 0
    if not path.is_file():
        return {
            "thread_id": None,
            "usage": {},
            "event_count": 0,
            "malformed_event_count": 0,
        }
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            event_count += 1
            if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
                thread_id = event["thread_id"]
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                usage = {
                    str(key): int(value)
                    for key, value in event["usage"].items()
                    if isinstance(value, int) and not isinstance(value, bool)
                }
    return {
        "thread_id": thread_id,
        "usage": usage,
        "event_count": event_count,
        "malformed_event_count": malformed,
    }


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def execute_agent(
    *,
    executable: str,
    prefix_args: list[str],
    repository: Path,
    prompt_path: Path,
    run_directory: Path,
    model: str,
    reasoning_effort: str,
    timeout_minutes: int,
) -> dict[str, Any]:
    run_directory.mkdir(parents=True, exist_ok=True)
    events_path = run_directory / "events.jsonl"
    stderr_path = run_directory / "stderr.log"
    final_path = run_directory / "final-message.txt"
    result_path = run_directory / "runner-result.json"
    product_changes_path = run_directory / "product-changes.json"
    prompt = prompt_path.read_text(encoding="utf-8-sig")
    command = [
        executable,
        *prefix_args,
        "exec",
        "--ephemeral",
        "--json",
        "--ignore-user-config",
        "--ignore-rules",
        "--approve-for-me",
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        "sandbox_workspace_write.network_access=false",
        "-C",
        str(repository),
        "-o",
        str(final_path),
        "-",
    ]
    started_at = now_iso()
    timed_out = False
    spawn_error: str | None = None
    exit_code: int | None = None
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process: subprocess.Popen[str] | None = None
    with events_path.open("w", encoding="utf-8", newline="\n") as stdout_handle, stderr_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as stderr_handle:
        try:
            process = subprocess.Popen(
                command,
                cwd=repository,
                stdin=subprocess.PIPE,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
                start_new_session=(os.name != "nt"),
            )
            try:
                process.communicate(prompt, timeout=timeout_minutes * 60)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_process_tree(process)
                process.wait(timeout=30)
            exit_code = process.returncode
        except OSError as exc:
            spawn_error = f"{type(exc).__name__}: {exc}"
    ended_at = now_iso()
    trace = parse_jsonl(events_path)
    product_changes = collect_product_changes(repository)
    atomic_write_json(product_changes_path, product_changes)
    receipt_path = repository / ".benchmark" / "agent-receipt.json"
    final_text = final_path.read_text(encoding="utf-8", errors="replace") if final_path.is_file() else ""
    contaminated_signal = "RUN CONTAMINATED" in final_text
    needs_intervention = "RUN NEEDS INTERVENTION" in final_text
    result = {
        "schema_version": 1,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "spawn_error": spawn_error,
        "events_path": str(events_path),
        "stderr_path": str(stderr_path),
        "final_message_path": str(final_path),
        "receipt_path": str(receipt_path),
        "receipt_exists": receipt_path.is_file(),
        "product_changes_path": str(product_changes_path),
        "product_changes_sha256": sha256(product_changes_path),
        "contaminated_signal": contaminated_signal,
        "needs_intervention": needs_intervention,
        **trace,
    }
    atomic_write_json(result_path, result)
    result["result_path"] = str(result_path)
    return result


def recorder_arguments(action: str, output_root: Path, **values: str | None) -> list[str]:
    arguments = ["-OutputRoot", str(output_root), "-Action", action]
    switches = {"ConfirmSameExecutionSettings"}
    for key, value in values.items():
        if key in switches:
            if value:
                arguments.append(f"-{key}")
        elif value is not None and str(value).strip():
            arguments.extend([f"-{key}", str(value)])
    return arguments


def update_state_from_operator(state: dict[str, Any], operator_log: dict[str, Any]) -> None:
    operator_by_key = {run["run_key"]: run for run in operator_log["runs"]}
    for run_key, run_state in state["runs"].items():
        operator_run = operator_by_key[run_key]
        run_state["operator_status"] = operator_run["status"]
        run_state["operator_started_at"] = operator_run["operator_started_at"]
        run_state["operator_ended_at"] = operator_run["operator_ended_at"]
        run_state["thread_id"] = operator_run["thread_id"]


def make_initial_state(manifest: dict[str, Any], automation_profile_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "pilot_id": manifest["pilot_id"],
        "runner_version": RUNNER_VERSION,
        "automation_profile_sha256": automation_profile_sha256,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "sealed": False,
        "validation_exit_code": None,
        "summary_path": None,
        "runs": {
            run["run_key"]: {
                "task_id": run["task_id"],
                "variant": run["variant"],
                "operator_status": "pending",
                "operator_started_at": None,
                "operator_ended_at": None,
                "thread_id": None,
                "attempts": 0,
                "last_result": None,
                "note": None,
            }
            for run in manifest["runs"]
        },
    }


def profile_value(args: argparse.Namespace, executable: str, version: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "pilot_id": "pilot-004",
        "runner_version": RUNNER_VERSION,
        "created_at": now_iso(),
        "agent_executable": executable,
        "agent_prefix_args": args.agent_prefix_arg,
        "agent_version": version,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "permission_profile": args.permission_profile,
        "network_policy": args.network_policy,
        "time_budget_minutes": args.time_budget_minutes,
        "max_parallel": args.max_parallel,
        "selected_task_ids": args.task_id,
        "selected_variants": args.variant,
        "retry_policy": "never retry automatically; interrupted and failed attempts are contaminated",
        "event_evidence": "Codex JSONL is Harness command/tool trace, not proof of exact model-visible file bytes",
    }


def comparable_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in profile.items() if key != "created_at"}


def prepare_output(
    *,
    script_root: Path,
    output_root: Path,
    args: argparse.Namespace,
    harness: str,
) -> None:
    output_root.parent.mkdir(parents=True, exist_ok=True)
    prepare_script = script_root / "prepare_pilot.ps1"
    result = invoke_powershell(
        prepare_script,
        [
            "-OutputRoot",
            str(output_root),
            "-Model",
            args.model,
            "-ReasoningEffort",
            args.reasoning_effort,
            "-PermissionProfile",
            args.permission_profile,
            "-Harness",
            harness,
            "-NetworkPolicy",
            args.network_policy,
            "-TimeBudgetMinutes",
            str(args.time_budget_minutes),
            "-TaskIds",
            ",".join(args.task_id),
            "-Variants",
            ",".join(args.variant),
        ],
    )
    require_success(result, "pilot preparation")
    validator = script_root / "validate_pilot.py"
    validation = run_command(
        [sys.executable, str(validator), "--output-root", str(output_root), "--prepared-only"],
        timeout=900,
    )
    require_success(validation, "prepared apparatus validation")


def read_operator(output_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    operator = output_root / "_operator"
    return (
        load_json(operator / "pilot-manifest.json"),
        load_json(operator / "execution-profile.json"),
        load_json(operator / "operator-run-log.json"),
    )


def ensure_execution_profile(
    execution_profile: dict[str, Any], args: argparse.Namespace, harness: str
) -> None:
    expected = {
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "permission_profile": args.permission_profile,
        "harness": harness,
        "network_policy": args.network_policy,
        "time_budget_minutes": args.time_budget_minutes,
        "selected_task_ids": args.task_id,
        "selected_variants": args.variant,
    }
    mismatches = {
        key: {"recorded": execution_profile.get(key), "requested": value}
        for key, value in expected.items()
        if execution_profile.get(key) != value
    }
    if mismatches:
        raise RuntimeError(f"Resume settings differ from the checksummed execution profile: {mismatches}")


def record_action(
    recorder: Path,
    output_root: Path,
    action: str,
    **values: str | None,
) -> None:
    result = invoke_powershell(recorder, recorder_arguments(action, output_root, **values))
    require_success(result, f"operator action {action}")


def recover_interrupted_runs(
    *,
    output_root: Path,
    recorder: Path,
    manifest: dict[str, Any],
    operator_log: dict[str, Any],
    state: dict[str, Any],
) -> None:
    manifest_by_key = {run["run_key"]: run for run in manifest["runs"]}
    for operator_run in operator_log["runs"]:
        if operator_run["status"] != "running":
            continue
        run_key = operator_run["run_key"]
        repository = Path(manifest_by_key[run_key]["repository_path"])
        receipt = repository / manifest["agent_receipt"]["path"]
        state_result = state["runs"].get(run_key, {}).get("last_result")
        successful_result = (
            isinstance(state_result, dict)
            and state_result.get("exit_code") == 0
            and not state_result.get("timed_out")
            and not state_result.get("contaminated_signal")
            and receipt.is_file()
        )
        if successful_result:
            record_action(
                recorder,
                output_root,
                "Finish",
                RunKey=run_key,
                ThreadId=state_result.get("thread_id"),
            )
            state["runs"][run_key]["note"] = "Recovered a completed result after runner interruption."
        else:
            record_action(
                recorder,
                output_root,
                "Contaminate",
                RunKey=run_key,
                ThreadId=(state_result or {}).get("thread_id") if isinstance(state_result, dict) else None,
                Message="automation runner was interrupted; the attempt was not retried",
            )
            state["runs"][run_key]["note"] = "Interrupted attempt marked contaminated; no automatic retry."


def summarize(output_root: Path, script_root: Path) -> subprocess.CompletedProcess[str]:
    return run_command(
        [sys.executable, str(script_root / "summarize_pilot.py"), "--output-root", str(output_root)],
        timeout=300,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", required=True)
    parser.add_argument(
        "--permission-profile",
        default="workspace-write; approval=automatic-review",
    )
    parser.add_argument("--network-policy", default="disabled", choices=["disabled", "enabled-but-task-prohibited"])
    parser.add_argument("--time-budget-minutes", type=int, default=30)
    parser.add_argument("--max-parallel", type=int, default=3, choices=[1, 2, 3])
    parser.add_argument("--agent-command", default="codex")
    parser.add_argument("--agent-prefix-arg", action="append", default=[])
    parser.add_argument(
        "--task-id",
        action="append",
        default=[],
        help="Task to include; repeat for a subset. Defaults to every configured task.",
    )
    parser.add_argument(
        "--variant",
        action="append",
        default=[],
        choices=["B", "H"],
        help="Routing variant to include; repeat for a subset. Defaults to B and H.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.time_budget_minutes <= 240:
        raise SystemExit("--time-budget-minutes must be between 1 and 240")

    script_root = Path(__file__).resolve().parent
    config = load_json(script_root / "pilot-config.json")
    configured_task_ids = [str(task["task_id"]) for task in config["tasks"]]
    configured_variants = [str(variant) for variant in config["variants"]]
    args.task_id = args.task_id or configured_task_ids
    args.variant = args.variant or configured_variants
    if len(args.task_id) != len(set(args.task_id)):
        raise SystemExit("--task-id cannot contain duplicates")
    if len(args.variant) != len(set(args.variant)):
        raise SystemExit("--variant cannot contain duplicates")
    unknown_tasks = sorted(set(args.task_id) - set(configured_task_ids))
    if unknown_tasks:
        raise SystemExit(f"Unknown --task-id values: {unknown_tasks}")
    output_root = args.output_root.expanduser().resolve()
    operator = output_root / "_operator"
    lock_path = operator / "automation.lock"

    executable = resolve_command(args.agent_command)
    version = command_version(executable, args.agent_prefix_arg)
    harness = f"Codex CLI automated runner {RUNNER_VERSION}; {version}"
    desired_automation_profile = profile_value(args, executable, version)

    if output_root.exists() and not args.resume:
        raise SystemExit(f"Output root already exists; use --resume or choose a new path: {output_root}")
    if not output_root.exists() and args.resume:
        raise SystemExit(f"Cannot resume a missing output root: {output_root}")
    if not output_root.exists():
        prepare_output(
            script_root=script_root,
            output_root=output_root,
            args=args,
            harness=harness,
        )

    with RunnerLock(lock_path, resume=args.resume):
        manifest, execution_profile, operator_log = read_operator(output_root)
        ensure_execution_profile(execution_profile, args, harness)
        automation_profile_path = operator / "automation-profile.json"
        state_path = operator / "automation-state.json"
        if automation_profile_path.exists():
            recorded_profile = load_json(automation_profile_path)
            if comparable_profile(recorded_profile) != comparable_profile(desired_automation_profile):
                raise RuntimeError("Resume automation settings differ from automation-profile.json.")
        else:
            atomic_write_json(automation_profile_path, desired_automation_profile)
        automation_profile_sha = sha256(automation_profile_path)

        if state_path.exists():
            state = load_json(state_path)
            if state.get("automation_profile_sha256") != automation_profile_sha:
                raise RuntimeError("automation-state.json references a different automation profile.")
        else:
            state = make_initial_state(manifest, automation_profile_sha)

        if operator_log.get("sealed_at") is not None:
            summary_result = summarize(output_root, script_root)
            require_success(summary_result, "summary refresh")
            print(f"Pilot is already sealed. Summary: {operator / 'comparison.md'}")
            if state.get("validation_exit_code") != 0:
                return 1
            return 2 if any(run["status"] == "contaminated" for run in operator_log["runs"]) else 0

        recorder = script_root / "record_operator_run.ps1"
        recover_interrupted_runs(
            output_root=output_root,
            recorder=recorder,
            manifest=manifest,
            operator_log=operator_log,
            state=state,
        )
        _, _, operator_log = read_operator(output_root)
        update_state_from_operator(state, operator_log)
        state["updated_at"] = now_iso()
        atomic_write_json(state_path, state)

        if args.dry_run:
            summary_result = summarize(output_root, script_root)
            require_success(summary_result, "dry-run summary")
            print("pilot-004 dry run OK: preparation, hashes, repositories, and automation state are ready")
            print(f"Summary: {operator / 'comparison.md'}")
            return 0

        manifest_by_key = {run["run_key"]: run for run in manifest["runs"]}
        any_failure = any(run["status"] == "contaminated" for run in operator_log["runs"])
        for task_id in dict.fromkeys(run["task_id"] for run in manifest["runs"]):
            _, _, operator_log = read_operator(output_root)
            operator_by_key = {run["run_key"]: run for run in operator_log["runs"]}
            task_runs = [
                run
                for run in manifest["runs"]
                if run["task_id"] == task_id and operator_by_key[run["run_key"]]["status"] == "pending"
            ]
            if not task_runs:
                continue

            for run in task_runs:
                record_action(recorder, output_root, "Start", RunKey=run["run_key"])
                state_run = state["runs"][run["run_key"]]
                state_run["attempts"] += 1
                state_run["operator_status"] = "running"
            state["updated_at"] = now_iso()
            atomic_write_json(state_path, state)

            results: dict[str, dict[str, Any]] = {}
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(args.max_parallel, len(task_runs)),
                thread_name_prefix=f"pilot-{task_id}",
            ) as executor:
                future_by_key = {
                    executor.submit(
                        execute_agent,
                        executable=executable,
                        prefix_args=args.agent_prefix_arg,
                        repository=Path(run["repository_path"]),
                        prompt_path=Path(run["prompt_path"]),
                        run_directory=operator / "runs" / run["run_key"],
                        model=args.model,
                        reasoning_effort=args.reasoning_effort,
                        timeout_minutes=args.time_budget_minutes,
                    ): run["run_key"]
                    for run in task_runs
                }
                for future in concurrent.futures.as_completed(future_by_key):
                    run_key = future_by_key[future]
                    try:
                        results[run_key] = future.result()
                    except Exception as exc:  # preserve the other variants and leave evidence
                        results[run_key] = {
                            "exit_code": None,
                            "timed_out": False,
                            "spawn_error": f"{type(exc).__name__}: {exc}",
                            "receipt_exists": False,
                            "contaminated_signal": False,
                            "needs_intervention": False,
                            "thread_id": None,
                        }

            for run in task_runs:
                run_key = run["run_key"]
                result = results[run_key]
                state["runs"][run_key]["last_result"] = result
                success = (
                    result.get("exit_code") == 0
                    and not result.get("timed_out")
                    and not result.get("spawn_error")
                    and result.get("receipt_exists") is True
                    and not result.get("contaminated_signal")
                    and not result.get("needs_intervention")
                )
                if success:
                    record_action(
                        recorder,
                        output_root,
                        "Finish",
                        RunKey=run_key,
                        ThreadId=result.get("thread_id"),
                    )
                    state["runs"][run_key]["operator_status"] = "completed"
                else:
                    any_failure = True
                    reasons = []
                    if result.get("timed_out"):
                        reasons.append("time budget exceeded")
                    if result.get("spawn_error"):
                        reasons.append("Agent process failed to start")
                    if result.get("exit_code") not in (0, None):
                        reasons.append(f"Agent exited with code {result.get('exit_code')}")
                    if result.get("contaminated_signal"):
                        reasons.append("Agent reported external-context contamination")
                    if result.get("needs_intervention"):
                        reasons.append("Agent requested operator intervention in unattended mode")
                    if not result.get("receipt_exists"):
                        reasons.append("Agent receipt missing")
                    message = "; ".join(reasons) or "unclassified automated-run failure"
                    record_action(
                        recorder,
                        output_root,
                        "Contaminate",
                        RunKey=run_key,
                        ThreadId=result.get("thread_id"),
                        Message=message,
                    )
                    state["runs"][run_key]["operator_status"] = "contaminated"
                    state["runs"][run_key]["note"] = message
                state["updated_at"] = now_iso()
                atomic_write_json(state_path, state)

            if any_failure and args.stop_on_failure:
                summary_result = summarize(output_root, script_root)
                require_success(summary_result, "partial summary")
                print(f"Stopped after a contaminated run. Resume evidence is in {operator}", file=sys.stderr)
                return 2

        _, _, operator_log = read_operator(output_root)
        unfinished = [run["run_key"] for run in operator_log["runs"] if run["status"] not in TERMINAL_STATUSES]
        if unfinished:
            raise RuntimeError(f"Runner ended with unfinished runs: {unfinished}")

        record_action(
            recorder,
            output_root,
            "Seal",
            ConfirmSameExecutionSettings="true",
        )
        state["sealed"] = True
        validator_command = [
            sys.executable,
            str(script_root / "validate_pilot.py"),
            "--output-root",
            str(output_root),
        ]
        if version.startswith("mock-codex"):
            validator_command.append("--skip-security-acceptance")
        validator_result = run_command(validator_command, timeout=3600)
        state["validation_exit_code"] = validator_result.returncode
        state["validation_stdout"] = validator_result.stdout
        state["validation_stderr"] = validator_result.stderr
        state["updated_at"] = now_iso()
        atomic_write_json(state_path, state)

        summary_result = summarize(output_root, script_root)
        require_success(summary_result, "final summary")
        state["summary_path"] = str(operator / "comparison.md")
        atomic_write_json(state_path, state)

        if validator_result.returncode != 0:
            print(validator_result.stdout, end="")
            print(validator_result.stderr, file=sys.stderr, end="")
            return 1
        print(validator_result.stdout, end="")
        print(f"Automated comparison: {operator / 'comparison.md'}")
        return 2 if any_failure else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
