from __future__ import annotations

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CI_SCRIPTS = ROOT / "scripts" / "ci"
sys.path.insert(0, str(CI_SCRIPTS))

import _common as ci_common  # noqa: E402
from _common import (  # noqa: E402
    CIValidationError,
    DEFAULT_MANIFEST,
    atomic_write_json,
    acceptance_surface_fingerprint,
    consume_validation_lease,
    enforce_acceptance_rollout,
    evaluate_acceptance_policy,
    expand_profile,
    git_sha,
    issue_validation_lease,
    load_json,
    load_mapping_registry,
    machine_inventory,
    promotion_lane_assignments,
    project_team_acceptance_metadata,
    sha256_json,
    finalize_validation_lease,
    timing_prediction,
    validate_acceptance_policy,
    validate_review_package,
    validate_and_expand_manifest,
    validate_mapping_registry,
)
from aggregate_test_results import aggregate  # noqa: E402
from run_test_lane import run_lane  # noqa: E402
from run_test_shard import (  # noqa: E402
    TimedTextResult, _cost_inputs, _over_budget_diagnosis, run_selected,
)
from validate_change import (  # noqa: E402
    SelectionRefused,
    _claim_bounded_triage,
    _cost_diagnostics,
    _record_recurrence,
    _record_run_attempt,
    build_selection,
    main as validate_change_main,
)
from validate_ci import validate_binding, validate_workflows  # noqa: E402


class CIValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(DEFAULT_MANIFEST)
        self.registry = load_mapping_registry(self.manifest)
        self.portfolios = load_json(
            ROOT / "tests" / "fixtures" / "ci-validation" / "change-portfolios-v1.json"
        )
        self.acceptance_portfolios = load_json(
            ROOT / "tests" / "fixtures" / "ci-validation" / "acceptance-policy-v1.json"
        )

    def _write_manifest(self, directory: Path, manifest: dict) -> Path:
        path = directory / "manifest.json"
        atomic_write_json(path, manifest)
        return path

    def _result_payloads(self, expected_os: str = "Windows") -> tuple[dict, dict[str, list[str]]]:
        test_ids, assignments, _ = validate_and_expand_manifest(self.manifest)
        manifest_hash = sha256_json(self.manifest)
        inventory = machine_inventory(self.manifest)
        inventory_hash = inventory["inventory_sha256"]
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
                "mapping_registry_sha256": inventory["mapping_registry_sha256"],
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
                    "mapping_registry_sha256": sample["mapping_registry_sha256"],
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
        self.assertEqual(self.registry["stages"]["fast"]["budget_seconds"], 15)
        self.assertEqual(self.registry["stages"]["checkpoint"]["budget_seconds"], 90)
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
        self.assertTrue(all(set(shard).issubset({"id", "surface", "budget_seconds"}) for shard in workspace))
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
            self.assertTrue(item["dependencies"])
            self.assertTrue(item["reason"])
        self.assertEqual(inventory["mapping_registry_sha256"], sha256_json(self.registry))

    @staticmethod
    def _portfolio_session(portfolio: dict) -> dict:
        subsystems = portfolio["subsystems"]
        return {
            "primary_subsystem_id": subsystems[0] if subsystems else "",
            "affected_subsystem_ids": subsystems[1:],
            "expected_writes": portfolio["expected_writes"],
        }

    def _select_portfolio(self, portfolio: dict) -> dict:
        with mock.patch(
            "validate_change.changed_paths", return_value=(portfolio["changed_paths"], False)
        ), mock.patch("validate_change.dirty_fingerprint", return_value="1" * 64):
            return build_selection(
                self.manifest,
                portfolio["stage"],
                git_sha(),
                "synthetic-portfolio",
                self._portfolio_session(portfolio),
                "synthetic-session.json",
            )

    def _acceptance_policy(self, gates: list[dict], *, rollout: str = "new-workstreams-enforced") -> dict:
        return {
            "schema_version": 1,
            "contract_type": "orrery-acceptance-policy-v1",
            "rollout_mode": rollout,
            "workstream_id": "acceptance-fixture",
            "scope_revision": 2,
            "composition": "all_of",
            "acceptance_gates": gates,
        }

    def _acceptance_gate(
        self, gate_id: str, kind: str, *, required_before: str = "fast",
        status: str = "accepted", receipt_ref: dict | None = None,
    ) -> dict:
        return {
            "id": gate_id,
            "kind": kind,
            "required_before": required_before,
            "authority_role": "product-maintainer" if kind == "human_experience" else "contract-maintainer",
            "contract_ref": self.acceptance_portfolios["contract_ref"],
            "surface_ids": ["observatory-graph"],
            "status": status,
            "evidence_requirements": ["exact-contract", "surface-fingerprint"],
            "receipt_ref": receipt_ref,
        }

    @staticmethod
    def _receipt_reference(path: Path, payload: dict) -> dict:
        atomic_write_json(path, payload)
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_generic_router_selects_docs_authority_and_collaboration_portfolios(self) -> None:
        generic = [
            portfolio for portfolio in self.portfolios["portfolios"]
            if portfolio["id"] != "w6-1-regression"
        ]
        self.assertEqual([item["id"] for item in generic], [
            "docs-only", "authority-a4-class", "collaboration-maintenance",
            "w7-2-graph-only", "u2-2-maintenance", "unified-common-security",
        ])
        for portfolio in generic:
            with self.subTest(portfolio=portfolio["id"]):
                plan = self._select_portfolio(portfolio)
                self.assertEqual(plan["mapping_ids"], portfolio["expected_mapping_ids"])
                self.assertLessEqual(plan["selected_test_count"], portfolio["max_selected"])
                self.assertTrue(set(portfolio["required_test_ids"]).issubset(plan["selected_test_ids"]))
                self.assertFalse(set(portfolio["forbidden_test_ids"]) & set(plan["selected_test_ids"]))

    def test_regression_portfolio_is_data_only_and_heavy_claims_are_promotion_owned_once(self) -> None:
        portfolio = next(
            item for item in self.portfolios["portfolios"] if item["id"] == "w6-1-regression"
        )
        plan = self._select_portfolio(portfolio)
        entries = {item["test_id"]: item for item in self.registry["tests"]}
        assignments = validate_and_expand_manifest(self.manifest)[1]
        assigned = [test_id for values in assignments.values() for test_id in values]
        regression_ids = portfolio["regression_test_ids"]
        promotion_only = [
            test_id for test_id in regression_ids
            if entries[test_id]["allowed_stages"] == ["promotion"]
        ]
        self.assertEqual(len(regression_ids), 24)
        self.assertGreaterEqual(len(promotion_only), 20)
        self.assertLess(plan["selected_test_count"], 24)
        self.assertFalse(set(promotion_only) & set(plan["selected_test_ids"]))
        self.assertTrue(all(assigned.count(test_id) == 1 for test_id in promotion_only))

    def test_production_router_and_registry_have_no_task_or_branch_specific_switch(self) -> None:
        forbidden = ("w6" + "-1", "codex/" + "w6", "incremental-maintenance-quick-remove")
        production = list(CI_SCRIPTS.glob("*.py")) + [
            CI_SCRIPTS / "test-shards.json",
            CI_SCRIPTS / "change-mapping.json",
            CI_SCRIPTS / "acceptance-profiles-v1.json",
            CI_SCRIPTS / "README.md",
        ]
        for path in production:
            text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path.name):
                self.assertFalse(any(token in text for token in forbidden))

    def test_registry_mutations_fail_closed_for_unregistered_duplicate_unknown_and_heavy(self) -> None:
        self.assertEqual(
            [item["id"] for item in self.portfolios["mutations"]],
            [
                "unregistered-test", "unmapped-path", "unknown-dependency",
                "overlapping-mapping", "broad-expected-write", "forged-usage", "roi-as-gate",
            ],
        )
        shard_surfaces = {item["id"]: item["surface"] for item in self.manifest["shards"]}
        unregistered = copy.deepcopy(self.registry)
        unregistered["tests"].pop()
        with mock.patch.object(ci_common, "load_mapping_registry", return_value=unregistered), self.assertRaisesRegex(
            CIValidationError, "unregistered.*owner_surface.*dependencies"
        ):
            validate_and_expand_manifest(self.manifest)

        duplicate = copy.deepcopy(self.registry)
        duplicate["tests"].append(copy.deepcopy(duplicate["tests"][0]))
        with self.assertRaisesRegex(CIValidationError, "duplicate registered test ID"):
            validate_mapping_registry(duplicate, shard_surfaces)

        unknown = copy.deepcopy(self.registry)
        unknown["tests"][0]["dependencies"] = ["missing-generic-mapping"]
        with self.assertRaisesRegex(CIValidationError, "Unknown dependencies.*path_mappings metadata"):
            validate_mapping_registry(unknown, shard_surfaces)

        heavy = copy.deepcopy(self.registry)
        heavy_entry = next(item for item in heavy["tests"] if item["cost_class"] == "heavy")
        heavy_entry["allowed_stages"] = ["checkpoint", "promotion"]
        with self.assertRaisesRegex(CIValidationError, "heavy registered test.*lower stage"):
            validate_mapping_registry(heavy, shard_surfaces)

    def test_actual_paths_are_primary_broad_scope_refuses_and_overlap_fails_closed(self) -> None:
        graph = next(item for item in self.portfolios["portfolios"] if item["id"] == "w7-2-graph-only")
        session = self._portfolio_session(graph)
        session["expected_writes"] = [
            "packages/project-orrery-core/src/project_orrery_core/maintenance.py"
        ]
        with mock.patch(
            "validate_change.changed_paths", return_value=(graph["changed_paths"], False)
        ), mock.patch("validate_change.dirty_fingerprint", return_value="2" * 64):
            plan = build_selection(
                self.manifest, "checkpoint", git_sha(), "actual-primary", session, "fixture.json"
            )
        self.assertEqual(plan["selection_mode"], "actual-changed-paths")
        self.assertEqual(plan["mapping_ids"], ["observatory-graph"])
        self.assertNotIn(
            "test_workspace_maintenance.WorkspaceMaintenanceTests."
            "test_minimal_git_incremental_refresh_and_target_preflight_checkpoint",
            plan["selected_test_ids"],
        )

        broad = self._portfolio_session(graph)
        broad["expected_writes"] = ["packages/project-orrery-observatory/**"]
        with mock.patch("validate_change.changed_paths", return_value=(graph["changed_paths"], False)):
            with self.assertRaisesRegex(SelectionRefused, "directory-wide") as raised:
                build_selection(
                    self.manifest, "checkpoint", git_sha(), "broad-refusal", broad, "fixture.json"
                )
        self.assertIn("exact repository file", "\n".join(raised.exception.required_metadata))

        overlap = copy.deepcopy(self.registry)
        overlap["path_mappings"].append({
            "id": "overlap-fixture",
            "patterns": [graph["changed_paths"][0]],
            "subsystems": ["test-coverage"],
            "surfaces": ["mutation-only"],
            "high_risk": False,
        })
        with mock.patch.object(ci_common, "load_mapping_registry", return_value=overlap), mock.patch(
            "validate_change.load_mapping_registry", return_value=overlap
        ), mock.patch("validate_change.changed_paths", return_value=(graph["changed_paths"], False)):
            with self.assertRaisesRegex(SelectionRefused, "overlapping"):
                build_selection(
                    self.manifest, "checkpoint", git_sha(), "overlap-refusal",
                    self._portfolio_session(graph), "fixture.json",
                )

    def test_cost_diagnostics_are_advisory_unknown_usage_and_roi_fields_cannot_gate(self) -> None:
        portfolio = next(
            item for item in self.portfolios["portfolios"] if item["id"] == "unified-common-security"
        )
        plan = self._select_portfolio(portfolio)
        plan["cost_diagnostic_inputs"].update({
            "router_setup_wall_seconds": 0.25,
            "rerun_count": 1,
            "change_volume": {
                "test_changed_files": 1, "test_changed_lines": 8,
                "ci_changed_files": 1, "ci_changed_lines": 20,
            },
            "independent_optimization_workstream": True,
            "expected_future_runs": 10,
            "baseline_test_runtime_seconds": 12.0,
            "optimization_investment_seconds": 20.0,
        })
        diagnostic = _cost_diagnostics(plan, test_runtime=8.0, slow_ids=["fixture.slow"])
        self.assertEqual(diagnostic["host_usage"]["status"], "Unknown")
        self.assertEqual(diagnostic["host_usage"]["agent_token_usage"], "Unknown")
        self.assertEqual(diagnostic["gate_effect"], "none")
        self.assertEqual(diagnostic["total_setup_build_wall_seconds"], 0.25)
        self.assertEqual(diagnostic["break_even"]["break_even_runs"], 5)
        self.assertEqual(diagnostic["break_even"]["projected_net_savings_seconds"], 20.0)

        forged = copy.deepcopy(plan)
        forged["cost_diagnostic_inputs"]["host_usage"] = {"agent_token_usage": 1234}
        with self.assertRaisesRegex(CIValidationError, "usage/token claims"):
            _cost_inputs(forged)
        forged_root = copy.deepcopy(plan)
        forged_root["cost_diagnostics"] = {"host_usage": {"agent_token_usage": 1234}}
        with self.assertRaisesRegex(CIValidationError, "forged usage/token claims"):
            _cost_inputs(forged_root)
        roi_gate = copy.deepcopy(plan)
        roi_gate["cost_diagnostic_inputs"]["gate_effect"] = "pass"
        with self.assertRaisesRegex(CIValidationError, "ROI gate"):
            _cost_inputs(roi_gate)

        passing = mock.Mock(failures=[], errors=[])
        product_failure = mock.Mock(failures=[("fixture", "failure")], errors=[])
        self.assertEqual(_over_budget_diagnosis(
            budget_exceeded=True, result=product_failure, records=[], budget_seconds=90,
            selection_plan=plan,
        )["classification"], "product-test-failure")
        fallback = copy.deepcopy(plan)
        fallback["selection_mode"] = "conservative-subsystem-fallback"
        self.assertEqual(_over_budget_diagnosis(
            budget_exceeded=True, result=passing, records=[{"duration_seconds": 10}],
            budget_seconds=90, selection_plan=fallback,
        )["classification"], "router-over-selection")
        self.assertEqual(_over_budget_diagnosis(
            budget_exceeded=True, result=passing, records=[{"duration_seconds": 10}],
            budget_seconds=90, selection_plan=plan,
        )["classification"], "fixture-runtime-variance")
        self.assertEqual(_over_budget_diagnosis(
            budget_exceeded=True, result=passing, records=[{"duration_seconds": 50}],
            budget_seconds=90, selection_plan=plan,
        )["classification"], "genuinely-slow-path")

        receipt = {
            "budget_exceeded": True,
            "slowest_tests": [{"test_id": "fixture.slow"}],
            "over_budget_diagnosis": {"classification": "genuinely-slow-path"},
        }
        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "validate_change.git_output", return_value=temporary
        ):
            first = copy.deepcopy(plan)
            first["workstream"] = {"workstream_id": "independent-one"}
            second = copy.deepcopy(plan)
            second["workstream"] = {"workstream_id": "independent-two"}
            self.assertEqual(
                _record_recurrence(first, receipt), "first-independent-workstream-observation"
            )
            recurrence = _record_recurrence(second, receipt)
        self.assertEqual(recurrence["finding_type"], "advisory-routing-cost-recurrence")
        self.assertFalse(recurrence["automatic_task_created"])
        self.assertFalse(recurrence["creates_adr_state_or_relation_fact"])

        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "validate_change.git_output", return_value=temporary
        ):
            one_attempt = copy.deepcopy(plan)
            one_attempt["workstream"] = {"workstream_id": "feature-task"}
            _claim_bounded_triage(one_attempt)
            with self.assertRaisesRegex(SelectionRefused, "already used its one bounded triage"):
                _claim_bounded_triage(one_attempt)

        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "validate_change.git_output", return_value=temporary
        ):
            self.assertEqual(_record_run_attempt(plan), 0)
            self.assertEqual(_record_run_attempt(plan), 1)

        self._assert_acceptance_policy_all_of_authority_freshness_and_team_projection()
        self._assert_validation_lease_is_one_run_idempotent_and_failure_requires_human_override()
        self._assert_predictive_p95_and_iterating_caps_refuse_before_execution()
        self._assert_formal_selection_plan_without_lease_refuses_before_test_loading()

    def _assert_acceptance_policy_all_of_authority_freshness_and_team_projection(self) -> None:
        session = {"workstream_id": "acceptance-fixture", "scope_revision": 2}
        legacy = evaluate_acceptance_policy(
            None, requested_stage="fast", session=session, surface_fingerprint="0" * 64
        )
        self.assertEqual(legacy["classification"], "legacy-unclassified")
        self.assertEqual(legacy["decision"], "shadow-allow")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            human_path = directory / "human.json"
            gate = self._acceptance_gate(
                "experience", "human_experience",
                receipt_ref={"path": str(human_path), "sha256": "0" * 64},
            )
            policy = self._acceptance_policy([gate])
            fingerprint = acceptance_surface_fingerprint(
                policy=policy,
                mapping_registry_sha256=sha256_json(self.registry),
                relevant_paths=["scripts/ci/validate_change.py"],
            )
            human_receipt = {
                "schema_version": 1,
                "contract_type": "orrery-acceptance-gate-receipt-v1",
                "workstream_id": "acceptance-fixture",
                "scope_revision": 2,
                "expected_scope_revision": 2,
                "gate_id": "experience",
                "contract_ref": self.acceptance_portfolios["contract_ref"],
                "authority_role": "product-maintainer",
                "actor_type": "human",
                "actor_id": "maintainer-fixture",
                "revision": 1,
                "decision": "accepted",
                "surface_fingerprint": fingerprint,
            }
            policy["acceptance_gates"][0]["receipt_ref"] = self._receipt_reference(
                human_path, human_receipt
            )
            accepted = evaluate_acceptance_policy(
                policy, requested_stage="fast", session=session,
                surface_fingerprint=fingerprint,
            )
            self.assertEqual(accepted["decision"], "allow")
            self.assertEqual(evaluate_acceptance_policy(
                policy, requested_stage="checkpoint", session=session,
                surface_fingerprint=fingerprint,
            )["decision"], "allow")
            agent_receipt = {**human_receipt, "actor_type": "agent", "actor_id": "agent-fixture"}
            policy["acceptance_gates"][0]["receipt_ref"] = self._receipt_reference(
                directory / "agent.json", agent_receipt
            )
            self.assertEqual(evaluate_acceptance_policy(
                policy, requested_stage="fast", session=session,
                surface_fingerprint=fingerprint,
            )["decision"], "refuse")

            contract_path = directory / "contract.json"
            contract_gate = self._acceptance_gate(
                "contract-proof", "contract",
                receipt_ref={"path": str(contract_path), "sha256": "0" * 64},
            )
            mixed = self._acceptance_policy([copy.deepcopy(gate), contract_gate])
            mixed_fingerprint = acceptance_surface_fingerprint(
                policy=mixed,
                mapping_registry_sha256=sha256_json(self.registry),
                relevant_paths=["scripts/ci/validate_change.py"],
            )
            mixed_human_receipt = {**human_receipt, "surface_fingerprint": mixed_fingerprint}
            mixed["acceptance_gates"][0]["receipt_ref"] = self._receipt_reference(
                human_path, mixed_human_receipt
            )
            mechanical = {
                **mixed_human_receipt,
                "gate_id": "contract-proof",
                "authority_role": "contract-maintainer",
                "actor_type": "mechanical",
                "actor_id": "ci-contract-evaluator",
                "contract_result": "pass",
                "contract_approval": {
                    "actor_type": "human", "decision": "accepted",
                    "contract_ref": self.acceptance_portfolios["contract_ref"],
                },
            }
            mixed["acceptance_gates"][1]["receipt_ref"] = self._receipt_reference(
                contract_path, mechanical
            )
            self.assertEqual(evaluate_acceptance_policy(
                mixed, requested_stage="fast", session=session,
                surface_fingerprint=mixed_fingerprint,
            )["decision"], "allow")
            revoked = copy.deepcopy(mixed)
            revoked["acceptance_gates"][0]["authority_role"] = "revoked-role"
            self.assertEqual(evaluate_acceptance_policy(
                revoked, requested_stage="fast", session=session,
                surface_fingerprint=mixed_fingerprint,
            )["decision"], "refuse")
            projection = project_team_acceptance_metadata(mixed)
            projection_text = json.dumps(projection)
            self.assertEqual(projection["execution_capability"], "request-only")
            self.assertEqual(projection["network_default"], "personal-zero-network")
            self.assertNotIn(str(human_path), projection_text)
            self.assertNotIn("contract_approval", projection_text)

            for kind, actor_type, evidence in (
                ("measurement", "mechanical", {"threshold_result": "pass"}),
                ("operation_authorization", "human", {"action_time_authorized": True}),
                (
                    "platform_matrix", "mechanical",
                    {"platform_results": {"windows-latest": "pass", "ubuntu-latest": "pass"}},
                ),
            ):
                gate_path = directory / f"{kind}.json"
                kind_gate = self._acceptance_gate(
                    f"{kind.replace('_', '-')}-gate", kind,
                    receipt_ref={"path": str(gate_path), "sha256": "0" * 64},
                )
                kind_policy = self._acceptance_policy([kind_gate])
                kind_fingerprint = acceptance_surface_fingerprint(
                    policy=kind_policy,
                    mapping_registry_sha256=sha256_json(self.registry),
                    relevant_paths=["scripts/ci/validate_change.py"],
                )
                kind_receipt = {
                    **human_receipt,
                    "gate_id": kind_gate["id"],
                    "authority_role": kind_gate["authority_role"],
                    "actor_type": actor_type,
                    "actor_id": f"{kind}-evaluator",
                    "surface_fingerprint": kind_fingerprint,
                    **evidence,
                }
                if actor_type == "mechanical":
                    kind_receipt["contract_approval"] = {
                        "actor_type": "human", "decision": "accepted",
                        "contract_ref": self.acceptance_portfolios["contract_ref"],
                    }
                kind_policy["acceptance_gates"][0]["receipt_ref"] = self._receipt_reference(
                    gate_path, kind_receipt
                )
                self.assertEqual(evaluate_acceptance_policy(
                    kind_policy, requested_stage="fast", session=session,
                    surface_fingerprint=kind_fingerprint,
                )["decision"], "allow", kind)

        unknown = self._acceptance_policy([
            self._acceptance_gate("unknown-kind", "future-kind", status="future-status")
        ])
        result = evaluate_acceptance_policy(
            unknown, requested_stage="fast", session=session, surface_fingerprint="1" * 64
        )
        self.assertEqual(result["decision"], "refuse")
        self.assertEqual(result["gate_results"][0]["reason"], "unknown-kind-or-status")
        stale_scope = copy.deepcopy(unknown)
        stale_scope["scope_revision"] = 1
        with self.assertRaisesRegex(CIValidationError, "scope revision is stale"):
            validate_acceptance_policy(stale_scope, session=session)
        forged_blob = copy.deepcopy(unknown)
        forged_blob["acceptance_gates"][0]["contract_ref"]["blob_oid"] = "0" * 40
        with self.assertRaisesRegex(CIValidationError, "missing or forged"):
            validate_acceptance_policy(forged_blob)
        explicit_legacy = copy.deepcopy(unknown)
        explicit_legacy["rollout_mode"] = "explicit-legacy-adoption"
        with self.assertRaisesRegex(CIValidationError, "human-reviewed"):
            validate_acceptance_policy(explicit_legacy)
        enforcement = {
            "schema_version": 1,
            "contract_type": "orrery-acceptance-enforcement-v1",
            "mode": "new-workstreams-enforced",
            "activated_at": "2026-08-30T00:00:00Z",
            "human_decision": "accepted",
        }
        with self.assertRaisesRegex(CIValidationError, "must declare acceptance gates"):
            enforce_acceptance_rollout(
                None,
                session={**session, "captured_at": "2026-08-30T01:00:00Z"},
                enforcement=enforcement,
            )
        self.assertEqual(enforce_acceptance_rollout(
            None,
            session={**session, "captured_at": "2026-08-29T23:00:00Z"},
            enforcement=enforcement,
        ), "legacy-shadow")

        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "_common.validate_acceptance_policy", return_value=unknown
        ):
            root = Path(temporary)
            (root / "surface.txt").write_text("one", encoding="utf-8")
            first = acceptance_surface_fingerprint(
                policy=unknown, mapping_registry_sha256="a" * 64,
                relevant_paths=["surface.txt"], root=root,
            )
            (root / "unrelated.md").write_text("ignored", encoding="utf-8")
            stable = acceptance_surface_fingerprint(
                policy=unknown, mapping_registry_sha256="a" * 64,
                relevant_paths=["surface.txt"], root=root,
            )
            (root / "surface.txt").write_text("two", encoding="utf-8")
            changed = acceptance_surface_fingerprint(
                policy=unknown, mapping_registry_sha256="a" * 64,
                relevant_paths=["surface.txt"], root=root,
            )
        self.assertEqual(first, stable)
        self.assertNotEqual(first, changed)
        validate_review_package({
            "schema_version": 1,
            "contract_type": "orrery-acceptance-review-package-v1",
            "purpose": "review one bounded user-visible behavior",
            "invariants": ["no authority drift"],
            "representative_cases": ["before", "after", "boundary"],
            "negative_cases": ["rejected input"],
            "known_gaps": [],
            "contract_ref": self.acceptance_portfolios["contract_ref"],
            "surface_fingerprint": "2" * 64,
            "reproduction_ref": "local:review-package",
        })

    def _assert_validation_lease_is_one_run_idempotent_and_failure_requires_human_override(self) -> None:
        acceptance = {"decision": "allow"}
        prediction = {
            "decision": "allow", "reasons": [], "predicted_total_p95_seconds": 1.0,
        }
        plan = {
            "stage": "fast", "budget_seconds": 15.0,
            "selected_test_ids": ["fixture.test"],
            "workstream": {"workstream_id": "acceptance-fixture"},
            "surface_fingerprint": "3" * 64,
        }
        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "_common.git_private_ci_path",
            side_effect=lambda name, root=ROOT: Path(temporary) / name,
        ):
            issued = issue_validation_lease(
                plan, acceptance=acceptance, prediction=prediction, scope_revision=2,
                surface_fingerprint=plan["surface_fingerprint"], receipt_inputs=["human.json"],
            )
            plan["validation_lease"] = issued["lease"]
            consumed = consume_validation_lease(plan)
            self.assertEqual(consumed["run_identity"], issued["lease"]["run_identity"])
            passed_receipt = {
                "contract_type": "orrery-test-shard-result-v2", "outcome": "passed",
                "successful": True, "evidence_eligible": True, "duration_seconds": 0.5,
            }
            finalize_validation_lease(consumed, passed_receipt)
            reused = issue_validation_lease(
                plan, acceptance=acceptance, prediction=prediction, scope_revision=2,
                surface_fingerprint=plan["surface_fingerprint"], receipt_inputs=["human.json"],
            )
            self.assertEqual(reused["decision"], "reuse-prior-receipt")
            checkpoint_plan = {
                **plan, "stage": "checkpoint", "budget_seconds": 90.0,
            }
            checkpoint_plan.pop("validation_lease", None)
            checkpoint = issue_validation_lease(
                checkpoint_plan, acceptance=acceptance, prediction=prediction,
                scope_revision=2, surface_fingerprint=checkpoint_plan["surface_fingerprint"],
                receipt_inputs=["human.json"],
            )
            checkpoint_plan["validation_lease"] = checkpoint["lease"]
            checkpoint_lease = consume_validation_lease(checkpoint_plan)
            finalize_validation_lease(checkpoint_lease, passed_receipt)
            self.assertEqual(issue_validation_lease(
                checkpoint_plan, acceptance=acceptance, prediction=prediction,
                scope_revision=2, surface_fingerprint=checkpoint_plan["surface_fingerprint"],
                receipt_inputs=["human.json"],
            )["decision"], "reuse-prior-receipt")

            failed_plan = {**plan, "surface_fingerprint": "4" * 64}
            failed_plan.pop("validation_lease")
            failed = issue_validation_lease(
                failed_plan, acceptance=acceptance, prediction=prediction, scope_revision=2,
                surface_fingerprint=failed_plan["surface_fingerprint"], receipt_inputs=[],
            )
            failed_plan["validation_lease"] = failed["lease"]
            failed_lease = consume_validation_lease(failed_plan)
            finalize_validation_lease(failed_lease, {
                "contract_type": "orrery-test-shard-result-v2", "outcome": "failed",
                "successful": False, "evidence_eligible": False, "duration_seconds": 0.25,
            })
            with self.assertRaisesRegex(CIValidationError, "human override"):
                issue_validation_lease(
                    failed_plan, acceptance=acceptance, prediction=prediction, scope_revision=2,
                    surface_fingerprint=failed_plan["surface_fingerprint"], receipt_inputs=[],
                )
            override = {
                "schema_version": 1,
                "contract_type": "orrery-validation-rerun-override-v1",
                "actor_type": "human",
                "actor_id": "maintainer-fixture",
                "authority_role": "maintainer",
                "decision": "authorized",
                "request_key": failed["request_key"],
                "expected_lease_status": "validation-cost-blocked",
                "revision": 1,
                "previous_receipt_sha256": "5" * 64,
            }
            authorized = issue_validation_lease(
                failed_plan, acceptance=acceptance, prediction=prediction, scope_revision=2,
                surface_fingerprint=failed_plan["surface_fingerprint"], receipt_inputs=[],
                human_override=override,
            )
            self.assertTrue(authorized["lease"]["override_authorized"])
            forged_plan = copy.deepcopy(failed_plan)
            forged_plan["validation_lease"] = copy.deepcopy(authorized["lease"])
            forged_plan["validation_lease"]["allowed_test_ids"] = ["forged.test"]
            with self.assertRaisesRegex(CIValidationError, "forged"):
                consume_validation_lease(forged_plan)
            stage_mismatch = copy.deepcopy(failed_plan)
            stage_mismatch["validation_lease"] = copy.deepcopy(authorized["lease"])
            stage_mismatch["stage"] = "checkpoint"
            with self.assertRaisesRegex(CIValidationError, "stage or allowed test IDs mismatch"):
                consume_validation_lease(stage_mismatch)
            with self.assertRaisesRegex(CIValidationError, "missing a validation lease"):
                consume_validation_lease({key: value for key, value in plan.items() if key != "validation_lease"})

            expired_plan = {**plan, "surface_fingerprint": "7" * 64}
            expired_plan.pop("validation_lease", None)
            with mock.patch("_common.time.time", return_value=100.0):
                expired = issue_validation_lease(
                    expired_plan, acceptance=acceptance, prediction=prediction, scope_revision=2,
                    surface_fingerprint=expired_plan["surface_fingerprint"], receipt_inputs=[],
                )
            expired_plan["validation_lease"] = expired["lease"]
            with mock.patch("_common.time.time", return_value=1001.0), self.assertRaisesRegex(
                CIValidationError, "expired"
            ):
                consume_validation_lease(expired_plan)
            with self.assertRaisesRegex(CIValidationError, "predictive budget refusal"):
                issue_validation_lease(
                    {**plan, "surface_fingerprint": "8" * 64}, acceptance=acceptance,
                    prediction={"decision": "refuse", "reasons": ["fixture-p95-over-budget"]},
                    scope_revision=2, surface_fingerprint="8" * 64, receipt_inputs=[],
                )

    def _assert_predictive_p95_and_iterating_caps_refuse_before_execution(self) -> None:
        environment = "FixtureOS:3.11"
        history = {"tests": {
            f"{environment}:fast.one": {"p95_seconds": 4.0},
            f"{environment}:fast.two": {"p95_seconds": 5.0},
            f"{environment}:slow.maintenance": {"p95_seconds": 95.0},
        }}
        allowed = timing_prediction(
            ["fast.one", "fast.two"], stage="fast", environment_key=environment,
            router_setup_p95_seconds=1.0, history=history,
        )
        self.assertEqual(allowed["decision"], "allow")
        count_refusal = timing_prediction(
            [f"known.{index}" for index in range(21)], stage="fast",
            environment_key=environment, history={"tests": {
                f"{environment}:known.{index}": {"p95_seconds": 0.1} for index in range(21)
            }},
        )
        self.assertIn("fast-selected-count-exceeds-20", count_refusal["reasons"])
        unknown = timing_prediction(
            ["unknown.test"], stage="fast", environment_key=environment, history=history
        )
        self.assertIn("timing-history-unknown-conservative-refusal", unknown["reasons"])
        maintenance = timing_prediction(
            ["slow.maintenance"], stage="checkpoint", environment_key=environment, history=history
        )
        self.assertIn("checkpoint-single-test-p95-exceeds-30-seconds", maintenance["reasons"])
        self.assertIn("checkpoint-total-p95-exceeds-60-seconds", maintenance["reasons"])

        plan = {
            "stage": "fast", "budget_seconds": 15.0,
            "selected_test_ids": ["fast.one"],
            "workstream": {"workstream_id": "iterating-fixture"},
            "surface_fingerprint": "6" * 64,
        }
        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "_common.git_private_ci_path",
            side_effect=lambda name, root=ROOT: Path(temporary) / name,
        ):
            too_slow = {"decision": "allow", "reasons": [], "predicted_total_p95_seconds": 21.0}
            with self.assertRaisesRegex(CIValidationError, "focused validation only"):
                issue_validation_lease(
                    plan, acceptance={"decision": "allow"}, prediction=allowed,
                    scope_revision=2, surface_fingerprint=plan["surface_fingerprint"],
                    receipt_inputs=[], task_phase="iterating",
                )
            focused_plan = {**plan, "stage": "focused", "budget_seconds": 20.0}
            with self.assertRaisesRegex(CIValidationError, "20 tests or 20 seconds"):
                issue_validation_lease(
                    focused_plan, acceptance={"decision": "allow"}, prediction=too_slow,
                    scope_revision=2, surface_fingerprint=focused_plan["surface_fingerprint"],
                    receipt_inputs=[], task_phase="iterating",
                )

    def _assert_formal_selection_plan_without_lease_refuses_before_test_loading(self) -> None:
        portfolio = next(
            item for item in self.portfolios["portfolios"] if item["id"] == "w7-2-graph-only"
        )
        plan = self._select_portfolio(portfolio)
        plan["dirty_fingerprint"] = ci_common.dirty_fingerprint()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            plan_path = directory / "plan.json"
            atomic_write_json(plan_path, plan)
            with mock.patch("run_test_shard._load_selected_tests") as loader, self.assertRaisesRegex(
                CIValidationError, "missing a validation lease"
            ):
                run_selected(
                    manifest_path=DEFAULT_MANIFEST, shard=None, profile=None,
                    output=directory / "receipt.json", selection_plan_path=plan_path,
                )
            loader.assert_not_called()

    def test_unmapped_path_refuses_formal_receipt_and_explains_registry_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "refusal.json"
            argv = [
                "validate_change.py", "--stage", "fast", "--base", git_sha(),
                "--output", str(output), "--dry-run",
            ]
            with mock.patch("validate_change.changed_paths", return_value=(["unknown/new.xyz"], False)), mock.patch(
                "sys.argv", argv
            ):
                return_code = validate_change_main()
            receipt = load_json(output)
        self.assertNotEqual(return_code, 0)
        self.assertEqual(receipt["contract_type"], "orrery-local-validation-refusal-v1")
        self.assertFalse(receipt["evidence_eligible"])
        self.assertIn("unmapped", "\n".join(receipt["runner_errors"]))
        self.assertIn("path_mappings", "\n".join(receipt["required_metadata"]))

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

    def test_inventory_rejects_stale_registry_and_unknown_owner_shard(self) -> None:
        stale = copy.deepcopy(self.registry)
        stale["tests"].append({
            **copy.deepcopy(stale["tests"][0]),
            "test_id": "test_missing_module.MissingTests.test_dead_selector_equivalent",
        })
        with mock.patch.object(ci_common, "load_mapping_registry", return_value=stale), self.assertRaisesRegex(
            CIValidationError, "exact test registry differs.*stale="
        ):
            validate_and_expand_manifest(self.manifest)

        unknown_owner = copy.deepcopy(self.registry)
        unknown_owner["tests"][0]["owner_shard"] = "missing-owner-shard"
        shard_surfaces = {item["id"]: item["surface"] for item in self.manifest["shards"]}
        with self.assertRaisesRegex(CIValidationError, "owner shard/surface mismatch|unknown owner_shard"):
            validate_mapping_registry(unknown_owner, shard_surfaces)

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
            test_id = (
                "test_authority_release_candidate_gate.AuthorityReleaseCandidateGateTests."
                "test_historical_v020_inputs_match_frozen_hashes"
            )
            registry = copy.deepcopy(self.registry)
            for entry in registry["tests"]:
                entry["allowed_stages"] = ["fast", "checkpoint", "promotion"] if entry["test_id"] == test_id else ["promotion"]
            output = directory / "result.json"
            with mock.patch.dict(os.environ, {"RUNNER_OS": "FixtureOS"}, clear=False), mock.patch.object(
                ci_common, "load_mapping_registry", return_value=registry
            ), mock.patch("run_test_shard.load_mapping_registry", return_value=registry):
                payload, successful = run_selected(
                    manifest_path=DEFAULT_MANIFEST, shard=None, profile="fast", output=output
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
            self.assertEqual(payload["mapping_registry_sha256"], sha256_json(registry))
            self.assertFalse(payload["budget_exceeded"])
            self.assertGreaterEqual(
                payload["cost_diagnostics"]["total_setup_build_wall_seconds"],
                payload["cost_diagnostics"]["router_setup_wall_seconds"],
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["shard"], "fast")

    def test_runner_enforces_profile_budget_without_changing_promotion_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            test_id = (
                "test_authority_release_candidate_gate.AuthorityReleaseCandidateGateTests."
                "test_historical_v020_inputs_match_frozen_hashes"
            )
            registry = copy.deepcopy(self.registry)
            registry["stages"]["fast"]["budget_seconds"] = 0.000001
            for entry in registry["tests"]:
                entry["allowed_stages"] = ["fast", "checkpoint", "promotion"] if entry["test_id"] == test_id else ["promotion"]
            with mock.patch.object(ci_common, "load_mapping_registry", return_value=registry), mock.patch(
                "run_test_shard.load_mapping_registry", return_value=registry
            ):
                payload, successful = run_selected(
                    manifest_path=DEFAULT_MANIFEST,
                    shard=None,
                    profile="fast",
                    output=directory / "result.json",
                )
            self.assertFalse(successful)
            self.assertTrue(payload["budget_exceeded"])
            self.assertEqual(payload["role"], "local-fast-evidence")

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
            payloads[duplicate_target]["replayed_child_gate"] = True
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
            self.assertIn("replayed a child-owned acceptance gate", joined)
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
