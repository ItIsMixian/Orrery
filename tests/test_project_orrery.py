from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
