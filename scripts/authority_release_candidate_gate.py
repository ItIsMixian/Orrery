#!/usr/bin/env python3
"""Build and validate an offline Authority Model release candidate.

This is a local candidate gate, not a publisher. It never edits the source
release manifest, creates a tag, uses the network, or marks a candidate as a
public release. The caller supplies the candidate SemVer and manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "project-orrery"
POLICY_PATH = REPOSITORY_ROOT / "packaging" / "authority-release-candidate-policy.json"
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")
SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9]{20,}"),
    re.compile(rb"ghp_[A-Za-z0-9]{20,}"),
    re.compile(rb"AKIA[A-Z0-9]{16}"),
)
SENSITIVE_MANIFEST_KEYS = {
    "api_key",
    "apikey",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "provider_key",
    "secret",
    "token",
}
SUBPROCESS_TIMEOUT_SECONDS = 120
SUBPROCESS_ENV_ALLOWLIST = {
    "COMSPEC",
    "NUMBER_OF_PROCESSORS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "WINDIR",
}


class CandidateGateError(RuntimeError):
    """Raised when a candidate cannot safely cross the local gate."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateGateError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CandidateGateError(f"JSON root must be an object: {path}")
    return payload


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256(path.read_bytes())


def _canonical_text_sha256(path: Path) -> str:
    """Hash tracked JSON content independently of checkout line endings."""

    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return _sha256(content)


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise CandidateGateError(f"candidate version is not supported SemVer: {value!r}")
    return tuple(int(part) for part in match.groups())


def _source_files(policy: Mapping[str, Any]) -> list[Path]:
    forbidden_parts = tuple(
        tuple(PurePosixPath(str(value)).parts)
        for value in policy["forbidden_archive_parts"]
    )
    forbidden_names = {str(value).casefold() for value in policy["forbidden_archive_names"]}
    files: list[Path] = []
    for path in sorted(SKILL_ROOT.rglob("*")):
        if path.is_symlink():
            raise CandidateGateError(
                f"release source symlinks are not allowed: {path.relative_to(SKILL_ROOT).as_posix()}"
            )
        if not path.is_file():
            continue
        relative = path.relative_to(SKILL_ROOT).as_posix()
        folded_parts = tuple(part.casefold() for part in PurePosixPath(relative).parts)
        forbidden = any(
            tuple(part.casefold() for part in blocked)
            == folded_parts[index : index + len(blocked)]
            for blocked in forbidden_parts
            for index in range(0, len(folded_parts) - len(blocked) + 1)
        )
        if (
            path.name == ".DS_Store"
            or "__pycache__" in path.parts
            or path.suffix in {".pyc", ".pyo"}
        ):
            continue
        if path.name.casefold() in forbidden_names:
            raise CandidateGateError(f"forbidden release input: {relative}")
        if forbidden:
            raise CandidateGateError(f"forbidden release input: {relative}")
        content = path.read_bytes()
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            raise CandidateGateError(f"possible plaintext credential in release input: {relative}")
        files.append(path)
    return files


def _matches_forbidden_parts(parts: tuple[str, ...], policy: Mapping[str, Any]) -> bool:
    folded_parts = tuple(part.casefold() for part in parts)
    for value in policy["forbidden_archive_parts"]:
        blocked = tuple(
            part.casefold() for part in PurePosixPath(str(value)).parts
        )
        if any(
            folded_parts[index : index + len(blocked)] == blocked
            for index in range(0, len(folded_parts) - len(blocked) + 1)
        ):
            return True
    return False


