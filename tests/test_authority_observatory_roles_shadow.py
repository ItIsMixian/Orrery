from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
OBSERVATORY_SOURCE = (
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
)
for source in (CORE_SOURCE, OBSERVATORY_SOURCE):
    sys.path.insert(0, str(source))

import project_orrery_observatory  # noqa: E402
from project_orrery_core.authority import (  # noqa: E402
    AUTHORITY_MODEL_VERSION,
    evaluate_authority,
)
from project_orrery_observatory.authority_role_shadow import (  # noqa: E402
    AuthorityRoleParseError,
    authority_role_input_snapshot,
    build_observatory_role_shadow,
    collect_authority_role_observations,
    normalize_design_lifecycle,
)


def write_role(docs_dir: Path, relative: str, header: str = "") -> Path:
    path = docs_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = f"\n{header.strip()}\n" if header.strip() else "\n"
    path.write_text(
        f"# {path.stem}{metadata}\n## Evidence\n\nExample.\n",
        encoding="utf-8",
    )
    return path


class AuthorityObservatoryRoleShadowTests(unittest.TestCase):
    def build_shadow(self, docs_dir: Path, **kwargs: object) -> dict:
        return build_observatory_role_shadow(
            docs_dir,
            evaluator=evaluate_authority,
            authority_model_version=AUTHORITY_MODEL_VERSION,
            **kwargs,
        )

    def test_role_shadow_is_not_a_top_level_observatory_api(self) -> None:
        self.assertFalse(hasattr(project_orrery_observatory, "build_observatory_role_shadow"))

    def test_design_lifecycle_is_strict_and_unknown_by_default(self) -> None:
        cases = {
            "Approved": "approved",
            "Approved for local use": "approved",
            "Draft": "draft",
            "Deprecated": "deprecated",
            "Accepted": "unknown",
            "": "unknown",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_design_lifecycle(raw), expected)

    def test_design_plan_and_state_claims_stay_independent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-role-shadow-") as temporary:
            docs_dir = Path(temporary) / "docs"
            write_role(docs_dir, "design/draft.md", "Status: Draft")
            write_role(docs_dir, "implementation/plans/feature.md", "Status: Active")
            write_role(docs_dir, "state/current.md")

            report = self.build_shadow(docs_dir)
            by_role = {
                document["role"]: document
                for document in report["role_contract"]["documents"]
            }
            self.assertEqual(by_role["design"]["claims"]["design_lifecycle"], "draft")
            self.assertIn("approved-design", by_role["design"]["must_not_infer"])
            self.assertTrue(by_role["plan"]["claims"]["planned"])
            self.assertTrue(by_role["state"]["claims"]["current"])
            self.assertNotIn("implementation_claim", by_role["plan"]["claims"])
            self.assertNotIn("implementation_claim", by_role["state"]["claims"])
            self.assertFalse(report["production_behavior_switched"])

    def test_validation_presence_status_and_free_form_result_remain_unknown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-role-shadow-") as temporary:
            docs_dir = Path(temporary) / "docs"
            write_role(
                docs_dir,
                "validation/status-only.md",
                "Status: Passed for local integration",
            )
            write_role(
                docs_dir,
                "validation/free-form.md",
                "Result: six runs valid; cost passed; quality failed",
            )

            report = self.build_shadow(docs_dir)
            validations = report["role_contract"]["documents"]
            self.assertEqual(len(validations), 2)
            self.assertTrue(
                all(
                    document["claims"]["validation_evidence"] == "unknown"
                    for document in validations
                )
            )
            self.assertEqual(report["role_contract"]["validation_unknown"], 2)

    def test_explicit_result_or_outcome_can_be_normalized(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-role-shadow-") as temporary:
            docs_dir = Path(temporary) / "docs"
            write_role(docs_dir, "validation/pass.md", "Result: Passed")
            write_role(docs_dir, "validation/fail.md", "Outcome: Failed")

            report = self.build_shadow(docs_dir)
            results = {
                document["source"]: document["claims"]["validation_evidence"]
                for document in report["role_contract"]["documents"]
            }
            self.assertEqual(
                results,
                {
                    "docs/validation/fail.md": "failed",
                    "docs/validation/pass.md": "passed",
                },
            )

    def test_hidden_executable_validation_fails_closed_to_unknown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-role-shadow-") as temporary:
            docs_dir = Path(temporary) / "docs"
            write_role(docs_dir, "validation/pass.md", "Result: Passed")

            report = self.build_shadow(
                docs_dir, evidence_visibility=("revision-content",)
            )
            document = report["role_contract"]["documents"][0]
            self.assertEqual(document["claims"]["validation_evidence"], "unknown")
            self.assertIn("validated", document["must_not_infer"])

    def test_conflicting_explicit_validation_metadata_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-role-shadow-") as temporary:
            docs_dir = Path(temporary) / "docs"
            write_role(
                docs_dir,
                "validation/conflict.md",
                "Result: Passed\nOutcome: Failed",
            )
            with self.assertRaises(AuthorityRoleParseError):
                collect_authority_role_observations(docs_dir)

    def test_snapshot_tracks_only_role_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-role-shadow-") as temporary:
            docs_dir = Path(temporary) / "docs"
            role_path = write_role(docs_dir, "design/example.md", "Status: Approved")
            before = authority_role_input_snapshot(docs_dir)
            self.assertRegex(
                before,
                r"^observatory-authority-role-inputs:sha256:[0-9a-f]{64}$",
            )
            write_role(docs_dir, "design/README.md", "Status: Draft")
            write_role(docs_dir, "state/_template.md")
            write_role(docs_dir, "library/unrelated.md")
            self.assertEqual(before, authority_role_input_snapshot(docs_dir))
            role_path.write_text("# changed\n", encoding="utf-8")
            self.assertNotEqual(before, authority_role_input_snapshot(docs_dir))

    def test_repository_roles_are_observed_without_inventing_validation_success(self) -> None:
        report = self.build_shadow(REPOSITORY_ROOT / "docs")
        counts = report["role_contract"]["counts"]
        self.assertGreaterEqual(counts["design"], 7)
        self.assertGreaterEqual(counts["plan"], 12)
        self.assertGreaterEqual(counts["state"], 6)
        self.assertGreaterEqual(counts["validation"], 20)
        validations = [
            document
            for document in report["role_contract"]["documents"]
            if document["role"] == "validation"
        ]
        self.assertTrue(validations)
        self.assertTrue(
            all(
                document["claims"]["validation_evidence"] == "unknown"
                for document in validations
            )
        )


if __name__ == "__main__":
    unittest.main()
