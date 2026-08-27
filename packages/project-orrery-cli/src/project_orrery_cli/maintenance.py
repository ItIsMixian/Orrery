"""Workspace maintenance CLI: local scan, queue, confirmation, and remove-worktree."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.maintenance import (
    authorize_maintenance_item,
    execute_maintenance_authorization,
    inspect_maintenance_item,
    list_maintenance_queue,
    load_maintenance_policy,
    maintenance_status,
    read_maintenance_receipt,
    run_maintenance_scan,
)

from .protocol import JsonExitCode, emit, issue, response


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only Project Orrery workspace maintenance")
    commands = parser.add_subparsers(dest="command", required=True)
    policy = commands.add_parser("policy")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)
    _common(policy_commands.add_parser("show"))
    scan = commands.add_parser("scan")
    _common(scan)
    scan.add_argument("--reason", choices=("manual", "integration-event", "closure-event", "observatory-catch-up"), default="manual")
    scan.add_argument("--timeout", type=float, default=120.0)
    queue = commands.add_parser("queue")
    _common(queue)
    inspect = commands.add_parser("inspect")
    _common(inspect)
    inspect.add_argument("item_id")
    authorize = commands.add_parser("authorize")
    _common(authorize)
    authorize.add_argument("item_id")
    authorize.add_argument("--action", required=True, choices=("remove-worktree",))
    authorize.add_argument("--actor", required=True)
    execute = commands.add_parser("execute")
    _common(execute)
    execute.add_argument("authorization_id")
    receipt = commands.add_parser("receipt")
    _common(receipt)
    receipt.add_argument("receipt_id")
    schedule = commands.add_parser("schedule")
    schedule_commands = schedule.add_subparsers(dest="schedule_command", required=True)
    _common(schedule_commands.add_parser("status"))
    status = commands.add_parser("status")
    _common(status)
    return parser


def _failure(command: str, json_output: bool, exc: Exception) -> int:
    if json_output:
        emit(response(command, status="error", exit_code=JsonExitCode.OPERATION_FAILED, errors=[issue("maintenance_operation_failed", str(exc))]))
    else:
        print(f"ERROR: {exc}", file=sys.stderr)
    return int(JsonExitCode.OPERATION_FAILED)


def _success(command: str, data: dict[str, object], json_output: bool) -> int:
    if json_output:
        emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
    else:
        if command == "maintenance-scan":
            print(f"Scan: {data['scan']['status']} · suggestions {len(data.get('queue', []))}")
            print("Destructive action performed: no")
        elif command == "maintenance-queue":
            print(f"Suggestions: {len(data['items'])}")
        elif command == "maintenance-authorize":
            print(f"Authorization: {data['authorization']['authorization_id']}")
            print("Execution performed: no")
        elif command == "maintenance-execute":
            print(f"Receipt: {data['receipt']['receipt_id']} · {data['receipt']['outcome']}")
            print("Branch deleted: no")
        else:
            print(data)
    return int(JsonExitCode.OK)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    command = f"maintenance-{arguments.command}"
    try:
        if arguments.command == "policy":
            data = {"policy": load_maintenance_policy(arguments.target), "writes_performed": False, "network_performed": False}
        elif arguments.command == "scan":
            data = run_maintenance_scan(arguments.target, reason=arguments.reason, timeout_seconds=arguments.timeout)
            if data["scan"]["status"] in {"failed", "timed-out"}:
                raise ValueError(f"maintenance scan {data['scan']['status']}: {data.get('error', {}).get('type', 'Unknown')}")
        elif arguments.command == "queue":
            data = list_maintenance_queue(arguments.target)
        elif arguments.command == "inspect":
            data = {"item": inspect_maintenance_item(arguments.target, arguments.item_id), "writes_performed": False, "network_performed": False}
        elif arguments.command == "authorize":
            data = authorize_maintenance_item(arguments.target, item_id=arguments.item_id, action=arguments.action, actor_id=arguments.actor)
        elif arguments.command == "execute":
            data = execute_maintenance_authorization(arguments.target, authorization_id=arguments.authorization_id)
        elif arguments.command == "receipt":
            data = {"receipt": read_maintenance_receipt(arguments.target, arguments.receipt_id), "writes_performed": False, "network_performed": False}
        elif arguments.command == "schedule":
            status = maintenance_status(arguments.target)["scheduler"]
            data = {"scheduler": status, "writes_performed": False, "network_performed": False}
        else:
            data = maintenance_status(arguments.target)
    except (ValueError, OSError) as exc:
        return _failure(command, arguments.json_output, exc)
    return _success(command, data, arguments.json_output)


if __name__ == "__main__":
    raise SystemExit(main())
