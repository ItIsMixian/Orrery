"""Read-only Personal Observatory projection over canonical collaboration data.

The collector deliberately delegates Git identity, Scope, finding, and lifecycle
semantics to ``project_orrery_core.collaboration``.  This module only aggregates
those machine contracts for presentation; it does not mutate Workstream sessions
or infer the future W3 review/integration/cleanup decisions.
"""

from __future__ import annotations

import html
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECTION_SCHEMA = "project-orrery-personal-observatory-v1"
W3_SLOT_KEYS = ("review_queue", "integration_eligibility", "cleanup_eligibility")


def _now(value: str | None = None) -> str:
    return value or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _short_oid(value: object) -> str:
    text = str(value or "")
    return text[:9] if text else "Unknown"


def _branch_label(value: object) -> str:
    text = str(value or "")
    return text.removeprefix("refs/heads/") if text else "detached"


def _w3_slots(projection: Mapping[str, Any] | None) -> dict[str, dict[str, str]]:
    """Consume display-ready W3 slots without implementing any W3 policy."""

    if projection is None:
        return {
            key: {
                "status": "unavailable",
                "label": "Unavailable",
                "detail": "W3 not integrated",
                "source": "optional-w3-slot",
            }
            for key in W3_SLOT_KEYS
        }
    slots: dict[str, dict[str, str]] = {}
    for key in W3_SLOT_KEYS:
        value = projection.get(key)
        if not isinstance(value, Mapping):
            slots[key] = {
                "status": "unavailable",
                "label": "Unavailable",
                "detail": "W3 slot missing",
                "source": "optional-w3-slot",
            }
            continue
        slots[key] = {
            "status": str(value.get("status", "unknown")),
            "label": str(value.get("label", "Unknown")),
            "detail": str(value.get("detail", "W3 provider supplied no detail")),
            "source": str(value.get("source", "w3-display-provider")),
        }
    return slots


def _unavailable_worktree(record: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "workstream_id": "Unavailable",
        "worktree_id": "Unknown",
        "worktree_path": str(record.get("worktree", "Unknown")),
        "branch": _branch_label(record.get("branch")),
        "head": str(record.get("HEAD", "")),
        "integration_ref": "Unknown",
        "integration_oid": "Unknown",
        "merge_base": "Unknown",
        "ahead": None,
        "behind": None,
        "fact_scope": "unknown",
        "dirty": None,
        "dirty_entry_count": None,
        "untracked_count": None,
        "primary_subsystem_id": "Unknown",
        "affected_subsystem_ids": [],
        "scope_revision": None,
        "scope_path_count": None,
        "scope_paths": [],
        "lifecycle_phase": "unavailable",
        "runtime_condition": "stale-unknown",
        "evidence_freshness": "unknown",
        "session_state": "unavailable",
        "captured_at": None,
        "platform_session": None,
        "finding_counts": {},
        "findings": [],
        "availability": "unavailable",
        "unavailable_reason": reason,
        "has_session": False,
        "display_group": "unavailable",
    }


