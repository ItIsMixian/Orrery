#!/usr/bin/env python3
"""Root-only Unified Observatory Candidate supervisor and visible front door."""
from __future__ import annotations

import argparse
import ctypes
import hmac
import json
import logging
import os
import secrets
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
for component in ("project-orrery-core", "project-orrery-observatory", "project-orrery-cli"):
    source = ROOT / "packages" / component / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

import build_unified_observatory  # noqa: E402
import serve as legacy_serve  # noqa: E402
from project_orrery_cli.operating_rules import preflight_repository_query  # noqa: E402
from project_orrery_core.maintenance import maintenance_status  # noqa: E402
from project_orrery_observatory.active_task_projection import (  # noqa: E402
    build_active_task_projection,
    collect_active_task_detail,
    render_task_fragment,
)
from project_orrery_observatory.unified_observatory import capability_document  # noqa: E402
from serve_team_observatory import TeamUIState  # noqa: E402


legacy_serve.docsite_qa.configure_authority_route_preflight(
    lambda question: preflight_repository_query(ROOT, question, fact_scope="candidate")
)


COOKIE_NAME = "orrery_local_control"
BODY_LIMIT = 64 * 1024


def _git_private_path(relative: str) -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--git-path", relative], cwd=ROOT,
        capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Unified Observatory requires an Orrery Git worktree")
    value = Path(completed.stdout.strip())
    return value.resolve() if value.is_absolute() else (ROOT / value).resolve()


def _pid_alive(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel32.GetExitCodeProcess.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        try:
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


class RuntimeIdentity:
    def __init__(self) -> None:
        self.root = _git_private_path("orrery/runtime/unified-observatory")
        self.marker = self.root / "runtime.json"
        self.log_path = self.root / "unified.log"
        self.instance_id = uuid.uuid4().hex
        self.root.mkdir(parents=True, exist_ok=True)

    def recover(self) -> None:
        if not self.marker.exists():
            return
        try:
            previous = json.loads(self.marker.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            previous = {}
        if _pid_alive(previous.get("pid")):
            raise RuntimeError("another Unified Observatory supervisor is already running")
        self.marker.unlink(missing_ok=True)

    def ready(self, *, port: int) -> None:
        value = {
            "schema_version": 1,
            "contract_type": "unified-observatory-runtime-identity-v1",
            "instance_id": self.instance_id,
            "pid": os.getpid(),
            "host": "127.0.0.1",
            "port": port,
            "url": f"http://127.0.0.1:{port}/",
            "ready": True,
            "written_at": time.time(),
        }
        temporary = self.marker.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.marker)

    def cleanup(self) -> None:
        try:
            value = json.loads(self.marker.read_text(encoding="utf-8"))
            if value.get("instance_id") == self.instance_id:
                self.marker.unlink(missing_ok=True)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return


def _logger(identity: RuntimeIdentity, *, console: bool) -> logging.Logger:
    logger = logging.getLogger("orrery-unified")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(identity.log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    if console:
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logger.addHandler(stream)
    return logger


class UnifiedState:
    def __init__(
        self, *, page: str, registrations, authority_status, graph_provider_payload,
        fact_rules_projection,
        identity, logger,
    ):
        self.page = legacy_serve.inject_qa(page).encode("utf-8")
        self.registrations = tuple(registrations)
        self.authority_status = authority_status
        self.graph_provider_payload = dict(graph_provider_payload or {})
        self.fact_rules_projection = dict(fact_rules_projection or {})
        self.identity = identity
        self.logger = logger
        self.control_token = secrets.token_urlsafe(32)
        self.team = TeamUIState(ROOT, page)
        self.server: UnifiedServer | None = None
        self.close_lock = threading.RLock()
        self.closed = False

    def health(self) -> dict[str, Any]:
        broker = legacy_serve._MANAGED_BROKER_SERVER
        return {
            "schema_version": 1,
            "contract_type": "unified-observatory-health-v1",
            "status": "ready" if not self.closed else "stopping",
            "single_visible_url": True,
            "public_listener": "127.0.0.1",
            "managed_helpers": {
                "broker": "running" if broker is not None else "not-configured",
                "team-coordinator": "running" if self.team.coordinator is not None else "stopped",
            },
            "team_execution_capability": False,
            "writes_author_documents": False,
        }

    def capabilities(self) -> dict[str, Any]:
        return capability_document(self.registrations, mode="dynamic")

    def diagnostics(self) -> dict[str, Any]:
        try:
            lines = self.identity.log_path.read_text(encoding="utf-8").splitlines()[-120:]
        except OSError:
            lines = []
        return {"schema_version": 1, "lines": lines, "path_exposed": False}

    def request_stop(self) -> None:
        server = self.server
        if server is not None:
            def stop() -> None:
                server.shutdown()
                server.server_close()

            threading.Thread(target=stop, daemon=True, name="orrery-unified-stop").start()

    def close(self) -> None:
        with self.close_lock:
            if self.closed:
                return
            self.closed = True
            try:
                self.team.close()
            finally:
                legacy_serve._stop_managed_broker()
                self.identity.cleanup()
                self.logger.info("runtime stopped; helper ownership released")


class UnifiedServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], state: UnifiedState):
        self.state = state
        super().__init__(address, UnifiedHandler)
        state.server = self

    def server_close(self) -> None:
        self.state.close()
        super().server_close()


