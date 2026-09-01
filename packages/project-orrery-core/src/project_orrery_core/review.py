"""Evidence-first local review, speculative integration, and conservative cleanup."""
from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import tempfile
import time
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping, Sequence

from .collaboration import (
    CAPABILITIES,
    COLLABORATION_CONTRACT_ID,
    COLLABORATION_SCHEMA_VERSION,
    _write_private_session,
    collect_scope_observation,
    inspect_worktree_status,
    load_collaboration_config,
    load_subsystem_registry,
    resolve_integration_oid,
    validate_collaboration_contract,
)
from .subprocess_policy import no_window_options


REVIEW_SCHEMA_VERSION = 1
REVIEW_DECISION_SCHEMA_VERSION = 1
CLOSURE_SCHEMA_VERSION = 2
INTEGRATION_DRY_RUN_SCHEMA_VERSION = 1
CLEANUP_ELIGIBILITY_SCHEMA_VERSION = 1
_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_PACKAGE_ID = re.compile(r"^review-[0-9a-f]{24}$")
_TEMPORARY_DECISION = re.compile(r"PO-DEC-[A-Za-z0-9][A-Za-z0-9-]*")
_FORMAL_ADR_PATH = re.compile(r"^docs/decisions/(\d{4})-[^/]+\.md$")
_FORMAL_ADR_REFERENCE = re.compile(r"ADR-(\d{4})")
_REVIEW_HASH_DOMAIN = b"project-orrery-review-package-v1\0"
_FINDING_SET_HASH_DOMAIN = b"project-orrery-review-finding-set-v1\0"
_DECISION_HASH_DOMAIN = b"project-orrery-review-decision-v1\0"
_CLOSURE_HASH_DOMAIN = b"project-orrery-closure-record-v1\0"
_RUN_HASH_DOMAIN = b"project-orrery-speculative-integration-v1\0"
_VALIDATION_HASH_DOMAIN = b"project-orrery-validation-set-v1\0"
_INVALIDATION_CONDITIONS = [
    "candidate-head-changed",
    "target-oid-changed",
    "scope-revision-changed",
    "scope-fingerprint-changed",
    "finding-set-changed",
    "collaboration-schema-changed",
    "review-package-content-changed",
    "validation-evidence-expired-or-changed",
]


