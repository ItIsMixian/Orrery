from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    atomic_write_json,
    dirty_fingerprint,
    git_output,
    git_sha,
    load_json,
    load_mapping_registry,
    machine_inventory,
    sha256_json,
    validate_and_expand_manifest,
)


RUNNER = Path(__file__).with_name("run_test_shard.py")
RECEIPT_TYPE = "orrery-local-validation-receipt-v1"
REFUSAL_TYPE = "orrery-local-validation-refusal-v1"
PLAN_TYPE = "orrery-test-selection-plan-v1"


class SelectionRefused(CIValidationError):
    def __init__(self, message: str, required_metadata: list[str]) -> None:
        super().__init__(message)
        self.required_metadata = required_metadata


def _resolve_commit(value: str) -> str:
    resolved = str(git_output(["rev-parse", "--verify", f"{value}^{{commit}}"])).strip().lower()
    if len(resolved) != 40:
        raise CIValidationError(f"base did not resolve to an exact commit: {value}")
    return resolved


def _private_session() -> tuple[dict[str, Any] | None, str | None]:
    raw = str(git_output(["rev-parse", "--path-format=absolute", "--git-path", "orrery/worktree.json"])).strip()
    path = Path(raw)
    if not path.is_file():
        return None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CIValidationError(f"cannot read Git-private Workstream session: {exc}") from exc
    if not isinstance(value, dict):
        raise CIValidationError("Git-private Workstream session must be a JSON object")
    return value, str(path)


def resolve_base(requested: str | None) -> tuple[str, str, dict[str, Any] | None, str | None]:
    session, session_path = _private_session()
    source = "explicit"
    value = requested
    if value is None and session is not None:
        lineage = session.get("lineage")
        if isinstance(lineage, dict) and isinstance(lineage.get("task_base_oid"), str):
            value = str(lineage["task_base_oid"])
            source = "workstream-lineage-task-base"
        elif isinstance(session.get("merge_base"), str):
            value = str(session["merge_base"])
            source = "workstream-merge-base"
    if value is None:
        value = "main"
        source = "git-main-fallback"
    commit = _resolve_commit(value)
    merge_base = str(git_output(["merge-base", commit, "HEAD"])).strip().lower()
    if len(merge_base) != 40:
        raise CIValidationError("cannot resolve exact validation merge base")
    return merge_base, source, session, session_path


def _nul_paths(arguments: list[str]) -> list[str]:
    raw = git_output(arguments, text=False)
    assert isinstance(raw, bytes)
    return [item.decode("utf-8", errors="surrogateescape").replace("\\", "/") for item in raw.split(b"\0") if item]


def changed_paths(base_sha: str) -> tuple[list[str], bool]:
    values = set(_nul_paths(["diff", "--name-only", "-z", f"{base_sha}...HEAD"]))
    values.update(_nul_paths(["diff", "--name-only", "-z"]))
    values.update(_nul_paths(["diff", "--cached", "--name-only", "-z"]))
    values.update(_nul_paths(["ls-files", "--others", "--exclude-standard", "-z"]))
    dirty = bool(str(git_output(["status", "--porcelain=v1", "--untracked-files=all"])).strip())
    return sorted(values), dirty


