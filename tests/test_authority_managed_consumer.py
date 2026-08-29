from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "authority-meta-model"
    / "v1"
    / "managed-consumer.json"
)
SCHEMA_PATH = (
    CORE_SOURCE
    / "project_orrery_core"
    / "schema"
    / "authority-managed-consumer-v1.json"
)
for source in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE):
    sys.path.insert(0, str(source))

from project_orrery_cli.authority_consumer import inspect_managed_consumer  # noqa: E402
from project_orrery_core.authority_consumer import (  # noqa: E402
    MANAGED_CONSUMER_CONTRACT,
    evaluate_managed_authority_consumer,
)
import project_orrery_cli  # noqa: E402
import project_orrery_core  # noqa: E402


def write_file(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class AuthorityManagedConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def healthy_input(self) -> dict:
        value = copy.deepcopy(self.fixture["healthy_input"])
        value["expected_versions"] = copy.deepcopy(
            self.fixture["expected_versions"]
        )
        value["observed_versions"] = copy.deepcopy(
            self.fixture["expected_versions"]
        )
        return value

    @staticmethod
    def apply_case(value: dict, changes: dict) -> None:
        for dotted, item in changes.items():
            target = value
            parts = dotted.split(".")
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = item

    def test_versioned_fixture_covers_every_selection_and_failure_boundary(self) -> None:
        self.assertEqual(self.fixture["contract_type"], MANAGED_CONSUMER_CONTRACT)
        seen = set()
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                inputs = self.healthy_input()
                self.apply_case(inputs, case["set"])
                result = evaluate_managed_authority_consumer(**inputs)
                codes = [item["code"] for item in result["readiness"]["blockers"]]
                self.assertEqual(result["selection"]["effective"], case["effective"])
                self.assertEqual(
                    result["selection"]["active_consumer"], case["active_consumer"]
                )
                self.assertEqual(codes, case["blockers"])
                self.assertEqual(result["selection"]["active_consumer"], "legacy")
                self.assertFalse(
                    result["selection"]["production_behavior_switched"]
                )
                if result["selection"]["effective"] == "enabled":
                    self.assertEqual(
                        result["selection"]["target_consumer"],
                        "managed-authority-projection",
                    )
                    self.assertTrue(result["selection"]["rollout_ready"])
                self.assertFalse(result["selection"]["switch_authorized"])
                self.assertEqual(
                    result["selection"]["maintainer_enable_decision"], "pending"
                )
                seen.add(case["id"])
        self.assertTrue(
            {
                "legacy-default",
                "shadow",
                "candidate-projection",
                "enabled",
                "explicit-rollback",
                "unsupported-model",
                "collector-failure",
                "evaluator-failure",
                "projection-failure",
                "collector-version-drift",
                "evaluator-version-drift",
                "projection-version-drift",
                "source-drift",
                "reconciliation-drift",
                "partial-render",
                "ai-selection",
                "coordinator-selection",
                "unknown-scope",
                "local-only-scope",
            }.issubset(seen)
        )

    def test_same_input_contract_and_plans_are_deterministic(self) -> None:
        inputs = self.healthy_input()
        first = evaluate_managed_authority_consumer(**inputs)
        second = evaluate_managed_authority_consumer(**copy.deepcopy(inputs))
        self.assertEqual(first, second)
        self.assertRegex(first["contract_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(first["binding_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            first["rollout_plan"]["binding_hash"], first["binding_hash"]
        )
        self.assertEqual(
            first["rollback_plan"]["binding_hash"], first["binding_hash"]
        )

    def test_rollback_is_atomic_offline_and_does_not_mutate_author_or_release(self) -> None:
        inputs = self.healthy_input()
        inputs["requested_selection"] = "rollback"
        result = evaluate_managed_authority_consumer(**inputs)
        self.assertEqual(result["selection"]["effective"], "rollback")
        self.assertEqual(result["selection"]["active_consumer"], "legacy")
        self.assertEqual(result["rollback_plan"]["atomicity"], "complete-page-or-legacy")
        for key in ("writes_author_documents", "network_required", "modifies_release"):
            self.assertFalse(result["rollback_plan"][key])
            self.assertFalse(result["guarantees"][key])
        self.assertFalse(result["guarantees"]["partial_claim_page_allowed"])

    def test_schema_tracks_the_exact_top_level_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        contract = evaluate_managed_authority_consumer(**self.healthy_input())
        self.assertEqual(schema["properties"]["contract_type"]["const"], MANAGED_CONSUMER_CONTRACT)
        self.assertEqual(set(schema["required"]), set(contract))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(
            hasattr(project_orrery_core, "evaluate_managed_authority_consumer")
        )
        self.assertFalse(hasattr(project_orrery_cli, "inspect_managed_consumer"))

    def write_repository_fixture(self, root: Path) -> None:
        write_file(
            root,
            ".project-orrery.json",
            '{"manifest_format":1,"document_schema":1,"authority_model_version":1}\n',
        )
        write_file(root, "docs/core/principles.md", "# Seed\n")
        write_file(
            root,
            "docs/decisions/0001-test.md",
            "# ADR-0001: Test\n\nStatus: Accepted\n",
        )

    def test_cli_inspect_is_read_only_offline_and_hides_normalized_observations(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-a3-consumer-") as temporary:
            root = Path(temporary)
            self.write_repository_fixture(root)
            before = tree_digest(root)
            with mock.patch("socket.socket", side_effect=AssertionError("network forbidden")):
                result = inspect_managed_consumer(
                    root,
                    requested_selection="legacy",
                    selection_authority="system-default",
                    fact_scope="candidate",
                    evidence_visibility=(
                        "revision-content",
                        "human-or-agent-assertion",
                    ),
                )
            self.assertEqual(before, tree_digest(root))
        self.assertEqual(result["selection"]["effective"], "legacy")
        self.assertEqual(result["selection"]["active_consumer"], "legacy")
        self.assertFalse(result["inspection"]["writes_performed"])
        self.assertFalse(result["inspection"]["normalized_observations_exposed"])
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertNotIn('"documents"', encoded)
        self.assertNotIn('"observations"', encoded)

    def test_unified_cli_outputs_machine_readable_inspect_and_readiness(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = os.pathsep.join(
            str(path) for path in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE)
        )
        inspect_run = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "project_orrery_cli",
                "authority-consumer",
                "inspect",
                "--target",
                str(REPOSITORY_ROOT),
                "--fact-scope",
                "candidate",
                "--json",
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(inspect_run.returncode, 0, inspect_run.stderr)
        inspect_payload = json.loads(inspect_run.stdout)
        self.assertEqual(inspect_payload["command"], "authority-consumer-inspect")
        self.assertEqual(inspect_payload["data"]["selection"]["requested"], "legacy")

        readiness_run = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "project_orrery_cli",
                "authority-consumer",
                "readiness",
                "--target",
                str(REPOSITORY_ROOT),
                "--selection",
                "enabled",
                "--fact-scope",
                "canonical",
                "--json",
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(readiness_run.returncode, 0, readiness_run.stderr)
        readiness_payload = json.loads(readiness_run.stdout)
        self.assertEqual(
            readiness_payload["command"], "authority-consumer-readiness"
        )
        self.assertEqual(
            readiness_payload["data"]["selection"]["effective"], "enabled"
        )
        self.assertIn("rollout_plan", readiness_payload["data"])
        self.assertIn("rollback_plan", readiness_payload["data"])

    def test_ai_readiness_request_cannot_override_selection(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = os.pathsep.join(
            str(path) for path in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE)
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "project_orrery_cli",
                "authority-consumer",
                "readiness",
                "--target",
                str(REPOSITORY_ROOT),
                "--selection",
                "enabled",
                "--selection-authority",
                "ai",
                "--fact-scope",
                "canonical",
                "--json",
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 5, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["data"]["selection"]["effective"], "unavailable")
        self.assertEqual(payload["data"]["selection"]["active_consumer"], "legacy")
        self.assertFalse(payload["data"]["selection"]["switch_authorized"])


if __name__ == "__main__":
    unittest.main()
