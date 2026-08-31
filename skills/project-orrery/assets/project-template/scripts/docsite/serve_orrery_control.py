#!/usr/bin/env python3
"""Serve the root-only, loopback-only Orrery Maintenance console."""
from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sys
import threading
import webbrowser
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
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from project_orrery_core.maintenance import (  # noqa: E402
    execute_quick_remove_item,
    maintenance_status,
    quick_remove_preflight,
    request_background_catch_up,
    request_background_maintenance_refresh,
)
from project_orrery_observatory.personal_observatory import (  # noqa: E402
    render_maintenance_control_document,
)


BODY_LIMIT = 8 * 1024
COOKIE_NAME = "orrery_maintenance_control"


class ControlState:
    def __init__(self, project_root: Path):
        root = Path(project_root).resolve()
        if root != ROOT.resolve():
            raise ValueError("Orrery control entry is root-only")
        self.project_root = root
        self.control_token = secrets.token_urlsafe(32)
        self.render_lock = threading.RLock()

    def status(self) -> dict[str, Any]:
        value = maintenance_status(self.project_root)
        value["control_available"] = True
        value["api_base"] = "/control/api/maintenance"
        value["authority"] = "host-local-remove-worktree-only"
        value["team_authority"] = False
        return value

    def page(self) -> bytes:
        with self.render_lock:
            return render_maintenance_control_document(self.status()).encode("utf-8")


class ControlServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], state: ControlState):
        self.state = state
        super().__init__(address, ControlHandler)

    def handle_error(self, request: Any, client_address: Any) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class ControlHandler(BaseHTTPRequestHandler):
    server: ControlServer

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
        if value is None or not hmac.compare_digest(value.value, self.server.state.control_token):
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
            "connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'",
        )
        if cookie:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE_NAME}={self.server.state.control_token}; HttpOnly; SameSite=Strict; Path=/control/",
            )
        self.end_headers()

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(raw))
        self.wfile.write(raw)

    def _error(self, status: int, error: Exception) -> None:
        self._json(
            status,
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "network_performed": False,
            },
        )

    def _body(self, expected: set[str]) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid body length") from exc
        if length <= 0 or length > BODY_LIMIT:
            raise ValueError("bounded request body required")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be JSON") from exc
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("request fields are not allowed")
        return value

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._host()
            if self.path in {"/", "/control/", "/control/maintenance"}:
                raw = self.server.state.page()
                self._headers(HTTPStatus.OK, "text/html; charset=utf-8", len(raw), cookie=True)
                self.wfile.write(raw)
                return
            if self.path == "/control/api/maintenance/status":
                self._control()
                self._json(HTTPStatus.OK, {"maintenance": self.server.state.status()})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
        except PermissionError as exc:
            self._error(HTTPStatus.FORBIDDEN, exc)
        except (OSError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, exc)

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._origin()
            self._control()
            if self.path == "/control/api/maintenance/scan":
                self._body(set())
                refresh = request_background_maintenance_refresh(self.server.state.project_root, reason="manual")
                self._json(HTTPStatus.ACCEPTED, {"background_refresh": refresh})
                return
            if self.path == "/control/api/maintenance/preflight":
                body = self._body({"target_id"})
                preflight = quick_remove_preflight(
                    self.server.state.project_root,
                    target_id=str(body["target_id"]),
                )
                self._json(HTTPStatus.OK, {"preflight": preflight})
                return
            if self.path == "/control/api/maintenance/quick-remove":
                body = self._body({"item_id"})
                result = execute_quick_remove_item(
                    self.server.state.project_root,
                    item_id=str(body["item_id"]),
                    actor_id="local-owner",
                )
                self._json(HTTPStatus.OK, result)
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
        except PermissionError as exc:
            self._error(HTTPStatus.FORBIDDEN, exc)
        except (OSError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, exc)


def create_server(project_root: Path, *, port: int = 0) -> ControlServer:
    return ControlServer(("127.0.0.1", port), ControlState(project_root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the root-only Orrery Maintenance console on loopback")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args()
    server = create_server(ROOT, port=args.port)
    host, port = server.server_address[:2]
    url = f"http://{host}:{port}/control/maintenance"
    request_background_catch_up(ROOT)
    print(f"Orrery Maintenance: {url}", flush=True)
    if args.open_browser:
        threading.Timer(0.15, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
