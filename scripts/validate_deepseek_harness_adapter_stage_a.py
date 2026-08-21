#!/usr/bin/env python3
"""Run the no-model DeepSeek Harness Adapter lifecycle in a fresh DSH_HOME."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_ROOT = REPOSITORY_ROOT / "adapters" / "deepseek-harness"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tgz"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dsh-js", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, default=DEFAULT_ADAPTER_ROOT)
    parser.add_argument("--node", default="node")
    parser.add_argument("--pnpm-store-dir", type=Path)
    return parser.parse_args()


def run(command: list[str], *, env: dict[str, str], cwd: Path, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
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


def copy_source(adapter_root: Path, destination: Path, version: str) -> None:
    shutil.copytree(adapter_root, destination)
    package_path = destination / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["version"] = version
    write_json(package_path, package)
    manifest_path = destination / "adapter-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["adapter"]["version"] = version
    write_json(manifest_path, manifest)


def build_tarball(source: Path, destination: Path) -> None:
    files = sorted(
        path
        for path in source.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(source).parts)
        and path.suffix not in EXCLUDED_SUFFIXES
    )
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for path in files:
                    relative = path.relative_to(source).as_posix()
                    payload = path.read_bytes()
                    info = tarfile.TarInfo(f"package/{relative}")
                    info.size = len(payload)
                    info.mtime = 0
                    info.mode = 0o755 if relative.startswith("scripts/") else 0o644
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    bundle.addfile(info, io.BytesIO(payload))


def profile_manifest(home: Path, profile: str) -> dict[str, Any]:
    return json.loads((home / "profiles" / profile / "package.json").read_text(encoding="utf-8"))


def write_probe(output: Path, marker: Path) -> Path:
    probe = output / "probe.mjs"
    probe.write_text(
        "\n".join(
            [
                "import { writeFileSync } from 'node:fs'",
                "export const name = 'project-orrery-stage-a-probe'",
                "export const inject = ['skills']",
                "export function apply(ctx) {",
                "  void ctx.loader.await().then(async () => {",
                "    const skills = await ctx.skills.list({ cwd: process.cwd() })",
                "    const loaded = await ctx.skills.get('project-orrery', { cwd: process.cwd() })",
                "    writeFileSync(process.env.ORRERY_DSH_PROBE, JSON.stringify({ skills, loaded }, null, 2))",
                "    process.emit('SIGTERM')",
                "  })",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    patch = output / "probe.patch.yml"
    patch.write_text(
        "\n".join(
            [
                "- insert:",
                "    - id: project-orrery-stage-a-probe",
                f"      name: {probe.as_uri()}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    marker.parent.mkdir(parents=True, exist_ok=True)
    return patch


def run_probe(
    node: str,
    dsh_js: Path,
    profile: str,
    patch: Path,
    marker: Path,
    *,
    env: dict[str, str],
    cwd: Path,
) -> dict[str, Any]:
    marker.unlink(missing_ok=True)
    probe_env = env.copy()
    probe_env["ORRERY_DSH_PROBE"] = str(marker)
    run([node, str(dsh_js), "--profile", profile, "--patch", str(patch)], env=probe_env, cwd=cwd)
    if not marker.is_file():
        raise RuntimeError("DeepSeek Harness probe did not write its discovery marker")
    return json.loads(marker.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    output = args.output_root.expanduser().resolve()
    dsh_js = args.dsh_js.expanduser().resolve()
    adapter_root = args.adapter_root.expanduser().resolve()
    if output.exists():
        print(f"ERROR: output root already exists: {output}", file=sys.stderr)
        return 2
    if output.anchor and output == Path(output.anchor):
        print(f"ERROR: refusing filesystem root: {output}", file=sys.stderr)
        return 2
    if not dsh_js.is_file():
        print(f"ERROR: dsh entrypoint not found: {dsh_js}", file=sys.stderr)
        return 2

    manifest = json.loads((adapter_root / "adapter-manifest.json").read_text(encoding="utf-8"))
    package_name = manifest["distribution"]["package_name"]
    current_version = manifest["adapter"]["version"]
    legacy_version = "0.0.9"
    profile = "orrery-stage-a"
    output.mkdir(parents=True)
    home = output / "dsh-home"
    project = output / "author-project"
    project.mkdir()
    authored = project / "AGENTS.md"
    authored.write_text("author-owned\n", encoding="utf-8")
    authored_before = sha256(authored)

    sources = output / "sources"
    old_source = sources / "old"
    current_source = sources / "current"
    copy_source(adapter_root, old_source, legacy_version)
    copy_source(adapter_root, current_source, current_version)
    old_package = output / f"{package_name}-{legacy_version}.tgz"
    current_package = output / f"{package_name}-{current_version}.tgz"
    build_tarball(old_source, old_package)
    build_tarball(current_source, current_package)

    env = os.environ.copy()
    env["DSH_HOME"] = str(home)
    env["DSH_AGENTS_HOME"] = str(output / "agents-home")
    env["DSH_TELEMETRY_DISABLED"] = "1"
    env["npm_config_cache"] = str(output / "npm-cache")
    store_dir = args.pnpm_store_dir.expanduser().resolve() if args.pnpm_store_dir else output / "pnpm-store"
    env["npm_config_store_dir"] = str(store_dir)
    env["PNPM_HOME"] = str(output / "pnpm-home")
    for key in ("DEEPSEEK_API_KEY", "DEEPSEEK_SEARCH_BASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(key, None)

    version_output = run([args.node, str(dsh_js), "--version"], env=env, cwd=project)
    add_old = run(
        [args.node, str(dsh_js), "plugin", "--profile", profile, "add", old_package.as_uri()],
        env=env,
        cwd=project,
    )
    old_profile = profile_manifest(home, profile)
    if old_profile.get("dependencies", {}).get(package_name) is None:
        raise RuntimeError("old Adapter dependency was not installed")
    if package_name not in old_profile.get("dsh", {}).get("profile", {}).get("bundles", []):
        raise RuntimeError("old Adapter bundle was not activated")

    dump_old = run(
        [args.node, str(dsh_js), "--profile", profile, "--dump-config"],
        env=env,
        cwd=project,
    )
    if "project-orrery-skill" not in dump_old.stdout:
        raise RuntimeError("composed config does not contain the Project Orrery plugin row")
    marker = output / "probe-installed.json"
    patch = write_probe(output, marker)
    discovered_old = run_probe(args.node, dsh_js, profile, patch, marker, env=env, cwd=project)
    old_match = [skill for skill in discovered_old.get("skills", []) if skill.get("name") == "project-orrery"]
    if len(old_match) != 1 or discovered_old.get("loaded", {}).get("provider") != "project-orrery":
        raise RuntimeError(f"unexpected old Adapter discovery result: {discovered_old!r}")

    add_current = run(
        [args.node, str(dsh_js), "plugin", "--profile", profile, "add", current_package.as_uri()],
        env=env,
        cwd=project,
    )
    current_profile = profile_manifest(home, profile)
    dependency = current_profile.get("dependencies", {}).get(package_name, "")
    if current_version not in dependency:
        raise RuntimeError(f"profile did not upgrade to {current_version}: {dependency!r}")
    update_current = run(
        [args.node, str(dsh_js), "plugin", "--profile", profile, "update", package_name],
        env=env,
        cwd=project,
    )
    discovered_current = run_probe(args.node, dsh_js, profile, patch, marker, env=env, cwd=project)
    current_match = [skill for skill in discovered_current.get("skills", []) if skill.get("name") == "project-orrery"]
    if len(current_match) != 1:
        raise RuntimeError(f"unexpected current Adapter discovery result: {discovered_current!r}")

    remove = run(
        [args.node, str(dsh_js), "plugin", "--profile", profile, "remove", package_name],
        env=env,
        cwd=project,
    )
    removed_profile = profile_manifest(home, profile)
    if package_name in removed_profile.get("dependencies", {}):
        raise RuntimeError("Adapter dependency remains after removal")
    if package_name in removed_profile.get("dsh", {}).get("profile", {}).get("bundles", []):
        raise RuntimeError("Adapter bundle remains active after removal")
    discovered_removed = run_probe(args.node, dsh_js, profile, patch, marker, env=env, cwd=project)
    if discovered_removed.get("skills"):
        raise RuntimeError(f"Adapter remains discoverable after removal: {discovered_removed!r}")
    if discovered_removed.get("loaded") is not None:
        raise RuntimeError(f"removed Adapter body still loaded: {discovered_removed!r}")
    if sha256(authored) != authored_before:
        raise RuntimeError("author-owned AGENTS.md changed during profile lifecycle")

    summary = {
        "result": "pass",
        "model_calls": 0,
        "credentials_copied": False,
        "dsh_version": version_output.stdout.strip(),
        "dsh_home": str(home),
        "profile": profile,
        "adapter_version": current_version,
        "legacy_version": legacy_version,
        "installed_old_dependency": old_profile["dependencies"][package_name],
        "installed_current_dependency": dependency,
        "discovered_old": old_match,
        "discovered_current": current_match,
        "discovered_after_remove": discovered_removed.get("skills", []),
        "author_file_sha256": authored_before,
        "package_sha256": {
            legacy_version: sha256(old_package),
            current_version: sha256(current_package),
        },
        "plugin_outputs": {
            "add_old": add_old.stdout.strip(),
            "add_current": add_current.stdout.strip(),
            "update_current": update_current.stdout.strip(),
            "remove": remove.stdout.strip(),
        },
    }
    write_json(output / "result.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
