"""Versioned registration and presentation shell for the root-only Observatory.

The shell owns composition metadata, navigation, and failure isolation.  It
does not parse project facts or implement consumer domain actions.
"""
from __future__ import annotations

import html
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from typing import Any

from .display_vocabulary import (
    NAVIGATION_LABELS,
    TECHNICAL_DETAILS_LABEL,
    display_status,
)


SHELL_CONTRACT = "unified-observatory-shell-v1"
REGISTRATION_CONTRACT = "unified-observatory-consumer-registration-v1"
SHELL_API_VERSION = 1

PRIVILEGE_CAPABILITIES = {
    "read-only": {
        "read-docs", "search-docs", "read-status", "read-graph", "read-derived-view",
    },
    "provider-opt-in": {
        "read-derived-view", "configure-provider", "ask-provider", "refresh-derived-view",
    },
    "team-opt-in-request-only": {
        "read-status", "enable-team", "manage-local-transport", "send-request",
        "decide-request", "share-metadata",
    },
    "host-local-action-specific": {
        "read-status", "background-refresh", "target-preflight", "local-remove-worktree",
    },
}


class RegistrationError(ValueError):
    """Raised when shell integrity or a privilege boundary is invalid."""


@dataclass(frozen=True)
class ConsumerRegistration:
    consumer_id: str
    consumer_version: str
    shell_api_versions: tuple[int, ...]
    navigation_identity: str
    navigation_label: str
    navigation_order: int
    route_prefix: str | None
    capabilities: tuple[str, ...]
    transport: str
    network: str
    privilege: str
    authority: str
    static_fallback: str
    failure_policy: str
    source_contract_id: str
    source_contract_version: str
    required: bool = False
    status: str = "available"
    reason: str | None = None

    def public_descriptor(self) -> dict[str, Any]:
        value = asdict(self)
        value["registration_contract"] = REGISTRATION_CONTRACT
        value["navigation"] = {
            "identity": value.pop("navigation_identity"),
            "label": value.pop("navigation_label"),
            "order": value.pop("navigation_order"),
        }
        value["mode_requirements"] = {
            "transport": value.pop("transport"),
            "network": value.pop("network"),
        }
        value["source_contract"] = {
            "id": value.pop("source_contract_id"),
            "version": value.pop("source_contract_version"),
        }
        value["shell_api_versions"] = list(value["shell_api_versions"])
        value["capabilities"] = list(value["capabilities"])
        return value


def _validate_registration(item: ConsumerRegistration) -> None:
    if not item.consumer_id or not item.navigation_identity:
        raise RegistrationError("consumer and navigation identities are required")
    if SHELL_API_VERSION not in item.shell_api_versions:
        raise RegistrationError(f"{item.consumer_id} does not support shell API v1")
    if item.route_prefix is not None and not item.route_prefix.startswith("/api/v1/"):
        raise RegistrationError(f"{item.consumer_id} route must stay under /api/v1")
    if item.privilege not in PRIVILEGE_CAPABILITIES:
        raise RegistrationError(f"{item.consumer_id} declares an unknown privilege class")
    excess = set(item.capabilities) - PRIVILEGE_CAPABILITIES[item.privilege]
    if excess:
        raise RegistrationError(
            f"{item.consumer_id} privilege escalation: {', '.join(sorted(excess))}"
        )
    if item.static_fallback not in {"read-only", "read-only-unavailable"}:
        raise RegistrationError(f"{item.consumer_id} has an unsafe static fallback")
    if item.failure_policy not in {"fail-shell", "quarantine-consumer"}:
        raise RegistrationError(f"{item.consumer_id} has an unknown failure policy")
    if item.required and item.failure_policy != "fail-shell":
        raise RegistrationError(f"required consumer {item.consumer_id} must fail the shell")
    if not item.source_contract_id or not item.source_contract_version:
        raise RegistrationError(f"{item.consumer_id} must declare its source contract")


