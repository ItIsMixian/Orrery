from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
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

    def test_plain_chinese_status_taxonomy_has_no_generic_pending_fallback(self) -> None:
        cases = (
            ({"runtime_condition": "active"}, ("正在进行", "in-progress")),
            ({"runtime_condition": "waiting-for-user"}, ("等待人工确认", "human-confirmation-pending")),
            ({"session_state": "stale"}, ("状态待刷新／证据过期", "stale-evidence")),
            ({"lifecycle_phase": "historical"}, ("历史任务", "historical")),
            ({"session_state": "missing"}, ("缺少任务记录", "session-missing")),
            ({"status": "unregistered"}, ("未登记", "unregistered")),
            ({"evidence_freshness": "unknown"}, ("关系证据不足", "relation-evidence-insufficient")),
            ({"candidate_status_code": "candidate-validation-pending"}, ("候选已冻结 · 等待验证", "candidate-validation-pending")),
            ({"candidate_status_code": "candidate-validated"}, ("候选已验证 · 尚未关闭", "candidate-validated")),
            ({"candidate_status_code": "candidate-validation-failed"}, ("候选验证失败 · 尚未关闭", "candidate-validation-failed")),
        )
        for axes, expected in cases:
            with self.subTest(axes=axes):
                self.assertEqual(graph_ui._plain_state(axes), expected)

    def test_candidate_lifecycle_is_supplemental_and_preserves_graph_semantics(self) -> None:
        payload = json.loads(json.dumps(self.provider))
        before = graph_ui.build_relation_graph_projection(payload)
        candidate_head = next(
            item["head_oid"] for item in before["nodes"] if item["workstream_id"] == "CI2-late"
        )
        payload["candidate_lifecycle"] = {
            "CI2-late": {
                "candidate_state": "candidate-frozen", "validation_status": "pending",
                "closure_state": "open", "status_code": "candidate-validation-pending",
                "candidate_sha": candidate_head,
            }
        }
        after = graph_ui.build_relation_graph_projection(payload)
        node = next(item for item in after["nodes"] if item["workstream_id"] == "CI2-late")
        self.assertEqual(node["plain_status_code"], "candidate-validation-pending")
        self.assertEqual(node["validation_status"], "pending")
        self.assertEqual(
            [(item["relation_id"], item["source_workstream_id"], item["target_workstream_id"]) for item in before["edges"]],
            [(item["relation_id"], item["source_workstream_id"], item["target_workstream_id"]) for item in after["edges"]],
        )
        self.assertEqual(before["active_tip_workstream_ids"], after["active_tip_workstream_ids"])

    def test_core_payload_maps_three_lenses_and_independent_axes(self) -> None:
        projection = self.projection
        self.assertEqual(projection["status"], "ready")
        self.assertEqual(projection["projection_schema_version"], 2)
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
        self.assertEqual(projection["history_candidate_ids"], [])
        self.assertEqual(projection["history_index"]["status"], "unavailable")
        self.assertEqual(projection["history_index"]["record_count"], 0)
        self.assertEqual(
            projection["classification_inventory"],
            {
                "graph_node_count": 14,
                "missing_series": 12,
                "missing_program_phase": 14,
                "missing_both": 12,
                "history_record_count": 0,
                "history_missing_series": 0,
                "history_missing_program_phase": 0,
                "authority": "explicit-metadata-only",
                "name_inference_performed": False,
                "lineage_inference_performed": False,
            },
        )
        self.assertEqual(nodes["CI1"]["series_id"], "CI")
        self.assertEqual(nodes["CI2-late"]["task_code"], "CI2")
        self.assertEqual(nodes["waiting-task"]["plain_status"], "等待人工确认")
        self.assertEqual(nodes["offline-unknown"]["plain_status"], "关系证据不足")

        self.assertTrue(projection["conflicts"])
        self.assertTrue(all(item["relation_type"] == "conflict-fact" for item in projection["conflicts"]))
        self.assertTrue(all(item["conflict_evidence"]["location"] for item in projection["conflicts"]))
        self.assertTrue(all(item["conflict_evidence"]["impact"] for item in projection["conflicts"]))
        self.assertTrue(all(item["conflict_evidence"]["source"] for item in projection["conflicts"]))
        self.assertTrue(projection["comparison_suggestions"])
        self.assertTrue(all(item["relation_type"] == "comparison-suggestion" for item in projection["comparison_suggestions"]))
        self.assertTrue(projection["suppressed_pairs"])
        conflict_pairs = {
            frozenset((item["source_workstream_id"], item["target_workstream_id"]))
            for item in projection["conflicts"]
        }
        comparison_pairs = {
            frozenset((item["source_workstream_id"], item["target_workstream_id"]))
            for item in projection["comparison_suggestions"]
        }
        self.assertTrue(conflict_pairs.isdisjoint(comparison_pairs))
        safe = next(
            link for node in projection["nodes"] for link in node["source_links"] if link["href"]
        )
        self.assertTrue(safe["href"].startswith("#lib-"))

        panel = graph_ui.render_workstream_relation_graph_panel(projection)
        for token in (
            'data-wg-lens="succession"', 'data-wg-lens="dependency"',
            'data-wg-lens="conflict"', "打开同事实任务关系列表", "只读",
            'data-wg-comparison-toggle', 'class="wg-comparison-drawer"',
            "不提供应用、撤销、关闭、删除、合并或远程执行",
        ):
            self.assertIn(token, panel)
        self.assertNotIn('class="wg-series"', panel)
        self.assertIn("waiting-task", panel)
        self.assertIn("blocked-by-conflict", panel)
        self.assertIn("synthetic-non-authoritative", panel)

        lens_types = {
            "succession": {"derived_from", "absorbs", "series-display"},
            "dependency": {"depends_on", "series-display"},
            "conflict": {"conflict-fact"},
        }
        for lens, allowed in lens_types.items():
            with self.subTest(lens=lens):
                layout = graph_ui.build_readability_layout(projection, lens=lens)
                self.assertTrue(layout["nodes"])
                self.assertTrue(all(item["relation_type"] in allowed for item in layout["edges"]))
                self.assertTrue(
                    layout["geometry_postconditions"]["passed"],
                    layout["geometry_postconditions"]["violations"],
                )
                self.assertEqual(len(layout["placement_translations"]), len(layout["component_bounds"]))
                self.assertEqual(layout["program_bands"], [])
                self.assertEqual(layout["component_headers"], [])
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
                        horizontal_gap = max(
                            0,
                            right["x"] - (left["x"] + left["width"]),
                            left["x"] - (right["x"] + right["width"]),
                        )
                        vertical_gap = max(
                            0,
                            right["y"] - (left["y"] + left["height"]),
                            left["y"] - (right["y"] + right["height"]),
                        )
                        self.assertGreaterEqual(
                            math.hypot(horizontal_gap, vertical_gap), 40,
                            f"node gap: {left_id} / {right_id}",
                        )
                edge_by_id = {item["display_edge_id"]: item for item in layout["edges"]}
                for route in layout["routes"]:
                    self.assertTrue(route["has_arrow"])
                    self.assertLessEqual(route["bend_count"], 2)
                    self.assertGreaterEqual(route["shortest_segment"], 16)
                    self.assertLessEqual(route["stretch"], 1.65)
                    self.assertTrue(route["source_port"])
                    self.assertTrue(route["target_port"])
                    edge = edge_by_id[route["edge_id"]]
                    if edge["relation_type"] in {"series-display", "conflict-fact"}:
                        self.assertTrue(route["has_label"])
                    self.assertEqual(
                        route["line_encoding"],
                        (
                            "series" if edge_by_id[route["edge_id"]]["relation_type"] == "series-display"
                            else {"succession": "solid", "dependency": "dashed", "conflict": "compound"}[lens]
                        ),
                    )
                    for node_id, rect in boxes:
                        if node_id in {edge["display_from_id"], edge["display_to_id"]}:
                            continue
                        for start, end in zip(route["points"], route["points"][1:]):
                            self.assertFalse(
                                _segment_hits_rect(start, end, rect),
                                f"edge {route['edge_id']} crosses {node_id}",
                            )

        collapsed = graph_ui.build_readability_layout(projection, lens="succession")
        self.assertFalse([item for item in collapsed["chains"] if item["history_ids"]])
        history_projection = {
            "nodes": [
                {
                    "workstream_id": item, "display_prefix": item, "display_name": item,
                    "status": "completed" if item.startswith("old") else "active",
                    "session_state": "current", "runtime_condition": "inactive" if item.startswith("old") else "active",
                    "lifecycle_phase": "historical" if item.startswith("old") else "implementing",
                    "evidence_freshness": "current", "scope_status": "current",
                    "closure_reason": "responsibility-transferred" if item.startswith("old") else None,
                    "plain_status": "历史任务" if item.startswith("old") else "正在进行",
                    "plain_status_code": "historical" if item.startswith("old") else "active",
                    "primary_subsystem_id": "test-coverage", "affected_subsystem_ids": [],
                    "visibility": "worktree-local", "observability": "local", "source_links": [],
                    "series_id": None, "series_order": None, "program_id": None, "phase_id": None,
                }
                for item in ("old-1", "old-2", "direct", "tip")
            ],
            "edges": [
                {
                    "relation_id": f"edge-{source}", "relation_type": "derived_from",
                    "source_workstream_id": source, "target_workstream_id": target,
                    "lifecycle": "active", "certainty": "confirmed",
                    "effective_active_succession": True, "source_links": [],
                }
                for source, target in (("old-2", "old-1"), ("direct", "old-2"), ("tip", "direct"))
            ],
            # These are relation-connected predecessors, not strict archived
            # history identities. Strict history is grouped independently.
            "active_tip_workstream_ids": ["tip"], "history_candidate_ids": [],
            "comparison_suggestions": [], "conflicts": [], "program_groups": [],
        }
        collapsed = graph_ui.build_readability_layout(history_projection, lens="succession")
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
            history_projection, lens="succession", expanded_chain_ids=[chain["chain_id"]]
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
        self.assertEqual(dependency_empty["semantic_edge_count"], 0)
        self.assertGreater(dependency_empty["series_edge_count"], 0)
        self.assertTrue(all(item["relation_type"] == "series-display" for item in dependency_empty["edges"]))

        one_dependency = copy.deepcopy(projection)
        dependency_edge = next(
            item for item in one_dependency["edges"] if item["relation_type"] == "depends_on"
        )
        one_dependency["edges"] = [dependency_edge]
        dependency_pair = graph_ui.build_readability_layout(one_dependency, lens="dependency")
        self.assertGreaterEqual(len(dependency_pair["nodes"]), 2)
        self.assertEqual(dependency_pair["semantic_edge_count"], 1)
        self.assertTrue(all(item["has_arrow"] for item in dependency_pair["routes"]))

    def test_invalid_provider_store_graph_legacy_and_links_fail_closed(self) -> None:
        private_session = graph_ui._safe_source_link({
            "kind": "workstream-session",
            "ref": "git-private-session:CI6-local-validation-router-tier-enforcement@e5ee31c418fa4d2d81f3df792f683064a0a9c5d0",
        })
        self.assertIsNone(private_session["href"])
        for disposition in ("archive", "archive-conflict", "archive-unresolved"):
            archived = graph_ui._safe_source_link({
                "kind": "other",
                "ref": f"retired-session-{disposition}:sha256:" + "a" * 64,
            })
            self.assertIsNone(archived["href"])
        with self.assertRaisesRegex(graph_ui.RelationGraphUnavailable, "safe whitelist"):
            graph_ui._safe_source_link({
                "kind": "other",
                "ref": "retired-session-archive-unresolved:sha256:not-a-hash",
            })

        out_of_graph_capture = copy.deepcopy(self.provider)
        proposal = {
            "contract_type": "workstream-relation-proposal-event",
            "relation_id": "relation-outside-current-graph",
            "proposal_id": "proposal-outside-current-graph",
            "revision": 1,
            "source_workstream_id": "archived-task-outside-current-graph",
            "target_workstream_id": "W5E",
            "relation_type": "depends_on",
            "required_for": "integration",
            "evidence": [{"category": "workstream-session", "ref": "git-private:archived-task"}],
            "rationale": "preserved in the separate Relation Inbox",
            "consequence": "not projected as a dangling Graph edge",
        }
        out_of_graph_capture["relation_capture"] = {
            "schema_version": 2,
            "effective_relations": [],
            "pending_proposals": [{"current": proposal}],
        }
        projected = graph_ui.project_core_relation_graph(lambda: out_of_graph_capture)
        self.assertEqual(projected["status"], "ready")
        self.assertNotIn(
            "relation-outside-current-graph",
            {item["relation_id"] for item in projected["edges"]},
        )

        malformed_out_of_graph = copy.deepcopy(out_of_graph_capture)
        malformed_out_of_graph["relation_capture"]["pending_proposals"][0]["current"]["evidence"] = [
            {"category": "validation", "ref": "https://example.invalid/private"}
        ]
        malformed = graph_ui.project_core_relation_graph(lambda: malformed_out_of_graph)
        self.assertEqual(malformed["status"], "unavailable")
        self.assertEqual(malformed["error"]["code"], "unsafe-source-link")

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
        self.assertNotIn("C:/private/secret", json.dumps(failed))
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

    def test_graph_native_series_comparison_overlay_and_conflict_tracks(self) -> None:
        dependency = graph_ui.build_readability_layout(self.projection, lens="dependency")
        series_edges = [item for item in dependency["edges"] if item["relation_type"] == "series-display"]
        self.assertTrue(series_edges)
        self.assertTrue(all(item["presentation_only"] for item in series_edges))
        self.assertTrue(any(item["series_id"] == "CI" for item in series_edges))
        self.assertEqual(dependency["series_lanes"], [])
        self.assertTrue(dependency["geometry_postconditions"]["passed"])
        self.assertTrue({"CI1", "CI2-late"}.issubset(dependency["visible_fact_ids"]))

        overlay = graph_ui.build_readability_layout(
            self.projection, lens="succession", include_comparisons=True
        )
        self.assertEqual(
            overlay["comparison_edge_count"], len(self.projection["comparison_suggestions"])
        )
        self.assertTrue(any(item["line_encoding"] == "comparison" for item in overlay["routes"]))
        self.assertTrue(all(
            item["relation_type"] != "conflict-fact"
            for item in overlay["edges"] if item["relation_type"] == "comparison-suggestion"
        ))

        zero_conflicts = copy.deepcopy(self.projection)
        zero_conflicts["conflicts"] = []
        empty = graph_ui.build_readability_layout(zero_conflicts, lens="conflict")
        self.assertEqual(empty["nodes"], [])
        self.assertEqual(empty["edges"], [])
        self.assertEqual(empty["series_edge_count"], 0)
        self.assertEqual(empty["comparison_edge_count"], 0)

        many = copy.deepcopy(self.projection)
        targets = ["W5E", "waiting-task", "blocked-task", "failed-task"]
        many["conflicts"] = [
            {
                "id": f"confirmed-conflict-{index}",
                "relation_type": "conflict-fact",
                "source_workstream_id": "CI1",
                "target_workstream_id": target,
                "certainty": "confirmed",
                "lifecycle": "effective",
                "conflict_evidence": {
                    "location": [f"module/{index}"], "impact": "exclusive contract",
                    "source": "synthetic geometry fixture",
                },
                "reason_codes": ["explicit-human-conflict-finding"],
                "source_links": [],
            }
            for index, target in enumerate(targets)
        ]
        routed = graph_ui.build_readability_layout(many, lens="conflict")
        self.assertEqual(len(routed["routes"]), 4)
        segments: dict[tuple[tuple[int, int], tuple[int, int]], str] = {}
        edge_by_id = {item["display_edge_id"]: item for item in routed["edges"]}
        for route in routed["routes"]:
            edge = edge_by_id[route["edge_id"]]
            self.assertTrue(route["has_label"])
            for start, end in zip(route["points"], route["points"][1:]):
                self.assertNotEqual(start, end)
                normalized = tuple(sorted((start, end)))
                self.assertNotIn(normalized, segments, f"coincident segment: {route['edge_id']}")
                segments[normalized] = route["edge_id"]
                for node_id, rect in routed["positions"].items():
                    if node_id in {edge["display_from_id"], edge["display_to_id"]}:
                        continue
                    self.assertFalse(
                        _segment_hits_rect(start, end, rect),
                        f"edge {route['edge_id']} crosses {node_id}",
                    )

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

    def test_program_membership_is_containment_only_and_same_semantics_bundle_is_declared(self) -> None:
        provider = copy.deepcopy(self.provider)
        provider["program_hierarchy"] = {
            "schema_version": 1,
            "contract_type": "workstream-program-hierarchy-inspection",
            "groups": [
                {"group_id": "program-w", "group_kind": "program", "parent_group_id": None,
                 "display_label": "W program", "order": 0},
                {"group_id": "phase-w5", "group_kind": "phase", "parent_group_id": "program-w",
                 "display_label": "W5 phase", "order": 5},
            ],
            "memberships": [
                {"membership_id": "member-w5e", "workstream_id": "W5E",
                 "group_path": ["program-w", "phase-w5"]},
            ],
            "pending_group_events": [], "pending_membership_events": [],
            "read_only": True, "writes_performed": False, "name_inference_performed": False,
            "relation_effects": {"series": False, "relations": False, "gates": False,
                                 "closure": False, "ownership": False},
        }
        projection = graph_ui.project_core_relation_graph(lambda: provider)
        before_relations = len(projection["edges"])
        self.assertEqual(next(item for item in projection["nodes"] if item["workstream_id"] == "W5E")["phase_id"], "phase-w5")
        layout = graph_ui.build_readability_layout(projection, lens="succession")
        self.assertEqual(layout["program_bands"], [])
        self.assertTrue(layout["geometry_postconditions"]["passed"])
        self.assertEqual(len(projection["edges"]), before_relations)

        provider["program_hierarchy"]["memberships"].append({
            "membership_id": "member-out-of-graph",
            "workstream_id": "W5D-lan-collaboration-harness",
            "group_path": ["program-w", "phase-w5"],
        })
        quarantined_membership = graph_ui.project_core_relation_graph(lambda: provider)
        self.assertEqual(quarantined_membership["status"], "ready")
        self.assertEqual(len(quarantined_membership["nodes"]), len(projection["nodes"]))
        self.assertEqual(len(quarantined_membership["edges"]), before_relations)
        self.assertNotIn(
            "W5D-lan-collaboration-harness",
            {item["workstream_id"] for item in quarantined_membership["nodes"]},
        )

        invalid_in_graph = copy.deepcopy(provider)
        invalid_in_graph["program_hierarchy"]["memberships"][0]["group_path"] = ["program-w"]
        failed = graph_ui.project_core_relation_graph(lambda: invalid_in_graph)
        self.assertEqual(failed["status"], "unavailable")
        self.assertEqual(failed["error"]["code"], "invalid-provider")
        self.assertEqual(failed["nodes"], [])
        self.assertEqual(failed["edges"], [])

        bundled = copy.deepcopy(self.projection)
        ids = [item["workstream_id"] for item in bundled["nodes"] if item.get("evidence_freshness") == "current" and item.get("scope_status") == "current"][:4]
        self.assertEqual(len(ids), 4)
        common, targets = ids[0], ids[1:]
        bundled["active_tip_workstream_ids"] = targets
        bundled["edges"] = [
            {
                "relation_id": f"bundle-edge-{index}", "relation_type": "derived_from",
                "source_workstream_id": target, "target_workstream_id": common,
                "lifecycle": "active", "certainty": "confirmed", "required_for": None,
                "evidence_status": "confirmed", "evidence": {}, "reason_codes": [],
                "source_links": [], "origin": "native",
            }
            for index, target in enumerate(targets)
        ]
        bundle_layout = graph_ui.build_readability_layout(bundled, lens="succession")
        self.assertEqual(len(bundle_layout["route_bundles"]), 1)
        bundle = bundle_layout["route_bundles"][0]
        self.assertEqual(len(bundle["edge_ids"]), 3)
        self.assertLessEqual(abs(bundle["trunk_points"][1][1] - bundle["trunk_points"][0][1]), 64)
        self.assertEqual(bundle["endpoint_kind"], "source")
        bundled_routes = [item for item in bundle_layout["routes"] if item["route_bundle_id"] == bundle["bundle_id"]]
        self.assertEqual(len(bundled_routes), 3)
        self.assertEqual({tuple(item["points"][:2]) for item in bundled_routes}, {tuple(bundle["trunk_points"])})

        mixed = copy.deepcopy(bundled)
        mixed["edges"][0]["lifecycle"] = "stale"
        mixed_layout = graph_ui.build_readability_layout(mixed, lens="succession")
        self.assertLess(len([item for item in mixed_layout["routes"] if item["route_bundle_id"]]), 3)

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

    def test_component_local_packing_and_module_boundary_projection(self) -> None:
        def node(workstream_id: str, module: str, *, runtime: str = "active", affected: list[str] | None = None) -> dict:
            return {
                "workstream_id": workstream_id, "display_prefix": workstream_id,
                "display_name": workstream_id, "status": "active", "session_state": "current",
                "lifecycle_phase": "implementing", "runtime_condition": runtime,
                "evidence_freshness": "current", "scope_status": "current", "closure_reason": None,
                "plain_status": "正在进行", "plain_status_code": "active",
                "primary_subsystem_id": module, "affected_subsystem_ids": affected or [],
                "visibility": "worktree-local", "observability": "local", "source_links": [],
                "series_id": None, "series_order": None, "program_id": None, "phase_id": None,
            }

        disconnected = {
            "nodes": [node(f"component-{index}", "documentation-system") for index in range(4)],
            "edges": [], "active_tip_workstream_ids": [f"component-{index}" for index in range(4)],
            "history_candidate_ids": [], "comparison_suggestions": [], "conflicts": [], "program_groups": [],
        }
        packed = graph_ui.build_readability_layout(disconnected, lens="succession")
        self.assertGreaterEqual(len({item["x"] for item in packed["positions"].values()}), 2)

        scoped = {
            "nodes": [
                node("doc-task", "documentation-system"),
                node("authority-task", "authority-meta-model"),
                node("multi-task", "multi-worktree-collaboration", runtime="paused", affected=["documentation-system"]),
            ],
            "edges": [{
                "relation_id": "cross-module", "relation_type": "derived_from",
                "source_workstream_id": "doc-task", "target_workstream_id": "authority-task",
                "lifecycle": "active", "certainty": "confirmed", "effective_active_succession": True,
                "source_links": [],
            }],
            "active_tip_workstream_ids": ["doc-task", "multi-task"], "history_candidate_ids": [],
            "comparison_suggestions": [], "conflicts": [], "program_groups": [],
        }
        documentation = graph_ui.build_readability_layout(
            scoped, lens="succession", subsystem="documentation-system"
        )
        full_ids = {item["workstream_id"] for item in documentation["nodes"] if not item.get("is_boundary_stub")}
        boundary_ids = {item["boundary_external_id"] for item in documentation["nodes"] if item.get("is_boundary_stub")}
        self.assertEqual(full_ids, {"doc-task", "multi-task"})
        self.assertEqual(boundary_ids, {"authority-task"})
        active_only = graph_ui.build_readability_layout(
            scoped, lens="succession", subsystem="documentation-system", runtime="active"
        )
        self.assertEqual(
            {item["workstream_id"] for item in active_only["nodes"] if not item.get("is_boundary_stub")},
            {"doc-task"},
        )

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
        self.assertIn("MIN_ZOOM=.3,MAX_ZOOM=2", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("Math.max(MIN_ZOOM,Math.min(1.15", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("history:all", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("organizationalClassificationCounts", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("组织分类未登记", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("wg-overview", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("wg-overview", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-node:focus,.wg-node:focus-visible{outline:none!important}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertNotIn("drop-shadow(0 0 4px color-mix", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("expandedChains:new Set()", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("data-wg-expand-all", page)
        self.assertNotIn("data-wg-collapse-all", page)
        self.assertIn("data-wg-zoom-in", page)
        self.assertIn("data-wg-fit", page)
        self.assertIn("data-wg-inspector-close", page)
        self.assertIn('class="wg-inspector" hidden', page)
        self.assertIn('aria-label="关闭技术详情"', page)
        self.assertIn("任务关系列表", page)
        self.assertIn("当前没有已登记的依赖关系", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("层级 ${String(lane.rank+1)", graph_ui.WORKSTREAM_GRAPH_JS)
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
        self.assertIn("wg-edge-label", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("同系列演进（仅展示）", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("compact?'系列演进'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("lineEncoding", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("0 条依赖边 · 0 个孤立节点", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("有关系证据的上游任务，点击展开", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("收起历史", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("H${", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("--wg-node-width:224px;--wg-node-height:96px", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("RANK_GAP=144,ROW_GAP=40,SERIES_GAP=88,SERIES_ROW_GAP=54", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("function localRanks", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("PACK_WIDTH=1180,BLOCK_GAP=56", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("declareBundles(displayEdges,blockById)", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("boundaryByExternal", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("扩展任务范围", page)
        self.assertIn("显示直接关联任务", page)
        self.assertIn("显示影响本模块的任务", page)
        self.assertIn("data-wg-semantic-context", page)
        self.assertIn("height:nodeIds.size?canvasBottom+54:1", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("componentLayouts", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("occupiedBounds", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("placementTranslations", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("const programBands=[]", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("positions.clear()", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("layoutSeries", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("programTop", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("rowCursor+=componentRows+1", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("routeReserve", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn("trackY=nodeTop-26", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("window.matchMedia('(max-width:640px)')", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("function applySelectionFocus", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("verticalBlockers", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("svg g.is-muted{opacity:.22", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("data-wg-edge-id", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("data-wg-node-id", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn(".wg-graph-panel{min-width:0;width:100%", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-inspector[hidden]{display:none!important}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-edge-hit:focus-visible{stroke:", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertNotIn(".wg-edge-hit:focus-visible,.wg-inspector", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-mobile-ledger{position:absolute;width:1px", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-graph-panel{display:block", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-mobile-ledger{position:static", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-comparison-drawer", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn(".wg-edge.series-display{stroke:var(--wg-dim);stroke-width:1.5}", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("W ›", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn(".wg-bundle-trunk", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("--wg-node-accent", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertNotIn(".wg-node.is-endpoint>rect{stroke:var(--wg-ink)", graph_ui.WORKSTREAM_GRAPH_CSS)
        self.assertIn("kind==='node'", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertIn("declareBundles", graph_ui.WORKSTREAM_GRAPH_JS)
        self.assertNotIn(".wg-series{", graph_ui.WORKSTREAM_GRAPH_CSS)
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
        self.assertEqual(component["version"], "0.1.20")
        self.assertEqual(versions["components"]["observatory"]["version"], "0.1.20")
        test_ids = [item["test_id"] for item in mapping["tests"]]
        self.assertTrue(any(value.startswith("test_workstream_relation_graph_observatory.") for value in test_ids))
        self.assertTrue(any(value.startswith("test_workstream_graph_visual_prototype.") for value in test_ids))
        self.assertIn("scripts/docsite/build_workstream_relation_graph.py", component["managed_tools"])


if __name__ == "__main__":
    unittest.main()
