#!/usr/bin/env python3
"""Build a deterministic npm-compatible tarball for the DeepSeek adapter."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "deepseek-harness"
MANIFEST = ADAPTER_ROOT / "adapter-manifest.json"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tgz"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package the Orrery DeepSeek Harness adapter")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "dist")
    parser.add_argument("--check-adapter-version")
    return parser.parse_args()


def included_files() -> list[Path]:
    return sorted(
        path
        for path in ADAPTER_ROOT.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(ADAPTER_ROOT).parts)
        and path.suffix not in EXCLUDED_SUFFIXES
    )


def build_tarball(files: list[Path], destination: Path) -> None:
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for source in files:
                    relative = source.relative_to(ADAPTER_ROOT).as_posix()
                    payload = source.read_bytes()
                    info = tarfile.TarInfo(f"package/{relative}")
                    info.size = len(payload)
                    info.mtime = 0
                    info.mode = 0o755 if relative.startswith("scripts/") else 0o644
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    bundle.addfile(info, io.BytesIO(payload))


def main() -> int:
    args = parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    version = str(manifest["adapter"]["version"])
    package_name = str(manifest["distribution"]["package_name"])
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
    archive = output / f"{package_name}-{version}.tgz"
    checksum = output / f"{package_name}-{version}.sha256"
    build_tarball(files, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
