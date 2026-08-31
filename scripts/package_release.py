#!/usr/bin/env python3
"""Build the deterministic Orrery release archive from exact committed Git blobs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = "skills/project-orrery/release-manifest.json"
BUILDER_PATH = "scripts/package_release.py"
ARCHIVE_ROOT = "project-orrery"
BUILDER_CONTRACT = 2
ALLOWED_EXACT = {"LICENSE", "packages/component-versions.json"}
ALLOWED_PREFIXES = (
    "skills/project-orrery/",
    "packages/project-orrery-core/",
    "packages/project-orrery-cli/",
    "packages/project-orrery-observatory/",
    "adapters/harness-json/",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package an exact committed Orrery release")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "dist")
    parser.add_argument("--check-tag", help="Fail unless this tag equals v<release version>")
    parser.add_argument("--source-sha", default="HEAD", help="Exact commit to package; defaults to HEAD")
    parser.add_argument("--receipt-file", type=Path, help="Optional non-release path for the deterministic receipt")
    return parser.parse_args()


def git(*arguments: str, text: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *arguments], cwd=REPOSITORY_ROOT, capture_output=True, check=False
    )
    if completed.returncode:
        message = completed.stderr.decode("utf-8", "replace").strip()
        raise ValueError(message or f"git {' '.join(arguments)} failed")
    return completed.stdout.decode("utf-8") if text else completed.stdout


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def archive_path(source_path: str) -> str:
    relative = source_path.removeprefix("skills/project-orrery/")
    value = PurePosixPath(ARCHIVE_ROOT, relative).as_posix()
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or ".." in parsed.parts or value.startswith("/"):
        raise ValueError(f"unsafe archive path: {value}")
    return value


def included(source_path: str) -> bool:
    return source_path in ALLOWED_EXACT or any(source_path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def tree_entries(source_sha: str) -> list[dict[str, Any]]:
    raw = git("ls-tree", "-r", "-z", source_sha)
    assert isinstance(raw, bytes)
    entries: list[dict[str, Any]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        if not included(path):
            continue
        if kind != "blob" or mode == "120000":
            raise ValueError(f"release inventory requires regular Git blobs: {path} ({mode} {kind})")
        target = archive_path(path)
        content = git("cat-file", "blob", oid)
        assert isinstance(content, bytes)
        entries.append(
            {
                "source_path": path,
                "archive_path": target,
                "oid": oid,
                "mode": mode,
                "size": len(content),
                "sha256": sha256(content),
                "content": content,
            }
        )
    entries.sort(key=lambda item: item["archive_path"].casefold())
    names = [entry["archive_path"] for entry in entries]
    if len(names) != len(set(names)) or len(names) != len({name.casefold() for name in names}):
        raise ValueError("duplicate or case-colliding archive paths")
    return entries


def main() -> int:
    args = parse_args()
    try:
        dirty = git("status", "--porcelain", "--untracked-files=all", text=True)
        assert isinstance(dirty, str)
        if dirty:
            raise ValueError("release source worktree is dirty or contains untracked files")
        source_sha = str(git("rev-parse", "--verify", f"{args.source_sha}^{{commit}}", text=True)).strip()
        if len(source_sha) != 40:
            raise ValueError("release source did not resolve to a full 40-character commit SHA")
        builder_oid = str(git("rev-parse", f"{source_sha}:{BUILDER_PATH}", text=True)).strip()
        committed_builder = git("cat-file", "blob", builder_oid)
        assert isinstance(committed_builder, bytes)
        if (REPOSITORY_ROOT / BUILDER_PATH).read_bytes() != committed_builder:
            raise ValueError("running builder bytes do not match the selected source commit")

        manifest_oid = str(git("rev-parse", f"{source_sha}:{MANIFEST_PATH}", text=True)).strip()
        manifest_bytes = git("cat-file", "blob", manifest_oid)
        assert isinstance(manifest_bytes, bytes)
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        version = str(manifest["version"])
        expected_tag = f"v{version}"
        if args.check_tag and args.check_tag != expected_tag:
            raise ValueError(f"tag {args.check_tag!r} does not match release manifest {expected_tag!r}")
        if manifest.get("distribution", {}).get("tag") != expected_tag:
            raise ValueError("distribution tag does not match the release version")
        if int(manifest.get("distribution", {}).get("builder_contract", 0)) != BUILDER_CONTRACT:
            raise ValueError("release manifest builder contract does not match this builder")

        entries = tree_entries(source_sha)
        path_list = "".join(f"{entry['archive_path']}\n" for entry in entries).encode("utf-8")
        path_list_hash = sha256(path_list)
        expected_count = int(manifest["distribution"]["archive_entries"])
        expected_paths = str(manifest["distribution"]["archive_path_list_sha256"])
        if len(entries) != expected_count or path_list_hash != expected_paths:
            raise ValueError(
                f"archive inventory mismatch: observed {len(entries)}/{path_list_hash}, "
                f"expected {expected_count}/{expected_paths}"
            )

        output = args.output_dir.expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        archive = output / f"project-orrery-v{version}.zip"
        checksum = output / f"project-orrery-v{version}.sha256"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as bundle:
            for entry in entries:
                info = zipfile.ZipInfo(entry["archive_path"], date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                permissions = 0o755 if entry["mode"] == "100755" else 0o644
                info.external_attr = (permissions & 0xFFFF) << 16
                bundle.writestr(info, entry["content"])
        archive_hash = sha256(archive.read_bytes())
        checksum_bytes = f"{archive_hash}  {archive.name}\n".encode("ascii")
        checksum.write_bytes(checksum_bytes)
        receipt = {
            "receipt_format": 1,
            "builder_contract": BUILDER_CONTRACT,
            "allowlist_contract": manifest["distribution"]["allowlist_contract"],
            "source_sha": source_sha,
            "manifest_oid": manifest_oid,
            "manifest_sha256": sha256(manifest_bytes),
            "builder_oid": builder_oid,
            "archive_root": f"{ARCHIVE_ROOT}/",
            "entry_count": len(entries),
            "path_list_sha256": path_list_hash,
            "archive_sha256": archive_hash,
            "checksum_sha256": sha256(checksum_bytes),
            "entries": [{key: value for key, value in entry.items() if key != "content"} for entry in entries],
        }
        receipt_bytes = (json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")
        if args.receipt_file:
            receipt_path = args.receipt_file.expanduser().resolve()
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_bytes(receipt_bytes)
        print(archive)
        print(checksum)
        print(receipt_bytes.decode("ascii"), end="")
        return 0
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
