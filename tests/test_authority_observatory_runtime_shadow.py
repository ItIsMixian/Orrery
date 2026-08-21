from __future__ import annotations

import hashlib
import sys
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
from project_orrery_observatory.runtime_shadow import (  # noqa: E402
    render_with_authority_shadow,
)


class AuthorityObservatoryRuntimeShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docs_dir = REPOSITORY_ROOT / "docs"
        cls.agents_file = REPOSITORY_ROOT / "AGENTS.md"
        cls.title = "Project Orrery authority runtime shadow test"
        cls.legacy_page, cls.legacy_stats = build_docsite.render_site(
            cls.docs_dir,
            cls.agents_file,
            REPOSITORY_ROOT,
            cls.title,
        )

    def render_shadow(self, **kwargs: object) -> tuple[str, dict, dict]:
        return render_with_authority_shadow(
            self.docs_dir,
            self.agents_file,
            REPOSITORY_ROOT,
            self.title,
            legacy_renderer=build_docsite.render_site,
            legacy_adr_parser=build_docsite.parse_adrs,
            evaluator=evaluate_authority,
            authority_model_version=AUTHORITY_MODEL_VERSION,
            **kwargs,
        )

    def test_runtime_bridge_is_not_a_top_level_observatory_api(self) -> None:
        self.assertFalse(
            hasattr(project_orrery_observatory, "render_with_authority_shadow")
        )

    def test_real_legacy_render_is_byte_identical_during_dual_run(self) -> None:
        page, stats, report = self.render_shadow()
        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        self.assertEqual(
            report["production"]["html_sha256"],
            hashlib.sha256(self.legacy_page.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(report["production"]["stats"], self.legacy_stats)
        self.assertFalse(report["production_behavior_switched"])

    def test_real_repository_runtime_shadow_combines_adr_and_role_contracts(self) -> None:
        _, _, report = self.render_shadow()
        self.assertEqual(report["shadow"]["status"], "match")
        self.assertEqual(report["shadow"]["fact_scope"], "unknown")
        self.assertEqual(
            report["shadow"]["adr"]["comparison"]["checked"],
            self.legacy_stats["adrs"],
        )
        counts = report["shadow"]["roles"]["role_contract"]["counts"]
        self.assertEqual(counts["design"], 7)
        self.assertEqual(counts["plan"], 12)
        self.assertEqual(counts["state"], 6)
        self.assertGreaterEqual(counts["validation"], 30)

    def test_shadow_evaluator_failure_isolated_from_legacy_output(self) -> None:
        def broken_evaluator(*_args: object, **_kwargs: object) -> dict:
            raise RuntimeError("synthetic shadow failure")

        page, stats, report = render_with_authority_shadow(
            self.docs_dir,
            self.agents_file,
            REPOSITORY_ROOT,
            self.title,
            legacy_renderer=build_docsite.render_site,
            legacy_adr_parser=build_docsite.parse_adrs,
            evaluator=broken_evaluator,
            authority_model_version=AUTHORITY_MODEL_VERSION,
        )
        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        self.assertEqual(report["shadow"]["status"], "unavailable")
        self.assertEqual(report["shadow"]["error"]["type"], "RuntimeError")
        self.assertFalse(report["production_behavior_switched"])

    def test_shadow_scope_is_explicit_without_changing_render(self) -> None:
        page, stats, report = self.render_shadow(fact_scope="candidate")
        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        self.assertEqual(report["shadow"]["fact_scope"], "candidate")
        self.assertEqual(
            report["shadow"]["adr"]["conformance_input"]["fact_scope"],
            "candidate",
        )
        self.assertEqual(
            report["shadow"]["roles"]["conformance_input"]["fact_scope"],
            "candidate",
        )


if __name__ == "__main__":
    unittest.main()