def _utc_timestamp(value: str | None = None) -> str:
    return value or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_hash(domain: bytes, value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(domain + encoded).hexdigest()


def _git(
    repository: Path,
    *arguments: str,
    binary: bool = False,
    check: bool = True,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[Any]:
    env = {
        **os.environ,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_EDITOR": "true",
        "GIT_SEQUENCE_EDITOR": "true",
        "GIT_AUTHOR_NAME": "Project Orrery Dry Run",
        "GIT_AUTHOR_EMAIL": "orrery-dry-run@example.invalid",
        "GIT_COMMITTER_NAME": "Project Orrery Dry Run",
        "GIT_COMMITTER_EMAIL": "orrery-dry-run@example.invalid",
    }
    if environment:
        env.update(environment)
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
        check=False,
        env=env,
        **no_window_options(),
    )
    if check and completed.returncode:
        stderr = completed.stderr if isinstance(completed.stderr, str) else b""
        stdout = completed.stdout if isinstance(completed.stdout, str) else b""
        detail = str(stderr or stdout).strip()
        raise ValueError(
            f"Git operation failed for {' '.join(arguments)}" + (f": {detail}" if detail else "")
        )
    return completed


def _repository_root(project_root: Path) -> Path:
    value = str(_git(Path(project_root), "rev-parse", "--show-toplevel").stdout).strip()
    return Path(os.path.abspath(value))


def _common_git_dir(project_root: Path) -> Path:
    root = _repository_root(project_root)
    value = str(
        _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout
    ).strip()
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return Path(os.path.abspath(path))


def _private_area(project_root: Path, *parts: str, create: bool = False) -> Path:
    common = _common_git_dir(project_root)
    path = common.joinpath("orrery", *parts)
    try:
        path.resolve(strict=False).relative_to(common.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValueError("Git-private collaboration path escaped the common Git directory") from exc
    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(f"cannot create Git-private collaboration directory: {exc}") from exc
    return path


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix=f"{path.stem}.", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    except OSError as exc:
        raise ValueError(f"cannot write Git-private collaboration record: {exc}") from exc


def _read_regular_json(path: Path, *, description: str) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot inspect {description}: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"{description} must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {description}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return value


def _schema_hash() -> str:
    resource = files("project_orrery_core").joinpath("schema", "collaboration-v1.json")
    return hashlib.sha256(resource.read_bytes()).hexdigest()


def _finding_set_hash(session: Mapping[str, Any]) -> str:
    material = {
        "active": sorted(
            [dict(item) for item in session.get("findings", [])],
            key=lambda item: (str(item.get("finding_id")), str(item.get("finding_fingerprint"))),
        ),
        "history": sorted(
            [dict(item) for item in session.get("finding_history", [])],
            key=lambda item: (str(item.get("finding_id")), str(item.get("finding_fingerprint"))),
        ),
    }
    return _canonical_hash(_FINDING_SET_HASH_DOMAIN, material)


def _package_hash(package: Mapping[str, Any]) -> str:
    material = {key: value for key, value in package.items() if key not in {"package_id", "content_hash"}}
    return _canonical_hash(_REVIEW_HASH_DOMAIN, material)


def _validate_package_hash(package: Mapping[str, Any]) -> None:
    expected = _package_hash(package)
    if package.get("content_hash") != expected:
        raise ValueError("review package content hash does not match its evidence")
    if package.get("package_id") != f"review-{expected[:24]}":
        raise ValueError("review package ID does not match its content hash")


def load_review_package(project_root: Path, package: str | Path) -> dict[str, Any]:
    if isinstance(package, Path) or os.path.sep in os.fspath(package) or "/" in os.fspath(package):
        path = Path(package).expanduser().absolute()
        allowed = _private_area(project_root, "reviews", "packages")
        try:
            path.resolve(strict=True).relative_to(allowed.resolve(strict=True))
        except (OSError, ValueError) as exc:
            raise ValueError("review package path is outside the Git-private review area") from exc
    else:
        package_id = str(package)
        if not _PACKAGE_ID.fullmatch(package_id):
            raise ValueError("review package ID is invalid")
        path = _private_area(project_root, "reviews", "packages") / f"{package_id}.json"
    value = _read_regular_json(path, description="review package")
    validate_collaboration_contract(value)
    if value.get("contract_type") != "review-package":
        raise ValueError("review package has the wrong contract type")
    _validate_package_hash(value)
    value["_git_private_path"] = str(path)
    return value


def _changed_paths(repository: Path, target_oid: str, candidate_head: str) -> list[str]:
    raw = _git(
        repository,
        "diff",
        "--name-only",
        "-z",
        f"{target_oid}..{candidate_head}",
        binary=True,
    ).stdout
    assert isinstance(raw, bytes)
    return sorted(
        {
            item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
            for item in raw.split(b"\0")
            if item
        }
    )


def _diff_stat(repository: Path, target_oid: str, candidate_head: str) -> str:
    return str(
        _git(repository, "diff", "--stat", "--summary", f"{target_oid}..{candidate_head}").stdout
    ).strip()


def _path_matches(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/")
    if normalized.endswith("/**"):
        prefix = normalized[:-3].rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatch.fnmatchcase(path, normalized)


def evaluate_state_alignment(
    project_root: Path,
    *,
    changed_paths: Sequence[str],
    scope: Mapping[str, Any],
) -> dict[str, Any]:
    """Conservatively require affected implementation and subsystem State to move together."""
    registry = load_subsystem_registry(project_root)
    entries = {str(item["subsystem_id"]): item for item in registry["entries"]}
    all_state_docs = {
        str(path) for item in registry["entries"] for path in item.get("state_docs", [])
    }
    subsystem_ids = list(
        dict.fromkeys([*scope["declared_subsystem_ids"], *scope["derived_subsystem_ids"]])
    )
    checks: list[dict[str, Any]] = []
    for subsystem_id in subsystem_ids:
        entry = entries.get(str(subsystem_id))
        if entry is None:
            checks.append(
                {
                    "subsystem_id": subsystem_id,
                    "result": "unknown",
                    "reason": "subsystem-is-not-in-the-authoritative-registry",
                    "implementation_paths": [],
                    "state_docs": [],
                    "changed_state_docs": [],
                }
            )
            continue
        state_docs = [str(path) for path in entry["state_docs"]]
        matching = sorted(
            {
                path
                for path in changed_paths
                if any(_path_matches(path, str(pattern)) for pattern in entry["path_patterns"])
            }
        )
        implementation = [path for path in matching if path not in all_state_docs]
        changed_state = [path for path in state_docs if path in changed_paths]
        if implementation and not changed_state:
            result, reason = "failed", "implementation-changed-without-candidate-state-update"
        elif implementation:
            result, reason = "passed", "implementation-and-candidate-state-changed-together"
        else:
            result, reason = "passed", "no-matching-implementation-change"
        checks.append(
            {
                "subsystem_id": subsystem_id,
                "result": result,
                "reason": reason,
                "implementation_paths": implementation,
                "state_docs": state_docs,
                "changed_state_docs": changed_state,
            }
        )
    overall = "failed" if any(item["result"] == "failed" for item in checks) else (
        "unknown" if any(item["result"] == "unknown" for item in checks) else "passed"
    )
    return {
        "result": overall,
        "checks": checks,
        "method": "registry-path-and-state-change-consistency-v1",
        "semantic_claim": "structural-only-no-ai-authority",
    }


def _tree_paths(repository: Path, oid: str, prefix: str) -> list[str]:
    raw = _git(repository, "ls-tree", "-r", "--name-only", "-z", oid, "--", prefix, binary=True).stdout
    assert isinstance(raw, bytes)
    return sorted(
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for item in raw.split(b"\0")
        if item
    )


def _blob_text(repository: Path, oid: str, path: str) -> str | None:
    completed = _git(repository, "show", f"{oid}:{path}", binary=True, check=False)
    if completed.returncode:
        return None
    assert isinstance(completed.stdout, bytes)
    try:
        return completed.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def evaluate_adr_alignment(
    project_root: Path,
    *,
    target_oid: str,
    candidate_head: str,
    changed_paths: Sequence[str],
) -> dict[str, Any]:
    """Check provisional IDs, formal-number collisions, accepted ADR rewrites, and references."""
    root = _repository_root(project_root)
    candidate_decisions = _tree_paths(root, candidate_head, "docs/decisions")
    target_decisions = set(_tree_paths(root, target_oid, "docs/decisions"))
    target_number_paths: dict[str, list[str]] = {}
    for path in target_decisions:
        match = _FORMAL_ADR_PATH.fullmatch(path)
        if match:
            target_number_paths.setdefault(match.group(1), []).append(path)
    numbers: dict[str, list[str]] = {}
    for path in candidate_decisions:
        match = _FORMAL_ADR_PATH.fullmatch(path)
        if match:
            numbers.setdefault(match.group(1), []).append(path)
    duplicate_numbers = [
        {"number": number, "paths": paths}
        for number, paths in sorted(numbers.items())
        if len(paths) > 1
    ]
    for number, paths in sorted(numbers.items()):
        target_paths = target_number_paths.get(number, [])
        if target_paths and set(target_paths) != set(paths):
            duplicate_numbers.append(
                {"number": number, "paths": sorted(set(paths) | set(target_paths))}
            )
    accepted_rewrites = sorted(
        path for path in changed_paths if path in target_decisions and _FORMAL_ADR_PATH.fullmatch(path)
    )
    provisional_paths = sorted(
        path
        for path in candidate_decisions
        if path.startswith("docs/decisions/proposals/") and path.endswith(".md")
    )
    temporary_ids: set[str] = set()
    missing_formal_references: set[str] = set()
    candidate_numbers = set(numbers)
    for path in changed_paths:
        if not path.endswith(".md"):
            continue
        text = _blob_text(root, candidate_head, path)
        if text is None:
            continue
        temporary_ids.update(_TEMPORARY_DECISION.findall(text))
        for number in _FORMAL_ADR_REFERENCE.findall(text):
            if number not in candidate_numbers:
                missing_formal_references.add(f"ADR-{number}")
    for path in provisional_paths:
        text = _blob_text(root, candidate_head, path)
        if text:
            temporary_ids.update(_TEMPORARY_DECISION.findall(text))
    target_numbers = sorted(
        {
            match.group(1)
            for path in target_decisions
            if (match := _FORMAL_ADR_PATH.fullmatch(path)) is not None
        }
    )
    next_number = max((int(item) for item in target_numbers), default=0) + 1
    allocation_suggestions = [
        {
            "temporary_id": temporary_id,
            "suggested_formal_id": f"ADR-{next_number + index:04d}",
            "authority": "non-authoritative-integrator-candidate",
        }
        for index, temporary_id in enumerate(sorted(temporary_ids))
    ]
    blockers: list[str] = []
    if provisional_paths or temporary_ids:
        blockers.append("temporary-adr-id-requires-integrator-finalization")
    if duplicate_numbers:
        blockers.append("formal-adr-number-conflict")
    if accepted_rewrites:
        blockers.append("existing-formal-adr-modified-in-candidate")
    if missing_formal_references:
        blockers.append("formal-adr-reference-target-missing")
    return {
        "result": "failed" if blockers else "passed",
        "provisional_paths": provisional_paths,
        "temporary_ids": sorted(temporary_ids),
        "allocation_suggestions": allocation_suggestions,
        "duplicate_formal_numbers": duplicate_numbers,
        "accepted_adr_rewrites": accepted_rewrites,
        "missing_formal_references": sorted(missing_formal_references),
        "blockers": blockers,
        "allocation_authority": "integrator-only",
    }


def assert_clean_integration_worktree(path: Path, *, expected_head: str | None = None) -> None:
    """Fail closed if an integration workspace is not a clean listed worktree at the expected OID."""
    root = _repository_root(path)
    if os.path.normcase(os.path.realpath(root)) != os.path.normcase(os.path.realpath(path)):
        raise ValueError("integration worktree path is not its Git toplevel")
    status = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True).stdout
    assert isinstance(status, bytes)
    if status:
        raise ValueError("integration worktree must be clean before speculative integration")
    head = str(_git(root, "rev-parse", "HEAD").stdout).strip().lower()
    if expected_head is not None and head != expected_head:
        raise ValueError("integration worktree HEAD does not match the pinned start OID")


def _validation_environment() -> dict[str, str]:
    blocked_fragments = ("OPENAI", "ANTHROPIC", "DEEPSEEK", "API_KEY", "ACCESS_TOKEN", "CODEX_HOME")
    return {
        key: value
        for key, value in os.environ.items()
        if not any(fragment in key.upper() for fragment in blocked_fragments)
    }


def _run_validations(
    integration_root: Path,
    *,
    commands: Sequence[str],
    evidence_root: Path,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    evidence_root.mkdir(parents=True, exist_ok=True)
    if not commands:
        return [
            {
                "command": "(missing required validation command)",
                "result": "failed",
                "evidence_ref": "git-private:unavailable",
                "completed_at": _utc_timestamp(),
                "exit_code": 2,
                "stdout_sha256": hashlib.sha256(b"").hexdigest(),
                "stderr_sha256": hashlib.sha256(b"required validation command missing").hexdigest(),
                "duration_ms": 0,
            }
        ]
    for index, command in enumerate(commands, start=1):
        if not command.strip():
            raise ValueError("validation command must not be empty")
        try:
            arguments = shlex.split(command, posix=True)
        except ValueError as exc:
            raise ValueError(f"cannot parse validation command: {exc}") from exc
        if not arguments:
            raise ValueError("validation command must contain an executable")
        started = time.monotonic()
        timed_out = False
        try:
            completed = subprocess.run(
                arguments,
                cwd=integration_root,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=False,
                check=False,
                timeout=timeout_seconds,
                env=_validation_environment(),
            )
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = (exc.stderr or b"") + b"\nProject Orrery validation timeout\n"
            exit_code = 124
            timed_out = True
        duration_ms = int((time.monotonic() - started) * 1000)
        log_path = evidence_root / f"validation-{index:03d}.log"
        log_path.write_bytes(
            b"command: "
            + command.encode("utf-8", errors="replace")
            + b"\nexit_code: "
            + str(exit_code).encode("ascii")
            + b"\nstdout:\n"
            + stdout
            + b"\nstderr:\n"
            + stderr
        )
        results.append(
            {
                "command": command,
                "result": "passed" if exit_code == 0 else "failed",
                "evidence_ref": f"git-private:{log_path.relative_to(_common_git_dir(integration_root)).as_posix()}",
                "completed_at": _utc_timestamp(),
                "exit_code": exit_code,
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
                "duration_ms": duration_ms,
                "timed_out": timed_out,
            }
        )
    return results


def _validation_contract_view(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "command": str(item["command"]),
            "result": str(item["result"]),
            "evidence_ref": str(item["evidence_ref"]),
            "completed_at": str(item["completed_at"]),
        }
        for item in results
    ]


def _conflict_paths(integration_root: Path) -> list[str]:
    raw = _git(
        integration_root,
        "diff",
        "--name-only",
        "--diff-filter=U",
        "-z",
        binary=True,
        check=False,
    ).stdout
    assert isinstance(raw, bytes)
    return sorted(
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for item in raw.split(b"\0")
        if item
    )


def _risk_policy(
    *,
    project_mode: str,
    changed_paths: Sequence[str],
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    reasons: list[str] = []
    high = any(
        item.get("kind") == "direct"
        or item.get("severity") == "l3"
        or item.get("exclusive_resource_ids")
        for item in findings
    )
    if any(
        "/schema/" in f"/{path}"
        or "/migrations/" in f"/{path}"
        or path in {"packages/component-versions.json", "skills/project-orrery/release-manifest.json"}
        or path.endswith((".pem", ".key"))
        for path in changed_paths
    ):
        high = True
        reasons.append("schema-release-credential-or-migration-surface")
    elevated = any(
        item.get("kind") in {"authority", "semantic"}
        or len(item.get("required_member_ids", [])) > 1
        for item in findings
    ) or any(
        path == "AGENTS.md"
        or path in {"docs/PROGRESS.md", "docs/HANDOFF.md", "docs/DEVLOG.md"}
        or path.startswith(("docs/state/", "docs/decisions/", "docs/design/"))
        for path in changed_paths
    )
    if high:
        level = "high"
        reasons.append("high-risk-or-l3-surface")
    elif elevated:
        level = "elevated"
        reasons.append("authority-shared-interface-or-cross-member-surface")
    else:
        level = "normal"
        reasons.append("personal-or-team-ordinary-change")
    non_author = level != "normal"
    if project_mode == "team" and level != "normal":
        non_author = True
    return {
        "level": level,
        "reasons": list(dict.fromkeys(reasons)),
        "required_human_reviewers": 1,
        "required_approval_capability": "integrator" if project_mode == "team" and level == "normal" else "reviewer",
        "non_author_reviewer_required": non_author,
        "ai_counts_as_human_reviewer": False,
    }


def _current_review_inputs(project_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = _repository_root(project_root)
    status = inspect_worktree_status(root)
    if status["identity"]["is_primary"]:
        raise ValueError("review generation is prohibited in the primary worktree")
    if status["identity"]["dirty"]:
        raise ValueError("candidate worktree must be clean before review generation")
    if status["session"]["state"] != "current":
        raise ValueError("review generation requires a current Git-private Workstream session")
    session = status["session"]["record"]
    assert isinstance(session, dict)
    if session.get("lifecycle_phase") != "validating":
        raise ValueError("review generation requires the Workstream validating lifecycle phase")
    if not isinstance(session.get("scope_observation"), Mapping) or not session.get("scope_fingerprint"):
        raise ValueError("review generation requires a W2 scope refresh and bound Scope fingerprint")
    scope = collect_scope_observation(root, session=session, scope_revision=int(session["scope_revision"]))
    if scope["scope_fingerprint"] != session["scope_fingerprint"]:
        raise ValueError("current Scope observation drifted from the Git-private session")
    active_findings = [
        item
        for item in session.get("findings", [])
        if item.get("disposition") in {"open", "acknowledged"}
    ]
    if any(item.get("review_ready_blocked", False) for item in active_findings):
        raise ValueError("active W2 findings still block Review Ready")
    return status, session, scope


def generate_review_package(
    project_root: Path,
    *,
    target_ref: str | None = None,
    strategy: str = "merge",
    validation_commands: Sequence[str] | None = None,
    validation_timeout_seconds: int = 300,
    validation_freshness_seconds: int = 86400,
    ai_summary: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Run a disposable local merge/rebase and persist an immutable evidence-first package."""
    if strategy not in {"merge", "rebase"}:
        raise ValueError("speculative integration strategy must be merge or rebase")
    if validation_timeout_seconds < 1 or validation_freshness_seconds < 1:
        raise ValueError("validation timeout and freshness window must be positive")
    root = _repository_root(project_root)
    status, session, scope = _current_review_inputs(root)
    selected_ref = target_ref or str(session["integration_ref"])
    if not selected_ref.startswith("refs/heads/"):
        raise ValueError("integration target must be a local branch ref")
    target_oid = resolve_integration_oid(root, selected_ref)
    candidate_head = str(status["identity"]["head"])
    merge_base = str(_git(root, "merge-base", candidate_head, target_oid).stdout).strip().lower()
    changed_paths = _changed_paths(root, target_oid, candidate_head)
    if not changed_paths:
        raise ValueError("candidate has no changes relative to the pinned integration target")
    findings = [dict(item) for item in session.get("findings", [])]
    finding_history = [dict(item) for item in session.get("finding_history", [])]
    finding_hash = _finding_set_hash(session)
    schema_hash = _schema_hash()
    timestamp = _utc_timestamp(generated_at)
    run_id = _canonical_hash(
        _RUN_HASH_DOMAIN,
        {
            "candidate_head": candidate_head,
            "target_oid": target_oid,
            "scope_revision": session["scope_revision"],
            "scope_fingerprint": scope["scope_fingerprint"],
            "finding_set_hash": finding_hash,
            "schema_hash": schema_hash,
            "strategy": strategy,
        },
    )[:24]
    evidence_root = _private_area(root, "reviews", "evidence", f"run-{run_id}", create=True)
    commands = list(validation_commands if validation_commands is not None else session["validation_surfaces"])
    validation_hash = _canonical_hash(_VALIDATION_HASH_DOMAIN, commands)
    author_before = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True).stdout
    author_head_before = str(_git(root, "rev-parse", "HEAD").stdout).strip().lower()
    integration_clean = False
    merge_result = "failed"
    conflict_paths: list[str] = []
    validation_details: list[dict[str, Any]] = []
    integration_path_text = ""
    cleanup_error: str | None = None
    with tempfile.TemporaryDirectory(prefix="orrery-speculative-integration-") as temporary_root:
        integration_path = Path(temporary_root) / "integration-worktree"
        integration_path_text = str(integration_path)
        start_oid = target_oid if strategy == "merge" else candidate_head
        _git(root, "worktree", "add", "--detach", str(integration_path), start_oid)
        try:
            assert_clean_integration_worktree(integration_path, expected_head=start_oid)
            integration_clean = True
            if strategy == "merge":
                attempt = _git(
                    integration_path,
                    "merge",
                    "--no-commit",
                    "--no-ff",
                    candidate_head,
                    check=False,
                )
            else:
                attempt = _git(
                    integration_path,
                    "rebase",
                    "--onto",
                    target_oid,
                    merge_base,
                    candidate_head,
                    check=False,
                )
            if attempt.returncode:
                conflict_paths = _conflict_paths(integration_path)
                merge_result = "conflicted" if conflict_paths else "failed"
            else:
                merge_result = "passed"
                validation_details = _run_validations(
                    integration_path,
                    commands=commands,
                    evidence_root=evidence_root,
                    timeout_seconds=validation_timeout_seconds,
                )
        finally:
            _git(integration_path, "merge", "--abort", check=False)
            _git(integration_path, "rebase", "--abort", check=False)
            removal = _git(root, "worktree", "remove", "--force", str(integration_path), check=False)
            if removal.returncode:
                cleanup_error = str(removal.stderr or removal.stdout).strip() or "worktree-remove-failed"

    author_after = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True).stdout
    author_head_after = str(_git(root, "rev-parse", "HEAD").stdout).strip().lower()
    author_unchanged = author_before == author_after and author_head_before == author_head_after
    current_target_oid = resolve_integration_oid(root, selected_ref)
    target_drifted = current_target_oid != target_oid
    state_alignment = evaluate_state_alignment(root, changed_paths=changed_paths, scope=scope)
    adr_alignment = evaluate_adr_alignment(
        root,
        target_oid=target_oid,
        candidate_head=candidate_head,
        changed_paths=changed_paths,
    )
    validation_contract = _validation_contract_view(validation_details)
    validations_passed = bool(validation_details) and all(
        item["result"] == "passed" for item in validation_details
    )
    from .workstream_relation_capture import relation_gate_eligibility

    validation_relation_gate = relation_gate_eligibility(
        root, source_workstream_id=str(session["workstream_id"]), required_for="validation"
    )
    ready = all(
        (
            integration_clean,
            merge_result == "passed",
            validations_passed,
            state_alignment["result"] == "passed",
            adr_alignment["result"] == "passed",
            not target_drifted,
            author_unchanged,
            cleanup_error is None,
            validation_relation_gate["eligible"],
        )
    )
    report = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "integration-report",
        "report_id": f"integration-{run_id}",
        "candidate_head": candidate_head,
        "target_ref": selected_ref,
        "target_oid": target_oid,
        "merge_base": merge_base,
        "scope_revision": int(session["scope_revision"]),
        "finding_ids": sorted({str(item["finding_id"]) for item in findings}),
        "validations": validation_contract,
        "state_alignment": str(state_alignment["result"]),
        "result": "ready-for-human-integration" if ready else (
            "stale" if target_drifted else "failed" if merge_result != "passed" else "blocked"
        ),
        "member_id": str(session["member_id"]),
        "host_id": str(session["host_id"]),
        "visibility": "worktree-local",
        "observability": "local",
        "generated_at": timestamp,
        "strategy": strategy,
        "integration_worktree_clean": integration_clean,
        "merge_result": merge_result,
        "conflict_paths": conflict_paths,
        "target_drifted": target_drifted,
        "author_worktree_unchanged": author_unchanged,
        "validation_set_hash": validation_hash,
    }
    validate_collaboration_contract(report)
    binding = {
        "candidate_head": candidate_head,
        "target_ref": selected_ref,
        "target_oid": target_oid,
        "merge_base": merge_base,
        "scope_revision": int(session["scope_revision"]),
        "scope_fingerprint": str(scope["scope_fingerprint"]),
        "finding_set_hash": finding_hash,
        "collaboration_schema_id": COLLABORATION_CONTRACT_ID,
        "collaboration_schema_version": COLLABORATION_SCHEMA_VERSION,
        "collaboration_schema_hash": schema_hash,
        "validation_set_hash": validation_hash,
    }
    risk = _risk_policy(
        project_mode=str(session["project_mode"]), changed_paths=changed_paths, findings=findings
    )
    evidence_refs = [f"git:{candidate_head}", f"git:{target_oid}"] + [
        str(item["evidence_ref"]) for item in validation_details
    ]
    unknown_boundaries = [
        "AI summary is optional, derived, and cannot create Authority",
        "semantic State consistency remains a human review responsibility beyond structural checks",
        "no fetch or remote branch observation was performed",
    ]
    if cleanup_error:
        unknown_boundaries.append(f"temporary integration worktree cleanup error: {cleanup_error}")
    if not validation_relation_gate["eligible"]:
        unknown_boundaries.append("effective validation dependency remains incomplete")
    package: dict[str, Any] = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "review-package",
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "package_id": "review-" + "0" * 24,
        "content_hash": "0" * 64,
        "hash_excludes": ["package_id", "content_hash"],
        "binding": binding,
        "workstream_id": str(session["workstream_id"]),
        "author_member_id": str(session["member_id"]),
        "author_host_id": str(session["host_id"]),
        "risk": risk,
        "evidence": {
            "scope": scope,
            "findings": findings,
            "finding_history": finding_history,
            "changed_paths": changed_paths,
            "diff_stat": _diff_stat(root, target_oid, candidate_head),
            "validations": validation_details,
            "state_alignment": state_alignment,
            "adr_alignment": adr_alignment,
            "speculative_integration": report,
            "evidence_refs": list(dict.fromkeys(evidence_refs)),
            "unknown_boundaries": unknown_boundaries,
        },
        "ai_summary": {
            "status": "provided" if ai_summary is not None else "unavailable",
            "authority": "derived-non-authoritative",
            "text": ai_summary or "",
            "generated_at": timestamp,
        },
        "presentation_order": ["evidence", "ai_summary"],
        "invalidation_conditions": list(_INVALIDATION_CONDITIONS),
        "validation_fresh_until": (
            dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            + dt.timedelta(seconds=validation_freshness_seconds)
        ).isoformat().replace("+00:00", "Z"),
        "visibility": "worktree-local",
        "observability": "local",
        "generated_at": timestamp,
    }
    content_hash = _package_hash(package)
    package["content_hash"] = content_hash
    package["package_id"] = f"review-{content_hash[:24]}"
    validate_collaboration_contract(package)
    package_path = _private_area(root, "reviews", "packages", create=True) / f"{package['package_id']}.json"
    _atomic_json(package_path, package)
    if ready:
        updated_session = dict(session)
        old_phase = str(updated_session["lifecycle_phase"])
        updated_session.update(
            {
                "lifecycle_phase": "review-ready",
                "runtime_condition": "active",
                "evidence_freshness": "current",
                "lifecycle_revision": int(updated_session.get("lifecycle_revision", 1)) + 1,
                "last_transition": {
                    "from_phase": old_phase,
                    "to_phase": "review-ready",
                    "reason": "evidence-first-review-package-gate-passed",
                    "occurred_at": timestamp,
                },
                "review_package_id": package["package_id"],
                "review_package_content_hash": content_hash,
            }
        )
        _write_private_session(root, updated_session)
    return {
        "dry_run_schema_version": INTEGRATION_DRY_RUN_SCHEMA_VERSION,
        "review_package": package,
        "review_package_path": str(package_path),
        "integration_worktree_path": integration_path_text,
        "integration_ref_updated": False,
        "branch_deleted": False,
        "worktree_deleted": False,
        "writes_performed": True,
        "write_targets": ["git-private-review-package", "git-private-validation-evidence"],
        "network_performed": False,
        "relation_gate_eligibility": validation_relation_gate,
    }


def inspect_review_package_freshness(project_root: Path, package: str | Path) -> dict[str, Any]:
    root = _repository_root(project_root)
    review = load_review_package(root, package)
    status = inspect_worktree_status(root)
    session = status["session"]["record"]
    reasons: list[str] = []
    binding = review["binding"]
    if status["identity"]["head"] != binding["candidate_head"]:
        reasons.append("candidate-head-changed")
    try:
        current_target = resolve_integration_oid(root, str(binding["target_ref"]))
    except ValueError:
        current_target = None
        reasons.append("target-ref-unavailable")
    if current_target is not None and current_target != binding["target_oid"]:
        reasons.append("target-oid-changed")
    if status["session"]["state"] != "current" or not isinstance(session, Mapping):
        reasons.append("workstream-session-not-current")
    else:
        if int(session["scope_revision"]) != int(binding["scope_revision"]):
            reasons.append("scope-revision-changed")
        if session.get("scope_fingerprint") != binding["scope_fingerprint"]:
            reasons.append("scope-fingerprint-changed")
        if _finding_set_hash(session) != binding["finding_set_hash"]:
            reasons.append("finding-set-changed")
        if _canonical_hash(
            _VALIDATION_HASH_DOMAIN, list(session.get("validation_surfaces", []))
        ) != binding["validation_set_hash"]:
            reasons.append("validation-set-changed")
        if session.get("review_package_id") != review["package_id"] or session.get(
            "review_package_content_hash"
        ) != review["content_hash"]:
            reasons.append("review-package-session-binding-changed")
        if session.get("evidence_freshness") != "current":
            reasons.append("validation-evidence-expired-or-changed")
    if _schema_hash() != binding["collaboration_schema_hash"]:
        reasons.append("collaboration-schema-changed")
    try:
        fresh_until = dt.datetime.fromisoformat(
            str(review["validation_fresh_until"]).replace("Z", "+00:00")
        )
    except ValueError:
        reasons.append("validation-freshness-invalid")
    else:
        if dt.datetime.now(dt.timezone.utc) > fresh_until:
            reasons.append("validation-evidence-expired-or-changed")
    reasons = list(dict.fromkeys(reasons))
    clean_review = {key: value for key, value in review.items() if not key.startswith("_")}
    return {
        "package_id": review["package_id"],
        "package_content_hash": review["content_hash"],
        "fresh": not reasons,
        "stale_reasons": reasons,
        "binding": dict(binding),
        "package": clean_review,
        "writes_performed": False,
        "network_performed": False,
    }


def _decision_directory(project_root: Path, package_id: str, *, create: bool = False) -> Path:
    return _private_area(project_root, "reviews", "decisions", package_id, create=create)


def _load_decisions(project_root: Path, package: Mapping[str, Any]) -> list[dict[str, Any]]:
    directory = _decision_directory(project_root, str(package["package_id"]))
    if not directory.is_dir():
        return []
    decisions: list[dict[str, Any]] = []
    for path in sorted(directory.glob("decision-*.json")):
        value = _read_regular_json(path, description="review decision")
        validate_collaboration_contract(value)
        if value.get("contract_type") != "review-decision":
            raise ValueError("review decision has the wrong contract type")
        if value.get("package_id") != package["package_id"] or value.get(
            "package_content_hash"
        ) != package["content_hash"]:
            raise ValueError("review decision is not bound to the selected review package")
        decisions.append(value)
    return decisions


def record_review_decision(
    project_root: Path,
    *,
    package: str | Path,
    action: str,
    actor_id: str,
    reason: str,
    evidence_refs: Sequence[str],
    actor_kind: str = "human",
    actor_capabilities: Sequence[str] = (),
    decided_at: str | None = None,
) -> dict[str, Any]:
    if action not in {"approve", "request-changes", "hold", "reject"}:
        raise ValueError("review action must be Approve, Request Changes, Hold, or Reject")
    if actor_kind != "human":
        raise ValueError("AI or Agent actors cannot record review actions")
    if not actor_id.strip() or not reason.strip() or not evidence_refs:
        raise ValueError("review action requires actor, reason, and at least one evidence reference")
    if any(not str(item).strip() for item in evidence_refs):
        raise ValueError("review evidence references must not be empty")
    freshness = inspect_review_package_freshness(project_root, package)
    if not freshness["fresh"]:
        raise ValueError("stale review package cannot receive a review action")
    review = freshness["package"]
    capabilities = list(dict.fromkeys(actor_capabilities))
    if any(item not in CAPABILITIES for item in capabilities):
        raise ValueError("review actor capabilities contain an unsupported value")
    if actor_id == review["author_member_id"] and not capabilities:
        capabilities = list(CAPABILITIES)
    if "reviewer" not in capabilities:
        raise ValueError("review action requires a human Reviewer capability")
    timestamp = _utc_timestamp(decided_at)
    material = {
        "package_id": review["package_id"],
        "package_content_hash": review["content_hash"],
        "action": action,
        "actor_id": actor_id,
        "reason": reason.strip(),
        "evidence_refs": list(dict.fromkeys(str(item) for item in evidence_refs)),
        "decided_at": timestamp,
    }
    digest = _canonical_hash(_DECISION_HASH_DOMAIN, material)
    decision = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "review-decision",
        "decision_schema_version": REVIEW_DECISION_SCHEMA_VERSION,
        "decision_id": f"decision-{digest[:24]}",
        "package_id": review["package_id"],
        "package_content_hash": review["content_hash"],
        "action": action,
        "actor_id": actor_id.strip(),
        "actor_kind": "human",
        "actor_is_author": actor_id == review["author_member_id"],
        "actor_capabilities": capabilities,
        "reason": reason.strip(),
        "evidence_refs": material["evidence_refs"],
        "decided_at": timestamp,
        "invalidation_conditions": list(_INVALIDATION_CONDITIONS),
        "visibility": "local-only",
        "observability": "local",
    }
    validate_collaboration_contract(decision)
    path = _decision_directory(project_root, review["package_id"], create=True) / f"{decision['decision_id']}.json"
    _atomic_json(path, decision)
    status = inspect_worktree_status(project_root)
    session = status["session"]["record"]
    if not isinstance(session, Mapping):
        raise ValueError("review action requires the bound Git-private Workstream session")
    updated_session = dict(session)
    old_phase = str(updated_session["lifecycle_phase"])
    if action == "request-changes":
        new_phase, runtime, freshness = "implementing", "active", "stale"
    elif action == "reject":
        new_phase, runtime, freshness = "validating", "paused", "stale"
    elif action == "hold":
        new_phase, runtime, freshness = "review-ready", "paused", "current"
    else:
        new_phase, runtime, freshness = "review-ready", "active", "current"
    updated_session.update(
        {
            "lifecycle_phase": new_phase,
            "runtime_condition": runtime,
            "evidence_freshness": freshness,
            "lifecycle_revision": int(updated_session.get("lifecycle_revision", 1)) + 1,
            "last_transition": {
                "from_phase": old_phase,
                "to_phase": new_phase,
                "reason": f"human-review-{action}",
                "occurred_at": timestamp,
            },
        }
    )
    _write_private_session(_repository_root(project_root), updated_session)
    return {
        "decision": decision,
        "decision_path": str(path),
        "writes_performed": True,
        "network_performed": False,
    }


def _evaluate_decision_policy(
    package: Mapping[str, Any], decisions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    latest_by_actor: dict[str, Mapping[str, Any]] = {}
    for decision in sorted(decisions, key=lambda item: (str(item["decided_at"]), str(item["decision_id"]))):
        latest_by_actor[str(decision["actor_id"])] = decision
    current = list(latest_by_actor.values())
    blocking = [
        dict(item) for item in current if item["action"] in {"request-changes", "hold", "reject"}
    ]
    approvals = [dict(item) for item in current if item["action"] == "approve"]
    risk = package["risk"]
    required_capability = str(risk["required_approval_capability"])
    human_approvals = [
        item
        for item in approvals
        if item.get("actor_kind") == "human"
        and required_capability in item.get("actor_capabilities", [])
    ]
    non_author = [item for item in human_approvals if not item.get("actor_is_author")]
    reasons: list[str] = []
    if blocking:
        reasons.append("current-review-action-blocks-integration")
    if len(human_approvals) < int(risk["required_human_reviewers"]):
        reasons.append("required-human-reviewer-count-not-met")
        reasons.append(f"required-{required_capability}-approval-missing")
    if risk["non_author_reviewer_required"] and not non_author:
        reasons.append("required-non-author-reviewer-missing")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "latest_decisions": current,
        "human_approval_count": len(human_approvals),
        "non_author_approval_count": len(non_author),
        "ai_approval_count": 0,
        "required_human_reviewers": risk["required_human_reviewers"],
        "required_approval_capability": required_capability,
        "non_author_reviewer_required": risk["non_author_reviewer_required"],
    }


def compute_integration_eligibility(project_root: Path, package: str | Path) -> dict[str, Any]:
    freshness = inspect_review_package_freshness(project_root, package)
    review = freshness["package"]
    decisions = _load_decisions(project_root, review)
    policy = _evaluate_decision_policy(review, decisions)
    gate_passed = (
        review["evidence"]["speculative_integration"]["result"]
        == "ready-for-human-integration"
    )
    reasons = list(freshness["stale_reasons"])
    if not gate_passed:
        reasons.append("speculative-integration-gate-not-passed")
    reasons.extend(policy["reasons"])
    from .workstream_relation_capture import relation_gate_eligibility

    relation_gate = relation_gate_eligibility(
        Path(project_root), source_workstream_id=str(review["workstream_id"]), required_for="integration"
    )
    if not relation_gate["eligible"]:
        reasons.append("effective-integration-dependency-incomplete")
    reasons = list(dict.fromkeys(reasons))
    return {
        "eligibility_schema_version": 1,
        "eligible": not reasons,
        "reasons": reasons,
        "package_id": review["package_id"],
        "binding": review["binding"],
        "review_policy": policy,
        "recommended_action": "await-human-integrator" if not reasons else "resolve-and-rerun-review",
        "integration_ref_updated": False,
        "writes_performed": False,
        "network_performed": False,
        "relation_gate_eligibility": relation_gate,
    }


def write_closure_record(
    project_root: Path,
    *,
    package: str | Path,
    final_oid: str,
    actor_id: str,
    actor_capabilities: Sequence[str] = (),
    closed_at: str | None = None,
) -> dict[str, Any]:
    root = _repository_root(project_root)
    review = load_review_package(root, package)
    from .workstream_relation_capture import relation_gate_eligibility

    relation_gate = relation_gate_eligibility(
        root, source_workstream_id=str(review["workstream_id"]), required_for="integration"
    )
    if not relation_gate["eligible"]:
        raise ValueError("effective integration dependency blocks integration closure")
    capabilities = list(dict.fromkeys(actor_capabilities))
    if actor_id == review["author_member_id"] and not capabilities:
        capabilities = list(CAPABILITIES)
    if "integrator" not in capabilities:
        raise ValueError("closure record requires a human Integrator capability")
    if not _OID.fullmatch(final_oid):
        raise ValueError("final integration OID must be a full commit OID")
    current_target = resolve_integration_oid(root, str(review["binding"]["target_ref"]))
    if current_target != final_oid:
        raise ValueError("final OID does not match the current local integration ref")
    if _git(root, "merge-base", "--is-ancestor", str(review["binding"]["candidate_head"]), final_oid, check=False).returncode:
        raise ValueError("candidate HEAD is not traceable as an ancestor of the final integration OID")
    status = inspect_worktree_status(root)
    session = status["session"]["record"]
    if not isinstance(session, Mapping) or status["identity"]["head"] != review["binding"]["candidate_head"]:
        raise ValueError("closure requires the original candidate worktree and HEAD")
    if int(session["scope_revision"]) != int(review["binding"]["scope_revision"]):
        raise ValueError("closure Scope revision drifted from the review package")
    if session.get("scope_fingerprint") != review["binding"]["scope_fingerprint"]:
        raise ValueError("closure Scope fingerprint drifted from the review package")
    if _finding_set_hash(session) != review["binding"]["finding_set_hash"]:
        raise ValueError("closure finding set drifted from the review package")
    if _canonical_hash(
        _VALIDATION_HASH_DOMAIN, list(session.get("validation_surfaces", []))
    ) != review["binding"]["validation_set_hash"]:
        raise ValueError("closure validation set drifted from the review package")
    if _schema_hash() != review["binding"]["collaboration_schema_hash"]:
        raise ValueError("closure schema drifted from the review package")
    try:
        validation_fresh_until = dt.datetime.fromisoformat(
            str(review["validation_fresh_until"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("closure validation freshness timestamp is invalid") from exc
    if dt.datetime.now(dt.timezone.utc) > validation_fresh_until:
        raise ValueError("closure validation evidence expired; rerun review before integration")
    decisions = _load_decisions(root, review)
    policy = _evaluate_decision_policy(review, decisions)
    if not policy["passed"]:
        raise ValueError("closure requires a review package that satisfied human review policy")
    validations = review["evidence"]["validations"]
    if not validations or any(item.get("result") != "passed" for item in validations):
        raise ValueError("closure requires passed validation evidence")
    timestamp = _utc_timestamp(closed_at)
    material = {
        "workstream_id": review["workstream_id"],
        "original_workspace_path": str(root),
        "candidate_head": review["binding"]["candidate_head"],
        "target_ref": review["binding"]["target_ref"],
        "review_target_oid": review["binding"]["target_oid"],
        "final_oid": final_oid,
        "review_package_id": review["package_id"],
        "actor_id": actor_id,
        "closed_at": timestamp,
    }
    digest = _canonical_hash(_CLOSURE_HASH_DOMAIN, material)
    closure = {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "contract_type": "closure-record",
        "closure_schema_version": CLOSURE_SCHEMA_VERSION,
        "closure_id": f"closure-{digest[:24]}",
        "workstream_id": review["workstream_id"],
        "original_workspace_path": str(root),
        "workspace_classification": "integrated-closed",
        "workspace_classification_label": "Integrated/Closed",
        "candidate_head": review["binding"]["candidate_head"],
        "final_head": review["binding"]["candidate_head"],
        "target_ref": review["binding"]["target_ref"],
        "review_target_oid": review["binding"]["target_oid"],
        "final_oid": final_oid,
        "integration_oid": final_oid,
        "review_package_id": review["package_id"],
        "review_package_content_hash": review["content_hash"],
        "decision_ids": sorted(str(item["decision_id"]) for item in decisions),
        "validation_refs": list(
            dict.fromkeys(str(item["evidence_ref"]) for item in validations)
        ),
        "closure_reason": "integrated",
        "actor_id": actor_id,
        "cleanup_operator_id": actor_id,
        "closed_at": timestamp,
        "storage": "git-private-common",
        "visibility": "local-only",
        "observability": "local",
    }
    closure["cleanup_action_log_ref"] = (
        f"git-private:orrery/closures/actions/{closure['closure_id']}/"
    )
    closure["actual_cleanup_actions"] = []
    validate_collaboration_contract(closure)
    path = _private_area(root, "closures", create=True) / f"{closure['closure_id']}.json"
    _atomic_json(path, closure)
    updated_session = dict(session)
    old_phase = str(updated_session["lifecycle_phase"])
    updated_session.update(
        {
            "integration_oid": final_oid,
            "merge_base": str(_git(root, "merge-base", final_oid, review["binding"]["candidate_head"]).stdout).strip(),
            "lifecycle_phase": "integrated",
            "runtime_condition": "active",
            "evidence_freshness": "current",
            "lifecycle_revision": int(updated_session.get("lifecycle_revision", 1)) + 1,
            "last_transition": {
                "from_phase": old_phase,
                "to_phase": "integrated",
                "reason": "candidate-is-ancestor-of-final-integration-oid",
                "occurred_at": timestamp,
            },
        }
    )
    _write_private_session(root, updated_session)
    try:
        from .maintenance import record_maintenance_event

        maintenance_event = record_maintenance_event(
            root, reason="integration-event", occurred_at=timestamp
        )
    except Exception as error:
        maintenance_event = {
            "status": "unavailable",
            "error_type": type(error).__name__,
            "integration_or_closure_affected": False,
        }
    return {
        "closure_record": closure,
        "closure_path": str(path),
        "storage": "git-private-common",
        "author_worktree_files_changed": False,
        "integration_ref_updated": False,
        "writes_performed": True,
        "network_performed": False,
        "maintenance_event": maintenance_event,
    }


def _load_closure_for_package(project_root: Path, package: Mapping[str, Any]) -> tuple[dict[str, Any] | None, Path | None]:
    directory = _private_area(project_root, "closures")
    if not directory.is_dir():
        return None, None
    matches: list[tuple[dict[str, Any], Path]] = []
    for path in directory.glob("closure-*.json"):
        value = _read_regular_json(path, description="closure record")
        validate_collaboration_contract(value)
        if value.get("review_package_id") == package["package_id"] and value.get(
            "review_package_content_hash"
        ) == package["content_hash"]:
            matches.append((value, path))
    if not matches:
        return None, None
    matches.sort(key=lambda item: (str(item[0]["closed_at"]), str(item[0]["closure_id"])))
    return matches[-1]


def _directory_size(root: Path) -> int:
    total = 0
    for directory, names, files_in_directory in os.walk(root, followlinks=False):
        names[:] = [name for name in names if not (Path(directory) / name).is_symlink()]
        for name in files_in_directory:
            path = Path(directory) / name
            try:
                if path.is_symlink():
                    continue
                total += path.stat().st_size
            except OSError:
                continue
    return total


def compute_cleanup_eligibility(
    project_root: Path,
    *,
    package: str | Path,
    ignored_allowlist: Sequence[str] = (),
) -> dict[str, Any]:
    """Compatibility wrapper for the current Candidate workspace cleanup contract."""
    from .workspace_cleanup import compute_workspace_cleanup_eligibility

    return compute_workspace_cleanup_eligibility(
        project_root,
        workspace_path=project_root,
        package=package,
        ignored_allowlist=ignored_allowlist,
    )
