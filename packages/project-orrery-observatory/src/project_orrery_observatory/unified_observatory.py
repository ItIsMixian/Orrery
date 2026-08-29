"""Versioned registration and presentation shell for the root-only Observatory.

The shell owns composition metadata, navigation, and failure isolation.  It
does not parse project facts or implement consumer domain actions.
"""
from __future__ import annotations

import html
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from typing import Any


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
@media(max-width:460px){header.top{gap:7px;padding:0 10px}.top h1{max-width:116px;overflow:hidden;text-overflow:ellipsis}.rightgrp{gap:6px}.tbtn{padding:6px 8px}#q{width:118px}.uo-authority dl{grid-template-columns:1fr}.page{padding-top:20px}}
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
   if(!window.confirm('Stop the local Orrery runtime?'))return;stop.disabled=true;
   try{const response=await fetch('/api/v1/shell/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!response.ok)throw new Error('stop refused');stop.textContent='Stopping…'}catch(error){stop.disabled=false;stop.textContent='Stop failed'}
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
        f'<h2>{_esc(label)}</h2><p><b>Unavailable / Unknown.</b> {_esc(reason)}</p>'
        '<p style="margin-top:10px">其他 consumer 与文档阅读保持可用；此状态不会推断为完成或安全。</p>'
        '</section></article>'
    )


def _authority_page(status: Mapping[str, Any] | None, reason: str | None) -> str:
    if status is None:
        return _status_page("authority", "Authority", reason or "A3 managed-consumer contract is unavailable.")
    selection = status.get("selection", {}) if isinstance(status.get("selection"), Mapping) else {}
    readiness = status.get("readiness", {}) if isinstance(status.get("readiness"), Mapping) else {}
    rollout = status.get("rollout_plan", {}) if isinstance(status.get("rollout_plan"), Mapping) else {}
    rollback = status.get("rollback_plan", {}) if isinstance(status.get("rollback_plan"), Mapping) else {}
    return (
        '<article class="page wide" id="authority" data-kind="authority-managed-consumer" '
        'data-authority="derived-read-only" data-contract="authority-managed-consumer-v1">'
        '<section class="uo-panel uo-authority"><div class="uo-topline"><span class="uo-live static"></span>A3 MANAGED CONSUMER · READ ONLY</div>'
        '<h2>Authority consumer status</h2><p>Shell 只显示 A3 的受限状态；不会选择、启用或拼接 Authority claims。</p><dl>'
        f'<dt>Active consumer</dt><dd>{_esc(selection.get("active_consumer", "Unknown"))}</dd>'
        f'<dt>Requested / effective</dt><dd>{_esc(selection.get("requested", "Unknown"))} / {_esc(selection.get("effective", "Unknown"))}</dd>'
        f'<dt>Readiness</dt><dd>{_esc(readiness.get("status", "Unknown"))}</dd>'
        f'<dt>Production switched</dt><dd>{_esc(selection.get("production_behavior_switched", False))}</dd>'
        f'<dt>Rollout plan</dt><dd>{_esc(rollout.get("plan_id", "Unavailable"))}</dd>'
        f'<dt>Rollback plan</dt><dd>{_esc(rollback.get("plan_id", "Unavailable"))}</dd>'
        '</dl><p>AI 与 Coordinator 均无 selection authority；partial render 不会进入页面。</p></section></article>'
    )


def _overview_page(
    registrations: Sequence[ConsumerRegistration], *, mode: str
) -> str:
    caps = "".join(
        '<div class="uo-cap %s"><b>%s</b><small>%s · %s</small></div>'
        % (
            "unavailable" if item.status != "available" else "",
            _esc(item.navigation_label),
            _esc(item.status),
            _esc(item.reason or item.source_contract_version),
        )
        for item in registrations
    )
    dynamic = mode == "dynamic"
    actions = (
        '<div class="uo-actions"><button class="uo-button" type="button" data-uo-open-ask>Open Ask Docs</button>'
        '<button class="uo-button danger" type="button" data-uo-stop>Stop Orrery</button></div>'
        if dynamic
        else '<div class="uo-actions"><button class="uo-button" type="button" disabled>Dynamic controls unavailable in static mode</button></div>'
    )
    return (
        '<article class="page wide" id="overview" data-kind="unified-observatory-overview" '
        f'data-mode="{_esc(mode)}"><div class="uo-grid"><section class="uo-panel">'
        f'<div class="uo-topline"><span class="uo-live {"" if dynamic else "static"}"></span>{"ONE LOOPBACK URL" if dynamic else "STATIC FILE · NO RUNTIME"}</div>'
        '<h2>Orrery Observatory</h2><p>一个导航壳组合文档、搜索、AI 与本机协作 consumer；缺失证据保持 Unavailable / Unknown。</p>'
        f'<div class="uo-caps">{caps}</div>{actions}</section><aside class="uo-panel"><h3>Runtime boundaries</h3><ul class="uo-boundary">'
        f'<li><b>{"Dynamic local control" if dynamic else "Static read-only"}</b><span>{"127.0.0.1 only; one visible UI URL" if dynamic else "no server · no cookie · no control"}</span></li>'
        '<li><b>Personal default</b><span>zero-network; Team and provider access are independent opt-ins</span></li>'
        '<li><b>Derived views</b><span>cannot create State, ADR, approval or Validation facts</span></li>'
        '<li><b>Local actions</b><span>provider-owned capability and fresh preflight remain required</span></li>'
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
        "overview": ("overview", "Overview", "accepted"),
        "docs": ("dashboard", "Docs & Search", "state"),
        "ask": ("dashboard", "Ask Docs", "deferred"),
        "authority": ("authority", "Authority", "state"),
        "personal": ("personal-observatory", "Personal", "state"),
        "team": ("team-observatory", "Team", "proposed"),
        "workstreams": ("workstream-relation-graph", "Workstreams", "proposed"),
        "maintenance": ("workspace-maintenance", "Maintenance", "state"),
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
    result = page.replace("</style>", SHELL_CSS + "</style>", 1)
    result = result.replace(nav_marker, nav_marker + unified_nav, 1)
    result = result.replace(content_marker, "".join(pages) + content_marker, 1)
    result = result.replace(
        '<div class="rightgrp">',
        '<div class="rightgrp"><button class="tbtn uo-mobile-toggle" type="button" data-uo-nav-toggle aria-label="Open navigation" aria-expanded="false">☰</button>',
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
