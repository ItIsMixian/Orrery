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
.to-head{display:block;padding:22px 24px 18px;
 border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(127,176,255,.09),transparent 66%)}
.to-kicker{display:block;color:var(--to-blue);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;
 letter-spacing:.14em;text-transform:uppercase}.to-head h2{font-size:27px;margin:5px 0}.to-head p{margin:0;color:var(--mut);font-size:12.5px;max-width:760px}
.to-onboarding{padding:24px}.to-onboarding[hidden],.to-workspace[hidden],.to-history[hidden]{display:none}.to-onboarding h3{font-size:15px;margin:0 0 5px}
.to-onboarding>p{margin:0 0 18px;color:var(--mut);font-size:12px;max-width:760px}.to-flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;
 align-items:stretch;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--line);gap:1px}.to-step{padding:16px;background:var(--bg2)}
.to-step small{display:block;color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em}.to-step b{display:block;margin:5px 0;font-size:14px}.to-step span{display:block;color:var(--mut);font-size:10.5px}.to-arrow{display:grid;place-items:center;background:var(--bg2);color:var(--to-blue);padding:0 10px}
.to-safe{display:grid;grid-template-columns:1fr 1fr;margin-top:14px;border:1px solid var(--line);border-radius:10px;overflow:hidden}.to-safe>div{padding:13px 15px;background:var(--bg2)}
.to-safe>div+div{border-left:1px solid var(--line)}.to-safe b{display:block;font-size:11.5px}.to-safe span{display:block;margin-top:4px;color:var(--mut);font-size:10.5px}
.to-action{appearance:none;border:1px solid var(--line);border-radius:7px;background:var(--bg3);color:var(--fg);padding:9px 12px;
 font:700 10.5px/1.2 inherit;cursor:pointer}.to-action:hover:not(:disabled){border-color:var(--to-blue);color:var(--to-blue)}.to-action:focus-visible{outline:2px solid var(--to-blue);outline-offset:2px}
