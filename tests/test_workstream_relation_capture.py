from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
):
    sys.path.insert(0, str(source))

from project_orrery_core.collaboration import (  # noqa: E402
    _write_private_session,
    create_worktree,
    inspect_worktree_status,
    transition_workstream_session,
    write_workstream_session,
)
from project_orrery_core.workstream_relation_capture import (  # noqa: E402
    CAPTURE_MAX_FILE_BYTES,
    accept_proposal,
    auto_capture_derived_from,
    capture_storage_root,
    change_integrator_role,
    change_proposal_gate,
    defer_proposal,
    evidence_reference,
    inspect_integrator_roles,
    inspect_relation_capture,
    inspect_task_series,
    register_task_series,
    relation_gate_eligibility,
    reject_proposal,
    suggest_relation,
)
from project_orrery_core.workstream_relations import (  # noqa: E402
    append_relation_event,
    build_relation_record,
    default_relation_evidence,
    load_relation_history,
)
from project_orrery_core.schema import WORKSTREAM_RELATION_CAPTURE_SCHEMA  # noqa: E402
from project_orrery_core.team import _atomic_json, _coordinator_path, _read_json, enable_team  # noqa: E402
from project_orrery_cli import workstream_relations as relation_cli  # noqa: E402
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


STAMP = "2026-08-30T12:00:00Z"


