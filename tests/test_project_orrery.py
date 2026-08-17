from __future__ import annotations

import json
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "project-orrery"
INSTALLER = SKILL_ROOT / "scripts" / "install_project_orrery.py"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_installation.py"


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

            upgraded = run_python(INSTALLER, "--target", str(target), "--upgrade-tools")
            self.assertEqual(upgraded.returncode, 0, upgraded.stdout + upgraded.stderr)
            self.assertEqual(agents.read_text(encoding="utf-8"), "# Existing authority\n")
            self.assertNotEqual(custom_tool.read_text(encoding="utf-8"), "# existing viewer tool\n")
            backups = list((target / ".project-orrery-backup").glob("*/scripts/docsite/serve.py"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "# existing viewer tool\n")

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
                    base_url="https://example.test/v1",
                    model="default-model",
                    intent_model="fast-model",
                    audit_model="audit-model",
                )
                raw = json.loads((target / "ai-config.json").read_text(encoding="utf-8"))
                self.assertNotIn("apiKey", raw)
                self.assertEqual(raw["intentModel"], "fast-model")
                self.assertEqual(raw["auditModel"], "audit-model")

                cleared_environment = {
                    key: value for key, value in os.environ.items()
                    if key not in {
                        "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_BASE_URL",
                        "OPENAI_API_BASE", "OPENAI_MODEL", "OPENAI_INTENT_MODEL",
                        "OPENAI_AUDIT_MODEL", "DOCSITE_AI_CONFIG",
                    }
                }
                with mock.patch.dict(os.environ, cleared_environment, clear=True), mock.patch.object(
                    module, "_keyring_get", return_value=None
                ):
                    config = module.load_config()
                self.assertEqual(config["base_url"], "https://example.test/v1")
                self.assertEqual(config["model"], "default-model")
                self.assertEqual(config["intent_model"], "fast-model")
                self.assertEqual(config["audit_model"], "audit-model")
            finally:
                sys.modules.pop(spec.name, None)

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
            ):
                environment.pop(name, None)
            environment.update({"DOCSITE_NO_BROWSER": "1", "DOCSITE_PORT": "0", "PYTHONUNBUFFERED": "1"})
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
                self.assertIn("AI 服务设置", html)
                token_match = re.search(r"ORRERY_SETTINGS_TOKEN='([^']+)'", html)
                self.assertIsNotNone(token_match)
                token = token_match.group(1)
                self.assertGreaterEqual(len(token), 32)

                status = read_json_url(base + "/api/ai-config")
                self.assertFalse(status["hasKey"])
                self.assertNotIn("apiKey", status)

                payload = json.dumps({
                    "baseUrl": "http://127.0.0.1:9/v1",
                    "model": "settings-test-model",
                    "intentModel": "settings-fast-model",
                    "auditModel": "settings-audit-model",
                    "apiKey": "",
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
                }
                saved = read_json_url(urllib.request.Request(
                    base + "/api/ai-config",
                    data=payload,
                    headers=authorized_headers,
                    method="POST",
                ))
                self.assertEqual(saved["model"], "settings-test-model")
                stored = json.loads((target / "ai-config.json").read_text(encoding="utf-8"))
                self.assertNotIn("apiKey", stored)
                self.assertEqual(stored["auditModel"], "settings-audit-model")

                sentinel = "orrery-secret-must-not-echo"
                test_payload = json.dumps({
                    "baseUrl": "http://127.0.0.1:9/v1",
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
                process.terminate()
                try:
                    process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
