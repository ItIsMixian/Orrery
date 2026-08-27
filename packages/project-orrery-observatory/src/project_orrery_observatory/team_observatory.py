"""Presentation-only Team Observatory sibling page.

The page consumes the Core-owned ``team-read-only-projection`` contract.  It
contains no Team permission, revision, TTL, or request-decision policy.
"""

from __future__ import annotations

import html
import json
from typing import Any, Mapping


TEAM_UI_SCHEMA = "project-orrery-team-observatory-v1"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


TEAM_OBSERVATORY_CSS = r"""
.to-shell{--to-green:#63d6cf;--to-amber:#f2ba5e;--to-red:#ff786b;--to-blue:#7fb0ff;
 margin:0 0 24px;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--bg)}
.to-head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;padding:22px 24px 18px;
 border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(127,176,255,.08),transparent 62%)}
.to-kicker{display:block;color:var(--to-blue);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;
 letter-spacing:.14em;text-transform:uppercase}.to-head h2{font-size:26px;margin:4px 0}.to-head p{margin:0;color:var(--mut);font-size:12.5px}
.to-boundary{align-self:start;border:1px solid var(--line);border-radius:7px;padding:7px 10px;color:var(--mut);
 font:600 10px/1.3 "Cascadia Code",Consolas,monospace}.to-boundary::before{content:"● ";color:var(--to-green)}
.to-onboarding{padding:24px}.to-onboarding[hidden],.to-workspace[hidden]{display:none}.to-onboarding h3{font-size:15px;margin:0 0 5px}
.to-onboarding>p{margin:0 0 18px;color:var(--mut);font-size:12px;max-width:760px}.to-flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;
 align-items:stretch;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--line);gap:1px}.to-step{padding:16px;background:var(--bg2)}
.to-step small{display:block;color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em}.to-step b{display:block;margin:5px 0;font-size:14px}.to-step span{display:block;color:var(--mut);font-size:10.5px}.to-arrow{display:grid;place-items:center;background:var(--bg2);color:var(--to-blue);padding:0 10px}
.to-safe{display:grid;grid-template-columns:1fr 1fr;margin-top:14px;border:1px solid var(--line);border-radius:10px;overflow:hidden}.to-safe>div{padding:13px 15px;background:var(--bg2)}
.to-safe>div+div{border-left:1px solid var(--line)}.to-safe b{display:block;font-size:11.5px}.to-safe span{display:block;margin-top:4px;color:var(--mut);font-size:10.5px}
.to-action{appearance:none;border:1px solid var(--line);border-radius:7px;background:var(--bg3);color:var(--fg);padding:8px 12px;
 font:700 10.5px/1.2 inherit;cursor:pointer}.to-action:hover:not(:disabled){border-color:var(--to-blue);color:var(--to-blue)}.to-action:focus-visible{outline:2px solid var(--to-blue);outline-offset:2px}
.to-action.primary{background:var(--to-blue);border-color:var(--to-blue);color:#07111f}.to-action.danger{color:var(--to-red)}.to-action:disabled{opacity:.42;cursor:not-allowed}
.to-onboarding .to-action{margin-top:15px}.to-toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:7px;padding:12px 24px;border-bottom:1px solid var(--line);background:var(--bg2)}
.to-toolbar .to-spacer{flex:1}.to-mode{font:700 10px/1.2 "Cascadia Code",Consolas,monospace;color:var(--to-green);padding-right:8px}
.to-statusline{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:1px;background:var(--line);border-bottom:1px solid var(--line)}
.to-statusline>div{min-width:0;padding:11px 13px;background:var(--bg)}.to-statusline small{display:block;color:var(--mut);font:700 8.5px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.07em;text-transform:uppercase}
.to-statusline b{display:block;margin-top:4px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.to-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(300px,.75fr)}
.to-main,.to-side{min-width:0;padding:20px 24px}.to-side{border-left:1px solid var(--line);background:var(--bg2)}.to-section+.to-section{margin-top:22px}.to-section-head{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:9px}
.to-section-head h3{margin:0;font-size:13px}.to-section-head span{color:var(--mut);font-size:10px}.to-member{border-top:1px solid var(--line)}.to-member>summary{display:grid;grid-template-columns:minmax(120px,.8fr) 1fr auto;gap:12px;align-items:center;padding:11px 2px;cursor:pointer;list-style:none}
.to-member>summary::-webkit-details-marker{display:none}.to-member h4{margin:0;font-size:12.5px}.to-member code{overflow:hidden;text-overflow:ellipsis}.to-caps{color:var(--mut);font-size:9.5px}.to-worktable{border-top:1px solid var(--line)}
.to-workrow{display:grid;grid-template-columns:minmax(130px,1fr) 90px 90px minmax(110px,.8fr) 90px;gap:10px;padding:10px 2px;border-bottom:1px solid var(--line);font-size:10px;align-items:center}.to-workrow b,.to-workrow code{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.to-presence{font-weight:800;text-transform:uppercase}.to-presence.online{color:var(--to-green)}.to-presence.offline,.to-presence.stale-unknown{color:var(--to-amber)}.to-presence.unavailable,.to-presence.unknown{color:var(--mut)}
.to-request{border-top:1px solid var(--line);padding:10px 0}.to-request-head{display:flex;justify-content:space-between;gap:10px}.to-request b{font-size:11px}.to-request p{margin:4px 0;color:var(--mut);font-size:10px}.to-request-actions{display:flex;gap:6px;margin-top:7px}.to-request .to-action{padding:6px 9px;font-size:9.5px}
.to-privacy{border-top:1px solid var(--line);padding-top:11px;color:var(--mut);font-size:10.5px;line-height:1.55}.to-privacy b{color:var(--fg)}.to-empty{padding:13px 0;color:var(--mut);font-size:11px;border-top:1px solid var(--line)}
.to-notice{min-height:34px;padding:10px 24px;border-top:1px solid var(--line);color:var(--mut);font-size:10.5px}.to-notice.error{color:var(--to-red)}
@media(max-width:900px){.to-grid{grid-template-columns:1fr}.to-side{border-left:0;border-top:1px solid var(--line)}.to-statusline{grid-template-columns:repeat(3,1fr)}}
@media(max-width:640px){.to-shell{margin:0 -18px 24px;border-left:0;border-right:0;border-radius:0}.to-head{grid-template-columns:1fr;padding:18px}.to-boundary{justify-self:start}.to-onboarding,.to-main,.to-side{padding:17px 18px}.to-flow{grid-template-columns:1fr}.to-arrow{padding:5px;transform:rotate(90deg)}.to-safe{grid-template-columns:1fr}.to-safe>div+div{border-left:0;border-top:1px solid var(--line)}
 .to-toolbar{padding:11px 18px}.to-toolbar .to-spacer{display:none}.to-action{min-height:38px}.to-statusline{grid-template-columns:1fr 1fr}.to-workrow{grid-template-columns:1fr 1fr}.to-workrow>*:first-child{grid-column:1/-1}.to-member>summary{grid-template-columns:1fr auto}.to-member>summary code{grid-column:1/-1}.to-notice{padding:10px 18px}}
@media(prefers-reduced-motion:reduce){.to-shell *{scroll-behavior:auto!important;transition:none!important}}
"""


