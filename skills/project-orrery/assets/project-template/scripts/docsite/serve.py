#!/usr/bin/env python3
"""Local server: the docs reader + an 'ask the docs' decision co-pilot panel.

  GET  /        -> the interactive reader (build_docsite) with a 💬 panel injected
  POST /ask     -> {question} -> two-stage RAG over the docs (docsite_qa) ->
                   {answer, citations:[{id,page,title}]}; citations are clickable
                   chips that jump to the source doc in the reader.

Run on the HOST (needs network + your LLM env — see _llm.py):

    # PowerShell
    $env:OPENAI_API_KEY="sk-..."     # or DEEPSEEK_API_KEY (+ OPENAI_BASE_URL)
    python -X utf8 scripts/docsite/serve.py
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_HERE.parent))

import docsite_qa  # noqa: E402  (also sets sys.path for _llm + build_docsite)
import build_docsite as bd  # noqa: E402
import _llm  # noqa: E402

DOCS = _ROOT / "docs"
AGENTS = _ROOT / "AGENTS.md"

# --- injected QA panel -----------------------------------------------------

QA_STYLE = """<style>
#qa-fab{position:fixed;right:22px;bottom:22px;z-index:200;background:var(--acc);color:#08110b;
 border:none;border-radius:24px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer;
 box-shadow:0 8px 24px rgba(0,0,0,.35)}
#qa-panel{position:fixed;right:22px;bottom:78px;z-index:200;width:430px;max-width:calc(100vw - 44px);
 max-height:78vh;display:none;flex-direction:column;background:var(--bg2);border:1px solid var(--line);
 border-radius:18px;box-shadow:0 20px 56px rgba(0,0,0,.45);overflow:hidden}
#qa-panel.open{display:flex}
.qa-head{padding:14px 18px;display:flex;align-items:center;gap:8px}
.qa-head b{font-size:14.5px}.qa-head .mut{color:var(--mut);font-size:12px}
.qa-head .settings{margin-left:auto;border:1px solid var(--line);background:var(--bg3);color:var(--fg);
 width:30px;height:30px;border-radius:9px;cursor:pointer;font-size:15px;line-height:1}
.qa-head .settings:hover{border-color:var(--acc);color:var(--acc)}
.qa-head .x{margin-left:auto;cursor:pointer;color:var(--mut);font-size:19px;line-height:1}
.qa-head .settings+.x{margin-left:2px}
.qa-head .x:hover{color:var(--fg)}
.qa-in{padding:12px 16px 14px;border-top:1px solid var(--line)}
.qa-box{position:relative;background:var(--bg3);border:1px solid var(--line);border-radius:14px;
 padding:11px 46px 11px 14px;transition:border-color .15s,box-shadow .15s}
.qa-box:focus-within{border-color:var(--acc);box-shadow:0 2px 14px rgba(0,0,0,.12)}
#qa-q{display:block;width:100%;background:transparent;border:0;outline:none;color:var(--fg);
 font-size:14px;line-height:1.5;font-family:inherit;resize:none;max-height:140px;overflow-y:auto}
#qa-send{position:absolute;right:8px;bottom:8px;width:30px;height:30px;border-radius:50%;border:0;
 background:var(--acc);color:var(--bg);cursor:pointer;font-size:17px;line-height:1;
 display:flex;align-items:center;justify-content:center}
#qa-send:disabled{opacity:.4;cursor:default}
.qa-hint{color:var(--mut);font-size:11px;margin-top:9px}
.qa-ex{margin:0 0 11px;display:flex;flex-wrap:wrap;gap:7px;align-items:center}
.qa-ex-lbl{font-size:11px;color:var(--mut)}
.qa-chip-ex{font-size:12px;padding:4px 11px;border-radius:16px;border:1px solid var(--line);
 background:transparent;color:var(--fg);cursor:pointer;transition:border-color .12s,color .12s}
.qa-chip-ex:hover{border-color:var(--acc);color:var(--acc)}
.qa-out{flex:1;min-height:0;padding:14px 16px;overflow-y:auto;
 scrollbar-width:thin;scrollbar-color:transparent transparent}
.qa-out:hover{scrollbar-color:var(--line) transparent}
.qa-out::-webkit-scrollbar{width:8px}
.qa-out::-webkit-scrollbar-thumb{background:transparent;border-radius:4px}
.qa-out:hover::-webkit-scrollbar-thumb{background:var(--line)}
.qa-q-echo{background:var(--bg3);border-left:3px solid var(--acc);border-radius:10px;
 padding:9px 13px;font-size:13.5px;color:var(--fg);line-height:1.5;margin-bottom:14px}