class UnifiedHandler(legacy_serve.Handler):
    server: UnifiedServer

    def log_message(self, fmt: str, *args: Any) -> None:
        self.server.state.logger.info("%s %s", self.command, self.path)

    def _cookie_authorized(self) -> bool:
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        value = cookie.get(COOKIE_NAME)
        return value is not None and hmac.compare_digest(
            value.value, self.server.state.control_token
        )

    def _send_page(self) -> None:
        body = self.server.state.page
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.send_header(
            "Set-Cookie",
            f"{COOKIE_NAME}={self.server.state.control_token}; HttpOnly; SameSite=Strict; Path=/",
        )
        self.end_headers()
        self.wfile.write(body)

    def _exact_body(self, expected: set[str]) -> dict[str, Any]:
        value = self._read_json_body()
        if set(value) != expected:
            raise ValueError("request fields are not allowed")
        return value

    def _require_mutation_boundary(self) -> bool:
        if not self._same_origin_authorized() or not self._cookie_authorized():
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "same-origin local control cookie required"})
            return False
        return True

    def _search(self) -> dict[str, Any]:
        query = parse_qs(urlsplit(self.path).query).get("q", [""])[0].strip().lower()
        if not query or len(query) > 160:
            raise ValueError("search query must contain 1..160 characters")
        hits = []
        for item in legacy_serve.CORPUS:
            haystack = (str(item.get("title", "")) + "\n" + str(item.get("text", ""))).lower()
            if query in haystack:
                hits.append({
                    "id": item.get("id"), "page": item.get("page"),
                    "kind": item.get("kind"), "title": item.get("title"),
                })
            if len(hits) == 40:
                break
        return {"query": query, "hits": hits, "bounded": True}

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_authorized():
            self._send_json(HTTPStatus.MISDIRECTED_REQUEST, {"error": "Host must match the current loopback listener"})
            return
        path = urlsplit(self.path).path
        try:
            if path == "/":
                self._send_page()
                return
            if path == "/api/v1/health":
                self._send_json(HTTPStatus.OK, self.server.state.health())
                return
            if path == "/api/v1/capabilities":
                self._send_json(HTTPStatus.OK, self.server.state.capabilities())
                return
            if path == "/api/v1/docs/search":
                self._send_json(HTTPStatus.OK, self._search())
                return
            if path == "/api/v1/authority/status":
                self._send_json(HTTPStatus.OK, self.server.state.authority_status or {"status": "unavailable"})
                return
            if path == "/api/v1/authority/operating-rules":
                self._send_json(HTTPStatus.OK, self.server.state.fact_rules_projection)
                return
            if path == "/api/v1/personal/status":
                projection = build_active_task_projection(ROOT)
                self._send_json(HTTPStatus.OK, {
                    "status": "available",
                    "authority": "host-local-projection",
                    "revision": projection["revision"],
                    "counts": projection["counts"],
                    "captured_at": projection["captured_at"],
                })
                return
            if path == "/api/v1/personal/tasks":
                projection = build_active_task_projection(ROOT)
                public_projection = {
                    key: value for key, value in projection.items()
                    if key not in {"maintenance"}
                }
                self._send_json(HTTPStatus.OK, {
                    "projection": public_projection,
                    "fragment": render_task_fragment(projection),
                })
                return
            if path.startswith("/api/v1/personal/tasks/"):
                task_id = path.removeprefix("/api/v1/personal/tasks/")
                if not task_id or len(task_id) > 64:
                    raise ValueError("task id must contain 1..64 characters")
                self._send_json(HTTPStatus.OK, collect_active_task_detail(ROOT, task_id))
                return
            if path == "/api/v1/team/status":
                self._send_json(HTTPStatus.OK, self.server.state.team.public_status())
                return
            if path == "/api/v1/workstreams/graph":
                self._send_json(HTTPStatus.OK, {
                    **self.server.state.graph_provider_payload,
                    "dynamic_delivery": "startup-cached-projection",
                })
                return
            if path == "/api/v1/maintenance/status":
                self._send_json(HTTPStatus.OK, {"maintenance": maintenance_status(ROOT)})
                return
            if path == "/api/v1/diagnostics":
                self._send_json(HTTPStatus.OK, self.server.state.diagnostics())
                return
            if path == "/api/v1/ai/settings":
                self.path = "/api/ai-config"
                super().do_GET()
                return
            if path.startswith("/api/"):
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
                return
            super().do_GET()
        except (OSError, ValueError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)[:400]})

    def do_POST(self) -> None:  # noqa: N802
        if not self._require_mutation_boundary():
            return
        path = urlsplit(self.path).path
        try:
            if path == "/api/v1/shell/stop":
                self._exact_body(set())
                self._send_json(HTTPStatus.ACCEPTED, {"status": "stopping"})
                self.server.state.request_stop()
                return
            aliases = {
                "/api/v1/ai/ask": "/ask",
                "/api/v1/ai/ask-stream": "/ask_stream",
                "/api/v1/ai/settings": "/api/ai-config",
                "/api/v1/ai/settings/test": "/api/ai-config/test",
                "/api/v1/ai/refresh/briefing": "/api/refresh/briefing",
                "/api/v1/ai/refresh/roadmap": "/api/refresh/roadmap",
                "/api/v1/ai/refresh/milestones": "/api/refresh/milestones",
                "/api/v1/ai/refresh/radar": "/api/refresh/radar",
            }
            if path in aliases:
                self.path = aliases[path]
                super().do_POST()
                return
            if path.startswith("/api/v1/team/"):
                action = path.removeprefix("/api/v1/team/")
                expected = {
                    "request/decision": {"request_id", "decision"},
                    "join/confirm": {"request_id"},
                }.get(action, set())
                body = self._exact_body(expected)
                try:
                    payload = self.server.state.team.perform(
                        action, body, refresh_legacy_page=False,
                    )
                except KeyError:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
                    return
                self._send_json(HTTPStatus.OK, dict(payload))
                return
            maintenance_actions = {
                "/api/v1/maintenance/refresh": ("maintenance/scan", set()),
                "/api/v1/maintenance/preflight": ("maintenance/preflight", {"target_id"}),
                "/api/v1/maintenance/remove-worktree": ("maintenance/quick-remove", {"item_id"}),
            }
            if path in maintenance_actions:
                action, expected = maintenance_actions[path]
                payload = self.server.state.team.perform(
                    action, self._exact_body(expected), refresh_legacy_page=False,
                )
                self._send_json(HTTPStatus.OK, dict(payload))
                return
            if path.startswith("/api/"):
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
                return
            super().do_POST()
        except PermissionError as error:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": str(error)[:400]})
        except (OSError, ValueError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)[:400]})

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._require_mutation_boundary():
            return
        path = urlsplit(self.path).path
        if path == "/api/v1/ai/settings/key":
            self.path = "/api/ai-config/key"
            super().do_DELETE()
            return
        if path.startswith("/api/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not-found"})
            return
        super().do_DELETE()