TEAM_OBSERVATORY_JS = r"""
(function(){
  const page=document.getElementById('team-observatory'); if(!page) return;
  const q=(s)=>page.querySelector(s), qa=(s)=>Array.from(page.querySelectorAll(s));
  const text=(el,value)=>{if(el) el.textContent=value==null?'Unknown':String(value)};
  const node=(tag,cls,value)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(value!=null)el.textContent=String(value);return el};
  let state=null;
  async function api(path,body){
    const options={method:body===undefined?'GET':'POST',headers:{'Accept':'application/json'}};
    if(body!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body)}
    const response=await fetch(path,options); const value=await response.json();
    if(!response.ok) throw new Error(value.error||'Local Team operation failed'); return value;
  }
  function renderMembers(projection){
    const root=q('[data-team-members]');root.replaceChildren();
    const members=(projection&&projection.members)||[];
    if(!members.length){root.append(node('div','to-empty','No shared Member snapshot · Unknown / Unavailable'));return}
    members.forEach(member=>{const details=node('details','to-member');details.open=true;const summary=node('summary');
      summary.append(node('h4',null,member.member_id),node('code',null,(member.active_host&&member.active_host.host_id)||'Host Unknown'),node('span','to-caps',(member.capabilities||[]).join(' · ')));details.append(summary);
      const table=node('div','to-worktable');const streams=member.workstreams||[];
      if(!streams.length)table.append(node('div','to-empty','No shared Workstream · Unavailable'));
      streams.forEach(work=>{const row=node('div','to-workrow');
        row.append(node('b',null,work.workstream_id),node('span','to-presence '+work.presence,work.presence),node('span',null,(work.reported_workstream||{}).lifecycle_phase||'Unknown'),node('code',null,(work.scope||{}).primary_subsystem_id||'Unmapped'),node('span',null,'r'+work.revision));table.append(row)});
      details.append(table);root.append(details)});
  }
  function renderRequests(requests){const root=q('[data-team-requests]');root.replaceChildren();
    if(!requests.length){root.append(node('div','to-empty','Request inbox empty'));return}
    requests.forEach(request=>{const item=node('div','to-request');const head=node('div','to-request-head');head.append(node('b',null,request.request_kind),node('span',null,request.status));item.append(head,node('p',null,request.summary));
      if(request.status==='pending-local-confirmation'){const actions=node('div','to-request-actions');['accept','reject'].forEach(decision=>{const button=node('button','to-action'+(decision==='reject'?' danger':''),decision==='accept'?'Accept locally':'Reject locally');button.type='button';button.dataset.requestDecision=decision;button.dataset.requestId=request.request_id;actions.append(button)});item.append(actions)}root.append(item)});
  }
  function render(value){state=value;const config=value.config||{};const enabled=!!config.enabled;const running=!!(value.coordinator&&value.coordinator.running);
    q('[data-team-onboarding]').hidden=enabled;q('[data-team-workspace]').hidden=!enabled;
    text(q('[data-team-mode]'),enabled?'TEAM · OPT-IN':'PERSONAL · ZERO NETWORK');text(q('[data-team-runtime]'),config.runtime_status||'personal-zero-network');
    text(q('[data-team-member]'),config.member_id||'implicit local');text(q('[data-team-host]'),config.host_id||'not configured');
    text(q('[data-team-sharing]'),config.sharing_enabled?'sharing':'off');text(q('[data-team-heartbeat]'),config.heartbeat&&config.heartbeat.enabled?'on':'off');
    text(q('[data-team-last-seen]'),value.projection&&value.projection.generated_at||'Unavailable');text(q('[data-team-outbox]'),value.outbox_count||0);
    qa('[data-team-action]').forEach(button=>{const action=button.dataset.teamAction;button.disabled=(action==='enable'&&enabled)||(action==='disable'&&!enabled)||(action==='start'&&(!enabled||running))||(action==='stop'&&!running)||(['heartbeat','sharing','capture','sync','request-create'].includes(action)&&!enabled)||(action==='sync'&&!running)});
    text(q('[data-action-heartbeat]'),config.heartbeat&&config.heartbeat.enabled?'Heartbeat off':'Heartbeat on');text(q('[data-action-sharing]'),config.sharing_enabled?'Sharing off':'Sharing on');
    renderMembers(value.projection);renderRequests(value.requests||[]);
  }
  async function refresh(){try{render(await api('/team/api/status'));q('[data-team-notice]').className='to-notice';text(q('[data-team-notice]'),'Local state refreshed · no secrets returned')}catch(error){q('[data-team-notice]').className='to-notice error';text(q('[data-team-notice]'),error.message)}}
  page.addEventListener('click',async(event)=>{const button=event.target.closest('button');if(!button)return;let path=null,body={};
    if(button.dataset.teamAction){path='/team/api/'+button.dataset.teamAction}else if(button.dataset.requestDecision){path='/team/api/request/decision';body={request_id:button.dataset.requestId,decision:button.dataset.requestDecision}}else{return}
    button.disabled=true;try{await api(path,body);await refresh()}catch(error){q('[data-team-notice]').className='to-notice error';text(q('[data-team-notice]'),error.message);button.disabled=false}});
  refresh();
})();
"""