def _hash_working_paths(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        digest.update(relative.encode("utf-8", errors="surrogateescape") + b"\0")
        path = ROOT / relative
        if path.is_file():
            try:
                digest.update(path.read_bytes())
            except OSError as exc:
                digest.update(f"unreadable:{exc}".encode())
        else:
            digest.update(b"missing")
    return digest.hexdigest()


def _test_source_hash(test_ids: list[str]) -> str:
    modules = sorted({test_id.split(".", 1)[0] for test_id in test_ids})
    paths = [f"tests/{module}.py" for module in modules]
    paths.extend(["scripts/ci/_common.py", "scripts/ci/run_test_shard.py", "scripts/ci/validate_change.py"])
    return _hash_working_paths(paths)


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _session_scope(session: dict[str, Any] | None) -> tuple[set[str], list[str]]:
    if session is None:
        return set(), []
    subsystems = {str(session.get("primary_subsystem_id", ""))}
    affected = session.get("affected_subsystem_ids")
    if isinstance(affected, list):
        subsystems.update(str(item) for item in affected)
    expected = session.get("expected_writes")
    expected_writes = [str(item).replace("\\", "/") for item in expected] if isinstance(expected, list) else []
    return {item for item in subsystems if item}, expected_writes


def build_selection(
    manifest: dict[str, Any], stage: str, base_sha: str, base_source: str,
    session: dict[str, Any] | None, session_path: str | None,
) -> dict[str, Any]:
    all_ids, _, _ = validate_and_expand_manifest(manifest)
    inventory = machine_inventory(manifest)
    metadata = {item["test_id"]: item for item in inventory["tests"]}
    registry = load_mapping_registry(manifest)
    paths, dirty = changed_paths(base_sha)
    subsystems, expected_writes = _session_scope(session)
    mappings = registry["path_mappings"]
    path_scoped_mappings: list[dict[str, Any]] = []
    subsystem_fallback_mappings: list[dict[str, Any]] = []
    path_explain: list[dict[str, Any]] = []
    for mapping in mappings:
        matched_paths = [path for path in paths if _matches(path, mapping["patterns"])]
        matched_expected = [value for value in expected_writes if any(
            fnmatch.fnmatchcase(value, pattern) or fnmatch.fnmatchcase(pattern, value)
            for pattern in mapping["patterns"]
        )]
        matched_subsystems = sorted(subsystems & set(mapping["subsystems"]))
        if matched_paths or matched_expected:
            path_scoped_mappings.append(mapping)
            path_explain.append({
                "mapping_id": mapping["id"], "changed_paths": matched_paths,
                "expected_writes": matched_expected, "subsystems": matched_subsystems,
                "surfaces": mapping["surfaces"], "high_risk": mapping["high_risk"],
            })
        elif matched_subsystems:
            subsystem_fallback_mappings.append(mapping)
    unknown_paths = [
        path for path in paths
        if not any(_matches(path, mapping["patterns"]) for mapping in mappings)
    ]
    unknown_expected = [
        value for value in expected_writes
        if not any(any(
            fnmatch.fnmatchcase(value, pattern) or fnmatch.fnmatchcase(pattern, value)
            for pattern in mapping["patterns"]
        ) for mapping in mappings)
    ]
    if unknown_paths or unknown_expected:
        raise SelectionRefused(
            f"change scope contains unmapped paths/expected writes: paths={unknown_paths}, expected_writes={unknown_expected}",
            [
                "Add one generic path_mappings entry with id, patterns, subsystems, surfaces, and high_risk.",
                "Then reference that mapping id from exact test dependencies; do not add task-ID branches to the router.",
            ],
        )
    selected_mappings = path_scoped_mappings or subsystem_fallback_mappings
    if not path_scoped_mappings:
        path_explain.extend({
            "mapping_id": mapping["id"], "changed_paths": [], "expected_writes": [],
            "subsystems": sorted(subsystems & set(mapping["subsystems"])),
            "surfaces": mapping["surfaces"], "high_risk": mapping["high_risk"],
        } for mapping in subsystem_fallback_mappings)
    mapping_ids = {mapping["id"] for mapping in selected_mappings}
    if not mapping_ids:
        raise SelectionRefused(
            "no generic mapping was derived from Git diff or Workstream scope",
            ["Add or correct path_mappings metadata for the changed path/subsystem/expected-write surface."],
        )
    selected_ids = sorted(
        test_id for test_id, entry in metadata.items()
        if stage in entry["allowed_stages"] and mapping_ids.intersection(entry["dependencies"])
    )
    if not selected_ids:
        raise SelectionRefused(
            f"no registered {stage} tests depend on mappings {sorted(mapping_ids)}",
            [
                "Register at least one exact test entry with owner_surface, owner_shard, allowed_stages, "
                "cost_class, budget_seconds, dependencies, and reason."
            ],
        )
    head = git_sha()
    fingerprint = dirty_fingerprint()
    budget = float(registry["stages"][stage]["budget_seconds"])
    relevant_hash = _hash_working_paths(paths)
    dependency_hash = sha256_json({
        "mappings": path_explain, "selected_test_ids": selected_ids,
        "registry_sha256": sha256_json(registry), "session_subsystems": sorted(subsystems),
    })
    environment = {
        name: os.environ.get(name)
        for name in registry["reuse"]["environment_gates"]
    }
    security_mappings = set(registry["reuse"]["security_high_risk_mappings"])
    high_risk = bool(mapping_ids & security_mappings)
    reuse_reasons: list[str] = []
    if stage not in {"fast", "checkpoint"}:
        reuse_reasons.append("reuse-is-limited-to-fast-and-checkpoint")
    if dirty:
        reuse_reasons.append("working-tree-is-dirty")
    if high_risk:
        reuse_reasons.append("security-high-risk-surface")
    reuse_reasons.append("reuse-execution-not-enabled-by-contract-v1")
    reuse_key = {
        "test_source_sha256": _test_source_hash(selected_ids),
        "selector_dependency_sha256": dependency_hash,
        "relevant_tree_sha256": relevant_hash,
        "python": platform.python_version(), "os": platform.system(),
        "runner_version": registry["runner_version"],
        "receipt_schema_version": 1, "manifest_sha256": sha256_json(manifest),
        "mapping_registry_sha256": sha256_json(registry),
        "inventory_sha256": inventory["inventory_sha256"], "environment_gates": environment,
    }
    return {
        "schema_version": 1, "contract_type": PLAN_TYPE, "stage": stage,
        "role": registry["stages"][stage]["role"],
        "head_sha": head, "base_sha": base_sha, "base_source": base_source,
        "dirty": dirty, "dirty_fingerprint": fingerprint,
        "manifest_sha256": sha256_json(manifest),
        "mapping_registry_sha256": sha256_json(registry),
        "inventory_sha256": inventory["inventory_sha256"],
        "selected_test_ids": selected_ids, "selected_test_count": len(selected_ids),
        "budget_seconds": budget, "changed_paths": paths, "unknown_paths": unknown_paths,
        "mapping_ids": sorted(mapping_ids), "path_explain": path_explain,
        "selected_tests": [metadata[test_id] for test_id in selected_ids],
        "workstream": {
            "session_path": session_path,
            "workstream_id": session.get("workstream_id") if session else None,
            "primary_subsystem_id": session.get("primary_subsystem_id") if session else None,
            "affected_subsystem_ids": session.get("affected_subsystem_ids", []) if session else [],
            "expected_writes": expected_writes,
        },
        "reuse": {
            "schema_version": registry["reuse"]["schema_version"],
            "mode": registry["reuse"]["mode"], "decision": "refused",
            "eligible_inputs": not reuse_reasons[:-1], "reasons": reuse_reasons, "key": reuse_key,
        },
    }


def _default_output(stage: str) -> Path:
    raw = str(git_output(["rev-parse", "--path-format=absolute", "--git-path", "orrery/ci-validation/receipts"])).strip()
    return Path(raw) / f"latest-{stage}.json"


def _dry_receipt(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        **plan,
        "contract_type": RECEIPT_TYPE,
        "outcome": "dry-run", "successful": False, "completed": True,
        "evidence_eligible": False, "duration_seconds": 0.0,
        "timed_out": False, "interrupted": False, "runner_errors": [],
        "os": platform.system(), "python": platform.python_version(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a local change to the only tier-evidence runner")
    parser.add_argument("--stage", choices=("fast", "checkpoint", "candidate"), required=True)
    parser.add_argument("--base", help="base SHA/ref; defaults to the Git-private Workstream task base")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--reuse", action="store_true", help="evaluate the conservative reuse contract")
    arguments = parser.parse_args()
    started = time.perf_counter()
    output = arguments.output.resolve() if arguments.output else _default_output(arguments.stage)
    base_sha: str | None = None
    base_source: str | None = None
    try:
        manifest_path = arguments.manifest.resolve()
        manifest = load_json(manifest_path)
        base_sha, base_source, session, session_path = resolve_base(arguments.base)
        plan = build_selection(manifest, arguments.stage, base_sha, base_source, session, session_path)
        if arguments.dry_run:
            receipt = _dry_receipt(plan)
            atomic_write_json(output, receipt)
            if arguments.explain:
                print(json.dumps(receipt, ensure_ascii=False, indent=2))
            else:
                print(
                    f"DRY-RUN {arguments.stage}: {plan['selected_test_count']} tests, "
                    f"budget {plan['budget_seconds']}s, receipt {output}"
                )
            return 0
        plan_path = output.with_suffix(output.suffix + ".plan.json")
        atomic_write_json(plan_path, plan)
        command = [
            sys.executable, "-X", "utf8", str(RUNNER), "--manifest", str(manifest_path),
            "--selection-plan", str(plan_path), "--output", str(output),
        ]
        try:
            completed = subprocess.run(
                command, cwd=ROOT, check=False, timeout=float(plan["budget_seconds"])
            )
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            receipt = {
                **plan, "contract_type": RECEIPT_TYPE, "outcome": "timeout",
                "successful": False, "completed": False, "evidence_eligible": False,
                "duration_seconds": round(time.perf_counter() - started, 6),
                "timed_out": True, "interrupted": False,
                "runner_errors": ["validation runner exceeded the stage budget and was terminated"],
                "os": platform.system(), "python": platform.python_version(),
            }
            atomic_write_json(output, receipt)
            print(f"FAIL {arguments.stage}: timed out at {plan['budget_seconds']}s", file=sys.stderr)
            return 1
        if not output.is_file():
            raise CIValidationError("runner returned without a versioned receipt")
        receipt = load_json(output)
        receipt["runner_contract_type"] = receipt.get("contract_type")
        receipt["contract_type"] = RECEIPT_TYPE
        receipt["schema_version"] = 1
        receipt["router_explain"] = plan["path_explain"]
        receipt["reuse"] = plan["reuse"]
        receipt["invoked_by"] = "validate_change.py"
        receipt["evidence_eligible"] = return_code == 0 and receipt.get("successful") is True
        atomic_write_json(output, receipt)
        if arguments.explain:
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0 if receipt["evidence_eligible"] else 1
    except KeyboardInterrupt:
        interruption = {
            "schema_version": 1,
            "contract_type": REFUSAL_TYPE,
            "stage": arguments.stage,
            "head_sha": git_sha(),
            "base_sha": base_sha,
            "base_source": base_source,
            "dirty_fingerprint": dirty_fingerprint(),
            "outcome": "interrupted",
            "successful": False,
            "completed": False,
            "evidence_eligible": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "runner_errors": ["validation router was interrupted; no tier evidence is valid"],
            "required_metadata": [],
            "os": platform.system(),
            "python": platform.python_version(),
        }
        atomic_write_json(output, interruption)
        print("FAIL validation router: interrupted; no tier evidence is valid", file=sys.stderr)
        return 130
    except SelectionRefused as exc:
        refusal = {
            "schema_version": 1,
            "contract_type": REFUSAL_TYPE,
            "stage": arguments.stage,
            "head_sha": git_sha(),
            "base_sha": base_sha,
            "base_source": base_source,
            "dirty_fingerprint": dirty_fingerprint(),
            "outcome": "refused",
            "successful": False,
            "completed": True,
            "evidence_eligible": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "runner_errors": [str(exc)],
            "required_metadata": exc.required_metadata,
            "os": platform.system(),
            "python": platform.python_version(),
        }
        atomic_write_json(output, refusal)
        print(f"REFUSED {arguments.stage}: {exc}", file=sys.stderr)
        for item in exc.required_metadata:
            print(f"- required metadata: {item}", file=sys.stderr)
        return 2
    except (CIValidationError, OSError) as exc:
        message = str(exc)
        required = ["Repair the manifest/registry contract reported by runner_errors before requesting tier evidence."]
        if "unregistered=" in message:
            required = [
                "Add one exact tests entry with owner_surface, owner_shard, allowed_stages, cost_class, "
                "budget_seconds, dependencies, and reason."
            ]
        elif "Unknown dependencies" in message:
            required = [
                "Add the missing generic path_mappings entry or correct the exact test dependencies list."
            ]
        refusal = {
            "schema_version": 1, "contract_type": REFUSAL_TYPE, "stage": arguments.stage,
            "head_sha": git_sha(), "base_sha": base_sha, "base_source": base_source,
            "dirty_fingerprint": dirty_fingerprint(), "outcome": "refused",
            "successful": False, "completed": True, "evidence_eligible": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "runner_errors": [message], "required_metadata": required,
            "os": platform.system(), "python": platform.python_version(),
        }
        atomic_write_json(output, refusal)
        print(f"FAIL validation router: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
