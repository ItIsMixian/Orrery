"""Safely scaffold or upgrade Project Orrery without platform-specific runtime APIs."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable

from project_orrery_core import build_project_manifest, iter_authority_assets, rendered_bytes, rendered_content
from project_orrery_observatory import MANAGED_TOOLS, iter_observatory_assets, projected_bytes

from .context import CliContext, repository_context
from .protocol import JsonExitCode, emit, issue, response


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install a traceable Markdown documentation observatory.")
    parser.add_argument("--target", type=Path, default=Path.cwd(), help="Target repository root")
    parser.add_argument("--title", help="Human-readable project title; defaults to directory name")
    parser.add_argument("--upgrade-tools", action="store_true", help="Replace managed viewer files after backup")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing")
    parser.add_argument("--json", action="store_true", help="Emit the stable machine-readable response contract")
    return parser.parse_args(argv)


def template_assets(context: CliContext) -> Iterable[tuple[Path, Path]]:
    seen: set[Path] = set()
    for relative, source in iter_authority_assets(context.authority_root):
        seen.add(relative)
        yield relative, source
    for relative, source in iter_observatory_assets(context.observatory_root):
        if relative in seen:
            raise ValueError(f"duplicate Core/Observatory template path: {relative.as_posix()}")
        yield relative, source


def backup_file(target_root: Path, relative: Path, stamp: str, dry_run: bool) -> Path:
    backup = target_root / ".project-orrery-backup" / stamp / relative
    if not dry_run:
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_root / relative, backup)
    return backup


def _action(kind: str, relative: str, **details: object) -> dict[str, object]:
    value: dict[str, object] = {"action": kind, "path": relative}
    value.update(details)
    return value


def _human_action(value: dict[str, object]) -> str | None:
    kind = str(value["action"])
    relative = str(value["path"])
    if kind == "backup":
        return None
    if kind == "create":
        return f"CREATE  {relative}"
    if kind == "keep":
        suffix = " (unchanged)" if value.get("reason") == "unchanged" else ""
        return f"KEEP    {relative}{suffix}"
    if kind == "skip":
        return f"SKIP    {relative} (existing authored file)"
    if kind == "upgrade":
        return f"UPGRADE {relative} (backup: {value['backup_path']})"
    return f"{kind.upper():<7} {relative}"


def _failure(args: argparse.Namespace, code: str, human_message: str, json_message: str | None = None) -> int:
    if args.json:
        exit_code = JsonExitCode.INVALID_REQUEST
        emit(
            response(
                "scaffold",
                status="error",
                exit_code=exit_code,
                errors=[issue(code, json_message or human_message)],
            )
        )
        return int(exit_code)
    print(f"ERROR: {human_message}", file=sys.stderr)
    return 2


def run(args: argparse.Namespace, context: CliContext) -> int:
    target = args.target.expanduser().resolve()
    today = dt.date.today().isoformat()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    manifest_path = target / ".project-orrery.json"
    existing_manifest: dict = {}
    if manifest_path.is_file():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    title = args.title or existing_manifest.get("title") or target.name
    replacements = {
        "PROJECT_TITLE": title,
        "PROJECT_TITLE_PY": title.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n"),
        "PROJECT_SLUG": target.name.lower().replace(" ", "-"),
        "TODAY": today,
    }

    if not context.authority_root.is_dir():
        return _failure(
            args,
            "authority_template_missing",
            f"authority template directory is missing: {context.authority_root}",
            "authority template directory is missing",
        )
    if target.exists() and not target.is_dir():
        return _failure(args, "target_not_directory", f"target is not a directory: {target}")
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    actions: list[dict[str, object]] = []
    mixed_tools: list[str] = []
    preserved_authored: list[str] = []
    expected_hashes: dict[str, str] = {}
    try:
        sources = list(template_assets(context))
    except (FileNotFoundError, ValueError) as exc:
        return _failure(args, "template_inventory_invalid", str(exc))
    for relative, source in sorted(sources):
        destination = target / relative
        content = (
            rendered_content(projected_bytes(relative, source), replacements)
            if relative in MANAGED_TOOLS
            else rendered_bytes(source, replacements)
        )
        if relative in MANAGED_TOOLS:
            expected_hashes[relative.as_posix()] = hashlib.sha256(content).hexdigest()

        if not destination.exists():
            actions.append(_action("create", relative.as_posix()))
            if not args.dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            continue

        existing = destination.read_bytes()
        if existing == content:
            actions.append(_action("keep", relative.as_posix(), reason="unchanged"))
            continue

        if args.upgrade_tools and relative in MANAGED_TOOLS:
            backup = backup_file(target, relative, stamp, args.dry_run)
            backup_relative = backup.relative_to(target).as_posix()
            actions.append(_action("backup", backup_relative, source_path=relative.as_posix()))
            actions.append(_action("upgrade", relative.as_posix(), backup_path=backup_relative))
            if not args.dry_run:
                destination.write_bytes(content)
        else:
            actions.append(_action("skip", relative.as_posix(), reason="existing_authored_file"))
            preserved_authored.append(relative.as_posix())
            if relative in MANAGED_TOOLS:
                mixed_tools.append(relative.as_posix())

    toolchain_version = context.release.version
    if mixed_tools:
        toolchain_version = str(existing_manifest.get("toolchain_version") or existing_manifest.get("version") or "unknown")

    manifest = build_project_manifest(
        existing_manifest,
        release=context.release,
        title=title,
        today=today,
        toolchain_version=toolchain_version,
        toolchain_status="mixed" if mixed_tools else "current",
        managed_tools=[path.as_posix() for path in MANAGED_TOOLS],
        expected_tool_hashes=expected_hashes,
    )
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    old_manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path.is_file() else ""
    manifest_action = "KEEP" if old_manifest_text == manifest_text else ("UPDATE" if manifest_path.exists() else "WRITE")
    actions.append(_action(manifest_action.lower(), ".project-orrery.json"))
    if not args.dry_run:
        manifest_path.write_text(manifest_text, encoding="utf-8")

    if args.json:
        warnings = (
            [
                issue(
                    "mixed_toolchain",
                    "partial/mixed viewer toolchain; differing files were preserved",
                    paths=mixed_tools,
                )
            ]
            if mixed_tools
            else []
        )
        change_actions = {"create", "write", "update", "upgrade"}
        emit(
            response(
                "scaffold",
                status="warning" if warnings else "ok",
                exit_code=JsonExitCode.OK,
                data={
                    "target": str(target),
                    "dry_run": bool(args.dry_run),
                    "upgrade_tools": bool(args.upgrade_tools),
                    "changed": not args.dry_run and any(item["action"] in change_actions for item in actions),
                    "predicted_changes": sum(item["action"] in change_actions for item in actions),
                    "authority_status": "migration_pending",
                    "toolchain_status": "mixed" if mixed_tools else "current",
                    "actions": actions,
                    "preserved_authored_paths": preserved_authored,
                    "managed_tool_conflicts": mixed_tools,
                },
                warnings=warnings,
            )
        )
    else:
        print(f"Project Orrery {context.release.version} -> {target}")
        for action in actions:
            rendered = _human_action(action)
            if rendered is not None:
                print(rendered)
        if mixed_tools:
            print("WARNING: partial/mixed viewer toolchain; differing files were preserved:")
            for relative in mixed_tools:
                print(f"- {relative}")
        print("Authority status: migration pending; copying files does not adopt the model.")
        print("Dry run only; no files changed." if args.dry_run else "Scaffold operation complete.")
    return 0


def main(argv: list[str] | None = None, *, context: CliContext | None = None) -> int:
    return run(parse_args(argv), context or repository_context())


if __name__ == "__main__":
    raise SystemExit(main())
