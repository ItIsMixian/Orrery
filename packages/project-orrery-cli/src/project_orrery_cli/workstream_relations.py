"""Dependency-light Workstream relation discovery, plan, apply, undo, and inspection CLI."""
from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path
from typing import Any, Mapping

from project_orrery_core.workstream_relation_execution import (
    RecoveryRequiredError,
    build_execution_plan,
    build_execution_undo_plan,
    discover_execution_candidates,
    execute_apply_plan,
    execute_undo_plan,
    inspect_execution_state,
    issue_local_confirmation,
    issue_local_undo_confirmation,
    load_execution_receipt,
    recover_transaction,
)
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


_MAX_INPUT_BYTES = 2 * 1024 * 1024


def _add_target(parser: argparse.ArgumentParser, *, legacy: bool = False) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")
    if legacy:
        parser.add_argument("--no-legacy", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and execute exact local Workstream relation plans")
    actions = parser.add_subparsers(dest="action", required=True)
    graph = actions.add_parser("graph", help="load the read-only Core relation graph")
    _add_target(graph, legacy=True)
    succession = actions.add_parser("succession-plan", help="compute deterministic active-tip conflict pairs")
    _add_target(succession, legacy=True)
    propose = actions.add_parser("propose", help="explicitly append one proposed relation")
    _add_target(propose)
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

    discover = actions.add_parser("discover", help="infer proposed/Unknown candidates from exact local evidence")
    _add_target(discover)
    discover.add_argument("--spec", type=Path, help="bounded JSON explicit relation/hint input")
    discover.add_argument("--recorded-at")

    plan = actions.add_parser("plan", help="build an exact hash-bound batch apply plan")
    _add_target(plan)
    plan.add_argument("--discovery", type=Path, required=True)
    plan.add_argument("--lifecycle", action="append", required=True, metavar="RELATION_ID=STATE")
    plan.add_argument("--actor-id", required=True)
    plan.add_argument("--issued-at")
    plan.add_argument("--expires-at")
    plan.add_argument("--confirm-local", action="store_true")

    apply = actions.add_parser("apply", help="execute one exact locally confirmed batch plan")
    _add_target(apply)
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--plan-id", required=True)
    apply.add_argument("--plan-hash", required=True)
    apply.add_argument("--confirmation-id", required=True)
    apply.add_argument("--confirmation-token", required=True)
    apply.add_argument("--actor-id", required=True)
    apply.add_argument("--occurred-at")

    inspect = actions.add_parser("inspect", help="inspect apply/undo eligibility and recovery journals")
    _add_target(inspect)
    inspect.add_argument("--recover", metavar="TRANSACTION_ID")
    inspect.add_argument("--actor-id")
    inspect.add_argument("--occurred-at")

    undo = actions.add_parser("undo", help="plan or execute exact-receipt append-only undo")
    _add_target(undo)
    undo.add_argument("--receipt-id")
    undo.add_argument("--receipt", type=Path)
    undo.add_argument("--undo-plan", type=Path)
    undo.add_argument("--actor-id", required=True)
    undo.add_argument("--issued-at")
    undo.add_argument("--expires-at")
    undo.add_argument("--confirm-local", action="store_true")
    undo.add_argument("--execute", action="store_true")
    undo.add_argument("--plan-id")
    undo.add_argument("--plan-hash")
    undo.add_argument("--confirmation-id")
    undo.add_argument("--confirmation-token")
    undo.add_argument("--occurred-at")

    receipt = actions.add_parser("receipt", help="load and validate one deterministic execution receipt")
    _add_target(receipt)
    receipt.add_argument("--receipt-id", required=True)
    return parser


def _read_json(path: Path, label: str) -> dict[str, Any]:
    candidate = Path(path).expanduser().absolute()
    try:
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise ValueError(f"{label} does not exist") from exc
    if not stat.S_ISREG(metadata.st_mode) or candidate.is_symlink() or metadata.st_size > _MAX_INPUT_BYTES:
        raise ValueError(f"{label} must be a bounded regular JSON file")
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def _source_links(values: list[str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for value in values:
        kind, separator, reference = value.partition("=")
        if not separator or not kind or not reference:
            raise ValueError("--source-link must use KIND=REF")
        result.append({"kind": kind, "ref": reference})
    return result


def _mapping(values: list[str], label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if not separator or not key or not item or key in result:
            raise ValueError(f"{label} must use unique KEY=VALUE entries")
        result[key] = item
    return result


def _failure(command: str, json_output: bool, exc: ValueError) -> int:
    code = "workstream_relation_recovery_required" if isinstance(exc, RecoveryRequiredError) else "workstream_relation_operation_failed"
    if json_output:
        emit(response(command, status="error", exit_code=JsonExitCode.OPERATION_FAILED, errors=[issue(code, str(exc))]))
    else:
        print(f"ERROR: {exc}", file=sys.stderr)
    return int(JsonExitCode.OPERATION_FAILED)


def _emit_result(command: str, data: Mapping[str, Any], json_output: bool, *, exit_code: JsonExitCode = JsonExitCode.OK, warning: str | None = None) -> int:
    if json_output:
        warnings = [] if warning is None else [issue("workstream_relation_unknown_or_blocked", warning)]
        emit(response(command, status="ok" if exit_code == JsonExitCode.OK else "warning", exit_code=exit_code, data=data, warnings=warnings))
    else:
        if command == "workstream-relation-discover":
            print(f"Proposed candidates: {len(data['candidates'])}")
            print(f"Unknown candidates: {len(data['unknown_candidates'])}")
        elif command == "workstream-relation-plan":
            print(f"Plan: {data['plan']['plan_id']}")
            print(f"Operations: {len(data['plan']['apply_plan']['operations'])}")
            print(f"Local confirmation: {'issued' if data.get('confirmation') else 'required'}")
        elif command == "workstream-relation-apply":
            print(f"Apply receipt: {data['receipt_id']}")
            print(f"Relations appended: {len(data['w7a_apply_receipt']['relation_events'])}")
        elif command == "workstream-relation-inspect":
            inspection = data.get("inspection", data)
            print(f"Graph status: {inspection['graph_status']}")
            print(f"Recovery required: {len(inspection['pending_recovery_transaction_ids'])}")
        elif command == "workstream-relation-undo":
            print(f"Undo plan: {data['plan']['plan_id']}" if "plan" in data else f"Undo receipt: {data['receipt_id']}")
        elif command == "workstream-relation-receipt":
            print(f"Receipt: {data['receipt_id']}")
            print(f"Operation: {data['operation']}")
        if warning:
            print(f"WARNING: {warning}", file=sys.stderr)
    return int(exit_code)


def _legacy_graph(arguments: argparse.Namespace) -> int:
    command = "workstream-relation-graph" if arguments.action == "graph" else "workstream-succession-plan"
    try:
        graph = load_relation_graph(arguments.target, include_legacy=not arguments.no_legacy)
        data = graph if arguments.action == "graph" else build_succession_plan(graph)
    except ValueError as exc:
        return _failure(command, arguments.json_output, exc)
    valid = graph["validation"]["valid"]
    exit_code = JsonExitCode.OK if valid else JsonExitCode.COMPATIBILITY_FAILED
    if arguments.json_output:
        emit(response(command, status="ok" if valid else "warning", exit_code=exit_code, data=data, warnings=[] if valid else [issue("relation_graph_invalid", "relation graph failed structural validation")]))
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


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.action in {"graph", "succession-plan"}:
        return _legacy_graph(arguments)
    if arguments.action == "propose":
        command = "workstream-relation-propose"
        ancestry = arguments.ancestry_status or ("unknown" if arguments.relation_type == "derived_from" else "not-applicable")
        dependency = arguments.dependency_status or ("unknown" if arguments.relation_type == "depends_on" else "not-applicable")
        ownership = arguments.ownership_transfer_status or ("unknown" if arguments.relation_type == "absorbs" else "not-applicable")
        evidence = default_relation_evidence(
            status="unknown", source_head_oid=arguments.source_head_oid,
            target_head_oid=arguments.target_head_oid, task_base_oid=arguments.task_base_oid,
            ownership_transfer_oid=arguments.ownership_transfer_oid,
            source_head_status=arguments.source_head_status, target_head_status=arguments.target_head_status,
            scope_status=arguments.scope_status, ancestry_status=ancestry,
            dependency_status=dependency, ownership_transfer_status=ownership,
            target_unique_commits_after_base=arguments.target_unique_commits_after_base,
        )
        try:
            data = append_proposed_relation(
                arguments.target, relation_id=arguments.relation_id,
                relation_type=arguments.relation_type, source_workstream_id=arguments.source_workstream_id,
                target_workstream_id=arguments.target_workstream_id, reason=arguments.reason,
                actor_id=arguments.actor_id, recorded_at=arguments.recorded_at, evidence=evidence,
                source_links=_source_links(arguments.source_link),
            )
        except ValueError as exc:
            return _failure(command, arguments.json_output, exc)
        if arguments.json_output:
            emit(response(command, status="ok", exit_code=JsonExitCode.OK, data=data))
        else:
            print(f"Proposed relation: {data['record']['relation_id']}")
            print(f"Edge: {data['record']['source_workstream_id']} -> {data['record']['target_workstream_id']}")
            print("Storage: git-common-private append-only")
        return int(JsonExitCode.OK)

    command = f"workstream-relation-{arguments.action}"
    try:
        if arguments.action == "discover":
            spec = {} if arguments.spec is None else _read_json(arguments.spec, "discovery spec")
            if set(spec) - {"explicit_relations", "similarity_hints"}:
                raise ValueError("discovery spec contains unsupported fields")
            data = discover_execution_candidates(
                arguments.target, explicit_relations=spec.get("explicit_relations", []),
                similarity_hints=spec.get("similarity_hints", []), recorded_at=arguments.recorded_at,
            )
            unknown = bool(data["unknown_candidates"] or data["rejected_hints"])
            return _emit_result(command, data, arguments.json_output, exit_code=JsonExitCode.COMPATIBILITY_FAILED if unknown else JsonExitCode.OK, warning="Unknown relation evidence remains" if unknown else None)
        if arguments.action == "plan":
            discovery = _read_json(arguments.discovery, "execution discovery")
            plan = build_execution_plan(
                arguments.target, discovery, target_lifecycles=_mapping(arguments.lifecycle, "--lifecycle"),
                actor_id=arguments.actor_id, issued_at=arguments.issued_at, expires_at=arguments.expires_at,
            )
            result: dict[str, Any] = {"plan": plan}
            if arguments.confirm_local:
                result["confirmation"] = issue_local_confirmation(arguments.target, plan, actor_id=arguments.actor_id)
            return _emit_result(command, result, arguments.json_output)
        if arguments.action == "apply":
            receipt = execute_apply_plan(
                arguments.target, _read_json(arguments.plan, "execution plan"),
                plan_id=arguments.plan_id, plan_hash=arguments.plan_hash,
                confirmation_id=arguments.confirmation_id, confirmation_token=arguments.confirmation_token,
                actor_id=arguments.actor_id, occurred_at=arguments.occurred_at,
            )
            return _emit_result(command, receipt, arguments.json_output)
        if arguments.action == "inspect":
            if arguments.recover:
                if not arguments.actor_id:
                    raise ValueError("--recover requires --actor-id")
                recovered = recover_transaction(arguments.target, arguments.recover, actor_id=arguments.actor_id, occurred_at=arguments.occurred_at)
                return _emit_result(command, {"recovery": recovered, "inspection": inspect_execution_state(arguments.target)}, arguments.json_output)
            data = inspect_execution_state(arguments.target)
            blocked = bool(data["pending_recovery_transaction_ids"])
            return _emit_result(command, data, arguments.json_output, exit_code=JsonExitCode.COMPATIBILITY_FAILED if blocked else JsonExitCode.OK, warning="transaction recovery required" if blocked else None)
        if arguments.action == "receipt":
            return _emit_result(command, load_execution_receipt(arguments.target, arguments.receipt_id), arguments.json_output)
        if arguments.action == "undo":
            if arguments.execute:
                if not arguments.undo_plan or not all((arguments.plan_id, arguments.plan_hash, arguments.confirmation_id, arguments.confirmation_token)):
                    raise ValueError("undo --execute requires exact plan file, ID/hash, confirmation ID/token")
                data = execute_undo_plan(
                    arguments.target, _read_json(arguments.undo_plan, "undo execution plan"),
                    plan_id=arguments.plan_id, plan_hash=arguments.plan_hash,
                    confirmation_id=arguments.confirmation_id, confirmation_token=arguments.confirmation_token,
                    actor_id=arguments.actor_id, occurred_at=arguments.occurred_at,
                )
                return _emit_result(command, data, arguments.json_output)
            if bool(arguments.receipt_id) == bool(arguments.receipt):
                raise ValueError("undo planning requires exactly one of --receipt-id or --receipt")
            receipt = load_execution_receipt(arguments.target, arguments.receipt_id) if arguments.receipt_id else _read_json(arguments.receipt, "apply receipt")
            plan = build_execution_undo_plan(
                arguments.target, receipt, actor_id=arguments.actor_id,
                issued_at=arguments.issued_at, expires_at=arguments.expires_at,
            )
            result = {"plan": plan}
            if arguments.confirm_local:
                result["confirmation"] = issue_local_undo_confirmation(arguments.target, plan, actor_id=arguments.actor_id)
            return _emit_result(command, result, arguments.json_output)
    except ValueError as exc:
        return _failure(command, arguments.json_output, exc)
    raise AssertionError("unreachable relation action")


if __name__ == "__main__":
    raise SystemExit(main())
