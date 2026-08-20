#!/usr/bin/env python3
"""Audit a complete Codex app-server turn against the controlled Pilot policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from _common import atomic_write_json, load_json, read_jsonl
from hook_audit import (
    _extract_content_proofs,
    _is_proxy_command,
    _normalize_command,
    _unwrap_powershell_command,
)


INFORMATIONAL_ITEM_TYPES = {
    "agentMessage",
    "error",
    "plan",
    "reasoning",
    "userMessage",
}


def _reported_path(value: str, repository_root: Path | None) -> str:
    normalized = value.replace("\\", "/")
    candidate = Path(value)
    if repository_root is None or not candidate.is_absolute():
        return normalized
    try:
        return candidate.resolve().relative_to(repository_root).as_posix()
    except (OSError, ValueError):
        return normalized


def _file_change_paths(item: dict[str, Any], repository_root: Path | None) -> list[str]:
    paths: list[str] = []
    changes = item.get("changes")
    if isinstance(changes, list):
        for change in changes:
            if isinstance(change, dict) and isinstance(change.get("path"), str):
                paths.append(_reported_path(change["path"], repository_root))
    return sorted(set(paths))


def validate(
    events: list[dict[str, Any]],
    proxy_events: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    proxy_script = str(policy.get("proxy_script", ".benchmark/context_read_proxy.py"))
    repository_value = policy.get("repository_root")
    repository_root = (
        Path(repository_value).resolve()
        if isinstance(repository_value, str) and repository_value
        else None
    )
    expected_write_paths = {
        str(path).replace("\\", "/") for path in policy.get("expected_write_paths", [])
    }
    postwrite_commands = {
        _normalize_command(str(command)) for command in policy.get("postwrite_commands", [])
    }
    informational = INFORMATIONAL_ITEM_TYPES | {
        str(item) for item in policy.get("allowed_informational_item_types", [])
    }

    started_local: dict[str, str] = {}
    completed_local: set[str] = set()
    first_write_index: int | None = None
    command_count = 0
    unapproved_commands: list[str] = []
    prewrite_validation_commands: list[str] = []
    failed_proxy_commands: list[str] = []
    failed_postwrite_commands: list[str] = []
    unexpected_item_types: list[str] = []
    unexpected_write_paths: list[str] = []
    proofs: list[dict[str, Any]] = []
    turn_ids: set[tuple[str, str]] = set()
    completed_turns: list[tuple[str, str]] = []

    for index, event in enumerate(events):
        method = str(event.get("method", ""))
        params = event.get("params")
        item = params.get("item") if isinstance(params, dict) else None
        if method == "turn/completed" and isinstance(params, dict):
            turn = params.get("turn")
            if isinstance(turn, dict) and turn.get("status") == "completed":
                completed_turns.append((str(params.get("threadId", "")), str(turn.get("id", ""))))
            continue
        if not isinstance(item, dict) or method not in {"item/started", "item/completed"}:
            continue
        item_type = str(item.get("type", ""))
        item_id = str(item.get("id", ""))
        if isinstance(params, dict):
            turn_ids.add((str(params.get("threadId", "")), str(params.get("turnId", ""))))
        if method == "item/started" and item_type in {"commandExecution", "fileChange"}:
            started_local[item_id] = item_type
            if item_type == "fileChange" and first_write_index is None:
                first_write_index = index
            continue
        if method != "item/completed":
            continue
        if item_type == "commandExecution":
            completed_local.add(item_id)
            command_count += 1
            command = str(item.get("command", ""))
            normalized = _normalize_command(_unwrap_powershell_command(command))
            proxy_command = _is_proxy_command(command, proxy_script)
            postwrite_command = normalized in postwrite_commands
            if postwrite_command and (first_write_index is None or index < first_write_index):
                prewrite_validation_commands.append(command)
            if not proxy_command and not postwrite_command:
                unapproved_commands.append(command)
            status_ok = item.get("status") == "completed" and item.get("exitCode") == 0
            if not status_ok:
                if proxy_command:
                    failed_proxy_commands.append(item_id)
                elif postwrite_command:
                    failed_postwrite_commands.append(item_id)
            proofs.extend(_extract_content_proofs(item.get("aggregatedOutput")))
        elif item_type == "fileChange":
            completed_local.add(item_id)
            paths = _file_change_paths(item, repository_root)
            if not paths:
                unexpected_write_paths.append("<unreported-path>")
            unexpected_write_paths.extend(path for path in paths if path not in expected_write_paths)
            if item.get("status") != "completed":
                unexpected_write_paths.append("<incomplete-file-change>")
        elif item_type not in informational:
            unexpected_item_types.append(item_type or "<missing-type>")

    incomplete_local_items = sorted(set(started_local) - completed_local)
    proxy_reads = [event for event in proxy_events if event.get("operation") == "read"]
    proxy_ids = [str(event.get("request_id", "")) for event in proxy_reads]
    duplicate_proxy_ids = sorted(
        request_id for request_id, count in Counter(proxy_ids).items() if not request_id or count != 1
    )
    proof_by_id: dict[str, list[dict[str, Any]]] = {}
    for proof in proofs:
        proof_by_id.setdefault(str(proof.get("request_id", "")), []).append(proof)
    missing_proofs: list[str] = []
    invalid_proofs: list[str] = []
    for read in proxy_reads:
        request_id = str(read.get("request_id", ""))
        matches = proof_by_id.get(request_id, [])
        if len(matches) != 1:
            missing_proofs.append(request_id or "<missing-request-id>")
            continue
        proof = matches[0]
        if (
            not proof.get("proof_valid")
            or proof.get("claimed_returned_sha256") != read.get("returned_sha256")
        ):
            invalid_proofs.append(request_id)

    minimum_reads = int(policy.get("minimum_content_reads", 1))
    valid_turn_ids = {pair for pair in turn_ids if all(pair)}
    completed_turn_ids = {pair for pair in completed_turns if all(pair)}
    turn_alignment_valid = len(valid_turn_ids) == 1 and completed_turn_ids == valid_turn_ids
    failures_present = any(
        (
            unapproved_commands,
            prewrite_validation_commands,
            failed_proxy_commands,
            failed_postwrite_commands,
            unexpected_item_types,
            unexpected_write_paths,
            incomplete_local_items,
            duplicate_proxy_ids,
            missing_proofs,
            invalid_proofs,
        )
    ) or len(proxy_reads) < minimum_reads or first_write_index is None or not turn_alignment_valid
    return {
        "schema_version": 1,
        "apparatus_valid": not failures_present,
        "evidence_mode": "codex-app-server-jsonrpc-posthoc-v1",
        "event_count": len(events),
        "content_reads_total": len(proxy_reads),
        "content_reads_proved": len(proxy_reads) - len(missing_proofs) - len(invalid_proofs),
        "returned_bytes_total": sum(int(event.get("returned_bytes", 0)) for event in proxy_reads),
        "completed_command_count": command_count,
        "minimum_content_reads": minimum_reads,
        "first_write_event_index": first_write_index,
        "turn_alignment_valid": turn_alignment_valid,
        "unapproved_commands": unapproved_commands,
        "prewrite_validation_commands": prewrite_validation_commands,
        "failed_proxy_commands": failed_proxy_commands,
        "failed_postwrite_commands": failed_postwrite_commands,
        "unexpected_item_types": sorted(set(unexpected_item_types)),
        "unexpected_write_paths": sorted(set(unexpected_write_paths)),
        "incomplete_local_items": incomplete_local_items,
        "duplicate_request_ids": duplicate_proxy_ids,
        "missing_output_proofs": missing_proofs,
        "invalid_output_proofs": invalid_proofs,
        "evidence_scope": (
            "complete app-server JSON-RPC event stream plus read-proxy hashes; post-hoc rejection, "
            "not real-time prevention and not proof of attention or comprehension"
        ),
    }


def _proof_output(request_id: str, content: str) -> tuple[str, str]:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    metadata = {
        "request_id": request_id,
        "path": "src/app.py",
        "returned_sha256": digest,
    }
    output = (
        "ORRERY_READ_BEGIN "
        + json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        + "\n"
        + content
        + f"\nORRERY_READ_END {request_id}\n"
    )
    return output, digest


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="orrery-appserver-validator-") as temporary:
        repository = Path(temporary) / "repository"
        repository.mkdir()
        request_id = "read-1"
        output, digest = _proof_output(request_id, "alpha")
        thread_id, turn_id = "thread-1", "turn-1"

        def item(method: str, value: dict[str, Any]) -> dict[str, Any]:
            return {
                "method": method,
                "params": {"threadId": thread_id, "turnId": turn_id, "item": value},
            }

        proxy_command = "python .benchmark/context_read_proxy.py read --path src/app.py --start 1 --end 1"
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
                    "aggregatedOutput": output,
                },
            ),
            item(
                "item/started",
                {
                    "id": "write",
                    "type": "fileChange",
                    "changes": [{"path": str(repository / "src/app.py")}],
                },
            ),
            item(
                "item/completed",
                {
                    "id": "write",
                    "type": "fileChange",
                    "status": "completed",
                    "changes": [{"path": str(repository / "src/app.py")}],
                },
            ),
            item("item/started", {"id": "test", "type": "commandExecution"}),
            item(
                "item/completed",
                {
                    "id": "test",
                    "type": "commandExecution",
                    "command": "python -m unittest -q",
                    "status": "completed",
                    "exitCode": 0,
                    "aggregatedOutput": "OK",
                },
            ),
            {
                "method": "turn/completed",
                "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed"}},
            },
        ]
        proxy_events = [
            {
                "operation": "read",
                "request_id": request_id,
                "returned_sha256": digest,
                "returned_bytes": 5,
            }
        ]
        policy = {
            "repository_root": str(repository),
            "proxy_script": ".benchmark/context_read_proxy.py",
            "postwrite_commands": ["python -m unittest -q"],
            "expected_write_paths": ["src/app.py"],
            "minimum_content_reads": 1,
        }
        valid = validate(events, proxy_events, policy)
        if not valid["apparatus_valid"]:
            raise RuntimeError("valid app-server stream was rejected: " + repr(valid))
        direct = list(events)
        direct.insert(
            2,
            item(
                "item/completed",
                {
                    "id": "direct",
                    "type": "commandExecution",
                    "command": "Get-Content src/app.py",
                    "status": "completed",
                    "exitCode": 0,
                    "aggregatedOutput": "alpha",
                },
            ),
        )
        if validate(direct, proxy_events, policy)["apparatus_valid"]:
            raise RuntimeError("direct content read was accepted")
        early = [events[0], events[1], events[4], events[5], *events[2:4], events[6]]
        if validate(early, proxy_events, policy)["apparatus_valid"]:
            raise RuntimeError("pre-write validation command was accepted")
    return {"self_test": "passed", "cases": 3}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--proxy-log", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            result = self_test()
        else:
            if args.events is None or args.proxy_log is None or args.policy is None:
                parser.error("--events, --proxy-log and --policy are required unless --self-test is used")
            result = validate(
                read_jsonl(args.events.resolve(strict=True)),
                read_jsonl(args.proxy_log.resolve(strict=True)),
                load_json(args.policy.resolve(strict=True), {}),
            )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"app-server-event-validator: {exc}", file=__import__("sys").stderr)
        return 2
    if args.output:
        atomic_write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if (args.self_test or result["apparatus_valid"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
