#!/usr/bin/env python3
"""Run the root-only, loopback-only W5B Team Observatory experience."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

import build_personal_observatory
from project_orrery_core.team import (
    capture_metadata_envelope,
    configure_heartbeat,
    confirm_join,
    decide_request,
    disable_team,
    enable_team,
    fetch_projection,
    fetch_requests,
    inspect_outbox,
    inspect_discovery_status,
    load_team_config,
    queue_sync_event,
    publish_discovery_once,
    scan_discovery_candidates,
    send_request,
    set_sharing,
    start_coordinator_server,
    stop_owned_coordinator_server,
    sync_now,
)
from project_orrery_core.maintenance import (
    authorize_maintenance_item,
    execute_maintenance_authorization,
    execute_quick_remove_item,
    maintenance_status,
    quick_remove_preflight,
    request_background_maintenance_refresh,
)
from project_orrery_observatory.team_observatory import inject_team_observatory, safe_json


UI_BODY_LIMIT = 16 * 1024
REQUEST_ID = re.compile(r"^request-[0-9a-f]{24}$")
COOKIE_NAME = "orrery_team_control"


def build_team_page(project_root: Path) -> str:
    if Path(project_root).resolve() != ROOT.resolve():
        raise ValueError("Team Observatory entry is root-only")
    previous = os.environ.get("ORRERY_PERSONAL_OBSERVATORY_VIEW")
    os.environ["ORRERY_PERSONAL_OBSERVATORY_VIEW"] = "1"
    try:
        page, _stats, _authority, _personal = build_personal_observatory.render_personal_site(
            ROOT / "docs", ROOT / "AGENTS.md", ROOT, "Orrery · Documentation",
            maintenance_control_available=True,
        )
    finally:
        if previous is None:
            os.environ.pop("ORRERY_PERSONAL_OBSERVATORY_VIEW", None)
        else:
            os.environ["ORRERY_PERSONAL_OBSERVATORY_VIEW"] = previous
    page = inject_team_observatory(page)
    if os.environ.get("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW", "").strip().lower() in {"1", "true", "yes", "on"}:
        import build_workstream_relation_graph

        page, _projection = build_workstream_relation_graph.inject_enabled_relation_graph(page, ROOT)
    return page


class TeamUIState:
    def __init__(self, project_root: Path, page: str):
        self.project_root = Path(project_root).resolve()
        self.page = page.encode("utf-8")
        self.control_token = secrets.token_urlsafe(32)
        self.coordinator = None
        self.coordinator_thread: threading.Thread | None = None
        self.coordinator_runtime: dict[str, Any] | None = None
        self.lock = threading.RLock()

    def start_coordinator(self) -> None:
        with self.lock:
            if self.coordinator is not None:
                raise ValueError("Coordinator is already owned by this UI")
            server, runtime = start_coordinator_server(
                self.project_root, bind="127.0.0.1", port=0
            )
            thread = threading.Thread(
                target=server.serve_forever,
                kwargs={"poll_interval": 0.1},
                daemon=True,
                name="orrery-team-coordinator",
            )
            thread.start()
            self.coordinator = server
            self.coordinator_thread = thread
            self.coordinator_runtime = dict(runtime)

    def stop_coordinator(self) -> None:
        with self.lock:
            if self.coordinator is None:
                raise ValueError("Coordinator is not owned by this UI")
            server = self.coordinator
            thread = self.coordinator_thread
            stop_owned_coordinator_server(self.project_root, server)
            if thread is not None:
                thread.join(timeout=5)
            self.coordinator = None
            self.coordinator_thread = None
            self.coordinator_runtime = None

    def close(self) -> None:
        with self.lock:
            if self.coordinator is not None:
                self.stop_coordinator()

    def endpoint(self) -> str:
        if not self.coordinator_runtime:
            raise ValueError("Coordinator is stopped")
        return str(self.coordinator_runtime["endpoint"])

    def public_status(self) -> dict[str, Any]:
        config = load_team_config(self.project_root)
        enabled = bool(config.get("enabled"))
        projection = None
        requests: list[dict[str, Any]] = []
        if enabled and self.coordinator_runtime:
            projection = fetch_projection(self.project_root, endpoint=self.endpoint())
            requests = fetch_requests(self.project_root, endpoint=self.endpoint())
        outbox_count = 0
        if enabled:
            outbox_count = len(inspect_outbox(self.project_root).get("events", []))
        public_config = {
            key: config.get(key)
            for key in (
                "enabled", "runtime_status", "member_id", "device_id", "host_id",
                "active_host_id", "sharing_enabled", "heartbeat", "ttl_seconds",
            )
            if key in config
        }
        return {
            "schema": "project-orrery-team-ui-status-v1",
            "config": public_config,
            "coordinator": {
                "owned": self.coordinator is not None,
                "running": self.coordinator_runtime is not None,
                "bind": "127.0.0.1" if self.coordinator_runtime else None,
            },
            "projection": projection,
            "requests": requests,
            "outbox_count": outbox_count,
            "lan": inspect_discovery_status(self.project_root) if enabled else {
                "status": {"status": "personal-zero-network"}, "candidates": [],
                "join_requests": [], "membership_from_discovery": False,
            },
            "authority": "derived-read-only",
            "execution_capability": False,
            "privacy": "metadata-only",
        }

    def discovery_probe(self) -> None:
        """One explicit, bounded loopback probe used by the local UI."""
        endpoint = self.endpoint()
        failure: list[BaseException] = []

        def scan() -> None:
            try:
                scan_discovery_candidates(
                    self.project_root, bind="127.0.0.1", timeout_seconds=0.5
                )
            except BaseException as exc:  # surfaced on the UI request thread
                failure.append(exc)

        thread = threading.Thread(target=scan, daemon=True, name="orrery-team-discovery-probe")
        thread.start()
        time.sleep(0.05)
        publish_discovery_once(
            self.project_root, endpoint=endpoint, target="127.0.0.1"
        )
        thread.join(timeout=2)
        if thread.is_alive():
            raise ValueError("bounded discovery probe did not stop")
        if failure:
            raise ValueError("bounded discovery probe failed") from failure[0]

    def refresh_page(self) -> None:
        if self.project_root.resolve() == ROOT.resolve():
            self.page = build_team_page(self.project_root).encode("utf-8")


class TeamUIServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], state: TeamUIState):
        self.state = state
        super().__init__(address, TeamUIHandler)

    def handle_error(self, request: Any, client_address: Any) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)

    def server_close(self) -> None:
        self.state.close()
        super().server_close()


class TeamUIHandler(BaseHTTPRequestHandler):
    server: TeamUIServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _expected_hosts(self) -> set[str]:
        port = self.server.server_address[1]
        return {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _host(self) -> str:
        host = self.headers.get("Host", "")
        if host not in self._expected_hosts():
            raise PermissionError("Host validation failed")
        return host

    def _origin(self) -> None:
        host = self._host()
        if self.headers.get("Origin") != f"http://{host}":
            raise PermissionError("same-origin validation failed")

    def _control(self) -> None:
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        value = cookie.get(COOKIE_NAME)
        if value is None or not hmac.compare_digest(
            value.value, self.server.state.control_token
        ):
            raise PermissionError("Host-local control validation failed")

    def _headers(self, status: int, content_type: str, length: int, *, cookie: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'",
        )
        if cookie:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE_NAME}={self.server.state.control_token}; HttpOnly; SameSite=Strict; Path=/team/",
            )
        self.end_headers()

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        raw = safe_json(payload)
        self._headers(status, "application/json; charset=utf-8", len(raw))
        self.wfile.write(raw)

    def _error(self, status: int, error: Exception) -> None:
        category = "permission-denied" if isinstance(error, PermissionError) else "operation-failed"
        self._json(status, {"error": f"Local Team {category}", "error_type": type(error).__name__})

    def _body(self, expected: set[str]) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("invalid body length") from error
        if length <= 0 or length > UI_BODY_LIMIT:
            raise ValueError("bounded request body required")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body must be JSON") from error
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("request fields are not allowed")
        return value

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._host()
            if self.path in {"/", "/team/"}:
                raw = self.server.state.page
                self._headers(HTTPStatus.OK, "text/html; charset=utf-8", len(raw), cookie=True)
                self.wfile.write(raw)
                return
            if self.path == "/team/api/status":
                self._control()
                self._json(HTTPStatus.OK, self.server.state.public_status())
                return
            if self.path == "/team/api/maintenance/status":
                self._control()
                self._json(HTTPStatus.OK, {"maintenance": maintenance_status(self.server.state.project_root)})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
        except PermissionError as error:
            self._error(HTTPStatus.FORBIDDEN, error)
        except ValueError as error:
            self._error(HTTPStatus.BAD_REQUEST, error)

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._origin()
            self._control()
            expected = set()
            if self.path == "/team/api/request/decision":
                expected = {"request_id", "decision"}
            elif self.path == "/team/api/join/confirm":
                expected = {"request_id"}
            elif self.path == "/team/api/maintenance/authorize":
                expected = {"item_id", "action"}
            elif self.path == "/team/api/maintenance/execute":
                expected = {"authorization_id"}
            elif self.path == "/team/api/maintenance/preflight":
                expected = {"target_id"}
            elif self.path == "/team/api/maintenance/quick-remove":
                expected = {"item_id"}
            body = self._body(expected)
            root = self.server.state.project_root
            maintenance_action = self.path.startswith("/team/api/maintenance/")
            maintenance_payload: Mapping[str, Any] | None = None
            if self.path == "/team/api/enable":
                enable_team(root, member_id="local-owner", device_id="local-device", host_id="local-host")
            elif self.path == "/team/api/disable":
                if self.server.state.coordinator is not None:
                    self.server.state.stop_coordinator()
                disable_team(root)
            elif self.path == "/team/api/start":
                self.server.state.start_coordinator()
            elif self.path == "/team/api/stop":
                self.server.state.stop_coordinator()
            elif self.path == "/team/api/heartbeat":
                config = load_team_config(root)
                configure_heartbeat(root, enabled=not bool(config.get("heartbeat", {}).get("enabled")))
            elif self.path == "/team/api/sharing":
                config = load_team_config(root)
                set_sharing(root, enabled=not bool(config.get("sharing_enabled")))
            elif self.path == "/team/api/capture":
                envelope = capture_metadata_envelope(root)
                queue_sync_event(root, envelope, event_kind="workstream-change", immediate=True)
            elif self.path == "/team/api/sync":
                sync_now(root, endpoint=self.server.state.endpoint())
            elif self.path == "/team/api/discovery":
                self.server.state.discovery_probe()
            elif self.path == "/team/api/join/confirm":
                request_id = str(body["request_id"])
                if not re.fullmatch(r"join-[0-9a-f]{24}", request_id):
                    raise ValueError("join request is invalid")
                confirm_join(root, request_id=request_id)
            elif self.path == "/team/api/request-create":
                envelope = capture_metadata_envelope(root)
                config = load_team_config(root)
                send_request(
                    root, endpoint=self.server.state.endpoint(),
                    target_member_id=str(config["member_id"]),
                    workstream_id=str(envelope["workstream_id"]),
                    request_kind="pause-workstream",
                    summary="Pause at the next local safe point",
                )
            elif self.path == "/team/api/maintenance-request":
                envelope = capture_metadata_envelope(root)
                config = load_team_config(root)
                send_request(
                    root, endpoint=self.server.state.endpoint(),
                    target_member_id=str(config["member_id"]),
                    workstream_id=str(envelope["workstream_id"]),
                    request_kind="cleanup",
                    summary="Evaluate workspace maintenance on the target member host",
                )
            elif self.path == "/team/api/request/decision":
                request_id = str(body["request_id"])
                decision = str(body["decision"])
                if not REQUEST_ID.fullmatch(request_id) or decision not in {"accept", "reject"}:
                    raise ValueError("request decision is invalid")
                selected = next(
                    (item for item in fetch_requests(root, endpoint=self.server.state.endpoint())
                     if item.get("request_id") == request_id),
                    None,
                )
                if selected is None:
                    raise ValueError("request is unavailable")
                decide_request(
                    root, endpoint=self.server.state.endpoint(), request_record=selected,
                    decision=decision, reason=f"{decision}ed in Host-local Team Observatory",
                )
            elif self.path == "/team/api/maintenance/scan":
                request_background_maintenance_refresh(root, reason="manual")
            elif self.path == "/team/api/maintenance/preflight":
                maintenance_payload = {
                    "preflight": quick_remove_preflight(root, target_id=str(body["target_id"]))
                }
            elif self.path == "/team/api/maintenance/quick-remove":
                maintenance_payload = execute_quick_remove_item(
                    root,
                    item_id=str(body["item_id"]),
                    actor_id="local-owner",
                )
            elif self.path == "/team/api/maintenance/authorize":
                authorize_maintenance_item(
                    root,
                    item_id=str(body["item_id"]),
                    action=str(body["action"]),
                    actor_id="local-owner",
                )
            elif self.path == "/team/api/maintenance/execute":
                execute_maintenance_authorization(
                    root, authorization_id=str(body["authorization_id"])
                )
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
                return
            if maintenance_action:
                self.server.state.refresh_page()
            payload = maintenance_payload or ({"maintenance": maintenance_status(root)} if maintenance_action else self.server.state.public_status())
            self._json(HTTPStatus.OK, payload)
        except PermissionError as error:
            self._error(HTTPStatus.FORBIDDEN, error)
        except (ValueError, OSError) as error:
            self._error(HTTPStatus.BAD_REQUEST, error)


def create_server(project_root: Path, page: str, *, port: int = 0) -> TeamUIServer:
    root = Path(project_root).resolve()
    if root != ROOT.resolve():
        raise ValueError("Team Observatory dynamic entry is root-only")
    return TeamUIServer(("127.0.0.1", port), TeamUIState(root, page))


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve root-only W5B Team Observatory on loopback")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    page = build_team_page(ROOT)
    server = create_server(ROOT, page, port=args.port)
    host, port = server.server_address[:2]
    print(f"Team Observatory: http://{host}:{port}/team/", flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
