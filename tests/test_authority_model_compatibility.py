from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
FIXTURE = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "authority-meta-model"
    / "v1"
    / "compatibility.json"
)

sys.path.insert(0, str(CORE_SOURCE))

from project_orrery_core.authority import AUTHORITY_MODEL_VERSION  # noqa: E402
from project_orrery_core.authority_compatibility import (  # noqa: E402
    AUTHORITY_MODEL_FIELD,
    AUTHORITY_MODEL_FIXTURE_IDS,
    PUBLIC_AUTHORITY_MODEL_VERSION,
    AuthorityModelCompatibilityError,
    judge_authority_model_version,
    judge_project_authority_model,
)


class AuthorityModelCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_public_version_maps_to_internal_fixture_without_reusing_its_id(self) -> None:
        self.assertEqual(PUBLIC_AUTHORITY_MODEL_VERSION, 1)
        self.assertEqual(AUTHORITY_MODEL_FIXTURE_IDS[1], AUTHORITY_MODEL_VERSION)
        self.assertEqual(self.fixture["public_authority_model_version"], 1)
        self.assertEqual(self.fixture["internal_fixture_id"], "amm-fixture-v1")
        self.assertNotEqual(str(PUBLIC_AUTHORITY_MODEL_VERSION), AUTHORITY_MODEL_VERSION)

    def test_fixture_freezes_orthogonal_version_and_upgrade_boundaries(self) -> None:
        contract = self.fixture["contract"]
        self.assertEqual(contract["project_field"], AUTHORITY_MODEL_FIELD)
        self.assertFalse(contract["ordinary_tool_upgrade_may_select_model"])
        self.assertFalse(contract["manifest_format_changes"])
        self.assertFalse(contract["document_schema_changes"])

    def test_every_compatibility_case_matches_core_judgment(self) -> None:
        unavailable = self.fixture["contract"]["unavailable_must_not_infer"]
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                result = judge_project_authority_model(
                    case["manifest"],
                    supported_versions=case["supported_versions"],
                    known_versions=case["known_versions"],
                )
                for key, value in case["expected"].items():
                    self.assertEqual(result[key], value, key)
                if result["authority_evaluation_capability"] == "available":
                    self.assertEqual(result["must_not_infer"], [])
                else:
                    self.assertEqual(result["must_not_infer"], unavailable)

    def test_missing_differs_from_present_null(self) -> None:
        missing = judge_project_authority_model({})
        present_null = judge_project_authority_model({AUTHORITY_MODEL_FIELD: None})
        self.assertEqual(missing["status"], "legacy-unversioned")
        self.assertEqual(present_null["status"], "invalid")

    def test_discrete_support_does_not_fill_numeric_gaps(self) -> None:
        result = judge_authority_model_version(
            2,
            supported_versions=(1, 3),
            known_versions=(1, 3),
        )
        self.assertEqual(result["status"], "unsupported-unknown")
        self.assertEqual(result["authority_evaluation_capability"], "unavailable")
        self.assertEqual(result["read_only_browsing"], "available")

    def test_unknown_newer_and_downgrade_incompatibility_fail_closed(self) -> None:
        newer = judge_authority_model_version(
            4,
            supported_versions=(1, 3),
            known_versions=(1, 3),
        )
        downgrade = judge_authority_model_version(
            1,
            supported_versions=(2,),
            known_versions=(1, 2),
        )
        self.assertEqual(newer["status"], "unsupported-newer")
        self.assertEqual(downgrade["status"], "unsupported-known")
        self.assertEqual(newer["must_not_infer"], downgrade["must_not_infer"])

    def test_invalid_consumer_capability_declarations_are_rejected(self) -> None:
        invalid_declarations = (
            {"supported_versions": (1, 1), "known_versions": (1,)},
            {"supported_versions": (0,), "known_versions": (0,)},
            {"supported_versions": (2,), "known_versions": (1,)},
            {"supported_versions": (True,), "known_versions": (True,)},
        )
        for declaration in invalid_declarations:
            with self.subTest(declaration=declaration):
                with self.assertRaises(AuthorityModelCompatibilityError):
                    judge_authority_model_version(1, **declaration)

    def test_gate_b_judgment_is_not_yet_a_top_level_public_api(self) -> None:
        import project_orrery_core

        self.assertFalse(hasattr(project_orrery_core, "judge_authority_model_version"))
        self.assertFalse(hasattr(project_orrery_core, "PUBLIC_AUTHORITY_MODEL_VERSION"))


if __name__ == "__main__":
    unittest.main()
