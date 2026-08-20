"""Canonical author-document template access and token rendering."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator


EXCLUDED_TEMPLATE_PARTS = {"__pycache__", ".DS_Store"}
EXCLUDED_TEMPLATE_SUFFIXES = {".pyc", ".pyo"}


def authority_template_root() -> Path:
    return Path(__file__).resolve().parent / "templates" / "authority"


def iter_authority_assets(root: Path | None = None) -> Iterator[tuple[Path, Path]]:
    source_root = root or authority_template_root()
    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        relative = source.relative_to(source_root)
        if any(part in EXCLUDED_TEMPLATE_PARTS for part in relative.parts):
            continue
        if source.suffix in EXCLUDED_TEMPLATE_SUFFIXES:
            continue
        yield relative, source


def rendered_content(raw: bytes, replacements: dict[str, str]) -> bytes:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    for token, value in replacements.items():
        text = text.replace("{{" + token + "}}", value)
    return text.encode("utf-8")


def rendered_bytes(source: Path, replacements: dict[str, str]) -> bytes:
    return rendered_content(source.read_bytes(), replacements)
