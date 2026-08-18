#!/usr/bin/env python3
"""Independent acceptance Oracle for Pilot 007."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


PACKAGER = Path("scripts/package_release.py")
EXPORTER = Path("experiments/context-routing/harness/export_sanitized_evidence.py")
SEALER = Path("experiments/context-routing/harness/seal_raw_evidence.py")
RETENTION = Path("experiments/context-routing/harness/raw-evidence-retention-policy.json")
TEXT_SUFFIXES = {".bat", ".css", ".html", ".js", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"gh[opsu]_[A-Za-z0-9]{8,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*[^\s,;]+"),
)


def run_python(repository: Path, script: Path, *arguments: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(repository / script), *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def changed_paths(repository: Path) -> set[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=repository,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        raise RuntimeError("cannot inspect candidate changed paths")
    paths: set[str] = set()
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        value = entry[3:] if len(entry) > 3 else entry
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        if not value.startswith(".benchmark/"):
            paths.add(value.replace("\\", "/"))
    return paths


def require_changed(repository: Path, required: set[str], failures: list[str]) -> None:
    missing = sorted(required - changed_paths(repository))
    if missing:
        failures.append("required implementation or regression files were not changed: " + ", ".join(missing))


def normalize_copy(root: Path, newline: bytes, *, odd_mode: bool) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        path.write_bytes(canonical.replace(b"\n", newline))
        os.utime(path, (1_700_000_000 if odd_mode else 1_600_000_000,) * 2)
        try:
            path.chmod(0o777 if odd_mode else 0o600)
        except OSError:
            pass


def build_fixture(repository: Path, destination: Path, newline: bytes, odd_mode: bool) -> Path:
    (destination / "scripts").mkdir(parents=True)
    (destination / "skills").mkdir()
    shutil.copy2(repository / PACKAGER, destination / PACKAGER)
    shutil.copytree(repository / "skills/project-orrery", destination / "skills/project-orrery")
    normalize_copy(destination / "skills/project-orrery", newline, odd_mode=odd_mode)
    return destination


def check_027(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    apparatus: list[str] = []
    source_path = repository / PACKAGER
    if not source_path.is_file():
        return ["release packager is missing"], apparatus
    require_changed(repository, {"scripts/package_release.py", "tests/test_project_orrery.py"}, failures)
    source = source_path.read_text(encoding="utf-8")
    if re.search(r"\bos\.access\s*\(", source):
        failures.append("archive mode still depends on host os.access")
    with tempfile.TemporaryDirectory(prefix="orrery-p007-package-") as temporary:
        root = Path(temporary)
        archives: list[Path] = []
        for name, newline, odd_mode in (("lf", b"\n", False), ("crlf", b"\r\n", True)):
            case = build_fixture(repository, root / name, newline, odd_mode)
            result = run_python(case, PACKAGER, "--output-dir", str(case / "dist"))
            if result.returncode:
                failures.append(f"packager failed for {name} fixture: {(result.stdout + result.stderr).strip()}")
                continue
            found = list((case / "dist").glob("*.zip"))
            if len(found) != 1:
                failures.append(f"packager produced {len(found)} zip files for {name} fixture")
                continue
            archives.append(found[0])
        if len(archives) == 2:
            if archives[0].read_bytes() != archives[1].read_bytes():
                failures.append("LF/CRLF, mtime, or mode variants did not produce identical zip bytes")
            with zipfile.ZipFile(archives[0]) as bundle:
                infos = bundle.infolist()
                if [info.filename for info in infos] != sorted(info.filename for info in infos):
                    failures.append("zip entries are not sorted")
                if any(info.date_time != (2020, 1, 1, 0, 0, 0) for info in infos):
                    failures.append("zip timestamps are not fixed")
                if any((info.external_attr >> 16) & 0o777 not in {0o644, 0o755} for info in infos):
                    failures.append("zip modes are outside the deterministic 0644/0755 policy")
    return failures, apparatus


def contains_sensitive_text(value: Any) -> bool:
    encoded = json.dumps(value, ensure_ascii=False)
    forbidden = ("provider says secret body", "source code must not escape", "D:\\\\private", "C:\\\\Users")
    return any(item in encoded for item in forbidden) or any(pattern.search(encoded) for pattern in SECRET_PATTERNS)


def check_028(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    apparatus: list[str] = []
    if not (repository / EXPORTER).is_file():
        return ["R1 exporter is missing"], apparatus
    require_changed(
        repository,
        {
            "experiments/context-routing/harness/export_sanitized_evidence.py",
            "experiments/context-routing/harness/README.md",
            "tests/test_context_routing_h2.py",
        },
        failures,
    )
    with tempfile.TemporaryDirectory(prefix="orrery-p007-r1-") as temporary:
        root = Path(temporary)
        run_root = root / "raw"; run_root.mkdir()
        (run_root / "events.jsonl").write_text(
            '{"message":"provider says secret body","token":"sk-supersecret123","path":"D:\\\\private\\\\repo"}\n',
            encoding="utf-8",
        )
        (run_root / "source.txt").write_text("source code must not escape\n", encoding="utf-8")
        manifest = run_root / "raw-evidence-manifest.json"
        sealed = run_python(
            repository,
            SEALER,
            "seal", "--run-root", str(run_root), "--manifest", str(manifest),
            "--policy", str(repository / RETENTION), "--pilot-id", "pilot-fixture",
            "--run-id", "secret-run", "--classification", "decision_supporting",
            "--source-commit", "a" * 40, "--apparatus-version", "fixture-v1",
            "--created-at", "2026-08-18T00:00:00+08:00",
        )
        if sealed.returncode:
            return failures, ["cannot seal Oracle fixture: " + sealed.stdout + sealed.stderr]
        before = snapshot(run_root)
        output_a = root / "r1-a.json"
        output_b = root / "r1-b.json"
        first = run_python(repository, EXPORTER, "--manifest", str(manifest), "--output", str(output_a))
        second = run_python(repository, EXPORTER, "--manifest", str(manifest), "--output", str(output_b))
        if first.returncode or second.returncode or not output_a.is_file() or not output_b.is_file():
            failures.append("valid sealed R0 could not be exported twice")
        else:
            if output_a.read_bytes() != output_b.read_bytes():
                failures.append("R1 export is not byte-for-byte deterministic")
            try:
                payload = json.loads(output_a.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(f"R1 output is not JSON: {exc}")
            else:
                encoded = json.dumps(payload, ensure_ascii=False)
                for required in ("pilot-fixture", "secret-run", "decision_supporting", "a" * 40, "events.jsonl", sha256(manifest)):
                    if required not in encoded:
                        failures.append(f"R1 output omitted required inventory or identity value: {required}")
                if contains_sensitive_text(payload):
                    failures.append("R1 output leaked secret, body text, or absolute path")
        if snapshot(run_root) != before:
            failures.append("exporter mutated sealed R0 evidence")
        inside = run_python(repository, EXPORTER, "--manifest", str(manifest), "--output", str(run_root / "unsafe.json"))
        if inside.returncode == 0 or (run_root / "unsafe.json").exists():
            failures.append("exporter accepted an output path inside sealed R0")
        original = (run_root / "events.jsonl").read_text(encoding="utf-8")
        (run_root / "events.jsonl").write_text(original + "tamper\n", encoding="utf-8")
        tampered = run_python(repository, EXPORTER, "--manifest", str(manifest), "--output", str(root / "tampered.json"))
        if tampered.returncode == 0:
            failures.append("exporter accepted a tampered R0 manifest inventory")
    return failures, apparatus


def check_029(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    apparatus: list[str] = []
    require_changed(repository, {"README.md", "README.zh-CN.md"}, failures)
    documents = ((repository / "README.md", False), (repository / "README.zh-CN.md", True))
    for path, chinese in documents:
        if not path.is_file():
            failures.append(f"missing {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in ("npm.cmd", r"D:\Tools\Codex", "codex.cmd", "--version"):
            if token not in text:
                failures.append(f"{path.name} does not contain {token}")
        if re.search(r"(?is)Set-ExecutionPolicy.{0,80}(Unrestricted|Bypass)", text):
            failures.append(f"{path.name} recommends weakening ExecutionPolicy")
        if chinese and not re.search(r"[\u4e00-\u9fff]", text):
            failures.append("Chinese README has no Chinese explanation")
        if not chinese and "ExecutionPolicy" not in text:
            failures.append("English README does not explain the ExecutionPolicy case")
        if "skills/project-orrery" not in text or "--require-integrated" not in text:
            failures.append(f"{path.name} lost the existing Skill adoption boundary")
    return failures, apparatus


def self_test() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    safe = {"inventory": [{"path": "events.jsonl", "bytes": 12, "sha256": "a" * 64}]}
    unsafe = {"message": "provider says secret body", "token": "sk-supersecret123", "path": r"D:\private"}
    if contains_sensitive_text(safe):
        failures.append("sensitive-text helper rejected safe inventory")
    if not contains_sensitive_text(unsafe):
        failures.append("sensitive-text helper missed fixture secret")
    return failures, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--task-id", choices=("PO-CR-027", "PO-CR-028", "PO-CR-029"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            failures, apparatus = self_test()
        elif args.repository and args.task_id:
            repository = args.repository.resolve(strict=True)
            failures, apparatus = {
                "PO-CR-027": check_027,
                "PO-CR-028": check_028,
                "PO-CR-029": check_029,
            }[args.task_id](repository)
        else:
            parser.error("provide --self-test or --repository with --task-id")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        failures, apparatus = [], [f"oracle exception: {type(exc).__name__}: {exc}"]
    result = {"schema_version": 1, "passed": not failures and not apparatus, "task_failures": failures, "apparatus_errors": apparatus}
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 2 if apparatus else (1 if failures else 0)


if __name__ == "__main__":
    raise SystemExit(main())
