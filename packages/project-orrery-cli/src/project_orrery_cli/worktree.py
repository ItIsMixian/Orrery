"""Local worktree creation, guards, status, and Git-private sessions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from project_orrery_core.collaboration import (
    attach_platform_session,
    acknowledge_workstream_finding,
    collect_scope_observation,
    create_worktree,
    inspect_primary_write_guard,
    inspect_worktree_overlap,
    inspect_worktree_status,
    plan_adapter_session_route,
    refresh_workstream_scope,
    transition_workstream_session,
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

    route = actions.add_parser("route", help="plan an Adapter session route without writing")
    _add_common_target(route)
    route.add_argument("--adapter-manifest", required=True, type=Path)
    route.add_argument("--platform-session-id")

    overlap = actions.add_parser("overlap", help="inspect local and supplied peer scope findings")
    _add_common_target(overlap)
    overlap.add_argument("--peer-scope", action="append", type=Path, default=[])
    overlap.add_argument("--no-local-worktrees", action="store_true")

    scope = actions.add_parser("scope", help="inspect or refresh Scope Expansion B")
    scope_actions = scope.add_subparsers(dest="scope_action", required=True)
    scope_inspect = scope_actions.add_parser("inspect", help="collect path scope without writing")
    _add_common_target(scope_inspect)
    scope_refresh = scope_actions.add_parser("refresh", help="refresh Git-private scope metadata")
    _add_common_target(scope_refresh)
    scope_refresh.add_argument("--peer-scope", action="append", type=Path, default=[])
    scope_refresh.add_argument("--no-local-worktrees", action="store_true")
    scope_refresh.add_argument("--confirm-l2", action="store_true")
    scope_refresh.add_argument("--reason")

    finding = actions.add_parser("finding", help="manage derived overlap findings")
    finding_actions = finding.add_subparsers(dest="finding_action", required=True)
    acknowledge = finding_actions.add_parser(
        "acknowledge", help="locally acknowledge one Semantic/Authority/Unknown L2 finding"
    )
    _add_common_target(acknowledge)
    acknowledge.add_argument("finding_id")
    acknowledge.add_argument("--reason", required=True)

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
    create.add_argument("--base-workstream-id")
    create.add_argument("--task-base-oid")

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
    write.add_argument("--base-workstream-id")
    write.add_argument("--task-base-oid")

    transition = session_actions.add_parser("transition", help="apply one legal lifecycle transition")
    _add_common_target(transition)
    transition.add_argument("--reason", required=True)
    transition.add_argument("--phase")
    transition.add_argument("--runtime-condition")
    transition.add_argument("--evidence-freshness")
    transition.add_argument("--closure-reason")

    attach = session_actions.add_parser("attach", help="attach a platform session privately")
    _add_common_target(attach)
    attach.add_argument("--adapter-manifest", required=True, type=Path)
    attach.add_argument("--platform-session-id", required=True)
    attach.add_argument("--rebind", action="store_true")
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


def _load_peer_scopes(paths: list[Path]) -> list[dict[str, object]]:
    scopes: list[dict[str, object]] = []
    for path in paths:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read peer scope {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"peer scope {path} must contain a JSON object")
        candidate = value
        if isinstance(value.get("data"), dict):
            candidate = value["data"]
        if isinstance(candidate.get("scope"), dict):
            candidate = candidate["scope"]
        elif isinstance(candidate.get("current_scope"), dict):
            candidate = candidate["current_scope"]
        scopes.append(candidate)
    return scopes


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

    if arguments.action == "route":
        command = "worktree-session-route"
        try:
            data = plan_adapter_session_route(
                arguments.target,
                adapter_manifest=arguments.adapter_manifest,
                platform_session_id=arguments.platform_session_id,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        exit_code = JsonExitCode.OK if data["allowed"] else JsonExitCode.COMPATIBILITY_FAILED
        if arguments.json_output:
            warnings = [] if data["allowed"] else [issue(data["reason"], data["next_action"])]
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
            print(f"Next action: {data['next_action']}")
        return int(exit_code)

    if arguments.action == "overlap":
        command = "worktree-overlap"
        try:
            data = inspect_worktree_overlap(
                arguments.target,
                peer_scopes=_load_peer_scopes(arguments.peer_scope),
                include_local_worktrees=not arguments.no_local_worktrees,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        blocked = data["review_ready_blocked"]
        exit_code = JsonExitCode.COMPATIBILITY_FAILED if blocked else JsonExitCode.OK
        if arguments.json_output:
            emit(
                response(
                    command,
                    status="warning" if blocked else "ok",
                    exit_code=exit_code,
                    data=data,
                    warnings=(
                        [issue("overlap-findings-block-review-ready", "resolve or acknowledge findings locally")]
                        if blocked
                        else []
                    ),
                )
            )
        else:
            print(f"Findings: {len(data['findings'])}")
            print(f"Unknown peers: {len(data['unavailable_peers'])}")
            print(f"Review Ready blocked: {'yes' if blocked else 'no'}")
        return int(exit_code)

    if arguments.action == "scope" and arguments.scope_action == "inspect":
        command = "worktree-scope-inspect"
        try:
            data = collect_scope_observation(arguments.target)
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Scope revision: {data['scope_revision']}")
            print(f"Paths: {len(data['path_entries'])}")
            print(f"Fingerprint: {data['scope_fingerprint']}")
        return int(JsonExitCode.OK)

    if arguments.action == "scope" and arguments.scope_action == "refresh":
        command = "worktree-scope-refresh"
        try:
            data = refresh_workstream_scope(
                arguments.target,
                peer_scopes=_load_peer_scopes(arguments.peer_scope),
                include_local_worktrees=not arguments.no_local_worktrees,
                confirm_l2=arguments.confirm_l2,
                reason=arguments.reason,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        allowed = data["expansion"]["allowed"]
        exit_code = JsonExitCode.OK if allowed else JsonExitCode.COMPATIBILITY_FAILED
        if arguments.json_output:
            emit(
                response(
                    command,
                    status="ok" if allowed else "warning",
                    exit_code=exit_code,
                    data=data,
                    warnings=(
                        []
                        if allowed
                        else [issue(data["expansion"]["reason"], "scope expansion blocked locally")]
                    ),
                )
            )
        else:
            print(f"Expansion: {data['expansion']['level']}")
            print(f"Allowed: {'yes' if allowed else 'no'}")
            print(f"Scope revision: {data['scope']['scope_revision']}")
        return int(exit_code)

    if arguments.action == "finding":
        command = "worktree-finding-acknowledge"
        try:
            data = acknowledge_workstream_finding(
                arguments.target,
                finding_id=arguments.finding_id,
                reason=arguments.reason,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            finding = data["finding"]
            print(f"Finding: {finding['finding_id']}")
            print(f"Acknowledged: {finding['acknowledgement_progress']}")
        return int(JsonExitCode.OK)

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
                base_workstream_id=arguments.base_workstream_id,
                task_base_oid=arguments.task_base_oid,
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

    if arguments.session_action == "transition":
        command = "worktree-session-transition"
        try:
            data = transition_workstream_session(
                arguments.target,
                reason=arguments.reason,
                lifecycle_phase=arguments.phase,
                runtime_condition=arguments.runtime_condition,
                evidence_freshness=arguments.evidence_freshness,
                closure_reason=arguments.closure_reason,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Lifecycle phase: {data['session']['lifecycle_phase']}")
            print(f"Lifecycle revision: {data['session']['lifecycle_revision']}")
        return int(JsonExitCode.OK)

    if arguments.session_action == "attach":
        command = "worktree-session-attach"
        try:
            data = attach_platform_session(
                arguments.target,
                adapter_manifest=arguments.adapter_manifest,
                platform_session_id=arguments.platform_session_id,
                rebind=arguments.rebind,
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            attached = data["session"]["platform_session"]
            print(f"Platform session: {attached['adapter']}:{attached['session_id']}")
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
            base_workstream_id=arguments.base_workstream_id,
            task_base_oid=arguments.task_base_oid,
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
