#!/usr/bin/env python3
"""Validate cross-linked proxy and PostToolUse evidence for content reads."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _common import read_jsonl


def validate(proxy_log: Path, hook_log: Path) -> dict[str, Any]:
    proxy_events = read_jsonl(proxy_log)
    hook_events = read_jsonl(hook_log)
    reads = [event for event in proxy_events if event.get("operation") == "read"]
    read_ids = [str(event.get("request_id")) for event in reads]
    duplicate_ids = sorted(key for key, count in Counter(read_ids).items() if count != 1)

    proofs: dict[str, list[dict[str, Any]]] = {}
    denied_attempts = 0
    unexpected_allows: list[str] = []
    for event in hook_events:
        if event.get("hook_event_name") == "PreToolUse":
            if event.get("decision") == "deny":
                denied_attempts += 1
            if event.get("decision") == "allow" and event.get("command_kind") not in {
                "proxy",
                "postwrite",
                "write",
                "non-content",
            }:
                unexpected_allows.append(str(event.get("tool_use_id")))
        for proof in event.get("content_proofs", []):
            proofs.setdefault(str(proof.get("request_id")), []).append(proof)

    missing_proofs: list[str] = []
    invalid_proofs: list[str] = []
    for event in reads:
        request_id = str(event.get("request_id"))
        matching = proofs.get(request_id, [])
        if len(matching) != 1:
            missing_proofs.append(request_id)
            continue
        proof = matching[0]
        if not proof.get("proof_valid") or proof.get("canonical_model_response_sha256") != event.get(
            "returned_sha256"
        ):
            invalid_proofs.append(request_id)

    valid = not (duplicate_ids or missing_proofs or invalid_proofs or unexpected_allows)
    return {
        "schema_version": 1,
        "apparatus_valid": valid,
        "content_reads_proved": len(reads) - len(missing_proofs) - len(invalid_proofs),
        "content_reads_total": len(reads),
        "returned_bytes_total": sum(int(event.get("returned_bytes", 0)) for event in reads),
        "denied_bypass_attempts": denied_attempts,
        "duplicate_request_ids": duplicate_ids,
        "missing_post_tool_proofs": missing_proofs,
        "invalid_post_tool_proofs": invalid_proofs,
        "unexpected_allowed_tools": unexpected_allows,
        "evidence_scope": "controlled local tool surface; does not prove model attention or comprehension",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy-log", type=Path, required=True)
    parser.add_argument("--hook-log", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.proxy_log, args.hook_log)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"access-audit-validator: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    sys.stdout.write(encoded)
    return 0 if result["apparatus_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
