from __future__ import annotations

import hashlib
import json
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "brand" / "orrery-brand-contract-v1.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OrreryBrandContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_contract_classifies_brand_technical_protocol_and_history(self) -> None:
        self.assertEqual(self.contract["schema_version"], 1)
        self.assertEqual(self.contract["contract_type"], "orrery-brand-only-contract")
        self.assertEqual(self.contract["current_brand"]["display_name"], "Orrery")
        self.assertEqual(self.contract["current_brand"]["repository"], "ItIsMixian/Orrery")
        self.assertIn("project-orrery", self.contract["stable_technical_ids"]["denylist"])
        self.assertIn("schema $id", self.contract["protocol_ids"]["denylist"])
        self.assertIn("docs/decisions/**", self.contract["historical_facts"]["denylist_globs"])
        self.assertEqual(
            self.contract["historical_facts"]["first_new_release_asset_pattern"],
            "project-orrery-*",
        )

    def test_current_brand_surfaces_use_orrery_and_current_repository(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        docs_readme = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        seed = (ROOT / "docs" / "core" / "principles.md").read_text(encoding="utf-8")
        self.assertIn("# Orrery", readme)
        self.assertIn("# Orrery", readme_zh)
        self.assertIn("https://github.com/ItIsMixian/Orrery", readme)
        self.assertIn("https://github.com/ItIsMixian/Orrery", readme_zh)
        self.assertNotIn("github.com/ItIsMixian/project-orrery", readme + readme_zh)
        self.assertTrue(agents.startswith("# Orrery："))
        self.assertTrue(docs_readme.startswith("# Orrery "))
        self.assertTrue(seed.startswith("# Seed：Orrery "))

    def test_default_self_host_display_and_target_title_projection_are_separate(self) -> None:
        default_title = self.contract["current_brand"]["default_observatory_title"]
        for relative in (
            "scripts/docsite/build_docsite.py",
            "scripts/docsite/build_authority_projection.py",
            "scripts/docsite/build_personal_observatory.py",
            "scripts/docsite/build_workstream_relation_graph.py",
            "scripts/docsite/serve.py",
            "scripts/docsite/serve_team_observatory.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(default_title, text, relative)
            self.assertNotIn("Project Orrery · Documentation", text, relative)

        component = json.loads(
            (ROOT / "packages/project-orrery-observatory/src/project_orrery_observatory/component.json").read_text(
                encoding="utf-8"
            )
        )
        expected_projection = self.contract["target_project_title"]["required_projection"]
        for replacements in component["template_projection"].values():
            self.assertEqual(replacements[default_title], expected_projection)

        for relative in self.contract["target_project_title"]["protected_paths"]:
            self.assertIn(
                self.contract["target_project_title"]["token"],
                (ROOT / relative).read_text(encoding="utf-8"),
                relative,
            )

        broker = (ROOT / "scripts/docsite/llm_broker.py").read_text(encoding="utf-8")
        template_broker = (
            ROOT / "skills/project-orrery/assets/project-template/scripts/docsite/llm_broker.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Orrery Broker:", broker)
        self.assertIn("Orrery Broker:", template_broker)
        self.assertNotIn("Project Orrery Broker:", broker + template_broker)

    def test_display_metadata_changes_without_identity_alias_or_duplicate_implementation(self) -> None:
        expected = {
            "codex": ("project-orrery-codex", "Orrery Codex Adapter"),
            "claude-code": ("project-orrery-claude-code", "Orrery Claude Code Adapter"),
            "deepseek-harness": (
                "project-orrery-deepseek-harness",
                "Orrery DeepSeek Harness Adapter",
            ),
        }
        for adapter, (identity, display_name) in expected.items():
            manifest = json.loads(
                (ROOT / "adapters" / adapter / "adapter-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["adapter"]["id"], identity)
            self.assertEqual(manifest["adapter"]["name"], display_name)

        harness = json.loads(
            (ROOT / "adapters/harness-json/adapter-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(harness["adapter"]["name"], "Orrery Harness JSON Adapter")
        self.assertEqual(harness["adapter"]["distribution"], "project-orrery-harness-json-adapter")
        self.assertEqual(
            harness["workstream_capabilities"]["adapter_id"],
            "project-orrery-harness-json",
        )
        self.assertTrue(
            (ROOT / "adapters/harness-json/README.md")
            .read_text(encoding="utf-8")
            .startswith("# Orrery Harness JSON Adapter")
        )
        harness_runner = (ROOT / "adapters/harness-json/run_harness.py").read_text(encoding="utf-8")
        self.assertIn("Invoke the Orrery CLI through JSON only.", harness_runner)
        self.assertIn("Project Orrery CLI timed out", harness_runner)

        skill = (ROOT / "skills/project-orrery/SKILL.md").read_text(encoding="utf-8")
        codex_skill = (ROOT / "adapters/codex/SKILL.md").read_text(encoding="utf-8")
        claude_plugin = json.loads(
            (ROOT / "adapters/claude-code/.claude-plugin/plugin.json").read_text(encoding="utf-8")
        )
        deepseek_package = json.loads(
            (ROOT / "adapters/deepseek-harness/package.json").read_text(encoding="utf-8")
        )
        self.assertTrue(skill.startswith("---\nname: project-orrery\n"))
        self.assertTrue(codex_skill.startswith("---\nname: project-orrery\n"))
        self.assertEqual(claude_plugin["name"], "project-orrery")
        self.assertEqual(deepseek_package["name"], "project-orrery-deepseek-harness-adapter")

    def test_python_distributions_imports_cli_and_project_manifest_remain_stable(self) -> None:
        expected_packages = {
            "project-orrery-core": "project_orrery_core",
            "project-orrery-cli": "project_orrery_cli",
            "project-orrery-observatory": "project_orrery_observatory",
        }
        for distribution, import_name in expected_packages.items():
            project = tomllib.loads((ROOT / "packages" / distribution / "pyproject.toml").read_text(encoding="utf-8"))
            self.assertEqual(project["project"]["name"], distribution)
            self.assertTrue((ROOT / "packages" / distribution / "src" / import_name).is_dir())

        cli = tomllib.loads((ROOT / "packages/project-orrery-cli/pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("project-orrery", cli["project"]["scripts"])
        self.assertNotIn("orrery", cli["project"]["scripts"])
        manifest = json.loads((ROOT / ".project-orrery.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "project-orrery")

    def test_protocol_and_historical_hash_denylists_are_unchanged(self) -> None:
        protected = {}
        protected.update(self.contract["protocol_ids"]["immutable_schema_sha256"])
        protected.update(self.contract["historical_facts"]["immutable_sha256"])
        for relative, expected_hash in protected.items():
            self.assertEqual(_sha256(ROOT / relative), expected_hash, relative)

        baseline = json.loads(
            (ROOT / "tests/fixtures/platform_neutral_phase0_baseline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            baseline["published_release"]["archive_sha256"],
            self.contract["historical_facts"]["published_v0_2_0_archive_sha256"],
        )
        serve = (ROOT / "scripts/docsite/serve.py").read_text(encoding="utf-8")
        broker = (ROOT / "scripts/docsite/llm_broker.py").read_text(encoding="utf-8")
        self.assertIn("ORRERY_SETTINGS_TOKEN", serve)
        self.assertIn("X-Orrery-Settings-Token", serve)
        self.assertIn('BROKER_NAMESPACE = "project-orrery-broker/provider"', broker)
        self.assertIn('BROKER_TOKEN_SERVICE = "project-orrery-broker/access"', broker)


if __name__ == "__main__":
    unittest.main()
