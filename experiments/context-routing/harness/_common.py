from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


FORBIDDEN_REPOSITORY_PARTS = {".git", ".benchmark", ".codex"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, encoded)
    finally:
        os.close(descriptor)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def normalize_repository_path(root: Path, raw_path: str) -> tuple[str, Path]:
    candidate_text = raw_path.strip().replace("\\", "/")
    pure = PurePosixPath(candidate_text)
    if (
        not candidate_text
        or pure.is_absolute()
        or re.match(r"^[A-Za-z]:", candidate_text)
        or any(part in {"", ".", ".."} or ":" in part for part in pure.parts)
    ):
        raise ValueError(f"path must be a normalized repository-relative path: {raw_path!r}")
    if any(part.lower() in FORBIDDEN_REPOSITORY_PARTS for part in pure.parts):
        raise ValueError(f"path is outside the benchmark evidence surface: {raw_path!r}")

    root = root.resolve(strict=True)
    candidate = root.joinpath(*pure.parts)
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symbolic links are not allowed in evidence reads: {raw_path!r}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {raw_path!r}") from exc
    return pure.as_posix(), candidate


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    if not path.is_file():
        return values
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            values.append(value)
    return values
