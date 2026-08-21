from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
DOCSITE_SOURCE = REPOSITORY_ROOT / "scripts" / "docsite"
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "authority-meta-model" / "v1"
for source in (CORE_SOURCE, OBSERVATORY_SOURCE, CLI_SOURCE, DOCSITE_SOURCE):
    sys.path.insert(0, str(source))

import build_docsite  # noqa: E402
import build_authority_projection as authority_projection_site  # noqa: E402
import project_orrery_cli.authority_observations as authority_observations  # noqa: E402
import project_orrery_observatory  # noqa: E402
from project_orrery_cli.authority_observations import (  # noqa: E402
    DEFAULT_EVIDENCE_VISIBILITY,
    build_cli_authority_contract,
)
from project_orrery_observatory.authority_projection import (  # noqa: E402
    AuthorityProjectionError,
    PROJECTION_SCHEMA,
    build_authority_projection,
)


def write_file(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class AuthorityObservatoryProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cli_fixture = json.loads(
            (FIXTURE_ROOT / "cli-observation-contract.json").read_text(encoding="utf-8")
        )
        cls.projection_fixture = json.loads(
            (FIXTURE_ROOT / "observatory-projection.json").read_text(encoding="utf-8")
        )
        cls.docs_dir = REPOSITORY_ROOT / "docs"
        cls.agents_file = REPOSITORY_ROOT / "AGENTS.md"
        cls.title = "Project Orrery M2.2 projection test"
        cls.legacy_page, cls.legacy_stats = build_docsite.render_site(
            cls.docs_dir, cls.agents_file, REPOSITORY_ROOT, cls.title
        )

    def write_cli_fixture(self, root: Path) -> None:
        for document in self.cli_fixture["documents"]:
            write_file(root, document["path"], document["content"])

    def projection_from_bundle(self, bundle: dict) -> dict:
        inputs = bundle["conformance_input"]
        return build_authority_projection(
            bundle,
            authority_model_version=inputs["authority_model_version"],
            repository_snapshot=inputs["repository_snapshot"],
            fact_scope=inputs["fact_scope"],
            evidence_visibility=inputs["evidence_visibility"],
        )

    def render_runtime(self):
        return authority_projection_site.render_candidate_site(
            self.docs_dir, self.agents_file, REPOSITORY_ROOT, self.title
        )

    def projection_environment(self) -> dict[str, str]:
        return {
            "ORRERY_AUTHORITY_PROJECTION_VIEW": "1",
            "ORRERY_AUTHORITY_SHADOW_VIEW": "",
            "ORRERY_AUTHORITY_SHADOW_REPORT": "",
            "ORRERY_AUTHORITY_FACT_SCOPE": "candidate",
            "ORRERY_AUTHORITY_EVIDENCE_VISIBILITY": "",
        }

    def test_observatory_package_imports_without_cli_dependency(self) -> None:
        self.assertFalse(
            hasattr(project_orrery_observatory, "build_authority_projection")
        )
        source = (
            OBSERVATORY_SOURCE
            / "project_orrery_observatory"
            / "authority_projection.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("import project_orrery_cli", source)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(OBSERVATORY_SOURCE)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import project_orrery_observatory.authority_projection as p; print(p.PROJECTION_SCHEMA)",
            ],
            cwd=tempfile.gettempdir(),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), PROJECTION_SCHEMA)

    def test_fixture_projects_exact_m2_1_claims_and_sources(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="orrery-observatory-projection-"
        ) as temporary:
            root = Path(temporary)
            self.write_cli_fixture(root)
            bundle = build_cli_authority_contract(root, fact_scope="candidate")
            projection = self.projection_from_bundle(bundle)

        self.assertEqual(projection["projection_schema"], PROJECTION_SCHEMA)
        self.assertEqual(projection["reconciliation"]["status"], "match")
        self.assertEqual(
            projection["reconciliation"]["source_contract"],
            self.projection_fixture["source_contract"],
        )
        self.assertEqual(
            list(projection["roles"]), self.projection_fixture["expected_roles"]
        )
        self.assertEqual(
            projection["decision_graph"]["effective_decisions"],
            self.projection_fixture["expected_effective_decisions"],
        )
        bundle_by_source = {
            document["source"]: document for document in bundle["documents"]
        }
        for documents in projection["roles"].values():
            for document in documents:
                original = bundle_by_source[document["source"]]
                self.assertEqual(document["claims"], original["claims"])
                self.assertEqual(document["relations"], original["relations"])
                self.assertEqual(document["source_sha256"], original["source_sha256"])
                self.assertTrue(document["source_href"].startswith("#"))

    def test_projection_is_deterministic_and_scope_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="orrery-observatory-projection-"
        ) as temporary:
            root = Path(temporary)
            self.write_cli_fixture(root)
            bundle = build_cli_authority_contract(root, fact_scope="candidate")
            first = self.projection_from_bundle(bundle)
            second = self.projection_from_bundle(bundle)
            self.assertEqual(first, second)
            with self.assertRaisesRegex(
                AuthorityProjectionError, "conformance input does not match"
            ):
                build_authority_projection(
                    bundle,
                    authority_model_version=bundle["conformance_input"][
                        "authority_model_version"
                    ],
                    repository_snapshot=bundle["conformance_input"][
                        "repository_snapshot"
                    ],
                    fact_scope="canonical",
                    evidence_visibility=DEFAULT_EVIDENCE_VISIBILITY,
                )

    def test_tampered_source_and_provenance_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="orrery-observatory-projection-"
        ) as temporary:
            root = Path(temporary)
            self.write_cli_fixture(root)
            bundle = build_cli_authority_contract(root)
        unsafe = copy.deepcopy(bundle)
        unsafe["documents"][0]["source"] = "../outside.md"
        with self.assertRaisesRegex(
            AuthorityProjectionError, "unsafe repository source"
        ):
            self.projection_from_bundle(unsafe)
        mismatch = copy.deepcopy(bundle)
        mismatch["documents"][0]["evidence_provenance"][0]["source_sha256"] = (
            "sha256:" + "0" * 64
        )
        with self.assertRaisesRegex(
            AuthorityProjectionError, "evidence/source mismatch"
        ):
            self.projection_from_bundle(mismatch)

    def test_default_and_rollback_paths_are_exact_legacy(self) -> None:
        disabled = {
            "ORRERY_AUTHORITY_PROJECTION_VIEW": "",
            "ORRERY_AUTHORITY_SHADOW_VIEW": "",
            "ORRERY_AUTHORITY_SHADOW_REPORT": "",
            "ORRERY_AUTHORITY_FACT_SCOPE": "",
            "ORRERY_AUTHORITY_EVIDENCE_VISIBILITY": "",
        }
        with mock.patch.dict(os.environ, disabled, clear=False):
            page_before, stats_before, report_before = self.render_runtime()
        with mock.patch.dict(os.environ, self.projection_environment(), clear=False):
            projected_page, projected_stats, projected_report = self.render_runtime()
        with mock.patch.dict(os.environ, disabled, clear=False):
            page_after, stats_after, report_after = self.render_runtime()

        self.assertEqual(page_before, self.legacy_page)
        self.assertEqual(page_after, self.legacy_page)
        self.assertEqual(stats_before, self.legacy_stats)
        self.assertEqual(stats_after, self.legacy_stats)
        self.assertIsNone(report_before)
        self.assertIsNone(report_after)
        self.assertNotEqual(projected_page, self.legacy_page)
        self.assertEqual(projected_stats, self.legacy_stats)
        self.assertEqual(projected_report["authority_projection"]["status"], "ready")

    def test_explicit_projection_renders_model_scope_claims_and_source_links(
        self,
    ) -> None:
        with mock.patch.dict(os.environ, self.projection_environment(), clear=False):
            page, stats, report = self.render_runtime()
        projection = report["authority_projection"]
        self.assertEqual(stats, self.legacy_stats)
        self.assertIn('id="authority-candidate-projection"', page)
        self.assertIn('data-creates-project-facts="false"', page)
        self.assertIn("scope: candidate", page)
        self.assertIn("reconciliation: match", page)
        self.assertIn('href="#adr-0011"', page)
        self.assertIn("docs/core/principles.md", page)
        self.assertEqual(projection["conformance_input"]["fact_scope"], "candidate")
        self.assertEqual(projection["decision_graph"]["status"], "evaluated")
        self.assertFalse(projection["production_behavior_switched"])

    def test_collector_failure_returns_unmodified_legacy_page(self) -> None:
        with mock.patch.object(
            authority_observations,
            "build_cli_authority_contract",
            side_effect=RuntimeError("synthetic collector failure"),
        ):
            with mock.patch.dict(
                os.environ, self.projection_environment(), clear=False
            ):
                page, stats, report = self.render_runtime()
        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        projection = report["authority_projection"]
        self.assertEqual(projection["status"], "unavailable")
        self.assertEqual(projection["error"]["type"], "RuntimeError")
        self.assertNotIn("documents", projection)

    def test_reconciliation_drift_returns_unmodified_legacy_page(self) -> None:
        original_snapshot = authority_observations.authority_observation_snapshot
        calls = 0

        def drifting_snapshot(root: Path) -> str:
            nonlocal calls
            calls += 1
            value = original_snapshot(root)
            if calls == 1:
                return value
            return value.replace("sha256:", "sha256:drift-", 1)

        with mock.patch.object(
            authority_observations,
            "authority_observation_snapshot",
            side_effect=drifting_snapshot,
        ):
            with mock.patch.dict(
                os.environ, self.projection_environment(), clear=False
            ):
                page, stats, report = self.render_runtime()
        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        projection = report["authority_projection"]
        self.assertEqual(projection["status"], "unavailable")
        self.assertEqual(projection["error"]["type"], "AuthorityProjectionError")

    def test_invalid_evidence_visibility_returns_unmodified_legacy_page(self) -> None:
        environment = self.projection_environment()
        environment["ORRERY_AUTHORITY_EVIDENCE_VISIBILITY"] = "invented-evidence"
        with mock.patch.dict(os.environ, environment, clear=False):
            page, stats, report = self.render_runtime()
        self.assertEqual(page, self.legacy_page)
        self.assertEqual(stats, self.legacy_stats)
        self.assertEqual(report["authority_projection"]["status"], "unavailable")

    def test_visibility_is_reconciled_and_hidden_assertions_stay_unknown(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="orrery-observatory-projection-"
        ) as temporary:
            root = Path(temporary)
            self.write_cli_fixture(root)
            bundle = build_cli_authority_contract(
                root,
                fact_scope="candidate",
                evidence_visibility=("revision-content",),
            )
            projection = self.projection_from_bundle(bundle)
        validation = projection["roles"]["validation"][0]
        self.assertEqual(
            projection["conformance_input"]["evidence_visibility"],
            ["revision-content"],
        )
        self.assertEqual(validation["claims"]["validation_evidence"], "unknown")
        self.assertNotIn("validation_assertion", validation["claims"])
        self.assertFalse(validation["evidence_provenance"][0]["visible"])

    def test_legacy_model_fails_closed_to_legacy_reader(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="orrery-observatory-legacy-"
        ) as temporary:
            root = Path(temporary)
            write_file(root, ".project-orrery.json", '{"manifest_format": 1}\n')
            write_file(root, "AGENTS.md", "# Agent\n")
            write_file(root, "docs/core/principles.md", "# Seed\n")
            docs = root / "docs"
            legacy_page, legacy_stats = build_docsite.render_site(
                docs, root / "AGENTS.md", root, self.title
            )
            with mock.patch.dict(
                os.environ, self.projection_environment(), clear=False
            ):
                page, stats, report = authority_projection_site.render_candidate_site(
                    docs, root / "AGENTS.md", root, self.title
                )
        self.assertEqual(page, legacy_page)
        self.assertEqual(stats, legacy_stats)
        self.assertEqual(report["authority_projection"]["status"], "unavailable")
        self.assertNotIn('id="authority-candidate-projection"', page)

    def test_projection_renderer_escapes_bundle_controlled_text(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="orrery-observatory-projection-"
        ) as temporary:
            root = Path(temporary)
            self.write_cli_fixture(root)
            bundle = build_cli_authority_contract(root)
        bundle["documents"][-1]["subject"] = "<script>alert(1)</script>"
        projection = self.projection_from_bundle(bundle)
        panel = authority_projection_site.build_authority_candidate_projection_panel(
            projection
        )
        self.assertNotIn("<script>alert(1)</script>", panel)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", panel)


if __name__ == "__main__":
    unittest.main()
