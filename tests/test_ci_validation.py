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
    machine_inventory,
    promotion_lane_assignments,
    sha256_json,
    validate_and_expand_manifest,
)
from aggregate_test_results import aggregate  # noqa: E402
from run_test_lane import run_lane  # noqa: E402
from run_test_shard import TimedTextResult, run_selected  # noqa: E402
from validate_change import build_selection  # noqa: E402
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
        inventory_hash = machine_inventory(self.manifest)["inventory_sha256"]
        head = git_sha()
        payloads = {}
        for shard, selected in assignments.items():
            payloads[shard] = {
                "schema_version": 2,
                "contract_type": "orrery-test-shard-result-v2",
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
        sample = next(iter(payloads.values()))
        for lane, shards in promotion_lane_assignments(self.manifest).items():
            atomic_write_json(
                directory / lane / "lane-result.json",
                {
                    "schema_version": 1,
                    "contract_type": "orrery-test-lane-result-v1",
                    "sha": sample["sha"],
                    "os": sample["os"],
                    "python": sample["python"],
                    "lane": lane,
                    "manifest_sha256": sample["manifest_sha256"],
                    "shards": shards,
                    "records": [
                        {
                            "shard": shard,
                            "return_code": 0,
                            "result_file": f"result-{shard}.json",
                            "result_present": True,
                            "successful": True,
                        }
                        for shard in shards
                    ],
                    "successful": True,
                    "completed": True,
                    "duration_seconds": 0.01,
                },
            )

    def test_inventory_assigns_every_final_test_once_and_splits_workspace_methods(self) -> None:
        test_ids, assignments, fast_ids = validate_and_expand_manifest(self.manifest)
        checkpoint_ids = expand_profile(self.manifest, "checkpoint", test_ids)
        lanes = promotion_lane_assignments(self.manifest)
        assigned = [test_id for selected in assignments.values() for test_id in selected]
        self.assertEqual(sorted(assigned), test_ids)
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertLess(len(fast_ids), len(test_ids))
        self.assertTrue(set(fast_ids).issubset(checkpoint_ids))
        self.assertLess(len(checkpoint_ids), len(test_ids))
        self.assertEqual(self.manifest["fast"]["budget_seconds"], 15)
        self.assertEqual(self.manifest["checkpoint"]["budget_seconds"], 90)
        self.assertEqual(len(lanes), 10)
        lane_shards = [shard for members in lanes.values() for shard in members]
        self.assertEqual(sorted(lane_shards), sorted(assignments))
        self.assertEqual(len(lane_shards), len(set(lane_shards)))
        self.assertEqual(lanes["lane-01"], ["team-relations-execution"])
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
        minimal_git = (
            "test_workstream_relation_execution.WorkstreamRelationExecutionTests."
            "test_minimal_git_binding_rejections_and_state_axes_checkpoint"
        )
        self.assertNotIn(minimal_git, checkpoint_ids)
        self.assertIn(minimal_git, assignments["team-relations-execution"])

    def test_machine_inventory_gives_every_test_owner_stage_cost_budget_and_reason(self) -> None:
        inventory = machine_inventory(self.manifest)
        self.assertEqual(inventory["test_count"], len(inventory["tests"]))
        self.assertEqual(
            {item["test_id"] for item in inventory["tests"]},
            set(validate_and_expand_manifest(self.manifest)[0]),
        )
        for item in inventory["tests"]:
            self.assertTrue(item["owner_surface"])
            self.assertTrue(item["owner_shard"])
            self.assertTrue(item["allowed_stages"])
            self.assertIn(item["cost_class"], {"low", "medium", "heavy"})
            self.assertGreater(item["budget_seconds"], 0)
            self.assertTrue(item["dependency_reasons"])
        claims = self.manifest["routing"]["claim_sets"]
        w6 = next(item for item in claims if item["id"] == "w6-1-original-24")
        all_ids = validate_and_expand_manifest(self.manifest)[0]
        claimed = expand_profile(self.manifest, "checkpoint", all_ids)
        w6_ids = set()
        for selector in w6["selectors"]:
            from _common import expand_selectors
            w6_ids.update(expand_selectors([selector], all_ids, "fixture w6 claim"))
        self.assertEqual(len(w6_ids), 24)
        self.assertLess(len(w6_ids & set(claimed)), 24)

    def test_router_derives_w6_fast_and_checkpoint_without_full_24(self) -> None:
        maintenance_path = "packages/project-orrery-core/src/project_orrery_core/maintenance.py"
        with mock.patch("validate_change.changed_paths", return_value=([maintenance_path], False)), mock.patch(
            "validate_change.dirty_fingerprint", return_value="1" * 64
        ):
            fast = build_selection(self.manifest, "fast", git_sha(), "fixture", None, None)
            checkpoint = build_selection(
                self.manifest, "checkpoint", git_sha(), "fixture", None, None
            )
        contract = (
            "test_workspace_maintenance.WorkspaceMaintenanceTests."
            "test_versioned_contract_policy_and_synthetic_corpus_are_fail_closed"
        )
        minimal = (
            "test_workspace_maintenance.WorkspaceMaintenanceTests."
            "test_minimal_git_incremental_refresh_and_target_preflight_checkpoint"
        )
        heavy = (
            "test_workspace_maintenance.WorkspaceMaintenanceTests."
            "test_remove_worktree_executor_preserves_branch_commit_and_receipt"
        )
        self.assertEqual(fast["selected_test_ids"], [contract])
        self.assertEqual(checkpoint["selected_test_ids"], sorted([contract, minimal]))
        self.assertNotIn(heavy, checkpoint["selected_test_ids"])
        self.assertLess(checkpoint["selected_test_count"], 24)
        self.assertEqual(checkpoint["reuse"]["decision"], "refused")
        self.assertIn("security-high-risk-surface", checkpoint["reuse"]["reasons"])

    def test_router_mutations_reject_dead_and_heavy_lower_stage_selectors(self) -> None:
        dead = copy.deepcopy(self.manifest)
        dead["routing"]["path_rules"][0]["selectors"]["fast"] = ["test_missing_ci6.*"]
        with self.assertRaisesRegex(CIValidationError, "matched no final unittest ID"):
            validate_and_expand_manifest(dead)
        heavy = copy.deepcopy(self.manifest)
        heavy["routing"]["path_rules"][0]["selectors"]["checkpoint"] = [
            "test_workspace_maintenance.WorkspaceMaintenanceTests."
            "test_remove_worktree_executor_preserves_branch_commit_and_receipt"
        ]
        with self.assertRaisesRegex(CIValidationError, "heavy or disallowed test entered checkpoint"):
            validate_and_expand_manifest(heavy)

    def test_w6_promotion_only_claims_are_complete_once_only_and_absent_below_promotion(self) -> None:
        all_ids, assignments, _ = validate_and_expand_manifest(self.manifest)
        checkpoint = set(expand_profile(self.manifest, "checkpoint", all_ids))
        claim = next(
            item for item in self.manifest["routing"]["claim_sets"]
            if item["id"] == "w6-1-original-24"
        )
        from _common import expand_selectors
        promotion_only = set(
            expand_selectors(claim["promotion_only_selectors"], all_ids, "fixture promotion-only")
        )
        assigned = [test_id for values in assignments.values() for test_id in values]
        self.assertTrue(promotion_only)
        self.assertFalse(promotion_only & checkpoint)
        self.assertTrue(all(assigned.count(test_id) == 1 for test_id in promotion_only))

    def test_lane_contract_rejects_missing_duplicate_unknown_and_heavy_cohabitation(self) -> None:
        missing = copy.deepcopy(self.manifest)
        missing["promotion_lanes"][-1]["shards"].remove("workspace-contract")
        with self.assertRaisesRegex(CIValidationError, "lane assignment is incomplete"):
            validate_and_expand_manifest(missing)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["promotion_lanes"][1]["shards"].append("workspace-contract")
        with self.assertRaisesRegex(CIValidationError, "multiple lanes"):
            validate_and_expand_manifest(duplicate)

        unknown = copy.deepcopy(self.manifest)
        unknown["promotion_lanes"][1]["shards"][0] = "unknown-shard"
        with self.assertRaisesRegex(CIValidationError, "unknown shard"):
            validate_and_expand_manifest(unknown)

        cohabitation = copy.deepcopy(self.manifest)
        cohabitation["promotion_lanes"][0]["shards"].append("context-benchmark")
        cohabitation["promotion_lanes"][1]["shards"].remove("context-benchmark")
        with self.assertRaisesRegex(CIValidationError, "must remain isolated"):
            validate_and_expand_manifest(cohabitation)

    def test_lane_runner_preserves_shard_process_isolation_and_continues_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "lane"
            calls: list[str] = []

            def fake_run(command):
                shard = command[command.index("--shard") + 1]
                output = Path(command[command.index("--output") + 1])
                calls.append(shard)
                successful = len(calls) > 1
                atomic_write_json(
                    output,
                    {
                        "contract_type": "orrery-test-shard-result-v2",
                        "shard": shard,
                        "successful": successful,
                        "completed": True,
                    },
                )
                return 0 if successful else 1

            payload, successful = run_lane(
                manifest_path=DEFAULT_MANIFEST,
                lane="lane-02",
                output_dir=output_dir,
                executor=fake_run,
            )
            self.assertFalse(successful)
            self.assertEqual(calls, ["context-benchmark", "team-lan-harness"])
            self.assertEqual(payload["shards"], calls)
            self.assertFalse(payload["records"][0]["successful"])
            self.assertTrue(payload["records"][1]["successful"])
            self.assertTrue((output_dir / "result-context-benchmark.json").is_file())
            self.assertTrue((output_dir / "result-team-lan-harness.json").is_file())
            receipt = json.loads((output_dir / "lane-result.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["contract_type"], "orrery-test-lane-result-v1")

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
            for rule in manifest["routing"]["path_rules"]:
                rule["selectors"]["fast"] = list(manifest["fast"]["selectors"])
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
            for rule in manifest["routing"]["path_rules"]:
                rule["selectors"]["fast"] = list(manifest["fast"]["selectors"])
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
            self.assertEqual(result["expected_lane_count"], 10)
            self.assertEqual(result["artifact_lane_count"], 10)

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

    def test_aggregate_fails_on_missing_or_drifted_lane_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            payloads, _ = self._result_payloads()
            self._write_payloads(directory, payloads)
            (directory / "lane-02" / "lane-result.json").unlink()
            lane_three = directory / "lane-03" / "lane-result.json"
            drifted = json.loads(lane_three.read_text(encoding="utf-8"))
            drifted["shards"] = list(reversed(drifted["shards"]))
            atomic_write_json(lane_three, drifted)
            result = aggregate(
                manifest_path=DEFAULT_MANIFEST,
                results_dir=directory,
                expected_os="Windows",
                expected_sha=git_sha(),
                matrix_result="success",
                gate_result="success",
            )
            self.assertFalse(result["complete"])
            joined = "\n".join(result["errors"])
            self.assertIn("missing lane artifacts", joined)
            self.assertIn("lane lane-03 shard list differs", joined)

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

    def test_workflows_parallelize_os_lanes_and_cancel_only_superseded_fast(self) -> None:
        fast_text = (ROOT / ".github/workflows/fast-validation.yml").read_text(encoding="utf-8")
        promotion_text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        self.assertIn("cancel-in-progress: true", fast_text)
        self.assertIn("branches-ignore:\n      - \"promotion/**\"", fast_text)
        self.assertEqual(promotion_text.count("max-parallel: 10"), 2)
        self.assertIn("run_test_lane.py --lane", promotion_text)
        self.assertNotIn("run_test_shard.py --shard", promotion_text)
        ubuntu_lanes = promotion_text.split("  ubuntu-lanes:", 1)[1].split(
            "  ubuntu-gates:", 1
        )[0]
        ubuntu_gates = promotion_text.split("  ubuntu-gates:", 1)[1].split(
            "  smoke-test-windows:", 1
        )[0]
        self.assertIn("needs: preflight", ubuntu_lanes)
        self.assertIn("needs: preflight", ubuntu_gates)
        self.assertNotIn("windows-lanes", ubuntu_lanes)
        self.assertNotIn("windows-lanes", ubuntu_gates)

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fast = directory / "fast.yml"
            promotion = directory / "promotion.yml"
            fast.write_text(
                fast_text.replace('    branches-ignore:\n      - "promotion/**"\n', "", 1),
                encoding="utf-8",
            )
            promotion.write_text(
                promotion_text.replace(
                    "  ubuntu-lanes:\n    name:",
                    "  ubuntu-lanes:\n    needs: [preflight, windows-lanes]\n    name:",
                    1,
                ),
                encoding="utf-8",
            )
            errors = validate_workflows(fast, promotion)
            self.assertTrue(any("duplicating frozen promotion" in error for error in errors))
            self.assertTrue(any("must not wait for the Windows" in error for error in errors))

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

    def test_fast_installs_discovery_dependencies_before_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fast = directory / "fast.yml"
            promotion = directory / "promotion.yml"
            text = (ROOT / ".github/workflows/fast-validation.yml").read_text(encoding="utf-8")
            dependency_step = (
                "      - name: Install Fast discovery dependencies\n"
                "        run: python -m pip install \"wheel>=0.41,<1\" -r "
                "skills/project-orrery/assets/project-template/scripts/docsite/requirements.txt\n\n"
            )
            validation_step = (
                "      - name: Validate Fast and Promotion contracts\n"
                "        run: python scripts/ci/validate_ci.py --all\n\n"
            )
            self.assertLess(text.index(dependency_step), text.index(validation_step))
            reordered = text.replace(dependency_step, "", 1).replace(
                validation_step, validation_step + dependency_step, 1
            )
            fast.write_text(reordered, encoding="utf-8")
            shutil.copy2(ROOT / ".github/workflows/validate.yml", promotion)
            errors = validate_workflows(fast, promotion)
            self.assertTrue(
                any("before contract validation" in error for error in errors)
            )

    def test_fast_skips_artifact_upload_when_timing_result_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fast = directory / "fast.yml"
            promotion = directory / "promotion.yml"
            text = (ROOT / ".github/workflows/fast-validation.yml").read_text(encoding="utf-8")
            detection_step = "      - name: Detect non-Promotion timing result"
            upload_step = "      - name: Upload non-Promotion timing result"
            condition = "        if: ${{ always() && steps.fast-result.outputs.available == 'true' }}"
            self.assertLess(text.index(detection_step), text.index(upload_step))
            self.assertIn(condition, text)
            fast.write_text(text.replace(condition, "        if: ${{ always() }}", 1), encoding="utf-8")
            shutil.copy2(ROOT / ".github/workflows/validate.yml", promotion)
            errors = validate_workflows(fast, promotion)
            self.assertTrue(any("fast-result.outputs.available" in error for error in errors))

    def test_promotion_aggregates_install_discovery_dependencies_before_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fast = directory / "fast.yml"
            promotion = directory / "promotion.yml"
            shutil.copy2(ROOT / ".github/workflows/fast-validation.yml", fast)
            text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
            step = (
                "      - name: Install aggregate discovery dependencies\n"
                "        run: python -m pip install \"wheel>=0.41,<1\" -r "
                "skills/project-orrery/assets/project-template/scripts/docsite/requirements.txt\n"
            )
            self.assertEqual(text.count(step), 2)
            promotion.write_text(text.replace(step, "", 1), encoding="utf-8")
            errors = validate_workflows(fast, promotion)
            self.assertTrue(any("Windows aggregate" in error and "dependencies" in error for error in errors))

    def test_exact_sha_binding_rejects_main_sha_alias_and_mismatch(self) -> None:
        head = git_sha()
        self.assertEqual(validate_binding("codex/frozen-candidate", head), [])
        self.assertTrue(validate_binding("main", head))
        self.assertTrue(validate_binding(head, head))
        self.assertTrue(validate_binding("codex/frozen-candidate", "0" * 40))


if __name__ == "__main__":
    unittest.main()
