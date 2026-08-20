#!/usr/bin/env python3
"""Register docsite credentials through the Broker-only gateway.

The default mode configures the managed local Broker: the Provider key is
stored in the Broker namespace and docsite receives only a Broker client token.
Use ``--external-broker`` when a Broker is already running under another OS
identity; in that mode this command stores only its client token.

    python scripts/docsite/set_key.py
    python scripts/docsite/set_key.py --external-broker --base-url http://127.0.0.1:8788/v1
    python scripts/docsite/set_key.py --status
    python scripts/docsite/set_key.py --delete
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _llm  # noqa: E402
import llm_broker  # noqa: E402


_PRESETS = {
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "deepseek": ("https://api.deepseek.com", "deepseek-chat"),
    "custom": ("", ""),
}


def _managed_broker_url(current: dict) -> str:
    if current.get("provider") == "broker" and current.get("broker_mode") == "managed":
        try:
            return _llm.validate_provider_endpoint(
                "broker", current.get("base_url") or ""
            )[1]
        except ValueError:
            pass
    raw_port = os.environ.get("DOCSITE_MANAGED_BROKER_PORT", "0")
    try:
        port = int(raw_port)
    except ValueError as error:
        raise ValueError("DOCSITE_MANAGED_BROKER_PORT 必须是整数") from error
    if not 0 <= port <= 65535:
        raise ValueError("Broker 端口必须在 0..65535；0 表示启动时自动分配")
    return "http://127.0.0.1:%d/v1" % port


def _status(current: dict) -> int:
    mode = current.get("broker_mode") or (
        "external" if current.get("provider") == "broker" else "unmigrated"
    )
    print("gateway=broker-only | mode=%s" % mode)
    if current.get("provider") != "broker":
        print("尚未迁移：检测到直接 Provider 配置，docsite 不会使用它。")
        return 1
    base_url = current.get("base_url") or ""
    has_client = bool(base_url and _llm._keyring_get("broker", base_url))
    print(
        "broker=%s | client-token=%s"
        % (base_url or "<unset>", "已绑定" if has_client else "缺失")
    )
    if mode == "managed":
        raw = llm_broker._read_config()
        try:
            broker = llm_broker._validated_config(raw)
            has_provider = bool(
                _llm._keyring_get(
                    broker["provider"],
                    broker["baseUrl"],
                    namespace=llm_broker.BROKER_NAMESPACE,
                )
            )
            print(
                "upstream=%s %s | provider-key=%s"
                % (
                    broker["provider"],
                    broker["baseUrl"],
                    "已注册" if has_provider else "缺失",
                )
            )
        except ValueError as error:
            print("本机 Broker 配置无效：%s" % error)
            return 1
    return 0 if has_client else 1


def _delete(current: dict) -> int:
    if current.get("provider") == "broker" and current.get("base_url"):
        _llm.delete_key("broker", current["base_url"])
    if current.get("broker_mode") == "managed":
        try:
            llm_broker.delete_configured_provider_key()
        except (ValueError, RuntimeError):
            pass
        llm_broker._token_delete()
    _llm.delete_legacy_key()
    print(
        "已删除 docsite 的 Broker client token；本机托管模式也已删除上游 Provider Key。"
    )
    return 0


def _configure_managed(args: argparse.Namespace, current: dict) -> int:
    raw = llm_broker._read_config()
    current_upstream = (
        current.get("upstream_provider") or raw.get("provider") or "deepseek"
    )
    if current_upstream not in _PRESETS:
        current_upstream = "deepseek"
    provider = args.provider or current_upstream
    preset_base, preset_model = _PRESETS[provider]
    base_url = (
        args.base_url
        or current.get("upstream_base_url")
        or raw.get("baseUrl")
        or preset_base
    )
    model = args.model or current.get("model") or raw.get("model") or preset_model
    if not base_url or not model:
        raise ValueError("自定义上游必须显式提供 --base-url 和 --model")
    provider, base_url = _llm.validate_provider_endpoint(provider, base_url)
    key = getpass.getpass("粘贴上游 Provider API Key（输入不回显）: ").strip()
    if not key:
        raise ValueError("空输入，已取消")
    broker_config = {
        "provider": provider,
        "baseUrl": base_url,
        "model": model,
        "intentModel": args.intent_model
        or current.get("intent_model")
        or raw.get("intentModel")
        or "",
        "auditModel": args.audit_model
        or current.get("audit_model")
        or raw.get("auditModel")
        or "",
        "dailyRequestLimit": raw.get("dailyRequestLimit", 100),
        "dailyTokenLimit": raw.get("dailyTokenLimit", 1_000_000),
        "cacheTtlSeconds": raw.get("cacheTtlSeconds", 7 * 86400),
    }
    _, client_token = llm_broker.configure_broker(broker_config, key)
    broker_url = _managed_broker_url(current)
    _llm.store_key(client_token, "broker", broker_url)
    _llm.save_project_config(
        provider="broker",
        base_url=broker_url,
        model=model,
        intent_model=broker_config["intentModel"],
        audit_model=broker_config["auditModel"],
        enabled=True,
        broker_mode="managed",
        upstream_provider=provider,
        upstream_base_url=base_url,
    )
    if (
        current.get("provider")
        and current.get("base_url")
        and (
            current.get("provider") != "broker" or current.get("base_url") != broker_url
        )
    ):
        _llm.delete_key(current["provider"], current["base_url"])
    _llm.delete_legacy_key()
    print(
        "上游 API 已注册到本机 Broker；docsite 配置中只保留 Broker 端点和绑定 client token。"
    )
    print(
        "启动 docsite 后会自动启动托管 Broker：python -X utf8 scripts/docsite/serve.py"
    )
    return 0


def _configure_external(args: argparse.Namespace, current: dict) -> int:
    base_url = (
        args.base_url
        or (current.get("base_url") if current.get("broker_mode") == "external" else "")
        or "http://127.0.0.1:8788/v1"
    )
    _, base_url = _llm.validate_provider_endpoint("broker", base_url)
    model = args.model or current.get("model") or "gpt-4o-mini"
    token = getpass.getpass("粘贴外部 Broker client token（输入不回显）: ").strip()
    if not token:
        raise ValueError("空输入，已取消")
    _llm.store_key(token, "broker", base_url)
    _llm.save_project_config(
        provider="broker",
        base_url=base_url,
        model=model,
        intent_model=args.intent_model or current.get("intent_model") or "",
        audit_model=args.audit_model or current.get("audit_model") or "",
        enabled=True,
        broker_mode="external",
    )
    if current.get("broker_mode") == "managed":
        try:
            llm_broker.delete_configured_provider_key()
        except (ValueError, RuntimeError):
            pass
        llm_broker._token_delete()
    if (
        current.get("provider")
        and current.get("base_url")
        and (current.get("provider") != "broker" or current.get("base_url") != base_url)
    ):
        _llm.delete_key(current["provider"], current["base_url"])
    _llm.delete_legacy_key()
    print("已绑定外部隔离 Broker；本机未保存上游 Provider Key。")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register docsite AI access through Broker only."
    )
    parser.add_argument(
        "--delete", action="store_true", help="remove Broker credentials"
    )
    parser.add_argument(
        "--status", action="store_true", help="show Broker registration status"
    )
    parser.add_argument(
        "--external-broker",
        action="store_true",
        help="bind an isolated external Broker",
    )
    parser.add_argument(
        "--provider",
        choices=("openai", "deepseek", "custom"),
        help="managed Broker upstream",
    )
    parser.add_argument(
        "--base-url", help="upstream URL, or Broker URL with --external-broker"
    )
    parser.add_argument("--model", help="default model")
    parser.add_argument("--intent-model", default="", help="optional retrieval model")
    parser.add_argument("--audit-model", default="", help="optional synthesis model")
    args = parser.parse_args()
    current = _llm.load_config(read_credential=False)
    try:
        if args.status:
            raise SystemExit(_status(current))
        if args.delete:
            raise SystemExit(_delete(current))
        result = (
            _configure_external(args, current)
            if args.external_broker
            else _configure_managed(args, current)
        )
        raise SystemExit(result)
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
