#!/usr/bin/env python3
"""Return repository paths or text slices while emitting Harness-owned audit evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from _common import (
    append_jsonl,
    atomic_write_json,
    load_json,
    normalize_repository_path,
    now_iso,
    sha256_bytes,
)


REASON_CODES = {
    "dependency-found",
    "missing-authority",
    "security-boundary",
    "conflicting-facts",
    "validation-failure",
    "acceptance-gap",
}
EXCLUDED_ENUMERATION_PARTS = {".git", ".benchmark", ".codex", "__pycache__"}


def _environment_path(name: str) -> Path:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be set by the benchmark Harness")
    return Path(value).resolve()


def _repository_root() -> Path:
    configured = os.environ.get("ORRERY_BENCHMARK_REPO_ROOT", "").strip()
    return Path(configured).resolve(strict=True) if configured else Path.cwd().resolve(strict=True)


def _range_is_covered(ranges: list[list[int | None]], start: int, end: int | None) -> bool:
    requested_end = end if end is not None else sys.maxsize
    for prior_start, prior_end in ranges:
        covered_end = prior_end if prior_end is not None else sys.maxsize
        if prior_start <= start and covered_end >= requested_end:
            return True
    return False


def _register_read(path: str, start: int, end: int | None, reason: str | None) -> dict[str, Any]:
    state_path = _environment_path("ORRERY_ACCESS_STATE")
    state = load_json(state_path, {"schema_version": 1, "phase": "prewrite", "read_ranges": {}})
    ranges_by_path = state.setdefault("read_ranges", {})
    existing_paths = list(ranges_by_path)
    prior_ranges = ranges_by_path.get(path, [])
    expands_range = bool(prior_ranges) and not _range_is_covered(prior_ranges, start, end)
    exceeds_initial_budget = path not in ranges_by_path and len(existing_paths) >= 2
    require_reason = bool(state.get("require_expansion_reason", True))
    if require_reason and (expands_range or exceeds_initial_budget) and reason not in REASON_CODES:
        raise ValueError(
            "this read expands the initial aperture; pass --reason with an approved reason code"
        )
    if reason is not None and reason not in REASON_CODES:
        raise ValueError(f"unsupported reason code: {reason}")
    ranges_by_path.setdefault(path, []).append([start, end])
    atomic_write_json(state_path, state)
    return {
        "expansion": expands_range or exceeds_initial_budget,
        "expansion_reason_required": require_reason,
        "initial_unique_paths_before": len(existing_paths),
    }


def list_paths(root: Path, audit_path: Path, pattern: str | None, limit: int) -> int:
    if limit < 1 or limit > 5000:
        raise ValueError("--limit must be between 1 and 5000")
    paths: list[str] = []
    iterator = root.rglob(pattern or "*")
    for candidate in iterator:
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(root)
        if any(part in EXCLUDED_ENUMERATION_PARTS for part in relative.parts):
            continue
        paths.append(relative.as_posix())
        if len(paths) >= limit:
            break
    paths.sort()
    append_jsonl(
        audit_path,
        {
            "schema_version": 1,
            "timestamp": now_iso(),
            "request_id": str(uuid.uuid4()),
            "operation": "enumerate",
            "pattern": pattern,
            "result_count": len(paths),
            "observed_by": "tool_wrapper",
        },
    )
    sys.stdout.write("\n".join(paths))
    if paths:
        sys.stdout.write("\n")
    return 0


def read_slice(
    root: Path,
    audit_path: Path,
    raw_path: str,
    start: int,
    end: int | None,
    reason: str | None,
) -> int:
    if start < 1:
        raise ValueError("--start must be at least 1")
    if end is not None and end < start:
        raise ValueError("--end cannot be smaller than --start")
    normalized, path = normalize_repository_path(root, raw_path)
    if not path.is_file():
        raise FileNotFoundError(normalized)

    source = path.read_bytes()
    if b"\0" in source:
        raise ValueError("binary files are not supported by the text evidence proxy")
    text = source.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)
    selected = "".join(lines[start - 1 : end])
    returned = selected.encode("utf-8")
    aperture = _register_read(normalized, start, end, reason)
    request_id = str(uuid.uuid4())
    metadata = {
        "request_id": request_id,
        "path": normalized,
        "start_line": start,
        "end_line": end,
        "reason_code": reason,
        "source_sha256": sha256_bytes(source),
        "returned_sha256": sha256_bytes(returned),
        "returned_bytes": len(returned),
    }
    append_jsonl(
        audit_path,
        {
            "schema_version": 1,
            "timestamp": now_iso(),
            "operation": "read",
            "observed_by": "tool_wrapper",
            **metadata,
            **aperture,
        },
    )
    # Write bytes directly. On Windows, TextIO newline translation would turn
    # source CRLF into CRCRLF and break the independently recorded content hash.
    response = (
        "ORRERY_READ_BEGIN "
        + json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        + selected
        + f"\nORRERY_READ_END {request_id}\n"
    )
    sys.stdout.buffer.write(response.encode("utf-8"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list", help="enumerate repository paths without content")
    list_parser.add_argument("--glob", dest="pattern")
    list_parser.add_argument("--limit", type=int, default=1000)
    read_parser = subparsers.add_parser("read", help="return a UTF-8 text line range")
    read_parser.add_argument("--path", required=True)
    read_parser.add_argument("--start", type=int, default=1)
    read_parser.add_argument("--end", type=int)
    read_parser.add_argument("--reason", choices=sorted(REASON_CODES))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = _repository_root()
        audit_path = _environment_path("ORRERY_PROXY_AUDIT_LOG")
        if args.command == "list":
            return list_paths(root, audit_path, args.pattern, args.limit)
        return read_slice(root, audit_path, args.path, args.start, args.end, args.reason)
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(f"context-read-proxy: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
