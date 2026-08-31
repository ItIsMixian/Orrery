"""Versioned, append-only Workstream program and phase membership facts.

Program membership is deliberately orthogonal to task series and semantic
relations.  This module never creates relation events, gates, closure, or
ownership effects.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence


PROGRAM_SCHEMA_VERSION = 1
GROUP_KINDS = ("program", "phase")
EVENT_KINDS = ("accepted", "archived", "proposed", "rejected", "superseded")
MAX_EVENT_BYTES = 256 * 1024
MAX_EVENTS = 1024
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_EVENT_FILE = re.compile(r"^([1-9][0-9]{0,8})-([A-Za-z0-9][A-Za-z0-9._-]{0,127})\.json$")

SELF_HOST_W_GROUPS = (
    {"group_id": "workstream-w", "group_kind": "program", "parent_group_id": None,
     "display_label": "W · 多 Workstream 协作", "order": 0},
    {"group_id": "workstream-w5", "group_kind": "phase", "parent_group_id": "workstream-w",
     "display_label": "W5 · Team collaboration", "order": 5},
    {"group_id": "workstream-w6", "group_kind": "phase", "parent_group_id": "workstream-w",
     "display_label": "W6 · Workspace maintenance", "order": 6},
    {"group_id": "workstream-w7", "group_kind": "phase", "parent_group_id": "workstream-w",
     "display_label": "W7 · Relations / integration", "order": 7},
)
SELF_HOST_W_MEMBERS = {
    "workstream-w5": (
        "W5C-team-observatory-ux", "W5D-lan-collaboration-harness",
        "W5E-team-observatory-ui-closeout",
    ),
    "workstream-w6": ("W6.1-incremental-maintenance-quick-remove",),
    "workstream-w7": (
        "W7.1-archived-session-relation-projection",
        "W7.2.2-graph-arrow-scrollbar-visual-integration",
        "W7.2.3-workstream-graph-density-correction",
        "W7.3-workstream-relation-capture-confirmation",
        "W7.3-integration-acceptance",
    ),
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _event_hash(value: Mapping[str, Any]) -> str:
    body = dict(value)
    body.pop("event_hash", None)
    return _digest(body)


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a filesystem-safe identifier")
    return value


def _timestamp(value: str | None) -> str:
    candidate = value or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if not isinstance(candidate, str) or len(candidate) > 64:
        raise ValueError("recorded_at must be bounded")
    parsed = dt.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("recorded_at must include a timezone")
    return candidate


def _label(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 160 or any(c in value for c in "\r\n\0"):
        raise ValueError("display_label must be non-empty, single-line, and bounded")
    return value.strip()


def _source_links(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value or len(value) > 512 or "://" in value or value.startswith(("/", "~")):
            raise ValueError("source link must be a bounded relative or opaque reference")
        if re.match(r"^[A-Za-z]:", value) or any(part in {"", ".", ".."} for part in value.replace("\\", "/").split("/")):
            raise ValueError("source link must not escape the project evidence boundary")
        result.append(value.replace("\\", "/"))
    return sorted(set(result))


def hierarchy_storage_root(project_root: Path) -> Path:
    import subprocess
    root = Path(project_root).resolve()
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"], capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode:
        raise ValueError("program hierarchy requires a local Git repository")
    common = Path(completed.stdout.strip())
    if not common.is_absolute():
        common = root / common
    return Path(os.path.realpath(common)) / "orrery" / "workstream-program-hierarchy-v1"


def _unsafe(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        return True


def _read(path: Path) -> dict[str, Any]:
    if _unsafe(path) or not path.is_file() or path.stat().st_size > MAX_EVENT_BYTES:
        raise ValueError("program hierarchy event must be a bounded regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("program hierarchy event root must be an object")
    return value


def _history(root: Path, category: str, identifier: str | None = None) -> dict[str, list[dict[str, Any]]]:
    base = root / category
    if identifier:
        base = base / _identifier(identifier, f"{category} identifier")
    if not base.exists():
        return {}
    if _unsafe(base) or not base.is_dir():
        raise ValueError("program hierarchy storage must contain real directories")
    files = sorted(base.rglob("*.json"))
    if len(files) > MAX_EVENTS:
        raise ValueError("program hierarchy event count exceeds limit")
    result: dict[str, list[dict[str, Any]]] = {}
    for path in files:
        if not _EVENT_FILE.fullmatch(path.name) or _unsafe(path):
            raise ValueError("program hierarchy storage contains an invalid entry")
        value = _read(path)
        key = str(value.get("group_id") or value.get("membership_id") or "")
        result.setdefault(key, []).append(value)
    for values in result.values():
        values.sort(key=lambda item: int(item["revision"]))
        prior = None
        for revision, item in enumerate(values, 1):
            if item.get("revision") != revision or item.get("prior_event_hash") != prior:
                raise ValueError("program hierarchy revision chain is invalid")
            validate_program_event(item)
            prior = item["event_hash"]
    return result


def validate_program_event(value: Mapping[str, Any]) -> None:
    contract = value.get("contract_type")
    common = {"schema_version", "contract_type", "event_id", "event_hash", "revision", "event_kind",
              "lifecycle", "actor", "source_links", "recorded_at", "prior_event_hash", "writes_performed"}
    if contract == "workstream-group-event":
        required = common | {"group_id", "group_kind", "parent_group_id", "display_label", "order"}
    elif contract == "workstream-group-membership-event":
        required = common | {"membership_id", "workstream_id", "group_path"}
    else:
        raise ValueError("unsupported program hierarchy contract")
    if set(value) != required or value.get("schema_version") != PROGRAM_SCHEMA_VERSION:
        raise ValueError("program hierarchy fields do not match schema v1")
    _identifier(value.get("event_id"), "event_id")
    revision = value.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValueError("revision must be a positive integer")
    if value.get("event_kind") not in EVENT_KINDS or value.get("lifecycle") not in {"active", "archived", "proposed", "rejected", "superseded"}:
        raise ValueError("program hierarchy lifecycle is invalid")
    actor = value.get("actor")
    if not isinstance(actor, Mapping) or set(actor) != {"kind", "id", "role"}:
        raise ValueError("program hierarchy actor is invalid")
    if actor.get("kind") not in {"agent", "human", "tool"} or actor.get("role") not in {"integrator", "proposer"}:
        raise ValueError("program hierarchy actor role is invalid")
    _identifier(actor.get("id"), "actor id")
    if value["event_kind"] == "accepted" and (actor["kind"], actor["role"]) != ("human", "integrator"):
        raise ValueError("only a human integrator may accept program hierarchy facts")
    if value["event_kind"] == "proposed" and value["lifecycle"] != "proposed":
        raise ValueError("proposed event must remain proposed")
    if value["event_kind"] == "accepted" and value["lifecycle"] != "active":
        raise ValueError("accepted event must be active")
    if value["event_kind"] in {"archived", "rejected", "superseded"} and value["lifecycle"] != value["event_kind"]:
        raise ValueError("terminal event lifecycle mismatch")
    if value.get("source_links") != _source_links(value.get("source_links", [])):
        raise ValueError("program hierarchy source links are not normalized")
    _timestamp(value.get("recorded_at"))
    prior = value.get("prior_event_hash")
    if prior is not None and (not isinstance(prior, str) or not _HASH.fullmatch(prior)):
        raise ValueError("prior_event_hash is invalid")
    if (revision == 1) != (prior is None):
        raise ValueError("prior_event_hash does not match revision")
    if contract == "workstream-group-event":
        _identifier(value.get("group_id"), "group_id")
        if value.get("group_kind") not in GROUP_KINDS:
            raise ValueError("group_kind is unsupported")
        parent = value.get("parent_group_id")
        if value["group_kind"] == "program" and parent is not None:
            raise ValueError("program cannot have a parent")
        if value["group_kind"] == "phase" and not _identifier(parent, "parent_group_id"):
            raise ValueError("phase requires a program parent")
        _label(value.get("display_label"))
        if not isinstance(value.get("order"), int) or isinstance(value.get("order"), bool):
            raise ValueError("group order must be an integer")
    else:
        _identifier(value.get("membership_id"), "membership_id")
        _identifier(value.get("workstream_id"), "workstream_id")
        path = value.get("group_path")
        if not isinstance(path, list) or len(path) != 2 or any(_identifier(item, "group_path item") != item for item in path):
            raise ValueError("v1 membership requires one program and one phase")
    if not isinstance(value.get("writes_performed"), bool) or value.get("event_hash") != _event_hash(value):
        raise ValueError("program hierarchy event hash is invalid")


def _append(root: Path, category: str, identifier: str, value: dict[str, Any], expected_revision: int) -> dict[str, Any]:
    history = _history(root, category, identifier).get(identifier, [])
    if len(history) != expected_revision:
        raise ValueError("program hierarchy CAS revision mismatch")
    value["revision"] = expected_revision + 1
    value["prior_event_hash"] = history[-1]["event_hash"] if history else None
    value["event_hash"] = _event_hash(value)
    validate_program_event(value)
    target = root / category / identifier
    for ancestor in (root.parent, root, root / category, target):
        if ancestor.exists() and (_unsafe(ancestor) or not ancestor.is_dir()):
            raise ValueError("program hierarchy write target is unsafe")
        ancestor.mkdir(parents=True, exist_ok=True)
    destination = target / f"{value['revision']}-{value['event_id']}.json"
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if len(payload) > MAX_EVENT_BYTES:
        raise ValueError("program hierarchy event exceeds size limit")
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return dict(value)


def append_group_event(project_root: Path, *, group_id: str, group_kind: str, parent_group_id: str | None,
                       display_label: str, order: int, event_kind: str, expected_revision: int,
                       actor_kind: str, actor_id: str, actor_role: str, source_links: Sequence[str] = (),
                       recorded_at: str | None = None) -> dict[str, Any]:
    identifier = _identifier(group_id, "group_id")
    value = {
        "schema_version": 1, "contract_type": "workstream-group-event",
        "event_id": f"group-{_digest([identifier, expected_revision + 1, event_kind])[:24]}",
        "event_hash": "0" * 64, "revision": 0, "event_kind": event_kind,
        "group_id": identifier, "group_kind": group_kind, "parent_group_id": parent_group_id,
        "display_label": display_label, "order": order,
        "lifecycle": "active" if event_kind == "accepted" else event_kind,
        "actor": {"kind": actor_kind, "id": actor_id, "role": actor_role},
        "source_links": _source_links(source_links), "recorded_at": _timestamp(recorded_at),
        "prior_event_hash": None, "writes_performed": True,
    }
    return _append(hierarchy_storage_root(project_root), "groups", identifier, value, expected_revision)


def append_membership_event(project_root: Path, *, membership_id: str, workstream_id: str,
                            group_path: Sequence[str], event_kind: str, expected_revision: int,
                            actor_kind: str, actor_id: str, actor_role: str,
                            source_links: Sequence[str] = (), recorded_at: str | None = None) -> dict[str, Any]:
    identifier = _identifier(membership_id, "membership_id")
    value = {
        "schema_version": 1, "contract_type": "workstream-group-membership-event",
        "event_id": f"membership-{_digest([identifier, expected_revision + 1, event_kind])[:24]}",
        "event_hash": "0" * 64, "revision": 0, "event_kind": event_kind,
        "membership_id": identifier, "workstream_id": workstream_id, "group_path": list(group_path),
        "lifecycle": "active" if event_kind == "accepted" else event_kind,
        "actor": {"kind": actor_kind, "id": actor_id, "role": actor_role},
        "source_links": _source_links(source_links), "recorded_at": _timestamp(recorded_at),
        "prior_event_hash": None, "writes_performed": True,
    }
    return _append(hierarchy_storage_root(project_root), "memberships", identifier, value, expected_revision)


def inspect_program_hierarchy(project_root: Path) -> dict[str, Any]:
    root = hierarchy_storage_root(project_root)
    group_history = _history(root, "groups")
    membership_history = _history(root, "memberships")
    current_groups = {key: values[-1] for key, values in group_history.items() if values[-1]["lifecycle"] == "active"}
    programs = {key: value for key, value in current_groups.items() if value["group_kind"] == "program"}
    for value in current_groups.values():
        if value["group_kind"] == "phase" and value["parent_group_id"] not in programs:
            raise ValueError("phase parent is missing or not an active program")
    current_memberships: list[dict[str, Any]] = []
    seen_workstreams: set[str] = set()
    for values in membership_history.values():
        value = values[-1]
        if value["lifecycle"] != "active":
            continue
        program_id, phase_id = value["group_path"]
        phase = current_groups.get(phase_id)
        if program_id not in programs or not phase or phase["group_kind"] != "phase" or phase["parent_group_id"] != program_id:
            raise ValueError("membership group path does not resolve root-to-leaf")
        if value["workstream_id"] in seen_workstreams:
            raise ValueError("v1 permits only one active primary membership per Workstream")
        seen_workstreams.add(value["workstream_id"])
        current_memberships.append(dict(value))
    return {
        "schema_version": 1, "contract_type": "workstream-program-hierarchy-inspection",
        "groups": sorted((dict(item) for item in current_groups.values()), key=lambda item: (item["order"], item["group_id"])),
        "memberships": sorted(current_memberships, key=lambda item: item["workstream_id"]),
        "pending_group_events": sorted((dict(v[-1]) for v in group_history.values() if v[-1]["lifecycle"] == "proposed"), key=lambda item: item["group_id"]),
        "pending_membership_events": sorted((dict(v[-1]) for v in membership_history.values() if v[-1]["lifecycle"] == "proposed"), key=lambda item: item["workstream_id"]),
        "read_only": True, "writes_performed": False, "name_inference_performed": False,
        "relation_effects": {"series": False, "relations": False, "gates": False, "closure": False, "ownership": False},
    }


def apply_self_host_w_repair(project_root: Path, *, integrator_id: str, recorded_at: str | None = None) -> dict[str, Any]:
    """Apply the exact ADR-0020 repair fixture; never scan names or prefixes."""
    root = hierarchy_storage_root(project_root)
    source = ("docs/design/workstream-program-hierarchy-and-graph-bundling.md",)
    written: list[str] = []
    for group in SELF_HOST_W_GROUPS:
        history = _history(root, "groups", group["group_id"]).get(group["group_id"], [])
        if history and history[-1]["lifecycle"] == "active":
            continue
        append_group_event(project_root, **group, event_kind="accepted", expected_revision=len(history),
                           actor_kind="human", actor_id=integrator_id, actor_role="integrator",
                           source_links=source, recorded_at=recorded_at)
        written.append(group["group_id"])
    for phase_id, workstreams in SELF_HOST_W_MEMBERS.items():
        for workstream_id in workstreams:
            membership_id = "membership-" + _digest([workstream_id, "workstream-w", phase_id])[:24]
            history = _history(root, "memberships", membership_id).get(membership_id, [])
            if history and history[-1]["lifecycle"] == "active":
                continue
            append_membership_event(
                project_root, membership_id=membership_id, workstream_id=workstream_id,
                group_path=("workstream-w", phase_id), event_kind="accepted", expected_revision=len(history),
                actor_kind="human", actor_id=integrator_id, actor_role="integrator",
                source_links=source, recorded_at=recorded_at,
            )
            written.append(membership_id)
    return {"contract_type": "workstream-self-host-w-repair-receipt", "schema_version": 1,
            "written_ids": written, "writes_performed": bool(written),
            "name_inference_performed": False, "hierarchy": inspect_program_hierarchy(project_root)}
