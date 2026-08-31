#!/usr/bin/env python3
"""Minimal subprocess Adapter for the Orrery CLI JSON contract."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
COMMAND_ARGUMENTS: dict[str, dict[str, type | tuple[type, ...]]] = {
    "operating-rules-inspect": {
        "inventory_version": int,
        "inventory_file": str,
    },
    "authority-route-preflight": {
        "target": str,
        "query": str,
        "query_class": str,
        "fact_scope": str,
    },
    "scaffold": {
        "target": str,
        "title": str,
        "dry_run": bool,
        "upgrade_tools": bool,
    },
    "validate": {
        "target": str,
        "build": bool,
        "require_integrated": bool,
    },
    "check-update": {
        "target": str,
        "manifest_file": str,
        "manifest_url": str,
        "offline": bool,
        "cache_hours": (int, float),
    },
    "relations-suggest": {
        "target": str, "proposal_id": str, "relation_type": str,
        "source_workstream_id": str, "target_workstream_id": str,
        "required_for": str, "rationale": str, "consequence": str,
        "proposer_id": str, "platform_session_id": str,
        "evidence_category": str, "evidence_fact_scope": str,
        "evidence_hash": str, "evidence_ref": str,
    },
    "relations-inspect": {"target": str},
    "relations-accept": {
        "target": str, "proposal_id": str, "expected_revision": int,
        "confirmer_id": str, "confirmer_role": str,
    },
    "relations-change-gate": {
        "target": str, "proposal_id": str, "expected_revision": int,
        "required_for": str, "actor_id": str, "reason": str,
    },
    "relations-defer": {
        "target": str, "proposal_id": str, "expected_revision": int,
        "actor_id": str, "reason": str,
    },
    "relations-reject": {
        "target": str, "proposal_id": str, "expected_revision": int,
        "actor_id": str, "reason": str,
    },
}
REQUIRED_ARGUMENTS = {
    "operating-rules-inspect": set(),
    "authority-route-preflight": {"target", "query"},
    "scaffold": {"target"}, "validate": {"target"}, "check-update": set(),
    "relations-suggest": {
        "target", "proposal_id", "relation_type", "source_workstream_id",
        "target_workstream_id", "required_for", "rationale", "consequence", "proposer_id",
    },
    "relations-inspect": {"target"},
    "relations-accept": {"target", "proposal_id", "expected_revision", "confirmer_id", "confirmer_role"},
    "relations-change-gate": {"target", "proposal_id", "expected_revision", "required_for", "actor_id", "reason"},
    "relations-defer": {"target", "proposal_id", "expected_revision", "actor_id", "reason"},
    "relations-reject": {"target", "proposal_id", "expected_revision", "actor_id", "reason"},
}
SANITIZED_ENVIRONMENT = {
    "CODEX_HOME",
    "CODEX_CONFIG",
    "AGENTS_HOME",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
}
RESPONSE_KEYS = {
    "schema_version",
    "command",
    "status",
    "exit_code",
    "versions",
    "data",
    "warnings",
    "errors",
}
COMMAND_DATA_REQUIRED = {
    "operating-rules-inspect": {
        "schema_version", "contract_type", "requested_inventory_version",
        "supported_inventory_versions", "status", "read_only", "unknown",
        "reason", "inventory", "guarantees",
    },
    "authority-route-preflight": {
        "schema_version", "contract_type", "registry", "query", "selection",
        "selected_governing_sources", "excluded_lower_authority_sources",
        "claim_dimensions", "negative_evidence", "novelty_absence_gate",
        "guarantees", "receipt_hash",
    },
    "scaffold": {
        "target",
        "dry_run",
        "upgrade_tools",
        "changed",
        "predicted_changes",
        "authority_status",
        "toolchain_status",
        "actions",
        "preserved_authored_paths",
        "managed_tool_conflicts",
    },
    "validate": {"target", "valid", "integrated", "build_requested", "build_completed"},
    "check-update": {
        "status",
        "update_available",
        "migration_required",
        "local_skill_version",
        "latest_version",
        "target_toolchain_version",
        "target_document_schema",
        "target_manifest_format",
        "source",
        "warning",
        "release_url",
        "skill_url",
        "reasons",
    },
    "relations-suggest": {"event", "writes_performed", "effective_relation_created"},
    "relations-inspect": {"capture", "graph_status", "pending_recovery_transaction_ids"},
    "relations-accept": set(),
    "relations-change-gate": set(),
    "relations-defer": set(),
    "relations-reject": set(),
}


class RequestError(ValueError):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invoke the Orrery CLI through JSON only.")
    parser.add_argument("--request", type=Path, help="JSON request file; stdin is used when omitted")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter containing project_orrery_cli")
    parser.add_argument("--python-path", action="append", default=[], help="Explicit source root for checkout tests")
    parser.add_argument("--timeout", type=float, default=30.0, help="Subprocess timeout in seconds")
    return parser.parse_args(argv)


def _issue(code: str, message: str, **details: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code, "message": message}
    if details:
        result["details"] = details
    return result


def _adapter_error(command: str, exit_code: int, code: str, message: str, **details: Any) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "status": "error",
        "exit_code": exit_code,
        "versions": {"core": "unknown", "core_api": 0, "cli": "unknown"},
        "data": {},
        "warnings": [],
        "errors": [_issue(code, message, **details)],
    }


def _emit(payload: Mapping[str, Any]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True))


def load_request(path: Path | None) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8") if path is not None else sys.stdin.read()
        payload = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise RequestError(f"request is not readable JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RequestError("request root must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RequestError(f"unsupported request schema_version: {payload.get('schema_version')!r}")
    unknown_root = set(payload) - {"schema_version", "command", "arguments"}
    if unknown_root:
        raise RequestError("request has unknown fields: " + ", ".join(sorted(unknown_root)))
    command = payload.get("command")
    if command not in COMMAND_ARGUMENTS:
        raise RequestError(f"unsupported command: {command!r}")
    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        raise RequestError("arguments must be a JSON object")
    unknown_arguments = set(arguments) - set(COMMAND_ARGUMENTS[command])
    if unknown_arguments:
        raise RequestError("arguments have unknown fields: " + ", ".join(sorted(unknown_arguments)))
    missing = REQUIRED_ARGUMENTS[command] - set(arguments)
    if missing:
        raise RequestError("arguments are missing required fields: " + ", ".join(sorted(missing)))
    for name, value in arguments.items():
        expected = COMMAND_ARGUMENTS[command][name]
        if not isinstance(value, expected) or isinstance(value, bool) and expected != bool:
            raise RequestError(f"argument {name!r} has the wrong JSON type")
        if isinstance(value, str) and not value:
            raise RequestError(f"argument {name!r} must not be empty")
        if name == "cache_hours" and value < 0:
            raise RequestError("argument 'cache_hours' must be non-negative")
    if command.startswith("relations-"):
        if "expected_revision" in arguments and arguments["expected_revision"] < 1:
            raise RequestError("expected_revision must be positive")
        if arguments.get("required_for") not in {None, "implementation", "validation", "integration", "release"}:
            raise RequestError("required_for is not a supported dependency gate")
        if command == "relations-suggest" and arguments.get("relation_type") != "depends_on":
            raise RequestError("Harness JSON v1 only suggests semantic depends_on proposals")
        evidence_fields = {"evidence_category", "evidence_fact_scope", "evidence_hash", "evidence_ref"}
        supplied = evidence_fields.intersection(arguments)
        if supplied and supplied != evidence_fields:
            raise RequestError("relation evidence requires category, fact scope, hash, and ref together")
    return payload


def cli_arguments(request: Mapping[str, Any]) -> list[str]:
    command = str(request["command"])
    values = request["arguments"]
    if command == "operating-rules-inspect":
        arguments = ["operating-rules", "inspect"]
    elif command == "authority-route-preflight":
        arguments = ["operating-rules", "route"]
    elif command.startswith("relations-"):
        arguments = ["relations", command.removeprefix("relations-")]
    else:
        arguments = [command]
    flag_order = {
        "operating-rules-inspect": ("inventory_version", "inventory_file"),
        "authority-route-preflight": ("target", "query", "query_class", "fact_scope"),
        "scaffold": ("target", "title", "upgrade_tools", "dry_run"),
        "validate": ("target", "build", "require_integrated"),
        "check-update": ("target", "manifest_url", "manifest_file", "cache_hours", "offline"),
        "relations-suggest": (
            "target", "proposal_id", "relation_type", "source_workstream_id",
            "target_workstream_id", "required_for", "rationale", "consequence",
            "proposer_id", "platform_session_id",
        ),
        "relations-inspect": ("target",),
        "relations-accept": ("target", "proposal_id", "expected_revision", "confirmer_id", "confirmer_role"),
        "relations-change-gate": ("target", "proposal_id", "expected_revision", "required_for", "actor_id", "reason"),
        "relations-defer": ("target", "proposal_id", "expected_revision", "actor_id", "reason"),
        "relations-reject": ("target", "proposal_id", "expected_revision", "actor_id", "reason"),
    }
    for name in flag_order[command]:
        if name not in values:
            continue
        value = values[name]
        cli_name = {
            "relation_type": "type", "source_workstream_id": "source",
            "target_workstream_id": "target-workstream",
        }.get(name, name.replace("_", "-"))
        flag = "--" + cli_name
        if isinstance(value, bool):
            if value:
                arguments.append(flag)
        else:
            arguments.extend((flag, str(value)))
    if command == "relations-suggest":
        arguments.extend(("--proposer-kind", "harness"))
        evidence_fields = ("evidence_category", "evidence_fact_scope", "evidence_hash", "evidence_ref")
        if any(field in values for field in evidence_fields):
            if not all(field in values for field in evidence_fields):
                raise RequestError("relation evidence requires category, fact scope, hash, and ref together")
            arguments.extend(("--evidence", ",".join(str(values[field]) for field in evidence_fields)))
    if command in {"relations-accept", "relations-change-gate", "relations-defer", "relations-reject"}:
        arguments.extend(("--caller-kind", "harness", "--caller-context", "remote"))
    arguments.append("--json")
    return arguments


def child_environment(python_paths: list[str]) -> dict[str, str]:
    environment = dict(os.environ)
    for name in SANITIZED_ENVIRONMENT:
        environment.pop(name, None)
    environment.pop("PYTHONPATH", None)
    if python_paths:
        environment["PYTHONPATH"] = os.pathsep.join(str(Path(path).resolve()) for path in python_paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def validate_response(payload: Any, command: str, returncode: int) -> str | None:
    if not isinstance(payload, dict):
        return "CLI response root is not a JSON object"
    if set(payload) != RESPONSE_KEYS:
        return "CLI response fields do not match response schema v1"
    if payload.get("schema_version") != SCHEMA_VERSION:
        return "CLI response schema_version does not match request"
    expected_command = "workstream-relation-" + command.removeprefix("relations-") if command.startswith("relations-") else command
    if payload.get("command") != expected_command:
        return "CLI response command does not match request"
    if payload.get("status") not in {"ok", "warning", "error"}:
        return "CLI response has an invalid status"
    if payload.get("exit_code") != returncode:
        return "CLI response exit_code does not match process return code"
    versions = payload.get("versions")
    if not isinstance(versions, dict) or set(versions) != {"core", "core_api", "cli"}:
        return "CLI response versions do not match response schema v1"
    data = payload.get("data")
    if not isinstance(data, dict):
        return "CLI response data is not an object"
    if payload.get("status") != "error" and not COMMAND_DATA_REQUIRED[command].issubset(data):
        return "CLI response data are missing required command fields"
    for field in ("warnings", "errors"):
        values = payload.get(field)
        if not isinstance(values, list) or any(
            not isinstance(item, dict) or not {"code", "message"}.issubset(item) for item in values
        ):
            return f"CLI response {field} do not match response schema v1"
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    command = "harness"
    try:
        request = load_request(args.request)
        command = str(request["command"])
    except RequestError as exc:
        _emit(_adapter_error(command, 2, "invalid_request", str(exc)))
        return 2

    try:
        command_arguments = cli_arguments(request)
    except RequestError as exc:
        _emit(_adapter_error(command, 2, "invalid_request", str(exc)))
        return 2
    invocation = [args.python, "-X", "utf8", "-m", "project_orrery_cli", *command_arguments]
    try:
        completed = subprocess.run(
            invocation,
            env=child_environment(args.python_path),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(0.01, args.timeout),
            check=False,
        )
    except subprocess.TimeoutExpired:
        _emit(_adapter_error(command, 7, "cli_timeout", "Project Orrery CLI timed out"))
        return 7
    except OSError:
        _emit(_adapter_error(command, 3, "cli_start_failed", "Project Orrery CLI could not be started"))
        return 3

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        _emit(
            _adapter_error(
                command,
                3,
                "cli_protocol_error",
                "Project Orrery CLI did not emit a valid JSON response",
                process_exit_code=completed.returncode,
            )
        )
        return 3
    protocol_error = validate_response(payload, command, completed.returncode)
    if protocol_error:
        _emit(_adapter_error(command, 3, "cli_protocol_error", protocol_error))
        return 3
    _emit(payload)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
