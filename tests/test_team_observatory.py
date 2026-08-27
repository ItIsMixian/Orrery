from __future__ import annotations

import http.client
import importlib.util
import json
import sys
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
    ROOT / "scripts" / "docsite",
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from project_orrery_core.team import load_team_config, team_private_dir
from project_orrery_observatory.team_observatory import (
    TEAM_OBSERVATORY_CSS,
    inject_team_observatory,
    render_team_observatory_panel,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture


def _load_server_module():
    path = ROOT / "scripts" / "docsite" / "serve_team_observatory.py"
    spec = importlib.util.spec_from_file_location("w5b_team_server", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_personal_page() -> str:
    return (
        "<html><head><style>body{color:var(--fg)}</style></head><body>"
        '<aside><div class="nav-group"><a class="nav-item" data-target="personal-observatory">'
        '<span class="dot state"></span><span class="lbl">Personal Observatory</span></a></div></aside>'
        '<main><article class="page wide" id="personal-observatory"></article>'
        '</main><aside class="toc" id="toc"></aside></body></html>'
    )


class TeamObservatoryTests(unittest.TestCase):
    def test_team_page_is_a_sibling_with_graphical_zero_network_onboarding(self):
        page = inject_team_observatory(_base_personal_page())
        self.assertIn('data-target="team-observatory"', page)
        self.assertIn('<div class="nav-group expanded">', page)
        self.assertIn('<article class="page wide" id="team-observatory"', page)
        self.assertIn("Personal Mode 正在保护默认体验", page)
        self.assertIn("在本机启用 Team Mode", page)
        self.assertIn("只共享状态 · 请求需本机确认", page)
        self.assertIn("现在的情况", page)
        self.assertIn("建议操作", page)
        self.assertIn("成员与工作任务", page)
        self.assertIn("待处理请求", page)
        self.assertIn("已处理请求（0）", page)
        self.assertIn("本机控制与技术诊断", page)
        self.assertIn("确认只记录决定，不会自动执行", page)
        self.assertIn("开始共享项目状态", page)
        self.assertIn("采集本机状态", page)
        self.assertIn("创建测试请求", page)
        self.assertIn("在线状态广播已关闭，因此“状态已过期／未知”是预期结果", page)
        self.assertIn("检测到另一个本机协作服务登记，当前页面不能直接控制它", page)
        self.assertIn("其他本机服务占用中", page)
        self.assertIn("可能存在其他 Team 页面或失效的本机登记", page)
        self.assertNotIn("Start Coordinator", page)
        self.assertNotIn("Create local request", page)
        self.assertIn("@media(max-width:640px)", TEAM_OBSERVATORY_CSS)
        self.assertNotIn("<input", page)
        self.assertNotIn("contenteditable", page)
        self.assertNotIn("allow_lan_bind", page)
        self.assertLess(
            page.index('id="personal-observatory"'),
            page.index('id="team-observatory"'),
        )

    def test_root_entry_refuses_another_project(self):
        module = _load_server_module()
        with CollaborationGitFixture() as fixture:
            with self.assertRaisesRegex(ValueError, "root-only"):
                module.create_server(fixture.repository, "<html></html>")

    def test_loopback_ui_controls_core_team_projection_and_redacts_secrets(self):
        module = _load_server_module()
        with CollaborationGitFixture() as fixture:
            state = module.TeamUIState(fixture.worktree_a, inject_team_observatory(_base_personal_page()))
            server = module.TeamUIServer(("127.0.0.1", 0), state)
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
            thread.start()
            port = server.server_address[1]
            origin = f"http://127.0.0.1:{port}"
            def request(method: str, path: str, body=None, *, cookie=None, origin_header=True, host=None):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                headers = {"Accept": "application/json", "Host": host or f"127.0.0.1:{port}"}
                if cookie:
                    headers["Cookie"] = cookie
                if method == "POST":
                    headers["Content-Type"] = "application/json"
                    if origin_header:
                        headers["Origin"] = origin
                    payload = json.dumps({} if body is None else body).encode("utf-8")
                else:
                    payload = None
                connection.request(method, path, body=payload, headers=headers)
                response = connection.getresponse()
                raw = response.read()
                connection.close()
                return response, raw

            try:
                response, page = request("GET", "/team/")
                self.assertEqual(response.status, 200)
                cookie_header = response.getheader("Set-Cookie")
                self.assertIn("HttpOnly", cookie_header)
                self.assertIn("SameSite=Strict", cookie_header)
                cookie = cookie_header.split(";", 1)[0]
                self.assertIn(b"Personal Mode", page)

                response, _raw = request("GET", "/team/api/status")
                self.assertEqual(response.status, 403)

                response, raw = request("GET", "/team/api/status", cookie=cookie)
                disabled = json.loads(raw)
                self.assertEqual(response.status, 200)
                self.assertFalse(disabled["config"]["enabled"])
                self.assertFalse(disabled["coordinator"]["running"])

                response, raw = request("POST", "/team/api/enable", cookie=cookie, origin_header=False)
                self.assertEqual(response.status, 403)
                self.assertNotIn(str(fixture.worktree_a), raw.decode("utf-8"))

                response, raw = request(
                    "POST", "/team/api/enable", cookie=cookie, body={"unexpected": "field"},
                )
                self.assertEqual(response.status, 400)
                self.assertNotIn(str(fixture.worktree_a), raw.decode("utf-8"))
                try:
                    response, _raw = request(
                        "POST", "/team/api/enable", cookie=cookie,
                        body={"unexpected": "x" * (module.UI_BODY_LIMIT + 1)},
                    )
                except ConnectionError:
                    pass  # Windows may reset a connection whose oversized body is intentionally unread.
                else:
                    self.assertEqual(response.status, 400)

                response, raw = request("POST", "/team/api/enable", cookie=cookie)
                enabled = json.loads(raw)
                self.assertEqual(response.status, 200)
                self.assertTrue(enabled["config"]["enabled"])
                self.assertEqual(enabled["config"]["runtime_status"], "team-enabled-stopped")
                self.assertFalse(enabled["coordinator"]["running"])

                response, raw = request("POST", "/team/api/start", cookie=cookie)
                started = json.loads(raw)
                self.assertEqual(response.status, 200)
                self.assertTrue(started["coordinator"]["running"])
                self.assertEqual(started["coordinator"]["bind"], "127.0.0.1")
                self.assertEqual(started["projection"]["contract_type"], "team-read-only-projection")
                self.assertEqual(started["projection"]["authority"], "derived-read-only")
                self.assertFalse(started["projection"]["execution_capability"])

                for action in ("heartbeat", "sharing", "sharing", "capture", "sync"):
                    response, raw = request("POST", f"/team/api/{action}", cookie=cookie)
                    self.assertEqual(response.status, 200, (action, raw))

                response, raw = request("POST", "/team/api/request-create", cookie=cookie)
                first = json.loads(raw)
                self.assertEqual(response.status, 200)
                first_request = first["requests"][0]
                self.assertFalse(first_request["execution_performed"])
                response, raw = request(
                    "POST", "/team/api/request/decision", cookie=cookie,
                    body={"request_id": first_request["request_id"], "decision": "accept"},
                )
                accepted = json.loads(raw)
                self.assertEqual(response.status, 200)
                self.assertEqual(accepted["requests"][0]["status"], "accepted-locally")
                self.assertFalse(accepted["requests"][0]["execution_performed"])

                response, raw = request("POST", "/team/api/maintenance-request", cookie=cookie)
                requested = json.loads(raw)
                self.assertEqual(response.status, 200)
                cleanup_request = next(item for item in requested["requests"] if item["request_kind"] == "cleanup")
                self.assertEqual(cleanup_request["status"], "pending-local-confirmation")
                self.assertFalse(cleanup_request["execution_performed"])

                response, raw = request("POST", "/team/api/request-create", cookie=cookie)
                second = json.loads(raw)
                pending = next(item for item in second["requests"] if item["status"] == "pending-local-confirmation")
                response, raw = request(
                    "POST", "/team/api/request/decision", cookie=cookie,
                    body={"request_id": pending["request_id"], "decision": "reject"},
                )
                rejected = json.loads(raw)
                self.assertEqual(response.status, 200)
                selected = next(item for item in rejected["requests"] if item["request_id"] == pending["request_id"])
                self.assertEqual(selected["status"], "rejected-locally")
                self.assertFalse(selected["execution_performed"])

                serialized = json.dumps(rejected, sort_keys=True).lower()
                private = (team_private_dir(fixture.worktree_a) / "credential.json").read_text(encoding="utf-8")
                member_token = json.loads(private)["token"]
                self.assertNotIn(member_token, serialized)
                self.assertNotIn('"control"', serialized)
                self.assertNotIn('"credential_token"', serialized)
                self.assertNotIn('"api_key"', serialized)

                response, raw = request("POST", "/team/api/stop", cookie=cookie)
                stopped = json.loads(raw)
                self.assertEqual(response.status, 200)
                self.assertFalse(stopped["coordinator"]["running"])
                self.assertTrue(stopped["config"]["enabled"])

                response, _raw = request(
                    "GET", "/team/api/status", cookie=cookie, host=f"evil.example:{port}"
                )
                self.assertEqual(response.status, 403)

                response, raw = request("POST", "/team/api/start", cookie=cookie)
                self.assertEqual(response.status, 200)
                self.assertTrue(json.loads(raw)["coordinator"]["running"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            config = load_team_config(fixture.worktree_a)
            self.assertEqual(config["runtime_status"], "team-enabled-stopped")
            self.assertEqual(config["network_features"], [])


if __name__ == "__main__":
    unittest.main()
