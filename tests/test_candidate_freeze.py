from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
sys.path[:0] = [str(CORE_SOURCE), str(CLI_SOURCE), str(REPOSITORY_ROOT)]

import project_orrery_core.candidate_freeze as candidate_freeze  # noqa: E402
from project_orrery_core.candidate_freeze import (  # noqa: E402
    freeze_candidate,
    inspect_candidate_lifecycle,
    inspect_candidate_surface,
    record_candidate_validation,
    request_candidate_validation,
    validate_candidate_freeze_receipt,
    validate_candidate_validation_receipt,
)
from project_orrery_core.collaboration import (  # noqa: E402
    refresh_workstream_scope,
    write_workstream_session,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


class CandidateFreezeTests(unittest.TestCase):
    def _prepare(
        self, fixture: CollaborationGitFixture, *, expected: tuple[str, ...] = ("README.md",)
    ) -> tuple[Path, str]:
        root = fixture.worktree_b
        head = fixture.git(root, "rev-parse", "HEAD").stdout.strip()
        write_workstream_session(
            root,
            workstream_id="W3.1-fixture",
            primary_subsystem_id="project-structure",
            expected_writes=expected,
            validation_surfaces=["tests/test_candidate_freeze.py"],
            lifecycle_phase="implementing",
            member_id="fixture-owner",
        )
        refreshed = refresh_workstream_scope(root, include_local_worktrees=False)
        if not refreshed["expansion"]["allowed"]:
            refreshed = refresh_workstream_scope(
                root, include_local_worktrees=False, confirm_l2=True,
                reason="focused Candidate freeze fixture confirms its declared exact paths",
            )
        self.assertTrue(refreshed["local_work_allowed"], refreshed)
        return root, head

    @staticmethod
    def _edit(root: Path, relative: str = "README.md", text: str = "# accepted candidate\n") -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def _preview(self, root: Path, head: str, surface_ids: tuple[str, ...] = ("ui:fixture",)) -> dict[str, object]:
        return freeze_candidate(
            root, task_description_sha=head, accepted_surface_fingerprint=None,
            accepted_surface_ids=surface_ids,
        )

    def _freeze(self, root: Path, head: str, surface_ids: tuple[str, ...] = ("ui:fixture",)) -> dict[str, object]:
        preview = self._preview(root, head, surface_ids)
        return freeze_candidate(
            root, task_description_sha=head,
            accepted_surface_fingerprint=str(preview["accepted_surface_fingerprint"]),
            accepted_surface_ids=surface_ids, apply=True, message="freeze fixture Candidate",
        )

    def test_schema_validation_accepts_generated_receipts_and_rejects_extra_fields(self) -> None:
        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root)
            receipt = self._freeze(root, head)
            stored = json.loads(Path(str(receipt["receipt_path"])).read_text(encoding="utf-8"))
            validate_candidate_freeze_receipt(stored)
            invalid = dict(stored)
            invalid["forged"] = True
            with self.assertRaisesRegex(ValueError, "forbidden field"):
                validate_candidate_freeze_receipt(invalid)

    def test_dry_run_is_zero_write_and_apply_creates_one_commit_and_private_receipt(self) -> None:
        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root)
            before_status = fixture.git(root, "status", "--porcelain=v1").stdout
            started = time.monotonic()
            preview = self._preview(root, head)
            self.assertLess(time.monotonic() - started, 30)
            self.assertFalse(preview["writes_performed"])
            self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), head)
            self.assertEqual(fixture.git(root, "status", "--porcelain=v1").stdout, before_status)
            receipt = freeze_candidate(
                root, task_description_sha=head,
                accepted_surface_fingerprint=str(preview["accepted_surface_fingerprint"]),
                accepted_surface_ids=("ui:fixture",), apply=True,
            )
            self.assertTrue(receipt["writes_performed"])
            self.assertEqual(fixture.git(root, "rev-list", "--count", f"{head}..HEAD").stdout.strip(), "1")
            self.assertEqual(fixture.git(root, "status", "--porcelain=v1").stdout, "")
            self.assertTrue(Path(str(receipt["receipt_path"])).is_file())
            self.assertEqual(receipt["validation_status"], "pending")
            self.assertLess(receipt["elapsed_ms"], 30000)

    def test_acceptance_drift_and_unexpected_path_refuse_before_commit(self) -> None:
        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root, text="# first preview\n")
            accepted = self._preview(root, head)
            self._edit(root, text="# changed after acceptance\n")
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                freeze_candidate(
                    root, task_description_sha=head,
                    accepted_surface_fingerprint=str(accepted["accepted_surface_fingerprint"]),
                    accepted_surface_ids=("ui:fixture",), apply=True,
                )
            self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), head)
            self._edit(root, "rogue.txt", "unexpected\n")
            with self.assertRaisesRegex(ValueError, "unexpected changed path"):
                self._preview(root, head)
            self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), head)

    def test_conflict_forbidden_parity_and_diff_fail_before_commit(self) -> None:
        cases = (
            (("README.md",), {"README.md": "<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\n"}, (), "conflict marker"),
            (("README.pyc",), {"README.pyc": "not-bytecode\n"}, (), "forbidden artifact"),
            (("README.md", "copy.md"), {"README.md": "left\n", "copy.md": "right\n"}, (("README.md", "copy.md"),), "parity failed"),
            (("README.md",), {"README.md": "trailing whitespace   \n"}, (), "diff --check"),
        )
        for expected, files, pairs, error in cases:
            with self.subTest(error=error), CollaborationGitFixture() as fixture:
                root, head = self._prepare(fixture, expected=expected)
                for relative, text in files.items():
                    self._edit(root, relative, text)
                with self.assertRaisesRegex(ValueError, error):
                    freeze_candidate(
                        root, task_description_sha=head, accepted_surface_fingerprint=None,
                        exact_copy_pairs=pairs,
                    )
                self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), head)

    def test_hard_timeout_refuses_before_commit(self) -> None:
        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root)
            values = iter((0.0, 61.0))
            with self.assertRaisesRegex(ValueError, "hard timeout"):
                freeze_candidate(
                    root, task_description_sha=head,
                    accepted_surface_fingerprint=inspect_candidate_surface(
                        root, accepted_surface_ids=("ui:fixture",)
                    )["accepted_surface_fingerprint"],
                    accepted_surface_ids=("ui:fixture",), apply=True,
                    monotonic=lambda: next(values),
                )
            self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), head)

    def test_freeze_subprocess_boundary_invokes_git_only_and_no_validation(self) -> None:
        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root)
            calls: list[list[str]] = []
            original = candidate_freeze.subprocess.run

            def capture(command: list[str], **kwargs: object):  # type: ignore[no-untyped-def]
                calls.append(command)
                return original(command, **kwargs)

            with mock.patch.object(candidate_freeze.subprocess, "run", side_effect=capture):
                self._preview(root, head)
            self.assertTrue(calls)
            self.assertTrue(all(Path(command[0]).name.lower() in {"git", "git.exe"} for command in calls))
            forbidden = {"unittest", "pytest", "fast", "checkpoint", "candidate", "promotion", "build"}
            self.assertFalse(any(token.lower() in forbidden for command in calls for token in command[1:]))

    def test_async_pass_fail_are_immutable_and_failed_candidate_is_not_retried(self) -> None:
        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root)
            freeze = self._freeze(root, head)
            candidate = str(freeze["candidate_sha"])
            private_root = Path(str(freeze["receipt_path"])).parents[2]
            pending_status = inspect_candidate_lifecycle(
                private_root, workstream_id="W3.1-fixture", head_oid=candidate
            )
            self.assertEqual(pending_status["status_code"], "candidate-validation-pending")
            self.assertEqual(pending_status["closure_state"], "open")
            clean = fixture.git(root, "status", "--porcelain=v1").stdout
            request = request_candidate_validation(
                root, freeze_receipt_id=str(freeze["receipt_id"])
            )
            self.assertEqual(request["decision"], "requested")
            self.assertTrue(Path(str(request["request_path"])).is_file())
            self.assertEqual(fixture.git(root, "status", "--porcelain=v1").stdout, clean)
            passed = record_candidate_validation(
                root, freeze_receipt_id=str(freeze["receipt_id"]), validation_stage="focused",
                result_receipt={
                    "contract_type": "orrery-test-shard-result-v2", "head_sha": candidate,
                    "selected_test_ids": ["tests.pass"],
                    "records": [{"test_id": "tests.pass", "outcome": "success"}],
                    "successful": True, "completed": True, "duration_seconds": 0.01,
                    "os": "fixture", "python": "fixture",
                },
            )
            stored = json.loads(Path(str(passed["receipt_path"])).read_text(encoding="utf-8"))
            validate_candidate_validation_receipt(stored)
            self.assertEqual(passed["validation_status"], "validated")
            validated_status = inspect_candidate_lifecycle(
                private_root, workstream_id="W3.1-fixture", head_oid=candidate
            )
            self.assertEqual(validated_status["status_code"], "candidate-validated")
            closed_status = inspect_candidate_lifecycle(
                private_root, workstream_id="W3.1-fixture", head_oid=candidate,
                lifecycle_phase="closed", closure_reason="integrated",
            )
            self.assertEqual(closed_status["status_code"], "workstream-closed")
            self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), candidate)
            self.assertEqual(fixture.git(root, "status", "--porcelain=v1").stdout, clean)
            reused = request_candidate_validation(
                root, freeze_receipt_id=str(freeze["receipt_id"])
            )
            self.assertEqual(reused["decision"], "reuse-prior-receipt")
            invalid_validation = dict(stored)
            invalid_validation["candidate_unchanged"] = False
            with self.assertRaisesRegex(ValueError, "must equal True"):
                validate_candidate_validation_receipt(invalid_validation)

        with CollaborationGitFixture() as fixture:
            root, head = self._prepare(fixture)
            self._edit(root)
            freeze = self._freeze(root, head)
            candidate = str(freeze["candidate_sha"])
            failure_result = {
                "contract_type": "orrery-test-shard-result-v2", "head_sha": candidate,
                "selected_test_ids": ["tests.fail"],
                "records": [{"test_id": "tests.fail", "outcome": "failure"}],
                "successful": False, "completed": True, "duration_seconds": 0.01,
                "runner_errors": [],
            }
            failed = record_candidate_validation(
                root, freeze_receipt_id=str(freeze["receipt_id"]),
                result_receipt=failure_result, validation_stage="focused",
            )
            self.assertEqual(failed["validation_status"], "validation-failed")
            failed_status = inspect_candidate_lifecycle(
                Path(str(failed["receipt_path"])).parents[2],
                workstream_id="W3.1-fixture", head_oid=candidate,
            )
            self.assertEqual(failed_status["status_code"], "candidate-validation-failed")
            with self.assertRaisesRegex(ValueError, "cannot be retried"):
                record_candidate_validation(
                    root, freeze_receipt_id=str(freeze["receipt_id"]),
                    result_receipt=failure_result, validation_stage="focused",
                )
            with self.assertRaisesRegex(ValueError, "cannot be retried"):
                request_candidate_validation(
                    root, freeze_receipt_id=str(freeze["receipt_id"])
                )
            self.assertEqual(fixture.git(root, "rev-parse", "HEAD").stdout.strip(), candidate)
            self.assertEqual(fixture.git(root, "status", "--porcelain=v1").stdout, "")


if __name__ == "__main__":
    unittest.main()
