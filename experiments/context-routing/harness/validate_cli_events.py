#!/usr/bin/env python3
"""Audit a complete ``codex exec --json`` stream against the read-proxy policy."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _common import load_json, read_jsonl
from hook_audit import (
    _extract_content_proofs,
    _is_proxy_command,
    _normalize_command,
    _unwrap_powershell_command,
)


DEFAULT_INFORMATIONAL_ITEMS = {
    "agent_message",
    "reasoning",
    "error",
    "plan_update",
}


def _path_values(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"path", "file_path", "filename"} and isinstance(child, str):
                found.append(child.replace("\\", "/"))
            found.extend(_path_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_path_values(child))
    return found


def _reported_path(value: str, repository_root: Path | None) -> str:
    normalized = value.replace("\\", "/")
    if repository_root is None:
        return normalized
    candidate = Path(value)
    if not candidate.is_absolute():
        return normalized
    try:
        return candidate.resolve().relative_to(repository_root).as_posix()
    except (OSError, ValueError):
        return normalized


def validate(events_path: Path, proxy_log: Path, policy_path: Path) -> dict[str, Any]:
    events = read_jsonl(events_path)
    proxy_events = read_jsonl(proxy_log)
    policy = load_json(policy_path, {})
    proxy_script = str(policy.get("proxy_script", ".benchmark/context_read_proxy.py"))
    repository_value = policy.get("repository_root")
    repository_root = (
        Path(repository_value).resolve()
        if isinstance(repository_value, str) and repository_value
        else None
    )
    postwrite_commands = {
        _normalize_command(str(command)) for command in policy.get("postwrite_commands", [])
    }
    expected_write_paths = {
        str(path).replace("\\", "/") for path in policy.get("expected_write_paths", [])
    }
    informational_items = DEFAULT_INFORMATIONAL_ITEMS | {
        str(item) for item in policy.get("allowed_informational_item_types", [])
    }

    started_local: set[str] = set()
    completed_local: set[str] = set()
    unapproved_commands: list[str] = []
    failed_proxy_commands: list[str] = []
    failed_postwrite_commands: list[str] = []
    unexpected_item_types: list[str] = []
    unexpected_write_paths: list[str] = []
    proofs: list[dict[str, Any]] = []
    completed_command_count = 0

    for event in events:
        event_type = str(event.get("type", ""))
        item = event.get("item")
        if not isinstance(item, dict) or not event_type.startswith("item."):
            continue
        item_type = str(item.get("type", ""))
        item_id = str(item.get("id", ""))
        if event_type == "item.started" and item_type in {"command_execution", "file_change"}:
            started_local.add(item_id)
        if event_type != "item.completed":
            continue
        if item_type == "command_execution":
            completed_local.add(item_id)
            completed_command_count += 1
            command = str(item.get("command", ""))
            normalized = _normalize_command(_unwrap_powershell_command(command))
            proxy_command = _is_proxy_command(command, proxy_script)
            approved_postwrite = normalized in postwrite_commands
            if not proxy_command and not approved_postwrite:
                unapproved_commands.append(command)
            if item.get("status") != "completed" or item.get("exit_code") != 0:
                if proxy_command:
                    failed_proxy_commands.append(item_id)
                elif approved_postwrite:
                    failed_postwrite_commands.append(item_id)
            proofs.extend(_extract_content_proofs(item.get("aggregated_output")))
        elif item_type == "file_change":
            completed_local.add(item_id)
            paths = _path_values(item)
            if not paths:
                unexpected_write_paths.append("<unreported-path>")
            for path in paths:
                reported = _reported_path(path, repository_root)
                if reported not in expected_write_paths:
                    unexpected_write_paths.append(reported)
        elif item_type not in informational_items:
            unexpected_item_types.append(item_type or "<missing-type>")

    incomplete_local_items = sorted(started_local - completed_local)
    reads = [event for event in proxy_events if event.get("operation") == "read"]
    read_ids = [str(event.get("request_id")) for event in reads]
    duplicate_read_ids = sorted(key for key, count in Counter(read_ids).items() if count != 1)
    proof_map: dict[str, list[dict[str, Any]]] = {}
    for proof in proofs:
        proof_map.setdefault(str(proof.get("request_id")), []).append(proof)

    missing_proofs: list[str] = []
    invalid_proofs: list[str] = []
    for event in reads:
        request_id = str(event.get("request_id"))
        matching = proof_map.get(request_id, [])
        if len(matching) != 1:
            missing_proofs.append(request_id)
            continue
        proof = matching[0]
        if not proof.get("proof_valid") or proof.get("claimed_returned_sha256") != event.get(
            "returned_sha256"
        ):
            invalid_proofs.append(request_id)

    minimum_reads = int(policy.get("minimum_content_reads", 1))
    failures_present = any(
        (
            unapproved_commands,
            failed_proxy_commands,
            unexpected_item_types,
            unexpected_write_paths,
            incomplete_local_items,
            duplicate_read_ids,
            missing_proofs,
            invalid_proofs,
        )
    ) or len(reads) < minimum_reads
    return {
        "schema_version": 1,
        "apparatus_valid": not failures_present,
        "evidence_mode": "codex-exec-jsonl-posthoc",
        "content_reads_proved": len(reads) - len(missing_proofs) - len(invalid_proofs),
        "content_reads_total": len(reads),
        "returned_bytes_total": sum(int(event.get("returned_bytes", 0)) for event in reads),
        "completed_command_count": completed_command_count,
        "minimum_content_reads": minimum_reads,
        "unapproved_commands": unapproved_commands,
        "failed_proxy_commands": failed_proxy_commands,
        "failed_postwrite_commands": failed_postwrite_commands,
        "unexpected_item_types": sorted(set(unexpected_item_types)),
        "unexpected_write_paths": sorted(set(unexpected_write_paths)),
        "incomplete_local_items": incomplete_local_items,
        "duplicate_request_ids": duplicate_read_ids,
        "missing_output_proofs": missing_proofs,
        "invalid_output_proofs": invalid_proofs,
        "evidence_scope": (
            "complete codex exec JSONL event stream plus read-proxy hashes; post-hoc rejection, "
            "not real-time prevention and not proof of attention or comprehension"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--proxy-log", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(
            args.events.resolve(strict=True),
            args.proxy_log.resolve(strict=True),
            args.policy.resolve(strict=True),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"cli-event-validator: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    sys.stdout.write(encoded)
    return 0 if result["apparatus_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
