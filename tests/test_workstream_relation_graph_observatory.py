from __future__ import annotations

import copy
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(ROOT / "scripts" / "docsite") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "docsite"))

from project_orrery_observatory import workstream_relation_graph as graph_ui


def _load_builder():
    path = ROOT / "scripts" / "docsite" / "build_workstream_relation_graph.py"
    spec = importlib.util.spec_from_file_location("w7cb_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_page(*, team: bool = False, personal: bool = False) -> str:
    nav = (
        '<a class="nav-item" data-target="trends"><span class="dot proposed"></span>'
        '<span class="lbl">🔭 路线与趋势</span></a>'
    )
    if personal:
        nav += (
            '<a class="nav-item" data-target="personal-observatory"><span class="dot state"></span>'
            '<span class="lbl">Personal Observatory</span></a>'
        )
    if team:
        nav += (
            '<a class="nav-item" data-target="team-observatory"><span class="dot proposed"></span>'
            '<span class="lbl">Team Observatory</span></a>'
        )
    return (
        '<html><head><style>body{color:red}</style></head><body><aside class="sidebar">'
        '<div class="nav-group">' + nav + '</div></aside><main class="content">'
        '<article id="dashboard">legacy</article></main><aside class="toc" id="toc"></aside></body></html>'
    )


class WorkstreamRelationGraphObservatoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = _load_builder()
        cls.provider = cls.builder.synthetic_browser_provider()
        cls.projection = graph_ui.build_relation_graph_projection(cls.provider)

    def test_core_payload_maps_three_lenses_and_independent_axes(self) -> None:
        projection = self.projection
        self.assertEqual(projection["status"], "ready")
        self.assertEqual(projection["authority"], "synthetic-non-authoritative")
        self.assertEqual(projection["graph_contract"], "workstream-relation-graph")
        self.assertEqual(projection["plan_contract"], "workstream-succession-plan")
        self.assertTrue(projection["read_only"])
        self.assertFalse(projection["writes_performed"])
        self.assertFalse(projection["network_performed"])
        self.assertEqual(projection["available_actions"], [])

        nodes = {item["workstream_id"]: item for item in projection["nodes"]}
        self.assertEqual(nodes["waiting-task"]["runtime_condition"], "waiting-for-user")
        self.assertEqual(nodes["waiting-task"]["status"], "inactive")
        self.assertEqual(nodes["blocked-task"]["status"], "blocked")
        self.assertEqual(nodes["failed-task"]["status"], "failed")
        self.assertEqual(nodes["offline-unknown"]["status"], "unknown")
        self.assertFalse(nodes["waiting-task"]["is_active_tip"])
        self.assertFalse(nodes["blocked-task"]["is_active_tip"])
        self.assertFalse(nodes["failed-task"]["is_active_tip"])
        self.assertEqual(
            set(projection["active_tip_workstream_ids"]), {"CI2-late", "W5E"}
        )
        self.assertTrue(all(nodes[item]["runtime_condition"] == "active" for item in projection["active_tip_workstream_ids"]))

        dependencies = [
            item for item in projection["edges"]
            if item["relation_type"] == "depends_on" and item["source_workstream_id"] == "W5E"
        ]
        self.assertEqual({item["target_workstream_id"] for item in dependencies}, {"CI1", "W5D"})
        self.assertTrue(any(item["certainty"] == "proposed" for item in projection["edges"]))
        self.assertTrue(any(item["certainty"] == "stale" for item in projection["edges"]))
        self.assertIn("offline-unknown", projection["unknown_workstream_ids"])
        self.assertGreaterEqual(len(projection["history_candidate_ids"]), 2)

        compare = [item for item in projection["conflicts"] if item["disposition"] == "compare"]
        suppress = [item for item in projection["conflicts"] if item["disposition"] == "suppress"]
        self.assertTrue(any(item["certainty"] == "confirmed" for item in compare))
        self.assertTrue(any(item["certainty"] == "proposed" for item in compare))
        self.assertTrue(suppress)
        safe = next(
            link for node in projection["nodes"] for link in node["source_links"] if link["href"]
        )
        self.assertTrue(safe["href"].startswith("#lib-"))

        panel = graph_ui.render_workstream_relation_graph_panel(projection)
        for token in (
            'data-wg-lens="succession"', 'data-wg-lens="dependency"',
            'data-wg-lens="conflict"', "Accessible relation ledger", "READ ONLY",
            "No apply · undo · close · delete · merge · remote execution",
        ):
            self.assertIn(token, panel)
        self.assertIn("waiting-task", panel)
        self.assertIn("blocked-by-conflict", panel)
        self.assertIn("synthetic-non-authoritative", panel)

    def test_invalid_provider_store_graph_legacy_and_links_fail_closed(self) -> None:
        cases: list[tuple[str, dict, str]] = []
        old_provider = copy.deepcopy(self.provider)
        old_provider["provider_schema_version"] = 0
        cases.append(("provider", old_provider, "unsupported-provider-schema"))
        absent = copy.deepcopy(self.provider)
        absent["relation_root_present"] = False
        cases.append(("store", absent, "relation-store-absent"))
        invalid = copy.deepcopy(self.provider)
        invalid["graph"]["validation"] = {
            "valid": False, "errors": [{"code": "cycle"}], "warnings": []
        }
        cases.append(("graph", invalid, "core-graph-invalid"))
        dangling = copy.deepcopy(self.provider)
        dangling["graph"]["nodes"] = dangling["graph"]["nodes"][:-1]
        cases.append(("node", dangling, "dangling-node"))
        unsafe = copy.deepcopy(self.provider)
        unsafe["graph"]["nodes"][0]["source_links"] = [
            {"kind": "validation", "ref": "https://example.invalid/run"}
        ]
        cases.append(("link", unsafe, "unsafe-source-link"))
        windows_path = copy.deepcopy(self.provider)
        windows_path["graph"]["nodes"][0]["source_links"] = [
            {"kind": "validation", "ref": "C:/private/orrery/worktree.json"}
        ]
        cases.append(("path", windows_path, "unsafe-source-link"))
        legacy = copy.deepcopy(self.provider)
        selected = next(item for item in legacy["graph"]["nodes"] if item["workstream_id"] == "offline-unknown")
        selected["origin"] = "legacy-session-projection"
        cases.append(("legacy", legacy, "legacy-unknown"))

        for label, payload, expected in cases:
            with self.subTest(label=label):
                projection = graph_ui.project_core_relation_graph(lambda payload=payload: payload)
                self.assertEqual(projection["status"], "unavailable")
                self.assertEqual(projection["error"]["code"], expected)
                self.assertEqual(projection["nodes"], [])
                self.assertEqual(projection["edges"], [])
                self.assertEqual(projection["conflicts"], [])
                self.assertEqual(projection["available_actions"], [])

        failed = graph_ui.project_core_relation_graph(
            lambda: (_ for _ in ()).throw(RuntimeError("C:/private/secret prompt body"))
        )
        self.assertEqual(failed["error"]["code"], "core-provider-failure")
        self.assertNotIn("private", json.dumps(failed))
        self.assertNotIn("prompt body", json.dumps(failed))

    def test_missing_real_relation_store_is_zero_write_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp) / "repository"
            repository.mkdir()
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.email", "fixture@example.com"], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.name", "Fixture"], check=True)
            (repository / "README.md").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repository), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-q", "-m", "fixture"], check=True)
            relation_root = repository / ".git" / "orrery" / "workstream-relations"
            before = subprocess.run(
                ["git", "-C", str(repository), "status", "--porcelain=v1"],
                check=True, capture_output=True, text=True,
            ).stdout
            self.assertFalse(relation_root.exists())
            payload = self.builder.core_relation_provider(repository)
            projection = graph_ui.project_core_relation_graph(lambda: payload)
            after = subprocess.run(
                ["git", "-C", str(repository), "status", "--porcelain=v1"],
                check=True, capture_output=True, text=True,
            ).stdout
            self.assertEqual(before, after)
            self.assertFalse(relation_root.exists())
            self.assertEqual(projection["status"], "unavailable")
            self.assertEqual(projection["error"]["code"], "relation-store-absent")

    def test_corrected_w7a_compatibility_payload_preserves_non_active_runtime_states(self) -> None:
        payload = copy.deepcopy(self.builder.synthetic_browser_provider())
        self.assertEqual(payload["authority"], "synthetic-non-authoritative")
        nodes = {
            item["workstream_id"]: item for item in payload["graph"]["nodes"]
        }
        active_tips = set(payload["graph"]["active_tip_workstream_ids"])
        non_active_runtime = {
            "waiting-for-user", "paused", "blocked-by-conflict", "failed"
        }
        observed = {
            item["runtime_condition"] for item in nodes.values()
            if item["runtime_condition"] in non_active_runtime
        }
        self.assertTrue(observed)
        for item in nodes.values():
            if item["runtime_condition"] in non_active_runtime:
                self.assertNotIn(item["workstream_id"], active_tips)
                self.assertNotEqual(item["status"], "active")
        self.assertEqual(payload["graph"]["contract_type"], "workstream-relation-graph")
        self.assertEqual(payload["graph"]["schema_version"], 1)
        self.assertEqual(payload["succession_plan"]["contract_type"], "workstream-succession-plan")
        self.assertEqual(payload["succession_plan"]["schema_version"], 1)

        projection = graph_ui.project_core_relation_graph(lambda: payload)
        self.assertEqual(projection["status"], "ready")
        self.assertTrue(projection["nodes"])

    def test_page_is_keyboard_responsive_read_only_and_has_no_frontend_semantics(self) -> None:
        page = graph_ui.inject_workstream_relation_graph(
            _base_page(team=True, personal=True), self.projection
        )
        self.assertIn('data-target="personal-observatory"', page)
        self.assertIn('data-target="team-observatory"', page)
        self.assertIn('data-target="workstream-relation-graph"', page)
        self.assertIn('id="workstream-relation-graph"', page)
        self.assertIn("@media(max-width:640px)", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".top .sub,.searchwrap{display:none}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-filterbar{grid-template-columns:minmax(0,1fr)}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("@media(prefers-reduced-motion:reduce)", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(":focus-visible", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("ev.key==='Enter'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("ev.key===' '", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("function keyboardActivate", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("fetch(", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("XMLHttpRequest", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("WebSocket", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("subprocess", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("git worktree", graph_ui.WORKSTREAM_GRAPH_JS.lower())
        self.assertNotIn("branch similarity", graph_ui.WORKSTREAM_GRAPH_JS.lower())
        self.assertNotIn("<form", page)
        self.assertNotIn("data-wg-apply", page)
        self.assertNotIn("data-wg-delete", page)
        self.assertNotRegex(page, r'<(script|link)[^>]+https?://')

    def test_root_only_default_off_personal_team_adjacency_and_zero_network(self) -> None:
        sentinel = (_base_page(), {"adrs": 0}, None, None)
        with mock.patch.object(
            self.builder.build_personal_observatory,
            "render_personal_site",
            return_value=sentinel,
        ), mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW", None)
            result = self.builder.render_workstream_relation_graph_site(
                ROOT / "docs", ROOT / "AGENTS.md", ROOT, "Project Orrery"
            )
        self.assertEqual(result, (*sentinel, None))

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "root-only"):
                self.builder.inject_enabled_relation_graph(_base_page(), Path(temp))

        with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), mock.patch.object(
            socket, "create_connection", side_effect=AssertionError("network forbidden")
        ):
            projection = graph_ui.project_core_relation_graph(self.builder.synthetic_browser_provider)
        self.assertEqual(projection["status"], "ready")
        self.assertFalse(projection["network_performed"])

    def test_component_version_and_ci_inventory_include_production_and_prototype(self) -> None:
        component = json.loads(
            (ROOT / "packages" / "project-orrery-observatory" / "src" / "project_orrery_observatory" / "component.json").read_text(encoding="utf-8")
        )
        versions = json.loads((ROOT / "packages" / "component-versions.json").read_text(encoding="utf-8"))
        shards = json.loads((ROOT / "scripts" / "ci" / "test-shards.json").read_text(encoding="utf-8"))
        self.assertEqual(component["version"], "0.1.9")
        self.assertEqual(versions["components"]["observatory"]["version"], "0.1.9")
        selectors = [selector for shard in shards["shards"] for selector in shard["selectors"]]
        self.assertIn("test_workstream_relation_graph_observatory.*", selectors)
        self.assertIn("test_workstream_graph_visual_prototype.*", selectors)
        self.assertNotIn("scripts/docsite/build_workstream_relation_graph.py", component["managed_tools"])


if __name__ == "__main__":
    unittest.main()