.qa-empty{color:var(--mut);font-size:13px;line-height:1.7}
.qa-answer{line-height:1.8;font-size:14.5px;color:var(--fg)}
.qa-answer p{margin:0 0 10px} .qa-answer p:last-child{margin-bottom:0}
.qa-answer ul,.qa-answer ol{margin:0 0 10px;padding-left:22px} .qa-answer li{margin:4px 0}
.qa-answer h4{margin:12px 0 6px;font-size:14px;color:var(--strong)}
.qa-answer code{background:var(--code);color:var(--codefg);padding:1px 5px;border-radius:4px;font-size:12.5px}
.qa-answer strong{color:var(--strong)}
.qa-loading,.qa-err{color:var(--mut);font-size:13px;line-height:1.7}
.qa-err{color:var(--warn)}
.qa-cites{margin-top:15px;padding-top:13px;border-top:1px solid var(--line)}
.qa-cites-t{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin-bottom:8px}
.qa-chip{display:inline-block;margin:0 6px 6px 0;font-size:12px;padding:3px 11px;border-radius:16px;
 border:1px solid var(--line);background:var(--bg3);color:var(--acc);cursor:pointer}
.qa-chip:hover{border-color:var(--acc)}
#ai-settings-backdrop{position:fixed;inset:0;z-index:260;display:none;align-items:center;justify-content:center;
 padding:22px;background:rgba(4,10,16,.62);backdrop-filter:blur(3px)}
#ai-settings-backdrop.open{display:flex}
.ai-settings-card{width:560px;max-width:100%;max-height:90vh;overflow:auto;background:var(--bg2);
 border:1px solid var(--line);border-radius:18px;box-shadow:0 24px 72px rgba(0,0,0,.5)}
.ai-settings-head{display:flex;align-items:flex-start;gap:12px;padding:18px 20px 14px;border-bottom:1px solid var(--line)}
.ai-settings-head h3{margin:0 0 4px;font-size:17px;color:var(--strong)}
.ai-settings-head p{margin:0;color:var(--mut);font-size:12px;line-height:1.55}
.ai-settings-head button{margin-left:auto;border:0;background:transparent;color:var(--mut);cursor:pointer;font-size:22px}
.ai-settings-body{padding:18px 20px 20px}
.ai-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.ai-field{display:flex;flex-direction:column;gap:6px}.ai-field.full{grid-column:1/-1}
.ai-field label{font-size:12px;font-weight:650;color:var(--fg)}
.ai-field input,.ai-field select{width:100%;box-sizing:border-box;border:1px solid var(--line);border-radius:10px;
 background:var(--bg3);color:var(--fg);padding:10px 11px;font:inherit;font-size:13px;outline:none}
.ai-field input:focus,.ai-field select:focus{border-color:var(--acc);box-shadow:0 0 0 3px color-mix(in srgb,var(--acc) 18%,transparent)}
.ai-help{font-size:11px;color:var(--mut);line-height:1.5}
.ai-config-state{margin:14px 0 0;padding:11px 12px;border:1px solid var(--line);border-radius:11px;
 background:var(--bg3);font-size:12px;line-height:1.6;color:var(--mut);white-space:pre-line}
.ai-config-state.ok{border-color:#4b9b72;color:#72c996}.ai-config-state.err{border-color:var(--warn);color:var(--warn)}
.ai-actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:16px}
.ai-btn{border:1px solid var(--line);border-radius:10px;background:var(--bg3);color:var(--fg);
 padding:8px 13px;font:inherit;font-size:12px;font-weight:650;cursor:pointer}
