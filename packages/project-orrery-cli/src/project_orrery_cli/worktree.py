"""Read-only worktree status and explicit Git-private session writes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.collaboration import inspect_worktree_status, write_workstream_session

from .protocol import JsonExitCode, emit, issue, response


def _add_common_target(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect worktrees and manage private Workstream sessions")
    actions = parser.add_subparsers(dest="action", required=True)
    status = actions.add_parser("status", help="inspect current Git and private session status")
    _add_common_target(status)

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
