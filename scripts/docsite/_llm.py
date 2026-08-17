"""Generic OpenAI-compatible LLM provider for the doc-copilot (portable build).

This replaces the host project's internal provider so the doc-copilot can run
in any repo. Config is resolved from several sources, **highest priority first**:

  1. Environment variables:
       OPENAI_API_KEY / DEEPSEEK_API_KEY   the key
       OPENAI_BASE_URL                      e.g. https://api.deepseek.com/v1
       OPENAI_MODEL                         e.g. deepseek-chat / gpt-4o-mini
       OPENAI_INTENT_MODEL / OPENAI_AUDIT_MODEL  optional per-stage overrides
  2. The OS credential store — **secure, no plaintext on disk** — the key only.
       Store it through the local graphical settings panel or once with:
       python scripts/docsite/set_key.py
       (uses `keyring`: Windows Credential Manager / macOS Keychain / Secret Service)
  3. A JSON file pointed to by  DOCSITE_AI_CONFIG
  4. <project-root>/ai-config.json
  5. The host app's per-user config:  <userData>/ai-config.json
     where <userData> is derived from package.json "name"
       Windows : %APPDATA%/<name>
       macOS   : ~/Library/Application Support/<name>
       Linux   : ${XDG_CONFIG_HOME:-~/.config}/<name>

baseUrl/model are not secret and still come from env or a JSON file; only the
key is read from the credential store. Each JSON file uses the same shape an
Electron app would write. Project Orrery's own graphical settings never writes
``apiKey`` to JSON and uses this non-secret shape:
    {
      "baseUrl": "https://api.deepseek.com/v1",
      "model": "deepseek-chat",
      "intentModel": "deepseek-chat",
      "auditModel": "deepseek-chat"
    }
Env vars override file values field-by-field, so you can keep baseUrl/model in
the file and inject just the key via the environment.

The object returned by ``make_provider()`` exposes exactly what the doc-copilot
needs: ``.complete(LLMRequest)`` (returns a parsed dict), plus ``.client`` and
``.audit_model`` so the Q&A path can stream directly via the OpenAI SDK.

Requires the ``openai`` package (``pip install openai``).
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# placeholder keys shipped in *.example.json — treated as "no key"
_PLACEHOLDER_KEYS = {"", "sk-...", "your-api-key", "sk-xxxx"}

# OS credential store (via the `keyring` package): secure, no plaintext on disk.
KEYRING_SERVICE = "project-orrery"
KEYRING_USER = "OPENAI_API_KEY"


def _keyring_get() -> str | None:
    try:
        import keyring
        v = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    except Exception:  # noqa: BLE001 — keyring missing/locked is just "no key here"
        return None
    return v.strip() if isinstance(v, str) and v.strip() else None


def store_key(key: str) -> str:
    """Save the API key in the OS credential store; return the backend class name."""
    import keyring
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, key)
    return type(keyring.get_keyring()).__name__


def delete_key() -> None:
    try:
        import keyring
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
    except Exception:  # noqa: BLE001
        pass


@dataclass
class LLMRequest:
    system: str
    user: str
    json_schema: dict | None = None
    cache_system: bool = False
    max_tokens: int = 1024
    model_kind: str = "intent"  # "intent" (fast) | "audit" (strong)


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — missing/invalid file is just "no config here"
        return None


def project_config_path() -> Path:
    """Return the repository-local, git-ignored provider configuration path."""
    return _PROJECT_ROOT / "ai-config.json"


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ai-config-", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temporary_path = Path(temporary)
    try:
        temporary_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def save_project_config(
    *,
    base_url: str = "",
    model: str = "",
    intent_model: str = "",
    audit_model: str = "",
) -> Path:
    """Atomically persist non-secret provider settings.

    The graphical settings flow stores API keys in the OS credential store. If
    an older ``ai-config.json`` contains a plaintext ``apiKey``, saving through
    this function deliberately removes it while preserving unrelated fields.
    """
    path = project_config_path()
    data = _read_json(path) or {}
    if not isinstance(data, dict):
        data = {}
    data.pop("apiKey", None)
    values = {
        "baseUrl": base_url.strip(),
        "model": model.strip(),
        "intentModel": intent_model.strip(),
        "auditModel": audit_model.strip(),
    }
    for key, value in values.items():
        if value:
            data[key] = value
        else:
            data.pop(key, None)

    _write_json_atomic(path, data)
    return path


def remove_project_plaintext_key() -> bool:
    """Remove a legacy plaintext API key from the project config, if present."""
    path = project_config_path()
    data = _read_json(path)
    if not isinstance(data, dict) or "apiKey" not in data:
        return False
    data.pop("apiKey", None)
    _write_json_atomic(path, data)
    return True


def _is_real_key(k) -> bool:
    if not isinstance(k, str):
        return False
    k = k.strip()
    return bool(k) and not k.lower().startswith("sk-your") and k not in _PLACEHOLDER_KEYS


def _userdata_config_path() -> Path | None:
    """`<userData>/ai-config.json`, with <userData> derived from package.json name."""
    pkg = _PROJECT_ROOT / "package.json"
    data = _read_json(pkg) if pkg.exists() else None
    name = (data or {}).get("name")
    if not name:
        return None
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / name / "ai-config.json" if base else None


def _candidate_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.environ.get("DOCSITE_AI_CONFIG")
    if env_path:
        paths.append(Path(env_path))
    paths.append(_PROJECT_ROOT / "ai-config.json")
    ud = _userdata_config_path()
    if ud:
        paths.append(ud)
    return paths


def load_config() -> dict:
    """Resolve {api_key, base_url, model, intent_model, audit_model, source}.

    Env wins; then the first config file that supplies each field. baseUrl/model
    are picked up from a file even when that file has no usable key, so a
    DeepSeek/etc. endpoint is auto-detected and you only need to supply the key.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
    model = os.environ.get("OPENAI_MODEL")
    intent_model = os.environ.get("OPENAI_INTENT_MODEL")
    audit_model = os.environ.get("OPENAI_AUDIT_MODEL")
    source = "env" if api_key else None

    if not api_key:
        kr = _keyring_get()
        if kr:
            api_key, source = kr, "keyring"

    for p in _candidate_paths():
        data = _read_json(p)
        if not data:
            continue
        if not base_url and data.get("baseUrl"):
            base_url = data["baseUrl"]
        if not model and data.get("model"):
            model = data["model"]
        if not intent_model and data.get("intentModel"):
            intent_model = data["intentModel"]
        if not audit_model and data.get("auditModel"):
            audit_model = data["auditModel"]
        if not api_key and _is_real_key(data.get("apiKey")):
            api_key = data["apiKey"].strip()
            source = str(p)

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "intent_model": intent_model,
        "audit_model": audit_model,
        "source": source,
    }


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)
_BRACE = re.compile(r"\{[\s\S]*\}")


