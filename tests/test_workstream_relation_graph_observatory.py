from __future__ import annotations

import copy
import hashlib
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
from project_orrery_core.workstream_relations import build_relation_graph, build_succession_plan


def _rebind(payload: dict) -> dict:
    graph = payload["graph"]
    body = {key: value for key, value in graph.items() if key != "graph_hash"}
    graph["graph_hash"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    payload["succession_plan"] = build_succession_plan(graph)
    return payload


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
            '<span class="lbl">个人工作台</span></a>'
        )
    if team:
        nav += (
            '<a class="nav-item" data-target="team-observatory"><span class="dot proposed"></span>'
            '<span class="lbl">团队协作</span></a>'
        )
    return (
        '<html><head><style>body{color:red}</style></head><body><aside class="sidebar">'
        '<div class="nav-group">' + nav + '</div></aside><main class="content">'
        '<article id="dashboard">legacy</article></main><aside class="toc" id="toc"></aside></body></html>'
    )


def _segment_hits_rect(start: tuple[int, int], end: tuple[int, int], rect: dict) -> bool:
    left, right = rect["x"] + 1, rect["x"] + rect["width"] - 1
    top, bottom = rect["y"] + 1, rect["y"] + rect["height"] - 1
    if start[1] == end[1]:
        low, high = sorted((start[0], end[0]))
        return top <= start[1] <= bottom and max(low, left) <= min(high, right)
    if start[0] == end[0]:
        low, high = sorted((start[1], end[1]))
        return left <= start[0] <= right and max(low, top) <= min(high, bottom)
    raise AssertionError("layout route must be orthogonal")


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
            'data-wg-lens="conflict"', "任务关系列表", "只读",
            "不提供应用、撤销、关闭、删除、合并或远程执行",
        ):
            self.assertIn(token, panel)
        self.assertIn("waiting-task", panel)
        self.assertIn("blocked-by-conflict", panel)
        self.assertIn("synthetic-non-authoritative", panel)

        lens_types = {
            "succession": {"derived_from", "absorbs"},
            "dependency": {"depends_on"},
            "conflict": {"conflict-pair"},
        }
        for lens, allowed in lens_types.items():
            with self.subTest(lens=lens):
                layout = graph_ui.build_readability_layout(projection, lens=lens)
                self.assertTrue(layout["nodes"])
                self.assertTrue(all(item["relation_type"] in allowed for item in layout["edges"]))
                boxes = list(layout["positions"].items())
                for index, (left_id, left) in enumerate(boxes):
                    self.assertGreaterEqual(left["width"], 220)
                    self.assertLessEqual(left["width"], 280)
                    self.assertGreaterEqual(left["height"], 88)
                    for right_id, right in boxes[index + 1:]:
                        separated = (
                            left["x"] + left["width"] <= right["x"]
                            or right["x"] + right["width"] <= left["x"]
                            or left["y"] + left["height"] <= right["y"]
                            or right["y"] + right["height"] <= left["y"]
                        )
                        self.assertTrue(separated, f"overlap: {left_id} / {right_id}")
                edge_by_id = {item["display_edge_id"]: item for item in layout["edges"]}
                for route in layout["routes"]:
                    self.assertTrue(route["has_arrow"])
                    self.assertFalse(route["has_label"])
                    self.assertEqual(
                        route["line_encoding"],
                        {"succession": "solid", "dependency": "dashed", "conflict": "compound"}[lens],
                    )
                    edge = edge_by_id[route["edge_id"]]
                    for node_id, rect in boxes:
                        if node_id in {edge["display_from_id"], edge["display_to_id"]}:
                            continue
                        for start, end in zip(route["points"], route["points"][1:]):
                            self.assertFalse(
                                _segment_hits_rect(start, end, rect),
                                f"edge {route['edge_id']} crosses {node_id}",
                            )

        collapsed = graph_ui.build_readability_layout(projection, lens="succession")
        history_chains = [item for item in collapsed["chains"] if item["history_ids"]]
        self.assertTrue(history_chains)
        chain = history_chains[0]
        cluster = next(item for item in collapsed["nodes"] if item.get("chain_id") == chain["chain_id"])
        self.assertEqual(len(cluster["cluster_ids"]), len(chain["history_ids"]))
        self.assertEqual(cluster["cluster_ids"], chain["history_ids"])
        self.assertEqual(cluster["cluster_first_id"], chain["history_ids"][0])
        self.assertEqual(cluster["cluster_last_id"], chain["history_ids"][-1])
        self.assertEqual(cluster["cluster_tip_id"], chain["tip_id"])
        expanded = graph_ui.build_readability_layout(
            projection, lens="succession", expanded_chain_ids=[chain["chain_id"]]
        )
        self.assertFalse(any(item.get("chain_id") == chain["chain_id"] for item in expanded["nodes"]))
        self.assertTrue(set(chain["history_ids"]).issubset(expanded["visible_fact_ids"]))
        self.assertGreater(len(expanded["visible_fact_ids"]), len(collapsed["visible_fact_ids"]))
        collapse_control = next(
            item for item in expanded["nodes"] if item.get("collapse_chain_id") == chain["chain_id"]
        )
        self.assertEqual(collapse_control["workstream_id"], chain["history_ids"][0])
        self.assertEqual(collapse_control["expanded_history_count"], len(chain["history_ids"]))

        no_dependency = copy.deepcopy(projection)
        no_dependency["edges"] = [
            item for item in no_dependency["edges"] if item["relation_type"] != "depends_on"
        ]
        dependency_empty = graph_ui.build_readability_layout(no_dependency, lens="dependency")
        self.assertEqual(dependency_empty["nodes"], [])
        self.assertEqual(dependency_empty["edges"], [])
        self.assertEqual(dependency_empty["routes"], [])
        self.assertEqual(dependency_empty["lanes"], [])
        self.assertEqual(dependency_empty["width"], 1)
        self.assertEqual(dependency_empty["height"], 1)

        one_dependency = copy.deepcopy(projection)
        dependency_edge = next(
            item for item in one_dependency["edges"] if item["relation_type"] == "depends_on"
        )
        one_dependency["edges"] = [dependency_edge]
        dependency_pair = graph_ui.build_readability_layout(one_dependency, lens="dependency")
        self.assertEqual(len(dependency_pair["nodes"]), 2)
        self.assertEqual(len(dependency_pair["edges"]), 1)
        self.assertEqual(len(dependency_pair["routes"]), 1)
        self.assertTrue(dependency_pair["routes"][0]["has_arrow"])

    def test_invalid_provider_store_graph_legacy_and_links_fail_closed(self) -> None:
        cases: list[tuple[str, dict, str]] = []
        old_provider = copy.deepcopy(self.provider)
        old_provider["provider_schema_version"] = 0
        cases.append(("provider", old_provider, "unsupported-provider-schema"))
        invalid = copy.deepcopy(self.provider)
        invalid["graph"]["validation"] = {
            "valid": False, "errors": [{"code": "cycle"}], "warnings": []
        }
        cases.append(("graph", invalid, "core-graph-invalid"))
        dangling = copy.deepcopy(self.provider)
        dangling["graph"]["nodes"] = dangling["graph"]["nodes"][:-1]
        _rebind(dangling)
        cases.append(("node", dangling, "dangling-node"))
        unsafe = copy.deepcopy(self.provider)
        unsafe["graph"]["nodes"][0]["source_links"] = [
            {"kind": "validation", "ref": "https://example.invalid/run"}
        ]
        _rebind(unsafe)
        cases.append(("link", unsafe, "unsafe-source-link"))
        windows_path = copy.deepcopy(self.provider)
        windows_path["graph"]["nodes"][0]["source_links"] = [
            {"kind": "validation", "ref": "C:/private/orrery/worktree.json"}
        ]
        _rebind(windows_path)
        cases.append(("path", windows_path, "unsafe-source-link"))

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

        legacy = copy.deepcopy(self.provider)
        legacy["relation_root_present"] = False
        for item in [*legacy["graph"]["nodes"], *legacy["graph"]["edges"]]:
            item["origin"] = "legacy-session-projection"
        _rebind(legacy)
        projection = graph_ui.project_core_relation_graph(lambda: legacy)
        self.assertEqual(projection["status"], "ready")
        self.assertFalse(projection["native_relation_root_present"])
        self.assertEqual(projection["evidence_origins"], ["legacy-session-projection"])
        self.assertTrue(projection["nodes"])
        self.assertTrue(projection["edges"])

        graph = build_relation_graph([])
        empty = {
            "provider_schema_version": 1,
            "provider_id": "project-orrery-core.workstream-relations",
            "authority": "derived-read-only",
            "relation_root_present": False,
            "graph": graph,
            "succession_plan": build_succession_plan(graph),
        }
        unavailable = graph_ui.project_core_relation_graph(lambda: empty)
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertEqual(unavailable["error"]["code"], "relation-evidence-absent")

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
            self.assertEqual(projection["error"]["code"], "relation-evidence-absent")

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
        self.assertIn("event.key==='Enter'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("event.key===' '", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("function keyboardActivate", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("addEventListener('wheel'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("if(!event.ctrlKey)return", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("{passive:false}", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("MIN_ZOOM=.55,MAX_ZOOM=1.6", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("Math.max(1,Math.min(1.15", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("expandedChains:new Set()", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("data-wg-expand-all", page)
        self.assertIn("data-wg-collapse-all", page)
        self.assertIn("data-wg-zoom-in", page)
        self.assertIn("data-wg-fit", page)
        self.assertIn("data-wg-inspector-close", page)
        self.assertIn('class="wg-inspector" hidden', page)
        self.assertIn('aria-label="关闭技术详情"', page)
        self.assertIn("任务关系列表", page)
        self.assertIn("当前没有已登记的依赖关系", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("层级 ${String(lane.rank+1)", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("'documentation-system':'文档系统'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("`RANK ${String(lane.rank+1)", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("visibleFactIds", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("displayFrom", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("更早历史", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("从 ", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("→ 到 ", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("marker-end", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("markerUnits:'userSpaceOnUse'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("markerWidth:10,markerHeight:10", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn(".wg-edge.lens-conflict{stroke:var(--wg-red);stroke-width:4", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertNotIn("wg-edge-label-bg", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("wg-edge-label", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("lineEncoding", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("0 条依赖边 · 0 个孤立节点", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("点击展开，仅影响这条上游链", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("收起本链", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("H${", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("--wg-node-width:248px;--wg-node-height:104px", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-graph-panel{min-width:0;width:100%", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-inspector[hidden]{display:none!important}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-edge-hit:focus-visible{stroke:", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertNotIn(".wg-edge-hit:focus-visible,.wg-inspector", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-ledger{position:absolute;width:1px", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-graph-panel{display:none}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-ledger{position:static;width:auto", graph_ui.WORKSTREAM_GRAPH_CSS)
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

        docsite_source = (ROOT / "scripts" / "docsite" / "build_docsite.py").read_text(encoding="utf-8")
        self.assertIn("--scroll-thumb-hover:", docsite_source)
        self.assertIn("html:has(body.light)", docsite_source)
        self.assertIn("scrollbar-color:var(--scroll-thumb) var(--scroll-track)", docsite_source)
        self.assertIn("*::-webkit-scrollbar-thumb", docsite_source)
        self.assertIn("*::-webkit-scrollbar-button{display:none", docsite_source)

    def test_root_only_default_off_personal_team_adjacency_and_zero_network(self) -> None:
        sentinel = (_base_page(), {"adrs": 0}, None, None)
        with mock.patch.object(
            self.builder.build_personal_observatory,
            "render_personal_site",
            return_value=sentinel,
        ), mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW", None)
            result = self.builder.render_workstream_relation_graph_site(
                ROOT / "docs", ROOT / "AGENTS.md", ROOT, "Atlas Control"
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
        mapping = json.loads((ROOT / "scripts" / "ci" / "change-mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(component["version"], "0.1.15")
        self.assertEqual(versions["components"]["observatory"]["version"], "0.1.15")
        test_ids = [item["test_id"] for item in mapping["tests"]]
        self.assertTrue(any(value.startswith("test_workstream_relation_graph_observatory.") for value in test_ids))
        self.assertTrue(any(value.startswith("test_workstream_graph_visual_prototype.") for value in test_ids))
        self.assertNotIn("scripts/docsite/build_workstream_relation_graph.py", component["managed_tools"])


if __name__ == "__main__":
    unittest.main()
