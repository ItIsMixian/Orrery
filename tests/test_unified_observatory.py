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
from project_orrery_core import subprocess_policy  # noqa: E402
from project_orrery_observatory.unified_observatory import (  # noqa: E402
    ConsumerRegistration,
    RegistrationError,
    capability_document,
    inject_unified_shell,
    quarantine,
    validate_registrations,
)
from project_orrery_observatory.personal_observatory import inject_personal_observatory  # noqa: E402
from project_orrery_observatory.relation_inbox import RELATION_INBOX_JS, inject_relation_inbox  # noqa: E402
from project_orrery_observatory.team_observatory import inject_team_observatory  # noqa: E402


class FakeIdentity:
    def __init__(self, root: Path):
        self.root = root
        self.log_path = root / "unified.log"
        self.log_path.write_text("test runtime\n", encoding="utf-8")
        self.cleaned = False

    def cleanup(self) -> None:
        self.cleaned = True


def _bounded_docsite() -> tuple[str, dict, None]:
    """Small composition fixture; doc rendering has separate owner tests."""
    page = (
        '<!doctype html><html><head><title>Orrery · Documentation</title>'
        '<style>:root{--bg:#0f1115}.app{display:flex}</style></head><body>'
        '<header class="top"><h1>Orrery · Documentation</h1>'
        '<span class="sub">doc viewer · 源自 markdown</span><div class="rightgrp"></div></header>'
        '<div class="app"><aside class="sidebar"><div class="nav-top"></div>'
        '<div class="nav-group"><a class="nav-item" data-target="trends">'
        '<span class="dot proposed"></span><span class="lbl">🔭 路线与趋势</span></a></div>'
        '<div class="doc-tree"><a data-target="dashboard">AGENTS</a></div></aside>'
        '<main class="content"><article class="page" id="dashboard">authoritative docs</article>'
        '</main><aside class="toc" id="toc"></aside></div><input id="q"><div id="qa-panel"></div></body></html>'
    )
    return page, {"adrs": 0, "states": 0, "subs": 0, "documents": 1}, None


def _bounded_personal_site(*_args, **_kwargs):
    from project_orrery_observatory.personal_observatory import (
        inject_personal_observatory,
        unavailable_personal_observatory_projection,
    )

    page, stats, authority = _bounded_docsite()
    projection = unavailable_personal_observatory_projection(RuntimeError("bounded fixture"))
    projection["status"] = "ready"
    projection.pop("error", None)
    projection["maintenance"].update({
        "status": "ready",
        "control_available": True,
        "api_base": "/api/v1/maintenance",
        "refresh_path": "/refresh",
        "remove_path": "/remove-worktree",
        "reload_after_action": False,
    })
    return inject_personal_observatory(page, projection), stats, authority, projection


