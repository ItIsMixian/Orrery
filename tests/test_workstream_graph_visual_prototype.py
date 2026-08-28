from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "experiments" / "workstream-graph-visual-prototype"
FIXTURE = PROTOTYPE / "fixtures" / "workstream-graph.provisional.v1.json"


class WorkstreamGraphVisualPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
        cls.css = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")
        cls.javascript = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")

    def test_fixture_is_explicitly_provisional_and_versioned(self) -> None:
        self.assertEqual(self.fixture["fixture_version"], "workstream-graph-provisional-v1")
        self.assertEqual(self.fixture["authority"], "provisional/non-authoritative")
        self.assertIn("not a Core relation contract", self.fixture["purpose"])
        self.assertEqual(self.fixture["default_active_tip_id"], "w7c-a")

    def test_fixture_covers_succession_sibling_and_collapsed_history(self) -> None:
        edges = {(edge["source"], edge["target"], edge["view"]): edge for edge in self.fixture["edges"]}
        expected_chain = [
            ("w5c", "w6", "succession"),
            ("w6", "w5d", "succession"),
            ("w5d", "ci1", "succession"),
            ("ci1", "w5e", "succession"),
            ("w5e", "w7c-a", "succession"),
        ]
        for relation in expected_chain:
            self.assertIn(relation, edges)
        self.assertEqual(edges[("w5e", "w7a", "succession")]["relation"], "sibling-from-same-base")
        self.assertEqual(
            self.fixture["collapsed_history"][0]["node_ids"],
            ["w5c", "w6", "w5d"],
        )

    def test_fixture_covers_multi_predecessor_unknown_and_confirmed_conflict(self) -> None:
        dependencies = [
            edge for edge in self.fixture["edges"]
            if edge["view"] == "dependency" and edge["target"] == "w7c-b"
        ]
        confirmed_sources = {edge["source"] for edge in dependencies if edge["certainty"] == "confirmed"}
        self.assertEqual(confirmed_sources, {"w7a", "w7c-a"})
        self.assertTrue(any(edge["certainty"] == "unknown" for edge in dependencies))

        conflicts = [edge for edge in self.fixture["edges"] if edge["view"] == "conflict"]
        direct = next(edge for edge in conflicts if edge["certainty"] == "confirmed")
        self.assertEqual(direct["severity"], "L3/direct")
        self.assertIn("synthetic-path-overlap", {item["kind"] for item in direct["evidence"]})
        self.assertTrue(any(edge["certainty"] == "proposed" for edge in conflicts))

    def test_static_surface_has_real_controls_and_accessible_fallback(self) -> None:
        for token in (
            'data-mode="succession"',
            'data-mode="dependency"',
            'data-mode="conflict"',
            'id="subsystem-filter"',
            'id="status-filter"',
            'id="history-toggle"',
            'id="relation-ledger"',
            'aria-live="polite"',
        ):
            self.assertIn(token, self.html)
        self.assertIn("role=\"img\"", self.html)
        self.assertIn("PROVISIONAL / NON-AUTHORITATIVE", self.html)

    def test_responsive_keyboard_and_reduced_motion_contract(self) -> None:
        self.assertRegex(self.css, r"@media\s*\(max-width:\s*640px\)")
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn(":focus-visible", self.css)
        self.assertIn('event.key === "Enter"', self.javascript)
        self.assertIn('event.key === " "', self.javascript)
        self.assertIn('tabindex: 0', self.javascript)

    def test_prototype_has_no_production_or_external_runtime_dependency(self) -> None:
        self.assertNotIn("project_orrery_core", self.javascript)
        self.assertNotIn("serve_team_observatory", self.javascript)
        self.assertNotRegex(self.javascript, r"fetch\(\s*[\"']https?://")
        self.assertNotRegex(self.html, r"<(script|link)[^>]+https?://")
        self.assertEqual(
            re.findall(r'<script[^>]+src="([^"]+)"', self.html),
            ["prototype.js"],
        )


if __name__ == "__main__":
    unittest.main()
