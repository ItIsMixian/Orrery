from __future__ import annotations

import contextlib
import copy
import io
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from project_orrery_core.collaboration import create_worktree, inspect_worktree_status, write_workstream_session
from project_orrery_core.workstream_relation_execution import (
    RecoveryRequiredError,
    build_execution_plan,
    build_execution_undo_plan,
    discover_execution_candidates,
    execute_apply_plan,
    execute_undo_plan,
    inspect_execution_state,
    issue_local_confirmation,
    issue_local_undo_confirmation,
    load_execution_receipt,
    recover_transaction,
)
from project_orrery_core.workstream_relations import load_relation_graph, load_relation_history
from project_orrery_core.schema import WORKSTREAM_RELATION_EXECUTION_SCHEMA
from project_orrery_cli import workstream_relations as relations_cli
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture


DISCOVERY_AT = "2026-08-28T12:00:00Z"
PLAN_AT = "2026-08-28T12:01:00Z"
EXPIRES_AT = "2030-08-28T12:01:00Z"
APPLY_AT = "2026-08-28T12:02:00Z"
UNDO_AT = "2026-08-28T12:03:00Z"


class SanitizedSuccessionFixture:
    """Isolated W5C -> W6 -> W5D -> {CI1,W5E} topology."""

    def __init__(self) -> None:
        self.git_fixture = CollaborationGitFixture()
        self.root = self.git_fixture.repository
        self.worktrees: dict[str, Path] = {"W5C": self.root}
        self.parents: dict[str, str | None] = {"W5C": None}
        self.task_bases: dict[str, str | None] = {"W5C": None}
        self._write("W5C")
        self._child("W5C", "W6")
        self._child("W6", "W5D")
        self._child("W5D", "CI1")
        self._child("W5D", "W5E")

    def __enter__(self) -> "SanitizedSuccessionFixture":
        return self

    def __exit__(self, *_args: object) -> None:
        self.git_fixture.close()

    def _child(self, parent_id: str, child_id: str) -> None:
        parent = self.worktrees[parent_id]
        task_base = self.git_fixture.git(parent, "rev-parse", "HEAD").stdout.strip()
        path = self.git_fixture.root / child_id.lower()
        create_worktree(
            parent,
            workstream_id=child_id,
            branch=f"codex/{child_id.lower()}",
            path=path,
            primary_subsystem_id="project-structure",
            affected_subsystem_ids=("documentation-system", "release-and-toolchain", "test-coverage"),
            base_workstream_id=parent_id,
            task_base_oid=task_base,
        )
        self.worktrees[child_id] = path
        self.parents[child_id] = parent_id
        self.task_bases[child_id] = task_base
        self._write(child_id)

    def _write(
        self,
        workstream_id: str,
        *,
        runtime_condition: str = "active",
        lifecycle_phase: str = "implementing",
        evidence_freshness: str = "current",
        closure_reason: str | None = None,
    ) -> None:
        write_workstream_session(
            self.worktrees[workstream_id],
            workstream_id=workstream_id,
            primary_subsystem_id="project-structure",
            affected_subsystem_ids=("documentation-system", "release-and-toolchain", "test-coverage"),
            expected_writes=(f"fixture/{workstream_id}.txt",),
            validation_surfaces=(f"fixture:{workstream_id}",),
            runtime_condition=runtime_condition,
            lifecycle_phase=lifecycle_phase,
            evidence_freshness=evidence_freshness,
            closure_reason=closure_reason,
            base_workstream_id=self.parents[workstream_id],
            task_base_oid=self.task_bases[workstream_id],
            captured_at=DISCOVERY_AT,
        )

    def discovery(self, *, include_dependency: bool = True, include_similarity: bool = False) -> dict:
        explicit = []
        if include_dependency:
            explicit.append({
                "relation_id": "rel-w5e-depends-ci1",
                "relation_type": "depends_on",
                "source_workstream_id": "W5E",
                "target_workstream_id": "CI1",
                "reason": "late CI inventory/shards must finish before W5E closeout",
                "source_links": [{"kind": "validation", "ref": "fixture:ci1-inventory-shards"}],
            })
        hints = (
            [{"source_workstream_id": "codex/ui-new", "target_workstream_id": "codex/ui-old"}]
            if include_similarity else []
        )
        return discover_execution_candidates(
            self.root,
            explicit_relations=explicit,
            similarity_hints=hints,
            recorded_at=DISCOVERY_AT,
        )

    def plan(self, *, completed: bool = False, include_dependency: bool = True) -> tuple[dict, str]:
        discovery = self.discovery(include_dependency=include_dependency)
        lifecycles = {item["record"]["relation_id"]: "proposed" for item in discovery["candidates"]}
        successor = next(
            item["record"]["relation_id"]
            for item in discovery["candidates"]
            if item["record"]["source_workstream_id"] == "W5E"
            and item["record"]["target_workstream_id"] == "W5D"
            and item["record"]["relation_type"] == "derived_from"
        )
        lifecycles[successor] = "completed" if completed else "active"
        if include_dependency:
            lifecycles["rel-w5e-depends-ci1"] = "active"
        plan = build_execution_plan(
            self.root,
            discovery,
            target_lifecycles=lifecycles,
            actor_id="maintainer",
            issued_at=PLAN_AT,
            expires_at=EXPIRES_AT,
        )
        return plan, successor

    def statuses(self) -> dict[str, str]:
        return {
            name: self.git_fixture.git(path, "status", "--short").stdout
            for name, path in self.worktrees.items()
        }


