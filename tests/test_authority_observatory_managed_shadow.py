from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
OBSERVATORY_SOURCE = (
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
)
DOCSITE_SOURCE = REPOSITORY_ROOT / "scripts" / "docsite"
for source in (CORE_SOURCE, OBSERVATORY_SOURCE, DOCSITE_SOURCE):
    sys.path.insert(0, str(source))

import build_docsite  # noqa: E402
import docsite_insights  # noqa: E402


class AuthorityObservatoryManagedShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docs_dir = REPOSITORY_ROOT / "docs"
        cls.agents_file = REPOSITORY_ROOT / "AGENTS.md"
        cls.title = "Project Orrery managed Authority shadow test"
        cls.legacy_page, cls.legacy_stats = build_docsite.render_site(
            cls.docs_dir,
            cls.agents_file,
            REPOSITORY_ROOT,
            cls.title,
        )

    def render_runtime(self):
        return build_docsite._render_site_for_runtime(
            self.docs_dir,
            self.agents_file,
            REPOSITORY_ROOT,
            self.title,
        )

    def test_default_runtime_is_exact_legacy_path(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ORRERY_AUTHORITY_SHADOW_REPORT": "",
                "ORRERY_AUTHORITY_FACT_SCOPE": "",
                "ORRERY_AUTHORITY_SHADOW_VIEW": "",
            },
            clear=False,
        ):
            page, stats, report = self.render_runtime()

        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        self.assertIsNone(report)

    def test_opt_in_managed_runtime_writes_sidecar_without_switching_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-managed-shadow-") as temporary:
            report_path = Path(temporary) / "authority-shadow.json"
            with mock.patch.dict(
                os.environ,
                {
                    "ORRERY_AUTHORITY_SHADOW_REPORT": str(report_path),
                    "ORRERY_AUTHORITY_FACT_SCOPE": "candidate",
                    "ORRERY_AUTHORITY_SHADOW_VIEW": "",
                },
                clear=False,
            ):
                page, stats, report = self.render_runtime()

            self.assertEqual(page, self.legacy_page)
            self.assertEqual(stats, self.legacy_stats)
            self.assertIsNotNone(report)
            self.assertFalse(report["production_behavior_switched"])
            self.assertEqual(report["report_schema"], "authority-shadow-report-v1")
            self.assertEqual(report["authority_model"]["code"], "authority-model-supported")
            self.assertEqual(report["shadow"]["fact_scope"], "candidate")
            self.assertEqual(report["shadow"]["status"], "match")
            self.assertTrue(report_path.is_file())
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8")), report)

    def test_invalid_scope_fails_closed_but_preserves_legacy_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-managed-shadow-") as temporary:
            report_path = Path(temporary) / "authority-shadow.json"
            with mock.patch.dict(
                os.environ,
                {
                    "ORRERY_AUTHORITY_SHADOW_REPORT": str(report_path),
                    "ORRERY_AUTHORITY_FACT_SCOPE": "coordinator-owner",
                    "ORRERY_AUTHORITY_SHADOW_VIEW": "",
                },
                clear=False,
            ):
                page, stats, report = self.render_runtime()

            self.assertEqual(page, self.legacy_page)
            self.assertEqual(stats, self.legacy_stats)
            self.assertFalse(report["production_behavior_switched"])
            self.assertEqual(report["shadow"]["status"], "unavailable")
            self.assertEqual(report["shadow"]["fact_scope"], "coordinator-owner")
            self.assertEqual(
                report["shadow"]["error"]["type"], "AuthorityEvaluationError"
            )

    def test_explicit_shadow_view_adds_only_a_non_authoritative_panel(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ORRERY_AUTHORITY_SHADOW_REPORT": "",
                "ORRERY_AUTHORITY_FACT_SCOPE": "candidate",
                "ORRERY_AUTHORITY_SHADOW_VIEW": "1",
            },
            clear=False,
        ):
            page, stats, report = self.render_runtime()

        self.assertNotEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        self.assertIn('id="authority-shadow-diagnostic"', page)
        self.assertIn('data-authoritative="false"', page)
        self.assertIn('data-production-switched="false"', page)
        self.assertIn("非权威诊断", page)
        self.assertFalse(report["production_behavior_switched"])
        self.assertEqual(report["derived_view"]["status"], "rendered")
        self.assertFalse(report["derived_view"]["authoritative"])

    def test_insights_expose_health_counts_without_projecting_claims(self) -> None:
        report = {
            "production_behavior_switched": False,
            "authority_model": {"status": "supported"},
            "shadow": {
                "status": "mismatch",
                "fact_scope": "worktree",
                "adr": {
                    "comparison": {
                        "differences": [{"category": "parser-gap"}],
                        "relation_contract": {
                            "unresolved_targets": [{"target": "ADR-9999"}],
                            "effective_claims": {"effective_decision": "ADR-0009"},
                        },
                    }
                },
                "roles": {
                    "role_contract": {
                        "validation_unknown": ["validation-a", "validation-b"]
                    }
                },
            },
        }

        insight = docsite_insights.compute_authority_shadow_insights(report)

        self.assertFalse(insight["authoritative"])
        self.assertFalse(insight["creates_project_facts"])
        self.assertEqual(insight["difference_count"], 1)
        self.assertEqual(insight["unresolved_relation_count"], 1)
        self.assertEqual(insight["validation_unknown_count"], 2)
        self.assertNotIn("effective", str(insight))

    def test_root_and_template_projection_include_shadow_diagnostics(self) -> None:
        template_root = (
            REPOSITORY_ROOT
            / "skills"
            / "project-orrery"
            / "assets"
            / "project-template"
            / "scripts"
            / "docsite"
        )
        self.assertEqual(
            (DOCSITE_SOURCE / "docsite_insights.py").read_bytes(),
            (template_root / "docsite_insights.py").read_bytes(),
        )
        root_build = (DOCSITE_SOURCE / "build_docsite.py").read_text(encoding="utf-8")
        template_build = (template_root / "build_docsite.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            root_build,
            template_build.replace("{{PROJECT_TITLE_PY}}", "Project Orrery"),
        )


if __name__ == "__main__":
    unittest.main()
