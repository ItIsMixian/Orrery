from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
for source in (CORE_SOURCE, CLI_SOURCE):
    sys.path.insert(0, str(source))

from project_orrery_cli.authority_shadow import (  # noqa: E402
    LegacyAuthorityFacts,
    authority_input_snapshot,
    build_authority_shadow,
    scan_legacy_authority,
)
from project_orrery_cli.context import repository_context  # noqa: E402
from project_orrery_cli.validate import parse_args, run  # noqa: E402
from project_orrery_core.authority import AuthorityEvaluationError  # noqa: E402


def write_authority_fixture(
    root: Path, *, accepted: bool = True, pending: bool = False
) -> None:
    (root / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "state").mkdir(parents=True, exist_ok=True)
    status = "Accepted" if accepted else "Proposed"
    (root / "docs" / "decisions" / "0001-test.md").write_text(
        f"# ADR-0001: Test\n\nStatus: {status}\n", encoding="utf-8"
    )
    (root / "AGENTS.md").write_text(
        "docs/HANDOFF.md docs/PROGRESS.md docs/state/\n", encoding="utf-8"
    )
    progress = "migration pending\n" if pending else "integrated\n"
    (root / "docs" / "PROGRESS.md").write_text(progress, encoding="utf-8")


class AuthorityCliShadowTests(unittest.TestCase):
    def test_legacy_scan_remains_the_production_integration_heuristic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-authority-cli-") as temporary:
            root = Path(temporary)
            write_authority_fixture(root)
            facts = scan_legacy_authority(root)
            self.assertEqual(
                facts,
                LegacyAuthorityFacts(
                    accepted_adr=True,
                    entrance_mapped=True,
                    pending_marker=False,
                    integrated=True,
                ),
            )

            write_authority_fixture(root, pending=True)
            self.assertFalse(scan_legacy_authority(root).integrated)

    def test_shadow_matches_real_scan_and_does_not_switch_production(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-authority-cli-") as temporary:
            root = Path(temporary)
            write_authority_fixture(root)
            report = build_authority_shadow(root)
            self.assertEqual(report["comparison"]["status"], "match")
            self.assertEqual(report["comparison"]["differences"], [])
            self.assertEqual(report["production_authority"], "legacy-cli")
            self.assertFalse(report["production_behavior_switched"])
            self.assertEqual(report["core"]["claims"]["decision_status"], "accepted")
            self.assertEqual(report["core"]["fact_scope"], "unknown")

    def test_snapshot_hash_changes_with_visible_authority_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-authority-cli-") as temporary:
            root = Path(temporary)
            write_authority_fixture(root)
            before = authority_input_snapshot(root)
            self.assertRegex(before, r"^authority-inputs:sha256:[0-9a-f]{64}$")
            (root / "docs" / "PROGRESS.md").write_text("changed\n", encoding="utf-8")
            after = authority_input_snapshot(root)
            self.assertNotEqual(before, after)

    def test_shadow_classifies_parser_gap_without_changing_legacy_facts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-authority-cli-") as temporary:
            root = Path(temporary)
            write_authority_fixture(root)
            forged_legacy = LegacyAuthorityFacts(False, True, False, False)
            report = build_authority_shadow(root, forged_legacy)
            self.assertEqual(report["comparison"]["status"], "mismatch")
            self.assertEqual(
                report["comparison"]["differences"],
                [
                    {
                        "field": "accepted_adr",
                        "legacy": False,
                        "core": True,
                        "category": "parser-gap",
                    }
                ],
            )
            self.assertEqual(
                report["legacy"],
                {
                    "accepted_adr": False,
                    "entrance_mapped": True,
                    "pending_marker": False,
                    "integrated": False,
                },
            )

    def test_validator_reports_shadow_mismatch_as_warning_only(self) -> None:
        mismatch = {
            "comparison": {
                "differences": [
                    {
                        "field": "accepted_adr",
                        "legacy": True,
                        "core": False,
                        "category": "parser-gap",
                    }
                ]
            }
        }
        output = io.StringIO()
        with mock.patch(
            "project_orrery_cli.validate.build_authority_shadow", return_value=mismatch
        ):
            with contextlib.redirect_stdout(output):
                code = run(
                    parse_args(
                        ["--target", str(REPOSITORY_ROOT), "--require-integrated"]
                    ),
                    repository_context(),
                )
        self.assertEqual(code, 0)
        text = output.getvalue()
        self.assertIn("Authority status: integrated candidate", text)
        self.assertIn(
            "WARNING: authority shadow mismatch; legacy CLI remains authoritative", text
        )

    def test_validator_degrades_shadow_failure_to_warning_only(self) -> None:
        output = io.StringIO()
        with mock.patch(
            "project_orrery_cli.validate.build_authority_shadow",
            side_effect=AuthorityEvaluationError("unsupported test input"),
        ):
            with contextlib.redirect_stdout(output):
                code = run(
                    parse_args(
                        ["--target", str(REPOSITORY_ROOT), "--require-integrated"]
                    ),
                    repository_context(),
                )
        self.assertEqual(code, 0)
        text = output.getvalue()
        self.assertIn("Authority status: integrated candidate", text)
        self.assertIn(
            "WARNING: authority shadow unavailable; legacy CLI remains authoritative",
            text,
        )


if __name__ == "__main__":
    unittest.main()
