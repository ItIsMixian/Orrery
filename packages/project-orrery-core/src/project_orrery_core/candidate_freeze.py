"""Bounded Candidate freeze and immutable validation receipt contracts."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .collaboration import inspect_worktree_status
from .schema import CANDIDATE_FREEZE_RECEIPT_SCHEMA, CANDIDATE_VALIDATION_RECEIPT_SCHEMA
from .subprocess_policy import no_window_options


_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CONFLICT = re.compile(br"(?m)^(?:<<<<<<< |=======\r?$|>>>>>>> )")
_FORBIDDEN_NAMES = {".env", "ai-config.json", ".port", ".doccache.json"}
_FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".pyc"}
_FORBIDDEN_PARTS = {"__pycache__", "docs/_site", "dist", "build"}
_FREEZE_CHECKS = (
    "authority_current", "scope_allowed", "branch_current", "expected_paths_only",
    "acceptance_fingerprint_match", "conflict_markers_absent", "forbidden_artifacts_absent",
    "diff_check_passed", "exact_copy_parity_passed", "no_validation_invoked",
)
_STATUS_RECEIPT_LIMIT = 256
_STATUS_RECEIPT_BYTES = 512 * 1024


def _bounded_private_receipts(directory: Path, validator: Callable[[Mapping[str, Any]], None]) -> tuple[list[dict[str, Any]], int, int]:
    """Read a bounded regular-file receipt ledger without following links."""
    if not directory.is_dir():
        return [], 0, 0
    values: list[dict[str, Any]] = []
    broken = 0
    bytes_read = 0
    try:
        paths = sorted(directory.iterdir())[:_STATUS_RECEIPT_LIMIT]
    except OSError:
        return [], 1, 0
    for path in paths:
        try:
            metadata = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_size > _STATUS_RECEIPT_BYTES:
                broken += 1
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, Mapping):
                raise ValueError("receipt is not an object")
            validator(payload)
            values.append(dict(payload))
            bytes_read += metadata.st_size
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            broken += 1
    return values, broken, bytes_read


def inspect_candidate_lifecycle(
    private_orrery_root: Path,
    *,
    workstream_id: str,
    head_oid: str | None,
    lifecycle_phase: str = "unknown",
    closure_reason: str | None = None,
) -> dict[str, Any]:
    """Project freeze, validation, and closure as independent read-only axes."""
    root = Path(private_orrery_root).resolve()
    freeze_values, freeze_broken, freeze_bytes = _bounded_private_receipts(
        root / "candidate-freeze" / "receipts", validate_candidate_freeze_receipt
    )
    validation_values, validation_broken, validation_bytes = _bounded_private_receipts(
        root / "candidate-validation" / "receipts", validate_candidate_validation_receipt
    )
    matching_freezes = [
        item for item in freeze_values
        if item.get("workstream_id") == workstream_id
        and (not head_oid or item.get("candidate_sha") == head_oid)
    ]
    freeze = matching_freezes[-1] if matching_freezes else None
    matching_validations = [
        item for item in validation_values
        if freeze is not None
        and item.get("freeze_receipt_id") == freeze.get("receipt_id")
        and item.get("candidate_sha") == freeze.get("candidate_sha")
    ]
    validation_status = "not-requested"
    if freeze is not None:
        validation_status = "pending"
        if any(item.get("validation_status") == "validation-failed" for item in matching_validations):
            validation_status = "validation-failed"
        elif any(item.get("validation_status") == "validated" for item in matching_validations):
            validation_status = "validated"
    closure_state = "closed" if lifecycle_phase in {"integrated", "closed", "superseded"} or closure_reason else "open"
    if closure_state == "closed":
        status_code, label = "workstream-closed", "已关闭"
    elif freeze is None and (freeze_broken or validation_broken):
        status_code, label = "candidate-evidence-unknown", "候选证据待确认"
    elif freeze is None:
        status_code, label = "candidate-not-frozen", "尚未冻结候选"
    elif validation_status == "validated":
        status_code, label = "candidate-validated", "候选已验证"
    elif validation_status == "validation-failed":
        status_code, label = "candidate-validation-failed", "候选验证失败"
    else:
        status_code, label = "candidate-validation-pending", "候选已冻结 · 等待验证"
    return {
        "candidate_state": "candidate-frozen" if freeze is not None else ("unknown" if freeze_broken else "not-frozen"),
        "validation_status": validation_status,
        "closure_state": closure_state,
        "status_code": status_code,
        "display_label": label,
        "candidate_sha": freeze.get("candidate_sha") if freeze else None,
        "freeze_receipt_id": freeze.get("receipt_id") if freeze else None,
        "validation_receipt_ids": [str(item["receipt_id"]) for item in matching_validations],
        "receipt_files_read": len(freeze_values) + len(validation_values),
        "receipt_bytes_read": freeze_bytes + validation_bytes,
        "broken_receipt_files": freeze_broken + validation_broken,
        "writes_performed": False,
        "network_performed": False,
    }


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, check=False,
        **no_window_options(),
    )
    if check and completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return completed


def _git_text(root: Path, *arguments: str) -> str:
    return _git(root, *arguments).stdout.decode("utf-8", errors="strict").strip()


def _private_path(root: Path, relative: str) -> Path:
    top = Path(_git_text(root, "rev-parse", "--show-toplevel")).resolve()
    raw = _git_text(top, "rev-parse", "--path-format=absolute", "--git-path", relative)
    path = Path(raw)
    git_dir = Path(_git_text(top, "rev-parse", "--absolute-git-dir")).resolve()
    try:
        path.resolve(strict=False).relative_to(git_dir)
    except ValueError as exc:
        raise ValueError("Git-private receipt path escapes the worktree Git directory") from exc
    return path


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _schema_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, Mapping), "array": isinstance(value, list),
        "string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool), "null": value is None,
    }.get(expected, False)


def _validate(value: Any, schema: Mapping[str, Any], root: Mapping[str, Any], path: str) -> None:
    reference = schema.get("$ref")
    if isinstance(reference, str):
        prefix = "#/$defs/"
        target = root.get("$defs", {}).get(reference[len(prefix):]) if reference.startswith(prefix) else None
        if not isinstance(target, Mapping):
            raise ValueError(f"unsupported schema reference at {path}")
        _validate(value, target, root, path)
        return
    for component in schema.get("allOf", []):
        _validate(value, component, root, path)
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path} must equal {schema['const']!r}")
    if isinstance(schema.get("enum"), list) and value not in schema["enum"]:
        raise ValueError(f"{path} is not an allowed value")
    expected = schema.get("type")
    if isinstance(expected, str) and not _schema_type(value, expected):
        raise ValueError(f"{path} must be {expected}")
    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                raise ValueError(f"{path} is missing required field {name}")
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise ValueError(f"{path} contains forbidden field {sorted(unknown)[0]}")
        for name, item in value.items():
            child = properties.get(name)
            if isinstance(child, Mapping):
                _validate(item, child, root, f"{path}.{name}")
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            raise ValueError(f"{path} has too few items")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            raise ValueError(f"{path} has too many items")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise ValueError(f"{path} must contain unique items")
        if isinstance(schema.get("items"), Mapping):
            for index, item in enumerate(value):
                _validate(item, schema["items"], root, f"{path}[{index}]")
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            raise ValueError(f"{path} is too short")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            raise ValueError(f"{path} is too long")
        if isinstance(schema.get("pattern"), str) and re.search(schema["pattern"], value) is None:
            raise ValueError(f"{path} does not match the required pattern")
        if schema.get("format") == "date-time":
            try:
                dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"{path} must be an ISO date-time") from exc
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < int(schema["minimum"]):
            raise ValueError(f"{path} is below the minimum")
        if "maximum" in schema and value > int(schema["maximum"]):
            raise ValueError(f"{path} is above the maximum")


def validate_candidate_freeze_receipt(payload: Mapping[str, Any]) -> None:
    """Validate a Candidate freeze receipt against the central v1 schema."""
    _validate(payload, CANDIDATE_FREEZE_RECEIPT_SCHEMA, CANDIDATE_FREEZE_RECEIPT_SCHEMA, "receipt")


def validate_candidate_validation_receipt(payload: Mapping[str, Any]) -> None:
    """Validate an immutable Candidate validation receipt against the central v1 schema."""
    _validate(payload, CANDIDATE_VALIDATION_RECEIPT_SCHEMA, CANDIDATE_VALIDATION_RECEIPT_SCHEMA, "receipt")


def _normalized_paths(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        normalized = value.replace("\\", "/")
        if (not normalized or normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized)
                or any(part in {"", ".", ".."} for part in normalized.split("/"))
                or any(mark in normalized for mark in "*?[")):
            raise ValueError(f"expected write is not one exact repository path: {value}")
        result.append(normalized)
    if len(result) != len(set(result)):
        raise ValueError("expected writes must be unique")
    return sorted(result)


def _changed_paths(root: Path) -> list[str]:
    raw = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    fields = raw.split(b"\0")
    result: list[str] = []
    index = 0
    while index < len(fields) and fields[index]:
        entry = fields[index]
        if len(entry) < 4 or entry[2:3] != b" ":
            raise ValueError("cannot parse Git status entry")
        status_code = entry[:2]
        if b"R" in status_code or b"C" in status_code:
            raise ValueError("renamed or copied paths require an explicit pre-freeze commit")
        result.append(entry[3:].decode("utf-8", errors="strict").replace("\\", "/"))
        index += 1
    return sorted(set(result))


def _hash_surface(root: Path, expected_paths: Sequence[str], surface_ids: Sequence[str]) -> tuple[str, str]:
    manifest: list[dict[str, str]] = []
    for relative in expected_paths:
        path = root / relative
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            manifest.append({"path": relative, "mode": "missing", "sha256": hashlib.sha256(b"").hexdigest()})
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"candidate path must be a regular file: {relative}")
        manifest.append({"path": relative, "mode": "100755" if metadata.st_mode & stat.S_IXUSR else "100644",
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    relevant = hashlib.sha1(b"project-orrery-relevant-tree-v1\0" + canonical).hexdigest()
    surface = json.dumps({"relevant_tree_hash": relevant, "surface_ids": sorted(set(surface_ids))},
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    return relevant, hashlib.sha256(b"project-orrery-accepted-surface-v1\0" + surface).hexdigest()


def inspect_candidate_surface(root: Path, *, accepted_surface_ids: Sequence[str] = ()) -> dict[str, Any]:
    """Return the exact local acceptance fingerprint without writing Git or files."""
    root = Path(root).resolve()
    status = inspect_worktree_status(root)
    session = status["session"]["record"]
    if not isinstance(session, Mapping):
        raise ValueError("Candidate freeze requires a Git-private Workstream session")
    expected = _normalized_paths(session.get("expected_writes", []))
    relevant, fingerprint = _hash_surface(root, expected, accepted_surface_ids)
    return {"workstream_id": session["workstream_id"], "scope_revision": session["scope_revision"],
            "expected_paths": expected, "relevant_tree_hash": relevant,
            "accepted_surface_fingerprint": fingerprint,
            "changed_paths": _changed_paths(root), "writes_performed": False}


def _assert_structural(root: Path, changed: Sequence[str], expected: Sequence[str],
                       exact_copy_pairs: Sequence[tuple[str, str]]) -> None:
    unexpected = sorted(set(changed) - set(expected))
    if unexpected:
        raise ValueError(f"unexpected changed path: {unexpected[0]}")
    if not changed:
        raise ValueError("Candidate freeze requires at least one changed expected path")
    for relative in changed:
        lowered = relative.lower()
        name = Path(relative).name.lower()
        if (name in _FORBIDDEN_NAMES or Path(relative).suffix.lower() in _FORBIDDEN_SUFFIXES
                or any(lowered == part or lowered.startswith(part + "/") for part in _FORBIDDEN_PARTS)):
            raise ValueError(f"forbidden artifact in candidate: {relative}")
        path = root / relative
        if path.is_file() and _CONFLICT.search(path.read_bytes()):
            raise ValueError(f"merge conflict marker in candidate: {relative}")
    normalized_pairs = [tuple(_normalized_paths((left, right))) for left, right in exact_copy_pairs]
    for left, right in normalized_pairs:
        if left not in expected or right not in expected:
            raise ValueError("exact-copy paths must both belong to expected writes")
        left_path, right_path = root / left, root / right
        if not left_path.is_file() or not right_path.is_file() or left_path.read_bytes() != right_path.read_bytes():
            raise ValueError(f"exact-copy parity failed: {left} != {right}")
    for args in (("diff", "--check"), ("diff", "--cached", "--check")):
        completed = _git(root, *args, check=False)
        if completed.returncode:
            raise ValueError("git diff --check failed")


def freeze_candidate(
    root: Path, *, task_description_sha: str, accepted_surface_fingerprint: str | None,
    accepted_surface_ids: Sequence[str] = (), message: str = "Freeze accepted Candidate",
    exact_copy_pairs: Sequence[tuple[str, str]] = (), apply: bool = False,
    monotonic: Callable[[], float] = time.monotonic, hard_timeout_ms: int = 60000,
) -> dict[str, Any]:
    """Inspect or freeze one accepted tree using bounded structural checks only."""
    started = monotonic()
    root = Path(root).resolve()
    if not _OID.fullmatch(task_description_sha):
        raise ValueError("task-description SHA must be an exact Git object ID")
    if _git(root, "cat-file", "-e", f"{task_description_sha}^{{commit}}", check=False).returncode:
        raise ValueError("task-description SHA is not a local commit")
    head_before = _git_text(root, "rev-parse", "HEAD")
    if _git(root, "merge-base", "--is-ancestor", task_description_sha, head_before, check=False).returncode:
        raise ValueError("task-description SHA is not an ancestor of current HEAD")
    status = inspect_worktree_status(root)
    session = status["session"]["record"]
    if not isinstance(session, Mapping):
        raise ValueError("Candidate freeze requires a Git-private Workstream session")
    branch = _git_text(root, "symbolic-ref", "HEAD")
    if branch != session.get("branch") or session.get("head") != head_before:
        raise ValueError("worktree branch or session HEAD is stale")
    expansion = session.get("last_scope_expansion")
    if (session.get("runtime_condition") != "active" or session.get("findings")
            or not isinstance(expansion, Mapping) or expansion.get("decision") == "blocked"):
        raise ValueError("Workstream scope is not currently allowed")
    expected = _normalized_paths(session.get("expected_writes", []))
    changed = _changed_paths(root)
    _assert_structural(root, changed, expected, exact_copy_pairs)
    relevant, current_fingerprint = _hash_surface(root, expected, accepted_surface_ids)
    if accepted_surface_fingerprint is not None and not _SHA256.fullmatch(accepted_surface_fingerprint):
        raise ValueError("accepted surface fingerprint must be SHA-256")
    if accepted_surface_fingerprint is not None and accepted_surface_fingerprint != current_fingerprint:
        raise ValueError("accepted surface fingerprint no longer matches candidate bytes")
    preview = {"workstream_id": session["workstream_id"], "scope_revision": session["scope_revision"],
               "target_branch": branch, "expected_paths": expected, "staged_paths": changed,
               "relevant_tree_hash": relevant, "accepted_surface_fingerprint": current_fingerprint,
               "elapsed_ms": int((monotonic() - started) * 1000), "writes_performed": False}
    if not apply:
        return preview
    if accepted_surface_fingerprint is None:
        raise ValueError("apply requires the exact accepted surface fingerprint")
    if preview["elapsed_ms"] >= hard_timeout_ms:
        raise ValueError("Candidate freeze exceeded the hard timeout before staging")
    _git(root, "add", "-A", "--", *expected)
    staged = sorted(filter(None, _git_text(root, "diff", "--cached", "--name-only", "--").splitlines()))
    if staged != changed:
        raise ValueError("staged paths do not exactly match the inspected candidate")
    _assert_structural(root, staged, expected, exact_copy_pairs)
    if int((monotonic() - started) * 1000) >= hard_timeout_ms:
        raise ValueError("Candidate freeze exceeded the hard timeout before commit")
    _git(root, "commit", "-m", message, "--", *expected)
    candidate_sha = _git_text(root, "rev-parse", "HEAD")
    elapsed = int((monotonic() - started) * 1000)
    receipt_seed = f"{session['workstream_id']}\0{candidate_sha}\0{current_fingerprint}".encode()
    receipt = {
        "schema_version": 1, "contract_type": "candidate-freeze-receipt-v1",
        "receipt_id": "candidate-freeze-receipt-" + hashlib.sha256(receipt_seed).hexdigest()[:24],
        "workstream_id": session["workstream_id"], "task_description_sha": task_description_sha,
        "scope_revision": session["scope_revision"], "accepted_surface_fingerprint": current_fingerprint,
        "relevant_tree_hash": relevant, "target_branch": branch, "candidate_sha": candidate_sha,
        "expected_paths": expected, "staged_paths": staged,
        "structural_checks": {name: True for name in _FREEZE_CHECKS}, "elapsed_ms": elapsed,
        "frozen_at": _utc_now(), "validation_status": "pending", "network_performed": False,
        "worktree_removed": False, "visibility": "git-private-local-only",
    }
    validate_candidate_freeze_receipt(receipt)
    receipt_path = _private_path(root, f"orrery/candidate-freeze/receipts/{receipt['receipt_id']}.json")
    _atomic_json(receipt_path, receipt)
    return {**receipt, "receipt_path": str(receipt_path), "writes_performed": True}


def load_freeze_receipt(root: Path, receipt_id: str) -> dict[str, Any]:
    path = _private_path(Path(root).resolve(), f"orrery/candidate-freeze/receipts/{receipt_id}.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read Candidate freeze receipt: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Candidate freeze receipt must contain an object")
    validate_candidate_freeze_receipt(payload)
    return dict(payload)


def request_candidate_validation(
    root: Path, *, freeze_receipt_id: str, validation_stage: str = "focused"
) -> dict[str, Any]:
    """Create a Git-private exact-SHA handoff for the existing CI7 router."""
    root = Path(root).resolve()
    if validation_stage != "focused":
        raise ValueError("the initial asynchronous handoff delegates only the authorized focused stage")
    freeze = load_freeze_receipt(root, freeze_receipt_id)
    candidate = freeze["candidate_sha"]
    if _git_text(root, "rev-parse", "HEAD") != candidate or _changed_paths(root):
        raise ValueError("validation handoff requires the clean frozen Candidate checkout")
    receipt_dir = _private_path(root, "orrery/candidate-validation/receipts")
    if receipt_dir.is_dir():
        for path in sorted(receipt_dir.glob("*.json")):
            prior = json.loads(path.read_text(encoding="utf-8"))
            if prior.get("candidate_sha") != candidate or prior.get("validation_stage") != validation_stage:
                continue
            if prior.get("validation_status") == "validated":
                return {"decision": "reuse-prior-receipt", "receipt": prior,
                        "receipt_path": str(path), "writes_performed": False}
            if prior.get("validation_status") == "validation-failed":
                raise ValueError("unchanged failed Candidate validation cannot be retried")
    identity = {
        "freeze_receipt_id": freeze_receipt_id, "candidate_sha": candidate,
        "validation_stage": validation_stage,
        "accepted_surface_fingerprint": freeze["accepted_surface_fingerprint"],
        "relevant_tree_hash": freeze["relevant_tree_hash"],
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    path = _private_path(root, f"orrery/candidate-validation/requests/request-{digest[:24]}.json")
    if path.is_file():
        return {"decision": "reuse-pending-request", "request": json.loads(path.read_text(encoding="utf-8")),
                "request_path": str(path), "writes_performed": False}
    request = {
        "schema_version": 1, "contract_type": "candidate-validation-request-v1",
        "request_id": f"candidate-validation-request-{digest[:24]}",
        "workstream_id": freeze["workstream_id"], **identity,
        "router_entrypoint": "scripts/ci/validate_change.py",
        "router_policy": "existing-ci7-selection-lease-budget-no-repeat",
        "requested_at": _utc_now(), "writes_product": False,
        "visibility": "git-private-local-only",
    }
    _atomic_json(path, request)
    if _git_text(root, "rev-parse", "HEAD") != candidate or _changed_paths(root):
        raise ValueError("Candidate changed while validation handoff was being recorded")
    return {"decision": "requested", "request": request, "request_path": str(path),
            "writes_performed": True}


def record_candidate_validation(
    root: Path, *, freeze_receipt_id: str, result_receipt: Mapping[str, Any],
    validation_stage: str, started_at: str | None = None, completed_at: str | None = None,
) -> dict[str, Any]:
    """Append one exact-SHA validation result; never run tests or alter product bytes."""
    root = Path(root).resolve()
    freeze = load_freeze_receipt(root, freeze_receipt_id)
    candidate = freeze["candidate_sha"]
    if _git_text(root, "rev-parse", "HEAD") != candidate or _changed_paths(root):
        raise ValueError("validation recording requires the clean frozen Candidate checkout")
    if validation_stage not in {"focused", "fast", "checkpoint", "candidate", "promotion"}:
        raise ValueError("unsupported validation stage")
    ledger_path = _private_path(root, "orrery/candidate-validation/receipts")
    existing = sorted(ledger_path.glob("*.json")) if ledger_path.is_dir() else []
    for path in existing:
        prior = json.loads(path.read_text(encoding="utf-8"))
        if (prior.get("candidate_sha") == candidate and prior.get("validation_stage") == validation_stage
                and prior.get("validation_status") == "validation-failed"):
            raise ValueError("unchanged failed Candidate validation cannot be retried")
        if (prior.get("candidate_sha") == candidate and prior.get("validation_stage") == validation_stage
                and prior.get("validation_status") == "validated"):
            return {**prior, "receipt_path": str(path), "reused": True}
    if result_receipt.get("head_sha", result_receipt.get("sha")) != candidate:
        raise ValueError("runner result is not bound to the frozen Candidate SHA")
    selected = list(result_receipt.get("selected_test_ids", []))
    records = result_receipt.get("records", [])
    if not isinstance(records, list) or not all(isinstance(item, Mapping) for item in records):
        raise ValueError("runner result records are invalid")
    if result_receipt.get("contract_type") != "orrery-test-shard-result-v2":
        raise ValueError("unsupported validation runner receipt contract")
    if result_receipt.get("completed") is not True:
        raise ValueError("incomplete validation runner result cannot be recorded")
    if result_receipt.get("stage") not in {None, validation_stage}:
        raise ValueError("runner result stage does not match the requested validation stage")
    record_ids = [str(item.get("test_id", "")) for item in records]
    if not all(record_ids) or record_ids != selected:
        raise ValueError("runner result test records do not exactly match selected test IDs")
    passed = list(dict.fromkeys(str(item["test_id"]) for item in records if item.get("outcome") in {"success", "skipped", "expected-failure"}))
    failed = list(dict.fromkeys(str(item["test_id"]) for item in records if item.get("outcome") in {"failure", "unexpected-success"}))
    errors = list(dict.fromkeys(str(item["test_id"]) for item in records if item.get("outcome") not in {"success", "skipped", "expected-failure", "failure", "unexpected-success"}))
    successful = result_receipt.get("successful") is True and not failed and not errors
    result_id = hashlib.sha256(json.dumps(dict(result_receipt), sort_keys=True, default=str).encode()).hexdigest()
    began, ended = started_at or _utc_now(), completed_at or _utc_now()
    elapsed = max(0, int(float(result_receipt.get("duration_seconds", 0)) * 1000))
    seed = f"{candidate}\0{validation_stage}\0{result_id}".encode()
    receipt = {
        "schema_version": 1, "contract_type": "candidate-validation-receipt-v1",
        "receipt_id": "candidate-validation-receipt-" + hashlib.sha256(seed).hexdigest()[:24],
        "workstream_id": freeze["workstream_id"], "task_description_sha": freeze["task_description_sha"],
        "freeze_receipt_id": freeze_receipt_id, "candidate_sha": candidate,
        "accepted_surface_fingerprint": freeze["accepted_surface_fingerprint"],
        "relevant_tree_hash": freeze["relevant_tree_hash"], "validation_stage": validation_stage,
        "selected_test_ids": selected, "passed_test_ids": passed, "failed_test_ids": failed,
        "error_test_ids": errors, "result_receipt_ids": [result_id],
        "failure_codes": [] if successful else (["runner-error"] if result_receipt.get("runner_errors") else ["test-failure"]),
        "validation_status": "validated" if successful else "validation-failed",
        "candidate_unchanged": True, "unchanged_retry_performed": False, "writes_product": False,
        "elapsed_ms": elapsed, "started_at": began, "completed_at": ended,
        "environment": {"platform": str(result_receipt.get("os", platform.system())),
                        "runtime": str(result_receipt.get("python", platform.python_version())),
                        "runner": str(result_receipt.get("contract_type", "external-result-receipt"))},
        "visibility": "git-private-local-only",
    }
    validate_candidate_validation_receipt(receipt)
    if _git_text(root, "rev-parse", "HEAD") != candidate or _changed_paths(root):
        raise ValueError("Candidate changed while validation result was being recorded")
    path = ledger_path / f"{receipt['receipt_id']}.json"
    _atomic_json(path, receipt)
    return {**receipt, "receipt_path": str(path), "reused": False}
