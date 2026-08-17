#!/usr/bin/env python3
"""Independent security acceptance checks for pilot-003 candidate repositories.

The checks execute from the operator packet, not from Agent-authored tests. They
never use a real credential store or network connection and redirect project
configuration writes into temporary directories.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import os
import sys
import tempfile
import types
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


LLM_RELATIVE = Path("skills/project-orrery/assets/project-template/scripts/docsite/_llm.py")
SERVE_RELATIVE = Path("skills/project-orrery/assets/project-template/scripts/docsite/serve.py")
ENVIRONMENT_KEYS = {
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
    "OPENAI_MODEL",
    "OPENAI_INTENT_MODEL",
    "OPENAI_AUDIT_MODEL",
    "DOCSITE_AI_CONFIG",
}


@contextmanager
def controlled_environment(values: dict[str, str] | None = None) -> Iterator[None]:
    saved = {key: os.environ.get(key) for key in ENVIRONMENT_KEYS}
    try:
        for key in ENVIRONMENT_KEYS:
            os.environ.pop(key, None)
        for key, value in (values or {}).items():
            os.environ[key] = value
        yield
    finally:
        for key in ENVIRONMENT_KEYS:
            os.environ.pop(key, None)
        for key, value in saved.items():
            if value is not None:
                os.environ[key] = value


def load_source_module(path: Path) -> types.ModuleType:
    name = f"orrery_security_candidate_{uuid.uuid4().hex}"
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        source = path.read_text(encoding="utf-8-sig")
        exec(compile(source, str(path), "exec"), module.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def serialized_contains(value: Any, secret: str) -> bool:
    return secret in json.dumps(value, ensure_ascii=False, default=str)


def public_status_function(module: types.ModuleType):
    for name in ("public_config", "config_status", "public_config_status", "load_config"):
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate
    return None


def invoke_save_config(save: Any, values: dict[str, Any]) -> Any:
    """Call a candidate save API without imposing one public signature shape."""
    parameters = inspect.signature(save).parameters
    positional_mapping = next(
        (
            parameter
            for parameter in parameters.values()
            if parameter.kind in {parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD}
            and parameter.name in {"config", "data", "settings", "values"}
        ),
        None,
    )
    if positional_mapping is not None:
        return save(values)

    aliases = {
        "apiKey": "api_key",
        "baseUrl": "base_url",
        "intentModel": "intent_model",
        "auditModel": "audit_model",
    }
    accepts_extra = any(
        parameter.kind == parameter.VAR_KEYWORD for parameter in parameters.values()
    )
    keyword_values: dict[str, Any] = {}
    for source_name, value in values.items():
        target_name = aliases.get(source_name, source_name)
        if target_name in parameters or accepts_extra:
            keyword_values[target_name] = value
    return save(**keyword_values)


def check_public_environment_status(module_path: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    secret = "orrery-env-only-secret"
    module = load_source_module(module_path)
    try:
        with tempfile.TemporaryDirectory(prefix="orrery-security-status-") as temporary:
            module._PROJECT_ROOT = Path(temporary)
            if hasattr(module, "_keyring_get"):
                module._keyring_get = lambda: None
            function = public_status_function(module)
            if function is None:
                return ["no public configuration status function was found"], "environment-only hasKey"
            with controlled_environment({"OPENAI_API_KEY": secret}):
                status = function()
            if not isinstance(status, dict) or status.get("hasKey") is not True:
                errors.append("an environment-only credential is not reported as hasKey=true")
            if serialized_contains(status, secret):
                errors.append("public configuration status exposes the environment credential")
    finally:
        sys.modules.pop(module.__name__, None)
    return errors, "environment-only hasKey"


def check_secret_free_save(module_path: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    secret = "orrery-new-key-secret"
    module = load_source_module(module_path)
    try:
        save = getattr(module, "save_config", None)
        if not callable(save):
            return ["credential persistence task did not expose save_config"], "secret-free save"
        with tempfile.TemporaryDirectory(prefix="orrery-security-save-") as temporary:
            root = Path(temporary)
            module._PROJECT_ROOT = root
            stored: list[str] = []
            module.store_key = lambda key: stored.append(key) or "test-keyring"
            module._keyring_get = lambda: stored[-1] if stored else None
            with controlled_environment():
                result = invoke_save_config(save, {"apiKey": secret, "model": "model-after-save"})
            config_path = root / "ai-config.json"
            if not config_path.is_file():
                errors.append("save_config did not create the project ai-config.json")
            else:
                content = config_path.read_text(encoding="utf-8")
                if secret in content or "apiKey" in content:
                    errors.append("ai-config.json contains a plaintext credential field or value")
            if stored != [secret]:
                errors.append("the submitted credential was not written exactly once to the credential boundary")
            if serialized_contains(result, secret):
                errors.append("save_config returned the submitted credential")
    finally:
        sys.modules.pop(module.__name__, None)
    return errors, "secret-free save"


def check_environment_status_after_save(module_path: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    secret = "orrery-env-save-secret"
    module = load_source_module(module_path)
    try:
        save = getattr(module, "save_config", None)
        if not callable(save):
            return ["credential persistence task did not expose save_config"], "post-save environment hasKey"
        with tempfile.TemporaryDirectory(prefix="orrery-security-env-save-") as temporary:
            root = Path(temporary)
            module._PROJECT_ROOT = root
            module._keyring_get = lambda: None
            module.store_key = lambda key: (_ for _ in ()).throw(
                AssertionError("environment-only save must not write a credential")
            )
            with controlled_environment({"OPENAI_API_KEY": secret}):
                result = invoke_save_config(save, {"model": "environment-model"})
            if not isinstance(result, dict) or result.get("hasKey") is not True:
                errors.append("save_config loses environment-derived hasKey status in its return value")
            if serialized_contains(result, secret):
                errors.append("save_config returned the environment credential")
    finally:
        sys.modules.pop(module.__name__, None)
    return errors, "post-save environment hasKey"


def check_credential_failure_order(module_path: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    old_secret = "orrery-legacy-secret"
    new_secret = "orrery-replacement-secret"
    module = load_source_module(module_path)
    try:
        save = getattr(module, "save_config", None)
        if not callable(save):
            return ["credential persistence task did not expose save_config"], "credential failure ordering"
        with tempfile.TemporaryDirectory(prefix="orrery-security-order-") as temporary:
            root = Path(temporary)
            module._PROJECT_ROOT = root
            path = root / "ai-config.json"
            path.write_text(
                json.dumps({"apiKey": old_secret, "model": "model-before"}) + "\n",
                encoding="utf-8",
            )
            before = path.read_bytes()
            module._keyring_get = lambda: None

            def fail_store(_: str) -> str:
                raise RuntimeError("simulated credential-store failure")

            module.store_key = fail_store
            raised = False
            with controlled_environment():
                try:
                    invoke_save_config(save, {"apiKey": new_secret, "model": "model-after"})
                except Exception:
                    raised = True
            if not raised:
                errors.append("credential-store failure was swallowed")
            if path.read_bytes() != before:
                errors.append("project configuration changed before credential storage succeeded")
            if list(root.glob("*.tmp")):
                errors.append("credential-store failure left temporary configuration files")
    finally:
        sys.modules.pop(module.__name__, None)
    return errors, "credential failure ordering"


def check_atomic_replace_failure(module_path: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    module = load_source_module(module_path)
    original_replace = os.replace
    try:
        save = getattr(module, "save_config", None)
        if not callable(save):
            return ["credential persistence task did not expose save_config"], "atomic replace failure"
        with tempfile.TemporaryDirectory(prefix="orrery-security-atomic-") as temporary:
            root = Path(temporary)
            module._PROJECT_ROOT = root
            path = root / "ai-config.json"
            path.write_text(json.dumps({"model": "model-before"}) + "\n", encoding="utf-8")
            before = path.read_bytes()
            module._keyring_get = lambda: None
            module.store_key = lambda key: "test-keyring"

            def fail_replace(_: Any, __: Any) -> None:
                raise OSError("simulated atomic replacement failure")

            os.replace = fail_replace
            raised = False
            with controlled_environment():
                try:
                    invoke_save_config(save, {"model": "model-after"})
                except Exception:
                    raised = True
            if not raised:
                errors.append("atomic replacement failure was swallowed")
            if path.read_bytes() != before:
                errors.append("failed atomic replacement damaged the previous configuration")
            if list(root.glob("*.tmp")):
                errors.append("failed atomic replacement left temporary configuration files")
    finally:
        os.replace = original_replace
        sys.modules.pop(module.__name__, None)
    return errors, "atomic replace failure"


def call_name(node: ast.Call) -> str:
    parts: list[str] = []
    current: ast.AST = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def check_storage_before_persistence(paths: list[Path]) -> tuple[list[str], str]:
    errors: list[str] = []
    persistence_suffixes = {
        "write_text",
        "replace",
        "_write_json_atomic",
        "_atomic_write_json",
        "_write_project_config",
        "save_nonsecret_config",
        "save_project_config",
        "save_config",
        "save_settings",
    }
    flows = 0
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            calls = sorted(
                ((node.lineno, call_name(node)) for node in ast.walk(function) if isinstance(node, ast.Call)),
                key=lambda item: item[0],
            )
            store_lines = [line for line, name in calls if name.endswith("store_key")]
            if not store_lines:
                continue
            persistence_lines = [
                line
                for line, name in calls
                if name.rsplit(".", 1)[-1] in persistence_suffixes and not name.endswith("store_key")
            ]
            if not persistence_lines:
                continue
            flows += 1
            if min(persistence_lines) < min(store_lines):
                errors.append(
                    f"{path.name}:{function.name} persists non-secret configuration before store_key succeeds"
                )
    if flows == 0:
        errors.append("no credential-to-project persistence flow was found")
    return errors, "credential-before-config source order"


def handler_type_name(node: ast.ExceptHandler) -> str:
    value = node.type
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return ""


def check_provider_error_redaction(paths: list[Path]) -> tuple[list[str], str]:
    errors: list[str] = []
    # The legacy /ask branch intentionally has separate diagnostics. Limit this
    # check to the provider-test helpers instead of scanning all of do_POST.
    relevant_names = {"test_connection", "_config_test", "safe_error", "_safe_test_error"}
    checked = 0
    for path in paths:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
        for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            if function.name not in relevant_names:
                continue
            for handler in (node for node in ast.walk(function) if isinstance(node, ast.ExceptHandler)):
                if handler_type_name(handler) != "Exception" or not handler.name:
                    continue
                checked += 1
                for node in ast.walk(handler):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id in {"str", "repr"} and any(
                            isinstance(arg, ast.Name) and arg.id == handler.name for arg in node.args
                        ):
                            errors.append(
                                f"{path.name}:{function.name} stringifies a provider exception in a response path"
                            )
                    if isinstance(node, ast.FormattedValue) and isinstance(node.value, ast.Name):
                        if node.value.id == handler.name:
                            errors.append(
                                f"{path.name}:{function.name} interpolates a provider exception in a response path"
                            )
    if checked == 0:
        # Constant-message handlers may omit the exception binding entirely.
        combined = "\n".join(path.read_text(encoding="utf-8-sig") for path in paths)
        if "connection test failed" not in combined and "provider request failed" not in combined:
            errors.append("no reviewable provider-error redaction path was found")
    return errors, "provider error redaction"


def evaluate(repository: Path, task_id: str) -> dict[str, Any]:
    llm_path = repository / LLM_RELATIVE
    serve_path = repository / SERVE_RELATIVE
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    if not llm_path.is_file():
        return {"ok": False, "task_id": task_id, "checks": [], "errors": [f"missing {LLM_RELATIVE.as_posix()}"]}

    check_functions = []
    if task_id == "PO-CR-010":
        if not serve_path.is_file():
            return {"ok": False, "task_id": task_id, "checks": [], "errors": [f"missing {SERVE_RELATIVE.as_posix()}"]}
        serve_source = serve_path.read_text(encoding="utf-8-sig")
        for route in ("/api/ai-config", "/api/ai-config/test"):
            if route not in serve_source:
                errors.append(f"missing required route {route}")
        check_functions = [
            ("environment-only hasKey", lambda: check_public_environment_status(llm_path)),
            ("credential-before-config source order", lambda: check_storage_before_persistence([llm_path, serve_path])),
            ("provider error redaction", lambda: check_provider_error_redaction([llm_path, serve_path])),
        ]
    elif task_id == "PO-CR-011":
        check_functions = [
            ("secret-free save", lambda: check_secret_free_save(llm_path)),
            ("post-save environment hasKey", lambda: check_environment_status_after_save(llm_path)),
            ("credential failure ordering", lambda: check_credential_failure_order(llm_path)),
            ("atomic replace failure", lambda: check_atomic_replace_failure(llm_path)),
        ]
    else:
        return {"ok": True, "task_id": task_id, "checks": [], "errors": []}

    for expected_name, function in check_functions:
        try:
            check_errors, name = function()
        except Exception as exc:  # oracle failures are explicit apparatus failures
            name = expected_name
            check_errors = [f"operator oracle failed: {type(exc).__name__}: {exc}"]
        checks.append({"name": name, "passed": not check_errors})
        errors.extend(check_errors)
    return {"ok": not errors, "task_id": task_id, "checks": checks, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--task-id", required=True, choices=["PO-CR-010", "PO-CR-011"])
    args = parser.parse_args(argv)
    result = evaluate(args.repository.resolve(), args.task_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
