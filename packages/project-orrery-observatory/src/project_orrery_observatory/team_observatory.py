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
 border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(127,176,255,.09),transparent 66%)}
.to-kicker{display:block;color:var(--to-blue);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;
 letter-spacing:.14em;text-transform:uppercase}.to-head h2{font-size:27px;margin:5px 0}.to-head p{margin:0;color:var(--mut);font-size:12.5px;max-width:760px}
.to-boundary{align-self:start;border:1px solid var(--line);border-radius:7px;padding:7px 10px;color:var(--mut);font-size:10px;font-weight:650}
.to-boundary::before{content:"● ";color:var(--to-green)}
.to-onboarding{padding:24px}.to-onboarding[hidden],.to-workspace[hidden],.to-history[hidden]{display:none}.to-onboarding h3{font-size:15px;margin:0 0 5px}
.to-onboarding>p{margin:0 0 18px;color:var(--mut);font-size:12px;max-width:760px}.to-flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;
 align-items:stretch;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--line);gap:1px}.to-step{padding:16px;background:var(--bg2)}
.to-step small{display:block;color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em}.to-step b{display:block;margin:5px 0;font-size:14px}.to-step span{display:block;color:var(--mut);font-size:10.5px}.to-arrow{display:grid;place-items:center;background:var(--bg2);color:var(--to-blue);padding:0 10px}
.to-safe{display:grid;grid-template-columns:1fr 1fr;margin-top:14px;border:1px solid var(--line);border-radius:10px;overflow:hidden}.to-safe>div{padding:13px 15px;background:var(--bg2)}
.to-safe>div+div{border-left:1px solid var(--line)}.to-safe b{display:block;font-size:11.5px}.to-safe span{display:block;margin-top:4px;color:var(--mut);font-size:10.5px}
.to-action{appearance:none;border:1px solid var(--line);border-radius:7px;background:var(--bg3);color:var(--fg);padding:9px 12px;
 font:700 10.5px/1.2 inherit;cursor:pointer}.to-action:hover:not(:disabled){border-color:var(--to-blue);color:var(--to-blue)}.to-action:focus-visible{outline:2px solid var(--to-blue);outline-offset:2px}
