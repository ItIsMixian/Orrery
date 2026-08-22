from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
SCHEMA = (
    CORE_SOURCE
    / "project_orrery_core"
    / "schema"
    / "documentation-governance-finding-v1.json"
)
RULES = (
    CORE_SOURCE
    / "project_orrery_core"
    / "data"
    / "documentation-governance-rules-v1.json"
)
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "documentation-governance" / "v1"
FIXTURE = FIXTURE_ROOT / "fixture.json"

sys.path.insert(0, str(CORE_SOURCE))

from project_orrery_core.documentation_governance import (  # noqa: E402
    DOCUMENTATION_FINDING_CONTRACT_ID,
    DOCUMENTATION_FINDING_SCHEMA_VERSION,
    DOCUMENTATION_RULE_REGISTRY_ID,
    REQUIRED_MUST_NOT_INFER,
    DocumentationGovernanceContractError,
    canonical_documentation_finding_json,
    load_documentation_rule_registry,
    validate_documentation_finding,
    validate_documentation_rule_registry,
)


class DocumentationGovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.rules = json.loads(RULES.read_text(encoding="utf-8"))
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.cases = {case["id"]: case for case in cls.fixture["cases"]}
        cls.findings = [
            finding
            for case in cls.fixture["cases"]
            for finding in case["expected_findings"]
        ]

    def test_schema_freezes_provider_neutral_read_only_non_authoritative_fields(self) -> None:
        self.assertEqual(self.schema["$id"], "project-orrery-documentation-governance-finding-v1")
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            self.schema["properties"]["contract_id"]["const"],
            DOCUMENTATION_FINDING_CONTRACT_ID,
        )
        self.assertEqual(DOCUMENTATION_FINDING_SCHEMA_VERSION, 1)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            set(self.schema["properties"]["category"]["enum"]),
            {
                "role-boundary",
                "current-history",
                "evidence-duplication",
                "staleness",
                "link-integrity",
                "metadata",
                "growth",
                "ownership",
            },
        )
        self.assertEqual(
            self.schema["properties"]["severity"]["enum"],
            ["info", "warning", "review-required"],
        )
        self.assertEqual(
            self.schema["properties"]["authority"]["const"],
            "non-authoritative-observation",
        )
        serialized = json.dumps(self.schema).lower()
        for forbidden in (
            "prompt",
            "transcript",
            "credential",
            "patch_content",
            "replacement_content",
            "authority_status",
            "validation_result",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_rule_registry_is_frozen_offline_and_does_not_choose_global_budgets(self) -> None:
        validate_documentation_rule_registry(self.rules)
        loaded = load_documentation_rule_registry()
        self.assertEqual(loaded, self.rules)
        self.assertIsNot(loaded, load_documentation_rule_registry())
        self.assertEqual(self.rules["registry_id"], DOCUMENTATION_RULE_REGISTRY_ID)
        self.assertEqual(
            self.rules["advisory_configuration"],
            {
                "location": "unselected",
                "default_when_absent": "disabled",
                "thresholds_are_authority": False,
                "thresholds_are_project_local": True,
            },
        )
        self.assertEqual(set(self.rules["execution_constraints"].values()), {False})
        self.assertEqual({rule["default_exit_code"] for rule in self.rules["rules"]}, {0})
        self.assertEqual(
            {rule["rule_id"] for rule in self.rules["rules"]},
            {
                "DG-ENTRANCE-SOFT-BUDGET-001",
                "DG-ENTRANCE-LINK-DENSITY-001",
                "DG-DUPLICATE-CURRENT-FACT-001",
                "DG-CURRENT-HISTORY-RETENTION-001",
                "DG-BROKEN-AUTHORITY-LINK-001",
                "DG-STATE-ROLE-BOUNDARY-001",
                "DG-PLAN-ROLE-BOUNDARY-001",
                "DG-VALIDATION-ROLE-BOUNDARY-001",
                "DG-INACTIVE-PLAN-001",
                "DG-STRUCTURED-METADATA-MISUSE-001",
                "DG-GLOBAL-ENTRY-OWNERSHIP-001",
            },
        )
        serialized = json.dumps(self.rules).lower()
        for provider_specific in ("openai", "deepseek", "claude", "codex"):
            self.assertNotIn(provider_specific, serialized)

    def test_fixture_has_paired_positive_and_negative_controls_for_every_required_smell(self) -> None:
        required_coverage = {
            "overlong-entry",
            "high-density-entry",
            "duplicate-fact",
            "historical-content-in-current-entry",
            "broken-link",
            "state-plan-responsibility-mix",
            "plan-state-validation-responsibility-mix",
            "validation-plan-responsibility-mix",
            "inactive-plan",
            "structured-metadata-misuse",
            "concurrent-global-entry-ownership",
        }
        polarities: dict[str, set[str]] = {}
        for case in self.fixture["cases"]:
            self.assertTrue((FIXTURE_ROOT / case["document"]).is_file())
            for coverage in case["coverage"]:
                polarities.setdefault(coverage, set()).add(case["polarity"])
            if case["polarity"] == "positive":
                self.assertEqual(len(case["expected_findings"]), 1)
            else:
                self.assertEqual(case["expected_findings"], [])
        self.assertTrue(required_coverage.issubset(polarities))
        for coverage in required_coverage:
            self.assertEqual(polarities[coverage], {"positive", "negative"}, coverage)

    def test_every_golden_finding_validates_and_carries_exact_source_evidence(self) -> None:
        for finding in self.findings:
            with self.subTest(finding=finding["finding_id"]):
                validate_documentation_finding(finding)
                source_path = FIXTURE_ROOT / finding["source"]["document"]
                content = source_path.read_bytes()
                lines = content.decode("utf-8").splitlines()
                for evidence in finding["source_evidence"]:
                    self.assertEqual(evidence["path"], finding["source"]["document"])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), evidence["sha256"])
                    self.assertLessEqual(evidence["line_end"], len(lines))
                    self.assertLessEqual(evidence["line_start"], evidence["line_end"])
                self.assertEqual(set(finding["must_not_infer"]), REQUIRED_MUST_NOT_INFER)
                self.assertFalse(finding["producer"]["network_access"])

    def test_soft_budget_fixture_metrics_are_reproducible_and_advisory(self) -> None:
        line_case = self.cases["entrance-soft-budget-positive"]
        line_finding = line_case["expected_findings"][0]
        line_text = (FIXTURE_ROOT / line_case["document"]).read_text(encoding="utf-8")
        non_empty = sum(bool(line.strip()) for line in line_text.splitlines())
        self.assertEqual(non_empty, line_finding["observed"][0]["value"])
        self.assertGreater(non_empty, self.fixture["advisory_config"]["entrance_non_empty_lines"])

        density_case = self.cases["entrance-density-positive"]
        density_finding = density_case["expected_findings"][0]
        density_text = (FIXTURE_ROOT / density_case["document"]).read_text(encoding="utf-8")
        non_empty_lines = [line for line in density_text.splitlines() if line.strip()]
        link_count = len(re.findall(r"\[[^\]]+\]\([^)]+\)", density_text))
        density = round(100 * link_count / len(non_empty_lines))
        self.assertEqual(density, density_finding["observed"][0]["value"])
        self.assertGreater(
            density, self.fixture["advisory_config"]["entrance_link_density_percent"]
        )
        for finding in (line_finding, density_finding):
            self.assertEqual(finding["review"]["review_class"], "soft-budget")
            self.assertEqual(finding["review"]["program_gate"], "advisory")
            self.assertEqual(finding["review"]["authority_effect"], "none")

    def test_structural_gate_eligibility_is_not_an_enabled_or_authority_hard_gate(self) -> None:
        broken = self.cases["broken-link-positive"]["expected_findings"][0]
        self.assertEqual(broken["review"]["review_class"], "structural-integrity")
        self.assertEqual(broken["review"]["program_gate"], "eligible-not-enabled")
        for finding in self.findings:
            self.assertIn(finding["review"]["program_gate"], {"advisory", "eligible-not-enabled"})
            self.assertEqual(finding["review"]["trigger"], "human-review")
            self.assertEqual(finding["review"]["authority_effect"], "none")
            self.assertEqual(finding["review"]["author_document_effect"], "none")
            self.assertIn("document-invalid", finding["must_not_infer"])
        self.assertEqual({rule["default_exit_code"] for rule in self.rules["rules"]}, {0})
        serialized = json.dumps(self.rules).lower()
        self.assertNotIn("enabled-hard-gate", serialized)
        self.assertNotIn("authority-hard-gate", serialized)

    def test_broken_link_pair_resolves_deterministically_inside_fixture(self) -> None:
        for case_id, expected_missing in (
            ("broken-link-positive", 1),
            ("broken-link-negative", 0),
        ):
            case = self.cases[case_id]
            path = FIXTURE_ROOT / case["document"]
            text = path.read_text(encoding="utf-8")
            targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
            missing = sum(not (path.parent / target).resolve().is_file() for target in targets)
            self.assertEqual(missing, expected_missing)

    def test_status_and_acknowledgement_lifecycle_is_explicit(self) -> None:
        base = self.findings[0]
        for lifecycle in self.fixture["review_lifecycle_examples"]:
            with self.subTest(status=lifecycle["status"]):
                finding = copy.deepcopy(base)
                finding["review"].update(lifecycle)
                validate_documentation_finding(finding)

        invalid = copy.deepcopy(base)
        invalid["review"]["status"] = "acknowledged"
        with self.assertRaisesRegex(
            DocumentationGovernanceContractError, "require an acknowledgement"
        ):
            validate_documentation_finding(invalid)

        invalid = copy.deepcopy(base)
        invalid["review"].update(self.fixture["review_lifecycle_examples"][2])
        invalid["review"]["acknowledgement"]["review_after"] = None
        with self.assertRaisesRegex(DocumentationGovernanceContractError, "review_after"):
            validate_documentation_finding(invalid)

    def test_contract_rejects_escalation_and_author_document_write_fields(self) -> None:
        for forbidden_field in ("patch_content", "authority_status", "validation_result"):
            finding = copy.deepcopy(self.findings[0])
            finding[forbidden_field] = "forbidden"
            with self.subTest(field=forbidden_field), self.assertRaisesRegex(
                DocumentationGovernanceContractError, "forbidden field"
            ):
                validate_documentation_finding(finding)

        finding = copy.deepcopy(self.findings[0])
        finding["review"]["author_document_effect"] = "rewrite"
        with self.assertRaises(DocumentationGovernanceContractError):
            validate_documentation_finding(finding)

        finding = copy.deepcopy(self.findings[0])
        finding["authority"] = "effective-state"
        with self.assertRaises(DocumentationGovernanceContractError):
            validate_documentation_finding(finding)

    def test_validation_is_deterministic_offline_and_has_no_file_side_effects(self) -> None:
        before = {
            path.relative_to(FIXTURE_ROOT).as_posix(): path.read_bytes()
            for path in FIXTURE_ROOT.rglob("*")
            if path.is_file()
        }
        original = self.findings[0]
        reversed_top_level = dict(reversed(list(original.items())))
        left = canonical_documentation_finding_json(original)
        right = canonical_documentation_finding_json(reversed_top_level)
        self.assertEqual(left, right)
        after = {
            path.relative_to(FIXTURE_ROOT).as_posix(): path.read_bytes()
            for path in FIXTURE_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_normative_sources_resolve_and_contract_remains_internal(self) -> None:
        for relative in self.fixture["normative_sources"]:
            with self.subTest(path=relative):
                self.assertTrue((REPOSITORY_ROOT / relative).is_file())
        import project_orrery_core

        self.assertFalse(hasattr(project_orrery_core, "validate_documentation_finding"))


if __name__ == "__main__":
    unittest.main()
