"""Human review, eligibility, closure, and cleanup-advice commands."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.review import (
    compute_integration_eligibility,
    inspect_review_package_freshness,
    record_review_decision,
    write_closure_record,
)
from project_orrery_core.workspace_cleanup import (
    CLEANUP_ACTIONS,
    compute_workspace_cleanup_eligibility,
    inventory_workspaces,
    record_cleanup_action_receipt,
)

from .protocol import JsonExitCode, emit, issue, response


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and record local human integration review")
    actions = parser.add_subparsers(dest="command", required=True)
    inventory = actions.add_parser("inventory", help="inventory only bounded local workspace candidates")
    _common(inventory)
    inventory.add_argument("--workspace-root", action="append", default=[])
    inventory.add_argument("--candidate-path", action="append", default=[])
    inventory.add_argument("--classify", action="append", default=[])
    inventory.add_argument("--retain-path", action="append", default=[])
    inventory.add_argument("--recovery-path", action="append", default=[])

    inspect = actions.add_parser("inspect", help="check exact review-package input freshness")
    _common(inspect)
    inspect.add_argument("--package", required=True)

    decide = actions.add_parser("decide", help="record one local human review action")
    _common(decide)
    decide.add_argument("--package", required=True)
    decide.add_argument(
        "--action", required=True, choices=("approve", "request-changes", "hold", "reject")
    )
    decide.add_argument("--actor", required=True)
    decide.add_argument("--actor-kind", default="human", choices=("human", "ai"))
    decide.add_argument("--capability", action="append", default=[])
    decide.add_argument("--reason", required=True)
    decide.add_argument("--evidence", action="append", required=True)

    eligibility = actions.add_parser("eligibility", help="compute human integration eligibility")
    _common(eligibility)
    eligibility.add_argument("--package", required=True)

    closure = actions.add_parser("closure", help="write a Git-private post-integration closure record")
    _common(closure)
    closure.add_argument("--package", required=True)
    closure.add_argument("--final-oid", required=True)
    closure.add_argument("--actor", required=True)
    closure.add_argument("--capability", action="append", default=[])

    cleanup = actions.add_parser("cleanup", help="compute conservative cleanup advice only")
    _common(cleanup)
    cleanup.add_argument("--package")
    cleanup.add_argument("--workspace", type=Path)
    cleanup.add_argument("--workspace-root", action="append", default=[])
    cleanup.add_argument("--classify", action="append", default=[])
    cleanup.add_argument("--retain-path", action="append", default=[])
    cleanup.add_argument("--recovery-path", action="append", default=[])
    cleanup.add_argument("--allow-ignored", action="append", default=[])
    cleanup.add_argument("--authorize-action", action="append", choices=CLEANUP_ACTIONS, default=[])

    receipt = actions.add_parser(
        "cleanup-receipt", help="record a caller-attested external cleanup action without performing it"
    )
    _common(receipt)
    receipt.add_argument("--closure", required=True)
    receipt.add_argument("--action", required=True, choices=CLEANUP_ACTIONS)
    receipt.add_argument("--actor", required=True)
    receipt.add_argument("--authorization-id", required=True)
    receipt.add_argument("--evidence", action="append", required=True)
    receipt.add_argument("--occurred-at", required=True)
    return parser


def _classifications(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        path, separator, classification = value.rpartition("=")
        if not separator or not path.strip() or not classification.strip():
            raise ValueError("workspace classification must use PATH=CLASSIFICATION")
        result[path] = classification
    return result


def _failure(command: str, json_output: bool, exc: ValueError) -> int:
    if json_output:
        emit(
            response(
                command,
                status="error",
                exit_code=JsonExitCode.OPERATION_FAILED,
                errors=[issue("review_operation_failed", str(exc))],
            )
        )
    else:
        print(f"ERROR: {exc}", file=sys.stderr)
    return int(JsonExitCode.OPERATION_FAILED)


def _emit_or_print(
    *,
    command: str,
    data: dict[str, object],
    ok: bool,
    json_output: bool,
    warning: str,
) -> int:
    exit_code = JsonExitCode.OK if ok else JsonExitCode.COMPATIBILITY_FAILED
    if json_output:
        emit(
            response(
                command,
                status="ok" if ok else "warning",
                exit_code=exit_code,
                data=data,
                warnings=[] if ok else [issue("review_gate_blocked", warning)],
            )
        )
    else:
        print(f"Eligible: {'yes' if ok else 'no'}")
        if data.get("reasons"):
            print(f"Reasons: {', '.join(data['reasons'])}")
    return int(exit_code)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "inventory":
        command = "review-workspace-inventory"
        try:
            data = inventory_workspaces(
                arguments.target,
                workspace_roots=arguments.workspace_root,
                candidate_paths=arguments.candidate_path,
                classifications=_classifications(arguments.classify),
                retained_paths=arguments.retain_path,
                recovery_paths=arguments.recovery_path,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Inventory: {data['inventory_id']}")
            print(f"Workspaces: {len(data['entries'])}")
            print("Recursive disk discovery: no")
        return int(JsonExitCode.OK)

    if arguments.command == "inspect":
        command = "review-inspect"
        try:
            data = inspect_review_package_freshness(arguments.target, arguments.package)
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        return _emit_or_print(
            command=command,
            data=data,
            ok=bool(data["fresh"]),
            json_output=arguments.json_output,
            warning="review package inputs drifted",
        )

    if arguments.command == "decide":
        command = "review-decide"
        try:
            data = record_review_decision(
                arguments.target,
                package=arguments.package,
                action=arguments.action,
                actor_id=arguments.actor,
                actor_kind=arguments.actor_kind,
                actor_capabilities=arguments.capability,
                reason=arguments.reason,
                evidence_refs=arguments.evidence,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Decision: {data['decision']['action']}")
            print(f"Record: {data['decision_path']}")
        return int(JsonExitCode.OK)

    if arguments.command == "eligibility":
        command = "review-integration-eligibility"
        try:
            data = compute_integration_eligibility(arguments.target, arguments.package)
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        return _emit_or_print(
            command=command,
            data=data,
            ok=bool(data["eligible"]),
            json_output=arguments.json_output,
            warning="candidate is not eligible for human integration",
        )

    if arguments.command == "closure":
        command = "review-closure-record"
        try:
            data = write_closure_record(
                arguments.target,
                package=arguments.package,
                final_oid=arguments.final_oid,
                actor_id=arguments.actor,
                actor_capabilities=arguments.capability,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Closure: {data['closure_record']['closure_id']}")
            print(f"Record: {data['closure_path']}")
        return int(JsonExitCode.OK)

    if arguments.command == "cleanup-receipt":
        command = "review-cleanup-action-receipt"
        try:
            data = record_cleanup_action_receipt(
                arguments.target,
                closure_id=arguments.closure,
                action=arguments.action,
                actor_id=arguments.actor,
                authorization_id=arguments.authorization_id,
                evidence_refs=arguments.evidence,
                occurred_at=arguments.occurred_at,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Receipt: {data['receipt']['receipt_id']}")
            print("Destructive action performed by Orrery: no")
        return int(JsonExitCode.OK)

    command = "review-cleanup-eligibility"
    try:
        data = compute_workspace_cleanup_eligibility(
            arguments.target,
            workspace_path=arguments.workspace or arguments.target,
            package=arguments.package,
            workspace_roots=arguments.workspace_root,
            classifications=_classifications(arguments.classify),
            retained_paths=arguments.retain_path,
            recovery_paths=arguments.recovery_path,
            ignored_allowlist=arguments.allow_ignored,
            authorized_actions=arguments.authorize_action,
        )
    except ValueError as exc:
        return _failure(command, arguments.json_output, exc)
    return _emit_or_print(
        command=command,
        data=data,
        ok=bool(data["eligible"]),
        json_output=arguments.json_output,
        warning="worktree or branch is not conservatively cleanup-eligible",
    )


if __name__ == "__main__":
    raise SystemExit(main())
