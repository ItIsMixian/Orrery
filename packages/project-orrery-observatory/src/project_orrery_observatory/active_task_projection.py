"""Lightweight Git-private active-task projection for Personal Mode.

The startup path is deliberately narrow: one Git worktree-registry read,
bounded Git-private session JSON reads, and one existing Maintenance cache
snapshot.  It never opens worktree source files, Scope observations, findings,
or diffs.  Target-scoped Git evidence is collected only by the detail API.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


PROJECTION_CONTRACT = "orrery-active-task-projection-v1"
SESSION_LIMIT = 512 * 1024
WORKTREE_LIMIT = 256
FINISHED_PHASES = {"integrated", "closed", "superseded"}


def _normalized(value: object) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(value))))


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "Git worktree registry is unavailable")
    return completed.stdout


def _parse_worktree_porcelain(value: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in value.splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, data = line.partition(" ")
        current[key] = data if data else True
    if len(records) > WORKTREE_LIMIT:
        raise ValueError("Git worktree registry exceeds the bounded task projection limit")
    return records


def discover_worktree_registry(project_root: Path) -> dict[str, Any]:
    """Resolve registry records and private session paths without opening worktrees."""

    root = Path(project_root).resolve()
    records = _parse_worktree_porcelain(_git(root, "worktree", "list", "--porcelain"))
    common_value = _git(root, "rev-parse", "--git-common-dir").strip()
    common = Path(common_value)
    if not common.is_absolute():
        common = root / common
    common = common.resolve()
    primary_path = _normalized(records[0]["worktree"]) if records else _normalized(root)
    admin_by_path: dict[str, Path] = {}
    linked_root = common / "worktrees"
    if linked_root.is_dir():
        for admin in list(linked_root.iterdir())[:WORKTREE_LIMIT]:
            marker = admin / "gitdir"
            try:
                if marker.is_symlink() or marker.stat().st_size > 16 * 1024:
                    continue
                git_file = Path(marker.read_text(encoding="utf-8").strip())
                worktree = git_file.parent if git_file.name == ".git" else git_file
                admin_by_path[_normalized(worktree)] = admin.resolve()
            except (OSError, UnicodeError):
                continue
    enriched: list[dict[str, Any]] = []
    for item in records:
        path_key = _normalized(item["worktree"])
        is_primary = path_key == primary_path
        git_dir = common if is_primary else admin_by_path.get(path_key)
        enriched.append({
            **item,
            "is_primary": is_primary,
            "worktree_exists": Path(str(item["worktree"])).is_dir(),
            "session_path": str(git_dir / "orrery" / "worktree.json") if git_dir else None,
        })
    return {"common_dir": common, "records": enriched, "registry_calls": 2}


def _bounded_session(path_value: object, common_dir: Path) -> tuple[dict[str, Any] | None, str, int]:
    if not path_value:
        return None, "missing", 0
    path = Path(str(path_value))
    try:
        resolved = path.resolve()
        resolved.relative_to(common_dir.resolve())
        if path.is_symlink() or not path.is_file():
            return None, "missing", 0
        size = path.stat().st_size
        if size > SESSION_LIMIT:
            return None, "broken", 0
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return None, "broken", 0
    if not isinstance(value, dict) or value.get("contract_type") != "workstream-session":
        return None, "broken", size
    return value, "available", size


def _maintenance_entries(snapshot: Mapping[str, Any] | None) -> tuple[dict[str, Mapping[str, Any]], str]:
    cache = snapshot.get("cache", {}) if isinstance(snapshot, Mapping) else {}
    summary = cache.get("summary", {}) if isinstance(cache, Mapping) else {}
    entries = summary.get("entries", []) if isinstance(summary, Mapping) else []
    by_path = {
        _normalized(item["registered_path"]): item
        for item in entries
        if isinstance(item, Mapping) and item.get("registered_path")
    }
    state = str(cache.get("summary_state") or cache.get("status") or "unknown")
    return by_path, state


def _task_identity(session: Mapping[str, Any] | None, record: Mapping[str, Any]) -> tuple[str, str, str]:
    branch = str(record.get("branch", "")).removeprefix("refs/heads/") or "detached-worktree"
    workstream = str(session.get("workstream_id")) if session and session.get("workstream_id") else branch
    code, separator, name = workstream.partition("-")
    display_name = name.replace("-", " ") if separator else workstream.replace("-", " ")
    return workstream, code, display_name


def _default_maintenance_loader(root: Path) -> Mapping[str, Any]:
    from project_orrery_core.maintenance import maintenance_status

    return maintenance_status(root)


def build_active_task_projection(
    project_root: Path,
    *,
    registry_provider: Callable[[Path], Mapping[str, Any]] = discover_worktree_registry,
    maintenance_loader: Callable[[Path], Mapping[str, Any]] = _default_maintenance_loader,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Build the bounded startup/status projection used by Unified Personal Mode."""

    started = time.perf_counter()
    root = Path(project_root).resolve()
    registry = registry_provider(root)
    common = Path(registry["common_dir"]).resolve()
    try:
        maintenance = maintenance_loader(root)
        maintenance_error = None
    except Exception as error:  # cache failure remains Unknown; task identity survives
        maintenance = {}
        maintenance_error = type(error).__name__
    cache_by_path, cache_summary_state = _maintenance_entries(maintenance)
    tasks: list[dict[str, Any]] = []
    session_reads = 0
    session_bytes = 0
    revision_parts: list[str] = []
    for index, record in enumerate(registry.get("records", [])):
        session, session_status, byte_count = _bounded_session(record.get("session_path"), common)
        session_reads += 1
        session_bytes += byte_count
        workstream_id, task_code, display_name = _task_identity(session, record)
        branch = str(record.get("branch", "")).removeprefix("refs/heads/") or "detached"
        maintenance_entry = cache_by_path.get(_normalized(record.get("worktree", "")), {})
        phase = str(session.get("lifecycle_phase", "unknown")) if session else "unknown"
        runtime = str(session.get("runtime_condition", "unknown")) if session else "unknown"
        declared_freshness = str(session.get("evidence_freshness", "unknown")) if session else "unknown"
        session_matches_registry = bool(
            session
            and str(session.get("head")) == str(record.get("HEAD"))
            and str(session.get("branch", "")) == str(record.get("branch", ""))
        )
        cache_state = str(maintenance_entry.get("cache_state", cache_summary_state))
        evidence_freshness = (
            "current"
            if session_status == "available" and session_matches_registry and cache_state == "current"
            and declared_freshness == "current"
            else "refresh-needed"
        )
        category = "primary" if record.get("is_primary") else (
            "history" if phase in FINISHED_PHASES else "current"
        )
        tasks.append({
            "task_id": hashlib.sha256((str(record.get("worktree")) + "\0" + workstream_id).encode()).hexdigest()[:20],
            "workstream_id": workstream_id,
            "task_code": task_code,
            "display_name": display_name,
            "branch": branch,
            "head": str(record.get("HEAD", "Unknown"))[:12],
            "phase": phase,
            "runtime_condition": runtime,
            "primary_subsystem_id": str(session.get("primary_subsystem_id", "Unknown")) if session else "Unknown",
            "affected_subsystem_ids": list(session.get("affected_subsystem_ids", [])) if session else [],
            "evidence_freshness": evidence_freshness,
            "session_status": session_status,
            "session_revision": int(session.get("lifecycle_revision", session.get("scope_revision", 0))) if session else 0,
            "captured_at": str(session.get("captured_at")) if session and session.get("captured_at") else None,
            "category": category,
            "is_primary": bool(record.get("is_primary")),
            "worktree_presence": "present" if record.get("worktree_exists") else "missing",
            "workspace_state": str(maintenance_entry.get("classification", "unknown")),
            "cache_state": cache_state,
            "cache_scanned_at": maintenance_entry.get("scanned_at"),
            "technical_detail_available": bool(record.get("worktree_exists") and session_status == "available"),
            "_registry_index": index,
        })
        revision_parts.append("|".join((branch, str(record.get("HEAD")), workstream_id, str(session and session.get("captured_at")), cache_state)))
    tasks.sort(key=lambda item: (
        {"current": 0, "history": 1, "primary": 2}.get(str(item["category"]), 3),
        item["runtime_condition"] != "active",
        item["workstream_id"],
    ))
    for item in tasks:
        item.pop("_registry_index", None)
    current_count = sum(item["category"] == "current" for item in tasks)
    history_count = sum(item["category"] == "history" for item in tasks)
    return {
        "schema_version": 1,
        "contract_type": PROJECTION_CONTRACT,
        "status": "ready",
        "mode": "personal",
        "network_performed": False,
        "writes_performed": False,
        "captured_at": captured_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "revision": hashlib.sha256("\n".join(revision_parts).encode()).hexdigest(),
        "counts": {
            "registry_worktrees": len(tasks),
            "current": current_count,
            "history": history_count,
            "primary": sum(item["category"] == "primary" for item in tasks),
            "refresh_needed": sum(item["evidence_freshness"] != "current" for item in tasks),
        },
        "tasks": tasks,
        "maintenance": dict(maintenance),
        "cache_summary_state": cache_summary_state,
        "maintenance_error": maintenance_error,
        "read_boundary": {
            "registry_calls": int(registry.get("registry_calls", 0)),
            "session_files_attempted": session_reads,
            "session_bytes_read": session_bytes,
            "maintenance_cache_snapshots": 1,
            "worktree_source_files_read": 0,
            "scope_observations": 0,
            "diff_reads": 0,
            "startup_full_scan": False,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        },
    }


