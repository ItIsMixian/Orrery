from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = (
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
)
for source in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE):
    sys.path.insert(0, str(source))

from project_orrery_cli.context import CliContext, repository_context  # noqa: E402
from project_orrery_cli.update import evaluate, main  # noqa: E402
from project_orrery_core.manifests import ReleaseContract  # noqa: E402


PUBLIC_RELEASE_PATH = (
    REPOSITORY_ROOT / "skills" / "project-orrery" / "release-manifest.json"
)
PUBLISHED_V020_PATH = (
    CORE_SOURCE / "project_orrery_core" / "data" / "release-v0.2.0.json"
)


def load_public_release() -> dict[str, object]:
    value = json.loads(PUBLISHED_V020_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("public release fixture is not an object")
    return value


def future_release() -> dict[str, object]:
    return copy.deepcopy(json.loads(PUBLIC_RELEASE_PATH.read_text(encoding="utf-8")))


def project_manifest(*, model: object = ...) -> dict[str, object]:
    manifest: dict[str, object] = {
        "name": "project-orrery",
        "manifest_format": 1,
        "document_schema": 1,
        "toolchain_version": "0.2.0",
    }
    if model is not ...:
        manifest["authority_model_version"] = model
    return manifest


class AuthorityUpdateCompatibilityTests(unittest.TestCase):
    def test_historical_v020_without_declaration_preserves_update_behavior(self) -> None:
        release = load_public_release()
        result = evaluate(
            release,
            release,
            project_manifest(),
            "fixture",
            None,
        )
        self.assertEqual(result["status"], "up_to_date")
        self.assertFalse(result["migration_required"])
        self.assertEqual(result["reasons"], [])

    def test_future_release_accepts_explicitly_supported_project(self) -> None:
        result = evaluate(
            load_public_release(),
            future_release(),
            project_manifest(model=1),
            "fixture",
            None,
        )
        self.assertEqual(result["status"], "update_available_compatible")
        self.assertFalse(result["migration_required"])
        self.assertEqual(result["reasons"], [])

    def test_future_release_requires_review_for_legacy_project(self) -> None:
        result = evaluate(
            load_public_release(),
            future_release(),
            project_manifest(),
            "fixture",
            None,
        )
        self.assertEqual(result["status"], "update_available_migration_required")
        self.assertTrue(result["migration_required"])
        self.assertIn("legacy-unversioned", result["reasons"][0])
        self.assertIn("explicit-semantic-migration", result["reasons"][0])

    def test_future_release_fails_closed_for_unsupported_project(self) -> None:
        result = evaluate(
            load_public_release(),
            future_release(),
            project_manifest(model=2),
            "fixture",
            None,
        )
        self.assertEqual(result["status"], "update_available_migration_required")
        self.assertTrue(result["migration_required"])
        self.assertIn("unsupported-newer", result["reasons"][0])
        self.assertIn("release supports [1]", result["reasons"][0])

    def test_future_release_reports_an_invalid_selector_without_calling_it_missing(
        self,
    ) -> None:
        result = evaluate(
            load_public_release(),
            future_release(),
            project_manifest(model=True),
            "fixture",
            None,
        )
        self.assertEqual(result["status"], "update_available_migration_required")
        self.assertIn("authority model True is invalid", result["reasons"][0])
        self.assertIn("repair-invalid-field", result["reasons"][0])

    def test_skill_only_update_does_not_invent_a_project_migration(self) -> None:
        result = evaluate(
            load_public_release(),
            future_release(),
            None,
            "fixture",
            None,
        )
        self.assertEqual(result["status"], "update_available_compatible")
        self.assertFalse(result["migration_required"])

    def test_cli_json_uses_existing_contract_for_semantic_migration_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-update-") as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            (target / ".project-orrery.json").write_text(
                json.dumps(project_manifest()), encoding="utf-8"
            )
            manifest_path = root / "future-release.json"
            manifest_path.write_text(
                json.dumps(future_release()), encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                source_context = repository_context()
                historical_context = CliContext(
                    release=ReleaseContract(load_public_release()),
                    authority_root=source_context.authority_root,
                    observatory_root=source_context.observatory_root,
                )
                code = main(
                    [
                        "--target",
                        str(target),
                        "--manifest-file",
                        str(manifest_path),
                        "--json",
                    ],
                    context=historical_context,
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 5)
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["command"], "check-update")
            self.assertEqual(
                payload["data"]["status"],
                "update_available_migration_required",
            )
            self.assertEqual(
                payload["errors"][0]["code"],
                "compatibility_migration_required",
            )
            self.assertIn("legacy-unversioned", payload["data"]["reasons"][0])

    def test_malformed_future_release_fails_before_compatibility_claim(self) -> None:
        malformed = future_release()
        malformed["compatibility"].pop("authority_model_versions")
        with self.assertRaisesRegex(ValueError, "discrete support set"):
            evaluate(
                load_public_release(),
                malformed,
                project_manifest(model=1),
                "fixture",
                None,
            )


if __name__ == "__main__":
    unittest.main()
