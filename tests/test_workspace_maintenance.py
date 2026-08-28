from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
for source in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE, REPOSITORY_ROOT):
    sys.path.insert(0, str(source))

from project_orrery_core.collaboration import (  # noqa: E402
    CollaborationConfig,
    refresh_workstream_scope,
    transition_workstream_session,
    write_workstream_session,
)
from project_orrery_core.maintenance import (  # noqa: E402
    DEFAULT_POLICY,
    authorize_maintenance_item,
    catch_up_maintenance_scan,
    execute_maintenance_authorization,
    inspect_maintenance_item,
    list_maintenance_queue,
    load_host_preferences,
    load_maintenance_policy,
    maintenance_status,
    run_maintenance_scan,
    validate_host_preferences,
    validate_maintenance_contract,
    validate_maintenance_policy,
)
from project_orrery_core.review import (  # noqa: E402
    generate_review_package,
    record_review_decision,
    write_closure_record,
)
from project_orrery_core.workspace_cleanup import compute_workspace_cleanup_eligibility  # noqa: E402
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


PASS_COMMAND = 'python -c "import sys; sys.exit(0)"'
SCHEMA = CORE_SOURCE / "project_orrery_core" / "schema" / "maintenance-v1.json"
CORPUS = REPOSITORY_ROOT / "tests" / "fixtures" / "workspace-maintenance" / "v1" / "scenarios.json"