def validate_registrations(
    registrations: Iterable[ConsumerRegistration],
) -> tuple[ConsumerRegistration, ...]:
    items = tuple(registrations)
    consumer_ids: set[str] = set()
    navigation_ids: set[str] = set()
    route_prefixes: list[tuple[str, str]] = []
    for item in items:
        _validate_registration(item)
        if item.consumer_id in consumer_ids:
            raise RegistrationError(f"duplicate consumer id: {item.consumer_id}")
        if item.navigation_identity in navigation_ids:
            raise RegistrationError(f"duplicate navigation identity: {item.navigation_identity}")
        consumer_ids.add(item.consumer_id)
        navigation_ids.add(item.navigation_identity)
        if item.route_prefix:
            normalized = item.route_prefix.rstrip("/")
            for other_id, other in route_prefixes:
                if normalized == other or normalized.startswith(other + "/") or other.startswith(normalized + "/"):
                    raise RegistrationError(
                        f"route collision: {item.consumer_id} and {other_id}"
                    )
            route_prefixes.append((item.consumer_id, normalized))
    return tuple(sorted(items, key=lambda item: item.navigation_order))


def quarantine(
    registration: ConsumerRegistration, error: BaseException
) -> ConsumerRegistration:
    if registration.required or registration.failure_policy == "fail-shell":
        raise RegistrationError(
            f"required consumer {registration.consumer_id} failed"
        ) from error
    reason = f"{type(error).__name__}: {str(error)[:240]}"
    return replace(registration, status="unavailable", reason=reason)


def capability_document(
    registrations: Sequence[ConsumerRegistration], *, mode: str
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "contract_type": SHELL_CONTRACT,
        "shell_api_version": SHELL_API_VERSION,
        "mode": mode,
        "single_visible_url": mode == "dynamic",
        "writes_author_documents": False,
        "consumers": [item.public_descriptor() for item in registrations],
    }


SHELL_CSS = r"""
.uo-topline{display:flex;align-items:center;gap:8px;color:var(--mut);font:700 10px/1.2 "Cascadia Code",Consolas,monospace}
.uo-live{width:7px;height:7px;border-radius:50%;background:var(--accepted)}.uo-live.static{background:var(--deferred)}
.uo-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(260px,.7fr);gap:14px;margin-top:18px}
.uo-panel{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:16px;min-width:0}
.uo-panel h2,.uo-panel h3{margin:0 0 8px;color:var(--strong)}.uo-panel h2{font-size:19px}.uo-panel h3{font-size:13px}
.uo-panel p{margin:0;color:var(--mut);font-size:13px}.uo-caps{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:9px;overflow:hidden;margin-top:15px}
.uo-cap{background:var(--bg);padding:11px 12px;min-width:0}.uo-cap b{display:block;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.uo-cap small{display:block;color:var(--mut);font-size:10px;margin-top:3px}.uo-cap.unavailable b{color:var(--warn)}
.uo-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}.uo-button{border:1px solid var(--line);border-radius:7px;background:var(--bg3);color:var(--fg);padding:8px 11px;font:700 11px/1.2 inherit;cursor:pointer}.uo-button:hover{border-color:var(--acc);color:var(--acc)}.uo-button.danger{color:var(--warn)}
.uo-stop-global{white-space:nowrap;color:var(--warn)}.uo-disconnected{position:fixed;z-index:400;left:50%;top:calc(var(--hh) + 16px);transform:translateX(-50%);width:min(680px,calc(100vw - 24px));padding:13px 16px;border:1px solid var(--warn);border-radius:10px;background:var(--bg2);box-shadow:0 18px 55px rgba(0,0,0,.45);color:var(--fg);font-size:12px}.uo-disconnected b{display:block;margin-bottom:3px}.uo-disconnected span{color:var(--mut)}
.uo-boundary{list-style:none;margin:0;padding:0}.uo-boundary li{padding:9px 0;border-bottom:1px solid var(--line);font-size:11.5px}.uo-boundary li:last-child{border-bottom:0}.uo-boundary b{display:block}.uo-boundary span{color:var(--mut)}
.uo-authority dl{display:grid;grid-template-columns:140px 1fr;gap:7px 12px;margin:14px 0}.uo-authority dt{color:var(--mut);font-size:11px}.uo-authority dd{margin:0;font:12px/1.5 "Cascadia Code",Consolas,monospace;overflow-wrap:anywhere}
.uo-unavailable{border-left:3px solid var(--warn)}
.uo-mobile-toggle{display:none}.uo-backdrop{display:none}
@media(max-width:820px){
 .uo-mobile-toggle{display:inline-grid;place-items:center}.sidebar{display:none!important}.sidebar-resizer{display:none!important}
 body.uo-nav-open{overflow:hidden}body.uo-nav-open .sidebar{display:block!important;position:fixed;z-index:180;left:0;top:var(--hh);bottom:0;width:min(330px,88vw);height:auto;box-shadow:20px 0 50px rgba(0,0,0,.45)}
 body.uo-nav-open .uo-backdrop{display:block;position:fixed;z-index:170;inset:var(--hh) 0 0;background:rgba(0,0,0,.55)}
 .content{padding:0 18px}.uo-grid{grid-template-columns:1fr}.uo-caps{grid-template-columns:1fr}.top .sub{display:none}#q{width:min(42vw,190px)}
}
@media(max-width:460px){header.top{gap:6px;padding:0 8px}.top h1{max-width:82px;overflow:hidden;text-overflow:ellipsis}.rightgrp{gap:5px}.tbtn{padding:6px 7px}#q{display:none}.uo-stop-global{font-size:10px}.uo-authority dl{grid-template-columns:1fr}.page{padding-top:20px}}
@media(prefers-reduced-motion:reduce){.uo-panel *{transition:none!important;scroll-behavior:auto!important}}
"""


