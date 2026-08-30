from __future__ import annotations

import http.client
import json
import logging
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
OBSERVATORY_SOURCE = ROOT / "packages" / "project-orrery-observatory" / "src"
CLI_SOURCE = ROOT / "packages" / "project-orrery-cli" / "src"
CORE_SOURCE = ROOT / "packages" / "project-orrery-core" / "src"
DOCSITE = ROOT / "scripts" / "docsite"
for source in (OBSERVATORY_SOURCE, CLI_SOURCE, CORE_SOURCE, DOCSITE):
    sys.path.insert(0, str(source))

import build_unified_observatory  # noqa: E402
import serve_orrery  # noqa: E402
from project_orrery_observatory.unified_observatory import (  # noqa: E402
    ConsumerRegistration,
    RegistrationError,
    capability_document,
    inject_unified_shell,
    quarantine,
    validate_registrations,
)


class FakeIdentity:
    def __init__(self, root: Path):
        self.root = root
        self.log_path = root / "unified.log"
        self.log_path.write_text("test runtime\n", encoding="utf-8")
        self.cleaned = False

    def cleanup(self) -> None:
        self.cleaned = True


class UnifiedRegistrationTests(unittest.TestCase):
    def test_versioned_registration_and_capability_discovery_are_sanitized(self) -> None:
        registrations = build_unified_observatory.default_registrations(mode="dynamic")
        self.assertEqual(len(registrations), 8)
        document = capability_document(registrations, mode="dynamic")
        self.assertEqual(document["contract_type"], "unified-observatory-shell-v1")
        self.assertTrue(document["single_visible_url"])
        self.assertFalse(document["writes_author_documents"])
        encoded = json.dumps(document)
        self.assertNotIn(str(ROOT), encoded)
        self.assertNotIn("api_key", encoded.lower())
        self.assertEqual(
            {item["navigation"]["identity"] for item in document["consumers"]},
            {"overview", "docs", "ask", "authority", "personal", "team", "workstreams", "maintenance"},
        )

    def test_route_collision_and_privilege_escalation_fail_closed(self) -> None:
        registrations = list(build_unified_observatory.default_registrations(mode="dynamic"))
        source = registrations[2]
        collision = replace(
            source, consumer_id="collision", navigation_identity="collision",
            route_prefix="/api/v1/docs/search",
        )
        with self.assertRaisesRegex(RegistrationError, "route collision"):
            validate_registrations([*registrations, collision])
        escalation = replace(
            registrations[0], capabilities=("read-status", "local-remove-worktree")
        )
        with self.assertRaisesRegex(RegistrationError, "privilege escalation"):
            validate_registrations([escalation, *registrations[1:]])

    def test_optional_failure_quarantines_only_one_consumer(self) -> None:
        item = build_unified_observatory.default_registrations(mode="dynamic")[5]
        failed = quarantine(item, RuntimeError("provider unavailable"))
        self.assertEqual(failed.status, "unavailable")
        self.assertIn("RuntimeError", failed.reason or "")
        self.assertEqual(item.status, "available")
        required = replace(item, required=True, failure_policy="fail-shell")
        with self.assertRaises(RegistrationError):
            quarantine(required, RuntimeError("base docs failed"))

    def test_static_shell_has_navigation_but_no_dynamic_control_script(self) -> None:
        base = (
            '<!doctype html><html><head><style></style></head><body>'
            '<header><div class="rightgrp"></div></header><div class="app"><aside class="sidebar">'
            '<div class="nav-top"></div></aside><main class="content">'
            '<article class="page" id="dashboard"></article></main><aside class="toc" id="toc"></aside></div>'
            '</body></html>'
        )
        page = inject_unified_shell(
            base, build_unified_observatory.default_registrations(mode="static"),
            mode="static",
        )
        self.assertIn('data-unified-navigation', page)
        self.assertEqual(page.count('<aside class="sidebar" data-unified-sidebar'), 1)
        self.assertEqual(page.count('data-sidebar-scroll-container'), 1)
        self.assertEqual(page.count('data-project-document-tree'), 1)
        self.assertLess(page.index('data-unified-navigation'), page.index('data-project-document-tree'))
        self.assertIn('data-mode="static"', page)
        self.assertIn("无服务、无 cookie、无控制能力", page)
        self.assertNotIn("/api/v1/shell/stop", page)
        self.assertNotIn("Set-Cookie", page)
        self.assertIn("@media(max-width:820px)", page)


class UnifiedRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="orrery-unified-tests-")
        root = Path(cls.temporary.name)
        cls.identity = FakeIdentity(root)
        cls.logger = logging.getLogger("orrery-unified-tests")
        cls.logger.handlers.clear()
        cls.logger.addHandler(logging.FileHandler(cls.identity.log_path, encoding="utf-8"))
        cls.logger.setLevel(logging.INFO)
        synthetic_graph = build_unified_observatory.build_workstream_relation_graph.synthetic_browser_provider()
        with mock.patch.object(
            build_unified_observatory.build_workstream_relation_graph,
            "core_relation_provider",
            return_value=synthetic_graph,
        ):
            page, _stats, registrations, authority, graph_payload = build_unified_observatory.render_unified_site(
                ROOT, mode="dynamic",
            )
        cls.rendered_page = page
        state = serve_orrery.UnifiedState(
            page=page, registrations=registrations, authority_status=authority,
            graph_provider_payload=graph_payload,
            identity=cls.identity, logger=cls.logger,
        )
        cls.server = serve_orrery.UnifiedServer(("127.0.0.1", 0), state)
        cls.port = int(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        for handler in cls.logger.handlers[:]:
            handler.close()
            cls.logger.removeHandler(handler)
        cls.temporary.cleanup()

    @classmethod
    def request(cls, method: str, path: str, *, body: dict | None = None, cookie: str | None = None, origin: bool = False, host: str | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", cls.port, timeout=10)
        headers = {"Accept": "application/json", "Host": host or f"127.0.0.1:{cls.port}"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        if origin:
            headers["Origin"] = f"http://127.0.0.1:{cls.port}"
            headers["Sec-Fetch-Site"] = "same-origin"
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        result = response.status, dict(response.getheaders()), raw
        connection.close()
        return result

    def cookie(self) -> str:
        status, headers, _body = self.request("GET", "/")
        self.assertEqual(status, 200)
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_one_visible_url_composes_real_consumers_and_existing_docsite_style(self) -> None:
        status, _headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        for marker in (
            'id="dashboard"', 'id="authority"', 'id="personal-observatory"',
            'id="team-observatory"', 'id="workstream-relation-graph"',
            'id="workspace-maintenance"', 'id="q"', 'id="qa-panel"',
        ):
            self.assertIn(marker, text)
        self.assertIn("--bg:#0f1115", text)
        self.assertEqual(text.count('<aside class="sidebar"'), 1)
        self.assertEqual(text.count('data-sidebar-scroll-container'), 1)
        self.assertEqual(text.count('data-project-document-tree'), 1)
        self.assertNotIn('.uo-doc-tree{overflow', text)
        self.assertIn("data-nav-identity=\"overview\"", text)
        targets = {"overview": "overview", "personal": "personal-observatory", "team": "team-observatory", "workstreams": "workstream-relation-graph", "maintenance": "workspace-maintenance"}
        for identity, label in {
            "overview": "项目总览", "personal": "个人工作台", "team": "团队协作",
            "workstreams": "任务关系", "maintenance": "工作区维护",
        }.items():
            self.assertEqual(text.count(f'data-nav-identity="{identity}"'), 1)
            self.assertEqual(text.count(f'data-target="{targets[identity]}"'), 1)
            self.assertIn(label, text)
        for obsolete in ("Personal Observatory", "Team Observatory", "Workstream Graph", "Workspace Maintenance", "Stop Orrery"):
            self.assertNotIn(f'<span class="lbl">{obsolete}</span>', text)
        self.assertIn("关闭 Orrery 服务", text)
        self.assertIn("<title>Orrery · 项目观测台</title>", text)
        self.assertIn("文档观测台 · 源自 Markdown", text)
        self.assertNotIn('<header class="top"><h1>Orrery · Documentation', text)
        self.assertNotIn("doc viewer · 源自 markdown", text)
        self.assertNotIn("beforeunload", text)
        self.assertNotIn("unload", text)
        self.assertIn("/api/v1/team", text)
        self.assertIn('data-maintenance-refresh-path="/refresh"', text)
        self.assertIn('data-maintenance-remove-path="/remove-worktree"', text)
        self.assertIn('data-maintenance-reload-after-action="false"', text)
        maintenance_start = text.index('id="workspace-maintenance"')
        maintenance_header_end = text.index('</header>', maintenance_start)
        self.assertLess(text.index('data-maintenance-scan', maintenance_start), maintenance_header_end)
        self.assertNotIn('<div class="mo-actions">', text[maintenance_start:])
        self.assertIn('>刷新工作区状态</button>', text[maintenance_start:])
        self.assertIn('data-maintenance-page-size="8"', text[maintenance_start:])
        self.assertIn('<summary>技术策略详情</summary>', text[maintenance_start:])
        ask = next(
            item for item in self.server.state.registrations
            if item.consumer_id == "ask-docs"
        )
        self.assertEqual(ask.status, "unavailable")
        self.assertIn("尚未安全启用", ask.reason or "")
        production_source = (
            (ROOT / "scripts/docsite/build_unified_observatory.py").read_text(encoding="utf-8")
            + (ROOT / "scripts/docsite/serve_orrery.py").read_text(encoding="utf-8")
        )
        self.assertNotIn("experiments/unified-observatory-shell", production_source)

        status, _headers, body = self.request("GET", "/api/v1/health")
        health = json.loads(body)
        self.assertEqual(status, 200)
        self.assertTrue(health["single_visible_url"])
        self.assertEqual(health["public_listener"], "127.0.0.1")

    def test_host_origin_cookie_unknown_api_and_token_boundaries(self) -> None:
        cookie = self.cookie()
        status, _headers, _body = self.request(
            "GET", "/api/v1/health", host="attacker.example"
        )
        self.assertEqual(status, 421)
        status, _headers, _body = self.request(
            "POST", "/api/v1/maintenance/refresh", body={}, cookie=cookie
        )
        self.assertEqual(status, 403)
        status, _headers, _body = self.request(
            "POST", "/api/v1/maintenance/refresh", body={}, origin=True
        )
        self.assertEqual(status, 403)
        status, _headers, _body = self.request("GET", "/api/v1/not-real")
        self.assertEqual(status, 404)
        status, _headers, _body = self.request(
            "POST", "/api/v1/ai/settings", body={}, cookie=cookie, origin=True
        )
        self.assertEqual(status, 403)  # legacy per-start settings token remains required

    def test_team_opt_in_authority_ai_and_maintenance_do_not_escalate(self) -> None:
        before = self.server.state.team.public_status()
        status, _headers, body = self.request("GET", "/api/v1/team/status")
        team = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(team["config"].get("enabled"), before["config"].get("enabled"))
        self.assertFalse(team["execution_capability"])
        self.assertEqual(team["privacy"], "metadata-only")

        status, _headers, body = self.request("GET", "/api/v1/authority/status")
        authority = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(authority["selection"]["active_consumer"], "legacy")
        self.assertFalse(authority["selection"]["production_behavior_switched"])
        self.assertFalse(authority["guarantees"]["ai_may_select"])

        self.assertIn("window.confirm('只删除工作区，保留分支和提交。确认移除这个工作区？')", self.rendered_page)
        cookie = self.cookie()
        status, _headers, _body = self.request(
            "POST", "/api/v1/maintenance/remove-worktree", body={},
            cookie=cookie, origin=True,
        )
        self.assertEqual(status, 400)
        with mock.patch.object(
            self.server.state.team,
            "perform",
            return_value={"maintenance": {"status": "idle"}},
        ) as perform:
            status, _headers, _body = self.request(
                "POST", "/api/v1/maintenance/refresh", body={},
                cookie=cookie, origin=True,
            )
        self.assertEqual(status, 200)
        perform.assert_called_once_with(
            "maintenance/scan", {}, refresh_legacy_page=False,
        )

    def test_capabilities_search_and_unavailable_state_are_bounded(self) -> None:
        status, _headers, body = self.request("GET", "/api/v1/capabilities")
        capabilities = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(capabilities["consumers"]), 8)
        self.assertNotIn(str(ROOT), body.decode("utf-8"))
        self.assertTrue(all(item["status"] in {"available", "unavailable"} for item in capabilities["consumers"]))
        status, _headers, body = self.request("GET", "/api/v1/docs/search?q=Unified%20Observatory")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["bounded"])
        expected_hash = self.server.state.graph_provider_payload["graph"]["graph_hash"]
        with mock.patch("project_orrery_core.workstream_relations.build_relation_graph", side_effect=AssertionError("request-time graph recomputation")):
            status, _headers, body = self.request("GET", "/api/v1/workstreams/graph")
        value = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(value["dynamic_delivery"], "startup-cached-projection")
        self.assertEqual(value["graph"]["graph_hash"], expected_hash)

    def test_close_reclaims_owned_state_and_bound_port(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-unified-close-") as temporary:
            identity = FakeIdentity(Path(temporary))
            logger = logging.getLogger("orrery-unified-close-test")
            logger.handlers.clear()
            logger.addHandler(logging.NullHandler())
            state = serve_orrery.UnifiedState(
                page=self.rendered_page,
                registrations=self.server.state.registrations,
                authority_status=self.server.state.authority_status,
                graph_provider_payload=self.server.state.graph_provider_payload,
                identity=identity,
                logger=logger,
            )
            server = serve_orrery.UnifiedServer(("127.0.0.1", 0), state)
            port = int(server.server_address[1])
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("GET", "/", headers={"Host": f"127.0.0.1:{port}"})
                response = connection.getresponse()
                response.read()
                cookie = dict(response.getheaders())["Set-Cookie"].split(";", 1)[0]
                connection.close()
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request(
                    "POST", "/api/v1/shell/stop", body=b"{}",
                    headers={
                        "Host": f"127.0.0.1:{port}", "Origin": f"http://127.0.0.1:{port}",
                        "Sec-Fetch-Site": "same-origin", "Cookie": cookie,
                        "Content-Type": "application/json", "Accept": "application/json",
                    },
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 202)
                self.assertEqual(json.loads(response.read()), {"status": "stopping"})
                connection.close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                self.assertTrue(identity.cleaned)
                with self.assertRaises(OSError):
                    socket.create_connection(("127.0.0.1", port), timeout=0.5)
            finally:
                if thread.is_alive():
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)


class UnifiedLifecycleAndLauncherTests(unittest.TestCase):
    def test_stale_identity_recovers_but_live_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-unified-identity-") as temporary:
            root = Path(temporary)
            identity = serve_orrery.RuntimeIdentity()
            identity.root = root
            identity.marker = root / "runtime.json"
            identity.log_path = root / "unified.log"
            identity.marker.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
            identity.recover()
            self.assertFalse(identity.marker.exists())
            if os.name == "nt":
                exited = subprocess.Popen([sys.executable, "-c", "pass"])
                self.assertEqual(exited.wait(timeout=10), 0)
                identity.marker.write_text(
                    json.dumps({"pid": exited.pid}), encoding="utf-8"
                )
                identity.recover()
                self.assertFalse(identity.marker.exists())
            identity.marker.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "already running"):
                identity.recover()

    def test_headless_launcher_console_debug_and_legacy_rollback_are_explicit(self) -> None:
        vbs = (ROOT / "Start Orrery.vbs").read_text(encoding="utf-8")
        batch = (ROOT / "start-orrery.bat").read_text(encoding="utf-8")
        legacy = (ROOT / "start-docsite.bat").read_text(encoding="utf-8")
        self.assertIn("pythonw.exe", vbs)
        self.assertIn("shell.Run command, 0, False", vbs)
        self.assertIn('if /I "%~1"=="--console"', batch)
        self.assertIn("serve_orrery.py\" --console", batch)
        self.assertIn("scripts\\docsite\\serve.py", legacy)
        with mock.patch.object(serve_orrery, "_legacy", return_value=7) as rollback:
            self.assertEqual(serve_orrery.main(["--legacy", "--no-browser"]), 7)
        rollback.assert_called_once_with(False, True)


if __name__ == "__main__":
    unittest.main()