def _same_workspace_path(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> bool:
    return os.path.normcase(os.path.realpath(os.path.abspath(left))) == os.path.normcase(
        os.path.realpath(os.path.abspath(right))
    )


class WorkspaceMaintenanceTests(unittest.TestCase):
    def _closed(self, fixture: CollaborationGitFixture) -> tuple[dict[str, object], dict[str, object]]:
        (fixture.worktree_b / "README.md").write_text("# fixture\nmaintenance candidate\n", encoding="utf-8")
        fixture.git(fixture.worktree_b, "add", "README.md")
        fixture.git(fixture.worktree_b, "commit", "-m", "maintenance candidate")
        write_workstream_session(
            fixture.worktree_b,
            workstream_id="W6-maintenance-fixture",
            primary_subsystem_id="project-structure",
            expected_writes=["README.md"],
            validation_surfaces=[PASS_COMMAND],
            lifecycle_phase="implementing",
        )
        refreshed = refresh_workstream_scope(
            fixture.worktree_b,
            include_local_worktrees=False,
            occurred_at="2026-08-01T12:00:00Z",
        )
        if not refreshed["expansion"]["allowed"]:
            refresh_workstream_scope(
                fixture.worktree_b,
                include_local_worktrees=False,
                confirm_l2=True,
                reason="maintenance fixture confirms the declared surface",
                occurred_at="2026-08-01T12:00:01Z",
            )
        transition_workstream_session(
            fixture.worktree_b,
            lifecycle_phase="validating",
            evidence_freshness="current",
            reason="maintenance fixture validation",
            occurred_at="2026-08-01T12:01:00Z",
        )
        result = generate_review_package(fixture.worktree_b)
        package = result["review_package"]
        record_review_decision(
            fixture.worktree_b,
            package=package["package_id"],
            action="approve",
            actor_id="local-owner",
            reason="maintenance fixture integration approval",
            evidence_refs=[f"git:{package['binding']['candidate_head']}"],
        )
        fixture.git(fixture.repository, "merge", "--no-ff", "--no-edit", "codex/fixture-b")
        final_oid = fixture.git(fixture.repository, "rev-parse", "main").stdout.strip()
        closure = write_closure_record(
            fixture.worktree_b,
            package=package["package_id"],
            final_oid=final_oid,
            actor_id="local-owner",
            closed_at="2026-08-01T12:10:00Z",
        )
        transition_workstream_session(
            fixture.worktree_b,
            lifecycle_phase="closed",
            closure_reason="integrated",
            reason="maintenance fixture closes the integrated workstream",
            occurred_at="2026-08-01T12:10:01Z",
        )
        return result, closure

    def test_versioned_contract_policy_and_synthetic_corpus_are_fail_closed(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "project-orrery-maintenance-v1")
        for name in ("maintenance_policy", "maintenance_scan", "maintenance_queue_item", "maintenance_authorization", "maintenance_receipt"):
            self.assertFalse(schema["$defs"][name].get("additionalProperties", True))
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        self.assertEqual(len(corpus["scenarios"]), 11)
        self.assertEqual(
            {item["id"] for item in corpus["scenarios"]},
            {"clean-integrated", "dirty", "unique-commit", "untracked", "allowlisted-ignored", "sensitive-ignored", "reparse-escape", "stale-closure", "process-use", "recovery-evidence", "missing-path"},
        )
        self.assertFalse(corpus["destructive_action_performed"])
        valid = validate_maintenance_policy(DEFAULT_POLICY)
        self.assertFalse(valid["auto_remove_eligible_worktrees"])
        with self.assertRaisesRegex(ValueError, "unknown workspace maintenance policy field"):
            validate_maintenance_policy({**DEFAULT_POLICY, "shell": "rm -rf"})
        with self.assertRaisesRegex(ValueError, "unsupported in Phase 0-2"):
            validate_maintenance_policy({**DEFAULT_POLICY, "auto_remove_eligible_worktrees": True})
        with self.assertRaisesRegex(ValueError, "incompatible field"):
            validate_host_preferences({**load_host_preferences(REPOSITORY_ROOT), "cron": True})
        with self.assertRaisesRegex(ValueError, "unknown project collaboration config field"):
            CollaborationConfig.from_manifest({"collaboration": {"scheduler": {"command": "x"}}})
        with self.assertRaisesRegex(ValueError, "incompatible field"):
            validate_maintenance_contract(
                {
                    "schema_version": 1,
                    "contract_type": "maintenance-receipt",
                    "receipt_id": "maintenance-receipt-" + "1" * 24,
                    "authorization_id": "maintenance-authorization-" + "2" * 24,
                    "item_id": "maintenance-item-" + "3" * 24,
                    "action": "remove-worktree",
                    "started_at": "2026-08-27T00:00:00Z",
                    "finished_at": None,
                    "outcome": "unknown",
                    "preflight": {},
                    "postflight": {},
                    "execution_performed": False,
                    "branch_deleted": False,
                    "remote_branch_deleted": False,
                    "network_performed": False,
                    "shell": "forbidden",
                }
            )

    def test_scan_is_bounded_zero_network_debounced_single_flight_and_times_out(self) -> None:
        with CollaborationGitFixture() as fixture:
            with mock.patch.object(socket, "socket", side_effect=AssertionError("network socket opened")), mock.patch.object(socket, "create_connection", side_effect=AssertionError("network connection opened")):
                first = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:00:00Z")
            self.assertEqual(first["scan"]["status"], "succeeded")
            self.assertFalse(first["destructive_action_performed"])
            event = run_maintenance_scan(fixture.repository, reason="closure-event", now="2026-08-27T12:00:01Z", debounce_seconds=5)
            self.assertEqual(event["scan"]["status"], "debounced")
            lock = Path(fixture.git(fixture.repository, "rev-parse", "--path-format=absolute", "--git-path", "orrery/maintenance/scan.lock").stdout.strip())
            lock.parent.mkdir(parents=True, exist_ok=True)
            lock.write_text("locked", encoding="utf-8")
            concurrent = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:00:02Z")
            self.assertEqual(concurrent["scan"]["status"], "single-flight")
            lock.unlink()
            empty_inventory = {"inventory_schema_version": 1, "content_hash": "1" * 64, "entries": []}
            with mock.patch("project_orrery_core.maintenance.time.monotonic", side_effect=[0.0, 2.0]):
                timed = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:00:03Z", timeout_seconds=1, inventory_provider=lambda _root: empty_inventory)
            self.assertEqual(timed["scan"]["status"], "timed-out")
            hard_timed = run_maintenance_scan(
                fixture.repository,
                reason="manual",
                now="2026-08-27T12:00:03.500000Z",
                timeout_seconds=0.01,
                inventory_provider=lambda _root: (time.sleep(0.1), empty_inventory)[1],
            )
            self.assertEqual(hard_timed["scan"]["status"], "timed-out")
            with self.assertRaises(KeyboardInterrupt):
                run_maintenance_scan(
                    fixture.repository,
                    reason="manual",
                    now="2026-08-27T12:00:04Z",
                    inventory_provider=lambda _root: (_ for _ in ()).throw(KeyboardInterrupt()),
                )
            recovered = run_maintenance_scan(
                fixture.repository,
                reason="manual",
                now="2026-08-27T12:00:05Z",
                inventory_provider=lambda _root: empty_inventory,
            )
            self.assertEqual(recovered["scan"]["status"], "succeeded")
            runs = lock.parent / "runs"
            records = [json.loads(path.read_text(encoding="utf-8")) for path in runs.glob("maintenance-scan-*.json")]
            self.assertIn("interrupted", {record["status"] for record in records})

    def test_observatory_catch_up_respects_24_hour_freshness(self) -> None:
        with CollaborationGitFixture() as fixture:
            first = catch_up_maintenance_scan(fixture.repository, now="2026-08-25T00:00:00Z")
            self.assertTrue(first["scan_performed"])
            fresh = catch_up_maintenance_scan(fixture.repository, now="2026-08-25T23:59:00Z")
            self.assertEqual(fresh["status"], "fresh")
            self.assertFalse(fresh["scan_performed"])
            later = catch_up_maintenance_scan(fixture.repository, now="2026-08-26T00:01:00Z")
            self.assertTrue(later["scan_performed"])

    def test_queue_authorization_is_evidence_bound_and_drift_stales(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._closed(fixture)
            scan = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:00:00Z")
            event_dir = Path(
                fixture.git(
                    fixture.repository,
                    "rev-parse",
                    "--path-format=absolute",
                    "--git-path",
                    "orrery/maintenance/events",
                ).stdout.strip()
            )
            event_reasons = {
                json.loads(path.read_text(encoding="utf-8"))["reason"]
                for path in event_dir.glob("maintenance-event-*.json")
            }
            self.assertEqual(event_reasons, {"integration-event", "closure-event"})
            item = next(value for value in scan["queue"] if _same_workspace_path(value["workspace_path"], fixture.worktree_b))
            self.assertEqual(item["action"], "remove-worktree")
            self.assertEqual(len(item["binding"]["evidence_hash"]), 64)
            authorization = authorize_maintenance_item(fixture.repository, item_id=item["item_id"], action="remove-worktree", actor_id="maintainer", authorized_at="2026-08-27T12:01:00Z")
            self.assertEqual(authorization["authorization"]["status"], "authorized")
            self.assertFalse(authorization["authorization"]["execution_performed"])
            (fixture.worktree_b / "drift.txt").write_text("preserve\n", encoding="utf-8")
            stale = execute_maintenance_authorization(fixture.repository, authorization_id=authorization["authorization"]["authorization_id"], started_at="2026-08-27T12:02:00Z")
            self.assertEqual(stale["receipt"]["outcome"], "stale")
            self.assertTrue(fixture.worktree_b.exists())
            self.assertFalse(stale["destructive_action_performed"])

            (fixture.worktree_b / "drift.txt").unlink()
            rescanned = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:03:00Z")
            item = next(value for value in rescanned["queue"] if _same_workspace_path(value["workspace_path"], fixture.worktree_b))
            authorization = authorize_maintenance_item(
                fixture.repository,
                item_id=item["item_id"],
                action="remove-worktree",
                actor_id="maintainer",
                authorized_at="2026-08-27T12:04:00Z",
            )["authorization"]
            fixture.git(fixture.repository, "worktree", "lock", "--reason", "process-use fixture", str(fixture.worktree_b))
            process_use = execute_maintenance_authorization(
                fixture.repository,
                authorization_id=authorization["authorization_id"],
                started_at="2026-08-27T12:05:00Z",
            )
            self.assertEqual(process_use["receipt"]["outcome"], "stale")
            self.assertTrue(process_use["receipt"]["preflight"]["locked_or_process_use"])
            fixture.git(fixture.repository, "worktree", "unlock", str(fixture.worktree_b))

            rescanned = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:06:00Z")
            item = next(value for value in rescanned["queue"] if _same_workspace_path(value["workspace_path"], fixture.worktree_b))
            authorization = authorize_maintenance_item(
                fixture.repository,
                item_id=item["item_id"],
                action="remove-worktree",
                actor_id="maintainer",
                authorized_at="2026-08-27T12:07:00Z",
            )["authorization"]
            with mock.patch("project_orrery_core.maintenance._run_worktree_remove", side_effect=KeyboardInterrupt()):
                with self.assertRaises(KeyboardInterrupt):
                    execute_maintenance_authorization(
                        fixture.repository,
                        authorization_id=authorization["authorization_id"],
                        started_at="2026-08-27T12:08:00Z",
                    )
            receipt = next(
                value
                for value in maintenance_status(fixture.repository)["receipts"]
                if value["authorization_id"] == authorization["authorization_id"]
            )
            self.assertEqual(receipt["outcome"], "interrupted")
            self.assertFalse(receipt["execution_performed"])
            self.assertTrue(fixture.worktree_b.exists())

    def test_remove_worktree_executor_preserves_branch_commit_and_receipt(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._closed(fixture)
            scan = run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:00:00Z")
            item = next(value for value in scan["queue"] if _same_workspace_path(value["workspace_path"], fixture.worktree_b))
            authorization = authorize_maintenance_item(fixture.repository, item_id=item["item_id"], action="remove-worktree", actor_id="maintainer", authorized_at="2026-08-27T12:01:00Z")["authorization"]
            branch = item["binding"]["branch"]
            head = item["binding"]["head"]
            result = execute_maintenance_authorization(fixture.repository, authorization_id=authorization["authorization_id"], started_at="2026-08-27T12:02:00Z")
            receipt = result["receipt"]
            self.assertEqual(receipt["outcome"], "verified", receipt)
            self.assertFalse(fixture.worktree_b.exists())
            self.assertNotIn(str(fixture.worktree_b), fixture.git(fixture.repository, "worktree", "list", "--porcelain").stdout)
            self.assertEqual(fixture.git(fixture.repository, "show-ref", "--verify", branch).returncode, 0)
            self.assertEqual(fixture.git(fixture.repository, "cat-file", "-e", f"{head}^{{commit}}").returncode, 0)
            self.assertFalse(receipt["branch_deleted"])
            self.assertFalse(receipt["remote_branch_deleted"])
            stored = maintenance_status(fixture.repository)["receipts"][-1]
            self.assertEqual(stored["receipt_id"], receipt["receipt_id"])

    def test_action_surface_rejects_branch_path_shell_url_and_ai_authority(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._closed(fixture)
            run_maintenance_scan(fixture.repository, reason="manual", now="2026-08-27T12:00:00Z")
            item = next(value for value in list_maintenance_queue(fixture.repository)["items"] if _same_workspace_path(value["workspace_path"], fixture.worktree_b))
            for action in ("delete-local-branch", "delete-remote-branch", "remove-directory", "shell"):
                with self.assertRaisesRegex(ValueError, "only authorizes"):
                    authorize_maintenance_item(fixture.repository, item_id=item["item_id"], action=action, actor_id="maintainer")
            with self.assertRaisesRegex(ValueError, "local human"):
                authorize_maintenance_item(fixture.repository, item_id=item["item_id"], action="remove-worktree", actor_id="agent", actor_kind="ai")
            with self.assertRaisesRegex(ValueError, "invalid maintenance authorization ID"):
                execute_maintenance_authorization(fixture.repository, authorization_id="https://example.invalid/delete")
            eligibility = compute_workspace_cleanup_eligibility(fixture.repository, workspace_path=fixture.worktree_b)
            self.assertFalse(eligibility["actions"]["delete-remote-branch"]["eligible"])

    def test_cli_json_policy_schedule_and_invalid_execute_are_stable(self) -> None:
        environment = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join((str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))),
        }
        for arguments, expected_command in (
            (["policy", "show"], "maintenance-policy"),
            (["schedule", "status"], "maintenance-schedule"),
        ):
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", "maintenance", *arguments, "--target", str(REPOSITORY_ROOT), "--json"],
                cwd=REPOSITORY_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], expected_command)
            self.assertFalse(payload["data"]["network_performed"])
        invalid = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", "maintenance", "execute", "https://example.invalid/delete", "--target", str(REPOSITORY_ROOT), "--json"],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertNotEqual(invalid.returncode, 0)
        payload = json.loads(invalid.stdout)
        self.assertEqual(payload["status"], "error")
        self.assertIn("invalid maintenance authorization ID", payload["errors"][0]["message"])


if __name__ == "__main__":
    unittest.main()
