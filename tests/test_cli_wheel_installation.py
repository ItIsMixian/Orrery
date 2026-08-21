from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAMES = (
    "project-orrery-core",
    "project-orrery-observatory",
    "project-orrery-cli",
)


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class CliWheelInstallationTests(unittest.TestCase):
    def test_wheel_contains_observatory_assets_and_runs_without_source_repository(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-wheel-") as temporary:
            root = Path(temporary)
            staged_repository = root / "repository"
            staged_packages = staged_repository / "packages"
            staged_packages.mkdir(parents=True)
            for name in PACKAGE_NAMES:
                shutil.copytree(REPOSITORY_ROOT / "packages" / name, staged_packages / name)
            shutil.copytree(REPOSITORY_ROOT / "scripts" / "docsite", staged_repository / "scripts" / "docsite")
            shutil.copy2(REPOSITORY_ROOT / "start-docsite.bat", staged_repository / "start-docsite.bat")

            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            environment = os.environ.copy()
            environment["PIP_CACHE_DIR"] = str(root / "pip-cache")
            environment["TMP"] = environment["TEMP"] = str(root / "tmp")
            Path(environment["TMP"]).mkdir()
            for name in PACKAGE_NAMES:
                result = run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "wheel",
                        "--no-build-isolation",
                        "--no-deps",
                        "--wheel-dir",
                        str(wheelhouse),
                        str(staged_packages / name),
                    ],
                    cwd=staged_repository,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            observatory_wheel = next(wheelhouse.glob("project_orrery_observatory-*.whl"))
            component = json.loads(
                (REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src" / "project_orrery_observatory" / "component.json").read_text(encoding="utf-8")
            )
            with zipfile.ZipFile(observatory_wheel) as bundle:
                wheel_entries = set(bundle.namelist())
            for relative in component["managed_tools"]:
                self.assertIn(f"project_orrery_observatory/assets/{relative}", wheel_entries)

            runtime = root / "runtime"
            venv.EnvBuilder(with_pip=True).create(runtime)
            scripts = runtime / ("Scripts" if os.name == "nt" else "bin")
            runtime_python = scripts / ("python.exe" if os.name == "nt" else "python")
            wheels = sorted(str(path) for path in wheelhouse.glob("*.whl"))
            install = run(
                [str(runtime_python), "-m", "pip", "install", "--no-index", "--no-deps", *wheels],
                cwd=root,
                env=environment,
            )
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

            asset_probe = run(
                [
                    str(runtime_python),
                    "-c",
                    "from project_orrery_observatory import observatory_asset_root; print(observatory_asset_root())",
                ],
                cwd=root,
                env=environment,
            )
            self.assertEqual(asset_probe.returncode, 0, asset_probe.stdout + asset_probe.stderr)
            self.assertIn("site-packages", asset_probe.stdout.replace("\\", "/").lower())
            self.assertNotIn(str(staged_repository).replace("\\", "/").lower(), asset_probe.stdout.replace("\\", "/").lower())

            cli = scripts / ("project-orrery.exe" if os.name == "nt" else "project-orrery")
            target = root / "target"
            scaffold = run(
                [str(cli), "scaffold", "--target", str(target), "--title", "Wheel Fixture"],
                cwd=root,
                env=environment,
            )
            self.assertEqual(scaffold.returncode, 0, scaffold.stdout + scaffold.stderr)
            for relative in component["managed_tools"]:
                self.assertTrue((target / relative).is_file(), relative)
            validate = run([str(cli), "validate", "--target", str(target)], cwd=root, env=environment)
            self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
            self.assertIn("Project Orrery scaffold structure valid", validate.stdout)


if __name__ == "__main__":
    unittest.main()
