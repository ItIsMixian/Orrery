from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
SCHEMA = CORE_SOURCE / "project_orrery_core" / "schema" / "collaboration-v1.json"

sys.path.insert(0, str(CORE_SOURCE))
sys.path.insert(0, str(CLI_SOURCE))
sys.path.insert(0, str(REPOSITORY_ROOT))

from project_orrery_core.collaboration import (  # noqa: E402
    CAPABILITIES,
    COLLABORATION_CONTRACT_ID,
    DEFAULT_INTEGRATION_REF,
    RESERVED_SUBSYSTEM_IDS,
    CollaborationConfig,
    apply_capability_change,
    bootstrap_maintainer,
    build_project_mode_contract,
    build_scope_contract,
    credential_is_current,
    inspect_worktree_identity,
    load_subsystem_registry,
    remove_member,
    resolve_integration_oid,
    validate_collaboration_contract,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


class CollaborationContractTests(unittest.TestCase):
    def test_schema_bundle_freezes_all_phase_zero_contracts(self) -> None:
        payload = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(payload["$id"], COLLABORATION_CONTRACT_ID)
        self.assertEqual(payload["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            set(payload["$defs"]),
            {
                "capability_audit",
                "integration_report",
                "member",
                "overlap_finding",
                "project_mode",
                "scope",
                "subsystem_registry",
                "workstream_session",
                "worktree_identity",
            },
        )
        serialized = json.dumps(payload).lower()
        for forbidden in ("codex", "claude", "prompt", "transcript", "source_code", "unpush_diff"):
            self.assertNotIn(forbidden, serialized)
        for definition in payload["$defs"].values():
            self.assertFalse(definition.get("additionalProperties", True))

    def test_fixture_has_main_two_linked_worktrees_clone_untracked_and_unpushed(self) -> None:
        with CollaborationGitFixture() as fixture:
            records = fixture.git(fixture.repository, "worktree", "list", "--porcelain").stdout
            self.assertEqual(records.count("worktree "), 3)
            self.assertEqual(fixture.git(fixture.repository, "status", "--porcelain").stdout, "")
            self.assertIn(
                "untracked/same-path.txt",
                fixture.git(
                    fixture.worktree_a, "status", "--porcelain", "--untracked-files=all"
                ).stdout,
            )
            self.assertEqual(fixture.git(fixture.worktree_b, "status", "--porcelain").stdout, "")
            self.assertEqual(fixture.git(fixture.clone, "status", "--porcelain").stdout, "")
            self.assertEqual(
                fixture.git(fixture.clone, "rev-list", "--count", "origin/main..HEAD").stdout.strip(),
                "1",
            )
            linked_common = fixture.git(fixture.worktree_a, "rev-parse", "--git-common-dir").stdout.strip()
            clone_common = fixture.git(fixture.clone, "rev-parse", "--git-common-dir").stdout.strip()
            self.assertNotEqual(Path(linked_common), Path(clone_common))

    def test_integration_ref_default_and_oid_resolution_are_local_and_exact(self) -> None:
        with CollaborationGitFixture() as fixture:
            config = CollaborationConfig.from_manifest({})
            self.assertEqual(config.integration_ref, DEFAULT_INTEGRATION_REF)
            expected = fixture.git(fixture.repository, "rev-parse", "main").stdout.strip()
            self.assertEqual(resolve_integration_oid(fixture.repository, config.integration_ref), expected)
            fixture.git(fixture.repository, "tag", "fixture-tag")
            with self.assertRaisesRegex(ValueError, "local branch ref"):
                CollaborationConfig.from_manifest(
                    {"collaboration": {"integration_ref": "refs/tags/fixture-tag"}}
                )
            with self.assertRaisesRegex(ValueError, "cannot resolve integration ref"):
                resolve_integration_oid(fixture.repository, "refs/heads/missing")

    def test_primary_worktree_defaults_to_git_main_and_allows_listed_override(self) -> None:
        with CollaborationGitFixture() as fixture:
            default_identity = inspect_worktree_identity(
                fixture.worktree_b, CollaborationConfig.from_manifest({})
            )
            self.assertFalse(default_identity["is_primary"])
            self.assertEqual(default_identity["primary_worktree_source"], "git-main-worktree")
            self.assertEqual(
                Path(default_identity["primary_worktree_path"]), fixture.repository.resolve()
            )

            overridden = inspect_worktree_identity(
                fixture.worktree_b,
                CollaborationConfig.from_manifest(
                    {"collaboration": {"primary_worktree": str(fixture.worktree_b)}}
                ),
            )
            self.assertTrue(overridden["is_primary"])
            self.assertEqual(overridden["primary_worktree_source"], "maintainer-override")
            with self.assertRaisesRegex(ValueError, "listed Git worktree"):
                inspect_worktree_identity(
                    fixture.worktree_b,
                    CollaborationConfig.from_manifest(
                        {"collaboration": {"primary_worktree": str(fixture.root / "missing")}}
                    ),
                )

    def test_subsystem_registry_projects_explicit_agent_index_without_creating_state(self) -> None:
        with CollaborationGitFixture() as fixture:
            registry = load_subsystem_registry(fixture.repository)
            self.assertEqual(registry["entries"][0]["subsystem_id"], "project-structure")
            self.assertEqual(set(registry["reserved_scope_ids"]), set(RESERVED_SUBSYSTEM_IDS))
            missing = fixture.repository / "docs" / "state" / "missing.md"
            agents = fixture.repository / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8")
                + "\n## missing\n\n**ID**: `missing`\n\n**Dig**: [State](docs/state/missing.md).\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "existing State Doc"):
                load_subsystem_registry(fixture.repository)
            self.assertFalse(missing.exists())

    def test_scope_supports_mapped_unmapped_and_project_wide_without_registry_mutation(self) -> None:
        with CollaborationGitFixture() as fixture:
            registry = load_subsystem_registry(fixture.repository)
            before = json.dumps(registry, sort_keys=True)
            mapped = build_scope_contract(
                workstream_id="PO-WT-001",
                revision=1,
                primary_subsystem_id="project-structure",
                affected_subsystem_ids=[],
                registry=registry,
            )
            unmapped = build_scope_contract(
                workstream_id="PO-WT-002",
                revision=1,
                primary_subsystem_id="unmapped",
                affected_subsystem_ids=[],
                registry=registry,
            )
            project_wide = build_scope_contract(
                workstream_id="PO-WT-003",
                revision=1,
                primary_subsystem_id="project-wide",
                affected_subsystem_ids=["project-structure"],
                registry=registry,
            )
            self.assertEqual(mapped["scope_kind"], "mapped")
            self.assertEqual(unmapped["scope_kind"], "unmapped")
            self.assertEqual(project_wide["scope_kind"], "project-wide")
            self.assertEqual(json.dumps(registry, sort_keys=True), before)
            with self.assertRaisesRegex(ValueError, "unknown subsystem"):
                build_scope_contract(
                    workstream_id="PO-WT-004",
                    revision=1,
                    primary_subsystem_id="invented",
                    affected_subsystem_ids=[],
                    registry=registry,
                )

    def test_member_capabilities_are_composable_audited_and_revoke_local_credentials(self) -> None:
        member = bootstrap_maintainer("maintainer")
        validate_collaboration_contract(member)
        self.assertEqual(member["base_role"], "member")
        self.assertEqual(set(member["capabilities"]), set(CAPABILITIES))
        initial_epoch = member["credential_epoch"]
        changed = apply_capability_change(
            member,
            actor_id="maintainer",
            action="revoke",
            capability="reviewer",
            occurred_at="2026-08-21T00:00:00Z",
        )
        self.assertNotIn("reviewer", changed["capabilities"])
        self.assertEqual(changed["credential_epoch"], initial_epoch + 1)
        self.assertFalse(credential_is_current(changed, initial_epoch))
        self.assertFalse(credential_is_current(changed, True))
        self.assertEqual(changed["audit"][-1]["actor_id"], "maintainer")
        validate_collaboration_contract(changed)
        removed = remove_member(
            changed, actor_id="maintainer", occurred_at="2026-08-21T00:01:00Z"
        )
        self.assertEqual(removed["status"], "removed")
        self.assertEqual(removed["credential_state"], "revoked")
        self.assertEqual(removed["capabilities"], [])
        validate_collaboration_contract(removed)

    def test_session_finding_and_integration_report_samples_validate_and_reject_extra_data(self) -> None:
        oid = "a" * 40
        samples = [
            {
                "schema_version": 1,
                "contract_type": "workstream-session",
                "project_mode": "personal",
                "workstream_id": "PO-WT-001",
                "worktree_id": "local-1",
                "member_id": "local-owner",
                "host_id": "local-host",
                "active_host_id": "local-host",
                "platform_session": None,
                "branch": "refs/heads/codex/example",
                "head": oid,
                "integration_ref": "refs/heads/main",
                "integration_oid": oid,
                "merge_base": oid,
                "lifecycle_phase": "implementing",
                "runtime_condition": "active",
                "scope_revision": 1,
                "primary_subsystem_id": "project-structure",
                "affected_subsystem_ids": [],
                "expected_writes": ["packages/"],
                "governing_docs": ["docs/state/project-structure.md"],
                "validation_surfaces": ["python -m unittest"],
                "visibility": "worktree-local",
                "observability": "local",
                "captured_at": "2026-08-21T00:00:00Z",
            },
            {
                "schema_version": 1,
                "contract_type": "overlap-finding",
                "finding_id": "finding-1",
                "kind": "unknown",
                "disposition": "open",
                "severity": "l2",
                "workstream_ids": ["PO-WT-001"],
                "path_evidence": [],
                "authority_surfaces": [],
                "validation_surfaces": [],
                "required_member_ids": ["local-owner"],
                "acknowledgements": [],
                "member_id": "local-owner",
                "host_id": "local-host",
                "visibility": "local-only",
                "observability": "unknown",
                "created_at": "2026-08-21T00:00:00Z",
            },
            {
                "schema_version": 1,
                "contract_type": "integration-report",
                "report_id": "report-1",
                "candidate_head": oid,
                "target_ref": "refs/heads/main",
                "target_oid": oid,
                "merge_base": oid,
                "scope_revision": 1,
                "finding_ids": ["finding-1"],
                "validations": [
                    {
                        "command": "python -m unittest",
                        "result": "passed",
                        "evidence_ref": "docs/validation/example.md",
                        "completed_at": "2026-08-21T00:00:00Z",
                    }
                ],
                "state_alignment": "unknown",
                "result": "blocked",
                "member_id": "local-owner",
                "host_id": "local-host",
                "visibility": "worktree-local",
                "observability": "local",
                "generated_at": "2026-08-21T00:00:00Z",
            },
        ]
        for sample in samples:
            with self.subTest(contract_type=sample["contract_type"]):
                validate_collaboration_contract(sample)
        invalid = dict(samples[1])
        invalid["source_code"] = "forbidden"
        with self.assertRaisesRegex(ValueError, "forbidden field source_code"):
            validate_collaboration_contract(invalid)

    def test_personal_default_and_team_contract_never_start_network_runtime(self) -> None:
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network socket opened")), mock.patch.object(
            socket, "create_connection", side_effect=AssertionError("network connection opened")
        ):
            personal = build_project_mode_contract(CollaborationConfig.from_manifest({}))
            team = build_project_mode_contract(
                CollaborationConfig.from_manifest({"collaboration": {"project_mode": "team"}})
            )
        self.assertEqual(personal["project_mode"], "personal")
        self.assertEqual(personal["member_identity"], "implicit-local")
        self.assertEqual(personal["active_network_features"], [])
        self.assertFalse(any(personal["network_boundaries"].values()))
        self.assertEqual(team["project_mode"], "team")
        self.assertEqual(team["runtime_status"], "contract-only")
        self.assertEqual(team["active_network_features"], [])

    def test_cli_contract_inspection_is_json_local_only_and_write_free(self) -> None:
        with CollaborationGitFixture() as fixture:
            before = fixture.git(fixture.repository, "status", "--porcelain").stdout
            environment = dict(fixture.environment)
            command = [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "project_orrery_cli",
                "collaboration-contract",
                "--target",
                str(fixture.repository),
                "--json",
            ]
            completed = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                env={
                    **environment,
                    "PYTHONPATH": os.pathsep.join(
                        (str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))
                    ),
                },
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "collaboration-contract")
            self.assertEqual(payload["data"]["contract_id"], COLLABORATION_CONTRACT_ID)
            self.assertEqual(payload["data"]["mode"]["project_mode"], "personal")
            self.assertEqual(payload["data"]["mode"]["active_network_features"], [])
            self.assertNotIn("prompt", json.dumps(payload).lower())
            self.assertEqual(fixture.git(fixture.repository, "status", "--porcelain").stdout, before)


if __name__ == "__main__":
    unittest.main()