.to-action.primary{background:var(--to-blue);border-color:var(--to-blue);color:#07111f}.to-action.danger{color:var(--to-red)}.to-action:disabled{opacity:.42;cursor:not-allowed}
.to-onboarding .to-action{margin-top:15px}.to-brief{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr);gap:22px;padding:22px 24px;border-bottom:1px solid var(--line)}
.to-brief-label,.to-section-label{color:var(--to-blue);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.12em;text-transform:uppercase}
.to-brief h3{margin:6px 0 5px;font-size:18px;line-height:1.35}.to-brief p{margin:0;color:var(--mut);font-size:11.5px;line-height:1.6}
.to-signals{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--line)}
.to-signal{padding:12px 13px;background:var(--bg2);min-width:0}.to-signal small{display:block;color:var(--mut);font-size:9px}.to-signal b{display:block;margin-top:4px;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.to-actions{padding:17px 24px;border-bottom:1px solid var(--line);background:var(--bg2)}.to-actions-head{display:flex;justify-content:space-between;align-items:end;gap:14px;margin-bottom:10px}
.to-actions-head h3{margin:4px 0 0;font-size:13px}.to-actions-head span{color:var(--mut);font-size:10px}.to-action-strip{display:flex;flex-wrap:wrap;gap:7px}
.to-grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(270px,.72fr)}.to-main,.to-side{min-width:0;padding:20px 24px}.to-side{border-left:1px solid var(--line);background:var(--bg2)}
.to-section+.to-section{margin-top:22px}.to-section-head{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:9px}.to-section-head h3{margin:0;font-size:13px}.to-section-head span{color:var(--mut);font-size:10px}
.to-member{border-top:1px solid var(--line)}.to-member>summary{display:grid;grid-template-columns:minmax(170px,1fr) auto;gap:12px;align-items:center;padding:12px 2px;cursor:pointer;list-style:none}
.to-member>summary::-webkit-details-marker{display:none}.to-member-title h4{margin:0;font-size:12.5px}.to-member-title small{display:block;margin-top:3px;color:var(--mut);font-size:9.5px}.to-member code{overflow:hidden;text-overflow:ellipsis}.to-caps{color:var(--mut);font-size:9.5px}.to-worktable{border-top:1px solid var(--line)}
.to-workrow{display:grid;grid-template-columns:minmax(190px,1.15fr) minmax(170px,1fr);gap:14px;padding:12px 2px;border-bottom:1px solid var(--line);font-size:10px;align-items:center}.to-work-title b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.to-work-title small,.to-work-state small{display:block;margin-top:3px;color:var(--mut);font-size:9.5px}.to-presence{font-weight:800}.to-presence.online{color:var(--to-green)}.to-presence.offline,.to-presence.stale-unknown{color:var(--to-amber)}.to-presence.unavailable,.to-presence.unknown{color:var(--mut)}
.to-request{border-top:1px solid var(--line);padding:12px 0}.to-request-head{display:flex;justify-content:space-between;gap:10px;align-items:start}.to-request b{font-size:11px}.to-request-status{color:var(--to-amber);font-size:9.5px;text-align:right}.to-request-status.done{color:var(--mut)}.to-request p{margin:5px 0;color:var(--mut);font-size:10px;line-height:1.5}.to-request-meta{color:var(--mut);font-size:9px}.to-request-actions{display:flex;gap:6px;margin-top:8px}.to-request .to-action{padding:7px 10px;font-size:9.5px}
.to-history{margin-top:13px;border-top:1px solid var(--line);padding-top:10px}.to-history>summary{cursor:pointer;color:var(--mut);font-size:10.5px}.to-history .to-request{opacity:.78}
.to-diagnostics{border-top:1px solid var(--line);background:var(--bg2)}.to-diagnostics>summary{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:14px 24px;cursor:pointer;list-style:none}.to-diagnostics>summary::-webkit-details-marker{display:none}.to-diagnostics>summary b{font-size:11.5px}.to-diagnostics>summary span{display:block;margin-top:3px;color:var(--mut);font-size:9.5px}.to-diagnostics>summary em{color:var(--to-blue);font-style:normal;font-size:10px}.to-diagnostics[open]>summary{border-bottom:1px solid var(--line)}
.to-statusline{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:1px;background:var(--line)}.to-statusline>div{min-width:0;padding:11px 13px;background:var(--bg)}.to-statusline small{display:block;color:var(--mut);font:700 8.5px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.07em;text-transform:uppercase}.to-statusline b{display:block;margin-top:4px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.to-controlbar{display:flex;flex-wrap:wrap;align-items:center;gap:7px;padding:12px 24px}.to-controlbar .to-spacer{flex:1}.to-mode{font:700 10px/1.2 "Cascadia Code",Consolas,monospace;color:var(--to-green);padding-right:8px}
.to-privacy{border-top:1px solid var(--line);padding:12px 24px;color:var(--mut);font-size:10.5px;line-height:1.55}.to-privacy b{color:var(--fg)}.to-empty{padding:13px 0;color:var(--mut);font-size:11px;border-top:1px solid var(--line)}
.to-notice{min-height:34px;padding:10px 24px;border-top:1px solid var(--line);color:var(--mut);font-size:10.5px}.to-notice.error{color:var(--to-red)}
@media(max-width:900px){.to-brief,.to-grid{grid-template-columns:1fr}.to-side{border-left:0;border-top:1px solid var(--line)}.to-statusline{grid-template-columns:repeat(3,1fr)}}
@media(max-width:640px){.to-shell{margin:0 -18px 24px;border-left:0;border-right:0;border-radius:0}.to-head{grid-template-columns:1fr;padding:18px}.to-boundary{justify-self:start}.to-onboarding,.to-brief,.to-actions,.to-main,.to-side{padding:17px 18px}.to-flow{grid-template-columns:1fr}.to-arrow{padding:5px;transform:rotate(90deg)}.to-safe{grid-template-columns:1fr}.to-safe>div+div{border-left:0;border-top:1px solid var(--line)}
 .to-signals{grid-template-columns:1fr 1fr}.to-actions-head{align-items:start;flex-direction:column}.to-action{min-height:40px}.to-action-strip .to-action{flex:1 1 calc(50% - 7px)}.to-statusline{grid-template-columns:1fr 1fr}.to-workrow{grid-template-columns:1fr}.to-member>summary{grid-template-columns:1fr auto}.to-member>summary code{grid-column:1/-1}.to-diagnostics>summary,.to-controlbar,.to-privacy,.to-notice{padding-left:18px;padding-right:18px}.to-controlbar .to-spacer{display:none}}
@media(prefers-reduced-motion:reduce){.to-shell *{scroll-behavior:auto!important;transition:none!important}}
"""


TEAM_OBSERVATORY_JS = r"""
(function(){
  const page=document.getElementById('team-observatory'); if(!page) return;
  const q=(s)=>page.querySelector(s), qa=(s)=>Array.from(page.querySelectorAll(s));
  const text=(el,value)=>{if(el) el.textContent=value==null?'Unknown':String(value)};
  const node=(tag,cls,value)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(value!=null)el.textContent=String(value);return el};
  const presenceLabels={online:'在线',offline:'离线','stale-unknown':'状态已过期',unknown:'状态未知',unavailable:'暂不可用'};
  const phaseLabels={created:'已创建，尚未开始',planning:'正在规划',implementing:'正在实现',validating:'正在验证','review-ready':'等待审查',integrated:'已集成',closed:'已结束'};
  const requestLabels={'pause-workstream':'请求暂停任务',cleanup:'请求本机评估工作区维护'};
  const requestStatusLabels={'pending-local-confirmation':'等待你确认','accepted-locally':'已在本机接受（未执行）','rejected-locally':'已在本机拒绝'};
  const dateLabel=(value)=>{if(!value)return'时间未知';const date=new Date(value);if(Number.isNaN(date.getTime()))return String(value);return new Intl.DateTimeFormat('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(date)};
  const presenceNote=(value)=>value==='stale-unknown'?'心跳关闭或最近状态已过期':value==='unknown'?'证据不足，不能判断是否在线':value==='unavailable'?'当前无法读取该成员状态':'来自最近一次团队状态投影';
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
    text(q('[data-team-member-note]'),members.length<=1?'目前只有你的本机状态；其他成员接入与自动发现仍未实现。':'按成员查看其最近共享的任务状态；过期快照不会冒充实时在线。');
    if(!members.length){root.append(node('div','to-empty','还没有可用的成员状态。当前不能据此判断团队是否空闲。'));return}
    members.forEach(member=>{const details=node('details','to-member');details.open=true;const summary=node('summary');
      const title=node('div','to-member-title');title.append(node('h4',null,member.member_id==='local-owner'?'你（本机成员）':member.member_id),node('small',null,member.member_id));
      summary.append(title,node('span','to-caps',(member.capabilities||[]).join(' · ')||'member'));details.append(summary);
      const table=node('div','to-worktable');const streams=member.workstreams||[];
      if(!streams.length)table.append(node('div','to-empty','该成员还没有共享可见的工作任务。'));
      streams.forEach(work=>{const row=node('div','to-workrow');
        const visibility=(work.reported_workstream||{}).visibility||'Local-only';const subsystem=(work.scope||{}).primary_subsystem_id&&((work.scope||{}).primary_subsystem_id!=='unmapped')?'关联模块：'+work.scope.primary_subsystem_id:'尚未关联项目模块';
        const workTitle=node('div','to-work-title');workTitle.append(node('b',null,work.workstream_id),node('small',null,subsystem+' · '+visibility+' · r'+work.revision));
        const workState=node('div','to-work-state');workState.append(node('span','to-presence '+work.presence,presenceLabels[work.presence]||'状态未知'),node('small',null,(phaseLabels[(work.reported_workstream||{}).lifecycle_phase]||(work.reported_workstream||{}).lifecycle_phase||'阶段未知')+' · '+presenceNote(work.presence)));
        row.append(workTitle,workState);table.append(row)});
      details.append(table);root.append(details)});
  }
  function requestItem(request,done){const item=node('div','to-request');const head=node('div','to-request-head');
    head.append(node('b',null,requestLabels[request.request_kind]||request.request_kind),node('span','to-request-status'+(done?' done':''),requestStatusLabels[request.status]||request.status));item.append(head);
    const summary=request.summary==='Pause at the next local safe point'?'在下一个安全节点暂停该任务。':request.summary;item.append(node('p',null,summary));
    item.append(node('div','to-request-meta',(request.requester_id||'未知成员')+' → '+(request.target_member_id||'本机成员')+' · '+(request.workstream_id||'任务未知')+' · '+dateLabel(request.created_at)));
    if(!done){const actions=node('div','to-request-actions');[['accept','接受请求'],['reject','拒绝请求']].forEach(([decision,label])=>{const button=node('button','to-action'+(decision==='reject'?' danger':''),label);button.type='button';button.dataset.requestDecision=decision;button.dataset.requestId=request.request_id;actions.append(button)});item.append(actions)}return item;
  }
  function renderRequests(requests){const pendingRoot=q('[data-team-pending-requests]'),historyRoot=q('[data-team-request-history-list]'),history=q('[data-team-request-history]');pendingRoot.replaceChildren();historyRoot.replaceChildren();
    const pending=requests.filter(request=>request.status==='pending-local-confirmation'),done=requests.filter(request=>request.status!=='pending-local-confirmation');
    text(q('[data-team-pending-count]'),pending.length);text(q('[data-team-history-summary]'),'已处理请求（'+done.length+'）');
    if(!pending.length)pendingRoot.append(node('div','to-empty','目前没有需要你处理的请求。'));
    pending.forEach(request=>pendingRoot.append(requestItem(request,false)));done.forEach(request=>historyRoot.append(requestItem(request,true)));history.hidden=!done.length;
  }
  function renderBrief(value){const config=value.config||{},running=!!(value.coordinator&&value.coordinator.running),projection=value.projection||{},members=projection.members||[];
    const workstreams=members.reduce((count,member)=>count+(member.workstreams||[]).length,0),pending=(value.requests||[]).filter(request=>request.status==='pending-local-confirmation').length,outbox=value.outbox_count||0;
    const externalRegistered=!running&&config.runtime_status==='team-runtime-active';let summary,guidance;
    if(externalRegistered){summary='检测到另一个本机协作服务登记，当前页面不能直接控制它。';guidance='请回到原 Team 页面正常停止；如果原进程已经退出，可在技术诊断中退出 Team Mode 后重新启用。'}
    else if(!running){summary='Team Mode 已启用，但本机协作服务还没有启动。';guidance='先启动本机协作服务；这只会监听 127.0.0.1，不会把执行权交给其他成员。'}
    else if(!config.sharing_enabled){summary='协作服务正在运行，但项目状态尚未开始共享。';guidance='开启项目状态共享后，其他成员才能看到你主动提供的最小元数据。源码、对话和未 push diff 不会上传。'}
    else if(members.length<=1){summary='本机状态已经准备好，目前还没有其他成员接入。';guidance=outbox?'还有 '+outbox+' 项本机状态等待同步。':'当前没有待同步状态；自动发现与真实多机接入仍属于后续能力。'}
    else{summary='当前可见 '+members.length+' 名成员、'+workstreams+' 个工作任务。';guidance=pending?'有 '+pending+' 个请求等待你在本机确认。':'目前没有需要你处理的团队请求。'}
    if(running&&!(config.heartbeat&&config.heartbeat.enabled))guidance+=' 在线状态广播已关闭，因此“状态已过期／未知”是预期结果。';
    text(q('[data-team-summary]'),summary);text(q('[data-team-guidance]'),guidance);text(q('[data-team-service]'),running?'本机服务运行中':externalRegistered?'其他本机服务登记':'尚未启动');text(q('[data-team-member-count]'),members.length);text(q('[data-team-pending-count]'),pending);qa('[data-team-outbox]').forEach(element=>text(element,outbox));
  }
  function render(value){state=value;const config=value.config||{};const enabled=!!config.enabled;const running=!!(value.coordinator&&value.coordinator.running);
    const externalRegistered=!running&&config.runtime_status==='team-runtime-active';
    q('[data-team-onboarding]').hidden=enabled;q('[data-team-workspace]').hidden=!enabled;
    text(q('[data-team-mode]'),enabled?'TEAM · OPT-IN':'PERSONAL · ZERO NETWORK');text(q('[data-team-runtime]'),config.runtime_status||'personal-zero-network');
    text(q('[data-team-member]'),config.member_id||'implicit local');text(q('[data-team-host]'),config.host_id||'not configured');
    text(q('[data-team-sharing]'),config.sharing_enabled?'sharing':'off');text(q('[data-team-heartbeat]'),config.heartbeat&&config.heartbeat.enabled?'on':'off');
    text(q('[data-team-last-seen]'),value.projection&&value.projection.generated_at||'Unavailable');text(q('[data-team-outbox]'),value.outbox_count||0);
    qa('[data-team-action]').forEach(button=>{const action=button.dataset.teamAction;button.disabled=(action==='enable'&&enabled)||(action==='disable'&&!enabled)||(action==='start'&&(!enabled||running||externalRegistered))||(action==='stop'&&!running)||(['heartbeat','sharing','capture','sync','request-create','maintenance-request'].includes(action)&&!enabled)||(action==='sync'&&!running)});
    text(q('[data-action-start]'),running?'本机协作服务运行中':externalRegistered?'其他本机服务占用中':'启动本机协作服务');text(q('[data-action-heartbeat]'),config.heartbeat&&config.heartbeat.enabled?'关闭在线状态':'开启在线状态');text(q('[data-action-sharing]'),config.sharing_enabled?'暂停项目状态共享':'开始共享项目状态');text(q('[data-action-sync]'),(value.outbox_count||0)?'同步 '+value.outbox_count+' 项更新':'立即同步');
    renderBrief(value);renderMembers(value.projection);renderRequests(value.requests||[]);
  }
  async function refresh(){try{render(await api('/team/api/status'));q('[data-team-notice]').className='to-notice';text(q('[data-team-notice]'),'本机状态已刷新；没有返回凭据或源码内容。')}catch(error){q('[data-team-notice]').className='to-notice error';text(q('[data-team-notice]'),error.message)}}
  page.addEventListener('click',async(event)=>{const button=event.target.closest('button');if(!button)return;let path=null,body={};
    if(button.dataset.teamAction){path='/team/api/'+button.dataset.teamAction}else if(button.dataset.requestDecision){path='/team/api/request/decision';body={request_id:button.dataset.requestId,decision:button.dataset.requestDecision}}else{return}
    button.disabled=true;try{await api(path,body);await refresh()}catch(error){const action=button.dataset.teamAction||button.dataset.requestDecision;const friendly={start:'无法启动本机协作服务。可能存在其他 Team 页面或失效的本机登记，请按上方说明恢复。',disable:'无法退出 Team Mode。请先关闭其他本机 Team 页面后重试。',sync:'同步没有完成；本机待同步状态仍会保留。',accept:'请求尚未确认，请刷新后重试。',reject:'请求尚未拒绝，请刷新后重试。'}[action]||'本机操作没有完成；没有执行远程命令。';q('[data-team-notice]').className='to-notice error';text(q('[data-team-notice]'),friendly);button.disabled=false}});
  refresh();
})();
"""


def render_team_observatory_panel() -> str:
    return (
        '<article class="page wide" id="team-observatory" data-kind="team-observatory" '
        'data-title="Team Observatory" data-authority="derived-read-only">'
        '<section class="to-shell"><header class="to-head"><div><span class="to-kicker">TEAM OBSERVATORY · LOCAL CONTROL</span>'
        '<h2>团队指挥台</h2><p>先看谁在推进、哪里需要你处理；所有请求仍由目标成员在自己的电脑上确认。</p></div>'
        '<span class="to-boundary">只共享状态 · 请求需本机确认</span></header>'
        '<section class="to-onboarding" data-team-onboarding><h3>Personal Mode 正在保护默认体验</h3>'
        '<p>当前不会启动 Team socket。启用项目身份与启动 Coordinator 是两个独立动作；LAN bind 继续留在单独显式开关之后。</p>'
        '<div class="to-flow"><div class="to-step"><small>01 · DEFAULT</small><b>Personal</b><span>零监听、零发现、零同步</span></div><div class="to-arrow">→</div>'
        '<div class="to-step"><small>02 · LOCAL WRITE</small><b>Enable Team</b><span>只写 Git-private 配置，不开端口</span></div><div class="to-arrow">→</div>'
        '<div class="to-step"><small>03 · EXPLICIT RUNTIME</small><b>Serve locally</b><span>仅 127.0.0.1；关闭 UI 即停止</span></div></div>'
        '<div class="to-safe"><div><b>中央能做什么</b><span>读取版本化 metadata、聚合 Member → Workstream、发送 request。</span></div>'
        '<div><b>中央不能做什么</b><span>不能执行 shell／Agent／merge／delete；accept/reject 也只写本机 receipt。</span></div></div>'
        '<button class="to-action primary" type="button" data-team-action="enable">在本机启用 Team Mode</button></section>'
        '<section class="to-workspace" data-team-workspace hidden>'
        '<section class="to-brief"><div><span class="to-brief-label">现在的情况</span><h3 data-team-summary>正在读取本机团队状态…</h3><p data-team-guidance>状态不足时会保留 Unknown，不会推测成员在线或任务完成。</p></div>'
        '<div class="to-signals"><div class="to-signal"><small>团队连接</small><b data-team-service>尚未启动</b></div><div class="to-signal"><small>可见成员</small><b><span data-team-member-count>0</span> 人</b></div><div class="to-signal"><small>等待你处理</small><b><span data-team-pending-count>0</span> 项</b></div><div class="to-signal"><small>等待同步</small><b><span data-team-outbox>0</span> 项</b></div></div></section>'
        '<section class="to-actions"><div class="to-actions-head"><div><span class="to-section-label">建议操作</span><h3>按当前状态完成下一步</h3></div><span>这里的操作只影响你的本机节点</span></div><div class="to-action-strip">'
        '<button class="to-action primary" type="button" data-team-action="start" data-action-start>启动本机协作服务</button><button class="to-action" type="button" data-team-action="sharing" data-action-sharing>开始共享项目状态</button>'
        '<button class="to-action" type="button" data-team-action="capture">采集本机状态</button><button class="to-action" type="button" data-team-action="sync" data-action-sync>立即同步</button></div></section>'
        '<div class="to-grid"><main class="to-main"><section class="to-section"><div class="to-section-head"><h3>成员与工作任务</h3><span data-team-member-note>按成员查看最近共享的 Workstream</span></div><div data-team-members></div></section></main>'
        '<aside class="to-side"><section class="to-section" data-team-requests><div class="to-section-head"><h3>待处理请求</h3><span>确认只记录决定，不会自动执行</span></div><div data-team-pending-requests></div>'
        '<details class="to-history" data-team-request-history hidden><summary data-team-history-summary>已处理请求（0）</summary><div data-team-request-history-list></div></details></section></aside></div>'
        '<details class="to-diagnostics"><summary><div><b>本机控制与技术诊断</b><span>Coordinator、Host、在线状态、内部 ID 与测试入口</span></div><em>展开</em></summary><div>'
        '<div class="to-statusline"><div><small>Mode</small><b data-team-runtime>Unknown</b></div><div><small>Member</small><b data-team-member>Unknown</b></div>'
        '<div><small>Host</small><b data-team-host>Unknown</b></div><div><small>Sharing / Heartbeat</small><b><span data-team-sharing>off</span> · <span data-team-heartbeat>off</span></b></div>'
        '<div><small>Last seen</small><b data-team-last-seen>Unavailable</b></div><div><small>Outbox</small><b data-team-outbox>0</b></div></div>'
        '<div class="to-controlbar"><span class="to-mode" data-team-mode>TEAM</span><button class="to-action" type="button" data-team-action="stop">暂停团队连接</button>'
        '<button class="to-action" type="button" data-team-action="heartbeat" data-action-heartbeat>开启在线状态</button><button class="to-action" type="button" data-team-action="maintenance-request">请求成员本机评估维护</button><button class="to-action" type="button" data-team-action="request-create">创建测试请求</button><span class="to-spacer"></span><button class="to-action danger" type="button" data-team-action="disable">退出 Team Mode</button></div>'
        '<div class="to-privacy"><b>只共享最小元数据</b><br>不发送 Prompt、回答、reasoning、transcript、源码正文、未 push diff、member token、API key 或 credential。最后快照只按 Core TTL 投影，不冒充实时在线。</div></div></details></section>'
        '<div class="to-notice" data-team-notice>正在读取本机团队状态…</div></section></article>'
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
