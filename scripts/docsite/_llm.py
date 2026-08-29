"""Generic OpenAI-compatible LLM provider for the doc-copilot (portable build).

This replaces the host project's internal provider so the doc-copilot can run
in any repo. Config is resolved from several sources, **highest priority first**:

  1. Provider-specific environment variables:
       OPENAI_API_KEY / DEEPSEEK_API_KEY / DOCSITE_API_KEY
       DOCSITE_PROVIDER + OPENAI_BASE_URL   explicit Provider binding
       OPENAI_MODEL                         e.g. deepseek-chat / gpt-4o-mini
       OPENAI_INTENT_MODEL / OPENAI_AUDIT_MODEL  optional per-stage overrides
  2. A Provider-and-endpoint-bound OS credential slot — no plaintext on disk.
       Store it through the local graphical settings panel or once with:
       python scripts/docsite/set_key.py
       (uses `keyring`: Windows Credential Manager / macOS Keychain / Secret Service)
  3. A JSON file pointed to by DOCSITE_AI_CONFIG (non-secret settings only)
  4. <project-root>/ai-config.json
  5. The host app's per-user config: <userData>/ai-config.json
     where <userData> is derived from package.json "name"
       Windows : %APPDATA%/<name>
       macOS   : ~/Library/Application Support/<name>
       Linux   : ${XDG_CONFIG_HOME:-~/.config}/<name>

Provider/baseUrl/model are not secret and come from env or JSON. A saved config
must include an enabled flag and a fingerprint derived from Provider + Base URL;
otherwise startup fails closed. Orrery never writes ``apiKey`` to JSON.
    {
      "provider": "deepseek",
      "baseUrl": "https://api.deepseek.com",
      "model": "deepseek-chat",
      "intentModel": "deepseek-chat",
      "auditModel": "deepseek-chat",
      "enabled": true,
      "providerFingerprint": "sha256:..."
    }
Env vars override file values field-by-field, so you can keep baseUrl/model in
the file and inject just the key via the environment.

The object returned by ``make_provider()`` exposes exactly what the doc-copilot
needs: ``.complete(LLMRequest)`` (returns a parsed dict), plus ``.client`` and
``.audit_model`` so the Q&A path can stream directly via the OpenAI SDK.

Requires the ``openai`` package (``pip install openai``).

The dynamic docsite calls this module with ``require_broker=True``. Direct
Provider resolution remains only as an internal Broker/compatibility primitive;
it is not a supported docsite model-call path.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# placeholder keys shipped in *.example.json — treated as "no key"
_PLACEHOLDER_KEYS = {"", "sk-...", "your-api-key", "sk-xxxx"}

# Provider-bound OS credentials. The legacy shared slot is detected for an
# explicit one-time replacement, but is never used to initialize a provider.
KEYRING_NAMESPACE = "project-orrery/provider"
KEYRING_USER = "api-key"
LEGACY_KEYRING_SERVICE = "project-orrery"
LEGACY_KEYRING_USER = "OPENAI_API_KEY"
KNOWN_PROVIDER_HOSTS = {
    "openai": "api.openai.com",
    "deepseek": "api.deepseek.com",
}
_TEST_KEYRING: dict[tuple[str, str], str] = {}


def _keyring_read(service: str, user: str) -> str | None:
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        value = _TEST_KEYRING.get((service, user))
        return value.strip() if isinstance(value, str) and value.strip() else None
    try:
        import keyring
        v = keyring.get_password(service, user)
    except Exception:  # noqa: BLE001 — keyring missing/locked is just "no key here"
        return None
    return v.strip() if isinstance(v, str) and v.strip() else None


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def normalize_base_url(value: str) -> str:
    """Return a canonical explicit endpoint; reject credentials/query/fragment."""
    value = (value or "").strip()
    if not value:
        raise ValueError("Base URL 不能为空；不会回退到 SDK 默认端点")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Base URL 必须是有效的 http:// 或 https:// 地址")
    if parsed.username or parsed.password:
        raise ValueError("Base URL 不能包含用户名或密码")
    if parsed.query or parsed.fragment:
        raise ValueError("Base URL 不能包含 query 或 fragment")
    host = parsed.hostname.lower()
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("Base URL 端口无效") from error
    loopback = _is_loopback_host(host)
    if parsed.scheme == "http" and not loopback:
        raise ValueError("远程 Provider 必须使用 HTTPS；HTTP 只允许环回地址")
    display_host = "[%s]" % host if ":" in host else host
    default_port = 443 if parsed.scheme == "https" else 80
    netloc = display_host if port in (None, default_port) else "%s:%d" % (display_host, port)
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), netloc, path, "", ""))


def infer_provider(base_url: str) -> str:
    host = urlsplit(normalize_base_url(base_url)).hostname or ""
    if host == KNOWN_PROVIDER_HOSTS["openai"]:
        return "openai"
    if host == KNOWN_PROVIDER_HOSTS["deepseek"]:
        return "deepseek"
    if _is_loopback_host(host):
        return "broker"
    return "custom"


def provider_env_name(provider: str) -> str:
    return {
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "broker": "DOCSITE_API_KEY",
        "custom": "DOCSITE_API_KEY",
    }.get((provider or "").lower(), "")


def validate_provider_endpoint(provider: str, base_url: str) -> tuple[str, str]:
    provider = (provider or "").strip().lower()
    normalized = normalize_base_url(base_url)
    host = urlsplit(normalized).hostname or ""
    if provider not in ("openai", "deepseek", "broker", "custom"):
        raise ValueError("未知 Provider：%s" % (provider or "<empty>"))
    if provider in KNOWN_PROVIDER_HOSTS and host != KNOWN_PROVIDER_HOSTS[provider]:
        raise ValueError("%s Provider 必须使用 %s" % (provider, KNOWN_PROVIDER_HOSTS[provider]))
    if provider == "broker" and not _is_loopback_host(host):
        raise ValueError("Local Broker 必须使用环回地址")
    return provider, normalized


def provider_fingerprint(provider: str, base_url: str) -> str:
    provider, normalized = validate_provider_endpoint(provider, base_url)
    digest = hashlib.sha256((provider + "\n" + normalized).encode("utf-8")).hexdigest()
    return "sha256:" + digest


def credential_service(provider: str, base_url: str, *, namespace: str = KEYRING_NAMESPACE) -> str:
    return "%s/%s" % (namespace.rstrip("/"), provider_fingerprint(provider, base_url)[7:])


def _keyring_get(provider: str, base_url: str, *, namespace: str = KEYRING_NAMESPACE) -> str | None:
    return _keyring_read(credential_service(provider, base_url, namespace=namespace), KEYRING_USER)


def legacy_key_available() -> bool:
    return bool(_keyring_read(LEGACY_KEYRING_SERVICE, LEGACY_KEYRING_USER))


def store_key(key: str, provider: str, base_url: str, *, namespace: str = KEYRING_NAMESPACE) -> str:
    """Save a Provider-bound API key; return the backend class name."""
    service = credential_service(provider, base_url, namespace=namespace)
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        _TEST_KEYRING[(service, KEYRING_USER)] = key
        return "InMemoryTestKeyring"
    import keyring
    keyring.set_password(service, KEYRING_USER, key)
    return type(keyring.get_keyring()).__name__


def delete_key(provider: str, base_url: str, *, namespace: str = KEYRING_NAMESPACE) -> None:
    service = credential_service(provider, base_url, namespace=namespace)
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        _TEST_KEYRING.pop((service, KEYRING_USER), None)
        return
    try:
        import keyring
        keyring.delete_password(service, KEYRING_USER)
    except Exception:  # noqa: BLE001
        pass


def delete_legacy_key() -> None:
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        _TEST_KEYRING.pop((LEGACY_KEYRING_SERVICE, LEGACY_KEYRING_USER), None)
        return
    try:
        import keyring
        keyring.delete_password(LEGACY_KEYRING_SERVICE, LEGACY_KEYRING_USER)
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
    provider: str,
    base_url: str = "",
    model: str = "",
    intent_model: str = "",
    audit_model: str = "",
    enabled: bool = True,
    broker_mode: str = "",
    upstream_provider: str = "",
    upstream_base_url: str = "",
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
    provider, base_url = validate_provider_endpoint(provider, base_url)
    values = {
        "provider": provider,
        "baseUrl": base_url,
        "model": model.strip(),
        "intentModel": intent_model.strip(),
        "auditModel": audit_model.strip(),
        "providerFingerprint": provider_fingerprint(provider, base_url),
        "brokerMode": broker_mode.strip(),
        "upstreamProvider": upstream_provider.strip(),
        "upstreamBaseUrl": upstream_base_url.strip(),
    }
    for key, value in values.items():
        if value:
            data[key] = value
        else:
            data.pop(key, None)

    data["enabled"] = bool(enabled)
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


def _env_enabled(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def load_config(*, read_credential: bool = True) -> dict:
    """Resolve non-secret settings first, then the matching bound credential."""
    file_data: dict = {}
    legacy_plaintext = False
    for path in _candidate_paths():
        data = _read_json(path)
        if not isinstance(data, dict):
            continue
        for field in (
            "provider", "baseUrl", "model", "intentModel", "auditModel",
            "enabled", "providerFingerprint", "brokerMode", "upstreamProvider",
            "upstreamBaseUrl",
        ):
            if field not in file_data and field in data:
                file_data[field] = data[field]
        legacy_plaintext = legacy_plaintext or _is_real_key(data.get("apiKey"))

    base_url = (
        os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or file_data.get("baseUrl")
        or ""
    )
    provider = os.environ.get("DOCSITE_PROVIDER") or file_data.get("provider") or ""
    if not provider and base_url:
        try:
            provider = infer_provider(base_url)
        except ValueError:
            provider = ""
    model = os.environ.get("OPENAI_MODEL") or file_data.get("model") or ""
    intent_model = os.environ.get("OPENAI_INTENT_MODEL") or file_data.get("intentModel") or ""
    audit_model = os.environ.get("OPENAI_AUDIT_MODEL") or file_data.get("auditModel") or ""
    explicit_env_endpoint = bool(
        os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
    )
    configured_enabled = bool(file_data.get("enabled", False))
    endpoint_error = ""
    normalized = ""
    expected_fingerprint = ""
    try:
        provider, normalized = validate_provider_endpoint(provider, base_url)
        expected_fingerprint = provider_fingerprint(provider, normalized)
    except ValueError as error:
        endpoint_error = str(error)

    env_name = provider_env_name(provider)
    env_key = os.environ.get(env_name) if read_credential and env_name else None
    enabled_default = explicit_env_endpoint and bool(env_key)
    enabled = _env_enabled(os.environ.get("DOCSITE_AI_ENABLED"), configured_enabled or enabled_default)
    saved_fingerprint = os.environ.get("DOCSITE_PROVIDER_FINGERPRINT") or file_data.get("providerFingerprint") or ""
    binding_valid = bool(
        enabled
        and not endpoint_error
        and expected_fingerprint
        and (explicit_env_endpoint or saved_fingerprint == expected_fingerprint)
    )

    bound_key = None
    if read_credential and not endpoint_error and provider and normalized:
        bound_key = _keyring_get(provider, normalized)
    selected_key = env_key or bound_key
    api_key = selected_key if binding_valid else None
    source = ("env:" + env_name) if env_key else ("keyring" if bound_key else None)
    return {
        "api_key": api_key,
        "has_credential": bool(selected_key),
        "base_url": normalized or base_url,
        "model": model,
        "intent_model": intent_model,
        "audit_model": audit_model,
        "provider": provider,
        "broker_mode": str(file_data.get("brokerMode") or ""),
        "upstream_provider": str(file_data.get("upstreamProvider") or ""),
        "upstream_base_url": str(file_data.get("upstreamBaseUrl") or ""),
        "enabled": enabled,
        "binding_valid": binding_valid,
        "provider_fingerprint": saved_fingerprint,
        "expected_fingerprint": expected_fingerprint,
        "endpoint_error": endpoint_error,
        # Do not read the legacy shared key merely to report its existence.
        # Explicit save/delete operations clean that slot without loading it.
        "legacy_key_available": False,
        "legacy_plaintext_available": legacy_plaintext,
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

    def __init__(self, config: dict | None = None, *, require_broker: bool = False) -> None:
        try:
            from openai import OpenAI
            import httpx
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "需要 'openai' 包才能用 LLM 功能：pip install openai"
            ) from e
        cfg = config or load_config()
        if not cfg.get("enabled", True):
            raise RuntimeError("AI Provider 尚未启用")
        if not cfg.get("binding_valid", True):
            raise RuntimeError(cfg.get("endpoint_error") or "Provider 配置指纹不匹配，请重新保存并启用")
        key = cfg["api_key"]
        if not key:
            raise RuntimeError(
                "未找到当前 Provider 与 Base URL 绑定的 API Key。请通过本地设置页重新输入，"
                "或使用 set_key.py 通过 Broker 注册；不要把 Key 写进 ai-config.json。"
            )
        provider, base = validate_provider_endpoint(
            cfg.get("provider") or infer_provider(cfg.get("base_url") or ""),
            cfg.get("base_url") or "",
        )
        if require_broker and provider != "broker":
            raise RuntimeError(
                "动态 docsite 只允许通过 Broker 调用模型；请在 AI 设置中迁移旧的直接 Provider 配置"
            )
        default = cfg["model"]
        if not default:
            raise RuntimeError("默认模型不能为空")
        self.provider = provider
        self.base_url = base
        self._redaction_secret = key
        self.client = OpenAI(
            api_key=key,
            base_url=base,
            http_client=httpx.Client(follow_redirects=False),
        )
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
            error_text = repr(e).replace(self._redaction_secret, "[REDACTED]")
            return {"parse_error": True, "error": error_text, "raw_text": ""}
        return parse_json_lenient(content) if req.json_schema else {"text": content}


def make_provider(*, require_broker: bool = False) -> OpenAICompatProvider:
    return OpenAICompatProvider(require_broker=require_broker)
