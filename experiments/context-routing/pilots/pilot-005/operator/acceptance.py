#!/usr/bin/env python3
"""Frozen operator-only acceptance for Pilot 005.

The checker never edits a candidate repository. All target installations,
contract mutations, and link fixtures live in disposable temporary directories.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


INSTALLER = Path("skills/project-orrery/scripts/install_project_orrery.py")
VALIDATOR = Path("skills/project-orrery/scripts/validate_installation.py")
CONTRACT = Path("skills/project-orrery/managed-tools.json")
RELEASE = Path("skills/project-orrery/release-manifest.json")


def run_python(repository: Path, script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(repository / script), *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )


def snapshot_tree(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def create_link(link: Path, target: Path, *, directory: bool) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
        return
    except (OSError, NotImplementedError) as first:
        if os.name != "nt" or not directory:
            raise RuntimeError(f"link fixture unavailable: {first}") from first
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        raise RuntimeError("link fixture unavailable: " + (result.stdout + result.stderr).strip())


def contract_parts(payload: dict[str, Any]) -> tuple[str, int, str, list[str]]:
    format_keys = ("format_version", "schema_version", "managed_tools_contract_format")
    path_keys = ("managed_tools", "paths", "tools")
    format_key = next((key for key in format_keys if key in payload), "")
    path_key = next((key for key in path_keys if key in payload), "")
    value = payload.get(format_key) if format_key else None
    paths = payload.get(path_key) if path_key else None
    if not format_key or not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("managed-tools contract has no positive integer format version")
    if not path_key or not isinstance(paths, list) or not paths:
        raise ValueError("managed-tools contract has no non-empty path list")
    return format_key, value, path_key, paths


def safe_contract_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return False
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in raw_parts):
        return False
    pure = PurePosixPath(value)
    return not pure.is_absolute()


def release_contract_format(payload: dict[str, Any]) -> int | None:
    direct = payload.get("managed_tools_contract_format")
    if isinstance(direct, int) and not isinstance(direct, bool):
        return direct
    compatibility = payload.get("compatibility")
    if isinstance(compatibility, dict):
        nested = compatibility.get("managed_tools_contract_format")
        if isinstance(nested, int) and not isinstance(nested, bool):
            return nested
    return None


def check_025(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    apparatus: list[str] = []
    source = (repository / INSTALLER).read_text(encoding="utf-8")
    if not any(token in source for token in ("is_symlink", "S_ISLNK", "lstat")):
        failures.append("installer has no explicit POSIX symbolic-link detection")
    if not any(token in source for token in ("is_junction", "REPARSE_POINT", "st_file_attributes")):
        failures.append("installer has no explicit Windows junction/reparse-point detection")
    with tempfile.TemporaryDirectory(prefix="orrery-p005-link-") as temporary:
        root = Path(temporary)
        normal = root / "normal"
        installed = run_python(repository, INSTALLER, "--target", str(normal), "--title", "Normal")
        if installed.returncode:
            failures.append("normal fresh installation regressed")

        for dry_run in (False, True):
            external = root / ("external-dry" if dry_run else "external-write")
            external.mkdir()
            (external / "sentinel.txt").write_text("outside must remain unchanged\n", encoding="utf-8")
            target = root / ("target-dry" if dry_run else "target-write")
            target.mkdir()
            try:
                create_link(target / "scripts", external, directory=True)
            except RuntimeError as exc:
                apparatus.append(str(exc))
                break
            before = snapshot_tree(external)
            arguments = ["--target", str(target), "--title", "Linked"]
            if dry_run:
                arguments.append("--dry-run")
            result = run_python(repository, INSTALLER, *arguments)
            if result.returncode == 0:
                failures.append("installer accepted a linked target directory" + (" in dry-run" if dry_run else ""))
            if snapshot_tree(external) != before:
                failures.append("installer changed files beyond the target root through a directory link")

        if not apparatus:
            external_file = root / "external-manifest.json"
            original = '{"outside":"sentinel"}\n'
            external_file.write_text(original, encoding="utf-8")
            target = root / "target-file-link"
            target.mkdir()
            try:
                create_link(target / ".project-orrery.json", external_file, directory=False)
            except RuntimeError:
                # Non-elevated Windows commonly cannot create file symlinks. The
                # directory-junction fixture above still exercises a real
                # reparse-point escape; the source checks retain cross-platform
                # coverage for file symlinks.
                pass
            else:
                result = run_python(repository, INSTALLER, "--target", str(target), "--title", "Linked file")
                if result.returncode == 0:
                    failures.append("installer accepted a linked project manifest")
                if external_file.read_text(encoding="utf-8") != original:
                    failures.append("installer overwrote an external file through a file link")

        if not apparatus and normal.is_dir():
            custom = normal / "scripts" / "docsite" / "serve.py"
            if custom.is_file():
                custom.write_text("# local authored tool\n", encoding="utf-8")
                backup_external = root / "external-backups"
                backup_external.mkdir()
                try:
                    create_link(normal / ".project-orrery-backup", backup_external, directory=True)
                except RuntimeError as exc:
                    apparatus.append(str(exc))
                else:
                    before = snapshot_tree(backup_external)
                    result = run_python(repository, INSTALLER, "--target", str(normal), "--upgrade-tools")
                    if result.returncode == 0:
                        failures.append("installer accepted a linked backup root")
                    if snapshot_tree(backup_external) != before:
                        failures.append("upgrade wrote a backup beyond the target root through a link")
    return failures, apparatus


def copy_skill_repository(repository: Path, destination: Path) -> Path:
    copied = destination / "repository"
    (copied / "skills").mkdir(parents=True)
    shutil.copytree(repository / "skills" / "project-orrery", copied / "skills" / "project-orrery")
    return copied


def check_026(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    apparatus: list[str] = []
    contract_path = repository / CONTRACT
    if not contract_path.is_file():
        return ["managed-tools.json is missing"], apparatus
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if not isinstance(contract, dict):
            raise ValueError("contract is not an object")
        format_key, contract_format, path_key, paths = contract_parts(contract)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"managed-tools contract is invalid: {exc}"], apparatus
    if len(paths) != len(set(paths)) or not all(safe_contract_path(path) for path in paths):
        failures.append("managed-tools contract contains duplicate or unsafe paths")
    for relative in paths:
        if safe_contract_path(relative) and not (repository / "skills/project-orrery/assets/project-template" / relative).is_file():
            failures.append(f"managed tool is not a template file: {relative}")

    try:
        release = json.loads((repository / RELEASE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return failures + [f"release manifest is unreadable: {exc}"], apparatus
    if release_contract_format(release) != contract_format:
        failures.append("release manifest does not declare the managed-tools contract format")

    with tempfile.TemporaryDirectory(prefix="orrery-p005-contract-") as temporary:
        root = Path(temporary)
        target = root / "target"
        installed = run_python(repository, INSTALLER, "--target", str(target), "--title", "Contract")
        if installed.returncode:
            failures.append("normal install with the managed-tools contract failed")
        else:
            try:
                manifest = json.loads((target / ".project-orrery.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"installed manifest is unreadable: {exc}")
            else:
                expected = sorted(paths)
                if manifest.get("managed_tools") != expected:
                    failures.append("installed managed_tools does not equal the shared contract")
                hashes = manifest.get("expected_tool_hashes")
                if not isinstance(hashes, dict) or sorted(hashes) != expected:
                    failures.append("installed expected_tool_hashes keys do not equal the shared contract")
            validated = run_python(repository, VALIDATOR, "--target", str(target))
            if validated.returncode:
                failures.append("validator rejected a normal contract-derived installation")

            drifted = root / "drifted"
            shutil.copytree(target, drifted)
            drift_manifest_path = drifted / ".project-orrery.json"
            drift_manifest = json.loads(drift_manifest_path.read_text(encoding="utf-8"))
            drift_manifest["managed_tools"] = expected[:-1]
            drift_manifest_path.write_text(json.dumps(drift_manifest), encoding="utf-8")
            if run_python(repository, VALIDATOR, "--target", str(drifted)).returncode == 0:
                failures.append("validator accepted a drifted installed managed_tools set")

        bad_contracts: list[tuple[str, dict[str, Any], bool]] = []
        unsafe = dict(contract); unsafe[path_key] = [paths[0], "../escape"]
        duplicate = dict(contract); duplicate[path_key] = [paths[0], paths[0]]
        wrong_type = dict(contract); wrong_type[format_key] = "1"
        bad_contracts.extend((("unsafe", unsafe, False), ("duplicate", duplicate, False), ("wrong-type", wrong_type, False)))
        for label, bad, mismatch_release in bad_contracts:
            case = root / f"bad-{label}"
            copied = copy_skill_repository(repository, case)
            (copied / CONTRACT).write_text(json.dumps(bad), encoding="utf-8")
            bad_target = case / "target"
            install_result = run_python(copied, INSTALLER, "--target", str(bad_target), "--dry-run")
            if install_result.returncode == 0:
                failures.append(f"installer accepted {label} managed-tools contract")
            if bad_target.exists() and any(bad_target.iterdir()):
                failures.append(f"installer wrote target content before rejecting {label} contract")
            validation_target = target if target.exists() else case
            if run_python(copied, VALIDATOR, "--target", str(validation_target)).returncode == 0:
                failures.append(f"validator accepted {label} managed-tools contract")

        mismatch_case = root / "bad-release-format"
        copied = copy_skill_repository(repository, mismatch_case)
        mismatch_release = json.loads((copied / RELEASE).read_text(encoding="utf-8"))
        if "managed_tools_contract_format" in mismatch_release:
            mismatch_release["managed_tools_contract_format"] = contract_format + 1
        else:
            compatibility = mismatch_release.setdefault("compatibility", {})
            compatibility["managed_tools_contract_format"] = contract_format + 1
        (copied / RELEASE).write_text(json.dumps(mismatch_release), encoding="utf-8")
        if run_python(copied, INSTALLER, "--target", str(mismatch_case / "target"), "--dry-run").returncode == 0:
            failures.append("installer accepted release/managed-tools contract format mismatch")
        validation_target = target if target.exists() else mismatch_case
        if run_python(copied, VALIDATOR, "--target", str(validation_target)).returncode == 0:
            failures.append("validator accepted release/managed-tools contract format mismatch")
    return failures, apparatus


def self_test() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    apparatus: list[str] = []
    for unsafe in ("../x", "/x", "C:/x", "a\\b", "a/./b", "a//b", "a:b"):
        if safe_contract_path(unsafe):
            failures.append(f"unsafe path helper accepted {unsafe!r}")
    for safe in ("start-docsite.bat", "scripts/docsite/serve.py"):
        if not safe_contract_path(safe):
            failures.append(f"safe path helper rejected {safe!r}")
    with tempfile.TemporaryDirectory(prefix="orrery-p005-link-selftest-") as temporary:
        root = Path(temporary)
        target = root / "target"; target.mkdir()
        link = root / "link"
        try:
            create_link(link, target, directory=True)
        except RuntimeError as exc:
            apparatus.append(str(exc))
        else:
            if not link.exists():
                failures.append("link fixture was created but is not traversable")
    return failures, apparatus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--task-id", choices=("PO-CR-025", "PO-CR-026"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            failures, apparatus = self_test()
        elif args.repository and args.task_id == "PO-CR-025":
            failures, apparatus = check_025(args.repository.resolve(strict=True))
        elif args.repository and args.task_id == "PO-CR-026":
            failures, apparatus = check_026(args.repository.resolve(strict=True))
        else:
            parser.error("provide --self-test or --repository with --task-id")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        failures, apparatus = [], [f"oracle exception: {type(exc).__name__}: {exc}"]
    result = {
        "schema_version": 1,
        "passed": not failures and not apparatus,
        "task_failures": failures,
        "apparatus_errors": apparatus,
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 2 if apparatus else (1 if failures else 0)


if __name__ == "__main__":
    raise SystemExit(main())
