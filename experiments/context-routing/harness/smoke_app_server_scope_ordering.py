#!/usr/bin/env python3
"""Run one isolated Codex app-server turn to verify usage/fileChange ordering."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import subprocess
import tempfile
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROMPT = """Follow the repository instructions exactly.
First use a shell command to read instruction.txt. Only after reading it, use the apply_patch tool to change
marker.txt from BEFORE to AFTER. Do not use a shell command or redirection to write the file. Do not edit any
other file. Then reply with one short sentence.
"""

REQUIRED_RUNTIME_FILES = (
    "codex-code-mode-host.exe",
    "codex-command-runner.exe",
    "codex-windows-sandbox-setup.exe",
    "rg.exe",
)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _run(arguments: list[str], *, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _prepare_repository(repository: Path) -> str:
    repository.mkdir(parents=True)
    (repository / "AGENTS.md").write_text(
        "# Scope ordering smoke\n\n"
        "Read `instruction.txt` before any write. Only edit `marker.txt`, and use the apply_patch tool.\n",
        encoding="utf-8",
        newline="\n",
    )
    (repository / "instruction.txt").write_text(
        "Change the complete contents of marker.txt from BEFORE to AFTER.\n",
        encoding="utf-8",
        newline="\n",
    )
    (repository / "marker.txt").write_text("BEFORE\n", encoding="utf-8", newline="\n")
    commands = (
        ["git", "init", "-b", "scope-ordering-smoke"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "config", "core.filemode", "false"],
        ["git", "add", "--all"],
        [
            "git",
            "-c",
            "user.name=Project Orrery Benchmark",
            "-c",
            "user.email=benchmark@local.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "scope ordering smoke baseline",
        ],
    )
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2026-08-19T00:02:00+08:00",
            "GIT_COMMITTER_DATE": "2026-08-19T00:02:00+08:00",
        }
    )
    for command in commands:
        result = subprocess.run(
            command,
            cwd=repository,
            env=environment,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("cannot prepare smoke repository: " + result.stdout + result.stderr)
    head = _run(["git", "rev-parse", "HEAD"], cwd=repository)
    if head.returncode:
        raise RuntimeError("cannot resolve smoke baseline: " + head.stderr)
    return head.stdout.strip()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class AppServerClient:
    def __init__(
        self,
        executable: Path,
        repository: Path,
        output_root: Path,
        *,
        environment: dict[str, str] | None = None,
        config_overrides: tuple[str, ...] = (),
    ) -> None:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        command = [
            str(executable),
            "app-server",
            "--stdio",
            "-c",
            "analytics.enabled=false",
        ]
        for override in config_overrides:
            command.extend(("-c", override))
        self.command = command
        self.process = subprocess.Popen(
            command,
            cwd=repository,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creationflags,
        )
        if self.process.stdin is None or self.process.stdout is None or self.process.stderr is None:
            raise RuntimeError("app-server pipes were not created")
        self.messages: list[dict[str, Any]] = []
        self.incoming: queue.Queue[dict[str, Any] | BaseException | None] = queue.Queue()
        self._stdout_path = output_root / "server-events.jsonl"
        self._stderr_path = output_root / "server-stderr.log"
        self._client_path = output_root / "client-requests.jsonl"
        self._stdout_handle = self._stdout_path.open("w", encoding="utf-8", newline="\n", buffering=1)
        self._stderr_handle = self._stderr_path.open("w", encoding="utf-8", newline="\n", buffering=1)
        self._client_handle = self._client_path.open("w", encoding="utf-8", newline="\n", buffering=1)
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()

    def _read_stdout(self) -> None:
        try:
            assert self.process.stdout is not None
            for raw in self.process.stdout:
                self._stdout_handle.write(raw if raw.endswith("\n") else raw + "\n")
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    self.incoming.put(RuntimeError(f"non-JSON app-server stdout: {raw.rstrip()}: {exc}"))
                    continue
                if not isinstance(value, dict):
                    self.incoming.put(RuntimeError("app-server emitted a non-object JSON-RPC message"))
                    continue
                self.messages.append(value)
                self.incoming.put(value)
        except BaseException as exc:  # pragma: no cover - defensive thread boundary
            self.incoming.put(exc)
        finally:
            self.incoming.put(None)

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        for raw in self.process.stderr:
            self._stderr_handle.write(raw if raw.endswith("\n") else raw + "\n")

    def send(self, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        self._client_handle.write(payload + "\n")
        assert self.process.stdin is not None
        self.process.stdin.write(payload + "\n")
        self.process.stdin.flush()

    def wait_for(self, predicate: Callable[[dict[str, Any]], bool], deadline: float) -> dict[str, Any]:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out waiting for app-server message")
            try:
                value = self.incoming.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("timed out waiting for app-server message") from exc
            if value is None:
                raise RuntimeError(f"app-server stdout closed with exit code {self.process.poll()}")
            if isinstance(value, BaseException):
                raise value
            if "id" in value and "method" in value:
                raise RuntimeError(f"unexpected app-server request: {value.get('method')}")
            if predicate(value):
                return value

    def wait_for_response(self, request_id: int, deadline: float) -> dict[str, Any]:
        response = self.wait_for(lambda value: value.get("id") == request_id, deadline)
        if "error" in response:
            raise RuntimeError(f"app-server request {request_id} failed: {response['error']}")
        return response

    def close(self) -> None:
        try:
            if self.process.stdin is not None and not self.process.stdin.closed:
                self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self._stdout_thread.join(timeout=2)
        self._stderr_thread.join(timeout=2)
        self._stdout_handle.close()
        self._stderr_handle.close()
        self._client_handle.close()


def _usage_total(event: dict[str, Any]) -> dict[str, int] | None:
    if event.get("method") != "thread/tokenUsage/updated":
        return None
    params = event.get("params")
    token_usage = params.get("tokenUsage") if isinstance(params, dict) else None
    total = token_usage.get("total") if isinstance(token_usage, dict) else None
    if not isinstance(total, dict):
        return None
    expected = (
        "inputTokens",
        "cachedInputTokens",
        "cacheWriteInputTokens",
        "outputTokens",
        "reasoningOutputTokens",
        "totalTokens",
    )
    if not all(isinstance(total.get(key), int) and total[key] >= 0 for key in expected):
        return None
    return {key: int(total[key]) for key in expected}


def _analyze_ordering(
    messages: list[dict[str, Any]],
    *,
    thread_id: str,
    turn_id: str,
    repository: Path,
) -> dict[str, Any]:
    boundary_index: int | None = None
    boundary_item: dict[str, Any] | None = None
    command_completed_before = 0
    for index, event in enumerate(messages):
        params = event.get("params")
        item = params.get("item") if isinstance(params, dict) else None
        if event.get("method") == "item/completed" and isinstance(item, dict):
            if item.get("type") == "commandExecution" and boundary_index is None:
                command_completed_before += 1
        if event.get("method") == "item/started" and isinstance(item, dict) and item.get("type") == "fileChange":
            boundary_index = index
            boundary_item = item
            break

    usage_updates: list[dict[str, Any]] = []
    monotonic = True
    previous: dict[str, int] | None = None
    for index, event in enumerate(messages):
        params = event.get("params")
        if not isinstance(params, dict):
            continue
        if str(params.get("threadId", "")) != thread_id or str(params.get("turnId", "")) != turn_id:
            continue
        total = _usage_total(event)
        if total is None:
            continue
        if previous is not None and any(total[key] < previous[key] for key in total):
            monotonic = False
        previous = total
        usage_updates.append({"event_index": index, "total": total})

    before = [
        update
        for update in usage_updates
        if boundary_index is not None and update["event_index"] < boundary_index
    ]
    status = _run(["git", "status", "--short"], cwd=repository)
    changed_paths = []
    if status.returncode == 0:
        changed_paths = [line[3:].replace("\\", "/") for line in status.stdout.splitlines() if len(line) >= 4]
    marker_after = (repository / "marker.txt").read_text(encoding="utf-8") == "AFTER\n"
    turn_completed = any(
        event.get("method") == "turn/completed"
        and isinstance(event.get("params"), dict)
        and str(event["params"].get("threadId", "")) == thread_id
        and isinstance(event["params"].get("turn"), dict)
        and str(event["params"]["turn"].get("id", "")) == turn_id
        and event["params"]["turn"].get("status") == "completed"
        for event in messages
    )
    verified = bool(
        boundary_index is not None
        and before
        and monotonic
        and command_completed_before >= 1
        and marker_after
        and changed_paths == ["marker.txt"]
        and turn_completed
    )
    return {
        "schema_version": 1,
        "ordering_verified": verified,
        "thread_id": thread_id,
        "turn_id": turn_id,
        "event_count": len(messages),
        "method_counts": dict(sorted(Counter(str(event.get("method")) for event in messages if event.get("method")).items())),
        "scope_boundary": {
            "event_index": boundary_index,
            "item_id": boundary_item.get("id") if boundary_item else None,
            "changes": boundary_item.get("changes") if boundary_item else None,
        },
        "usage_updates": usage_updates,
        "prewrite_usage_update_count": len(before),
        "prewrite_usage": before[-1]["total"] if before else None,
        "usage_monotonic": monotonic,
        "command_executions_completed_before_scope": command_completed_before,
        "marker_after": marker_after,
        "changed_paths": changed_paths,
        "turn_completed": turn_completed,
    }


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    executable = args.codex_exe.resolve(strict=True)
    runtime_files: dict[str, str] = {}
    if os.name == "nt":
        for name in REQUIRED_RUNTIME_FILES:
            path = executable.parent / name
            if not path.is_file():
                raise RuntimeError(f"required Codex runtime sibling is missing: {path}")
            runtime_files[name] = _hash_file(path)
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise RuntimeError(f"output root already exists: {output_root}")
    output_root.mkdir(parents=True)
    repository = output_root / "repository"
    baseline_commit = _prepare_repository(repository)
    version = _run([str(executable), "--version"], cwd=repository)
    if version.returncode:
        raise RuntimeError("cannot read Codex version: " + version.stderr)
    metadata = {
        "schema_version": 1,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "single-turn app-server usage/fileChange ordering compatibility smoke",
        "formal_pilot": False,
        "codex_version": version.stdout.strip(),
        "codex_executable_sha256": _hash_file(executable),
        "codex_runtime_sibling_sha256": runtime_files,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "approval_policy": "never",
        "sandbox": "workspace-write",
        "repository": str(repository),
        "baseline_commit": baseline_commit,
        "prompt": PROMPT,
    }
    _write_json(output_root / "run-metadata.json", metadata)

    deadline = time.monotonic() + args.timeout_seconds
    client = AppServerClient(executable, repository, output_root)
    thread_id = ""
    turn_id = ""
    try:
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "project-orrery-scope-smoke", "version": "0.1.0"},
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
                    "model": args.model,
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
                    "input": [{"type": "text", "text": PROMPT}],
                    "cwd": str(repository),
                    "model": args.model,
                    "effort": args.reasoning_effort,
                    "approvalPolicy": "never",
                },
            }
        )
        turn_response = client.wait_for_response(3, deadline)
        turn = turn_response.get("result", {}).get("turn", {})
        turn_id = str(turn.get("id", ""))
        if not turn_id:
            raise RuntimeError("turn/start response has no turn id")
        client.wait_for(
            lambda value: value.get("method") == "turn/completed"
            and isinstance(value.get("params"), dict)
            and str(value["params"].get("threadId", "")) == thread_id
            and isinstance(value["params"].get("turn"), dict)
            and str(value["params"]["turn"].get("id", "")) == turn_id,
            deadline,
        )
        time.sleep(0.25)
    finally:
        client.close()

    report = _analyze_ordering(
        client.messages,
        thread_id=thread_id,
        turn_id=turn_id,
        repository=repository,
    )
    report["codex_version"] = metadata["codex_version"]
    report["output_root"] = str(output_root)
    _write_json(output_root / "ordering-report.json", report)
    return report


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="orrery-appserver-ordering-selftest-") as temporary:
        repository = Path(temporary) / "repository"
        _prepare_repository(repository)
        (repository / "marker.txt").write_text("AFTER\n", encoding="utf-8", newline="\n")
        thread_id = "thread-self-test"
        turn_id = "turn-self-test"
        total = {
            "inputTokens": 100,
            "cachedInputTokens": 40,
            "cacheWriteInputTokens": 0,
            "outputTokens": 10,
            "reasoningOutputTokens": 2,
            "totalTokens": 110,
        }
        command = {
            "method": "item/completed",
            "params": {
                "threadId": thread_id,
                "turnId": turn_id,
                "item": {"id": "command-1", "type": "commandExecution"},
            },
        }
        usage = {
            "method": "thread/tokenUsage/updated",
            "params": {
                "threadId": thread_id,
                "turnId": turn_id,
                "tokenUsage": {"total": total},
            },
        }
        boundary = {
            "method": "item/started",
            "params": {
                "threadId": thread_id,
                "turnId": turn_id,
                "item": {
                    "id": "write-1",
                    "type": "fileChange",
                    "changes": [{"path": str(repository / "marker.txt")}],
                },
            },
        }
        completed = {
            "method": "turn/completed",
            "params": {
                "threadId": thread_id,
                "turn": {"id": turn_id, "status": "completed"},
            },
        }
        valid = _analyze_ordering(
            [command, usage, boundary, completed],
            thread_id=thread_id,
            turn_id=turn_id,
            repository=repository,
        )
        if not valid["ordering_verified"]:
            raise RuntimeError("valid synthetic ordering was rejected")
        invalid = _analyze_ordering(
            [command, boundary, usage, completed],
            thread_id=thread_id,
            turn_id=turn_id,
            repository=repository,
        )
        if invalid["ordering_verified"]:
            raise RuntimeError("post-write-only usage was accepted")
    return {"self_test": "passed", "cases": 2}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-exe", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        try:
            result = self_test()
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f"app-server-scope-smoke-self-test: {exc}", file=__import__("sys").stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.codex_exe is None or args.output_root is None:
        parser.error("--codex-exe and --output-root are required unless --self-test is used")
    if args.timeout_seconds < 30 or args.timeout_seconds > 900:
        parser.error("--timeout-seconds must be between 30 and 900")
    try:
        result = run_smoke(args)
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
        output_root = args.output_root.resolve()
        if output_root.is_dir():
            _write_json(output_root / "failure.json", {"error": str(exc), "type": type(exc).__name__})
        print(f"app-server-scope-smoke: {exc}", file=__import__("sys").stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ordering_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