class UnifiedRegistrationTests(unittest.TestCase):
    def test_versioned_registration_and_capability_discovery_are_sanitized(self) -> None:
        registrations = build_unified_observatory.default_registrations(mode="dynamic")
        self.assertEqual(len(registrations), 9)
        document = capability_document(registrations, mode="dynamic")
        self.assertEqual(document["contract_type"], "unified-observatory-shell-v1")
        self.assertTrue(document["single_visible_url"])
        self.assertFalse(document["writes_author_documents"])
        encoded = json.dumps(document)
        self.assertNotIn(str(ROOT), encoded)
        self.assertNotIn("api_key", encoded.lower())
        self.assertEqual(
            {item["navigation"]["identity"] for item in document["consumers"]},
            {"overview", "docs", "ask", "authority", "personal", "team", "workstreams", "maintenance", "trends"},
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
        self.assertNotIn('data-nav-identity="ask"', page)
        self.assertNotIn('data-nav-identity="authority"', page)
        self.assertEqual(page.count('data-nav-identity="trends"'), 1)
        self.assertIn('data-uo-help-panel role="dialog"', page)
        self.assertIn('data-uo-help-close aria-label="关闭帮助与系统状态"', page)
        self.assertIn('aria-expanded="false">? 帮助</button>', page)
        self.assertIn("prefers-reduced-motion:reduce", page)
        self.assertIn("left:0;right:0;top:var(--hh);bottom:0;width:100vw;max-width:none;box-sizing:border-box", page)

        page, _stats, _authority = _bounded_docsite()
        projection = {
            "contract_type": "orrery-active-task-projection-v1",
            "captured_at": "2026-08-31T00:00:00Z",
            "counts": {"current": 0, "history": 0, "refresh_needed": 0, "registry_worktrees": 1},
            "tasks": [],
            "maintenance": {
                "status": "ready",
                "control_available": True,
                "api_base": "/api/v1/maintenance",
                "refresh_path": "/refresh",
                "remove_path": "/remove-worktree",
                "reload_after_action": False,
                "queue": [],
                "authorizations": [],
                "receipts": [],
                "protected_reasons": {},
            },
        }
        page = inject_personal_observatory(page, projection)
        page = inject_team_observatory(page, api_base="/api/v1/team", dynamic_control=True)
        page = inject_relation_inbox(
            page,
            {
                "pending_proposals": [], "effective_relations": [], "stale_confirmations": [],
                "writes_performed": False, "network_performed": False,
                "local_actions_require_same_origin_cookie": True, "central_request_only": True,
            },
            dynamic=True,
        )

        self.assertEqual(page.count('<section class="ri-shell" data-relation-inbox'), 2)
        personal_at = page.index('id="personal-observatory"')
        maintenance_at = page.index('id="workspace-maintenance"')
        team_at = page.index('id="team-observatory"')
        first_inbox = page.index('<section class="ri-shell" data-relation-inbox')
        second_inbox = page.index('<section class="ri-shell" data-relation-inbox', first_inbox + 1)
        self.assertLess(personal_at, first_inbox)
        self.assertLess(first_inbox, maintenance_at)
        self.assertLess(team_at, second_inbox)
        self.assertIn('data-request-only="true"', page[second_inbox:])
        self.assertIn("canAccept=p.relation_type!=='derived_from'", RELATION_INBOX_JS)
        self.assertIn("canChangeGate=p.relation_type==='depends_on'", RELATION_INBOX_JS)


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
        synthetic_capture = {
            "schema_version": 2,
            "privacy": {"prompt": False, "answer": False, "source": False, "diff": False, "credentials": False},
            "pending_proposals": [
                {
                    "current": {
                        "proposal_id": "proposal-a4-a3",
                        "revision": 1,
                        "relation_type": "depends_on",
                        "source_workstream_id": "a4",
                        "target_workstream_id": "a3",
                        "required_for": "integration",
                        "consequence": "A4 在集成前需要核对 A3 的权威边界。",
                        "rationale": "显式任务系列 predecessor 修复建议。",
                        "evidence": [{"category": "git", "ref": "bounded:a4-a3", "fact_scope": "candidate"}],
                    },
                    "local_confirmation": {"allowed": True, "read_only": False, "writes_performed": False},
                },
                {
                    "current": {
                        "proposal_id": "proposal-ci7-ci6",
                        "revision": 1,
                        "relation_type": "depends_on",
                        "source_workstream_id": "ci7",
                        "target_workstream_id": "ci6",
                        "required_for": "integration",
                        "consequence": "CI7 在集成前需要核对 CI6 的检查结果。",
                        "rationale": "显式任务系列 predecessor 修复建议。",
                        "evidence": [{"category": "git", "ref": "bounded:ci7-ci6", "fact_scope": "candidate"}],
                    },
                    "local_confirmation": {"allowed": False, "read_only": True, "writes_performed": False},
                },
            ],
            "effective_relations": [],
            "stale_confirmations": [],
            "writes_performed": False,
            "network_performed": False,
            "local_actions_require_same_origin_cookie": True,
            "central_request_only": True,
        }
        with (
            mock.patch.object(
                build_unified_observatory.build_personal_observatory,
                "render_personal_site",
                side_effect=_bounded_personal_site,
            ),
            mock.patch.object(
                build_unified_observatory.build_workstream_relation_graph,
                "core_relation_provider",
                return_value=synthetic_graph,
            ),
            mock.patch.object(
                build_unified_observatory,
                "relation_capture_payload",
                return_value=synthetic_capture,
            ),
        ):
            page, _stats, registrations, authority, graph_payload, fact_rules_projection = build_unified_observatory.render_unified_site(
                ROOT, mode="dynamic",
            )
        cls.rendered_page = page
        state = serve_orrery.UnifiedState(
            page=page, registrations=registrations, authority_status=authority,
            graph_provider_payload=graph_payload,
            fact_rules_projection=fact_rules_projection,
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
            'id="dashboard"', 'id="personal-observatory"',
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
        self.assertNotIn('data-nav-identity="authority"', text)
        self.assertNotIn('data-nav-identity="ask"', text)
        self.assertNotIn('data-nav-identity="operating-rules"', text)
        self.assertEqual(text.count('id="qa-fab"'), 1)
        ask_label = '<p class="uo-ask-note" data-ask-docs-label><strong>问文档</strong> · 入口位于右下角</p>'
        self.assertEqual(text.count(ask_label), 1)
        self.assertNotIn('<button class="uo-ask-note"', text)
        self.assertNotIn('<a class="uo-ask-note"', text)
        self.assertEqual(text.count('data-uo-help-panel'), 2)  # CSS/JS selector plus the one element
        self.assertEqual(text.count('<section class="uo-help-panel"'), 1)
        self.assertIn('role="dialog" aria-modal="false"', text)
        self.assertIn('data-uo-help-close aria-label="关闭帮助与系统状态"', text)
        self.assertIn("事实与规则", text)
        self.assertIn("项目原则", text)
        self.assertIn("Orrery 工作规则", text)
        self.assertIn("事实解释状态", text)
        self.assertIn("来源：项目文档", text)
        self.assertIn("来源：工具版本", text)
        self.assertNotIn("编辑规则", text)
        self.assertNotIn("批准规则", text)
        self.assertNotIn("启用规则", text)
        targets = {"overview": "overview", "docs": "dashboard", "personal": "personal-observatory", "team": "team-observatory", "workstreams": "workstream-relation-graph", "maintenance": "workspace-maintenance", "trends": "trends"}
        for identity, label in {
            "overview": "项目总览", "docs": "文档与搜索", "personal": "个人工作台",
            "team": "团队协作", "workstreams": "任务关系",
            "maintenance": "工作区维护", "trends": "路线与趋势",
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
        self.assertEqual(text.count('<section class="ri-shell" data-relation-inbox'), 2)
        self.assertIn('data-request-only="true"', text)
        self.assertIn("关系待确认", text)
        graph_start = text.index('id="workstream-relation-graph"')
        graph_end = text.index("</article>", graph_start)
        self.assertNotIn("/relations/accept", text[graph_start:graph_end])
        self.assertIn('data-maintenance-refresh-path="/refresh"', text)
        self.assertIn('data-maintenance-remove-path="/remove-worktree"', text)
        self.assertIn('data-maintenance-reload-after-action="false"', text)
        rail_start = text.index('data-unified-navigation')
        tree_start = text.index('data-project-document-tree')
        for identity in ("overview", "docs", "personal", "team", "workstreams", "maintenance", "trends"):
            self.assertLess(text.index(f'data-nav-identity="{identity}"'), tree_start)
        self.assertLess(rail_start, tree_start)
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

        status, _headers, body = self.request("GET", "/api/v1/workstreams/relations")
        self.assertEqual(status, 200)
        relation_capture = json.loads(body)
        self.assertTrue(relation_capture["privacy"]["prompt"] is False)
        self.assertTrue(relation_capture["local_actions_require_same_origin_cookie"])
        status, _headers, _body = self.request(
            "POST", "/api/v1/workstreams/relations/accept",
            body={"proposal_id": "not-real", "expected_revision": 1},
        )
        self.assertEqual(status, 403)
        status, _headers, _body = self.request(
            "POST", "/api/v1/workstreams/relations/accept",
            body={"proposal_id": "not-real", "expected_revision": 1},
            cookie=cookie, origin=True,
        )
        self.assertEqual(status, 400)

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

        status, _headers, body = self.request("GET", "/api/v1/authority/operating-rules")
        facts_rules = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(facts_rules["contract_type"], "authority-facts-and-rules-projection-v1")
        self.assertTrue(facts_rules["read_only"])
        self.assertFalse(facts_rules["creates_project_facts"])
        self.assertFalse(facts_rules["writes_target_project"])
        self.assertFalse(facts_rules["layer_boundary"]["merged"])
        rules = facts_rules["orrery_operating_rules"]
        if rules["status"] == "available":
            self.assertEqual(rules["inventory_id"], "orrery-operating-rules-v1")
        else:
            self.assertTrue(rules["read_only"])
            self.assertTrue(rules["reason"])

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
        self.assertEqual(len(capabilities["consumers"]), 9)
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

        def projection(revision: str, workstream_id: str):
            return {
                "status": "ready", "contract_type": "orrery-active-task-projection-v1",
                "captured_at": "2026-08-30T13:00:00Z", "revision": revision,
                "counts": {"registry_worktrees": 1, "current": 1, "history": 0, "primary": 0, "refresh_needed": 1},
                "tasks": [{
                    "task_id": revision, "workstream_id": workstream_id,
                    "task_code": workstream_id.split("-", 1)[0], "display_name": workstream_id,
                    "branch": "codex/fixture", "phase": "implementing",
                    "runtime_condition": "active", "primary_subsystem_id": "documentation-system",
                    "affected_subsystem_ids": [], "evidence_freshness": "refresh-needed",
                    "workspace_state": "registered-active", "category": "current",
                    "technical_detail_available": False,
                }],
                "maintenance": {}, "read_boundary": {"startup_full_scan": False},
            }
        with mock.patch.object(
            serve_orrery, "build_active_task_projection",
            side_effect=[projection("r1", "A4.1-first"), projection("r2", "NEW-second")],
        ):
            first_status, _headers, first_body = self.request("GET", "/api/v1/personal/tasks")
            second_status, _headers, second_body = self.request("GET", "/api/v1/personal/tasks")
        first, second = json.loads(first_body), json.loads(second_body)
        self.assertEqual((first_status, second_status), (200, 200))
        self.assertEqual(first["projection"]["revision"], "r1")
        self.assertEqual(second["projection"]["revision"], "r2")
        self.assertIn("NEW-second", second["fragment"])
        self.assertNotIn(str(ROOT), second_body.decode("utf-8"))

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
                fact_rules_projection=self.server.state.fact_rules_projection,
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
    def test_production_child_policy_is_windows_only_and_explicitly_disableable(self) -> None:
        with mock.patch.object(subprocess_policy.os, "name", "nt"):
            self.assertEqual(
                subprocess_policy.no_window_options(),
                {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)},
            )
            self.assertEqual(subprocess_policy.no_window_options(enabled=False), {})
        with mock.patch.object(subprocess_policy.os, "name", "posix"):
            self.assertEqual(subprocess_policy.no_window_options(), {})

    def test_unified_startup_and_refresh_git_sites_use_shared_child_policy(self) -> None:
        required_counts = {
            "packages/project-orrery-core/src/project_orrery_core/collaboration.py": 5,
            "packages/project-orrery-core/src/project_orrery_core/review.py": 1,
            "packages/project-orrery-core/src/project_orrery_core/team.py": 1,
            "packages/project-orrery-core/src/project_orrery_core/workstream_program_hierarchy.py": 1,
            "packages/project-orrery-core/src/project_orrery_core/workstream_relations.py": 1,
            "packages/project-orrery-core/src/project_orrery_core/workstream_relation_capture.py": 1,
            "packages/project-orrery-observatory/src/project_orrery_observatory/active_task_projection.py": 1,
            "scripts/docsite/docsite_insights.py": 1,
            "scripts/docsite/serve_orrery.py": 1,
        }
        for relative, expected in required_counts.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(source.count("**no_window_options()"), expected, relative)
        self.assertIn("**no_window_options(enabled=not console)", (ROOT / "scripts/docsite/serve_orrery.py").read_text(encoding="utf-8"))

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

    def test_live_healthy_identity_reuses_exact_loopback_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-unified-reuse-") as temporary:
            root = Path(temporary)
            identity = serve_orrery.RuntimeIdentity()
            identity.root = root
            identity.marker = root / "runtime.json"
            identity.log_path = root / "unified.log"
            port = 18765
            identity.marker.write_text(json.dumps({
                "schema_version": 1,
                "contract_type": "unified-observatory-runtime-identity-v1",
                "instance_id": "existing-instance",
                "pid": os.getpid(),
                "host": "127.0.0.1",
                "port": port,
                "url": f"http://127.0.0.1:{port}/",
                "ready": True,
            }), encoding="utf-8")
            response = mock.MagicMock()
            response.status = 200
            response.read.return_value = json.dumps({
                "contract_type": "unified-observatory-health-v1",
                "status": "ready",
                "single_visible_url": True,
            }).encode("utf-8")
            response.__enter__.return_value = response
            with mock.patch.object(serve_orrery, "urlopen", return_value=response) as opened:
                self.assertEqual(identity.reusable_url(), f"http://127.0.0.1:{port}/")
            self.assertEqual(opened.call_args.args[0].full_url, f"http://127.0.0.1:{port}/api/v1/health")

            with mock.patch.object(serve_orrery, "urlopen", side_effect=OSError("offline")):
                with self.assertRaisesRegex(RuntimeError, "unhealthy"):
                    identity.reusable_url()
            self.assertTrue(identity.marker.exists())

    def test_normal_main_reuses_before_render_and_console_legacy_keeps_console(self) -> None:
        identity = mock.Mock()
        identity.reusable_url.return_value = "http://127.0.0.1:18765/"
        logger = mock.Mock()
        with (
            mock.patch.object(serve_orrery, "RuntimeIdentity", return_value=identity),
            mock.patch.object(serve_orrery, "_logger", return_value=logger),
            mock.patch.object(serve_orrery.webbrowser, "open") as browser,
            mock.patch.object(
                serve_orrery.build_unified_observatory, "render_unified_site",
                side_effect=AssertionError("healthy reuse must precede construction"),
            ),
            mock.patch.object(serve_orrery.legacy_serve, "_stop_managed_broker"),
        ):
            self.assertEqual(serve_orrery.main([]), 0)
        browser.assert_called_once_with("http://127.0.0.1:18765/#overview")
        identity.recover.assert_not_called()
        identity.cleanup.assert_called_once_with()

        with mock.patch.object(serve_orrery.subprocess, "call", return_value=0) as child:
            self.assertEqual(serve_orrery._legacy(True, True), 0)
        self.assertNotIn("creationflags", child.call_args.kwargs)

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
