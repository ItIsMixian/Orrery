"""Read-only Workstream graph/plan CLI plus explicit proposed append."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.workstream_relations import (
    EVIDENCE_STATES,
    HEAD_STATES,
    RELATION_TYPES,
    append_proposed_relation,
    build_succession_plan,
    default_relation_evidence,
    load_relation_graph,
)

from .protocol import JsonExitCode, emit, issue, response


def _add_target(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--no-legacy", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and propose versioned Workstream relations")
    actions = parser.add_subparsers(dest="action", required=True)
    graph = actions.add_parser("graph", help="load the read-only Core relation graph")
    _add_target(graph)
    plan = actions.add_parser("succession-plan", help="compute deterministic active-tip conflict pairs")
    _add_target(plan)
    propose = actions.add_parser("propose", help="explicitly append one proposed relation in Git-private storage")
    propose.add_argument("--target", type=Path, default=Path("."))
    propose.add_argument("--json", action="store_true", dest="json_output")
    propose.add_argument("--relation-id", required=True)
    propose.add_argument("--type", required=True, choices=RELATION_TYPES, dest="relation_type")
    propose.add_argument("--source", required=True, dest="source_workstream_id")
    propose.add_argument("--target-workstream", required=True, dest="target_workstream_id")
    propose.add_argument("--reason", required=True)
    propose.add_argument("--actor-id", required=True)
    propose.add_argument("--recorded-at")
    propose.add_argument("--source-head-oid")
    propose.add_argument("--target-head-oid")
    propose.add_argument("--task-base-oid")
    propose.add_argument("--ownership-transfer-oid")
    propose.add_argument("--source-head-status", choices=HEAD_STATES, default="unknown")
    propose.add_argument("--target-head-status", choices=HEAD_STATES, default="unknown")
    propose.add_argument("--scope-status", choices=HEAD_STATES, default="unknown")
    propose.add_argument("--ancestry-status", choices=EVIDENCE_STATES)
    propose.add_argument("--dependency-status", choices=EVIDENCE_STATES)
    propose.add_argument("--ownership-transfer-status", choices=EVIDENCE_STATES)
    propose.add_argument("--target-unique-commits-after-base", type=int)
    propose.add_argument("--source-link", action="append", default=[], metavar="KIND=REF")
    return parser


def _source_links(values: list[str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for value in values:
        kind, separator, reference = value.partition("=")
        if not separator or not kind or not reference:
            raise ValueError("--source-link must use KIND=REF")
        result.append({"kind": kind, "ref": reference})
    return result


def _failure(command: str, json_output: bool, exc: ValueError) -> int:
    if json_output:
        emit(response(
            command,
            status="error",
            exit_code=JsonExitCode.OPERATION_FAILED,
            errors=[issue("workstream_relation_operation_failed", str(exc))],
        ))
    else:
        print(f"ERROR: {exc}", file=sys.stderr)
    return int(JsonExitCode.OPERATION_FAILED)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.action in {"graph", "succession-plan"}:
        command = "workstream-relation-graph" if arguments.action == "graph" else "workstream-succession-plan"
        try:
            graph = load_relation_graph(arguments.target, include_legacy=not arguments.no_legacy)
            data = graph if arguments.action == "graph" else build_succession_plan(graph)
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        valid = graph["validation"]["valid"]
        exit_code = JsonExitCode.OK if valid else JsonExitCode.COMPATIBILITY_FAILED
        warnings = [] if valid else [issue("relation_graph_invalid", "relation graph failed structural validation")]
        if arguments.json_output:
            emit(response(command, status="ok" if valid else "warning", exit_code=exit_code, data=data, warnings=warnings))
        elif arguments.action == "graph":
            print(f"Nodes: {len(graph['nodes'])}")
            print(f"Edges: {len(graph['edges'])}")
            print(f"Active tips: {len(graph['active_tip_workstream_ids'])}")
            print(f"Valid: {'yes' if valid else 'no'}")
        else:
            print(f"Active tips: {len(data['active_tip_workstream_ids'])}")
            print(f"Compare pairs: {len(data['compare_pairs'])}")
            print(f"Suppressed ancestor pairs: {len(data['suppress_direct_pairs'])}")
        return int(exit_code)

    command = "workstream-relation-propose"
    ancestry = arguments.ancestry_status
    dependency = arguments.dependency_status
    ownership = arguments.ownership_transfer_status
    if ancestry is None:
        ancestry = "unknown" if arguments.relation_type == "derived_from" else "not-applicable"
    if dependency is None:
        dependency = "unknown" if arguments.relation_type == "depends_on" else "not-applicable"
    if ownership is None:
        ownership = "unknown" if arguments.relation_type == "absorbs" else "not-applicable"
    evidence = default_relation_evidence(
        status="unknown",
        source_head_oid=arguments.source_head_oid,
        target_head_oid=arguments.target_head_oid,
        task_base_oid=arguments.task_base_oid,
        ownership_transfer_oid=arguments.ownership_transfer_oid,
        source_head_status=arguments.source_head_status,
        target_head_status=arguments.target_head_status,
        scope_status=arguments.scope_status,
        ancestry_status=ancestry,
        dependency_status=dependency,
        ownership_transfer_status=ownership,
        target_unique_commits_after_base=arguments.target_unique_commits_after_base,
    )
    try:
        data = append_proposed_relation(
            arguments.target,
            relation_id=arguments.relation_id,
            relation_type=arguments.relation_type,
            source_workstream_id=arguments.source_workstream_id,
            target_workstream_id=arguments.target_workstream_id,
            reason=arguments.reason,
            actor_id=arguments.actor_id,
            recorded_at=arguments.recorded_at,
            evidence=evidence,
            source_links=_source_links(arguments.source_link),
        )
    except ValueError as exc:
        return _failure(command, arguments.json_output, exc)
    if arguments.json_output:
        emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
    else:
        record = data["record"]
        print(f"Proposed relation: {record['relation_id']}")
        print(f"Edge: {record['source_workstream_id']} -> {record['target_workstream_id']}")
        print("Storage: git-common-private append-only")
    return int(JsonExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
