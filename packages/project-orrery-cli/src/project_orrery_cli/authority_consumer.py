"""Read-only A3 managed Authority consumer inspect/readiness CLI."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from project_orrery_core.authority_consumer import (
    MANAGED_COLLECTOR_VERSION,
    MANAGED_EVALUATOR_VERSION,
    MANAGED_PROJECTION_VERSION,
    evaluate_managed_authority_consumer,
)

from .protocol import JsonExitCode, emit, issue, response


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _snapshot_hash(snapshot: object) -> str | None:
    prefix = "cli-authority-observations:sha256:"
    if not isinstance(snapshot, str) or not snapshot.startswith(prefix):
        return None
    digest = snapshot.removeprefix(prefix)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        return None
    return "sha256:" + digest


def _read_manifest(root: Path) -> dict[str, Any]:
    path = root / ".project-orrery.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("project manifest must contain a JSON object")
    return value


def inspect_managed_consumer(
    root: Path,
    *,
    requested_selection: str,
    selection_authority: str,
    fact_scope: str,
    evidence_visibility: Sequence[str],
) -> dict[str, Any]:
    """Collect exact internal inputs but return only the bounded A3 contract."""

    from project_orrery_cli.authority_observations import (
        AUTHORITY_OBSERVATION_CONTRACT,
        AuthorityObservationParseError,
        authority_observation_snapshot,
        build_cli_authority_contract,
    )
    from project_orrery_core.authority import AuthorityEvaluationError, evaluate_authority
    from project_orrery_core.authority_compatibility import (
        AUTHORITY_MODEL_FIXTURE_IDS,
        judge_project_authority_model,
    )
    from project_orrery_observatory.authority_projection import (
        PROJECTION_SCHEMA,
        AuthorityProjectionError,
        build_authority_projection,
    )

    manifest = _read_manifest(root)
    capability = judge_project_authority_model(manifest)
    selected_version = capability.get("selected_version")
    evaluator_model_id = AUTHORITY_MODEL_FIXTURE_IDS.get(selected_version)
    repository_snapshot = "unavailable"
    source_expected: str | None = None
    source_observed: str | None = None
    reconciliation_expected: str | None = None
    reconciliation_observed: str | None = None
    health = {component: "unavailable" for component in ("collector", "evaluator", "projection")}
    render_status = "unavailable"
    stage = "collector"
    failure: dict[str, str] | None = None

    if capability.get("status") == "supported" and evaluator_model_id is not None:
        try:
            repository_snapshot = authority_observation_snapshot(root)
            source_expected = _snapshot_hash(repository_snapshot)
            bundle = build_cli_authority_contract(
                root,
                evaluator=evaluate_authority,
                authority_model_version=evaluator_model_id,
                fact_scope=fact_scope,
                evidence_visibility=evidence_visibility,
            )
            health["collector"] = "ready"
            health["evaluator"] = "ready"
            source_observed = _snapshot_hash(
                bundle.get("conformance_input", {}).get("repository_snapshot")
            )
            reconciliation_expected = _canonical_hash(bundle)
            stage = "projection"
            projection = build_authority_projection(
                bundle,
                authority_model_version=evaluator_model_id,
                repository_snapshot=repository_snapshot,
                fact_scope=fact_scope,
                evidence_visibility=evidence_visibility,
            )
            reconciliation_observed = projection.get("reconciliation", {}).get(
                "bundle_sha256"
            )
            health["projection"] = "ready"
            render_status = "complete"
        except Exception as error:
            if isinstance(error, AuthorityEvaluationError):
                health["collector"] = "ready"
                health["evaluator"] = "failed"
                stage = "evaluator"
            elif isinstance(error, AuthorityProjectionError):
                health["collector"] = "ready"
                health["evaluator"] = "ready"
                health["projection"] = "failed"
                stage = "projection"
            elif isinstance(error, AuthorityObservationParseError):
                health["collector"] = "failed"
                stage = "collector"
            else:
                health[stage] = "failed"
            render_status = "failed" if stage == "projection" else "unavailable"
            failure = {"type": type(error).__name__, "message": str(error)}

    contract = evaluate_managed_authority_consumer(
        requested_selection=requested_selection,
        selection_authority=selection_authority,
        authority_model_version=(
            selected_version if isinstance(selected_version, int) else None
        ),
        evaluator_model_id=evaluator_model_id,
        model_status=str(capability.get("status", "invalid")),
        repository_snapshot=repository_snapshot,
        fact_scope=fact_scope,
        evidence_visibility=evidence_visibility,
        expected_versions={
            "collector": MANAGED_COLLECTOR_VERSION,
            "evaluator": MANAGED_EVALUATOR_VERSION,
            "projection": MANAGED_PROJECTION_VERSION,
        },
        observed_versions={
            "collector": AUTHORITY_OBSERVATION_CONTRACT,
            "evaluator": MANAGED_EVALUATOR_VERSION,
            "projection": PROJECTION_SCHEMA,
        },
        component_health=health,
        source_hashes={"expected": source_expected, "observed": source_observed},
        reconciliation_hashes={
            "expected": reconciliation_expected,
            "observed": reconciliation_observed,
        },
        render_status=render_status,
        safety={
            "unknown_preserved": True,
            "local_only_preserved": True,
            "ai_non_escalation": True,
            "coordinator_cannot_select": True,
            "partial_claims_exposed": False,
        },
    )
    return {
        **contract,
        "inspection": {
            "writes_performed": False,
            "normalized_observations_exposed": False,
            "collection_failure": failure,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect the A3 managed Authority consumer contract"
    )
    actions = parser.add_subparsers(dest="action", required=True)
    for action in ("inspect", "readiness"):
        command = actions.add_parser(action)
        command.add_argument("--target", type=Path, default=Path("."))
        command.add_argument(
            "--fact-scope",
            default="unknown",
            choices=(
                "canonical",
                "candidate",
                "worktree",
                "local-only",
                "historical",
                "unknown",
            ),
        )
        command.add_argument(
            "--evidence-visibility",
            default="revision-content,human-or-agent-assertion",
            help="ordered, unique comma-separated evidence categories",
        )
        command.add_argument("--json", action="store_true", dest="json_output")
        if action == "readiness":
            command.add_argument(
                "--selection",
                required=True,
                choices=(
                    "legacy",
                    "shadow",
                    "candidate-projection",
                    "enabled",
                    "rollback",
                ),
            )
            command.add_argument(
                "--selection-authority", default="maintainer-explicit"
            )
    return parser


def _visibility(raw: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    if not values or len(values) != len(set(values)):
        raise ValueError("evidence visibility must be a non-empty unique CSV list")
    return values


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    command = f"authority-consumer-{arguments.action}"
    selection = "legacy" if arguments.action == "inspect" else arguments.selection
    authority = (
        "system-default"
        if arguments.action == "inspect"
        else arguments.selection_authority
    )
    try:
        data = inspect_managed_consumer(
            arguments.target,
            requested_selection=selection,
            selection_authority=authority,
            fact_scope=arguments.fact_scope,
            evidence_visibility=_visibility(arguments.evidence_visibility),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        if arguments.json_output:
            emit(
                response(
                    command,
                    status="error",
                    exit_code=JsonExitCode.OPERATION_FAILED,
                    errors=[issue("authority-consumer-inspection-failed", str(error))],
                )
            )
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return int(JsonExitCode.OPERATION_FAILED)

    requested = data["selection"]["requested"]
    effective = data["selection"]["effective"]
    accepted = arguments.action == "inspect" or requested == effective
    exit_code = JsonExitCode.OK if accepted else JsonExitCode.COMPATIBILITY_FAILED
    blockers = data["readiness"]["blockers"]
    if arguments.json_output:
        emit(
            response(
                command,
                status="ok" if accepted else "warning",
                exit_code=exit_code,
                data=data,
                warnings=(
                    issue(item["code"], item["detail"], component=item["component"])
                    for item in blockers
                ),
            )
        )
    else:
        print(f"Requested selection: {requested}")
        print(f"Effective selection: {effective}")
        print(f"Active consumer: {data['selection']['active_consumer']}")
        print(f"Managed readiness: {data['readiness']['status']}")
        print(f"Blockers: {len(blockers)}")
        print(f"Rollout plan: {data['rollout_plan']['plan_id']}")
        print(f"Rollback plan: {data['rollback_plan']['plan_id']}")
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
