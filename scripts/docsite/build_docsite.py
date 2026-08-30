#!/usr/bin/env python3
"""Build an interactive, single-file HTML doc viewer from the markdown docs.

Source of truth = the markdown docs. This HTML is a DERIVED, disposable
projection: never hand-edit the output; re-run this to regenerate.

Reader layout (progressive disclosure — one document at a time):
  - left sidebar  : grouped navigation by document family
  - center        : only the selected document is shown
  - right         : on-this-page table of contents for the selected document
Plus global search and clickable cross-references that switch pages.

Works on any repo that follows this doc convention — point --docs at its docs/.

Usage:
    python scripts/docsite/build_docsite.py
    python scripts/docsite/build_docsite.py --docs path/to/docs --out out.html
"""
from __future__ import annotations

import argparse
import base64
import html as htmllib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import docsite_insights as di  # local module: proactive (no-LLM) doc checks

# ---------------------------------------------------------------------------
# markdown rendering (mistune; tables/strikethrough are needed by the docs)
# ---------------------------------------------------------------------------

def make_md():
    import mistune
    for plugins in (["table", "strikethrough", "url"], ["table"], []):
        try:
            return mistune.create_markdown(escape=False, plugins=plugins)
        except Exception:
            continue
    return mistune.create_markdown(escape=False)


MD = make_md()


def render_md(text: str) -> str:
    out = MD(text)
    return out if isinstance(out, str) else str(out)


LOCAL_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^\s)>]+)>?\s*\)")


def inline_local_images(text: str, source_dir: Path) -> str:
    """Embed local doc images so the generated reader remains one HTML file."""
    mime_by_suffix = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    def replace(match):
        alt, target = match.group(1), match.group(2)
        if target.startswith(("http://", "https://", "data:")):
            return match.group(0)
        image_path = (source_dir / target).resolve()
        mime = mime_by_suffix.get(image_path.suffix.lower())
        if not mime or not image_path.is_file():
            return match.group(0)
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return '<img src="data:%s;base64,%s" alt="%s">' % (
            mime, encoded, htmllib.escape(alt, quote=True)
        )

    return LOCAL_IMAGE_RE.sub(replace, text)


# ---------------------------------------------------------------------------
# small helpers / parsing regexes
# ---------------------------------------------------------------------------

META_RE = re.compile(
    r"^\s*-?\s*(?:\*\*)?"
    r"(Status|Date|Primary layer|Decider\(s\)|Deciders?|Predecessors?|状态|日期|决策者|前置决定)"
    r"(?:\*\*)?\s*[:：]\s*(.*)$"
)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
ADR_TOKEN_RE = re.compile(r"ADR-(\d{4}(?:\.\d+)?)")
STATE_REF_RE = re.compile(r"state/([a-z0-9_-]+)\.md")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+[^)]*)?\)")
H2_RE = re.compile(r"^##\s+")
H1_RE = re.compile(r"^#\s+")


def split_head_body(text: str):
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if H2_RE.match(ln):
            return lines[:i], "\n".join(lines[i:])
    return lines, ""


def strip_first_h1(text: str) -> str:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if H1_RE.match(ln):
            del lines[i]
            break
    return "\n".join(lines)


def classify_status(val: str):
    v = val.strip().lower()
    if v.startswith("superseded"):
        return ("Superseded", "superseded")
    if v.startswith("deprecated"):
        return ("Deprecated", "deprecated")
    if v.startswith("proposed"):
        return ("Proposed", "proposed")
    if v.startswith("design"):
        return ("Design / Deferred", "deferred")
    if v.startswith("accepted"):
        if "superseded" in v:
            return ("Accepted → Superseded", "superseded")
        return ("Accepted", "accepted")
    cleaned = re.sub(r"[（(].*", "", val).strip()
    return (cleaned[:28] or "Unknown", "other")


def detect_layers(val: str):
    return [n for n in ("AI 能力", "主权", "姿态") if n in val]


# ---------------------------------------------------------------------------
# parsers
# ---------------------------------------------------------------------------

def parse_adrs(decisions_dir: Path):
    adrs = []
    fre = re.compile(r"^(\d{4}(?:\.\d+)?)-(.+)\.md$")
    for f in sorted(decisions_dir.glob("*.md")):
        m = fre.match(f.name)
        if not m:
            continue  # README.md
        num, slug = m.group(1), m.group(2)
        if num == "0000" or slug == "template":
            continue  # the ADR template is not a decision
        text = f.read_text(encoding="utf-8")
        title = num + " — " + slug.replace("-", " ")
        for ln in text.splitlines():
            if H1_RE.match(ln):
                title = re.sub(r"^#\s+", "", ln).strip()
                title = re.sub(r"^ADR-\d{4}(?:\.\d+)?\s*[:：·-]\s*", "", title, flags=re.I)
                break

        head, body = split_head_body(text)
        head_text = "\n".join(head)
        status_raw = date = layer_raw = ""
        predecessors = []
        for ln in head:
            mm = META_RE.match(ln)
            if not mm:
                continue
            key, val = mm.group(1), mm.group(2).strip()
            if key in ("Status", "状态"):
                status_raw = val
            elif key in ("Date", "日期"):
                date = val
            elif key.startswith("Primary"):
                layer_raw = val
            elif key.startswith("Predecessor") or key == "前置决定":
                predecessors += ADR_TOKEN_RE.findall(val)

        dm = DATE_RE.search(date) or DATE_RE.search(status_raw) or DATE_RE.search(head_text)
        date = dm.group(1) if dm else ""

        status_label, status_class = classify_status(status_raw)
        supersedes = ADR_TOKEN_RE.findall(status_raw) if "superseded by" in status_raw.lower() else []

        refs = set(ADR_TOKEN_RE.findall(body)) | set(predecessors) | set(supersedes)
        refs.discard(num)
        state_refs = sorted(set(STATE_REF_RE.findall(text)))

        adrs.append({
            "num": num, "numsort": float(num), "slug": slug, "file": f.name,
            "title": title, "status_raw": status_raw, "status": status_label,
            "status_class": status_class, "date": date, "layers": detect_layers(layer_raw),
            "predecessors": sorted(set(predecessors)), "supersedes": sorted(set(supersedes)),
            "state_refs": state_refs, "refs": sorted(refs),
            "source_dir": str(f.parent),
            "body_md": strip_first_h1(body) if body else strip_first_h1(text),
        })
    return adrs


def parse_state_docs(state_dir: Path):
    docs = {}
    for f in sorted(state_dir.glob("*.md")):
        if f.name.lower() in ("readme.md", "_template.md"):
            continue
        name = f.stem
        text = f.read_text(encoding="utf-8")
        title = name
        for ln in text.splitlines():
            if H1_RE.match(ln):
                title = re.sub(r"^#\s+", "", ln).strip()
                break
        _, body = split_head_body(text)
        docs[name] = {
            "name": name, "file": f.name, "title": title,
            "adr_refs": sorted(set(ADR_TOKEN_RE.findall(text))),
            "body_md": body or text,
        }
    return docs


def parse_subsystems(agents_file: Path):
    if not agents_file.exists():
        return []
    lines = agents_file.read_text(encoding="utf-8").splitlines()
    subs = []
    for i, ln in enumerate(lines):
        if not ln.startswith("## "):
            continue
        name = ln[3:].strip()
        window = "\n".join(lines[i + 1: i + 7])
        wm = re.search(r"\*\*What\*\*\s*[:：]\s*(.*)", window)
        tm = re.search(r"\*\*Truth\*\*\s*[:：]\s*(.*)", window)
        dm = re.search(r"\*\*Dig\*\*\s*[:：]\s*(.*)", window)
        if wm and tm and dm:
            dig = dm.group(1).strip()
            sdm = STATE_REF_RE.search(dig)
            subs.append({
                "name": name, "what": wm.group(1).strip(), "truth": tm.group(1).strip(),
                "dig": dig, "state_doc": sdm.group(1) if sdm else "",
                "adrs": sorted(set(ADR_TOKEN_RE.findall(dig))),
            })
    return subs


def parse_tables_overview(agents_file: Path):
    if not agents_file.exists():
        return ""
    text = agents_file.read_text(encoding="utf-8")
    m = re.search(r"^##\s+Tables overview.*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s+", rest, re.M)
    return render_md(rest[: nxt.start()] if nxt else rest)


def parse_snapshots(snap_dir: Path):
    snaps = []
    fre = re.compile(r"^(.+)-(assessment|review|alignment)-(\d{4}-\d{2}-\d{2})\.md$")
    for f in sorted(snap_dir.glob("*.md")):
        if f.name.lower() == "readme.md":
            continue
        m = fre.match(f.name)
        text = f.read_text(encoding="utf-8")
        title = f.stem
        for ln in text.splitlines():
            if H1_RE.match(ln):
                title = re.sub(r"^#\s+", "", ln).strip()
                break
        if m:
            topic, kind, date = m.group(1), m.group(2), m.group(3)
        else:
            topic, kind, date = f.stem, "other", ""
        side = {"assessment": "A", "review": "B", "alignment": "solo"}.get(kind, "solo")
        snaps.append({
            "file": f.name, "topic": topic, "kind": kind, "date": date, "side": side,
            "title": title, "has_update": bool(re.search(r"(Update \d{4}|校正|撤回)", text)),
            "body_md": strip_first_h1(text),
        })
    return snaps


def parse_library(docs_dir: Path, root: Path):
    wanted = [
        ("principles", docs_dir / "core" / "principles.md", "seed"),
        ("PROGRESS", docs_dir / "PROGRESS.md", "current"),
        ("HANDOFF", docs_dir / "HANDOFF.md", "current"),
        ("DEVLOG", docs_dir / "DEVLOG.md", "history"),
        ("product-philosophy", docs_dir / "product-philosophy.md", "product"),
        ("backlog", docs_dir / "backlog.md", "ideas"),
        ("docs-README", docs_dir / "README.md", "system"),
        ("decisions-README", docs_dir / "decisions" / "README.md", "system"),
        ("design-README", docs_dir / "design" / "README.md", "system"),
        ("implementation-README", docs_dir / "implementation" / "README.md", "system"),
        ("validation-README", docs_dir / "validation" / "README.md", "system"),
        ("library-README", docs_dir / "library" / "README.md", "library"),
    ]
    for folder, family in (("design", "design"), ("validation", "validation")):
        for f in sorted((docs_dir / folder).glob("*.md")):
            if f.name.lower() == "readme.md":
                continue
            wanted.append((f.stem, f, family))
    for f in sorted((docs_dir / "implementation" / "plans").glob("*.md")):
        wanted.append((f.stem, f, "implementation"))
    library_root = docs_dir / "library"
    if library_root.exists():
        for f in sorted(library_root.rglob("*.md")):
            if f == library_root / "README.md":
                continue
            rel_name = f.relative_to(library_root).with_suffix("").as_posix().replace("/", "-")
            wanted.append(("library-" + rel_name, f, "library"))
    out = []
    for name, f, family in wanted:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        title = name
        for ln in text.splitlines():
            if H1_RE.match(ln):
                title = re.sub(r"^#\s+", "", ln).strip()
                break
        out.append({
            "name": name,
            "title": title,
            "family": family,
            "source": f.relative_to(root).as_posix(),
            "adr_refs": sorted(set(ADR_TOKEN_RE.findall(text))),
            "state_refs": sorted(set(STATE_REF_RE.findall(text))),
            "body_md": strip_first_h1(text),
        })
    return out


# ---------------------------------------------------------------------------
# cross-reference resolution
# ---------------------------------------------------------------------------

