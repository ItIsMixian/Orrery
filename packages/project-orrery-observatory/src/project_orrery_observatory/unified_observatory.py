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
.uo-ask-note{margin-top:12px!important;font-size:11px!important}.uo-ask-note strong{color:var(--fg);font-weight:700}
.uo-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}.uo-button{border:1px solid var(--line);border-radius:7px;background:var(--bg3);color:var(--fg);padding:8px 11px;font:700 11px/1.2 inherit;cursor:pointer}.uo-button:hover{border-color:var(--acc);color:var(--acc)}.uo-button.danger{color:var(--warn)}
.uo-stop-global{white-space:nowrap;color:var(--warn)}.uo-disconnected{position:fixed;z-index:400;left:50%;top:calc(var(--hh) + 16px);transform:translateX(-50%);width:min(680px,calc(100vw - 24px));padding:13px 16px;border:1px solid var(--warn);border-radius:10px;background:var(--bg2);box-shadow:0 18px 55px rgba(0,0,0,.45);color:var(--fg);font-size:12px}.uo-disconnected b{display:block;margin-bottom:3px}.uo-disconnected span{color:var(--mut)}
.uo-boundary{list-style:none;margin:0;padding:0}.uo-boundary li{padding:9px 0;border-bottom:1px solid var(--line);font-size:11.5px}.uo-boundary li:last-child{border-bottom:0}.uo-boundary b{display:block}.uo-boundary span{color:var(--mut)}
.uo-authority dl{display:grid;grid-template-columns:140px 1fr;gap:7px 12px;margin:14px 0}.uo-authority dt{color:var(--mut);font-size:11px}.uo-authority dd{margin:0;font:12px/1.5 "Cascadia Code",Consolas,monospace;overflow-wrap:anywhere}
.uo-authority-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px;margin-top:16px}.uo-layer{border:1px solid var(--line);border-radius:10px;background:var(--bg);padding:14px;min-width:0}.uo-layer-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:10px}.uo-layer-head p{font-size:11px}.uo-source{flex:none;color:var(--mut);font:700 9px/1.4 "Cascadia Code",Consolas,monospace;border:1px solid var(--line);border-radius:999px;padding:3px 7px}.uo-principles,.uo-rules{list-style:none;margin:0;padding:0}.uo-principles li,.uo-rule{padding:9px 0;border-top:1px solid var(--line)}.uo-principles li:first-child,.uo-rule:first-child{border-top:0}.uo-principles b,.uo-rule b{display:block;color:var(--strong);font-size:12px}.uo-principles span,.uo-rule p{display:block;color:var(--mut);font-size:11px;margin:3px 0 0}.uo-rule summary{cursor:pointer;list-style:none}.uo-rule summary::-webkit-details-marker{display:none}.uo-rule summary:after{content:'＋';float:right;color:var(--mut)}.uo-rule[open] summary:after{content:'－'}.uo-rule dl{grid-template-columns:105px 1fr;margin:9px 0 0;padding:9px;background:var(--bg2);border-radius:7px}.uo-fact-status{margin-top:14px}.uo-fact-status>summary{cursor:pointer;color:var(--strong);font-weight:700}.uo-layer-note{margin-top:12px!important;padding-top:10px;border-top:1px solid var(--line)}
.uo-unavailable{border-left:3px solid var(--warn)}
.toc:empty{display:none}
.sidebar[data-unified-sidebar]{overscroll-behavior:contain;scrollbar-gutter:stable}.uo-rail{display:block;min-width:0}
.uo-app-nav{padding-bottom:8px;margin-bottom:5px}.uo-app-nav .nav-title{padding-top:4px}.uo-app-nav .nav-item{min-height:32px}
.uo-documents{margin:0;padding-top:5px;border-top:1px solid var(--line)}.uo-documents>.nav-title{padding-top:9px}
.uo-documents:not(.expanded)>.uo-doc-tree{display:none}.uo-doc-tree{min-width:0}.uo-doc-tree>.nav-group{margin-left:0}
.uo-doc-tree>.nav-group>.nav-title{padding-left:10px}.uo-documents>.nav-title .nav-chev{transition:transform .12s ease}
.uo-mobile-toggle{display:none}.uo-backdrop{display:none}
.uo-help-trigger{white-space:nowrap}.uo-help-backdrop{position:fixed;z-index:245;inset:var(--hh) 0 0;background:rgba(4,10,12,.52);backdrop-filter:blur(2px)}.uo-help-backdrop[hidden],.uo-help-panel[hidden]{display:none}.uo-help-panel{position:fixed;z-index:250;right:12px;top:calc(var(--hh) + 12px);bottom:12px;width:min(620px,calc(100vw - 24px));overflow:auto;background:var(--bg2);border:1px solid var(--line);border-radius:14px;box-shadow:0 24px 72px rgba(0,0,0,.48);padding:20px}.uo-help-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding-bottom:13px;border-bottom:1px solid var(--line)}.uo-help-head h2{margin:3px 0 4px;font-size:20px}.uo-help-head p{margin:0;color:var(--mut);font-size:11px}.uo-help-close{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line);border-radius:8px;background:var(--bg3);color:var(--fg);font-size:18px;cursor:pointer}.uo-help-close:hover,.uo-help-close:focus-visible,.uo-help-trigger:focus-visible{border-color:var(--acc);color:var(--acc);outline:2px solid var(--acc);outline-offset:2px}.uo-help-panel .uo-authority{border:0;background:transparent;padding:16px 0 0}.uo-help-panel .uo-authority-grid{grid-template-columns:1fr}.uo-help-panel .uo-fact-status{border-top:1px solid var(--line);padding-top:14px}
@media(max-width:820px){
 .uo-mobile-toggle{display:inline-grid;place-items:center}.sidebar{display:none!important}.sidebar-resizer{display:none!important}
 body.uo-nav-open{overflow:hidden}body.uo-nav-open .sidebar{display:block!important;position:fixed;z-index:180;left:0;top:var(--hh);bottom:0;width:min(330px,88vw);height:auto;box-shadow:20px 0 50px rgba(0,0,0,.45)}
 body.uo-nav-open .uo-backdrop{display:block;position:fixed;z-index:170;inset:var(--hh) 0 0;background:rgba(0,0,0,.55)}
 .content{padding:0 18px}.uo-grid,.uo-authority-grid{grid-template-columns:1fr}.uo-caps{grid-template-columns:1fr}.top .sub{display:none}#q{width:min(42vw,190px)}
 .uo-help-panel{left:0;right:0;top:var(--hh);bottom:0;width:100vw;max-width:none;box-sizing:border-box;border-radius:0;border-top:0;border-bottom:0;border-right:0;padding:18px}
}
@media(max-width:460px){header.top{gap:6px;padding:0 8px}.top h1{max-width:82px;overflow:hidden;text-overflow:ellipsis}.rightgrp{gap:5px}.tbtn{padding:6px 7px}#q{display:none}.uo-stop-global{font-size:10px}.uo-authority dl{grid-template-columns:1fr}.page{padding-top:20px}}
@media(prefers-reduced-motion:reduce){.uo-panel *,.uo-documents>.nav-title .nav-chev,.uo-help-panel *{transition:none!important;scroll-behavior:auto!important}}
"""


SHELL_JS = r"""
(function(){
 const toggle=document.querySelector('[data-uo-nav-toggle]'),backdrop=document.querySelector('[data-uo-backdrop]');
 function nav(open){document.body.classList.toggle('uo-nav-open',open);if(toggle)toggle.setAttribute('aria-expanded',open?'true':'false')}
 if(toggle)toggle.addEventListener('click',()=>nav(!document.body.classList.contains('uo-nav-open')));
 if(backdrop)backdrop.addEventListener('click',()=>nav(false));
 const documents=document.querySelector('[data-project-documents-toggle]');if(documents)documents.addEventListener('click',()=>{const group=documents.closest('[data-project-documents]');requestAnimationFrame(()=>documents.setAttribute('aria-expanded',group&&group.classList.contains('expanded')?'true':'false'))});
 document.addEventListener('click',event=>{if(event.target.closest('.nav-item')&&window.innerWidth<=820)nav(false)});
 const help=document.querySelector('[data-uo-help]'),helpPanel=document.querySelector('[data-uo-help-panel]'),helpBackdrop=document.querySelector('[data-uo-help-backdrop]'),helpClose=document.querySelector('[data-uo-help-close]');let helpReturn=null;
 function setHelp(open){if(!help||!helpPanel||!helpBackdrop)return;helpPanel.hidden=!open;helpBackdrop.hidden=!open;help.setAttribute('aria-expanded',open?'true':'false');if(open){helpReturn=document.activeElement;helpClose&&helpClose.focus()}else if(helpReturn&&typeof helpReturn.focus==='function')helpReturn.focus()}
 if(help)help.addEventListener('click',()=>setHelp(helpPanel&&helpPanel.hidden));if(helpClose)helpClose.addEventListener('click',()=>setHelp(false));if(helpBackdrop)helpBackdrop.addEventListener('click',()=>setHelp(false));
 document.addEventListener('keydown',event=>{if(!helpPanel||helpPanel.hidden)return;if(event.key==='Escape'){event.preventDefault();setHelp(false);return}if(event.key==='Tab'){const focusable=[...helpPanel.querySelectorAll('button,summary')].filter(item=>!item.disabled);if(!focusable.length)return;const first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}}});
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
 const documents=document.querySelector('[data-project-documents-toggle]');if(documents)documents.addEventListener('click',()=>{const group=documents.closest('[data-project-documents]');requestAnimationFrame(()=>documents.setAttribute('aria-expanded',group&&group.classList.contains('expanded')?'true':'false'))});
 document.addEventListener('click',event=>{if(event.target.closest('.nav-item')&&window.innerWidth<=820)nav(false)});
 const help=document.querySelector('[data-uo-help]'),helpPanel=document.querySelector('[data-uo-help-panel]'),helpBackdrop=document.querySelector('[data-uo-help-backdrop]'),helpClose=document.querySelector('[data-uo-help-close]');let helpReturn=null;
 function setHelp(open){if(!help||!helpPanel||!helpBackdrop)return;helpPanel.hidden=!open;helpBackdrop.hidden=!open;help.setAttribute('aria-expanded',open?'true':'false');if(open){helpReturn=document.activeElement;helpClose&&helpClose.focus()}else if(helpReturn&&typeof helpReturn.focus==='function')helpReturn.focus()}
 if(help)help.addEventListener('click',()=>setHelp(helpPanel&&helpPanel.hidden));if(helpClose)helpClose.addEventListener('click',()=>setHelp(false));if(helpBackdrop)helpBackdrop.addEventListener('click',()=>setHelp(false));document.addEventListener('keydown',event=>{if(!helpPanel||helpPanel.hidden)return;if(event.key==='Escape'){event.preventDefault();setHelp(false);return}if(event.key==='Tab'){const focusable=[...helpPanel.querySelectorAll('button,summary')].filter(item=>!item.disabled);if(!focusable.length)return;const first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}}});
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


def _help_panel(
    status: Mapping[str, Any] | None,
    reason: str | None,
    projection: Mapping[str, Any] | None,
) -> str:
    project_layer = projection.get("project_principles", {}) if isinstance(projection, Mapping) else {}
    rules_layer = projection.get("orrery_operating_rules", {}) if isinstance(projection, Mapping) else {}
    principles = project_layer.get("items", []) if isinstance(project_layer, Mapping) else []
    rules = rules_layer.get("rules", []) if isinstance(rules_layer, Mapping) else []
    principle_items = "".join(
        '<li><b>%s</b><span>%s</span></li>' % (
            _esc(item.get("title", "项目原则")), _esc(item.get("summary", "")),
        )
        for item in principles if isinstance(item, Mapping)
    ) or '<li><b>当前暂不可用</b><span>目标项目 Seed 无法安全读取。</span></li>'
    strength_labels = {"must": "必须", "must-not": "禁止", "should": "建议"}
    enforcement_labels = {
        "enforceable": "可机械检查", "partially-enforceable": "部分机械检查",
        "human-judgment": "需要人工判断",
    }
    rule_items = "".join(
        '<details class="uo-rule"><summary><b>%s</b><p>%s · %s</p></summary><dl>'
        '<dt>rule ID / version</dt><dd>%s / %s</dd>'
        '<dt>source</dt><dd>%s</dd>'
        '<dt>enforcement</dt><dd>%s</dd>'
        '<dt>failure / Unknown</dt><dd>%s / %s</dd>'
        '</dl></details>' % (
            _esc((item.get("summary") or {}).get("zh-CN", item.get("message_key", "工作规则"))),
            _esc(strength_labels.get(str(item.get("strength")), item.get("strength", "Unknown"))),
            _esc(enforcement_labels.get(str(item.get("mechanical_enforcement")), item.get("mechanical_enforcement", "Unknown"))),
            _esc(item.get("rule_id", "Unknown")), _esc(item.get("rule_version", "Unknown")),
            _esc("；".join(str(source.get("path", "")) for source in item.get("sources", []) if isinstance(source, Mapping))),
            _esc(item.get("mechanical_enforcement", "Unknown")),
            _esc(item.get("failure_behavior", "Unknown")), _esc(item.get("unknown_behavior", "Unknown")),
        )
        for item in rules if isinstance(item, Mapping)
    ) or '<div class="uo-rule"><b>当前暂不可用</b><p>工具规则 inventory 缺失或版本不兼容；已保持只读/Unknown。</p></div>'
    if status is None:
        status = {}
    selection = status.get("selection", {}) if isinstance(status.get("selection"), Mapping) else {}
    readiness = status.get("readiness", {}) if isinstance(status.get("readiness"), Mapping) else {}
    rollout = status.get("rollout_plan", {}) if isinstance(status.get("rollout_plan"), Mapping) else {}
    rollback = status.get("rollback_plan", {}) if isinstance(status.get("rollback_plan"), Mapping) else {}
    return (
        '<div class="uo-help-backdrop" data-uo-help-backdrop hidden></div>'
        '<section class="uo-help-panel" data-uo-help-panel role="dialog" aria-modal="false" aria-labelledby="uo-help-title" hidden>'
        '<header class="uo-help-head"><div><span class="uo-topline">帮助 / 系统状态 · 只读</span><h2 id="uo-help-title">Orrery 如何解释项目事实</h2><p>三层来源保持独立；此处没有编辑、批准、启用或执行能力。</p></div>'
        '<button class="uo-help-close" type="button" data-uo-help-close aria-label="关闭帮助与系统状态">×</button></header>'
        '<section class="uo-authority" data-authority="derived-read-only" data-contract="authority-managed-consumer-v1">'
        '<div class="uo-authority-grid"><section class="uo-layer"><div class="uo-layer-head"><div><h3>项目原则</h3><p>目标项目选择的方向与约束</p></div><span class="uo-source">来源：项目文档</span></div>'
        f'<ol class="uo-principles">{principle_items}</ol></section>'
        '<section class="uo-layer"><div class="uo-layer-head"><div><h3>Orrery 工作规则</h3><p>同版本工具在读取、判断与维护时遵循的规则</p></div><span class="uo-source">来源：工具版本</span></div>'
        f'<div class="uo-rules" data-operating-rules-version="{_esc(rules_layer.get("inventory_version", "Unknown") if isinstance(rules_layer, Mapping) else "Unknown")}">{rule_items}</div>'
        '<p class="uo-layer-note">这些规则不会写入或批准目标项目的 Seed、State 与发布事实。</p></section></div>'
        f'<details class="uo-fact-status"><summary>事实解释状态 · {_esc(display_status(readiness.get("status", "unknown")))}</summary>'
        f'<p style="margin-top:10px">当前读取器：{_esc(selection.get("active_consumer", "待确认"))}；{_esc(reason or "技术状态默认折叠，不影响上方两层来源边界。")}</p>'
        f'<details><summary>{TECHNICAL_DETAILS_LABEL}</summary><dl>'
        f'<dt>requested / effective</dt><dd>{_esc(selection.get("requested", "Unknown"))} / {_esc(selection.get("effective", "Unknown"))}</dd>'
        f'<dt>production switched</dt><dd>{_esc(selection.get("production_behavior_switched", False))}</dd>'
        f'<dt>rollout plan</dt><dd>{_esc(rollout.get("plan_id", "Unavailable"))}</dd>'
        f'<dt>rollback plan</dt><dd>{_esc(rollback.get("plan_id", "Unavailable"))}</dd>'
        '</dl></details><p>AI、页面与团队协调服务都没有编辑、批准、执行或权威选择权。</p></details></section></section>'
    )


def _overview_page(
    registrations: Sequence[ConsumerRegistration], *, mode: str
) -> str:
    visible_identities = {"overview", "docs", "personal", "team", "workstreams", "maintenance", "trends"}
    caps = "".join(
        '<div class="uo-cap %s"><b>%s</b><small>%s · %s</small></div>'
        % (
            "unavailable" if item.status != "available" else "",
            _esc(item.navigation_label),
            _esc(display_status(item.status)),
            _esc(item.reason or "来源契约已登记"),
        )
        for item in registrations if item.navigation_identity in visible_identities
    )
    dynamic = mode == "dynamic"
    return (
        '<article class="page wide" id="overview" data-kind="unified-observatory-overview" '
        f'data-mode="{_esc(mode)}"><div class="uo-grid"><section class="uo-panel">'
        f'<div class="uo-topline"><span class="uo-live {"" if dynamic else "static"}"></span>{"单一本机地址" if dynamic else "静态文件 · 无运行服务"}</div>'
        '<h2>Orrery 项目观测台</h2><p>一个导航入口组合文档、搜索与本机协作功能；证据不足时明确显示暂不可用。</p>'
        f'<div class="uo-caps">{caps}</div><p class="uo-ask-note" data-ask-docs-label><strong>问文档</strong> · 入口位于右下角</p></section><aside class="uo-panel"><h3>运行边界</h3><ul class="uo-boundary">'
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
    fact_rules_projection: Mapping[str, Any] | None = None,
) -> str:
    if mode not in {"static", "dynamic"}:
        raise ValueError("shell mode must be static or dynamic")
    items = validate_registrations(registrations)
    content_marker = '</main><aside class="toc" id="toc">'
    nav_marker = '<div class="nav-top">'
    if content_marker not in page or nav_marker not in page or "</style>" not in page:
        raise ValueError("base docsite composition markers are missing")
    pages = [_overview_page(items, mode=mode)]
    existing = {marker for marker in ("personal-observatory", "team-observatory", "workstream-relation-graph", "workspace-maintenance") if f'id="{marker}"' in page}
    for item in items:
        target = {
            "docs": "dashboard", "search": "dashboard", "ask": "dashboard",
            "workstreams": "workstream-relation-graph", "maintenance": "workspace-maintenance",
        }.get(item.navigation_identity, item.navigation_identity)
        if item.status != "available" and target not in existing and target not in {"overview", "authority", "dashboard", "trends"}:
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
        "trends": ("trends", NAVIGATION_LABELS["trends"], "proposed"),
    }
    by_identity = {item.navigation_identity: item for item in items}
    links = []
    for identity in ("overview", "docs", "personal", "team", "workstreams", "maintenance", "trends"):
        if identity not in by_identity:
            continue
        target, label, dot = nav_targets[identity]
        links.append(
            f'<a class="nav-item" data-target="{target}" data-nav-identity="{identity}">'
            f'<span class="dot {dot}"></span><span class="lbl">{label}</span></a>'
        )
    unified_nav = (
        '<div class="nav-group expanded uo-app-nav" data-unified-navigation><div class="nav-title nogrp">'
        '<span class="nav-icon">◉</span><span class="nav-gname">Orrery</span></div>'
        f'<div class="nav-items">{"".join(links)}</div></div>'
    )
    duplicate_targets = (
        "dashboard", "personal-observatory", "team-observatory",
        "workstream-relation-graph", "workspace-maintenance", "trends",
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
    def compose_sidebar(match: re.Match[str]) -> str:
        top, document_tree = match.group(1), match.group(2)
        documents = (
            '<div class="nav-group expanded uo-documents" data-project-documents>'
            '<div class="nav-title" data-project-documents-toggle aria-expanded="true">'
            '<span class="nav-icon">▤</span><span class="nav-gname">项目文档</span>'
            '<span class="nav-chev">▾</span></div>'
            f'<div class="uo-doc-tree" data-project-document-tree>{document_tree}</div></div>'
        )
        return top + '<div class="uo-rail">' + unified_nav + documents + '</div>'

    page, sidebar_count = re.subn(
        r'(<div class="nav-top">.*?</div>)(.*?)(?=</aside>(?:<div class="sidebar-resizer"|<main))',
        compose_sidebar,
        page,
        count=1,
        flags=re.DOTALL,
    )
    if sidebar_count != 1:
        raise ValueError("base docsite sidebar composition marker is missing")
    result = page.replace("</style>", SHELL_CSS + "</style>", 1)
    result = result.replace(
        '<aside class="sidebar">',
        '<aside class="sidebar" data-unified-sidebar data-sidebar-scroll-container>',
        1,
    )
    result = result.replace(content_marker, "".join(pages) + content_marker, 1)
    result = result.replace(
        '<div class="rightgrp">',
        '<div class="rightgrp"><button class="tbtn uo-mobile-toggle" type="button" data-uo-nav-toggle aria-label="打开导航" aria-expanded="false">☰</button>'
        + '<button class="tbtn uo-help-trigger" type="button" data-uo-help aria-controls="uo-help-title" aria-expanded="false">? 帮助</button>'
        + ('<button class="tbtn uo-stop-global" type="button" data-uo-stop>关闭 Orrery 服务</button>' if mode == "dynamic" else ""),
        1,
    )
    result = result.replace('<div class="app">', '<div class="uo-backdrop" data-uo-backdrop></div><div class="app">', 1)
    if mode == "static":
        result = result.replace("start-docsite.bat", "Start Orrery.vbs")
    result = result.replace("</body>", _help_panel(authority_status, authority_reason, fact_rules_projection) + "</body>", 1)
    shell_script = SHELL_JS if mode == "dynamic" else SHELL_STATIC_JS
    return result.replace("</body>", "<script>" + shell_script + "</script></body>", 1)


__all__ = [
    "SHELL_CONTRACT", "REGISTRATION_CONTRACT", "SHELL_API_VERSION",
    "ConsumerRegistration", "RegistrationError", "validate_registrations",
    "quarantine", "capability_document", "inject_unified_shell",
]
