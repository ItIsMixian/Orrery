"""Preview an explicit Authority Model migration without changing the project."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from project_orrery_core.authority_migration import plan_authority_model_migration

from .protocol import JsonExitCode, emit, issue, response


COMMAND = "migrate-authority-model"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview an explicit Authority Model migration"
    )
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--to", type=int, required=True, dest="target_version")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required in this checkpoint; report changes without writing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the stable machine-readable response contract",
    )
    return parser.parse_args(argv)


def _failure(
    args: argparse.Namespace,
    *,
    code: str,
    message: str,
    exit_code: JsonExitCode,
) -> int:
    if args.json:
        emit(
            response(
                COMMAND,
                status="error",
                exit_code=exit_code,
                data={"writes_performed": False},
                errors=[issue(code, message)],
            )
        )
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    return int(exit_code)


def run(args: argparse.Namespace) -> int:
    if not args.dry_run:
        return _failure(
            args,
            code="dry_run_required",
            message="this checkpoint supports dry-run only; add --dry-run",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if (
        isinstance(args.target_version, bool)
        or not isinstance(args.target_version, int)
        or args.target_version <= 0
    ):
        return _failure(
            args,
            code="target_version_invalid",
            message="--to must be a positive integer",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )

    root = args.target.expanduser().resolve()
    manifest_path = root / ".project-orrery.json"
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        plan = plan_authority_model_migration(
            manifest,
            target_version=args.target_version,
        )
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
    ) as exc:
        return _failure(
            args,
            code="migration_plan_unavailable",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
        )

    data = {
        "project_root": str(root),
        "manifest_path": str(manifest_path),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        **plan,
    }
    if not plan["allowed"]:
        error = issue(
            "authority_model_migration_blocked",
            f"migration dry-run blocked: {plan['reason_code']}",
            required_action=plan["required_action"],
        )
        if args.json:
            emit(
                response(
                    COMMAND,
                    status="error",
                    exit_code=JsonExitCode.COMPATIBILITY_FAILED,
                    data=data,
                    errors=[error],
                )
            )
        else:
            print("Authority Model migration DRY RUN: BLOCKED")
            print(f"Reason: {plan['reason_code']}")
            print(f"Required action: {plan['required_action']}")
            print("Writes performed: no")
        return int(JsonExitCode.COMPATIBILITY_FAILED)

    if args.json:
        emit(
            response(
                COMMAND,
                status="ok",
                exit_code=JsonExitCode.OK,
                data=data,
            )
        )
    else:
        print("Authority Model migration DRY RUN")
        print(f"Project: {root}")
        print(f"Source: {plan['source']['status']}")
        print(f"Target model: {args.target_version}")
        print(f"Predicted changes: {len(plan['changes'])}")
        print(f"Backup required: {'yes' if plan['backup_required'] else 'no'}")
        print(f"Required action: {plan['required_action']}")
        print("Writes performed: no")
    return int(JsonExitCode.OK)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
