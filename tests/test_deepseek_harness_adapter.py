from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "deepseek-harness"
MANIFEST = ADAPTER_ROOT / "adapter-manifest.json"
PACKAGE = ADAPTER_ROOT / "package.json"
DEPENDENCY_CHECK = ADAPTER_ROOT / "scripts" / "check_cli_dependency.py"
PACKAGER = REPOSITORY_ROOT / "scripts" / "package_deepseek_harness_adapter.py"
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


class DeepSeekHarnessAdapterTests(unittest.TestCase):
    def test_bundle_is_thin_versioned_and_experimental(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        components = json.loads(COMPONENT_VERSIONS.read_text(encoding="utf-8"))
        component = components["adapters"]["deepseek-harness"]

        self.assertEqual(manifest["adapter"]["id"], "project-orrery-deepseek-harness")
        self.assertEqual(manifest["adapter"]["distribution"], package["name"])
        self.assertEqual(manifest["adapter"]["version"], package["version"])
        self.assertEqual(manifest["adapter"]["version"], component["version"])
        self.assertEqual(manifest["adapter"]["support_status"], "experimental")
        self.assertEqual(manifest["runtime_compatibility"]["verified"], [])
        self.assertEqual(len(manifest["runtime_compatibility"]["tested"]), 1)
        self.assertEqual(
            manifest["runtime_compatibility"]["tested"][0]["runtime_version"],
            "@deepseek-ai/dsh 0.1.0-rc.8",
        )
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
            "explicit_skill_injection_passed_model_credential_blocked",
        )
        self.assertEqual(package["dsh"]["bundle"]["patch"], "./cordis.patch.yml")
        self.assertEqual(package["peerDependencies"]["@deepseek-ai/dsh-skill"], "0.1.0-rc.8")

        actual = {
            path.relative_to(ADAPTER_ROOT).as_posix()
            for path in ADAPTER_ROOT.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and "node_modules" not in path.parts
            and path.suffix not in {".pyc", ".pyo", ".tgz"}
        }
        self.assertEqual(actual, set(manifest["distribution"]["files"]))
        self.assertFalse((ADAPTER_ROOT / "assets" / "project-template").exists())
        source = (ADAPTER_ROOT / "index.js").read_text(encoding="utf-8")
        self.assertIn("ctx.skills.registerProvider", source)
        self.assertIn("BUNDLED_SKILL_RANK", source)
        skill = (ADAPTER_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("root `AGENTS.md`", skill)
        self.assertIn("scripts/check_cli_dependency.py", skill)
        self.assertNotIn("docs/state/", skill)
        for evidence in manifest["runtime_compatibility"]["evidence"]:
            self.assertTrue((REPOSITORY_ROOT / evidence).is_file())

    def test_package_is_deterministic_and_npm_compatible(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        version = manifest["adapter"]["version"]
        name = manifest["distribution"]["package_name"]
        with tempfile.TemporaryDirectory(prefix="orrery-dsh-package-a-") as first_dir, tempfile.TemporaryDirectory(
            prefix="orrery-dsh-package-b-"
        ) as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            for output in (first, second):
                result = run_python(PACKAGER, "--output-dir", str(output), "--check-adapter-version", version)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            archive_name = f"{name}-{version}.tgz"
            first_archive = first / archive_name
            second_archive = second / archive_name
            self.assertEqual(first_archive.read_bytes(), second_archive.read_bytes())
            expected = (first / f"{name}-{version}.sha256").read_text(encoding="ascii").split()[0]
            self.assertEqual(hashlib.sha256(first_archive.read_bytes()).hexdigest(), expected)
            with tarfile.open(first_archive, "r:gz") as bundle:
                names = set(bundle.getnames())
                package_json = json.loads(bundle.extractfile("package/package.json").read().decode("utf-8"))
            self.assertEqual(names, {f"package/{path}" for path in manifest["distribution"]["files"]})
            self.assertEqual(package_json["name"], name)
            self.assertEqual(package_json["version"], version)

    def test_cli_dependency_check_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-dsh-dependency-") as temporary:
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