class Resolver:
    def __init__(self, adrs, state_docs, library):
        incoming = Counter()
        for a in adrs:
            for r in a["refs"]:
                incoming[r] += 1
        by_num = defaultdict(list)
        for a in adrs:
            by_num[a["num"]].append(a)

        self.num_to_anchor = {}
        for num, group in by_num.items():
            group = sorted(group, key=lambda a: (-incoming[num], a["file"]))
            for idx, a in enumerate(group):
                a["anchor"] = "adr-" + num if idx == 0 else "adr-" + num + "-" + a["slug"]
                if idx == 0:
                    self.num_to_anchor[num] = a["anchor"]
            if len(group) > 1:
                for a in group:
                    a["dup_with"] = [g["title"] for g in group if g is not a]

        self.state_to_anchor = {n: "state-" + n for n in state_docs}
        self.doc_to_anchor = {d["name"].lower(): "lib-" + d["name"] for d in library}
        self.path_to_anchor = {d["source"].lower(): "lib-" + d["name"] for d in library}
        self.doc_to_anchor["handoff"] = "lib-HANDOFF"
        self.doc_to_anchor["readme"] = "lib-docs-README"

    def resolve_href(self, href: str):
        if href.startswith(("#", "http://", "https://", "mailto:")):
            return None
        m = re.search(r"(\d{4}(?:\.\d+)?)-[A-Za-z0-9_-]+\.md", href)
        if m and m.group(1) in self.num_to_anchor:
            return "#" + self.num_to_anchor[m.group(1)]
        ms = STATE_REF_RE.search(href)
        if ms and ms.group(1) in self.state_to_anchor:
            return "#" + self.state_to_anchor[ms.group(1)]
        normalized = href.split("#", 1)[0].split("?", 1)[0].replace("\\", "/").lower()
        for source, anchor in self.path_to_anchor.items():
            docs_relative = source.split("docs/", 1)[-1]
            if normalized.endswith(source) or normalized.endswith(docs_relative):
                return "#" + anchor
        md = re.search(r"([A-Za-z0-9_-]+)\.md", href)
        if md and md.group(1).lower() in self.doc_to_anchor:
            return "#" + self.doc_to_anchor[md.group(1).lower()]
        return ""

    def fix(self, html_str: str) -> str:
        def href_repl(m):
            val = m.group(1)
            new = self.resolve_href(val)
            if new is None:
                if val.startswith("http"):
                    return 'href="' + val + '" target="_blank" rel="noopener"'
                return m.group(0)
            if new == "":
                return 'href="#" class="deadref" title="not in this viewer"'
            return 'href="' + new + '"'

        html_str = re.sub(r'href="([^"]*)"', href_repl, html_str)
        return self._linkify_bare(html_str)

    def _linkify_bare(self, s: str) -> str:
        holds = []

        def stash(m):
            holds.append(m.group(0))
            return "\x00%d\x00" % (len(holds) - 1)

        s = re.sub(r"<a\b.*?</a>", stash, s, flags=re.S)
        s = re.sub(r"<code\b.*?</code>", stash, s, flags=re.S)

        def adr_repl(m):
            anchor = self.num_to_anchor.get(m.group(1))
            return '<a href="#%s" class="adrref">ADR-%s</a>' % (anchor, m.group(1)) if anchor else m.group(0)

        s = ADR_TOKEN_RE.sub(adr_repl, s)
        return re.sub(r"\x00(\d+)\x00", lambda m: holds[int(m.group(1))], s)


# ---------------------------------------------------------------------------
# HTML page builders (one <article class="page"> per document)
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    return htmllib.escape(s, quote=True)


def chip(text, cls="chip"):
    return '<span class="%s">%s</span>' % (cls, esc(text))


def build_overview_page(subs, tables_html, resolver):
    cards = []
    for s in subs:
        adr_chips = "".join(
            '<a class="chip" href="#%s">ADR-%s</a>' % (resolver.num_to_anchor.get(n, ""), n)
            for n in s["adrs"]
        )
        sd = s["state_doc"]
        sd_link = ('<a class="statelink" href="#state-%s">阅读 state/%s.md →</a>' % (sd, sd)) if sd else ""
        cards.append(
            '<div class="card sub"><div class="card-h"><span class="sub-name">%s</span></div>'
            '<div class="kv"><b>What</b> %s</div>'
            '<div class="kv"><b>Truth</b> <code>%s</code></div>'
            '<div class="card-f">%s %s</div></div>'
            % (esc(s["name"]), esc(s["what"]), esc(s["truth"]), sd_link, adr_chips)
        )
    grid = '<div class="grid">' + "".join(cards) + "</div>"
    tables = ('<h2 class="ov-h">Tables overview</h2><div class="md">%s</div>'
              % resolver.fix(tables_html)) if tables_html else ""
    inner = ('<h1 class="page-title">子系统仪表盘</h1>'
             '<p class="lead">从 <code>AGENTS.md</code> 解析。每张卡是一个子系统——点卡片里的链接进入对应的 state doc 或 ADR。</p>'
             + grid + tables)
    return '<article class="page wide" id="overview" data-kind="overview" data-title="子系统仪表盘">' + inner + '</article>'


def build_insights_page(insights):
    items, recent = insights["items"], insights["recent"]
    if items:
        cards = "".join(
            '<div class="ins ins-%s"><div><span class="ins-tag">%s %s</span>'
            '<a class="ins-title" href="#%s">%s</a></div>%s</div>'
            % (it["sev"], it["icon"], esc(it["tag"]), it["page"], esc(it["title"]),
               ('<div class="ins-detail">%s</div>' % esc(it["detail"])) if it["detail"] else "")
            for it in items)
        lint_body = '<div class="ins-list">' + cards + "</div>"
    else:
        lint_body = '<p class="ins-none">✓ 文档体检全部通过。</p>'
    rec = ""
    if recent:
        rec = ('<div class="ins-rec-h">最近动向 · 近 21 天</div><ul class="ins-recent">'
               + "".join("<li>%s</li>" % esc(r) for r in recent) + "</ul>")
    note = ("代码存在性 + git 时效 + 引用图，确定性检查"
            if insights["have_git"] else "代码存在性 + 引用图（未检测到 git）")
    fold = ('<details class="ins-fold"><summary>🔧 文档体检 · 维护用（%d 项 · %s）</summary>'
            '<div class="ins-foldbody">%s%s</div></details>' % (len(items), note, lint_body, rec))
    inner = ('<h1 class="page-title">📍 项目此刻</h1>'
             '<p class="lead">不用提问——一段给人看的项目态势综述（LLM 生成）。'
             '页面底部「文档体检」是给维护用的确定性检查。</p>'
             '<div id="briefing"><div class="brf-loading">正在生成项目态势综述…'
             '（首次约 30–60 秒，之后缓存；需经本地 serve 启动）</div></div>'
             + fold)
    return ('<article class="page wide on" id="insights" data-kind="insights" '
            'data-title="项目此刻">' + inner + "</article>")


def build_graph_page(legend):
    return ('<article class="page wide" id="graph-page" data-kind="graph" data-title="关系图谱">'
            '<h1 class="page-title">关系图谱</h1>'
            '<p class="lead">这里只显示核心事实链：Seed、有效 ADR 与 State。Implementation、Validation、Snapshot 和 Library 仍可从分类导航与搜索抵达，但不伪装成权威事实节点。'
            '<b style="color:#b083f0">紫线</b>=决策关系，灰线=核心文档中的实际引用。悬停高亮，点击跳转，拖拽重排。</p>'
            '<div class="gwrap"><svg id="graph"></svg><div class="legend">' + legend + '</div>'
            '<div class="ghint">拖背景平移 · 滚轮缩放 · 拖动节点 · 点击跳转</div></div></article>')


def build_adr_pages(adrs, resolver):
    order = sorted(adrs, key=lambda a: (a["date"] or "0000-00-00", a["numsort"]))
    items = []
    for a in order:
        body_md = inline_local_images(a["body_md"], Path(a["source_dir"]))
        body = resolver.fix(render_md(body_md))
        layer_chips = "".join(chip(l, "chip layer") for l in a["layers"])
        pred_chips = "".join(
            '<a class="chip" href="#%s">←ADR-%s</a>' % (resolver.num_to_anchor.get(p, ""), p)
            for p in a["predecessors"]
        )
        dup = ('<span class="chip warn" title="%s">⚠ 与 #%s 重号</span>'
               % (esc("; ".join(a["dup_with"])), a["num"])) if a.get("dup_with") else ""
        page = (
            '<article class="page" id="%s" data-kind="adr" data-title="%s">'
            '<h1 class="page-title">ADR-%s · %s <span class="badge %s">%s</span></h1>'
            '<div class="page-sub"><span>📅 %s</span>%s%s%s</div>'
            '<div class="md">%s</div></article>'
            % (a["anchor"], esc(a["title"]), a["num"], esc(a["title"]),
               a["status_class"], esc(a["status"]), esc(a["date"] or "—"),
               layer_chips, pred_chips, dup, body)
        )
        items.append({"id": a["anchor"], "label": "ADR-%s %s" % (a["num"], a["title"]),
                      "dot": a["status_class"], "html": page})
    return items


def build_state_pages(state_docs, resolver):
    items = []
    for name, d in state_docs.items():
        body = resolver.fix(render_md(d["body_md"]))
        page = (
            '<article class="page" id="state-%s" data-kind="state" data-title="%s">'
            '<h1 class="page-title">🧭 %s</h1>'
            '<div class="page-sub"><span class="src">docs/state/%s</span></div>'
            '<div class="md">%s</div></article>'
            % (name, esc(d["title"]), esc(d["title"]), esc(d["file"]), body)
        )
        items.append({"id": "state-" + name, "label": d["title"], "dot": "state", "html": page})
    return items


def build_snap_pages(snaps, resolver):
    order = sorted(snaps, key=lambda s: (s["date"] or "", {"A": 0, "B": 1, "solo": 2}.get(s["side"], 3)),
                   reverse=True)
    items = []
    for s in order:
        body = resolver.fix(render_md(s["body_md"]))
        side_label = {"A": "🟢 supporter", "B": "🔴 skeptic", "solo": "📋 audit"}.get(s["side"], "")
        upd = '<span class="chip warn">含校正</span>' if s["has_update"] else ""
        page = (
            '<article class="page" id="snap-%s" data-kind="snap" data-title="%s">'
            '<h1 class="page-title">%s</h1>'
            '<div class="page-sub"><span>%s</span><span>📅 %s</span>%s</div>'
            '<div class="md">%s</div></article>'
            % (esc(s["file"]), esc(s["title"]), esc(s["title"]), side_label, esc(s["date"] or "—"), upd, body)
        )
        dot = {"A": "accepted", "B": "warn", "solo": "state"}.get(s["side"], "other")
        items.append({"id": "snap-" + s["file"], "label": "%s · %s" % (s["date"] or "?", s["side"]),
                      "dot": dot, "html": page})
    return items


def build_lib_pages(library, resolver):
    items = []
    for d in library:
        body = resolver.fix(render_md(d["body_md"]))
        page = ('<article class="page" id="lib-%s" data-kind="lib" data-title="%s">'
                '<h1 class="page-title">📄 %s</h1><div class="md">%s</div></article>'
                % (d["name"], esc(d["title"]), esc(d["title"]), body))
        dot = {"seed": "accepted", "current": "warn", "implementation": "proposed",
               "validation": "state", "history": "superseded"}.get(d["family"], "other")
        items.append({"id": "lib-" + d["name"], "label": d["title"], "dot": dot,
                      "family": d["family"], "html": page})
    return items


