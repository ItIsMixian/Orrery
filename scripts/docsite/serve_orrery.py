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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
for component in ("project-orrery-core", "project-orrery-observatory", "project-orrery-cli"):
    source = ROOT / "packages" / component / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from project_orrery_core.subprocess_policy import no_window_options  # noqa: E402


build_unified_observatory = None
legacy_serve = None
maintenance_status = None
accept_proposal = None
change_proposal_gate = None
defer_proposal = None
local_confirmation_capability = None
reject_proposal = None
capability_document = None
TeamUIState = None
WorkstreamGraphDelivery = None
_DEFERRED_CORPUS_BUILDER = None
_RUNTIME_IMPORT_LOCK = threading.Lock()


def build_active_task_projection(*args, **kwargs):
    from project_orrery_observatory.active_task_projection import build_active_task_projection as implementation

    return implementation(*args, **kwargs)


def collect_active_task_detail(*args, **kwargs):
    from project_orrery_observatory.active_task_projection import collect_active_task_detail as implementation

    return implementation(*args, **kwargs)


def render_task_fragment(*args, **kwargs):
    from project_orrery_observatory.active_task_projection import render_task_fragment as implementation

    return implementation(*args, **kwargs)


def _load_runtime_components() -> None:
    global build_unified_observatory, legacy_serve, maintenance_status
    global accept_proposal, change_proposal_gate, defer_proposal
    global local_confirmation_capability, reject_proposal, capability_document, TeamUIState
    global WorkstreamGraphDelivery, _DEFERRED_CORPUS_BUILDER
    if legacy_serve is not None:
        return
    with _RUNTIME_IMPORT_LOCK:
        if legacy_serve is not None:
            return
        import build_unified_observatory as unified_builder
        import docsite_qa as qa_module
        original_corpus_builder = qa_module.build_corpus
        qa_module.build_corpus = lambda _docs, _agents: []
        try:
            import serve as legacy_runtime
        finally:
            qa_module.build_corpus = original_corpus_builder
        from project_orrery_cli.operating_rules import preflight_repository_query
        from project_orrery_core.maintenance import maintenance_status as maintenance_status_impl
        from project_orrery_core.workstream_relation_capture import (
            accept_proposal as accept_proposal_impl,
            change_proposal_gate as change_proposal_gate_impl,
            defer_proposal as defer_proposal_impl,
            local_confirmation_capability as local_confirmation_capability_impl,
            reject_proposal as reject_proposal_impl,
        )
        from project_orrery_observatory.unified_observatory import capability_document as capability_document_impl
        from project_orrery_observatory.workstream_graph_cache import (
            WorkstreamGraphDelivery as workstream_graph_delivery_impl,
        )
        from serve_team_observatory import TeamUIState as team_ui_state_impl

        legacy_runtime.docsite_qa.configure_authority_route_preflight(
            lambda question: preflight_repository_query(ROOT, question, fact_scope="candidate")
        )
        build_unified_observatory = unified_builder
        legacy_serve = legacy_runtime
        maintenance_status = maintenance_status_impl
        accept_proposal = accept_proposal_impl
        change_proposal_gate = change_proposal_gate_impl
        defer_proposal = defer_proposal_impl
        local_confirmation_capability = local_confirmation_capability_impl
        reject_proposal = reject_proposal_impl
        capability_document = capability_document_impl
        TeamUIState = team_ui_state_impl
        WorkstreamGraphDelivery = workstream_graph_delivery_impl
        _DEFERRED_CORPUS_BUILDER = lambda: original_corpus_builder(legacy_runtime.DOCS, legacy_runtime.AGENTS)


COOKIE_NAME = "orrery_local_control"
BODY_LIMIT = 64 * 1024


def _project_graph_payload(provider):
    from project_orrery_observatory.workstream_relation_graph import project_core_relation_graph

    return project_core_relation_graph(provider)


