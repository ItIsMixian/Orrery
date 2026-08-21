from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "authority-meta-model"
    / "v1"
    / "cli-observation-contract.json"
)
for source in (CORE_SOURCE, CLI_SOURCE):
    sys.path.insert(0, str(source))

from project_orrery_cli.authority_observations import (  # noqa: E402
    AUTHORITY_OBSERVATION_CONTRACT,
    AuthorityObservationParseError,
    authority_observation_snapshot,
    build_cli_authority_contract,
)
from project_orrery_cli.authority_shadow import (  # noqa: E402
    build_authority_shadow,
)
import project_orrery_cli  # noqa: E402


def write_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class AuthorityCliClaimsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def write_fixture(self, root: Path) -> None:
        for document in self.fixture["documents"]:
            write_file(root, document["path"], document["content"])
        write_file(
            root,
            "AGENTS.md",
            "docs/HANDOFF.md docs/PROGRESS.md docs/state/\n",
        )
        write_file(root, "docs/PROGRESS.md", "integrated\n")

    def by_role(self, contract: dict, role: str) -> list[dict]:
        return [
            document for document in contract["documents"] if document["role"] == role
        ]

    def test_fixture_freezes_complete_internal_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            self.write_fixture(root)
            contract = build_cli_authority_contract(root)

            self.assertEqual(
                contract["contract_version"], self.fixture["contract_version"]
            )
            self.assertEqual(contract["mode"], "candidate-shadow")
            self.assertFalse(contract["production_behavior_switched"])
            self.assertRegex(
                contract["conformance_input"]["repository_snapshot"],
                r"^cli-authority-observations:sha256:[0-9a-f]{64}$",
            )
            self.assertEqual(
                sorted({document["role"] for document in contract["documents"]}),
                self.fixture["expected"]["roles"],
            )
            self.assertEqual(contract["unresolved_relations"], [])
            graph = contract["decision_graph"]
            self.assertEqual(graph["status"], "evaluated")
            self.assertEqual(
                graph["result"]["relations"],
                self.fixture["expected"]["relations"],
            )
            self.assertEqual(
                graph["result"]["claims"]["effective_decisions"],
                self.fixture["expected"]["effective_decisions"],
            )

    def test_contract_is_not_exported_as_a_stable_cli_api(self) -> None:
        self.assertFalse(hasattr(project_orrery_cli, "build_cli_authority_contract"))

    def test_claims_and_evidence_are_bound_to_exact_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            self.write_fixture(root)
            contract = build_cli_authority_contract(root)

            for document in contract["documents"]:
                self.assertRegex(document["source_sha256"], r"^sha256:[0-9a-f]{64}$")
                self.assertTrue(document["source"])
                self.assertEqual(len(document["evidence_provenance"]), 1)
                evidence = document["evidence_provenance"][0]
                self.assertEqual(evidence["source"], document["source"])
                self.assertEqual(evidence["source_sha256"], document["source_sha256"])
                self.assertIsNotNone(evidence["capability"])
                self.assertTrue(evidence["visible"])

            for role in ("plan", "state"):
                document = self.by_role(contract, role)[0]
                self.assertNotIn("implementation_claim", document["claims"])

            validation = self.by_role(contract, "validation")[0]
            self.assertEqual(
                validation["claims"]["validation_assertion"],
                self.fixture["expected"]["validation_assertion"],
            )
            self.assertEqual(
                validation["claims"]["validation_evidence"],
                self.fixture["expected"]["validation_evidence"],
            )
            self.assertIn("validated", validation["must_not_infer"])
            self.assertEqual(
                validation["evidence_provenance"][0]["category"],
                "human-or-agent-assertion",
            )

    def test_contract_is_deterministic_and_ignores_non_authority_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            self.write_fixture(root)
            first = build_cli_authority_contract(root)
            second = build_cli_authority_contract(root)
            self.assertEqual(first, second)

            before = authority_observation_snapshot(root)
            write_file(root, "docs/library/unrelated.md", "changed\n")
            write_file(root, "docs/state/README.md", "changed\n")
            self.assertEqual(before, authority_observation_snapshot(root))
            write_file(root, "docs/state/example.md", "# changed\n")
            self.assertNotEqual(before, authority_observation_snapshot(root))

    def test_missing_relation_target_fails_closed_to_unknown_graph(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            write_file(
                root,
                "docs/decisions/0001-old.md",
                "# ADR-0001\n\nStatus: Superseded by ADR-9999\n",
            )
            contract = build_cli_authority_contract(root)
            self.assertEqual(contract["decision_graph"]["status"], "unknown")
            self.assertIsNone(contract["decision_graph"]["result"])
            self.assertEqual(
                contract["unresolved_relations"],
                [
                    {
                        "source": "ADR-9999",
                        "relation": "supersedes",
                        "target": "ADR-0001",
                        "reason": "replacement-not-visible",
                    }
                ],
            )

    def test_conflicting_metadata_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            write_file(
                root,
                "docs/validation/conflict.md",
                "# Validation\n\nResult: Passed\nOutcome: Failed\n",
            )
            with self.assertRaises(AuthorityObservationParseError):
                build_cli_authority_contract(root)

    def test_duplicate_decision_identifier_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            write_file(
                root,
                "docs/decisions/0001-first.md",
                "# ADR-0001\n\nStatus: Accepted\n",
            )
            write_file(
                root,
                "docs/decisions/0001-second.md",
                "# ADR-0001\n\nStatus: Accepted\n",
            )
            with self.assertRaisesRegex(
                AuthorityObservationParseError, "duplicate decision id ADR-0001"
            ):
                build_cli_authority_contract(root)

    def test_authority_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary) / "repo"
            outside = Path(temporary) / "outside.md"
            outside.write_text("# External state\n", encoding="utf-8")
            link = root / "docs" / "state" / "linked.md"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(
                AuthorityObservationParseError, "authority source cannot be a symlink"
            ):
                build_cli_authority_contract(root)

    def test_hidden_assertion_does_not_become_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            write_file(
                root,
                "docs/validation/reported.md",
                "# Validation\n\nResult: Passed\n",
            )
            contract = build_cli_authority_contract(
                root, evidence_visibility=("revision-content",)
            )
            validation = self.by_role(contract, "validation")[0]
            self.assertEqual(validation["claims"]["validation_evidence"], "unknown")
            self.assertNotIn("validation_assertion", validation["claims"])
            self.assertIn("validated", validation["must_not_infer"])
            self.assertFalse(validation["evidence_provenance"][0]["visible"])

    def test_legacy_shadow_embeds_full_contract_without_switching(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-cli-claims-") as temporary:
            root = Path(temporary)
            self.write_fixture(root)
            report = build_authority_shadow(root)
            self.assertEqual(
                report["candidate_contract"]["contract_version"],
                AUTHORITY_OBSERVATION_CONTRACT,
            )
            self.assertEqual(report["comparison"]["status"], "match")
            self.assertEqual(report["production_authority"], "legacy-cli")
            self.assertFalse(report["production_behavior_switched"])
            self.assertFalse(
                report["candidate_contract"]["production_behavior_switched"]
            )

    def test_self_host_repository_has_no_unresolved_normative_relation(self) -> None:
        contract = build_cli_authority_contract(REPOSITORY_ROOT)
        self.assertEqual(contract["decision_graph"]["status"], "evaluated")
        self.assertEqual(contract["unresolved_relations"], [])
        self.assertGreaterEqual(len(self.by_role(contract, "adr")), 11)
        self.assertGreaterEqual(len(self.by_role(contract, "validation")), 40)
        self.assertEqual(
            contract["decision_graph"]["result"]["relations"]["ADR-0011"],
            {"amends": ["ADR-0009"]},
        )
        self.assertTrue(
            all(
                document["claims"].get("validation_evidence") == "unknown"
                for document in self.by_role(contract, "validation")
            )
        )


if __name__ == "__main__":
    unittest.main()
