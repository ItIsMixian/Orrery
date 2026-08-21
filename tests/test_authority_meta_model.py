from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "authority-meta-model"
CONFORMANCE_V1 = FIXTURE_ROOT / "v1" / "conformance.json"

sys.path.insert(0, str(CORE_SOURCE))

from project_orrery_core.authority import (  # noqa: E402
    AUTHORITY_MODEL_VERSION,
    AuthorityEvaluationError,
    evaluate_authority,
)


class AuthorityMetaModelFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(CONFORMANCE_V1.read_text(encoding="utf-8"))
        cls.cases = {case["id"]: case for case in cls.fixture["cases"]}

    def test_fixture_contract_has_four_explicit_inputs_and_separate_versions(self) -> None:
        self.assertEqual(self.fixture["fixture_format"], 1)
        self.assertEqual(self.fixture["fixture_status"], "candidate")
        self.assertEqual(self.fixture["authority_model_version"], "amm-fixture-v1")
        self.assertEqual(
            self.fixture["contract"]["required_input_dimensions"],
            ["authority_model_version", "repository_snapshot", "fact_scope", "evidence_visibility"],
        )
        self.assertNotIn("document_schema", self.fixture)
        self.assertNotIn("project_manifest_format", self.fixture)
        self.assertNotIn("component_version", self.fixture)

    def test_every_case_is_versioned_scoped_and_evidence_bounded(self) -> None:
        required = set(self.fixture["contract"]["required_input_dimensions"])
        allowed_scopes = set(self.fixture["contract"]["fact_scopes"])
        allowed_evidence = set(self.fixture["contract"]["evidence_categories"])
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                self.assertEqual(set(case["input"]), required)
                self.assertEqual(case["input"]["authority_model_version"], self.fixture["authority_model_version"])
                self.assertIn(case["input"]["fact_scope"], allowed_scopes)
                self.assertTrue(set(case["input"]["evidence_visibility"]).issubset(allowed_evidence))
                self.assertTrue(case["input"]["repository_snapshot"])
                self.assertIsInstance(case["observations"], list)
                self.assertIn("claims", case["expected"])
                self.assertIn("must_not_infer", case["expected"])

    def test_required_semantic_scenarios_are_frozen(self) -> None:
        required_cases = {
            "accepted-not-implemented-not-validated",
            "implementation-present-validation-failed",
            "historical-implementation-removed-current",
            "supersede-effective-decision",
            "amend-preserves-base-effect",
            "draft-not-approved",
            "plan-not-current-state",
            "snapshot-not-live-state",
            "evidence-capability-boundaries",
            "derived-ai-non-escalation",
            "scope-not-coordinator-runtime",
            "deterministic-input-a",
            "deterministic-input-b",
            "visibility-with-validation",
            "visibility-without-validation",
        }
        self.assertTrue(required_cases.issubset(self.cases))

    def test_claim_dimensions_remain_independent(self) -> None:
        accepted = self.cases["accepted-not-implemented-not-validated"]["expected"]["claims"]
        self.assertEqual(accepted["decision_status"], "accepted")
        self.assertEqual(accepted["implementation_claim"], "unknown")
        self.assertEqual(accepted["validation_evidence"], "absent")

        failed = self.cases["implementation-present-validation-failed"]["expected"]["claims"]
        self.assertEqual(failed["implementation_claim"], "present")
        self.assertEqual(failed["validation_evidence"], "failed")

        historical = self.cases["historical-implementation-removed-current"]["expected"]["claims"]
        self.assertEqual(historical["historical_implementation_claim"], "present")
        self.assertEqual(historical["implementation_claim"], "absent")

    def test_lifecycle_relation_and_role_boundaries_are_explicit(self) -> None:
        supersede = self.cases["supersede-effective-decision"]["expected"]
        self.assertEqual(supersede["claims"]["effective_decision"], "ADR-0102")
        self.assertEqual(supersede["relations"]["ADR-0102"]["supersedes"], ["ADR-0101"])

        amend = self.cases["amend-preserves-base-effect"]["expected"]
        self.assertEqual(amend["claims"]["effective_decisions"], ["ADR-0103", "ADR-0104"])
        self.assertIn("amend-equals-supersede", amend["must_not_infer"])

        self.assertIn("approved-design", self.cases["draft-not-approved"]["expected"]["must_not_infer"])
        self.assertIn("planned-is-current", self.cases["plan-not-current-state"]["expected"]["must_not_infer"])
        self.assertFalse(self.cases["snapshot-not-live-state"]["expected"]["claims"]["live_state"])

    def test_all_fact_scopes_are_covered_without_coordinator_scope(self) -> None:
        declared_scopes = set(self.fixture["contract"]["fact_scopes"])
        covered_scopes = {
            case["input"]["fact_scope"]
            for case in self.cases.values()
            if case["id"].startswith("scope-")
        }
        self.assertEqual(
            declared_scopes,
            {"canonical", "candidate", "worktree", "local-only", "historical", "unknown"},
        )
        self.assertEqual(covered_scopes, declared_scopes)
        self.assertNotIn("coordinator", declared_scopes)
        separated = self.cases["scope-not-coordinator-runtime"]["expected"]
        self.assertIn("coordinator_runtime", separated)
        self.assertIn("lock-confers-authority", separated["must_not_infer"])

    def test_evidence_and_ai_cannot_escalate_authority(self) -> None:
        evidence = self.cases["evidence-capability-boundaries"]["expected"]
        self.assertEqual(evidence["claims"]["human-or-agent-assertion"], "assertion-only")
        self.assertEqual(evidence["claims"]["derived-ai-summary"], "derived-interpretation-only")
        self.assertIn("summary-is-primary-evidence", evidence["must_not_infer"])

        derived = self.cases["derived-ai-non-escalation"]["expected"]
        self.assertEqual(derived["claims"]["authority_level"], "derived")
        self.assertEqual(derived["claims"]["implementation_claim"], "unknown")
        self.assertEqual(set(derived["must_not_infer"]), {"approved", "implemented", "validated"})

    def test_comparison_contract_distinguishes_determinism_from_visibility(self) -> None:
        comparisons = {item["id"]: item for item in self.fixture["comparisons"]}
        same = comparisons["same-input-same-output"]
        left = self.cases[same["left_case"]]
        right = self.cases[same["right_case"]]
        self.assertEqual(left["input"], right["input"])
        self.assertEqual(left["source_facts"], right["source_facts"])
        self.assertEqual(left["expected"], right["expected"])
        self.assertEqual(same["allowed_input_differences"], [])

        visible = comparisons["visibility-difference-is-explicit"]
        left = self.cases[visible["left_case"]]
        right = self.cases[visible["right_case"]]
        differing = {key for key in left["input"] if left["input"][key] != right["input"][key]}
        self.assertEqual(differing, {"evidence_visibility"})
        self.assertNotEqual(left["expected"], right["expected"])
        self.assertEqual(visible["allowed_input_differences"], ["evidence_visibility"])
        self.assertTrue(visible["difference_reason"])

    def test_normative_sources_resolve_inside_repository(self) -> None:
        for relative in self.fixture["normative_sources"]:
            with self.subTest(path=relative):
                self.assertTrue((REPOSITORY_ROOT / relative).is_file())

    def test_core_shadow_evaluator_satisfies_every_golden_expectation(self) -> None:
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                result = evaluate_authority(case["input"], case["observations"])
                for key, value in case["expected"]["claims"].items():
                    self.assertEqual(result["claims"].get(key), value, key)
                for key, value in case["expected"].get("relations", {}).items():
                    self.assertEqual(result["relations"].get(key), value, key)
                for key, value in case["expected"].get("coordinator_runtime", {}).items():
                    self.assertEqual(result["coordinator_runtime"].get(key), value, key)
                self.assertTrue(
                    set(case["expected"]["must_not_infer"]).issubset(result["must_not_infer"]),
                    (case["expected"]["must_not_infer"], result["must_not_infer"]),
                )

    def test_shadow_differences_are_explicitly_classified(self) -> None:
        policy = self.fixture["contract"]["shadow_policy"]
        allowed_claims = set(policy["allowed_extra_claims"])
        allowed_prohibitions = set(policy["allowed_extra_prohibitions"])
        exercised_claims: set[str] = set()
        exercised_prohibitions: set[str] = set()

        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                result = evaluate_authority(case["input"], case["observations"])
                expected = case["expected"]
                extra_claims = set(result["claims"]) - set(expected["claims"])
                extra_prohibitions = set(result["must_not_infer"]) - set(expected["must_not_infer"])
                self.assertTrue(extra_claims.issubset(allowed_claims), extra_claims)
                self.assertTrue(extra_prohibitions.issubset(allowed_prohibitions), extra_prohibitions)
                self.assertEqual(result["relations"], expected.get("relations", {}))
                self.assertEqual(result["coordinator_runtime"], expected.get("coordinator_runtime", {}))
                exercised_claims.update(extra_claims)
                exercised_prohibitions.update(extra_prohibitions)

        self.assertEqual(exercised_claims, allowed_claims)
        self.assertEqual(exercised_prohibitions, allowed_prohibitions)

    def test_core_shadow_evaluator_is_deterministic_and_visibility_sensitive(self) -> None:
        left = self.cases["deterministic-input-a"]
        right = self.cases["deterministic-input-b"]
        self.assertEqual(
            evaluate_authority(left["input"], left["observations"]),
            evaluate_authority(right["input"], right["observations"]),
        )

        visible = self.cases["visibility-with-validation"]
        hidden = self.cases["visibility-without-validation"]
        visible_result = evaluate_authority(visible["input"], visible["observations"])
        hidden_result = evaluate_authority(hidden["input"], hidden["observations"])
        self.assertEqual(visible_result["claims"]["validation_evidence"], "passed")
        self.assertEqual(hidden_result["claims"]["validation_evidence"], "unknown")
        self.assertNotEqual(visible_result, hidden_result)

    def test_core_shadow_evaluator_fails_closed(self) -> None:
        case = self.cases["scope-canonical"]
        invalid_version = dict(case["input"], authority_model_version="future-version")
        with self.assertRaises(AuthorityEvaluationError):
            evaluate_authority(invalid_version, case["observations"])

        invalid_scope = dict(case["input"], fact_scope="coordinator")
        with self.assertRaises(AuthorityEvaluationError):
            evaluate_authority(invalid_scope, case["observations"])

        invalid_observation = [{"kind": "magic-authority", "evidence_category": "revision-content"}]
        with self.assertRaises(AuthorityEvaluationError):
            evaluate_authority(case["input"], invalid_observation)

        invalid_evidence = dict(case["input"], evidence_visibility=["provider-specific-ci"])
        with self.assertRaises(AuthorityEvaluationError):
            evaluate_authority(invalid_evidence, case["observations"])

    def test_core_owner_is_not_yet_a_top_level_public_api(self) -> None:
        import project_orrery_core

        self.assertEqual(AUTHORITY_MODEL_VERSION, "amm-fixture-v1")
        self.assertFalse(hasattr(project_orrery_core, "evaluate_authority"))


if __name__ == "__main__":
    unittest.main()
