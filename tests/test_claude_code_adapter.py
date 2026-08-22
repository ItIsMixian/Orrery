from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "claude-code"
MANIFEST = ADAPTER_ROOT / "adapter-manifest.json"
PLUGIN_MANIFEST = ADAPTER_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = ADAPTER_ROOT / ".claude-plugin" / "marketplace.json"
DEPENDENCY_CHECK = ADAPTER_ROOT / "scripts" / "check_cli_dependency.py"
PACKAGER = REPOSITORY_ROOT / "scripts" / "package_claude_code_adapter.py"
COMPONENT_VERSIONS = REPOSITORY_ROOT / "packages" / "component-versions.json"


def run_python(script: Path, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(script), *arguments],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )


class ClaudeCodeAdapterTests(unittest.TestCase):
    def test_plugin_is_thin_versioned_and_experimental(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        components = json.loads(COMPONENT_VERSIONS.read_text(encoding="utf-8"))
        component = components["adapters"]["claude-code"]

        self.assertEqual(manifest["adapter"]["id"], "project-orrery-claude-code")
        self.assertEqual(manifest["adapter"]["version"], "0.1.1")
        self.assertEqual(manifest["adapter"]["version"], plugin["version"])
        self.assertEqual(manifest["adapter"]["version"], marketplace["plugins"][0]["version"])
        self.assertEqual(manifest["adapter"]["version"], component["version"])
        self.assertEqual(manifest["adapter"]["support_status"], "experimental")
        self.assertEqual(manifest["runtime_compatibility"]["verified"], [])
        self.assertEqual(len(manifest["runtime_compatibility"]["tested"]), 1)
        self.assertEqual(manifest["runtime_compatibility"]["tested"][0]["runtime_version"], "2.1.87")
        self.assertEqual(len(component["runtime_evidence"]), 1)
        self.assertEqual(component["runtime_evidence"][0]["status"], "experimental")
        self.assertEqual(
            component["runtime_evidence"][0]["validation"],
            manifest["runtime_compatibility"]["evidence"][0],
        )
        self.assertEqual(
            component["runtime_evidence"][0]["stage_b_validation"],
            manifest["runtime_compatibility"]["evidence"][1],
        )
        self.assertEqual(
            component["runtime_evidence"][0]["stage_b_status"],
            "authentication_blocked_before_inference",
        )

        actual = {
            path.relative_to(ADAPTER_ROOT).as_posix()
            for path in ADAPTER_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
        }
        self.assertEqual(actual, set(manifest["distribution"]["files"]))
        self.assertFalse((ADAPTER_ROOT / "assets" / "project-template").exists())
        skill = (ADAPTER_ROOT / "skills" / "project-orrery" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/check_cli_dependency.py", skill)
        self.assertIn("root `AGENTS.md`", skill)
        self.assertNotIn("docs/state/", skill)
        for evidence in manifest["runtime_compatibility"]["evidence"]:
            self.assertTrue((REPOSITORY_ROOT / evidence).is_file())

    def test_package_is_deterministic_and_matches_checksum(self) -> None:
        version = json.loads(MANIFEST.read_text(encoding="utf-8"))["adapter"]["version"]
        with tempfile.TemporaryDirectory(prefix="orrery-claude-package-a-") as first_dir, tempfile.TemporaryDirectory(
            prefix="orrery-claude-package-b-"
        ) as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            for output in (first, second):
                result = run_python(PACKAGER, "--output-dir", str(output), "--check-adapter-version", version)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            archive_name = f"project-orrery-claude-code-adapter-v{version}.zip"
            first_archive = first / archive_name
            second_archive = second / archive_name
            self.assertEqual(first_archive.read_bytes(), second_archive.read_bytes())
            expected = (first / f"project-orrery-claude-code-adapter-v{version}.sha256").read_text(encoding="ascii").split()[0]
            self.assertEqual(hashlib.sha256(first_archive.read_bytes()).hexdigest(), expected)
            with zipfile.ZipFile(first_archive) as bundle:
                names = set(bundle.namelist())
            declared = json.loads(MANIFEST.read_text(encoding="utf-8"))["distribution"]["files"]
            self.assertEqual(names, {f"project-orrery-claude-code/{name}" for name in declared})

    def test_cli_dependency_check_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-claude-dependency-") as temporary:
            root = Path(temporary)
            executable_root = root / "bin"
            metadata_root = root / "metadata"
            executable_root.mkdir()
            metadata_root.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(executable_root)
            env["PYTHONPATH"] = str(metadata_root)

            missing = run_python(DEPENDENCY_CHECK, env=env)
            self.assertEqual(missing.returncode, 3)
            self.assertIn("code=cli_distribution_missing", missing.stderr)

            dist_info = metadata_root / "project_orrery_cli-0.2.0.dist-info"
            dist_info.mkdir()
            metadata = dist_info / "METADATA"
            metadata.write_text("Metadata-Version: 2.1\nName: project-orrery-cli\nVersion: 0.2.0\n", encoding="utf-8")
            entrypoint_name = "project-orrery.exe" if os.name == "nt" else "project-orrery"
            shutil.copy2(sys.executable, executable_root / entrypoint_name)
            incompatible = run_python(DEPENDENCY_CHECK, env=env)
            self.assertEqual(incompatible.returncode, 4)
            self.assertIn("code=cli_version_incompatible", incompatible.stderr)

            metadata.write_text("Metadata-Version: 2.1\nName: project-orrery-cli\nVersion: 0.1.1\n", encoding="utf-8")
            compatible = run_python(DEPENDENCY_CHECK, env=env)
            self.assertEqual(compatible.returncode, 0, compatible.stdout + compatible.stderr)


if __name__ == "__main__":
    unittest.main()
