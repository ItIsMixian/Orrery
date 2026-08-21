#!/usr/bin/env python3
"""Run the no-model Claude Code Adapter lifecycle in a fresh isolated home."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "claude-code"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, default=DEFAULT_ADAPTER_ROOT)
    parser.add_argument("--claude", default="claude")
    return parser.parse_args()


def run(command: list[str], *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command!r}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plugin_list(claude: str, *, env: dict[str, str], cwd: Path) -> list[dict[str, Any]]:
    result = run([claude, "plugin", "list", "--json"], env=env, cwd=cwd)
    parsed = json.loads(result.stdout)
    if not isinstance(parsed, list):
        raise RuntimeError("claude plugin list --json did not return a list")
    return parsed


def make_source(adapter_root: Path, source: Path, version: str, marketplace_name: str) -> None:
    if source.exists():
        shutil.rmtree(source)
    shutil.copytree(adapter_root, source)
    plugin_path = source / ".claude-plugin" / "plugin.json"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    plugin["version"] = version
    write_json(plugin_path, plugin)
    adapter_path = source / "adapter-manifest.json"
    adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
    adapter["adapter"]["version"] = version
    write_json(adapter_path, adapter)
    marketplace_path = source / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    marketplace["name"] = marketplace_name
    marketplace["plugins"][0]["version"] = version
    write_json(marketplace_path, marketplace)


def main() -> int:
    args = parse_args()
    output = args.output_root.expanduser().resolve()
    adapter_root = args.adapter_root.expanduser().resolve()
    if output.exists():
        print(f"ERROR: output root already exists: {output}", file=sys.stderr)
        return 2
    if output.anchor and output == Path(output.anchor):
        print(f"ERROR: refusing filesystem root: {output}", file=sys.stderr)
        return 2
    manifest = json.loads((adapter_root / "adapter-manifest.json").read_text(encoding="utf-8"))
    current_version = manifest["adapter"]["version"]
    legacy_version = "0.0.9"
    marketplace_name = "project-orrery-stage-a"
    plugin_id = f"project-orrery@{marketplace_name}"

    output.mkdir(parents=True)
    config = output / "claude-config"
    marketplace = output / "marketplace"
    source = marketplace / "plugin"
    project = output / "author-project"
    project.mkdir()
    authored = project / "AGENTS.md"
    authored.write_text("author-owned\n", encoding="utf-8")
    authored_before = sha256(authored)
    make_source(adapter_root, source, legacy_version, marketplace_name)

    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = str(config)
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
        env.pop(key, None)

    validate_marketplace = run([args.claude, "plugin", "validate", str(source)], env=env, cwd=project)
    validate_plugin = run(
        [args.claude, "plugin", "validate", str(source / ".claude-plugin" / "plugin.json")],
        env=env,
        cwd=project,
    )
    run([args.claude, "plugin", "marketplace", "add", str(source), "--scope", "user"], env=env, cwd=project)
    run([args.claude, "plugin", "install", plugin_id, "--scope", "user"], env=env, cwd=project)
    installed_old = plugin_list(args.claude, env=env, cwd=project)
    if len(installed_old) != 1 or installed_old[0].get("version") != legacy_version:
        raise RuntimeError(f"unexpected legacy install state: {installed_old!r}")

    make_source(adapter_root, source, current_version, marketplace_name)
    run([args.claude, "plugin", "marketplace", "update", marketplace_name], env=env, cwd=project)
    update = run([args.claude, "plugin", "update", plugin_id, "--scope", "user"], env=env, cwd=project)
    installed_current = plugin_list(args.claude, env=env, cwd=project)
    if len(installed_current) != 1 or installed_current[0].get("version") != current_version:
        raise RuntimeError(f"unexpected upgraded install state: {installed_current!r}")

    run(
        [args.claude, "plugin", "uninstall", plugin_id, "--scope", "user", "--keep-data"],
        env=env,
        cwd=project,
    )
    after_uninstall = plugin_list(args.claude, env=env, cwd=project)
    if after_uninstall:
        raise RuntimeError(f"plugin remains installed after uninstall: {after_uninstall!r}")
    if sha256(authored) != authored_before:
        raise RuntimeError("author-owned AGENTS.md changed during Plugin lifecycle")

    cache_versions = sorted(
        path.name
        for path in (config / "plugins" / "cache" / marketplace_name / "project-orrery").glob("*")
        if path.is_dir()
    )
    summary = {
        "result": "pass",
        "model_calls": 0,
        "credentials_copied": False,
        "claude_config_dir": str(config),
        "adapter_version": current_version,
        "legacy_version": legacy_version,
        "installed_old": installed_old,
        "installed_current": installed_current,
        "after_uninstall": after_uninstall,
        "cache_versions_after_uninstall": cache_versions,
        "author_file_sha256": authored_before,
        "validate_marketplace": validate_marketplace.stdout.strip(),
        "validate_plugin": validate_plugin.stdout.strip(),
        "update_output": update.stdout.strip(),
    }
    write_json(output / "result.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