def build_personal_observatory_projection(
    project_root: Path,
    *,
    include_local_worktrees: bool = True,
    excluded_branches: Sequence[str] = (),
    w3_projection: Mapping[str, Any] | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Aggregate W1/W2 contracts into a read-only Personal Mode snapshot.

    ``excluded_branches`` is a presentation-time isolation boundary.  Excluded
    worktrees are listed as Unavailable using the shared Git worktree registry,
    but their worktree files and private sessions are not opened.
    """

    from project_orrery_core.collaboration import (
        _normalized_path,
        _worktree_records,
        collect_scope_observation,
        compute_overlap_findings,
        inspect_worktree_status,
        reconcile_overlap_findings,
    )

    root = Path(project_root).expanduser().absolute()
    excluded = {
        value if value.startswith("refs/heads/") else f"refs/heads/{value}"
        for value in excluded_branches
    }
    records = _worktree_records(root) if include_local_worktrees else [
        {"worktree": str(root)}
    ]
    statuses: list[dict[str, Any]] = []
    scopes: list[dict[str, Any]] = []
    previous_findings: dict[str, dict[str, Any]] = {}
    unavailable_peers: list[dict[str, str]] = []
    unavailable_cards: list[dict[str, Any]] = []
    current_path = _normalized_path(root)

    for record in records:
        path = Path(str(record["worktree"]))
        branch = str(record.get("branch", ""))
        if branch in excluded:
            unavailable_cards.append(
                _unavailable_worktree(record, "excluded-worktree-contract-not-integrated")
            )
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(branch),
                    "reason": "excluded-worktree-contract-not-integrated",
                }
            )
            continue
        if not path.is_dir():
            unavailable_cards.append(_unavailable_worktree(record, "local-worktree-unavailable"))
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(branch),
                    "reason": "local-worktree-unavailable",
                }
            )
            continue
        try:
            status = inspect_worktree_status(path)
        except (OSError, ValueError) as error:
            unavailable_cards.append(
                _unavailable_worktree(record, f"status-unavailable:{type(error).__name__}")
            )
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(branch),
                    "reason": "local-worktree-status-unavailable",
                }
            )
            continue
        statuses.append(status)
        session = status["session"]["record"]
        if not isinstance(session, Mapping):
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(status["identity"]["branch"]),
                    "reason": "local-worktree-session-unavailable",
                }
            )
            continue
        for finding in session.get("findings", []):
            if isinstance(finding, Mapping) and finding.get("finding_id"):
                previous_findings[str(finding["finding_id"])] = dict(finding)
        try:
            scopes.append(collect_scope_observation(path, session=session))
        except (OSError, ValueError):
            unavailable_peers.append(
                {
                    "workstream_id": str(session.get("workstream_id", "unknown-workstream")),
                    "reason": "local-worktree-scope-unavailable",
                }
            )

    computed = compute_overlap_findings(scopes, unavailable_peers=unavailable_peers)
    reconciled = reconcile_overlap_findings(
        computed["findings"], list(previous_findings.values())
    )
    active_findings = reconciled["active"]
    scopes_by_worktree = {scope["worktree_id"]: scope for scope in scopes}
    findings_by_workstream: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in active_findings:
        for workstream_id in finding.get("workstream_ids", []):
            findings_by_workstream[str(workstream_id)].append(finding)

    cards: list[dict[str, Any]] = []
    for status in statuses:
        identity = status["identity"]
        session_info = status["session"]
        session = session_info["record"]
        scope = scopes_by_worktree.get(identity["worktree_id"])
        lifecycle = session_info.get("lifecycle") or {}
        workstream_id = (
            str(session.get("workstream_id"))
            if isinstance(session, Mapping)
            else _branch_label(identity["branch"])
        )
        relevant_findings = findings_by_workstream.get(workstream_id, [])
        finding_counts = Counter(str(item["kind"]) for item in relevant_findings)
        scope_paths = list(scope.get("path_entries", [])) if scope else []
        has_session = isinstance(session, Mapping)
        effective_phase = lifecycle.get("effective_phase", "unavailable")
        display_group = (
            "active"
            if has_session and effective_phase not in {"integrated", "closed"}
            else "inactive"
            if has_session
            else "worktree-only"
        )
        cards.append(
            {
                "workstream_id": workstream_id,
                "worktree_id": identity["worktree_id"],
                "worktree_path": identity["worktree_path"],
                "branch": _branch_label(identity["branch"]),
                "head": identity["head"],
                "integration_ref": identity["integration_ref"],
                "integration_oid": identity["integration_oid"],
                "merge_base": identity["merge_base"],
                "ahead": identity["ahead"],
                "behind": identity["behind"],
                "fact_scope": identity["fact_scope"],
                "dirty": identity["dirty"],
                "dirty_entry_count": identity["dirty_entry_count"],
                "untracked_count": identity["untracked_count"],
                "primary_subsystem_id": (
                    str(session.get("primary_subsystem_id", "Unknown"))
                    if isinstance(session, Mapping)
                    else "Unknown"
                ),
                "affected_subsystem_ids": (
                    list(session.get("affected_subsystem_ids", []))
                    if isinstance(session, Mapping)
                    else []
                ),
                "scope_revision": scope.get("scope_revision") if scope else None,
                "scope_path_count": len(scope_paths) if scope else None,
                "scope_paths": scope_paths,
                "lifecycle_phase": effective_phase,
                "declared_lifecycle_phase": lifecycle.get("declared_phase", "unavailable"),
                "runtime_condition": lifecycle.get("runtime_condition", "stale-unknown"),
                "evidence_freshness": lifecycle.get("evidence_freshness", "unknown"),
                "session_state": session_info["state"],
                "captured_at": (
                    str(session.get("captured_at")) if isinstance(session, Mapping) else None
                ),
                "platform_session": (
                    session.get("platform_session") if isinstance(session, Mapping) else None
                ),
                "finding_counts": dict(finding_counts),
                "findings": relevant_findings,
                "availability": "available",
                "unavailable_reason": None,
                "has_session": has_session,
                "display_group": display_group,
                "is_current": _normalized_path(Path(identity["worktree_path"])) == current_path,
                "is_primary": identity["is_primary"],
            }
        )
    cards.extend(unavailable_cards)
    cards.sort(
        key=lambda item: (
            not item.get("is_current", False),
            item.get("availability") != "available",
            str(item.get("workstream_id", "")),
        )
    )

    subsystem_workstreams: dict[str, set[str]] = defaultdict(set)
    for card in cards:
        if card.get("display_group") != "active":
            continue
        subsystem_ids = [card["primary_subsystem_id"], *card["affected_subsystem_ids"]]
        for subsystem_id in subsystem_ids:
            if subsystem_id and subsystem_id != "Unknown":
                subsystem_workstreams[str(subsystem_id)].add(card["workstream_id"])
    subsystems = [
        {"subsystem_id": subsystem_id, "workstream_ids": sorted(workstream_ids)}
        for subsystem_id, workstream_ids in sorted(subsystem_workstreams.items())
    ]

    current = next((card for card in cards if card.get("is_current")), None)
    finding_counts = Counter(str(item["kind"]) for item in active_findings)
    attention: list[dict[str, str]] = []
    for kind in ("direct", "authority", "semantic", "unknown"):
        count = finding_counts.get(kind, 0)
        if count:
            attention.append(
                {
                    "kind": kind,
                    "severity": "critical" if kind == "direct" else "warning",
                    "label": f"{kind.title()} finding × {count}",
                }
            )
    freshness_counts: Counter[str] = Counter()
    for card in cards:
        if card["availability"] != "available":
            freshness_counts["unavailable"] += 1
        elif card.get("display_group") == "active" and card["session_state"] == "stale":
            freshness_counts[str(card["session_state"])] += 1
    for state in ("stale", "unavailable"):
        count = freshness_counts[state]
        if count:
            attention.append(
                {
                    "kind": "freshness",
                    "severity": "warning" if state != "unavailable" else "unknown",
                    "label": f"Evidence {state} × {count} local worktrees / Unknown",
                }
            )
    if not attention:
        attention.append(
            {
                "kind": "remote-unknown",
                "severity": "unknown",
                "label": "No local finding; remote and unreported work remain Unknown",
            }
        )

    return {
        "projection_schema": PROJECTION_SCHEMA,
        "mode": "personal",
        "status": "ready",
        "read_only": True,
        "creates_project_facts": False,
        "writes_performed": False,
        "network_performed": False,
        "team_runtime_enabled": False,
        "captured_at": _now(captured_at),
        "project_root": str(root),
        "current": current,
        "workstreams": cards,
        "subsystems": subsystems,
        "findings": active_findings,
        "retired_findings": reconciled["retired"],
        "finding_counts": dict(finding_counts),
        "attention": attention,
        "remote_observability": {
            "status": "unknown",
            "label": "Unknown",
            "detail": "Personal Mode has no Team runtime or remote telemetry",
        },
        "w3": _w3_slots(w3_projection),
        "source_contracts": [
            "worktree-status-v1",
            "scope-observation-v1",
            "overlap-report-v1",
            "collaboration-v1",
        ],
    }


def unavailable_personal_observatory_projection(error: Exception) -> dict[str, Any]:
    return {
        "projection_schema": PROJECTION_SCHEMA,
        "mode": "personal",
        "status": "unavailable",
        "read_only": True,
        "creates_project_facts": False,
        "writes_performed": False,
        "network_performed": False,
        "team_runtime_enabled": False,
        "captured_at": _now(),
        "error": {"type": type(error).__name__, "message": str(error)},
        "workstreams": [],
        "subsystems": [],
        "findings": [],
        "attention": [],
        "remote_observability": {"status": "unknown", "label": "Unknown"},
        "w3": _w3_slots(None),
    }


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _value(value: object, suffix: str = "") -> str:
    return "Unknown" if value is None else f"{value}{suffix}"


def _status_class(value: object) -> str:
    text = str(value or "unknown").lower().replace("_", "-")
    if text in {"active", "current", "canonical", "resolved", "ready"}:
        return "ok"
    if text in {"blocked-by-conflict", "failed", "direct", "l3"}:
        return "bad"
    if text in {"unknown", "unavailable", "stale-unknown", "absent"}:
        return "unknown"
    return "warn"


def _status_token(label: str, value: object) -> str:
    return (
        '<span class="po-token %s"><span>%s</span><b>%s</b></span>'
        % (_status_class(value), _esc(label), _esc(value))
    )


def _finding_rows(findings: Sequence[Mapping[str, Any]]) -> str:
    if not findings:
        return (
            '<div class="po-empty" data-state="no-local-finding">'
            "No local finding · remote evidence remains Unknown</div>"
        )
    rows = []
    for finding in findings:
        evidence = finding.get("path_evidence") or finding.get("validation_surfaces") or []
        detail = ", ".join(str(item) for item in evidence[:3]) or str(
            finding.get("resolution_reason") or "Evidence available in Scope detail"
        )
        rows.append(
            '<div class="po-finding %s"><span class="po-finding-kind">%s</span>'
            '<span class="po-finding-detail">%s</span>'
            '<span class="po-ack">%s · %s</span></div>'
            % (
                _status_class(finding.get("kind")),
                _esc(str(finding.get("kind", "unknown")).title()),
                _esc(detail),
                _esc(finding.get("disposition", "open")),
                _esc(finding.get("acknowledgement_progress", "0/0")),
            )
        )
    return "".join(rows)


def _human_phase(value: object) -> str:
    return {
        "created": "刚建立",
        "investigating": "调研中",
        "implementing": "实现中",
        "validating": "验证中",
        "review-ready": "等待审查",
        "integrated": "已集成",
        "closed": "已关闭",
        "unavailable": "阶段未知",
    }.get(str(value), str(value))


def _human_runtime(value: object) -> str:
    return {
        "active": "正在推进",
        "waiting-for-user": "等待确认",
        "paused": "已暂停",
        "blocked-by-conflict": "被冲突阻塞",
        "failed": "执行失败",
        "offline": "Agent 离线",
        "stale-unknown": "运行状态未知",
    }.get(str(value), str(value))


def _human_freshness(value: object) -> str:
    return {
        "current": "证据最新",
        "stale": "证据已过期",
        "unknown": "证据未知",
    }.get(str(value), str(value))


def _workstream_card(card: Mapping[str, Any]) -> str:
    branch = card.get("branch", "Unknown")
    title = card.get("workstream_id", branch)
    path_rows = "".join(
        '<li><code>%s</code><span>%s</span></li>'
        % (_esc(item.get("path", "Unknown")), _esc(" · ".join(item.get("sources", []))))
        for item in card.get("scope_paths", [])
    ) or '<li class="po-muted">Scope unavailable</li>'
    agent = card.get("platform_session")
    agent_label = (
        f"{agent.get('adapter')} · {agent.get('session_id')}"
        if isinstance(agent, Mapping)
        else "Agent session Unavailable"
    )
    findings = card.get("findings", [])
    counts = card.get("finding_counts", {})
    finding_types = " · ".join(
        "%s %s" % (str(kind).title(), count)
        for kind, count in sorted(counts.items())
        if count
    ) or "No local finding"
    affected = card.get("affected_subsystem_ids", [])
    return (
        '<details class="po-workstream" data-workstream="%s" data-session-state="%s">'
        '<summary class="po-work-summary"><div class="po-work-name"><span class="po-kicker">%s</span>'
        '<h4>%s</h4><code>%s</code></div>'
        '<div class="po-work-now"><small>现在</small><b>%s</b><span>%s</span></div>'
        '<div class="po-work-scope"><small>影响范围</small><b>%s</b><span>%s affected · %s paths</span></div>'
        '<div class="po-work-signal"><small>信号</small><b>%s finding%s</b><span>%s · %s</span></div>'
        '<span class="po-open-label">查看证据</span></summary><div class="po-work-detail">'
        '<div class="po-tracks">%s%s%s</div>'
        '<div class="po-detail-grid"><div><b>Integration</b><code>%s</code></div>'
        '<div><b>Merge base</b><code>%s</code></div><div><b>HEAD</b><code>%s</code></div>'
        '<div><b>Ahead / behind</b><span>+%s / −%s</span></div><div><b>Session</b><span>%s</span></div>'
        '<div><b>Captured</b><span>%s</span></div><div class="po-detail-wide"><b>Worktree</b><code>%s</code></div>'
        '</div><div class="po-evidence-note">%s · Scope r%s · %s changes · %s untracked · %s</div>'
        '<div class="po-detail-section"><b>Findings and acknowledgement</b>%s</div>'
        '<div class="po-detail-section"><b>Scope paths and sources</b><ul class="po-paths">%s</ul></div>'
        '</div></details>'
        % (
            _esc(title),
            _esc(card.get("session_state", "unknown")),
            "CURRENT WORKSTREAM" if card.get("is_current") else "OPEN WORKSTREAM",
            _esc(title),
            _esc(branch),
            _esc(_human_phase(card.get("lifecycle_phase", "unavailable"))),
            _esc(_human_runtime(card.get("runtime_condition", "stale-unknown"))),
            _esc(card.get("primary_subsystem_id", "Unknown")),
            len(affected),
            _esc(_value(card.get("scope_path_count"))),
            len(findings),
            "" if len(findings) == 1 else "s",
            _esc(_human_freshness(card.get("evidence_freshness", "unknown"))),
            "dirty" if card.get("dirty") else "clean",
            _status_token("lifecycle", card.get("lifecycle_phase", "unavailable")),
            _status_token("runtime", card.get("runtime_condition", "stale-unknown")),
            _status_token("evidence", card.get("evidence_freshness", "unknown")),
            _esc(_short_oid(card.get("integration_oid"))),
            _esc(_short_oid(card.get("merge_base"))),
            _esc(_short_oid(card.get("head"))),
            _esc(_value(card.get("ahead"))),
            _esc(_value(card.get("behind"))),
            _esc(card.get("session_state", "unknown")),
            _esc(card.get("captured_at") or "Unknown"),
            _esc(card.get("worktree_path", "Unknown")),
            _esc(agent_label),
            _esc(_value(card.get("scope_revision"))),
            _esc(_value(card.get("dirty_entry_count"))),
            _esc(_value(card.get("untracked_count"))),
            _esc(finding_types),
            _finding_rows(findings),
            path_rows,
        )
    )


def _worktree_inventory_row(card: Mapping[str, Any]) -> str:
    group = str(card.get("display_group", "unavailable"))
    labels = {
        "inactive": "Integrated / closed session",
        "worktree-only": "No Workstream session",
        "unavailable": "Unavailable / Unknown",
    }
    title = (
        card.get("workstream_id")
        if card.get("has_session")
        else card.get("branch", "Unknown")
    )
    note = card.get("unavailable_reason") or (
        "%s · %s finding(s)"
        % (card.get("fact_scope", "Unknown"), len(card.get("findings", [])))
    )
    return (
        '<div class="po-inventory-row" data-display-group="%s">'
        '<div><b>%s</b><span>%s</span></div><code>%s</code><span>%s</span><span>%s</span>'
        '</div>'
        % (
            _esc(group),
            _esc(title),
            _esc(labels.get(group, "Observed locally")),
            _esc(card.get("branch", "Unknown")),
            _esc(card.get("lifecycle_phase", "unavailable")),
            _esc(note),
        )
    )


PERSONAL_OBSERVATORY_CSS = r"""
.po-shell{--po-cyan:#63d6cf;--po-amber:#f2ba5e;--po-red:#ff786b;--po-dim:#758097;
 margin:0 0 24px;border:1px solid var(--line);border-radius:16px;overflow:hidden;
 background:linear-gradient(180deg,rgba(127,176,255,.055),transparent 220px),var(--bg)}
.po-mast{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;padding:22px 24px 18px;
 border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(99,214,207,.07),transparent 58%)}
