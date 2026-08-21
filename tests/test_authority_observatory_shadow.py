from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
OBSERVATORY_SOURCE = (
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
)
DOCSITE_SOURCE = REPOSITORY_ROOT / "scripts" / "docsite"
for source in (CORE_SOURCE, OBSERVATORY_SOURCE, DOCSITE_SOURCE):
    sys.path.insert(0, str(source))

import build_docsite  # noqa: E402
import project_orrery_observatory  # noqa: E402
from project_orrery_core.authority import (  # noqa: E402
    AUTHORITY_MODEL_VERSION,
    evaluate_authority,
)
from project_orrery_observatory.authority_shadow import (  # noqa: E402
    authority_input_snapshot,
    build_observatory_authority_shadow,
    normalize_decision_status,
)


def write_adr(decisions_dir: Path, number: int, status: str) -> None:
    decisions_dir.mkdir(parents=True, exist_ok=True)
    (decisions_dir / f"{number:04d}-test-{number}.md").write_text(
        f"# ADR-{number:04d}: Test {number}\n\nStatus: {status}\n\n## Context\n\nTest.\n",
        encoding="utf-8",
    )


class AuthorityObservatoryShadowTests(unittest.TestCase):
    def build_shadow(self, decisions_dir: Path) -> tuple[list[dict], dict]:
        adrs = build_docsite.parse_adrs(decisions_dir)
        report = build_observatory_authority_shadow(
            adrs,
            decisions_dir,
            evaluator=evaluate_authority,
            authority_model_version=AUTHORITY_MODEL_VERSION,
        )
        return adrs, report

    def test_internal_shadow_adapter_is_not_a_top_level_observatory_api(self) -> None:
        self.assertFalse(hasattr(project_orrery_observatory, "build_observatory_authority_shadow"))

    def test_status_normalizer_covers_legacy_lifecycle_classes(self) -> None:
        cases = {
            "Accepted": "accepted",
            "Accepted; superseded by ADR-0099": "superseded",
            "Superseded": "superseded",
            "Deprecated": "deprecated",
            "Proposed": "proposed",
            "Design / Deferred": "deferred",
            "Rejected": "other",
            "": "other",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_decision_status(raw), expected)

    def test_real_legacy_parser_dual_run_matches_all_lifecycle_classes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            for number, status in enumerate(
                (
                    "Accepted",
                    "Accepted; superseded by ADR-0099",
                    "Superseded",
                    "Deprecated",
                    "Proposed",
                    "Design / Deferred",
                    "Rejected",
                ),
                start=1,
            ):
                write_adr(decisions_dir, number, status)

            adrs, report = self.build_shadow(decisions_dir)
            self.assertEqual(len(adrs), 7)
            self.assertEqual(report["comparison"]["status"], "match")
            self.assertEqual(report["comparison"]["checked"], 7)
            self.assertEqual(report["comparison"]["differences"], [])
            self.assertEqual(report["production_authority"], "legacy-observatory-parser")
            self.assertFalse(report["production_behavior_switched"])
            self.assertEqual(report["conformance_input"]["fact_scope"], "unknown")

    def test_repository_parser_output_matches_core_shadow(self) -> None:
        decisions_dir = REPOSITORY_ROOT / "docs" / "decisions"
        adrs, report = self.build_shadow(decisions_dir)
        self.assertGreaterEqual(len(adrs), 10)
        self.assertEqual(report["comparison"]["checked"], len(adrs))
        self.assertEqual(report["comparison"]["status"], "match")

    def test_forged_legacy_difference_is_classified_without_switching(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            adrs = build_docsite.parse_adrs(decisions_dir)
            forged = copy.deepcopy(adrs)
            forged[0]["status_class"] = "proposed"
            report = build_observatory_authority_shadow(
                forged,
                decisions_dir,
                evaluator=evaluate_authority,
                authority_model_version=AUTHORITY_MODEL_VERSION,
            )
            self.assertEqual(report["comparison"]["status"], "mismatch")
            self.assertEqual(
                report["comparison"]["differences"],
                [
                    {
                        "adr": "ADR-0001",
                        "field": "decision_status",
                        "legacy": "proposed",
                        "core": "accepted",
                        "category": "parser-gap",
                    }
                ],
            )
            self.assertFalse(report["production_behavior_switched"])

    def test_snapshot_changes_when_visible_adr_bytes_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            before = authority_input_snapshot(decisions_dir)
            self.assertRegex(before, r"^observatory-adr-inputs:sha256:[0-9a-f]{64}$")
            write_adr(decisions_dir, 1, "Proposed")
            after = authority_input_snapshot(decisions_dir)
            self.assertNotEqual(before, after)

    def test_snapshot_ignores_files_the_legacy_parser_does_not_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            before = authority_input_snapshot(decisions_dir)
            (decisions_dir / "README.md").write_text("changed\n", encoding="utf-8")
            (decisions_dir / "0000-template.md").write_text(
                "# Template\n\nStatus: Proposed\n", encoding="utf-8"
            )
            (decisions_dir / "1-not-an-adr.md").write_text(
                "# Non-standard\n\nStatus: Accepted\n", encoding="utf-8"
            )
            self.assertEqual(before, authority_input_snapshot(decisions_dir))

    def test_graph_and_reference_fields_stay_legacy_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            _, report = self.build_shadow(decisions_dir)
            self.assertEqual(
                report["comparison"]["legacy_only"],
                {
                    "predecessors": "legacy-graph-heuristic",
                    "supersedes": "legacy-graph-heuristic",
                    "refs": "legacy-reference-graph",
                    "state_refs": "legacy-reference-graph",
                },
            )


if __name__ == "__main__":
    unittest.main()
