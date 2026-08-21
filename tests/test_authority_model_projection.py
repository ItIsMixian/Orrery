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
from project_orrery_cli.scaffold import parse_args, run  # noqa: E402
from project_orrery_core.manifests import (  # noqa: E402
    ReleaseContract,
    build_project_manifest,
    default_release_contract,
)


FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "authority-meta-model"
    / "v1"
    / "projection.json"
)
PROJECT_SCHEMA_PATH = (
    CORE_SOURCE / "project_orrery_core" / "schema" / "project-manifest-v1.json"
)
PUBLIC_RELEASE_PATH = (
    REPOSITORY_ROOT / "skills" / "project-orrery" / "release-manifest.json"
)
BUNDLED_V020_PATH = (
    CORE_SOURCE / "project_orrery_core" / "data" / "release-v0.2.0.json"
)


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"fixture is not an object: {path}")
    return value


class AuthorityModelReleaseProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_object(FIXTURE_PATH)
        cls.release_payload = cls.fixture["candidate_release"]
        cls.release = ReleaseContract(cls.release_payload)

    def test_fixture_freezes_default_support_and_orthogonal_versions(self) -> None:
        self.assertEqual(self.fixture["fixture_id"], "amm-release-projection-v1")
        self.assertEqual(self.fixture["public_authority_model_version"], 1)
        self.assertEqual(self.release.authority_model_version, 1)
        self.assertEqual(self.release.supported_authority_model_versions, (1,))
        expected = self.fixture["expected"]
        self.assertFalse(expected["manifest_format_changes"])
        self.assertFalse(expected["document_schema_changes"])
        self.assertFalse(expected["ordinary_tool_upgrade_selects_model"])
        self.assertFalse(expected["published_v0_2_0_is_rewritten"])

    def test_release_contract_rejects_unpaired_or_invalid_model_declarations(self) -> None:
        base = copy.deepcopy(self.release_payload)
        cases: list[dict[str, object]] = []

        missing_default = copy.deepcopy(base)
        missing_default.pop("authority_model_version")
        cases.append(missing_default)

        missing_support = copy.deepcopy(base)
        missing_support["compatibility"].pop("authority_model_versions")
        cases.append(missing_support)

        unsupported_default = copy.deepcopy(base)
        unsupported_default["authority_model_version"] = 2
        cases.append(unsupported_default)

        duplicate_support = copy.deepcopy(base)
        duplicate_support["compatibility"]["authority_model_versions"][
            "supported"
        ] = [1, 1]
        cases.append(duplicate_support)

        boolean_default = copy.deepcopy(base)
        boolean_default["authority_model_version"] = True
        cases.append(boolean_default)

        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    ReleaseContract(payload)

    def test_project_manifest_schema_keeps_model_optional_but_validates_presence(self) -> None:
        schema = load_object(PROJECT_SCHEMA_PATH)
        self.assertNotIn("authority_model_version", schema["required"])
        self.assertEqual(
            schema["properties"]["authority_model_version"],
            {"type": "integer", "minimum": 1},
        )

    def test_new_project_manifest_selects_candidate_release_default(self) -> None:
        manifest = build_project_manifest(
            {},
            release=self.release,
            title="New project",
            today="2026-08-21",
            toolchain_version=self.release.version,
            toolchain_status="current",
            managed_tools=[],
            expected_tool_hashes={},
        )
        self.assertEqual(manifest["authority_model_version"], 1)
        self.assertEqual(manifest["manifest_format"], 1)
        self.assertEqual(manifest["document_schema"], 1)
        self.assertEqual(manifest["authority_status"], "migration_pending")

    def test_existing_legacy_manifest_preserves_missing_selector(self) -> None:
        existing = {
            "name": "project-orrery",
            "manifest_format": 1,
            "document_schema": 1,
            "authority_status": "migration_pending",
        }
        manifest = build_project_manifest(
            existing,
            release=self.release,
            title="Legacy project",
            today="2026-08-21",
            toolchain_version=self.release.version,
            toolchain_status="current",
            managed_tools=[],
            expected_tool_hashes={},
        )
        self.assertNotIn("authority_model_version", manifest)

    def test_existing_explicit_model_is_preserved(self) -> None:
        existing = {
            "name": "project-orrery",
            "manifest_format": 1,
            "document_schema": 1,
            "authority_model_version": 1,
            "authority_status": "integrated",
        }
        manifest = build_project_manifest(
            existing,
            release=self.release,
            title="Versioned project",
            today="2026-08-21",
            toolchain_version=self.release.version,
            toolchain_status="current",
            managed_tools=[],
            expected_tool_hashes={},
        )
        self.assertEqual(manifest["authority_model_version"], 1)

    def test_scaffold_upgrade_tools_does_not_migrate_legacy_project(self) -> None:
        source_context = repository_context()
        context = CliContext(
            release=self.release,
            authority_root=source_context.authority_root,
            observatory_root=source_context.observatory_root,
        )
        with tempfile.TemporaryDirectory(prefix="orrery-model-projection-") as temporary:
            root = Path(temporary)
            legacy = {
                "name": "project-orrery",
                "manifest_format": 1,
                "document_schema": 1,
                "authority_status": "migration_pending",
            }
            (root / ".project-orrery.json").write_text(
                json.dumps(legacy, indent=2) + "\n", encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = run(
                    parse_args(
                        [
                            "--target",
                            str(root),
                            "--upgrade-tools",
                            "--json",
                        ]
                    ),
                    context,
                )
            self.assertEqual(code, 0)
            manifest = load_object(root / ".project-orrery.json")
            self.assertNotIn("authority_model_version", manifest)

    def test_published_v020_contracts_remain_historical_and_unversioned(self) -> None:
        public = load_object(PUBLIC_RELEASE_PATH)
        bundled = load_object(BUNDLED_V020_PATH)
        for payload in (public, bundled):
            with self.subTest(source=payload.get("version")):
                self.assertEqual(payload["version"], "0.2.0")
                self.assertNotIn("authority_model_version", payload)
                self.assertNotIn(
                    "authority_model_versions", payload["compatibility"]
                )
        release = default_release_contract()
        self.assertIsNone(release.authority_model_version)
        self.assertEqual(release.supported_authority_model_versions, ())


if __name__ == "__main__":
    unittest.main()