SHELL_JS = r"""
(function(){
 const toggle=document.querySelector('[data-uo-nav-toggle]'),backdrop=document.querySelector('[data-uo-backdrop]');
 function nav(open){document.body.classList.toggle('uo-nav-open',open);if(toggle)toggle.setAttribute('aria-expanded',open?'true':'false')}
 if(toggle)toggle.addEventListener('click',()=>nav(!document.body.classList.contains('uo-nav-open')));
 if(backdrop)backdrop.addEventListener('click',()=>nav(false));
 document.addEventListener('click',event=>{if(event.target.closest('.nav-item')&&window.innerWidth<=820)nav(false)});
 const ask=document.querySelector('[data-uo-open-ask]');if(ask)ask.addEventListener('click',()=>{if(typeof qaToggle==='function')qaToggle()});
 const stop=document.querySelector('[data-uo-stop]');if(stop)stop.addEventListener('click',async()=>{
   if(!window.confirm('确认关闭当前 Orrery 本机服务？其他已打开的标签页也会断开。'))return;stop.disabled=true;
   try{const response=await fetch('/api/v1/shell/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!response.ok)throw new Error('关闭请求被拒绝');stop.textContent='服务已关闭';const banner=document.createElement('div');banner.className='uo-disconnected';banner.setAttribute('role','status');banner.innerHTML='<b>Orrery 服务已关闭</b><span>当前页面已经与本机服务断开，可以安全关闭标签页。</span>';document.body.append(banner)}catch(error){stop.disabled=false;stop.textContent='关闭失败，请重试'}
 });
})();
"""

SHELL_STATIC_JS = r"""
(function(){
 const toggle=document.querySelector('[data-uo-nav-toggle]'),backdrop=document.querySelector('[data-uo-backdrop]');
 function nav(open){document.body.classList.toggle('uo-nav-open',open);if(toggle)toggle.setAttribute('aria-expanded',open?'true':'false')}
 if(toggle)toggle.addEventListener('click',()=>nav(!document.body.classList.contains('uo-nav-open')));
 if(backdrop)backdrop.addEventListener('click',()=>nav(false));
 document.addEventListener('click',event=>{if(event.target.closest('.nav-item')&&window.innerWidth<=820)nav(false)});
})();
"""


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _status_page(identity: str, label: str, reason: str) -> str:
    return (
        f'<article class="page wide" id="{_esc(identity)}" data-kind="unavailable-consumer" '
        f'data-title="{_esc(label)}"><section class="uo-panel uo-unavailable">'
        f'<h2>{_esc(label)}</h2><p><b>当前暂不可用。</b> {_esc(reason)}</p>'
        '<p style="margin-top:10px">其他功能与文档阅读保持可用；证据不足不会被推断为完成或安全。</p>'
        '</section></article>'
    )


