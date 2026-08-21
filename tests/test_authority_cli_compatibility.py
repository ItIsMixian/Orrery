from __future__ import annotations

import contextlib
import io
import json
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

from project_orrery_cli.context import repository_context  # noqa: E402
from project_orrery_cli.validate import parse_args, run  # noqa: E402
from project_orrery_core import REQUIRED_SCAFFOLD_FILES  # noqa: E402


def write_integrated_scaffold(root: Path, *, model: object = ...) -> None:
    for relative in REQUIRED_SCAFFOLD_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    (root / "AGENTS.md").write_text(
        "docs/HANDOFF.md docs/PROGRESS.md docs/state/\n", encoding="utf-8"
    )
    (root / "docs" / "PROGRESS.md").write_text("integrated\n", encoding="utf-8")
    (root / "docs" / "decisions" / "0001-fixture.md").write_text(
        "# ADR-0001: Fixture\n\nStatus: Accepted\n", encoding="utf-8"
    )
    (root / ".gitignore").write_text(
        "docs/_site/\nscripts/docsite/.doccache.json\nscripts/docsite/.port\n"
        "ai-config.json\n.project-orrery-backup/\n",
        encoding="utf-8",
    )
    manifest: dict[str, object] = {
        "name": "project-orrery",
        "manifest_format": 1,
        "document_schema": 1,
        "toolchain_status": "current",
        "toolchain_version": "test",
    }
    if model is not ...:
        manifest["authority_model_version"] = model
    (root / ".project-orrery.json").write_text(json.dumps(manifest), encoding="utf-8")


def run_json(root: Path, *extra: str) -> tuple[int, dict]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = run(
            parse_args(["--target", str(root), "--json", *extra]),
            repository_context(),
        )
    return code, json.loads(output.getvalue())


class AuthorityCliCompatibilityTests(unittest.TestCase):
    def test_supported_model_is_reported_as_eligible_without_claiming_conformance(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-model-") as temporary:
            root = Path(temporary)
            write_integrated_scaffold(root, model=1)
            code, payload = run_json(root, "--require-integrated")
            self.assertEqual(code, 0)
            capability = payload["data"]["authority_model"]
            self.assertEqual(capability["status"], "supported")
            self.assertEqual(capability["strict_conformance_eligibility"], "eligible")
            self.assertNotIn("passed", json.dumps(capability))

    def test_unversioned_model_remains_readable_but_strict_validation_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-model-") as temporary:
            root = Path(temporary)
            write_integrated_scaffold(root)
            relaxed_code, relaxed = run_json(root)
            strict_code, strict = run_json(root, "--require-integrated")
            self.assertEqual(relaxed_code, 0)
            self.assertEqual(
                relaxed["data"]["authority_model"]["status"], "legacy-unversioned"
            )
            self.assertIn(
                "authority_model_legacy_unversioned",
                [item["code"] for item in relaxed["warnings"]],
            )
            self.assertNotIn(
                "authority_shadow_mismatch",
                [item["code"] for item in relaxed["warnings"]],
            )
            self.assertEqual(strict_code, 4)
            self.assertIn(
                "authority_model_required",
                [item["code"] for item in strict["errors"]],
            )

    def test_unknown_and_invalid_models_fail_closed_with_read_only_report(self) -> None:
        for selected in (99, True):
            with self.subTest(selected=selected):
                with tempfile.TemporaryDirectory(
                    prefix="orrery-cli-model-"
                ) as temporary:
                    root = Path(temporary)
                    write_integrated_scaffold(root, model=selected)
                    code, payload = run_json(root)
                    self.assertEqual(code, 4)
                    capability = payload["data"]["authority_model"]
                    self.assertEqual(capability["read_only_browsing"], "available")
                    self.assertEqual(
                        capability["authority_evaluation_capability"], "unavailable"
                    )
                    self.assertTrue(capability["must_not_infer"])

    def test_shadow_mismatch_is_a_structured_json_warning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-model-") as temporary:
            root = Path(temporary)
            write_integrated_scaffold(root, model=1)
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
            with mock.patch(
                "project_orrery_cli.validate.build_authority_shadow",
                return_value=mismatch,
            ):
                code, payload = run_json(root)
            self.assertEqual(code, 0)
            self.assertEqual(
                payload["warnings"][0]["code"], "authority_shadow_mismatch"
            )
            self.assertIn("differences", payload["warnings"][0]["details"])


if __name__ == "__main__":
    unittest.main()
