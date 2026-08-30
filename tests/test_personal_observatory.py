from __future__ import annotations

import json
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
import project_orrery_observatory.personal_observatory as personal_observatory
import project_orrery_core.workspace_cleanup as workspace_cleanup
from project_orrery_core.collaboration import (
    refresh_workstream_scope,
    transition_workstream_session,
    write_workstream_session,
)
from project_orrery_core.review import generate_review_package
from project_orrery_observatory.personal_observatory import (
    PERSONAL_OBSERVATORY_CSS,
    build_personal_observatory_projection,
    inject_personal_observatory,
    render_personal_observatory_panel,
    unavailable_personal_observatory_projection,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture


PASS_COMMAND = 'python -c "import sys; sys.exit(0)"'


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


def _w3_bundle(**overrides):
    actions = {
        action: {
            "eligible": action == "remove-worktree",
            "authorized": False,
            "performed": False,
            "implies_actions": [],
            "reasons": [] if action == "remove-worktree" else ["fixture-blocker"],
        }
        for action in (
            "remove-worktree",
            "delete-local-branch",
            "delete-remote-branch",
            "remove-directory",
        )
    }
    base = {
        "provider_schema_version": 1,
        "status": "ready",
        "review_queue": [
            {
                "queue_status": "pending",
                "package_id": "review-" + "a" * 24,
                "package_content_hash": "b" * 64,
                "package_path": "C:/git/private/review.json",
                "workstream_id": "W4B-review",
                "generated_at": "2026-08-23T00:00:00Z",
                "freshness": "current",
                "stale_reasons": [],
                "risk": {"level": "elevated"},
                "human_approval": {"count": 0, "required": 1},
                "integration": {
                    "eligible": False,
                    "reasons": ["required-human-reviewer-count-not-met"],
                },
                "binding": {
                    "target_oid": "c" * 40,
                    "candidate_head": "d" * 40,
                    "scope_fingerprint": "e" * 64,
                },
            }
        ],
        "inventory": {
            "inventory_schema_version": 1,
            "inventory_id": "inventory-fixture",
            "content_hash": "f" * 64,
            "classification_counts": {
                "registered-active": 1,
                "review-integration-pending": 0,
                "integrated-closed": 0,
                "legacy-unmanaged": 0,
                "generated-disposable": 0,
                "evidence-retained": 0,
                "unknown": 0,
            },
            "classification_labels": {
                "registered-active": "Registered active",
                "review-integration-pending": "Review/Integration pending",
                "integrated-closed": "Integrated/Closed",
                "legacy-unmanaged": "Legacy unmanaged",
                "generated-disposable": "Generated disposable",
                "evidence-retained": "Evidence/retained",
                "unknown": "Unknown",
            },
            "entries": [
                {
                    "workspace_id": "workspace-fixture",
                    "path": "C:/workspace/private",
                    "classification_label": "Registered active",
                    "protections": ["active-or-pending-workstream"],
                    "unknown": ["remote-state-not-observed"],
                    "estimated_reclaim_bytes": 4096,
                }
            ],
        },
        "cleanup": [
            {
                "workspace_id": "workspace-fixture",
                "path": "C:/workspace/private",
                "status": "blocked",
                "eligible": False,
                "reasons": ["workstream-is-active"],
                "unknown": [],
                "estimated_reclaim_bytes": 4096,
                "actions": actions,
            }
        ],
        "closures": [],
        "action_receipts": [
            {
                "receipt_id": "cleanup-action-" + "1" * 24,
                "action": "remove-worktree",
                "caller_attested_performed": True,
                "deletion_inferred": False,
                "authorization_id": "cleanup-authorization-fixture",
                "receipt_path": "C:/git/private/receipt.json",
            }
        ],
        "writes_performed": False,
        "network_performed": False,
    }
    base.update(overrides)
    return base


class PersonalObservatoryTests(unittest.TestCase):

    def test_health_projection_separates_36_worktree_like_delivery_reconciliation_and_hygiene(self):
        def card(workstream_id, *, phase="implementing", freshness="current", session=True,
                 current=False, primary=False, group="active"):
            return {
                "workstream_id": workstream_id,
                "branch": f"codex/{workstream_id}",
                "availability": "available",
                "has_session": session,
                "session_state": "current" if freshness == "current" else "stale",
                "evidence_freshness": freshness,
                "lifecycle_phase": phase,
                "is_current": current,
                "is_primary": primary,
                "display_group": group,
            }

        current = [card(f"current-{index}") for index in range(4)]
        current.append(card("review-pending", phase="review-ready"))
        stale = [card(f"stale-{index}", freshness="stale", group="reconciliation") for index in range(2)]
        primary = card("canonical-root", session=False, primary=True, group="protected-primary")
        candidate = card("candidate-local", session=False, current=True, group="candidate-unregistered")
        legacy = [
            card(f"legacy-{index}", session=False, group="worktree-only")
            for index in range(31)
        ]
        findings = [{
            "finding_id": "direct-current", "kind": "direct",
            "workstream_ids": ["current-0", "current-1"],
        }]
        findings.extend({
            "finding_id": f"direct-stale-{index}", "kind": "direct",
            "workstream_ids": ["current-0", "stale-0"],
        } for index in range(37))
        findings.extend({
            "finding_id": f"unknown-legacy-{index}", "kind": "unknown",
            "workstream_ids": [f"legacy-{index % 31}"],
        } for index in range(32))
        bundle = _w3_bundle(
            review_queue=[
                {"queue_status": "pending", "freshness": "current", "workstream_id": "review-pending"},
                {"queue_status": "pending", "freshness": "stale", "workstream_id": "stale-0"},
            ],
            inventory={
                "classification_counts": {
                    "registered-active": 4,
                    "review-integration-pending": 1,
                    "integrated-closed": 0,
                    "legacy-unmanaged": 31,
                    "generated-disposable": 0,
                    "evidence-retained": 2,
                    "unknown": 0,
                },
                "entries": [
                    {"estimated_reclaim_bytes": 1024} for _ in range(31)
                ],
            },
        )
        cards = [*current, *stale, primary, candidate, *legacy]
        health = personal_observatory._derive_health_projection(cards, findings, bundle)
        self.assertEqual(health["delivery_now"]["current_blocker_count"], 1)
        self.assertEqual(health["delivery_now"]["workstream_count"], 5)
        self.assertEqual(health["reconciliation"]["finding_count"], 37)
        self.assertEqual(health["reconciliation"]["stale_session_count"], 2)
        self.assertEqual(health["reconciliation"]["stale_review_count"], 1)
        self.assertEqual(health["reconciliation"]["unregistered_candidate_count"], 1)
        self.assertEqual(health["workspace_hygiene"]["total_worktrees"], 38)
        self.assertEqual(health["workspace_hygiene"]["legacy_unmanaged"], 31)
        self.assertEqual(health["workspace_hygiene"]["retained"], 2)
        self.assertEqual(health["workspace_hygiene"]["estimated_reclaim_bytes"], 31 * 1024)
        self.assertEqual(health["unknown_accounting"]["total"], 32)
        self.assertEqual(health["unknown_accounting"]["hygiene"], 32)
        panel = render_personal_observatory_panel(_ready_projection(
            current=candidate, workstreams=cards, findings=findings,
            w3_evidence=bundle, health=health,
        ))
        self.assertIn("交付状态", panel)
        self.assertIn("1 个确定的直接重叠需要处理", panel)
        self.assertIn("待确认的任务／历史状态", panel)
        self.assertIn("工作区清理建议", panel)
        self.assertIn("当前候选尚未登记任务，无法判断交付资格", panel)
        self.assertNotIn("需要对账", panel)
        self.assertNotIn("工作区卫生", panel)
        self.assertNotIn("38 个确定的直接重叠", panel)
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
        self.assertEqual(groups["PO-W1-FIXTURE"], "reconciliation")
        self.assertEqual(groups["PO-W2-FIXTURE"], "reconciliation")
        self.assertIn("protected-primary", groups.values())
        self.assertGreaterEqual(projection["finding_counts"].get("direct", 0), 1)
        self.assertEqual(projection["health"]["delivery_now"]["current_blocker_count"], 0)
        self.assertGreaterEqual(projection["health"]["reconciliation"]["finding_count"], 1)
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

            with mock.patch.object(
                collaboration, "inspect_worktree_status", guarded
            ), mock.patch.object(
                personal_observatory,
                "_collect_w3_projection",
                side_effect=AssertionError("automatic W3 provider crossed exclusion boundary"),
            ) as w3_provider:
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
        w3_provider.assert_not_called()
        self.assertIsNone(projection["w3_evidence"])
        self.assertEqual(projection["w3_provider_error"]["type"], "IsolationBoundary")
        self.assertEqual(
            projection["w3_provider_error"]["message"],
            "excluded-worktree-isolation-boundary",
        )
        self.assertTrue(
            all(slot["status"] == "unavailable" for slot in projection["w3"].values())
        )

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
        groups = {item["display_group"] for item in projection["workstreams"]}
        self.assertIn("protected-primary", groups)
        self.assertIn("candidate-unregistered", groups)
        self.assertTrue(groups.issubset({"protected-primary", "candidate-unregistered", "worktree-only"}))
        self.assertEqual(projection["health"]["delivery_now"]["current_blocker_count"], 0)
        self.assertEqual(projection["health"]["reconciliation"]["unregistered_candidate_count"], 1)
        self.assertNotIn("safe", str(projection).lower())

    def test_no_review_packages_still_projects_bounded_w3_inventory(self):
        original_cleanup = workspace_cleanup.compute_workspace_cleanup_eligibility
        with CollaborationGitFixture() as fixture, mock.patch.object(
            workspace_cleanup,
            "compute_workspace_cleanup_eligibility",
            wraps=original_cleanup,
        ) as cleanup_provider:
            projection = build_personal_observatory_projection(
                fixture.worktree_a, include_local_worktrees=False
            )
        self.assertEqual(projection["w3"]["review_queue"]["status"], "empty")
        self.assertEqual(projection["w3"]["review_queue"]["label"], "No review packages")
        self.assertEqual(projection["w3_evidence"]["review_queue"], [])
        counts = projection["w3_evidence"]["inventory"]["classification_counts"]
        self.assertEqual(len(counts), 7)
        self.assertEqual(
            set(counts),
            {
                "registered-active",
                "review-integration-pending",
                "integrated-closed",
                "legacy-unmanaged",
                "generated-disposable",
                "evidence-retained",
                "unknown",
            },
        )
        self.assertFalse(projection["w3_evidence"]["writes_performed"])
        self.assertFalse(projection["w3_evidence"]["network_performed"])
        cleanup_candidates = [
            item for item in projection["w3_evidence"]["inventory"]["entries"]
            if item["recommended_action"] == "evaluate-cleanup-eligibility"
        ]
        self.assertEqual(cleanup_provider.call_count, len(cleanup_candidates))
        self.assertEqual(len(projection["w3_evidence"]["cleanup"]), len(cleanup_candidates))

    def test_w3_provider_consumes_real_core_review_bundle_without_writes(self):
        with CollaborationGitFixture() as fixture:
            (fixture.worktree_b / "README.md").write_text(
                "# fixture\nW4 consumes canonical W3 evidence.\n", encoding="utf-8"
            )
            fixture.git(fixture.worktree_b, "add", "README.md")
            fixture.git(fixture.worktree_b, "commit", "-m", "candidate for W4 projection")
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W4-real-W3-provider",
                primary_subsystem_id="project-structure",
                expected_writes=("README.md",),
                validation_surfaces=(PASS_COMMAND,),
                lifecycle_phase="implementing",
            )
            refreshed = refresh_workstream_scope(
                fixture.worktree_b,
                include_local_worktrees=False,
                occurred_at="2026-08-23T00:00:00Z",
            )
            self.assertTrue(refreshed["expansion"]["allowed"], refreshed)
            transition_workstream_session(
                fixture.worktree_b,
                lifecycle_phase="validating",
                evidence_freshness="current",
                reason="fixture validation inputs ready",
                occurred_at="2026-08-23T00:01:00Z",
            )
            with mock.patch.object(
                socket, "socket", side_effect=AssertionError("network is forbidden")
            ), mock.patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network is forbidden"),
            ):
                generated = generate_review_package(fixture.worktree_b)
                before = fixture.git(
                    fixture.worktree_b, "status", "--porcelain=v1"
                ).stdout
                projection = build_personal_observatory_projection(
                    fixture.worktree_b, include_local_worktrees=False
                )
                after = fixture.git(
                    fixture.worktree_b, "status", "--porcelain=v1"
                ).stdout

        self.assertEqual(before, after)
        package = generated["review_package"]
        review = projection["w3_evidence"]["review_queue"][0]
        self.assertEqual(review["package_id"], package["package_id"])
        self.assertEqual(review["freshness"], "current")
        self.assertEqual(review["risk"], package["risk"])
        self.assertEqual(review["human_approval"]["count"], 0)
        self.assertEqual(review["human_approval"]["required"], 1)
        self.assertFalse(review["integration"]["eligible"])
        self.assertIn(
            "required-human-reviewer-count-not-met", review["integration"]["reasons"]
        )
        self.assertEqual(review["binding"], package["binding"])
        self.assertFalse(review["integration"]["integration_ref_updated"])
        self.assertFalse(review["integration"]["writes_performed"])
        self.assertFalse(projection["w3_evidence"]["network_performed"])

    def test_w3_provider_failure_and_old_schema_keep_w4a_fallback(self):
        with CollaborationGitFixture() as fixture, mock.patch.object(
            personal_observatory,
            "_collect_w3_projection",
            side_effect=ValueError("provider failed"),
        ):
            failed = build_personal_observatory_projection(
                fixture.worktree_a, include_local_worktrees=False
            )
        self.assertIsNone(failed["w3_evidence"])
        self.assertEqual(failed["w3_provider_error"]["type"], "ValueError")
        self.assertTrue(all(
            slot["detail"] == "W3 provider unavailable or incompatible · Unknown"
            for slot in failed["w3"].values()
        ))

        with CollaborationGitFixture() as fixture:
            old = build_personal_observatory_projection(
                fixture.worktree_a,
                include_local_worktrees=False,
                w3_projection={"provider_schema_version": 0},
            )
        self.assertIsNone(old["w3_evidence"])
        self.assertIn("unsupported W3", old["w3_provider_error"]["message"])
        self.assertEqual(old["w3"]["integration_eligibility"]["label"], "Unavailable")

        source = (
            ROOT
            / "packages"
            / "project-orrery-observatory"
            / "src"
            / "project_orrery_observatory"
            / "personal_observatory.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("from project_orrery_core.review import _private_area", source)
        self.assertNotIn("from project_orrery_core.review import _read_regular_json", source)
        legacy_slots = _ready_projection()["w3"]
        self.assertEqual(personal_observatory._w3_slots(legacy_slots), legacy_slots)

    def test_w3_projection_keeps_policy_actions_and_receipts_separate(self):
        bundle = _w3_bundle()
        with CollaborationGitFixture() as fixture:
            projection = build_personal_observatory_projection(
                fixture.worktree_a,
                include_local_worktrees=False,
                w3_projection=bundle,
            )
        self.assertEqual(projection["w3"]["review_queue"]["status"], "ready")
        self.assertEqual(projection["w3"]["integration_eligibility"]["status"], "blocked")
        actions = projection["w3_evidence"]["cleanup"][0]["actions"]
        self.assertEqual(len(actions), 4)
        self.assertTrue(all(not item["authorized"] for item in actions.values()))
        self.assertTrue(all(not item["performed"] for item in actions.values()))
        receipt = projection["w3_evidence"]["action_receipts"][0]
        self.assertTrue(receipt["caller_attested_performed"])
        self.assertFalse(receipt["deletion_inferred"])
        panel = render_personal_observatory_panel(projection)
        self.assertIn("required-human-reviewer-count-not-met", panel)
        self.assertIn("all seven classes", panel)
        self.assertIn("active-or-pending-workstream", panel)
        self.assertIn("remote-state-not-observed", panel)
        self.assertIn("4.0 KB", panel)
        self.assertIn("authorized False · performed False", panel)
        self.assertIn("deletion inferred=false", panel)
        self.assertIn("c" * 40, panel)
        self.assertIn("f" * 64, panel)

    def test_renderer_has_four_zones_progressive_detail_and_no_actions(self):
        projection = _ready_projection()
        panel = render_personal_observatory_panel(projection)
        self.assertIn('data-zone="project-status"', panel)
        self.assertIn('data-zone="attention"', panel)
        self.assertIn('data-zone="workstreams"', panel)
        self.assertIn('data-zone="subsystems"', panel)
        self.assertIn('data-state="no-worktree"', panel)
        self.assertIn("当前不能判断审查、集成和清理资格", panel)
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
        self.assertIn("交付状态", panel)
        self.assertIn("谁在推进什么", panel)
        self.assertIn("查看证据", panel)
        self.assertIn("技术证据", panel)
        self.assertIn('data-display-group="worktree-only"', panel)
        self.assertIn("没有任务登记", panel)
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
                    ROOT / "docs", ROOT / "AGENTS.md", ROOT, "Atlas Control"
                )
        self.assertEqual(result, (sentinel[0], sentinel[1], None, None))

    def test_workspace_maintenance_page_is_static_read_only_or_explicitly_host_local(self):
        base = (
            "<html><head><style></style></head><body><aside class=\"sidebar\">"
            '<a class="nav-item" data-target="trends"><span class="dot proposed"></span><span class="lbl">🔭 路线与趋势</span></a></aside>'
            '<main class="content"></main><aside class="toc" id="toc"></aside></body></html>'
        )
        static = inject_personal_observatory(base, _ready_projection())
        self.assertIn('data-target="workspace-maintenance"', static)
        self.assertIn('id="workspace-maintenance"', static)
        self.assertIn('data-maintenance-control="false"', static)
        self.assertIn("无定时任务", static)
        self.assertIn("分支保留", static)

        binding = {
            "workspace_id": "workspace-1",
            "worktree_identity": "0" * 64,
            "resolved_path": "C:/fixture/worktree",
            "git_dir": "C:/fixture/repo/.git/worktrees/fixture",
            "head": "1" * 40,
            "branch": "refs/heads/codex/fixture",
            "dirty_fingerprint": "9" * 64,
            "workstream_id": "W6",
            "session_phase": "closed",
            "integration_oid": "2" * 40,
            "inventory_content_hash": "3" * 64,
            "closure_id": "closure-1",
            "review_package_id": "review-1",
            "review_package_content_hash": "4" * 64,
            "validation_refs_hash": "5" * 64,
            "candidate_head": "1" * 40,
            "tracked_changes": [],
            "untracked_paths": [],
            "ignored_paths_hash": "6" * 64,
            "allowlisted_ignored_paths": [],
            "unique_commits": [],
            "evidence_hash": "7" * 64,
        }
        maintenance = {
            "status": "ready",
            "control_available": True,
            "last_run": {"status": "succeeded", "counts": {"worktrees": 9, "suggested": 1, "estimated_reclaim_bytes": 1024}},
            "queue": [{"item_id": "maintenance-item-" + "8" * 24, "workspace_id": "workspace-1", "workspace_path": "C:/fixture/worktree", "lifecycle": "suggested", "earliest_execute_at": "2026-08-27T00:00:00Z", "binding": binding}],
            "authorizations": [],
            "protected_reasons": {"primary-worktree": 1, "unknown:reparse": 1},
            "policy": {"integrated_grace_days": 7, "auto_remove_eligible_worktrees": False},
            "receipts": [],
            "cache": {
                "status": "current",
                "entries": [{
                    "workspace_id": "workspace-1",
                    "registered_path": "C:/fixture/worktree",
                    "branch": "refs/heads/codex/fixture",
                    "cache_state": "current",
                    "scanned_at": "2026-08-29T00:00:00Z",
                    "reasons": [],
                    "unknown": [],
                    "is_primary_worktree": False,
                    "remove_worktree_eligible": True,
                }, {
                    "workspace_id": "workspace-unknown",
                    "registered_path": "C:/fixture/unknown",
                    "branch": "refs/heads/codex/unknown",
                    "cache_state": "stale",
                    "scanned_at": "2026-08-28T00:00:00Z",
                    "reasons": ["target-refresh-failed"],
                    "unknown": ["cache-corrupt"],
                    "is_primary_worktree": False,
                    "remove_worktree_eligible": False,
                }],
            },
            "background_refresh": {"status": "idle"},
            "historical_evidence_warnings": [{
                "source": "legacy-last-run",
                "message": "unsupported maintenance contract schema version",
                "display_state": "historical-unknown",
                "affects_current_refresh": False,
                "affects_current_eligibility": False,
            }],
        }
        dynamic = inject_personal_observatory(base, _ready_projection(maintenance=maintenance))
        self.assertIn('data-maintenance-control="true"', dynamic)
        self.assertIn("后台增量扫描", dynamic)
        self.assertIn('data-maintenance-preflight="workspace-1"', dynamic)
        self.assertIn("快速删除", dynamic)
        self.assertIn('data-maintenance-eligible-count>1</b>', dynamic)
        self.assertEqual(dynamic.count('data-maintenance-preflight="workspace-1"'), 1)
        self.assertIn('class="mo-cache-state stale">历史状态</span>', dynamic)
        self.assertIn("主要保护原因", dynamic)
        self.assertIn("旧记录已原样保留", dynamic)
        self.assertIn("window.confirm", dynamic)
        self.assertIn("只删除工作区，保留分支和提交", dynamic)

        no_eligible = json.loads(json.dumps(maintenance))
        no_eligible["cache"]["entries"][0]["remove_worktree_eligible"] = False
        protected_dynamic = inject_personal_observatory(
            base, _ready_projection(maintenance=no_eligible)
        )
        self.assertIn('data-maintenance-eligible-count>0</b>', protected_dynamic)
        self.assertIn("目前没有可安全删除项", protected_dynamic)
        self.assertNotIn('data-maintenance-preflight="workspace-1"', protected_dynamic)

    def test_unavailable_projection_renders_stable_fallback(self):
        projection = unavailable_personal_observatory_projection(
            ValueError("fixture unavailable")
        )
        panel = render_personal_observatory_panel(projection)
        self.assertIn('data-status="unavailable"', panel)
        self.assertIn("fixture unavailable", panel)
        self.assertIn("只读", panel)
        self.assertFalse(projection["network_performed"])


if __name__ == "__main__":
    unittest.main()
