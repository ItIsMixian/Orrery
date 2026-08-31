"""Chinese-first relation confirmation inbox for the Unified Observatory."""
from __future__ import annotations

import html
import json
import re
from typing import Any, Mapping


RELATION_INBOX_CSS = r"""
.ri-shell{margin:18px 0;padding:18px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(135deg,rgba(244,201,107,.055),transparent 55%),var(--bg2)}.ri-head{display:flex;justify-content:space-between;gap:16px;align-items:start}.ri-head h3{margin:3px 0;font-size:17px}.ri-head p{margin:0;color:var(--mut);font-size:11px}.ri-kicker{color:#f4c96b;font:700 9px "Cascadia Code",Consolas,monospace;letter-spacing:.11em}.ri-count{padding:6px 8px;border:1px solid var(--line);border-radius:6px;color:var(--mut);font:700 10px "Cascadia Code",Consolas,monospace}.ri-list{display:grid;gap:9px;margin-top:14px}.ri-card{min-width:0;padding:13px;border:1px solid var(--line);border-left:4px solid #f4c96b;border-radius:8px;background:var(--bg)}.ri-card h4{margin:0;font-size:13px;overflow-wrap:anywhere}.ri-direction{margin:5px 0;color:var(--fg);font-size:11.5px;overflow-wrap:anywhere}.ri-gate{display:inline-block;margin-right:7px;padding:3px 6px;border-radius:4px;background:rgba(244,201,107,.1);color:#f4c96b;font:700 9px "Cascadia Code",Consolas,monospace}.ri-consequence,.ri-rationale{margin:6px 0;color:var(--mut);font-size:10.5px;line-height:1.55}.ri-evidence{display:flex;gap:5px;flex-wrap:wrap}.ri-evidence span{max-width:100%;padding:4px 6px;border:1px solid var(--line);border-radius:5px;color:var(--mut);font:9px "Cascadia Code",Consolas,monospace;overflow-wrap:anywhere}.ri-actions{display:flex;align-items:end;gap:7px;flex-wrap:wrap;margin-top:10px;padding-top:10px;border-top:1px solid var(--line)}.ri-actions button,.ri-actions select{min-height:36px;border:1px solid var(--line);border-radius:6px;background:var(--bg2);color:var(--fg);padding:0 9px;font:600 10px inherit}.ri-actions button{cursor:pointer}.ri-actions button.primary{border-color:#6ee7dd;color:#6ee7dd}.ri-actions button.danger{color:#ff8c82}.ri-actions label{display:grid;gap:3px;color:var(--mut);font-size:9px}.ri-empty{padding:12px;border:1px dashed var(--line);border-radius:7px;color:var(--mut);font-size:11px}.ri-notice{min-height:18px;margin-top:8px;color:var(--mut);font-size:10px}.ri-request-only{margin-top:10px;padding:8px;border:1px dashed var(--line);border-radius:6px;color:var(--mut);font-size:10px}@media(max-width:640px){.ri-shell{margin:14px 0;padding:14px}.ri-head{display:grid}.ri-count{justify-self:start}.ri-actions{display:grid;grid-template-columns:1fr}.ri-actions button,.ri-actions select{width:100%;min-width:0}}
"""