def _runtime_page(*, failed: bool = False) -> str:
    title = "Orrery 启动失败" if failed else "Orrery 正在启动"
    message = (
        "完整视图未能激活。服务仍在本机运行；请查看 Git-private runtime log，修复后停止并重新启动。"
        if failed else
        "正在整理项目关系并组装完整视图。这个页面会在准备完成后自动进入总览。"
    )
    state = "failed" if failed else "starting"
    pulse_color = "#e08484" if failed else "var(--accent)"
    pulse_animation = "none" if failed else "pulse 1.6s infinite"
    status_text = (
        "本机 listener 已就绪，完整视图激活失败"
        if failed else "本机 listener 已就绪 · 正在后台渲染"
    )
    polling = "" if failed else """
const maxDelay=2000;
let delay=350;
async function poll(){
  try{
    const response=await fetch('/api/v1/health',{cache:'no-store'});
    const health=await response.json();
    if(health.status==='ready'){location.replace('/#overview');return;}
    if(health.status==='failed'){location.reload();return;}
  }catch(_error){}
  delay=Math.min(maxDelay,delay+200);
  window.setTimeout(poll,delay);
}
window.setTimeout(poll,delay);
"""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{color-scheme:dark;--bg:#0f1115;--panel:#171a21;--line:#2b303b;--text:#eef1f6;--muted:#aab2c0;--accent:#8db4ff}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 50% 20%,#1d2638 0,var(--bg) 52%);color:var(--text);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{width:min(620px,calc(100vw - 32px));padding:34px;border:1px solid var(--line);border-radius:18px;background:rgba(23,26,33,.96);box-shadow:0 24px 70px #0008}}
.brand{{color:var(--accent);font-size:.78rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}}h1{{margin:.45rem 0 .7rem;font-size:clamp(1.7rem,5vw,2.5rem)}}p{{margin:.5rem 0;color:var(--muted)}}.status{{display:flex;align-items:center;gap:.75rem;margin-top:1.5rem;color:var(--text)}}
.pulse{{width:.75rem;height:.75rem;border-radius:50%;background:{pulse_color};box-shadow:0 0 0 0 #8db4ff88;animation:{pulse_animation}}}
button{{margin-top:1.5rem;padding:.65rem 1rem;border:1px solid var(--line);border-radius:9px;background:#202633;color:var(--text);cursor:pointer}}button:hover{{border-color:var(--accent)}}
@keyframes pulse{{70%{{box-shadow:0 0 0 12px #8db4ff00}}100%{{box-shadow:0 0 0 0 #8db4ff00}}}}@media(prefers-reduced-motion:reduce){{.pulse{{animation:none}}}}
</style></head><body><main data-orrery-runtime-state="{state}"><div class="brand">Orrery · Local Observatory</div><h1>{title}</h1><p>{message}</p>
<div class="status"><span class="pulse" aria-hidden="true"></span><span>{status_text}</span></div>
<button id="stop" type="button">停止 Orrery</button></main><script>
document.getElementById('stop').addEventListener('click',async()=>{{await fetch('/api/v1/shell/stop',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:'{{}}'}});document.getElementById('stop').disabled=true;}});
{polling}</script></body></html>"""


def _git_private_path(relative: str) -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--git-path", relative], cwd=ROOT,
        capture_output=True, text=True, check=False,
        **no_window_options(),
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

    def reusable_url(self) -> str | None:
        """Return one healthy live runtime URL, recover stale state, or fail closed."""
        if not self.marker.exists():
            return None
        try:
            previous = json.loads(self.marker.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("runtime identity is corrupt; refusing replacement") from exc
        pid = previous.get("pid")
        if not _pid_alive(pid):
            self.marker.unlink(missing_ok=True)
            return None
        port = previous.get("port")
        expected_url = f"http://127.0.0.1:{port}/" if isinstance(port, int) else None
        marker_status = previous.get("status")
        if marker_status is None and previous.get("ready") is True:
            marker_status = "ready"
        if (
            previous.get("contract_type") != "unified-observatory-runtime-identity-v1"
            or previous.get("host") != "127.0.0.1"
            or not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535)
            or previous.get("url") != expected_url
            or marker_status not in {"starting", "ready"}
        ):
            raise RuntimeError("live runtime identity is invalid; refusing replacement")
        health_url = f"http://127.0.0.1:{port}/api/v1/health"
        request = Request(health_url, headers={"Host": f"127.0.0.1:{port}", "Accept": "application/json"})
        try:
            with urlopen(request, timeout=1.5) as response:
                if response.status != HTTPStatus.OK:
                    raise RuntimeError(f"health returned HTTP {response.status}")
                payload = json.loads(response.read(BODY_LIMIT + 1).decode("utf-8"))
        except (OSError, URLError, UnicodeDecodeError, json.JSONDecodeError, RuntimeError) as exc:
            raise RuntimeError("live Unified Observatory is unhealthy; refusing replacement") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("contract_type") != "unified-observatory-health-v1"
            or payload.get("status") not in {"starting", "ready"}
            or payload.get("status") != marker_status
            or payload.get("single_visible_url") is not True
        ):
            raise RuntimeError("live Unified Observatory is unhealthy; refusing replacement")
        return expected_url

    def publish(self, *, port: int, status: str) -> None:
        if status not in {"starting", "ready", "failed"}:
            raise ValueError("runtime identity status must be starting, ready, or failed")
        value = {
            "schema_version": 1,
            "contract_type": "unified-observatory-runtime-identity-v1",
            "instance_id": self.instance_id,
            "pid": os.getpid(),
            "host": "127.0.0.1",
            "port": port,
            "url": f"http://127.0.0.1:{port}/",
            "status": status,
            "ready": status == "ready",
            "written_at": time.time(),
        }
        temporary = self.marker.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.marker)

    def ready(self, *, port: int) -> None:
        self.publish(port=port, status="ready")

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
        self, *, identity, logger, page: str | None = None, registrations=(),
        authority_status=None, graph_provider_payload=None, fact_rules_projection=None,
    ):
        if page is not None:
            _load_runtime_components()
        self.state_lock = threading.RLock()
        self.lifecycle_status = "ready" if page is not None else "starting"
        self.page = (
            legacy_serve.inject_qa(page).encode("utf-8")
            if page is not None else _runtime_page().encode("utf-8")
        )
        self.registrations = tuple(registrations)
        self.authority_status = authority_status
        self.graph_provider_payload = dict(graph_provider_payload or {})
        self.fact_rules_projection = dict(fact_rules_projection or {})
        cached_capture = self.graph_provider_payload.get("relation_capture")
        self.relation_capture_payload = dict(cached_capture) if isinstance(cached_capture, dict) else {
            "schema_version": 2,
            "contract_type": "workstream-relation-capture-inspection",
            "pending_proposals": [],
            "read_only": True,
            "writes_performed": False,
            "network_performed": False,
            "status": "unavailable",
        }
        self.relation_capture_payload["local_actions_require_same_origin_cookie"] = True
        self.relation_capture_payload["central_request_only"] = True
        self.identity = identity
        self.logger = logger
        self.control_token = secrets.token_urlsafe(32)
        self.team = TeamUIState(ROOT, page) if page is not None else None
        self.server: UnifiedServer | None = None
        self.close_lock = threading.RLock()
        self.closed = False
        self.cancel_render = threading.Event()
        self.render_worker: threading.Thread | None = None
        self.graph_delivery = None
        self.graph_activation_worker: threading.Thread | None = None
        self.corpus_worker: threading.Thread | None = None
        self.authority_load_lock = threading.Lock()
        self.relation_capture_ready = threading.Event()
        self.relation_capture_load_lock = threading.Lock()
        self.port: int | None = None

    def current_page(self) -> bytes:
        with self.state_lock:
            return self.page

    def status(self) -> str:
        with self.state_lock:
            return "stopping" if self.closed else self.lifecycle_status

    def bind_runtime(self, *, port: int) -> None:
        self.port = port
        self.identity.publish(port=port, status="starting")

    def activate(
        self, *, page: str, registrations, authority_status, graph_provider_payload,
        fact_rules_projection,
    ) -> bool:
        ready_page = legacy_serve.inject_qa(page).encode("utf-8")
        team = TeamUIState(ROOT, page)
        cached_capture = dict(graph_provider_payload or {}).get("relation_capture")
        relation_capture = dict(cached_capture) if isinstance(cached_capture, dict) else {
            "schema_version": 2,
            "contract_type": "workstream-relation-capture-inspection",
            "pending_proposals": [],
            "read_only": True,
            "writes_performed": False,
            "network_performed": False,
            "status": "unavailable",
        }
        relation_capture["local_actions_require_same_origin_cookie"] = True
        relation_capture["central_request_only"] = True
        with self.state_lock:
            if self.closed or self.cancel_render.is_set():
                team.close()
                return False
            self.page = ready_page
            self.registrations = tuple(registrations)
            self.authority_status = authority_status
            self.graph_provider_payload = dict(graph_provider_payload or {})
            self.fact_rules_projection = dict(fact_rules_projection or {})
            self.relation_capture_payload = relation_capture
            self.team = team
            self.lifecycle_status = "ready"
            if self.port is not None:
                self.identity.publish(port=self.port, status="ready")
        return True

    def start_graph_activation(self) -> None:
        with self.state_lock:
            if self.closed or self.graph_activation_worker is not None:
                return
            delivery = WorkstreamGraphDelivery(
                ROOT, logger=lambda message: self.logger.info("graph delivery %s", message),
            )
            self.graph_delivery = delivery
            activation = threading.Thread(
                target=delivery.start,
                kwargs={
                    "provider": lambda: build_unified_observatory.graph_provider_payload(ROOT),
                    "projector": _project_graph_payload,
                    "on_provider_payload": self._accept_graph_provider_payload,
                },
                daemon=True,
                name="orrery-workstream-graph-activation",
            )
            self.graph_activation_worker = activation
        activation.start()

    def start_corpus_activation(self) -> None:
        with self.state_lock:
            if self.closed or self.corpus_worker is not None or legacy_serve.CORPUS:
                return
            worker = threading.Thread(
                target=self._build_corpus,
                daemon=True,
                name="orrery-docsite-corpus-activation",
            )
            self.corpus_worker = worker
        worker.start()

    def _build_corpus(self) -> None:
        try:
            corpus = _DEFERRED_CORPUS_BUILDER()
        except Exception:
            self.logger.info("deferred corpus activation failed with a sanitized local error")
            return
        with self.state_lock:
            if not self.closed:
                legacy_serve.CORPUS = corpus
                self.logger.info("deferred corpus activation ready documents=%d", len(corpus))

    def ensure_corpus(self) -> None:
        self.start_corpus_activation()
        worker = self.corpus_worker
        if worker is not None and worker is not threading.current_thread():
            worker.join()

    def _accept_graph_provider_payload(self, payload: Mapping[str, Any]) -> None:
        capture = payload.get("relation_capture")
        if not isinstance(capture, Mapping):
            return
        value = dict(capture)
        value["local_actions_require_same_origin_cookie"] = True
        value["central_request_only"] = True
        with self.state_lock:
            if self.closed:
                return
            self.relation_capture_payload = value
            self.relation_capture_ready.set()

    def relation_capture_response(self) -> dict[str, Any]:
        with self.state_lock:
            current = dict(self.relation_capture_payload)
        if current.get("status") != "loading":
            return current
        delivery = self.graph_delivery
        if delivery is not None and delivery.health().get("status") == "refreshing":
            self.relation_capture_ready.wait(timeout=45)
            with self.state_lock:
                current = dict(self.relation_capture_payload)
            if current.get("status") != "loading":
                return current
        with self.relation_capture_load_lock:
            with self.state_lock:
                current = dict(self.relation_capture_payload)
            if current.get("status") != "loading" or self.closed:
                return current
            try:
                value = build_unified_observatory.relation_capture_payload(ROOT)
            except Exception:
                value = {
                    "schema_version": 2,
                    "contract_type": "workstream-relation-capture-inspection",
                    "status": "unavailable",
                    "pending_proposals": [],
                    "read_only": True,
                    "writes_performed": False,
                    "network_performed": False,
                    "reason_code": "relation-capture-refresh-failed",
                }
            self._accept_graph_provider_payload({"relation_capture": value})
            with self.state_lock:
                return dict(self.relation_capture_payload)

    def fail_render(self) -> None:
        with self.state_lock:
            if self.closed or self.cancel_render.is_set():
                return
            self.page = _runtime_page(failed=True).encode("utf-8")
            self.lifecycle_status = "failed"
            if self.port is not None:
                self.identity.publish(port=self.port, status="failed")

    def health(self) -> dict[str, Any]:
        broker = legacy_serve._MANAGED_BROKER_SERVER if legacy_serve is not None else None
        team = self.team
        graph = self.graph_delivery.health() if self.graph_delivery is not None else {
            "status": "empty", "cache_state": "empty", "generation": 0,
            "reason_codes": ["shell-not-activated"],
        }
        return {
            "schema_version": 1,
            "contract_type": "unified-observatory-health-v1",
            "status": self.status(),
            "single_visible_url": True,
            "public_listener": "127.0.0.1",
            "managed_helpers": {
                "broker": "running" if broker is not None else "not-configured",
                "team-coordinator": "running" if team is not None and team.coordinator is not None else "stopped",
            },
            "consumers": {"workstream-graph": graph},
            "team_execution_capability": False,
            "writes_author_documents": False,
        }

    def graph_delivery_payload(self) -> dict[str, Any]:
        delivery = self.graph_delivery
        if delivery is None:
            return {
                "schema_version": 1,
                "contract_type": "workstream-graph-delivery-v1",
                "status": "empty",
                "cache_state": "empty",
                "generation": 0,
                "reason_codes": ["shell-not-activated"],
                "projection": None,
                "authority": "derived-read-only",
                "read_only": True,
                "writes_author_documents": False,
                "network_performed": False,
                "execution_capability": False,
                "available_actions": [],
            }
        return delivery.snapshot()

    def authority_status_response(self) -> dict[str, Any]:
        with self.state_lock:
            if self.authority_status is not None:
                return dict(self.authority_status)
        with self.authority_load_lock:
            with self.state_lock:
                if self.authority_status is not None:
                    return dict(self.authority_status)
            try:
                value = build_unified_observatory.inspect_managed_consumer(
                    ROOT,
                    requested_selection="legacy",
                    selection_authority="system-default",
                    fact_scope="candidate",
                    evidence_visibility=("revision-content", "human-or-agent-assertion"),
                )
            except Exception:
                return {"status": "unavailable", "reason_code": "authority-status-load-failed"}
            with self.state_lock:
                if not self.closed:
                    self.authority_status = dict(value)
                return dict(value)

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
            self.close()

            def stop() -> None:
                server.shutdown()
                server.server_close()

            threading.Thread(target=stop, daemon=True, name="orrery-unified-stop").start()

    def close(self) -> None:
        with self.close_lock:
            if self.closed:
                return
            self.closed = True
            self.cancel_render.set()
            self.relation_capture_ready.set()
            try:
                if self.graph_delivery is not None:
                    self.graph_delivery.close()
                if self.graph_activation_worker is not None and self.graph_activation_worker is not threading.current_thread():
                    self.graph_activation_worker.join()
                if self.corpus_worker is not None and self.corpus_worker is not threading.current_thread():
                    self.corpus_worker.join()
                if self.team is not None:
                    self.team.close()
            finally:
                if legacy_serve is not None:
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


class LegacyCompatibleHandler(BaseHTTPRequestHandler):
    _CSP = (
        "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
    )

    def _send_security_headers(self, *, cache_control: str = "no-store") -> None:
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", self._CSP)

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(code, "application/json; charset=utf-8", body)

    def _host_authorized(self) -> bool:
        raw = self.headers.get("Host", "")
        try:
            parsed = urlsplit("http://" + raw)
            expected_port = int(self.server.server_address[1])
            return parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == expected_port
        except (TypeError, ValueError):
            return False

    def _same_origin_authorized(self) -> bool:
        if not self._host_authorized():
            return False
        origin = self.headers.get("Origin", "")
        try:
            parsed = urlsplit(origin)
            expected_port = int(self.server.server_address[1])
            if (
                parsed.scheme != "http"
                or parsed.hostname not in {"127.0.0.1", "localhost"}
                or parsed.port != expected_port
            ):
                return False
        except (TypeError, ValueError):
            return False
        fetch_site = self.headers.get("Sec-Fetch-Site", "")
        return not fetch_site or fetch_site in {"same-origin", "none"}

    def _settings_authorized(self) -> bool:
        _load_runtime_components()
        return legacy_serve.Handler._settings_authorized(self)

    def _read_json_body(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Content-Length is invalid") from error
        if length <= 0 or length > BODY_LIMIT:
            raise ValueError("request body is empty or exceeds 64 KiB")
        try:
            data = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body is not valid JSON") from error
        if not isinstance(data, dict):
            raise ValueError("request must be a JSON object")
        return data

    def do_GET(self) -> None:  # noqa: N802
        _load_runtime_components()
        legacy_serve.Handler.do_GET(self)

    def do_POST(self) -> None:  # noqa: N802
        _load_runtime_components()
        legacy_serve.Handler.do_POST(self)

    def do_DELETE(self) -> None:  # noqa: N802
        _load_runtime_components()
        legacy_serve.Handler.do_DELETE(self)


class UnifiedHandler(LegacyCompatibleHandler):
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
        body = self.server.state.current_page()
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
        self.server.state.ensure_corpus()
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
            if path == "/api/v1/diagnostics":
                self._send_json(HTTPStatus.OK, self.server.state.diagnostics())
                return
            if self.server.state.status() != "ready":
                self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {
                    "status": self.server.state.status(), "error": "full Observatory is not ready",
                })
                return
            if path == "/api/v1/capabilities":
                self._send_json(HTTPStatus.OK, self.server.state.capabilities())
                return
            if path == "/api/v1/docs/search":
                self._send_json(HTTPStatus.OK, self._search())
                return
            if path == "/api/v1/authority/status":
                self._send_json(HTTPStatus.OK, self.server.state.authority_status_response())
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
                self._send_json(HTTPStatus.OK, self.server.state.graph_delivery_payload())
                return
            if path == "/api/v1/workstreams/relations":
                self._send_json(HTTPStatus.OK, self.server.state.relation_capture_response())
                return
            if path == "/api/v1/maintenance/status":
                self._send_json(HTTPStatus.OK, {"maintenance": maintenance_status(ROOT)})
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
            if self.server.state.status() != "ready":
                self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {
                    "status": self.server.state.status(), "error": "full Observatory is not ready",
                })
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
                if path.startswith("/api/v1/ai/ask") or "/refresh/" in path:
                    self.server.state.ensure_corpus()
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
            relation_actions = {
                "/api/v1/workstreams/relations/accept": ("accept", {"proposal_id", "expected_revision"}),
                "/api/v1/workstreams/relations/change-gate": ("change-gate", {"proposal_id", "expected_revision", "required_for"}),
                "/api/v1/workstreams/relations/defer": ("defer", {"proposal_id", "expected_revision"}),
                "/api/v1/workstreams/relations/reject": ("reject", {"proposal_id", "expected_revision"}),
            }
            if path in relation_actions:
                action, expected = relation_actions[path]
                body = self._exact_body(expected)
                proposal_id = str(body["proposal_id"])
                revision = body["expected_revision"]
                if not isinstance(revision, int) or isinstance(revision, bool):
                    raise ValueError("expected_revision must be an integer")
                capability = local_confirmation_capability(ROOT, proposal_id)
                if capability["allowed"] is not True:
                    raise PermissionError("current local human lacks the required relation authority")
                actor_id = str(capability["member_id"])
                if action == "accept":
                    payload = accept_proposal(
                        ROOT, proposal_id, expected_revision=revision,
                        confirmer_id=actor_id, confirmer_role=str(capability["required_role"]),
                        caller_kind="human", caller_context="local", local_confirmation=True,
                    )
                elif action == "change-gate":
                    payload = change_proposal_gate(
                        ROOT, proposal_id, expected_revision=revision,
                        required_for=str(body["required_for"]), actor_id=actor_id,
                        reason="本机维护者在关系 inbox 中明确调整阻塞阶段",
                    )
                elif action == "defer":
                    payload = defer_proposal(
                        ROOT, proposal_id, expected_revision=revision, actor_id=actor_id,
                        reason="本机维护者要求等待更多关系证据",
                    )
                else:
                    payload = reject_proposal(
                        ROOT, proposal_id, expected_revision=revision, actor_id=actor_id,
                        reason="本机维护者拒绝当前关系建议",
                    )
                self.server.state.relation_capture_payload = build_unified_observatory.relation_capture_payload(ROOT)
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
    _load_runtime_components()
    environment = dict(os.environ)
    if no_browser:
        environment["DOCSITE_NO_BROWSER"] = "1"
    command = [sys.executable, "-X", "utf8", str(HERE.parent / "serve.py")]
    return subprocess.call(
        command, cwd=ROOT, env=environment,
        **no_window_options(enabled=not console),
    )


def _render_background(state: UnifiedState, *, started_at: float) -> None:
    render_started = time.perf_counter()
    state.logger.info(
        "startup phase=render-background status=starting elapsed_ms=%d",
        round((render_started - started_at) * 1000),
    )
    try:
        _load_runtime_components()
        page, _stats, registrations, authority, graph_provider_payload, fact_rules_projection = build_unified_observatory.render_unified_site(
            ROOT, mode="dynamic", ai_available=legacy_serve.PROVIDER is not None,
            base_site=(legacy_serve._page, legacy_serve._stats, legacy_serve._authority_shadow_report),
        )
        activated = state.activate(
            page=page, registrations=registrations, authority_status=authority,
            graph_provider_payload=graph_provider_payload,
            fact_rules_projection=fact_rules_projection,
        )
        if activated:
            state.logger.info(
                "startup phase=base-shell status=ready graph_status=%s phase_ms=%d total_ms=%d",
                state.graph_delivery.health()["status"] if state.graph_delivery is not None else "empty",
                round((time.perf_counter() - render_started) * 1000),
                round((time.perf_counter() - started_at) * 1000),
            )
            state.start_graph_activation()
            state.start_corpus_activation()
        else:
            state.logger.info(
                "startup phase=render-background status=cancelled total_ms=%d",
                round((time.perf_counter() - started_at) * 1000),
            )
    except Exception:
        state.logger.exception(
            "startup phase=render-background status=failed total_ms=%d",
            round((time.perf_counter() - started_at) * 1000),
        )
        try:
            state.fail_render()
        except Exception:
            state.logger.exception("startup phase=failure-projection status=failed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start root-only Unified Observatory Candidate")
    parser.add_argument("--port", type=int)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--console", action="store_true")
    parser.add_argument("--legacy", action="store_true", help="whole-shell rollback to current serve.py")
    arguments = parser.parse_args(argv)
    if arguments.legacy:
        return _legacy(arguments.console, arguments.no_browser)

    started_at = time.perf_counter()
    identity = RuntimeIdentity()
    logger = _logger(identity, console=arguments.console)
    server: UnifiedServer | None = None
    try:
        existing_url = identity.reusable_url()
        if existing_url is not None:
            url = f"{existing_url}#overview"
            logger.info("reusing healthy runtime url=%s visible_urls=1", url)
            if not arguments.no_browser:
                webbrowser.open(url)
            return 0
        identity.recover()
        state = UnifiedState(identity=identity, logger=logger)
        server = _bind_server(state, arguments.port)
        port = int(server.server_address[1])
        state.bind_runtime(port=port)
        url = f"http://127.0.0.1:{port}/#overview"
        logger.info(
            "startup phase=listener status=starting url=%s visible_urls=1 elapsed_ms=%d",
            url, round((time.perf_counter() - started_at) * 1000),
        )
        if not arguments.no_browser:
            threading.Timer(0.2, webbrowser.open, args=(url,)).start()
        state.render_worker = threading.Thread(
            target=_render_background,
            kwargs={"state": state, "started_at": started_at},
            daemon=True,
            name="orrery-unified-render",
        )
        state.render_worker.start()
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
            if legacy_serve is not None:
                legacy_serve._stop_managed_broker()
            identity.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
