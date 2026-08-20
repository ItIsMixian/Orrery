#!/usr/bin/env python3
"""Frozen v0.2-compatible scaffold fallback for a standalone Skill copy."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "project-template"
RELEASE_MANIFEST_PATH = SKILL_ROOT / "release-manifest.json"
RELEASE = json.loads(RELEASE_MANIFEST_PATH.read_text(encoding="utf-8"))
VERSION = str(RELEASE["version"])
PROJECT_MANIFEST_FORMAT = int(RELEASE["project_manifest_format"])
DOCUMENT_SCHEMA = int(RELEASE["document_schema"])

MANAGED_TOOLS = {
    Path("start-docsite.bat"),
    Path("scripts/docsite/_llm.py"),
    Path("scripts/docsite/build_docsite.py"),
    Path("scripts/docsite/docsite_insights.py"),
    Path("scripts/docsite/docsite_qa.py"),
    Path("scripts/docsite/llm_broker.py"),
    Path("scripts/docsite/requirements.txt"),
    Path("scripts/docsite/serve.py"),
    Path("scripts/docsite/set_key.py"),
}
EXCLUDED_TEMPLATE_PARTS = {"__pycache__", ".DS_Store"}
EXCLUDED_TEMPLATE_SUFFIXES = {".pyc", ".pyo"}


def is_template_asset(path: Path) -> bool:
    """Return whether a file is an authored scaffold asset, not local build debris."""
    relative = path.relative_to(TEMPLATE_ROOT)
    return not any(part in EXCLUDED_TEMPLATE_PARTS for part in relative.parts) and path.suffix not in EXCLUDED_TEMPLATE_SUFFIXES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install a traceable Markdown documentation observatory.")
    parser.add_argument("--target", type=Path, default=Path.cwd(), help="Target repository root")
    parser.add_argument("--title", help="Human-readable project title; defaults to directory name")
    parser.add_argument("--upgrade-tools", action="store_true", help="Replace managed viewer files after backup")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing")
    return parser.parse_args()


def rendered_bytes(source: Path, replacements: dict[str, str]) -> bytes:
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    for token, value in replacements.items():
        text = text.replace("{{" + token + "}}", value)
    return text.encode("utf-8")


def backup_file(target_root: Path, relative: Path, stamp: str, dry_run: bool) -> Path:
    backup = target_root / ".project-orrery-backup" / stamp / relative
    if not dry_run:
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_root / relative, backup)
    return backup


def main() -> int:
    args = parse_args()
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

    if not TEMPLATE_ROOT.is_dir():
        print(f"ERROR: template directory is missing: {TEMPLATE_ROOT}", file=sys.stderr)
        return 2
    if target.exists() and not target.is_dir():
        print(f"ERROR: target is not a directory: {target}", file=sys.stderr)
        return 2
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    actions: list[str] = []
    mixed_tools: list[str] = []
    expected_hashes: dict[str, str] = {}
    for source in sorted(p for p in TEMPLATE_ROOT.rglob("*") if p.is_file() and is_template_asset(p)):
        relative = source.relative_to(TEMPLATE_ROOT)
        destination = target / relative
        content = rendered_bytes(source, replacements)
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

    toolchain_version = VERSION
    if mixed_tools:
        toolchain_version = str(
            existing_manifest.get("toolchain_version")
            or existing_manifest.get("version")
            or "unknown"
        )

    manifest = dict(existing_manifest)
    manifest.update({
        "name": "project-orrery",
        "version": VERSION,
        "manifest_format": PROJECT_MANIFEST_FORMAT,
        "installed_skill_version": VERSION,
        "toolchain_version": toolchain_version,
        "document_schema": existing_manifest.get("document_schema", DOCUMENT_SCHEMA),
        "update_channel": existing_manifest.get("update_channel", RELEASE.get("channel", "stable")),
        "latest_manifest_url": RELEASE.get("latest_manifest_url"),
        "title": title,
        "installed": existing_manifest.get("installed", today),
        "last_scaffold_run": today,
        "authority_status": existing_manifest.get("authority_status", "migration_pending"),
        "toolchain_status": "mixed" if mixed_tools else "current",
        "managed_tools": sorted(p.as_posix() for p in MANAGED_TOOLS),
        "expected_tool_hashes": expected_hashes,
    })
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    old_manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path.is_file() else ""
    manifest_action = "KEEP" if old_manifest_text == manifest_text else ("UPDATE" if manifest_path.exists() else "WRITE")
    actions.append(f"{manifest_action:<7} .project-orrery.json")
    if not args.dry_run:
        manifest_path.write_text(manifest_text, encoding="utf-8")

    print(f"Project Orrery {VERSION} -> {target}")
    for action in actions:
        print(action)
    if mixed_tools:
        print("WARNING: partial/mixed viewer toolchain; differing files were preserved:")
        for relative in mixed_tools:
            print(f"- {relative}")
    print("Authority status: migration pending; copying files does not adopt the model.")
    print("Dry run only; no files changed." if args.dry_run else "Scaffold operation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
