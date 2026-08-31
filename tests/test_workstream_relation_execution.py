from __future__ import annotations

import contextlib
import io
import json
import os
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from project_orrery_core.collaboration import inspect_worktree_status, write_workstream_session
from project_orrery_core.workstream_relation_execution import (
    RecoveryRequiredError,
    build_execution_plan,
    build_execution_undo_plan,
    discover_execution_candidates,
    execute_apply_plan,
    inspect_execution_state,
    issue_local_confirmation,
    issue_local_undo_confirmation,
    load_execution_receipt,
    recover_transaction,
)
from project_orrery_core.workstream_relations import load_relation_graph, load_relation_history
from project_orrery_core.schema import WORKSTREAM_RELATION_EXECUTION_SCHEMA
from project_orrery_cli import workstream_relations as relations_cli


DISCOVERY_AT = "2026-08-28T12:00:00Z"
PLAN_AT = "2026-08-28T12:01:00Z"
EXPIRES_AT = "2030-08-28T12:01:00Z"
APPLY_AT = "2026-08-28T12:02:00Z"
UNDO_AT = "2026-08-28T12:03:00Z"


class SuccessionGitFixture:
    """Build only the real Git topology W7B needs.

    W1 already tests the production worktree-create acceptance path. Routing
    every W7B fixture edge through that path repeated its identity and rollback
    checks and made nine tests take more than fifteen minutes on Windows.
    """

    def __init__(self, *, topology: str = "full") -> None:
        if topology not in {"identity", "minimal", "full"}:
            raise ValueError(f"unsupported fixture topology: {topology}")
        self._temporary = tempfile.TemporaryDirectory(prefix="orrery-w7b-")
        self.root_parent = Path(self._temporary.name)
        self.root = self.root_parent / "repository"
        self.environment = dict(os.environ)
        self.environment.update(
            {
                "GIT_AUTHOR_NAME": "Orrery W7B Fixture",
                "GIT_AUTHOR_EMAIL": "w7b@example.invalid",
                "GIT_COMMITTER_NAME": "Orrery W7B Fixture",
                "GIT_COMMITTER_EMAIL": "w7b@example.invalid",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        self.worktrees: dict[str, Path] = {"W5C": self.root}
        self.parents: dict[str, str | None] = {"W5C": None}
        self.task_bases: dict[str, str | None] = {"W5C": None}
        self._build_repository()
        self._write("W5C")
        if topology == "minimal":
            self._child("W5C", "W5D")
            self._child("W5D", "W5E")
        elif topology == "full":
            self._child("W5C", "W6")
            self._child("W6", "W5D")
            self._child("W5D", "CI1")
            self._child("W5D", "W5E")

    def __enter__(self) -> "SuccessionGitFixture":
        return self

    def __exit__(self, *_args: object) -> None:
        self._temporary.cleanup()

    def git(
        self, cwd: Path, *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *arguments],
            env=self.environment,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if check and completed.returncode:
            raise AssertionError(
                f"git {' '.join(arguments)} failed in {cwd}:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        return completed

    def _build_repository(self) -> None:
        self.root.mkdir()
        self.git(self.root, "init")
        self.git(self.root, "branch", "-M", "main")
        (self.root / "README.md").write_text("# fixture\n", encoding="utf-8")
        (self.root / ".project-orrery.json").write_text(
            '{"name":"project-orrery","manifest_format":1}\n', encoding="utf-8"
        )
        state_root = self.root / "docs" / "state"
        state_root.mkdir(parents=True)
        for name, title in (
            ("project-structure.md", "Project structure State"),
            ("documentation-system.md", "Documentation system State"),
            ("release-and-toolchain.md", "Release and toolchain State"),
            ("test-coverage.md", "Test coverage State"),
        ):
            (state_root / name).write_text(f"# {title}\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text(
            "# Agent index\n\n"
            "## project structure\n\n**ID**: `project-structure`\n\n"
            "**Truth**: `.project-orrery.json`.\n\n"
            "**Dig**: [State](docs/state/project-structure.md).\n\n"
            "## documentation system\n\n**ID**: `documentation-system`\n\n"
            "**Truth**: `AGENTS.md`, `docs/`.\n\n"
            "**Dig**: [State](docs/state/documentation-system.md).\n\n"
            "## release and toolchain\n\n**ID**: `release-and-toolchain`\n\n"
            "**Truth**: `packages/`.\n\n"
            "**Dig**: [State](docs/state/release-and-toolchain.md).\n\n"
            "## test coverage\n\n**ID**: `test-coverage`\n\n"
            "**Truth**: `tests/`.\n\n"
            "**Dig**: [State](docs/state/test-coverage.md).\n",
            encoding="utf-8",
        )
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "fixture baseline")

    def _child(self, parent_id: str, child_id: str) -> None:
        parent = self.worktrees[parent_id]
        task_base = self.git(parent, "rev-parse", "HEAD").stdout.strip()
        path = self.root_parent / child_id.lower()
        self.git(
            parent,
            "worktree",
            "add",
            "-b",
            f"codex/{child_id.lower()}",
            str(path),
            task_base,
        )
        self.worktrees[child_id] = path
        self.parents[child_id] = parent_id
        self.task_bases[child_id] = task_base
        self._write(child_id)

    def _write(
        self,
        workstream_id: str,
        *,
        runtime_condition: str = "active",
        lifecycle_phase: str = "implementing",
        evidence_freshness: str = "current",
        closure_reason: str | None = None,
        exact_lineage: bool = True,
    ) -> None:
        base_id = self.parents[workstream_id] if exact_lineage else None
        task_base = self.task_bases[workstream_id] if exact_lineage else None
        with mock.patch(
            "project_orrery_core.workstream_relation_capture.auto_capture_derived_from",
            return_value={"status": "fixture-disabled", "writes_performed": False},
        ):
            write_workstream_session(
                self.worktrees[workstream_id],
                workstream_id=workstream_id,
                primary_subsystem_id="project-structure",
                affected_subsystem_ids=(
                    "documentation-system",
                    "release-and-toolchain",
                    "test-coverage",
                ),
                expected_writes=(f"fixture/{workstream_id}.txt",),
                validation_surfaces=(f"fixture:{workstream_id}",),
                runtime_condition=runtime_condition,
                lifecycle_phase=lifecycle_phase,
                evidence_freshness=evidence_freshness,
                closure_reason=closure_reason,
                base_workstream_id=base_id,
                task_base_oid=task_base,
                captured_at=DISCOVERY_AT,
            )

    def reset_head(self, workstream_id: str, oid: str) -> None:
        path = self.worktrees[workstream_id]
        self.git(path, "reset", "--hard", oid)
        self.git(path, "clean", "-fd")
        self._write(workstream_id)

    def discovery(
        self, *, include_dependency: bool = True, include_similarity: bool = False
    ) -> dict:
        explicit = []
        if include_dependency:
            explicit.append(
                {
                    "relation_id": "rel-w5e-depends-ci1",
                    "relation_type": "depends_on",
                    "source_workstream_id": "W5E",
                    "target_workstream_id": "CI1",
                    "reason": "late CI inventory/shards must finish before W5E closeout",
                    "source_links": [
                        {"kind": "validation", "ref": "fixture:ci1-inventory-shards"}
                    ],
                }
            )
        hints = (
            [
                {
                    "source_workstream_id": "codex/ui-new",
                    "target_workstream_id": "codex/ui-old",
                }
            ]
            if include_similarity
            else []
        )
        return discover_execution_candidates(
            self.root,
            explicit_relations=explicit,
            similarity_hints=hints,
            recorded_at=DISCOVERY_AT,
        )

    def plan(
        self, *, completed: bool = False, include_dependency: bool = True
    ) -> tuple[dict, str]:
        discovery = self.discovery(include_dependency=include_dependency)
        lifecycles = {
            item["record"]["relation_id"]: "proposed"
            for item in discovery["candidates"]
        }
        successor = next(
            item["record"]["relation_id"]
            for item in discovery["candidates"]
            if item["record"]["source_workstream_id"] == "W5E"
            and item["record"]["target_workstream_id"] == "W5D"
            and item["record"]["relation_type"] == "derived_from"
        )
        lifecycles[successor] = "completed" if completed else "active"
        if include_dependency:
            lifecycles["rel-w5e-depends-ci1"] = "active"
        plan = build_execution_plan(
            self.root,
            discovery,
            target_lifecycles=lifecycles,
            actor_id="maintainer",
            issued_at=PLAN_AT,
            expires_at=EXPIRES_AT,
        )
        return plan, successor

    def statuses(self) -> dict[str, str]:
        return {
            name: self.git(path, "status", "--short").stdout
            for name, path in self.worktrees.items()
        }


def confirm_and_apply(
    fixture: SuccessionGitFixture, plan: dict, *, occurred_at: str = APPLY_AT
) -> dict:
    confirmation = issue_local_confirmation(
        fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT
    )
    return execute_apply_plan(
        fixture.root,
        plan,
        plan_id=plan["plan_id"],
        plan_hash=plan["plan_hash"],
        confirmation_id=confirmation["confirmation_id"],
        confirmation_token=confirmation["confirmation_token"],
        actor_id="maintainer",
        occurred_at=occurred_at,
    )


class WorkstreamRelationExecutionTests(unittest.TestCase):
    def test_execution_schema_cli_surface_and_no_delete_contract_are_dependency_light(
        self,
    ) -> None:
        refs = {item["$ref"] for item in WORKSTREAM_RELATION_EXECUTION_SCHEMA["oneOf"]}
        self.assertIn("#/$defs/execution_plan", refs)
        self.assertIn("#/$defs/confirmation", refs)
        self.assertIn("#/$defs/receipt", refs)
        parser = relations_cli.build_parser()
        for command in ("discover", "plan", "apply", "inspect", "undo", "receipt"):
            with self.subTest(command=command):
                self.assertIn(command, parser._subparsers._group_actions[0].choices)
        source = (
            Path(__file__).parents[1]
            / "packages"
            / "project-orrery-core"
            / "src"
            / "project_orrery_core"
            / "workstream_relation_execution.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("delete-worktree", source)
        self.assertNotIn("delete-branch", source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)

    def test_minimal_git_binding_rejections_and_state_axes_checkpoint(self) -> None:
        with SuccessionGitFixture(topology="minimal") as fixture:
            for runtime in ("waiting-for-user", "paused", "blocked-by-conflict", "failed"):
                fixture._write("W5D", runtime_condition=runtime)
                with self.subTest(runtime=runtime), self.assertRaisesRegex(
                    ValueError, "predecessor must be runtime active"
                ):
                    fixture.plan(include_dependency=False)
            fixture._write("W5D", runtime_condition="active")
            plan, successor = fixture.plan(include_dependency=False)
            binding = next(
                item for item in plan["candidate_bindings"] if item["relation_id"] == successor
            )
            self.assertEqual(len(binding["target"]["session_hash"]), 64)
            self.assertEqual(len(binding["target"]["scope_hash"]), 64)
            self.assertEqual(len(binding["target"]["head_oid"]), 40)
            self.assertEqual(plan["graph_hash"], plan["apply_plan"]["graph_hash"])
            self.assertEqual(plan["actor"], {"kind": "human-local", "actor_id": "maintainer"})
            self.assertTrue(plan["execution_supported"])
            self.assertEqual(plan["destructive_actions"], [])

            confirmation = issue_local_confirmation(
                fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT
            )
            with self.assertRaisesRegex(
                ValueError, "forged, replayed, cross-project, or not exact"
            ):
                execute_apply_plan(
                    fixture.root,
                    plan,
                    plan_id=plan["plan_id"],
                    plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"],
                    confirmation_token="forged",
                    actor_id="maintainer",
                    occurred_at=APPLY_AT,
                )
            self.assertEqual(inspect_execution_state(fixture.root)["journal_statuses"], [])
            fixture._write("W5D", runtime_condition="waiting-for-user")
            with self.assertRaisesRegex(ValueError, "graph drifted|Session/HEAD/Scope drifted"):
                execute_apply_plan(
                    fixture.root,
                    plan,
                    plan_id=plan["plan_id"],
                    plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"],
                    confirmation_token=confirmation["confirmation_token"],
                    actor_id="maintainer",
                    occurred_at=APPLY_AT,
                )
            self.assertEqual(inspect_execution_state(fixture.root)["journal_statuses"], [])
            fixture._write("W5D", runtime_condition="active")
            discovery = fixture.discovery(include_dependency=False)
            expired = build_execution_plan(
                fixture.root,
                discovery,
                target_lifecycles={
                    item["record"]["relation_id"]: "proposed"
                    for item in discovery["candidates"]
                },
                actor_id="maintainer",
                issued_at="2020-01-01T00:00:00Z",
                expires_at="2020-01-01T00:01:00Z",
            )
            with self.assertRaisesRegex(ValueError, "expired"):
                issue_local_confirmation(fixture.root, expired, actor_id="maintainer")
            with SuccessionGitFixture(topology="identity") as other:
                with self.assertRaisesRegex(ValueError, "another local project"):
                    issue_local_confirmation(other.root, plan, actor_id="maintainer")

    def test_cli_apply_and_undo_accept_leading_dash_opaque_tokens(self) -> None:
        with SuccessionGitFixture(topology="minimal") as fixture, tempfile.TemporaryDirectory(
            prefix="orrery-w7b-leading-dash-token-"
        ) as temporary:
            scratch = Path(temporary)
            plan, _successor = fixture.plan(include_dependency=False)
            plan_path = scratch / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            with mock.patch(
                "project_orrery_core.workstream_relation_execution.secrets.token_urlsafe",
                return_value="-leading-dash-apply-token",
            ):
                confirmation = issue_local_confirmation(
                    fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT
                )
            self.assertTrue(confirmation["confirmation_token"].startswith("-"))

            apply_stream = io.StringIO()
            with contextlib.redirect_stdout(apply_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "apply",
                            "--target",
                            str(fixture.root),
                            "--plan",
                            str(plan_path),
                            "--plan-id",
                            plan["plan_id"],
                            "--plan-hash",
                            plan["plan_hash"],
                            "--confirmation-id",
                            confirmation["confirmation_id"],
                            f"--confirmation-token={confirmation['confirmation_token']}",
                            "--actor-id",
                            "maintainer",
                            "--occurred-at",
                            APPLY_AT,
                            "--json",
                        ]
                    ),
                    0,
                )
            receipt = json.loads(apply_stream.getvalue())["data"]
            undo_plan = build_execution_undo_plan(
                fixture.root,
                receipt,
                actor_id="maintainer",
                issued_at=PLAN_AT,
                expires_at=EXPIRES_AT,
            )
            undo_plan_path = scratch / "undo.json"
            undo_plan_path.write_text(json.dumps(undo_plan), encoding="utf-8")
            with mock.patch(
                "project_orrery_core.workstream_relation_execution.secrets.token_urlsafe",
                return_value="-leading-dash-undo-token",
            ):
                undo_confirmation = issue_local_undo_confirmation(
                    fixture.root, undo_plan, actor_id="maintainer", issued_at=PLAN_AT
                )
            self.assertTrue(undo_confirmation["confirmation_token"].startswith("-"))

            undo_stream = io.StringIO()
            with contextlib.redirect_stdout(undo_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "undo",
                            "--target",
                            str(fixture.root),
                            "--undo-plan",
                            str(undo_plan_path),
                            "--execute",
                            "--actor-id",
                            "maintainer",
                            "--plan-id",
                            undo_plan["plan_id"],
                            "--plan-hash",
                            undo_plan["plan_hash"],
                            "--confirmation-id",
                            undo_confirmation["confirmation_id"],
                            f"--confirmation-token={undo_confirmation['confirmation_token']}",
                            "--occurred-at",
                            UNDO_AT,
                            "--json",
                        ]
                    ),
                    0,
                )
            undo_receipt = json.loads(undo_stream.getvalue())["data"]
            self.assertEqual(undo_receipt["operation"], "undo")
            self.assertFalse(undo_receipt["history_deleted"])

    def test_full_topology_cli_apply_receipt_undo_and_legacy_discovery(self) -> None:
        with SuccessionGitFixture(topology="full") as fixture, tempfile.TemporaryDirectory(
            prefix="orrery-w7b-cli-"
        ) as temporary:
            before_status = fixture.statuses()

            w6_session_path = Path(
                inspect_worktree_status(fixture.worktrees["W6"])["session"]["path"]
            )
            exact_w6_session = w6_session_path.read_bytes()
            legacy_w6_session = json.loads(exact_w6_session)
            legacy_w6_session["lineage"] = {
                "lineage_schema_version": 1,
                "status": "legacy-unknown",
                "base_workstream_id": None,
                "task_base_oid": None,
                "validated_head": None,
            }
            w6_session_path.write_text(
                json.dumps(legacy_w6_session, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            legacy = fixture.discovery(include_similarity=True)
            self.assertIn(
                "legacy-no-lineage-evidence",
                next(
                    item
                    for item in legacy["unknown_candidates"]
                    if item["source_workstream_id"] == "W6"
                )["reason_codes"],
            )
            self.assertEqual(
                legacy["rejected_hints"][0]["reason_code"],
                "branch-or-path-similarity-insufficient-evidence",
            )
            self.assertFalse(legacy["similarity_inference_permitted"])
            w6_session_path.write_bytes(exact_w6_session)

            parent = fixture.worktrees["W5D"]
            baseline = str(fixture.task_bases["W5E"])
            (parent / "post-fork.txt").write_text("parent advanced\n", encoding="utf-8")
            fixture.git(parent, "add", "post-fork.txt")
            fixture.git(parent, "commit", "-m", "parent post fork")
            fixture._write("W5D")
            post_fork = fixture.discovery(include_dependency=False)
            siblings = [
                item
                for item in post_fork["candidates"]
                if item["record"]["target_workstream_id"] == "W5D"
            ]
            self.assertEqual(
                {item["record"]["source_workstream_id"] for item in siblings},
                {"CI1", "W5E"},
            )
            self.assertTrue(all(item["status"] == "proposed" for item in siblings))
            self.assertTrue(
                all(
                    item["record"]["evidence"]["target_unique_commits_after_base"] > 0
                    for item in siblings
                )
            )
            fixture.reset_head("W5D", baseline)

            original_path = Path(
                inspect_worktree_status(fixture.worktrees["W5D"])["session"]["path"]
            )
            original_bytes = original_path.read_bytes()
            scratch = Path(temporary)
            spec_path = scratch / "spec.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "explicit_relations": [
                            {
                                "relation_id": "rel-w5e-depends-ci1",
                                "relation_type": "depends_on",
                                "source_workstream_id": "W5E",
                                "target_workstream_id": "CI1",
                                "reason": "late CI adjacency",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            discover_stream = io.StringIO()
            with contextlib.redirect_stdout(discover_stream):
                discover_exit = relations_cli.main(
                    [
                        "discover",
                        "--target",
                        str(fixture.root),
                        "--spec",
                        str(spec_path),
                        "--recorded-at",
                        DISCOVERY_AT,
                        "--json",
                    ]
                )
            self.assertIn(discover_exit, (0, 5))
            discovery = json.loads(discover_stream.getvalue())["data"]
            triples = {
                (
                    item["record"]["relation_type"],
                    item["record"]["source_workstream_id"],
                    item["record"]["target_workstream_id"],
                )
                for item in discovery["candidates"]
            }
            self.assertIn(("derived_from", "W5E", "W5D"), triples)
            self.assertIn(("derived_from", "CI1", "W5D"), triples)
            self.assertIn(("depends_on", "W5E", "CI1"), triples)
            discovery_path = scratch / "discovery.json"
            discovery_path.write_text(json.dumps(discovery), encoding="utf-8")
            lifecycles: list[str] = []
            for item in discovery["candidates"]:
                record = item["record"]
                state = "proposed"
                if (record["source_workstream_id"], record["target_workstream_id"]) == (
                    "W5E",
                    "W5D",
                ):
                    state = "completed"
                elif (record["source_workstream_id"], record["target_workstream_id"]) == (
                    "W5E",
                    "CI1",
                ):
                    state = "active"
                lifecycles.extend(["--lifecycle", f"{record['relation_id']}={state}"])
            plan_stream = io.StringIO()
            with contextlib.redirect_stdout(plan_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "plan",
                            "--target",
                            str(fixture.root),
                            "--discovery",
                            str(discovery_path),
                            "--actor-id",
                            "maintainer",
                            "--issued-at",
                            PLAN_AT,
                            "--expires-at",
                            EXPIRES_AT,
                            "--confirm-local",
                            "--json",
                            *lifecycles,
                        ]
                    ),
                    0,
                )
            plan_data = json.loads(plan_stream.getvalue())["data"]
            plan = plan_data["plan"]
            confirmation = plan_data["confirmation"]
            plan_path = scratch / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError, "forged, replayed, cross-project, or not exact"
            ):
                execute_apply_plan(
                    fixture.root,
                    plan,
                    plan_id=plan["plan_id"],
                    plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"],
                    confirmation_token="forged",
                    actor_id="maintainer",
                    occurred_at=APPLY_AT,
                )
            self.assertEqual(inspect_execution_state(fixture.root)["journal_statuses"], [])

            apply_stream = io.StringIO()
            with mock.patch.object(
                socket.socket, "connect", side_effect=AssertionError("network forbidden")
            ), contextlib.redirect_stdout(apply_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "apply",
                            "--target",
                            str(fixture.root),
                            "--plan",
                            str(plan_path),
                            "--plan-id",
                            plan["plan_id"],
                            "--plan-hash",
                            plan["plan_hash"],
                            "--confirmation-id",
                            confirmation["confirmation_id"],
                            f"--confirmation-token={confirmation['confirmation_token']}",
                            "--actor-id",
                            "maintainer",
                            "--occurred-at",
                            APPLY_AT,
                            "--json",
                        ]
                    ),
                    0,
                )
            receipt = json.loads(apply_stream.getvalue())["data"]
            predecessor = inspect_worktree_status(fixture.worktrees["W5D"])["session"][
                "record"
            ]
            self.assertEqual(
                (
                    predecessor["lifecycle_phase"],
                    predecessor["runtime_condition"],
                    predecessor["closure_reason"],
                ),
                ("closed", "paused", "superseded"),
            )
            self.assertTrue(load_relation_graph(fixture.root)["validation"]["valid"])
            self.assertEqual(
                load_execution_receipt(fixture.root, receipt["receipt_id"]), receipt
            )
            self.assertTrue(
                all(len(item["event_hash"]) == 64 for item in receipt["relation_event_records"])
            )
            self.assertEqual(receipt["destructive_actions"], [])
            with self.assertRaisesRegex(ValueError, "graph drifted|replay"):
                execute_apply_plan(
                    fixture.root,
                    plan,
                    plan_id=plan["plan_id"],
                    plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"],
                    confirmation_token=confirmation["confirmation_token"],
                    actor_id="maintainer",
                    occurred_at=APPLY_AT,
                )

            receipt_stream = io.StringIO()
            with contextlib.redirect_stdout(receipt_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "receipt",
                            "--target",
                            str(fixture.root),
                            "--receipt-id",
                            receipt["receipt_id"],
                            "--json",
                        ]
                    ),
                    0,
                )
            self.assertEqual(json.loads(receipt_stream.getvalue())["data"], receipt)

            undo_stream = io.StringIO()
            with contextlib.redirect_stdout(undo_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "undo",
                            "--target",
                            str(fixture.root),
                            "--receipt-id",
                            receipt["receipt_id"],
                            "--actor-id",
                            "maintainer",
                            "--issued-at",
                            PLAN_AT,
                            "--expires-at",
                            EXPIRES_AT,
                            "--confirm-local",
                            "--json",
                        ]
                    ),
                    0,
                )
            undo_data = json.loads(undo_stream.getvalue())["data"]
            undo_path = scratch / "undo.json"
            undo_path.write_text(json.dumps(undo_data["plan"]), encoding="utf-8")
            undo_confirmation = undo_data["confirmation"]
            undo_execute_stream = io.StringIO()
            with contextlib.redirect_stdout(undo_execute_stream):
                self.assertEqual(
                    relations_cli.main(
                        [
                            "undo",
                            "--target",
                            str(fixture.root),
                            "--undo-plan",
                            str(undo_path),
                            "--execute",
                            "--actor-id",
                            "maintainer",
                            "--plan-id",
                            undo_data["plan"]["plan_id"],
                            "--plan-hash",
                            undo_data["plan"]["plan_hash"],
                            "--confirmation-id",
                            undo_confirmation["confirmation_id"],
                            f"--confirmation-token={undo_confirmation['confirmation_token']}",
                            "--occurred-at",
                            UNDO_AT,
                            "--json",
                        ]
                    ),
                    0,
                )
            undo_receipt = json.loads(undo_execute_stream.getvalue())["data"]
            self.assertEqual(original_path.read_bytes(), original_bytes)
            self.assertFalse(undo_receipt["history_deleted"])
            self.assertTrue(undo_receipt["appended_compensating_event_ids"])
            history = load_relation_history(fixture.root)
            self.assertTrue(all(len(item["events"]) >= 2 for item in history["histories"]))
            self.assertTrue(
                all(
                    item["lifecycle"] in {"cancelled", "stale"}
                    for item in history["current_records"]
                )
            )
            inspect_stream = io.StringIO()
            with contextlib.redirect_stdout(inspect_stream):
                self.assertEqual(
                    relations_cli.main(
                        ["inspect", "--target", str(fixture.root), "--json"]
                    ),
                    0,
                )
            self.assertEqual(
                json.loads(inspect_stream.getvalue())["data"]["graph_status"], "current"
            )
            self.assertEqual(fixture.statuses(), before_status)

    def test_full_topology_atomic_recovery_and_undo_drift_refusal(self) -> None:
        with SuccessionGitFixture(topology="full") as fixture:
            before_status = fixture.statuses()
            before_session = inspect_worktree_status(fixture.worktrees["W5D"])["session"][
                "record"
            ]
            plan, _ = fixture.plan()
            confirmation = issue_local_confirmation(
                fixture.root, plan, actor_id="maintainer", issued_at=PLAN_AT
            )
            with self.assertRaises(RecoveryRequiredError):
                execute_apply_plan(
                    fixture.root,
                    plan,
                    plan_id=plan["plan_id"],
                    plan_hash=plan["plan_hash"],
                    confirmation_id=confirmation["confirmation_id"],
                    confirmation_token=confirmation["confirmation_token"],
                    actor_id="maintainer",
                    occurred_at=APPLY_AT,
                    failure_injection="after-event-write:2",
                )
            inspection = inspect_execution_state(fixture.root)
            self.assertEqual(inspection["graph_status"], "blocked")
            transaction_id = inspection["pending_recovery_transaction_ids"][0]
            with self.assertRaises(RecoveryRequiredError):
                load_relation_graph(fixture.root)
            recovered = recover_transaction(
                fixture.root, transaction_id, actor_id="maintainer", occurred_at=UNDO_AT
            )
            self.assertEqual(recovered["status"], "rolled-back")
            self.assertFalse(recovered["history_deleted"])
            self.assertEqual(inspect_execution_state(fixture.root)["graph_status"], "current")
            self.assertEqual(
                inspect_worktree_status(fixture.worktrees["W5D"])["session"]["record"],
                before_session,
            )
            recovered_history = load_relation_history(fixture.root)
            self.assertTrue(recovered_history["histories"])
            self.assertTrue(
                all(
                    item["lifecycle"] in {"cancelled", "stale"}
                    for item in recovered_history["current_records"]
                )
            )

            w6_head = inspect_worktree_status(fixture.worktrees["W6"])["session"]["record"][
                "head"
            ]
            drift_discovery = discover_execution_candidates(
                fixture.root,
                explicit_relations=[
                    {
                        "relation_id": "rel-w5e-absorbs-w6-after-recovery",
                        "relation_type": "absorbs",
                        "source_workstream_id": "W5E",
                        "target_workstream_id": "W6",
                        "ownership_transfer_oid": w6_head,
                        "reason": "post-recovery drift fixture",
                        "source_links": [
                            {"kind": "validation", "ref": "fixture:recovery"}
                        ],
                    }
                ],
                recorded_at="2026-08-28T12:04:00Z",
            )
            lifecycles = {
                item["record"]["relation_id"]: "proposed"
                for item in drift_discovery["candidates"]
            }
            lifecycles["rel-w5e-absorbs-w6-after-recovery"] = "active"
            drift_plan = build_execution_plan(
                fixture.root,
                drift_discovery,
                target_lifecycles=lifecycles,
                actor_id="maintainer",
                issued_at=PLAN_AT,
                expires_at=EXPIRES_AT,
            )
            with mock.patch.object(
                socket.socket, "connect", side_effect=AssertionError("network forbidden")
            ):
                receipt = confirm_and_apply(
                    fixture, drift_plan, occurred_at="2026-08-28T12:05:00Z"
                )
            fixture._write("W6", runtime_condition="waiting-for-user")
            with self.assertRaisesRegex(ValueError, "drift"):
                build_execution_undo_plan(
                    fixture.root, receipt, actor_id="maintainer"
                )
            self.assertEqual(fixture.statuses(), before_status)


if __name__ == "__main__":
    unittest.main()
