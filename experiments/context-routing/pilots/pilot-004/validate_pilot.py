#!/usr/bin/env python3
"""Validate a prepared or completed Project Orrery pilot-004 output root.

This validator independently checks repository artifacts, hashes, diffs, and
commands. Agent receipts remain self-report and are validated only for internal
consistency; they are never upgraded to Harness access evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


FIXED_CHAIN = [
    "README.md",
    "skills/project-orrery/SKILL.md",
    "skills/project-orrery/references/architecture.md",
    "skills/project-orrery/references/migration-contract.md",
    "skills/project-orrery/assets/project-template/AGENTS.md",
    "skills/project-orrery/scripts/install_project_orrery.py",
    "skills/project-orrery/scripts/validate_installation.py",
]
EVENT_TYPES = {"enumerate", "search", "content_read", "scope_expand", "write", "command", "test"}
RECEIPT_KEYS = {
    "schema_version",
    "pilot_id",
    "prompt_revision",
    "task_id",
    "variant",
    "external_context_preflight",
    "agent_started_at",
    "agent_ended_at",
    "prewrite",
    "events",
    "operator_questions",
    "validation",
    "uncertainty",
    "evidence_note",
}
MANIFEST_KEYS = {
    "task_classification",
    "retrieval_strategy",
    "initial_content_paths",
    "expected_product_writes",
    "expected_validation",
    "expansion_conditions",
    "content_file_budget",
}
EVENT_KEYS = {
    "sequence",
    "event_type",
    "target_scope",
    "target",
    "reason_code",
    "content_extent",
    "range_or_query",
    "declared_before_access",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _nul_paths(value: str) -> set[str]:
    return {
        item.replace("\\", "/")
        for item in value.split("\0")
        if item
    }


def collect_product_changes(repository: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Independently collect tracked and untracked product changes."""
    tracked_result = git(repository, "diff", "--name-only", "-z", "HEAD", "--")
    if tracked_result.returncode != 0:
        return None, f"git diff failed: {tracked_result.stdout}{tracked_result.stderr}"
    untracked_result = git(repository, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked_result.returncode != 0:
        return None, f"git ls-files failed: {untracked_result.stdout}{untracked_result.stderr}"
    head_result = git(repository, "rev-parse", "HEAD")
    if head_result.returncode != 0:
        return None, f"git rev-parse failed: {head_result.stdout}{head_result.stderr}"

    tracked = _nul_paths(tracked_result.stdout)
    untracked = _nul_paths(untracked_result.stdout)
    entries: list[dict[str, Any]] = []
    for relative in sorted(tracked | untracked):
        path = repository / Path(relative)
        exists = path.is_file()
        entries.append(
            {
                "path": relative,
                "kind": "untracked" if relative in untracked else "tracked",
                "exists": exists,
                "bytes": path.stat().st_size if exists else None,
                "sha256": sha256(path) if exists else None,
            }
        )
    return (
        {
            "schema_version": 1,
            "observed_by": "harness",
            "repository_head": head_result.stdout.strip(),
            "entries": entries,
        },
        None,
    )


def command_text(command: list[str]) -> str:
    return " ".join(str(part) for part in command)


def safe_relative(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("/"):
        return False
    path = PurePosixPath(normalized)
    return ".." not in path.parts and "." not in path.parts


def parse_time(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a timezone-aware ISO 8601 string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} is not valid ISO 8601")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed


def require_exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        errors.append(f"{label} keys differ; missing={missing}, extra={extra}")
        return False
    return True


def validate_string_list(value: Any, label: str, errors: list[str], *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    if nonempty and not value:
        errors.append(f"{label} must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{label} must contain only non-empty strings")
        return []
    return value


def validate_context_manifest(
    context: Any,
    variant: str,
    run: dict[str, Any],
    errors: list[str],
) -> set[str]:
    label = f"{run['run_key']}: prewrite.context_manifest"
    if not require_exact_keys(context, MANIFEST_KEYS, label, errors):
        return set()

    if not isinstance(context["task_classification"], str) or not context["task_classification"].strip():
        errors.append(f"{label}.task_classification must be non-empty")
    expected_writes = validate_string_list(
        context["expected_product_writes"],
        f"{label}.expected_product_writes",
        errors,
        nonempty=True,
    )
    if expected_writes and set(expected_writes) != set(run["expected_product_write_paths"]):
        errors.append(f"{label}.expected_product_writes does not match the Prompt contract")
    expected_validation = validate_string_list(
        context["expected_validation"],
        f"{label}.expected_validation",
        errors,
        nonempty=True,
    )
    contract_validation = [command_text(list(command)) for command in run["validation_commands"]]
    if expected_validation and expected_validation != contract_validation:
        errors.append(f"{label}.expected_validation does not match the Prompt contract")
    validate_string_list(
        context["expansion_conditions"],
        f"{label}.expansion_conditions",
        errors,
        nonempty=True,
    )

    initial_entries = context["initial_content_paths"]
    if not isinstance(initial_entries, list):
        errors.append(f"{label}.initial_content_paths must be an array")
        initial_entries = []
    initial_paths: list[str] = []
    for index, entry in enumerate(initial_entries):
        entry_label = f"{label}.initial_content_paths[{index}]"
        if not isinstance(entry, dict) or set(entry) != {"path", "reason"}:
            errors.append(f"{entry_label} must contain only path and reason")
            continue
        if not safe_relative(entry["path"]):
            errors.append(f"{entry_label}.path must be repository-relative")
        elif not isinstance(entry["reason"], str) or not entry["reason"].strip():
            errors.append(f"{entry_label}.reason must be non-empty")
        else:
            initial_paths.append(entry["path"])
    if len(initial_paths) != len(set(initial_paths)):
        errors.append(f"{label}.initial_content_paths contains duplicates")

    if variant == "B":
        if context["retrieval_strategy"] is not None or context["content_file_budget"] is not None:
            errors.append(f"{label} must use null strategy and budget for variant B")
    else:
        if context["retrieval_strategy"] not in {"single_file", "bounded_multi_file", "dependency_expansion"}:
            errors.append(f"{label}.retrieval_strategy is invalid for variant H")
        if context["content_file_budget"] != 2:
            errors.append(f"{label}.content_file_budget must equal 2 for variant H")
        if len(initial_paths) > 2:
            errors.append(f"{label} exceeds the two-file initial content budget")
    return set(initial_paths)


def validate_receipt(
    receipt: Any,
    run: dict[str, Any],
    manifest: dict[str, Any],
    operator_run: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    run_key = run["run_key"]
    if not require_exact_keys(receipt, RECEIPT_KEYS, f"{run_key}: receipt", errors):
        return errors
    expected_values = {
        "schema_version": 1,
        "pilot_id": manifest["pilot_id"],
        "prompt_revision": manifest["prompt_revision"],
        "task_id": run["task_id"],
        "variant": run["variant"],
        "external_context_preflight": "clean",
        "evidence_note": "Agent self-report; not an independent Harness audit",
    }
    for key, expected in expected_values.items():
        if receipt[key] != expected:
            errors.append(f"{run_key}: receipt.{key} must equal {expected!r}")
    started = parse_time(receipt["agent_started_at"], f"{run_key}: agent_started_at", errors)
    ended = parse_time(receipt["agent_ended_at"], f"{run_key}: agent_ended_at", errors)
    if started is not None and ended is not None and ended < started:
        errors.append(f"{run_key}: agent_ended_at precedes agent_started_at")

    prewrite = receipt["prewrite"]
    if not isinstance(prewrite, dict) or set(prewrite) != {"context_manifest", "selected_evidence"}:
        errors.append(f"{run_key}: prewrite must contain context_manifest and selected_evidence")
        initial_paths: set[str] = set()
    else:
        initial_paths = validate_context_manifest(prewrite["context_manifest"], run["variant"], run, errors)
        selected = prewrite["selected_evidence"]
        if run["variant"] == "H":
            if not isinstance(selected, list) or not selected:
                errors.append(f"{run_key}: variant H requires non-empty selected_evidence")
            else:
                for index, item in enumerate(selected):
                    if not isinstance(item, dict) or set(item) != {"path", "scope", "fact"}:
                        errors.append(f"{run_key}: selected_evidence[{index}] must contain path, scope, fact")
                        continue
                    if not safe_relative(item["path"]):
                        errors.append(f"{run_key}: selected_evidence[{index}].path is unsafe")
                    for field in ("scope", "fact"):
                        if not isinstance(item[field], str) or not item[field].strip():
                            errors.append(f"{run_key}: selected_evidence[{index}].{field} must be non-empty")
        elif selected is not None:
            if not isinstance(selected, list):
                errors.append(f"{run_key}: selected_evidence must be null or an array")

    events = receipt["events"]
    if not isinstance(events, list) or not events:
        errors.append(f"{run_key}: events must be a non-empty array")
        events = []
    content_reads: list[str] = []
    expansions: set[str] = set()
    write_targets: set[str] = set()
    for index, event in enumerate(events):
        label = f"{run_key}: events[{index}]"
        if not require_exact_keys(event, EVENT_KEYS, label, errors):
            continue
        if event["sequence"] != index + 1:
            errors.append(f"{label}.sequence must be contiguous and equal {index + 1}")
        if event["event_type"] not in EVENT_TYPES:
            errors.append(f"{label}.event_type is unknown")
        if event["target_scope"] not in {"repository", "query", "command"}:
            errors.append(f"{label}.target_scope is unknown")
        if not isinstance(event["target"], str) or not event["target"].strip():
            errors.append(f"{label}.target must be non-empty")
            continue
        if event["target_scope"] == "repository" and not safe_relative(event["target"]):
            errors.append(f"{label}.target must be repository-relative")
        if event["event_type"] == "scope_expand":
            if event["target_scope"] != "repository" or event["declared_before_access"] is not True:
                errors.append(f"{label} must be a repository expansion declared before access")
            else:
                expansions.add(event["target"])
        elif event["event_type"] == "content_read":
            if event["target_scope"] != "repository":
                errors.append(f"{label}: content reads must stay in the repository")
            if event["content_extent"] not in {"full", "partial"}:
                errors.append(f"{label}.content_extent must be full or partial")
            if event["content_extent"] == "partial" and (
                not isinstance(event["range_or_query"], str) or not event["range_or_query"].strip()
            ):
                errors.append(f"{label}: partial reads require range_or_query")
            if run["variant"] in {"B", "H"}:
                if event["target"] not in initial_paths and event["target"] not in expansions:
                    errors.append(f"{label}: read was outside the Manifest without prior expansion")
                if event["declared_before_access"] is not True:
                    errors.append(f"{label}: B/H read must be declared before access")
            content_reads.append(event["target"])
        elif event["event_type"] == "write" and event["target_scope"] == "repository":
            write_targets.add(event["target"])

    expected_write_targets = set(run["expected_product_write_paths"])
    if not (expected_write_targets & write_targets):
        errors.append(f"{run_key}: receipt does not report any contracted product write")
    unexpected_reported_writes = write_targets - expected_write_targets - {manifest["agent_receipt"]["path"]}
    if unexpected_reported_writes:
        errors.append(f"{run_key}: receipt reports writes outside the contract: {sorted(unexpected_reported_writes)}")
    if manifest["agent_receipt"]["path"] not in write_targets:
        errors.append(f"{run_key}: receipt does not report its own receipt write")

    questions = receipt["operator_questions"]
    if not isinstance(questions, list):
        errors.append(f"{run_key}: operator_questions must be an array")
    else:
        for index, question in enumerate(questions):
            if not isinstance(question, dict) or set(question) != {"question", "answer"}:
                errors.append(f"{run_key}: operator_questions[{index}] must contain question and answer")
    if isinstance(questions, list) and len(questions) != len(operator_run.get("interventions", [])):
        errors.append(f"{run_key}: Agent and operator intervention counts differ")

    validations = validate_string_list(receipt["validation"], f"{run_key}: validation", errors, nonempty=True)
    for command in run["validation_commands"]:
        text = command_text(list(command))
        if validations and not any(text in item for item in validations):
            errors.append(f"{run_key}: validation receipt omits command: {text}")
    validate_string_list(receipt["uncertainty"], f"{run_key}: uncertainty", errors)
    return errors


def validate_pilot(
    output_root: Path,
    *,
    prepared_only: bool,
    skip_security_acceptance: bool = False,
) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    operator = output_root / "_operator"
    manifest_path = operator / "pilot-manifest.json"
    profile_path = operator / "execution-profile.json"
    log_path = operator / "operator-run-log.json"
    schema_path = operator / "agent-receipt.schema.json"
    security_path = operator / "holdout-acceptance.py"
    for path in (manifest_path, profile_path, log_path, schema_path, security_path):
        if not path.is_file():
            errors.append(f"missing operator artifact: {path.name}")
    if errors:
        return errors, warnings, 0

    try:
        manifest = load_json(manifest_path)
        profile = load_json(profile_path)
        operator_log = load_json(log_path)
        load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load operator artifacts: {exc}")
        return errors, warnings, 0

    if manifest.get("pilot_id") != "pilot-004" or manifest.get("prompt_revision") != "po-context-routing-pilot-004-v1":
        errors.append("unexpected pilot identity or prompt revision")
    if manifest.get("external_context_policy") != "repository_only":
        errors.append("pilot must use repository_only external context")
    profile_sha = sha256(profile_path)
    if profile_sha != manifest.get("execution_profile", {}).get("sha256"):
        errors.append("execution-profile.json checksum does not match manifest")
    if profile_sha != operator_log.get("execution_profile_sha256"):
        errors.append("operator run log references a different execution profile")
    if sha256(schema_path) != manifest.get("agent_receipt", {}).get("schema_sha256"):
        errors.append("Agent receipt schema checksum does not match manifest")
    security_manifest = manifest.get("holdout_acceptance", {})
    if security_manifest.get("path") != "holdout-acceptance.py":
        errors.append("holdout acceptance path is missing from the manifest")
    if security_manifest.get("task_ids") != ["PO-CR-012", "PO-CR-013", "PO-CR-014"]:
        errors.append("holdout acceptance task set differs from the apparatus contract")
    if sha256(security_path) != security_manifest.get("sha256"):
        errors.append("holdout-acceptance.py checksum does not match manifest")
    for field in ("model", "reasoning_effort", "permission_profile", "harness", "network_policy"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            errors.append(f"execution profile is missing {field}")

    selection = manifest.get("selection")
    selected_task_ids = selection.get("task_ids") if isinstance(selection, dict) else None
    selected_variants = selection.get("variants") if isinstance(selection, dict) else None
    if (
        not isinstance(selected_task_ids, list)
        or not selected_task_ids
        or len(selected_task_ids) != len(set(selected_task_ids))
        or not all(task_id in {"PO-CR-012", "PO-CR-013", "PO-CR-014"} for task_id in selected_task_ids)
    ):
        errors.append("manifest selection contains invalid task IDs")
        selected_task_ids = []
    if (
        not isinstance(selected_variants, list)
        or not selected_variants
        or len(selected_variants) != len(set(selected_variants))
        or not all(variant in {"B", "H"} for variant in selected_variants)
    ):
        errors.append("manifest selection contains invalid variants")
        selected_variants = []
    expected_run_keys = {
        f"{task_id}-{variant}"
        for task_id in selected_task_ids
        for variant in selected_variants
    }
    runs = manifest.get("runs")
    if not isinstance(runs, list) or len(runs) != len(expected_run_keys):
        errors.append("manifest run count does not match its explicit selection")
        runs = []
    run_keys = [run.get("run_key") for run in runs if isinstance(run, dict)]
    if set(run_keys) != expected_run_keys:
        errors.append("manifest run keys do not form the selected task/variant matrix")
    if isinstance(selection, dict) and selection.get("run_count") != len(expected_run_keys):
        errors.append("manifest selection run_count is inconsistent")
    if profile.get("selected_task_ids") != selected_task_ids:
        errors.append("execution profile task selection differs from manifest")
    if profile.get("selected_variants") != selected_variants:
        errors.append("execution profile variant selection differs from manifest")
    if len(run_keys) != len(set(run_keys)):
        errors.append("manifest contains duplicate run keys")
    log_runs = operator_log.get("runs") if isinstance(operator_log.get("runs"), list) else []
    log_by_key = {run.get("run_key"): run for run in log_runs if isinstance(run, dict)}
    if set(log_by_key) != set(run_keys):
        errors.append("operator run log does not match manifest run keys")

    completed_count = 0
    for run in runs:
        run_key = run.get("run_key", "<unknown>")
        repository = Path(str(run.get("repository_path", "")))
        prompt_path = Path(str(run.get("prompt_path", "")))
        if not repository.is_dir():
            errors.append(f"{run_key}: repository is missing")
            continue
        if (repository / "experiments" / "context-routing" / "pilots" / "pilot-004" / "operator").exists():
            errors.append(f"{run_key}: operator-only Oracle leaked into the target repository")
        if not prompt_path.is_file() or sha256(prompt_path) != run.get("prompt_sha256"):
            errors.append(f"{run_key}: Prompt is missing or checksum-mismatched")
        overlay = repository / manifest["harness_overlay"]["path"]
        if not overlay.is_file() or sha256(overlay) != manifest["harness_overlay"]["sha256"]:
            errors.append(f"{run_key}: Harness overlay is missing or checksum-mismatched")
        head = git(repository, "rev-parse", "HEAD")
        if head.returncode != 0 or head.stdout.strip() != run.get("repository_commit"):
            errors.append(f"{run_key}: repository HEAD differs from manifest")
        remotes = git(repository, "remote")
        if remotes.returncode != 0 or remotes.stdout.strip():
            errors.append(f"{run_key}: isolated repository must not have remotes")
        exclude_path = repository / ".git" / "info" / "exclude"
        if not exclude_path.is_file() or manifest["agent_receipt"]["path"] not in exclude_path.read_text(encoding="utf-8"):
            errors.append(f"{run_key}: Agent receipt is not locally excluded from product diff")

        if prepared_only:
            status = git(repository, "status", "--porcelain")
            if status.returncode != 0 or status.stdout.strip():
                errors.append(f"{run_key}: prepared repository is not clean")
            history = git(repository, "rev-list", "--count", "HEAD")
            if history.returncode != 0 or history.stdout.strip() != "1":
                errors.append(f"{run_key}: prepared repository must contain exactly one commit")
            continue

        operator_run = log_by_key.get(run_key, {})
        status_value = operator_run.get("status")
        if status_value == "contaminated":
            warnings.append(f"{run_key}: contaminated and excluded from comparison")
            continue
        if status_value != "completed":
            errors.append(f"{run_key}: operator status is not completed")
            continue
        completed_count += 1
        if parse_time(operator_run.get("operator_started_at"), f"{run_key}: operator_started_at", errors) is None:
            pass
        if parse_time(operator_run.get("operator_ended_at"), f"{run_key}: operator_ended_at", errors) is None:
            pass

        receipt_path = repository / manifest["agent_receipt"]["path"]
        if not receipt_path.is_file():
            errors.append(f"{run_key}: Agent receipt is missing")
        else:
            try:
                receipt = load_json(receipt_path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{run_key}: cannot load Agent receipt: {exc}")
            else:
                errors.extend(validate_receipt(receipt, run, manifest, operator_run))

        product_changes, collection_error = collect_product_changes(repository)
        if collection_error is not None or product_changes is None:
            errors.append(f"{run_key}: product change collection failed: {collection_error}")
        else:
            changed_paths = {entry["path"] for entry in product_changes["entries"]}
            allowed = set(run["expected_product_write_paths"])
            if not changed_paths:
                errors.append(f"{run_key}: no product changes were produced")
            unexpected = changed_paths - allowed
            if unexpected:
                errors.append(f"{run_key}: changed paths outside contract: {sorted(unexpected)}")

            changes_path = operator / "runs" / run_key / "product-changes.json"
            if changes_path.is_file():
                try:
                    recorded_changes = load_json(changes_path)
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f"{run_key}: cannot load Harness product changes: {exc}")
                else:
                    if recorded_changes != product_changes:
                        errors.append(f"{run_key}: Harness product change artifact no longer matches the repository")
                runner_result_path = operator / "runs" / run_key / "runner-result.json"
                if runner_result_path.is_file():
                    try:
                        runner_result = load_json(runner_result_path)
                    except (OSError, json.JSONDecodeError) as exc:
                        errors.append(f"{run_key}: cannot load runner result: {exc}")
                    else:
                        if runner_result.get("product_changes_sha256") != sha256(changes_path):
                            errors.append(f"{run_key}: runner result does not authenticate product-changes.json")
            elif (operator / "automation-profile.json").is_file():
                errors.append(f"{run_key}: automated run is missing Harness product-changes.json")
            else:
                warnings.append(
                    f"{run_key}: manual run has no frozen product-changes.json; validator used a live recomputation"
                )
        diff_check = git(repository, "diff", "--check")
        if diff_check.returncode != 0:
            errors.append(f"{run_key}: git diff --check failed: {diff_check.stdout}{diff_check.stderr}")

        for command in run["validation_commands"]:
            result = subprocess.run(
                [str(part) for part in command],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                errors.append(
                    f"{run_key}: validation failed ({command_text(list(command))}): "
                    f"{result.stdout}{result.stderr}"
                )

        if run.get("task_id") in security_manifest.get("task_ids", []):
            if skip_security_acceptance:
                warnings.append(f"{run_key}: operator security acceptance skipped by test-only mode")
            else:
                security_result = subprocess.run(
                    [
                        sys.executable,
                        str(security_path),
                        "--repository",
                        str(repository),
                        "--task-id",
                        str(run["task_id"]),
                    ],
                    cwd=repository,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                )
                if security_result.returncode != 0:
                    errors.append(
                        f"{run_key}: operator security acceptance failed: "
                        f"{security_result.stdout}{security_result.stderr}"
                    )

    if not prepared_only:
        if operator_log.get("sealed_at") is None or not isinstance(operator_log.get("operator_attestation"), dict):
            errors.append("operator run log is not sealed with an attestation")
        elif operator_log["operator_attestation"].get("same_execution_profile_used") is not True:
            errors.append("operator did not attest to a shared execution profile")
        if completed_count == 0:
            errors.append("no completed runs are available")
    return errors, warnings, completed_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--prepared-only", action="store_true")
    parser.add_argument(
        "--skip-security-acceptance",
        action="store_true",
        help="Test fixtures only; rejected unless automation-profile uses mock-codex.",
    )
    args = parser.parse_args(argv)
    output_root = args.output_root.resolve()
    if args.skip_security_acceptance:
        automation_profile_path = output_root / "_operator" / "automation-profile.json"
        try:
            automation_profile = load_json(automation_profile_path)
        except (OSError, json.JSONDecodeError):
            print("ERROR: security acceptance can only be skipped by a recorded mock-codex test run", file=sys.stderr)
            return 1
        if not str(automation_profile.get("agent_version", "")).startswith("mock-codex"):
            print("ERROR: security acceptance skip is restricted to mock-codex test fixtures", file=sys.stderr)
            return 1
    errors, warnings, completed = validate_pilot(
        output_root,
        prepared_only=args.prepared_only,
        skip_security_acceptance=args.skip_security_acceptance,
    )
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.prepared_only:
        print(f"pilot-004 prepared apparatus OK: {completed or len(load_json(output_root / '_operator' / 'pilot-manifest.json')['runs'])} isolated runs")
    else:
        print(f"pilot-004 completed artifacts OK: {completed} comparable runs")
        print("Agent access events remain self-report; no Harness read audit is claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