def collect_active_task_detail(
    project_root: Path,
    task_id: str,
    *,
    registry_provider: Callable[[Path], Mapping[str, Any]] = discover_worktree_registry,
    status_provider: Callable[[Path], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Collect target-only Git evidence after an explicit technical-detail request."""

    root = Path(project_root).resolve()
    registry = registry_provider(root)
    common = Path(registry["common_dir"]).resolve()
    target: Mapping[str, Any] | None = None
    target_session: Mapping[str, Any] | None = None
    for record in registry.get("records", []):
        session, _, _ = _bounded_session(record.get("session_path"), common)
        workstream_id, _, _ = _task_identity(session, record)
        candidate_id = hashlib.sha256((str(record.get("worktree")) + "\0" + workstream_id).encode()).hexdigest()[:20]
        if candidate_id == task_id:
            target, target_session = record, session
            break
    if target is None:
        raise ValueError("task is not present in the current Git worktree registry")
    if not target.get("worktree_exists"):
        return {"status": "unavailable", "reason": "worktree-missing", "task_id": task_id}
    if status_provider is None:
        from project_orrery_core.collaboration import inspect_worktree_status

        status_provider = inspect_worktree_status
    status = status_provider(Path(str(target["worktree"])))
    identity = status.get("identity", {})
    return {
        "status": "available",
        "task_id": task_id,
        "workstream_id": (target_session or {}).get("workstream_id"),
        "branch": str(identity.get("branch", target.get("branch", "Unknown"))).removeprefix("refs/heads/"),
        "head": str(identity.get("head", target.get("HEAD", "Unknown")))[:12],
        "ahead": identity.get("ahead"),
        "behind": identity.get("behind"),
        "dirty": identity.get("dirty"),
        "dirty_entry_count": identity.get("dirty_entry_count"),
        "untracked_count": identity.get("untracked_count"),
        "session_state": (status.get("session") or {}).get("state", "unknown"),
        "path_exposed": False,
        "source_content_read": False,
        "target_only": True,
    }


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


PHASE_LABELS = {
    "implementing": "实现中", "validating": "验证中", "review-ready": "待审查",
    "integrated": "已集成", "closed": "已关闭", "superseded": "已被接续",
    "unknown": "阶段待确认",
}
RUNTIME_LABELS = {
    "active": "正在推进", "waiting-for-user": "等待确认", "paused": "已暂停",
    "blocked-by-conflict": "冲突阻塞", "failed": "执行失败", "offline": "离线",
    "unknown": "运行状态待刷新", "stale-unknown": "运行状态待刷新",
}


def render_task_fragment(projection: Mapping[str, Any]) -> str:
    def task_row(item: Mapping[str, Any]) -> str:
        modules = [item.get("primary_subsystem_id", "Unknown"), *item.get("affected_subsystem_ids", [])]
        detail = (
            '<details class="at-detail" data-task-detail="%s"><summary>技术详情</summary>'
            '<div data-task-detail-body>展开后按需读取目标 Git 证据；不会读取源码正文。</div></details>'
            % _esc(item.get("task_id"))
            if item.get("technical_detail_available") else
            '<span class="at-detail-unavailable">技术详情暂不可用</span>'
        )
        return (
            '<article class="at-row" data-task-id="%s" data-task-category="%s">'
            '<div class="at-identity"><span class="at-code">%s</span><div><b>%s</b><small>%s</small></div></div>'
            '<div class="at-cell"><small>阶段</small><b>%s</b><span>%s</span></div>'
            '<div class="at-cell"><small>主要模块</small><b>%s</b><span>%s</span></div>'
            '<div class="at-cell"><small>证据</small><b class="%s">%s</b><span>%s</span></div>%s</article>'
            % (
                _esc(item.get("task_id")), _esc(item.get("category")),
                _esc(item.get("task_code")), _esc(item.get("display_name")), _esc(item.get("branch")),
                _esc(PHASE_LABELS.get(str(item.get("phase")), item.get("phase"))),
                _esc(RUNTIME_LABELS.get(str(item.get("runtime_condition")), item.get("runtime_condition"))),
                _esc(item.get("primary_subsystem_id", "Unknown")),
                _esc(" + ".join(str(value) for value in modules[1:]) or "无关联模块"),
                "current" if item.get("evidence_freshness") == "current" else "refresh",
                "证据最新" if item.get("evidence_freshness") == "current" else "状态待刷新",
                _esc(item.get("workspace_state", "Unknown")), detail,
            )
        )

    current = [item for item in projection.get("tasks", []) if item.get("category") == "current"]
    history = [item for item in projection.get("tasks", []) if item.get("category") == "history"]
    primary = [item for item in projection.get("tasks", []) if item.get("category") == "primary"]
    current_html = "".join(task_row(item) for item in current) or '<p class="at-empty">当前没有已登记、未结束的本机任务；远端与未上报任务仍为 Unknown。</p>'
    history_html = "".join(task_row(item) for item in history + primary)
    history_panel = (
        '<details class="at-history"><summary>历史与受保护工作区 · %d</summary><div>%s</div></details>'
        % (len(history) + len(primary), history_html)
        if history_html else ""
    )
    return current_html + history_panel


def render_active_task_panel(projection: Mapping[str, Any], *, dynamic: bool) -> str:
    counts = projection.get("counts", {})
    refresh = (
        '<button class="at-refresh" type="button" data-active-task-refresh>刷新任务状态</button>'
        if dynamic else '<span class="at-static">静态快照</span>'
    )
    return (
        '<article class="page wide" id="personal-observatory" data-kind="active-task-projection" '
        'data-title="个人工作台" data-status="ready" data-read-only="true">'
        '<section class="at-shell" data-active-task-projection data-endpoint="/api/v1/personal/tasks">'
        '<header class="at-head"><div><span class="at-kicker">PERSONAL / LOCAL EVIDENCE</span>'
        '<h2>谁在推进什么</h2><p>来自 Git worktree registry、Git-private 任务登记与 Maintenance cache；不读取对话或源码正文。</p></div>%s</header>'
        '<div class="at-stats"><div><b>%s</b><span>当前任务</span></div><div><b>%s</b><span>历史任务</span></div>'
        '<div><b>%s</b><span>状态待刷新</span></div><div><b>%s</b><span>Registry 工作区</span></div></div>'
        '<div class="at-list-head"><span>任务</span><span>阶段与运行</span><span>影响范围</span><span>证据新鲜度</span></div>'
        '<div class="at-list" data-active-task-list>%s</div>'
        '<footer><span data-active-task-status aria-live="polite">采集于 %s</span>'
        '<span>Personal zero-network · 主工作区受保护 · Unknown 不推断</span></footer></section></article>'
        % (
            refresh, _esc(counts.get("current", 0)), _esc(counts.get("history", 0)),
            _esc(counts.get("refresh_needed", 0)), _esc(counts.get("registry_worktrees", 0)),
            render_task_fragment(projection), _esc(projection.get("captured_at", "Unknown")),
        )
    )


ACTIVE_TASK_CSS = r"""
.at-shell{background:var(--bg2);border:1px solid var(--line);border-radius:13px;overflow:hidden;box-shadow:0 18px 45px rgba(0,0,0,.13)}
.at-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;padding:22px 24px;border-bottom:1px solid var(--line)}.at-head h2{margin:4px 0 5px;font-size:24px}.at-head p{margin:0;color:var(--mut);font-size:12px;max-width:720px}.at-kicker{color:var(--acc);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;letter-spacing:.13em}.at-refresh{border:1px solid var(--line);border-radius:8px;background:var(--bg3);color:var(--fg);padding:9px 12px;font:700 11px/1.2 inherit;cursor:pointer}.at-refresh:hover,.at-refresh:focus-visible{border-color:var(--acc);color:var(--acc);outline:none}.at-refresh[disabled]{opacity:.55;cursor:wait}.at-static{color:var(--mut);font-size:11px}
.at-stats{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--line)}.at-stats>div{padding:13px 18px;border-right:1px solid var(--line)}.at-stats>div:last-child{border-right:0}.at-stats b{display:block;font:700 20px/1.2 "Cascadia Code",Consolas,monospace}.at-stats span{color:var(--mut);font-size:10px}.at-list-head,.at-row{display:grid;grid-template-columns:minmax(230px,1.45fr) minmax(145px,.8fr) minmax(175px,1fr) minmax(135px,.72fr);gap:14px;align-items:center}.at-list-head{padding:9px 24px;color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.09em;text-transform:uppercase;border-bottom:1px solid var(--line)}.at-row{padding:14px 24px;border-bottom:1px solid var(--line);position:relative}.at-row:last-child{border-bottom:0}.at-identity{display:flex;gap:11px;align-items:center;min-width:0}.at-code{display:grid;place-items:center;min-width:47px;height:29px;border:1px solid var(--line);border-radius:5px;color:var(--acc);font:700 10px/1 "Cascadia Code",Consolas,monospace}.at-identity div,.at-cell{min-width:0}.at-identity b,.at-cell b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}.at-identity small,.at-cell small,.at-cell span{display:block;color:var(--mut);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:9.5px}.at-cell b.refresh{color:var(--warn)}.at-cell b.current{color:var(--accepted)}.at-detail{grid-column:1/-1;margin:0}.at-detail summary{cursor:pointer;color:var(--mut);font-size:10px;width:max-content}.at-detail>div{margin-top:9px;padding:10px 12px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--mut);font:11px/1.6 "Cascadia Code",Consolas,monospace}.at-detail-unavailable{grid-column:1/-1;color:var(--mut);font-size:10px}.at-history{border-top:1px solid var(--line)}.at-history>summary{padding:12px 24px;cursor:pointer;color:var(--mut);font-size:11px}.at-empty{margin:0;padding:26px 24px;color:var(--mut);font-size:12px}.at-shell footer{display:flex;justify-content:space-between;gap:12px;padding:11px 24px;color:var(--mut);font-size:9.5px;border-top:1px solid var(--line)}
@media(max-width:980px){.at-list-head{display:none}.at-row{grid-template-columns:1.2fr 1fr}.at-stats{grid-template-columns:1fr 1fr}.at-stats>div:nth-child(2){border-right:0}.at-stats>div:nth-child(-n+2){border-bottom:1px solid var(--line)}}
@media(max-width:560px){.at-head{padding:18px;flex-direction:column}.at-refresh{width:100%}.at-row{grid-template-columns:1fr;padding:14px 18px;gap:10px}.at-stats>div{padding:11px 14px}.at-shell footer{padding:10px 18px;flex-direction:column}.at-identity b,.at-cell b{white-space:normal}.at-cell span{white-space:normal}}
@media(prefers-reduced-motion:reduce){.at-shell *{scroll-behavior:auto!important;transition:none!important}}
"""


ACTIVE_TASK_JS = r"""
(function(){
 const shell=document.querySelector('[data-active-task-projection]');if(!shell)return;
 const list=shell.querySelector('[data-active-task-list]'),status=shell.querySelector('[data-active-task-status]'),button=shell.querySelector('[data-active-task-refresh]');
 async function loadDetail(details){if(details.dataset.loaded==='true')return;const body=details.querySelector('[data-task-detail-body]');body.textContent='正在读取目标 Git 证据…';try{const response=await fetch('/api/v1/personal/tasks/'+encodeURIComponent(details.dataset.taskDetail));if(!response.ok)throw new Error('request failed');const value=await response.json();body.textContent=value.status==='available'?('HEAD '+value.head+' · +'+value.ahead+' / −'+value.behind+' · '+(value.dirty?'有未提交改动':'工作区干净')+' · session '+value.session_state):'技术证据暂不可用：'+value.reason;details.dataset.loaded='true'}catch(error){body.textContent='技术证据读取失败；状态保持 Unknown。'}}
 function bindDetails(){list.querySelectorAll('[data-task-detail]').forEach(item=>item.addEventListener('toggle',()=>{if(item.open)loadDetail(item)},{once:false}))}
 if(button)button.addEventListener('click',async()=>{button.disabled=true;status.textContent='正在刷新 Git-private 任务状态…';try{const response=await fetch(shell.dataset.endpoint,{headers:{'Accept':'application/json'}});if(!response.ok)throw new Error('request failed');const value=await response.json();list.innerHTML=value.fragment;status.textContent='已刷新 · '+value.projection.captured_at;bindDetails()}catch(error){status.textContent='刷新失败；现有任务身份保留，状态待刷新。'}finally{button.disabled=false}});
 bindDetails();
})();
"""


__all__ = [
    "ACTIVE_TASK_CSS", "ACTIVE_TASK_JS", "PROJECTION_CONTRACT",
    "build_active_task_projection", "collect_active_task_detail",
    "discover_worktree_registry", "render_active_task_panel", "render_task_fragment",
]