def build_dashboard_page(insights, subs, tables_html, resolver, legend, adrs, state_docs):
    """Bento-style overview: KPI strip + tiled briefing / attention / subsystems / graph."""
    sc = Counter(a["status_class"] for a in adrs)

    def kpi(num, label, sub, warn=False):
        return ('<div class="kpi-card%s"><div class="kpi-num">%d</div>'
                '<div class="kpi-lbl">%s</div><div class="kpi-sub">%s</div></div>'
                % (" warn" if warn else "", num, esc(label), esc(sub)))
    n_attn = insights["counts"]["high"] + insights["counts"]["med"]
    kpis = ('<div class="kpi">'
            + kpi(len(adrs), "决策 ADR",
                  "%d 接受 · %d 提案 · %d 缓议/替代"
                  % (sc.get("accepted", 0), sc.get("proposed", 0), sc.get("deferred", 0) + sc.get("superseded", 0)))
            + kpi(len(state_docs), "状态文档", "子系统现状地图")
            + kpi(n_attn, "需关注", "断链 / 过期 / 悬置", warn=n_attn > 0)
            + kpi(len(insights["recent"]), "近 21 天", "文档改动次数")
            + '</div>')

    attn = [it for it in insights["items"] if it["sev"] in ("high", "med")][:6]
    attn_html = ("".join('<a class="attn-row attn-%s" href="#%s">%s %s</a>'
                         % (it["sev"], it["page"], it["icon"], esc(it["title"]))
                         for it in attn)
                 or '<div class="ins-none">✓ 暂无</div>')

    sub_html = "".join(
        '<a class="submini" href="#state-%s" title="%s"><b>%s</b><span>%s</span></a>'
        % (s["state_doc"], esc(s["what"]), esc(s["name"]), esc(s["what"]))
        for s in subs)

    tables = ('<details class="ins-fold"><summary>📑 Tables overview</summary>'
              '<div class="md ins-foldbody">%s</div></details>' % resolver.fix(tables_html)) if tables_html else ""
    items = insights["items"]
    if items:
        lint_cards = "".join(
            '<div class="ins ins-%s"><div><span class="ins-tag">%s %s</span>'
            '<a class="ins-title" href="#%s">%s</a></div>%s</div>'
            % (it["sev"], it["icon"], esc(it["tag"]), it["page"], esc(it["title"]),
               ('<div class="ins-detail">%s</div>' % esc(it["detail"])) if it["detail"] else "")
            for it in items)
        lint_body = '<div class="ins-list">' + lint_cards + "</div>"
    else:
        lint_body = '<p class="ins-none">✓ 文档体检全部通过。</p>'
    rec = ('<div class="ins-rec-h">最近动向 · 近 21 天</div><ul class="ins-recent">'
           + "".join("<li>%s</li>" % esc(r) for r in insights["recent"]) + "</ul>") if insights["recent"] else ""
    note = ("代码存在性 + git 时效 + 引用图" if insights["have_git"] else "代码存在性 + 引用图（无 git）")
    lint_fold = ('<details class="ins-fold"><summary>🔧 文档体检 · 维护用（%d 项 · %s）</summary>'
                 '<div class="ins-foldbody">%s%s</div></details>' % (len(items), note, lint_body, rec))

    main_tile = (
        '<div class="tile main"><div class="tile-h">📍 项目此刻</div>'
        '<div class="brf-scroll">'
        '<div id="brf-main"><div class="brf-loading">正在生成项目态势综述…（首次约 30–60 秒）</div></div>'
        '<div class="brf-block"><div class="brf-sub">现在活着的约束</div>'
        '<div id="brf-constraints" class="brf-list"></div></div>'
        '<div class="brf-block"><div class="brf-sub">还悬着什么</div>'
        '<div id="brf-open" class="brf-list"></div></div>'
        '</div></div>')
    side_tile = (
        '<div class="side">'
        '<div class="tile"><div class="tile-h">🩺 需要关心</div>' + attn_html + '</div>'
        '<div class="tile"><div class="tile-h">🧩 子系统</div>' + sub_html + '</div>'
        '</div>')
    graph_tile = (
        '<div class="tile graph" id="graph-tile"><div class="tile-h">🕸 关系图谱'
        '<button class="tile-x" onclick="toggleGraphFull()">⤢ 展开</button></div>'
        '<div class="gwrap"><svg id="graph"></svg><div class="legend">' + legend + '</div></div></div>')
    folded = '<div class="tile">' + tables + lint_fold + '</div>'
    inner = ('<div class="page-head"><h1 class="page-title">📊 总览</h1>'
             '<span class="th-right"><span class="upd" id="brf-upd"></span>'
             '<button class="tile-x" onclick="refreshBriefing()">↻ 更新</button></span></div>'
             '<p class="lead">数字为确定性统计；项目此刻态势由 LLM 生成、每条带可点引用。</p>'
             + kpis
             + '<div class="dash-grid">' + main_tile + side_tile + '</div>'
             + graph_tile + folded)
    return '<article class="page wide on" id="dashboard" data-kind="dashboard" data-title="总览">' + inner + '</article>'


def build_timeline(adrs, resolver):
    """Horizontal milestone timeline of ADRs; more-referenced ones are bigger (representative)."""
    indeg = Counter()
    for a in adrs:
        for r in a["refs"]:
            indeg[r] += 1
    order = sorted(adrs, key=lambda a: (a["date"] or "0000-00-00", a["numsort"]))
    items = []
    for a in order:
        n = indeg.get(a["num"], 0)
        sz = 9 + min(11, n * 2)
        big = " big" if n >= 2 else ""
        d = a["date"][5:] if a["date"] else "—"
        items.append('<a class="tl-item%s" href="#%s" title="%s · %s">'
                     '<span class="tl-dot %s" style="width:%dpx;height:%dpx"></span>'
                     '<span class="tl-num">ADR-%s</span><span class="tl-date">%s</span></a>'
                     % (big, a["anchor"], esc(a["title"]), a["date"] or "无日期",
                        a["status_class"], sz, sz, a["num"], d))
    return '<div class="tl-wrap"><div class="tl">' + "".join(items) + '</div></div>'


def build_trends_page():
    def block(icon, title, slot):
        return ('<div class="tile"><div class="tile-h">%s %s</div>'
                '<div id="%s" class="brf-list"><div class="brf-loading">正在综合路线图…（首次约 30–60 秒）</div></div></div>'
                % (icon, title, slot))
    grid = ('<div class="rm-grid">'
            + block("📅", "一周内", "rm-week") + block("🗓", "一个月", "rm-month")
            + block("📆", "一个季度", "rm-quarter") + block("🌅", "一年", "rm-year")
            + '</div>')
    community = ('<div class="tile" style="margin-top:14px">'
                 '<div class="tile-h">🌐 GitHub 趋势嗅探 · 点项目名打开仓库</div>'
                 '<div id="radar-host"><div class="brf-loading">正在联网分析同方向开源项目…'
                 '（首次约 30–60 秒，需本地服务与联网）</div></div></div>')
    inner = ('<div class="page-head"><h1 class="page-title">🔭 开发路线与趋势嗅探</h1>'
             '<span class="th-right"><span class="upd" id="rm-upd"></span>'
             '<button class="tile-x" onclick="refreshTrends()">↻ 更新</button></span></div>'
             '<p class="lead">项目里程碑与多尺度路线来自内部文档；GitHub 趋势嗅探联网寻找同方向开源游戏和开发工具，并给出可核验链接与项目启发。</p>'
             '<div class="tile"><div class="tile-h">⏳ 里程碑时间线 · 点节点跳 ADR</div>'
             '<div id="tl-host" class="tl-wrap"><div class="brf-loading">正在挑选关键里程碑…（首次约 30–60 秒）</div></div></div>'
             '<div style="height:14px"></div>' + grid + community)
    return '<article class="page wide" id="trends" data-kind="trends" data-title="开发路线与趋势嗅探">' + inner + '</article>'


def build_sidebar(adr_items, state_items, snap_items, lib_items):
    def items_html(items):
        return "".join(
            '<a class="nav-item" data-target="%s" title="%s"><span class="dot %s"></span>'
            '<span class="lbl">%s</span></a>' % (it["id"], esc(it["label"]), it["dot"], esc(it["label"]))
            for it in items
        )

    def grp(title, icon, items):
        n = len(items)
        chev = '<span class="nav-chev">▸</span>' if n > 3 else ''
        head = ('<div class="nav-title"><span class="nav-icon">%s</span>'
                '<span class="nav-gname">%s</span><span class="cnt">%d</span>%s</div>'
                % (icon, esc(title), n, chev))
        return '<div class="nav-group">%s<div class="nav-items">%s</div></div>' % (head, items_html(items))

    top = ('<div class="nav-top"><button class="nav-toggle" onclick="toggleNav()" '
           'title="折叠 / 展开侧栏">⟨</button></div>')
    overview_grp = (
        '<div class="nav-group"><div class="nav-title nogrp"><span class="nav-icon">📊</span>'
        '<span class="nav-gname">概览</span></div><div class="nav-items">'
        '<a class="nav-item" data-target="dashboard"><span class="dot warn"></span><span class="lbl">总览仪表盘</span></a>'
        '<a class="nav-item" data-target="trends"><span class="dot proposed"></span><span class="lbl">🔭 路线与趋势</span></a>'
        '</div></div>'
    )
    def family(name):
        return [it for it in lib_items if it.get("family") == name]

    groups = [
        ("当前 Current", "📍", family("current")),
        ("原则 Seed", "🌱", family("seed")),
        ("决策 ADR", "📋", adr_items),
        ("状态 State", "🧩", state_items),
        ("产品 Product", "🧱", family("product")),
        ("设计 Design", "🎨", family("design")),
        ("实施 Implementation", "🛠", family("implementation")),
        ("验证 Validation", "✅", family("validation")),
        ("快照 Snapshots", "📸", snap_items),
        ("想法 Ideas", "💭", family("ideas")),
        ("历史 History", "🕰", family("history")),
        ("资料 Library", "📚", family("library")),
        ("文档系统", "🗂", family("system")),
    ]
    return top + overview_grp + "".join(grp(title, icon, items) for title, icon, items in groups if items)


def build_graph_data(adrs, state_docs, library, resolver):
    nodes, edges, seen, connected = [], [], set(), set()
    for a in adrs:
        nodes.append({"id": a["anchor"], "label": "ADR-" + a["num"], "type": "adr",
                      "status": a["status_class"], "title": a["title"]})
    for name, d in state_docs.items():
        nodes.append({"id": "state-" + name, "label": name, "type": "state",
                      "status": "state", "title": d["title"]})
    for d in library:
        if d["family"] == "seed":
            nodes.append({"id": "lib-" + d["name"], "label": "Seed", "type": "seed",
                          "status": "seed", "title": d["title"]})
    node_ids = {n["id"] for n in nodes}

    def add_edge(s, t, kind):
        if s in node_ids and t in node_ids and s != t and (s, t, kind) not in seen:
            seen.add((s, t, kind))
            connected.add(frozenset((s, t)))
            edges.append({"s": s, "t": t, "kind": kind})

    def add_link_edges(source, markdown):
        for href in MD_LINK_RE.findall(markdown):
            resolved = resolver.resolve_href(href)
            if resolved and resolved.startswith("#"):
                target = resolved[1:]
                if frozenset((source, target)) not in connected:
                    add_edge(source, target, "link")

    seed_docs = [d for d in library if d["family"] == "seed"]
    for d in seed_docs:
        for a in adrs:
            add_edge("lib-" + d["name"], a["anchor"], "constraint")

    for a in adrs:
        for p in a["predecessors"]:
            anc = resolver.num_to_anchor.get(p)
            if anc:
                add_edge(a["anchor"], anc, "pred")
        for sr in a["state_refs"]:
            add_edge(a["anchor"], "state-" + sr, "touch")
    for name, d in state_docs.items():
        for r in d["adr_refs"]:
            anc = resolver.num_to_anchor.get(r)
            if anc:
                add_edge("state-" + name, anc, "rule")
    # Explicit Markdown links only connect documents that belong to the core
    # authority graph. Other families remain navigable and searchable.
    for a in adrs:
        add_link_edges(a["anchor"], a["body_md"])
    for name, d in state_docs.items():
        add_link_edges("state-" + name, d["body_md"])
    for d in seed_docs:
        add_link_edges("lib-" + d["name"], d["body_md"])
    return {"nodes": nodes, "edges": edges}


