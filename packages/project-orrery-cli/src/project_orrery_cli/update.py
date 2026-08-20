"""Check releases and migration compatibility without changing local state."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from project_orrery_core.compatibility import (
    compatibility_with_environment,
    direct_upgrade_supported,
    parse_version,
    target_dimensions,
)

from .context import CliContext, repository_context


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the latest Project Orrery release and target compatibility without modifying files."
    )
    parser.add_argument("--target", type=Path, help="Optional target repository containing .project-orrery.json")
    parser.add_argument("--manifest-url", help="Override the stable release manifest URL")
    parser.add_argument("--manifest-file", type=Path, help="Read a release manifest from disk (for mirrors/tests)")
    parser.add_argument("--cache-hours", type=float, default=24.0, help="Reuse a remote result for this many hours")
    parser.add_argument("--offline", action="store_true", help="Do not access the network; a cached result may be used")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args(argv)


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read release manifest {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("name") != "project-orrery":
        raise ValueError(f"invalid Project Orrery release manifest: {path}")
    parse_version(str(payload.get("version", "")))
    return payload


def cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return Path(tempfile.gettempdir()) / "project-orrery-update-cache" / f"{digest}.json"


def read_cached(path: Path, maximum_age_hours: float | None) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    if maximum_age_hours is not None:
        age_seconds = dt.datetime.now().timestamp() - path.stat().st_mtime
        if age_seconds > max(0.0, maximum_age_hours) * 3600:
            return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def fetch_latest(
    args: argparse.Namespace,
    local: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str, str | None]:
    if args.manifest_file:
        return read_manifest(args.manifest_file.expanduser().resolve()), "file", None

    url = args.manifest_url or local.get("latest_manifest_url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        return None, "unavailable", "local manifest has no valid update URL"
    cached_at = cache_path(url)
    cached = read_cached(cached_at, None if args.offline else args.cache_hours)
    if cached is not None:
        return cached, "cache-offline" if args.offline else "cache", None
    if args.offline:
        return None, "offline", "offline mode has no cached release manifest"

    request = urllib.request.Request(url, headers={"User-Agent": "Project-Orrery-update-checker"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("name") != "project-orrery":
            raise ValueError("remote response is not a Project Orrery release manifest")
        parse_version(str(payload.get("version", "")))
        cached_at.parent.mkdir(parents=True, exist_ok=True)
        cached_at.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return payload, "network", None
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        stale = read_cached(cached_at, None)
        if stale is not None:
            return stale, "stale-cache", f"network check failed; using stale cache: {exc}"
        return None, "unavailable", f"update check failed: {exc}"


def target_manifest(target: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    if target is None:
        return None, None
    path = target.expanduser().resolve() / ".project-orrery.json"
    if not path.is_file():
        return None, f"target has no {path.name}; compatibility applies to the Skill only"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"target manifest is unreadable: {exc}"
    if not isinstance(payload, dict):
        return None, "target manifest is not a JSON object"
    return payload, None


def evaluate(
    local: Mapping[str, Any],
    latest: Mapping[str, Any] | None,
    target: Mapping[str, Any] | None,
    source: str,
    warning: str | None,
) -> dict[str, Any]:
    local_version = str(local["version"])
    target_format, target_schema, target_toolchain = target_dimensions(target)
    result: dict[str, Any] = {
        "status": "unknown",
        "update_available": False,
        "migration_required": False,
        "local_skill_version": local_version,
        "latest_version": None,
        "target_toolchain_version": target_toolchain,
        "target_document_schema": target_schema,
        "target_manifest_format": target_format,
        "source": source,
        "warning": warning,
        "release_url": None,
        "skill_url": None,
        "reasons": [],
    }
    if latest is None:
        result["reasons"] = [warning or "latest release could not be determined"]
        return result

    latest_version = str(latest["version"])
    result["latest_version"] = latest_version
    distribution = latest.get("distribution", {})
    if isinstance(distribution, Mapping):
        result["release_url"] = distribution.get("release_url")
        result["skill_url"] = distribution.get("skill_url")

    current_tuple = parse_version(local_version)
    latest_tuple = parse_version(latest_version)
    if latest_tuple < current_tuple:
        result["status"] = "installed_newer"
        return result
    if latest_tuple == current_tuple:
        compatible, reasons = compatibility_with_environment(latest, target)
        result["status"] = "up_to_date" if compatible else "current_incompatible"
        result["migration_required"] = not compatible
        result["reasons"] = reasons
        return result

    result["update_available"] = True
    compatible, reasons = compatibility_with_environment(latest, target)
    direct = direct_upgrade_supported(local_version, latest.get("compatibility", {}).get("direct_upgrade_from"))
    if compatible and direct:
        result["status"] = "update_available_compatible"
    else:
        result["status"] = "update_available_migration_required"
        result["migration_required"] = True
        if not direct:
            reasons.insert(0, f"{local_version} is outside the release's direct-upgrade range")
    result["reasons"] = reasons
    return result


def print_human(result: Mapping[str, Any]) -> None:
    labels = {
        "up_to_date": "up to date",
        "update_available_compatible": "compatible update available",
        "update_available_migration_required": "update requires migration review",
        "installed_newer": "installed version is newer than the stable channel",
        "current_incompatible": "current Skill does not support this target schema",
        "unknown": "latest release unknown",
    }
    print("Project Orrery update status")
    print(f"- Local Skill: {result['local_skill_version']}")
    print(f"- Latest stable: {result['latest_version'] or 'unknown'} ({result['source']})")
    if result.get("target_toolchain_version") is not None:
        print(f"- Target toolchain: {result['target_toolchain_version']}")
        print(f"- Target document schema: {result['target_document_schema']}")
    print(f"- Result: {labels.get(result['status'], result['status'])}")
    for reason in result.get("reasons", []):
        print(f"  - {reason}")
    if result.get("warning"):
        print(f"WARNING: {result['warning']}")
    if result.get("release_url"):
        print(f"Release: {result['release_url']}")
    if result["status"] == "update_available_compatible":
        print("Next: install the tagged Skill, then preview the target tool upgrade with --upgrade-tools --dry-run.")
    elif result.get("migration_required"):
        print("Next: stop automatic upgrading and review the release migration notes against the target project.")


def main(argv: list[str] | None = None, *, context: CliContext | None = None) -> int:
    args = parse_args(argv)
    active = context or repository_context()
    local = dict(active.release.payload)
    try:
        parse_version(str(local.get("version", "")))
        latest, source, fetch_warning = fetch_latest(args, local)
        target, target_warning = target_manifest(args.target)
        warnings = "; ".join(item for item in (fetch_warning, target_warning) if item) or None
        result = evaluate(local, latest, target, source, warnings)
    except ValueError as exc:
        result = {
            "status": "unknown",
            "update_available": False,
            "migration_required": False,
            "local_skill_version": "unknown",
            "latest_version": None,
            "target_toolchain_version": None,
            "target_document_schema": None,
            "target_manifest_format": None,
            "source": "error",
            "warning": str(exc),
            "release_url": None,
            "skill_url": None,
            "reasons": [str(exc)],
        }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