.to-action.primary{background:var(--to-blue);border-color:var(--to-blue);color:#07111f}.to-action.danger{color:var(--to-red)}.to-action:disabled{opacity:.42;cursor:not-allowed}
.to-onboarding .to-action{margin-top:15px}.to-overview{padding:16px 24px 14px;border-bottom:1px solid var(--line)}
.to-section-label{color:var(--to-blue);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.12em;text-transform:uppercase}
.to-signals{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--line)}
.to-signal{padding:12px 13px;background:var(--bg2);min-width:0}.to-signal small{display:block;color:var(--mut);font-size:9px}.to-signal b{display:block;margin-top:4px;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.to-essential{display:flex;align-items:center;gap:13px;margin-top:11px}.to-mode-state{min-width:155px}.to-mode-state small{display:block;color:var(--mut);font:700 8.5px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em;text-transform:uppercase}.to-mode-state b{display:block;margin-top:3px;font-size:11px}.to-command-note{min-width:0;flex:1;margin:0;color:var(--mut);font-size:10px;line-height:1.45}.to-essential-actions{display:flex;align-items:center;justify-content:flex-end;flex-wrap:wrap;gap:7px}.to-icon-action{width:36px;height:34px;padding:0;display:inline-grid;place-items:center;font-size:15px}
.to-actions{padding:17px 24px;border-bottom:1px solid var(--line);background:var(--bg2)}.to-actions-head{display:flex;justify-content:space-between;align-items:end;gap:14px;margin-bottom:10px}
.to-actions-head h3{margin:4px 0 0;font-size:13px}.to-actions-head span{color:var(--mut);font-size:10px}.to-action-strip{display:flex;flex-wrap:wrap;gap:7px}
.to-grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(270px,.72fr)}.to-main,.to-side{min-width:0;padding:20px 24px}.to-side{border-left:1px solid var(--line);background:var(--bg2)}
.to-section+.to-section{margin-top:22px}.to-section-head{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:9px}.to-section-head h3{margin:0;font-size:13px}.to-section-head span{color:var(--mut);font-size:10px}
.to-member{border-top:1px solid var(--line)}.to-member>summary{display:grid;grid-template-columns:minmax(170px,1fr) auto;gap:12px;align-items:center;padding:12px 2px;cursor:pointer;list-style:none}
.to-member>summary::-webkit-details-marker{display:none}.to-member-title h4{margin:0;font-size:12.5px}.to-member-title small{display:block;margin-top:3px;color:var(--mut);font-size:9.5px}.to-member code{overflow:hidden;text-overflow:ellipsis}.to-caps{color:var(--mut);font-size:9.5px}.to-worktable{border-top:1px solid var(--line)}
.to-workrow{display:grid;grid-template-columns:minmax(190px,1.15fr) minmax(170px,1fr);gap:14px;padding:12px 2px;border-bottom:1px solid var(--line);font-size:10px;align-items:center}.to-work-title b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.to-work-title small,.to-work-state small{display:block;margin-top:3px;color:var(--mut);font-size:9.5px}.to-presence{font-weight:800}.to-presence.online{color:var(--to-green)}.to-presence.offline,.to-presence.stale-unknown{color:var(--to-amber)}.to-presence.unavailable,.to-presence.unknown{color:var(--mut)}
.to-request{border-top:1px solid var(--line);padding:12px 0}.to-request-head{display:flex;justify-content:space-between;gap:10px;align-items:start}.to-request b{font-size:11px}.to-request-status{color:var(--to-amber);font-size:9.5px;text-align:right}.to-request-status.done{color:var(--mut)}.to-request p{margin:5px 0;color:var(--mut);font-size:10px;line-height:1.5}.to-request-meta{color:var(--mut);font-size:9px}.to-request-actions{display:flex;gap:6px;margin-top:8px}.to-request .to-action{padding:7px 10px;font-size:9.5px}
.to-history{margin-top:13px;border-top:1px solid var(--line);padding-top:10px}.to-history>summary{cursor:pointer;color:var(--mut);font-size:10.5px}.to-history .to-request{opacity:.78}
.to-statusline{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line)}.to-statusline>div{min-width:0;padding:11px 13px;background:var(--bg)}.to-statusline small{display:block;color:var(--mut);font:700 8.5px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.07em;text-transform:uppercase}.to-statusline b{display:block;margin-top:4px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.to-controlbar{display:flex;flex-wrap:wrap;align-items:center;gap:7px;padding:12px 24px}.to-controlbar .to-spacer{flex:1}.to-mode{font:700 10px/1.2 "Cascadia Code",Consolas,monospace;color:var(--to-green);padding-right:8px}
.to-privacy{border-top:1px solid var(--line);padding:12px 24px;color:var(--mut);font-size:10.5px;line-height:1.55}.to-privacy b{color:var(--fg)}.to-empty{padding:13px 0;color:var(--mut);font-size:11px;border-top:1px solid var(--line)}
.to-notice{min-height:34px;padding:10px 24px;border-top:1px solid var(--line);color:var(--mut);font-size:10.5px}.to-notice.error{color:var(--to-red)}
.to-dialog-backdrop{position:fixed;inset:0;z-index:280;display:none;align-items:center;justify-content:center;padding:22px;background:rgba(4,10,16,.68);backdrop-filter:blur(3px)}.to-dialog-backdrop.open{display:flex}.to-dialog{width:min(760px,100%);max-height:90vh;overflow:auto;border:1px solid var(--line);border-radius:16px;background:var(--bg2);box-shadow:0 24px 72px rgba(0,0,0,.52)}.to-dialog-head{display:flex;align-items:flex-start;gap:14px;padding:17px 20px 14px;border-bottom:1px solid var(--line)}.to-dialog-head h3{margin:0 0 4px;font-size:16px}.to-dialog-head p{margin:0;color:var(--mut);font-size:10.5px;line-height:1.5}.to-dialog-close{margin-left:auto;border:0;background:transparent;color:var(--mut);font-size:22px;line-height:1;cursor:pointer}.to-dialog-close:hover{color:var(--fg)}
@media(max-width:900px){.to-grid{grid-template-columns:1fr}.to-side{border-left:0;border-top:1px solid var(--line)}.to-statusline{grid-template-columns:repeat(3,1fr)}.to-essential{align-items:flex-start;flex-wrap:wrap}.to-command-note{order:3;flex-basis:100%}.to-essential-actions{margin-left:auto}}
@media(max-width:640px){.to-shell{margin:0 -18px 24px;border-left:0;border-right:0;border-radius:0}.to-head{padding:18px}.to-onboarding,.to-overview,.to-actions,.to-main,.to-side{padding:17px 18px}.to-flow{grid-template-columns:1fr}.to-arrow{padding:5px;transform:rotate(90deg)}.to-safe{grid-template-columns:1fr}.to-safe>div+div{border-left:0;border-top:1px solid var(--line)}
 .to-signals{grid-template-columns:1fr 1fr}.to-essential{display:block}.to-mode-state{margin-bottom:9px}.to-essential-actions{display:grid;grid-template-columns:1fr 1fr}.to-essential-actions .to-action{width:100%;min-width:0}.to-essential-actions .to-icon-action{width:100%}.to-command-note{margin:10px 0}.to-actions-head{align-items:start;flex-direction:column}.to-action{min-height:40px}.to-action-strip .to-action{flex:1 1 calc(50% - 7px)}.to-statusline{grid-template-columns:1fr 1fr}.to-workrow{grid-template-columns:1fr}.to-member>summary{grid-template-columns:1fr auto}.to-member>summary code{grid-column:1/-1}.to-dialog-backdrop{padding:10px}.to-dialog{max-height:94vh}.to-dialog-head,.to-controlbar,.to-privacy,.to-notice{padding-left:18px;padding-right:18px}.to-controlbar .to-spacer{display:none}}
@media(prefers-reduced-motion:reduce){.to-shell *{scroll-behavior:auto!important;transition:none!important}}
"""


TEAM_OBSERVATORY_JS = r"""
(function(){
  const page=document.getElementById('team-observatory'); if(!page) return;
  const q=(s)=>page.querySelector(s), qa=(s)=>Array.from(page.querySelectorAll(s));
  const text=(el,value)=>{if(el) el.textContent=value==null?'待确认':String(value)};
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
    if(!response.ok) throw new Error(value.error||'本机团队操作失败'); return value;
  }
  function renderMembers(projection){
    const root=q('[data-team-members]');root.replaceChildren();
    const members=(projection&&projection.members)||[];
    text(q('[data-team-member-note]'),members.length<=1?'目前只有你的本机状态；可主动查找同项目的局域网候选，成员资格仍需目标主机本机确认。':'按成员查看其最近共享的任务状态；过期快照不会冒充实时在线。');
    if(!members.length){root.append(node('div','to-empty','还没有可用的成员状态。当前不能据此判断团队是否空闲。'));return}
    members.forEach(member=>{const details=node('details','to-member');details.open=true;const summary=node('summary');
      const title=node('div','to-member-title');title.append(node('h4',null,member.member_id==='local-owner'?'你（本机成员）':'团队成员'),node('small',null,'展开查看共享任务'));
      summary.append(title,node('span','to-caps',(member.capabilities||[]).length+' 项已声明能力'));details.append(summary);
      const table=node('div','to-worktable');const streams=member.workstreams||[];
      if(!streams.length)table.append(node('div','to-empty','该成员还没有共享可见的工作任务。'));
      streams.forEach(work=>{const row=node('div','to-workrow');
        const visibility=(work.reported_workstream||{}).visibility==='team-metadata'?'团队可见元数据':'仅本机可见';const subsystem=(work.scope||{}).primary_subsystem_id&&((work.scope||{}).primary_subsystem_id!=='unmapped')?'已关联项目模块':'尚未关联项目模块';
        const workTitle=node('div','to-work-title');workTitle.append(node('b',null,work.workstream_id),node('small',null,subsystem+' · '+visibility));
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
  function renderLan(lan,config){lan=lan||{};config=config||{};const status=lan.status||{},candidates=lan.candidates||[],joins=lan.join_requests||[],host=lan.coordinator_host||{};
    text(q('[data-lan-discovery]'),({'never-started':'尚未查找',running:'正在查找',succeeded:'查找完成',failed:'查找失败'}[status.status]||status.status||'尚未查找'));text(q('[data-lan-candidates]'),candidates.length);text(q('[data-lan-host-generation]'),host.generation==null?'待确认':'第 '+host.generation+' 代 · '+({'active':'当前','stale-unknown':'历史状态'}[host.status]||host.status||'待确认'));
    const root=q('[data-lan-results]');root.replaceChildren();
    if(!candidates.length)root.append(node('div','to-empty','尚未发现候选主机。发现结果只是不可信提示，不会自动加入团队。'));
    candidates.forEach(candidate=>{const packet=candidate.packet||{},endpoint=packet.endpoint||'',loopback=/^https?:\/\/(127\.0\.0\.1|localhost)(:|\/|$)/i.test(endpoint),selfHint=packet.host_hint&&packet.host_hint===config.host_id,local=loopback||selfHint;const item=node('div','to-request');item.append(node('b',null,local?'本机测试／本机主机':'不可信候选主机'),node('p',null,local?'这是当前电脑上的发现回环，用于验证流程，不代表另一台设备。':'找到同一项目指纹的局域网候选，仍未建立成员关系。'),node('div','to-request-meta','用户主动查找 · 项目指纹过滤 · 仍需目标主机本机确认 · 不会自动加入、执行或上传源码'));root.append(item)});
    joins.filter(item=>item.status==='pending').forEach(item=>{const row=node('div','to-request');row.append(node('b',null,'加入确认'),node('p',null,'该成员仍未加入；确认只签发成员凭据，不执行其电脑上的任何动作。'));const button=node('button','to-action','在目标主机本机确认加入');button.type='button';button.dataset.joinRequestId=item.request_id;row.append(button);root.append(row)});
  }
  function renderOverview(value){const config=value.config||{},running=!!(value.coordinator&&value.coordinator.running),projection=value.projection||{},members=projection.members||[];
    const pending=(value.requests||[]).filter(request=>request.status==='pending-local-confirmation').length,outbox=value.outbox_count||0;
    const externalRegistered=!running&&config.runtime_status==='team-runtime-active';let guidance;
    if(externalRegistered){guidance='检测到另一个本机协作服务登记；请回到原页面正常停止，或退出团队模式后重新启用。'}
    else if(!running){guidance='团队连接尚未启动；本地工作保持不受影响。'}
    else if(!config.sharing_enabled){guidance='团队连接已启动，项目状态共享仍处于暂停。'}
    else if(members.length<=1){guidance=outbox?'还有 '+outbox+' 项本机状态等待同步。':'目前只有你的本机成员状态。'}
    else{guidance=pending?'有 '+pending+' 个请求等待你在本机确认。':'目前没有需要你处理的团队请求。'}
    if(running&&!(config.heartbeat&&config.heartbeat.enabled))guidance+=' 在线状态广播已关闭，因此“状态已过期／未知”是预期结果。';
    text(q('[data-team-guidance]'),guidance);text(q('[data-team-service]'),running?'本机服务运行中':externalRegistered?'其他本机服务登记':'尚未启动');text(q('[data-team-member-count]'),members.length);text(q('[data-team-pending-count]'),pending);qa('[data-team-outbox]').forEach(element=>text(element,outbox));
    text(q('[data-lan-connection]'),running?'已连接 · 按递增版本聚合':externalRegistered?'其他本机服务运行中 · 当前页面不可控制':'未连接 · 本地工作已保留');
  }
  function render(value){state=value;const config=value.config||{};const enabled=!!config.enabled;const running=!!(value.coordinator&&value.coordinator.running);
    const externalRegistered=!running&&config.runtime_status==='team-runtime-active';
    q('[data-team-onboarding]').hidden=enabled;q('[data-team-workspace]').hidden=!enabled;
    text(q('[data-team-mode]'),enabled?'团队模式 · 已主动开启':'个人模式 · 零网络');text(q('[data-team-runtime]'),config.runtime_status||'personal-zero-network');
    text(q('[data-team-member]'),config.member_id||'implicit local');text(q('[data-team-host]'),config.host_id||'not configured');
    text(q('[data-team-sharing]'),config.sharing_enabled?'已共享':'已关闭');text(q('[data-team-heartbeat]'),config.heartbeat&&config.heartbeat.enabled?'已开启':'已关闭');
    text(q('[data-team-last-seen]'),value.projection&&value.projection.generated_at||'暂不可用');text(q('[data-team-outbox]'),value.outbox_count||0);
    const connection=q('[data-team-connection-action]');connection.dataset.teamAction=running?'stop':'start';
    qa('[data-team-action]').forEach(button=>{const action=button.dataset.teamAction;button.disabled=(action==='enable'&&enabled)||(action==='disable'&&!enabled)||(action==='start'&&(!enabled||running||externalRegistered))||(action==='stop'&&!running)||(['heartbeat','sharing','capture','sync','request-create','maintenance-request','discovery'].includes(action)&&!enabled)||(['sync','discovery'].includes(action)&&!running)});
    text(connection,running?'暂停团队连接':externalRegistered?'其他本机服务占用中':'启动团队连接');
    text(q('[data-action-heartbeat]'),config.heartbeat&&config.heartbeat.enabled?'关闭在线状态':'开启在线状态');text(q('[data-action-sharing]'),config.sharing_enabled?'暂停项目状态共享':'开始共享项目状态');text(q('[data-action-sync]'),(value.outbox_count||0)?'同步 '+value.outbox_count+' 项更新':'立即同步');
    renderOverview(value);renderMembers(value.projection);renderRequests(value.requests||[]);renderLan(value.lan,config);
  }
  function setSettings(open){const backdrop=q('[data-team-settings-backdrop]'),trigger=q('[data-team-settings-open]');backdrop.classList.toggle('open',open);backdrop.setAttribute('aria-hidden',open?'false':'true');trigger.setAttribute('aria-expanded',open?'true':'false');if(open)q('[data-team-settings-close]').focus();else trigger.focus()}
  const apiBase='__ORRERY_TEAM_API_BASE__';
  async function refresh(){try{render(await api(apiBase+'/status'));q('[data-team-notice]').className='to-notice';text(q('[data-team-notice]'),'本机状态已刷新；没有返回凭据或源码内容。')}catch(error){q('[data-team-notice]').className='to-notice error';text(q('[data-team-notice]'),error.message)}}
  page.addEventListener('click',async(event)=>{const button=event.target.closest('button');if(!button)return;if(button.hasAttribute('data-team-settings-open')){setSettings(true);return}if(button.hasAttribute('data-team-settings-close')){setSettings(false);return}let path=null,body={};
    if(button.dataset.teamAction){path=apiBase+'/'+button.dataset.teamAction}else if(button.dataset.requestDecision){path=apiBase+'/request/decision';body={request_id:button.dataset.requestId,decision:button.dataset.requestDecision}}else if(button.dataset.joinRequestId){path=apiBase+'/join/confirm';body={request_id:button.dataset.joinRequestId}}else{return}
    button.disabled=true;try{await api(path,body);await refresh()}catch(error){const action=button.dataset.teamAction||button.dataset.requestDecision;const friendly={start:'无法启动本机协作服务。可能存在其他团队页面或失效的本机登记，请按上方说明恢复。',disable:'无法退出团队模式。请先关闭其他本机团队页面后重试。',sync:'同步没有完成；本机待同步状态仍会保留。',accept:'请求尚未确认，请刷新后重试。',reject:'请求尚未拒绝，请刷新后重试。'}[action]||'本机操作没有完成；没有执行远程命令。';q('[data-team-notice]').className='to-notice error';text(q('[data-team-notice]'),friendly);button.disabled=false}});
  q('[data-team-settings-backdrop]').addEventListener('click',event=>{if(event.target===event.currentTarget)setSettings(false)});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&q('[data-team-settings-backdrop]').classList.contains('open'))setSettings(false)});
  refresh();
})();
"""


def render_team_observatory_panel() -> str:
    return (
        '<article class="page wide" id="team-observatory" data-kind="team-observatory" '
        'data-title="团队协作" data-authority="derived-read-only">'
        '<section class="to-shell"><header class="to-head"><div><span class="to-kicker">团队协作 · 本机控制</span>'
        '<h2>团队指挥台</h2><p>先看谁在推进、哪里需要你处理；所有请求仍由目标成员在自己的电脑上确认。</p></div></header>'
        '<section class="to-onboarding" data-team-onboarding><h3>个人模式正在保护默认体验</h3>'
        '<p>当前不会启动团队网络连接。启用项目团队身份与启动本机协作服务是两个独立动作；局域网监听仍需单独主动开启。</p>'
        '<div class="to-flow"><div class="to-step"><small>01 · 默认状态</small><b>个人模式</b><span>零监听、零发现、零同步</span></div><div class="to-arrow">→</div>'
        '<div class="to-step"><small>02 · 本机登记</small><b>启用团队模式</b><span>只写 Git-private 配置，不开端口</span></div><div class="to-arrow">→</div>'
        '<div class="to-step"><small>03 · 主动启动</small><b>启动本机协作服务</b><span>关闭网页不会停止服务；请使用右上角“关闭 Orrery 服务”</span></div></div>'
        '<div class="to-safe"><div><b>中央能做什么</b><span>读取版本化元数据、聚合成员与任务关系、发送请求。</span></div>'
        '<div><b>中央不能做什么</b><span>不能执行命令、Agent、合并或删除；接受／拒绝也只写本机回执。</span></div></div>'
        '<button class="to-action primary" type="button" data-team-action="enable">在本机启用团队模式</button></section>'
        '<section class="to-workspace" data-team-workspace hidden>'
        '<section class="to-overview"><div class="to-signals"><div class="to-signal"><small>团队连接</small><b data-team-service>尚未启动</b></div><div class="to-signal"><small>可见成员</small><b><span data-team-member-count>0</span> 人</b></div><div class="to-signal"><small>等待你处理</small><b><span data-team-pending-count>0</span> 项</b></div><div class="to-signal"><small>等待同步</small><b><span data-team-outbox>0</span> 项</b></div></div>'
        '<div class="to-essential"><div class="to-mode-state"><small>团队模式</small><b data-team-mode>团队模式 · 已主动开启</b></div><p class="to-command-note" data-team-guidance>正在读取本机团队状态…</p><div class="to-essential-actions">'
        '<button class="to-action primary" type="button" data-team-action="start" data-team-connection-action>启动团队连接</button><button class="to-action" type="button" data-team-action="heartbeat" data-action-heartbeat>开启在线状态</button>'
        '<button class="to-action to-icon-action" type="button" data-team-settings-open aria-label="本机设置与诊断" title="本机设置与诊断" aria-haspopup="dialog" aria-controls="team-local-settings" aria-expanded="false">⚙</button><button class="to-action danger" type="button" data-team-action="disable">退出团队模式</button></div></div></section>'
        '<section class="to-actions"><div class="to-actions-head"><div><span class="to-section-label">建议操作</span><h3>按当前状态完成下一步</h3></div><span>这里的操作只影响你的本机节点</span></div><div class="to-action-strip">'
        '<button class="to-action" type="button" data-team-action="discovery">在局域网查找团队成员</button><button class="to-action" type="button" data-team-action="sharing" data-action-sharing>开始共享项目状态</button>'
        '<button class="to-action" type="button" data-team-action="capture">采集本机状态</button><button class="to-action" type="button" data-team-action="sync" data-action-sync>立即同步</button></div></section>'
        '<div class="to-grid"><main class="to-main"><section class="to-section"><div class="to-section-head"><h3>发现、加入与连接</h3><span>主动点击后按项目指纹过滤；结果仍是不可信候选，必须由目标主机本机确认</span></div><p class="to-command-note">查找不会自动加入团队、执行操作或上传源码。回环结果会明确标为本机测试／本机主机。</p><div data-lan-results></div></section><section class="to-section"><div class="to-section-head"><h3>成员与工作任务</h3><span data-team-member-note>按成员查看最近共享的任务</span></div><div data-team-members></div></section></main>'
        '<aside class="to-side"><section class="to-section" data-team-requests><div class="to-section-head"><h3>待处理请求</h3><span>确认只记录决定，不会自动执行</span></div><div data-team-pending-requests></div>'
        '<details class="to-history" data-team-request-history hidden><summary data-team-history-summary>已处理请求（0）</summary><div data-team-request-history-list></div></details></section></aside></div>'
        '</section><div class="to-notice" data-team-notice>正在读取本机团队状态…</div></section>'
        '<div class="to-dialog-backdrop" data-team-settings-backdrop aria-hidden="true"><section class="to-dialog" id="team-local-settings" role="dialog" aria-modal="true" aria-labelledby="team-local-settings-title">'
        '<header class="to-dialog-head"><div><h3 id="team-local-settings-title">本机设置与诊断</h3><p>低频控制与协议字段；这里的动作仍只影响当前本机节点。</p></div><button class="to-dialog-close" type="button" data-team-settings-close aria-label="关闭本机设置">×</button></header>'
        '<div class="to-statusline"><div><small>运行模式</small><b data-team-runtime>待确认</b></div><div><small>成员 ID</small><b data-team-member>待确认</b></div>'
        '<div><small>主机 ID</small><b data-team-host>待确认</b></div><div><small>共享／心跳</small><b><span data-team-sharing>已关闭</span> · <span data-team-heartbeat>已关闭</span></b></div>'
        '<div><small>最近状态</small><b data-team-last-seen>暂不可用</b></div><div><small>待同步队列</small><b data-team-outbox>0</b></div>'
        '<div><small>发现状态／候选数</small><b><span data-lan-discovery>尚未查找</span> · <span data-lan-candidates>0</span></b></div><div><small>当前协调主机</small><b data-lan-host-generation>待确认</b></div><div><small>连接／重连</small><b data-lan-connection>未连接 · 本地工作已保留</b></div></div>'
        '<div class="to-controlbar"><button class="to-action" type="button" data-team-action="maintenance-request">请求成员本机评估维护</button><button class="to-action" type="button" data-team-action="request-create">创建测试请求</button></div>'
        '<div class="to-privacy"><b>只共享最小元数据</b><br>发现包仅含协议版本、不透明的项目／主机／设备提示，以及短期端点、随机数和到期时间；不发送提示词、回答、推理、对话记录、源码正文、未推送差异、成员令牌、API 密钥或凭据。最后快照只按 Core 有效期投影，不冒充实时在线；主机切换只允许手工递增代次，不自动选主。</div></section></div></article>'
    )


def inject_team_observatory(
    page: str,
    *,
    api_base: str = "/team/api",
    dynamic_control: bool = True,
) -> str:
    if 'id="team-observatory"' in page:
        raise ValueError("Team Observatory is already present")
    nav_marker = (
        '<a class="nav-item" data-target="personal-observatory">'
        '<span class="dot state"></span><span class="lbl">个人工作台</span></a>'
    )
    content_marker = '</main><aside class="toc" id="toc">'
    if nav_marker not in page or content_marker not in page or "</style>" not in page:
        raise ValueError("Personal Observatory composition markers are missing")
    result = page.replace("</style>", TEAM_OBSERVATORY_CSS + "</style>", 1)
    nav = (
        '<a class="nav-item" data-target="team-observatory">'
        '<span class="dot proposed"></span><span class="lbl">团队协作</span></a>'
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
    panel = render_team_observatory_panel()
    if not dynamic_control:
        panel = panel.replace("<button ", "<button disabled ")
        panel = panel.replace(
            "正在读取本机团队状态…",
            "静态只读；团队控制暂不可用，未启动服务、cookie、监听或网络。",
        )
    result = result.replace(content_marker, panel + content_marker, 1)
    if not dynamic_control:
        return result
    if not api_base.startswith("/api/") and api_base != "/team/api":
        raise ValueError("Team API base must be a local API path")
    script = '<script>' + TEAM_OBSERVATORY_JS.replace(
        "__ORRERY_TEAM_API_BASE__", api_base.rstrip("/")
    ) + '</script>'
    return result.replace("</body>", script + "</body>", 1)


def safe_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
