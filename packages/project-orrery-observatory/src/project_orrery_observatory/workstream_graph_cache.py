"""Git-private acceleration and non-blocking delivery for Workstream Graph."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


CACHE_SCHEMA_VERSION = 1
CACHE_CONTRACT = "workstream-graph-cache-v1"
DELIVERY_SCHEMA_VERSION = 1
DELIVERY_CONTRACT = "workstream-graph-delivery-v1"
MANIFEST_SCHEMA_VERSION = 2
MANIFEST_CONTRACT = "workstream-graph-input-manifest-v1"
INVALIDATION_CONTRACT = "workstream-graph-invalidation-v1"
MAX_CACHE_BYTES = 12 * 1024 * 1024
MAX_INPUT_FILE_BYTES = 2 * 1024 * 1024
MAX_INPUT_TOTAL_BYTES = 24 * 1024 * 1024
MAX_INPUT_FILES = 1024
MAX_GIT_OUTPUT_BYTES = 512 * 1024
PROVIDER_SCHEMA_VERSION = 1
PROJECTION_SCHEMA_VERSION = 2
_REASON = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
_CACHE_FIELDS = {
    "schema_version", "contract_type", "provider_schema_version",
    "projection_schema_version", "manifest_schema_version", "source_fingerprint",
    "generation", "projection", "projection_hash", "created_at", "refreshed_at",
    "writes_author_documents", "network_performed",
}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _no_window_options() -> dict[str, Any]:
    if os.name != "nt":
        return {}
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}


def _git(project_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project_root), *arguments], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
        **_no_window_options(),
    )
    if completed.returncode:
        raise ValueError("Graph cache requires a local Git repository")
    if len(completed.stdout.encode("utf-8")) > MAX_GIT_OUTPUT_BYTES:
        raise ValueError("Graph cache Git identity output exceeds the bounded size")
    return completed.stdout.strip()


def _git_common_dir(project_root: Path) -> Path:
    root = Path(project_root).resolve()
    value = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return Path(os.path.realpath(value))


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _ensure_private_root(project_root: Path) -> Path:
    common = _git_common_dir(project_root)
    root = common / "orrery" / "cache" / "workstream-graph-v1"
    for ancestor in (common, common / "orrery", common / "orrery" / "cache"):
        if os.path.lexists(ancestor) and (not ancestor.is_dir() or _is_link_or_reparse(ancestor)):
            raise ValueError("Graph cache ancestor must be a real directory")
    root.mkdir(parents=True, exist_ok=True)
    if _is_link_or_reparse(root) or not root.is_dir():
        raise ValueError("Graph cache root must be a real directory")
    return root


def _read_json(path: Path, *, maximum: int = MAX_CACHE_BYTES) -> dict[str, Any]:
    if _is_link_or_reparse(path):
        raise ValueError("Graph cache entry must not be a link or reparse point")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
        raise ValueError("Graph cache entry must be a bounded regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    after = path.lstat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Graph cache entry changed while being read")
    if not isinstance(value, dict):
        raise ValueError("Graph cache entry root must be an object")
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = _canonical_bytes(dict(value)) + b"\n"
    if len(payload) > MAX_CACHE_BYTES:
        raise ValueError("Graph cache entry exceeds the bounded size")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Graph projection must be an object")
    if value.get("contract_type") != "workstream-relation-graph-observatory":
        raise ValueError("Graph projection contract is incompatible")
    if value.get("projection_schema_version") != PROJECTION_SCHEMA_VERSION:
        raise ValueError("Graph projection schema is incompatible")
    if value.get("authority") != "derived-read-only":
        raise ValueError("Graph projection authority is incompatible")
    if value.get("read_only") is not True or value.get("writes_performed") is not False:
        raise ValueError("Graph projection is not read-only")
    if value.get("network_performed") is not False or value.get("execution_capability") is not False:
        raise ValueError("Graph projection exceeds the local read-only boundary")
    if len(_canonical_bytes(value)) > MAX_CACHE_BYTES:
        raise ValueError("Graph projection exceeds the bounded size")
    return dict(value)


def _validate_cache(value: Mapping[str, Any]) -> dict[str, Any]:
    if set(value) != _CACHE_FIELDS:
        raise ValueError("Graph cache fields do not match schema v1")
    if value.get("schema_version") != CACHE_SCHEMA_VERSION or value.get("contract_type") != CACHE_CONTRACT:
        raise ValueError("Graph cache contract is incompatible")
    if value.get("provider_schema_version") != PROVIDER_SCHEMA_VERSION:
        raise ValueError("Graph provider schema is incompatible")
    if value.get("projection_schema_version") != PROJECTION_SCHEMA_VERSION:
        raise ValueError("Graph projection schema is incompatible")
    if value.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError("Graph manifest schema is incompatible")
    if value.get("writes_author_documents") is not False or value.get("network_performed") is not False:
        raise ValueError("Graph cache authority boundary is incompatible")
    fingerprint = value.get("source_fingerprint")
    projection_hash = value.get("projection_hash")
    generation = value.get("generation")
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError("Graph cache source fingerprint is invalid")
    if not isinstance(projection_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", projection_hash):
        raise ValueError("Graph cache projection hash is invalid")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise ValueError("Graph cache generation is invalid")
    projection = _validate_projection(value.get("projection"))
    if _digest(projection) != projection_hash:
        raise ValueError("Graph cache projection hash does not match")
    return dict(value)


def _read_generation(root: Path) -> int:
    path = root / "invalidation.json"
    if not path.exists():
        return 0
    value = _read_json(path, maximum=16 * 1024)
    if set(value) != {"schema_version", "contract_type", "generation", "reason_code", "invalidated_at"}:
        raise ValueError("Graph invalidation fields do not match schema v1")
    if value.get("schema_version") != 1 or value.get("contract_type") != INVALIDATION_CONTRACT:
        raise ValueError("Graph invalidation contract is incompatible")
    generation = value.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise ValueError("Graph invalidation generation is invalid")
    return generation


def invalidate_workstream_graph_cache(project_root: Path, *, reason_code: str) -> dict[str, Any]:
    """Advance the local cache generation after an authoritative owner write succeeds."""
    if not isinstance(reason_code, str) or not _REASON.fullmatch(reason_code):
        raise ValueError("Graph invalidation reason must be a bounded reason code")
    root = _ensure_private_root(project_root)
    generation = _read_generation(root) + 1
    value = {
        "schema_version": 1, "contract_type": INVALIDATION_CONTRACT,
        "generation": generation, "reason_code": reason_code, "invalidated_at": _timestamp(),
    }
    _atomic_json(root / "invalidation.json", value)
    return {**value, "writes_author_documents": False, "network_performed": False}


def _integration_identity(project_root: Path) -> tuple[str, str]:
    config_path = project_root / ".project-orrery.json"
    value = _read_json(config_path, maximum=512 * 1024)
    collaboration = value.get("collaboration")
    integration_ref = collaboration.get("integration_ref", "refs/heads/main") if isinstance(collaboration, dict) else "refs/heads/main"
    if not isinstance(integration_ref, str) or not re.fullmatch(r"refs/(heads|remotes)/[A-Za-z0-9._/-]+", integration_ref):
        raise ValueError("Graph manifest integration ref is invalid")
    oid = _git(project_root, "rev-parse", "--verify", integration_ref)
    if not re.fullmatch(r"[0-9a-f]{40,64}", oid):
        raise ValueError("Graph manifest integration identity is invalid")
    return integration_ref, oid


def _live_worktree_identity(project_root: Path) -> dict[str, Any]:
    """Bind cache currentness to every registered live worktree HEAD/ref identity."""
    raw = _git(project_root, "worktree", "list", "--porcelain", "-z")
    records = [record for record in raw.split("\0\0") if record]
    if not records or len(records) > 256:
        raise ValueError("Graph manifest live worktree registry is invalid or unbounded")
    for record in records:
        fields = [field for field in record.split("\0") if field]
        if not fields or not fields[0].startswith("worktree "):
            raise ValueError("Graph manifest live worktree identity is malformed")
        heads = [field.removeprefix("HEAD ") for field in fields if field.startswith("HEAD ")]
        if len(heads) != 1 or not re.fullmatch(r"[0-9a-f]{40,64}", heads[0]):
            raise ValueError("Graph manifest live worktree HEAD is invalid")
        branches = [field.removeprefix("branch ") for field in fields if field.startswith("branch ")]
        if branches and (
            len(branches) != 1
            or not re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", branches[0])
        ):
            raise ValueError("Graph manifest live worktree ref is invalid")
    return {
        "count": len(records),
        "registry_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    }


def build_input_manifest(project_root: Path) -> dict[str, Any]:
    """Hash only bounded Graph-owned metadata and one configured integration identity."""
    root = Path(project_root).resolve()
    common = _git_common_dir(root)
    integration_ref, integration_oid = _integration_identity(root)
    allowed_roots = (
        common / "orrery" / "workstream-relations",
        common / "orrery" / "workstream-relation-capture-v2",
        common / "orrery" / "workstream-program-hierarchy-v1",
        common / "orrery" / "retired-worktree-sessions",
        common / "orrery" / "workstream-history-index-v1",
        common / "worktrees",
    )
    entries: list[dict[str, Any]] = []
    total = 0
    currentness = "current"
    reason_codes: list[str] = []
    primary_session = common / "orrery" / "worktree.json"
    if primary_session.exists():
        if _is_link_or_reparse(primary_session):
            currentness = "unknown"
            reason_codes.append("unsafe-primary-session")
        else:
            metadata = primary_session.stat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_INPUT_FILE_BYTES:
                currentness = "unknown"
                reason_codes.append("oversized-primary-session")
            else:
                total += metadata.st_size
                entries.append({
                    "id": primary_session.relative_to(common).as_posix(),
                    "size": metadata.st_size,
                    "mtime_ns": metadata.st_mtime_ns,
                    "sha256": hashlib.sha256(primary_session.read_bytes()).hexdigest(),
                })
    for source_root in allowed_roots:
        if not source_root.exists():
            continue
        if _is_link_or_reparse(source_root) or not source_root.is_dir():
            currentness = "unknown"
            reason_codes.append("unsafe-input-root")
            continue
        for candidate in sorted(source_root.rglob("*"), key=lambda item: item.as_posix()):
            if len(entries) >= MAX_INPUT_FILES:
                currentness = "unknown"
                reason_codes.append("input-file-limit")
                break
            if not candidate.is_file():
                continue
            if source_root == common / "worktrees" and candidate.name != "worktree.json":
                continue
            if _is_link_or_reparse(candidate):
                currentness = "unknown"
                reason_codes.append("unsafe-input-entry")
                continue
            metadata = candidate.stat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_INPUT_FILE_BYTES:
                currentness = "unknown"
                reason_codes.append("oversized-input-entry")
                continue
            total += metadata.st_size
            if total > MAX_INPUT_TOTAL_BYTES:
                currentness = "unknown"
                reason_codes.append("input-byte-limit")
                break
            relative = candidate.relative_to(common).as_posix()
            entries.append({
                "id": relative,
                "size": metadata.st_size,
                "mtime_ns": metadata.st_mtime_ns,
                "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
            })
    generation = _read_generation(_ensure_private_root(root))
    live_worktrees = _live_worktree_identity(root)
    fingerprint_input = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "projection_schema_version": PROJECTION_SCHEMA_VERSION,
        "generation": generation,
        "integration_ref": integration_ref,
        "integration_oid": integration_oid,
        "live_worktrees": live_worktrees,
        "entries": entries,
        "currentness": currentness,
        "reason_codes": sorted(set(reason_codes)),
    }
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "contract_type": MANIFEST_CONTRACT,
        **fingerprint_input,
        "source_fingerprint": _digest(fingerprint_input),
        "bounded": True,
        "full_source_scan_performed": False,
        "worktree_status_scan_performed": False,
        "network_performed": False,
    }


class WorkstreamGraphDelivery:
    """Own one cache generation and at most one background provider refresh."""

    def __init__(self, project_root: Path, *, logger: Callable[[str], None] | None = None):
        self.project_root = Path(project_root).resolve()
        self.cache_root = _ensure_private_root(self.project_root)
        self.logger = logger or (lambda _message: None)
        self._lock = threading.RLock()
        self._cancel = threading.Event()
        self._worker: threading.Thread | None = None
        self._watcher: threading.Thread | None = None
        self._provider: Callable[[], Mapping[str, Any]] | None = None
        self._projector: Callable[[Callable[[], Mapping[str, Any]]], Mapping[str, Any]] | None = None
        self._on_provider_payload: Callable[[Mapping[str, Any]], None] | None = None
        self._observed_invalidation_generation = 0
        self._state = "empty"
        self._reason_codes: list[str] = ["cache-not-inspected"]
        self._projection: dict[str, Any] | None = None
        self._generation = 0
        self._captured_at: str | None = None
        self._refreshed_at: str | None = None
        self._provider_runs = 0

    def _load_candidate(self, name: str) -> dict[str, Any] | None:
        path = self.cache_root / name
        if not path.exists():
            return None
        return _validate_cache(_read_json(path))

    def start(
        self,
        *,
        provider: Callable[[], Mapping[str, Any]],
        projector: Callable[[Callable[[], Mapping[str, Any]]], Mapping[str, Any]],
        on_provider_payload: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        self._provider = provider
        self._projector = projector
        self._on_provider_payload = on_provider_payload
        if self._cancel.is_set():
            with self._lock:
                self._state = "failed"
                self._reason_codes = ["activation-cancelled"]
            return self.snapshot()
        try:
            manifest = build_input_manifest(self.project_root)
        except Exception:
            manifest = None
        try:
            self._observed_invalidation_generation = _read_generation(self.cache_root)
        except Exception:
            self._observed_invalidation_generation = 0
        cached: dict[str, Any] | None = None
        cache_reason = "cache-absent"
        for name in ("current.json", "last-known.json"):
            try:
                cached = self._load_candidate(name)
                if cached is not None:
                    break
            except Exception:
                cache_reason = "cache-corrupt-or-incompatible"
        with self._lock:
            if self._cancel.is_set():
                self._state = "failed"
                self._reason_codes = ["activation-cancelled"]
                return self.snapshot()
            if cached is not None:
                self._projection = dict(cached["projection"])
                self._generation = int(cached["generation"])
                self._captured_at = str(cached["created_at"])
                self._refreshed_at = str(cached["refreshed_at"])
            if (
                cached is not None and manifest is not None
                and manifest.get("currentness") == "current"
                and cached.get("source_fingerprint") == manifest.get("source_fingerprint")
                and cached.get("generation") == manifest.get("generation")
            ):
                self._state = "cached-current"
                self._reason_codes = ["validated-cache-hit"]
                self.logger("Graph cache validated; background provider skipped")
                self._start_watcher()
                return self.snapshot()
            self._state = "refreshing"
            self._reason_codes = [
                "bounded-manifest-unknown" if manifest is None or manifest.get("currentness") != "current"
                else "source-fingerprint-changed" if cached is not None else cache_reason
            ]
            worker = threading.Thread(
                target=self._refresh,
                kwargs={
                    "manifest": manifest, "provider": provider, "projector": projector,
                    "on_provider_payload": on_provider_payload,
                },
                daemon=True,
                name="orrery-workstream-graph-refresh",
            )
            self._worker = worker
            worker.start()
            self._start_watcher()
            return self.snapshot()

    def _start_watcher(self) -> None:
        with self._lock:
            if self._watcher is not None and self._watcher.is_alive():
                return
            watcher = threading.Thread(
                target=self._watch_invalidations,
                daemon=True,
                name="orrery-workstream-graph-invalidation-watch",
            )
            self._watcher = watcher
            watcher.start()

    def _watch_invalidations(self) -> None:
        while not self._cancel.wait(0.25):
            try:
                generation = _read_generation(self.cache_root)
            except Exception:
                continue
            with self._lock:
                worker_active = self._worker is not None and self._worker.is_alive()
                if generation == self._observed_invalidation_generation or worker_active:
                    continue
                provider = self._provider
                projector = self._projector
                if provider is None or projector is None:
                    continue
            try:
                manifest = build_input_manifest(self.project_root)
            except Exception:
                manifest = None
            with self._lock:
                if self._cancel.is_set() or (self._worker is not None and self._worker.is_alive()):
                    continue
                self._observed_invalidation_generation = generation
                self._state = "refreshing"
                self._reason_codes = ["invalidation-generation-changed"]
                worker = threading.Thread(
                    target=self._refresh,
                    kwargs={
                        "manifest": manifest,
                        "provider": provider,
                        "projector": projector,
                        "on_provider_payload": self._on_provider_payload,
                    },
                    daemon=True,
                    name="orrery-workstream-graph-refresh",
                )
                self._worker = worker
                worker.start()

    def _refresh(
        self,
        *,
        manifest: Mapping[str, Any] | None,
        provider: Callable[[], Mapping[str, Any]],
        projector: Callable[[Callable[[], Mapping[str, Any]]], Mapping[str, Any]],
        on_provider_payload: Callable[[Mapping[str, Any]], None] | None,
    ) -> None:
        if self._cancel.is_set():
            return
        try:
            with self._lock:
                self._provider_runs += 1
            started = _timestamp()
            payload = dict(provider())
            if self._cancel.is_set():
                return
            if payload.get("provider_schema_version") != PROVIDER_SCHEMA_VERSION:
                raise ValueError("Graph provider schema is incompatible")
            if on_provider_payload is not None:
                try:
                    on_provider_payload(payload)
                except Exception:
                    self.logger("Graph provider side projection failed with a sanitized local error")
            projection = _validate_projection(projector(lambda: payload))
            if projection.get("status") != "ready":
                raise ValueError("Graph provider did not produce a complete ready projection")
            if self._cancel.is_set():
                return
            current_manifest = build_input_manifest(self.project_root)
            if current_manifest.get("currentness") != "current":
                raise ValueError("Graph input currentness cannot be proven")
            if manifest is not None and manifest.get("source_fingerprint") != current_manifest.get("source_fingerprint"):
                raise ValueError("Graph inputs changed during refresh")
            refreshed = _timestamp()
            value = {
                "schema_version": CACHE_SCHEMA_VERSION,
                "contract_type": CACHE_CONTRACT,
                "provider_schema_version": PROVIDER_SCHEMA_VERSION,
                "projection_schema_version": PROJECTION_SCHEMA_VERSION,
                "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
                "source_fingerprint": current_manifest["source_fingerprint"],
                "generation": current_manifest["generation"],
                "projection": projection,
                "projection_hash": _digest(projection),
                "created_at": started,
                "refreshed_at": refreshed,
                "writes_author_documents": False,
                "network_performed": False,
            }
            previous: dict[str, Any] | None = None
            try:
                previous = self._load_candidate("current.json")
            except Exception:
                previous = None
            if self._cancel.is_set():
                return
            if previous is not None:
                _atomic_json(self.cache_root / "last-known.json", previous)
            if self._cancel.is_set():
                return
            _atomic_json(self.cache_root / "current.json", value)
            if previous is None and not self._cancel.is_set():
                _atomic_json(self.cache_root / "last-known.json", value)
            with self._lock:
                if self._cancel.is_set():
                    return
                self._projection = projection
                self._generation = int(value["generation"])
                self._captured_at = started
                self._refreshed_at = refreshed
                self._state = "ready"
                self._reason_codes = ["atomic-refresh-complete"]
            self.logger("Graph cache refresh completed")
        except Exception:
            with self._lock:
                if self._cancel.is_set():
                    return
                self._state = "failed"
                self._reason_codes = ["provider-or-cache-refresh-failed"]
            self.logger("Graph cache refresh failed with a sanitized local error")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            state = self._state
            projection = dict(self._projection) if self._projection is not None else None
            cache_state = (
                "cached-current" if state == "cached-current" else
                "cached-stale" if projection is not None and state in {"refreshing", "failed"} else
                "empty" if projection is None else state
            )
            result: dict[str, Any] = {
                "schema_version": DELIVERY_SCHEMA_VERSION,
                "contract_type": DELIVERY_CONTRACT,
                "status": state,
                "cache_state": cache_state,
                "generation": self._generation,
                "captured_at": self._captured_at,
                "refreshed_at": self._refreshed_at,
                "provider_schema_version": PROVIDER_SCHEMA_VERSION,
                "projection_schema_version": PROJECTION_SCHEMA_VERSION,
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "reason_codes": list(self._reason_codes),
                "provider_runs_since_start": self._provider_runs,
                "projection": projection,
                "authority": "derived-read-only",
                "read_only": True,
                "writes_author_documents": False,
                "network_performed": False,
                "execution_capability": False,
                "available_actions": [],
            }
            return result

    def health(self) -> dict[str, Any]:
        value = self.snapshot()
        return {
            "status": value["status"], "cache_state": value["cache_state"],
            "generation": value["generation"], "reason_codes": value["reason_codes"],
        }

    def close(self, *, timeout: float = 1.0) -> bool:
        self._cancel.set()
        worker = self._worker
        watcher = self._watcher
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=max(0.0, timeout))
        if watcher is not None and watcher is not threading.current_thread():
            watcher.join(timeout=max(0.0, timeout))
        return (worker is None or not worker.is_alive()) and (watcher is None or not watcher.is_alive())
