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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install a traceable Markdown documentation observatory.")
    parser.add_argument("--target", type=Path, default=Path.cwd(), help="Target repository root")
    parser.add_argument("--title", help="Human-readable project title; defaults to directory name")
    parser.add_argument("--upgrade-tools", action="store_true", help="Replace managed viewer files after backup")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing")
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
        print(f"ERROR: authority template directory is missing: {context.authority_root}", file=sys.stderr)
        return 2
    if target.exists() and not target.is_dir():
        print(f"ERROR: target is not a directory: {target}", file=sys.stderr)
        return 2
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    actions: list[str] = []
    mixed_tools: list[str] = []
    expected_hashes: dict[str, str] = {}
    try:
        sources = list(template_assets(context))
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
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
            actions.append(f"CREATE  {relative.as_posix()}")
            if not args.dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            continue

        existing = destination.read_bytes()
        if existing == content:
            actions.append(f"KEEP    {relative.as_posix()} (unchanged)")
            continue

        if args.upgrade_tools and relative in MANAGED_TOOLS:
            backup = backup_file(target, relative, stamp, args.dry_run)
            actions.append(f"UPGRADE {relative.as_posix()} (backup: {backup.relative_to(target).as_posix()})")
            if not args.dry_run:
                destination.write_bytes(content)
        else:
            actions.append(f"SKIP    {relative.as_posix()} (existing authored file)")
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
    actions.append(f"{manifest_action:<7} .project-orrery.json")
    if not args.dry_run:
        manifest_path.write_text(manifest_text, encoding="utf-8")

    print(f"Project Orrery {context.release.version} -> {target}")
    for action in actions:
        print(action)
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