def render_team_observatory_panel() -> str:
    return (
        '<article class="page wide" id="team-observatory" data-kind="team-observatory" '
        'data-title="Team Observatory" data-authority="derived-read-only">'
        '<section class="to-shell"><header class="to-head"><div><span class="to-kicker">TEAM OBSERVATORY · LOCAL CONTROL</span>'
        '<h2>团队协作，不交出执行权</h2><p>Member → Workstream 元数据投影；所有请求在目标成员本机确认。</p></div>'
        '<span class="to-boundary">LOOPBACK ONLY · METADATA ONLY · REQUEST ONLY</span></header>'
        '<section class="to-onboarding" data-team-onboarding><h3>Personal Mode 正在保护默认体验</h3>'
        '<p>当前不会启动 Team socket。启用项目身份与启动 Coordinator 是两个独立动作；LAN bind 继续留在单独显式开关之后。</p>'
        '<div class="to-flow"><div class="to-step"><small>01 · DEFAULT</small><b>Personal</b><span>零监听、零发现、零同步</span></div><div class="to-arrow">→</div>'
        '<div class="to-step"><small>02 · LOCAL WRITE</small><b>Enable Team</b><span>只写 Git-private 配置，不开端口</span></div><div class="to-arrow">→</div>'
        '<div class="to-step"><small>03 · EXPLICIT RUNTIME</small><b>Serve locally</b><span>仅 127.0.0.1；关闭 UI 即停止</span></div></div>'
        '<div class="to-safe"><div><b>中央能做什么</b><span>读取版本化 metadata、聚合 Member → Workstream、发送 request。</span></div>'
        '<div><b>中央不能做什么</b><span>不能执行 shell／Agent／merge／delete；accept/reject 也只写本机 receipt。</span></div></div>'
        '<button class="to-action primary" type="button" data-team-action="enable">Enable Team locally</button></section>'
        '<section class="to-workspace" data-team-workspace hidden><div class="to-toolbar"><span class="to-mode" data-team-mode>TEAM</span>'
        '<button class="to-action" type="button" data-team-action="start">Start Coordinator</button><button class="to-action" type="button" data-team-action="stop">Stop Coordinator</button>'
        '<button class="to-action" type="button" data-team-action="heartbeat" data-action-heartbeat>Heartbeat on</button><button class="to-action" type="button" data-team-action="sharing" data-action-sharing>Sharing off</button>'
        '<span class="to-spacer"></span><button class="to-action" type="button" data-team-action="capture">Capture</button><button class="to-action" type="button" data-team-action="sync">Sync now</button>'
        '<button class="to-action" type="button" data-team-action="request-create">Create local request</button><button class="to-action danger" type="button" data-team-action="disable">Disable Team</button></div>'
        '<div class="to-statusline"><div><small>Mode</small><b data-team-runtime>Unknown</b></div><div><small>Member</small><b data-team-member>Unknown</b></div>'
        '<div><small>Host</small><b data-team-host>Unknown</b></div><div><small>Sharing / Heartbeat</small><b><span data-team-sharing>off</span> · <span data-team-heartbeat>off</span></b></div>'
        '<div><small>Last seen</small><b data-team-last-seen>Unavailable</b></div><div><small>Outbox</small><b data-team-outbox>0</b></div></div>'
        '<div class="to-grid"><main class="to-main"><section class="to-section"><div class="to-section-head"><h3>Member → Workstream</h3><span>Online / Offline / Stale / Unknown / Unavailable</span></div><div data-team-members></div></section></main>'
        '<aside class="to-side"><section class="to-section"><div class="to-section-head"><h3>Request inbox</h3><span>local receipt · execution false</span></div><div data-team-requests></div></section>'
        '<section class="to-section to-privacy"><b>Metadata-only privacy boundary</b><br>不发送 Prompt、回答、reasoning、transcript、源码正文、未 push diff、member token、API key 或 credential。最后快照只按 Core TTL 投影，不冒充实时在线。</section></aside></div></section>'
        '<div class="to-notice" data-team-notice>Loading local Team state…</div></section></article>'
    )


