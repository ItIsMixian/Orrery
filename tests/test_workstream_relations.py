from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-observatory" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
):
    sys.path.insert(0, str(source))

from project_orrery_cli import workstream_relations as relations_cli  # noqa: E402
from project_orrery_core import workstream_relations as relation_core  # noqa: E402
from project_orrery_core.collaboration import (  # noqa: E402
    _write_private_session,
    build_workstream_session,
    create_worktree,
    write_workstream_session,
)
from project_orrery_core.schema import WORKSTREAM_RELATIONS_SCHEMA  # noqa: E402
from project_orrery_core.workstream_relations import (  # noqa: E402
    _node_from_session,
    append_proposed_relation,
    build_apply_plan,
    build_discovery_plan,
    build_relation_graph,
    build_relation_record,
    build_succession_plan,
    build_undo_plan,
    default_relation_evidence,
    discover_relation_candidates,
    load_archived_session_index,
    load_legacy_session_projection,
    load_relation_graph,
    load_relation_history,
    relation_storage_root,
    retired_session_archive_root,
    validate_apply_receipt,
    validate_relation_record,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "workstream-relations" / "v1" / "succession-chain.json"
W7C_FIXTURE = ROOT / "tests" / "fixtures" / "workstream-relations" / "v1" / "w7c-consumer-compatibility.json"
TIMESTAMP = "2026-08-28T00:00:00Z"


class LocalGitRepository:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="orrery-relations-")
        self.root = Path(self.temporary.name) / "repository"
        self.root.mkdir()
        self.environment = dict(os.environ)
        self.environment.update({
            "GIT_AUTHOR_NAME": "Orrery Relations",
            "GIT_AUTHOR_EMAIL": "relations@example.invalid",
            "GIT_COMMITTER_NAME": "Orrery Relations",
            "GIT_COMMITTER_EMAIL": "relations@example.invalid",
            "GIT_CONFIG_NOSYSTEM": "1",
        })
        self.git("init")
        self.git("branch", "-M", "main")
        (self.root / "base.txt").write_text("base\n", encoding="utf-8")
        (self.root / ".project-orrery.json").write_text(
            '{"name":"project-orrery","manifest_format":1}\n', encoding="utf-8"
        )
        state_root = self.root / "docs" / "state"
        state_root.mkdir(parents=True)
        (state_root / "project-structure.md").write_text("# Project structure State\n", encoding="utf-8")
        (state_root / "test-coverage.md").write_text("# Test coverage State\n", encoding="utf-8")
        (state_root / "multi-worktree-collaboration.md").write_text(
            "# Multi-worktree collaboration State\n", encoding="utf-8"
        )
        (self.root / "AGENTS.md").write_text(
            "# Agent index\n\n"
            "## project structure\n\n"
            "**ID**: `project-structure`\n\n"
            "**Truth**: `.project-orrery.json`.\n\n"
            "**Dig**: [State](docs/state/project-structure.md).\n\n"
            "## test coverage\n\n"
            "**ID**: `test-coverage`\n\n"
            "**Truth**: `tests/`.\n\n"
            "**Dig**: [State](docs/state/test-coverage.md).\n\n"
            "## multi-worktree collaboration\n\n"
            "**ID**: `multi-worktree-collaboration`\n\n"
            "**Truth**: `packages/`.\n\n"
            "**Dig**: [State](docs/state/multi-worktree-collaboration.md).\n",
            encoding="utf-8",
        )
        self.git("add", ".")
        self.git("commit", "-m", "base")

    def close(self) -> None:
        self.temporary.cleanup()

    def __enter__(self) -> "LocalGitRepository":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def git(self, *arguments: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", "-C", str(cwd or self.root), *arguments],
            env=self.environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if check and result.returncode:
            raise AssertionError(f"git {' '.join(arguments)} failed:\n{result.stdout}{result.stderr}")
        return result

    def commit(self, path: str, content: str, message: str, *, cwd: Path | None = None) -> str:
        worktree = cwd or self.root
        target = worktree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.git("add", path, cwd=worktree)
        self.git("commit", "-m", message, cwd=worktree)
        return self.git("rev-parse", "HEAD", cwd=worktree).stdout.strip()


def relation(
    relation_id: str,
    relation_type: str,
    source: str,
    target: str,
    *,
    lifecycle: str = "proposed",
    source_head: str | None = None,
    target_head: str | None = None,
    task_base: str | None = None,
    evidence_status: str = "unknown",
    ancestry_status: str | None = None,
    dependency_status: str | None = None,
    ownership_status: str | None = None,
    ownership_transfer: str | None = None,
    target_unique: int | None = None,
) -> dict[str, object]:
    if ancestry_status is None:
        ancestry_status = "unknown" if relation_type == "derived_from" else "not-applicable"
    if dependency_status is None:
        dependency_status = "unknown" if relation_type == "depends_on" else "not-applicable"
    if ownership_status is None:
        ownership_status = "unknown" if relation_type == "absorbs" else "not-applicable"
    current = "current" if evidence_status == "confirmed" else "unknown"
    return build_relation_record(
        relation_id=relation_id,
        event_id=f"event-{relation_id}",
        revision=1,
        relation_type=relation_type,
        source_workstream_id=source,
        target_workstream_id=target,
        lifecycle=lifecycle,
        recorded_at=TIMESTAMP,
        actor_kind="human",
        actor_id="maintainer",
        origin="native",
        reason="synthetic relation",
        evidence=default_relation_evidence(
            status=evidence_status,
            source_head_oid=source_head,
            target_head_oid=target_head,
            task_base_oid=task_base,
            ownership_transfer_oid=ownership_transfer,
            source_head_status=current,
            target_head_status=current,
            scope_status=current,
            ancestry_status=ancestry_status,
            dependency_status=dependency_status,
            ownership_transfer_status=ownership_status,
            target_unique_commits_after_base=target_unique,
        ),
        source_links=[{"kind": "relation", "ref": f"fixture:{relation_id}"}],
        writes_performed=False,
    )


def node(
    workstream_id: str,
    head_oid: str | None,
    *,
    lifecycle_phase: str = "implementing",
    runtime_condition: str = "active",
    evidence_freshness: str = "current",
    session_state: str = "current",
    scope_status: str = "current",
    closure_reason: str | None = None,
    status: str | None = None,
    origin: str = "native",
    primary_subsystem_id: str = "multi-worktree-collaboration",
    affected_subsystem_ids: list[str] | None = None,
    visibility: str = "worktree-local",
    observability: str = "local",
) -> dict[str, object]:
    if status is None:
        if session_state != "current":
            status = "stale"
        elif lifecycle_phase in {"closed", "integrated"}:
            status = "completed"
        elif runtime_condition == "blocked-by-conflict":
            status = "blocked"
        elif runtime_condition == "failed":
            status = "failed"
        elif runtime_condition in {"waiting-for-user", "paused"}:
            status = "inactive"
        elif runtime_condition in {"offline", "stale-unknown", "unknown"}:
            status = "unknown"
        elif lifecycle_phase == "review-ready":
            status = "review-pending"
        else:
            status = "active"
    return {
        "workstream_id": workstream_id,
        "status": status,
        "session_state": session_state,
        "lifecycle_phase": lifecycle_phase,
        "runtime_condition": runtime_condition,
        "evidence_freshness": evidence_freshness,
        "head_oid": head_oid,
        "scope_status": scope_status,
        "closure_reason": closure_reason,
        "primary_subsystem_id": primary_subsystem_id,
        "affected_subsystem_ids": affected_subsystem_ids or [],
        "visibility": visibility,
        "observability": observability,
        "source_links": [{"kind": "workstream-session", "ref": f"fixture:{workstream_id}"}],
        "origin": origin,
    }


class WorkstreamRelationTests(unittest.TestCase):
    def _archived_lineage_fixture(
        self,
        repository: LocalGitRepository,
        *,
        keep_parent_live: bool = False,
    ) -> dict[str, object]:
        parent = Path(repository.temporary.name) / "w5d"
        parent_head = repository.git("rev-parse", "HEAD").stdout.strip()
        if keep_parent_live:
            repository.git("worktree", "add", "-b", "codex/w5d-archived", str(parent), "main")
        else:
            repository.git("branch", "codex/w5d-archived", parent_head)
        child = repository.root
        child_record = build_workstream_session(
            child,
            workstream_id="CI1-tiered-parallel-validation",
            primary_subsystem_id="test-coverage",
            affected_subsystem_ids=["multi-worktree-collaboration"],
            expected_writes=["scripts/ci/"],
            governing_docs=["docs/decisions/0014-dynamic-workstream-succession-contract.md"],
            validation_surfaces=["tests.test_ci_validation"],
            lifecycle_phase="validating",
            runtime_condition="waiting-for-user",
            evidence_freshness="current",
            captured_at=TIMESTAMP,
        )
        child_record["lineage"] = {
            "lineage_schema_version": 1,
            "status": "current",
            "base_workstream_id": "W5D-lan-collaboration-harness",
            "task_base_oid": parent_head,
            "validated_head": parent_head,
        }
        child_write = _write_private_session(child, child_record)
        if keep_parent_live:
            parent_record = copy.deepcopy(child_record)
            parent_git_dir = repository.git(
                "rev-parse", "--absolute-git-dir", cwd=parent
            ).stdout.strip()
            parent_worktree_digest = hashlib.sha256(
                os.path.normcase(os.path.realpath(parent_git_dir)).encode("utf-8")
            ).hexdigest()[:24]
            parent_record.update({
                "workstream_id": "W5D-lan-collaboration-harness",
                "worktree_id": f"local-{parent_worktree_digest}",
                "branch": "refs/heads/codex/w5d-archived",
                "lifecycle_phase": "closed",
                "runtime_condition": "offline",
                "closure_reason": "superseded",
                "primary_subsystem_id": "multi-worktree-collaboration",
                "affected_subsystem_ids": ["test-coverage"],
                "expected_writes": ["packages/project-orrery-core/", "tests/"],
                "validation_surfaces": ["tests.test_workstream_relations"],
                "lineage": {
                    "lineage_schema_version": 1,
                    "status": "legacy-unknown",
                    "base_workstream_id": None,
                    "task_base_oid": None,
                    "validated_head": None,
                },
            })
            parent_write = _write_private_session(parent, parent_record)
            parent_session = Path(parent_write["session_path"])
        else:
            parent_record = copy.deepcopy(child_record)
            parent_record.update({
                "workstream_id": "W5D-lan-collaboration-harness",
                "branch": "refs/heads/codex/w5d-archived",
                "lifecycle_phase": "closed",
                "runtime_condition": "offline",
                "evidence_freshness": "current",
                "closure_reason": "superseded",
                "primary_subsystem_id": "multi-worktree-collaboration",
                "affected_subsystem_ids": ["test-coverage"],
                "expected_writes": ["packages/project-orrery-core/", "tests/"],
                "validation_surfaces": ["tests.test_workstream_relations"],
                "lineage": {
                    "lineage_schema_version": 1,
                    "status": "legacy-unknown",
                    "base_workstream_id": None,
                    "task_base_oid": None,
                    "validated_head": None,
                },
            })
            parent_session = Path(repository.temporary.name) / "retired-source-worktree.json"
            parent_session.write_text(
                json.dumps(parent_record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        child_session = Path(child_write["session_path"])
        archive_root = retired_session_archive_root(repository.root)
        archive_file = (
            archive_root
            / "2026-08-29"
            / f"codex-w5d-archived-{parent_head[:12]}"
            / "worktree.json"
        )
        archive_file.parent.mkdir(parents=True)
        archive_file.write_bytes(parent_session.read_bytes())
        return {
            "parent": parent,
            "child": child,
            "parent_head": parent_head,
            "parent_session": parent_session,
            "child_session": child_session,
            "archive_root": archive_root,
            "archive_file": archive_file,
        }

    def test_schema_fixture_active_tips_late_ci_and_no_layout_contract(self) -> None:
        self.assertEqual(WORKSTREAM_RELATIONS_SCHEMA["$defs"]["relation_type"]["enum"], ["derived_from", "depends_on", "absorbs"])
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        graph = build_relation_graph(payload["records"], nodes=payload["nodes"])
        self.assertTrue(graph["validation"]["valid"])
        self.assertEqual(graph["active_tip_workstream_ids"], ["CI2-late", "W5E"])
        plan = build_succession_plan(graph)
        self.assertIn(
            ("CI2-late", "W5E"),
            {(item["left_workstream_id"], item["right_workstream_id"]) for item in plan["compare_pairs"]},
        )
        self.assertTrue(any("execution-dependency-does-not-suppress" in item["reason_codes"] for item in plan["compare_pairs"]))
        late_pairs = [
            item for item in plan["compare_pairs"]
            if "CI2-late" in {item["left_workstream_id"], item["right_workstream_id"]}
        ]
        self.assertEqual(
            [(item["left_workstream_id"], item["right_workstream_id"]) for item in late_pairs],
            [("CI2-late", "W5E")],
        )
        mixed_pair = next(
            item for item in plan["compare_pairs"]
            if {item["left_workstream_id"], item["right_workstream_id"]} == {"W5D", "W5E"}
        )
        self.assertIn("execution-dependency-does-not-suppress", mixed_pair["reason_codes"])
        self.assertNotIn(
            ("W5D", "W5E"),
            {(item["left_workstream_id"], item["right_workstream_id"]) for item in plan["suppress_direct_pairs"]},
        )
        serialized = json.dumps(graph, sort_keys=True)
        for forbidden in ('"color"', '"coordinates"', '"layout"', '"ui_text"'):
            self.assertNotIn(forbidden, serialized)
        self.assertTrue(all("source_links" in node for node in graph["nodes"]))
        self.assertTrue(all("evidence" in edge for edge in graph["edges"]))

    def test_runtime_and_evidence_axes_fail_closed_for_active_tips(self) -> None:
        def session(workstream_id: str, runtime: str, *, lifecycle: str = "implementing", evidence: str = "current") -> dict[str, object]:
            return {
                "workstream_id": workstream_id,
                "head": (workstream_id[0].lower() if workstream_id[0].lower() in "abcdef" else "a") * 40,
                "lifecycle_phase": lifecycle,
                "runtime_condition": runtime,
                "evidence_freshness": evidence,
                "closure_reason": None,
                "primary_subsystem_id": "multi-worktree-collaboration",
                "affected_subsystem_ids": ["test-coverage"],
                "visibility": "worktree-local",
                "observability": "local",
            }

        inactive_conditions = [
            "waiting-for-user", "paused", "blocked-by-conflict", "failed", "offline", "stale-unknown",
        ]
        projected = [
            _node_from_session(session(runtime, runtime), "current") for runtime in inactive_conditions
        ]
        projected.extend([
            _node_from_session(session("active", "active"), "current"),
            _node_from_session(session("review", "active", lifecycle="review-ready"), "current"),
            _node_from_session(session("unknown-evidence", "active", evidence="unknown"), "current"),
        ])
        graph = build_relation_graph([], nodes=projected)
        self.assertEqual(graph["active_tip_workstream_ids"], ["active", "review"])
        status = {item["workstream_id"]: item["status"] for item in graph["nodes"]}
        self.assertEqual(status["waiting-for-user"], "inactive")
        self.assertEqual(status["paused"], "inactive")
        self.assertEqual(status["blocked-by-conflict"], "blocked")
        self.assertEqual(status["failed"], "failed")
        self.assertEqual(status["offline"], "unknown")
        self.assertEqual(status["stale-unknown"], "unknown")
        self.assertEqual(status["review"], "review-pending")
        self.assertIn("unknown-evidence", graph["unknown_workstream_ids"])
        contradictory = node("contradictory", "f" * 40, runtime_condition="paused")
        contradictory["status"] = "active"
        with self.assertRaisesRegex(ValueError, "does not match its independent state axes"):
            build_relation_graph([], nodes=[contradictory])

    def test_completed_takeover_requires_closed_superseded_predecessor(self) -> None:
        completed = relation("rel-successor-predecessor", "derived_from", "successor", "predecessor", lifecycle="completed")
        open_nodes = [node("successor", "b" * 40), node("predecessor", "a" * 40)]
        invalid = build_relation_graph([completed], nodes=open_nodes)
        self.assertFalse(invalid["validation"]["valid"])
        self.assertIn(
            "completed-takeover-predecessor-not-closed-superseded",
            {item["code"] for item in invalid["validation"]["errors"]},
        )
        pair = build_succession_plan(invalid)["compare_pairs"][0]
        self.assertIn("completed-takeover-predecessor-not-closed-superseded", pair["reason_codes"])

        closed_nodes = [
            node("successor", "b" * 40),
            node(
                "predecessor", "a" * 40, lifecycle_phase="closed", runtime_condition="paused",
                closure_reason="superseded",
            ),
        ]
        valid = build_relation_graph([completed], nodes=closed_nodes)
        self.assertTrue(valid["validation"]["valid"])
        self.assertEqual(valid["active_tip_workstream_ids"], ["successor"])
        self.assertEqual(build_succession_plan(valid)["compare_pairs"], [])

    def test_multiple_semantic_predecessors_allow_only_one_primary_git_parent(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertTrue(build_relation_graph(payload["records"], nodes=payload["nodes"])["validation"]["valid"])
        second_parent = relation("rel-w5e-w6-parent", "derived_from", "W5E", "W6")
        graph = build_relation_graph([*payload["records"], second_parent], nodes=payload["nodes"])
        self.assertFalse(graph["validation"]["valid"])
        self.assertIn("multiple-primary-git-parents", {item["code"] for item in graph["validation"]["errors"]})
        with self.assertRaisesRegex(ValueError, "only derived_from can carry a Git task-base OID"):
            relation("rel-dependency-mixed", "depends_on", "W5E", "W5D", task_base="a" * 40)
        with self.assertRaisesRegex(ValueError, "only absorbs can carry an ownership-transfer OID"):
            relation("rel-derived-mixed", "derived_from", "W5E", "W5D", ownership_transfer="a" * 40)

    def test_self_duplicate_and_cycle_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot reference itself"):
            relation("rel-self", "depends_on", "A", "A")
        first = relation("rel-a-b", "depends_on", "A", "B")
        duplicate = copy.deepcopy(first)
        duplicate["relation_id"] = "rel-a-b-copy"
        duplicate["event_id"] = "event-rel-a-b-copy"
        graph = build_relation_graph([first, duplicate])
        self.assertIn("duplicate-edge", {item["code"] for item in graph["validation"]["errors"]})
        cycle = build_relation_graph([first, relation("rel-b-a", "depends_on", "B", "A")])
        self.assertIn("relation-cycle", {item["code"] for item in cycle["validation"]["errors"]})

    def test_exact_oid_ancestry_and_nonancestor_are_verified_locally(self) -> None:
        with LocalGitRepository() as repository:
            base = repository.git("rev-parse", "HEAD").stdout.strip()
            repository.git("switch", "-c", "child")
            child = repository.commit("child.txt", "child\n", "child")
            valid = relation(
                "rel-child-base", "derived_from", "child", "base", lifecycle="active",
                source_head=child, target_head=base, task_base=base, evidence_status="confirmed",
                ancestry_status="confirmed", target_unique=0,
            )
            validate_relation_record(valid, project_root=repository.root)
            absorbed = relation(
                "rel-child-absorbs-base", "absorbs", "child", "base", lifecycle="active",
                source_head=child, target_head=base, evidence_status="confirmed",
                ownership_status="confirmed", ownership_transfer=base, target_unique=0,
            )
            validate_relation_record(absorbed, project_root=repository.root)
            repository.git("switch", "main")
            other = repository.commit("other.txt", "other\n", "other")
            invalid = relation(
                "rel-child-other", "derived_from", "child", "other", lifecycle="active",
                source_head=child, target_head=other, task_base=other, evidence_status="confirmed",
                ancestry_status="confirmed", target_unique=0,
            )
            with self.assertRaisesRegex(ValueError, "not supported by local Git"):
                validate_relation_record(invalid, project_root=repository.root)
            missing = copy.deepcopy(valid)
            missing["evidence"]["source_head_oid"] = "f" * 40
            with self.assertRaisesRegex(ValueError, "does not resolve exactly"):
                validate_relation_record(missing, project_root=repository.root)

    def test_parent_post_fork_sibling_unknown_and_l3_remain_compared(self) -> None:
        parent = "a" * 40
        child = "b" * 40
        sibling = "c" * 40
        nodes = [
            node("parent", parent),
            node("child", child),
        ]
        drift = relation(
            "rel-child-parent", "derived_from", "child", "parent", lifecycle="active",
            source_head=child, target_head=parent, task_base=parent, evidence_status="confirmed",
            ancestry_status="confirmed", target_unique=1,
        )
        drift_graph = build_relation_graph([drift], nodes=nodes)
        self.assertEqual(drift_graph["active_tip_workstream_ids"], ["child", "parent"])
        drift_plan = build_succession_plan(drift_graph)
        self.assertIn("parent-post-fork-or-unknown-commits", drift_plan["compare_pairs"][0]["reason_codes"])

        sibling_nodes = [node("parent", parent, runtime_condition="paused"), node("child", child), node("sibling", sibling)]
        child_edge = relation(
            "rel-child-parent-current", "derived_from", "child", "parent", lifecycle="active",
            source_head=child, target_head=parent, task_base=parent, evidence_status="confirmed",
            ancestry_status="confirmed", target_unique=0,
        )
        sibling_edge = relation(
            "rel-sibling-parent", "derived_from", "sibling", "parent", lifecycle="active",
            source_head=sibling, target_head=parent, task_base=parent, evidence_status="confirmed",
            ancestry_status="confirmed", target_unique=0,
        )
        sibling_plan = build_succession_plan(build_relation_graph([child_edge, sibling_edge], nodes=sibling_nodes))
        pair = next(item for item in sibling_plan["compare_pairs"] if {item["left_workstream_id"], item["right_workstream_id"]} == {"child", "sibling"})
        self.assertIn("sibling-successors", pair["reason_codes"])
        constrained = build_relation_graph(
            [child_edge], nodes=nodes,
            pair_constraints=[{"left_workstream_id":"child","right_workstream_id":"parent","reasons":["l3-exclusive-resource"]}],
        )
        constrained_plan = build_succession_plan(constrained)
        self.assertEqual(constrained_plan["suppress_direct_pairs"], [])
        self.assertIn("l3-exclusive-resource", constrained_plan["compare_pairs"][0]["reason_codes"])

    def test_similarity_is_never_evidence_and_unknown_parent_stays_proposed(self) -> None:
        with LocalGitRepository() as repository:
            plan = discover_relation_candidates(
                repository.root,
                similarity_hints=[{"source_workstream_id":"codex/w7-ui","target_workstream_id":"codex/w5-ui"}],
            )
            self.assertEqual(plan["candidates"], [])
            self.assertEqual(plan["rejected_hints"][0]["status"], "unknown")
            self.assertEqual(plan["rejected_hints"][0]["reason_code"], "branch-or-path-similarity-insufficient-evidence")

        child_head = "d" * 40
        unknown = relation(
            "rel-child-unknown", "derived_from", "child", "missing-parent",
            source_head=child_head,
        )
        graph = build_relation_graph(
            [unknown],
            nodes=[node("child", child_head)],
        )
        self.assertEqual(graph["unknown_workstream_ids"], ["missing-parent"])
        unknown_pair = build_succession_plan(graph)["compare_pairs"][0]
        self.assertIn("stale-or-unknown-endpoint", unknown_pair["reason_codes"])

    def test_stale_head_and_scope_evidence_never_suppress(self) -> None:
        parent_head = "a" * 40
        child_head = "b" * 40
        stale = relation(
            "rel-child-stale-parent", "derived_from", "child", "parent", lifecycle="active",
            source_head=child_head, target_head=parent_head, task_base=parent_head,
            evidence_status="confirmed", ancestry_status="confirmed", target_unique=0,
        )
        stale["evidence"]["source_head_status"] = "stale"
        stale["evidence"]["scope_status"] = "stale"
        nodes = [
            node("child", child_head),
            node("parent", parent_head),
        ]
        graph = build_relation_graph([stale], nodes=nodes)
        edge = graph["edges"][0]
        self.assertFalse(edge["effective_active_succession"])
        self.assertIn("head-stale-or-unknown", edge["evidence_reason_codes"])
        self.assertIn("scope-stale-or-unknown", edge["evidence_reason_codes"])
        plan = build_succession_plan(graph)
        self.assertEqual(plan["suppress_direct_pairs"], [])
        self.assertEqual(
            {(item["left_workstream_id"], item["right_workstream_id"]) for item in plan["compare_pairs"]},
            {("child", "parent")},
        )

    def test_storage_is_append_only_author_tree_clean_and_survives_worktree_removal(self) -> None:
        with LocalGitRepository() as repository:
            relation_root = relation_storage_root(repository.root)
            self.assertFalse(relation_root.exists())
            empty = load_relation_history(repository.root)
            self.assertEqual(empty["current_records"], [])
            self.assertFalse(relation_root.exists())
            before = repository.git("status", "--short").stdout
            linked = Path(repository.temporary.name) / "linked"
            repository.git("worktree", "add", "-b", "relation-linked", str(linked), "main")
            with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
                appended = append_proposed_relation(
                    linked,
                    relation_id="rel-local-proposed",
                    relation_type="depends_on",
                    source_workstream_id="later-ci",
                    target_workstream_id="w5e",
                    reason="explicit local proposal",
                    actor_id="maintainer",
                    recorded_at=TIMESTAMP,
                )
            self.assertTrue(appended["writes_performed"])
            self.assertEqual(repository.git("status", "--short").stdout, before)
            with self.assertRaisesRegex(ValueError, "already has append-only history"):
                append_proposed_relation(
                    linked, relation_id="rel-local-proposed", relation_type="depends_on",
                    source_workstream_id="later-ci", target_workstream_id="w5e",
                    reason="must not overwrite", actor_id="maintainer", recorded_at=TIMESTAMP,
                )
            repository.git("worktree", "remove", str(linked))
            loaded = load_relation_history(repository.root)
            self.assertEqual([item["relation_id"] for item in loaded["current_records"]], ["rel-local-proposed"])
            self.assertFalse(linked.exists())

    def test_legacy_task_base_projects_read_only_without_session_rewrite(self) -> None:
        with CollaborationGitFixture() as fixture:
            parent = fixture.worktree_a
            parent_file = parent / "parent.txt"
            parent_file.write_text("parent\n", encoding="utf-8")
            fixture.git(parent, "add", "parent.txt")
            fixture.git(parent, "commit", "-m", "parent")
            parent_head = fixture.git(parent, "rev-parse", "HEAD").stdout.strip()
            write_workstream_session(parent, workstream_id="parent", primary_subsystem_id="project-structure")
            child = fixture.root / "relation-child"
            create_worktree(
                parent, workstream_id="child", branch="codex/relation-child", path=child,
                primary_subsystem_id="project-structure", base_workstream_id="parent", task_base_oid=parent_head,
            )
            parent_session = Path(fixture.git(parent, "rev-parse", "--git-path", "orrery/worktree.json").stdout.strip())
            child_session = Path(fixture.git(child, "rev-parse", "--git-path", "orrery/worktree.json").stdout.strip())
            before = (parent_session.read_bytes(), child_session.read_bytes())
            projection = load_legacy_session_projection(fixture.repository)
            edge = next(item for item in projection["records"] if item["source_workstream_id"] == "child")
            self.assertEqual(edge["relation_type"], "derived_from")
            self.assertEqual(edge["target_workstream_id"], "parent")
            self.assertEqual(edge["evidence"]["task_base_oid"], parent_head)
            self.assertFalse(projection["writes_performed"])
            self.assertEqual((parent_session.read_bytes(), child_session.read_bytes()), before)

    def test_archived_relation_endpoint_restores_closed_axes_and_binds_graph_hash(self) -> None:
        with LocalGitRepository() as repository:
            fixture = self._archived_lineage_fixture(repository)
            archive_file = fixture["archive_file"]
            self.assertIsInstance(archive_file, Path)
            before_bytes = archive_file.read_bytes()
            child_session = fixture["child_session"]
            self.assertIsInstance(child_session, Path)
            before_child_session = child_session.read_bytes()
            before_status = repository.git("status", "--short").stdout
            self.assertFalse(relation_storage_root(repository.root).exists())
            self.assertFalse(Path(fixture["parent"]).exists())
            with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
                graph = load_relation_graph(repository.root)
            archived = next(
                item for item in graph["nodes"]
                if item["workstream_id"] == "W5D-lan-collaboration-harness"
            )
            self.assertEqual(
                (
                    archived["session_state"],
                    archived["lifecycle_phase"],
                    archived["runtime_condition"],
                    archived["evidence_freshness"],
                    archived["scope_status"],
                    archived["closure_reason"],
                ),
                ("current", "closed", "offline", "current", "current", "superseded"),
            )
            self.assertEqual(archived["status"], "completed")
            self.assertEqual(archived["head_oid"], fixture["parent_head"])
            archive_index = load_archived_session_index(
                repository.root,
                referenced_workstream_ids=["W5D-lan-collaboration-harness"],
            )
            archived_endpoint = archive_index["resolved_sessions"][0]
            self.assertEqual(archived_endpoint["origin"], "retired-session-archive")
            self.assertEqual(
                archived_endpoint["session"]["branch"],
                "refs/heads/codex/w5d-archived",
            )
            self.assertEqual(archived["origin"], "legacy-session-projection")
            self.assertEqual(archived["visibility"], "git-private-local-only")
            self.assertEqual(archived["observability"], "retired-archive-local")
            self.assertNotIn(archived["workstream_id"], graph["active_tip_workstream_ids"])
            self.assertNotEqual(archived["status"], "review-pending")
            archive_link = archived["source_links"][0]["ref"]
            self.assertRegex(archive_link, r"^retired-session-archive:sha256:[0-9a-f]{64}$")
            self.assertNotIn(str(fixture["archive_root"]), json.dumps(graph, sort_keys=True))

            edge = next(
                item for item in graph["edges"]
                if item["source_workstream_id"] == "CI1-tiered-parallel-validation"
                and item["target_workstream_id"] == "W5D-lan-collaboration-harness"
            )
            self.assertEqual(edge["evidence"]["target_head_status"], "current")
            self.assertFalse(edge["effective_active_succession"])
            self.assertIn("predecessor-lifecycle-not-active-takeover", edge["evidence_reason_codes"])
            self.assertEqual(build_succession_plan(graph)["suppress_direct_pairs"], [])
            self.assertEqual(archive_file.read_bytes(), before_bytes)
            self.assertEqual(child_session.read_bytes(), before_child_session)
            self.assertEqual(repository.git("status", "--short").stdout, before_status)
            self.assertFalse(relation_storage_root(repository.root).exists())

            changed = json.loads(archive_file.read_text(encoding="utf-8"))
            changed["captured_at"] = "2026-08-28T23:59:59Z"
            archive_file.write_text(json.dumps(changed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            changed_graph = load_relation_graph(repository.root)
            self.assertNotEqual(changed_graph["graph_hash"], graph["graph_hash"])
            changed_link = next(
                item for item in changed_graph["nodes"]
                if item["workstream_id"] == "W5D-lan-collaboration-harness"
            )["source_links"][0]["ref"]
            self.assertNotEqual(changed_link, archive_link)

            discovery = discover_relation_candidates(repository.root)
            candidate = next(
                item for item in discovery["candidates"]
                if item["target_workstream_id"] == "W5D-lan-collaboration-harness"
            )
            self.assertEqual(candidate["evidence"]["target_head_status"], "unknown")
            self.assertNotEqual(candidate["evidence"]["status"], "confirmed")

    def test_archived_session_live_precedence_equivalent_duplicates_conflict_and_unreferenced(self) -> None:
        with LocalGitRepository() as repository:
            fixture = self._archived_lineage_fixture(repository, keep_parent_live=True)
            parent = fixture["parent"]
            self.assertIsInstance(parent, Path)
            live_parent_session = fixture["parent_session"]
            self.assertIsInstance(live_parent_session, Path)
            live_parent_record = json.loads(live_parent_session.read_text(encoding="utf-8"))
            live_parent_record.update({
                "lifecycle_phase": "validating",
                "runtime_condition": "waiting-for-user",
                "evidence_freshness": "current",
                "closure_reason": None,
                "captured_at": "2026-08-29T01:00:00Z",
            })
            _write_private_session(parent, live_parent_record)
            live_projection = load_legacy_session_projection(repository.root)
            live_node = next(
                item for item in live_projection["nodes"]
                if item["workstream_id"] == "W5D-lan-collaboration-harness"
            )
            self.assertEqual(live_node["origin"], "legacy-session-projection")
            self.assertEqual(live_node["runtime_condition"], "waiting-for-user")

            repository.git("worktree", "remove", str(parent))
            archive_file = fixture["archive_file"]
            archive_root = fixture["archive_root"]
            self.assertIsInstance(archive_file, Path)
            self.assertIsInstance(archive_root, Path)
            original = archive_file.read_bytes()
            entry_name = archive_file.parent.name
            exact_duplicate = archive_root / "2026-08-30" / entry_name / "worktree.json"
            exact_duplicate.parent.mkdir(parents=True)
            exact_duplicate.write_bytes(original)
            semantic_duplicate = archive_root / "2026-08-31" / entry_name / "worktree.json"
            semantic_duplicate.parent.mkdir(parents=True)
            semantic_duplicate.write_text(
                json.dumps(json.loads(original.decode("utf-8")), separators=(",", ":")),
                encoding="utf-8",
            )
            unrelated = json.loads(original.decode("utf-8"))
            unrelated["workstream_id"] = "unreferenced-history"
            unrelated_file = archive_root / "2026-09-01" / entry_name / "worktree.json"
            unrelated_file.parent.mkdir(parents=True)
            unrelated_file.write_text(json.dumps(unrelated, sort_keys=True), encoding="utf-8")
            deduped = load_archived_session_index(
                repository.root,
                referenced_workstream_ids=["W5D-lan-collaboration-harness"],
            )
            self.assertEqual(deduped["resolved_workstream_ids"], ["W5D-lan-collaboration-harness"])
            self.assertEqual(deduped["resolved_sessions"][0]["equivalent_copy_count"], 3)
            self.assertRegex(
                deduped["resolved_sessions"][0]["evidence_id"],
                r"^retired-session-archive:sha256:[0-9a-f]{64}$",
            )
            self.assertEqual(deduped["unreferenced_archive_count"], 1)
            append_proposed_relation(
                repository.root,
                relation_id="native-ci1-w5d",
                relation_type="derived_from",
                source_workstream_id="CI1-tiered-parallel-validation",
                target_workstream_id="W5D-lan-collaboration-harness",
                reason="synthetic native precedence",
                actor_id="maintainer",
                recorded_at=TIMESTAMP,
            )

            conflict = json.loads(original.decode("utf-8"))
            conflict["captured_at"] = "2026-08-29T02:00:00Z"
            conflict_file = archive_root / "2026-09-02" / entry_name / "worktree.json"
            conflict_file.parent.mkdir(parents=True)
            conflict_file.write_text(json.dumps(conflict, sort_keys=True), encoding="utf-8")
            conflicted = load_relation_graph(repository.root)
            matching_edges = [
                item for item in conflicted["edges"]
                if item["relation_type"] == "derived_from"
                and item["source_workstream_id"] == "CI1-tiered-parallel-validation"
                and item["target_workstream_id"] == "W5D-lan-collaboration-harness"
            ]
            self.assertEqual(len(matching_edges), 1)
            self.assertEqual(matching_edges[0]["origin"], "native")
            conflict_node = next(
                item for item in conflicted["nodes"]
                if item["workstream_id"] == "W5D-lan-collaboration-harness"
            )
            self.assertNotIn(
                "unreferenced-history",
                {item["workstream_id"] for item in conflicted["nodes"]},
            )
            self.assertEqual(conflict_node["status"], "unknown")
            self.assertEqual(conflict_node["origin"], "relation-only")
            self.assertRegex(
                conflict_node["source_links"][0]["ref"],
                r"^retired-session-archive-conflict:sha256:[0-9a-f]{64}$",
            )
            self.assertNotIn("W5D-lan-collaboration-harness", conflicted["active_tip_workstream_ids"])

    def test_archived_session_reader_rejects_malformed_unknown_inconsistent_and_unsafe_inputs(self) -> None:
        with LocalGitRepository() as repository:
            fixture = self._archived_lineage_fixture(repository)
            archive_file = fixture["archive_file"]
            archive_root = fixture["archive_root"]
            self.assertIsInstance(archive_file, Path)
            self.assertIsInstance(archive_root, Path)
            original = archive_file.read_bytes()

            archive_file.write_bytes(b"{not-json")
            with self.assertRaisesRegex(ValueError, "archive session JSON"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            archive_file.write_bytes(original)

            unknown_schema = json.loads(original.decode("utf-8"))
            unknown_schema["schema_version"] = 2
            archive_file.write_text(json.dumps(unknown_schema), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported archived Workstream session"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            archive_file.write_bytes(original)

            unreferenced_unknown = json.loads(original.decode("utf-8"))
            unreferenced_unknown.update({"workstream_id": "unreferenced-unknown", "schema_version": 2})
            unreferenced_unknown_file = (
                archive_root / "2026-08-30" / archive_file.parent.name / "worktree.json"
            )
            unreferenced_unknown_file.parent.mkdir(parents=True)
            unreferenced_unknown_file.write_text(json.dumps(unreferenced_unknown), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported archived Workstream session"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            shutil.rmtree(unreferenced_unknown_file.parents[1])

            inconsistent = json.loads(original.decode("utf-8"))
            inconsistent["branch"] = "refs/heads/codex/missing-archive-branch"
            archive_file.write_text(json.dumps(inconsistent), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "archive branch"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            archive_file.write_bytes(original)

            wrong_entry = archive_file.parent.with_name("codex-w5d-archived-deadbeef")
            archive_file.parent.rename(wrong_entry)
            wrong_file = wrong_entry / "worktree.json"
            with self.assertRaisesRegex(ValueError, "archive entry identity"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            wrong_entry.rename(archive_file.parent)

            archive_file.write_bytes(b"x" * (relation_core.ARCHIVE_MAX_FILE_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "size limit"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            archive_file.write_bytes(original)

            extra_depth = archive_file.parent / "nested"
            extra_depth.mkdir()
            with self.assertRaisesRegex(ValueError, "exactly one worktree.json"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            extra_depth.rmdir()

            aggregate_duplicate = (
                archive_root / "2026-08-30" / archive_file.parent.name / "worktree.json"
            )
            aggregate_duplicate.parent.mkdir(parents=True)
            aggregate_duplicate.write_bytes(original)
            with mock.patch.object(
                relation_core,
                "ARCHIVE_MAX_TOTAL_BYTES",
                len(original) * 2 - 1,
            ):
                with self.assertRaisesRegex(ValueError, "aggregate size limit"):
                    load_archived_session_index(
                        repository.root,
                        referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                    )
            shutil.rmtree(aggregate_duplicate.parents[1])

            unsafe_entry = archive_root / "2026-08-29" / "..unsafe"
            unsafe_entry.mkdir()
            (unsafe_entry / "worktree.json").write_bytes(original)
            with self.assertRaisesRegex(ValueError, "unsafe archive entry"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            shutil.rmtree(unsafe_entry)

            archive_file.unlink()
            archive_file.mkdir()
            with self.assertRaisesRegex(ValueError, "regular file"):
                load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            archive_file.rmdir()
            archive_file.write_bytes(original)

            original_reparse_check = relation_core._is_reparse_or_symlink
            with mock.patch.object(
                relation_core,
                "_is_reparse_or_symlink",
                side_effect=lambda path: Path(path) == archive_file or original_reparse_check(Path(path)),
            ):
                with self.assertRaisesRegex(ValueError, "symlink or reparse"):
                    load_archived_session_index(
                        repository.root,
                        referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                    )

            symlink_target = Path(repository.temporary.name) / "outside-session.json"
            symlink_target.write_bytes(original)
            archive_file.unlink()
            try:
                archive_file.symlink_to(symlink_target)
            except OSError:
                archive_file.write_bytes(original)
            else:
                with self.assertRaisesRegex(ValueError, "symlink or reparse"):
                    load_archived_session_index(
                        repository.root,
                        referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                    )
                archive_file.unlink()
                archive_file.write_bytes(original)

            with mock.patch.object(relation_core, "ARCHIVE_MAX_FILES", 3):
                for offset in range(3):
                    duplicate = (
                        archive_root
                        / f"{2100 + offset:04d}-01-01"
                        / archive_file.parent.name
                        / "worktree.json"
                    )
                    duplicate.parent.mkdir(parents=True)
                    duplicate.write_bytes(original)
                with self.assertRaisesRegex(ValueError, "file count limit"):
                    load_archived_session_index(
                        repository.root,
                        referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                    )

    def test_archived_session_index_is_read_only_zero_network_and_has_no_execution_surface(self) -> None:
        with LocalGitRepository() as repository:
            fixture = self._archived_lineage_fixture(repository)
            archive_file = fixture["archive_file"]
            archive_root = fixture["archive_root"]
            self.assertIsInstance(archive_file, Path)
            self.assertIsInstance(archive_root, Path)
            before = archive_file.read_bytes()
            extras_file = (
                archive_root.parent
                / "retired-worktree-session-extras"
                / "2026-09-01"
                / "archived-fixture-extras"
                / "ci-validation"
                / "receipt.json"
            )
            extras_file.parent.mkdir(parents=True)
            extras_file.write_bytes(b'{"preserved":true}\n')
            extras_before = extras_file.read_bytes()
            author_status = repository.git("status", "--short").stdout
            with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
                index = load_archived_session_index(
                    repository.root,
                    referenced_workstream_ids=["W5D-lan-collaboration-harness"],
                )
            self.assertFalse(index["writes_performed"])
            self.assertFalse(index["network_performed"])
            self.assertFalse(index["execution_supported"])
            self.assertEqual(index["destructive_actions"], [])
            self.assertEqual(index["resolved_workstream_ids"], ["W5D-lan-collaboration-harness"])
            self.assertEqual(archive_file.read_bytes(), before)
            self.assertEqual(extras_file.read_bytes(), extras_before)
            self.assertEqual(repository.git("status", "--short").stdout, author_status)
            serialized = json.dumps(index, sort_keys=True)
            self.assertNotIn(str(archive_root), serialized)
            for forbidden in (
                "apply", "undo", "review-ready", "write-session", "create-relation",
                "create-worktree", "online", "active-tip",
            ):
                self.assertNotIn(f'"{forbidden}"', serialized)

    def test_apply_undo_and_discovery_contracts_bind_session_receipt_and_no_drift(self) -> None:
        candidate = relation("rel-future", "derived_from", "future-ci", "W5E")
        discovery = build_discovery_plan([candidate], graph_hash="a" * 64)
        predecessor = {
            "workstream_id": "W5E", "session_hash": "b" * 64, "session_state": "current",
            "head_oid": "c" * 40, "lifecycle_phase": "validating", "runtime_condition": "active",
            "evidence_freshness": "current", "scope_status": "current", "closure_reason": None,
        }
        active_request = {
            "relation_id": "rel-future", "target_lifecycle": "active",
            "predecessor_session": predecessor,
            "transition": {
                "lifecycle_phase": "validating", "runtime_condition": "paused",
                "evidence_freshness": "current", "closure_reason": None,
            },
        }
        apply_plan = build_apply_plan(discovery, takeover_requests=[active_request])
        append_operation = next(item for item in apply_plan["operations"] if item["action"] == "append-relation-event")
        receipt = {
            "schema_version": 1,
            "contract_type": "workstream-relation-apply-receipt",
            "receipt_id": "receipt-local-1",
            "plan_id": apply_plan["plan_id"],
            "plan_hash": apply_plan["plan_hash"],
            "graph_hash": apply_plan["graph_hash"],
            "confirmed_locally": True,
            "relation_events": [{
                "relation_id": "rel-future", "event_id": "event-rel-future-applied",
                "event_hash": append_operation["event_hash"], "prior_lifecycle": None,
                "resulting_lifecycle": "active",
            }],
            "predecessor_transitions": [{
                "relation_id": "rel-future", "workstream_id": "W5E",
                "original_session_hash": "b" * 64, "resulting_session_hash": "d" * 64,
                "original_head_oid": "c" * 40, "resulting_head_oid": "c" * 40,
                "original_lifecycle_phase": "validating", "resulting_lifecycle_phase": "validating",
                "original_runtime_condition": "active", "resulting_runtime_condition": "paused",
                "original_evidence_freshness": "current", "resulting_evidence_freshness": "current",
                "original_scope_status": "current", "resulting_scope_status": "current",
                "original_closure_reason": None, "resulting_closure_reason": None,
            }],
            "writes_performed": True,
        }
        validate_apply_receipt(receipt, apply_plan=apply_plan)
        undo_plan = build_undo_plan(apply_receipt=receipt)
        self.assertTrue(discovery["confirmation_required"])
        self.assertFalse(apply_plan["execution_supported"])
        self.assertEqual(apply_plan["atomicity"], "all-operations-or-none")
        self.assertEqual(apply_plan["no_drift_policy"], "exact-graph-session-and-head-or-fail")
        self.assertEqual(apply_plan["destructive_actions"], [])
        self.assertEqual(apply_plan["output_contract"]["contract_type"], "workstream-relation-apply-receipt")
        self.assertTrue(all(apply_plan["preservation_contract"].values()))
        self.assertFalse(undo_plan["deletes_history"])
        self.assertEqual(undo_plan["no_drift_policy"], "exact-receipt-session-and-head-or-fail")
        self.assertEqual(undo_plan["output_contract"]["contract_type"], "workstream-relation-undo-receipt")
        self.assertTrue(all(undo_plan["preservation_contract"].values()))
        self.assertEqual(undo_plan["operations"][0]["action"], "append-compensating-event")
        restore = next(item for item in undo_plan["operations"] if item["action"] == "restore-predecessor-session")
        self.assertEqual(restore["expected_session_hash"], "d" * 64)
        self.assertEqual(restore["restore_session_hash"], "b" * 64)
        drifted = copy.deepcopy(receipt)
        drifted["plan_hash"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "does not match the exact apply plan"):
            validate_apply_receipt(drifted, apply_plan=apply_plan)

        completed_request = copy.deepcopy(active_request)
        completed_request["target_lifecycle"] = "completed"
        completed_request["transition"] = {
            "lifecycle_phase": "closed", "runtime_condition": "paused",
            "evidence_freshness": "current", "closure_reason": "superseded",
        }
        completed_plan = build_apply_plan(discovery, takeover_requests=[completed_request])
        self.assertTrue(any(
            item["action"] == "transition-predecessor-session" and item["target_lifecycle_phase"] == "closed"
            for item in completed_plan["operations"]
        ))
        incomplete_request = copy.deepcopy(completed_request)
        incomplete_request["transition"] = None
        with self.assertRaisesRegex(ValueError, "requires closed/superseded predecessor or atomic transition"):
            build_apply_plan(discovery, takeover_requests=[incomplete_request])
        for payload in (discovery, apply_plan, undo_plan):
            serialized = json.dumps(payload, sort_keys=True)
            self.assertNotIn("delete-worktree", serialized)
            self.assertNotIn("delete-branch", serialized)

    def test_w7c_consumer_compatibility_fixture_maps_without_ui_authority(self) -> None:
        payload = json.loads(W7C_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["authority"], "synthetic-non-authoritative")
        graph = build_relation_graph(payload["records"], nodes=payload["nodes"])
        plan = build_succession_plan(graph)
        self.assertTrue(graph["validation"]["valid"])
        for graph_node in graph["nodes"]:
            self.assertTrue(set(payload["required_node_fields"]).issubset(graph_node))
        for edge in graph["edges"]:
            self.assertTrue(set(payload["required_edge_fields"]).issubset(edge))
        self.assertTrue(set(payload["required_plan_fields"]).issubset(plan))
        self.assertEqual(graph["active_tip_workstream_ids"], ["successor"])
        self.assertEqual(graph["unknown_workstream_ids"], ["unknown-peer"])
        serialized = json.dumps({"graph": graph, "plan": plan}, sort_keys=True)
        for forbidden in ('"color"', '"coordinates"', '"layout"', '"collapsed"', '"ui_text"'):
            self.assertNotIn(forbidden, serialized)
        unsafe = copy.deepcopy(payload["records"][0])
        unsafe["source_links"][0]["ref"] = "fixture:unsafe\nlink"
        with self.assertRaisesRegex(ValueError, "source link ref"):
            build_relation_graph([unsafe], nodes=payload["nodes"])

    def test_graph_and_cli_json_are_deterministic(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        first = build_relation_graph(payload["records"], nodes=payload["nodes"])
        second = build_relation_graph(list(reversed(payload["records"])), nodes=list(reversed(payload["nodes"])))
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        with LocalGitRepository() as repository:
            outputs: list[str] = []
            for _ in range(2):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    exit_code = relations_cli.main(["graph", "--target", str(repository.root), "--no-legacy", "--json"])
                self.assertEqual(exit_code, 0)
                outputs.append(stream.getvalue())
            self.assertEqual(outputs[0], outputs[1])
            envelope = json.loads(outputs[0])
            self.assertEqual(envelope["command"], "workstream-relation-graph")
            self.assertEqual(envelope["data"]["active_tip_workstream_ids"], [])

    def test_cli_propose_is_explicit_and_graph_plan_are_read_only(self) -> None:
        parsed = relations_cli.build_parser().parse_args([
            "propose", "--relation-id", "rel-cli", "--type", "depends_on",
            "--source", "CI-new", "--target-workstream", "W5E", "--reason", "local confirmation",
            "--actor-id", "maintainer",
        ])
        self.assertEqual(parsed.relation_type, "depends_on")
        with LocalGitRepository() as repository:
            propose_output = io.StringIO()
            with contextlib.redirect_stdout(propose_output):
                exit_code = relations_cli.main([
                    "propose", "--target", str(repository.root), "--json", "--relation-id", "rel-cli",
                    "--type", "depends_on", "--source", "CI-new", "--target-workstream", "W5E",
                    "--reason", "local confirmation", "--actor-id", "maintainer", "--recorded-at", TIMESTAMP,
                ])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(propose_output.getvalue())["data"]["record"]["lifecycle"], "proposed")
            before = list(relation_storage_root(repository.root).rglob("*.json"))
            for command in ("graph", "succession-plan"):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(relations_cli.main([command, "--target", str(repository.root), "--no-legacy", "--json"]), 0)
            self.assertEqual(list(relation_storage_root(repository.root).rglob("*.json")), before)


if __name__ == "__main__":
    unittest.main()
