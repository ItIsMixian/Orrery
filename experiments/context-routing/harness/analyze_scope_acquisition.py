#!/usr/bin/env python3
"""Derive passive pre-write Scope Acquisition metrics from Codex app-server events."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from _common import atomic_write_json, load_json, read_jsonl
from hook_audit import _extract_content_proofs


USAGE_FIELDS = {
    "inputTokens": "input_tokens",
    "cachedInputTokens": "cached_input_tokens",
    "cacheWriteInputTokens": "cache_write_input_tokens",
    "outputTokens": "output_tokens",
    "reasoningOutputTokens": "reasoning_output_tokens",
    "totalTokens": "total_tokens",
}


def _usage(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    normalized: dict[str, int] = {}
    for source, target in USAGE_FIELDS.items():
        item = value.get(source, 0 if source == "cacheWriteInputTokens" else None)
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            return None
        normalized[target] = item
    return normalized


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


def _is_monotonic(previous: dict[str, int], current: dict[str, int]) -> bool:
    return all(current[key] >= previous[key] for key in USAGE_FIELDS.values())


def _proofs_before(events: list[dict[str, Any]], boundary_index: int) -> list[dict[str, Any]]:
    proofs: list[dict[str, Any]] = []
    for event in events[:boundary_index]:
        if event.get("method") != "item/completed":
            continue
        params = event.get("params")
        item = params.get("item") if isinstance(params, dict) else None
        if not isinstance(item, dict) or item.get("type") != "commandExecution":
            continue
        proofs.extend(_extract_content_proofs(item.get("aggregatedOutput")))
    return proofs


def analyze(
    events: list[dict[str, Any]],
    proxy_events: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []
    legacy_exec = any(event.get("type") == "turn.completed" for event in events)
    app_server = any(isinstance(event.get("method"), str) for event in events)
    if legacy_exec and not app_server:
        reasons.append("legacy_codex_exec_has_only_turn_aggregate_usage")

    repository_value = policy.get("repository_root")
    repository_root = (
        Path(repository_value).resolve()
        if isinstance(repository_value, str) and repository_value
        else None
    )
    expected_paths = {
        str(path).replace("\\", "/") for path in policy.get("expected_write_paths", [])
    }

    boundary_index: int | None = None
    boundary_params: dict[str, Any] | None = None
    boundary_item: dict[str, Any] | None = None
    first_write_paths: list[str] = []
    for index, event in enumerate(events):
        if event.get("method") != "item/started":
            continue
        params = event.get("params")
        item = params.get("item") if isinstance(params, dict) else None
        if isinstance(item, dict) and item.get("type") == "fileChange":
            boundary_index = index
            boundary_params = params
            boundary_item = item
            first_write_paths = _file_change_paths(item, repository_root)
            break

    if boundary_index is None:
        reasons.append("missing_item_started_file_change_scope_boundary")
    elif not first_write_paths:
        reasons.append("first_file_change_has_no_reported_paths")
    elif not expected_paths or any(path not in expected_paths for path in first_write_paths):
        reasons.append("first_file_change_is_outside_expected_product_paths")

    thread_id = str(boundary_params.get("threadId", "")) if boundary_params else ""
    turn_id = str(boundary_params.get("turnId", "")) if boundary_params else ""
    if boundary_index is not None and (not thread_id or not turn_id):
        reasons.append("scope_boundary_missing_thread_or_turn_id")

    usage_updates: list[dict[str, Any]] = []
    previous: dict[str, int] | None = None
    for index, event in enumerate(events):
        if event.get("method") != "thread/tokenUsage/updated":
            continue
        params = event.get("params")
        if not isinstance(params, dict):
            reasons.append("invalid_token_usage_notification")
            continue
        usage_container = params.get("tokenUsage")
        total = _usage(usage_container.get("total")) if isinstance(usage_container, dict) else None
        if total is None:
            reasons.append("invalid_token_usage_total")
            continue
        update = {
            "event_index": index,
            "thread_id": str(params.get("threadId", "")),
            "turn_id": str(params.get("turnId", "")),
            "total": total,
        }
        if thread_id and turn_id and update["thread_id"] == thread_id and update["turn_id"] == turn_id:
            if previous is not None and not _is_monotonic(previous, total):
                reasons.append("non_monotonic_cumulative_token_usage")
            previous = total
            usage_updates.append(update)

    before = [
        update
        for update in usage_updates
        if boundary_index is not None and update["event_index"] < boundary_index
    ]
    prewrite_usage = before[-1]["total"] if before else None
    final_usage = usage_updates[-1]["total"] if usage_updates else None
    if boundary_index is not None and prewrite_usage is None:
        reasons.append("missing_cumulative_usage_before_scope_boundary")
    if not bool(policy.get("scope_usage_ordering_verified")):
        reasons.append("app_server_usage_file_change_ordering_not_verified")

    proxy_reads = [event for event in proxy_events if event.get("operation") == "read"]
    proxy_by_id: dict[str, list[dict[str, Any]]] = {}
    for event in proxy_reads:
        proxy_by_id.setdefault(str(event.get("request_id", "")), []).append(event)
    duplicate_proxy_ids = sorted(key for key, values in proxy_by_id.items() if not key or len(values) != 1)
    if duplicate_proxy_ids:
        reasons.append("duplicate_or_missing_proxy_request_ids")

    proofs = _proofs_before(events, boundary_index or 0)
    proved_reads: list[dict[str, Any]] = []
    invalid_proofs: list[str] = []
    seen_proof_ids: set[str] = set()
    for proof in proofs:
        request_id = str(proof.get("request_id", ""))
        matching = proxy_by_id.get(request_id, [])
        if request_id in seen_proof_ids or len(matching) != 1:
            invalid_proofs.append(request_id or "<missing-request-id>")
            continue
        seen_proof_ids.add(request_id)
        proxy = matching[0]
        if (
            not proof.get("proof_valid")
            or proof.get("claimed_returned_sha256") != proxy.get("returned_sha256")
        ):
            invalid_proofs.append(request_id)
            continue
        proved_reads.append(proxy)
    if invalid_proofs:
        reasons.append("invalid_prewrite_proxy_proofs")

    minimum_reads = int(policy.get("minimum_prewrite_content_reads", 1))
    if boundary_index is not None and len(proved_reads) < minimum_reads:
        reasons.append("insufficient_proved_prewrite_content_reads")

    unique_slices: dict[tuple[Any, ...], dict[str, Any]] = {}
    for read in proved_reads:
        key = (
            read.get("path"),
            read.get("start_line"),
            read.get("end_line"),
            read.get("returned_sha256"),
        )
        unique_slices.setdefault(key, read)

    unavailable_reasons = sorted(set(reasons))
    valid = not unavailable_reasons
    non_cached = None
    if prewrite_usage is not None:
        non_cached = max(
            0,
            prewrite_usage["input_tokens"] - prewrite_usage["cached_input_tokens"],
        )
    return {
        "schema_version": 1,
        "metric": "input-to-scope-lock",
        "measurement_valid": valid,
        "precision": "exact" if valid else "unavailable",
        "unavailable_reasons": unavailable_reasons,
        "event_count": len(events),
        "scope_lock": {
            "boundary": "item/started:fileChange" if boundary_index is not None else None,
            "event_index": boundary_index,
            "thread_id": thread_id or None,
            "turn_id": turn_id or None,
            "item_id": boundary_item.get("id") if boundary_item else None,
            "paths": first_write_paths,
        },
        "prewrite_usage": prewrite_usage,
        "prewrite_non_cached_input_tokens": non_cached,
        "final_usage": final_usage,
        "usage_updates": {
            "before_scope_lock": len(before),
            "same_turn_total": len(usage_updates),
        },
        "prewrite_evidence": {
            "content_reads_proved": len(proved_reads),
            "unique_content_paths": len({str(read.get("path")) for read in proved_reads}),
            "returned_bytes": sum(int(read.get("returned_bytes", 0)) for read in proved_reads),
            "unique_slice_bytes": sum(int(read.get("returned_bytes", 0)) for read in unique_slices.values()),
            "paths": sorted({str(read.get("path")) for read in proved_reads}),
            "invalid_proof_request_ids": sorted(set(invalid_proofs)),
        },
        "evidence_scope": (
            (
                "passive app-server cumulative usage immediately before the first started product fileChange, "
                "plus independently hashed read-proxy output completed before that boundary; this proves event "
                "ordering and returned bytes, not model attention, understanding, or subjective scope confidence"
            )
            if minimum_reads > 0
            else (
                "ordering-only compatibility probe using passive app-server cumulative usage immediately before "
                "the first started product fileChange; no read-proxy proof was required, so this establishes "
                "event ordering but not independently proved content delivery, model attention, understanding, "
                "or subjective scope confidence"
            )
        ),
    }


def _notification(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"method": method, "params": params}


def _total(value: int) -> dict[str, int]:
    return {
        "inputTokens": value,
        "cachedInputTokens": value // 2,
        "cacheWriteInputTokens": 0,
        "outputTokens": value // 10,
        "reasoningOutputTokens": value // 20,
        "totalTokens": value + value // 10,
    }


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="orrery-scope-analyzer-") as temporary:
        root = Path(temporary)
        repository = root / "repository"
        repository.mkdir()
        content = "alpha\n"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        request_id = "read-1"
        proof = (
            "ORRERY_READ_BEGIN "
            + json.dumps(
                {
                    "request_id": request_id,
                    "path": "src/a.py",
                    "returned_sha256": digest,
                },
                separators=(",", ":"),
            )
            + "\n"
            + content
            + f"\nORRERY_READ_END {request_id}\n"
        )
        thread_id = "thread-1"
        turn_id = "turn-1"
        events = [
            _notification(
                "thread/tokenUsage/updated",
                {"threadId": thread_id, "turnId": turn_id, "tokenUsage": {"last": _total(100), "total": _total(100)}},
            ),
            _notification(
                "item/completed",
                {
                    "threadId": thread_id,
                    "turnId": turn_id,
                    "item": {"id": "command-1", "type": "commandExecution", "aggregatedOutput": proof},
                },
            ),
            _notification(
                "thread/tokenUsage/updated",
                {"threadId": thread_id, "turnId": turn_id, "tokenUsage": {"last": _total(100), "total": _total(200)}},
            ),
            _notification(
                "item/started",
                {
                    "threadId": thread_id,
                    "turnId": turn_id,
                    "item": {
                        "id": "write-1",
                        "type": "fileChange",
                        "changes": [{"path": "src/a.py", "diff": "", "kind": {"type": "update"}}],
                    },
                },
            ),
            _notification(
                "thread/tokenUsage/updated",
                {"threadId": thread_id, "turnId": turn_id, "tokenUsage": {"last": _total(200), "total": _total(400)}},
            ),
        ]
        proxy_events = [
            {
                "operation": "read",
                "request_id": request_id,
                "path": "src/a.py",
                "start_line": 1,
                "end_line": 1,
                "returned_sha256": digest,
                "returned_bytes": len(content.encode("utf-8")),
            }
        ]
        policy = {
            "repository_root": str(repository),
            "expected_write_paths": ["src/a.py"],
            "minimum_prewrite_content_reads": 1,
            "scope_usage_ordering_verified": True,
        }
        valid = analyze(events, proxy_events, policy)
        if not valid["measurement_valid"]:
            raise RuntimeError("valid synthetic scope stream was rejected: " + repr(valid["unavailable_reasons"]))
        if valid["prewrite_usage"]["input_tokens"] != 200:
            raise RuntimeError("scope boundary did not select the latest pre-write cumulative usage")
        if valid["prewrite_evidence"]["content_reads_proved"] != 1:
            raise RuntimeError("pre-write proxy proof was not counted")

        non_monotonic = list(events)
        non_monotonic[2] = _notification(
            "thread/tokenUsage/updated",
            {"threadId": thread_id, "turnId": turn_id, "tokenUsage": {"last": _total(50), "total": _total(50)}},
        )
        if analyze(non_monotonic, proxy_events, policy)["measurement_valid"]:
            raise RuntimeError("non-monotonic usage was accepted")

        wrong_path = json.loads(json.dumps(events))
        wrong_path[3]["params"]["item"]["changes"][0]["path"] = "src/outside.py"
        if analyze(wrong_path, proxy_events, policy)["measurement_valid"]:
            raise RuntimeError("out-of-scope first write was accepted")

        legacy = [
            {"type": "turn.started"},
            {"type": "item.started", "item": {"type": "file_change", "id": "write-1"}},
            {"type": "turn.completed", "usage": {"input_tokens": 999}},
        ]
        legacy_result = analyze(legacy, [], policy)
        if "legacy_codex_exec_has_only_turn_aggregate_usage" not in legacy_result["unavailable_reasons"]:
            raise RuntimeError("legacy aggregate-only stream was not identified")
    return {"self_test": "passed", "cases": 4}


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
            result = analyze(
                read_jsonl(args.events.resolve(strict=True)),
                read_jsonl(args.proxy_log.resolve(strict=True)),
                load_json(args.policy.resolve(strict=True), {}),
            )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"scope-acquisition-analyzer: {exc}", file=__import__("sys").stderr)
        return 2
    if args.output:
        atomic_write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if (args.self_test or result["measurement_valid"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
