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
    create_worktree,
    credential_is_current,
    inspect_primary_write_guard,
    inspect_worktree_status,
    inspect_worktree_identity,
    load_subsystem_registry,
    remove_member,
    resolve_integration_oid,
    validate_collaboration_contract,
    worktree_session_path,
    write_workstream_session,
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

    def test_worktree_status_is_read_only_and_private_sessions_cover_linked_and_clone(self) -> None:
        with CollaborationGitFixture() as fixture:
            sessions = []
            for root in (fixture.worktree_b, fixture.clone):
                with self.subTest(root=root.name):
                    before = fixture.git(root, "status", "--porcelain", "--untracked-files=all").stdout
                    with mock.patch.object(
                        socket, "socket", side_effect=AssertionError("network socket opened")
                    ), mock.patch.object(
                        socket, "create_connection", side_effect=AssertionError("network connection opened")
                    ):
                        status = inspect_worktree_status(root)
                    self.assertEqual(
                        set(status),
                        {"status_schema_version", "identity", "session", "writes_performed"},
                    )
                    self.assertEqual(status["status_schema_version"], 1)
                    self.assertFalse(status["writes_performed"])
                    self.assertEqual(status["session"]["state"], "absent")
                    expected_text = fixture.git(
                        root, "rev-parse", "--git-path", "orrery/worktree.json"
                    ).stdout.strip()
                    expected = Path(expected_text)
                    if not expected.is_absolute():
                        expected = root / expected
                    self.assertEqual(worktree_session_path(root), expected.absolute())
                    self.assertFalse(expected.exists())

                    written = write_workstream_session(
                        root,
                        workstream_id=f"W1-{root.name}",
                        primary_subsystem_id="project-structure",
                        expected_writes=["packages/project-orrery-core/"],
                        captured_at="2026-08-22T00:00:00Z",
                    )
                    self.assertTrue(written["writes_performed"])
                    self.assertEqual(Path(written["session_path"]), expected.absolute())
                    self.assertTrue(expected.is_file())
                    refreshed = inspect_worktree_status(root)
                    self.assertEqual(refreshed["session"]["state"], "current")
                    self.assertEqual(refreshed["session"]["stale_reasons"], [])
                    self.assertEqual(
                        refreshed["identity"]["dirty_fingerprint"],
                        refreshed["session"]["record"]["dirty_fingerprint"],
                    )
                    self.assertEqual(
                        fixture.git(root, "status", "--porcelain", "--untracked-files=all").stdout,
                        before,
                    )
                    sessions.append(refreshed["session"]["record"])
            for field in (
                "project_mode",
                "integration_ref",
                "primary_subsystem_id",
                "affected_subsystem_ids",
                "expected_writes",
                "governing_docs",
                "validation_surfaces",
                "visibility",
                "observability",
            ):
                self.assertEqual(sessions[0][field], sessions[1][field])
            self.assertNotEqual(sessions[0]["worktree_id"], sessions[1]["worktree_id"])

    def test_session_staleness_tracks_branch_head_integration_and_dirty_fingerprint(self) -> None:
        with CollaborationGitFixture() as fixture:
            root = fixture.worktree_b
            write_workstream_session(
                root,
                workstream_id="W1-stale",
                primary_subsystem_id="project-structure",
                captured_at="2026-08-22T00:00:00Z",
            )

            dirty_path = root / "dirty.txt"
            dirty_path.write_text("dirty\n", encoding="utf-8")
            dirty_status = inspect_worktree_status(root)
            self.assertEqual(dirty_status["session"]["state"], "stale")
            self.assertEqual(
                dirty_status["session"]["stale_reasons"], ["dirty-fingerprint-changed"]
            )
            dirty_path.unlink()
            self.assertEqual(inspect_worktree_status(root)["session"]["state"], "current")

            fixture.git(root, "branch", "-m", "codex/fixture-renamed")
            branch_status = inspect_worktree_status(root)
            self.assertEqual(branch_status["session"]["stale_reasons"], ["branch-changed"])

        with CollaborationGitFixture() as fixture:
            root = fixture.worktree_b
            write_workstream_session(
                root,
                workstream_id="W1-head",
                primary_subsystem_id="project-structure",
                captured_at="2026-08-22T00:00:00Z",
            )
            changed = root / "head.txt"
            changed.write_text("head\n", encoding="utf-8")
            fixture.git(root, "add", "head.txt")
            fixture.git(root, "commit", "-m", "advance candidate head")
            self.assertEqual(
                inspect_worktree_status(root)["session"]["stale_reasons"], ["head-changed"]
            )

        with CollaborationGitFixture() as fixture:
            root = fixture.worktree_b
            write_workstream_session(
                root,
                workstream_id="W1-integration",
                primary_subsystem_id="project-structure",
                captured_at="2026-08-22T00:00:00Z",
            )
            integrated = fixture.repository / "integration.txt"
            integrated.write_text("integration\n", encoding="utf-8")
            fixture.git(fixture.repository, "add", "integration.txt")
            fixture.git(fixture.repository, "commit", "-m", "advance integration")
            status = inspect_worktree_status(root)
            self.assertEqual(status["session"]["stale_reasons"], ["integration-oid-changed"])
            self.assertEqual(status["identity"]["behind"], 1)

    def test_worktree_cli_has_stable_json_and_explicit_private_write(self) -> None:
        with CollaborationGitFixture() as fixture:
            environment = {
                **fixture.environment,
                "PYTHONPATH": os.pathsep.join(
                    (str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))
                ),
            }
            before = fixture.git(fixture.worktree_b, "status", "--porcelain").stdout
            base_command = [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", "worktree"]
            status = subprocess.run(
                [*base_command, "status", "--target", str(fixture.worktree_b), "--json"],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload["command"], "worktree-status")
            self.assertEqual(status_payload["versions"]["core"], "0.1.3")
            self.assertEqual(status_payload["versions"]["cli"], "0.1.8")
            self.assertEqual(status_payload["data"]["session"]["state"], "absent")
            self.assertFalse(status_payload["data"]["writes_performed"])

            write = subprocess.run(
                [
                    *base_command,
                    "session",
                    "write",
                    "--target",
                    str(fixture.worktree_b),
                    "--workstream-id",
                    "W1-cli",
                    "--primary-subsystem-id",
                    "project-structure",
                    "--expected-write",
                    "packages/",
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
            write_payload = json.loads(write.stdout)
            self.assertEqual(write_payload["command"], "worktree-session-write")
            self.assertTrue(write_payload["data"]["writes_performed"])
            self.assertTrue(Path(write_payload["data"]["session_path"]).is_file())
            self.assertEqual(
                fixture.git(fixture.worktree_b, "status", "--porcelain").stdout, before
            )

            refreshed = subprocess.run(
                [*base_command, "status", "--target", str(fixture.worktree_b), "--json"],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(refreshed.returncode, 0, refreshed.stdout + refreshed.stderr)
            self.assertEqual(json.loads(refreshed.stdout)["data"]["session"]["state"], "current")

    def test_primary_write_guard_blocks_clean_and_dirty_primary_but_allows_isolation(self) -> None:
        with CollaborationGitFixture() as fixture:
            with mock.patch.object(
                socket, "socket", side_effect=AssertionError("network socket opened")
            ), mock.patch.object(
                socket, "create_connection", side_effect=AssertionError("network connection opened")
            ):
                clean = inspect_primary_write_guard(fixture.repository)
                isolated = inspect_primary_write_guard(fixture.worktree_b)
            self.assertFalse(clean["allowed"])
            self.assertEqual(clean["reason"], "primary-worktree-write-prohibited")
            self.assertEqual(clean["recovery"], "create-or-connect-isolated-workstream")
            self.assertTrue(isolated["allowed"])
            self.assertEqual(isolated["reason"], "isolated-worktree")
            self.assertFalse(clean["writes_performed"])

            dirty = fixture.repository / "existing-author-change.txt"
            dirty.write_text("preserve me\n", encoding="utf-8")
            dirty_guard = inspect_primary_write_guard(fixture.repository)
            self.assertFalse(dirty_guard["allowed"])
            self.assertEqual(
                dirty_guard["reason"], "primary-worktree-dirty-recovery-required"
            )
            self.assertEqual(
                dirty_guard["recovery"], "review-and-selectively-transfer-existing-changes"
            )
            self.assertTrue(dirty.is_file())

    def test_create_worktree_pins_integration_and_preserves_dirty_primary(self) -> None:
        with CollaborationGitFixture() as fixture:
            dirty = fixture.repository / "existing-author-change.txt"
            dirty.write_text("preserve me\n", encoding="utf-8")
            before = fixture.git(
                fixture.repository, "status", "--porcelain", "--untracked-files=all"
            ).stdout
            integration_oid = fixture.git(fixture.repository, "rev-parse", "main").stdout.strip()
            target = fixture.root / "created-worktree"
            with mock.patch.object(
                socket, "socket", side_effect=AssertionError("network socket opened")
            ), mock.patch.object(
                socket, "create_connection", side_effect=AssertionError("network connection opened")
            ):
                result = create_worktree(
                    fixture.repository,
                    workstream_id="W1.2-create",
                    branch="codex/w1-2-created",
                    path=target,
                    primary_subsystem_id="project-structure",
                    expected_writes=["packages/"],
                )
            self.assertTrue(result["writes_performed"])
            self.assertTrue(result["source"]["dirty"])
            self.assertEqual(result["source"]["integration_oid"], integration_oid)
            self.assertEqual(result["branch"], "refs/heads/codex/w1-2-created")
            self.assertEqual(result["status"]["identity"]["head"], integration_oid)
            self.assertEqual(result["status"]["identity"]["dirty"], False)
            self.assertFalse(result["status"]["identity"]["is_primary"])
            self.assertEqual(result["status"]["session"]["state"], "current")
            self.assertEqual(
                result["status"]["session"]["record"]["lifecycle_phase"], "created"
            )
            self.assertEqual(
                fixture.git(fixture.repository, "status", "--porcelain", "--untracked-files=all").stdout,
                before,
            )
            self.assertNotEqual(
                fixture.git(target, "rev-parse", "--absolute-git-dir").stdout.strip(),
                fixture.git(fixture.repository, "rev-parse", "--absolute-git-dir").stdout.strip(),
            )
            self.assertEqual(
                Path(
                    fixture.git(
                        target, "rev-parse", "--path-format=absolute", "--git-common-dir"
                    ).stdout.strip()
                ).resolve(),
                Path(
                    fixture.git(
                        fixture.repository,
                        "rev-parse",
                        "--path-format=absolute",
                        "--git-common-dir",
                    ).stdout.strip()
                ).resolve(),
            )

    def test_create_worktree_collisions_and_session_failure_leave_no_partial_state(self) -> None:
        with CollaborationGitFixture() as fixture:
            existing_path = fixture.root / "existing-path"
            existing_path.mkdir()
            with self.assertRaisesRegex(ValueError, "path already exists"):
                create_worktree(
                    fixture.repository,
                    workstream_id="W1.2-path",
                    branch="codex/w1-2-path",
                    path=existing_path,
                    primary_subsystem_id="project-structure",
                )
            self.assertNotEqual(
                fixture.git(
                    fixture.repository,
                    "show-ref",
                    "--verify",
                    "--quiet",
                    "refs/heads/codex/w1-2-path",
                    check=False,
                ).returncode,
                0,
            )

            fixture.git(fixture.repository, "branch", "codex/w1-2-existing", "main")
            with self.assertRaisesRegex(ValueError, "branch already exists"):
                create_worktree(
                    fixture.repository,
                    workstream_id="W1.2-branch",
                    branch="codex/w1-2-existing",
                    path=fixture.root / "branch-collision",
                    primary_subsystem_id="project-structure",
                )

            rollback_target = fixture.root / "rollback-worktree"
            with mock.patch(
                "project_orrery_core.collaboration.write_workstream_session",
                side_effect=ValueError("injected private session failure"),
            ), self.assertRaisesRegex(ValueError, "rolled back"):
                create_worktree(
                    fixture.repository,
                    workstream_id="W1.2-rollback",
                    branch="codex/w1-2-rollback",
                    path=rollback_target,
                    primary_subsystem_id="project-structure",
                )
            self.assertFalse(rollback_target.exists())
            self.assertNotIn(
                str(rollback_target),
                fixture.git(fixture.repository, "worktree", "list", "--porcelain").stdout,
            )
            self.assertNotEqual(
                fixture.git(
                    fixture.repository,
                    "show-ref",
                    "--verify",
                    "--quiet",
                    "refs/heads/codex/w1-2-rollback",
                    check=False,
                ).returncode,
                0,
            )

    def test_create_worktree_rolls_back_if_integration_ref_drifts(self) -> None:
        with CollaborationGitFixture() as fixture:
            target = fixture.root / "drift-worktree"
            original_write = write_workstream_session

            def advance_integration_then_write(root: Path, **fields: object) -> dict[str, object]:
                changed = fixture.repository / "integration-drift.txt"
                changed.write_text("advanced\n", encoding="utf-8")
                fixture.git(fixture.repository, "add", "integration-drift.txt")
                fixture.git(fixture.repository, "commit", "-m", "advance integration during create")
                return original_write(root, **fields)

            with mock.patch(
                "project_orrery_core.collaboration.write_workstream_session",
                side_effect=advance_integration_then_write,
            ), self.assertRaisesRegex(ValueError, "integration ref changed"):
                create_worktree(
                    fixture.repository,
                    workstream_id="W1.2-drift",
                    branch="codex/w1-2-drift",
                    path=target,
                    primary_subsystem_id="project-structure",
                )
            self.assertFalse(target.exists())
            self.assertNotEqual(
                fixture.git(
                    fixture.repository,
                    "show-ref",
                    "--verify",
                    "--quiet",
                    "refs/heads/codex/w1-2-drift",
                    check=False,
                ).returncode,
                0,
            )

    def test_worktree_create_and_guard_cli_use_stable_json_and_exit_codes(self) -> None:
        with CollaborationGitFixture() as fixture:
            environment = {
                **fixture.environment,
                "PYTHONPATH": os.pathsep.join(
                    (str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))
                ),
            }
            base = [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", "worktree"]
            blocked = subprocess.run(
                [*base, "guard", "--target", str(fixture.repository), "--json"],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(blocked.returncode, 5, blocked.stdout + blocked.stderr)
            blocked_payload = json.loads(blocked.stdout)
            self.assertEqual(blocked_payload["command"], "worktree-primary-write-guard")
            self.assertEqual(blocked_payload["status"], "warning")
            self.assertFalse(blocked_payload["data"]["allowed"])

            target = fixture.root / "cli-created"
            created = subprocess.run(
                [
                    *base,
                    "create",
                    "W1.2-cli",
                    "--target",
                    str(fixture.repository),
                    "--branch",
                    "codex/w1-2-cli",
                    "--path",
                    str(target),
                    "--from",
                    "refs/heads/main",
                    "--primary-subsystem-id",
                    "project-structure",
                    "--json",
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            payload = json.loads(created.stdout)
            self.assertEqual(payload["command"], "worktree-create")
            self.assertEqual(payload["versions"]["core"], "0.1.3")
            self.assertEqual(payload["versions"]["cli"], "0.1.8")
            self.assertEqual(payload["data"]["status"]["session"]["state"], "current")

            allowed = subprocess.run(
                [*base, "guard", "--target", str(target), "--json"],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
            self.assertTrue(json.loads(allowed.stdout)["data"]["allowed"])


if __name__ == "__main__":
    unittest.main()
