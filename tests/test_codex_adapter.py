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
ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "codex"
ADAPTER_MANIFEST = ADAPTER_ROOT / "adapter-manifest.json"
ADAPTER_INSTALLER = ADAPTER_ROOT / "scripts" / "install_adapter.py"
ADAPTER_DEPENDENCY_CHECK = ADAPTER_ROOT / "scripts" / "check_cli_dependency.py"
ADAPTER_PACKAGER = REPOSITORY_ROOT / "scripts" / "package_codex_adapter.py"
COMPONENT_VERSIONS = REPOSITORY_ROOT / "packages" / "component-versions.json"


def run_python(
    script: Path,
    *arguments: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
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


class CodexAdapterTests(unittest.TestCase):
    def test_adapter_is_thin_versioned_and_has_scoped_runtime_evidence(self) -> None:
        manifest = json.loads(ADAPTER_MANIFEST.read_text(encoding="utf-8"))
        components = json.loads(COMPONENT_VERSIONS.read_text(encoding="utf-8"))
        codex = components["adapters"]["codex"]

        self.assertEqual(manifest["adapter"]["id"], "project-orrery-codex")
        self.assertEqual(manifest["adapter"]["version"], codex["version"])
        self.assertEqual(manifest["adapter"]["support_status"], "experimental")
        self.assertEqual(manifest["adapter"]["support_status"], codex["support_status"])
        runtime = manifest["runtime_compatibility"]
        self.assertEqual(runtime["status"], "verified")
        self.assertEqual(len(runtime["verified"]), 1)
        verified = runtime["verified"][0]
        self.assertEqual(verified["runtime_version"], "codex-cli 0.148.0-alpha.21")
        self.assertEqual(verified["os"], "Windows 11 Pro x64 10.0.26200 (build 26200)")
        self.assertEqual(verified["adapter_version"], "0.1.0")
        self.assertNotEqual(verified["adapter_version"], manifest["adapter"]["version"])
        self.assertEqual(verified["core_api"], manifest["requires"]["core_api"])
        self.assertEqual(verified["cli_requirement"], ">=0.1.0,<0.2.0")
        self.assertIn("implicit_invocation", verified["scope"])
        self.assertIn("recoverable_uninstall", verified["scope"])
        self.assertEqual(len(runtime["evidence"]), 1)
        evidence = REPOSITORY_ROOT / runtime["evidence"][0]
        self.assertTrue(evidence.is_file())
        self.assertEqual(len(codex["runtime_evidence"]), 1)
        self.assertEqual(codex["runtime_evidence"][0]["validation"], runtime["evidence"][0])
        self.assertEqual(manifest["requires"]["core_api"], codex["core_api"])
        self.assertEqual(manifest["requires"]["cli"]["minimum"], codex["cli"]["minimum"])

        actual = {
            path.relative_to(ADAPTER_ROOT).as_posix()
            for path in ADAPTER_ROOT.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        }
        self.assertEqual(actual, set(manifest["distribution"]["files"]))
        self.assertFalse((ADAPTER_ROOT / "assets").exists())
        self.assertFalse((ADAPTER_ROOT / "references").exists())
        self.assertFalse((ADAPTER_ROOT / "release-manifest.json").exists())

        skill = (ADAPTER_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: project-orrery\ndescription:"))
        self.assertIn("project-orrery scaffold", skill)
        self.assertIn("scripts/check_cli_dependency.py", skill)
        self.assertIn("root `AGENTS.md`", skill)
        self.assertIn("does not contain", skill)
        self.assertNotIn("docs/state/", skill)
        self.assertNotIn("assets/project-template", skill)

    def test_adapter_package_is_deterministic_and_matches_checksum(self) -> None:
        manifest = json.loads(ADAPTER_MANIFEST.read_text(encoding="utf-8"))
        version = manifest["adapter"]["version"]
        with tempfile.TemporaryDirectory(prefix="orrery-adapter-package-a-") as first_directory, tempfile.TemporaryDirectory(
            prefix="orrery-adapter-package-b-"
        ) as second_directory:
            first = Path(first_directory)
            second = Path(second_directory)
            for output in (first, second):
                packaged = run_python(
                    ADAPTER_PACKAGER,
                    "--output-dir",
                    str(output),
                    "--check-adapter-version",
                    version,
                )
                self.assertEqual(packaged.returncode, 0, packaged.stdout + packaged.stderr)

            archive_name = f"project-orrery-codex-adapter-v{version}.zip"
            checksum_name = f"project-orrery-codex-adapter-v{version}.sha256"
            first_archive = first / archive_name
            second_archive = second / archive_name
            self.assertEqual(first_archive.read_bytes(), second_archive.read_bytes())
            expected = (first / checksum_name).read_text(encoding="ascii").split()[0]
            self.assertEqual(hashlib.sha256(first_archive.read_bytes()).hexdigest(), expected)
            with zipfile.ZipFile(first_archive) as bundle:
                names = set(bundle.namelist())
                extracted = first / "extracted"
                bundle.extractall(extracted)
            self.assertEqual(names, {f"project-orrery/{name}" for name in manifest["distribution"]["files"]})
            self.assertNotIn("project-orrery/assets/project-template/AGENTS.md", names)

            installed_root = first / "installed-skills"
            installed = run_python(
                extracted / "project-orrery" / "scripts" / "install_adapter.py",
                "--source",
                str(extracted / "project-orrery"),
                "--destination-root",
                str(installed_root),
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            self.assertTrue((installed_root / "project-orrery" / "adapter-manifest.json").is_file())

    def test_installer_lifecycle_is_previewable_recoverable_and_project_neutral(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-adapter-lifecycle-") as temporary:
            root = Path(temporary)
            skills_root = root / "skills"
            target_project = root / "target-project"
            target_project.mkdir()
            authored = target_project / "AGENTS.md"
            authored.write_text("author-owned\n", encoding="utf-8")

            preview = run_python(
                ADAPTER_INSTALLER,
                "--destination-root",
                str(skills_root),
                "--dry-run",
            )
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            self.assertIn("DRY-RUN", preview.stdout)
            self.assertFalse(skills_root.exists())

            installed = run_python(ADAPTER_INSTALLER, "--destination-root", str(skills_root))
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            destination = skills_root / "project-orrery"
            self.assertTrue((destination / "adapter-manifest.json").is_file())
            self.assertEqual(authored.read_text(encoding="utf-8"), "author-owned\n")

            kept = run_python(ADAPTER_INSTALLER, "--destination-root", str(skills_root))
            self.assertEqual(kept.returncode, 0, kept.stdout + kept.stderr)
            self.assertIn("KEEP", kept.stdout)

            installed_readme = destination / "README.md"
            installed_readme.write_text("locally changed\n", encoding="utf-8")
            upgrade_preview = run_python(
                ADAPTER_INSTALLER,
                "--destination-root",
                str(skills_root),
                "--upgrade",
                "--dry-run",
            )
            self.assertEqual(upgrade_preview.returncode, 0, upgrade_preview.stdout + upgrade_preview.stderr)
            self.assertEqual(installed_readme.read_text(encoding="utf-8"), "locally changed\n")
            backup_root = skills_root.parent / ".project-orrery-adapter-backup"
            self.assertFalse(backup_root.exists())

            upgraded = run_python(
                ADAPTER_INSTALLER,
                "--destination-root",
                str(skills_root),
                "--upgrade",
            )
            self.assertEqual(upgraded.returncode, 0, upgraded.stdout + upgraded.stderr)
            backups = list(backup_root.glob("*/project-orrery/README.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "locally changed\n")
            self.assertFalse(any(path.name == "SKILL.md" for path in skills_root.rglob("SKILL.md") if path.parent != destination))
            self.assertEqual(installed_readme.read_bytes(), (ADAPTER_ROOT / "README.md").read_bytes())

            uninstall_preview = run_python(
                ADAPTER_INSTALLER,
                "--destination-root",
                str(skills_root),
                "--uninstall",
                "--dry-run",
            )
            self.assertEqual(uninstall_preview.returncode, 0, uninstall_preview.stdout + uninstall_preview.stderr)
            self.assertTrue(destination.exists())

            uninstalled = run_python(
                ADAPTER_INSTALLER,
                "--destination-root",
                str(skills_root),
                "--uninstall",
            )
            self.assertEqual(uninstalled.returncode, 0, uninstalled.stdout + uninstalled.stderr)
            self.assertFalse(destination.exists())
            trash_root = skills_root.parent / ".project-orrery-adapter-trash"
            trash = list(trash_root.glob("*/project-orrery/adapter-manifest.json"))
            self.assertEqual(len(trash), 1)
            self.assertIn("RESTORE", uninstalled.stdout)
            self.assertEqual(authored.read_text(encoding="utf-8"), "author-owned\n")

    def test_installer_refuses_unknown_conflicts_and_backs_up_legacy_skill(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-adapter-conflicts-") as temporary:
            root = Path(temporary)
            unknown_root = root / "unknown-skills"
            unknown = unknown_root / "project-orrery"
            unknown.mkdir(parents=True)
            user_file = unknown / "user-owned.txt"
            user_file.write_text("preserve\n", encoding="utf-8")
            refused = run_python(ADAPTER_INSTALLER, "--destination-root", str(unknown_root), "--upgrade")
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(user_file.read_text(encoding="utf-8"), "preserve\n")
            self.assertFalse((unknown_root.parent / ".project-orrery-adapter-backup").exists())

            legacy_root = root / "legacy-skills"
            legacy = legacy_root / "project-orrery"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("legacy skill\n", encoding="utf-8")
            (legacy / "release-manifest.json").write_text(
                json.dumps({"name": "project-orrery", "version": "0.2.0"}),
                encoding="utf-8",
            )
            without_upgrade = run_python(ADAPTER_INSTALLER, "--destination-root", str(legacy_root))
            self.assertEqual(without_upgrade.returncode, 2)
            self.assertEqual((legacy / "SKILL.md").read_text(encoding="utf-8"), "legacy skill\n")

            migrated = run_python(
                ADAPTER_INSTALLER,
                "--destination-root",
                str(legacy_root),
                "--upgrade",
            )
            self.assertEqual(migrated.returncode, 0, migrated.stdout + migrated.stderr)
            self.assertTrue((legacy / "adapter-manifest.json").is_file())
            legacy_backups = list(
                (legacy_root.parent / ".project-orrery-adapter-backup").glob("*/project-orrery/release-manifest.json")
            )
            self.assertEqual(len(legacy_backups), 1)
            preserved = json.loads(legacy_backups[0].read_text(encoding="utf-8"))
            self.assertEqual(preserved["version"], "0.2.0")

    def test_packager_rejects_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-adapter-version-") as temporary:
            result = run_python(
                ADAPTER_PACKAGER,
                "--output-dir",
                temporary,
                "--check-adapter-version",
                "99.0.0",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("does not match", result.stderr)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_cli_dependency_check_fails_closed_and_accepts_declared_version(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-adapter-dependency-") as temporary:
            root = Path(temporary)
            executable_root = root / "bin"
            metadata_root = root / "metadata"
            executable_root.mkdir()
            metadata_root.mkdir()

            base_env = os.environ.copy()
            base_env["PATH"] = str(executable_root)
            base_env["PYTHONPATH"] = str(metadata_root)
            missing_distribution = run_python(ADAPTER_DEPENDENCY_CHECK, env=base_env)
            self.assertEqual(missing_distribution.returncode, 3)
            self.assertIn("code=cli_distribution_missing", missing_distribution.stderr)

            dist_info = metadata_root / "project_orrery_cli-0.2.0.dist-info"
            dist_info.mkdir()
            metadata = dist_info / "METADATA"
            metadata.write_text(
                "Metadata-Version: 2.1\nName: project-orrery-cli\nVersion: 0.1.0\n",
                encoding="utf-8",
            )
            missing_entrypoint = run_python(ADAPTER_DEPENDENCY_CHECK, env=base_env)
            self.assertEqual(missing_entrypoint.returncode, 3)
            self.assertIn("code=cli_entrypoint_missing", missing_entrypoint.stderr)

            entrypoint_name = "project-orrery.exe" if os.name == "nt" else "project-orrery"
            entrypoint_path = executable_root / entrypoint_name
            shutil.copy2(sys.executable, entrypoint_path)
            metadata.write_text(
                "Metadata-Version: 2.1\nName: project-orrery-cli\nVersion: 0.2.0\n",
                encoding="utf-8",
            )
            incompatible = run_python(ADAPTER_DEPENDENCY_CHECK, env=base_env)
            self.assertEqual(incompatible.returncode, 4)
            self.assertIn("code=cli_version_incompatible", incompatible.stderr)
            self.assertIn("installed=0.2.0", incompatible.stderr)

            metadata.write_text(
                "Metadata-Version: 2.1\nName: project-orrery-cli\nVersion: 0.1.0\n",
                encoding="utf-8",
            )
            compatible = run_python(ADAPTER_DEPENDENCY_CHECK, env=base_env)
            self.assertEqual(compatible.returncode, 0, compatible.stdout + compatible.stderr)
            self.assertIn("version=0.1.0", compatible.stdout)
            self.assertIn(entrypoint_name, compatible.stdout.lower())


if __name__ == "__main__":
    unittest.main()