def build_search_index(adrs, state_docs, snaps, subs, library):
    idx = []

    def add(id_, type_, title, text):
        idx.append({"id": id_, "type": type_, "title": title,
                    "text": re.sub(r"\s+", " ", text)[:1400].lower()})

    add("dashboard", "page", "总览（项目此刻 / 子系统 / 图谱）",
        "dashboard overview 项目此刻 子系统 关系图谱 " + " ".join(s["name"] for s in subs))
    add("trends", "page", "开发路线（周 / 月 / 季 / 年）",
        "开发 进度 路线图 周 月 季 年 待办 roadmap milestone")
    for a in adrs:
        add(a["anchor"], "ADR", "ADR-" + a["num"] + " " + a["title"], a["title"] + " " + a["body_md"])
    for name, d in state_docs.items():
        add("state-" + name, "state", d["title"], d["body_md"])
    for s in snaps:
        add("snap-" + s["file"], "snapshot", s["title"], s["body_md"])
    for d in library:
        add("lib-" + d["name"], d["family"], d["title"], d["body_md"])
    return idx


def graph_legend_html():
    items = [("accepted", "#3ecf8e"), ("proposed", "#f0b429"), ("superseded", "#b083f0"),
             ("deferred", "#56b6e0"), ("deprecated", "#7a8190"), ("state doc", "#6ea8fe"),
             ("Seed", "#58b368")]
    return "".join('<span><i class="dot" style="background:%s"></i>%s</span>' % (c, n) for n, c in items)


# ---------------------------------------------------------------------------
# CSS / JS
# ---------------------------------------------------------------------------