.ai-btn:hover{border-color:var(--acc)}.ai-btn.primary{background:var(--acc);border-color:var(--acc);color:#08110b}
.ai-btn.danger{color:var(--warn)}.ai-btn:disabled{opacity:.5;cursor:default}
.ai-security{margin-top:14px;color:var(--mut);font-size:10.5px;line-height:1.55}
@media(max-width:620px){.ai-grid{grid-template-columns:1fr}.ai-field.full{grid-column:auto}}
</style>"""

QA_HTML = """<button id="qa-fab" onclick="qaToggle()">💬 问文档</button>
<div id="qa-panel">
 <div class="qa-head"><b>问文档</b><span class="mut">· 决策副驾</span><button class="settings" onclick="aiOpenSettings()" title="AI 服务设置" aria-label="AI 服务设置">⚙</button><span class="x" onclick="qaToggle()">×</span></div>
 <div class="qa-out" id="qa-out"><div class="qa-empty">问点什么，我会基于项目文档检索 + 综合作答，每条结论都带可点引用。</div></div>
 <div class="qa-in">
  <div class="qa-ex" id="qa-ex"></div>
  <div class="qa-box">
   <textarea id="qa-q" rows="1" placeholder="问点什么… 例如：当前实现受哪些 ADR 约束？"></textarea>
   <button id="qa-send" onclick="qaAsk()" title="发送 (Ctrl/⌘+Enter)">↑</button>
  </div>
  <div class="qa-hint">Ctrl/⌘+Enter 发送 · 约 10–30 秒（检索 + 综合）</div>
 </div>
</div>
<div id="ai-settings-backdrop" onclick="if(event.target===this)aiCloseSettings()">
 <section class="ai-settings-card" role="dialog" aria-modal="true" aria-labelledby="ai-settings-title">
  <div class="ai-settings-head">
   <div><h3 id="ai-settings-title">AI 服务设置</h3><p>仅作用于这台电脑上的动态文档服务；静态 HTML 不会保存凭据。</p></div>
   <button onclick="aiCloseSettings()" aria-label="关闭">×</button>
  </div>
  <div class="ai-settings-body">
   <div class="ai-grid">
    <div class="ai-field">
     <label for="ai-provider">服务商预设</label>
     <select id="ai-provider" onchange="aiApplyPreset()"><option value="openai">OpenAI</option><option value="deepseek">DeepSeek</option><option value="custom">自定义 OpenAI-compatible</option></select>
    </div>
    <div class="ai-field">
     <label for="ai-model">默认模型</label>
     <input id="ai-model" autocomplete="off" placeholder="gpt-4o-mini">
    </div>
    <div class="ai-field full">
     <label for="ai-base-url">Base URL</label>
     <input id="ai-base-url" autocomplete="off" placeholder="留空使用 OpenAI 默认地址">
    </div>
    <div class="ai-field full">
     <label for="ai-api-key">API Key</label>
     <input id="ai-api-key" type="password" autocomplete="new-password" spellcheck="false" placeholder="留空则保留当前凭据">
     <div class="ai-help" id="ai-key-help">Key 不会回显，也不会写入 ai-config.json。</div>
    </div>
    <div class="ai-field">
     <label for="ai-intent-model">快速／检索模型（可选）</label>
     <input id="ai-intent-model" autocomplete="off" placeholder="默认沿用上方模型">
    </div>
    <div class="ai-field">
     <label for="ai-audit-model">综合／审计模型（可选）</label>
     <input id="ai-audit-model" autocomplete="off" placeholder="默认沿用上方模型">
    </div>
   </div>
   <div class="ai-config-state" id="ai-config-state">正在读取本地配置…</div>
   <div class="ai-actions">
    <button class="ai-btn" id="ai-test" onclick="aiTestSettings()">测试连接</button>
    <button class="ai-btn primary" id="ai-save" onclick="aiSaveSettings()">保存并启用</button>
    <button class="ai-btn danger" id="ai-delete" onclick="aiDeleteKey()">删除系统凭据</button>
   </div>
   <div class="ai-security">安全说明：API Key 只提交给当前 127.0.0.1 服务，并写入操作系统凭据库；页面不会获得已保存 Key 的原文。Base URL 与模型写入项目根目录中已忽略的 ai-config.json。环境变量始终拥有更高优先级。</div>
  </div>
 </section>
</div>"""

QA_SCRIPT = r"""<script>
const ORRERY_SETTINGS_TOKEN='__ORRERY_SETTINGS_TOKEN__';
const AI_PRESETS={
 openai:{baseUrl:'',model:'gpt-4o-mini'},
 deepseek:{baseUrl:'https://api.deepseek.com',model:'deepseek-chat'},
 custom:{baseUrl:'',model:''}
};
function qaToggle(){const p=document.getElementById('qa-panel');p.classList.toggle('open');
 if(p.classList.contains('open'))document.getElementById('qa-q').focus();}
const QA_EX=[
 {l:"当前做到哪里",q:"当前阶段已经实现了什么，下一步是什么？"},
 {l:"决策如何生效",q:"当前实现受哪些有效 ADR 约束？"},
 {l:"状态是否可信",q:"哪些 state doc 可能已经过期或缺少验证？"},
 {l:"文档为何分层",q:"为什么要把 ADR、state doc、plan 和 snapshot 分开？"}
];
function autoGrow(){const q=document.getElementById('qa-q');if(!q)return;q.style.height='auto';q.style.height=Math.min(q.scrollHeight,140)+'px';}
(function(){const e=document.getElementById('qa-ex');if(!e)return;
 e.innerHTML='<span class="qa-ex-lbl">试试</span>'+QA_EX.map((x,i)=>'<button class="qa-chip-ex" data-i="'+i+'">'+x.l+'</button>').join('');
 e.querySelectorAll('.qa-chip-ex').forEach(b=>b.onclick=()=>{const q=document.getElementById('qa-q');q.value=QA_EX[+b.dataset.i].q;autoGrow();qaAsk();});
 const qel=document.getElementById('qa-q'); if(qel) qel.addEventListener('input',autoGrow);})();
function mdToHtml(t){
 t=(''+t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 t=t.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 const L=t.split(/\r?\n/); let h='',i=0;
 const ul=s=>/^\s*[-*]\s+/.test(s),ol=s=>/^\s*\d+\.\s+/.test(s),hd=s=>/^\s*#{1,6}\s+/.test(s),bl=s=>/^\s*$/.test(s);
 while(i<L.length){
  if(hd(L[i])){ h+='<h4>'+L[i].replace(/^\s*#{1,6}\s+/,'')+'</h4>'; i++; continue; }
  if(ul(L[i])){ let it=[]; while(i<L.length&&ul(L[i])){ it.push('<li>'+L[i].replace(/^\s*[-*]\s+/,'')+'</li>'); i++; } h+='<ul>'+it.join('')+'</ul>'; continue; }
  if(ol(L[i])){ let it=[]; while(i<L.length&&ol(L[i])){ it.push('<li>'+L[i].replace(/^\s*\d+\.\s+/,'')+'</li>'); i++; } h+='<ol>'+it.join('')+'</ol>'; continue; }
  if(bl(L[i])){ i++; continue; }
  let p=[]; while(i<L.length&&!bl(L[i])&&!ul(L[i])&&!ol(L[i])&&!hd(L[i])){ p.push(L[i]); i++; } h+='<p>'+p.join('<br>')+'</p>';
 }
 return h;
}
function renderQaCites(out, cs){
 if(!cs||!cs.length) return;
 const c=document.createElement('div'); c.className='qa-cites';
 c.innerHTML='<div class="qa-cites-t">引用 · 点击跳到原文</div>';
 cs.forEach(x=>{const el=document.createElement('a');el.className='qa-chip';el.textContent=x.title;
   el.onclick=()=>{if(window.showPage)showPage(x.page);};c.appendChild(el);});
 out.appendChild(c);
}
async function qaAsk(){
 const qel=document.getElementById('qa-q'),out=document.getElementById('qa-out'),btn=document.getElementById('qa-send');
 const q=qel.value.trim(); if(!q) return;
 btn.disabled=true; qel.value=''; autoGrow();
 const ex=document.getElementById('qa-ex'); if(ex) ex.style.display='none';
 out.innerHTML='<div class="qa-q-echo">'+q.replace(/</g,'&lt;')+'</div><div class="qa-answer"></div>';
 const ansEl=out.querySelector('.qa-answer');
 ansEl.innerHTML='<span class="qa-loading">检索中…</span>';
 try{
  const resp=await fetch('/ask_stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
  if(!resp.body){ // no streaming support: read whole
   const txt=await resp.text(); const ci=txt.indexOf('[[CITES]]');
   ansEl.innerHTML=mdToHtml((ci>=0?txt.slice(0,ci):txt).trim());
   if(ci>=0){ try{ renderQaCites(out, JSON.parse(txt.slice(ci+9))); }catch(e){} }
   btn.disabled=false; return;
  }
  const reader=resp.body.getReader(), dec=new TextDecoder(); let acc='', cites=null;
  while(true){ const {done,value}=await reader.read(); if(done) break;
   acc+=dec.decode(value,{stream:true});
   const ei=acc.indexOf('[[ERROR]]');
   if(ei>=0){ ansEl.innerHTML='<div class="qa-err">出错：'+acc.slice(ei+9).replace(/</g,'&lt;')+'</div>'; btn.disabled=false; return; }
   let body=acc; const ci=acc.indexOf('[[CITES]]');
   if(ci>=0){ body=acc.slice(0,ci); cites=acc.slice(ci+9); }
   ansEl.innerHTML=mdToHtml(body.trim()||'…');
  }
  if(cites){ try{ renderQaCites(out, JSON.parse(cites)); }catch(e){} }
 }catch(e){ out.innerHTML='<div class="qa-err">请求失败：'+e+'</div>'; }
 finally{ btn.disabled=false; }
}
function aiField(id){return document.getElementById(id);}
function aiBusy(v){['ai-test','ai-save','ai-delete'].forEach(id=>{const e=aiField(id);if(e)e.disabled=v;});}
function aiSetState(text,kind=''){const e=aiField('ai-config-state');e.textContent=text;e.className='ai-config-state'+(kind?' '+kind:'');}
function aiDetectProvider(baseUrl){const u=(baseUrl||'').toLowerCase();if(u.includes('deepseek'))return'deepseek';if(!u||u.includes('api.openai.com'))return'openai';return'custom';}
function aiApplyPreset(){const p=AI_PRESETS[aiField('ai-provider').value]||AI_PRESETS.custom;aiField('ai-base-url').value=p.baseUrl;aiField('ai-model').value=p.model;}
function aiPayload(){return{
 baseUrl:aiField('ai-base-url').value.trim(),model:aiField('ai-model').value.trim(),
 intentModel:aiField('ai-intent-model').value.trim(),auditModel:aiField('ai-audit-model').value.trim(),
 apiKey:aiField('ai-api-key').value.trim()
};}
async function aiRequest(path,method='GET',body=null){const options={method,cache:'no-store',credentials:'same-origin',headers:{'Accept':'application/json'}};
 if(method!=='GET')options.headers['X-Orrery-Settings-Token']=ORRERY_SETTINGS_TOKEN;
 if(body!==null){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
 const response=await fetch(path,options);let data={};try{data=await response.json();}catch(e){}
 if(!response.ok)throw new Error(data.error||('HTTP '+response.status));return data;}
function aiRenderConfig(data,prefix=''){const source=data.hasKey?('已配置 · '+data.keySource):'未配置';
 aiField('ai-key-help').textContent='API Key：'+source+'。Key 不会回显，也不会写入 ai-config.json。';
 const overrides=(data.environmentOverrides||[]).length?'\n环境变量覆盖：'+data.environmentOverrides.join('、'):'';
 const provider=data.providerReady?'Provider 已就绪':'Provider 尚不可用'+(data.providerError?'：'+data.providerError:'');
 aiSetState((prefix?prefix+'\n':'')+provider+'\nAPI Key：'+source+overrides,data.providerReady?'ok':'');}
async function aiLoadSettings(){aiBusy(true);aiSetState('正在读取本地配置…');try{const data=await aiRequest('/api/ai-config');
 aiField('ai-provider').value=aiDetectProvider(data.baseUrl);aiField('ai-base-url').value=data.baseUrl||'';
 aiField('ai-model').value=data.model||'gpt-4o-mini';aiField('ai-intent-model').value=data.intentModel||'';
 aiField('ai-audit-model').value=data.auditModel||'';aiField('ai-api-key').value='';aiRenderConfig(data);
 }catch(e){aiSetState('读取失败：'+e.message,'err');}finally{aiBusy(false);}}
function aiOpenSettings(){aiField('ai-settings-backdrop').classList.add('open');aiLoadSettings();}
function aiCloseSettings(){aiField('ai-settings-backdrop').classList.remove('open');aiField('ai-api-key').value='';}
async function aiSaveSettings(){aiBusy(true);aiSetState('正在安全保存并重新加载 Provider…');try{const data=await aiRequest('/api/ai-config','POST',aiPayload());
 aiField('ai-api-key').value='';aiRenderConfig(data,data.message||'配置已保存。');
 }catch(e){aiSetState('保存失败：'+e.message,'err');}finally{aiBusy(false);}}
async function aiTestSettings(){aiBusy(true);aiSetState('正在发送一个最小测试请求；这可能产生少量模型费用…');try{const data=await aiRequest('/api/ai-config/test','POST',aiPayload());
 aiSetState((data.message||'连接成功')+'\n模型：'+(data.model||aiField('ai-model').value),'ok');
 }catch(e){aiSetState('连接失败：'+e.message,'err');}finally{aiBusy(false);}}
async function aiDeleteKey(){if(!window.confirm('删除 Project Orrery 保存在系统凭据库中的 API Key？环境变量或外部配置文件不会被修改。'))return;
 aiBusy(true);aiSetState('正在删除系统凭据…');try{const data=await aiRequest('/api/ai-config/key','DELETE');aiField('ai-api-key').value='';aiRenderConfig(data,data.message||'系统凭据已删除。');
 }catch(e){aiSetState('删除失败：'+e.message,'err');}finally{aiBusy(false);}}
document.addEventListener('keydown',e=>{if(e.target&&e.target.id==='qa-q'&&e.key==='Enter'&&(e.ctrlKey||e.metaKey))qaAsk();if(e.key==='Escape'&&aiField('ai-settings-backdrop').classList.contains('open'))aiCloseSettings();});
</script>"""


SETTINGS_TOKEN = secrets.token_urlsafe(32)


def inject_qa(html: str) -> str:
    script = QA_SCRIPT.replace("__ORRERY_SETTINGS_TOKEN__", SETTINGS_TOKEN)
    return html.replace("</body>", QA_STYLE + QA_HTML + script + "</body>", 1)


# --- build once at startup --------------------------------------------------

print("building reader…", flush=True)
_page, _stats = bd.render_site(
    DOCS,
    AGENTS,
    _ROOT,
    os.environ.get("DOCSITE_TITLE", "{{PROJECT_TITLE_PY}} · Documentation"),
)
HTML = inject_qa(_page).encode("utf-8")
print("  pages: %(adrs)d ADR / %(states)d state / %(snaps)d snap / %(documents)d classified docs" % _stats, flush=True)

print("building corpus…", flush=True)
CORPUS = docsite_qa.build_corpus(DOCS, AGENTS)
print("  corpus: %d docs" % len(CORPUS), flush=True)

PROVIDER = None
PNAME = "not initialized"
CFG = None
_CONFIG_LOCK = threading.RLock()
_MAX_CONFIG_BODY = 64 * 1024


def _reload_provider() -> bool:
    global PROVIDER, PNAME, CFG
    try:
        provider, name, config = docsite_qa.get_provider()
        PROVIDER, PNAME, CFG = provider, name, config
        print("provider: %s" % PNAME, flush=True)
        return True
    except Exception as e:  # noqa: BLE001
        PROVIDER, PNAME, CFG = None, repr(e), None
        print("provider init FAILED: %s" % PNAME, flush=True)
        return False


def _key_source_label(source) -> str:
    if source == "env":
        return "环境变量"
    if source == "keyring":
        return "系统凭据库"
    if source:
        try:
            if Path(source).resolve() == _llm.project_config_path().resolve():
                return "项目 ai-config.json"
        except (OSError, TypeError, ValueError):
            pass
        return "外部配置文件"
    return "未配置"


def _environment_overrides() -> list[str]:
    fields = (
        ("API Key", ("OPENAI_API_KEY", "DEEPSEEK_API_KEY")),
        ("Base URL", ("OPENAI_BASE_URL", "OPENAI_API_BASE")),
        ("默认模型", ("OPENAI_MODEL",)),
        ("快速模型", ("OPENAI_INTENT_MODEL",)),
        ("综合模型", ("OPENAI_AUDIT_MODEL",)),
    )
    return [label for label, names in fields if any(os.environ.get(name) for name in names)]


def _provider_status() -> dict:
    cfg = _llm.load_config()
    has_key = bool(cfg.get("api_key"))
    if PROVIDER is not None:
        provider_error = ""
    elif not has_key:
        provider_error = "缺少 API Key"
    else:
        provider_error = "Provider 初始化失败；请检查 Base URL、模型和依赖"
    return {
        "providerReady": PROVIDER is not None,
        "hasKey": has_key,
        "keySource": _key_source_label(cfg.get("source")),
        "baseUrl": cfg.get("base_url") or "",
        "model": cfg.get("model") or "gpt-4o-mini",
        "intentModel": cfg.get("intent_model") or "",
        "auditModel": cfg.get("audit_model") or "",
        "environmentOverrides": _environment_overrides(),
        "providerError": provider_error,
    }


def _clean_field(data: dict, key: str, label: str, limit: int, *, required: bool = False) -> str:
    value = data.get(key, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError("%s 必须是字符串" % label)
    value = value.strip()
    if len(value) > limit:
        raise ValueError("%s 过长" % label)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("%s 含有非法控制字符" % label)
    if required and not value:
        raise ValueError("%s 不能为空" % label)
    return value


def _validated_settings(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("请求必须是 JSON 对象")
    base_url = _clean_field(data, "baseUrl", "Base URL", 2048)
    if base_url:
        parsed = urlsplit(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Base URL 必须是有效的 http:// 或 https:// 地址")
        if parsed.username or parsed.password:
            raise ValueError("Base URL 不能包含用户名或密码")
        base_url = base_url.rstrip("/")
    return {
        "base_url": base_url,
        "model": _clean_field(data, "model", "默认模型", 200, required=True),
        "intent_model": _clean_field(data, "intentModel", "快速模型", 200),
        "audit_model": _clean_field(data, "auditModel", "综合模型", 200),
        "api_key": _clean_field(data, "apiKey", "API Key", 4096),
    }


def _safe_error(error: Exception, secret: str = "") -> str:
    message = str(error) or type(error).__name__
    if secret:
        message = message.replace(secret, "[REDACTED]")
    return message[:1200]


def _save_ai_settings(data: dict) -> dict:
    settings = _validated_settings(data)
    with _CONFIG_LOCK:
        current = _llm.load_config()
        key = settings["api_key"]
        if key:
            _llm.store_key(key)
        elif current.get("api_key") and _key_source_label(current.get("source")) == "项目 ai-config.json":
            # Migrate a legacy plaintext project key before rewriting the file.
            _llm.store_key(current["api_key"])
        _llm.save_project_config(
            base_url=settings["base_url"],
            model=settings["model"],
            intent_model=settings["intent_model"],
            audit_model=settings["audit_model"],
        )
        ready = _reload_provider()
        status = _provider_status()
        status["message"] = "配置已保存并启用。" if ready else "非敏感配置已保存；仍需提供有效 API Key。"
        return status


def _delete_ai_key() -> dict:
    with _CONFIG_LOCK:
        removed_plaintext = _llm.remove_project_plaintext_key()
        _llm.delete_key()
        _reload_provider()
        status = _provider_status()
        if status["hasKey"]:
            status["message"] = "系统凭据已删除，但环境变量或外部配置仍在提供 API Key。"
        elif removed_plaintext:
            status["message"] = "系统凭据与项目配置中的旧明文 Key 已删除。"
        else:
            status["message"] = "系统凭据已删除。"
        return status


def _test_ai_settings(data: dict) -> dict:
    settings = _validated_settings(data)
    current = _llm.load_config()
    key = settings["api_key"] or current.get("api_key") or ""
    if not key:
        raise ValueError("没有可用于测试的 API Key")
    config = {
        "api_key": key,
        "base_url": settings["base_url"] or None,
        "model": settings["model"],
        "intent_model": settings["intent_model"] or None,
        "audit_model": settings["audit_model"] or None,
        "source": "settings-test",
    }
    provider = _llm.OpenAICompatProvider(config)
    result = provider.complete(_llm.LLMRequest(
        system="You are a connection test. Reply briefly.",
        user="Reply with OK.",
        max_tokens=8,
        model_kind="intent",
    ))
    if result.get("parse_error"):
        raise RuntimeError(_safe_error(RuntimeError(result.get("error") or "模型请求失败"), key))
    return {"ok": True, "message": "连接成功。", "model": provider.intent_model}


_reload_provider()

# Persisted cache so we DON'T regenerate on every launch:
# first run (no cache) auto-generates; later runs reuse cache and rely on the
# manual ↻ refresh button; cache older than 10 days auto-regenerates.
_CACHE = _HERE.parent / ".doccache.json"
_MAXAGE = 10 * 86400  # 10 days


def _load_cache():
    try:
        return json.loads(_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(key, data):
    c = _load_cache()
    c[key] = {"data": data, "ts": time.time()}
    try:
        _CACHE.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


BRIEFING = None; BRIEFING_TS = None
ROADMAP = None; ROADMAP_TS = None
MILESTONES = None; MILESTONES_TS = None
RADAR = None; RADAR_TS = None


def _gen_briefing():
    global BRIEFING, BRIEFING_TS
    if PROVIDER is None:
        BRIEFING = {"error": "provider not available: %s" % PNAME}; return
    try:
        print("generating project briefing… (LLM)", flush=True)
        BRIEFING = docsite_qa.generate_briefing(PROVIDER, CORPUS)
        if not BRIEFING.get("error"):
            BRIEFING_TS = time.time(); _save_cache("briefing", BRIEFING)
            print("briefing ready", flush=True)
        else:
            print("briefing failed: %s" % BRIEFING.get("error"), flush=True)
    except Exception as e:  # noqa: BLE001
        BRIEFING = {"error": "briefing raised: %r" % e}


def _gen_roadmap():
    global ROADMAP, ROADMAP_TS
    if PROVIDER is None:
        ROADMAP = {"error": "provider not available: %s" % PNAME}; return
    try:
        print("generating roadmap… (LLM)", flush=True)
        ROADMAP = docsite_qa.generate_roadmap(PROVIDER, CORPUS)
        if not ROADMAP.get("error"):
            ROADMAP_TS = time.time(); _save_cache("roadmap", ROADMAP)
            print("roadmap ready", flush=True)
        else:
            print("roadmap failed: %s" % ROADMAP.get("error"), flush=True)
    except Exception as e:  # noqa: BLE001
        ROADMAP = {"error": "roadmap raised: %r" % e}


def _refresh_briefing():
    global BRIEFING, BRIEFING_TS
    BRIEFING = None; BRIEFING_TS = None
    threading.Thread(target=_gen_briefing, daemon=True).start()


def _refresh_roadmap():
    global ROADMAP, ROADMAP_TS
    ROADMAP = None; ROADMAP_TS = None
    threading.Thread(target=_gen_roadmap, daemon=True).start()


def _gen_milestones():
    global MILESTONES, MILESTONES_TS
    if PROVIDER is None:
        MILESTONES = {"error": "provider not available: %s" % PNAME}; return
    try:
        print("generating milestones… (LLM)", flush=True)
        MILESTONES = docsite_qa.generate_milestones(PROVIDER, CORPUS)
        if not MILESTONES.get("error"):
            MILESTONES_TS = time.time(); _save_cache("milestones", MILESTONES)
            print("milestones ready", flush=True)
        else:
            print("milestones failed: %s" % MILESTONES.get("error"), flush=True)
    except Exception as e:  # noqa: BLE001
        MILESTONES = {"error": "milestones raised: %r" % e}


def _refresh_milestones():
    global MILESTONES, MILESTONES_TS
    MILESTONES = None; MILESTONES_TS = None
    threading.Thread(target=_gen_milestones, daemon=True).start()


def _github_token():
    # optional: env GITHUB_TOKEN raises GitHub's anonymous rate limit; else anonymous
    return os.environ.get("GITHUB_TOKEN") or None


def _gen_radar():
    global RADAR, RADAR_TS
    if PROVIDER is None:
        RADAR = {"error": "provider not available: %s" % PNAME}; return
    try:
        print("generating community radar… (LLM + 联网)", flush=True)
        extra = [k.strip() for k in os.environ.get("DOCSITE_RADAR_KEYWORDS", "").split(",") if k.strip()]
        RADAR = docsite_qa.generate_radar(PROVIDER, CORPUS, github_token=_github_token(), extra_keywords=extra)
        if not RADAR.get("error"):
            RADAR_TS = time.time(); _save_cache("radar", RADAR)
        print("radar ready", flush=True)
    except Exception as e:  # noqa: BLE001
        RADAR = {"error": "radar raised: %r" % e}


def _refresh_radar():
    global RADAR, RADAR_TS
    RADAR = None; RADAR_TS = None
    threading.Thread(target=_gen_radar, daemon=True).start()


def _init_cached(key, gen):
    e = _load_cache().get(key)
    if e and e.get("data") and not e["data"].get("error") and (time.time() - e.get("ts", 0)) < _MAXAGE:
        print("%s: using cache" % key, flush=True)
        return e["data"], e["ts"]
    threading.Thread(target=gen, daemon=True).start()
    return None, None


BRIEFING, BRIEFING_TS = _init_cached("briefing", _gen_briefing)
ROADMAP, ROADMAP_TS = _init_cached("roadmap", _gen_roadmap)
MILESTONES, MILESTONES_TS = _init_cached("milestones", _gen_milestones)
RADAR, RADAR_TS = _init_cached("radar", _gen_radar)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _settings_authorized(self) -> bool:
        supplied = self.headers.get("X-Orrery-Settings-Token", "")
        return bool(supplied) and secrets.compare_digest(supplied, SETTINGS_TOKEN)

    def _read_json_body(self) -> dict:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Content-Type 必须是 application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Content-Length 无效") from error
        if length <= 0 or length > _MAX_CONFIG_BODY:
            raise ValueError("请求体为空或超过 64 KiB")
        try:
            data = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("请求体不是有效 JSON") from error
        if not isinstance(data, dict):
            raise ValueError("请求必须是 JSON 对象")
        return data

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/ai-config":
            self._send_json(200, _provider_status())
            return
        if self.path.startswith("/briefing"):
            if "refresh" in self.path and PROVIDER is not None:
                _refresh_briefing()
            body = {"pending": True} if BRIEFING is None else {**BRIEFING, "_ts": BRIEFING_TS}
            self._send(200, "application/json; charset=utf-8",
                       json.dumps(body, ensure_ascii=False).encode("utf-8"))
            return
        if self.path.startswith("/roadmap"):
            if "refresh" in self.path and PROVIDER is not None:
                _refresh_roadmap()
            body = {"pending": True} if ROADMAP is None else {**ROADMAP, "_ts": ROADMAP_TS}
            self._send(200, "application/json; charset=utf-8",
                       json.dumps(body, ensure_ascii=False).encode("utf-8"))
            return
        if self.path.startswith("/milestones"):
            if "refresh" in self.path and PROVIDER is not None:
                _refresh_milestones()
            body = {"pending": True} if MILESTONES is None else {**MILESTONES, "_ts": MILESTONES_TS}
            self._send(200, "application/json; charset=utf-8",
                       json.dumps(body, ensure_ascii=False).encode("utf-8"))
            return
        if self.path.startswith("/radar"):
            if "refresh" in self.path and PROVIDER is not None:
                _refresh_radar()
            body = {"pending": True} if RADAR is None else {**RADAR, "_ts": RADAR_TS}
            self._send(200, "application/json; charset=utf-8",
                       json.dumps(body, ensure_ascii=False).encode("utf-8"))
            return
        if self.path.startswith("/favicon"):
            self._send(204, "text/plain", b"")
            return
        self._send(200, "text/html; charset=utf-8", HTML)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path in ("/api/ai-config", "/api/ai-config/test"):
            if not self._settings_authorized():
                self._send_json(403, {"error": "设置令牌无效；请从当前本地页面重新打开设置。"})
                return
            try:
                data = self._read_json_body()
                result = _save_ai_settings(data) if path == "/api/ai-config" else _test_ai_settings(data)
                self._send_json(200, result)
            except ValueError as error:
                self._send_json(400, {"error": _safe_error(error)})
            except Exception as error:  # noqa: BLE001
                secret = data.get("apiKey", "") if "data" in locals() and isinstance(data, dict) else ""
                self._send_json(500, {"error": _safe_error(error, secret)})
            return
        if self.path.startswith("/ask_stream"):
            try:
                n = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(n) or b"{}")
                q = (data.get("question") or "").strip()
            except Exception:
                q = ""
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            try:
                if not q:
                    self.wfile.write(b"[[ERROR]] empty question")
                elif PROVIDER is None:
                    self.wfile.write(("[[ERROR]] provider not available: %s" % PNAME).encode("utf-8"))
                else:
                    for chunk in docsite_qa.ask_stream(PROVIDER, CORPUS, q):
                        self.wfile.write(chunk.encode("utf-8"))
                        self.wfile.flush()
            except Exception as e:  # noqa: BLE001
                try:
                    self.wfile.write(("\n[[ERROR]] %r" % e).encode("utf-8"))
                except Exception:
                    pass
            return
        if self.path != "/ask":
            self._send(404, "text/plain", b"not found")
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(n) or b"{}")
            q = (data.get("question") or "").strip()
            if not q:
                res = {"error": "empty question"}
            elif PROVIDER is None:
                res = {"error": "LLM provider not available: %s" % PNAME}
            else:
                res = docsite_qa.ask(q, PROVIDER, CORPUS, verbose=True)
        except Exception as e:  # noqa: BLE001
            res = {"error": "server error: %r" % e}
        self._send(200, "application/json; charset=utf-8",
                   json.dumps(res, ensure_ascii=False).encode("utf-8"))

    def do_DELETE(self):
        path = urlsplit(self.path).path
        if path != "/api/ai-config/key":
            self._send_json(404, {"error": "not found"})
            return
        if not self._settings_authorized():
            self._send_json(403, {"error": "设置令牌无效；请从当前本地页面重新打开设置。"})
            return
        try:
            self._send_json(200, _delete_ai_key())
        except Exception as error:  # noqa: BLE001
            self._send_json(500, {"error": _safe_error(error)})

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s %s\n" % (self.command, self.path))


def main():
    srv = None
    port = None
    requested = os.environ.get("DOCSITE_PORT", "").strip()
    try:
        ports = [int(requested)] if requested else range(8765, 8785)
    except ValueError:
        print("invalid DOCSITE_PORT: %s" % requested)
        return
    for p in ports:
        if p < 0 or p > 65535:
            print("invalid DOCSITE_PORT: %s" % p)
            return
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = srv.server_address[1]
            break
        except OSError:
            continue
    if srv is None:
        print("no free port in 8765-8784")
        return
    port_path = _HERE.parent / ".port"
    try:
        port_path.write_text(str(port), encoding="utf-8")
    except Exception:
        pass
    url = "http://127.0.0.1:%d/" % port
    print("\n  ✓ 文档问答已启动： %s" % url, flush=True)
    print("    停止：关闭此进程 (Ctrl+C / taskkill)\n", flush=True)
    if os.environ.get("DOCSITE_NO_BROWSER") != "1":
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        try:
            if port_path.read_text(encoding="utf-8").strip() == str(port):
                port_path.unlink()
        except (OSError, ValueError):
            pass


if __name__ == "__main__":
    main()
