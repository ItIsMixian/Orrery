from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from _common import (
    CIValidationError,
    DEFAULT_MANIFEST,
    ROOT,
    expand_profile,
    load_json,
    promotion_lane_assignments,
    validate_and_expand_manifest,
)


FAST_WORKFLOW = ROOT / ".github" / "workflows" / "fast-validation.yml"
PROMOTION_WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _require(text: str, needle: str, errors: list[str], owner: str) -> None:
    if needle not in text:
        errors.append(f"{owner} missing required contract text: {needle}")


def _top_level_trigger_block(text: str) -> str:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line == "on:"), None)
    if start is None:
        raise CIValidationError("workflow has no top-level on block")
    collected: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line.startswith((" ", "\t")):
            break
        collected.append(line)
    return "\n".join(collected)


def validate_workflows(
    fast_path: Path = FAST_WORKFLOW, promotion_path: Path = PROMOTION_WORKFLOW
) -> list[str]:
    errors: list[str] = []
    try:
        fast = fast_path.read_text(encoding="utf-8")
        promotion = promotion_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read workflows: {exc}"]
    try:
        fast_triggers = _top_level_trigger_block(fast)
        promotion_triggers = _top_level_trigger_block(promotion)
    except CIValidationError as exc:
        return [str(exc)]
    if "  push:" not in fast_triggers or "  pull_request:" not in fast_triggers:
        errors.append("Fast workflow must run for push and pull_request")
    if "--profile fast" not in fast:
        errors.append("Fast workflow must invoke the explicit non-promotion Fast profile")
    if "ORRERY_TEST_BUILD" in fast:
        errors.append("Fast workflow must not imitate dynamic Promotion coverage")
    if "smoke-test (" in fast:
        errors.append("Fast workflow must not use Promotion required-check names")
    _require(fast, "validate_ci.py --all", errors, "Fast workflow")
    _require(fast, "validate_installation.py --target . --require-integrated", errors, "Fast workflow")
    _require(
        fast,
        "group: fast-validation-${{ github.head_ref || github.ref_name }}",
        errors,
        "Fast workflow",
    )
    _require(fast, "cancel-in-progress: true", errors, "Fast workflow")
    fast_dependency_step = "- name: Install Fast discovery dependencies"
    fast_dependency_command = (
        'run: python -m pip install "wheel>=0.41,<1" -r '
        "skills/project-orrery/assets/project-template/scripts/docsite/requirements.txt"
    )
    fast_validation_step = "- name: Validate Fast and Promotion contracts"
    _require(fast, fast_dependency_step, errors, "Fast workflow")
    _require(fast, fast_dependency_command, errors, "Fast workflow")
    if fast_dependency_command in fast and fast_validation_step in fast:
        if fast.index(fast_dependency_command) > fast.index(fast_validation_step):
            errors.append("Fast workflow must install discovery dependencies before contract validation")
    fast_result_step = "- name: Detect non-Promotion timing result"
    fast_upload_step = "- name: Upload non-Promotion timing result"
    _require(fast, fast_result_step, errors, "Fast workflow")
    _require(fast, 'available={str(result.is_file()).lower()}', errors, "Fast workflow")
    _require(
        fast,
        "if: ${{ always() && steps.fast-result.outputs.available == 'true' }}",
        errors,
        "Fast workflow",
    )
    if fast_result_step in fast and fast_upload_step in fast:
        if fast.index(fast_result_step) > fast.index(fast_upload_step):
            errors.append("Fast workflow must detect the timing result before artifact upload")

    if "  workflow_dispatch:" not in promotion_triggers:
        errors.append("Promotion workflow must use explicit workflow_dispatch")
    if "  push:" not in promotion_triggers or '      - "promotion/**"' not in promotion_triggers:
        errors.append("Promotion push trigger must be restricted to the frozen promotion/** namespace")
    if "  pull_request:" in promotion_triggers or "branches-ignore" in promotion_triggers:
        errors.append("Promotion workflow must not run on pull_request or broad branch exclusions")
    for needle in (
        "candidate_ref:",
        "candidate_sha:",
        "ref: ${{ needs.preflight.outputs.candidate_sha }}",
        "github.event_name == 'workflow_dispatch' && inputs.candidate_ref || github.ref",
        "github.event_name == 'workflow_dispatch' && inputs.candidate_sha || github.sha",
        "validate_ci.py --bind",
        "test_inventory.py",
        "test_inventory.py --lane-list",
        "run_test_lane.py --lane",
        "aggregate_test_results.py",
        "validate_repository_gates.py",
        "validate_installation.py --target . --require-integrated",
        "build_docsite.py --out",
        'ORRERY_TEST_BUILD: "1"',
        "name: smoke-test (windows-latest)",
        "name: smoke-test (ubuntu-latest)",
        "matrix-result",
        "gate-result",
        "if: ${{ always() }}",
    ):
        _require(promotion, needle, errors, "Promotion workflow")
    for required_name in ("name: smoke-test (windows-latest)", "name: smoke-test (ubuntu-latest)"):
        if promotion.count(required_name) != 1:
            errors.append(f"Promotion workflow must define required name exactly once: {required_name}")
    if "run_test_shard.py --shard" in promotion:
        errors.append("Promotion workflow must execute physical lanes, not one hosted job per logical shard")
    if promotion.count("max-parallel: 10") != 2:
        errors.append("Promotion workflow must bound both OS lane matrices to ten concurrent jobs")
    try:
        ubuntu_lanes = promotion.split("  ubuntu-lanes:", 1)[1].split("  ubuntu-gates:", 1)[0]
        ubuntu_gates = promotion.split("  ubuntu-gates:", 1)[1].split(
            "  smoke-test-windows:", 1
        )[0]
    except IndexError:
        errors.append("Promotion workflow must define explicit Ubuntu lane and gate jobs")
    else:
        for owner, section in (("Ubuntu lanes", ubuntu_lanes), ("Ubuntu gates", ubuntu_gates)):
            if "needs: preflight" not in section:
                errors.append(f"{owner} must start independently after preflight")
            if "windows-lanes" in section or "windows-gates" in section:
                errors.append(f"{owner} must not wait for the Windows execution wave")
    preflight = promotion.split("  windows-lanes:", 1)[0]
    dependency_step = "- name: Install preflight discovery dependencies"
    _require(preflight, dependency_step, errors, "Promotion preflight")
    _require(
        preflight,
        "skills/project-orrery/assets/project-template/scripts/docsite/requirements.txt",
        errors,
        "Promotion preflight",
    )
    if dependency_step in preflight and "- name: Bind checkout to frozen candidate ref and SHA" in preflight:
        if preflight.index(dependency_step) > preflight.index("- name: Bind checkout to frozen candidate ref and SHA"):
            errors.append("Promotion preflight must install discovery dependencies before exact-SHA inventory validation")
    aggregate_dependency_step = "- name: Install aggregate discovery dependencies"
    aggregate_sections = {
        "Windows": promotion.split("  smoke-test-windows:", 1)[-1].split(
            "  smoke-test-ubuntu:", 1
        )[0],
        "Ubuntu": promotion.split("  smoke-test-ubuntu:", 1)[-1],
    }
    for platform, section in aggregate_sections.items():
        _require(section, aggregate_dependency_step, errors, f"Promotion {platform} aggregate")
        _require(
            section,
            "skills/project-orrery/assets/project-template/scripts/docsite/requirements.txt",
            errors,
            f"Promotion {platform} aggregate",
        )
        aggregate_step = "- name: Fail-closed aggregate"
        if aggregate_dependency_step in section and aggregate_step in section:
            if section.index(aggregate_dependency_step) > section.index(aggregate_step):
                errors.append(
                    f"Promotion {platform} aggregate must install discovery dependencies before inventory aggregation"
                )
    branch_items = [line.strip() for line in promotion_triggers.splitlines() if line.strip().startswith("-")]
    if branch_items != ['- "promotion/**"']:
        errors.append(f"Promotion push branches must be exactly promotion/**: {branch_items}")
    return errors