def parse_json_lenient(text: str) -> dict:
    """Best-effort JSON-object extraction from a model reply.

    Handles ```json fences and chatter around a single top-level object.
    Always returns a dict; on failure includes ``parse_error: True``.
    """
    if not text:
        return {"raw_text": "", "parse_error": True, "error": "empty response"}
    s = text.strip()
    if s.startswith("```"):
        s = _FENCE.sub("", s).strip()
    try:
        v = json.loads(s)
        return v if isinstance(v, dict) else {"value": v}
    except json.JSONDecodeError:
        pass
    m = _BRACE.search(s)
    if m:
        try:
            v = json.loads(m.group(0))
            return v if isinstance(v, dict) else {"value": v}
        except json.JSONDecodeError as e:
            return {"raw_text": text, "parse_error": True, "error": "brace parse: %s" % e}
    return {"raw_text": text, "parse_error": True, "error": "no JSON object found"}


class OpenAICompatProvider:
    """Thin wrapper over an OpenAI-compatible chat-completions endpoint."""

    name = "openai-compat"

    def __init__(self, config: dict | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "需要 'openai' 包才能用 LLM 功能：pip install openai"
            ) from e
        cfg = config or load_config()
        key = cfg["api_key"]
        if not key:
            tried = " / ".join(str(p) for p in _candidate_paths())
            raise RuntimeError(
                "未找到 API Key。请任选其一：\n"
                "  · 【推荐·不落明文】运行  python scripts/docsite/set_key.py  存入系统凭据库\n"
                "  · 设置环境变量 OPENAI_API_KEY（或 DEEPSEEK_API_KEY）\n"
                "  · 在下列任一 ai-config.json 的 \"apiKey\" 字段填入 key：\n"
                f"    {tried}"
            )
        base = cfg["base_url"]
        self.client = OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)
        default = cfg["model"] or "gpt-4o-mini"
        self.audit_model = cfg["audit_model"] or default
        self.intent_model = cfg["intent_model"] or default

    def complete(self, req: LLMRequest) -> dict:
        model = self.intent_model if req.model_kind == "intent" else self.audit_model
        system = req.system
        kwargs: dict = {}
        if req.json_schema:
            system = (
                system
                + "\n\n只输出一个 JSON 对象（不要 markdown 代码块、不要解释）。"
                + "字段需符合此 schema：\n"
                + json.dumps(req.json_schema, ensure_ascii=False)
            )
            kwargs["response_format"] = {"type": "json_object"}
        try:
            r = self.client.chat.completions.create(
                model=model,
                max_tokens=req.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": req.user},
                ],
                **kwargs,
            )
            content = r.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001 — surface as a parse_error for the UI
            return {"parse_error": True, "error": repr(e), "raw_text": ""}
        return parse_json_lenient(content) if req.json_schema else {"text": content}


def make_provider() -> OpenAICompatProvider:
    return OpenAICompatProvider()
