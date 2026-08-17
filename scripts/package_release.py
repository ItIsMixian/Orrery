#!/usr/bin/env python3
"""Build the public Project Orrery Skill archive and checksum."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "project-orrery"
RELEASE_MANIFEST = SKILL_ROOT / "release-manifest.json"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package the Project Orrery Skill release")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "dist")
    parser.add_argument("--check-tag", help="Fail unless this tag equals v<release version>")
    return parser.parse_args()


def included(path: Path) -> bool:
    relative = path.relative_to(SKILL_ROOT)
    return not any(part in EXCLUDED_PARTS for part in relative.parts) and path.suffix not in EXCLUDED_SUFFIXES


def main() -> int:
    args = parse_args()
    manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    version = str(manifest["version"])
    expected_tag = f"v{version}"
    if args.check_tag and args.check_tag != expected_tag:
        print(f"ERROR: tag {args.check_tag!r} does not match release manifest {expected_tag!r}", file=sys.stderr)
        return 2
    distribution_tag = manifest.get("distribution", {}).get("tag")
    if distribution_tag != expected_tag:
        print(f"ERROR: distribution tag {distribution_tag!r} does not match {expected_tag!r}", file=sys.stderr)
        return 2

    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"project-orrery-v{version}.zip"
    checksum = output / f"project-orrery-v{version}.sha256"
    files = sorted(path for path in SKILL_ROOT.rglob("*") if path.is_file() and included(path))

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in files:
            relative = source.relative_to(SKILL_ROOT).as_posix()
            info = zipfile.ZipInfo(f"project-orrery/{relative}", date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(source, os.X_OK) else 0o644) << 16
            bundle.writestr(info, source.read_bytes(), compresslevel=9)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
