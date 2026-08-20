#!/usr/bin/env python3
"""Build the experimental Project Orrery Codex adapter archive and checksum."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "codex"
MANIFEST = ADAPTER_ROOT / "adapter-manifest.json"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package the Project Orrery Codex adapter")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "dist")
    parser.add_argument("--check-adapter-version", help="fail unless this equals the adapter version")
    return parser.parse_args()


def included_files() -> list[Path]:
    return sorted(
        path
        for path in ADAPTER_ROOT.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(ADAPTER_ROOT).parts)
        and path.suffix not in EXCLUDED_SUFFIXES
    )


def main() -> int:
    args = parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    version = str(manifest["adapter"]["version"])
    if manifest["adapter"].get("support_status") != "experimental":
        print("ERROR: runtime evidence is required before changing adapter support status", file=sys.stderr)
        return 2
    if args.check_adapter_version and args.check_adapter_version != version:
        print(
            f"ERROR: requested adapter version {args.check_adapter_version!r} does not match {version!r}",
            file=sys.stderr,
        )
        return 2

    files = included_files()
    actual = {path.relative_to(ADAPTER_ROOT).as_posix() for path in files}
    declared = set(manifest["distribution"]["files"])
    if actual != declared:
        print(
            f"ERROR: adapter file list mismatch; missing={sorted(declared - actual)}, extra={sorted(actual - declared)}",
            file=sys.stderr,
        )
        return 2

    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"project-orrery-codex-adapter-v{version}.zip"
    checksum = output / f"project-orrery-codex-adapter-v{version}.sha256"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in files:
            relative = source.relative_to(ADAPTER_ROOT).as_posix()
            info = zipfile.ZipInfo(f"project-orrery/{relative}", date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if relative.startswith("scripts/") else 0o644) << 16
            bundle.writestr(info, source.read_bytes(), compresslevel=9)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

