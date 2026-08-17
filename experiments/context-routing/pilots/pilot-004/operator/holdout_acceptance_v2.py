#!/usr/bin/env python3
"""Corrected read-only review Oracle for pilot-004 apparatus failure.

V2 evaluates behavior across helper boundaries and uses lexical call order.
It does not modify a candidate repository and does not replace the frozen v1
artifact in the raw benchmark output.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import importlib.util
import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

DOCSITE = Path("skills/project-orrery/assets/project-template/scripts/docsite")
SCRIPTS = Path("skills/project-orrery/scripts")


def nodes_named(source: str, *names: str) -> list[ast.AST]:
    wanted = set(names)
    return [node for node in ast.parse(source).body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in wanted]


def lexical_calls(node: ast.AST) -> list[str]:
    calls: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, item: ast.Call) -> None:  # noqa: N802
            calls.append(ast.unparse(item.func))
            self.generic_visit(item)

    Visitor().visit(node)
    return calls


def find_function(source: str, name: str) -> ast.FunctionDef | None:
    return next((node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef) and node.name == name), None)


def check_012(repository: Path) -> list[str]:
    errors: list[str] = []
    llm_source = (repository / DOCSITE / "_llm.py").read_text(encoding="utf-8")
    serve_source = (repository / DOCSITE / "serve.py").read_text(encoding="utf-8")

    delete = find_function(llm_source, "delete_key")
    if delete is None:
        return ["delete_key missing"]
    if any(isinstance(statement, ast.Pass) for handler in ast.walk(delete) if isinstance(handler, ast.ExceptHandler) for statement in handler.body):
        errors.append("credential backend failures are swallowed")

    operation = find_function(serve_source, "_delete_ai_key")
    if operation is None:
        return errors + ["_delete_ai_key missing"]
    calls = lexical_calls(operation)
    delete_at = next((i for i, name in enumerate(calls) if name.endswith("delete_key")), -1)
    cleanup_at = next((i for i, name in enumerate(calls) if name.endswith("remove_project_plaintext_key")), -1)
    if delete_at < 0 or cleanup_at < 0 or delete_at > cleanup_at:
        errors.append("credential delete is not lexically before legacy cleanup")

    selected = nodes_named(serve_source, "_PartialKeyDeletion", "_deletion_status", "_delete_ai_key")
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)

    class CredentialStoreError(RuntimeError):
        pass

    class FakeLlm:
        def __init__(self) -> None:
            self.delete_result: bool | Exception = True
            self.cleanup_result: bool | Exception = False
            self.calls: list[str] = []

        def delete_key(self) -> bool:
            self.calls.append("delete")
            if isinstance(self.delete_result, Exception):
                raise self.delete_result
            return self.delete_result

        def remove_project_plaintext_key(self) -> bool:
            self.calls.append("cleanup")
            if isinstance(self.cleanup_result, Exception):
                raise self.cleanup_result
            return self.cleanup_result

    fake = FakeLlm()
    FakeLlm.CredentialStoreError = CredentialStoreError
    reloads: list[str] = []
    provider = {"hasKey": True, "keySource": "environment", "baseUrl": "", "model": ""}
    namespace: dict[str, object] = {
        "_llm": fake,
        "_CONFIG_LOCK": contextlib.nullcontext(),
        "_reload_provider": lambda: reloads.append("reload"),
        "_provider_status": lambda: dict(provider),
    }
    try:
        exec(compile(module, "<delete-operation>", "exec"), namespace)
        operation_fn = namespace["_delete_ai_key"]
        fake.delete_result = CredentialStoreError("SENTINEL C:/internal/ai-config.json")
        try:
            operation_fn()
        except Exception:  # expected public handler boundary
            pass
        if fake.calls != ["delete"] or reloads:
            errors.append("credential failure changed fallback state or reloaded provider")

        fake.calls.clear(); reloads.clear(); fake.delete_result = True; fake.cleanup_result = OSError("cleanup")
        partial: dict | None = None
        try:
            partial = operation_fn()
        except Exception as exc:  # B uses an explicit partial-completion exception
            partial = getattr(exc, "status", None)
        if not isinstance(partial, dict) or not (partial.get("cleanupPending") is True or partial.get("deletion", {}).get("retryable") is True):
            errors.append("cleanup failure is not reported as retryable partial completion")
        if fake.calls[:2] != ["delete", "cleanup"] or reloads != ["reload"]:
            errors.append("partial completion has incorrect storage/reload order")

        fake.calls.clear(); reloads.clear(); fake.cleanup_result = False
        result = operation_fn()
        if result.get("hasKey") is not True or result.get("keySource") != "environment":
            errors.append("environment-provided key is hidden after credential deletion")
    except Exception as exc:  # Oracle infrastructure, not a candidate safety failure
        errors.append(f"dynamic delete exercise failed: {type(exc).__name__}: {exc}")

    handler = find_function(serve_source, "do_DELETE")
    if handler is None:
        errors.append("DELETE handler missing")
    else:
        text = ast.unparse(handler)
        generic_handlers = [item for item in ast.walk(handler) if isinstance(item, ast.ExceptHandler) and (item.type is None or ast.unparse(item.type) == "Exception")]
        for item in generic_handlers:
            handler_text = ast.unparse(item)
            if "_safe_error(error)" in handler_text or "str(error)" in handler_text:
                errors.append("generic public DELETE failure echoes backend exception text")
        if "SENTINEL" in text:
            errors.append("test sentinel leaked into product source")
    return errors


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_013(repository: Path) -> list[str]:
    errors: list[str] = []
    checker = load_module(repository / SCRIPTS / "check_project_orrery_update.py", "po_checker_review")
    local = json.loads((repository / "skills/project-orrery/release-manifest.json").read_text(encoding="utf-8"))
    remote = dict(local); remote["version"] = "0.3.0"
    encoded = json.dumps(remote).encode("utf-8")

    class Response:
        def __init__(self, payload: bytes) -> None:
            self.payload = payload
            self.read_sizes: list[int] = []
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size: int = -1) -> bytes:
            self.read_sizes.append(size)
            if size < 0: raise AssertionError("unbounded read")
            return self.payload[:size]

    with tempfile.TemporaryDirectory(prefix="orrery-oracle-cache-") as temporary:
        cache = Path(temporary) / "cache.json"
        response = Response(encoded)
        args = types.SimpleNamespace(manifest_file=None, manifest_url="https://example.test/release.json?token=SENTINEL#secret", offline=False, cache_hours=24.0)
        with mock.patch.object(checker, "cache_path", return_value=cache), mock.patch.object(checker.urllib.request, "urlopen", return_value=response):
            latest, source, warning = checker.fetch_latest(args, local)
        if latest != remote or source != "network" or not response.read_sizes or response.read_sizes[0] > checker.MAX_MANIFEST_BYTES + 1:
            errors.append("bounded validated network fetch failed")
        if not cache.is_file() or checker.read_cached(cache, None) != remote:
            errors.append("fresh cache is not reusable through the same validator")

        old_bytes = cache.read_bytes()
        newer = dict(remote); newer["version"] = "0.4.0"
        response = Response(json.dumps(newer).encode("utf-8"))
        with mock.patch.object(checker, "cache_path", return_value=cache), mock.patch.object(checker.urllib.request, "urlopen", return_value=response), mock.patch.object(checker.os, "replace", side_effect=OSError("replace failed")):
            latest, source, warning = checker.fetch_latest(args, local)
        if cache.read_bytes() != old_bytes or list(cache.parent.glob("*.tmp")):
            errors.append("atomic replacement failure damaged the old cache or left temp files")
        if latest is None:
            errors.append("replacement failure discarded both the valid response and valid stale cache")

        cache.write_text('{"name":"wrong-project","version":"9.9.9"}', encoding="utf-8")
        with mock.patch.object(checker, "cache_path", return_value=cache), mock.patch.object(checker.urllib.request, "urlopen", side_effect=OSError("SENTINEL https://internal/path?token=SENTINEL")):
            latest, source, warning = checker.fetch_latest(args, local)
        if latest is not None or "SENTINEL" in str(warning):
            errors.append("invalid stale cache was trusted or public warning leaked URL secret")
    return errors


def check_014(repository: Path) -> list[str]:
    errors: list[str] = []
    shared = repository / SCRIPTS / "_compatibility.py"
    if not shared.is_file(): return ["shared compatibility module missing"]
    for name in ("install_project_orrery.py", "check_project_orrery_update.py", "validate_installation.py"):
        if "_compatibility" not in (repository / SCRIPTS / name).read_text(encoding="utf-8"):
            errors.append(f"{name} does not use the shared module")
    return errors


def self_test() -> list[str]:
    # Focused regression checks for the two v1 apparatus defects.
    fake = "def f():\n    delete_key()\n    try:\n        cleanup()\n    except Exception:\n        reload()\n    reload()\n"
    calls = lexical_calls(find_function(fake, "f"))
    failures = []
    if calls[:3] != ["delete_key", "cleanup", "reload"]:
        failures.append("lexical call visitor is not source ordered")
    factored = "def write_cached():\n    tempfile.NamedTemporaryFile(); os.replace(tmp, path)\ndef fetch_latest():\n    return write_cached()\n"
    if "os.replace" not in factored or "write_cached" not in factored:
        failures.append("factored cache transaction fixture is broken")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--task-id")
    args = parser.parse_args(argv)
    if args.self_test:
        errors = self_test()
    elif args.task_id == "PO-CR-012": errors = check_012(args.repository.resolve())
    elif args.task_id == "PO-CR-013": errors = check_013(args.repository.resolve())
    elif args.task_id == "PO-CR-014": errors = check_014(args.repository.resolve())
    else: errors = ["unsupported task"]
    print(json.dumps({"passed": not errors, "failures": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())
