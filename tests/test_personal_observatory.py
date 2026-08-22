from __future__ import annotations

import importlib.util
import os
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
    ROOT / "scripts" / "docsite",
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

import build_docsite
from project_orrery_core.collaboration import write_workstream_session
from project_orrery_observatory.personal_observatory import (
    PERSONAL_OBSERVATORY_CSS,
    build_personal_observatory_projection,
    inject_personal_observatory,
    render_personal_observatory_panel,
    unavailable_personal_observatory_projection,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture


def _load_builder_module():
    path = ROOT / "scripts" / "docsite" / "build_personal_observatory.py"
    spec = importlib.util.spec_from_file_location("w4_personal_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ready_projection(**overrides):
    base = {
        "projection_schema": "project-orrery-personal-observatory-v1",
        "mode": "personal",
        "status": "ready",
        "read_only": True,
        "creates_project_facts": False,
        "writes_performed": False,
        "network_performed": False,
        "team_runtime_enabled": False,
        "captured_at": "2026-08-22T12:00:00Z",
        "current": None,
        "workstreams": [],
        "subsystems": [],
        "findings": [],
        "attention": [
            {
                "kind": "remote-unknown",
                "severity": "unknown",
                "label": "No local finding; remote and unreported work remain Unknown",
            }
        ],
        "w3": {
            key: {
                "status": "unavailable",
                "label": "Unavailable",
                "detail": "W3 not integrated",
                "source": "optional-w3-slot",
            }
            for key in (
                "review_queue",
                "integration_eligibility",
                "cleanup_eligibility",
            )
        },
    }
    base.update(overrides)
    return base


class PersonalObservatoryTests(unittest.TestCase):
    def _sessions(self, fixture: CollaborationGitFixture) -> None:
        write_workstream_session(
            fixture.worktree_a,
            workstream_id="PO-W1-FIXTURE",
            primary_subsystem_id="project-structure",
            affected_subsystem_ids=("test-coverage",),
            expected_writes=("untracked/same-path.txt",),
            validation_surfaces=("python -m unittest tests.test_collaboration_contract",),
        )
        write_workstream_session(
            fixture.worktree_b,
            workstream_id="PO-W2-FIXTURE",
            primary_subsystem_id="project-structure",
            affected_subsystem_ids=("test-coverage",),
            expected_writes=("untracked/same-path.txt",),
            validation_surfaces=("python -m unittest tests.test_collaboration_contract",),
        )

    def test_projection_reuses_w1_w2_contracts_without_network_or_writes(self):
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            before = {
                path: fixture.git(path, "status", "--porcelain=v1").stdout
                for path in (fixture.repository, fixture.worktree_a, fixture.worktree_b)
            }
            with mock.patch.object(
                socket, "socket", side_effect=AssertionError("network is forbidden")
            ):
                projection = build_personal_observatory_projection(
                    fixture.worktree_a, captured_at="2026-08-22T12:00:00Z"
                )
            after = {
                path: fixture.git(path, "status", "--porcelain=v1").stdout
                for path in (fixture.repository, fixture.worktree_a, fixture.worktree_b)
            }
        self.assertEqual(before, after)
        self.assertEqual(projection["status"], "ready")
        self.assertTrue(projection["read_only"])
        self.assertFalse(projection["writes_performed"])
        self.assertFalse(projection["network_performed"])
        self.assertFalse(projection["team_runtime_enabled"])
        self.assertEqual(projection["current"]["workstream_id"], "PO-W1-FIXTURE")
        self.assertEqual(projection["current"]["scope_revision"], 1)
        self.assertTrue(
            any(item["workstream_id"] == "PO-W2-FIXTURE" for item in projection["workstreams"])
        )
        groups = {
            item["workstream_id"]: item["display_group"]
            for item in projection["workstreams"]
        }
        self.assertEqual(groups["PO-W1-FIXTURE"], "active")
        self.assertEqual(groups["PO-W2-FIXTURE"], "active")
        self.assertIn("worktree-only", groups.values())
        self.assertGreaterEqual(projection["finding_counts"].get("direct", 0), 1)
        self.assertEqual(projection["remote_observability"]["status"], "unknown")

    def test_excluded_worktree_is_listed_but_never_opened(self):
        import project_orrery_core.collaboration as collaboration

        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            original = collaboration.inspect_worktree_status
            opened: list[Path] = []

            def guarded(path):
                resolved = Path(path).resolve()
                if resolved == fixture.worktree_b.resolve():
                    raise AssertionError("excluded worktree was opened")
                opened.append(resolved)
                return original(path)

            with mock.patch.object(collaboration, "inspect_worktree_status", guarded):
                projection = build_personal_observatory_projection(
                    fixture.worktree_a,
                    excluded_branches=("codex/fixture-b",),
                )
        self.assertTrue(opened)
        excluded = [
            item for item in projection["workstreams"]
            if item.get("unavailable_reason") == "excluded-worktree-contract-not-integrated"
        ]
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0]["branch"], "codex/fixture-b")
        self.assertEqual(excluded[0]["evidence_freshness"], "unknown")
        self.assertEqual(excluded[0]["display_group"], "unavailable")

    def test_absent_session_and_remote_boundary_stay_unknown(self):
        with CollaborationGitFixture() as fixture:
            projection = build_personal_observatory_projection(fixture.worktree_a)
        self.assertEqual(projection["findings"], [])
        self.assertTrue(
            any("Unknown" in item["label"] for item in projection["attention"])
        )
        self.assertTrue(
            all(item["primary_subsystem_id"] == "Unknown" for item in projection["workstreams"])
        )
        self.assertTrue(
            all(item["display_group"] == "worktree-only" for item in projection["workstreams"])
        )
        self.assertNotIn("safe", str(projection).lower())

    def test_w3_slots_fail_closed_without_a_contract(self):
        with CollaborationGitFixture() as fixture:
            projection = build_personal_observatory_projection(
                fixture.worktree_a, include_local_worktrees=False
            )
        for slot in projection["w3"].values():
            self.assertEqual(slot["status"], "unavailable")
            self.assertEqual(slot["label"], "Unavailable")
            self.assertEqual(slot["detail"], "W3 not integrated")

    def test_renderer_has_four_zones_progressive_detail_and_no_actions(self):
        projection = _ready_projection()
        panel = render_personal_observatory_panel(projection)
        self.assertIn('data-zone="project-status"', panel)
        self.assertIn('data-zone="attention"', panel)
        self.assertIn('data-zone="workstreams"', panel)
        self.assertIn('data-zone="subsystems"', panel)
        self.assertIn('data-state="no-worktree"', panel)
        self.assertIn("W3 not integrated", panel)
        self.assertIn('data-read-only="true"', panel)
        self.assertNotIn("<form", panel)
        self.assertNotIn("<button", panel)
        self.assertNotIn("onclick=", panel)
        self.assertNotIn("fetch(", panel)

    def test_renderer_separates_lifecycle_runtime_and_freshness(self):
        card = {
            "availability": "available",
            "workstream_id": "PO-W2&lt;unsafe",
            "worktree_id": "local-fixture",
            "worktree_path": "C:/fixture/<unsafe>",
            "branch": "codex/fixture",
            "head": "a" * 40,
            "integration_oid": "b" * 40,
            "merge_base": "c" * 40,
            "ahead": 2,
            "behind": 1,
            "fact_scope": "worktree",
            "dirty": True,
            "dirty_entry_count": 2,
            "untracked_count": 1,
            "primary_subsystem_id": "project-structure",
            "affected_subsystem_ids": ["test-coverage"],
            "scope_revision": 4,
            "scope_path_count": 1,
            "scope_paths": [{"path": "tests/<unsafe>.py", "sources": ["untracked"]}],
            "lifecycle_phase": "implementing",
            "runtime_condition": "waiting-for-user",
            "evidence_freshness": "stale",
            "session_state": "stale",
            "captured_at": "2026-08-22T12:00:00Z",
            "platform_session": None,
            "findings": [],
            "is_current": True,
            "has_session": True,
            "display_group": "active",
        }
        inventory = dict(
            card,
            workstream_id="codex/fixture-without-session",
            branch="codex/fixture-without-session",
            has_session=False,
            display_group="worktree-only",
            lifecycle_phase="unavailable",
            is_current=False,
        )
        panel = render_personal_observatory_panel(
            _ready_projection(current=card, workstreams=[card, inventory])
        )
        self.assertIn("lifecycle</span><b>implementing", panel)
        self.assertIn("runtime</span><b>waiting-for-user", panel)
        self.assertIn("evidence</span><b>stale", panel)
        self.assertIn('class="po-work-summary"', panel)
        self.assertIn("项目现在怎么样", panel)
        self.assertIn("谁在推进什么", panel)
        self.assertIn("查看证据", panel)
        self.assertIn("技术证据", panel)
        self.assertIn('data-display-group="worktree-only"', panel)
        self.assertIn("No Workstream session", panel)
        self.assertNotIn("<unsafe>", panel)
        self.assertIn("&amp;lt;unsafe", panel)

    def test_injection_adds_a_separate_page_and_leaves_dashboard_untouched(self):
        base = (
            "<html><head><style>body{color:red}</style></head><body>"
            '<aside class="sidebar"><a class="nav-item" data-target="trends">'
            '<span class="dot proposed"></span><span class="lbl">🔭 路线与趋势</span></a></aside>'
            '<main class="content">'
            '<article class="page wide on" id="dashboard" data-kind="dashboard" '
            'data-title="总览"><p>legacy</p></article>'
            '</main><aside class="toc" id="toc"></aside></body></html>'
        )
        result = inject_personal_observatory(base, _ready_projection())
        dashboard = result[
            result.index('<article class="page wide on" id="dashboard"'):
            result.index("</article>") + len("</article>")
        ]
        self.assertEqual(
            dashboard,
            '<article class="page wide on" id="dashboard" data-kind="dashboard" '
            'data-title="总览"><p>legacy</p></article>',
        )
        self.assertIn('data-target="personal-observatory"', result)
        self.assertIn("@media(max-width:640px)", PERSONAL_OBSERVATORY_CSS)
        self.assertIn("grid-template-columns:1fr", PERSONAL_OBSERVATORY_CSS)
        self.assertIn(
            '<article class="page wide" id="personal-observatory"', result
        )
        self.assertGreater(
            result.index('id="personal-observatory"'), result.index("</article>")
        )

    def test_root_only_entry_preserves_legacy_bytes_when_disabled(self):
        builder = _load_builder_module()
        sentinel = ("<html>legacy</html>", {"adrs": 0}, None)
        with mock.patch.object(builder, "_base_site", return_value=sentinel):
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("ORRERY_PERSONAL_OBSERVATORY_VIEW", None)
                result = builder.render_personal_site(
                    ROOT / "docs", ROOT / "AGENTS.md", ROOT, "Project Orrery"
                )
        self.assertEqual(result, (sentinel[0], sentinel[1], None, None))

    def test_unavailable_projection_renders_stable_fallback(self):
        projection = unavailable_personal_observatory_projection(
            ValueError("fixture unavailable")
        )
        panel = render_personal_observatory_panel(projection)
        self.assertIn('data-status="unavailable"', panel)
        self.assertIn("fixture unavailable", panel)
        self.assertIn("READ ONLY", panel)
        self.assertFalse(projection["network_performed"])


if __name__ == "__main__":
    unittest.main()
