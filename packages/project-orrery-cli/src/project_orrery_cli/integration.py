"""Speculative integration dry-run command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.review import generate_review_package

from .protocol import JsonExitCode, emit, issue, response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an evidence-first review package in a disposable integration worktree"
    )
    parser.add_argument("--candidate", type=Path, default=Path("."))
    parser.add_argument("--target", dest="target_ref")
    parser.add_argument("--strategy", choices=("merge", "rebase"), default="merge")
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--validation-command", action="append", default=None)
    parser.add_argument("--validation-timeout", type=int, default=300)
    parser.add_argument("--validation-freshness", type=int, default=86400)
    parser.add_argument("--ai-summary-file", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def _failure(json_output: bool, exc: ValueError) -> int:
    if json_output:
        emit(
            response(
                "integrate-dry-run",
                status="error",
                exit_code=JsonExitCode.OPERATION_FAILED,
                errors=[issue("speculative_integration_failed", str(exc))],
            )
        )
    else:
        print(f"ERROR: {exc}", file=sys.stderr)
    return int(JsonExitCode.OPERATION_FAILED)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    summary: str | None = None
    if arguments.ai_summary_file is not None:
        try:
            summary = arguments.ai_summary_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return _failure(arguments.json_output, ValueError(f"cannot read AI summary file: {exc}"))
    try:
        data = generate_review_package(
            arguments.candidate,
            target_ref=arguments.target_ref,
            strategy=arguments.strategy,
            validation_commands=arguments.validation_command,
            validation_timeout_seconds=arguments.validation_timeout,
            validation_freshness_seconds=arguments.validation_freshness,
            ai_summary=summary,
        )
    except ValueError as exc:
        return _failure(arguments.json_output, exc)
    ready = (
        data["review_package"]["evidence"]["speculative_integration"]["result"]
        == "ready-for-human-integration"
    )
    exit_code = JsonExitCode.OK if ready else JsonExitCode.COMPATIBILITY_FAILED
    if arguments.json_output:
        emit(
            response(
                "integrate-dry-run",
                status="ok" if ready else "warning",
                exit_code=exit_code,
                data=data,
                warnings=(
                    []
                    if ready
                    else [
                        issue(
                            "speculative_integration_not_ready",
                            "review evidence was preserved but integration eligibility is blocked",
                        )
                    ]
                ),
            )
        )
    else:
        package = data["review_package"]
        print(f"Review package: {package['package_id']}")
        print(f"Evidence: {data['review_package_path']}")
        print(f"Speculative result: {package['evidence']['speculative_integration']['result']}")
        print("Integration ref updated: no")
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
