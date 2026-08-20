#!/usr/bin/env python3
"""Optional local OpenAI-compatible broker with Provider-key isolation controls.

Run this script under a dedicated OS account if the Provider key must be outside
the docsite/Agent identity. Running it as the same user still provides caching,
endpoint pinning and budgets, but not process-level secret isolation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import getpass
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _llm  # noqa: E402

BROKER_NAMESPACE = "project-orrery-broker/provider"
BROKER_TOKEN_SERVICE = "project-orrery-broker/access"
BROKER_TOKEN_USER = "client-token"
MAX_REQUEST_BODY = 2 * 1024 * 1024
MAX_RESPONSE_BODY = 16 * 1024 * 1024


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)


def _user_data_dir() -> Path:
    override = os.environ.get("DOCSITE_BROKER_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return Path(base or Path.home()) / "project-orrery-broker"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "project-orrery-broker"
    return (
        Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
        / "project-orrery-broker"
    )


def config_path() -> Path:
    return _user_data_dir() / "broker-config.json"


def cache_path() -> Path:
    return _user_data_dir() / "broker-cache.sqlite3"


def _read_config() -> dict:
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_config(data: dict) -> None:
    path = config_path()
    _ensure_private_directory(path.parent)
    fd, temporary = tempfile.mkstemp(
        prefix=".broker-config-", suffix=".tmp", dir=path.parent
    )
    os.close(fd)
    temp_path = Path(temporary)
    try:
        temp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _token_get() -> str | None:
    return _llm._keyring_read(BROKER_TOKEN_SERVICE, BROKER_TOKEN_USER)


def _token_set(value: str) -> None:
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        _llm._TEST_KEYRING[(BROKER_TOKEN_SERVICE, BROKER_TOKEN_USER)] = value
        return
    import keyring

    keyring.set_password(BROKER_TOKEN_SERVICE, BROKER_TOKEN_USER, value)


def _token_delete() -> None:
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        _llm._TEST_KEYRING.pop((BROKER_TOKEN_SERVICE, BROKER_TOKEN_USER), None)
        return
    try:
        import keyring

        keyring.delete_password(BROKER_TOKEN_SERVICE, BROKER_TOKEN_USER)
    except Exception:  # noqa: BLE001
        pass


def _validated_config(data: dict) -> dict:
    provider, base_url = _llm.validate_provider_endpoint(
        str(data.get("provider") or ""), str(data.get("baseUrl") or "")
    )
    model = str(data.get("model") or "").strip()
    if not model:
        raise ValueError("Broker 默认模型不能为空")
    models = [model]
    for field in ("intentModel", "auditModel"):
        value = str(data.get(field) or "").strip()
        if value and value not in models:
            models.append(value)
    daily_requests = int(data.get("dailyRequestLimit", 100))
    daily_tokens = int(data.get("dailyTokenLimit", 1_000_000))
    cache_ttl = int(data.get("cacheTtlSeconds", 7 * 86400))
    if not 1 <= daily_requests <= 100_000:
        raise ValueError("dailyRequestLimit 必须在 1..100000")
    if not 1 <= daily_tokens <= 1_000_000_000:
        raise ValueError("dailyTokenLimit 必须在 1..1000000000")
    if not 0 <= cache_ttl <= 365 * 86400:
        raise ValueError("cacheTtlSeconds 必须在 0..31536000")
    return {
        "provider": provider,
        "baseUrl": base_url,
        "model": model,
        "intentModel": str(data.get("intentModel") or "").strip(),
        "auditModel": str(data.get("auditModel") or "").strip(),
        "allowedModels": models,
        "dailyRequestLimit": daily_requests,
        "dailyTokenLimit": daily_tokens,
        "cacheTtlSeconds": cache_ttl,
    }


class BrokerState:
    def __init__(
        self,
        config: dict,
        provider_key: str,
        client_token: str,
        *,
        database: Path | None = None,
    ):
        self.config = _validated_config(config)
        self.provider_key = provider_key
        self.client_token = client_token
        self.database = database or cache_path()
        _ensure_private_directory(self.database.parent)
        self._db_lock = threading.RLock()
        self._flight_guard = threading.Lock()
        self._flights: dict[str, tuple[threading.Lock, int]] = {}
        self._init_db()

    @property
    def upstream_url(self) -> str:
        return self.config["baseUrl"].rstrip("/") + "/chat/completions"

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30)
        if os.name != "nt":
            self.database.chmod(0o600)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @contextmanager
    def _database(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._db_lock, self._database() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(cache_key TEXT PRIMARY KEY, body BLOB NOT NULL, content_type TEXT NOT NULL, "
                "created REAL NOT NULL, total_tokens INTEGER NOT NULL DEFAULT 0)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS daily "
                "(day TEXT PRIMARY KEY, requests INTEGER NOT NULL DEFAULT 0, tokens INTEGER NOT NULL DEFAULT 0)"
            )

    def cache_key(self, payload: dict) -> str:
        canonical = json.dumps(
            {"baseUrl": self.config["baseUrl"], "payload": payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def cached(self, key: str) -> tuple[bytes, str] | None:
        ttl = self.config["cacheTtlSeconds"]
        if ttl <= 0:
            return None
        with self._db_lock, self._database() as db:
            row = db.execute(
                "SELECT body, content_type, created FROM cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row or time.time() - float(row[2]) > ttl:
                if row:
                    db.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
                return None
            return bytes(row[0]), str(row[1])

    def put_cache(self, key: str, body: bytes, content_type: str, tokens: int) -> None:
        with self._db_lock, self._database() as db:
            db.execute(
                "INSERT OR REPLACE INTO cache(cache_key, body, content_type, created, total_tokens) "
                "VALUES (?, ?, ?, ?, ?)",
                (key, body, content_type, time.time(), tokens),
            )

    @contextmanager
    def flight(self, key: str):
        with self._flight_guard:
            current = self._flights.get(key)
            lock, users = current if current else (threading.Lock(), 0)
            self._flights[key] = (lock, users + 1)
        lock.acquire()
        try:
            yield
        finally:
            lock.release()
            with self._flight_guard:
                current = self._flights.get(key)
                if current and current[0] is lock:
                    users = current[1] - 1
                    if users:
                        self._flights[key] = (lock, users)
                    else:
                        self._flights.pop(key, None)

    def usage(self) -> dict:
        day = time.strftime("%Y-%m-%d", time.localtime())
        with self._db_lock, self._database() as db:
            row = db.execute(
                "SELECT requests, tokens FROM daily WHERE day = ?", (day,)
            ).fetchone()
        return {
            "day": day,
            "requests": int(row[0]) if row else 0,
            "tokens": int(row[1]) if row else 0,
        }

    def token_ceiling(self, payload: dict) -> int:
        raw_limit = payload.get("max_tokens", payload.get("max_completion_tokens"))
        try:
            output_limit = int(raw_limit)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "max_tokens is required for enforceable token budgets"
            ) from error
        if output_limit <= 0:
            raise ValueError("max_tokens must be positive")
        request_bytes = len(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        )
        return request_bytes + output_limit

    def reserve_request(self, token_ceiling: int) -> None:
        day = time.strftime("%Y-%m-%d", time.localtime())
        with self._db_lock, self._database() as db:
            row = db.execute(
                "SELECT requests, tokens FROM daily WHERE day = ?", (day,)
            ).fetchone()
            requests = int(row[0]) if row else 0
            tokens = int(row[1]) if row else 0
            if requests >= self.config["dailyRequestLimit"]:
                raise RuntimeError("daily request budget exceeded")
            if tokens + token_ceiling > self.config["dailyTokenLimit"]:
                raise RuntimeError("daily token budget would be exceeded")
            db.execute(
                "INSERT INTO daily(day, requests, tokens) VALUES (?, 1, ?) "
                "ON CONFLICT(day) DO UPDATE SET requests = requests + 1, "
                "tokens = tokens + excluded.tokens",
                (day, token_ceiling),
            )

    def settle_tokens(self, reserved: int, actual: int) -> None:
        day = time.strftime("%Y-%m-%d", time.localtime())
        with self._db_lock, self._database() as db:
            row = db.execute(
                "SELECT tokens FROM daily WHERE day = ?", (day,)
            ).fetchone()
            current = int(row[0]) if row else 0
            db.execute(
                "UPDATE daily SET tokens = ? WHERE day = ?",
                (max(0, current - reserved + actual), day),
            )


class BrokerHandler(BaseHTTPRequestHandler):
    server_version = "ProjectOrreryBroker/0.1"

    @property
    def state(self) -> BrokerState:
        return self.server.state  # type: ignore[attr-defined]

    def _headers(
        self, content_type: str, length: int | None = None, *, cache: str = "no-store"
    ) -> None:
        self.send_header("Content-Type", content_type)
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")

    def _json(self, code: int, data: dict, **headers: str) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._headers("application/json; charset=utf-8", len(body))
        for name, value in headers.items():
            self.send_header(name.replace("_", "-"), value)
        self.end_headers()
        self.wfile.write(body)

    def _host_authorized(self) -> bool:
        try:
            parsed = urlsplit("http://" + self.headers.get("Host", ""))
            return _llm._is_loopback_host(parsed.hostname) and parsed.port == int(
                self.server.server_address[1]
            )
        except (TypeError, ValueError):
            return False

    def _client_authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        prefix = "Bearer "
        return supplied.startswith(prefix) and secrets.compare_digest(
            supplied[len(prefix) :], self.state.client_token
        )

    def do_GET(self) -> None:
        if not self._host_authorized():
            self._json(421, {"error": "loopback Host required"})
            return
        if self.path != "/health":
            self._json(404, {"error": "not found"})
            return
        usage = self.state.usage()
        self._json(
            200,
            {
                "ok": True,
                "provider": self.state.config["provider"],
                "baseUrl": self.state.config["baseUrl"],
                "allowedModels": self.state.config["allowedModels"],
                "usage": usage,
                "limits": {
                    "requests": self.state.config["dailyRequestLimit"],
                    "tokens": self.state.config["dailyTokenLimit"],
                },
            },
        )

    def do_POST(self) -> None:
        if not self._host_authorized():
            self._json(421, {"error": "loopback Host required"})
            return
        if self.path != "/v1/chat/completions":
            self._json(404, {"error": "not found"})
            return
        if not self._client_authorized():
            self._json(401, {"error": "invalid broker client token"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if not 0 < length <= MAX_REQUEST_BODY:
            self._json(413, {"error": "request body missing or too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "invalid JSON"})
            return
        if not isinstance(payload, dict):
            self._json(400, {"error": "JSON object required"})
            return
        model = payload.get("model")
        if model not in self.state.config["allowedModels"]:
            self._json(403, {"error": "model is not allowlisted"})
            return
        if payload.get("stream"):
            self._stream_upstream(payload)
        else:
            self._complete_upstream(payload)

    def _upstream_headers(self) -> dict[str, str]:
        return {
            "Authorization": "Bearer " + self.state.provider_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "project-orrery-broker/0.1",
        }

    def _complete_upstream(self, payload: dict) -> None:
        key = self.state.cache_key(payload)
        cached = self.state.cached(key)
        if cached:
            body, content_type = cached
            self.send_response(200)
            self._headers(content_type, len(body))
            self.send_header("X-Orrery-Broker-Cache", "HIT")
            self.end_headers()
            self.wfile.write(body)
            return
        with self.state.flight(key):
            cached = self.state.cached(key)
            if cached:
                body, content_type = cached
                self.send_response(200)
                self._headers(content_type, len(body))
                self.send_header("X-Orrery-Broker-Cache", "HIT")
                self.end_headers()
                self.wfile.write(body)
                return
            try:
                reserved_tokens = self.state.token_ceiling(payload)
                self.state.reserve_request(reserved_tokens)
            except ValueError as error:
                self._json(400, {"error": str(error)})
                return
            except RuntimeError as error:
                self._json(429, {"error": str(error)})
                return
            try:
                import httpx

                with httpx.Client(
                    timeout=120, follow_redirects=False, trust_env=False
                ) as client:
                    response = client.post(
                        self.state.upstream_url,
                        json=payload,
                        headers=self._upstream_headers(),
                    )
                if 300 <= response.status_code < 400:
                    self._json(502, {"error": "upstream redirect refused"})
                    return
                body = response.content[:MAX_RESPONSE_BODY].replace(
                    self.state.provider_key.encode("utf-8"), b"[REDACTED]"
                )
                content_type = response.headers.get(
                    "Content-Type", "application/json; charset=utf-8"
                )
                tokens = None
                try:
                    reported = (response.json().get("usage") or {}).get("total_tokens")
                    tokens = int(reported) if reported is not None else None
                except (ValueError, TypeError, json.JSONDecodeError):
                    pass
                if tokens is not None and tokens >= 0:
                    self.state.settle_tokens(reserved_tokens, tokens)
                if (
                    response.status_code == 200
                    and len(response.content) <= MAX_RESPONSE_BODY
                ):
                    self.state.put_cache(key, body, content_type, tokens or 0)
                self.send_response(response.status_code)
                self._headers(content_type, len(body))
                self.send_header("X-Orrery-Broker-Cache", "MISS")
                self.end_headers()
                self.wfile.write(body)
            except Exception as error:  # noqa: BLE001
                message = str(error).replace(self.state.provider_key, "[REDACTED]")
                self._json(502, {"error": message[:500]})

    def _stream_upstream(self, payload: dict) -> None:
        try:
            reserved_tokens = self.state.token_ceiling(payload)
            self.state.reserve_request(reserved_tokens)
        except ValueError as error:
            self._json(400, {"error": str(error)})
            return
        except RuntimeError as error:
            self._json(429, {"error": str(error)})
            return
        try:
            import httpx

            with httpx.Client(
                timeout=120, follow_redirects=False, trust_env=False
            ) as client:
                with client.stream(
                    "POST",
                    self.state.upstream_url,
                    json=payload,
                    headers=self._upstream_headers(),
                ) as response:
                    if 300 <= response.status_code < 400:
                        self._json(502, {"error": "upstream redirect refused"})
                        return
                    self.send_response(response.status_code)
                    self._headers(
                        response.headers.get("Content-Type", "text/event-stream"),
                        cache="no-cache",
                    )
                    self.send_header("Connection", "close")
                    self.end_headers()
                    secret_bytes = self.state.provider_key.encode("utf-8")
                    pending = b""
                    for chunk in response.iter_bytes():
                        if chunk:
                            pending += chunk
                            keep = max(0, len(secret_bytes) - 1)
                            if len(pending) <= keep:
                                continue
                            emit, pending = pending[:-keep] if keep else pending, (
                                pending[-keep:] if keep else b""
                            )
                            self.wfile.write(emit.replace(secret_bytes, b"[REDACTED]"))
                            self.wfile.flush()
                    if pending:
                        self.wfile.write(pending.replace(secret_bytes, b"[REDACTED]"))
                        self.wfile.flush()
                    self.close_connection = True
        except Exception as error:  # noqa: BLE001
            message = str(error).replace(self.state.provider_key, "[REDACTED]")
            if not self.wfile.closed:
                try:
                    self.wfile.write(("\n[[ERROR]] " + message[:500]).encode("utf-8"))
                except OSError:
                    pass

    def do_OPTIONS(self) -> None:
        self._json(403, {"error": "CORS is disabled"})

    def log_message(self, fmt, *args) -> None:
        sys.stderr.write("broker %s %s\n" % (self.command, self.path))


class BrokerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True


def build_server(state: BrokerState, port: int) -> ThreadingHTTPServer:
    server = BrokerHTTPServer(("127.0.0.1", port), BrokerHandler)
    server.state = state  # type: ignore[attr-defined]
    return server


def _require_keyring() -> None:
    if os.environ.get("ORRERY_TEST_IN_MEMORY_KEYRING") == "1":
        return
    try:
        import keyring  # noqa: F401
    except ImportError:
        raise SystemExit("需要 keyring 包：pip install keyring")


def configure_broker(config: dict, provider_key: str = "") -> tuple[dict, str]:
    """Persist one Broker upstream registration without exposing its Provider key."""
    _require_keyring()
    previous = _read_config()
    try:
        previous = _validated_config(previous)
    except ValueError:
        previous = {}
    data = _validated_config(config)
    provider_key = provider_key.strip()
    if provider_key:
        _llm.store_key(
            provider_key,
            data["provider"],
            data["baseUrl"],
            namespace=BROKER_NAMESPACE,
        )
    stored = _llm._keyring_get(
        data["provider"], data["baseUrl"], namespace=BROKER_NAMESPACE
    )
    if not stored:
        raise ValueError("Broker 缺少当前上游 Provider 绑定的 API Key")
    token = _token_get() or secrets.token_urlsafe(32)
    _token_set(token)
    _write_config(data)
    if previous and (
        previous.get("provider") != data["provider"]
        or previous.get("baseUrl") != data["baseUrl"]
    ):
        _llm.delete_key(
            previous["provider"],
            previous["baseUrl"],
            namespace=BROKER_NAMESPACE,
        )
    return data, token


def load_broker_state(*, database: Path | None = None) -> BrokerState:
    """Load the configured Provider key and client token into a Broker runtime."""
    _require_keyring()
    data = _validated_config(_read_config())
    provider_key = _llm._keyring_get(
        data["provider"], data["baseUrl"], namespace=BROKER_NAMESPACE
    )
    client_token = _token_get()
    if not provider_key or not client_token:
        raise RuntimeError("Broker 缺少 Provider Key 或 client token")
    return BrokerState(data, provider_key, client_token, database=database)


def delete_configured_provider_key() -> None:
    data = _validated_config(_read_config())
    _llm.delete_key(data["provider"], data["baseUrl"], namespace=BROKER_NAMESPACE)


def command_configure(args: argparse.Namespace) -> int:
    config = {
        "provider": args.provider,
        "baseUrl": args.base_url,
        "model": args.model,
        "intentModel": args.intent_model,
        "auditModel": args.audit_model,
        "dailyRequestLimit": args.daily_request_limit,
        "dailyTokenLimit": args.daily_token_limit,
        "cacheTtlSeconds": args.cache_ttl,
    }
    key = getpass.getpass("粘贴上游 Provider API Key（输入不回显）: ").strip()
    if not key:
        raise SystemExit("空输入，已取消。")
    configure_broker(config, key)
    print("Broker 配置完成；Provider Key 已绑定到 Broker OS 身份的凭据槽。")
    print("运行 client-token 子命令取得一次性复制用的 Broker client token。")
    return 0


def command_status(_args: argparse.Namespace) -> int:
    _require_keyring()
    raw = _read_config()
    if not raw:
        print("Broker 尚未配置。")
        return 1
    try:
        data = _validated_config(raw)
    except ValueError as error:
        print("Broker 配置无效：%s" % error)
        return 1
    has_key = bool(
        _llm._keyring_get(data["provider"], data["baseUrl"], namespace=BROKER_NAMESPACE)
    )
    print(
        json.dumps(
            {
                "configured": True,
                "provider": data["provider"],
                "baseUrl": data["baseUrl"],
                "allowedModels": data["allowedModels"],
                "hasProviderKey": has_key,
                "hasClientToken": bool(_token_get()),
                "configPath": str(config_path()),
                "cachePath": str(cache_path()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if has_key and _token_get() else 1


def command_client_token(_args: argparse.Namespace) -> int:
    _require_keyring()
    token = _token_get()
    if not token:
        raise SystemExit("Broker client token 尚未生成；请先 configure。")
    print(token)
    return 0


def command_rotate_token(_args: argparse.Namespace) -> int:
    _require_keyring()
    token = secrets.token_urlsafe(32)
    _token_set(token)
    print(token)
    return 0


def command_delete_key(_args: argparse.Namespace) -> int:
    _require_keyring()
    delete_configured_provider_key()
    print("Broker Provider Key 已删除；非秘密配置和 client token 保留。")
    return 0


def command_serve(args: argparse.Namespace) -> int:
    try:
        state = load_broker_state()
    except (RuntimeError, ValueError) as error:
        raise SystemExit("%s；请先 configure。" % error) from error
    data = state.config
    server = build_server(state, args.port)
    port = int(server.server_address[1])
    print("Project Orrery Broker: http://127.0.0.1:%d/v1" % port, flush=True)
    print(
        "Provider=%s | Base=%s | models=%s"
        % (data["provider"], data["baseUrl"], ",".join(data["allowedModels"])),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project Orrery deterministic local LLM broker"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    configure = sub.add_parser(
        "configure", help="store a bound Provider key and non-secret broker config"
    )
    configure.add_argument(
        "--provider", required=True, choices=("openai", "deepseek", "custom")
    )
    configure.add_argument("--base-url", required=True)
    configure.add_argument("--model", required=True)
    configure.add_argument("--intent-model", default="")
    configure.add_argument("--audit-model", default="")
    configure.add_argument("--daily-request-limit", type=int, default=100)
    configure.add_argument("--daily-token-limit", type=int, default=1_000_000)
    configure.add_argument("--cache-ttl", type=int, default=7 * 86400)
    configure.set_defaults(func=command_configure)
    sub.add_parser("status", help="show non-secret status").set_defaults(
        func=command_status
    )
    sub.add_parser(
        "client-token", help="print the broker client token, never the Provider key"
    ).set_defaults(func=command_client_token)
    sub.add_parser(
        "rotate-client-token", help="rotate and print the broker client token"
    ).set_defaults(func=command_rotate_token)
    sub.add_parser(
        "delete-key", help="delete only the Broker Provider key"
    ).set_defaults(func=command_delete_key)
    serve = sub.add_parser("serve", help="start the loopback broker")
    serve.add_argument("--port", type=int, default=8788)
    serve.set_defaults(func=command_serve)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
