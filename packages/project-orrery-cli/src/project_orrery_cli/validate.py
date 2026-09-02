"""Validate an installation without calling a model, network, or Agent runtime."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from project_orrery_core import REQUIRED_SCAFFOLD_FILES
from project_orrery_core.authority import AuthorityEvaluationError
from project_orrery_core.authority_compatibility import judge_project_authority_model

from .authority_shadow import build_authority_shadow, scan_legacy_authority
from .context import CliContext, repository_context
from .protocol import JsonExitCode, emit, issue, response


LEGACY_LAUNCHER_REPLACEMENTS = {
    "start-docsite.bat": ("Start Orrery.vbs", "Start Orrery Console.bat"),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an installed Project Orrery scaffold"
    )
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build docs/_site/index.html; requires dependencies",
    )
    parser.add_argument(
        "--require-integrated",
        action="store_true",
        help="Fail unless the authority chain appears integrated",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the stable machine-readable response contract",
    )
    return parser.parse_args(argv)


def _authority_model_summary(capability: dict[str, object] | None) -> str:
    if capability is None:
        return "unavailable (project manifest could not be interpreted)"
    selected = capability["selected_version"]
    status = capability["status"]
    if status == "supported":
        return f"{selected} (supported; strict evaluation eligible)"
    return f"{status} (read-only; {capability['required_action']})"


def run(args: argparse.Namespace, context: CliContext) -> int:
    root = args.target.expanduser().resolve()
    problems: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    build_completed = False
    authority_model: dict[str, object] | None = None

    def problem(code: str, message: str, **details: object) -> None:
        problems.append(issue(code, message, **details))

    def warning(code: str, message: str, **details: object) -> None:
        warnings.append(issue(code, message, **details))

    for relative in REQUIRED_SCAFFOLD_FILES:
        replacements = LEGACY_LAUNCHER_REPLACEMENTS.get(relative, ())
        if not (root / relative).is_file() and not (
            replacements and all((root / replacement).is_file() for replacement in replacements)
        ):
            problem(
                "required_file_missing",
                f"missing required file: {relative}",
                path=relative,
            )

    for script in sorted((root / "scripts" / "docsite").glob("*.py")):
        try:
            source = script.read_text(encoding="utf-8")
            compile(source, str(script), "exec")
        except (OSError, SyntaxError) as exc:
            problem(
                "python_compile_failed",
                f"Python compile failed: {script.name}: {exc}",
                path=script.name,
            )

    for path in [root / "AGENTS.md", *sorted((root / "docs").rglob("*.md"))]:
        if path.is_file() and re.search(
            r"\{\{[A-Z0-9_]+\}\}", path.read_text(encoding="utf-8")
        ):
            relative = path.relative_to(root).as_posix()
            problem(
                "unresolved_template_token",
                f"unresolved template token: {relative}",
                path=relative,
            )

    gitignore = root / ".gitignore"
    safety_entries = (
        "docs/_site/",
        "scripts/docsite/.doccache.json",
        "scripts/docsite/.port",
        "ai-config.json",
        ".project-orrery-backup/",
    )
    ignored = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    missing_ignores = [entry for entry in safety_entries if entry not in ignored]
    if missing_ignores:
        warning(
            "gitignore_safety_entries_missing",
            ".gitignore is missing safety entries: " + ", ".join(missing_ignores),
            entries=missing_ignores,
        )

    manifest_path = root / ".project-orrery.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("toolchain_status") == "mixed":
                warning("toolchain_mixed", "viewer toolchain is marked partial/mixed")
            legacy_manifest = (
                manifest.get("name") == "project-orrery"
                and "manifest_format" not in manifest
            )
            manifest_format = 1 if legacy_manifest else manifest.get("manifest_format")
            schema = manifest.get("document_schema", 1 if legacy_manifest else None)
            if legacy_manifest:
                warning(
                    "legacy_project_manifest",
                    "legacy v0.1 project manifest detected; rerun the current installer to record version dimensions",
                )
            if manifest_format != context.release.project_manifest_format:
                problem(
                    "project_manifest_format_unsupported",
                    "unsupported .project-orrery.json format: "
                    f"{manifest_format!r}; expected {context.release.project_manifest_format}",
                    actual=manifest_format,
                    expected=context.release.project_manifest_format,
                )
            schema_rule = context.release.compatibility["document_schema"]
            if (
                not isinstance(schema, int)
                or not schema_rule["minimum"] <= schema <= schema_rule["maximum"]
            ):
                problem(
                    "document_schema_unsupported",
                    f"unsupported document schema: {schema!r}; supported range is "
                    f"{schema_rule['minimum']}..{schema_rule['maximum']}",
                    actual=schema,
                    minimum=schema_rule["minimum"],
                    maximum=schema_rule["maximum"],
                )
            if manifest.get("toolchain_status") == "current" and not manifest.get(
                "toolchain_version"
            ):
                warning(
                    "toolchain_version_missing",
                    "current viewer toolchain has no recorded toolchain_version",
                )
            authority_model = judge_project_authority_model(manifest)
            model_status = authority_model["status"]
            if model_status == "legacy-unversioned":
                warning(
                    "authority_model_legacy_unversioned",
                    "Authority Model version is not selected; raw Markdown remains readable but deterministic Authority claims are unavailable",
                    capability=authority_model,
                )
                if args.require_integrated:
                    problem(
                        "authority_model_required",
                        "strict integrated validation requires an explicitly supported authority_model_version",
                        capability=authority_model,
                    )
            elif model_status != "supported":
                problem(
                    "authority_model_unsupported",
                    f"Authority Model capability is {model_status}; deterministic Authority claims fail closed",
                    capability=authority_model,
                )
        except json.JSONDecodeError:
            warning(
                "project_manifest_invalid_json",
                ".project-orrery.json is not valid JSON",
            )
    else:
        problem(
            "project_manifest_missing",
            "missing required file: .project-orrery.json",
            path=".project-orrery.json",
        )

    legacy_authority = scan_legacy_authority(root)
    integrated = legacy_authority.integrated
    if (
        authority_model is not None
        and authority_model["authority_evaluation_capability"] == "available"
    ):
        try:
            shadow = build_authority_shadow(root, legacy_authority)
        except (AuthorityEvaluationError, OSError, ValueError) as exc:
            warning(
                "authority_shadow_unavailable",
                f"authority shadow unavailable; legacy CLI remains authoritative: {exc}",
            )
        else:
            differences = shadow["comparison"]["differences"]
            if differences:
                summary = ", ".join(
                    f"{item['field']}[{item['category']}] legacy={item['legacy']!r} core={item['core']!r}"
                    for item in differences
                )
                warning(
                    "authority_shadow_mismatch",
                    "authority shadow mismatch; legacy CLI remains authoritative: "
                    + summary,
                    differences=differences,
                )
    if not integrated:
        warning(
            "authority_migration_pending",
            "authority migration is pending; scaffold presence is not formal adoption",
        )
        if args.require_integrated:
            problem(
                "authority_not_integrated",
                "authority chain is not integrated: add an accepted project ADR and update AGENTS/PROGRESS",
            )

    if args.build and not problems:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "scripts/docsite/build_docsite.py"],
            cwd=root,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode:
            problem(
                "static_build_failed",
                "static build failed:\n" + (result.stdout + result.stderr).strip(),
            )
        elif not (root / "docs" / "_site" / "index.html").is_file():
            problem(
                "static_build_output_missing",
                "static build reported success but docs/_site/index.html is missing",
            )
        else:
            build_completed = True

    if problems:
        if args.json:
            exit_code = JsonExitCode.VALIDATION_FAILED
            emit(
                response(
                    "validate",
                    status="error",
                    exit_code=exit_code,
                    data={
                        "target": str(root),
                        "valid": False,
                        "integrated": integrated,
                        "authority_model": authority_model,
                        "build_requested": bool(args.build),
                        "build_completed": build_completed,
                    },
                    warnings=warnings,
                    errors=problems,
                )
            )
            return int(exit_code)
        print("Project Orrery validation FAILED")
        print(f"Authority model: {_authority_model_summary(authority_model)}")
        for item in problems:
            print(f"- {item['message']}")
        for item in warnings:
            print(f"WARNING: {item['message']}")
        return 1

    suffix = " + static build" if args.build else ""
    if args.json:
        emit(
            response(
                "validate",
                status="warning" if warnings else "ok",
                exit_code=JsonExitCode.OK,
                data={
                    "target": str(root),
                    "valid": True,
                    "integrated": integrated,
                    "authority_status": (
                        "integrated_candidate" if integrated else "migration_pending"
                    ),
                    "authority_model": authority_model,
                    "build_requested": bool(args.build),
                    "build_completed": build_completed,
                },
                warnings=warnings,
            )
        )
    else:
        print(f"Project Orrery scaffold structure valid{suffix}: {root}")
        print(
            "Authority status: integrated candidate"
            if integrated
            else "Authority status: migration pending"
        )
        print(f"Authority model: {_authority_model_summary(authority_model)}")
        for item in warnings:
            print(f"WARNING: {item['message']}")
    return 0


def main(argv: list[str] | None = None, *, context: CliContext | None = None) -> int:
    return run(parse_args(argv), context or repository_context())


if __name__ == "__main__":
    raise SystemExit(main())
