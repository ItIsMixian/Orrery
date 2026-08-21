"""Restore an exact Authority Model migration backup after reviewed preview."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from project_orrery_core.authority_migration import (
    AuthorityModelMigrationPlanError,
    plan_authority_model_restore,
)

from .authority_migrate import AuthorityModelApplyError, _backup_and_replace
from .protocol import JsonExitCode, emit, issue, response


COMMAND = "restore-authority-model"
RESTORE_RECEIPT_DOMAIN = b"project-orrery-authority-model-restore-v1\0"
MIGRATION_BACKUP_ROOT = Path(".project-orrery-backup") / "authority-model"


class AuthorityModelRestoreRequestError(ValueError):
    """Raised when the requested backup path is outside the safe restore scope."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or restore an exact Authority Model migration backup"
    )
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument(
        "--backup",
        type=Path,
        required=True,
        help="Project-relative backup_path reported by migrate-authority-model",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the backup and emit a restore receipt without writing",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Restore after exact current and backup snapshot confirmation",
    )
    parser.add_argument(
        "--restore-receipt",
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


def _resolve_backup_path(root: Path, requested: Path) -> tuple[Path, str]:
    if requested.is_absolute():
        raise AuthorityModelRestoreRequestError(
            "--backup must be a project-relative migration backup path"
        )
    expected_prefix = tuple(part.casefold() for part in MIGRATION_BACKUP_ROOT.parts)
    requested_prefix = tuple(part.casefold() for part in requested.parts[:2])
    if ".." in requested.parts or requested_prefix != expected_prefix:
        raise AuthorityModelRestoreRequestError(
            "backup must be under .project-orrery-backup/authority-model"
        )

    unresolved = root / requested
    if unresolved.is_symlink() or unresolved.parent.is_symlink():
        raise AuthorityModelRestoreRequestError(
            "backup file and generated backup directory symlinks are not allowed"
        )
    try:
        expected_backup_root = root / MIGRATION_BACKUP_ROOT
        backup_root = expected_backup_root.resolve(strict=True)
        resolved = unresolved.resolve(strict=True)
    except OSError:
        raise
    if backup_root != expected_backup_root:
        raise AuthorityModelRestoreRequestError(
            "Authority Model backup root must not be redirected"
        )

    try:
        scoped = resolved.relative_to(backup_root)
    except ValueError as exc:
        raise AuthorityModelRestoreRequestError(
            "backup must stay inside .project-orrery-backup/authority-model"
        ) from exc
    if (
        len(scoped.parts) != 2
        or not re.fullmatch(
            r"\d{8}T\d{6}\.\d{6}Z-[0-9a-f]{12}", scoped.parts[0]
        )
        or scoped.name != ".project-orrery.json"
    ):
        raise AuthorityModelRestoreRequestError(
            "backup must be a generated Authority Model migration manifest"
        )
    if not resolved.is_file():
        raise AuthorityModelRestoreRequestError("backup must be a regular file")

    normalized = resolved.relative_to(root.resolve()).as_posix()
    return resolved, normalized


def _restore_receipt(
    current_hash: str, backup_relative: str, backup_hash: str
) -> str:
    payload = (
        RESTORE_RECEIPT_DOMAIN
        + current_hash.encode("ascii")
        + b"\0"
        + backup_relative.encode("utf-8")
        + b"\0"
        + backup_hash.encode("ascii")
    )
    return hashlib.sha256(payload).hexdigest()


def run(args: argparse.Namespace) -> int:
    if bool(args.dry_run) == bool(args.apply):
        return _failure(
            args,
            code="restore_mode_required",
            message="choose exactly one of --dry-run or --apply",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if args.dry_run and args.restore_receipt:
        return _failure(
            args,
            code="restore_receipt_not_allowed",
            message="--restore-receipt is only valid with --apply",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if args.apply and not args.restore_receipt:
        return _failure(
            args,
            code="restore_receipt_required",
            message="--apply requires --restore-receipt from a dry-run",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    if args.restore_receipt and not re.fullmatch(
        r"[0-9A-Fa-f]{64}", args.restore_receipt
    ):
        return _failure(
            args,
            code="restore_receipt_invalid",
            message="--restore-receipt must contain exactly 64 hex digits",
            exit_code=JsonExitCode.INVALID_REQUEST,
        )

    root = args.target.expanduser().resolve()
    manifest_path = root / ".project-orrery.json"
    try:
        backup_path, backup_relative = _resolve_backup_path(root, args.backup)
    except AuthorityModelRestoreRequestError as exc:
        return _failure(
            args,
            code="restore_backup_out_of_scope",
            message=str(exc),
            exit_code=JsonExitCode.INVALID_REQUEST,
        )
    except OSError as exc:
        return _failure(
            args,
            code="restore_backup_unavailable",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
        )

    try:
        current_bytes = manifest_path.read_bytes()
        backup_bytes = backup_path.read_bytes()
    except OSError as exc:
        return _failure(
            args,
            code="restore_input_unavailable",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
        )

    try:
        current_manifest = json.loads(current_bytes)
        backup_manifest = json.loads(backup_bytes)
        plan = plan_authority_model_restore(current_manifest, backup_manifest)
    except (UnicodeDecodeError, json.JSONDecodeError, AuthorityModelMigrationPlanError) as exc:
        return _failure(
            args,
            code="restore_manifest_incompatible",
            message=str(exc),
            exit_code=JsonExitCode.COMPATIBILITY_FAILED,
        )

    current_hash = hashlib.sha256(current_bytes).hexdigest()
    backup_hash = hashlib.sha256(backup_bytes).hexdigest()
    receipt = _restore_receipt(current_hash, backup_relative, backup_hash)
    bytes_changed = current_bytes != backup_bytes
    data = {
        "project_root": str(root),
        "manifest_path": str(manifest_path),
        "manifest_sha256": current_hash,
        "backup_path": backup_relative,
        "backup_sha256": backup_hash,
        "proposed_manifest_sha256": backup_hash,
        **plan,
        "semantic_changed": plan["changed"],
        "changed": bytes_changed if plan["allowed"] else False,
        "undo_backup_required": bytes_changed if plan["allowed"] else False,
        "mode": "apply" if args.apply else "dry-run",
        "operation_status": "pending" if args.apply else "previewed",
        "predicted_bytes_changed": bytes_changed if plan["allowed"] else None,
        "restore_precondition": (
            {
                "expected_manifest_sha256": current_hash,
                "expected_backup_path": backup_relative,
                "expected_backup_sha256": backup_hash,
                "receipt": receipt,
            }
            if plan["allowed"]
            else None
        ),
    }
    if not plan["allowed"]:
        error = issue(
            "authority_model_restore_blocked",
            f"restore blocked: {plan['reason_code']}",
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
            mode_label = "APPLY" if args.apply else "DRY RUN"
            print(f"Authority Model restore {mode_label}: BLOCKED")
            print(f"Reason: {plan['reason_code']}")
            print(f"Required action: {plan['required_action']}")
            print("Writes performed: no")
        return int(JsonExitCode.COMPATIBILITY_FAILED)

    if args.dry_run:
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
            print("Authority Model restore DRY RUN")
            print(f"Project: {root}")
            print(f"Backup: {backup_relative}")
            print(f"Restore target: {plan['backup']['status']}")
            print(f"Undo backup required: {'yes' if bytes_changed else 'no'}")
            print(f"Restore receipt: {receipt}")
            print("Writes performed: no")
        return int(JsonExitCode.OK)

    assert args.restore_receipt is not None
    if args.restore_receipt.casefold() != receipt:
        return _failure(
            args,
            code="restore_receipt_stale_or_mismatched",
            message="current manifest or backup differs from dry-run; review a new receipt",
            exit_code=JsonExitCode.COMPATIBILITY_FAILED,
            data=data,
        )
    if not bytes_changed:
        data["writes_performed"] = False
        data["undo_backup_path"] = None
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
            print("Authority Model restore APPLY: no changes required")
            print("Writes performed: no")
        return int(JsonExitCode.OK)

    try:
        undo_backup = _backup_and_replace(
            root,
            manifest_path,
            current_bytes,
            backup_bytes,
            backup_kind="authority-model-restore",
        )
    except AuthorityModelApplyError as exc:
        return _failure(
            args,
            code="authority_model_restore_failed",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
            data={
                **data,
                "undo_backup_path": (
                    exc.backup_path.as_posix() if exc.backup_path else None
                ),
            },
        )
    except OSError as exc:
        return _failure(
            args,
            code="authority_model_restore_failed",
            message=str(exc),
            exit_code=JsonExitCode.OPERATION_FAILED,
            data={**data, "undo_backup_path": None},
        )

    data["writes_performed"] = True
    data["undo_backup_path"] = undo_backup.as_posix()
    data["operation_status"] = "restored"
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
        print("Authority Model restore APPLY: complete")
        print(f"Restored from: {backup_relative}")
        print(f"Undo backup: {undo_backup.as_posix()}")
        print("Writes performed: yes")
    return int(JsonExitCode.OK)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