RELATION_INBOX_JS = r"""
(()=>{'use strict';const panels=[...document.querySelectorAll('[data-relation-inbox]')];if(!panels.length)return;
const gateLabels={implementation:'实现完成前',validation:'验证完成前',integration:'集成前',release:'发布前'};
const relationLabels={derived_from:'继承来源',depends_on:'阶段依赖',absorbs:'责任接管'};
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
async function api(path,body){const response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const value=await response.json();if(!response.ok)throw new Error(value.error||'本机关系操作失败');return value}
function render(panel,data){const list=panel.querySelector('[data-ri-list]'),count=panel.querySelector('[data-ri-count]'),requestOnly=panel.dataset.requestOnly==='true';list.replaceChildren();const items=data.pending_proposals||[];count.textContent=`${items.length} 项`;
 if(!items.length){list.append(el('div','ri-empty','当前没有等待人工确认的关系建议。'));return}
 items.forEach(item=>{const p=item.current,card=el('article','ri-card'),title=el('h4',null,`${relationLabels[p.relation_type]||p.relation_type} · revision ${p.revision}`),direction=el('div','ri-direction',`${p.source_workstream_id} 依赖／接续 ${p.target_workstream_id}`),copy=el('p','ri-consequence',p.consequence),why=el('p','ri-rationale',`原因：${p.rationale}`),evidence=el('div','ri-evidence');card.append(title,direction);if(p.required_for)direction.prepend(el('span','ri-gate',gateLabels[p.required_for]||p.required_for));card.append(copy,why,evidence);(p.evidence||[]).forEach(value=>evidence.append(el('span',null,`${value.category} · ${value.ref} · ${value.fact_scope}`)));
  const capability=item.local_confirmation||{},allowed=!requestOnly&&capability.allowed===true&&panel.dataset.dynamic==='true';if(allowed){const actions=el('div','ri-actions'),accept=el('button','primary','接受'),defer=el('button',null,'暂缓／Unknown'),reject=el('button','danger','拒绝'),canAccept=p.relation_type!=='derived_from',canChangeGate=p.relation_type==='depends_on',bindings=[];let label=null,select=null,change=null;if(canAccept)bindings.push([accept,'accept']);if(canChangeGate){label=el('label',null,'阻塞阶段');select=el('select');['implementation','validation','integration','release'].forEach(gate=>{const option=el('option',null,gateLabels[gate]);option.value=gate;option.selected=gate===p.required_for;select.append(option)});label.append(select);change=el('button',null,'更改阶段');bindings.push([change,'change-gate'])}bindings.push([defer,'defer'],[reject,'reject']);bindings.forEach(([button,action])=>button.addEventListener('click',async()=>{button.disabled=true;try{const body={proposal_id:p.proposal_id,expected_revision:p.revision};if(action==='change-gate')body.required_for=select.value;await api(`/api/v1/workstreams/relations/${action}`,body);await refresh()}catch(error){panel.querySelector('[data-ri-notice]').textContent=error.message;button.disabled=false}}));if(canAccept)actions.append(accept);if(canChangeGate)actions.append(label,change);actions.append(defer,reject);card.append(actions)}else{card.append(el('div','ri-request-only',requestOnly?'中央／团队视图只能发送请求；确认必须回到具备权限的成员本机。':'当前本机身份没有该 gate 所需的 task owner／integrator 权限。'))}list.append(card)})}
async function refresh(){try{const data=await api('/api/v1/workstreams/relations');panels.forEach(panel=>render(panel,data));}catch(error){panels.forEach(panel=>panel.querySelector('[data-ri-notice]').textContent=error.message)}}
panels.forEach(panel=>{const payload=panel.querySelector('[data-ri-payload]');if(payload)render(panel,JSON.parse(payload.textContent))});if(panels.some(panel=>panel.dataset.dynamic==='true'))refresh();})();
"""


def _panel(capture: Mapping[str, Any], *, dynamic: bool, request_only: bool) -> str:
    payload = json.dumps(dict(capture), ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")
    return (
        '<section class="ri-shell" data-relation-inbox data-dynamic="%s" data-request-only="%s" '
        'aria-label="关系待确认"><div class="ri-head"><div><span class="ri-kicker">RELATION INBOX / 本机证据</span>'
        '<h3>关系待确认</h3><p>先看谁依赖谁、在哪个阶段阻塞、证据与接受后果。</p></div>'
        '<span class="ri-count" data-ri-count>0 项</span></div><div class="ri-list" data-ri-list></div>'
        '<div class="ri-notice" data-ri-notice aria-live="polite"></div>'
        '<script type="application/json" data-ri-payload>%s</script></section>'
        % (str(dynamic).lower(), str(request_only).lower(), payload)
    )


def _inject_before_article_end(page: str, article_id: str, panel: str) -> str:
    """Insert into one generated page article without depending on its internal presentation."""
    identity = 'id="%s"' % article_id
    identity_at = page.find(identity)
    article_at = page.rfind("<article", 0, identity_at + 1)
    if identity_at < 0 or article_at < 0:
        raise ValueError("Unified %s article is unavailable" % article_id)

    depth = 0
    for match in re.finditer(r"</?article\b[^>]*>", page[article_at:], flags=re.IGNORECASE):
        token = match.group(0)
        if token.startswith("</"):
            depth -= 1
            if depth == 0:
                insert_at = article_at + match.start()
                return page[:insert_at] + panel + page[insert_at:]
        else:
            depth += 1
    raise ValueError("Unified %s article boundary is incomplete" % article_id)


def inject_relation_inbox(page: str, capture: Mapping[str, Any], *, dynamic: bool) -> str:
    """Inject Personal local-confirmation and Team request-only views without adding navigation."""
    if 'data-relation-inbox' in page:
        raise ValueError("relation inbox is already present")
    if "</style>" not in page or "</body>" not in page:
        raise ValueError("Unified Personal/Team composition markers are unavailable")
    result = page.replace("</style>", RELATION_INBOX_CSS + "</style>", 1)
    result = _inject_before_article_end(
        result,
        "personal-observatory",
        _panel(capture, dynamic=dynamic, request_only=False),
    )
    result = _inject_before_article_end(
        result,
        "team-observatory",
        _panel(capture, dynamic=False, request_only=True),
    )
    return result.replace("</body>", "<script>" + RELATION_INBOX_JS + "</script></body>", 1)


__all__ = ["RELATION_INBOX_CSS", "RELATION_INBOX_JS", "inject_relation_inbox"]