def validate_binding(candidate_ref: str, candidate_sha: str) -> list[str]:
    errors: list[str] = []
    if not candidate_ref.strip():
        errors.append("candidate ref is empty")
    normalized_ref = candidate_ref.removeprefix("refs/heads/")
    if normalized_ref == "main":
        errors.append("Promotion candidate ref must be non-main")
    if FULL_SHA_RE.fullmatch(candidate_ref):
        errors.append("candidate ref must name an explicit ref, not repeat the SHA")
    if not FULL_SHA_RE.fullmatch(candidate_sha):
        errors.append("candidate SHA must be exactly 40 hexadecimal characters")
        return errors
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        errors.append(f"cannot resolve checked-out HEAD: {result.stderr.strip()}")
    elif result.stdout.strip().lower() != candidate_sha.lower():
        errors.append(
            f"checked-out HEAD {result.stdout.strip().lower()} does not equal frozen candidate SHA {candidate_sha.lower()}"
        )
    return errors


def validate_all(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_json(manifest_path)
        all_ids, assignments, fast_ids = validate_and_expand_manifest(manifest)
        lanes = promotion_lane_assignments(manifest)
        checkpoint_ids = expand_profile(manifest, "checkpoint", all_ids)
        if len(assignments) < 8:
            errors.append("Promotion manifest must retain meaningful parallel sharding")
        if len(lanes) != 10:
            errors.append("CI5 Promotion manifest must define exactly ten physical lanes")
        if set(fast_ids) == set(all_ids):
            errors.append("Fast profile must remain a strict subset and cannot masquerade as Promotion")
        if not set(fast_ids).issubset(checkpoint_ids):
            errors.append("Checkpoint must include every Fast test before adding adjacency")
        if set(checkpoint_ids) == set(all_ids):
            errors.append("Checkpoint must remain a strict subset and cannot masquerade as Promotion")
        if float(manifest["fast"]["budget_seconds"]) > 15:
            errors.append("Fast profile budget must remain at or below 15 seconds")
        if float(manifest["checkpoint"]["budget_seconds"]) > 90:
            errors.append("Checkpoint profile budget must remain at or below 90 seconds")
        w7b_shards = [item for item in manifest["shards"] if item["id"] == "team-relations-execution"]
        if len(w7b_shards) != 1:
            errors.append("W7B execution must have one dedicated Promotion shard")
        elif float(w7b_shards[0].get("budget_seconds", 0)) != 300:
            errors.append("W7B Promotion shard must retain its 300-second hard budget")
        packaging_ids = {
            test_id
            for shard in manifest["shards"]
            if shard["surface"] == "Packaging/Adapters/docsite"
            for test_id in assignments[shard["id"]]
        }
        required_packaging = {
            "test_project_orrery.ProjectOrreryTests.test_release_package_contains_clean_versioned_skill_and_checksum",
            "test_cli_wheel_installation.CliWheelInstallationTests.test_wheel_contains_observatory_assets_and_runs_without_source_repository",
        }
        missing_packaging = sorted(required_packaging - packaging_ids)
        if missing_packaging:
            errors.append(f"Promotion packaging surface lost critical tests: {missing_packaging}")
    except CIValidationError as exc:
        errors.append(str(exc))
    errors.extend(validate_workflows())
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent Fast/Promotion CI contract validator")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--all", action="store_true", help="validate manifest completeness and both workflows")
    parser.add_argument("--bind", action="store_true", help="validate checked-out exact candidate ref/SHA binding")
    parser.add_argument("--candidate-ref")
    parser.add_argument("--candidate-sha")
    arguments = parser.parse_args()
    if not arguments.all and not arguments.bind:
        parser.error("select --all and/or --bind")
    errors: list[str] = []
    if arguments.all:
        errors.extend(validate_all(arguments.manifest.resolve()))
    if arguments.bind:
        if arguments.candidate_ref is None or arguments.candidate_sha is None:
            parser.error("--bind requires --candidate-ref and --candidate-sha")
        errors.extend(validate_binding(arguments.candidate_ref, arguments.candidate_sha))
    if errors:
        print("FAIL CI contract:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("PASS CI contract: Fast role, Promotion completeness, exact-SHA binding, and fail-closed gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
