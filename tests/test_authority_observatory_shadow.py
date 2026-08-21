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
    AuthorityRelationParseError,
    authority_input_snapshot,
    build_observatory_authority_shadow,
    collect_decision_observations,
    normalize_decision_status,
)


def write_adr(
    decisions_dir: Path,
    number: int,
    status: str,
    *,
    metadata: tuple[str, ...] = (),
    body: str = "Test.",
) -> None:
    decisions_dir.mkdir(parents=True, exist_ok=True)
    metadata_text = "".join(f"{line}\n" for line in metadata)
    (decisions_dir / f"{number:04d}-test-{number}.md").write_text(
        f"# ADR-{number:04d}: Test {number}\n\nStatus: {status}\n"
        f"{metadata_text}\n## Context\n\n{body}\n",
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
                    "Accepted; superseded",
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

    def test_explicit_supersedes_yields_effective_decision(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            write_adr(
                decisions_dir,
                2,
                "Accepted",
                metadata=("Supersedes: [ADR-0001](0001-test-1.md)",),
            )
            _, report = self.build_shadow(decisions_dir)
            contract = report["comparison"]["relation_contract"]
            self.assertEqual(contract["status"], "match")
            self.assertEqual(
                contract["core_relations"],
                {"ADR-0002": {"supersedes": ["ADR-0001"]}},
            )
            self.assertEqual(contract["effective_claims"], {"effective_decision": "ADR-0002"})

    def test_status_superseded_by_is_inverted_to_normative_direction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Superseded by ADR-0002")
            write_adr(decisions_dir, 2, "Accepted")
            adrs, report = self.build_shadow(decisions_dir)
            self.assertEqual(adrs[0]["supersedes"], ["0002"])
            contract = report["comparison"]["relation_contract"]
            self.assertEqual(
                contract["core_relations"],
                {"ADR-0002": {"supersedes": ["ADR-0001"]}},
            )
            self.assertEqual(contract["legacy_superseded_by"], {"ADR-0001": ["ADR-0002"]})
            self.assertEqual(contract["effective_claims"], {"effective_decision": "ADR-0002"})

    def test_amends_preserves_base_and_amendment_as_effective(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            write_adr(
                decisions_dir,
                2,
                "Accepted",
                metadata=("Amends: [ADR-0001](0001-test-1.md)",),
            )
            _, report = self.build_shadow(decisions_dir)
            contract = report["comparison"]["relation_contract"]
            self.assertEqual(
                contract["core_relations"], {"ADR-0002": {"amends": ["ADR-0001"]}}
            )
            self.assertEqual(
                contract["effective_claims"],
                {"effective_decisions": ["ADR-0001", "ADR-0002"]},
            )

    def test_predecessor_and_body_refs_do_not_become_normative_relations(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted")
            write_adr(
                decisions_dir,
                2,
                "Accepted",
                metadata=("Predecessor: ADR-0001",),
                body="See ADR-0001 and state/example.md.",
            )
            adrs = build_docsite.parse_adrs(decisions_dir)
            normalized = collect_decision_observations(adrs, decisions_dir)
            self.assertEqual(adrs[1]["predecessors"], ["0001"])
            self.assertEqual(normalized["sources"], [])
            self.assertNotIn("supersedes", normalized["observations"][1])
            self.assertNotIn("amends", normalized["observations"][1])

    def test_malformed_explicit_relation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Accepted", metadata=("Amends: earlier choice",))
            adrs = build_docsite.parse_adrs(decisions_dir)
            with self.assertRaises(AuthorityRelationParseError):
                collect_decision_observations(adrs, decisions_dir)

    def test_missing_relation_target_remains_unknown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-observatory-shadow-") as temporary:
            decisions_dir = Path(temporary) / "docs" / "decisions"
            write_adr(decisions_dir, 1, "Superseded by ADR-9999")
            _, report = self.build_shadow(decisions_dir)
            contract = report["comparison"]["relation_contract"]
            self.assertEqual(contract["status"], "unknown")
            self.assertEqual(report["comparison"]["status"], "unknown")
            self.assertEqual(
                contract["unresolved_targets"],
                [
                    {
                        "source": "ADR-9999",
                        "relation": "supersedes",
                        "target": "ADR-0001",
                        "reason": "replacement-not-visible",
                    }
                ],
            )
            self.assertEqual(contract["effective_claims"], {})

    def test_repository_amendments_have_explicit_core_relations(self) -> None:
        decisions_dir = REPOSITORY_ROOT / "docs" / "decisions"
        _, report = self.build_shadow(decisions_dir)
        contract = report["comparison"]["relation_contract"]
        self.assertEqual(contract["status"], "match")
        self.assertEqual(contract["unresolved_targets"], [])
        self.assertEqual(
            contract["core_relations"],
            {
                "ADR-0004": {"amends": ["ADR-0001"]},
                "ADR-0005": {"amends": ["ADR-0002"]},
                "ADR-0006": {"amends": ["ADR-0003"]},
                "ADR-0008": {"amends": ["ADR-0007"]},
                "ADR-0009": {"amends": ["ADR-0001"]},
                "ADR-0010": {"amends": ["ADR-0009"]},
            },
        )

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
                    "refs": "legacy-reference-graph",
                    "state_refs": "legacy-reference-graph",
                },
            )


if __name__ == "__main__":
    unittest.main()
