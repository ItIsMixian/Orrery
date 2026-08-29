#!/usr/bin/env python3
"""Install, upgrade, or recoverably uninstall the Orrery Codex adapter."""
from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ADAPTER_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "adapter-manifest.json"
LEGACY_MANIFEST_NAME = "release-manifest.json"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the Orrery Codex adapter")
    parser.add_argument(
        "--source",
        type=Path,
        default=ADAPTER_ROOT,
        help="extracted adapter directory (defaults to this adapter checkout)",
    )
    parser.add_argument(
        "--destination-root",
        type=Path,
        default=Path.home() / ".agents" / "skills",
        help="parent directory where Codex discovers user skills",
    )
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--upgrade", action="store_true", help="back up and replace a recognized install")
    operation.add_argument("--uninstall", action="store_true", help="move a recognized install to recoverable trash")
    parser.add_argument("--dry-run", action="store_true", help="report actions without writing")
    return parser.parse_args()


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_NAME
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        adapter = manifest["adapter"]
        distribution = manifest["distribution"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"invalid adapter manifest at {path}: {error}") from error
    if adapter.get("id") != "project-orrery-codex":
        raise ValueError(f"unexpected adapter id in {path}")
    if distribution.get("install_directory") != "project-orrery":
        raise ValueError(f"unsafe install directory in {path}")
    declared = distribution.get("files")
    if not isinstance(declared, list) or not declared:
        raise ValueError(f"adapter manifest has no distribution file list: {path}")
    return manifest


def included_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)
        and path.suffix not in EXCLUDED_SUFFIXES
    )


def validate_distribution(root: Path, manifest: dict[str, Any]) -> None:
    actual = {path.relative_to(root).as_posix() for path in included_files(root)}
    declared = set(manifest["distribution"]["files"])
    if actual != declared:
        missing = sorted(declared - actual)
        extra = sorted(actual - declared)
        raise ValueError(f"adapter file list mismatch; missing={missing}, extra={extra}")


def resolved_target(destination_root: Path, install_directory: str) -> tuple[Path, Path]:
    root = destination_root.expanduser().resolve()
    if root.anchor and root == Path(root.anchor):
        raise ValueError(f"refusing filesystem-root skills directory: {root}")
    target = (root / install_directory).resolve()
    if target == root or target.parent != root:
        raise ValueError(f"unsafe adapter destination: {target}")
    if target.anchor and target == Path(target.anchor):
        raise ValueError(f"refusing filesystem-root destination: {target}")
    return root, target


def existing_kind(target: Path) -> str:
    if not target.exists():
        return "missing"
    if not target.is_dir():
        return "unknown"
    adapter_manifest = target / MANIFEST_NAME
    if adapter_manifest.is_file():
        try:
            if json.loads(adapter_manifest.read_text(encoding="utf-8")).get("adapter", {}).get("id") == "project-orrery-codex":
                return "adapter"
        except (OSError, json.JSONDecodeError, TypeError):
            return "unknown"
    legacy_manifest = target / LEGACY_MANIFEST_NAME
    if legacy_manifest.is_file() and (target / "SKILL.md").is_file():
        try:
            if json.loads(legacy_manifest.read_text(encoding="utf-8")).get("name") == "project-orrery":
                return "legacy-skill"
        except (OSError, json.JSONDecodeError, TypeError):
            return "unknown"
    return "unknown"


def trees_equal(source: Path, target: Path) -> bool:
    source_files = {path.relative_to(source).as_posix(): path for path in included_files(source)}
    target_files = {path.relative_to(target).as_posix(): path for path in included_files(target)}
    if source_files.keys() != target_files.keys():
        return False
    return all(filecmp.cmp(source_files[name], target_files[name], shallow=False) for name in source_files)


def timestamped_destination(root: Path, category: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return root.parent / category / stamp / "project-orrery"


def stage_adapter(source: Path, root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".project-orrery-adapter-stage-", dir=root))
    for source_file in included_files(source):
        relative = source_file.relative_to(source)
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
    return stage


def install_or_upgrade(source: Path, root: Path, target: Path, kind: str, *, upgrade: bool, dry_run: bool) -> int:
    if kind == "adapter" and trees_equal(source, target):
        print(f"KEEP {target} (adapter already matches source)")
        return 0
    if kind == "unknown":
        print(f"ERROR: refusing to overwrite unrecognized path: {target}", file=sys.stderr)
        return 2
    if kind in {"adapter", "legacy-skill"} and not upgrade:
        print(f"ERROR: recognized {kind} already exists at {target}; preview and use --upgrade", file=sys.stderr)
        return 2

    verb = "INSTALL" if kind == "missing" else "UPGRADE"
    backup = timestamped_destination(root, ".project-orrery-adapter-backup") if kind != "missing" else None
    print(f"{verb} {target}")
    if backup is not None:
        print(f"BACKUP {target} -> {backup}")
    print("NOTICE adapter installation does not install or upgrade project-orrery-cli")
    if dry_run:
        print("DRY-RUN no files changed")
        return 0

    stage = stage_adapter(source, root)
    if backup is None:
        stage.replace(target)
        return 0

    backup.parent.mkdir(parents=True, exist_ok=False)
    shutil.move(str(target), str(backup))
    try:
        stage.replace(target)
    except Exception:
        if not target.exists() and backup.exists():
            shutil.move(str(backup), str(target))
        raise
    return 0


def uninstall(root: Path, target: Path, kind: str, *, dry_run: bool) -> int:
    if kind == "missing":
        print(f"KEEP {target} (nothing installed)")
        return 0
    if kind != "adapter":
        print(f"ERROR: refusing to uninstall unrecognized or legacy path: {target}", file=sys.stderr)
        return 2
    trash = timestamped_destination(root, ".project-orrery-adapter-trash")
    print(f"UNINSTALL {target} -> {trash}")
    if dry_run:
        print("DRY-RUN no files changed")
        return 0
    trash.parent.mkdir(parents=True, exist_ok=False)
    shutil.move(str(target), str(trash))
    print(f"RESTORE by moving {trash} back to {target}")
    return 0


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    try:
        manifest = load_manifest(source)
        validate_distribution(source, manifest)
        root, target = resolved_target(args.destination_root, manifest["distribution"]["install_directory"])
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    kind = existing_kind(target)
    if args.uninstall:
        return uninstall(root, target, kind, dry_run=args.dry_run)
    return install_or_upgrade(source, root, target, kind, upgrade=args.upgrade, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