CSS = r"""
:root{
 --hh:54px;
 --sidebar-w:286px;
 --bg:#0f1115; --bg2:#161a22; --bg3:#1d2230; --fg:#dfe3ec; --mut:#98a1b0;
 --line:#2a3142; --acc:#7fb0ff; --code:#0b0e14; --codefg:#cdd6e6;
 --strong:#f2f4f9;
 --scroll-track:rgba(148,163,183,.055); --scroll-thumb:rgba(148,163,183,.32);
 --scroll-thumb-hover:rgba(110,231,221,.54);
 --accepted:#3ecf8e; --proposed:#f0b429; --deprecated:#7a8190;
 --superseded:#b083f0; --deferred:#56b6e0; --other:#9aa3b2; --warn:#ff8f6b; --state:#6ea8fe;
}
body.light{
 --bg:#e9e3d6; --bg2:#faf7f0; --bg3:#f1ece0; --fg:#322e27; --mut:#6f6857;
 --line:#ddd4c1; --acc:#9a6324; --code:#f0ead9; --codefg:#4a4436;
 --strong:#1d1a15;
 --scroll-track:rgba(50,46,39,.045); --scroll-thumb:rgba(111,104,87,.30);
 --scroll-thumb-hover:rgba(154,99,36,.50);
 --accepted:#2f9e6b; --proposed:#9c7508; --deprecated:#8a8475;
 --superseded:#7a52b3; --deferred:#2f7fa8; --other:#8a8475; --warn:#b5562f; --state:#2f6fb0;
}
html:has(body.light){
 --scroll-track:rgba(50,46,39,.045); --scroll-thumb:rgba(111,104,87,.30);
 --scroll-thumb-hover:rgba(154,99,36,.50);
}
*{box-sizing:border-box;scrollbar-width:thin;scrollbar-color:var(--scroll-thumb) var(--scroll-track)}
*::-webkit-scrollbar{width:10px;height:10px}
*::-webkit-scrollbar-track{background:var(--scroll-track)}
*::-webkit-scrollbar-thumb{min-width:36px;min-height:36px;border:2px solid transparent;border-radius:999px;
 background:var(--scroll-thumb);background-clip:padding-box}
*::-webkit-scrollbar-thumb:hover{background:var(--scroll-thumb-hover);background-clip:padding-box}
*::-webkit-scrollbar-corner{background:transparent}
*::-webkit-scrollbar-button{display:none;width:0;height:0}
html,body{margin:0;background:var(--bg);color:var(--fg);
 font:15.5px/1.65 -apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
 transition:background .2s,color .2s}
a{color:var(--acc);text-decoration:none} a:hover{text-decoration:underline}
.deadref{color:var(--mut);cursor:help;text-decoration:underline dotted}
code{background:var(--code);padding:1.5px 6px;border-radius:5px;
 font:13px/1.5 "Cascadia Code",Consolas,monospace;color:var(--codefg);word-break:break-word}

header.top{position:sticky;top:0;z-index:40;height:var(--hh);background:var(--bg);
 border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;padding:0 18px}
.top h1{font-size:15px;margin:0;font-weight:700;white-space:nowrap}
.top .sub{color:var(--mut);font-size:12px}
.rightgrp{margin-left:auto;display:flex;align-items:center;gap:10px}
.tbtn{background:var(--bg3);border:1px solid var(--line);color:var(--fg);
 border-radius:8px;padding:6px 10px;cursor:pointer;font-size:14px;line-height:1}
.tbtn:hover{border-color:var(--acc)}
.searchwrap{position:relative}
#q{background:var(--bg3);border:1px solid var(--line);color:var(--fg);
 padding:7px 11px;border-radius:8px;width:230px;font-size:13px}
#results{position:absolute;right:0;top:40px;width:430px;max-height:70vh;overflow:auto;
 background:var(--bg2);border:1px solid var(--line);border-radius:10px;
 box-shadow:0 12px 40px rgba(0,0,0,.4);display:none}
#results a{display:block;padding:9px 13px;border-bottom:1px solid var(--line);color:var(--fg)}
#results a:hover{background:var(--bg3);text-decoration:none}
#results .rt{font-size:11px;color:var(--mut);text-transform:uppercase;margin-right:7px}

.app{display:flex;align-items:flex-start}
.sidebar{width:var(--sidebar-w);flex:none;position:sticky;top:var(--hh);height:calc(100vh - var(--hh));
 overflow-y:auto;border-right:1px solid var(--line);padding:14px 8px 60px;background:var(--bg);
 transition:width .15s ease}
.sidebar-resizer{width:8px;flex:none;align-self:stretch;position:sticky;top:var(--hh);
 height:calc(100vh - var(--hh));margin-left:-4px;z-index:12;cursor:col-resize;touch-action:none;
 outline:none;background:transparent}
.sidebar-resizer::after{content:"";display:block;width:2px;height:100%;margin:0 auto;
 background:transparent;transition:background .12s}
.sidebar-resizer:hover::after,.sidebar-resizer:focus-visible::after,body.nav-resizing .sidebar-resizer::after{background:var(--acc)}
body.nav-resizing{cursor:col-resize;user-select:none}
body.nav-resizing .sidebar{transition:none}
.nav-top{display:flex;justify-content:flex-end;padding:0 6px 8px}
.nav-toggle{background:var(--bg3);border:1px solid var(--line);color:var(--mut);border-radius:7px;
 padding:3px 10px;cursor:pointer;font-size:13px;line-height:1}
.nav-toggle:hover{color:var(--fg);border-color:var(--acc)}
.nav-group{margin-bottom:4px}
.nav-title{display:flex;align-items:center;gap:7px;cursor:pointer;
 font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);
 padding:8px 10px 5px;user-select:none}
.nav-title:hover{color:var(--fg)} .nav-title.nogrp{cursor:default}
.nav-icon{font-size:14px;flex:none}
.nav-gname{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cnt{opacity:.55;font-size:11px} .nav-chev{font-size:10px;opacity:.7;flex:none}
.nav-group:not(.expanded) .nav-items .nav-item:nth-child(n+4){display:none}
body.nav-collapsed .sidebar{width:52px;padding:8px 0 60px}
body.nav-collapsed .sidebar-resizer{display:none}
body.nav-collapsed .nav-gname,body.nav-collapsed .cnt,body.nav-collapsed .nav-chev,body.nav-collapsed .nav-items{display:none}
body.nav-collapsed .nav-title{justify-content:center;padding:11px 0}
body.nav-collapsed .nav-icon{font-size:20px}
body.nav-collapsed .nav-top{justify-content:center;padding:0 0 8px}
.nav-item{display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:7px;
 font-size:13px;color:var(--fg);cursor:pointer;text-decoration:none}
.nav-item:hover{background:var(--bg3);text-decoration:none}
.nav-item.active{background:var(--bg3);color:var(--acc);font-weight:600}
.nav-item .lbl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0}
.dot{width:8px;height:8px;border-radius:50%;flex:none;display:inline-block}
.dot.accepted{background:var(--accepted)} .dot.proposed{background:var(--proposed)}
.dot.deprecated{background:var(--deprecated)} .dot.superseded{background:var(--superseded)}
.dot.deferred{background:var(--deferred)} .dot.other{background:var(--other)}
.dot.state{background:var(--state)} .dot.warn{background:var(--warn)}

.content{flex:1;min-width:0;padding:0 30px}
.toc{width:212px;flex:none;position:sticky;top:var(--hh);height:calc(100vh - var(--hh));
 overflow-y:auto;padding:24px 14px}
.toc-title{color:var(--mut);text-transform:uppercase;font-size:10.5px;letter-spacing:.05em;margin-bottom:9px}
.toc-link{display:block;padding:4px 9px;border-radius:6px;color:var(--mut);font-size:12.5px;
 border-left:2px solid transparent;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toc-link:hover{color:var(--fg);background:var(--bg3);text-decoration:none}

.page{display:none;max-width:48rem;margin:0 auto;padding:26px 2px 90px}
.page.wide{max-width:72rem}
.page.on{display:block}
.page-title{font-size:23px;line-height:1.3;margin:0 0 8px;color:var(--strong);font-weight:700;
 display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.page-sub{display:flex;gap:8px;flex-wrap:wrap;align-items:center;color:var(--mut);font-size:13px;
 margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--line)}
.ov-h{font-size:16px;margin:30px 0 12px;color:var(--strong)}

.lead{color:var(--mut);font-size:13.5px;line-height:1.7;margin:0 0 20px}
.src{color:var(--mut);font-size:12px;font-family:monospace}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
.card{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:15px}
.card.sub .card-h{display:flex;align-items:center;gap:8px;margin-bottom:9px}
.sub-name{font-weight:700;font-size:15px}
.kv{font-size:13.5px;margin:6px 0;line-height:1.6} .kv b{color:var(--mut);font-weight:600;margin-right:5px}
.card-f{margin-top:11px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.statelink{font-size:12.5px;font-weight:600}
.chip{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:20px;
 background:var(--bg3);color:var(--mut);border:1px solid var(--line)}
.chip.layer{color:var(--superseded);border-color:var(--line)}
.chip.warn{color:var(--warn);border-color:var(--warn);background:transparent}
a.chip:hover{color:var(--fg);text-decoration:none;border-color:var(--acc)}
.badge{font-size:12px;font-weight:700;padding:2px 10px;border-radius:20px;color:#08110b;white-space:nowrap}
.badge.accepted{background:var(--accepted)} .badge.proposed{background:var(--proposed)}
.badge.deprecated{background:var(--deprecated)} .badge.superseded{background:var(--superseded)}
.badge.deferred{background:var(--deferred)} .badge.other{background:var(--other)}

.md{font-size:16px;line-height:1.85}
.md>p,.md>ul,.md>ol,.md>blockquote,.md>h1,.md>h2,.md>h3,.md>h4{max-width:44rem}
.md p{margin:0 0 15px}
.md strong{color:var(--strong);font-weight:600}
.md h2{font-size:17px;margin:32px 0 11px;border-bottom:1px solid var(--line);padding-bottom:6px;color:var(--strong);scroll-margin-top:70px}
.md h3{font-size:15px;margin:22px 0 8px;color:var(--strong);scroll-margin-top:70px}
.md table{border-collapse:collapse;margin:14px 0;font-size:13.5px;width:100%;display:block;overflow-x:auto}
.md img{display:block;max-width:100%;height:auto;margin:18px auto;border-radius:8px}
.md th,.md td{border:1px solid var(--line);padding:7px 11px;text-align:left;line-height:1.5}
.md th{background:var(--bg3)}
.md blockquote{border-left:3px solid var(--acc);margin:14px 0;padding:6px 16px;color:var(--mut);max-width:44rem}
.md pre{background:var(--code);padding:13px 15px;border-radius:8px;overflow-x:auto;line-height:1.5}
.md pre code{background:none;padding:0}
.md ul,.md ol{padding-left:24px} .md li{margin:6px 0;line-height:1.78}
.md li>ul,.md li>ol{margin-top:6px}

#graph{width:100%;height:100%;background:var(--bg2);border:1px solid var(--line);border-radius:12px;cursor:grab}
#graph:active{cursor:grabbing}
.gwrap{position:relative}
.legend{position:absolute;top:12px;left:12px;background:var(--bg2);border:1px solid var(--line);
 border-radius:9px;padding:9px 12px;font-size:12px}
.legend span{display:inline-flex;align-items:center;gap:5px;margin-right:12px}
.ghint{position:absolute;bottom:12px;right:14px;color:var(--mut);font-size:11.5px}
.gnode circle{cursor:pointer;stroke:#0b0e14;stroke-width:1.5}
.gnode text{font:10px monospace;fill:var(--mut);pointer-events:none}
.gnode:hover text{fill:var(--fg)}

.ins-list{display:flex;flex-direction:column;gap:10px;margin:8px auto 16px;max-width:52rem}
.ins{background:var(--bg2);border:1px solid var(--line);border-left:3px solid var(--mut);
 border-radius:10px;padding:11px 15px}
.ins-high{border-left-color:var(--warn)} .ins-med{border-left-color:var(--proposed)}
.ins-low{border-left-color:var(--deferred)}
.ins-tag{font-size:11px;color:var(--mut);margin-right:9px;white-space:nowrap}
.ins-title{font-weight:600;font-size:14px;color:var(--fg)}
.ins-title:hover{color:var(--acc)}
.ins-detail{color:var(--mut);font-size:12.5px;margin-top:5px;line-height:1.6}
.ins-recent{max-width:52rem;margin:0 auto;color:var(--mut);font-size:12.5px;line-height:1.95;
 font-family:"Cascadia Code",Consolas,monospace;list-style:none;padding-left:0}
.ins-none{color:var(--accepted);font-size:14px}
.ins-rec-h{font-size:13px;color:var(--strong);margin:16px 0 7px}
.brf{max-width:46rem;margin:0 auto}
.brf-now{font-size:16px;line-height:1.9;background:var(--bg2);border:1px solid var(--line);
 border-left:3px solid var(--acc);border-radius:10px;padding:15px 18px;color:var(--fg)}
.brf-sec{margin-top:22px}
.brf-sec h3{font-size:14px;color:var(--strong);margin:0 0 8px}
.brf-sec p{margin:0;line-height:1.85}
.brf-sec ul{margin:0;padding-left:22px} .brf-sec li{margin:9px 0;line-height:1.75}
.brf-cites{white-space:normal}
.brf-cite{display:inline-block;font-size:11px;padding:1px 7px;margin:0 2px;border-radius:12px;
 border:1px solid var(--line);background:var(--bg3);color:var(--acc);vertical-align:middle}
.brf-cite:hover{border-color:var(--acc);text-decoration:none}
.brf-loading,.brf-note{color:var(--mut);font-size:13px;max-width:46rem;margin:0 auto;
 padding:16px 0;line-height:1.7}
.ins-fold{max-width:52rem;margin:30px auto 0;border-top:1px solid var(--line)}
.ins-fold>summary{cursor:pointer;color:var(--mut);font-size:13px;padding:11px 0;list-style:none}
.ins-fold>summary::-webkit-details-marker{display:none}
.ins-fold>summary:hover{color:var(--fg)}
.ins-foldbody{padding-top:6px}

.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:4px 0 16px}
.kpi-card{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:13px 15px}
.kpi-card.warn{border-color:var(--warn)}
.kpi-num{font-size:27px;font-weight:700;color:var(--strong);line-height:1.05}
.kpi-card.warn .kpi-num{color:var(--warn)}
.kpi-lbl{font-size:12.5px;color:var(--fg);margin-top:4px}
.kpi-sub{font-size:11px;color:var(--mut);margin-top:2px}
.dash-grid{display:grid;grid-template-columns:1.9fr 1fr;gap:14px;align-items:start;margin-bottom:14px}
.side{display:flex;flex-direction:column;gap:14px;min-width:0}
.rm-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:1000px){.rm-grid{grid-template-columns:1fr}}
.rdr-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.rdr-item{display:block;padding:10px 13px;border:1px solid var(--line);border-radius:10px;color:var(--fg);text-decoration:none}
.rdr-item:hover{border-color:var(--acc);text-decoration:none}
.rdr-h{display:flex;align-items:baseline;gap:8px}
.rdr-name{font-weight:700;font-size:13px;color:var(--acc);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rdr-star{margin-left:auto;font-size:11.5px;color:var(--mut);white-space:nowrap}
.rdr-note{font-size:12.5px;color:var(--mut);margin-top:4px;line-height:1.55}
@media(max-width:1000px){.rdr-grid{grid-template-columns:1fr}}
.page-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.page-head .page-title{margin:0}
.th-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.th-right .tile-x{margin-left:0}
.upd{font-size:11px;color:var(--mut);white-space:nowrap}
.tl-wrap{overflow-x:auto;scrollbar-width:thin;scrollbar-color:transparent transparent}
.tl-wrap:hover{scrollbar-color:var(--line) transparent}
.tl-wrap::-webkit-scrollbar{height:8px}
.tl-wrap::-webkit-scrollbar-thumb{background:transparent;border-radius:4px}
.tl-wrap:hover::-webkit-scrollbar-thumb{background:var(--line)}
.tl{display:flex;gap:20px;position:relative;padding:10px 18px 12px;min-width:max-content}
.tl::before{content:"";position:absolute;left:22px;right:22px;top:41px;height:2px;
 background:linear-gradient(90deg,var(--accepted),var(--acc),var(--superseded));opacity:.5;border-radius:2px}
.tl-item{flex:none;width:140px;display:flex;flex-direction:column;align-items:center;text-decoration:none}
.tl-date{font-size:10px;color:var(--mut);font-family:"Cascadia Code",Consolas,monospace;
 background:var(--bg3);border:1px solid var(--line);border-radius:10px;padding:1px 9px;line-height:16px;margin-bottom:8px}
.tl-dot{width:13px;height:13px;border-radius:50%;background:var(--acc);
 box-shadow:0 0 0 4px color-mix(in srgb,var(--acc) 20%,transparent);
 position:relative;z-index:1;margin-bottom:12px;transition:box-shadow .12s}
.tl-label{font-size:11.5px;color:var(--fg);text-align:center;line-height:1.4;
 background:var(--bg2);border:1px solid var(--line);border-radius:9px;padding:7px 10px;
 transition:transform .12s,border-color .12s,color .12s;
 display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.tl-item:hover .tl-label{transform:translateY(-2px);border-color:var(--acc);color:var(--acc)}
.tl-item:hover .tl-dot{box-shadow:0 0 0 6px color-mix(in srgb,var(--acc) 28%,transparent)}
.tl-dot.accepted{background:var(--accepted)} .tl-dot.proposed{background:var(--proposed)}
.tl-dot.superseded{background:var(--superseded)} .tl-dot.deferred{background:var(--deferred)}
.tl-dot.deprecated{background:var(--deprecated)} .tl-dot.other{background:var(--other)}
.tile{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;min-width:0}
.tile.span2{grid-column:span 2} .tile.span3{grid-column:span 3}
.tile.span4{grid-column:span 4} .tile.span6{grid-column:span 6}
.tile.main{border-left:3px solid var(--acc);display:flex;flex-direction:column}
.tile.main .tile-h{flex:none}
.tile-h{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);
 margin:0 0 11px;display:flex;align-items:center;gap:6px}
.tile-x{margin-left:auto;background:var(--bg3);border:1px solid var(--line);color:var(--mut);
 border-radius:6px;padding:2px 9px;font-size:11px;cursor:pointer}
.tile-x:hover{color:var(--fg);border-color:var(--acc)}
.attn-row{display:block;padding:8px 4px 8px 11px;font-size:13px;color:var(--fg);
 border-bottom:1px solid var(--line);line-height:1.5;border-left:3px solid var(--line)}
.attn-row:last-child{border-bottom:0} .attn-row:hover{color:var(--acc);text-decoration:none}
.attn-high{border-left-color:var(--warn)} .attn-med{border-left-color:var(--proposed)}
.submini{display:block;padding:8px 11px;border:1px solid var(--line);border-radius:9px;margin-bottom:8px;color:var(--fg)}
.submini:last-child{margin-bottom:0} .submini:hover{border-color:var(--acc);text-decoration:none}
.submini b{font-size:13px} .submini span{display:block;font-size:11.5px;color:var(--mut);margin-top:2px;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.brf-scroll{flex:1;min-height:0;overflow-y:auto;padding-right:6px;
 scrollbar-width:thin;scrollbar-color:transparent transparent}
.brf-scroll:hover{scrollbar-color:var(--line) transparent}
.brf-scroll::-webkit-scrollbar{width:8px}
.brf-scroll::-webkit-scrollbar-thumb{background:transparent;border-radius:4px}
.brf-scroll:hover::-webkit-scrollbar-thumb{background:var(--line)}
.brf-block{margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
#brf-main .brf-block:first-child{margin-top:0;padding-top:0;border-top:0}
.brf-sub{font-size:13px;font-weight:700;color:var(--strong);margin-bottom:8px}
.tile.main p{margin:0;font-size:14px;line-height:1.75;color:var(--fg)}
.brf-list ul{margin:0;padding-left:18px} .brf-list li{margin:7px 0;line-height:1.7;font-size:14px}
.tile.graph .gwrap{height:52vh}
.tile.graph.full{position:fixed;inset:14px;z-index:300;margin:0;box-shadow:0 20px 60px rgba(0,0,0,.55)}
.tile.graph.full .gwrap{height:calc(100% - 36px)}
@media(max-width:1000px){.kpi{grid-template-columns:repeat(2,1fr)} .dash-grid{grid-template-columns:1fr}}
@media(max-width:640px){
 .kpi{grid-template-columns:1fr}
 header.top{gap:8px;padding:0 10px}
 .top .sub{display:none}
 .rightgrp{min-width:0;gap:6px}
 .searchwrap{min-width:0}
 #q{width:min(230px,36vw)}
 #results{position:fixed;left:10px;right:10px;top:calc(var(--hh) - 2px);width:auto}
}

@media(max-width:1150px){.toc{display:none}}
@media(max-width:820px){.sidebar,.sidebar-resizer{display:none}}
"""

