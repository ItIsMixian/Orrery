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
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_HERE.parent))

import docsite_qa  # noqa: E402  (also sets sys.path for _llm + build_docsite)
import build_docsite as bd  # noqa: E402

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
.qa-head .x{margin-left:auto;cursor:pointer;color:var(--mut);font-size:19px;line-height:1}
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
</style>"""

QA_HTML = """<button id="qa-fab" onclick="qaToggle()">💬 问文档</button>
<div id="qa-panel">
 <div class="qa-head"><b>问文档</b><span class="mut">· 决策副驾</span><span class="x" onclick="qaToggle()">×</span></div>
 <div class="qa-out" id="qa-out"><div class="qa-empty">问点什么，我会基于项目文档检索 + 综合作答，每条结论都带可点引用。</div></div>
 <div class="qa-in">
  <div class="qa-ex" id="qa-ex"></div>
  <div class="qa-box">
   <textarea id="qa-q" rows="1" placeholder="问点什么… 例如：当前实现受哪些 ADR 约束？"></textarea>
   <button id="qa-send" onclick="qaAsk()" title="发送 (Ctrl/⌘+Enter)">↑</button>
  </div>
  <div class="qa-hint">Ctrl/⌘+Enter 发送 · 约 10–30 秒（检索 + 综合）</div>
 </div>
</div>"""

QA_SCRIPT = r"""<script>
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
document.addEventListener('keydown',e=>{if(e.target&&e.target.id==='qa-q'&&e.key==='Enter'&&(e.ctrlKey||e.metaKey))qaAsk();});
</script>"""


def inject_qa(html: str) -> str:
    return html.replace("</body>", QA_STYLE + QA_HTML + QA_SCRIPT + "</body>", 1)


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

try:
    PROVIDER, PNAME, CFG = docsite_qa.get_provider()
    print("provider: %s" % PNAME, flush=True)
except Exception as e:  # noqa: BLE001
    PROVIDER, PNAME = None, repr(e)
    print("provider init FAILED: %s" % PNAME, flush=True)

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
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
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

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s %s\n" % (self.command, self.path))


def main():
    srv = None
    port = None
    for p in range(8765, 8785):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if srv is None:
        print("no free port in 8765-8784")
        return
    try:
        (_HERE.parent / ".port").write_text(str(port), encoding="utf-8")
    except Exception:
        pass
    url = "http://127.0.0.1:%d/" % port
    print("\n  ✓ 文档问答已启动： %s" % url, flush=True)
    print("    停止：关闭此进程 (Ctrl+C / taskkill)\n", flush=True)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
