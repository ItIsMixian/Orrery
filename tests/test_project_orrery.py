from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import unittest
import urllib.error
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "project-orrery"
INSTALLER = SKILL_ROOT / "scripts" / "install_project_orrery.py"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_installation.py"
UPDATE_CHECKER = SKILL_ROOT / "scripts" / "check_project_orrery_update.py"
RELEASE_MANIFEST = SKILL_ROOT / "release-manifest.json"
PACKAGER = REPOSITORY_ROOT / "scripts" / "package_release.py"
PHASE0_BASELINE = REPOSITORY_ROOT / "tests" / "fixtures" / "platform_neutral_phase0_baseline.json"
COMPONENT_VERSIONS = REPOSITORY_ROOT / "packages" / "component-versions.json"
CORE_ROOT = REPOSITORY_ROOT / "packages" / "project-orrery-core"
CLI_ROOT = REPOSITORY_ROOT / "packages" / "project-orrery-cli"
OBSERVATORY_ROOT = REPOSITORY_ROOT / "packages" / "project-orrery-observatory"
PACKAGE_SOURCES = (CORE_ROOT / "src", OBSERVATORY_ROOT / "src", CLI_ROOT / "src")
CURRENT_VERSION = str(json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))["version"])


def run_python(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(script), *arguments],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_neutral_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    source_path = os.pathsep.join(str(path) for path in PACKAGE_SOURCES)
    if environment.get("PYTHONPATH"):
        source_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = source_path
    return subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", *arguments],
        cwd=REPOSITORY_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def read_json_url(request: urllib.request.Request | str) -> dict:
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class ProjectOrreryTests(unittest.TestCase):
    def test_skill_frontmatter_has_only_trigger_metadata(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(?P<header>.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md needs YAML frontmatter")
        header = match.group("header")
        keys = [line.split(":", 1)[0].strip() for line in header.splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: project-orrery", header)
        self.assertIn("Install, migrate, audit, and maintain", header)

    def test_phase0_published_contract_inventory_is_preserved(self) -> None:
        baseline = json.loads(PHASE0_BASELINE.read_text(encoding="utf-8"))
        published = baseline["published_release"]
        self.assertEqual(published["version"], "0.2.0")
        self.assertEqual(published["tag"], "v0.2.0")
        self.assertEqual(
            published["archive_sha256"],
            "13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394",
        )
        self.assertEqual(published["archive_entry_count"], len(published["skill_paths"]))

        current_skill_paths = {
            path.relative_to(SKILL_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
        }
        self.assertTrue(set(published["skill_paths"]).issubset(current_skill_paths))
        packaged_managed_tools = {f"assets/project-template/{path}" for path in published["managed_tools"]}
        self.assertTrue(packaged_managed_tools.issubset(current_skill_paths))
        self.assertTrue(set(baseline["cli_entrypoints"].values()).issubset(current_skill_paths))

        release_manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(set(baseline["release_manifest_required_fields"]).issubset(release_manifest))

        for readme_name, markers in baseline["public_support_markers"].items():
            readme = (REPOSITORY_ROOT / readme_name).read_text(encoding="utf-8")
            for marker in markers:
                self.assertIn(marker, readme)

    def test_phase0_human_cli_output_and_template_entry_are_stable(self) -> None:
        baseline = json.loads(PHASE0_BASELINE.read_text(encoding="utf-8"))
        fragments = baseline["human_output_fragments"]
        with tempfile.TemporaryDirectory(prefix="project-orrery-phase0-") as temporary:
            target = Path(temporary) / "target"
            preview = run_python(
                INSTALLER,
                "--target",
                str(target),
                "--title",
                "Orrery Baseline",
                "--dry-run",
            )
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            for fragment in fragments["installer_dry_run"]:
                self.assertIn(fragment, preview.stdout)

            installed = run_python(
                INSTALLER,
                "--target",
                str(target),
                "--title",
                "Orrery Baseline",
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            agents_heading = (target / "AGENTS.md").read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(agents_heading, baseline["template_agent_heading"])

            project_manifest = json.loads((target / ".project-orrery.json").read_text(encoding="utf-8"))
            self.assertTrue(set(baseline["project_manifest_required_fields"]).issubset(project_manifest))
            self.assertTrue(
                set(baseline["published_release"]["managed_tools"]).issubset(project_manifest["managed_tools"])
            )

            validated = run_python(VALIDATOR, "--target", str(target))
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            for fragment in fragments["validator"]:
                self.assertIn(fragment, validated.stdout)

            checked = run_python(
                UPDATE_CHECKER,
                "--target",
                str(target),
                "--manifest-file",
                str(RELEASE_MANIFEST),
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            for fragment in fragments["update_checker"]:
                self.assertIn(fragment, checked.stdout)

    def test_phase1_component_boundaries_and_compatibility_projection(self) -> None:
        versions = json.loads(COMPONENT_VERSIONS.read_text(encoding="utf-8"))
        self.assertEqual(versions["status"], "unreleased")
        self.assertEqual(versions["legacy_compatibility"]["wrapper_supported_through"], "0.3.x")
        for name, root in (("core", CORE_ROOT), ("cli", CLI_ROOT), ("observatory", OBSERVATORY_ROOT)):
            pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
            self.assertEqual(pyproject["project"]["version"], versions["components"][name]["version"])

        core_release = json.loads(
            (CORE_ROOT / "src" / "project_orrery_core" / "data" / "release-v0.3.0.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(core_release, json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8")))
        self.assertEqual(core_release["status"], "release-candidate")
        self.assertIsNone(core_release["released"])

        canonical_root = CORE_ROOT / "src" / "project_orrery_core" / "templates" / "authority"
        compatibility_root = SKILL_ROOT / "assets" / "project-template"
        canonical_paths = {
            path.relative_to(canonical_root).as_posix()
            for path in canonical_root.rglob("*")
            if path.is_file()
        }
        self.assertIn("AGENTS.md", canonical_paths)
        for relative in canonical_paths:
            canonical = (canonical_root / relative).read_text(encoding="utf-8").replace("\r\n", "\n")
            compatibility = (compatibility_root / relative).read_text(encoding="utf-8").replace("\r\n", "\n")
            self.assertEqual(canonical, compatibility, relative)

        observatory = json.loads(
            (OBSERVATORY_ROOT / "src" / "project_orrery_observatory" / "component.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(observatory["version"], versions["components"]["observatory"]["version"])
        self.assertIn("scripts/docsite/llm_broker.py", observatory["managed_tools"])
        for relative in observatory["managed_tools"]:
            self.assertTrue((REPOSITORY_ROOT / relative).is_file(), relative)
            self.assertTrue((compatibility_root / relative).is_file(), relative)
        self.assertEqual(len(observatory["managed_runtime"]), 102)
        for relative in observatory["managed_runtime"]:
            self.assertTrue((REPOSITORY_ROOT / relative).is_file(), relative)

        for name in ("install_project_orrery.py", "validate_installation.py", "check_project_orrery_update.py"):
            wrapper = (SKILL_ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn("project_orrery_cli", wrapper)
            self.assertLess(len(wrapper), 2000)
            self.assertTrue((SKILL_ROOT / "scripts" / f"_legacy_{name}").is_file())

    def test_phase1_neutral_cli_matches_legacy_paths_and_preserves_authored_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-phase1-") as temporary:
            root = Path(temporary)
            skill_target = root / "skill-entry"
            neutral_target = root / "neutral-entry"
            title = "Phase One Equivalence"
            legacy = run_python(INSTALLER, "--target", str(skill_target), "--title", title)
            neutral = run_neutral_cli("scaffold", "--target", str(neutral_target), "--title", title)
            self.assertEqual(legacy.returncode, 0, legacy.stdout + legacy.stderr)
            self.assertEqual(neutral.returncode, 0, neutral.stdout + neutral.stderr)
            self.assertEqual(
                legacy.stdout.replace(str(skill_target.resolve()), "<target>"),
                neutral.stdout.replace(str(neutral_target.resolve()), "<target>"),
            )

            skill_files = {
                path.relative_to(skill_target).as_posix()
                for path in skill_target.rglob("*")
                if path.is_file()
            }
            neutral_files = {
                path.relative_to(neutral_target).as_posix()
                for path in neutral_target.rglob("*")
                if path.is_file()
            }
            self.assertEqual(skill_files, neutral_files)
            for relative in skill_files:
                self.assertEqual((skill_target / relative).read_bytes(), (neutral_target / relative).read_bytes(), relative)

            legacy_validation = run_python(VALIDATOR, "--target", str(skill_target))
            neutral_validation = run_neutral_cli("validate", "--target", str(neutral_target))
            self.assertEqual(legacy_validation.returncode, 0, legacy_validation.stdout + legacy_validation.stderr)
            self.assertEqual(neutral_validation.returncode, 0, neutral_validation.stdout + neutral_validation.stderr)
            self.assertEqual(
                legacy_validation.stdout.replace(str(skill_target.resolve()), "<target>"),
                neutral_validation.stdout.replace(str(neutral_target.resolve()), "<target>"),
            )

            authored = neutral_target / "AGENTS.md"
            authored.write_text("# Existing authority\n", encoding="utf-8")
            preserved = run_neutral_cli("scaffold", "--target", str(neutral_target), "--title", title)
            self.assertEqual(preserved.returncode, 0, preserved.stdout + preserved.stderr)
            self.assertEqual(authored.read_text(encoding="utf-8"), "# Existing authority\n")
            self.assertIn("SKIP    AGENTS.md (existing authored file)", preserved.stdout)

            skill_update = run_python(
                UPDATE_CHECKER,
                "--target",
                str(skill_target),
                "--manifest-file",
                str(RELEASE_MANIFEST),
            )
            neutral_update = run_neutral_cli(
                "check-update",
                "--target",
                str(skill_target),
                "--manifest-file",
                str(RELEASE_MANIFEST),
            )
            self.assertEqual(skill_update.returncode, 0, skill_update.stdout + skill_update.stderr)
            self.assertEqual(skill_update.stdout, neutral_update.stdout)

    def test_phase1_packaged_skill_uses_standalone_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-phase1-package-") as temporary:
            root = Path(temporary)
            packaged = run_python(PACKAGER, "--output-dir", str(root), "--check-tag", f"v{CURRENT_VERSION}")
            self.assertEqual(packaged.returncode, 0, packaged.stdout + packaged.stderr)
            archive = root / f"project-orrery-v{CURRENT_VERSION}.zip"
            extracted = root / "extracted"
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extracted)
            standalone = extracted / "project-orrery"
            target = root / "target"
            installed = run_python(
                standalone / "scripts" / "install_project_orrery.py",
                "--target",
                str(target),
                "--title",
                "Standalone Skill",
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            self.assertEqual(
                (target / "AGENTS.md").read_text(encoding="utf-8").splitlines()[0],
                "# Standalone Skill: Agent state index",
            )
            validated = run_python(standalone / "scripts" / "validate_installation.py", "--target", str(target))
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            environment = {
                key: value for key, value in os.environ.items()
                if key not in {"PYTHONPATH", "PYTHONHOME"}
            }
            offline_runtime = subprocess.run(
                [sys.executable, "-X", "utf8", str(target / "scripts/docsite/serve_orrery.py"), "--help"],
                cwd=target,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(offline_runtime.returncode, 0, offline_runtime.stdout + offline_runtime.stderr)
            self.assertIn("Unified Observatory", offline_runtime.stdout)

    def test_fresh_install_validates_and_builds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-test-") as temporary:
            target = Path(temporary)
            installed = run_python(
                INSTALLER,
                "--target",
                str(target),
                "--title",
                "Orrery Test Project",
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)

            manifest = json.loads((target / ".project-orrery.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["title"], "Orrery Test Project")
            self.assertEqual(manifest["authority_status"], "migration_pending")
            self.assertEqual(manifest["manifest_format"], 1)
            self.assertEqual(manifest["installed_skill_version"], CURRENT_VERSION)
            self.assertEqual(manifest["toolchain_version"], CURRENT_VERSION)
            self.assertEqual(manifest["document_schema"], 1)
            self.assertFalse(any("__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"} for path in target.rglob("*")))
            ignore_rules = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".venv/", ignore_rules)
            self.assertIn("venv/", ignore_rules)
            self.assertTrue((target / "scripts" / "docsite" / "llm_broker.py").is_file())

            arguments = ["--target", str(target)]
            if os.environ.get("ORRERY_TEST_BUILD") == "1":
                arguments.append("--build")
            validated = run_python(VALIDATOR, *arguments)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            self.assertIn("Project Orrery scaffold structure valid", validated.stdout)
            if os.environ.get("ORRERY_TEST_BUILD") == "1":
                static_html = (target / "docs" / "_site" / "index.html").read_text(encoding="utf-8")
                self.assertNotIn("AI 服务设置", static_html)
                self.assertNotIn("ORRERY_SETTINGS_TOKEN", static_html)

    def test_existing_authored_files_are_preserved_and_tools_are_backed_up(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-upgrade-") as temporary:
            target = Path(temporary)
            agents = target / "AGENTS.md"
            custom_tool = target / "scripts" / "docsite" / "serve.py"
            custom_tool.parent.mkdir(parents=True)
            agents.write_text("# Existing authority\n", encoding="utf-8")
            custom_tool.write_text("# existing viewer tool\n", encoding="utf-8")

            installed = run_python(INSTALLER, "--target", str(target), "--title", "Existing Project")
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            self.assertEqual(agents.read_text(encoding="utf-8"), "# Existing authority\n")
            self.assertEqual(custom_tool.read_text(encoding="utf-8"), "# existing viewer tool\n")
            manifest = json.loads((target / ".project-orrery.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["toolchain_status"], "mixed")
            self.assertEqual(manifest["toolchain_version"], "unknown")

            upgraded = run_python(INSTALLER, "--target", str(target), "--upgrade-tools")
            self.assertEqual(upgraded.returncode, 0, upgraded.stdout + upgraded.stderr)
            self.assertEqual(agents.read_text(encoding="utf-8"), "# Existing authority\n")
            self.assertNotEqual(custom_tool.read_text(encoding="utf-8"), "# existing viewer tool\n")
            backups = list((target / ".project-orrery-backup").glob("*/scripts/docsite/serve.py"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "# existing viewer tool\n")
            manifest = json.loads((target / ".project-orrery.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["toolchain_status"], "current")
            self.assertEqual(manifest["toolchain_version"], CURRENT_VERSION)

    def test_update_checker_distinguishes_compatible_and_migrating_releases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-update-") as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            installed = run_python(INSTALLER, "--target", str(target), "--title", "Update Project")
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)

            compatible = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
            compatible["version"] = "0.3.0"
            compatible["distribution"]["tag"] = "v0.3.0"
            compatible_path = root / "compatible.json"
            compatible_path.write_text(json.dumps(compatible), encoding="utf-8")
            checked = run_python(
                UPDATE_CHECKER,
                "--target", str(target),
                "--manifest-file", str(compatible_path),
                "--json",
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            envelope = json.loads(checked.stdout)
            self.assertEqual(envelope["schema_version"], 1)
            self.assertEqual(envelope["command"], "check-update")
            self.assertEqual(envelope["exit_code"], checked.returncode)
            result = envelope["data"]
            self.assertEqual(result["status"], "update_available_compatible")
            self.assertFalse(result["migration_required"])

            migrating = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
            migrating["version"] = "1.0.0"
            migrating["compatibility"]["direct_upgrade_from"] = {
                "minimum": "1.0.0",
                "maximum_exclusive": "2.0.0",
            }
            migrating_path = root / "migrating.json"
            migrating_path.write_text(json.dumps(migrating), encoding="utf-8")
            checked = run_python(
                UPDATE_CHECKER,
                "--target", str(target),
                "--manifest-file", str(migrating_path),
                "--json",
            )
            self.assertEqual(checked.returncode, 5, checked.stdout + checked.stderr)
            envelope = json.loads(checked.stdout)
            self.assertEqual(envelope["errors"][0]["code"], "compatibility_migration_required")
            result = envelope["data"]
            self.assertEqual(result["status"], "update_available_migration_required")
            self.assertTrue(result["migration_required"])

    def test_update_checker_reports_unsupported_target_schema(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-schema-") as temporary:
            target = Path(temporary)
            installed = run_python(INSTALLER, "--target", str(target), "--title", "Future Project")
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            path = target / ".project-orrery.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["document_schema"] = 99
            path.write_text(json.dumps(manifest), encoding="utf-8")

            checked = run_python(
                UPDATE_CHECKER,
                "--target", str(target),
                "--manifest-file", str(RELEASE_MANIFEST),
                "--json",
            )
            self.assertEqual(checked.returncode, 5, checked.stdout + checked.stderr)
            envelope = json.loads(checked.stdout)
            result = envelope["data"]
            self.assertEqual(result["status"], "current_incompatible")
            self.assertTrue(result["migration_required"])

    def test_release_package_contains_clean_versioned_skill_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-package-") as temporary:
            output = Path(temporary)
            packaged = run_python(PACKAGER, "--output-dir", str(output), "--check-tag", f"v{CURRENT_VERSION}")
            self.assertEqual(packaged.returncode, 0, packaged.stdout + packaged.stderr)
            archive = output / f"project-orrery-v{CURRENT_VERSION}.zip"
            checksum = output / f"project-orrery-v{CURRENT_VERSION}.sha256"
            self.assertTrue(archive.is_file())
            expected = checksum.read_text(encoding="ascii").split()[0]
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), expected)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
            self.assertIn("project-orrery/SKILL.md", names)
            self.assertIn("project-orrery/release-manifest.json", names)
            self.assertIn("project-orrery/scripts/check_project_orrery_update.py", names)
            self.assertIn("project-orrery/assets/project-template/scripts/docsite/llm_broker.py", names)
            self.assertIn("project-orrery/packages/project-orrery-core/src/project_orrery_core/manifests.py", names)
            self.assertIn("project-orrery/packages/project-orrery-cli/src/project_orrery_cli/scaffold.py", names)
            self.assertIn("project-orrery/packages/project-orrery-observatory/src/project_orrery_observatory/unified_observatory.py", names)
            self.assertIn("project-orrery/adapters/harness-json/run_harness.py", names)
            self.assertEqual(len(names), 162)
            manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
            path_list = "".join(f"{name}\n" for name in sorted(names)).encode("utf-8")
            self.assertEqual(
                hashlib.sha256(path_list).hexdigest(),
                manifest["distribution"]["archive_path_list_sha256"],
            )
            self.assertFalse(any("__pycache__" in name or name.endswith((".pyc", ".pyo")) for name in names))

    def test_provider_config_persists_models_without_plaintext_key(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-config-") as temporary:
            target = Path(temporary)
            installed = run_python(INSTALLER, "--target", str(target), "--title", "Config Project")
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)

            module_path = target / "scripts" / "docsite" / "_llm.py"
            spec = importlib.util.spec_from_file_location("project_orrery_test_llm", module_path)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            try:
                spec.loader.exec_module(module)
                module.save_project_config(
                    provider="custom",
                    base_url="https://example.test/v1",
                    model="default-model",
                    intent_model="fast-model",
                    audit_model="audit-model",
                )
                raw = json.loads((target / "ai-config.json").read_text(encoding="utf-8"))
                self.assertNotIn("apiKey", raw)
                self.assertEqual(raw["intentModel"], "fast-model")
                self.assertEqual(raw["auditModel"], "audit-model")
                self.assertTrue(raw["enabled"])
                self.assertEqual(raw["provider"], "custom")
                self.assertRegex(raw["providerFingerprint"], r"^sha256:[0-9a-f]{64}$")
                self.assertNotEqual(
                    module.credential_service("custom", "https://example.test/v1"),
                    module.credential_service("custom", "https://other.example/v1"),
                )
                with self.assertRaisesRegex(ValueError, "远程 Provider 必须使用 HTTPS"):
                    module.validate_provider_endpoint("custom", "http://example.test/v1")
                with self.assertRaisesRegex(ValueError, "api.deepseek.com"):
                    module.validate_provider_endpoint("deepseek", "https://api.openai.com/v1")

                cleared_environment = {
                    key: value for key, value in os.environ.items()
                    if key not in {
                        "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_BASE_URL",
                        "OPENAI_API_BASE", "OPENAI_MODEL", "OPENAI_INTENT_MODEL",
                        "OPENAI_AUDIT_MODEL", "DOCSITE_AI_CONFIG", "DOCSITE_API_KEY",
                        "DOCSITE_PROVIDER", "DOCSITE_AI_ENABLED", "DOCSITE_PROVIDER_FINGERPRINT",
                    }
                }
                with mock.patch.dict(os.environ, cleared_environment, clear=True), mock.patch.object(
                    module, "_keyring_get", return_value=None
                ), mock.patch.object(
                    module, "legacy_key_available", return_value=False
                ):
                    config = module.load_config()
                self.assertEqual(config["base_url"], "https://example.test/v1")
                self.assertEqual(config["model"], "default-model")
                self.assertEqual(config["intent_model"], "fast-model")
                self.assertEqual(config["audit_model"], "audit-model")
                self.assertTrue(config["binding_valid"])
                self.assertIsNone(config["api_key"])

                raw["baseUrl"] = "https://drift.example/v1"
                (target / "ai-config.json").write_text(json.dumps(raw), encoding="utf-8")
                with mock.patch.dict(os.environ, cleared_environment, clear=True), mock.patch.object(
                    module, "_keyring_get", return_value="bound-secret"
                ), mock.patch.object(module, "legacy_key_available", return_value=False):
                    drifted = module.load_config()
                self.assertFalse(drifted["binding_valid"])
                self.assertIsNone(drifted["api_key"])

                provider_only_environment = dict(cleared_environment)
                provider_only_environment.update({
                    "DOCSITE_PROVIDER": "custom", "DOCSITE_API_KEY": "env-secret",
                })
                with mock.patch.dict(os.environ, provider_only_environment, clear=True), mock.patch.object(
                    module, "_keyring_get", return_value=None
                ):
                    provider_only = module.load_config()
                self.assertFalse(provider_only["binding_valid"])
                self.assertIsNone(provider_only["api_key"])
            finally:
                sys.modules.pop(spec.name, None)

    def test_broker_registration_replaces_old_upstream_without_exposing_keys(self) -> None:
        broker_path = REPOSITORY_ROOT / "scripts" / "docsite" / "llm_broker.py"
        spec = importlib.util.spec_from_file_location("project_orrery_registration_broker", broker_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        broker = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = broker
        try:
            with tempfile.TemporaryDirectory(prefix="project-orrery-registration-") as temporary, mock.patch.dict(
                os.environ,
                {
                    "ORRERY_TEST_IN_MEMORY_KEYRING": "1",
                    "DOCSITE_BROKER_DATA_DIR": temporary,
                },
            ):
                spec.loader.exec_module(broker)
                first = {
                    "provider": "custom",
                    "baseUrl": "http://127.0.0.1:9001/v1",
                    "model": "first-model",
                }
                second = {
                    "provider": "custom",
                    "baseUrl": "http://127.0.0.1:9002/v1",
                    "model": "second-model",
                }
                _, first_token = broker.configure_broker(first, "first-provider-secret")
                _, second_token = broker.configure_broker(second, "second-provider-secret")
                self.assertEqual(first_token, second_token)
                self.assertIsNone(broker._llm._keyring_get(
                    "custom", first["baseUrl"], namespace=broker.BROKER_NAMESPACE
                ))
                self.assertEqual(
                    broker._llm._keyring_get("custom", second["baseUrl"], namespace=broker.BROKER_NAMESPACE),
                    "second-provider-secret",
                )
                persisted = json.loads(broker.config_path().read_text(encoding="utf-8"))
                self.assertEqual(persisted["baseUrl"], second["baseUrl"])
                self.assertNotIn("first-provider-secret", broker.config_path().read_text(encoding="utf-8"))
                self.assertNotIn("second-provider-secret", broker.config_path().read_text(encoding="utf-8"))
        finally:
            sys.modules.pop(spec.name, None)

    def test_all_docsite_ai_entrypoints_are_broker_only(self) -> None:
        docsite = REPOSITORY_ROOT / "scripts" / "docsite"
        serve = (docsite / "serve.py").read_text(encoding="utf-8")
        qa = (docsite / "docsite_qa.py").read_text(encoding="utf-8")
        terminal = (docsite / "set_key.py").read_text(encoding="utf-8")
        self.assertNotIn('<option value="broker">', serve)
        self.assertIn('provider="broker"', serve)
        self.assertIn("get_provider(require_broker=True)", serve)
        self.assertIn("def get_provider(*, require_broker=True)", qa)
        self.assertNotIn("get_provider()", qa)
        self.assertIn('choices=("openai", "deepseek", "custom")', terminal)
        self.assertIn('provider="broker"', terminal)

    @unittest.skipUnless(os.environ.get("ORRERY_TEST_BUILD") == "1", "dynamic reader dependencies not requested")
    def test_graphical_ai_settings_api_is_local_and_never_echoes_keys(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-orrery-settings-") as temporary:
            target = Path(temporary)
            installed = run_python(INSTALLER, "--target", str(target), "--title", "Settings Project")
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)

            environment = os.environ.copy()
            for name in (
                "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE",
                "OPENAI_MODEL", "OPENAI_INTENT_MODEL", "OPENAI_AUDIT_MODEL", "DOCSITE_AI_CONFIG",
                "DOCSITE_API_KEY", "DOCSITE_PROVIDER", "DOCSITE_AI_ENABLED", "DOCSITE_PROVIDER_FINGERPRINT",
            ):
                environment.pop(name, None)
            environment.update({
                "DOCSITE_NO_BROWSER": "1",
                "DOCSITE_PORT": "0",
                "DOCSITE_MANAGED_BROKER_PORT": "0",
                "DOCSITE_BROKER_DATA_DIR": str(target / ".test-broker"),
                "PYTHONUNBUFFERED": "1",
                "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
                "ORRERY_TEST_IN_MEMORY_KEYRING": "1",
                "ORRERY_TEST_NO_EXTERNAL_NETWORK": "1",
            })
            process = subprocess.Popen(
                [sys.executable, "-X", "utf8", "scripts/docsite/serve.py"],
                cwd=target,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
            )
            try:
                port_path = target / "scripts" / "docsite" / ".port"
                deadline = time.time() + 20
                while time.time() < deadline and not port_path.is_file() and process.poll() is None:
                    time.sleep(0.1)
                if not port_path.is_file():
                    output = process.stdout.read() if process.stdout else ""
                    self.fail("dynamic reader failed to start:\n" + output)
                base = "http://127.0.0.1:%s" % port_path.read_text(encoding="utf-8").strip()
                with urllib.request.urlopen(base + "/", timeout=10) as response:
                    html = response.read().decode("utf-8")
                    self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
                    self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")
                    self.assertIn("frame-ancestors 'none'", response.headers.get("Content-Security-Policy", ""))
                self.assertIn("AI 服务设置 · Broker 统一管理", html)
                self.assertIn('id="ai-broker-mode"', html)
                self.assertNotIn('<option value="broker">', html)
                self.assertEqual(html.count('id="ai-settings-button"'), 1)
                self.assertLess(html.index('id="ai-settings-button"'), html.index('id="themeToggle"'))
                self.assertNotIn('class="settings"', html)
                self.assertIn("/api/refresh/briefing", html)
                self.assertNotIn("/briefing?refresh=1", html)
                token_match = re.search(r"ORRERY_SETTINGS_TOKEN='([^']+)'", html)
                self.assertIsNotNone(token_match)
                token = token_match.group(1)
                self.assertGreaterEqual(len(token), 32)

                status = read_json_url(base + "/api/ai-config")
                self.assertFalse(status["hasKey"])
                self.assertNotIn("apiKey", status)
                self.assertFalse(status["providerReady"])
                self.assertEqual(status["brokerMode"], "managed")

                sentinel = "orrery-secret-must-not-echo"
                payload = json.dumps({
                    "brokerMode": "managed",
                    "provider": "custom",
                    "baseUrl": "http://127.0.0.1:9/v1",
                    "model": "settings-test-model",
                    "intentModel": "settings-fast-model",
                    "auditModel": "settings-audit-model",
                    "apiKey": sentinel,
                }).encode("utf-8")
                unauthorized = urllib.request.Request(
                    base + "/api/ai-config",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    urllib.request.urlopen(unauthorized, timeout=10)
                self.assertEqual(denied.exception.code, 403)

                authorized_headers = {
                    "Content-Type": "application/json",
                    "X-Orrery-Settings-Token": token,
                    "Origin": base,
                }
                saved = read_json_url(urllib.request.Request(
                    base + "/api/ai-config",
                    data=payload,
                    headers=authorized_headers,
                    method="POST",
                ))
                self.assertEqual(saved["model"], "settings-test-model")
                self.assertTrue(saved["providerReady"])
                self.assertTrue(saved["managedProviderCredential"])
                self.assertNotIn(sentinel, json.dumps(saved))
                stored = json.loads((target / "ai-config.json").read_text(encoding="utf-8"))
                self.assertNotIn("apiKey", stored)
                self.assertEqual(stored["auditModel"], "settings-audit-model")
                self.assertEqual(stored["provider"], "broker")
                self.assertEqual(stored["brokerMode"], "managed")
                self.assertEqual(stored["upstreamProvider"], "custom")
                self.assertEqual(stored["upstreamBaseUrl"], "http://127.0.0.1:9/v1")
                self.assertRegex(stored["baseUrl"], r"^http://127\.0\.0\.1:\d+/v1$")
                self.assertTrue(stored["enabled"])
                self.assertRegex(stored["providerFingerprint"], r"^sha256:[0-9a-f]{64}$")

                hostile_origin = dict(authorized_headers)
                hostile_origin["Origin"] = "http://attacker.invalid"
                with self.assertRaises(urllib.error.HTTPError) as blocked_origin:
                    urllib.request.urlopen(urllib.request.Request(
                        base + "/api/ai-config", data=payload, headers=hostile_origin, method="POST"
                    ), timeout=10)
                self.assertEqual(blocked_origin.exception.code, 403)

                oversized_question = json.dumps({"question": "x" * (64 * 1024)}).encode("utf-8")
                with self.assertRaises(urllib.error.HTTPError) as blocked_body:
                    urllib.request.urlopen(urllib.request.Request(
                        base + "/ask", data=oversized_question,
                        headers={"Content-Type": "application/json", "Origin": base}, method="POST"
                    ), timeout=10)
                self.assertEqual(blocked_body.exception.code, 400)

                insecure_payload = json.dumps({
                    "brokerMode": "managed", "provider": "custom", "baseUrl": "http://example.com/v1",
                    "model": "settings-test-model", "intentModel": "", "auditModel": "", "apiKey": "",
                }).encode("utf-8")
                with self.assertRaises(urllib.error.HTTPError) as blocked_http:
                    urllib.request.urlopen(urllib.request.Request(
                        base + "/api/ai-config", data=insecure_payload,
                        headers=authorized_headers, method="POST"
                    ), timeout=10)
                self.assertEqual(blocked_http.exception.code, 400)

                class FailingSettingsUpstream(BaseHTTPRequestHandler):
                    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
                        body = b'{"error":"synthetic upstream failure"}'
                        self.send_response(503)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)

                    def log_message(self, _format: str, *_args: object) -> None:
                        return

                failing_upstream = ThreadingHTTPServer(
                    ("127.0.0.1", 0), FailingSettingsUpstream
                )
                failing_thread = threading.Thread(
                    target=failing_upstream.serve_forever, daemon=True
                )
                failing_thread.start()
                try:
                    test_payload = json.dumps({
                        "brokerMode": "managed",
                        "provider": "custom",
                        "baseUrl": "http://127.0.0.1:%d/v1"
                        % failing_upstream.server_address[1],
                        "model": "settings-test-model",
                        "intentModel": "",
                        "auditModel": "",
                        "apiKey": sentinel,
                    }).encode("utf-8")
                    test_request = urllib.request.Request(
                        base + "/api/ai-config/test",
                        data=test_payload,
                        headers=authorized_headers,
                        method="POST",
                    )
                    with self.assertRaises(urllib.error.HTTPError) as failed_test:
                        urllib.request.urlopen(test_request, timeout=10)
                    error_body = failed_test.exception.read().decode("utf-8")
                    self.assertNotIn(sentinel, error_body)
                    self.assertEqual(failed_test.exception.code, 500)
                finally:
                    failing_upstream.shutdown()
                    failing_upstream.server_close()
                    failing_thread.join(timeout=5)

                external_token = "external-broker-token-must-not-echo"
                external_payload = json.dumps({
                    "brokerMode": "external",
                    "provider": "custom",
                    "baseUrl": "http://127.0.0.1:9/v1",
                    "model": "external-model",
                    "intentModel": "",
                    "auditModel": "",
                    "apiKey": external_token,
                }).encode("utf-8")
                external = read_json_url(urllib.request.Request(
                    base + "/api/ai-config",
                    data=external_payload,
                    headers=authorized_headers,
                    method="POST",
                ))
                self.assertEqual(external["brokerMode"], "external")
                self.assertTrue(external["providerReady"])
                self.assertNotIn(external_token, json.dumps(external))
                stored_external = json.loads((target / "ai-config.json").read_text(encoding="utf-8"))
                self.assertEqual(stored_external["provider"], "broker")
                self.assertEqual(stored_external["brokerMode"], "external")
                self.assertEqual(stored_external["baseUrl"], "http://127.0.0.1:9/v1")
            finally:
                process.terminate()
                try:
                    process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=10)

    @unittest.skipUnless(os.environ.get("ORRERY_TEST_BUILD") == "1", "broker dependencies not requested")
    def test_local_broker_caches_enforces_budget_and_refuses_redirects(self) -> None:
        broker_path = REPOSITORY_ROOT / "scripts" / "docsite" / "llm_broker.py"
        spec = importlib.util.spec_from_file_location("project_orrery_test_broker", broker_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        broker = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = broker

        class UpstreamHandler(BaseHTTPRequestHandler):
            requests = 0
            redirect = False
            authorization = ""
            delay = 0.0

            def do_POST(self):
                type(self).requests += 1
                type(self).authorization = self.headers.get("Authorization", "")
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                if type(self).delay:
                    time.sleep(type(self).delay)
                if type(self).redirect:
                    self.send_response(302)
                    self.send_header("Location", "https://example.invalid/steal")
                    self.end_headers()
                    return
                body = json.dumps({
                    "id": "test", "object": "chat.completion",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "OK"}}],
                    "usage": {"total_tokens": 7},
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _fmt, *_args):
                pass

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
        upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        upstream_thread.start()
        server = None
        try:
            spec.loader.exec_module(broker)
            with tempfile.TemporaryDirectory(prefix="project-orrery-broker-") as temporary:
                provider_secret = "provider-secret-sentinel"
                client_token = "broker-client-token"
                state = broker.BrokerState({
                    "provider": "custom",
                    "baseUrl": "http://127.0.0.1:%d/v1" % upstream.server_address[1],
                    "model": "broker-test-model",
                    "dailyRequestLimit": 2,
                    "dailyTokenLimit": 1000,
                    "cacheTtlSeconds": 3600,
                }, provider_secret, client_token, database=Path(temporary) / "cache.sqlite3")
                server = broker.build_server(state, 0)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = "http://127.0.0.1:%d" % server.server_address[1]
                payload = json.dumps({
                    "model": "broker-test-model",
                    "messages": [{"role": "user", "content": "hello"}],
                    "max_tokens": 8,
                }).encode("utf-8")
                headers = {"Content-Type": "application/json", "Authorization": "Bearer " + client_token}

                UpstreamHandler.delay = 0.2
                barrier = threading.Barrier(3)
                results = []
                errors = []

                def request_once():
                    barrier.wait()
                    try:
                        response = urllib.request.urlopen(urllib.request.Request(
                            base + "/v1/chat/completions", data=payload,
                            headers=headers, method="POST"
                        ), timeout=10)
                        results.append((response.headers.get("X-Orrery-Broker-Cache"), response.read()))
                    except Exception as error:  # noqa: BLE001
                        errors.append(error)

                callers = [threading.Thread(target=request_once) for _ in range(2)]
                for caller in callers:
                    caller.start()
                barrier.wait()
                for caller in callers:
                    caller.join(timeout=10)
                self.assertFalse(errors)
                self.assertEqual(sorted(result[0] for result in results), ["HIT", "MISS"])
                self.assertEqual(results[0][1], results[1][1])
                first_body = results[0][1]
                self.assertEqual(UpstreamHandler.requests, 1)
                self.assertEqual(UpstreamHandler.authorization, "Bearer " + provider_secret)
                self.assertFalse(state._flights)
                self.assertNotIn(provider_secret.encode("utf-8"), first_body)
                self.assertNotIn(provider_secret.encode("utf-8"), (Path(temporary) / "cache.sqlite3").read_bytes())

                oversized_tokens = json.dumps({
                    "model": "broker-test-model",
                    "messages": [{"role": "user", "content": "too many tokens"}],
                    "max_tokens": 2000,
                }).encode("utf-8")
                with self.assertRaises(urllib.error.HTTPError) as token_budget:
                    urllib.request.urlopen(urllib.request.Request(
                        base + "/v1/chat/completions", data=oversized_tokens,
                        headers=headers, method="POST"
                    ), timeout=10)
                self.assertEqual(token_budget.exception.code, 429)

                UpstreamHandler.redirect = True
                redirect_payload = json.dumps({
                    "model": "broker-test-model",
                    "messages": [{"role": "user", "content": "redirect"}],
                    "max_tokens": 8,
                }).encode("utf-8")
                with self.assertRaises(urllib.error.HTTPError) as redirect:
                    urllib.request.urlopen(urllib.request.Request(
                        base + "/v1/chat/completions", data=redirect_payload,
                        headers=headers, method="POST"
                    ), timeout=10)
                self.assertEqual(redirect.exception.code, 502)

                budget_payload = json.dumps({
                    "model": "broker-test-model",
                    "messages": [{"role": "user", "content": "over budget"}],
                    "max_tokens": 8,
                }).encode("utf-8")
                with self.assertRaises(urllib.error.HTTPError) as budget:
                    urllib.request.urlopen(urllib.request.Request(
                        base + "/v1/chat/completions", data=budget_payload,
                        headers=headers, method="POST"
                    ), timeout=10)
                self.assertEqual(budget.exception.code, 429)
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            upstream.shutdown()
            upstream.server_close()
            sys.modules.pop(spec.name, None)


if __name__ == "__main__":
    unittest.main()
