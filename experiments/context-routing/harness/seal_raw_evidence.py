#!/usr/bin/env python3
"""Seal, verify, or report retention status for a repository-external raw run directory."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from _common import atomic_write_json, load_json, sha256_bytes


TOOL_ID = "project-orrery/seal_raw_evidence.py@1"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CLASSIFICATIONS = {"contaminated", "exploratory", "decision_supporting", "release_supporting"}
MANIFEST_KEYS = {
    "schema_version",
    "pilot_id",
    "run_id",
    "classification",
    "sensitivity",
    "created_at",
    "expires_at",
    "source_commit",
    "apparatus_version",
    "sealed_by",
    "files",
    "derived_exports",
}


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed


def _manifest_files(run_root: Path, manifest_path: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    root = run_root.resolve(strict=True)
    for path in sorted(root.rglob("*")):
        if path == manifest_path or not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError(f"raw evidence cannot contain symbolic links: {path}")
        relative = path.relative_to(root).as_posix()
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"unsafe raw evidence path: {relative}")
        content = path.read_bytes()
        files.append({"path": relative, "bytes": len(content), "sha256": sha256_bytes(content)})
    return files


def _validate_manifest_shape(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    if set(manifest) != MANIFEST_KEYS:
        raise ValueError("manifest fields do not match schema v1")
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported manifest schema version")
    if not isinstance(manifest.get("pilot_id"), str) or not manifest["pilot_id"]:
        raise ValueError("pilot_id must be a non-empty string")
    if not isinstance(manifest.get("run_id"), str) or not manifest["run_id"]:
        raise ValueError("run_id must be a non-empty string")
    if manifest.get("classification") not in CLASSIFICATIONS:
        raise ValueError("invalid retention classification")
    if manifest.get("sensitivity") != "restricted":
        raise ValueError("raw evidence sensitivity must be restricted")
    _parse_datetime(str(manifest.get("created_at", "")))
    if manifest.get("expires_at") is not None:
        _parse_datetime(str(manifest["expires_at"]))
    if not COMMIT_PATTERN.fullmatch(str(manifest.get("source_commit", ""))):
        raise ValueError("invalid source commit")
    if not isinstance(manifest.get("apparatus_version"), str) or not manifest["apparatus_version"]:
        raise ValueError("apparatus_version must be a non-empty string")
    if manifest.get("sealed_by") != TOOL_ID:
        raise ValueError("unexpected sealing tool")
    if not isinstance(manifest.get("files"), list) or not isinstance(
        manifest.get("derived_exports"), list
    ):
        raise ValueError("files and derived_exports must be arrays")
    seen_paths: set[str] = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise ValueError("invalid manifest file entry")
        relative = entry.get("path")
        pure = PurePosixPath(str(relative))
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or pure.is_absolute()
            or re.match(r"^[A-Za-z]:", relative)
            or any(part in {"", ".", ".."} or ":" in part for part in pure.parts)
        ):
            raise ValueError("unsafe manifest file path")
        if relative in seen_paths:
            raise ValueError("duplicate manifest file path")
        seen_paths.add(relative)
        if not isinstance(entry.get("bytes"), int) or isinstance(entry.get("bytes"), bool) or entry["bytes"] < 0:
            raise ValueError("invalid manifest file byte count")
        if not SHA256_PATTERN.fullmatch(str(entry.get("sha256", ""))):
            raise ValueError("invalid manifest file hash")
    for entry in manifest["derived_exports"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "reviewed"}:
            raise ValueError("invalid derived export entry")
        export_path = entry.get("path")
        export_pure = PurePosixPath(str(export_path))
        if (
            not isinstance(export_path, str)
            or not export_path
            or "\\" in export_path
            or export_pure.is_absolute()
            or re.match(r"^[A-Za-z]:", export_path)
            or any(part in {"", ".", ".."} or ":" in part for part in export_pure.parts)
        ):
            raise ValueError("invalid derived export path")
        if not SHA256_PATTERN.fullmatch(str(entry.get("sha256", ""))):
            raise ValueError("invalid derived export hash")
        if not isinstance(entry.get("reviewed"), bool):
            raise ValueError("derived export review flag must be boolean")
    return manifest


def seal(
    *,
    run_root: Path,
    manifest_path: Path,
    policy_path: Path,
    pilot_id: str,
    run_id: str,
    classification: str,
    source_commit: str,
    apparatus_version: str,
    created_at: str,
) -> dict[str, Any]:
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise ValueError("source commit must be a 40-character lowercase Git SHA")
    policy = load_json(policy_path)
    classes = policy.get("classifications", {})
    if classification not in classes:
        raise ValueError(f"unknown retention classification: {classification}")
    created = _parse_datetime(created_at)
    retention_days = classes[classification].get("retention_days")
    expires_at = (
        (created + timedelta(days=int(retention_days))).isoformat()
        if retention_days is not None
        else None
    )
    manifest = {
        "schema_version": 1,
        "pilot_id": pilot_id,
        "run_id": run_id,
        "classification": classification,
        "sensitivity": policy.get("default_sensitivity", "restricted"),
        "created_at": created.isoformat(),
        "expires_at": expires_at,
        "source_commit": source_commit,
        "apparatus_version": apparatus_version,
        "sealed_by": TOOL_ID,
        "files": _manifest_files(run_root, manifest_path),
        "derived_exports": [],
    }
    atomic_write_json(manifest_path, manifest)
    return manifest


def verify(manifest_path: Path) -> dict[str, Any]:
    manifest = _validate_manifest_shape(load_json(manifest_path))
    root = manifest_path.parent.resolve(strict=True)
    failures: list[dict[str, Any]] = []
    expected_paths: set[str] = set()
    for entry in manifest.get("files", []):
        relative = str(entry.get("path", ""))
        pure = PurePosixPath(relative)
        if not relative or pure.is_absolute() or ".." in pure.parts:
            failures.append({"path": relative, "reason": "unsafe-path"})
            continue
        expected_paths.add(relative)
        path = root.joinpath(*pure.parts)
        if not path.is_file() or path.is_symlink():
            failures.append({"path": relative, "reason": "missing-or-symlink"})
            continue
        content = path.read_bytes()
        if len(content) != entry.get("bytes"):
            failures.append({"path": relative, "reason": "size-mismatch"})
        if sha256_bytes(content) != entry.get("sha256"):
            failures.append({"path": relative, "reason": "hash-mismatch"})

    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path and not path.is_symlink()
    }
    for unexpected in sorted(actual_paths - expected_paths):
        failures.append({"path": unexpected, "reason": "unsealed-file"})
    return {
        "schema_version": 1,
        "valid": not failures,
        "manifest": manifest_path.name,
        "file_count": len(expected_paths),
        "failures": failures,
    }


def retention_status(manifest_path: Path, at: str) -> dict[str, Any]:
    manifest = _validate_manifest_shape(load_json(manifest_path))
    current = _parse_datetime(at)
    expires_value = manifest.get("expires_at")
    if expires_value is None:
        status = "active"
    else:
        expires = _parse_datetime(str(expires_value))
        status = "expired" if current >= expires else "active"
    return {
        "schema_version": 1,
        "run_id": manifest.get("run_id"),
        "classification": manifest.get("classification"),
        "expires_at": expires_value,
        "status": status,
        "automatic_deletion": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument("--run-root", type=Path, required=True)
    seal_parser.add_argument("--manifest", type=Path)
    seal_parser.add_argument("--policy", type=Path, required=True)
    seal_parser.add_argument("--pilot-id", required=True)
    seal_parser.add_argument("--run-id", required=True)
    seal_parser.add_argument(
        "--classification",
        choices=["contaminated", "exploratory", "decision_supporting", "release_supporting"],
        required=True,
    )
    seal_parser.add_argument("--source-commit", required=True)
    seal_parser.add_argument("--apparatus-version", required=True)
    seal_parser.add_argument("--created-at", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--manifest", type=Path, required=True)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--manifest", type=Path, required=True)
    status_parser.add_argument("--at", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "seal":
            run_root = args.run_root.resolve(strict=True)
            manifest_path = (
                args.manifest.resolve()
                if args.manifest
                else run_root / "raw-evidence-manifest.json"
            )
            try:
                manifest_path.relative_to(run_root)
            except ValueError as exc:
                raise ValueError("manifest must remain inside the raw run root") from exc
            result = seal(
                run_root=run_root,
                manifest_path=manifest_path,
                policy_path=args.policy,
                pilot_id=args.pilot_id,
                run_id=args.run_id,
                classification=args.classification,
                source_commit=args.source_commit,
                apparatus_version=args.apparatus_version,
                created_at=args.created_at,
            )
            exit_code = 0
        elif args.command == "verify":
            result = verify(args.manifest.resolve(strict=True))
            exit_code = 0 if result["valid"] else 1
        else:
            result = retention_status(args.manifest.resolve(strict=True), args.at)
            exit_code = 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"raw-evidence: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