def inject_team_observatory(page: str) -> str:
    if 'id="team-observatory"' in page:
        raise ValueError("Team Observatory is already present")
    nav_marker = (
        '<a class="nav-item" data-target="personal-observatory">'
        '<span class="dot state"></span><span class="lbl">Personal Observatory</span></a>'
    )
    content_marker = '</main><aside class="toc" id="toc">'
    if nav_marker not in page or content_marker not in page or "</style>" not in page:
        raise ValueError("Personal Observatory composition markers are missing")
    result = page.replace("</style>", TEAM_OBSERVATORY_CSS + "</style>", 1)
    nav = (
        '<a class="nav-item" data-target="team-observatory">'
        '<span class="dot proposed"></span><span class="lbl">Team Observatory</span></a>'
    )
    result = result.replace(nav_marker, nav_marker + nav, 1)
    marker_index = result.index(nav_marker)
    group_index = result.rfind('<div class="nav-group">', 0, marker_index)
    if group_index < 0:
        raise ValueError("Overview navigation group is missing")
    result = (
        result[:group_index]
        + result[group_index:].replace(
            '<div class="nav-group">', '<div class="nav-group expanded">', 1
        )
    )
    result = result.replace(content_marker, render_team_observatory_panel() + content_marker, 1)
    script = '<script>' + TEAM_OBSERVATORY_JS + '</script>'
    return result.replace("</body>", script + "</body>", 1)


def safe_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
