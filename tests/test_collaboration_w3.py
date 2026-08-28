from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
sys.path.insert(0, str(CORE_SOURCE))
sys.path.insert(0, str(CLI_SOURCE))
sys.path.insert(0, str(REPOSITORY_ROOT))

from project_orrery_core.collaboration import (  # noqa: E402
    refresh_workstream_scope,
    transition_workstream_session,
    validate_collaboration_contract,
    worktree_session_path,
    write_workstream_session,
)
from project_orrery_core.review import (  # noqa: E402
    _evaluate_decision_policy,
    _risk_policy,
    assert_clean_integration_worktree,
    compute_cleanup_eligibility,
    compute_integration_eligibility,
    generate_review_package,
    inspect_review_package_freshness,
    record_review_decision,
    write_closure_record,
)
import project_orrery_core.workspace_cleanup as workspace_cleanup  # noqa: E402
from project_orrery_core.workspace_cleanup import (  # noqa: E402
    CLEANUP_ACTIONS,
    compute_workspace_cleanup_eligibility,
    inventory_workspaces,
    record_cleanup_action_receipt,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


PASS_COMMAND = 'python -c "import sys; sys.exit(0)"'
FAIL_COMMAND = 'python -c "import sys; sys.exit(7)"'


def _same_path(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> bool:
    """Compare Windows short/long aliases as one filesystem identity."""
    return os.path.normcase(os.path.realpath(os.path.abspath(left))) == os.path.normcase(
        os.path.realpath(os.path.abspath(right))
    )


class CollaborationW3Tests(unittest.TestCase):
    def _prepare_session(
        self,
        fixture: CollaborationGitFixture,
        *,
        root: Path | None = None,
        workstream_id: str = "W3-review",
        primary_subsystem_id: str = "project-structure",
        affected_subsystem_ids: tuple[str, ...] = (),
        expected_writes: tuple[str, ...] = ("README.md",),
        validation_command: str = PASS_COMMAND,
        member_id: str = "local-owner",
    ) -> dict[str, object]:
        selected = root or fixture.worktree_b
        write_workstream_session(
            selected,
            workstream_id=workstream_id,
            primary_subsystem_id=primary_subsystem_id,
            affected_subsystem_ids=affected_subsystem_ids,
            expected_writes=expected_writes,
            validation_surfaces=[validation_command],
            lifecycle_phase="implementing",
            member_id=member_id,
        )
        refreshed = refresh_workstream_scope(
            selected,
            include_local_worktrees=False,
            occurred_at="2026-08-22T12:00:00Z",
        )
        if not refreshed["expansion"]["allowed"] and refreshed["expansion"]["level"] == "l2":
            refreshed = refresh_workstream_scope(
                selected,
                include_local_worktrees=False,
                confirm_l2=True,
                reason="W3 fixture explicitly includes this Authority or subsystem surface",
                occurred_at="2026-08-22T12:00:30Z",
            )
        self.assertTrue(refreshed["expansion"]["allowed"], refreshed)
        transition_workstream_session(
            selected,
            lifecycle_phase="validating",
            evidence_freshness="current",
            reason="W3 validation inputs are ready",
            occurred_at="2026-08-22T12:01:00Z",
        )
        return refreshed

    def _commit_readme_candidate(self, fixture: CollaborationGitFixture, text: str = "candidate") -> None:
        (fixture.worktree_b / "README.md").write_text(f"# fixture\n{text}\n", encoding="utf-8")
        fixture.git(fixture.worktree_b, "add", "README.md")
        fixture.git(fixture.worktree_b, "commit", "-m", "candidate review change")

    def _ready_package(self, fixture: CollaborationGitFixture) -> dict[str, object]:
        self._commit_readme_candidate(fixture)
        self._prepare_session(fixture)
        return generate_review_package(fixture.worktree_b)

    def _closed_package(self, fixture: CollaborationGitFixture) -> tuple[dict[str, object], dict[str, object]]:
        result = self._ready_package(fixture)
        package = result["review_package"]
        record_review_decision(
            fixture.worktree_b,
            package=package["package_id"],
            action="approve",
            actor_id="local-owner",
            reason="approved for manual fixture integration",
            evidence_refs=[f"git:{package['binding']['candidate_head']}"],
        )
        fixture.git(fixture.repository, "merge", "--no-ff", "--no-edit", "codex/fixture-b")
        final_oid = fixture.git(fixture.repository, "rev-parse", "main").stdout.strip()
        closure = write_closure_record(
            fixture.worktree_b,
            package=package["package_id"],
            final_oid=final_oid,
            actor_id="local-owner",
        )
        return result, closure

    def test_review_package_is_evidence_first_bound_hashed_private_and_zero_network(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._commit_readme_candidate(fixture)
            self._prepare_session(fixture)
            before_status = fixture.git(
                fixture.worktree_b, "status", "--porcelain", "--untracked-files=all"
            ).stdout
            before_head = fixture.git(fixture.worktree_b, "rev-parse", "HEAD").stdout.strip()
            with mock.patch.object(
                socket, "socket", side_effect=AssertionError("network socket opened")
            ), mock.patch.object(
                socket, "create_connection", side_effect=AssertionError("network connection opened")
            ):
                result = generate_review_package(
                    fixture.worktree_b,
                    strategy="rebase",
                    ai_summary="Derived navigation only; evidence remains authoritative.",
                )
            package = result["review_package"]
            validate_collaboration_contract(package)
            self.assertEqual(package["presentation_order"], ["evidence", "ai_summary"])
            self.assertEqual(package["ai_summary"]["authority"], "derived-non-authoritative")
            self.assertEqual(package["evidence"]["speculative_integration"]["result"], "ready-for-human-integration")
            self.assertEqual(package["evidence"]["speculative_integration"]["strategy"], "rebase")
            self.assertEqual(package["binding"]["candidate_head"], before_head)
            self.assertEqual(package["binding"]["collaboration_schema_version"], 1)
            self.assertEqual(len(package["binding"]["finding_set_hash"]), 64)
            self.assertEqual(len(package["binding"]["collaboration_schema_hash"]), 64)
            self.assertEqual(len(package["binding"]["validation_set_hash"]), 64)
            package_path = Path(result["review_package_path"])
            common = Path(
                fixture.git(
                    fixture.worktree_b, "rev-parse", "--path-format=absolute", "--git-common-dir"
                ).stdout.strip()
            )
            package_path.resolve().relative_to(common.resolve())
            self.assertFalse(result["integration_ref_updated"])
            self.assertFalse(result["branch_deleted"])
            self.assertFalse(result["worktree_deleted"])
            self.assertFalse(result["network_performed"])
            self.assertEqual(
                fixture.git(
                    fixture.worktree_b, "status", "--porcelain", "--untracked-files=all"
                ).stdout,
                before_status,
            )
            self.assertEqual(fixture.git(fixture.worktree_b, "rev-parse", "HEAD").stdout.strip(), before_head)

    def test_package_stales_on_candidate_input_drift(self) -> None:
        with CollaborationGitFixture() as fixture:
            result = self._ready_package(fixture)
            package_id = result["review_package"]["package_id"]
            self.assertTrue(inspect_review_package_freshness(fixture.worktree_b, package_id)["fresh"])
            session_path = worktree_session_path(fixture.worktree_b)
            original_session = session_path.read_bytes()
            session = json.loads(original_session.decode("utf-8"))
            session["scope_revision"] += 1
            session["validation_surfaces"].append(FAIL_COMMAND)
            session["finding_history"] = [
                {
                    "schema_version": 1,
                    "contract_type": "overlap-finding",
                    "finding_id": "finding-test-drift",
                    "kind": "unknown",
                    "disposition": "resolved",
                    "severity": "l2",
                    "workstream_ids": [session["workstream_id"]],
                    "path_evidence": [],
                    "authority_surfaces": [],
                    "validation_surfaces": [],
                    "required_member_ids": [session["member_id"]],
                    "acknowledgements": [],
                    "member_id": session["member_id"],
                    "host_id": session["host_id"],
                    "visibility": "worktree-local",
                    "observability": "local",
                    "created_at": "2026-08-22T12:02:00Z",
                }
            ]
            session_path.write_text(json.dumps(session), encoding="utf-8")
            private_drift = inspect_review_package_freshness(fixture.worktree_b, package_id)
            self.assertIn("scope-revision-changed", private_drift["stale_reasons"])
            self.assertIn("finding-set-changed", private_drift["stale_reasons"])
            self.assertIn("validation-set-changed", private_drift["stale_reasons"])
            session_path.write_bytes(original_session)
            (fixture.worktree_b / "after-review.txt").write_text("drift\n", encoding="utf-8")
            fixture.git(fixture.worktree_b, "add", "after-review.txt")
            fixture.git(fixture.worktree_b, "commit", "-m", "drift after review")
            stale = inspect_review_package_freshness(fixture.worktree_b, package_id)
            self.assertFalse(stale["fresh"])
            self.assertIn("candidate-head-changed", stale["stale_reasons"])
            with self.assertRaisesRegex(ValueError, "stale review package"):
                record_review_decision(
                    fixture.worktree_b,
                    package=package_id,
                    action="approve",
                    actor_id="local-owner",
                    reason="stale approval must fail",
                    evidence_refs=["git:stale"],
                )

        with CollaborationGitFixture() as fixture:
            result = self._ready_package(fixture)
            package_id = result["review_package"]["package_id"]
            (fixture.repository / "target-drift.txt").write_text("target drift\n", encoding="utf-8")
            fixture.git(fixture.repository, "add", "target-drift.txt")
            fixture.git(fixture.repository, "commit", "-m", "target drift after review")
            target_stale = inspect_review_package_freshness(fixture.worktree_b, package_id)
            self.assertIn("target-oid-changed", target_stale["stale_reasons"])

    def test_dirty_integration_worktree_and_conflicting_dry_run_fail_closed(self) -> None:
        with CollaborationGitFixture() as fixture:
            with tempfile.TemporaryDirectory(prefix="orrery-dirty-integration-") as temporary:
                integration = Path(temporary) / "worktree"
                fixture.git(fixture.repository, "worktree", "add", "--detach", str(integration), "main")
                try:
                    (integration / "dirty.txt").write_text("dirty\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "must be clean"):
                        assert_clean_integration_worktree(integration)
                finally:
                    fixture.git(fixture.repository, "worktree", "remove", "--force", str(integration))

        with CollaborationGitFixture() as fixture:
            self._commit_readme_candidate(fixture, "candidate side")
            (fixture.repository / "README.md").write_text("# fixture\ntarget side\n", encoding="utf-8")
            fixture.git(fixture.repository, "add", "README.md")
            fixture.git(fixture.repository, "commit", "-m", "target conflicting change")
            self._prepare_session(fixture)
            result = generate_review_package(fixture.worktree_b)
            report = result["review_package"]["evidence"]["speculative_integration"]
            self.assertEqual(report["merge_result"], "conflicted")
            self.assertIn("README.md", report["conflict_paths"])
            self.assertEqual(report["result"], "failed")
            self.assertFalse(result["integration_ref_updated"])

    def test_validation_failure_and_candidate_state_drift_block_review_ready(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._commit_readme_candidate(fixture)
            self._prepare_session(fixture, validation_command=FAIL_COMMAND)
            result = generate_review_package(fixture.worktree_b)
            package = result["review_package"]
            self.assertEqual(package["evidence"]["validations"][0]["exit_code"], 7)
            self.assertEqual(package["evidence"]["speculative_integration"]["result"], "blocked")

        with CollaborationGitFixture() as fixture:
            feature = fixture.worktree_b / "packages" / "feature.py"
            feature.parent.mkdir()
            feature.write_text("VALUE = 1\n", encoding="utf-8")
            fixture.git(fixture.worktree_b, "add", "packages/feature.py")
            fixture.git(fixture.worktree_b, "commit", "-m", "implementation without State")
            self._prepare_session(
                fixture,
                primary_subsystem_id="release-and-toolchain",
                expected_writes=("packages/feature.py",),
            )
            result = generate_review_package(fixture.worktree_b)
            alignment = result["review_package"]["evidence"]["state_alignment"]
            self.assertEqual(alignment["result"], "failed")
            self.assertIn(
                "implementation-changed-without-candidate-state-update",
                {item["reason"] for item in alignment["checks"]},
            )

    def test_risk_policy_human_actions_and_ai_only_do_not_satisfy_review(self) -> None:
        team_risk = _risk_policy(project_mode="team", changed_paths=["README.md"], findings=[])
        self.assertEqual(team_risk["required_approval_capability"], "integrator")
        team_package = {"risk": team_risk}
        reviewer_only = {
            "action": "approve",
            "actor_id": "team-reviewer",
            "actor_kind": "human",
            "actor_is_author": False,
            "actor_capabilities": ["reviewer"],
            "decided_at": "2026-08-22T12:00:00Z",
            "decision_id": "decision-reviewer-only",
        }
        self.assertIn(
            "required-integrator-approval-missing",
            _evaluate_decision_policy(team_package, [reviewer_only])["reasons"],
        )
        integrator = dict(reviewer_only)
        integrator.update(
            {
                "actor_id": "team-integrator",
                "actor_capabilities": ["reviewer", "integrator"],
                "decision_id": "decision-integrator",
            }
        )
        self.assertTrue(_evaluate_decision_policy(team_package, [integrator])["passed"])
        with CollaborationGitFixture() as fixture:
            result = self._ready_package(fixture)
            package_id = result["review_package"]["package_id"]
            missing = compute_integration_eligibility(fixture.worktree_b, package_id)
            self.assertFalse(missing["eligible"])
            self.assertIn("required-human-reviewer-count-not-met", missing["reasons"])
            with self.assertRaisesRegex(ValueError, "AI or Agent actors"):
                record_review_decision(
                    fixture.worktree_b,
                    package=package_id,
                    action="approve",
                    actor_id="ai-reviewer",
                    actor_kind="ai",
                    actor_capabilities=["reviewer"],
                    reason="AI-only approval is non-authoritative",
                    evidence_refs=["git:ai-summary"],
                )
            approved = record_review_decision(
                fixture.worktree_b,
                package=package_id,
                action="approve",
                actor_id="local-owner",
                reason="personal ordinary change reviewed against raw evidence",
                evidence_refs=[f"git:{result['review_package']['binding']['candidate_head']}"],
                decided_at="2026-08-22T12:10:00Z",
            )
            validate_collaboration_contract(approved["decision"])
            self.assertTrue(compute_integration_eligibility(fixture.worktree_b, package_id)["eligible"])
            hold = record_review_decision(
                fixture.worktree_b,
                package=package_id,
                action="hold",
                actor_id="local-owner",
                reason="pause after new human concern",
                evidence_refs=["git:human-concern"],
                decided_at="2026-08-22T12:11:00Z",
            )
            self.assertEqual(hold["decision"]["action"], "hold")
            self.assertFalse(compute_integration_eligibility(fixture.worktree_b, package_id)["eligible"])

    def test_elevated_authority_change_requires_non_author_reviewer(self) -> None:
        with CollaborationGitFixture() as fixture:
            state = fixture.worktree_b / "docs" / "state" / "project-structure.md"
            state.write_text("# Project structure State\n\nCandidate fact.\n", encoding="utf-8")
            fixture.git(fixture.worktree_b, "add", str(state.relative_to(fixture.worktree_b)))
            fixture.git(fixture.worktree_b, "commit", "-m", "candidate State update")
            self._prepare_session(
                fixture,
                expected_writes=("docs/state/project-structure.md",),
            )
            result = generate_review_package(fixture.worktree_b)
            package = result["review_package"]
            self.assertEqual(package["risk"]["level"], "elevated")
            self.assertTrue(package["risk"]["non_author_reviewer_required"])
            record_review_decision(
                fixture.worktree_b,
                package=package["package_id"],
                action="approve",
                actor_id="local-owner",
                reason="author self review",
                evidence_refs=["repository:docs/state/project-structure.md"],
            )
            self.assertIn(
                "required-non-author-reviewer-missing",
                compute_integration_eligibility(fixture.worktree_b, package["package_id"])["reasons"],
            )
            record_review_decision(
                fixture.worktree_b,
                package=package["package_id"],
                action="approve",
                actor_id="independent-reviewer",
                actor_capabilities=["reviewer"],
                reason="independent Authority review",
                evidence_refs=["repository:docs/state/project-structure.md"],
            )
            final_eligibility = compute_integration_eligibility(
                fixture.worktree_b, package["package_id"]
            )
            self.assertTrue(final_eligibility["eligible"], final_eligibility)

    def test_temporary_and_conflicting_adr_numbers_block_integration(self) -> None:
        with CollaborationGitFixture() as fixture:
            target_adr = fixture.repository / "docs" / "decisions" / "0001-existing.md"
            target_adr.parent.mkdir(parents=True)
            target_adr.write_text("# ADR-0001 existing\n", encoding="utf-8")
            fixture.git(fixture.repository, "add", "docs/decisions/0001-existing.md")
            fixture.git(fixture.repository, "commit", "-m", "canonical ADR number")
            candidate_adr = fixture.worktree_b / "docs" / "decisions" / "0001-conflict.md"
            candidate_adr.parent.mkdir(parents=True)
            candidate_adr.write_text(
                "# PO-DEC-W3-CONFLICT\n\nProposed formal reference ADR-0001.\n",
                encoding="utf-8",
            )
            fixture.git(fixture.worktree_b, "add", "docs/decisions/0001-conflict.md")
            fixture.git(fixture.worktree_b, "commit", "-m", "conflicting candidate ADR")
            self._prepare_session(
                fixture,
                primary_subsystem_id="documentation-system",
                expected_writes=("docs/decisions/0001-conflict.md",),
            )
            result = generate_review_package(fixture.worktree_b)
            adr = result["review_package"]["evidence"]["adr_alignment"]
            self.assertEqual(adr["result"], "failed")
            self.assertIn("formal-adr-number-conflict", adr["blockers"])
            self.assertIn("PO-DEC-W3-CONFLICT", adr["temporary_ids"])

    def test_closure_and_cleanup_are_private_advisory_and_invalidate_on_local_files(self) -> None:
        with CollaborationGitFixture() as fixture:
            result, closure = self._closed_package(fixture)
            package = result["review_package"]
            closure_path = Path(closure["closure_path"])
            common = Path(
                fixture.git(
                    fixture.worktree_b, "rev-parse", "--path-format=absolute", "--git-common-dir"
                ).stdout.strip()
            )
            closure_path.resolve().relative_to(common.resolve())
            self.assertFalse(closure["author_worktree_files_changed"])
            self.assertTrue(
                _same_path(
                    closure["closure_record"]["original_workspace_path"], fixture.worktree_b
                )
            )
            self.assertEqual(closure["closure_record"]["final_head"], package["binding"]["candidate_head"])
            self.assertEqual(closure["closure_record"]["actual_cleanup_actions"], [])
            eligible = compute_cleanup_eligibility(
                fixture.worktree_b, package=package["package_id"]
            )
            self.assertTrue(eligible["eligible"], eligible["reasons"])
            self.assertEqual(set(eligible["actions"]), set(CLEANUP_ACTIONS))
            self.assertTrue(all(not item["performed"] for item in eligible["actions"].values()))
            (fixture.worktree_b / "local-only.txt").write_text("preserve\n", encoding="utf-8")
            invalidated = compute_cleanup_eligibility(
                fixture.worktree_b, package=package["package_id"]
            )
            self.assertFalse(invalidated["eligible"])
            self.assertIn("unknown-untracked-paths-present", invalidated["reasons"])

    def test_inventory_is_bounded_and_legacy_unknown_requires_explicit_adoption(self) -> None:
        with CollaborationGitFixture() as fixture:
            undiscovered = fixture.root / "same-prefix-but-not-a-candidate"
            undiscovered.mkdir()
            inventory = inventory_workspaces(
                fixture.worktree_b,
                workspace_roots=[fixture.root],
                candidate_paths=[fixture.clone],
            )
            paths = {Path(item["path"]) for item in inventory["entries"]}
            self.assertIn(fixture.clone, paths)
            self.assertNotIn(undiscovered, paths)
            clone = next(item for item in inventory["entries"] if Path(item["path"]) == fixture.clone)
            self.assertEqual(clone["classification"], "legacy-unmanaged")
            self.assertFalse(clone["explicitly_adopted_or_classified"])
            self.assertIn("explicit-adoption-or-classification-required", clone["unknown"])
            self.assertFalse(inventory["source_contract"]["recursive_disk_or_prefix_discovery"])
            blocked = compute_workspace_cleanup_eligibility(
                fixture.worktree_b,
                workspace_path=fixture.clone,
                workspace_roots=[fixture.root],
            )
            self.assertIn(
                "legacy-or-unknown-workspace-requires-explicit-adoption", blocked["reasons"]
            )
            adopted = compute_workspace_cleanup_eligibility(
                fixture.worktree_b,
                workspace_path=fixture.clone,
                workspace_roots=[fixture.root],
                classifications={str(fixture.clone): "legacy-unmanaged"},
            )
            self.assertNotIn(
                "legacy-or-unknown-workspace-requires-explicit-adoption", adopted["reasons"]
            )
            self.assertIn("git-identity-or-common-dir-not-verified", adopted["reasons"])
            self.assertFalse(adopted["eligible"])

    def test_active_benchmark_recovery_and_path_escape_are_retained_or_blocked(self) -> None:
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="active-task",
                primary_subsystem_id="project-structure",
                expected_writes=["README.md"],
                lifecycle_phase="implementing",
            )
            active_inventory = inventory_workspaces(fixture.worktree_b)
            active = next(
                item
                for item in active_inventory["entries"]
                if _same_path(item["path"], fixture.worktree_b)
            )
            self.assertEqual(active["classification"], "registered-active")
            self.assertIn("active-or-pending-workstream", active["protections"])
            active_gate = compute_workspace_cleanup_eligibility(
                fixture.worktree_b, workspace_path=fixture.worktree_b
            )
            self.assertIn("workstream-is-active", active_gate["reasons"])

            benchmark = fixture.root / "raw-evidence"
            recovery = fixture.root / "immutable-recovery"
            benchmark.mkdir()
            recovery.mkdir()
            (benchmark / "manifest.json").write_text("{}\n", encoding="utf-8")
            (recovery / "recovery.txt").write_text("retain\n", encoding="utf-8")
            retained_inventory = inventory_workspaces(
                fixture.worktree_b,
                workspace_roots=[fixture.root],
                candidate_paths=[benchmark, recovery],
                classifications={
                    str(benchmark): "evidence-retained",
                    str(recovery): "unknown",
                },
                retained_paths=[benchmark],
                recovery_paths=[recovery],
            )
            by_path = {Path(item["path"]): item for item in retained_inventory["entries"]}
            self.assertIn("evidence-retention-policy", by_path[benchmark]["protections"])
            self.assertIn("recovery-or-immutable-policy", by_path[recovery]["protections"])
            for selected, extra in ((benchmark, {"retained_paths": [benchmark]}), (recovery, {"recovery_paths": [recovery]})):
                gate = compute_workspace_cleanup_eligibility(
                    fixture.worktree_b,
                    workspace_path=selected,
                    workspace_roots=[fixture.root],
                    classifications={str(selected): "evidence-retained" if selected == benchmark else "unknown"},
                    **extra,
                )
                self.assertIn("workspace-is-protected-or-retained", gate["reasons"])
                self.assertFalse(gate["eligible"])

            link = fixture.root / "bounded-root" / "escape-link"
            link.parent.mkdir()
            link.mkdir()
            with mock.patch.object(workspace_cleanup, "_has_reparse_or_symlink", return_value=True):
                escaped = inventory_workspaces(
                    fixture.worktree_b,
                    workspace_roots=[link.parent],
                    candidate_paths=[link],
                    classifications={str(link): "generated-disposable"},
                )
            escaped_entry = next(item for item in escaped["entries"] if Path(item["path"]) == link)
            self.assertFalse(escaped_entry["path_safe"])
            self.assertIn("symlink-or-reparse-path-boundary", escaped_entry["unknown"])

    def test_unique_commit_unknown_files_and_sensitive_ignored_paths_block_cleanup(self) -> None:
        with CollaborationGitFixture() as fixture:
            result, _closure = self._closed_package(fixture)
            (fixture.worktree_b / "unique.txt").write_text("unique\n", encoding="utf-8")
            fixture.git(fixture.worktree_b, "add", "unique.txt")
            fixture.git(fixture.worktree_b, "commit", "-m", "unique after closure")
            unique = compute_workspace_cleanup_eligibility(
                fixture.worktree_b,
                workspace_path=fixture.worktree_b,
                package=result["review_package"]["package_id"],
            )
            self.assertIn(
                "workspace-has-commits-not-reachable-from-integration-oid", unique["reasons"]
            )
            self.assertTrue(unique["unique_commits"])

        with CollaborationGitFixture() as fixture:
            result, _closure = self._closed_package(fixture)
            info_exclude = Path(
                fixture.git(fixture.worktree_b, "rev-parse", "--git-path", "info/exclude").stdout.strip()
            )
            if not info_exclude.is_absolute():
                info_exclude = fixture.worktree_b / info_exclude
            info_exclude.parent.mkdir(parents=True, exist_ok=True)
            with info_exclude.open("a", encoding="utf-8") as stream:
                stream.write("ai-config.json\ncache.bin\n")
            (fixture.worktree_b / "ai-config.json").write_text("secret-boundary\n", encoding="utf-8")
            (fixture.worktree_b / "cache.bin").write_text("cache\n", encoding="utf-8")
            (fixture.worktree_b / "unknown.tmp").write_text("unknown\n", encoding="utf-8")
            files = compute_workspace_cleanup_eligibility(
                fixture.worktree_b,
                workspace_path=fixture.worktree_b,
                package=result["review_package"]["package_id"],
                ignored_allowlist=["*.bin", "ai-config.json"],
            )
            self.assertIn("unknown-untracked-paths-present", files["reasons"])
            self.assertIn("unknown-or-sensitive-ignored-paths-present", files["reasons"])
            self.assertIn("ai-config.json", files["unknown_ignored_paths"])
            self.assertIn("cache.bin", files["allowlisted_ignored_paths"])

    def test_cleanup_authorizations_are_independent_zero_delete_and_receipts_remain_private(self) -> None:
        with CollaborationGitFixture() as fixture:
            result, closure_result = self._closed_package(fixture)
            original_git = workspace_cleanup._git
            calls: list[tuple[str, ...]] = []

            def observed_git(repository: Path, *arguments: str, **kwargs: object):
                calls.append(tuple(arguments))
                return original_git(repository, *arguments, **kwargs)

            with mock.patch.object(workspace_cleanup, "_git", side_effect=observed_git), mock.patch.object(
                socket, "socket", side_effect=AssertionError("network socket opened")
            ), mock.patch.object(
                socket, "create_connection", side_effect=AssertionError("network connection opened")
            ):
                contract = compute_workspace_cleanup_eligibility(
                    fixture.worktree_b,
                    workspace_path=fixture.worktree_b,
                    package=result["review_package"]["package_id"],
                    authorized_actions=["remove-worktree"],
                )
            self.assertTrue(contract["eligible"], contract["reasons"])
            self.assertTrue(contract["actions"]["remove-worktree"]["authorized"])
            self.assertTrue(
                all(
                    not details["authorized"]
                    for action, details in contract["actions"].items()
                    if action != "remove-worktree"
                )
            )
            self.assertTrue(all(details["implies_actions"] == [] for details in contract["actions"].values()))
            self.assertTrue(all(not details["performed"] for details in contract["actions"].values()))
            forbidden = {
                ("worktree", "remove"),
                ("branch", "-d"),
                ("branch", "-D"),
                ("push", "--delete"),
            }
            self.assertFalse(any(any(pair == call[index : index + 2] for pair in forbidden for index in range(len(call) - 1)) for call in calls))
            authorization_id = contract["actions"]["remove-worktree"]["authorization_id"]
            receipt = record_cleanup_action_receipt(
                fixture.worktree_b,
                closure_id=closure_result["closure_record"]["closure_id"],
                action="remove-worktree",
                actor_id="local-owner",
                authorization_id=authorization_id,
                evidence_refs=["external:operator-confirmation"],
                occurred_at="2026-08-22T14:00:00Z",
            )
            receipt_path = Path(receipt["receipt_path"])
            common = Path(
                fixture.git(
                    fixture.worktree_b, "rev-parse", "--path-format=absolute", "--git-common-dir"
                ).stdout.strip()
            )
            receipt_path.resolve().relative_to(common.resolve())
            self.assertFalse(receipt["destructive_action_performed"])
            self.assertEqual(receipt["receipt"]["verification"], "caller-attested-external-action")

    def test_cli_json_and_exit_codes_are_stable_without_main_or_cleanup_mutation(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._commit_readme_candidate(fixture)
            self._prepare_session(fixture)
            environment = {
                **fixture.environment,
                "PYTHONPATH": os.pathsep.join(
                    (str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))
                ),
            }
            integrate = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "project_orrery_cli",
                    "integrate",
                    "--candidate",
                    str(fixture.worktree_b),
                    "--dry-run",
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(integrate.returncode, 0, integrate.stdout + integrate.stderr)
            payload = json.loads(integrate.stdout)
            self.assertEqual(payload["command"], "integrate-dry-run")
            self.assertEqual(payload["versions"]["core"], "0.1.11")
            self.assertEqual(payload["versions"]["cli"], "0.1.15")
            self.assertFalse(payload["data"]["integration_ref_updated"])
            package_id = payload["data"]["review_package"]["package_id"]
            eligibility = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "project_orrery_cli",
                    "review",
                    "eligibility",
                    "--target",
                    str(fixture.worktree_b),
                    "--package",
                    package_id,
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(eligibility.returncode, 5, eligibility.stdout + eligibility.stderr)
            eligibility_payload = json.loads(eligibility.stdout)
            self.assertEqual(eligibility_payload["command"], "review-integration-eligibility")
            self.assertFalse(eligibility_payload["data"]["eligible"])
            decision = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "project_orrery_cli",
                    "review",
                    "decide",
                    "--target",
                    str(fixture.worktree_b),
                    "--package",
                    package_id,
                    "--action",
                    "approve",
                    "--actor",
                    "author",
                    "--capability",
                    "reviewer",
                    "--reason",
                    "reviewed raw integration evidence",
                    "--evidence",
                    f"git:{payload['data']['review_package']['binding']['candidate_head']}",
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(decision.returncode, 0, decision.stdout + decision.stderr)
            decision_payload = json.loads(decision.stdout)
            self.assertEqual(decision_payload["command"], "review-decide")
            self.assertEqual(decision_payload["data"]["decision"]["action"], "approve")
            self.assertEqual(
                fixture.git(fixture.repository, "rev-parse", "main").stdout.strip(),
                payload["data"]["review_package"]["binding"]["target_oid"],
            )
            inventory = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "project_orrery_cli",
                    "review",
                    "inventory",
                    "--target",
                    str(fixture.worktree_b),
                    "--workspace-root",
                    str(fixture.root),
                    "--candidate-path",
                    str(fixture.clone),
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(inventory.returncode, 0, inventory.stdout + inventory.stderr)
            inventory_payload = json.loads(inventory.stdout)
            self.assertEqual(inventory_payload["command"], "review-workspace-inventory")
            self.assertFalse(
                inventory_payload["data"]["source_contract"]["recursive_disk_or_prefix_discovery"]
            )
            cleanup = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "project_orrery_cli",
                    "review",
                    "cleanup",
                    "--target",
                    str(fixture.worktree_b),
                    "--workspace",
                    str(fixture.clone),
                    "--workspace-root",
                    str(fixture.root),
                    "--classify",
                    f"{fixture.clone}=legacy-unmanaged",
                    "--authorize-action",
                    "remove-directory",
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(cleanup.returncode, 5, cleanup.stdout + cleanup.stderr)
            cleanup_payload = json.loads(cleanup.stdout)
            self.assertEqual(cleanup_payload["command"], "review-cleanup-eligibility")
            self.assertTrue(cleanup_payload["data"]["actions"]["remove-directory"]["authorized"])
            self.assertTrue(
                all(not item["performed"] for item in cleanup_payload["data"]["actions"].values())
            )


if __name__ == "__main__":
    unittest.main()
