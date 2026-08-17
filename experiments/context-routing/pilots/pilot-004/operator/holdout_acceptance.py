#!/usr/bin/env python3
"""Operator-only holdout acceptance for Project Orrery pilot-004.

This file is copied only to the output root's _operator directory.  It must
never be present in an Agent target repository or prompt.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path


DOCSITE = Path("skills/project-orrery/assets/project-template/scripts/docsite")
SCRIPTS = Path("skills/project-orrery/scripts")


def function_node(source: str, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    tree = ast.parse(source)
    return next((node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name), None)


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def calls_in_order(node: ast.AST) -> list[str]:
    return [dotted_name(item.func) for item in ast.walk(node) if isinstance(item, ast.Call)]


def check_delete_sources(llm_source: str, serve_source: str) -> list[str]:
    errors: list[str] = []
    delete = function_node(llm_source, "delete_key")
    if delete is None:
        return ["_llm.delete_key is missing"]
    for handler in (item for item in ast.walk(delete) if isinstance(item, ast.ExceptHandler)):
        if any(isinstance(statement, ast.Pass) for statement in handler.body):
            errors.append("delete_key still swallows a credential-backend failure")

    operation = function_node(serve_source, "_delete_ai_key")
    if operation is None:
        errors.append("serve._delete_ai_key is missing")
    else:
        calls = calls_in_order(operation)
        delete_at = next((i for i, name in enumerate(calls) if name.endswith("delete_key")), None)
        cleanup_at = next((i for i, name in enumerate(calls) if name.endswith("remove_project_plaintext_key")), None)
        reload_at = next((i for i, name in enumerate(calls) if name.endswith("_reload_provider")), None)
        if delete_at is None or cleanup_at is None:
            errors.append("credential deletion and legacy cleanup are not both visible in the transaction")
        elif delete_at > cleanup_at:
            errors.append("legacy fallback is modified before credential deletion succeeds")
        if reload_at is None or (cleanup_at is not None and reload_at < cleanup_at):
            errors.append("provider reload does not occur after storage cleanup")

    safe = function_node(serve_source, "_safe_error")
    if safe is None:
        errors.append("serve._safe_error is missing")
    else:
        module = ast.Module(body=[safe], type_ignores=[])
        ast.fix_missing_locations(module)
        namespace: dict[str, object] = {}
        try:
            exec(compile(module, "<safe-error>", "exec"), namespace)
            sentinel = "SENTINEL-SECRET C:/internal/project/ai-config.json"
            rendered = str(namespace["_safe_error"](RuntimeError(sentinel)))
            if "SENTINEL-SECRET" in rendered or "ai-config.json" in rendered:
                errors.append("public error sanitizer exposes backend secret or internal path")
        except Exception as exc:  # noqa: BLE001 - an Oracle infrastructure failure is explicit
            errors.append(f"cannot exercise public error sanitizer: {type(exc).__name__}: {exc}")
    return errors


def check_cache_source(source: str) -> list[str]:
    errors: list[str] = []
    fetch = function_node(source, "fetch_latest")
    cached = function_node(source, "read_cached")
    if fetch is None or cached is None:
        return ["fetch_latest/read_cached API is missing"]
    fetch_text = ast.unparse(fetch)
    read_calls = [item for item in ast.walk(fetch) if isinstance(item, ast.Call) and dotted_name(item.func).endswith(".read")]
    if not read_calls or any(not call.args for call in read_calls):
        errors.append("remote response is read without an explicit bound")
    if "replace" not in fetch_text or not any(token in fetch_text.lower() for token in ("temp", "tmp")):
        errors.append("cache update is not a temporary-file plus atomic-replace transaction")
    cached_calls = calls_in_order(cached)
    if not any(name.endswith(("read_manifest", "validate_manifest", "validate_release_manifest")) for name in cached_calls):
        errors.append("stale cache does not pass through the release-manifest validator")
    whole = source.lower()
    if not any(token in whole for token in ("urlsplit", "urlparse", "redact", "sanitize")):
        errors.append("no URL/error redaction boundary is present")
    return errors


def check_shared_compatibility(repository: Path) -> list[str]:
    errors: list[str] = []
    shared = repository / SCRIPTS / "_compatibility.py"
    if not shared.is_file():
        return ["shared compatibility module _compatibility.py was not created"]
    consumers = [
        repository / SCRIPTS / "install_project_orrery.py",
        repository / SCRIPTS / "check_project_orrery_update.py",
        repository / SCRIPTS / "validate_installation.py",
    ]
    for path in consumers:
        text = path.read_text(encoding="utf-8")
        if "_compatibility" not in text:
            errors.append(f"{path.name} does not consume the shared compatibility module")

    installer = consumers[0].read_text(encoding="utf-8")
    preflight_at = min((index for token in ("compatib", "preflight") if (index := installer.lower().find(token)) >= 0), default=-1)
    side_effects = [index for token in ("target.mkdir", "backup_file(", "write_text(", "write_bytes(") if (index := installer.find(token)) >= 0]
    if preflight_at < 0 or (side_effects and preflight_at > min(side_effects)):
        errors.append("installer compatibility preflight is not before its first filesystem side effect")

    with subprocess.Popen(
        [sys.executable, "-c", "import importlib.util,sys; p=sys.argv[1]; s=importlib.util.spec_from_file_location('po_compat',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)", str(shared)],
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        stdout, stderr = process.communicate(timeout=20)
        if process.returncode != 0:
            errors.append(f"shared module import failed: {stderr.strip()}")
        if stdout.strip():
            errors.append("shared module import produced CLI output")
    return errors


def self_test() -> list[str]:
    failures: list[str] = []
    unsafe_llm = "def delete_key():\n    try:\n        backend()\n    except Exception:\n        pass\n"
    unsafe_serve = "def _safe_error(error, secret=''):\n    return str(error)\ndef _delete_ai_key():\n    _llm.remove_project_plaintext_key(); _llm.delete_key(); _reload_provider()\n"
    safe_llm = "def delete_key():\n    try:\n        backend()\n    except PasswordDeleteError:\n        return False\n"
    safe_serve = "def _safe_error(error, secret=''):\n    return 'credential operation failed'\ndef _delete_ai_key():\n    _llm.delete_key(); _llm.remove_project_plaintext_key(); _reload_provider()\n"
    if not check_delete_sources(unsafe_llm, unsafe_serve):
        failures.append("PO-CR-012 unsafe fixture was not rejected")
    if check_delete_sources(safe_llm, safe_serve):
        failures.append("PO-CR-012 minimal safe fixture was rejected")

    unsafe_cache = "def read_cached(path, age):\n    return json.loads(path.read_text())\ndef fetch_latest(args, local):\n    data=response.read(); path.write_text(data); return data,'remote',str(error)\n"
    safe_cache = "from urllib.parse import urlsplit\ndef read_manifest(path): return {}\ndef read_cached(path, age): return read_manifest(path)\ndef fetch_latest(args, local):\n    data=response.read(MAXIMUM+1); temp_path.write_text(data); temp_path.replace(path); return data,'remote',sanitize(error)\n"
    if not check_cache_source(unsafe_cache):
        failures.append("PO-CR-013 unsafe fixture was not rejected")
    if check_cache_source(safe_cache):
        failures.append("PO-CR-013 minimal safe fixture was rejected")
    return failures


def evaluate(repository: Path, task_id: str) -> list[str]:
    if task_id == "PO-CR-012":
        return check_delete_sources(
            (repository / DOCSITE / "_llm.py").read_text(encoding="utf-8"),
            (repository / DOCSITE / "serve.py").read_text(encoding="utf-8"),
        )
    if task_id == "PO-CR-013":
        return check_cache_source((repository / SCRIPTS / "check_project_orrery_update.py").read_text(encoding="utf-8"))
    if task_id == "PO-CR-014":
        return check_shared_compatibility(repository)
    return [f"unsupported task: {task_id}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--task-id")
    args = parser.parse_args(argv)
    failures = self_test() if args.self_test else evaluate(args.repository.resolve(), args.task_id)
    print(json.dumps({"passed": not failures, "failures": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
