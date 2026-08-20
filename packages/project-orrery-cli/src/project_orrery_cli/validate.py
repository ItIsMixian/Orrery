"""Validate an installation without calling a model, network, or Agent runtime."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from project_orrery_core import REQUIRED_SCAFFOLD_FILES

from .context import CliContext, repository_context


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an installed Project Orrery scaffold")
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--build", action="store_true", help="Build docs/_site/index.html; requires dependencies")
    parser.add_argument("--require-integrated", action="store_true", help="Fail unless the authority chain appears integrated")
    return parser.parse_args(argv)


def run(args: argparse.Namespace, context: CliContext) -> int:
    root = args.target.expanduser().resolve()
    problems: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED_SCAFFOLD_FILES:
        if not (root / relative).is_file():
            problems.append(f"missing required file: {relative}")

    for script in sorted((root / "scripts" / "docsite").glob("*.py")):
        try:
            source = script.read_text(encoding="utf-8")
            compile(source, str(script), "exec")
        except (OSError, SyntaxError) as exc:
            problems.append(f"Python compile failed: {script.name}: {exc}")

    for path in [root / "AGENTS.md", *sorted((root / "docs").rglob("*.md"))]:
        if path.is_file() and re.search(r"\{\{[A-Z0-9_]+\}\}", path.read_text(encoding="utf-8")):
            problems.append(f"unresolved template token: {path.relative_to(root).as_posix()}")

    gitignore = root / ".gitignore"
    safety_entries = (
        "docs/_site/",
        "scripts/docsite/.doccache.json",
        "scripts/docsite/.port",
        "ai-config.json",
        ".project-orrery-backup/",
    )
    ignored = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    missing_ignores = [entry for entry in safety_entries if entry not in ignored]
    if missing_ignores:
        warnings.append(".gitignore is missing safety entries: " + ", ".join(missing_ignores))

    manifest_path = root / ".project-orrery.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("toolchain_status") == "mixed":
                warnings.append("viewer toolchain is marked partial/mixed")
            legacy_manifest = manifest.get("name") == "project-orrery" and "manifest_format" not in manifest
            manifest_format = 1 if legacy_manifest else manifest.get("manifest_format")
            schema = manifest.get("document_schema", 1 if legacy_manifest else None)
            if legacy_manifest:
                warnings.append("legacy v0.1 project manifest detected; rerun the current installer to record version dimensions")
            if manifest_format != context.release.project_manifest_format:
                problems.append(
                    "unsupported .project-orrery.json format: "
                    f"{manifest_format!r}; expected {context.release.project_manifest_format}"
                )
            schema_rule = context.release.compatibility["document_schema"]
            if not isinstance(schema, int) or not schema_rule["minimum"] <= schema <= schema_rule["maximum"]:
                problems.append(
                    f"unsupported document schema: {schema!r}; supported range is "
                    f"{schema_rule['minimum']}..{schema_rule['maximum']}"
                )
            if manifest.get("toolchain_status") == "current" and not manifest.get("toolchain_version"):
                warnings.append("current viewer toolchain has no recorded toolchain_version")
        except json.JSONDecodeError:
            warnings.append(".project-orrery.json is not valid JSON")
    else:
        problems.append("missing required file: .project-orrery.json")

    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").is_file() else ""
    progress_text = (root / "docs" / "PROGRESS.md").read_text(encoding="utf-8") if (root / "docs" / "PROGRESS.md").is_file() else ""
    accepted_adr = False
    for adr in (root / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md"):
        if adr.name.startswith("0000-"):
            continue
        if re.search(r"(?im)^Status\s*:\s*Accepted\b", adr.read_text(encoding="utf-8")):
            accepted_adr = True
            break
    entrance_mapped = all(token in agents_text for token in ("docs/HANDOFF.md", "docs/PROGRESS.md", "docs/state/"))
    pending_marker = "migration pending" in progress_text.lower() or "迁移待" in progress_text
    integrated = accepted_adr and entrance_mapped and not pending_marker
    if not integrated:
        warnings.append("authority migration is pending; scaffold presence is not formal adoption")
        if args.require_integrated:
            problems.append("authority chain is not integrated: add an accepted project ADR and update AGENTS/PROGRESS")

    if args.build and not problems:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "scripts/docsite/build_docsite.py"],
            cwd=root,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode:
            problems.append("static build failed:\n" + (result.stdout + result.stderr).strip())
        elif not (root / "docs" / "_site" / "index.html").is_file():
            problems.append("static build reported success but docs/_site/index.html is missing")

    if problems:
        print("Project Orrery validation FAILED")
        for problem in problems:
            print(f"- {problem}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        return 1

    suffix = " + static build" if args.build else ""
    print(f"Project Orrery scaffold structure valid{suffix}: {root}")
    print("Authority status: integrated candidate" if integrated else "Authority status: migration pending")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


def main(argv: list[str] | None = None, *, context: CliContext | None = None) -> int:
    return run(parse_args(argv), context or repository_context())


if __name__ == "__main__":
    raise SystemExit(main())
