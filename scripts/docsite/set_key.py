#!/usr/bin/env python3
"""Securely store / clear the doc-copilot LLM API key — no plaintext on disk.

The key goes into the OS credential store (Windows Credential Manager / macOS
Keychain / Linux Secret Service) via the `keyring` package; `_llm.py` reads it
from there at runtime (priority just below environment variables).

    python scripts/docsite/set_key.py            # paste key (hidden input)
    python scripts/docsite/set_key.py --status   # is a key stored?
    python scripts/docsite/set_key.py --delete   # remove the stored key
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _llm  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Securely store the doc-copilot API key in the OS credential store (no plaintext)."
    )
    ap.add_argument("--delete", action="store_true", help="remove the stored key")
    ap.add_argument("--status", action="store_true", help="report whether a key is stored")
    args = ap.parse_args()

    try:
        import keyring  # noqa: F401
    except ImportError:
        sys.exit("需要 keyring 包：pip install keyring")

    if args.status:
        stored = _llm._keyring_get()
        backend = type(__import__("keyring").get_keyring()).__name__
        print(f"service={_llm.KEYRING_SERVICE} | backend={backend} | 已存储: {'是' if stored else '否'}")
        return

    if args.delete:
        _llm.delete_key()
        print("已从系统凭据库删除该 key。")
        return

    key = getpass.getpass("粘贴 API key（输入不回显，回车确认）: ").strip()
    if not key:
        sys.exit("空输入，已取消。")
    backend = _llm.store_key(key)
    ok = _llm._keyring_get() == key
    print(f"已安全存入：service={_llm.KEYRING_SERVICE}，backend={backend}，校验={'OK' if ok else '失败'}")
    print("以后直接启动即可，无需明文、无需环境变量：")
    print("  python -X utf8 scripts/docsite/serve.py")


if __name__ == "__main__":
    main()
