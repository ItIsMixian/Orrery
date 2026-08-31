from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
):
    sys.path.insert(0, str(source))

from project_orrery_core.collaboration import (  # noqa: E402
    acknowledge_overlap_finding,
    build_workstream_session,
    collect_lineage_ancestry_proofs,
    collect_scope_observation,
    compute_overlap_findings,
    create_worktree,
    inspect_worktree_status,
    write_workstream_session,
)
from project_orrery_observatory.personal_observatory import (  # noqa: E402
    build_personal_observatory_projection,
    render_personal_observatory_panel,
)
from project_orrery_cli import worktree as worktree_cli  # noqa: E402
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


class StackedLineageTests(unittest.TestCase):
    def _commit(self, fixture: CollaborationGitFixture, root: Path, path: str, content: str, message: str) -> str:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        fixture.git(root, "add", path)
        fixture.git(root, "commit", "-m", message)
        return fixture.git(root, "rev-parse", "HEAD").stdout.strip()

    def _add_worktree(
        self, fixture: CollaborationGitFixture, name: str, branch: str, start_oid: str,
    ) -> Path:
        target = fixture.root / name
        fixture.git(
            fixture.repository, "worktree", "add", "-b", branch, str(target), start_oid,
        )
        return target

    def test_stacked_create_binds_exact_local_parent_head(self) -> None:
        parsed = worktree_cli.build_parser().parse_args([
            "session", "write", "--workstream-id", "child-work",
            "--primary-subsystem-id", "project-structure",
            "--base-workstream-id", "parent-work", "--task-base-oid", "a" * 40,
        ])
        self.assertEqual(parsed.base_workstream_id, "parent-work")
        self.assertEqual(parsed.task_base_oid, "a" * 40)
        with CollaborationGitFixture() as fixture:
            parent = fixture.worktree_a
            parent_head = self._commit(
                fixture, parent, "parent.txt", "parent\n", "parent checkpoint",
            )
            write_workstream_session(
                parent, workstream_id="parent-work", primary_subsystem_id="project-structure",
            )
            created = create_worktree(
                parent, workstream_id="child-work", branch="codex/child-work",
                path=fixture.root / "child-work", primary_subsystem_id="project-structure",
                base_workstream_id="parent-work", task_base_oid=parent_head,
            )
            self.assertEqual(created["source"]["task_start_oid"], parent_head)
            self.assertEqual(
                created["status"]["session"]["record"]["lineage"]["status"], "current",
            )
            with self.assertRaisesRegex(ValueError, "exact recorded parent Workstream HEAD"):
                build_workstream_session(
                    fixture.worktree_b, workstream_id="wrong-child",
                    primary_subsystem_id="project-structure", base_workstream_id="parent-work",
                    task_base_oid=fixture.git(fixture.repository, "rev-parse", "main").stdout.strip(),
                )

    def test_w5c_w6_w5d_chain_excludes_only_verified_inheritance(self) -> None:
        with CollaborationGitFixture() as fixture:
            w5c = fixture.worktree_a
            self._commit(
                fixture, w5c, "docs/state/project-structure.md",
                "# Project structure State\nW5C base\n", "W5C authority base",
            )
            w5c_head = self._commit(
                fixture, w5c, "chain/shared.txt", "W5C\n", "W5C shared base",
            )
            write_workstream_session(
                w5c, workstream_id="W5C", primary_subsystem_id="project-structure",
                evidence_freshness="current",
            )

            w6 = self._add_worktree(fixture, "stack-w6", "codex/stack-w6", w5c_head)
            w6_base = w5c_head
            w6_head = self._commit(
                fixture, w6, "chain/w6-only.txt", "W6 base\n", "W6 own delta",
            )
            write_workstream_session(
                w6, workstream_id="W6", primary_subsystem_id="project-structure",
                base_workstream_id="W5C", task_base_oid=w6_base,
                evidence_freshness="current",
            )

            w5d = self._add_worktree(fixture, "stack-w5d", "codex/stack-w5d", w6_head)
            w5d_base = w6_head
            self._commit(
                fixture, w5d, "chain/w6-only.txt", "W5D changed inherited file\n",
                "W5D current-task change",
            )
            w5d_head = self._commit(
                fixture, w5d, "chain/w5d-only.txt", "W5D only\n", "W5D own path",
            )
            write_workstream_session(
                w5d, workstream_id="W5D", primary_subsystem_id="project-structure",
                expected_writes=["packages/component-versions.json"],
                base_workstream_id="W6", task_base_oid=w5d_base,
                evidence_freshness="current",
            )

            scopes = [
                collect_scope_observation(w5c),
                collect_scope_observation(w6),
                collect_scope_observation(w5d),
            ]
            self.assertEqual(
                {entry["path"] for entry in scopes[2]["path_entries"] if "committed" in entry["sources"]},
                {"chain/w5d-only.txt", "chain/w6-only.txt"},
            )
            self.assertNotIn(
                "docs/state/project-structure.md",
                {entry["path"] for entry in scopes[2]["path_entries"]},
            )

            legacy_scopes = []
            for root in (w5c, w6, w5d):
                session = copy.deepcopy(inspect_worktree_status(root)["session"]["record"])
                session["lineage"] = {
                    "lineage_schema_version": 1, "status": "legacy-unknown",
                    "base_workstream_id": None, "task_base_oid": None, "validated_head": None,
                }
                legacy_scopes.append(collect_scope_observation(root, session=session))
            before = compute_overlap_findings(legacy_scopes)
            before_counts = {
                kind: sum(item["kind"] == kind for item in before["findings"])
                for kind in ("direct", "authority")
            }
            self.assertGreater(before_counts["direct"], 0)
            self.assertGreater(before_counts["authority"], 0)

            proofs = collect_lineage_ancestry_proofs(fixture.repository, scopes)
            after = compute_overlap_findings(scopes, lineage_ancestry_proofs=proofs)
            after_counts = {
                kind: sum(item["kind"] == kind for item in after["findings"])
                for kind in ("direct", "authority")
            }
            self.assertEqual(after_counts, {"direct": 0, "authority": 0})
            self.assertEqual(
                {item["status"] for item in after["lineage_summaries"] if item["workstream_id"] != "W5C"},
                {"current"},
            )

            projection = build_personal_observatory_projection(
                fixture.repository, w3_projection={}, captured_at="2026-08-27T23:00:00Z",
            )
            chain_direct = [
                item for item in projection["findings"]
                if item["kind"] == "direct" and set(item["workstream_ids"]).issubset({"W5C", "W6", "W5D"})
            ]
            self.assertEqual(chain_direct, [])
            page = render_personal_observatory_panel(projection)
            self.assertIn("接续任务链", page)
            self.assertIn(w5d_base[:9], page)
            self.assertIn("任务链内独立发现", page)

            sibling = self._add_worktree(
                fixture, "stack-w5e", "codex/stack-w5e", w5d_base,
            )
            self._commit(
                fixture, sibling, "chain/w6-only.txt", "W5E sibling change\n",
                "W5E sibling collision",
            )
            write_workstream_session(
                sibling, workstream_id="W5E", primary_subsystem_id="project-structure",
                expected_writes=["packages/component-versions.json"],
                base_workstream_id="W6", task_base_oid=w5d_base,
                evidence_freshness="current",
            )

            self._commit(
                fixture, w6, "chain/w6-only.txt", "W6 changed after W5D fork\n",
                "W6 post-fork collision",
            )
            write_workstream_session(
                w6, workstream_id="W6", primary_subsystem_id="project-structure",
                base_workstream_id="W5C", task_base_oid=w6_base,
                evidence_freshness="current",
            )
            changed_scopes = [
                collect_scope_observation(w5c),
                collect_scope_observation(w6),
                collect_scope_observation(w5d),
            ]
            changed = compute_overlap_findings(
                changed_scopes,
                lineage_ancestry_proofs=collect_lineage_ancestry_proofs(
                    fixture.repository, changed_scopes
                ),
            )
            collision = next(
                item for item in changed["findings"]
                if item["kind"] == "direct" and item["workstream_ids"] == ["W5D", "W6"]
            )
            self.assertIn("chain/w6-only.txt", collision["path_evidence"])
            self.assertTrue(collision["review_ready_blocked"])
            with self.assertRaisesRegex(ValueError, "cannot be acknowledged"):
                acknowledge_overlap_finding(
                    collision, member_id="local-owner", reason="must not bypass L3", scope_revision=1,
                )

            sibling_scopes = [collect_scope_observation(w5d), collect_scope_observation(sibling)]
            sibling_report = compute_overlap_findings(
                sibling_scopes,
                lineage_ancestry_proofs=collect_lineage_ancestry_proofs(
                    fixture.repository, sibling_scopes
                ),
            )
            self.assertTrue(any(item["kind"] == "direct" for item in sibling_report["findings"]))
            self.assertTrue(any(item["severity"] == "l3" for item in sibling_report["findings"]))

            with self.assertRaisesRegex(ValueError, "existing local commit"):
                build_workstream_session(
                    w5d, workstream_id="invalid-missing", primary_subsystem_id="project-structure",
                    base_workstream_id="W6", task_base_oid="f" * 40,
                )
            unrelated = self._commit(
                fixture, fixture.repository, "unrelated.txt", "main only\n", "non-ancestor base",
            )
            with self.assertRaisesRegex(ValueError, "ancestor of current HEAD"):
                build_workstream_session(
                    w5d, workstream_id="invalid-nonancestor", primary_subsystem_id="project-structure",
                    base_workstream_id="main-work", task_base_oid=unrelated,
                )

            drifted = copy.deepcopy(scopes[2])
            drifted["lineage"]["validated_head"] = w5c_head
            drift_report = compute_overlap_findings(
                [scopes[1], drifted], lineage_ancestry_proofs=proofs,
            )
            summary = next(
                item for item in drift_report["lineage_summaries"]
                if item["workstream_id"] == "W5D"
            )
            self.assertEqual(summary["status"], "input-drift-unknown")
            self.assertTrue(any(item["kind"] == "direct" for item in drift_report["findings"]))

            self.fixture_counts = {"before": before_counts, "after": after_counts}
            self.assertEqual(w5d_head, scopes[2]["head"])


if __name__ == "__main__":
    unittest.main()