.po-kicker{display:block;color:var(--po-cyan);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;
 letter-spacing:.14em;text-transform:uppercase}.po-mast h2{margin:4px 0 4px;font-size:26px;letter-spacing:-.025em}
.po-mast p,.po-ws-head p{margin:0;color:var(--mut);font-size:12.5px}.po-lock{align-self:start;display:flex;
 gap:7px;align-items:center;color:var(--mut);font:600 11px/1.2 "Cascadia Code",Consolas,monospace;
 border:1px solid var(--line);padding:7px 10px;border-radius:7px}.po-lock::before{content:"●";color:var(--po-cyan)}
.po-zone{padding:20px 24px;border-bottom:1px solid var(--line)}.po-zone:last-child{border-bottom:0}
.po-zone-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:13px}
.po-zone-head h3{margin:0;font-size:15px;letter-spacing:.01em}.po-zone-head span{color:var(--mut);font-size:11.5px}
.po-project-grid{display:grid;grid-template-columns:1.2fr repeat(3,minmax(120px,.7fr));gap:1px;background:var(--line);
 border:1px solid var(--line);border-radius:11px;overflow:hidden}.po-project-cell{min-width:0;padding:13px 14px;background:var(--bg2)}
.po-project-cell small{display:block;color:var(--mut);font:700 9.5px/1.2 "Cascadia Code",Consolas,monospace;
 letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}.po-project-cell b{display:block;font-size:14px;overflow-wrap:anywhere}
