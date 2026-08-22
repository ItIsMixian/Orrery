"""CLI orchestration for the opt-in Team Mode foundation."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from project_orrery_core.team import (
    capture_metadata_envelope,
    change_member_capability,
    configure_heartbeat,
    confirm_join,
    create_invite,
    decide_request,
    disable_team,
    enable_team,
    fetch_projection,
    fetch_requests,
    finalize_join,
    inspect_outbox,
    load_team_config,
    queue_sync_event,
    request_host_switch,
    request_join,
    send_request,
    set_sharing,
    start_coordinator_server,
    switch_active_host,
    sync_now,
)

from .protocol import JsonExitCode, emit, issue, response


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Orrery opt-in Team Mode foundation")
    commands = parser.add_subparsers(dest="action", required=True)
    status = commands.add_parser("status")
    _common(status)

    enable = commands.add_parser("enable")
    _common(enable)
    enable.add_argument("--member-id", required=True)
    enable.add_argument("--device-id", required=True)
    enable.add_argument("--host-id", required=True)
    enable.add_argument("--allow-lan-bind", action="store_true")
    enable.add_argument("--ttl-seconds", type=int, default=300)
    enable.add_argument("--debounce-milliseconds", type=int, default=750)

    disable = commands.add_parser("disable")
    _common(disable)

    heartbeat = commands.add_parser("heartbeat")
    _common(heartbeat)
    heartbeat.add_argument("mode", choices=("on", "off"))
    heartbeat.add_argument("--interval-seconds", type=int, default=60)

    sharing = commands.add_parser("sharing")
    _common(sharing)
    sharing.add_argument("mode", choices=("on", "off"))

    serve = commands.add_parser("serve")
    _common(serve)
    serve.add_argument("--bind", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=0)

    capture = commands.add_parser("capture")
    _common(capture)
    capture.add_argument("--event-kind", default="workstream-change")
    capture.add_argument("--immediate", action="store_true")

    outbox = commands.add_parser("outbox")
    _common(outbox)

    sync = commands.add_parser("sync-now")
    _common(sync)
    sync.add_argument("--endpoint", required=True)

    invite = commands.add_parser("invite-create")
    _common(invite)
    invite.add_argument("--candidate-member-id", required=True)
    invite.add_argument("--endpoint", required=True)
    invite.add_argument("--expires-at")

    join_request = commands.add_parser("join-request")
    _common(join_request)
    join_request.add_argument("--invite", required=True)

    join_confirm = commands.add_parser("join-confirm")
    _common(join_confirm)
    join_confirm.add_argument("--request-id", required=True)

    join_finalize = commands.add_parser("join-finalize")
    _common(join_finalize)

    capability = commands.add_parser("capability")
    _common(capability)
    capability.add_argument("change", choices=("grant", "revoke"))
    capability.add_argument("--member-id", required=True)
    capability.add_argument("--capability", choices=("reviewer", "integrator", "admin"), required=True)

    host = commands.add_parser("host-switch")
    _common(host)
    host.add_argument("--host-id", required=True)
    host.add_argument("--device-id", required=True)
    host.add_argument("--endpoint")

    projection = commands.add_parser("projection")
    _common(projection)
    projection.add_argument("--endpoint", required=True)

    request_create = commands.add_parser("request-create")
    _common(request_create)
    request_create.add_argument("--endpoint", required=True)
    request_create.add_argument("--target-member-id", required=True)
    request_create.add_argument("--workstream-id", required=True)
    request_create.add_argument("--kind", required=True)
    request_create.add_argument("--summary", required=True)

    inbox = commands.add_parser("request-inbox")
    _common(inbox)
    inbox.add_argument("--endpoint", required=True)

    decision = commands.add_parser("request-decide")
    _common(decision)
    decision.add_argument("--endpoint", required=True)
    decision.add_argument("--request-id", required=True)
    decision.add_argument("--decision", choices=("accept", "reject"), required=True)
    decision.add_argument("--reason", required=True)
    return parser


def _print_human(action: str, data: object) -> None:
    print(f"Team {action}: {json.dumps(data, ensure_ascii=False, sort_keys=True)}")


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        action = arguments.action
        target = arguments.target
        if action == "status":
            data = load_team_config(target)
        elif action == "enable":
            data = enable_team(
                target, member_id=arguments.member_id, device_id=arguments.device_id,
                host_id=arguments.host_id, allow_lan_bind=arguments.allow_lan_bind,
                ttl_seconds=arguments.ttl_seconds, debounce_milliseconds=arguments.debounce_milliseconds,
            )
        elif action == "disable":
            data = disable_team(target)
        elif action == "heartbeat":
            data = configure_heartbeat(
                target, enabled=arguments.mode == "on", interval_seconds=arguments.interval_seconds,
            )
        elif action == "sharing":
            data = set_sharing(target, enabled=arguments.mode == "on")
        elif action == "serve":
            server, runtime = start_coordinator_server(target, bind=arguments.bind, port=arguments.port)
            if arguments.json_output:
                emit(response("team-serve", status="ok", exit_code=JsonExitCode.OK, data=runtime))
            else:
                _print_human("serve", runtime)
            try:
                server.serve_forever(poll_interval=0.1)
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return int(JsonExitCode.OK)
        elif action == "capture":
            envelope = capture_metadata_envelope(target)
            data = {
                "envelope": envelope,
                "outbox": queue_sync_event(
                    target, envelope, event_kind=arguments.event_kind, immediate=arguments.immediate,
                ),
            }
        elif action == "outbox":
            data = inspect_outbox(target)
        elif action == "sync-now":
            data = sync_now(target, endpoint=arguments.endpoint)
        elif action == "invite-create":
            expires = arguments.expires_at or (
                dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
            ).isoformat().replace("+00:00", "Z")
            data = create_invite(
                target, candidate_member_id=arguments.candidate_member_id,
                endpoint=arguments.endpoint, expires_at=expires,
            )
        elif action == "join-request":
            data = request_join(target, invite=arguments.invite)
        elif action == "join-confirm":
            data = confirm_join(target, request_id=arguments.request_id)
        elif action == "join-finalize":
            data = finalize_join(target)
        elif action == "capability":
            data = change_member_capability(
                target, member_id=arguments.member_id, action=arguments.change,
                capability=arguments.capability,
            )
        elif action == "host-switch":
            data = switch_active_host(target, host_id=arguments.host_id, device_id=arguments.device_id)
            if arguments.endpoint:
                data["coordinator"] = request_host_switch(target, endpoint=arguments.endpoint)
        elif action == "projection":
            data = fetch_projection(target, endpoint=arguments.endpoint)
        elif action == "request-create":
            data = send_request(
                target, endpoint=arguments.endpoint, target_member_id=arguments.target_member_id,
                workstream_id=arguments.workstream_id, request_kind=arguments.kind,
                summary=arguments.summary,
            )
        elif action == "request-inbox":
            data = {"requests": fetch_requests(target, endpoint=arguments.endpoint)}
        elif action == "request-decide":
            records = fetch_requests(target, endpoint=arguments.endpoint)
            selected = next((item for item in records if item.get("request_id") == arguments.request_id), None)
            if selected is None:
                raise ValueError("request is not in the local member inbox")
            data = decide_request(
                target, endpoint=arguments.endpoint, request_record=selected,
                decision=arguments.decision, reason=arguments.reason,
            )
        else:
            raise ValueError("unsupported Team command")
    except ValueError as exc:
        if arguments.json_output:
            emit(response(
                f"team-{arguments.action}", status="error", exit_code=JsonExitCode.VALIDATION_FAILED,
                errors=[issue("team_operation_failed", str(exc))],
            ))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return int(JsonExitCode.VALIDATION_FAILED)
    if arguments.json_output:
        emit(response(f"team-{arguments.action}", status="ok", exit_code=JsonExitCode.OK, data=data))
    else:
        _print_human(arguments.action, data)
    return int(JsonExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
