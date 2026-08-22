"""Local worktree creation, guards, status, and Git-private sessions."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.collaboration import (
    create_worktree,
    inspect_primary_write_guard,
    inspect_worktree_status,
    write_workstream_session,
)

from .protocol import JsonExitCode, emit, issue, response


def _add_common_target(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect worktrees and manage private Workstream sessions")
    actions = parser.add_subparsers(dest="action", required=True)
    status = actions.add_parser("status", help="inspect current Git and private session status")
    _add_common_target(status)

    guard = actions.add_parser("guard", help="check the primary-worktree product-write boundary")
    _add_common_target(guard)

    create = actions.add_parser("create", help="create an isolated linked Workstream worktree")
    _add_common_target(create)
    create.add_argument("workstream_id")
    create.add_argument("--branch", required=True)
    create.add_argument("--path", type=Path)
    create.add_argument("--from", dest="integration_ref")
    create.add_argument("--primary-subsystem-id", required=True)
    create.add_argument("--affected-subsystem-id", action="append", default=[])
    create.add_argument("--expected-write", action="append", default=[])
    create.add_argument("--governing-doc", action="append", default=[])
    create.add_argument("--validation-surface", action="append", default=[])

    session = actions.add_parser("session", help="manage the private Workstream session")
    session_actions = session.add_subparsers(dest="session_action", required=True)
    write = session_actions.add_parser("write", help="write or refresh the private Workstream session")
    _add_common_target(write)
    write.add_argument("--workstream-id", required=True)
    write.add_argument("--primary-subsystem-id", required=True)
    write.add_argument("--affected-subsystem-id", action="append", default=[])
    write.add_argument("--expected-write", action="append", default=[])
    write.add_argument("--governing-doc", action="append", default=[])
    write.add_argument("--validation-surface", action="append", default=[])
    write.add_argument("--scope-revision", type=int, default=1)
    return parser


def _failure(command: str, json_output: bool, exc: ValueError) -> int:
    if json_output:
        emit(
            response(
                command,
                status="error",
                exit_code=JsonExitCode.OPERATION_FAILED,
                errors=[issue("worktree_operation_failed", str(exc))],
            )
        )
    else:
        print(f"ERROR: {exc}", file=sys.stderr)
    return int(JsonExitCode.OPERATION_FAILED)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.action == "status":
        command = "worktree-status"
        try:
            data = inspect_worktree_status(arguments.target)
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            identity = data["identity"]
            session = data["session"]
            print(f"Worktree: {identity['worktree_path']}")
            print(f"Branch: {identity['branch'] or '(detached)'}")
            print(f"HEAD: {identity['head']}")
            print(f"Integration: {identity['integration_ref']}@{identity['integration_oid']}")
            print(f"Ahead/behind: {identity['ahead']}/{identity['behind']}")
            print(f"Fact scope: {identity['fact_scope']}")
            print(f"Dirty: {'yes' if identity['dirty'] else 'no'} ({identity['dirty_entry_count']} entries)")
            print(f"Session: {session['state']} ({session['path']})")
            if session["stale_reasons"]:
                print(f"Session stale reasons: {', '.join(session['stale_reasons'])}")
        return int(JsonExitCode.OK)

    if arguments.action == "guard":
        command = "worktree-primary-write-guard"
        try:
            data = inspect_primary_write_guard(arguments.target)
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        exit_code = JsonExitCode.OK if data["allowed"] else JsonExitCode.COMPATIBILITY_FAILED
        if arguments.json_output:
            warnings = (
                []
                if data["allowed"]
                else [issue(data["reason"], "product write blocked by primary-worktree guard")]
            )
            emit(
                response(
                    command,
                    status="ok" if data["allowed"] else "warning",
                    exit_code=exit_code,
                    data=data,
                    warnings=warnings,
                )
            )
        else:
            print(f"Decision: {data['decision']}")
            print(f"Reason: {data['reason']}")
            print(f"Recovery: {data['recovery']}")
        return int(exit_code)

    if arguments.action == "create":
        command = "worktree-create"
        try:
            data = create_worktree(
                arguments.target,
                workstream_id=arguments.workstream_id,
                branch=arguments.branch,
                path=arguments.path,
                integration_ref=arguments.integration_ref,
                primary_subsystem_id=arguments.primary_subsystem_id,
                affected_subsystem_ids=arguments.affected_subsystem_id,
                expected_writes=arguments.expected_write,
                governing_docs=arguments.governing_doc,
                validation_surfaces=arguments.validation_surface,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Worktree created: {data['worktree_path']}")
            print(f"Branch: {data['branch']}")
            print(
                f"Integration: {data['source']['integration_ref']}@"
                f"{data['source']['integration_oid']}"
            )
            print(f"Session: {data['session_path']}")
        return int(JsonExitCode.OK)

    command = "worktree-session-write"
    try:
        data = write_workstream_session(
            arguments.target,
            workstream_id=arguments.workstream_id,
            primary_subsystem_id=arguments.primary_subsystem_id,
            affected_subsystem_ids=arguments.affected_subsystem_id,
            expected_writes=arguments.expected_write,
            governing_docs=arguments.governing_doc,
            validation_surfaces=arguments.validation_surface,
            scope_revision=arguments.scope_revision,
        )
    except ValueError as exc:
        return _failure(command, arguments.json_output, exc)
    if arguments.json_output:
        emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
    else:
        print(f"Workstream session written: {data['session_path']}")
        print(f"Workstream: {data['session']['workstream_id']}")
        print(f"HEAD: {data['session']['head']}")
    return int(JsonExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
