#!/usr/bin/env python3
"""Create a local JSON and Markdown comparison for a pilot-004 output root."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temporary, path)


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def changed_paths(repository: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [line[3:].strip().replace("\\", "/") for line in result.stdout.splitlines() if len(line) >= 4]


def receipt_metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "content_reads_self_reported": None,
            "enumerations_self_reported": None,
            "searches_self_reported": None,
            "scope_expansions_self_reported": None,
        }
    receipt = load_json(path)
    events = receipt.get("events", [])
    count = lambda kind: sum(1 for event in events if event.get("event_type") == kind)
    return {
        "content_reads_self_reported": count("content_read"),
        "enumerations_self_reported": count("enumerate"),
        "searches_self_reported": count("search"),
        "scope_expansions_self_reported": count("scope_expand"),
    }


def mean(values: list[float | int]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def build_summary(output_root: Path) -> dict[str, Any]:
    operator = output_root / "_operator"
    manifest = load_json(operator / "pilot-manifest.json")
    log = load_json(operator / "operator-run-log.json")
    state_path = operator / "automation-state.json"
    state = load_json(state_path) if state_path.is_file() else {"runs": {}}
    log_by_key = {run["run_key"]: run for run in log["runs"]}
    rows: list[dict[str, Any]] = []

    for run in manifest["runs"]:
        run_key = run["run_key"]
        operator_run = log_by_key[run_key]
        run_state = state.get("runs", {}).get(run_key, {})
        result = run_state.get("last_result") or {}
        started = parse_time(operator_run.get("operator_started_at"))
        ended = parse_time(operator_run.get("operator_ended_at"))
        duration = round((ended - started).total_seconds(), 3) if started and ended else None
        agent_started = parse_time(result.get("started_at"))
        agent_ended = parse_time(result.get("ended_at"))
        agent_duration = (
            round((agent_ended - agent_started).total_seconds(), 3)
            if agent_started and agent_ended
            else None
        )
        repository = Path(run["repository_path"])
        receipt = repository / manifest["agent_receipt"]["path"]
        metrics = receipt_metrics(receipt)
        rows.append(
            {
                "run_key": run_key,
                "task_id": run["task_id"],
                "variant": run["variant"],
                "status": operator_run["status"],
                "operator_seconds": duration,
                "agent_seconds": agent_duration,
                "attempts": run_state.get("attempts", 0),
                "thread_id": operator_run.get("thread_id"),
                "exit_code": result.get("exit_code"),
                "timed_out": result.get("timed_out"),
                "usage": result.get("usage", {}),
                "harness_event_count": result.get("event_count"),
                "malformed_harness_events": result.get("malformed_event_count"),
                "changed_paths": changed_paths(repository),
                "note": run_state.get("note"),
                **metrics,
            }
        )

    by_variant: dict[str, Any] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["variant"]].append(row)
    selected_variants = manifest.get("selection", {}).get("variants", ["A", "B", "C"])
    for variant in selected_variants:
        items = grouped[variant]
        completed = [row for row in items if row["status"] == "completed"]
        token_keys = {
            key
            for row in completed
            for key, value in row.get("usage", {}).items()
            if isinstance(value, int) and not isinstance(value, bool)
        }
        by_variant[variant] = {
            "completed": len(completed),
            "contaminated": sum(row["status"] == "contaminated" for row in items),
            "pending_or_running": sum(row["status"] not in {"completed", "contaminated"} for row in items),
            "mean_operator_seconds": mean(
                [row["operator_seconds"] for row in completed if row["operator_seconds"] is not None]
            ),
            "mean_agent_seconds": mean(
                [row["agent_seconds"] for row in completed if row["agent_seconds"] is not None]
            ),
            "mean_content_reads_self_reported": mean(
                [
                    row["content_reads_self_reported"]
                    for row in completed
                    if row["content_reads_self_reported"] is not None
                ]
            ),
            "usage_totals": {
                key: sum(int(row.get("usage", {}).get(key, 0)) for row in completed) for key in sorted(token_keys)
            },
        }

    return {
        "schema_version": 1,
        "pilot_id": manifest["pilot_id"],
        "generated_at": datetime.now().astimezone().isoformat(),
        "sealed": log.get("sealed_at") is not None,
        "validation_exit_code": state.get("validation_exit_code"),
        "selection": manifest.get("selection", {}),
        "evidence_boundary": (
            "Codex JSONL independently records emitted Harness events and commands, but Agent receipt reads remain "
            "self-report and neither source proves the exact bytes visible to the model."
        ),
        "variants": by_variant,
        "runs": rows,
    }


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Project Orrery context-routing pilot-004 B/H automated comparison",
        "",
        f"> Generated: `{summary['generated_at']}`  ",
        f"> Sealed: `{str(summary['sealed']).lower()}`  ",
        f"> Full validator exit code: `{summary['validation_exit_code']}`",
        "",
        "This is an experiment report, not an ADR or a released routing policy.",
        "",
        "## Evidence boundary",
        "",
        summary["evidence_boundary"],
        "",
        "## Variant summary",
        "",
        "| Variant | Completed | Contaminated | Pending/running | Mean agent seconds | Mean self-reported content reads | Usage totals |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for variant in summary["selection"].get("variants", summary["variants"]):
        item = summary["variants"][variant]
        lines.append(
            f"| {variant} | {item['completed']} | {item['contaminated']} | {item['pending_or_running']} | "
            f"{item['mean_agent_seconds']} | {item['mean_content_reads_self_reported']} | "
            f"`{json.dumps(item['usage_totals'], ensure_ascii=False, sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Individual runs",
            "",
            "| Run | Status | Agent seconds | Attempts | Self-reported reads | Harness events | Changed paths | Note |",
            "|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in summary["runs"]:
        changed = "<br>".join(f"`{path}`" for path in row["changed_paths"]) or "—"
        note = (row.get("note") or "—").replace("|", "\\|")
        lines.append(
            f"| {row['run_key']} | {row['status']} | {row['agent_seconds']} | {row['attempts']} | "
            f"{row['content_reads_self_reported']} | {row['harness_event_count']} | {changed} | {note} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation gate",
            "",
            "Do not promote this report into an architecture decision until task acceptance, dependency recall, "
            "contamination, and evidence provenance have been reviewed together. Lower read counts alone do not win.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    output_root = args.output_root.resolve()
    summary = build_summary(output_root)
    operator = output_root / "_operator"
    atomic_write(operator / "automation-summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    atomic_write(operator / "comparison.md", markdown(summary))
    print(operator / "comparison.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
