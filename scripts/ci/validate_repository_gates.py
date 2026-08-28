from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

from _common import CIValidationError, ROOT


LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FORBIDDEN_NAMES = {"ai-config.json", ".doccache.json", ".port"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def repository_paths(root: Path = ROOT) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise CIValidationError(result.stderr.decode("utf-8", errors="replace").strip())
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]


def validate_forbidden_artifacts(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        lowered_parts = [part.lower() for part in path.parts]
        if path.name.lower() in FORBIDDEN_NAMES:
            errors.append(f"tracked local runtime artifact: {path.as_posix()}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or "__pycache__" in lowered_parts:
            errors.append(f"tracked Python cache artifact: {path.as_posix()}")
        if len(lowered_parts) >= 2 and lowered_parts[0] == "docs" and lowered_parts[1] == "_site":
            errors.append(f"tracked generated docsite artifact: {path.as_posix()}")
    return errors


def _link_target(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1]
    value = value.split(maxsplit=1)[0]
    if not value or value.startswith(("#", "http://", "https://", "mailto:", "data:")):
        return None
    return unquote(value.split("#", 1)[0].split("?", 1)[0])


def validate_markdown_links(root: Path, paths: list[Path]) -> tuple[list[str], int, int]:
    errors: list[str] = []
    checked_files = 0
    checked_links = 0
    for relative in paths:
        if relative.suffix.lower() != ".md":
            continue
        if relative.parts[:3] == ("tests", "fixtures", "documentation-governance"):
            continue
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"cannot read Markdown {relative.as_posix()}: {exc}")
            continue
        checked_files += 1
        for raw in LINK_RE.findall(text):
            target = _link_target(raw)
            if target is None:
                continue
            checked_links += 1
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"Markdown link escapes repository: {relative.as_posix()} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"missing Markdown link: {relative.as_posix()} -> {target}")
    return errors, checked_files, checked_links


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository gates outside unittest shards")
    parser.parse_args()
    try:
        paths = repository_paths()
        errors = validate_forbidden_artifacts(paths)
        link_errors, markdown_files, links = validate_markdown_links(ROOT, paths)
        errors.extend(link_errors)
        if errors:
            print("FAIL repository gates:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(
            f"PASS repository gates: {len(paths)} tracked/untracked repository paths, {markdown_files} Markdown files, "
            f"{links} local links, no forbidden runtime/generated artifacts"
        )
        return 0
    except CIValidationError as exc:
        print(f"FAIL repository gates: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
