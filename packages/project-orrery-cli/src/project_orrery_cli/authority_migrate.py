"""Preview an explicit Authority Model migration without changing the project."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

from project_orrery_core.authority_migration import (
    materialize_authority_model_migration,
    plan_authority_model_migration,
)

from .protocol import JsonExitCode, emit, issue, response


COMMAND = "migrate-authority-model"
APPLY_RECEIPT_DOMAIN = b"project-orrery-authority-model-apply-v1\0"


class AuthorityModelApplyError(OSError):
    """An apply failure that may retain an exact recovery backup."""

    def __init__(self, message: str, *, backup_path: Path | None = None) -> None:
        super().__init__(message)
        self.backup_path = backup_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview an explicit Authority Model migration"
    )
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--to", type=int, required=True, dest="target_version")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report proposed changes and an apply receipt without writing",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply an allowed plan after exact snapshot confirmation",
    )
    parser.add_argument(
        "--apply-receipt",
        help="Required with --apply; copy from the reviewed dry-run output",
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
    data: dict[str, object] | None = None,
) -> int:
    if args.json:
        emit(
            response(
                COMMAND,
                status="error",
                exit_code=exit_code,
                data={"writes_performed": False, **(data or {})},
                errors=[issue(code, message)],
            )
        )
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    return int(exit_code)


def _manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _apply_receipt(
    current_hash: str, target_version: int, proposed_hash: str
) -> str:
    payload = (
        APPLY_RECEIPT_DOMAIN
        + current_hash.encode("ascii")
        + b"\0"
        + str(target_version).encode("ascii")
        + b"\0"
        + proposed_hash.encode("ascii")
    )
    return hashlib.sha256(payload).hexdigest()


def _backup_and_replace(
    root: Path,
    manifest_path: Path,
    before: bytes,
    after: bytes,
) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup_relative = (
        Path(".project-orrery-backup")
        / "authority-model"
        / f"{stamp}-{hashlib.sha256(before).hexdigest()[:12]}"
        / ".project-orrery.json"
    )
    backup_path = root / backup_relative
    backup_path.parent.mkdir(parents=True, exist_ok=False)
    with backup_path.open("xb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())

    temporary_path: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=".project-orrery.", suffix=".tmp", dir=root
        )
        temporary_path = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(after)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, stat.S_IMODE(manifest_path.stat().st_mode))
        os.replace(temporary_path, manifest_path)
        temporary_path = None
    except OSError as exc:
        raise AuthorityModelApplyError(
            str(exc), backup_path=backup_relative
        ) from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return backup_relative


def run(args: argparse.Namespace) -> int:
    if bool(args.dry_run) == bool(args.apply):
        return _failure(
            args,
            code="migration_mode_required",
            message="choose exactly one of --dry-run or --apply",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if args.dry_run and args.apply_receipt:
        return _failure(
            args,
            code="apply_receipt_not_allowed",
            message="--apply-receipt is only valid with --apply",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if args.apply and not args.apply_receipt:
        return _failure(
            args,
            code="apply_receipt_required",
            message="--apply requires --apply-receipt from a dry-run",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if args.apply_receipt and not re.fullmatch(
        r"[0-9A-Fa-f]{64}", args.apply_receipt
    ):
        return _failure(
            args,
            code="apply_receipt_invalid",
            message="--apply-receipt must contain exactly 64 hex digits",
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

    current_hash = hashlib.sha256(manifest_bytes).hexdigest()
    proposed_manifest: dict[str, object] | None = None
    proposed_bytes: bytes | None = None
    if plan["allowed"]:
        proposed_manifest = materialize_authority_model_migration(manifest, plan)
        proposed_bytes = (
            _manifest_bytes(proposed_manifest) if plan["changed"] else manifest_bytes
        )

    proposed_hash = hashlib.sha256(proposed_bytes).hexdigest() if proposed_bytes else None
    receipt = (
        _apply_receipt(current_hash, args.target_version, proposed_hash)
        if proposed_hash
        else None
    )
    data = {
        "project_root": str(root),
        "manifest_path": str(manifest_path),
        "manifest_sha256": current_hash,
        **plan,
        "mode": "apply" if args.apply else "dry-run",
        "operation_status": "pending" if args.apply else "previewed",
        "proposed_manifest_sha256": proposed_hash,
        "predicted_bytes_changed": (
            proposed_bytes != manifest_bytes if proposed_bytes is not None else None
        ),
        "apply_precondition": (
            {
                "expected_manifest_sha256": current_hash,
                "target_version": args.target_version,
                "receipt": receipt,
            }
            if plan["allowed"]
            else None
        ),
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

    if args.dry_run and args.json:
        emit(
            response(
                COMMAND,
                status="ok",
                exit_code=JsonExitCode.OK,
                data=data,
            )
        )
    elif args.dry_run:
        print("Authority Model migration DRY RUN")
        print(f"Project: {root}")
        print(f"Source: {plan['source']['status']}")
        print(f"Target model: {args.target_version}")
        print(f"Predicted changes: {len(plan['changes'])}")
        print(f"Backup required: {'yes' if plan['backup_required'] else 'no'}")
        print(f"Required action: {plan['required_action']}")
        print(f"Apply receipt: {receipt}")
        print("Writes performed: no")
    if args.dry_run:
        return int(JsonExitCode.OK)

    assert args.apply_receipt is not None
    if receipt is None or args.apply_receipt.casefold() != receipt:
        return _failure(
            args,
            code="apply_receipt_stale_or_mismatched",
            message="manifest, target, or proposal differs from dry-run; review a new receipt",
            exit_code=JsonExitCode.COMPATIBILITY_FAILED,
            data=data,
        )
    if not plan["changed"]:
        data["writes_performed"] = False
        data["backup_path"] = None
        data["operation_status"] = "no-op"
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
            print("Authority Model migration APPLY: no changes required")
            print("Writes performed: no")
        return int(JsonExitCode.OK)

    assert proposed_bytes is not None
    try:
        backup_relative = _backup_and_replace(
            root, manifest_path, manifest_bytes, proposed_bytes
        )
    except AuthorityModelApplyError as exc:
        return _failure(
            args,
            code="authority_model_apply_failed",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
            data={
                **data,
                "backup_path": (
                    exc.backup_path.as_posix() if exc.backup_path else None
                ),
            },
        )
    except OSError as exc:
        return _failure(
            args,
            code="authority_model_apply_failed",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
            data={**data, "backup_path": None},
        )

    data["writes_performed"] = True
    data["backup_path"] = backup_relative.as_posix()
    data["operation_status"] = "applied"
    data["manifest_sha256_after"] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
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
        print("Authority Model migration APPLY: complete")
        print(f"Backup: {backup_relative.as_posix()}")
        print("Writes performed: yes")
    return int(JsonExitCode.OK)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
