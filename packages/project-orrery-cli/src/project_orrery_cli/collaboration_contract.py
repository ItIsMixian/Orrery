"""Read-only Phase 0 collaboration contract inspection."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from project_orrery_core.collaboration import inspect_collaboration

from .protocol import JsonExitCode, emit, issue, response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Project Orrery collaboration contracts")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        data = inspect_collaboration(arguments.target)
    except ValueError as exc:
        if arguments.json_output:
            emit(
                response(
                    "collaboration-contract",
                    status="error",
                    exit_code=JsonExitCode.VALIDATION_FAILED,
                    errors=[issue("collaboration_contract_invalid", str(exc))],
                )
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return int(JsonExitCode.VALIDATION_FAILED)
    if arguments.json_output:
        emit(
            response(
                "collaboration-contract",
                status="ok",
                exit_code=JsonExitCode.OK,
                data=data,
            )
        )
    else:
        identity = data["identity"]
        mode = data["mode"]
        print(f"Project mode: {mode['project_mode']} ({mode['runtime_status']})")
        print(f"Worktree: {identity['worktree_path']}")
        print(f"Branch: {identity['branch'] or '(detached)'}")
        print(f"HEAD: {identity['head']}")
        print(f"Integration: {identity['integration_ref']}@{identity['integration_oid']}")
        print(f"Primary worktree: {identity['primary_worktree_path']}")
        print(f"Subsystems: {len(data['subsystems']['entries'])}")
    return int(JsonExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
