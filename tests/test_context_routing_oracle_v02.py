import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ORACLE = (
    REPO_ROOT
    / "experiments"
    / "context-routing"
    / "oracles"
    / "oracle-v0.2"
    / "oracle.py"
)


class ContextRoutingOracleV02Tests(unittest.TestCase):
    def run_oracle(self, argument: str, timeout: int = 120):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(ORACLE), argument],
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )

    def test_fixture_manifest_verifies(self):
        completed = self.run_oracle("--verify-fixture")
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["verified"])
        self.assertEqual(7, report["files"])
        self.assertTrue(report["schema_valid"])
        self.assertTrue(report["state_fixture_valid"])
        self.assertEqual([], report["failures"])

    def test_static_controls_cover_layered_verdicts(self):
        completed = self.run_oracle("--self-test")
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual("passed", report["self_test"])
        self.assertEqual(20, report["cases"])
        self.assertEqual(3, report["control_families"]["paraphrase_positive"])
        self.assertEqual(6, report["control_families"]["contradiction"])
        self.assertEqual(6, report["control_families"]["mutation"])
        self.assertEqual(0, report["model_calls"])
        self.assertFalse(report["pilot_created"])


if __name__ == "__main__":
    unittest.main()