def _authority_page(status: Mapping[str, Any] | None, reason: str | None) -> str:
    if status is None:
        return _status_page("authority", NAVIGATION_LABELS["authority"], reason or "当前无法读取完整的权威状态。")
    selection = status.get("selection", {}) if isinstance(status.get("selection"), Mapping) else {}
    readiness = status.get("readiness", {}) if isinstance(status.get("readiness"), Mapping) else {}
    rollout = status.get("rollout_plan", {}) if isinstance(status.get("rollout_plan"), Mapping) else {}
    rollback = status.get("rollback_plan", {}) if isinstance(status.get("rollback_plan"), Mapping) else {}
    return (
        '<article class="page wide" id="authority" data-kind="authority-managed-consumer" '
        'data-authority="derived-read-only" data-contract="authority-managed-consumer-v1">'
        '<section class="uo-panel uo-authority"><div class="uo-topline"><span class="uo-live static"></span>权威状态 · 只读</div>'
        '<h2>权威状态</h2><p>这里只呈现受限的当前状态，不会选择、启用或拼接项目权威事实。</p>'
        f'<p style="margin-top:10px">当前读取器：{_esc(selection.get("active_consumer", "待确认"))}；准备状态：{_esc(display_status(readiness.get("status", "unknown")))}</p>'
        f'<details><summary>{TECHNICAL_DETAILS_LABEL}</summary><dl>'
        f'<dt>requested / effective</dt><dd>{_esc(selection.get("requested", "Unknown"))} / {_esc(selection.get("effective", "Unknown"))}</dd>'
        f'<dt>production switched</dt><dd>{_esc(selection.get("production_behavior_switched", False))}</dd>'
        f'<dt>rollout plan</dt><dd>{_esc(rollout.get("plan_id", "Unavailable"))}</dd>'
        f'<dt>rollback plan</dt><dd>{_esc(rollback.get("plan_id", "Unavailable"))}</dd>'
        '</dl></details><p>AI 与团队协调服务都没有权威选择权；不完整结果不会进入页面。</p></section></article>'
    )


def _overview_page(
    registrations: Sequence[ConsumerRegistration], *, mode: str
) -> str:
    caps = "".join(
        '<div class="uo-cap %s"><b>%s</b><small>%s · %s</small></div>'
        % (
            "unavailable" if item.status != "available" else "",
            _esc(item.navigation_label),
            _esc(display_status(item.status)),
            _esc(item.reason or "来源契约已登记"),
        )
        for item in registrations
    )
    dynamic = mode == "dynamic"
    actions = (
        '<div class="uo-actions"><button class="uo-button" type="button" data-uo-open-ask>打开文档问答</button></div>'
        if dynamic
        else '<div class="uo-actions"><button class="uo-button" type="button" disabled>静态阅读模式不提供动态控制</button></div>'
    )
    return (
        '<article class="page wide" id="overview" data-kind="unified-observatory-overview" '
        f'data-mode="{_esc(mode)}"><div class="uo-grid"><section class="uo-panel">'
        f'<div class="uo-topline"><span class="uo-live {"" if dynamic else "static"}"></span>{"单一本机地址" if dynamic else "静态文件 · 无运行服务"}</div>'
        '<h2>Orrery 项目观测台</h2><p>一个导航入口组合文档、搜索、问答与本机协作功能；证据不足时明确显示暂不可用。</p>'
        f'<div class="uo-caps">{caps}</div>{actions}</section><aside class="uo-panel"><h3>运行边界</h3><ul class="uo-boundary">'
        f'<li><b>{"本机动态控制" if dynamic else "静态只读"}</b><span>{"仅监听 127.0.0.1，并只提供一个可见页面地址" if dynamic else "无服务、无 cookie、无控制能力"}</span></li>'
        '<li><b>默认个人模式</b><span>零网络；团队协作与模型服务必须分别主动开启</span></li>'
        '<li><b>派生视图</b><span>不能创建 State、ADR、批准或 Validation 事实</span></li>'
        '<li><b>本机操作</b><span>仍需来源功能授权与最新的目标预检</span></li>'
        '</ul></aside></div></article>'
    )