JS = r"""
const DATA = JSON.parse(document.getElementById('graphdata').textContent);
const SI = JSON.parse(document.getElementById('searchidx').textContent);

function showPage(id){
  let ok=false;
  document.querySelectorAll('.page').forEach(p=>{const on=p.id===id;p.classList.toggle('on',on);if(on)ok=true;});
  if(!ok){if(id!=='overview')showPage('overview');return;}
  document.querySelectorAll('.nav-item').forEach(a=>a.classList.toggle('active',a.dataset.target===id));
  buildToc(id);
  window.scrollTo(0,0);
  try{localStorage.setItem('docPage',id);}catch(e){}
  try{history.replaceState(null,'','#'+id);}catch(e){}
  if(id==='dashboard'){ loadBriefing(); drawGraph(); requestAnimationFrame(syncMainH); }
  if(id==='trends'){ loadRoadmap(); loadMilestones(); loadRadar(); }
  const act=document.querySelector('.nav-item.active');
  if(act){const g=act.closest('.nav-group');if(g)g.classList.remove('collapsed');act.scrollIntoView({block:'nearest'});}
}
function buildToc(id){
  const page=document.getElementById(id), toc=document.getElementById('toc');
  if(!toc) return;
  const hs=page?page.querySelectorAll('.md h2'):[];
  if(!hs||hs.length<2){toc.innerHTML='';return;}
  let h='<div class="toc-title">本页</div>';
  hs.forEach((x,i)=>{if(!x.id)x.id=id+'-s'+i;
    h+='<a class="toc-link" href="#'+x.id+'">'+x.textContent.replace(/</g,'&lt;')+'</a>';});
  toc.innerHTML=h;
}

document.addEventListener('click',e=>{
  const ni=e.target.closest('.nav-item');
  if(ni){e.preventDefault();showPage(ni.dataset.target);return;}
  const nt=e.target.closest('.nav-title');
  if(nt){
    if(document.body.classList.contains('nav-collapsed')){ document.body.classList.remove('nav-collapsed'); saveNav(); return; }
    if(nt.classList.contains('nogrp')) return;
    const g=nt.closest('.nav-group'); g.classList.toggle('expanded');
    const ch=nt.querySelector('.nav-chev'); if(ch) ch.textContent=g.classList.contains('expanded')?'▾':'▸';
    return;
  }
  const a=e.target.closest('a[href^="#"]');
  if(a){
    const id=a.getAttribute('href').slice(1); if(!id) return;
    const t=document.getElementById(id);
    if(t&&t.classList.contains('page')){e.preventDefault();showPage(id);hideResults();return;}
    if(t){const host=t.closest('.page');
      if(host&&!host.classList.contains('on')){e.preventDefault();showPage(host.id);
        setTimeout(()=>{const el=document.getElementById(id);if(el)el.scrollIntoView({behavior:'smooth',block:'start'});},60);}}
  }
});

const q=document.getElementById('q'), results=document.getElementById('results');
function hideResults(){results.style.display='none';}
q.addEventListener('input',()=>{
  const t=q.value.trim().toLowerCase();
  if(t.length<2){hideResults();return;}
  const hits=SI.filter(x=>x.title.toLowerCase().includes(t)||x.text.includes(t)).slice(0,40);
  results.innerHTML = hits.length ? hits.map(h=>
    '<a href="#'+h.id+'"><span class="rt">'+h.type+'</span>'+h.title.replace(/</g,'&lt;')+'</a>').join('')
    : '<a>无匹配</a>';
  results.style.display='block';
});
document.addEventListener('click',e=>{if(!e.target.closest('.searchwrap'))hideResults();});

function applyTheme(t){const l=t==='light';document.body.classList.toggle('light',l);
  try{localStorage.setItem('docTheme',t);}catch(e){}
  const b=document.getElementById('themeToggle');if(b)b.textContent=l?'🌙':'☀';}
function toggleTheme(){applyTheme(document.body.classList.contains('light')?'dark':'light');}

let _brfDone=false;
function esc1(s){return (''+(s||'')).replace(/</g,'&lt;');}
function fmtTs(ts){ if(!ts) return ''; try{const d=new Date(ts*1000),p=n=>(''+n).padStart(2,'0');
  return '更新于 '+p(d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());}catch(e){return '';} }
function citeLabel(c){
  const t=c.title||c.page||'';
  const m=t.match(/ADR-\d{4}(\.\d+)?/); if(m) return m[0];
  if(c.page==='lib-seed') return 'Seed';
  if(c.page&&c.page.indexOf('state-')===0) return c.page.slice(6);
  if(c.page==='lib-backlog') return 'backlog';
  return t.slice(0,14);
}
function _cites(a){ if(!a||!a.length)return''; return ' <span class="brf-cites">'+a.slice(0,6).map(c=>'<a class="brf-cite" href="#'+c.page+'">'+esc1(citeLabel(c))+'</a>').join('')+'</span>'; }
function fillBriefing(d){
  const main=document.getElementById('brf-main');
  if(main) main.innerHTML='<div class="brf-block"><div class="brf-sub">此刻</div><p>'+esc1(d.now&&d.now.text)+_cites(d.now&&d.now.cites)+'</p></div>'
    +'<div class="brf-block"><div class="brf-sub">最近在往哪走</div><p>'+esc1(d.direction&&d.direction.text)+_cites(d.direction&&d.direction.cites)+'</p></div>';
  const c=document.getElementById('brf-constraints');
  if(c) c.innerHTML='<ul>'+((d.constraints)||[]).map(o=>'<li>'+esc1(o.text)+_cites(o.cites)+'</li>').join('')+'</ul>';
  const o=document.getElementById('brf-open');
  if(o) o.innerHTML='<ul>'+((d.open)||[]).map(x=>'<li>'+esc1(x.text)+_cites(x.cites)+'</li>').join('')+'</ul>';
}
function briefingUnavailable(message){
  const note='<div class="brf-note">'+esc1(message)+'</div>';
  ['brf-main','brf-constraints','brf-open'].forEach(id=>{const el=document.getElementById(id);if(el)el.innerHTML=note;});
}
function loadBriefing(){
  if(_brfDone) return;
  const main=document.getElementById('brf-main'); if(!main) return;
  fetch('/briefing').then(r=>r.json()).then(d=>{
    if(d.pending){ setTimeout(loadBriefing,3000); return; }
    _brfDone=true;
    const u=document.getElementById('brf-upd'); if(u) u.textContent=fmtTs(d._ts);
    if(d.error){ briefingUnavailable('态势综述生成失败：'+(d.detail||d.error)); return; }
    fillBriefing(d);
  }).catch(()=>{ _brfDone=true; briefingUnavailable('项目态势需通过 start-docsite.bat 启动，并保持服务窗口打开。'); });
}
function refreshBriefing(){ _brfDone=false; const m=document.getElementById('brf-main');
  if(m) m.innerHTML='<div class="brf-loading">更新中…（约 30–60 秒）</div>';
  fetch('/api/refresh/briefing',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(()=>loadBriefing()).catch(()=>loadBriefing()); }
let _rmDone=false;
function roadmapUnavailable(message){
  const note='<div class="brf-note">'+esc1(message)+'</div>';
  ['rm-week','rm-month','rm-quarter','rm-year'].forEach(id=>{const el=document.getElementById(id);if(el)el.innerHTML=note;});
}
function loadRoadmap(){
  if(_rmDone) return;
  const w=document.getElementById('rm-week'); if(!w) return;
  fetch('/roadmap').then(r=>r.json()).then(d=>{
    if(d.pending){ setTimeout(loadRoadmap,3000); return; }
    _rmDone=true;
    const u=document.getElementById('rm-upd'); if(u) u.textContent=fmtTs(d._ts);
    if(d.error){ roadmapUnavailable('路线图生成失败：'+(d.detail||d.error)); return; }
    const fill=(id,arr)=>{const el=document.getElementById(id); if(!el)return;
      el.innerHTML=(arr&&arr.length)?('<ul>'+arr.map(o=>'<li>'+esc1(o.text)+_cites(o.cites)+'</li>').join('')+'</ul>'):'<div class="brf-note" style="padding:4px 0">暂无近期项</div>';};
    fill('rm-week',d.week); fill('rm-month',d.month); fill('rm-quarter',d.quarter); fill('rm-year',d.year);
  }).catch(()=>{ _rmDone=true; roadmapUnavailable('路线图需通过 start-docsite.bat 启动，并保持服务窗口打开。'); });
}
function refreshRoadmap(){ _rmDone=false; const w=document.getElementById('rm-week');
  if(w) w.innerHTML='<div class="brf-loading">更新中…（约 30–60 秒）</div>';
  fetch('/api/refresh/roadmap',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(()=>loadRoadmap()).catch(()=>loadRoadmap()); }
let _msDone=false;
function loadMilestones(){
  if(_msDone) return;
  const host=document.getElementById('tl-host'); if(!host) return;
  fetch('/milestones').then(r=>r.json()).then(d=>{
    if(d.pending){ setTimeout(loadMilestones,3000); return; }
    _msDone=true;
    if(d.error||!d.milestones||!d.milestones.length){ host.innerHTML='<div class="brf-note" style="padding:8px 2px">（无里程碑）</div>'; return; }
    host.innerHTML='<div class="tl">'+d.milestones.map(m=>{
      const pg=(m.cites&&m.cites[0])?m.cites[0].page:'';
      const dt=(m.date||'').slice(5)||'—';
      return '<a class="tl-item" href="#'+pg+'" title="'+esc1(m.label)+'"><span class="tl-date">'+dt+'</span><span class="tl-dot"></span><span class="tl-label">'+esc1(m.label)+'</span></a>';
    }).join('')+'</div>';
  }).catch(()=>{ _msDone=true; host.innerHTML='<div class="brf-note" style="padding:8px 2px">（里程碑需经本地 serve 加载。）</div>'; });
}
function refreshMilestones(){ _msDone=false; const h=document.getElementById('tl-host');
  if(h) h.innerHTML='<div class="brf-loading">更新中…（约 30–60 秒）</div>';
  fetch('/api/refresh/milestones',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(()=>loadMilestones()).catch(()=>loadMilestones()); }
function refreshTrends(){ refreshRoadmap(); refreshMilestones(); refreshRadar(); }
let _rdDone=false;
function loadRadar(){
  if(_rdDone) return;
  const h=document.getElementById('radar-host'); if(!h) return;
  fetch('/radar').then(r=>r.json()).then(d=>{
    if(d.pending){ setTimeout(loadRadar,3000); return; }
    _rdDone=true;
    if(d.error){ h.innerHTML='<div class="brf-note">对标失败：'+esc1(d.error)+'（GitHub 可能需要代理）</div>'; return; }
    let html='';
    if(d.overview) html+='<p style="margin:0 0 12px;line-height:1.75;font-size:14px">'+esc1(d.overview)+'</p>';
    if(d.competitors&&d.competitors.length){ html+='<div class="rdr-grid">'+d.competitors.map(c=>
      '<a class="rdr-item" href="'+esc1(c.url)+'" target="_blank" rel="noopener"><div class="rdr-h"><span class="rdr-name">'+esc1(c.name)+'</span><span class="rdr-star">⭐'+(c.stars||0)+'</span></div><div class="rdr-note">'+esc1(c.note)+'</div></a>').join('')+'</div>'; }
    if(d.takeaways&&d.takeaways.length){ html+='<div class="brf-sub" style="margin-top:15px">对我们的启发</div><div class="brf-list"><ul>'+d.takeaways.map(t=>'<li>'+esc1(t)+'</li>').join('')+'</ul></div>'; }
    if(d.keywords&&d.keywords.length){ html+='<div class="upd" style="margin-top:11px">搜索词：'+d.keywords.map(esc1).join(' · ')+'</div>'; }
    h.innerHTML=html||'<div class="brf-note">（无对标结果）</div>';
  }).catch(()=>{ _rdDone=true; h.innerHTML='<div class="brf-note">（社区对标需经本地 serve 加载。）</div>'; });
}
function refreshRadar(){ _rdDone=false; const h=document.getElementById('radar-host');
  if(h) h.innerHTML='<div class="brf-loading">更新中…（联网，约 30–60 秒）</div>';
  fetch('/api/refresh/radar',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(()=>loadRadar()).catch(()=>loadRadar()); }
function toggleGraphFull(){
  const t=document.getElementById('graph-tile'); if(!t) return;
  t.classList.toggle('full');
  const b=t.querySelector('.tile-x'); if(b) b.textContent=t.classList.contains('full')?'⤢ 收起':'⤢ 展开';
  if(window.__graphResize) requestAnimationFrame(window.__graphResize);
}
function syncMainH(){
  const g=document.querySelector('.dash-grid'); if(!g) return;
  const s=g.querySelector('.side'), m=g.querySelector('.tile.main'); if(!s||!m) return;
  if(window.innerWidth<=1000){ m.style.height=''; return; }   // single-column: natural height
  m.style.height=s.offsetHeight+'px';                          // left height = right two tiles combined
}
let _rt; window.addEventListener('resize',function(){clearTimeout(_rt);_rt=setTimeout(syncMainH,150);});

let gdrawn=false;
function drawGraph(){
  if(gdrawn) return; gdrawn=true;
  const svg=document.getElementById('graph');
  let W=svg.clientWidth||960, H=svg.clientHeight||620, cx=W/2, cy=H/2; const L=92;
  const COL={accepted:'#3ecf8e',proposed:'#f0b429',deprecated:'#7a8190',
    superseded:'#b083f0',deferred:'#56b6e0',other:'#9aa3b2',state:'#6ea8fe',seed:'#58b368'};
  const N=DATA.nodes.map((n,i)=>({...n,
    x:cx+Math.cos(i*2.39)*Math.min(W,H)*0.4, y:cy+Math.sin(i*2.39)*Math.min(W,H)*0.4, vx:0,vy:0}));
  const idx={}; N.forEach(n=>idx[n.id]=n);
  const E=DATA.edges.filter(e=>idx[e.s]&&idx[e.t]).map(e=>({...e,s:idx[e.s],t:idx[e.t]}));
  const deg={}; E.forEach(e=>{deg[e.s.id]=(deg[e.s.id]||0)+1;deg[e.t.id]=(deg[e.t.id]||0)+1;});
  N.forEach(n=>{ n.r=n.type==='state'?10:n.type==='seed'?11:6+Math.min(8,(deg[n.id]||0)); });
  // warm start (Fruchterman-Reingold) so it opens already spread
  const k=Math.sqrt((W*H)/(N.length||1))*0.6;
  for(let it=0;it<260;it++){ const t=1-it/260;
    N.forEach(n=>{n.dx=0;n.dy=0;});
    for(let i=0;i<N.length;i++)for(let j=i+1;j<N.length;j++){let a=N[i],b=N[j],dx=a.x-b.x,dy=a.y-b.y,d=Math.sqrt(dx*dx+dy*dy)||.5,f=k*k/d;dx/=d;dy/=d;a.dx+=dx*f;a.dy+=dy*f;b.dx-=dx*f;b.dy-=dy*f;}
    E.forEach(e=>{let dx=e.s.x-e.t.x,dy=e.s.y-e.t.y,d=Math.sqrt(dx*dx+dy*dy)||.5,f=d*d/k;dx/=d;dy/=d;e.s.dx-=dx*f;e.s.dy-=dy*f;e.t.dx+=dx*f;e.t.dy+=dy*f;});
    N.forEach(n=>{n.dx+=(cx-n.x)*.02;n.dy+=(cy-n.y)*.02;let dp=Math.hypot(n.dx,n.dy)||1,s=Math.min(dp,18*t+1);n.x+=n.dx/dp*s;n.y+=n.dy/dp*s;});
  }
  const NS='http://www.w3.org/2000/svg'; svg.innerHTML='';
  const view=document.createElementNS(NS,'g'); svg.appendChild(view);
  const gE=document.createElementNS(NS,'g'),gN=document.createElementNS(NS,'g'); view.appendChild(gE); view.appendChild(gN);
  const elE=E.map(e=>{const l=document.createElementNS(NS,'line');
    l.setAttribute('stroke',e.kind==='pred'?'#b083f0':'#5b647a');
    l.setAttribute('stroke-width',e.kind==='pred'?'1.4':'1');
    l.setAttribute('stroke-opacity',e.kind==='pred'?'.55':'.24'); gE.appendChild(l); return l;});
  let pan={x:0,y:0}, zoom=1, dragNode=null, dragMoved=false, panning=false, panStart=null, alpha=0.6;
  function viewT(){ view.setAttribute('transform','translate('+pan.x+','+pan.y+') scale('+zoom+')'); }
  function c2w(ev){ const b=svg.getBoundingClientRect(); return {x:(ev.clientX-b.left-pan.x)/zoom, y:(ev.clientY-b.top-pan.y)/zoom}; }
  const elN=N.map(n=>{
    const g=document.createElementNS(NS,'g'); g.setAttribute('class','gnode');
    const c=document.createElementNS(NS,'circle'); c.setAttribute('r',n.r); c.setAttribute('fill',COL[n.status]||'#999');
    if(n.type==='state'){c.setAttribute('stroke','#fff');c.setAttribute('stroke-width','2');}
    const tx=document.createElementNS(NS,'text'); tx.setAttribute('x',n.r+4); tx.setAttribute('y',4); tx.textContent=n.label;
    g.appendChild(c); g.appendChild(tx);
    g.addEventListener('click',()=>{ if(!dragMoved) showPage(n.id); });
    g.addEventListener('mouseenter',()=>{ tx.style.fontWeight='700'; alpha=Math.max(alpha,.4);
      elE.forEach((l,ei)=>{const h=E[ei].s.id===n.id||E[ei].t.id===n.id; l.setAttribute('stroke-opacity',h?'.95':'.05');}); });
    g.addEventListener('mouseleave',()=>{ tx.style.fontWeight='';
      elE.forEach((l,ei)=>l.setAttribute('stroke-opacity',E[ei].kind==='pred'?'.55':'.24')); });
    g.addEventListener('mousedown',ev=>{ dragNode=n; dragMoved=false; alpha=.6; ev.stopPropagation(); ev.preventDefault(); });
    gN.appendChild(g); return g;
  });
  svg.addEventListener('mousedown',ev=>{ if(ev.target.closest('.gnode'))return; panning=true; panStart={x:ev.clientX-pan.x,y:ev.clientY-pan.y}; });
  window.addEventListener('mousemove',ev=>{
    if(dragNode){ dragMoved=true; const w=c2w(ev); dragNode.x=w.x; dragNode.y=w.y; dragNode.vx=0; dragNode.vy=0; }
    else if(panning){ pan.x=ev.clientX-panStart.x; pan.y=ev.clientY-panStart.y; viewT(); }
  });
  window.addEventListener('mouseup',()=>{ dragNode=null; panning=false; });
  svg.addEventListener('wheel',ev=>{ ev.preventDefault(); const b=svg.getBoundingClientRect(), mx=ev.clientX-b.left, my=ev.clientY-b.top;
    const f=ev.deltaY<0?1.1:0.9, nz=Math.max(.3,Math.min(3,zoom*f));
    pan.x=mx-((mx-pan.x)/zoom)*nz; pan.y=my-((my-pan.y)/zoom)*nz; zoom=nz; viewT(); }, {passive:false});
  function syncSize(){ W=svg.clientWidth||W; H=svg.clientHeight||H; cx=W/2; cy=H/2; alpha=Math.max(alpha,0.5); }
  window.__graphResize=syncSize;
  function render(){ elE.forEach((l,i)=>{l.setAttribute('x1',E[i].s.x);l.setAttribute('y1',E[i].s.y);l.setAttribute('x2',E[i].t.x);l.setAttribute('y2',E[i].t.y);});
    elN.forEach((g,i)=>g.setAttribute('transform','translate('+N[i].x+','+N[i].y+')')); }
  let raf;
  function tick(){
    const pg=svg.closest('.page');
    if(pg&&pg.classList.contains('on')){
      alpha+=(0.05-alpha)*0.02;            // settle toward a gentle perpetual floor (keeps it alive)
      const a=alpha;
      N.forEach(n=>{n.fx=0;n.fy=0;});
      for(let i=0;i<N.length;i++)for(let j=i+1;j<N.length;j++){
        let p=N[i],q=N[j],dx=p.x-q.x,dy=p.y-q.y,d2=dx*dx+dy*dy||1,d=Math.sqrt(d2),f=1700/d2;
        dx/=d;dy/=d; p.fx+=dx*f;p.fy+=dy*f;q.fx-=dx*f;q.fy-=dy*f;
      }
      E.forEach(e=>{ let dx=e.t.x-e.s.x,dy=e.t.y-e.s.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=(d-L)*0.02;
        dx/=d;dy/=d; e.s.fx+=dx*f;e.s.fy+=dy*f; e.t.fx-=dx*f;e.t.fy-=dy*f; });
      N.forEach(n=>{ n.fx+=(cx-n.x)*0.004; n.fy+=(cy-n.y)*0.004;
        n.fx+=(Math.random()-0.5)*1.1*a; n.fy+=(Math.random()-0.5)*1.1*a;
        if(n===dragNode) return;
        n.vx=(n.vx+n.fx*a)*0.9; n.vy=(n.vy+n.fy*a)*0.9;
        let sp=Math.hypot(n.vx,n.vy); if(sp>6){ n.vx*=6/sp; n.vy*=6/sp; }
        n.x+=n.vx; n.y+=n.vy;
      });
      render();
    }
    raf=requestAnimationFrame(tick);
  }
  viewT(); render(); tick();
}

function saveNav(){ try{localStorage.setItem('navCollapsed',document.body.classList.contains('nav-collapsed')?'1':'0');}catch(e){} }
function toggleNav(){ document.body.classList.toggle('nav-collapsed'); saveNav();
  const b=document.querySelector('.nav-toggle'); if(b) b.textContent=document.body.classList.contains('nav-collapsed')?'⟩':'⟨'; }
const NAV_DEFAULT=286,NAV_MIN=220,NAV_MAX=520;
function setNavWidth(value,persist){
  const max=Math.min(NAV_MAX,Math.max(NAV_MIN,window.innerWidth*.45));
  const width=Math.round(Math.max(NAV_MIN,Math.min(max,Number(value)||NAV_DEFAULT)));
  document.documentElement.style.setProperty('--sidebar-w',width+'px');
  const r=document.querySelector('.sidebar-resizer');
  if(r) r.setAttribute('aria-valuenow',''+width);
  if(persist!==false){try{localStorage.setItem('navWidth',''+width);}catch(e){}}
  if(window.__graphResize) requestAnimationFrame(window.__graphResize);
}
function setupNavResize(){
  const r=document.querySelector('.sidebar-resizer'); if(!r)return;
  let startX=0,startW=NAV_DEFAULT,active=false;
  const stop=()=>{if(!active)return;active=false;document.body.classList.remove('nav-resizing');};
  r.addEventListener('pointerdown',e=>{
    if(document.body.classList.contains('nav-collapsed'))return;
    active=true;startX=e.clientX;startW=document.querySelector('.sidebar').getBoundingClientRect().width;
    document.body.classList.add('nav-resizing');r.setPointerCapture(e.pointerId);e.preventDefault();
  });
  r.addEventListener('pointermove',e=>{if(active)setNavWidth(startW+e.clientX-startX,true);});
  r.addEventListener('pointerup',stop);r.addEventListener('pointercancel',stop);
  r.addEventListener('dblclick',()=>setNavWidth(NAV_DEFAULT,true));
  r.addEventListener('keydown',e=>{
    if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight'&&e.key!=='Home')return;
    const current=document.querySelector('.sidebar').getBoundingClientRect().width;
    const next=e.key==='Home'?NAV_DEFAULT:current+(e.key==='ArrowLeft'?-1:1)*(e.shiftKey?40:16);
    setNavWidth(next,true);e.preventDefault();
  });
}
(function(){let t='dark';try{t=localStorage.getItem('docTheme')||'dark';}catch(e){}applyTheme(t);})();
(function(){let w=NAV_DEFAULT;try{w=Number(localStorage.getItem('navWidth'))||NAV_DEFAULT;}catch(e){}setNavWidth(w,false);setupNavResize();})();
(function(){let v='0';try{v=localStorage.getItem('navCollapsed')||'0';}catch(e){}
  if(v==='1'){document.body.classList.add('nav-collapsed');const b=document.querySelector('.nav-toggle');if(b)b.textContent='⟩';}})();
(function(){let id='';try{id=decodeURIComponent(location.hash.slice(1));}catch(e){}
  if(!id){try{id=localStorage.getItem('docPage')||'';}catch(e){}}
  showPage(id||'dashboard');})();
"""


