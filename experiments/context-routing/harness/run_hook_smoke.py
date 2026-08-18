#!/usr/bin/env python3
"""Run one tiny Codex CLI task to verify current Hook/tool-response evidence semantics."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from _common import atomic_write_json, now_iso
from seal_raw_evidence import seal, verify
from validate_access_audit import validate
from validate_cli_events import validate as validate_cli_events


SCRIPT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PARENT = Path(r"D:\coding warehouse\project-orrery-benchmark")


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None, input_text: str | None = None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )


def copy_apparatus(repository: Path) -> None:
    benchmark = repository / ".benchmark"
    benchmark.mkdir(parents=True)
    for name in ("_common.py", "context_read_proxy.py", "hook_audit.py"):
        shutil.copy2(SCRIPT_ROOT / name, benchmark / name)
    codex = repository / ".codex"
    codex.mkdir(parents=True)
    hook_command = f'"{Path(sys.executable).resolve()}" "{(benchmark / "hook_audit.py").resolve()}"'
    hook_handler = {
        "type": "command",
        "command": hook_command,
        "commandWindows": hook_command,
        "timeout": 30,
    }
    hooks = {
        "description": "Generated Hook smoke configuration with absolute local commands.",
        "hooks": {
            "SessionStart": [{"matcher": "startup", "hooks": [hook_handler]}],
            "PreToolUse": [{"matcher": "^Bash$", "hooks": [hook_handler]}],
            "PostToolUse": [{"matcher": "^Bash$", "hooks": [hook_handler]}],
        },
    }
    atomic_write_json(codex / "hooks.json", hooks)
    (codex / "config.toml").write_text("[features]\nhooks = true\n", encoding="utf-8", newline="\n")


def hook_config_overrides(repository: Path) -> list[str]:
    script = (repository / ".benchmark" / "hook_audit.py").resolve().as_posix()
    python = Path(sys.executable).resolve().as_posix()
    command = f'"{python}" "{script}"'
    handler = (
        "{type=\"command\","
        f"command='{command}',command_windows='{command}',timeout=30}}"
    )
    return [
        f'hooks.SessionStart=[{{matcher="^startup$",hooks=[{handler}]}}]',
        f'hooks.PreToolUse=[{{matcher="^Bash$",hooks=[{handler}]}}]',
        f'hooks.PostToolUse=[{{matcher="^Bash$",hooks=[{handler}]}}]',
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=r"D:\Tools\Codex\npm\codex.cmd")
    parser.add_argument("--output-parent", type=Path, default=DEFAULT_OUTPUT_PARENT)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="medium")
    args = parser.parse_args(argv)

    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    output_root = args.output_parent.resolve() / f"h2-hook-smoke-{stamp}"
    if output_root.exists():
        raise RuntimeError(f"output already exists: {output_root}")
    repository = output_root / "repository"
    operator = output_root / "_operator"
    repository.mkdir(parents=True)
    operator.mkdir(parents=True)

    (repository / "note.txt").write_text(
        "ORRERY_SENTINEL_7F2A\nsecond line\n", encoding="utf-8", newline="\n"
    )
    initialized = run(["git", "init", "-b", "benchmark"], cwd=repository)
    if initialized.returncode != 0:
        raise RuntimeError(initialized.stderr)
    run(["git", "add", "note.txt"], cwd=repository)
    committed = run(
        [
            "git",
            "-c",
            "user.name=Project Orrery Benchmark",
            "-c",
            "user.email=benchmark@local.invalid",
            "commit",
            "-m",
            "hook smoke baseline",
        ],
        cwd=repository,
    )
    if committed.returncode != 0:
        raise RuntimeError(committed.stderr)
    source_commit = run(["git", "rev-parse", "HEAD"], cwd=repository).stdout.strip()
    copy_apparatus(repository)
    exclude = repository / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(".benchmark/\n.codex/\n")

    policy_path = operator / "access-policy.json"
    state_path = operator / "access-state.json"
    proxy_log = operator / "proxy-audit.jsonl"
    hook_log = operator / "hook-audit.jsonl"
    atomic_write_json(
        policy_path,
        {
            "schema_version": 1,
            "proxy_script": ".benchmark/context_read_proxy.py",
            "allowed_non_content_tools": ["update_plan"],
            "postwrite_commands": [],
            "expected_write_paths": [],
            "minimum_content_reads": 1,
        },
    )
    atomic_write_json(
        state_path,
        {"schema_version": 1, "phase": "prewrite", "read_ranges": {}},
    )
    environment = {
        **os.environ,
        "ORRERY_BENCHMARK_REPO_ROOT": str(repository),
        "ORRERY_PROXY_AUDIT_LOG": str(proxy_log),
        "ORRERY_HOOK_AUDIT_LOG": str(hook_log),
        "ORRERY_ACCESS_STATE": str(state_path),
        "ORRERY_ACCESS_POLICY": str(policy_path),
    }
    prompt = (
        "This is a controlled read-only Hook smoke test. Do not edit files. "
        "Use exactly `python .benchmark/context_read_proxy.py read --path note.txt --start 1 --end 1`, "
        "then reply with only the returned sentinel line. Do not use any other tool or command."
    )
    (operator / "prompt.txt").write_text(prompt + "\n", encoding="utf-8", newline="\n")
    events_path = operator / "events.jsonl"
    stderr_path = operator / "stderr.log"
    final_path = operator / "final-message.txt"
    command = [
        str(Path(args.codex).resolve(strict=True)),
        "--dangerously-bypass-hook-trust",
        "--approve-for-me",
        "--model",
        args.model,
        "-c",
        f'model_reasoning_effort="{args.reasoning_effort}"',
        "-c",
        "sandbox_workspace_write.network_access=false",
        "-c",
        "features.hooks=true",
        "-c",
        f'projects."{repository.as_posix()}".trust_level="trusted"',
    ]
    for override in hook_config_overrides(repository):
        command.extend(["-c", override])
    command.extend([
        "exec",
        "--ephemeral",
        "--json",
        "--ignore-user-config",
        "-C",
        str(repository),
        "-o",
        str(final_path),
        "-",
    ])
    started_at = now_iso()
    result = run(command, cwd=repository, env=environment, input_text=prompt)
    ended_at = now_iso()
    events_path.write_text(result.stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(result.stderr, encoding="utf-8", newline="\n")

    hook_audit = validate(proxy_log, hook_log) if proxy_log.exists() and hook_log.exists() else None
    cli_audit = (
        validate_cli_events(events_path, proxy_log, policy_path)
        if proxy_log.exists()
        else {"apparatus_valid": False, "error": "proxy audit log missing"}
    )
    audit = hook_audit if hook_audit and hook_audit.get("apparatus_valid") else cli_audit
    final_text = final_path.read_text(encoding="utf-8", errors="replace") if final_path.is_file() else ""
    accepted = (
        result.returncode == 0
        and audit.get("apparatus_valid") is True
        and final_text.strip() == "ORRERY_SENTINEL_7F2A"
    )
    summary = {
        "schema_version": 1,
        "started_at": started_at,
        "ended_at": ended_at,
        "codex_exit_code": result.returncode,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "source_commit": source_commit,
        "accepted": accepted,
        "final_message": final_text.strip(),
        "access_audit": audit,
        "hook_audit_available": hook_audit is not None,
    }
    atomic_write_json(operator / "smoke-summary.json", summary)
    classification = "exploratory" if accepted else "contaminated"
    manifest_path = output_root / "raw-evidence-manifest.json"
    seal(
        run_root=output_root,
        manifest_path=manifest_path,
        policy_path=SCRIPT_ROOT / "raw-evidence-retention-policy.json",
        pilot_id="h2-hook-smoke",
        run_id=output_root.name,
        classification=classification,
        source_commit=source_commit,
        apparatus_version="h2-read-proof-v0.1",
        created_at=started_at,
    )
    sealed_evidence = verify(manifest_path)
    summary["raw_evidence_verification"] = sealed_evidence
    if not sealed_evidence["valid"]:
        accepted = False
        summary["accepted"] = False
    print(json.dumps({"output_root": str(output_root), **summary}, ensure_ascii=False, indent=2))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
