#!/usr/bin/env python3
"""Codex PreToolUse/PostToolUse hook for the controlled read-proxy experiment."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from _common import (
    append_jsonl,
    atomic_write_json,
    canonical_sha256,
    iter_strings,
    load_json,
    now_iso,
    sha256_bytes,
)


BEGIN_MARKER = "ORRERY_READ_BEGIN "
END_MARKER = "\nORRERY_READ_END "
SHELL_META = set(";&|><`$(){}@\r\n")


def _required_path(name: str) -> Path:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be set by the benchmark Harness")
    return Path(value).resolve()


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def _unwrap_powershell_command(command: str) -> str:
    stripped = command.strip()
    patterns = (
        r'^"[^"]*(?:pwsh|powershell)\.exe"\s+-Command\s+\'([^\']*)\'$',
        r'^(?:pwsh|powershell)(?:\.exe)?\s+-Command\s+\'([^\']*)\'$',
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, stripped, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return stripped


def _is_proxy_command(command: str, proxy_script: str) -> bool:
    candidate = _unwrap_powershell_command(command)
    if any(character in SHELL_META for character in candidate):
        return False
    normalized_script = proxy_script.replace("\\", "[\\\\/]").replace("/", "[\\\\/]")
    pattern = (
        r'^\s*(?:python(?:\.exe)?|py(?:\.exe)?\s+-3)\s+"?'
        + normalized_script
        + r'"?\s+(?:list|read)\b'
    )
    return re.fullmatch(pattern + r".*", candidate, flags=re.IGNORECASE) is not None


def _load_state(path: Path) -> dict[str, Any]:
    return load_json(path, {"schema_version": 1, "phase": "prewrite", "read_ranges": {}})


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _extract_content_proofs(tool_response: Any) -> list[dict[str, Any]]:
    proofs: list[dict[str, Any]] = []
    for candidate in iter_strings(tool_response):
        search_from = 0
        while True:
            begin = candidate.find(BEGIN_MARKER, search_from)
            if begin < 0:
                break
            header_end = candidate.find("\n", begin)
            if header_end < 0:
                break
            try:
                metadata = json.loads(candidate[begin + len(BEGIN_MARKER) : header_end])
            except json.JSONDecodeError:
                search_from = header_end + 1
                continue
            request_id = metadata.get("request_id")
            end_tokens = (
                f"\r\nORRERY_READ_END {request_id}",
                f"{END_MARKER}{request_id}",
            )
            matches = [
                (candidate.find(token, header_end + 1), token)
                for token in end_tokens
            ]
            matches = [(position, token) for position, token in matches if position >= 0]
            if not matches:
                search_from = header_end + 1
                continue
            content_end, end_token = min(matches, key=lambda item: item[0])
            content = candidate[header_end + 1 : content_end]
            actual_hash = sha256_bytes(content.encode("utf-8"))
            canonical_content = content.replace("\r\n", "\n").replace("\r", "\n")
            canonical_hash = sha256_bytes(canonical_content.encode("utf-8"))
            windows_recovered_content = content.replace("\r\r\n", "\r\n")
            windows_recovered_hash = sha256_bytes(windows_recovered_content.encode("utf-8"))
            claimed_hash = metadata.get("returned_sha256")
            candidate_hashes = {
                "raw": actual_hash,
                "canonical-lf": canonical_hash,
                "windows-text-translation-recovered": windows_recovered_hash,
            }
            matched_form = next(
                (name for name, digest in candidate_hashes.items() if digest == claimed_hash),
                None,
            )
            proofs.append(
                {
                    "request_id": request_id,
                    "path": metadata.get("path"),
                    "claimed_returned_sha256": claimed_hash,
                    "model_response_sha256": actual_hash,
                    "canonical_model_response_sha256": canonical_hash,
                    "windows_recovered_model_response_sha256": windows_recovered_hash,
                    "newline_normalization": "CRLF/CR to LF",
                    "matched_response_form": matched_form,
                    "proof_valid": matched_form is not None,
                }
            )
            search_from = content_end + len(end_token)
    return proofs


def handle(payload: dict[str, Any]) -> dict[str, Any]:
    policy_path = _required_path("ORRERY_ACCESS_POLICY")
    state_path = _required_path("ORRERY_ACCESS_STATE")
    audit_path = _required_path("ORRERY_HOOK_AUDIT_LOG")
    policy = load_json(policy_path, {})
    state = _load_state(state_path)
    event_name = str(payload.get("hook_event_name", ""))
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input")
    command = ""
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        command = tool_input["command"]

    event: dict[str, Any] = {
        "schema_version": 1,
        "timestamp": now_iso(),
        "hook_event_name": event_name,
        "tool_name": tool_name,
        "tool_use_id": payload.get("tool_use_id"),
        "phase": state.get("phase", "prewrite"),
        "tool_input_sha256": canonical_sha256(tool_input),
    }
    response: dict[str, Any] = {}

    if event_name == "PreToolUse":
        if tool_name == "Bash":
            proxy_script = str(policy.get("proxy_script", ".benchmark/context_read_proxy.py"))
            normalized = _normalize_command(command)
            if _is_proxy_command(command, proxy_script):
                event.update({"decision": "allow", "command_kind": "proxy", "command": command})
            elif state.get("phase") == "postwrite" and normalized in {
                _normalize_command(item) for item in policy.get("postwrite_commands", [])
            }:
                event.update({"decision": "allow", "command_kind": "postwrite", "command": command})
            else:
                event.update({"decision": "deny", "command_kind": "unapproved", "command": command})
                response = _deny("Use the Harness read proxy or an approved post-write command.")
        elif tool_name == "apply_patch":
            event.update({"decision": "allow", "command_kind": "write"})
            state["phase"] = "postwrite"
            atomic_write_json(state_path, state)
        elif tool_name in set(policy.get("allowed_non_content_tools", ["update_plan"])):
            event.update({"decision": "allow", "command_kind": "non-content"})
        else:
            event.update({"decision": "deny", "command_kind": "unknown-tool"})
            response = _deny(f"Tool {tool_name!r} is outside the controlled benchmark surface.")
    elif event_name == "PostToolUse":
        tool_response = payload.get("tool_response")
        event.update(
            {
                "decision": "observe",
                "tool_response_sha256": canonical_sha256(tool_response),
                "content_proofs": _extract_content_proofs(tool_response),
            }
        )
    else:
        event.update({"decision": "ignore"})

    append_jsonl(audit_path, event)
    return response


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be a JSON object")
        response = handle(payload)
        sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"hook-audit: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