def build_page(title, sidebar, pages_html, graph_json, search_json):
    parts = []
    parts.append('<!doctype html><html lang="zh"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append("<title>" + esc(title) + "</title><style>" + CSS + "</style></head><body>")
    parts.append(
        '<div id="fileBanner" style="display:none;position:sticky;top:0;z-index:9999;'
        'background:#7a2e2e;color:#fff;padding:10px 16px;text-align:center;'
        'font:14px/1.55 system-ui,sans-serif">'
        '⚠️ 这是直接打开的静态 HTML，只能浏览文档；<b>AI 功能</b>'
        '（项目此刻 / 问答 / 开发路线）需要本地服务。请双击项目根目录的<b>启动脚本</b>'
        '（<code style="background:rgba(255,255,255,.22);padding:1px 6px;border-radius:4px">start-docsite.bat</code>），'
        '它会启动服务并自动打开可用版本。</div>'
        "<script>if(location.protocol==='file:'){var b=document.getElementById('fileBanner');if(b)b.style.display='block';}</script>"
    )
    parts.append('<header class="top"><h1>' + esc(title) + "</h1>"
                 '<span class="sub">doc viewer · 源自 markdown</span>'
                 '<div class="rightgrp">'
                 '<button id="themeToggle" class="tbtn" onclick="toggleTheme()" title="切换 浅色 / 深色">☀</button>'
                 '<div class="searchwrap"><input id="q" placeholder="搜索全部…" autocomplete="off">'
                 '<div id="results"></div></div></div></header>')
    parts.append('<div class="app">'
                 '<aside class="sidebar">' + sidebar + '</aside>'
                 '<div class="sidebar-resizer" role="separator" aria-orientation="vertical" '
                 'aria-label="调整左侧栏目宽度" aria-valuemin="220" aria-valuemax="520" '
                 'aria-valuenow="286" tabindex="0" title="拖动调整宽度；双击恢复默认"></div>'
                 '<main class="content">' + pages_html + '</main>'
                 '<aside class="toc" id="toc"></aside>'
                 '</div>')
    parts.append('<script id="graphdata" type="application/json">' + graph_json + "</script>")
    parts.append('<script id="searchidx" type="application/json">' + search_json + "</script>")
    parts.append("<script>" + JS + "</script></body></html>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def render_site(docs_dir: Path, agents_file: Path, root: Path, title="Orrery · Documentation"):
    """Parse all docs and return (html_string, stats). Reused by serve.py."""
    adrs = parse_adrs(docs_dir / "decisions")
    state_docs = parse_state_docs(docs_dir / "state")
    subs = parse_subsystems(agents_file)
    tables_html = parse_tables_overview(agents_file)
    snaps = parse_snapshots(docs_dir / "snapshots") if (docs_dir / "snapshots").exists() else []
    library = parse_library(docs_dir, root)

    resolver = Resolver(adrs, state_docs, library)

    insights = di.compute_insights(adrs, state_docs, subs, resolver, docs_dir, agents_file, root)
    dashboard = build_dashboard_page(insights, subs, tables_html, resolver, graph_legend_html(), adrs, state_docs)
    trends = build_trends_page()
    adr_items = build_adr_pages(adrs, resolver)
    state_items = build_state_pages(state_docs, resolver)
    snap_items = build_snap_pages(snaps, resolver)
    lib_items = build_lib_pages(library, resolver)

    pages_html = dashboard + trends + "".join(
        it["html"] for it in (adr_items + state_items + snap_items + lib_items))
    sidebar = build_sidebar(adr_items, state_items, snap_items, lib_items)
    graph_json = json.dumps(build_graph_data(adrs, state_docs, library, resolver)).replace("</", "<\\/")
    search_json = json.dumps(build_search_index(adrs, state_docs, snaps, subs, library)).replace("</", "<\\/")

    page = build_page(title, sidebar, pages_html, graph_json, search_json)
    stats = {"adrs": len(adrs), "states": len(state_docs), "subs": len(subs),
             "snaps": len(snaps), "documents": len(library),
             "plans": sum(d["family"] == "implementation" for d in library),
             "library": sum(d["family"] == "library" for d in library),
             "dups": sorted({a["num"] for a in adrs if a.get("dup_with")})}
    return page, stats


def _write_authority_shadow_report(path: Path, report: dict) -> None:
    """Atomically write disposable shadow telemetry selected by the operator."""

    path = path.expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
        ) as temporary:
            json.dump(report, temporary, ensure_ascii=False, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary_name = temporary.name
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def _authority_shadow_view_enabled() -> bool:
    return os.environ.get("ORRERY_AUTHORITY_SHADOW_VIEW", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _build_authority_shadow_diagnostic_panel(report: dict) -> str:
    insight = di.compute_authority_shadow_insights(report)
    labels = {
        "match": "一致",
        "mismatch": "有差异",
        "unknown": "Unknown",
        "unavailable": "不可用",
    }
    status = str(insight["status"])
    notices = "".join(
        "<li>%s</li>" % esc(notice) for notice in insight["notices"]
    )
    metrics = (
        '<span style="margin-right:14px">差异 <b>%d</b></span>'
        '<span style="margin-right:14px">未解析关系 <b>%d</b></span>'
        '<span>Validation Unknown <b>%d</b></span>'
        % (
            insight["difference_count"],
            insight["unresolved_relation_count"],
            insight["validation_unknown_count"],
        )
    )
    return (
        '<section id="authority-shadow-diagnostic" '
        'data-view-type="authority-shadow-diagnostic" '
        'data-authoritative="false" data-production-switched="false" '
        'style="margin:0 0 16px;padding:14px 16px;border:1px dashed #b083f0;'
        'border-radius:12px;background:rgba(176,131,240,.08)">'
        '<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">'
        '<b>🧭 Authority Shadow · 非权威诊断</b>'
        '<span class="chip">%s</span><span class="chip">scope: %s</span>'
        '<span class="chip">model: %s</span></div>'
        '<div style="margin-top:9px;font-size:13px">%s</div>'
        '<ul style="margin:9px 0 0;padding-left:20px;font-size:13px;line-height:1.65">%s</ul>'
        '<div style="margin-top:8px;font-size:12px;opacity:.8">'
        '仅显示 Candidate shadow 的比较健康度；不创建或改变 State、ADR、Implementation、Validation。</div>'
        '</section>'
        % (
            esc(labels.get(status, status)),
            esc(insight["fact_scope"]),
            esc(insight["authority_model_status"]),
            metrics,
            notices,
        )
    )


def _inject_authority_shadow_diagnostic(page: str, report: dict) -> str:
    marker = (
        '<article class="page wide on" id="dashboard" '
        'data-kind="dashboard" data-title="总览">'
    )
    if marker not in page:
        raise ValueError("dashboard projection marker not found")
    panel = _build_authority_shadow_diagnostic_panel(report)
    return page.replace(marker, marker + panel, 1)


def _render_site_for_runtime(
    docs_dir: Path,
    agents_file: Path,
    root: Path,
    title: str,
):
    """Optionally dual-run the internal Authority evaluator without switching output.

    ``ORRERY_AUTHORITY_SHADOW_REPORT`` is an experimental maintainer switch.  When
    absent, this is exactly the legacy render path.  When present, supported source
    checkouts can emit a JSON sidecar while the returned HTML/statistics remain the
    legacy renderer's bytes.  Missing packages, invalid manifests, evaluator errors,
    and report-write failures never become production rendering decisions.
    """

    report_target = os.environ.get("ORRERY_AUTHORITY_SHADOW_REPORT", "").strip()
    view_enabled = _authority_shadow_view_enabled()
    if not report_target and not view_enabled:
        page, stats = render_site(docs_dir, agents_file, root, title)
        return page, stats, None

    fact_scope = os.environ.get("ORRERY_AUTHORITY_FACT_SCOPE", "unknown").strip() or "unknown"
    try:
        from project_orrery_core.authority import evaluate_authority
        from project_orrery_core.authority_compatibility import (
            AUTHORITY_MODEL_FIXTURE_IDS,
            judge_project_authority_model,
        )
        from project_orrery_observatory.runtime_shadow import (
            render_with_authority_shadow,
        )

        manifest_path = root / ".project-orrery.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        capability = judge_project_authority_model(manifest)
        selected_version = capability.get("selected_version")
        fixture_version = AUTHORITY_MODEL_FIXTURE_IDS.get(selected_version, "unavailable")
        page, stats, report = render_with_authority_shadow(
            docs_dir,
            agents_file,
            root,
            title,
            legacy_renderer=render_site,
            legacy_adr_parser=parse_adrs,
            evaluator=evaluate_authority,
            authority_model_version=fixture_version,
            fact_scope=fact_scope,
            authority_model_capability=capability,
        )
    except Exception as error:  # the experimental path must fail closed
        page, stats = render_site(docs_dir, agents_file, root, title)
        report = {
            "mode": "shadow",
            "report_schema": "authority-shadow-report-v1",
            "production_authority": "legacy-observatory-renderer",
            "production_behavior_switched": False,
            "shadow": {
                "status": "unavailable",
                "fact_scope": fact_scope,
                "error": {"type": type(error).__name__, "message": str(error)},
            },
        }
    else:
        report = dict(report)
        report["report_schema"] = "authority-shadow-report-v1"

    if view_enabled:
        try:
            page = _inject_authority_shadow_diagnostic(page, report)
        except Exception as error:
            report["derived_view"] = {
                "status": "unavailable",
                "authoritative": False,
                "production_behavior_switched": False,
                "error": {"type": type(error).__name__, "message": str(error)},
            }
        else:
            report["derived_view"] = {
                "status": "rendered",
                "view_type": "authority-shadow-diagnostic",
                "authoritative": False,
                "production_behavior_switched": False,
            }

    if report_target:
        try:
            _write_authority_shadow_report(Path(report_target), report)
        except Exception as error:
            print(
                "WARNING: authority shadow report was not written: %s: %s"
                % (type(error).__name__, error)
            )
    return page, stats, report


def main():
    here = Path(__file__).resolve()
    root = here.parents[2]
    ap = argparse.ArgumentParser(description="Build interactive HTML doc viewer.")
    ap.add_argument("--docs", default=str(root / "docs"))
    ap.add_argument("--agents", default=str(root / "AGENTS.md"))
    ap.add_argument("--out", default=str(root / "docs" / "_site" / "index.html"))
    ap.add_argument("--title", default="Orrery · Documentation")
    args = ap.parse_args()

    page, stats, authority_report = _render_site_for_runtime(
        Path(args.docs), Path(args.agents), root, args.title
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")

    print("doc viewer built:")
    print("  output : %s  (%.0f KB)" % (out, out.stat().st_size / 1024))
    print("  adrs : %(adrs)d | states : %(states)d | subsys : %(subs)d | snaps : %(snaps)d | docs : %(documents)d | plans : %(plans)d | library : %(library)d"
          % stats)
    if stats["dups"]:
        print("  note : duplicate ADR numbers: %s" % ", ".join(stats["dups"]))
    if authority_report is not None:
        shadow = authority_report.get("shadow", {})
        print("  authority shadow : %s" % shadow.get("status", "unavailable"))


if __name__ == "__main__":
    main()