.po-project-cell code{display:inline-block;margin-top:3px}.po-attention-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:12px}
.po-attention,.po-w3{border:1px solid var(--line);border-radius:11px;background:var(--bg2);padding:13px}
.po-alert{display:flex;gap:10px;align-items:center;padding:8px 2px;border-bottom:1px solid var(--line);font-size:12.5px}
.po-alert:last-child{border-bottom:0}.po-alert::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--po-amber)}
.po-alert.unknown::before{background:var(--po-dim)}.po-alert.critical::before{background:var(--po-red)}
.po-w3-row{display:grid;grid-template-columns:1fr auto;gap:9px;padding:8px 2px;border-bottom:1px solid var(--line);font-size:12px}
.po-w3-row:last-child{border-bottom:0}.po-w3-row small{grid-column:1/-1;color:var(--mut)}
.po-workstreams{display:grid;grid-template-columns:minmax(0,1fr);gap:10px}.po-workstream{min-width:0;
 border:1px solid var(--line);border-radius:12px;background:var(--bg2);padding:15px;box-shadow:inset 3px 0 0 var(--po-cyan)}
.po-workstream.unavailable{box-shadow:inset 3px 0 0 var(--po-dim)}.po-ws-head{display:flex;gap:10px;align-items:start;
 justify-content:space-between}.po-ws-head h4{margin:3px 0 1px;font-size:15px;overflow-wrap:anywhere}.po-scope{border:1px solid var(--line);
 padding:3px 8px;border-radius:5px;font:700 10px/1.4 "Cascadia Code",Consolas,monospace;text-transform:uppercase}