def _validate_historical_inputs(policy: Mapping[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in policy["historical_inputs"].items():
        digest = _canonical_text_sha256(REPOSITORY_ROOT / relative)
        if digest != expected:
            raise CandidateGateError(
                f"historical input changed: {relative}; expected {expected}, got {digest}"
            )
        observed[str(relative)] = digest
    return observed


def _validate_candidate_manifest(
    payload: Mapping[str, Any], policy: Mapping[str, Any], expected_version: str | None
) -> tuple[str, tuple[int, ...]]:
    def reject_sensitive(value: Any, trail: tuple[str, ...] = ()) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                normalized = str(key).casefold().replace("-", "_")
                if normalized in SENSITIVE_MANIFEST_KEYS:
                    location = ".".join((*trail, str(key)))
                    raise CandidateGateError(
                        f"candidate release manifest contains forbidden secret field: {location}"
                    )
                reject_sensitive(nested, (*trail, str(key)))
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                reject_sensitive(nested, (*trail, str(index)))

    reject_sensitive(payload)
    sys.path.insert(0, str(CORE_SOURCE))
    try:
        from project_orrery_core.manifests import ReleaseContract
    finally:
        sys.path.pop(0)

    try:
        contract = ReleaseContract(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise CandidateGateError(f"invalid candidate release contract: {exc}") from exc
    version = contract.version
    current = _read_object(SKILL_ROOT / "release-manifest.json")
    if _version_tuple(version) <= _version_tuple(str(current["version"])):
        raise CandidateGateError(
            f"candidate version {version} must be newer than historical {current['version']}"
        )
    if expected_version is not None and version != expected_version:
        raise CandidateGateError(
            f"candidate version {version} does not match reviewed version {expected_version}"
        )
    expected_default = int(policy["authority_model"]["default"])
    expected_supported = tuple(policy["authority_model"]["supported"])
    if contract.authority_model_version != expected_default:
        raise CandidateGateError("candidate release must default to Authority Model 1")
    if contract.supported_authority_model_versions != expected_supported:
        raise CandidateGateError(
            "candidate release must declare the exact discrete Authority support set [1]"
        )
    distribution = payload.get("distribution")
    if not isinstance(distribution, Mapping) or distribution.get("tag") != f"v{version}":
        raise CandidateGateError("candidate distribution tag must equal v<candidate version>")
    return version, expected_supported


def _candidate_manifest_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _zip_mode(relative: str) -> int:
    return 0o755 if Path(relative).suffix.casefold() in {".py", ".bat", ".cmd", ".sh"} else 0o644


def build_candidate_archive(
    destination: Path,
    *,
    candidate_manifest: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    manifest_bytes = _candidate_manifest_bytes(candidate_manifest)
    entries: list[dict[str, str]] = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in _source_files(policy):
            relative = source.relative_to(SKILL_ROOT).as_posix()
            content = manifest_bytes if relative == "release-manifest.json" else source.read_bytes()
            archive_name = f"project-orrery/{relative}"
            info = zipfile.ZipInfo(archive_name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = _zip_mode(relative) << 16
            bundle.writestr(info, content, compresslevel=9)
            entries.append({"path": archive_name, "sha256": _sha256(content)})
    return _file_sha256(destination), entries


def _inspect_and_extract(archive: Path, destination: Path, policy: Mapping[str, Any]) -> None:
    forbidden_names = {str(value).casefold() for value in policy["forbidden_archive_names"]}
    seen: set[str] = set()
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            name = info.filename
            pure = PurePosixPath(name)
            canonical_name = name.casefold()
            if (
                "\\" in name
                or canonical_name in seen
                or pure.is_absolute()
                or ".." in pure.parts
                or not pure.parts
                or pure.parts[0] != "project-orrery"
            ):
                raise CandidateGateError(f"unsafe or duplicate archive entry: {name}")
            seen.add(canonical_name)
            if stat.S_ISLNK((info.external_attr >> 16) & 0xFFFF):
                raise CandidateGateError(f"archive symlink is not allowed: {name}")
            if pure.name.casefold() in forbidden_names:
                raise CandidateGateError(f"forbidden archive entry: {name}")
            if _matches_forbidden_parts(tuple(pure.parts), policy):
                raise CandidateGateError(f"forbidden archive entry: {name}")
            content = bundle.read(info)
            if any(pattern.search(content) for pattern in SECRET_PATTERNS):
                raise CandidateGateError(
                    f"possible plaintext credential in archive entry: {name}"
                )
            target = destination.joinpath(*pure.parts)
            try:
                target.resolve(strict=False).relative_to(destination.resolve())
            except ValueError as exc:
                raise CandidateGateError(
                    f"archive entry escapes extraction root: {name}"
                ) from exc
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def _subprocess_environment(
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in SUBPROCESS_ENV_ALLOWLIST
    }
    environment["PYTHONUTF8"] = "1"
    if extra is not None:
        environment.update(extra)
    return environment


def _run(
    command: list[str], *, cwd: Path, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=dict(env) if env is not None else _subprocess_environment(),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise CandidateGateError(
            f"subprocess exceeded {SUBPROCESS_TIMEOUT_SECONDS}s timeout: {command[0]}"
        ) from exc


def _require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode:
        raise CandidateGateError(
            f"{label} failed ({result.returncode}): {(result.stdout + result.stderr).strip()}"
        )


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _source_cli_environment() -> dict[str, str]:
    sources = os.pathsep.join(str(path) for path in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE))
    return _subprocess_environment({"PYTHONPATH": sources})


def _json_command(arguments: list[str], *, cwd: Path) -> dict[str, Any]:
    result = _run(
        [sys.executable, "-X", "utf8", "-m", "project_orrery_cli", *arguments],
        cwd=cwd,
        env=_source_cli_environment(),
    )
    _require_success(result, " ".join(arguments[:1]))
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CandidateGateError(f"CLI did not return JSON: {result.stdout}") from exc
    if not isinstance(payload, dict):
        raise CandidateGateError("CLI response must be an object")
    return payload


def _offline_lifecycle(extracted_skill: Path, temporary: Path) -> dict[str, Any]:
    installer = extracted_skill / "scripts" / "install_project_orrery.py"
    public_installer = SKILL_ROOT / "scripts" / "install_project_orrery.py"

    new_target = temporary / "new-project"
    _require_success(
        _run([sys.executable, "-X", "utf8", str(installer), "--target", str(new_target), "--title", "Candidate New"], cwd=temporary),
        "offline new scaffold",
    )
    new_manifest = _read_object(new_target / ".project-orrery.json")
    if new_manifest.get("authority_model_version") != 1:
        raise CandidateGateError("offline new scaffold did not select Authority Model 1")
    if new_manifest.get("authority_status") != "migration_pending":
        raise CandidateGateError("new scaffold selector was confused with adoption state")

    legacy_target = temporary / "legacy-project"
    _require_success(
        _run([sys.executable, "-X", "utf8", str(public_installer), "--target", str(legacy_target), "--title", "Legacy"], cwd=REPOSITORY_ROOT),
        "current-source v0.2-manifest legacy scaffold",
    )
    if "authority_model_version" in _read_object(legacy_target / ".project-orrery.json"):
        raise CandidateGateError("historical scaffold unexpectedly selected a model")
    _require_success(
        _run([sys.executable, "-X", "utf8", str(installer), "--target", str(legacy_target), "--upgrade-tools"], cwd=temporary),
        "candidate ordinary legacy upgrade",
    )
    legacy_manifest_path = legacy_target / ".project-orrery.json"
    legacy_manifest = _read_object(legacy_manifest_path)
    if "authority_model_version" in legacy_manifest:
        raise CandidateGateError("ordinary candidate upgrade silently migrated a legacy project")

    fail_closed: dict[str, bool] = {}
    for label, selector in (("unsupported", 2), ("invalid", True)):
        target = temporary / f"{label}-project"
        shutil.copytree(legacy_target, target)
        manifest_path = target / ".project-orrery.json"
        manifest = _read_object(manifest_path)
        manifest["authority_model_version"] = selector
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        before = _tree_digest(target)
        result = _run(
            [sys.executable, "-X", "utf8", str(installer), "--target", str(target), "--upgrade-tools"],
            cwd=temporary,
        )
        if result.returncode == 0 or _tree_digest(target) != before:
            raise CandidateGateError(f"{label} target did not fail closed without writes")
        fail_closed[label] = True

    before_migration = legacy_manifest_path.read_bytes()
    preview = _json_command(
        ["migrate-authority-model", "--target", str(legacy_target), "--to", "1", "--dry-run", "--json"],
        cwd=REPOSITORY_ROOT,
    )
    receipt = preview["data"]["apply_precondition"]["receipt"]
    applied = _json_command(
        ["migrate-authority-model", "--target", str(legacy_target), "--to", "1", "--apply", "--apply-receipt", receipt, "--json"],
        cwd=REPOSITORY_ROOT,
    )
    backup = applied["data"]["backup_path"]
    if _read_object(legacy_manifest_path).get("authority_model_version") != 1:
        raise CandidateGateError("explicit migration did not select Authority Model 1")
    restore_preview = _json_command(
        ["restore-authority-model", "--target", str(legacy_target), "--backup", backup, "--dry-run", "--json"],
        cwd=REPOSITORY_ROOT,
    )
    restore_receipt = restore_preview["data"]["restore_precondition"]["receipt"]
    _json_command(
        ["restore-authority-model", "--target", str(legacy_target), "--backup", backup, "--apply", "--restore-receipt", restore_receipt, "--json"],
        cwd=REPOSITORY_ROOT,
    )
    if legacy_manifest_path.read_bytes() != before_migration:
        raise CandidateGateError("Authority restore did not recover exact pre-migration bytes")

    return {
        "offline_installer": {
            "new_scaffold": "authority-model-1-selected-adoption-pending",
            "legacy_baseline": "current-source-with-public-v0.2-manifest",
            "legacy_ordinary_upgrade": "selector-missing-preserved",
            "fail_closed_targets": fail_closed,
        },
        "explicit_authority_lifecycle": {
            "execution_path": "source-neutral-cli",
            "migration": "receipt-gated",
            "exact_restore": True,
        },
    }


def _validate_self_host(root: Path) -> dict[str, Any]:
    manifest = _read_object(root / ".project-orrery.json")
    if manifest.get("authority_model_version") != 1:
        raise CandidateGateError("self-host project does not explicitly select Authority Model 1")
    result = _run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SKILL_ROOT / "scripts" / "validate_installation.py"),
            "--target",
            str(root),
            "--require-integrated",
        ],
        cwd=REPOSITORY_ROOT,
    )
    _require_success(result, "self-host integrated validation")
    return {
        "authority_model_version": 1,
        "authority_status": manifest.get("authority_status"),
        "selector_is_not_implementation_evidence": True,
    }


def run_gate(
    *,
    candidate_manifest_path: Path,
    output_dir: Path,
    expected_version: str | None = None,
    self_host_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    if candidate_manifest_path.is_symlink() or not candidate_manifest_path.is_file():
        raise CandidateGateError("candidate manifest must be a regular non-symlink file")
    policy = _read_object(POLICY_PATH)
    candidate_bytes = candidate_manifest_path.read_bytes()
    if any(pattern.search(candidate_bytes) for pattern in SECRET_PATTERNS):
        raise CandidateGateError("candidate manifest appears to contain a plaintext credential")
    candidate = _read_object(candidate_manifest_path)
    version, supported = _validate_candidate_manifest(candidate, policy, expected_version)
    historical = _validate_historical_inputs(policy)

    archive_name = f"project-orrery-candidate-v{version}.zip"
    checksum_name = f"project-orrery-candidate-v{version}.sha256"
    receipt_name = f"project-orrery-candidate-v{version}.gate.json"
    if output_dir.exists():
        raise CandidateGateError(
            "candidate output directory must not already exist; refusing partial overwrite"
        )

    with tempfile.TemporaryDirectory(prefix="orrery-authority-release-gate-") as raw:
        temporary = Path(raw)
        first = temporary / "candidate-1.zip"
        second = temporary / "candidate-2.zip"
        first_hash, entries = build_candidate_archive(
            first, candidate_manifest=candidate, policy=policy
        )
        second_hash, second_entries = build_candidate_archive(
            second, candidate_manifest=candidate, policy=policy
        )
        if first_hash != second_hash or entries != second_entries or first.read_bytes() != second.read_bytes():
            raise CandidateGateError("candidate packaging is not byte-for-byte deterministic")
        extracted = temporary / "extracted"
        _inspect_and_extract(first, extracted, policy)
        packaged_manifest = _read_object(extracted / "project-orrery" / "release-manifest.json")
        if packaged_manifest != candidate:
            raise CandidateGateError("packaged candidate manifest differs from reviewed input")
        lifecycle = _offline_lifecycle(extracted / "project-orrery", temporary)
        self_host = _validate_self_host(self_host_root.expanduser().resolve())

        blockers = list(policy["release_blockers"])
        receipt: dict[str, Any] = {
            "contract": policy["contract"],
            "candidate_version": version,
            "candidate_manifest_source_sha256": _sha256(candidate_bytes),
            "candidate_manifest_packaged_sha256": _sha256(_candidate_manifest_bytes(candidate)),
            "authority_model": {"default": 1, "supported": list(supported)},
            "historical_inputs": historical,
            "archive": {
                "name": archive_name,
                "sha256": first_hash,
                "entry_count": len(entries),
                "entries": entries,
            },
            "offline_installer": lifecycle["offline_installer"],
            "explicit_authority_lifecycle": lifecycle[
                "explicit_authority_lifecycle"
            ],
            "self_host": self_host,
            "candidate_ready": True,
            "release_ready": False,
            "release_blockers": blockers,
            "claims_not_established": [
                "authority-consumer-production-switched",
                "authority-model-implemented-by-target-project",
                "authority-model-validated-by-selector",
                "public-release-created",
            ],
        }
        receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        checksum_bytes = f"{first_hash}  {archive_name}\n".encode("ascii")

        output_dir.parent.mkdir(parents=True, exist_ok=True)
        staged_output = Path(
            tempfile.mkdtemp(
                prefix=f".{output_dir.name}.staging-", dir=output_dir.parent
            )
        )
        try:
            shutil.copyfile(first, staged_output / archive_name)
            (staged_output / checksum_name).write_bytes(checksum_bytes)
            (staged_output / receipt_name).write_bytes(receipt_bytes)
            os.replace(staged_output, output_dir)
        except Exception:
            shutil.rmtree(staged_output, ignore_errors=True)
            raise
    return receipt


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate a local Authority Model release candidate without publishing"
    )
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-version")
    parser.add_argument("--self-host-root", type=Path, default=REPOSITORY_ROOT)
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    candidate_manifest = args.candidate_manifest.expanduser()
    if not candidate_manifest.is_absolute():
        candidate_manifest = Path.cwd() / candidate_manifest
    try:
        receipt = run_gate(
            candidate_manifest_path=candidate_manifest,
            output_dir=args.output_dir.expanduser().resolve(),
            expected_version=args.expected_version,
            self_host_root=args.self_host_root,
        )
    except (CandidateGateError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