def _bind_server(state: UnifiedState, requested: int | None) -> UnifiedServer:
    ports = [requested] if requested is not None else list(range(8765, 8785))
    for port in ports:
        if port is None or port < 0 or port > 65535:
            raise ValueError("port must be in 0..65535")
        try:
            return UnifiedServer(("127.0.0.1", port), state)
        except OSError:
            continue
    raise RuntimeError("no free loopback port in the requested range")


def _legacy(console: bool, no_browser: bool) -> int:
    environment = dict(os.environ)
    if no_browser:
        environment["DOCSITE_NO_BROWSER"] = "1"
    command = [sys.executable, "-X", "utf8", str(HERE.parent / "serve.py")]
    return subprocess.call(command, cwd=ROOT, env=environment)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start root-only Unified Observatory Candidate")
    parser.add_argument("--port", type=int)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--console", action="store_true")
    parser.add_argument("--legacy", action="store_true", help="whole-shell rollback to current serve.py")
    arguments = parser.parse_args(argv)
    if arguments.legacy:
        return _legacy(arguments.console, arguments.no_browser)

    identity = RuntimeIdentity()
    logger = _logger(identity, console=arguments.console)
    server: UnifiedServer | None = None
    try:
        identity.recover()
        page, _stats, registrations, authority, graph_provider_payload, fact_rules_projection = build_unified_observatory.render_unified_site(
            ROOT, mode="dynamic", ai_available=legacy_serve.PROVIDER is not None,
        )
        state = UnifiedState(
            page=page, registrations=registrations, authority_status=authority,
            graph_provider_payload=graph_provider_payload, identity=identity, logger=logger,
            fact_rules_projection=fact_rules_projection,
        )
        server = _bind_server(state, arguments.port)
        port = int(server.server_address[1])
        identity.ready(port=port)
        url = f"http://127.0.0.1:{port}/#overview"
        logger.info("runtime ready url=%s visible_urls=1", url)
        if not arguments.no_browser:
            threading.Timer(0.2, webbrowser.open, args=(url,)).start()
        server.serve_forever(poll_interval=0.1)
        return 0
    except KeyboardInterrupt:
        logger.info("console interrupt requested")
        return 0
    except Exception:
        logger.exception("startup/runtime failure")
        return 1
    finally:
        if server is not None:
            server.server_close()
        else:
            legacy_serve._stop_managed_broker()
            identity.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