class WorkstreamRelationCaptureTests(unittest.TestCase):
    def test_versioned_positive_and_negative_schema_fixtures(self) -> None:
        from jsonschema import Draft202012Validator

        fixture = json.loads((
            ROOT / "tests" / "fixtures" / "workstream-relation-capture" / "v2" / "contract-cases.json"
        ).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(WORKSTREAM_RELATION_CAPTURE_SCHEMA)
        validator = Draft202012Validator(WORKSTREAM_RELATION_CAPTURE_SCHEMA)
        for name, value in fixture["positive"].items():
            with self.subTest(positive=name):
                self.assertEqual(list(validator.iter_errors(value)), [])
        for item in fixture["negative"]:
            with self.subTest(negative=item["case"]):
                self.assertTrue(list(validator.iter_errors(item["value"])))

    def _sessions(self, fixture: CollaborationGitFixture) -> None:
        write_workstream_session(
            fixture.worktree_a, workstream_id="source-task",
            primary_subsystem_id="project-structure", evidence_freshness="current",
        )
        write_workstream_session(
            fixture.worktree_b, workstream_id="target-task",
            primary_subsystem_id="test-coverage", evidence_freshness="current",
        )

    def _suggest(self, fixture: CollaborationGitFixture, proposal_id: str = "proposal-validation", gate: str = "validation") -> dict:
        return suggest_relation(
            fixture.worktree_a,
            proposal_id=proposal_id,
            relation_type="depends_on",
            source_workstream_id="source-task",
            target_workstream_id="target-task",
            required_for=gate,
            rationale="target owns the required validation fixture",
            consequence="source cannot complete the named gate until target is complete",
            proposer_kind="agent",
            proposer_id="agent-observer",
            fact_scope="worktree",
            evidence=[evidence_reference(
                category="validation", reference="tests/fixture.json",
                fact_scope="candidate", digest="a" * 64,
            )],
            recorded_at=STAMP,
        )

    def test_schema_append_only_suggest_change_defer_reject_and_cas(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            suggested = self._suggest(fixture)
            self.assertFalse(suggested["authority_granted"])
            self.assertEqual(suggested["event"]["required_for"], "validation")
            changed = change_proposal_gate(
                fixture.worktree_a, "proposal-validation", expected_revision=1,
                required_for="implementation", actor_id="local-owner",
                reason="dependency is needed before implementation can finish", recorded_at="2026-08-30T12:01:00Z",
            )
            self.assertEqual(changed["event"]["revision"], 2)
            self.assertEqual(changed["event"]["required_for"], "implementation")
            with self.assertRaisesRegex(ValueError, "revision changed"):
                reject_proposal(
                    fixture.worktree_a, "proposal-validation", expected_revision=1,
                    actor_id="local-owner", reason="stale decision",
                )
            deferred = defer_proposal(
                fixture.worktree_a, "proposal-validation", expected_revision=2,
                actor_id="local-owner", reason="evidence is not conclusive",
                recorded_at="2026-08-30T12:02:00Z",
            )
            self.assertEqual(deferred["event"]["status"], "deferred-unknown")
            files = list((capture_storage_root(fixture.worktree_a) / "proposals" / "proposal-validation").glob("*.json"))
            self.assertEqual(len(files), 3)

    def test_agent_harness_remote_and_session_spoof_cannot_decide(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            self._suggest(fixture)
            with self.assertRaisesRegex(PermissionError, "Agent/session/remote"):
                accept_proposal(
                    fixture.worktree_a, "proposal-validation", expected_revision=1,
                    confirmer_id="local-owner", confirmer_role="task-owner",
                    caller_kind="agent", caller_context="local", local_confirmation=True,
                )
            with self.assertRaisesRegex(PermissionError, "local human"):
                reject_proposal(
                    fixture.worktree_a, "proposal-validation", expected_revision=1,
                    actor_id="agent-session", reason="spoof", caller_kind="session",
                    caller_context="central-request", local_confirmation=False,
                )
            self.assertEqual(inspect_relation_capture(fixture.worktree_a)["counts"]["pending"], 1)

    def test_cli_json_suggest_inspect_and_remote_accept_receipts_are_bounded(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = relation_cli.main([
                    "suggest", "--target", str(fixture.worktree_a), "--json",
                    "--proposal-id", "cli-validation", "--type", "depends_on",
                    "--source", "source-task", "--target-workstream", "target-task",
                    "--required-for", "validation", "--rationale", "explicit validation evidence",
                    "--consequence", "validation cannot close until the target completes",
                    "--proposer-kind", "agent", "--proposer-id", "cli-agent",
                ])
            receipt = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["data"]["event"]["required_for"], "validation")
            self.assertFalse(receipt["data"]["authority_granted"])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = relation_cli.main([
                    "inspect", "--target", str(fixture.worktree_a), "--json",
                ])
            inspection = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(inspection["data"]["capture"]["counts"]["pending"], 1)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = relation_cli.main([
                    "accept", "--target", str(fixture.worktree_a), "--json",
                    "--proposal-id", "cli-validation", "--expected-revision", "1",
                    "--confirmer-id", "local-owner", "--confirmer-role", "task-owner",
                    "--caller-context", "remote", "--confirm-local",
                ])
            denied = json.loads(output.getvalue())
            self.assertEqual(exit_code, 3)
            self.assertEqual(denied["status"], "error")
            self.assertEqual(inspect_relation_capture(fixture.worktree_a)["counts"]["effective"], 0)

    def test_task_owner_accepts_local_gate_and_current_effective_relation_blocks(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            self._suggest(fixture)
            accepted = accept_proposal(
                fixture.worktree_a, "proposal-validation", expected_revision=1,
                confirmer_id="local-owner", confirmer_role="task-owner",
                local_confirmation=True, recorded_at="2026-08-30T12:03:00Z",
            )
            self.assertEqual(accepted["confirmation"]["confirmer"]["role"], "task-owner")
            inspection = inspect_relation_capture(fixture.worktree_a)
            self.assertEqual(inspection["counts"]["effective"], 1)
            gate = relation_gate_eligibility(
                fixture.worktree_a, source_workstream_id="source-task", required_for="validation",
            )
            self.assertFalse(gate["eligible"])
            target_session = dict(inspect_worktree_status(fixture.worktree_b)["session"]["record"])
            target_session.update({
                "lifecycle_phase": "closed", "runtime_condition": "paused",
                "closure_reason": "abandoned", "lifecycle_revision": 2,
            })
            _write_private_session(fixture.worktree_b, target_session)
            self.assertTrue(relation_gate_eligibility(
                fixture.worktree_a, source_workstream_id="source-task", required_for="validation",
            )["eligible"])

    def test_integrator_required_for_project_gate_and_personal_owner_is_sole_default(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            self._suggest(fixture, proposal_id="proposal-integration", gate="integration")
            roles = inspect_integrator_roles(fixture.worktree_a)
            self.assertEqual(roles["integrator_member_ids"], ["local-owner"])
            self.assertTrue(roles["sole_integrator"])
            with self.assertRaisesRegex(PermissionError, "integrator"):
                accept_proposal(
                    fixture.worktree_a, "proposal-integration", expected_revision=1,
                    confirmer_id="local-owner", confirmer_role="task-owner",
                    local_confirmation=True,
                )
            accepted = accept_proposal(
                fixture.worktree_a, "proposal-integration", expected_revision=1,
                confirmer_id="local-owner", confirmer_role="integrator",
                local_confirmation=True, recorded_at="2026-08-30T12:05:00Z",
            )
            self.assertEqual(accepted["confirmation"]["confirmer"]["authority_revision"], 0)

    def test_team_integrator_grant_revoke_cas_spoof_and_empty_registry_fail_closed(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            enable_team(
                fixture.worktree_a, member_id="local-owner", device_id="device-a", host_id="host-a",
                occurred_at=STAMP,
            )
            coordinator_path = _coordinator_path(fixture.worktree_a)
            coordinator = _read_json(coordinator_path)
            coordinator["members"]["reviewer"] = {
                "member_kind": "human", "status": "active", "credential_state": "active",
            }
            _atomic_json(coordinator_path, coordinator)
            granted = change_integrator_role(
                fixture.worktree_a, member_id="reviewer", action="grant",
                actor_id="local-owner", expected_revision=0, recorded_at="2026-08-30T12:04:00Z",
            )
            self.assertIn("reviewer", granted["roles"]["integrator_member_ids"])
            with self.assertRaisesRegex(ValueError, "revision changed"):
                change_integrator_role(
                    fixture.worktree_a, member_id="reviewer", action="revoke",
                    actor_id="local-owner", expected_revision=0,
                )
            with self.assertRaisesRegex(PermissionError, "local human project owner"):
                change_integrator_role(
                    fixture.worktree_a, member_id="reviewer", action="revoke",
                    actor_id="agent-session", expected_revision=1, caller_kind="agent",
                    caller_context="central-request",
                )
            revoked = change_integrator_role(
                fixture.worktree_a, member_id="reviewer", action="revoke",
                actor_id="local-owner", expected_revision=1, recorded_at="2026-08-30T12:05:00Z",
            )
            self.assertEqual(revoked["roles"]["integrator_member_ids"], ["local-owner"])
            self._suggest(fixture, proposal_id="team-integration", gate="integration")
            empty_roles = dict(revoked["roles"], integrator_member_ids=[])
            with mock.patch(
                "project_orrery_core.workstream_relation_capture.inspect_integrator_roles",
                return_value=empty_roles,
            ):
                with self.assertRaisesRegex(PermissionError, "no current human integrator"):
                    accept_proposal(
                        fixture.worktree_a, "team-integration", expected_revision=1,
                        confirmer_id="local-owner", confirmer_role="integrator", local_confirmation=True,
                    )

    def test_stale_confirmation_stops_blocking_and_old_revision_conflicts_are_rejected(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            self._suggest(fixture)
            accept_proposal(
                fixture.worktree_a, "proposal-validation", expected_revision=1,
                confirmer_id="local-owner", confirmer_role="task-owner", local_confirmation=True,
                recorded_at="2026-08-30T12:06:00Z",
            )
            changed = fixture.worktree_a / "after-confirmation.txt"
            changed.write_text("drift\n", encoding="utf-8")
            fixture.git(fixture.worktree_a, "add", "after-confirmation.txt")
            fixture.git(fixture.worktree_a, "commit", "-m", "drift after relation confirmation")
            inspection = inspect_relation_capture(fixture.worktree_a)
            self.assertEqual(inspection["proposals"][0]["display_status"], "stale")
            self.assertEqual(inspection["counts"]["effective"], 0)
            self.assertTrue(relation_gate_eligibility(
                fixture.worktree_a, source_workstream_id="source-task", required_for="validation",
            )["eligible"])
            with self.assertRaisesRegex(ValueError, "only a current proposed"):
                accept_proposal(
                    fixture.worktree_a, "proposal-validation", expected_revision=2,
                    confirmer_id="local-owner", confirmer_role="task-owner", local_confirmation=True,
                )

    def test_cycle_duplicate_and_self_edges_fail_closed(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            self._suggest(fixture, proposal_id="source-needs-target", gate="integration")
            accept_proposal(
                fixture.worktree_a, "source-needs-target", expected_revision=1,
                confirmer_id="local-owner", confirmer_role="integrator", local_confirmation=True,
            )
            suggest_relation(
                fixture.worktree_a, proposal_id="target-needs-source", relation_type="depends_on",
                source_workstream_id="target-task", target_workstream_id="source-task",
                required_for="integration", rationale="reverse dependency",
                consequence="would create a cycle", proposer_kind="agent", proposer_id="agent-observer",
            )
            with self.assertRaisesRegex(ValueError, "Core DAG"):
                accept_proposal(
                    fixture.worktree_a, "target-needs-source", expected_revision=1,
                    confirmer_id="local-owner", confirmer_role="integrator", local_confirmation=True,
                )
            with self.assertRaisesRegex(ValueError, "cannot reference itself"):
                suggest_relation(
                    fixture.worktree_a, proposal_id="self-edge", relation_type="depends_on",
                    source_workstream_id="source-task", target_workstream_id="source-task",
                    required_for="validation", rationale="bad self edge", consequence="invalid",
                    proposer_kind="agent", proposer_id="agent-observer",
                )

    def test_legacy_dependency_without_gate_remains_unknown_and_non_blocking(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            head = fixture.git(fixture.worktree_a, "rev-parse", "HEAD").stdout.strip()
            record = build_relation_record(
                relation_id="legacy-dependency", event_id="legacy-event", revision=1,
                relation_type="depends_on", source_workstream_id="source-task",
                target_workstream_id="target-task", lifecycle="active", recorded_at=STAMP,
                actor_kind="import", actor_id="legacy-v1", origin="native",
                reason="historical relation without required_for",
                evidence=default_relation_evidence(
                    status="confirmed", source_head_oid=head, target_head_oid=head,
                    source_head_status="current", target_head_status="current", scope_status="current",
                    ancestry_status="not-applicable", dependency_status="confirmed",
                    ownership_transfer_status="not-applicable",
                ),
                writes_performed=True,
            )
            append_relation_event(fixture.worktree_a, record)
            inspection = inspect_relation_capture(fixture.worktree_a)
            self.assertEqual(inspection["legacy_unknown_dependencies"][0]["required_for"], "unknown/unspecified")
            self.assertTrue(relation_gate_eligibility(
                fixture.worktree_a, source_workstream_id="source-task", required_for="validation",
            )["eligible"])

    def test_registration_auto_derived_from_is_exact_and_idempotent(self) -> None:
        with CollaborationGitFixture() as fixture:
            parent = fixture.worktree_a
            parent_head = fixture.git(parent, "rev-parse", "HEAD").stdout.strip()
            write_workstream_session(
                parent, workstream_id="parent-task", primary_subsystem_id="project-structure",
                evidence_freshness="current",
            )
            created = create_worktree(
                parent, workstream_id="child-task", branch="codex/capture-child",
                path=fixture.root / "capture-child", primary_subsystem_id="project-structure",
                base_workstream_id="parent-task", task_base_oid=parent_head,
            )
            child = Path(created["worktree_path"])
            self.assertEqual(created["status"]["session"]["record"]["lineage"]["status"], "current")
            records = load_relation_history(child)["current_records"]
            derived = [item for item in records if item["source_workstream_id"] == "child-task"]
            self.assertEqual(len(derived), 1)
            refreshed = write_workstream_session(
                child, workstream_id="child-task", primary_subsystem_id="project-structure",
                base_workstream_id="parent-task", task_base_oid=parent_head,
                evidence_freshness="current",
            )
            self.assertFalse(refreshed["relation_capture"]["writes_performed"])
            self.assertEqual(len(load_relation_history(child)["current_records"]), len(records))

    def test_unknown_lineage_supersedes_only_obsolete_automatic_proposals(self) -> None:
        with CollaborationGitFixture() as fixture:
            def unknown_session(task_base: str, scope_revision: int) -> dict:
                return {
                    "workstream_id": "child-task",
                    "head": "a" * 40,
                    "scope_revision": scope_revision,
                    "lineage": {
                        "base_workstream_id": "missing-parent",
                        "task_base_oid": task_base,
                        "status": "parent-unverified-unknown",
                    },
                }

            first = auto_capture_derived_from(
                fixture.worktree_a, unknown_session("b" * 40, 1), recorded_at="2026-08-31T00:00:00Z",
            )
            first_id = first["proposal"]["event"]["proposal_id"]
            self.assertTrue(first["writes_performed"])
            with self.assertRaisesRegex(PermissionError, "Core-verified mechanical ancestry"):
                accept_proposal(
                    fixture.worktree_a, first_id, expected_revision=1,
                    confirmer_id="local-owner", confirmer_role="task-owner",
                    local_confirmation=True,
                )

            manual = suggest_relation(
                fixture.worktree_a, proposal_id="human-lineage-observation",
                relation_type="derived_from", source_workstream_id="child-task",
                target_workstream_id="missing-parent", required_for=None,
                rationale="human wants to preserve a separate observation",
                consequence="this observation remains pending until a human decides it",
                proposer_kind="human", proposer_id="local-owner",
                recorded_at="2026-08-31T00:00:01Z",
            )
            self.assertTrue(manual["writes_performed"])

            second = auto_capture_derived_from(
                fixture.worktree_a, unknown_session("c" * 40, 2), recorded_at="2026-08-31T00:00:02Z",
            )
            second_id = second["proposal"]["event"]["proposal_id"]
            self.assertNotEqual(first_id, second_id)
            self.assertEqual(second["superseded_proposal_ids"], [first_id])

            inspection = inspect_relation_capture(fixture.worktree_a)
            by_id = {item["proposal_id"]: item for item in inspection["proposals"]}
            self.assertEqual(by_id[first_id]["display_status"], "superseded")
            self.assertEqual(by_id[first_id]["history_count"], 2)
            self.assertEqual(by_id[second_id]["display_status"], "proposed")
            self.assertEqual(by_id["human-lineage-observation"]["display_status"], "proposed")
            self.assertEqual(inspection["counts"]["pending"], 2)

            repeated = auto_capture_derived_from(
                fixture.worktree_a, unknown_session("c" * 40, 2), recorded_at="2026-08-31T00:00:03Z",
            )
            self.assertFalse(repeated["writes_performed"])
            self.assertEqual(repeated["superseded_proposal_ids"], [])
            self.assertEqual(inspect_relation_capture(fixture.worktree_a)["counts"]["pending"], 2)

            returned = auto_capture_derived_from(
                fixture.worktree_a, unknown_session("b" * 40, 3), recorded_at="2026-08-31T00:00:04Z",
            )
            returned_id = returned["proposal"]["event"]["proposal_id"]
            self.assertNotEqual(returned_id, first_id)
            self.assertEqual(returned["superseded_proposal_ids"], [second_id])
            final = inspect_relation_capture(fixture.worktree_a)
            self.assertEqual(final["counts"]["pending"], 2)
            self.assertEqual(
                {item["proposal_id"] for item in final["pending_proposals"]},
                {"human-lineage-observation", returned_id},
            )

    def test_explicit_series_is_display_metadata_and_predecessor_stays_proposed(self) -> None:
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b, workstream_id="authority-a3",
                primary_subsystem_id="project-structure", evidence_freshness="current",
                series_id="authority", task_code="A3", series_order=3,
            )
            first = write_workstream_session(
                fixture.worktree_a, workstream_id="authority-a4",
                primary_subsystem_id="project-structure", evidence_freshness="current",
                series_id="authority", task_code="A4", series_order=4,
                series_predecessor_workstream_id="authority-a3",
                series_predecessor_required_for="integration",
            )
            self.assertFalse(first["task_series"]["effective_relation_created"])
            capture = inspect_relation_capture(fixture.worktree_a)
            self.assertEqual(capture["counts"]["pending"], 1)
            self.assertEqual(capture["counts"]["effective"], 0)
            self.assertEqual(inspect_task_series(fixture.worktree_a)["items"][0]["series_id"], "authority")
            refreshed = write_workstream_session(
                fixture.worktree_a, workstream_id="authority-a4",
                primary_subsystem_id="project-structure", evidence_freshness="current",
                series_id="authority", task_code="A4", series_order=4,
                series_predecessor_workstream_id="authority-a3",
                series_predecessor_required_for="integration",
            )
            self.assertFalse(refreshed["task_series"]["writes_performed"])
            self.assertEqual(inspect_relation_capture(fixture.worktree_a)["counts"]["pending"], 1)

    def test_private_observed_heads_can_seed_repair_proposal_but_never_make_it_effective(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            source_head = fixture.git(fixture.worktree_a, "rev-parse", "HEAD").stdout.strip()
            target_head = fixture.git(fixture.worktree_b, "rev-parse", "HEAD").stdout.strip()
            result = register_task_series(
                fixture.worktree_a, workstream_id="source-task", series_id="CI", task_code="CI7",
                series_order=7, series_predecessor_workstream_id="target-task",
                suggested_required_for="integration", actor="self-host-repair",
                proposal_observed_head_oids=(source_head, target_head),
            )
            self.assertEqual(result["proposal"]["event"]["source_head_oid"], source_head)
            self.assertEqual(result["proposal"]["event"]["target_head_oid"], target_head)
            self.assertFalse(result["effective_relation_created"])
            self.assertEqual(inspect_relation_capture(fixture.worktree_a)["counts"]["effective"], 0)

    def test_absorbs_requires_context_and_human_integrator(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            with self.assertRaisesRegex(ValueError, "requires closure"):
                suggest_relation(
                    fixture.worktree_a, proposal_id="bad-absorbs", relation_type="absorbs",
                    source_workstream_id="source-task", target_workstream_id="target-task",
                    required_for=None, rationale="take over", consequence="ownership moves",
                    proposer_kind="agent", proposer_id="agent-observer",
                )
            transition_workstream_session(
                fixture.worktree_b, runtime_condition="paused", reason="prepare explicit takeover",
                occurred_at="2026-08-30T12:07:00Z",
            )
            suggested = suggest_relation(
                fixture.worktree_a, proposal_id="absorbs-target", relation_type="absorbs",
                source_workstream_id="source-task", target_workstream_id="target-task",
                required_for=None, rationale="source assumes remaining ownership",
                consequence="target responsibilities transfer to source",
                proposer_kind="agent", proposer_id="agent-observer",
                absorbs_context={
                    "target_closure": "open",
                    "validation_refs": ["docs/validation/fixture.md"],
                    "scope_refs": ["git-private:target-task"],
                    "unfinished_responsibilities": ["finish release evidence"],
                },
            )
            self.assertEqual(suggested["event"]["absorbs_context"]["target_closure"], "open")
            with self.assertRaisesRegex(PermissionError, "integrator"):
                accept_proposal(
                    fixture.worktree_a, "absorbs-target", expected_revision=1,
                    confirmer_id="local-owner", confirmer_role="task-owner", local_confirmation=True,
                )
            accepted = accept_proposal(
                fixture.worktree_a, "absorbs-target", expected_revision=1,
                confirmer_id="local-owner", confirmer_role="integrator", local_confirmation=True,
            )
            self.assertEqual(accepted["effective_relation"]["relation_type"], "absorbs")

    def test_privacy_path_size_count_and_symlink_style_boundaries_fail_closed(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._sessions(fixture)
            with self.assertRaisesRegex(ValueError, "absolute path or URL"):
                evidence_reference(
                    category="harness", reference="https://example.invalid/raw",
                    fact_scope="unknown", digest="b" * 64,
                )
            root = capture_storage_root(fixture.worktree_a)
            bad = root / "proposals" / "oversized"
            bad.mkdir(parents=True)
            (bad / "1-event.json").write_bytes(b"{" + b"x" * CAPTURE_MAX_FILE_BYTES)
            with self.assertRaisesRegex(ValueError, "size limit"):
                inspect_relation_capture(fixture.worktree_a)
            self.assertEqual(fixture.git(fixture.worktree_a, "status", "--porcelain").stdout.count("\n"), 1)


if __name__ == "__main__":
    unittest.main()
