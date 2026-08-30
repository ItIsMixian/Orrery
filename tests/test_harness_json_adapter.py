from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
import uuid
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "harness-json"
HARNESS = ADAPTER_ROOT / "run_harness.py"
MANIFEST = ADAPTER_ROOT / "adapter-manifest.json"
REQUEST_SCHEMA = ADAPTER_ROOT / "schemas" / "request-v1.schema.json"
RESPONSE_SCHEMA = ADAPTER_ROOT / "schemas" / "response-v1.schema.json"
REQUEST_FIXTURE = REPOSITORY_ROOT / "tests" / "fixtures" / "harness-json" / "scaffold-dry-run-v1.json"
COMPONENT_VERSIONS = REPOSITORY_ROOT / "packages" / "component-versions.json"
RELEASE_MANIFEST = REPOSITORY_ROOT / "skills" / "project-orrery" / "release-manifest.json"
PACKAGE_SOURCES = (
    REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src",
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src",
    REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src",
)


def run_harness(request: dict, *, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-X", "utf8", str(HARNESS)]
    for source in PACKAGE_SOURCES:
        command.extend(("--python-path", str(source)))
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        input=json.dumps(request),
        env=environment,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class HarnessJsonAdapterTests(unittest.TestCase):
    def assert_response(self, completed: subprocess.CompletedProcess[str], expected_code: int) -> dict:
        self.assertEqual(completed.returncode, expected_code, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(payload), set(schema["required"]))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["exit_code"], completed.returncode)
        self.assertIn(payload["status"], schema["properties"]["status"]["enum"])
        self.assertIn(payload["exit_code"], schema["properties"]["exit_code"]["enum"])
        self.assertEqual(set(payload["versions"]), {"core", "core_api", "cli"})
        for field in ("warnings", "errors"):
            for item in payload[field]:
                self.assertTrue({"code", "message"}.issubset(item))
        return payload

    def test_manifest_schemas_versions_and_platform_isolation_are_consistent(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        components = json.loads(COMPONENT_VERSIONS.read_text(encoding="utf-8"))
        request_schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        response_schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
        pyproject = tomllib.loads(
            (REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "pyproject.toml").read_text(encoding="utf-8")
        )
        harness_component = components["adapters"]["harness-json"]

        self.assertEqual(manifest["adapter"]["support_status"], "experimental")
        self.assertEqual(manifest["adapter"]["version"], harness_component["version"])
        self.assertEqual(manifest["dependencies"]["cli"]["minimum"], "0.1.1")
        self.assertEqual(pyproject["project"]["version"], components["components"]["cli"]["version"])
        self.assertEqual(request_schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(response_schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            set(response_schema["$defs"]),
            {"operating_rules_data", "authority_route_data", "issue", "action", "scaffold_data", "validate_data", "update_data"},
        )
        self.assertEqual(len(response_schema["allOf"]), 5)
        self.assertEqual(
            set(response_schema["properties"]["exit_code"]["enum"]),
            {int(code) for code in manifest["protocol"]["exit_codes"]},
        )
        self.assertFalse(manifest["isolation"]["loads_skill_md"])
        self.assertFalse(manifest["isolation"]["loads_codex_config"])
        self.assertFalse(manifest["isolation"]["invokes_agent_runtime"])
        self.assertFalse((ADAPTER_ROOT / "SKILL.md").exists())
        self.assertFalse(any(path.name == "SKILL.md" for path in ADAPTER_ROOT.rglob("*")))
        self.assertEqual(manifest["runtime_evidence"], [])

    def test_scaffold_fixture_dry_run_is_deterministic_and_write_free(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-harness-dry-run-") as temporary:
            target = Path(temporary) / "target"
            request = json.loads(REQUEST_FIXTURE.read_text(encoding="utf-8"))
            request["arguments"]["target"] = str(target)
            first = self.assert_response(run_harness(request), 0)
            second = self.assert_response(run_harness(request), 0)
            self.assertEqual(first, second)
            self.assertEqual(first["command"], "scaffold")
            self.assertTrue(first["data"]["dry_run"])
            self.assertFalse(first["data"]["changed"])
            self.assertGreater(first["data"]["predicted_changes"], 0)
            self.assertIn("create", {item["action"] for item in first["data"]["actions"]})
            self.assertFalse(target.exists())

    def test_operating_rules_and_authority_preflight_are_read_only_harness_commands(self) -> None:
        inspected = self.assert_response(
            run_harness({
                "schema_version": 1,
                "command": "operating-rules-inspect",
                "arguments": {"inventory_version": 1},
            }),
            0,
        )
        self.assertTrue(inspected["data"]["read_only"])
        self.assertEqual(inspected["data"]["inventory"]["inventory_id"], "orrery-operating-rules-v1")
        receipt = self.assert_response(
            run_harness({
                "schema_version": 1,
                "command": "authority-route-preflight",
                "arguments": {
                    "target": str(REPOSITORY_ROOT),
                    "query": "Why are existing authority rules absent from the Skill?",
                    "fact_scope": "candidate",
                },
            }),
            0,
        )
        self.assertIn("authority-meta-model", receipt["data"]["selection"]["concept_ids"])
        self.assertFalse(receipt["data"]["guarantees"]["writes_target_project"])
        self.assertFalse(receipt["data"]["novelty_absence_gate"]["absence_claim_allowed"])

    def test_install_validate_and_preserve_author_files_without_agent_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-harness-install-") as temporary:
            root = Path(temporary)
            target = root / "target"
            fake_codex_home = root / "codex-home"
            fake_agents_home = root / "agents-home"
            fake_codex_home.mkdir()
            fake_agents_home.mkdir()
            (fake_codex_home / "config.toml").write_text('secret = "must-not-appear"\n', encoding="utf-8")
            (fake_agents_home / "SKILL.md").write_text("must not load\n", encoding="utf-8")
            environment = dict(os.environ)
            environment.update(
                {
                    "CODEX_HOME": str(fake_codex_home),
                    "AGENTS_HOME": str(fake_agents_home),
                    "OPENAI_API_KEY": "must-not-appear",
                }
            )

            installed = self.assert_response(
                run_harness(
                    {
                        "schema_version": 1,
                        "command": "scaffold",
                        "arguments": {"target": str(target), "title": "Harness Install"},
                    },
                    environment=environment,
                ),
                0,
            )
            self.assertTrue(installed["data"]["changed"])
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertNotIn("must-not-appear", json.dumps(installed))

            validated = self.assert_response(
                run_harness(
                    {"schema_version": 1, "command": "validate", "arguments": {"target": str(target)}},
                    environment=environment,
                ),
                0,
            )
            self.assertTrue(validated["data"]["valid"])
            self.assertFalse(validated["data"]["integrated"])

            authored = target / "AGENTS.md"
            authored.write_text("# Author-owned entrance\n", encoding="utf-8")
            preserved = self.assert_response(
                run_harness(
                    {
                        "schema_version": 1,
                        "command": "scaffold",
                        "arguments": {"target": str(target), "title": "Harness Install", "dry_run": True},
                    },
                    environment=environment,
                ),
                0,
            )
            self.assertIn("AGENTS.md", preserved["data"]["preserved_authored_paths"])
            self.assertEqual(authored.read_text(encoding="utf-8"), "# Author-owned entrance\n")
            self.assertEqual((fake_codex_home / "config.toml").read_text(encoding="utf-8"), 'secret = "must-not-appear"\n')
            self.assertEqual((fake_agents_home / "SKILL.md").read_text(encoding="utf-8"), "must not load\n")

    def test_new_project_exposes_two_layers_and_brownfield_seed_state_are_byte_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-two-layer-install-") as temporary:
            root = Path(temporary)
            new_target = root / "new"
            installed = self.assert_response(
                run_harness({
                    "schema_version": 1, "command": "scaffold",
                    "arguments": {"target": str(new_target), "title": "Two Layers"},
                }),
                0,
            )
            self.assertTrue(installed["data"]["changed"])
            entrance = (new_target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Orrery 工作规则", entrance)
            self.assertIn("项目 Seed", entrance)
            self.assertIn("两层", entrance)

            brownfield = root / "brownfield"
            (brownfield / "docs" / "core").mkdir(parents=True)
            (brownfield / "docs" / "state").mkdir(parents=True)
            seed_path = brownfield / "docs" / "core" / "principles.md"
            state_path = brownfield / "docs" / "state" / "custom.md"
            agents_path = brownfield / "AGENTS.md"
            seed_bytes = b"# Author Seed\r\n\r\n\xff-owned-by-author\r\n"
            state_bytes = b"# Author State\r\ncurrent=unknown\r\n"
            agents_bytes = b"# Author AGENTS\r\n"
            seed_path.write_bytes(seed_bytes)
            state_path.write_bytes(state_bytes)
            agents_path.write_bytes(agents_bytes)
            first = self.assert_response(
                run_harness({
                    "schema_version": 1, "command": "scaffold",
                    "arguments": {"target": str(brownfield), "title": "Brownfield"},
                }),
                0,
            )
            self.assertIn("docs/core/principles.md", first["data"]["preserved_authored_paths"])
            self.assertEqual(seed_path.read_bytes(), seed_bytes)
            self.assertEqual(state_path.read_bytes(), state_bytes)
            self.assertEqual(agents_path.read_bytes(), agents_bytes)
            upgraded = self.assert_response(
                run_harness({
                    "schema_version": 1, "command": "scaffold",
                    "arguments": {
                        "target": str(brownfield), "title": "Brownfield",
                        "upgrade_tools": True,
                    },
                }),
                0,
            )
            self.assertIn("docs/core/principles.md", upgraded["data"]["preserved_authored_paths"])
            self.assertEqual(seed_path.read_bytes(), seed_bytes)
            self.assertEqual(state_path.read_bytes(), state_bytes)
            self.assertEqual(agents_path.read_bytes(), agents_bytes)

    def test_mixed_toolchain_is_a_structured_warning_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-harness-mixed-") as temporary:
            target = Path(temporary) / "target"
            custom_tool = target / "scripts" / "docsite" / "serve.py"
            custom_tool.parent.mkdir(parents=True)
            custom_tool.write_text("# author tool\n", encoding="utf-8")
            payload = self.assert_response(
                run_harness(
                    {
                        "schema_version": 1,
                        "command": "scaffold",
                        "arguments": {"target": str(target), "title": "Mixed Toolchain"},
                    }
                ),
                0,
            )
            self.assertEqual(payload["status"], "warning")
            self.assertEqual(payload["warnings"][0]["code"], "mixed_toolchain")
            self.assertEqual(payload["data"]["toolchain_status"], "mixed")
            self.assertIn("scripts/docsite/serve.py", payload["data"]["managed_tool_conflicts"])
            self.assertEqual(custom_tool.read_text(encoding="utf-8"), "# author tool\n")

            preview = self.assert_response(
                run_harness(
                    {
                        "schema_version": 1,
                        "command": "scaffold",
                        "arguments": {
                            "target": str(target),
                            "title": "Mixed Toolchain",
                            "upgrade_tools": True,
                            "dry_run": True,
                        },
                    }
                ),
                0,
            )
            actions = preview["data"]["actions"]
            self.assertIn("backup", {item["action"] for item in actions})
            self.assertIn("upgrade", {item["action"] for item in actions})
            upgrade = next(item for item in actions if item["action"] == "upgrade" and item["path"] == "scripts/docsite/serve.py")
            self.assertTrue(upgrade["backup_path"].startswith(".project-orrery-backup/"))
            self.assertFalse((target / ".project-orrery-backup").exists())
            self.assertEqual(custom_tool.read_text(encoding="utf-8"), "# author tool\n")

    def test_schema_incompatibility_fails_closed_for_validate_and_update(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-harness-schema-") as temporary:
            target = Path(temporary) / "target"
            installed = self.assert_response(
                run_harness(
                    {
                        "schema_version": 1,
                        "command": "scaffold",
                        "arguments": {"target": str(target), "title": "Future Schema"},
                    }
                ),
                0,
            )
            self.assertEqual(installed["status"], "ok")
            manifest_path = target / ".project-orrery.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["document_schema"] = 99
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            validated = self.assert_response(
                run_harness(
                    {"schema_version": 1, "command": "validate", "arguments": {"target": str(target)}}
                ),
                4,
            )
            self.assertIn("document_schema_unsupported", {item["code"] for item in validated["errors"]})

            checked = self.assert_response(
                run_harness(
                    {
                        "schema_version": 1,
                        "command": "check-update",
                        "arguments": {"target": str(target), "manifest_file": str(RELEASE_MANIFEST)},
                    }
                ),
                5,
            )
            self.assertEqual(checked["data"]["status"], "current_incompatible")
            self.assertEqual(checked["errors"][0]["code"], "compatibility_migration_required")

    def test_offline_update_without_cache_and_invalid_request_have_stable_failures(self) -> None:
        unique_url = f"https://offline-{uuid.uuid4().hex}.invalid/release.json"
        offline = self.assert_response(
            run_harness(
                {
                    "schema_version": 1,
                    "command": "check-update",
                    "arguments": {"manifest_url": unique_url, "offline": True},
                }
            ),
            6,
        )
        self.assertEqual(offline["data"]["source"], "offline")
        self.assertEqual(offline["errors"][0]["code"], "update_unavailable")

        invalid = self.assert_response(
            run_harness(
                {
                    "schema_version": 1,
                    "command": "validate",
                    "arguments": {"target": ".", "arbitrary_cli_argument": "forbidden"},
                }
            ),
            2,
        )
        self.assertEqual(invalid["command"], "harness")
        self.assertEqual(invalid["errors"][0]["code"], "invalid_request")


if __name__ == "__main__":
    unittest.main()