def inject_unified_shell(
    page: str,
    registrations: Sequence[ConsumerRegistration],
    *,
    mode: str,
    authority_status: Mapping[str, Any] | None = None,
    authority_reason: str | None = None,
) -> str:
    if mode not in {"static", "dynamic"}:
        raise ValueError("shell mode must be static or dynamic")
    items = validate_registrations(registrations)
    content_marker = '</main><aside class="toc" id="toc">'
    nav_marker = '<div class="nav-top">'
    if content_marker not in page or nav_marker not in page or "</style>" not in page:
        raise ValueError("base docsite composition markers are missing")
    pages = [_overview_page(items, mode=mode), _authority_page(authority_status, authority_reason)]
    existing = {marker for marker in ("personal-observatory", "team-observatory", "workstream-relation-graph", "workspace-maintenance") if f'id="{marker}"' in page}
    for item in items:
        target = {
            "docs": "dashboard", "search": "dashboard", "ask": "dashboard",
            "workstreams": "workstream-relation-graph", "maintenance": "workspace-maintenance",
        }.get(item.navigation_identity, item.navigation_identity)
        if item.status != "available" and target not in existing and target not in {"overview", "authority", "dashboard"}:
            pages.append(_status_page(target, item.navigation_label, item.reason or "Consumer is unavailable."))
    nav_targets = {
        "overview": ("overview", NAVIGATION_LABELS["overview"], "accepted"),
        "docs": ("dashboard", NAVIGATION_LABELS["docs"], "state"),
        "ask": ("dashboard", NAVIGATION_LABELS["ask"], "deferred"),
        "authority": ("authority", NAVIGATION_LABELS["authority"], "state"),
        "personal": ("personal-observatory", NAVIGATION_LABELS["personal"], "state"),
        "team": ("team-observatory", NAVIGATION_LABELS["team"], "proposed"),
        "workstreams": ("workstream-relation-graph", NAVIGATION_LABELS["workstreams"], "proposed"),
        "maintenance": ("workspace-maintenance", NAVIGATION_LABELS["maintenance"], "state"),
    }
    by_identity = {item.navigation_identity: item for item in items}
    links = []
    for identity in ("overview", "docs", "ask", "authority", "personal", "team", "workstreams", "maintenance"):
        if identity not in by_identity:
            continue
        target, label, dot = nav_targets[identity]
        links.append(
            f'<a class="nav-item" data-target="{target}" data-nav-identity="{identity}">'
            f'<span class="dot {dot}"></span><span class="lbl">{label}</span></a>'
        )
    unified_nav = (
        '<div class="nav-group expanded" data-unified-navigation><div class="nav-title nogrp">'
        '<span class="nav-icon">◉</span><span class="nav-gname">Orrery</span></div>'
        f'<div class="nav-items">{"".join(links)}</div></div>'
    )
    duplicate_targets = (
        "dashboard", "personal-observatory", "team-observatory",
        "workstream-relation-graph", "workspace-maintenance",
    )
    duplicate_pattern = (
        r'<a class="nav-item"[^>]*data-target="(?:'
        + "|".join(map(re.escape, duplicate_targets))
        + r')"[^>]*>.*?</a>'
    )
    page = re.sub(duplicate_pattern, "", page, flags=re.DOTALL)
    page = re.sub(
        r"<title>.*?</title>",
        "<title>Orrery · 项目观测台</title>",
        page,
        count=1,
        flags=re.DOTALL,
    )
    page = re.sub(
        r'<header class="top"><h1>.*?</h1><span class="sub">.*?</span>',
        '<header class="top"><h1>Orrery · 项目观测台</h1>'
        '<span class="sub">文档观测台 · 源自 Markdown</span>',
        page,
        count=1,
        flags=re.DOTALL,
    )
    result = page.replace("</style>", SHELL_CSS + "</style>", 1)
    result = result.replace(nav_marker, nav_marker + unified_nav, 1)
    result = result.replace(content_marker, "".join(pages) + content_marker, 1)
    result = result.replace(
        '<div class="rightgrp">',
        '<div class="rightgrp"><button class="tbtn uo-mobile-toggle" type="button" data-uo-nav-toggle aria-label="打开导航" aria-expanded="false">☰</button>'
        + ('<button class="tbtn uo-stop-global" type="button" data-uo-stop>关闭 Orrery 服务</button>' if mode == "dynamic" else ""),
        1,
    )
    result = result.replace('<div class="app">', '<div class="uo-backdrop" data-uo-backdrop></div><div class="app">', 1)
    if mode == "static":
        result = result.replace("start-docsite.bat", "Start Orrery.vbs")
    shell_script = SHELL_JS if mode == "dynamic" else SHELL_STATIC_JS
    return result.replace("</body>", "<script>" + shell_script + "</script></body>", 1)


__all__ = [
    "SHELL_CONTRACT", "REGISTRATION_CONTRACT", "SHELL_API_VERSION",
    "ConsumerRegistration", "RegistrationError", "validate_registrations",
    "quarantine", "capability_document", "inject_unified_shell",
]
