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
    attach_platform_session,
    acknowledge_overlap_finding,
    collect_scope_observation,
    compute_overlap_findings,
    apply_capability_change,
    bootstrap_maintainer,
    build_project_mode_contract,
    build_scope_contract,
    create_worktree,
    credential_is_current,
    inspect_primary_write_guard,
    inspect_worktree_overlap,
    inspect_worktree_status,
    inspect_worktree_identity,
    load_adapter_capabilities,
    load_subsystem_registry,
    remove_member,
    plan_adapter_session_route,
    reconcile_overlap_findings,
    refresh_workstream_scope,
    resolve_integration_oid,
    transition_workstream_session,
    validate_collaboration_contract,
    worktree_session_path,
    write_workstream_session,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


class CollaborationContractTests(unittest.TestCase):
    def assertSameFilesystemPath(self, left: Path, right: Path) -> None:  # noqa: N802
        self.assertEqual(
            os.path.normcase(os.path.realpath(os.path.abspath(left))),
            os.path.normcase(os.path.realpath(os.path.abspath(right))),
        )

    def test_schema_bundle_freezes_all_phase_zero_contracts(self) -> None:
        payload = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(payload["$id"], COLLABORATION_CONTRACT_ID)
        self.assertEqual(payload["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            set(payload["$defs"]),
            {
                "capability_audit",
                "adapter_capabilities",
                "integration_report",
                "member",
                "overlap_finding",
                "path_evidence",
                "project_mode",
                "review_binding",
                "review_decision",
                "review_package",
                "review_risk",
                "scope",
                "scope_observation",
                "scope_path",
                "stacked_lineage",
                "subsystem_registry",
                "workstream_session",
                "worktree_identity",
                "closure_record",
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
                    self.assertSameFilesystemPath(worktree_session_path(root), expected)
                    self.assertFalse(expected.exists())

                    written = write_workstream_session(
                        root,
                        workstream_id=f"W1-{root.name}",
                        primary_subsystem_id="project-structure",
                        expected_writes=["packages/project-orrery-core/"],
                        captured_at="2026-08-22T00:00:00Z",
                    )
                    self.assertTrue(written["writes_performed"])
                    self.assertSameFilesystemPath(Path(written["session_path"]), expected)
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
            self.assertEqual(status_payload["versions"]["core"], "0.1.20")
            self.assertEqual(status_payload["versions"]["cli"], "0.1.22")
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
            self.assertEqual(payload["versions"]["core"], "0.1.20")
            self.assertEqual(payload["versions"]["cli"], "0.1.22")
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

    def test_lifecycle_transitions_are_legal_separate_and_fail_closed_at_future_gates(self) -> None:
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W1.3-lifecycle",
                primary_subsystem_id="project-structure",
                lifecycle_phase="created",
            )
            transitioned = transition_workstream_session(
                fixture.worktree_b,
                lifecycle_phase="investigating",
                runtime_condition="waiting-for-user",
                evidence_freshness="stale",
                reason="need maintainer input",
                occurred_at="2026-08-22T00:00:00Z",
            )["session"]
            self.assertEqual(transitioned["lifecycle_phase"], "investigating")
            self.assertEqual(transitioned["runtime_condition"], "waiting-for-user")
            self.assertEqual(transitioned["evidence_freshness"], "stale")
            self.assertEqual(transitioned["lifecycle_revision"], 2)
            self.assertEqual(transitioned["last_transition"]["from_phase"], "created")

            with self.assertRaisesRegex(ValueError, "illegal Workstream lifecycle transition"):
                transition_workstream_session(
                    fixture.worktree_b,
                    lifecycle_phase="validating",
                    reason="skip implementation",
                )
            transition_workstream_session(
                fixture.worktree_b, lifecycle_phase="implementing", reason="resume implementation"
            )
            transition_workstream_session(
                fixture.worktree_b, lifecycle_phase="validating", reason="run validation"
            )
            with self.assertRaisesRegex(ValueError, "future executable review gate"):
                transition_workstream_session(
                    fixture.worktree_b,
                    lifecycle_phase="review-ready",
                    evidence_freshness="current",
                    reason="self reported",
                )
            with self.assertRaisesRegex(ValueError, "explicit closure reason"):
                transition_workstream_session(
                    fixture.worktree_b, lifecycle_phase="closed", reason="stop"
                )
            closed = transition_workstream_session(
                fixture.worktree_b,
                lifecycle_phase="closed",
                closure_reason="abandoned",
                reason="maintainer stopped the workstream",
            )["session"]
            self.assertEqual(closed["closure_reason"], "abandoned")
            with self.assertRaisesRegex(ValueError, "not legal for a finished Workstream"):
                attach_platform_session(
                    fixture.worktree_b,
                    adapter_manifest=REPOSITORY_ROOT
                    / "adapters"
                    / "codex"
                    / "adapter-manifest.json",
                    platform_session_id="too-late",
                )

    def test_stale_git_binding_revokes_effective_review_ready_without_mutating_session(self) -> None:
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W1.3-review-revocation",
                primary_subsystem_id="project-structure",
                lifecycle_phase="review-ready",
                evidence_freshness="current",
            )
            current = inspect_worktree_status(fixture.worktree_b)
            self.assertEqual(current["session"]["lifecycle"]["effective_phase"], "review-ready")
            (fixture.worktree_b / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            stale = inspect_worktree_status(fixture.worktree_b)
            self.assertEqual(stale["session"]["state"], "stale")
            self.assertEqual(stale["session"]["lifecycle"]["effective_phase"], "validating")
            self.assertTrue(stale["session"]["lifecycle"]["review_ready_revoked"])
            self.assertEqual(stale["session"]["record"]["lifecycle_phase"], "review-ready")

    def test_adapter_route_attach_and_no_rebind_fallback_are_private_and_zero_network(self) -> None:
        manifest = REPOSITORY_ROOT / "adapters" / "codex" / "adapter-manifest.json"
        harness_manifest = REPOSITORY_ROOT / "adapters" / "harness-json" / "adapter-manifest.json"
        capabilities = load_adapter_capabilities(manifest)
        self.assertTrue(capabilities["attach"])
        self.assertFalse(capabilities["rebind"])
        self.assertFalse(load_adapter_capabilities(harness_manifest)["attach"])
        for adapter in ("claude-code", "deepseek-harness"):
            declared = load_adapter_capabilities(
                REPOSITORY_ROOT / "adapters" / adapter / "adapter-manifest.json"
            )
            self.assertTrue(declared["attach"])
            self.assertFalse(declared["launch"])
            self.assertFalse(declared["rebind"])
            self.assertFalse(declared["message"])
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W1.3-route",
                primary_subsystem_id="project-structure",
                lifecycle_phase="created",
            )
            planned = plan_adapter_session_route(
                fixture.worktree_b,
                adapter_manifest=manifest,
                platform_session_id="session-1",
            )
            self.assertFalse(planned["allowed"])
            self.assertEqual(planned["reason"], "platform-session-attach-required")
            self.assertFalse(planned["writes_performed"])
            self.assertFalse(planned["network_performed"])
            attached = attach_platform_session(
                fixture.worktree_b,
                adapter_manifest=manifest,
                platform_session_id="session-1",
            )
            self.assertEqual(attached["session"]["lifecycle_phase"], "investigating")
            self.assertEqual(attached["session"]["platform_session"]["session_id"], "session-1")
            allowed = plan_adapter_session_route(
                fixture.worktree_b,
                adapter_manifest=manifest,
                platform_session_id="session-1",
            )
            self.assertTrue(allowed["allowed"])
            self.assertEqual(allowed["reason"], "platform-session-attached")
            fallback = plan_adapter_session_route(
                fixture.worktree_b,
                adapter_manifest=manifest,
                platform_session_id="session-2",
            )
            self.assertEqual(fallback["reason"], "adapter-rebind-unavailable")
            self.assertEqual(
                fallback["next_action"], "create-new-workstream-and-open-new-platform-session"
            )
            with self.assertRaisesRegex(ValueError, "does not support platform-session rebind"):
                attach_platform_session(
                    fixture.worktree_b,
                    adapter_manifest=manifest,
                    platform_session_id="session-2",
                    rebind=True,
                )
            primary = plan_adapter_session_route(
                fixture.repository,
                adapter_manifest=manifest,
                platform_session_id="session-primary",
            )
            self.assertEqual(primary["reason"], "primary-worktree-write-prohibited")

    def test_lifecycle_and_adapter_cli_commands_have_stable_json_and_fail_closed_routes(self) -> None:
        manifest = REPOSITORY_ROOT / "adapters" / "codex" / "adapter-manifest.json"
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W1.3-cli",
                primary_subsystem_id="project-structure",
                lifecycle_phase="created",
            )
            environment = {
                **fixture.environment,
                "PYTHONPATH": os.pathsep.join(
                    (str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))
                ),
            }
            base = [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", "worktree"]

            def run(*arguments: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [*base, *arguments, "--json"],
                    cwd=REPOSITORY_ROOT,
                    env=environment,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )

            route = run(
                "route",
                "--target",
                str(fixture.worktree_b),
                "--adapter-manifest",
                str(manifest),
                "--platform-session-id",
                "cli-session",
            )
            self.assertEqual(route.returncode, 5, route.stdout + route.stderr)
            route_payload = json.loads(route.stdout)
            self.assertEqual(route_payload["command"], "worktree-session-route")
            self.assertEqual(route_payload["data"]["reason"], "platform-session-attach-required")
            self.assertFalse(route_payload["data"]["writes_performed"])

            attach = run(
                "session",
                "attach",
                "--target",
                str(fixture.worktree_b),
                "--adapter-manifest",
                str(manifest),
                "--platform-session-id",
                "cli-session",
            )
            self.assertEqual(attach.returncode, 0, attach.stdout + attach.stderr)
            attach_payload = json.loads(attach.stdout)
            self.assertEqual(attach_payload["command"], "worktree-session-attach")
            self.assertTrue(attach_payload["data"]["writes_performed"])

            allowed = run(
                "route",
                "--target",
                str(fixture.worktree_b),
                "--adapter-manifest",
                str(manifest),
                "--platform-session-id",
                "cli-session",
            )
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
            self.assertTrue(json.loads(allowed.stdout)["data"]["allowed"])

            transition = run(
                "session",
                "transition",
                "--target",
                str(fixture.worktree_b),
                "--phase",
                "implementing",
                "--reason",
                "begin CLI implementation",
            )
            self.assertEqual(transition.returncode, 0, transition.stdout + transition.stderr)
            transition_payload = json.loads(transition.stdout)
            self.assertEqual(transition_payload["command"], "worktree-session-transition")
            self.assertEqual(transition_payload["data"]["session"]["lifecycle_phase"], "implementing")

    def test_w2_collects_all_path_sources_and_derives_authority_subsystems_and_resources(self) -> None:
        with CollaborationGitFixture() as fixture:
            root = fixture.worktree_a
            committed = root / "packages" / "committed.py"
            committed.parent.mkdir()
            committed.write_text("committed\n", encoding="utf-8")
            fixture.git(root, "add", "packages/committed.py")
            fixture.git(root, "commit", "-m", "candidate committed path")
            staged = root / "packages" / "staged.py"
            staged.write_text("staged\n", encoding="utf-8")
            fixture.git(root, "add", "packages/staged.py")
            (root / "README.md").write_text("# fixture\nunstaged\n", encoding="utf-8")
            write_workstream_session(
                root,
                workstream_id="W2-collect",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=[
                    "packages/expected.py",
                    "packages/",
                    "docs/state/project-structure.md",
                    "packages/component-versions.json",
                    "packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json",
                ],
                captured_at="2026-08-22T01:00:00Z",
            )
            with mock.patch.object(
                socket, "socket", side_effect=AssertionError("network socket opened")
            ), mock.patch.object(
                socket, "create_connection", side_effect=AssertionError("network connection opened")
            ):
                scope = collect_scope_observation(root, captured_at="2026-08-22T01:01:00Z")
            entries = {entry["path"]: entry for entry in scope["path_entries"]}
            self.assertIn("committed", entries["packages/committed.py"]["sources"])
            self.assertIn("staged", entries["packages/staged.py"]["sources"])
            self.assertIn("unstaged", entries["README.md"]["sources"])
            self.assertIn("untracked", entries["untracked/same-path.txt"]["sources"])
            self.assertIn("expected", entries["packages/expected.py"]["sources"])
            self.assertIn("expected", entries["packages/**"]["sources"])
            self.assertIn(
                "release-and-toolchain", entries["packages/expected.py"]["subsystem_ids"]
            )
            self.assertIn(
                "state:docs/state/project-structure.md",
                entries["docs/state/project-structure.md"]["authority_surfaces"],
            )
            self.assertIn(
                "schema-migration",
                entries[
                    "packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json"
                ]["exclusive_resource_ids"],
            )
            self.assertIn(
                "release", entries["packages/component-versions.json"]["exclusive_resource_ids"]
            )
            validate_collaboration_contract(scope)

    def test_w2_direct_authority_semantic_unknown_and_source_provenance(self) -> None:
        with CollaborationGitFixture() as fixture:
            for root, workstream in (
                (fixture.worktree_a, "W2-a"),
                (fixture.worktree_b, "W2-b"),
            ):
                same = root / "overlap" / "same.txt"
                same.parent.mkdir()
                same.write_text(workstream, encoding="utf-8")
                write_workstream_session(
                    root,
                    workstream_id=workstream,
                    primary_subsystem_id="release-and-toolchain",
                    expected_writes=["docs/state/project-structure.md"],
                    validation_surfaces=["python -m unittest tests.test_collaboration_contract"],
                    member_id=f"member-{workstream[-1]}",
                    captured_at="2026-08-22T02:00:00Z",
                )
            left = collect_scope_observation(fixture.worktree_a)
            right = collect_scope_observation(fixture.worktree_b)
            report = compute_overlap_findings(
                [left, right],
                unavailable_peers=[
                    {
                        "workstream_id": "W2-remote",
                        "member_id": "member-remote",
                        "reason": "sharing-off",
                    }
                ],
            )
            kinds = {finding["kind"] for finding in report["findings"]}
            self.assertEqual(kinds, {"direct", "authority", "semantic", "unknown"})
            direct = next(
                finding
                for finding in report["findings"]
                if finding["kind"] == "direct"
                and "overlap/same.txt" in finding["path_evidence"]
            )
            self.assertEqual(direct["severity"], "l3")
            self.assertEqual(
                {item["workstream_id"] for item in direct["path_provenance"]}, {"W2-a", "W2-b"}
            )
            self.assertTrue(all("untracked" in item["sources"] for item in direct["path_provenance"]))
            unknown = next(item for item in report["findings"] if item["kind"] == "unknown")
            self.assertEqual(unknown["observability"], "unavailable")
            self.assertTrue(unknown["review_ready_blocked"])
            self.assertFalse(report["network_performed"])

    def test_w2_scope_expansion_b_l1_l2_and_l3_are_local_and_fail_closed(self) -> None:
        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-l1",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/new.py"],
                captured_at="2026-08-22T03:00:00Z",
            )
            l1 = refresh_workstream_scope(
                fixture.worktree_b,
                include_local_worktrees=False,
                occurred_at="2026-08-22T03:01:00Z",
            )
            self.assertEqual(l1["expansion"]["level"], "l1")
            self.assertTrue(l1["expansion"]["allowed"])
            self.assertEqual(l1["session"]["scope_revision"], 2)
            self.assertFalse(l1["network_performed"])

        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-l2",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["tests/new_test.py"],
                captured_at="2026-08-22T03:10:00Z",
            )
            l2_blocked = refresh_workstream_scope(
                fixture.worktree_b,
                include_local_worktrees=False,
                occurred_at="2026-08-22T03:11:00Z",
            )
            self.assertEqual(l2_blocked["expansion"]["level"], "l2")
            self.assertFalse(l2_blocked["local_work_allowed"])
            l2_confirmed = refresh_workstream_scope(
                fixture.worktree_b,
                include_local_worktrees=False,
                confirm_l2=True,
                reason="task explicitly includes the test subsystem",
                occurred_at="2026-08-22T03:12:00Z",
            )
            self.assertTrue(l2_confirmed["local_work_allowed"])
            self.assertEqual(l2_confirmed["session"]["scope_revision"], 2)
            self.assertIn("test-coverage", l2_confirmed["session"]["affected_subsystem_ids"])
            self.assertEqual(
                l2_confirmed["session"]["last_scope_expansion"]["decision"], "confirmed-local"
            )

        with CollaborationGitFixture() as fixture:
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-l3",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/component-versions.json"],
                captured_at="2026-08-22T03:20:00Z",
            )
            l3 = refresh_workstream_scope(
                fixture.worktree_b,
                include_local_worktrees=False,
                occurred_at="2026-08-22T03:21:00Z",
            )
            self.assertEqual(l3["expansion"]["level"], "l3")
            self.assertFalse(l3["expansion"]["allowed"])
            self.assertTrue(l3["review_ready_blocked"] or not l3["local_work_allowed"])
            route = plan_adapter_session_route(
                fixture.worktree_b,
                adapter_manifest=REPOSITORY_ROOT / "adapters" / "codex" / "adapter-manifest.json",
                platform_session_id="w2-l3-session",
            )
            self.assertFalse(route["allowed"])
            self.assertEqual(route["reason"], "scope-expansion-l3-blocked")
            with self.assertRaisesRegex(ValueError, "only for an L2"):
                refresh_workstream_scope(
                    fixture.worktree_b,
                    include_local_worktrees=False,
                    confirm_l2=True,
                    reason="central request must not bypass L3",
                )

        custom = CollaborationConfig.from_manifest(
            {
                "collaboration": {
                    "exclusive_resources": [
                        {"resource_id": "database-lock", "path_patterns": ["db/migrations/**"]}
                    ]
                }
            }
        )
        self.assertEqual(custom.exclusive_resources[0]["resource_id"], "database-lock")

    def test_scope_refresh_ignores_conflicts_between_other_local_workstreams(self) -> None:
        with CollaborationGitFixture() as fixture:
            worktree_c = fixture.root / "worktree-c"
            fixture.git(
                fixture.repository,
                "worktree",
                "add",
                "-b",
                "codex/fixture-c",
                str(worktree_c),
                "main",
            )
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-current",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/current-only.py"],
            )
            write_workstream_session(
                fixture.worktree_a,
                workstream_id="W2-peer-a",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/peer-shared.py"],
            )
            write_workstream_session(
                worktree_c,
                workstream_id="W2-peer-c",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/peer-shared.py"],
            )

            topology = inspect_worktree_overlap(fixture.worktree_b)
            self.assertTrue(
                any(
                    set(finding["workstream_ids"]) == {"W2-peer-a", "W2-peer-c"}
                    and finding["kind"] == "direct"
                    for finding in topology["findings"]
                )
            )

            refreshed = refresh_workstream_scope(fixture.worktree_b)
            self.assertTrue(refreshed["expansion"]["allowed"])
            self.assertTrue(refreshed["local_work_allowed"])
            self.assertEqual(refreshed["findings"], [])
            self.assertEqual(refreshed["session"]["runtime_condition"], "active")

    def test_shared_imported_commit_conflicts_only_when_both_workstreams_expect_writes(self) -> None:
        with CollaborationGitFixture() as fixture:
            shared = fixture.worktree_a / "packages" / "shared.py"
            shared.parent.mkdir()
            shared.write_text("shared = True\n", encoding="utf-8")
            fixture.git(fixture.worktree_a, "add", "packages/shared.py")
            fixture.git(fixture.worktree_a, "commit", "-m", "shared candidate")
            shared_oid = fixture.git(
                fixture.worktree_a, "rev-parse", "HEAD"
            ).stdout.strip()
            fixture.git(fixture.worktree_b, "merge", "--ff-only", shared_oid)

            write_workstream_session(
                fixture.worktree_a,
                workstream_id="W2-shared-source",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/shared.py"],
            )
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-shared-consumer",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/consumer-only.py"],
            )

            refreshed = refresh_workstream_scope(fixture.worktree_b)
            self.assertTrue(refreshed["local_work_allowed"])
            self.assertFalse(
                any("packages/shared.py" in item["path_evidence"] for item in refreshed["findings"])
            )

            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-shared-consumer",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/shared.py"],
            )
            blocked = refresh_workstream_scope(fixture.worktree_b)
            self.assertEqual(blocked["expansion"]["level"], "l3")
            self.assertFalse(blocked["local_work_allowed"])
            shared_finding = next(
                item
                for item in blocked["findings"]
                if item["kind"] == "direct" and "packages/shared.py" in item["path_evidence"]
            )
            self.assertEqual(
                {tuple(item["sources"]) for item in shared_finding["path_provenance"]},
                {("expected",)},
            )

    def test_exact_clean_frozen_ancestor_does_not_block_descendant_scope_refresh(self) -> None:
        with CollaborationGitFixture() as fixture:
            (fixture.worktree_a / "untracked" / "same-path.txt").unlink()
            shared = fixture.worktree_a / "packages" / "frozen.py"
            shared.parent.mkdir()
            shared.write_text("frozen = True\n", encoding="utf-8")
            fixture.git(fixture.worktree_a, "add", "packages/frozen.py")
            fixture.git(fixture.worktree_a, "commit", "-m", "frozen candidate")
            frozen_oid = fixture.git(
                fixture.worktree_a, "rev-parse", "HEAD"
            ).stdout.strip()
            fixture.git(fixture.worktree_b, "merge", "--ff-only", frozen_oid)

            write_workstream_session(
                fixture.worktree_a,
                workstream_id="W2-frozen-source",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/frozen.py"],
            )
            write_workstream_session(
                fixture.worktree_b,
                workstream_id="W2-frozen-consumer",
                primary_subsystem_id="release-and-toolchain",
                expected_writes=["packages/frozen.py"],
            )
            git_dir = Path(
                fixture.git(
                    fixture.worktree_a, "rev-parse", "--absolute-git-dir"
                ).stdout.strip()
            )
            receipt_dir = git_dir / "orrery" / "candidate-freeze"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / f"{frozen_oid}.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "contract_type": "candidate-freeze-receipt-v1",
                        "workstream_id": "W2-frozen-source",
                        "branch": "refs/heads/codex/fixture-a",
                        "candidate_sha": frozen_oid,
                        "accepted_surface_fingerprint": "a" * 64,
                        "validation_status": "pending",
                        "closed": False,
                        "cleanup_ready": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            topology = inspect_worktree_overlap(fixture.worktree_b)
            self.assertIn("W2-frozen-source", topology["inherited_frozen_ancestor_ids"])
            self.assertTrue(
                any("packages/frozen.py" in item["path_evidence"] for item in topology["findings"])
            )
            refreshed = refresh_workstream_scope(fixture.worktree_b)
            self.assertTrue(refreshed["local_work_allowed"])
            self.assertEqual(refreshed["findings"], [])

            shared.write_text("frozen = False\n", encoding="utf-8")
            blocked = refresh_workstream_scope(fixture.worktree_b)
            self.assertEqual(blocked["expansion"]["level"], "l3")
            self.assertFalse(blocked["local_work_allowed"])
            self.assertTrue(
                any("packages/frozen.py" in item["path_evidence"] for item in blocked["findings"])
            )

    def test_w2_cross_member_ack_progress_stales_on_scope_change_and_resolves_mechanically(self) -> None:
        with CollaborationGitFixture() as fixture:
            for root, workstream, member, expected in (
                (fixture.worktree_a, "W2-member-a", "member-a", "packages/a.py"),
                (fixture.worktree_b, "W2-member-b", "member-b", "packages/b.py"),
            ):
                write_workstream_session(
                    root,
                    workstream_id=workstream,
                    primary_subsystem_id="release-and-toolchain",
                    expected_writes=[expected],
                    validation_surfaces=["schema-contract-tests"],
                    member_id=member,
                    captured_at="2026-08-22T04:00:00Z",
                )
            left = collect_scope_observation(fixture.worktree_a)
            right = collect_scope_observation(fixture.worktree_b)
            initial = compute_overlap_findings([left, right])["findings"]
            semantic = next(item for item in initial if item["kind"] == "semantic")
            with self.assertRaisesRegex(ValueError, "confirmed by a member locally"):
                acknowledge_overlap_finding(
                    semantic,
                    member_id="member-a",
                    reason="central request",
                    scope_revision=1,
                    source="central-request",
                )
            one = acknowledge_overlap_finding(
                semantic,
                member_id="member-a",
                reason="member A accepts local coordination risk",
                scope_revision=1,
                acknowledged_at="2026-08-22T04:01:00Z",
            )
            self.assertEqual(one["acknowledgement_progress"], "1/2")
            self.assertFalse(one["acknowledgement_complete"])
            self.assertTrue(one["review_ready_blocked"])
            both = acknowledge_overlap_finding(
                one,
                member_id="member-b",
                reason="member B accepts local coordination risk",
                scope_revision=1,
                acknowledged_at="2026-08-22T04:02:00Z",
            )
            self.assertEqual(both["acknowledgement_progress"], "2/2")
            self.assertTrue(both["acknowledgement_complete"])
            self.assertFalse(both["review_ready_blocked"])

            changed_right = dict(right)
            changed_right["scope_revision"] = 2
            changed_right["scope_fingerprint"] = "b" * 64
            changed = compute_overlap_findings([left, changed_right])["findings"]
            reconciled = reconcile_overlap_findings(changed, [both])
            self.assertEqual(reconciled["active"][0]["disposition"], "open")
            self.assertEqual(reconciled["retired"][0]["disposition"], "stale")
            self.assertEqual(reconciled["retired"][0]["resolution_reason"], "scope-or-baseline-binding-changed")

            resolved = reconcile_overlap_findings([], reconciled["active"])
            self.assertEqual(resolved["retired"][0]["disposition"], "resolved")
            self.assertFalse(resolved["retired"][0]["blocking"])

    def test_w2_cli_overlap_and_scope_refresh_use_stable_json_and_zero_network(self) -> None:
        with CollaborationGitFixture() as fixture:
            for root, workstream in (
                (fixture.worktree_a, "W2-cli-a"),
                (fixture.worktree_b, "W2-cli-b"),
            ):
                write_workstream_session(
                    root,
                    workstream_id=workstream,
                    primary_subsystem_id="release-and-toolchain",
                    expected_writes=["packages/shared.py"],
                    captured_at="2026-08-22T05:00:00Z",
                )
            environment = {
                **fixture.environment,
                "PYTHONPATH": os.pathsep.join(
                    (str(CLI_SOURCE), str(CORE_SOURCE), str(OBSERVATORY_SOURCE))
                ),
            }
            base = [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", "worktree"]
            overlap = subprocess.run(
                [*base, "overlap", "--target", str(fixture.worktree_a), "--json"],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(overlap.returncode, 5, overlap.stdout + overlap.stderr)
            payload = json.loads(overlap.stdout)
            self.assertEqual(payload["command"], "worktree-overlap")
            self.assertFalse(payload["data"]["network_performed"])
            self.assertTrue(payload["data"]["review_ready_blocked"])

            scope = subprocess.run(
                [
                    *base,
                    "scope",
                    "refresh",
                    "--target",
                    str(fixture.worktree_a),
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
            self.assertEqual(scope.returncode, 5, scope.stdout + scope.stderr)
            scope_payload = json.loads(scope.stdout)
            self.assertEqual(scope_payload["command"], "worktree-scope-refresh")
            self.assertEqual(scope_payload["data"]["expansion"]["level"], "l3")
            self.assertFalse(scope_payload["data"]["network_performed"])


if __name__ == "__main__":
    unittest.main()