def confirm_and_apply(fixture: SanitizedSuccessionFixture, plan: dict, *, occurred_at: str = APPLY_AT) -> dict:
    confirmation = issue_local_confirmation(fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT)
    return execute_apply_plan(
        fixture.root,
        plan,
        plan_id=plan["plan_id"],
        plan_hash=plan["plan_hash"],
        confirmation_id=confirmation["confirmation_id"],
        confirmation_token=confirmation["confirmation_token"],
        actor_id="maintainer",
        occurred_at=occurred_at,
    )


class WorkstreamRelationExecutionTests(unittest.TestCase):
    def test_execution_schema_cli_surface_and_no_delete_contract_are_dependency_light(self) -> None:
        refs = {item["$ref"] for item in WORKSTREAM_RELATION_EXECUTION_SCHEMA["oneOf"]}
        self.assertIn("#/$defs/execution_plan", refs)
        self.assertIn("#/$defs/confirmation", refs)
        self.assertIn("#/$defs/receipt", refs)
        parser = relations_cli.build_parser()
        for command in ("discover", "plan", "apply", "inspect", "undo", "receipt"):
            with self.subTest(command=command):
                self.assertIn(command, parser._subparsers._group_actions[0].choices)
        source = (
            Path(__file__).parents[1]
            / "packages" / "project-orrery-core" / "src" / "project_orrery_core"
            / "workstream_relation_execution.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("delete-worktree", source)
        self.assertNotIn("delete-branch", source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)

    def test_discovery_uses_exact_lineage_and_reports_late_ci_legacy_unknown_and_similarity(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            fixture._write("W5C")
            write_workstream_session(
                fixture.git_fixture.worktree_a,
                workstream_id="legacy-no-lineage",
                primary_subsystem_id="project-structure",
                evidence_freshness="current",
                captured_at=DISCOVERY_AT,
            )
            discovery = fixture.discovery(include_similarity=True)
            triples = {
                (
                    item["record"]["relation_type"],
                    item["record"]["source_workstream_id"],
                    item["record"]["target_workstream_id"],
                )
                for item in discovery["candidates"]
            }
            self.assertIn(("derived_from", "W5E", "W5D"), triples)
            self.assertIn(("derived_from", "CI1", "W5D"), triples)
            self.assertIn(("depends_on", "W5E", "CI1"), triples)
            self.assertIn(
                "legacy-no-lineage-evidence",
                next(item for item in discovery["unknown_candidates"] if item["source_workstream_id"] == "legacy-no-lineage")["reason_codes"],
            )
            self.assertEqual(discovery["rejected_hints"][0]["reason_code"], "branch-or-path-similarity-insufficient-evidence")
            self.assertFalse(discovery["similarity_inference_permitted"])
            self.assertFalse(discovery["writes_performed"])
            self.assertEqual(fixture.git_fixture.git(fixture.root, "status", "--short").stdout, "")

    def test_parent_post_fork_sibling_nonancestor_and_unknown_remain_proposed(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            parent = fixture.worktrees["W5D"]
            (parent / "post-fork.txt").write_text("parent advanced\n", encoding="utf-8")
            fixture.git_fixture.git(parent, "add", "post-fork.txt")
            fixture.git_fixture.git(parent, "commit", "-m", "parent post fork")
            fixture._write("W5D")
            discovery = fixture.discovery(include_dependency=False)
            w5e = next(
                item for item in discovery["candidates"]
                if item["record"]["source_workstream_id"] == "W5E"
                and item["record"]["target_workstream_id"] == "W5D"
            )
            self.assertEqual(w5e["status"], "proposed")
            self.assertNotEqual(w5e["record"]["evidence"]["target_unique_commits_after_base"], 0)
            sibling_sources = {
                item["record"]["source_workstream_id"]
                for item in discovery["candidates"]
                if item["record"]["target_workstream_id"] == "W5D"
            }
            self.assertEqual(sibling_sources, {"CI1", "W5E"})
            bad = fixture.discovery(include_dependency=False)
            self.assertTrue(all(item["status"] == "proposed" for item in bad["candidates"]))

    def test_plan_binds_graph_session_head_scope_and_excludes_nonactive_predecessor_states(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            for runtime in ("waiting-for-user", "paused", "blocked-by-conflict", "failed"):
                fixture._write("W5D", runtime_condition=runtime)
                with self.assertRaisesRegex(ValueError, "predecessor must be runtime active"):
                    fixture.plan()
            fixture._write("W5D", runtime_condition="active")
            plan, successor = fixture.plan()
            binding = next(item for item in plan["candidate_bindings"] if item["relation_id"] == successor)
            self.assertEqual(len(binding["target"]["session_hash"]), 64)
            self.assertEqual(len(binding["target"]["scope_hash"]), 64)
            self.assertEqual(len(binding["target"]["head_oid"]), 40)
            self.assertEqual(plan["graph_hash"], plan["apply_plan"]["graph_hash"])
            self.assertEqual(plan["actor"], {"kind": "human-local", "actor_id": "maintainer"})
            self.assertTrue(plan["execution_supported"])
            self.assertEqual(plan["destructive_actions"], [])

    def test_confirmation_forgery_expiry_cross_project_and_drift_fail_before_product_writes(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            plan, _ = fixture.plan()
            confirmation = issue_local_confirmation(fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT)
            with self.assertRaisesRegex(ValueError, "forged, replayed, cross-project, or not exact"):
                execute_apply_plan(
                    fixture.root, plan, plan_id=plan["plan_id"], plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"], confirmation_token="forged",
                    actor_id="maintainer", occurred_at=APPLY_AT,
                )
            self.assertEqual(inspect_execution_state(fixture.root)["journal_statuses"], [])
            fixture._write("W5D", runtime_condition="waiting-for-user")
            with self.assertRaisesRegex(ValueError, "graph drifted|Session/HEAD/Scope drifted"):
                execute_apply_plan(
                    fixture.root, plan, plan_id=plan["plan_id"], plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"],
                    confirmation_token=confirmation["confirmation_token"], actor_id="maintainer",
                    occurred_at=APPLY_AT,
                )
            self.assertEqual(inspect_execution_state(fixture.root)["journal_statuses"], [])
            expired = build_execution_plan(
                fixture.root, fixture.discovery(),
                target_lifecycles={item["record"]["relation_id"]: "proposed" for item in fixture.discovery()["candidates"]},
                actor_id="maintainer", issued_at="2020-01-01T00:00:00Z", expires_at="2020-01-01T00:01:00Z",
            )
            with self.assertRaisesRegex(ValueError, "expired"):
                issue_local_confirmation(fixture.root, expired, actor_id="maintainer")
        with SanitizedSuccessionFixture() as first, SanitizedSuccessionFixture() as second:
            plan, _ = first.plan()
            with self.assertRaisesRegex(ValueError, "another local project"):
                issue_local_confirmation(second.root, plan, actor_id="maintainer")

    def test_atomic_failure_blocks_graph_then_recovery_restores_sessions_and_retains_history(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            before_status = fixture.statuses()
            before_hash = inspect_worktree_status(fixture.worktrees["W5D"])["session"]["record"]
            plan, _ = fixture.plan()
            confirmation = issue_local_confirmation(fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT)
            with self.assertRaises(RecoveryRequiredError):
                execute_apply_plan(
                    fixture.root, plan, plan_id=plan["plan_id"], plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"], confirmation_token=confirmation["confirmation_token"],
                    actor_id="maintainer", occurred_at=APPLY_AT, failure_injection="after-event-write:2",
                )
            inspection = inspect_execution_state(fixture.root)
            self.assertEqual(inspection["graph_status"], "blocked")
            transaction_id = inspection["pending_recovery_transaction_ids"][0]
            with self.assertRaises(RecoveryRequiredError):
                load_relation_graph(fixture.root)
            recovered = recover_transaction(fixture.root, transaction_id, actor_id="maintainer", occurred_at=UNDO_AT)
            self.assertEqual(recovered["status"], "rolled-back")
            self.assertFalse(recovered["history_deleted"])
            self.assertEqual(inspect_execution_state(fixture.root)["graph_status"], "current")
            self.assertEqual(inspect_worktree_status(fixture.worktrees["W5D"])["session"]["record"], before_hash)
            self.assertTrue(load_relation_history(fixture.root)["histories"])
            self.assertTrue(all(item["lifecycle"] in {"cancelled", "stale"} for item in load_relation_history(fixture.root)["current_records"]))
            self.assertEqual(fixture.statuses(), before_status)

    def test_batch_apply_completed_invariant_replay_receipt_and_author_tree_clean(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            before_status = fixture.statuses()
            plan, successor = fixture.plan(completed=True)
            with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
                receipt = confirm_and_apply(fixture, plan)
            predecessor = inspect_worktree_status(fixture.worktrees["W5D"])["session"]["record"]
            self.assertEqual((predecessor["lifecycle_phase"], predecessor["runtime_condition"], predecessor["closure_reason"]), ("closed", "paused", "superseded"))
            graph = load_relation_graph(fixture.root)
            self.assertTrue(graph["validation"]["valid"])
            self.assertEqual(load_execution_receipt(fixture.root, receipt["receipt_id"]), receipt)
            self.assertTrue(all(len(item["event_hash"]) == 64 for item in receipt["relation_event_records"]))
            with self.assertRaisesRegex(ValueError, "graph drifted|replay"):
                execute_apply_plan(
                    fixture.root, plan, plan_id=plan["plan_id"], plan_hash=plan["plan_hash"],
                    confirmation_id=receipt["confirmation_id"], confirmation_token="replayed",
                    actor_id="maintainer", occurred_at=APPLY_AT,
                )
            self.assertIn(successor, {item["relation_id"] for item in receipt["relation_event_records"]})
            self.assertEqual(fixture.statuses(), before_status)
            self.assertEqual(receipt["destructive_actions"], [])

    def test_undo_success_restores_exact_session_and_appends_history_while_drift_refuses(self) -> None:
        with SanitizedSuccessionFixture() as fixture:
            original_path = Path(inspect_worktree_status(fixture.worktrees["W5D"])["session"]["path"])
            original_bytes = original_path.read_bytes()
            plan, _ = fixture.plan()
            receipt = confirm_and_apply(fixture, plan)
            undo_plan = build_execution_undo_plan(
                fixture.root, receipt, actor_id="maintainer", issued_at=PLAN_AT, expires_at=EXPIRES_AT,
            )
            confirmation = issue_local_undo_confirmation(fixture.root, undo_plan, actor_id="maintainer", issued_at=PLAN_AT)
            undo_receipt = execute_undo_plan(
                fixture.root, undo_plan, plan_id=undo_plan["plan_id"], plan_hash=undo_plan["plan_hash"],
                confirmation_id=confirmation["confirmation_id"], confirmation_token=confirmation["confirmation_token"],
                actor_id="maintainer", occurred_at=UNDO_AT,
            )
            self.assertEqual(original_path.read_bytes(), original_bytes)
            self.assertFalse(undo_receipt["history_deleted"])
            self.assertTrue(undo_receipt["appended_compensating_event_ids"])
            self.assertTrue(all(len(item["events"]) >= 2 for item in load_relation_history(fixture.root)["histories"]))
            self.assertTrue(all(item["lifecycle"] in {"cancelled", "stale"} for item in load_relation_history(fixture.root)["current_records"]))
        with SanitizedSuccessionFixture() as fixture:
            plan, _ = fixture.plan()
            receipt = confirm_and_apply(fixture, plan)
            fixture._write("W5D", runtime_condition="waiting-for-user")
            with self.assertRaisesRegex(ValueError, "drift"):
                build_execution_undo_plan(fixture.root, receipt, actor_id="maintainer")

    def test_cli_discover_plan_apply_receipt_undo_and_inspect_json(self) -> None:
        with SanitizedSuccessionFixture() as fixture, tempfile.TemporaryDirectory(prefix="orrery-w7b-cli-") as temporary:
            scratch = Path(temporary)
            spec_path = scratch / "spec.json"
            spec_path.write_text(json.dumps({"explicit_relations": [{
                "relation_id": "rel-w5e-depends-ci1",
                "relation_type": "depends_on",
                "source_workstream_id": "W5E",
                "target_workstream_id": "CI1",
                "reason": "late CI adjacency",
            }]}), encoding="utf-8")
            discover_stream = io.StringIO()
            with contextlib.redirect_stdout(discover_stream):
                discover_exit = relations_cli.main(["discover", "--target", str(fixture.root), "--spec", str(spec_path), "--recorded-at", DISCOVERY_AT, "--json"])
            self.assertIn(discover_exit, (0, 5))
            discovery = json.loads(discover_stream.getvalue())["data"]
            discovery_path = scratch / "discovery.json"
            discovery_path.write_text(json.dumps(discovery), encoding="utf-8")
            lifecycles = []
            for item in discovery["candidates"]:
                record = item["record"]
                state = "active" if (
                    (record["source_workstream_id"], record["target_workstream_id"])
                    in {("W5E", "W5D"), ("W5E", "CI1")}
                ) else "proposed"
                lifecycles.extend(["--lifecycle", f"{record['relation_id']}={state}"])
            plan_stream = io.StringIO()
            with contextlib.redirect_stdout(plan_stream):
                self.assertEqual(relations_cli.main([
                    "plan", "--target", str(fixture.root), "--discovery", str(discovery_path),
                    "--actor-id", "maintainer", "--issued-at", PLAN_AT, "--expires-at", EXPIRES_AT,
                    "--confirm-local", "--json", *lifecycles,
                ]), 0)
            plan_data = json.loads(plan_stream.getvalue())["data"]
            plan_path = scratch / "plan.json"
            plan_path.write_text(json.dumps(plan_data["plan"]), encoding="utf-8")
            apply_stream = io.StringIO()
            confirmation = plan_data["confirmation"]
            with contextlib.redirect_stdout(apply_stream):
                self.assertEqual(relations_cli.main([
                    "apply", "--target", str(fixture.root), "--plan", str(plan_path),
                    "--plan-id", plan_data["plan"]["plan_id"], "--plan-hash", plan_data["plan"]["plan_hash"],
                    "--confirmation-id", confirmation["confirmation_id"], "--confirmation-token", confirmation["confirmation_token"],
                    "--actor-id", "maintainer", "--occurred-at", APPLY_AT, "--json",
                ]), 0)
            receipt = json.loads(apply_stream.getvalue())["data"]
            receipt_stream = io.StringIO()
            with contextlib.redirect_stdout(receipt_stream):
                self.assertEqual(relations_cli.main(["receipt", "--target", str(fixture.root), "--receipt-id", receipt["receipt_id"], "--json"]), 0)
            self.assertEqual(json.loads(receipt_stream.getvalue())["data"], receipt)
            undo_stream = io.StringIO()
            with contextlib.redirect_stdout(undo_stream):
                self.assertEqual(relations_cli.main([
                    "undo", "--target", str(fixture.root), "--receipt-id", receipt["receipt_id"],
                    "--actor-id", "maintainer", "--issued-at", PLAN_AT, "--expires-at", EXPIRES_AT,
                    "--confirm-local", "--json",
                ]), 0)
            undo_data = json.loads(undo_stream.getvalue())["data"]
            undo_path = scratch / "undo.json"
            undo_path.write_text(json.dumps(undo_data["plan"]), encoding="utf-8")
            undo_confirmation = undo_data["confirmation"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(relations_cli.main([
                    "undo", "--target", str(fixture.root), "--undo-plan", str(undo_path), "--execute",
                    "--actor-id", "maintainer", "--plan-id", undo_data["plan"]["plan_id"],
                    "--plan-hash", undo_data["plan"]["plan_hash"],
                    "--confirmation-id", undo_confirmation["confirmation_id"],
                    "--confirmation-token", undo_confirmation["confirmation_token"],
                    "--occurred-at", UNDO_AT, "--json",
                ]), 0)
            inspect_stream = io.StringIO()
            with contextlib.redirect_stdout(inspect_stream):
                self.assertEqual(relations_cli.main(["inspect", "--target", str(fixture.root), "--json"]), 0)
            inspection = json.loads(inspect_stream.getvalue())["data"]
            self.assertEqual(inspection["graph_status"], "current")
            self.assertTrue(inspection["receipt_ids"])


if __name__ == "__main__":
    unittest.main()
