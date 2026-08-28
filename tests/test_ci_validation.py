from __future__ import annotations

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CI_SCRIPTS = ROOT / "scripts" / "ci"
sys.path.insert(0, str(CI_SCRIPTS))

from _common import (  # noqa: E402
    CIValidationError,
    DEFAULT_MANIFEST,
    atomic_write_json,
    expand_profile,
    git_sha,
    load_json,
    sha256_json,
    validate_and_expand_manifest,
)
from aggregate_test_results import aggregate  # noqa: E402
from run_test_shard import TimedTextResult, run_selected  # noqa: E402
from validate_ci import validate_binding, validate_workflows  # noqa: E402


class CIValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(DEFAULT_MANIFEST)

    def _write_manifest(self, directory: Path, manifest: dict) -> Path:
        path = directory / "manifest.json"
        atomic_write_json(path, manifest)
        return path

    def _result_payloads(self, expected_os: str = "Windows") -> tuple[dict, dict[str, list[str]]]:
        test_ids, assignments, _ = validate_and_expand_manifest(self.manifest)
        manifest_hash = sha256_json(self.manifest)
        inventory_hash = sha256_json(test_ids)
        head = git_sha()
        payloads = {}
        for shard, selected in assignments.items():
            payloads[shard] = {
                "schema_version": 1,
                "contract_type": "orrery-test-shard-result-v1",
                "role": "promotion-shard",
                "sha": head,
                "os": expected_os,
                "python": "3.11.0",
                "shard": shard,
                "manifest_sha256": manifest_hash,
                "inventory_sha256": inventory_hash,
                "orrery_test_build": "1",
                "selected_test_count": len(selected),
                "selected_test_ids": selected,
                "records": [
                    {
                        "sha": head,
                        "os": expected_os,
                        "python": "3.11.0",
                        "shard": shard,
                        "test_id": test_id,
                        "outcome": "success",
                        "duration_seconds": 0.001,
                    }
                    for test_id in selected
                ],
                "tests_run": len(selected),
                "successful": True,
                "completed": True,
                "duration_seconds": 0.01,
                "runner_errors": [],
            }
        return payloads, assignments

    def _write_payloads(self, directory: Path, payloads: dict[str, dict]) -> None:
        for shard, payload in payloads.items():
            atomic_write_json(directory / shard / "result.json", payload)

    def test_inventory_assigns_every_final_test_once_and_splits_workspace_methods(self) -> None:
        test_ids, assignments, fast_ids = validate_and_expand_manifest(self.manifest)
        checkpoint_ids = expand_profile(self.manifest, "checkpoint", test_ids)
        assigned = [test_id for selected in assignments.values() for test_id in selected]
        self.assertEqual(sorted(assigned), test_ids)
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertLess(len(fast_ids), len(test_ids))
        self.assertTrue(set(fast_ids).issubset(checkpoint_ids))
        self.assertLess(len(checkpoint_ids), len(test_ids))
        self.assertEqual(self.manifest["fast"]["budget_seconds"], 15)
        self.assertEqual(self.manifest["checkpoint"]["budget_seconds"], 90)
        w7b = next(
            shard for shard in self.manifest["shards"] if shard["id"] == "team-relations-execution"
        )
        self.assertEqual(w7b["budget_seconds"], 300)
        self.assertEqual(
            assignments["team-relations-execution"],
            sorted(
                test_id
                for test_id in test_ids
                if test_id.startswith("test_workstream_relation_execution.")
            ),
        )
        workspace = [
            shard for shard in self.manifest["shards"] if shard["surface"] == "Workspace Maintenance"
        ]
        self.assertGreaterEqual(len(workspace), 4)
        self.assertFalse(any("test_workspace_maintenance.*" in shard["selectors"] for shard in workspace))

    def test_inventory_rejects_missing_duplicate_and_dead_selectors(self) -> None:
        missing = copy.deepcopy(self.manifest)
        workspace_contract = next(item for item in missing["shards"] if item["id"] == "workspace-contract")
        workspace_contract["selectors"] = [
            "test_workspace_maintenance.WorkspaceMaintenanceTests.test_action_surface_rejects_branch_path_shell_url_and_ai_authority"
        ]
        with self.assertRaisesRegex(CIValidationError, "multiple shards|incomplete"):
            validate_and_expand_manifest(missing)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["shards"][0]["selectors"].append("test_context_routing_oracle_v02.*")
        with self.assertRaisesRegex(CIValidationError, "multiple shards"):
            validate_and_expand_manifest(duplicate)

        dead = copy.deepcopy(self.manifest)
        dead["shards"][0]["selectors"][0] = "test_module_that_does_not_exist.*"
        with self.assertRaisesRegex(CIValidationError, "matched no final unittest ID"):
            validate_and_expand_manifest(dead)

    def test_timing_result_preserves_unittest_failure_semantics(self) -> None:
        class FailingTest(unittest.TestCase):
            def test_failure(self) -> None:
                self.fail("expected failure")

        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, resultclass=TimedTextResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(FailingTest)
        )
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.records[0]["outcome"], "failure")
        self.assertGreaterEqual(result.records[0]["duration_seconds"], 0)

    def test_runner_emits_sha_os_python_test_id_outcome_and_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = copy.deepcopy(self.manifest)
            manifest["fast"]["selectors"] = [
                "test_authority_release_candidate_gate.AuthorityReleaseCandidateGateTests.test_historical_v020_inputs_match_frozen_hashes"
            ]
            manifest_path = self._write_manifest(directory, manifest)
            output = directory / "result.json"
            with mock.patch.dict(os.environ, {"RUNNER_OS": "FixtureOS"}, clear=False):
                payload, successful = run_selected(
                    manifest_path=manifest_path, shard=None, profile="fast", output=output
                )
            self.assertTrue(successful)
            self.assertEqual(payload["sha"], git_sha())
            self.assertEqual(payload["os"], "FixtureOS")
            self.assertRegex(str(payload["python"]), r"^\d+\.\d+\.\d+")
            self.assertEqual(payload["records"][0]["outcome"], "success")
            self.assertIn("duration_seconds", payload["records"][0])
            self.assertEqual(payload["records"][0]["sha"], payload["sha"])
            self.assertEqual(payload["records"][0]["os"], payload["os"])
            self.assertEqual(payload["records"][0]["python"], payload["python"])
            self.assertEqual(payload["records"][0]["shard"], "fast")
            self.assertEqual(payload["budget_seconds"], 15.0)
            self.assertFalse(payload["budget_exceeded"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["shard"], "fast")

    def test_runner_enforces_profile_budget_without_changing_promotion_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = copy.deepcopy(self.manifest)
            manifest["fast"]["budget_seconds"] = 0.000001
            manifest["fast"]["selectors"] = [
                "test_authority_release_candidate_gate.AuthorityReleaseCandidateGateTests.test_historical_v020_inputs_match_frozen_hashes"
            ]
            manifest_path = self._write_manifest(directory, manifest)
            payload, successful = run_selected(
                manifest_path=manifest_path,
                shard=None,
                profile="fast",
                output=directory / "result.json",
            )
            self.assertFalse(successful)
            self.assertTrue(payload["budget_exceeded"])
            self.assertEqual(payload["role"], "non-promotion-feedback")

    def test_aggregate_accepts_complete_once_only_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            payloads, _ = self._result_payloads()
            self._write_payloads(directory, payloads)
            result = aggregate(
                manifest_path=DEFAULT_MANIFEST,
                results_dir=directory,
                expected_os="Windows",
                expected_sha=git_sha(),
                matrix_result="success",
                gate_result="success",
            )
            self.assertTrue(result["complete"], result["errors"])
            self.assertEqual(result["expected_test_count"], result["recorded_test_count"])

    def test_aggregate_fails_on_missing_duplicate_failed_or_skipped_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            payloads, assignments = self._result_payloads()
            removed = next(iter(payloads))
            payloads.pop(removed)
            duplicate_target = next(iter(payloads))
            payloads[duplicate_target]["records"].append(
                copy.deepcopy(payloads[duplicate_target]["records"][0])
            )
            payloads[duplicate_target]["successful"] = False
            self._write_payloads(directory, payloads)
            result = aggregate(
                manifest_path=DEFAULT_MANIFEST,
                results_dir=directory,
                expected_os="Windows",
                expected_sha=git_sha(),
                matrix_result="cancelled",
                gate_result="skipped",
            )
            self.assertFalse(result["complete"])
            joined = "\n".join(result["errors"])
            self.assertIn("missing shard artifacts", joined)
            self.assertIn("did not execute exactly once", joined)
            self.assertIn("cancelled", joined)
            self.assertIn("skipped", joined)
            self.assertTrue(assignments[removed])

    def test_workflow_validator_separates_fast_and_promotion_roles(self) -> None:
        self.assertEqual(validate_workflows(), [])
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fast = directory / "fast.yml"
            promotion = directory / "promotion.yml"
            shutil.copy2(ROOT / ".github/workflows/fast-validation.yml", fast)
            text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
            promotion.write_text(text.replace("  workflow_dispatch:", "  push:", 1), encoding="utf-8")
            errors = validate_workflows(fast, promotion)
            self.assertTrue(any("workflow_dispatch" in error for error in errors))

    def test_promotion_preflight_installs_discovery_dependencies_before_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fast = directory / "fast.yml"
            promotion = directory / "promotion.yml"
            shutil.copy2(ROOT / ".github/workflows/fast-validation.yml", fast)
            text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
            step = (
                "      - name: Install preflight discovery dependencies\n"
                "        run: python -m pip install \"wheel>=0.41,<1\" -r "
                "skills/project-orrery/assets/project-template/scripts/docsite/requirements.txt\n"
            )
            self.assertIn(step, text)
            promotion.write_text(text.replace(step, "", 1), encoding="utf-8")
            errors = validate_workflows(fast, promotion)
            self.assertTrue(any("preflight" in error.lower() and "dependencies" in error for error in errors))

    def test_exact_sha_binding_rejects_main_sha_alias_and_mismatch(self) -> None:
        head = git_sha()
        self.assertEqual(validate_binding("codex/frozen-candidate", head), [])
        self.assertTrue(validate_binding("main", head))
        self.assertTrue(validate_binding(head, head))
        self.assertTrue(validate_binding("codex/frozen-candidate", "0" * 40))


if __name__ == "__main__":
    unittest.main()
