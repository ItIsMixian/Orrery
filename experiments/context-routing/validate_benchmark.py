#!/usr/bin/env python3
"""Validate Project Orrery's context-routing research corpus and run records."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


TASK_ID_RE = re.compile(r"^PO-CR-[0-9]{3}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TASK_CATEGORIES = {
    "documentation",
    "local_code",
    "cross_module",
    "security",
    "release",
    "architecture",
    "testing",
    "ci",
}
RISK_LEVELS = {"low", "medium", "high"}
VARIANTS = {"A", "B", "C"}
EVENT_TYPES = {
    "enumerate",
    "search",
    "content_read",
    "write",
    "command",
    "test",
    "scope_expand",
}
EVIDENCE_ORIGINS = {"harness", "tool_wrapper", "manual", "agent"}
INDEPENDENT_ORIGINS = {"harness", "tool_wrapper"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _is_safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("/"):
        return False
    path = PurePosixPath(normalized)
    return ".." not in path.parts and "." not in path.parts


def _require_keys(value: Any, keys: Iterable[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    missing = [key for key in keys if key not in value]
    if missing:
        errors.append(f"{label} is missing: {', '.join(missing)}")
        return False
    return True


def _parse_datetime(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_none: bool = False,
) -> datetime | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be an ISO 8601 date-time string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be an ISO 8601 date-time string")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed


def _validate_string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    nonempty: bool = False,
    paths: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    if nonempty and not value:
        errors.append(f"{label} must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{label} must contain only non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label} contains duplicate values")
    if paths:
        for item in value:
            if not _is_safe_relative_path(item):
                errors.append(f"{label} contains unsafe path: {item!r}")
    return value


def validate_corpus(data: Any, repo_root: Path, *, check_git: bool = True) -> list[str]:
    errors: list[str] = []
    if not _require_keys(data, ("schema_version", "corpus_id", "description", "tasks"), "corpus", errors):
        return errors
    if data["schema_version"] != 1:
        errors.append("corpus.schema_version must equal 1")
    if not isinstance(data["corpus_id"], str) or not data["corpus_id"].strip():
        errors.append("corpus.corpus_id must be a non-empty string")
    if not isinstance(data["description"], str) or not data["description"].strip():
        errors.append("corpus.description must be a non-empty string")
    tasks = data["tasks"]
    if not isinstance(tasks, list) or not tasks:
        errors.append("corpus.tasks must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    diff_cache: dict[tuple[str, str], set[str]] = {}
    commit_cache: dict[str, bool] = {}
    path_cache: dict[tuple[str, str], bool] = {}

    def commit_exists(commit: str) -> bool:
        if commit not in commit_cache:
            commit_cache[commit] = _git(repo_root, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0
        return commit_cache[commit]

    def path_exists(commit: str, path: str) -> bool:
        key = (commit, path)
        if key not in path_cache:
            path_cache[key] = _git(repo_root, "cat-file", "-e", f"{commit}:{path}").returncode == 0
        return path_cache[key]

    for index, task in enumerate(tasks):
        label = f"tasks[{index}]"
        if not _require_keys(
            task,
            ("id", "title", "category", "risk", "prompt", "source", "oracle", "tags"),
            label,
            errors,
        ):
            continue
        task_id = task["id"]
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            errors.append(f"{label}.id must match PO-CR-NNN")
            task_id = label
        elif task_id in seen_ids:
            errors.append(f"duplicate task id: {task_id}")
        else:
            seen_ids.add(task_id)
        if not isinstance(task["title"], str) or not task["title"].strip():
            errors.append(f"{task_id}.title must be a non-empty string")
        if task["category"] not in TASK_CATEGORIES:
            errors.append(f"{task_id}.category is unknown: {task['category']!r}")
        if task["risk"] not in RISK_LEVELS:
            errors.append(f"{task_id}.risk is unknown: {task['risk']!r}")
        if not isinstance(task["prompt"], str) or not task["prompt"].strip():
            errors.append(f"{task_id}.prompt must be a non-empty string")
        _validate_string_list(task["tags"], f"{task_id}.tags", errors)

        source = task["source"]
        if not _require_keys(
            source,
            ("kind", "repository", "base_commit", "reference_commit", "prompt_provenance", "oracle_provenance"),
            f"{task_id}.source",
            errors,
        ):
            continue
        if source["kind"] != "git_history" or source["repository"] != "project-orrery":
            errors.append(f"{task_id}.source must identify Project Orrery Git history")
        if source["prompt_provenance"] != "reconstructed_from_commit":
            errors.append(f"{task_id}.source.prompt_provenance must disclose reconstruction")
        if source["oracle_provenance"] != "git_diff":
            errors.append(f"{task_id}.source.oracle_provenance must equal git_diff")
        base_commit = source["base_commit"]
        reference_commit = source["reference_commit"]
        for field_name, commit in (("base_commit", base_commit), ("reference_commit", reference_commit)):
            if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
                errors.append(f"{task_id}.source.{field_name} must be a full lowercase Git SHA")
            elif check_git and not commit_exists(commit):
                errors.append(f"{task_id}.source.{field_name} does not exist: {commit}")

        oracle = task["oracle"]
        if not _require_keys(
            oracle,
            ("reference_changed_paths", "curated_context_paths", "validation_commands", "acceptance_criteria"),
            f"{task_id}.oracle",
            errors,
        ):
            continue
        changed_paths = _validate_string_list(
            oracle["reference_changed_paths"],
            f"{task_id}.oracle.reference_changed_paths",
            errors,
            nonempty=True,
            paths=True,
        )
        context_paths = _validate_string_list(
            oracle["curated_context_paths"],
            f"{task_id}.oracle.curated_context_paths",
            errors,
            paths=True,
        )
        _validate_string_list(
            oracle["validation_commands"],
            f"{task_id}.oracle.validation_commands",
            errors,
        )
        _validate_string_list(
            oracle["acceptance_criteria"],
            f"{task_id}.oracle.acceptance_criteria",
            errors,
            nonempty=True,
        )

        if check_git and COMMIT_RE.fullmatch(str(base_commit)) and COMMIT_RE.fullmatch(str(reference_commit)):
            if commit_exists(base_commit) and commit_exists(reference_commit):
                diff_key = (base_commit, reference_commit)
                if diff_key not in diff_cache:
                    result = _git(repo_root, "diff", "--name-only", base_commit, reference_commit)
                    if result.returncode != 0:
                        errors.append(f"{task_id}: git diff failed: {result.stderr.strip()}")
                        diff_cache[diff_key] = set()
                    else:
                        diff_cache[diff_key] = {
                            line.strip().replace("\\", "/")
                            for line in result.stdout.splitlines()
                            if line.strip()
                        }
                missing_from_diff = set(changed_paths) - diff_cache[diff_key]
                if missing_from_diff:
                    errors.append(
                        f"{task_id}.oracle.reference_changed_paths not present in Git diff: "
                        + ", ".join(sorted(missing_from_diff))
                    )
                for context_path in context_paths:
                    if not path_exists(base_commit, context_path) and not path_exists(reference_commit, context_path):
                        errors.append(
                            f"{task_id}.oracle.curated_context_paths does not exist at base or reference commit: "
                            f"{context_path}"
                        )
    return errors


def validate_run_record(data: Any, task_ids: set[str]) -> list[str]:
    errors: list[str] = []
    required = (
        "schema_version",
        "run_id",
        "task_id",
        "variant",
        "repository_commit",
        "started_at",
        "ended_at",
        "execution",
        "events",
        "metrics",
        "artifacts",
        "outcome",
        "evaluation",
    )
    if not _require_keys(data, required, "run", errors):
        return errors
    if data["schema_version"] != 1:
        errors.append("run.schema_version must equal 1")
    if not isinstance(data["run_id"], str) or not data["run_id"].strip():
        errors.append("run.run_id must be a non-empty string")
    if data["task_id"] not in task_ids:
        errors.append(f"run.task_id is not in the corpus: {data['task_id']!r}")
    if data["variant"] not in VARIANTS:
        errors.append(f"run.variant is unknown: {data['variant']!r}")
    if not isinstance(data["repository_commit"], str) or not COMMIT_RE.fullmatch(data["repository_commit"]):
        errors.append("run.repository_commit must be a full lowercase Git SHA")
    started_at = _parse_datetime(data["started_at"], "run.started_at", errors, allow_none=True)
    ended_at = _parse_datetime(data["ended_at"], "run.ended_at", errors, allow_none=True)
    if started_at is not None and ended_at is not None and ended_at < started_at:
        errors.append("run.ended_at must not be earlier than run.started_at")

    execution_keys = (
        "model",
        "harness",
        "toolchain",
        "permission_profile",
        "prompt_revision",
        "prompt_sha256",
        "external_context_policy",
        "operator_interventions",
    )
    if _require_keys(data["execution"], execution_keys, "run.execution", errors):
        for key in ("model", "harness", "toolchain", "permission_profile", "prompt_revision"):
            value = data["execution"][key]
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"run.execution.{key} must be null or a non-empty string")
        prompt_sha256 = data["execution"]["prompt_sha256"]
        if prompt_sha256 is not None and (not isinstance(prompt_sha256, str) or not SHA256_RE.fullmatch(prompt_sha256)):
            errors.append("run.execution.prompt_sha256 must be null or a 64-character lowercase SHA-256")
        external_context_policy = data["execution"]["external_context_policy"]
        if external_context_policy not in {"repository_only", "frozen_identical", "uncontrolled", None}:
            errors.append("run.execution.external_context_policy is unknown")
        _validate_string_list(
            data["execution"]["operator_interventions"],
            "run.execution.operator_interventions",
            errors,
        )
    events = data["events"]
    if not isinstance(events, list):
        errors.append("run.events must be an array")
        events = []
    last_sequence = 0
    for index, event in enumerate(events):
        label = f"run.events[{index}]"
        if not _require_keys(event, ("sequence", "timestamp", "event_type", "observed_by", "target_scope", "target", "reason_code"), label, errors):
            continue
        sequence = event["sequence"]
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= last_sequence:
            errors.append(f"{label}.sequence must be a strictly increasing positive integer")
        else:
            last_sequence = sequence
        if event["event_type"] not in EVENT_TYPES:
            errors.append(f"{label}.event_type is unknown: {event['event_type']!r}")
        if event["observed_by"] not in EVIDENCE_ORIGINS:
            errors.append(f"{label}.observed_by is unknown: {event['observed_by']!r}")
        _parse_datetime(event["timestamp"], f"{label}.timestamp", errors, allow_none=True)
        target_scope = event["target_scope"]
        if target_scope not in {"repository", "external", "query", "command"}:
            errors.append(f"{label}.target_scope is unknown: {target_scope!r}")
        target = event["target"]
        if not isinstance(target, str) or not target.strip():
            errors.append(f"{label}.target must be a non-empty string")
        elif target_scope == "repository" and event["event_type"] in {"enumerate", "content_read", "write", "scope_expand"} and not _is_safe_relative_path(target):
            errors.append(f"{label}.target must be a safe repository-relative path")
        elif target_scope == "external" and not target.startswith("external://"):
            errors.append(f"{label}.target must use a redacted external:// identifier")

    metric_keys = (
        "input_tokens",
        "output_tokens",
        "wall_time_seconds",
        "provider_cost",
        "documents_touched",
        "documentation_sync_seconds",
        "conflict_warning_delay_seconds",
    )
    if _require_keys(data["metrics"], metric_keys, "run.metrics", errors):
        for key in metric_keys:
            value = data["metrics"][key]
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
                errors.append(f"run.metrics.{key} must be null or a non-negative number")

    if _require_keys(data["artifacts"], ("changed_paths", "diff_git_oid"), "run.artifacts", errors):
        _validate_string_list(
            data["artifacts"]["changed_paths"],
            "run.artifacts.changed_paths",
            errors,
            paths=True,
        )
        diff_git_oid = data["artifacts"]["diff_git_oid"]
        if diff_git_oid is not None and (not isinstance(diff_git_oid, str) or not COMMIT_RE.fullmatch(diff_git_oid)):
            errors.append("run.artifacts.diff_git_oid must be null or a 40-character lowercase Git object id")

    outcome_keys = (
        "task_accepted",
        "validation_passed",
        "missed_dependencies",
        "irrelevant_reads",
        "necessary_reads_missed",
        "scope_expansions",
        "notes",
    )
    if _require_keys(data["outcome"], outcome_keys, "run.outcome", errors):
        for key in ("task_accepted", "validation_passed"):
            if data["outcome"][key] is not None and not isinstance(data["outcome"][key], bool):
                errors.append(f"run.outcome.{key} must be true, false, or null")
        for key in ("missed_dependencies", "irrelevant_reads", "necessary_reads_missed", "scope_expansions"):
            value = data["outcome"][key]
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                errors.append(f"run.outcome.{key} must be null or a non-negative integer")
        if not isinstance(data["outcome"]["notes"], str):
            errors.append("run.outcome.notes must be a string")

    if _require_keys(
        data["evaluation"],
        ("reference_match", "apparatus_valid", "confounds", "notes"),
        "run.evaluation",
        errors,
    ):
        if data["evaluation"]["reference_match"] not in {"exact", "functional", "partial", "failed", "not_evaluated"}:
            errors.append("run.evaluation.reference_match is unknown")
        apparatus_valid = data["evaluation"]["apparatus_valid"]
        if apparatus_valid is not None and not isinstance(apparatus_valid, bool):
            errors.append("run.evaluation.apparatus_valid must be true, false, or null")
        _validate_string_list(data["evaluation"]["confounds"], "run.evaluation.confounds", errors)
        if not isinstance(data["evaluation"]["notes"], str):
            errors.append("run.evaluation.notes must be a string")
    return errors


def summarize_run(data: dict[str, Any]) -> dict[str, Any]:
    events = data.get("events", []) if isinstance(data, dict) else []
    origin_counts = Counter(
        event.get("observed_by")
        for event in events
        if isinstance(event, dict) and event.get("observed_by") in EVIDENCE_ORIGINS
    )
    event_counts = Counter(
        event.get("event_type")
        for event in events
        if isinstance(event, dict) and event.get("event_type") in EVENT_TYPES
    )
    independent_events = sum(origin_counts[origin] for origin in INDEPENDENT_ORIGINS)
    return {
        "total_events": sum(origin_counts.values()),
        "independently_observed_events": independent_events,
        "origin_counts": dict(sorted(origin_counts.items())),
        "event_counts": dict(sorted(event_counts.items())),
        "content_read_compliance_observable": any(
            isinstance(event, dict)
            and event.get("event_type") == "content_read"
            and event.get("observed_by") in INDEPENDENT_ORIGINS
            for event in events
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--repo-root", type=Path, default=default_root)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--skip-git", action="store_true", help="Skip commit and diff checks")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    experiment_root = Path(__file__).resolve().parent
    corpus_path = (args.corpus or experiment_root / "corpus.json").resolve()
    runs_path = (args.runs or experiment_root / "runs").resolve()

    try:
        corpus = load_json(corpus_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load corpus: {exc}", file=sys.stderr)
        return 1
    errors = validate_corpus(corpus, repo_root, check_git=not args.skip_git)
    task_ids = {
        task.get("id")
        for task in corpus.get("tasks", [])
        if isinstance(task, dict) and isinstance(task.get("id"), str)
    }

    run_count = 0
    if runs_path.exists():
        for path in sorted(runs_path.glob("*.json")):
            if path.name.startswith("_"):
                continue
            run_count += 1
            try:
                run = load_json(path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{path}: cannot load run record: {exc}")
                continue
            for error in validate_run_record(run, task_ids):
                errors.append(f"{path.name}: {error}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    category_counts = Counter(task["category"] for task in corpus["tasks"])
    print(
        f"Corpus OK: {len(corpus['tasks'])} tasks; "
        + ", ".join(f"{name}={count}" for name, count in sorted(category_counts.items()))
    )
    print(f"Run records OK: {run_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
