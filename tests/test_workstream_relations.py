from __future__ import annotations

import contextlib
import copy
import io
import json
import os
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
from project_orrery_core.collaboration import create_worktree, write_workstream_session  # noqa: E402
from project_orrery_core.schema import WORKSTREAM_RELATIONS_SCHEMA  # noqa: E402
from project_orrery_core.workstream_relations import (  # noqa: E402
    append_proposed_relation,
    build_apply_plan,
    build_discovery_plan,
    build_relation_graph,
    build_relation_record,
    build_succession_plan,
    build_undo_plan,
    default_relation_evidence,
    discover_relation_candidates,
    load_legacy_session_projection,
    load_relation_graph,
    load_relation_history,
    relation_storage_root,
    validate_relation_record,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "workstream-relations" / "v1" / "succession-chain.json"
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
        self.commit("base.txt", "base\n", "base")

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


class WorkstreamRelationTests(unittest.TestCase):
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
            {"workstream_id":"parent","status":"active","evidence_status":"current","head_oid":parent,"scope_status":"current","source_links":[],"origin":"native"},
            {"workstream_id":"child","status":"active","evidence_status":"current","head_oid":child,"scope_status":"current","source_links":[],"origin":"native"},
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

        sibling_nodes = [*nodes, {"workstream_id":"sibling","status":"active","evidence_status":"current","head_oid":sibling,"scope_status":"current","source_links":[],"origin":"native"}]
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
            nodes=[{
                "workstream_id": "child", "status": "active", "evidence_status": "current",
                "head_oid": child_head, "scope_status": "current", "source_links": [], "origin": "native",
            }],
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
            {"workstream_id":"child","status":"active","evidence_status":"current","head_oid":child_head,"scope_status":"current","source_links":[],"origin":"native"},
            {"workstream_id":"parent","status":"active","evidence_status":"current","head_oid":parent_head,"scope_status":"current","source_links":[],"origin":"native"},
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

    def test_apply_undo_and_discovery_contracts_never_delete_or_execute(self) -> None:
        candidate = relation("rel-future", "depends_on", "future-ci", "W5E")
        discovery = build_discovery_plan([candidate], graph_hash="a" * 64)
        apply_plan = build_apply_plan(discovery)
        undo_plan = build_undo_plan(apply_receipt_id="receipt-local-1", relation_ids=["rel-future"])
        self.assertTrue(discovery["confirmation_required"])
        self.assertFalse(apply_plan["execution_supported"])
        self.assertEqual(apply_plan["destructive_actions"], [])
        self.assertEqual(apply_plan["output_contract"]["contract_type"], "workstream-relation-apply-receipt")
        self.assertTrue(all(apply_plan["preservation_contract"].values()))
        self.assertFalse(undo_plan["deletes_history"])
        self.assertEqual(undo_plan["output_contract"]["contract_type"], "workstream-relation-undo-receipt")
        self.assertTrue(all(undo_plan["preservation_contract"].values()))
        self.assertEqual(undo_plan["operations"][0]["action"], "append-compensating-event")
        for payload in (discovery, apply_plan, undo_plan):
            serialized = json.dumps(payload, sort_keys=True)
            self.assertNotIn("delete-worktree", serialized)
            self.assertNotIn("delete-branch", serialized)

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