.po-scope.ok{color:var(--po-cyan)}.po-scope.warn{color:var(--po-amber)}.po-scope.unknown{color:var(--po-dim)}
.po-tracks{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}.po-token{display:inline-grid;grid-template-columns:auto auto;
 gap:5px;align-items:center;border:1px solid var(--line);padding:4px 7px;border-radius:6px;font:10px/1.2 "Cascadia Code",Consolas,monospace}
.po-token span{color:var(--mut)}.po-token.ok b{color:var(--po-cyan)}.po-token.warn b{color:var(--po-amber)}
.po-token.bad b{color:var(--po-red)}.po-token.unknown b{color:var(--po-dim)}.po-summary-grid{display:grid;
 grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--line);border-radius:8px;overflow:hidden}
.po-summary-grid>div{display:flex;flex-direction:column;gap:2px;min-width:0;padding:9px 11px;border-right:1px solid var(--line)}
.po-summary-grid>div:last-child{border-right:0}.po-summary-grid small{color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em}
.po-summary-grid b{font-size:12px;overflow-wrap:anywhere}.po-summary-grid span{color:var(--mut);font-size:10.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-finding{display:grid;grid-template-columns:72px minmax(0,1fr) auto;gap:8px;
 padding:7px 0;border-top:1px solid var(--line);font-size:11px}.po-finding-kind{font-weight:800;text-transform:uppercase}
.po-finding.bad .po-finding-kind{color:var(--po-red)}.po-finding.warn .po-finding-kind{color:var(--po-amber)}
.po-finding.unknown .po-finding-kind{color:var(--po-dim)}.po-finding-detail{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-ack{color:var(--mut);white-space:nowrap}.po-empty{padding:8px 0;color:var(--mut);font-size:11.5px;border-top:1px solid var(--line)}
.po-workstream details{margin-top:8px;border-top:1px solid var(--line);padding-top:8px}.po-workstream summary{cursor:pointer;
 color:var(--acc);font-size:11.5px}.po-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.po-detail-grid>div{display:flex;flex-direction:column;gap:3px;min-width:0}.po-detail-grid b{font-size:10px;color:var(--mut)}
.po-detail-wide{grid-column:1/-1}.po-detail-section{margin-top:12px}.po-detail-section>b{display:block;color:var(--mut);font-size:10px;margin-bottom:5px}
.po-paths{list-style:none;margin:10px 0 0;padding:0;max-height:180px;overflow:auto}.po-paths li{display:flex;justify-content:space-between;
 gap:12px;padding:5px 0;border-top:1px solid var(--line);font-size:10.5px}.po-paths span{color:var(--mut)}
.po-subsystems{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.po-subsystem{border-left:2px solid var(--po-cyan);
 background:var(--bg2);padding:10px 11px;min-width:0}.po-subsystem b{display:block;font-size:12px;margin-bottom:3px;overflow-wrap:anywhere}
.po-subsystem span{display:block;color:var(--mut);font-size:10.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-inventory{margin-top:12px;border:1px solid var(--line);border-radius:10px;background:var(--bg2);overflow:hidden}
.po-inventory>summary{cursor:pointer;padding:11px 13px;color:var(--acc);font-size:12px}.po-inventory-body{border-top:1px solid var(--line)}
.po-inventory-row{display:grid;grid-template-columns:minmax(180px,1.2fr) minmax(140px,1fr) 100px minmax(180px,1fr);gap:12px;
 align-items:center;padding:9px 13px;border-top:1px solid var(--line);font-size:10.5px}.po-inventory-row:first-child{border-top:0}
.po-inventory-row>div{display:flex;flex-direction:column;min-width:0}.po-inventory-row b,.po-inventory-row span,.po-inventory-row code{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.po-inventory-row>span,.po-inventory-row>div span{color:var(--mut)}
.po-muted{color:var(--mut)!important}.po-foot{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;
 color:var(--mut);font:10px/1.5 "Cascadia Code",Consolas,monospace;padding:11px 24px;background:var(--bg2)}
.po-brief{padding:28px 28px 24px;border-bottom:1px solid var(--line);background:var(--bg2)}
.po-brief-top{display:flex;justify-content:space-between;align-items:start;gap:24px}.po-brief h2{font-size:30px;line-height:1.18;
 letter-spacing:-.035em;margin:7px 0 8px;color:var(--strong)}.po-brief-top p{max-width:720px;margin:0;color:var(--fg);font-size:15px;line-height:1.7}
.po-brief-grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(260px,.65fr);gap:24px;margin-top:24px}
.po-signals{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.po-signals>div{padding:13px 14px 12px;border-right:1px solid var(--line)}.po-signals>div:last-child{border-right:0}
.po-signals b{display:block;font-size:24px;line-height:1.1;margin-bottom:5px;color:var(--strong)}.po-signals span{color:var(--mut);font-size:11px}
.po-signals .critical b{color:var(--po-red)}.po-proof{display:grid;gap:7px;border-left:1px solid var(--line);padding-left:18px}
.po-proof>div{display:flex;justify-content:space-between;gap:14px;align-items:baseline}.po-proof small{color:var(--mut);font-size:10px}
.po-proof b,.po-proof code{font-size:10.5px;text-align:right}.po-priorities{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.po-priorities li{display:grid;grid-template-columns:10px minmax(0,1fr);gap:13px;padding:13px 2px;border-bottom:1px solid var(--line)}
.po-priority-mark{width:8px;height:8px;margin-top:7px;border-radius:50%;background:var(--po-amber)}
.po-priorities li.critical .po-priority-mark{background:var(--po-red)}.po-priorities li.unknown .po-priority-mark{background:var(--po-dim)}
.po-priorities b{font-size:13.5px}.po-priorities p{margin:2px 0 0;color:var(--mut);font-size:11.5px;line-height:1.55}
.po-workstream{padding:0;box-shadow:none;border-radius:9px;background:var(--bg2)}.po-workstream[open]{border-color:color-mix(in srgb,var(--acc) 45%,var(--line))}
.po-workstream>.po-work-summary{display:grid;grid-template-columns:minmax(210px,1.35fr) minmax(130px,.75fr) minmax(150px,.9fr) minmax(140px,.8fr) auto;
 gap:14px;align-items:center;padding:13px 14px;cursor:pointer;list-style:none;color:var(--fg)}.po-work-summary::-webkit-details-marker{display:none}
.po-work-summary:hover{background:var(--bg3)}.po-work-name,.po-work-now,.po-work-scope,.po-work-signal{display:flex;flex-direction:column;min-width:0}
.po-work-name h4{font-size:13px;margin:2px 0 3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.po-work-name code{width:max-content;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-work-summary small{font-size:9px;color:var(--mut);letter-spacing:.06em;text-transform:uppercase}.po-work-summary b{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.po-work-summary div>span:not(.po-kicker){font-size:10.5px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.po-open-label{color:var(--acc);font-size:10px;white-space:nowrap}.po-workstream[open] .po-open-label{font-size:0}.po-workstream[open] .po-open-label::after{content:"收起";font-size:10px}
.po-work-detail{padding:0 14px 14px;border-top:1px solid var(--line)}.po-evidence-note{margin:10px 0;color:var(--mut);font-size:10.5px}
.po-subsystems{grid-template-columns:repeat(2,minmax(0,1fr))}.po-subsystem{display:flex;justify-content:space-between;gap:16px;align-items:center;
 border-left:0;border-bottom:1px solid var(--line);padding:10px 2px;background:transparent}.po-subsystem div{min-width:0}.po-subsystem code{max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-vault{margin:0;border-top:1px solid var(--line);background:var(--bg2)}.po-vault>summary{display:flex;justify-content:space-between;gap:20px;
 align-items:center;padding:15px 24px;cursor:pointer;list-style:none}.po-vault>summary::-webkit-details-marker{display:none}.po-vault>summary div{display:flex;flex-direction:column}
.po-vault>summary b{font-size:13px}.po-vault>summary span{color:var(--mut);font-size:10.5px}.po-vault-body{padding:0 24px 20px;border-top:1px solid var(--line)}
.po-vault-body h4{font-size:11px;margin:16px 0 7px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
@media(max-width:900px){.po-project-grid{grid-template-columns:1fr 1fr}
 .po-attention-grid{grid-template-columns:1fr}.po-subsystems{grid-template-columns:1fr 1fr}.po-brief-grid{grid-template-columns:1fr}
 .po-proof{border-left:0;border-top:1px solid var(--line);padding:12px 0 0}.po-workstream>.po-work-summary{grid-template-columns:minmax(190px,1.2fr) repeat(3,minmax(110px,.8fr))}.po-open-label{display:none}}
@media(max-width:640px){.po-shell{border-left:0;border-right:0;border-radius:0;
 margin:0 -18px 24px}
 header.top{gap:8px;padding:0 12px}header.top h1{min-width:0;overflow:hidden;text-overflow:ellipsis}
 header.top .sub,header.top .searchwrap{display:none}.rightgrp{gap:6px}
 .po-mast{grid-template-columns:1fr;padding:18px}.po-lock{justify-self:start}.po-zone{padding:17px 18px}
 .po-project-grid{grid-template-columns:1fr}.po-workstream{padding:0}.po-tracks{display:grid;grid-template-columns:1fr}
 .po-token{justify-content:space-between}.po-summary-grid{grid-template-columns:1fr}.po-summary-grid>div{border-right:0;border-top:1px solid var(--line)}
 .po-summary-grid>div:first-child{border-top:0}.po-finding{grid-template-columns:1fr auto}
 .po-finding-detail{grid-column:1/-1;white-space:normal}.po-detail-grid{grid-template-columns:1fr}.po-subsystems{grid-template-columns:1fr}
 .po-inventory-row{grid-template-columns:1fr}.po-inventory-row>span{white-space:normal}.po-inventory-row>code{width:max-content;max-width:100%}
 .po-foot{padding:11px 18px}.po-zone-head{align-items:start;flex-direction:column;gap:3px}
 .po-brief{padding:22px 18px}.po-brief-top{display:block}.po-brief h2{font-size:27px}.po-lock{margin-top:16px;width:max-content;max-width:100%}
 .po-signals{grid-template-columns:1fr 1fr}.po-signals>div:nth-child(2){border-right:0}.po-signals>div:nth-child(-n+2){border-bottom:1px solid var(--line)}
 .po-signals b{font-size:21px}.po-proof>div{align-items:start}.po-workstream>.po-work-summary{grid-template-columns:1fr 1fr;padding:13px}
 .po-work-name{grid-column:1/-1;border-bottom:1px solid var(--line);padding-bottom:10px}.po-work-signal{grid-column:1/-1}
 .po-work-detail{padding:0 13px 13px}.po-subsystems{grid-template-columns:1fr}.po-subsystem{align-items:start;flex-direction:column;gap:5px}.po-subsystem code{max-width:100%}
 .po-vault>summary{padding:14px 18px}.po-vault-body{padding:0 18px 18px}}
@media(prefers-reduced-motion:reduce){.po-shell *{scroll-behavior:auto!important;transition:none!important}}
"""


def render_personal_observatory_panel(projection: Mapping[str, Any]) -> str:
    if projection.get("status") != "ready":
        error = projection.get("error", {})
        return (
            '<article class="page wide" id="personal-observatory" data-kind="personal-observatory" '
            'data-title="Personal Observatory" data-status="unavailable" data-read-only="true">'
            '<section class="po-shell"><div class="po-brief"><span class="po-kicker">PERSONAL OBSERVATORY</span>'
            '<h2>项目态势暂不可用</h2><p>Unavailable · %s: %s</p>'
            '<span class="po-lock">READ ONLY · ZERO EXTERNAL NETWORK</span></div></section></article>'
            % (_esc(error.get("type", "Unknown")), _esc(error.get("message", "Unknown")))
        )
    current = projection.get("current") or {}
    w3_labels = {
        "review_queue": "Review queue",
        "integration_eligibility": "Integration eligibility",
        "cleanup_eligibility": "Cleanup eligibility",
    }
    w3_rows = "".join(
        '<div class="po-w3-row" data-w3-slot="%s"><b>%s</b><span class="po-scope unknown">%s</span>'
        '<small>%s</small></div>'
        % (
            _esc(key),
            _esc(w3_labels[key]),
            _esc(projection["w3"][key]["label"]),
            _esc(projection["w3"][key]["detail"]),
        )
        for key in W3_SLOT_KEYS
    )
    active_cards = [
        card for card in projection["workstreams"]
        if card.get("display_group") == "active"
    ]
    inventory_cards = [
        card for card in projection["workstreams"]
        if card.get("display_group") != "active"
    ]
    workstreams = "".join(_workstream_card(card) for card in active_cards)
    if not workstreams:
        workstreams = (
            '<div class="po-empty" data-state="no-worktree">No active Workstream · Unknown</div>'
        )
    inventory = ""
    if inventory_cards:
        inventory = (
            '<details class="po-inventory"><summary>本机可见 worktree · %d（非活动项，按需查看）</summary>'
            '<div class="po-inventory-body">%s</div></details>'
            % (
                len(inventory_cards),
                "".join(_worktree_inventory_row(card) for card in inventory_cards),
            )
        )
    subsystems = "".join(
        '<div class="po-subsystem"><div><b>%s</b><span>%d 个未结束 Workstream</span></div>'
        '<code>%s</code></div>'
        % (
            _esc(item["subsystem_id"]),
            len(item["workstream_ids"]),
            _esc(" · ".join(item["workstream_ids"])),
        )
        for item in projection["subsystems"]
    ) or '<div class="po-empty" data-state="no-subsystem">No mapped subsystem · Unknown</div>'
    finding_counts = projection.get("finding_counts", {})
    direct_count = int(finding_counts.get("direct", 0))
    authority_count = int(finding_counts.get("authority", 0))
    semantic_count = int(finding_counts.get("semantic", 0))
    unknown_count = int(finding_counts.get("unknown", 0))
    running_count = sum(
        card.get("runtime_condition") == "active" for card in active_cards
    )
    paused_count = sum(
        card.get("runtime_condition") in {"paused", "waiting-for-user"}
        for card in active_cards
    )
    blocked_count = sum(
        card.get("runtime_condition") in {"blocked-by-conflict", "failed", "offline"}
        for card in active_cards
    )
    stale_count = sum(
        card.get("evidence_freshness") != "current" for card in active_cards
    )
    focus = current if current.get("display_group") == "active" else (
        active_cards[0] if active_cards else None
    )
    if focus:
        project_summary = (
            "当前 %s 正在推进 %s，处于%s。"
            % (
                focus.get("workstream_id", "Unknown Workstream"),
                focus.get("primary_subsystem_id", "Unknown subsystem"),
                _human_phase(focus.get("lifecycle_phase", "unavailable")),
            )
        )
        if focus.get("runtime_condition") != "active":
            project_summary += " 运行状态为%s。" % _human_runtime(
                focus.get("runtime_condition", "stale-unknown")
            )
        if len(active_cards) > 1:
            project_summary += " 本机还有 %d 个未结束 Workstream。" % (
                len(active_cards) - 1
            )
    else:
        project_summary = "本机没有可确认的未结束 Workstream；远端和未上报工作仍为 Unknown。"

    priorities: list[tuple[str, str, str]] = []
    if direct_count:
        priorities.append((
            "critical",
            "%d 个确定的直接重叠需要处理" % direct_count,
            "这些是 W1/W2 已证明的路径或独占面重叠，不是推测。",
        ))
    if authority_count or semantic_count:
        priorities.append((
            "warning",
            "%d 个权威／语义交叉需要复核" % (authority_count + semantic_count),
            "共享 subsystem 不自动等于冲突，但需要人工确认意图。",
        ))
    if blocked_count or paused_count:
        priorities.append((
            "warning",
            "%d 个 Workstream 没有处于持续执行状态" % (blocked_count + paused_count),
            "%d 个阻塞／失败／离线，%d 个暂停或等待确认。" % (
                blocked_count,
                paused_count,
            ),
        ))
    if stale_count:
        priorities.append((
            "warning",
            "%d 个未结束 Workstream 的证据已过期" % stale_count,
            "页面仍展示最后一次本机观测，但不能把它当作当前事实。",
        ))
    if all(slot.get("status") == "unavailable" for slot in projection["w3"].values()):
        priorities.append((
            "unknown",
            "当前不能判断审查、集成和清理资格",
            "W3 contract 尚未进入 main；页面不会自行补造这些结论。",
        ))
    if unknown_count:
        priorities.append((
            "unknown",
            "%d 项重叠证据仍是 Unknown" % unknown_count,
            "多数来自无 session 或隔离的本机 worktree；Unknown 不等于没有冲突。",
        ))
    if not priorities:
        priorities.append((
            "unknown",
            "本机没有明确告警",
            "Personal Mode 不观察远端，因此仍不能表达为全局零风险。",
        ))
    priority_html = "".join(
        '<li class="%s"><span class="po-priority-mark"></span><div><b>%s</b><p>%s</p></div></li>'
        % (_esc(severity), _esc(title), _esc(detail))
        for severity, title, detail in priorities
    )
    return (
        '<article class="page wide" id="personal-observatory" data-kind="personal-observatory" '
        'data-title="Personal Observatory" data-status="ready" data-read-only="true">'
        '<section class="po-shell" data-mode="personal" data-network-performed="false">'
        '<section class="po-brief" data-zone="project-status"><div class="po-brief-top">'
        '<div><span class="po-kicker">PERSONAL OBSERVATORY · LOCAL BRIEF</span>'
        '<h2>项目现在怎么样</h2><p>%s</p></div>'
        '<span class="po-lock">READ ONLY · ZERO EXTERNAL NETWORK</span></div>'
        '<div class="po-brief-grid"><div class="po-signals">'
        '<div><b>%d</b><span>未结束 Workstream</span></div><div><b>%d</b><span>正在推进</span></div>'
        '<div><b>%d</b><span>暂停／阻塞</span></div><div class="%s"><b>%d</b><span>确定直接重叠</span></div>'
        '</div><aside class="po-proof"><div><small>本机范围</small><b>%d worktrees</b></div>'
        '<div><small>趋势</small><b>Unknown · 无历史快照</b></div><div><small>交付资格</small><b>Unavailable · W3 未集成</b></div>'
        '<div><small>采集时间</small><code>%s</code></div></aside></div></section>'
        '<section class="po-zone" data-zone="attention"><div class="po-zone-head"><h3>先看这些</h3>'
        '<span>确定事实优先；Unknown 单独保留</span></div><ol class="po-priorities">%s</ol></section>'
        '<section class="po-zone" data-zone="workstreams"><div class="po-zone-head"><h3>谁在推进什么</h3>'
        '<span>未 integrated / closed；点击行查看审计证据</span></div>'
        '<div class="po-workstreams">%s</div></section>'
        '<section class="po-zone" data-zone="subsystems"><div class="po-zone-head"><h3>影响到哪里</h3>'
        '<span>来自 Workstream 声明的 primary + affected subsystem</span></div><div class="po-subsystems">%s</div></section>'
        '<details class="po-vault"><summary><div><b>技术证据</b><span>Git、W3 display slots 与本机 worktree inventory</span></div>'
        '<span>按需展开</span></summary><div class="po-vault-body"><section><h4>W3 display slots</h4><div class="po-w3">%s</div></section>%s</div></details>'
        '<div class="po-foot"><span>captured %s</span><span>%s · writes false · network false · Team false</span></div>'
        '</section></article>'
        % (
            _esc(project_summary),
            len(active_cards),
            running_count,
            paused_count + blocked_count,
            "critical" if direct_count else "",
            direct_count,
            len(projection["workstreams"]),
            _esc(projection["captured_at"]),
            priority_html,
            workstreams,
            subsystems,
            w3_rows,
            inventory,
            _esc(projection["captured_at"]),
            _esc(projection["projection_schema"]),
        )
    )


def inject_personal_observatory(page: str, projection: Mapping[str, Any]) -> str:
    nav_marker = (
        '<a class="nav-item" data-target="trends"><span class="dot proposed"></span>'
        '<span class="lbl">🔭 路线与趋势</span></a>'
    )
    content_marker = '</main><aside class="toc" id="toc">'
    if nav_marker not in page:
        raise ValueError("Observatory navigation marker not found")
    if content_marker not in page:
        raise ValueError("Observatory content marker not found")
    if "</style>" not in page:
        raise ValueError("document style marker not found")
    result = page.replace("</style>", PERSONAL_OBSERVATORY_CSS + "</style>", 1)
    nav_item = (
        '<a class="nav-item" data-target="personal-observatory">'
        '<span class="dot state"></span><span class="lbl">Personal Observatory</span></a>'
    )
    result = result.replace(nav_marker, nav_marker + nav_item, 1)
    return result.replace(
        content_marker,
        render_personal_observatory_panel(projection) + content_marker,
        1,
    )


def write_projection_json(path: Path, projection: Mapping[str, Any]) -> None:
    """Write an explicitly requested disposable snapshot outside authority docs."""

    target = Path(os.path.abspath(os.fspath(path.expanduser())))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
