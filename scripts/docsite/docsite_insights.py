#!/usr/bin/env python3
"""Proactive 'doc co-pilot' checks — surface what to care about WITHOUT asking.

Deterministic only (no LLM): code-existence + git recency + reference graph.
Consumed by build_docsite.render_site to render the 🩺 洞察台 (insights) page,
which is the reader's default landing page.

Signals:
  - 断链   : a state doc points at a `src/...py` that no longer exists
  - 可能过期: the referenced code changed N times AFTER the state doc was last edited (git)
  - 悬置   : an ADR is still `Proposed` and old
  - 孤立   : a state doc nobody (ADR / AGENTS / README) links to
  - 重号   : two ADRs share a number
  - 超长   : a state doc over the configurable 200-line soft cap
  - 最近动向: docs/ commits in the last 21 days (git)
"""
from __future__ import annotations

import datetime as _dt
import re
import subprocess
from pathlib import Path

_STATE_REF = re.compile(r"state/([a-z0-9_-]+)\.md")
_CODE_REF = re.compile(
    r"(?:src|app|lib|pkg|internal|cmd|server|client|api|apps|packages)/"
    r"[\w/.{},\-]+\.(?:py|ts|tsx|js|jsx|mjs|cjs|go|java|kt|rb|rs|php|cs|vue|svelte)"
)


def _git(root: Path, *args) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True, timeout=12, encoding="utf-8")
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _expand(p: str):
    """src/app/{loop,prompts}.py -> two concrete paths."""
    if "{" in p and "}" in p:
        pre = p[:p.index("{")]
        inner = p[p.index("{") + 1:p.index("}")]
        suf = p[p.index("}") + 1:]
        return [pre + x + suf for x in inner.split(",")]
    return [p]


def _code_paths(text: str):
    seen, res = set(), []
    for m in _CODE_REF.findall(text):
        for p in _expand(m):
            if p.endswith(".py") and p not in seen:
                seen.add(p)
                res.append(p)
    return res


def compute_insights(adrs, state_docs, subs, resolver, docs_dir: Path,
                     agents_file: Path, root: Path):
    items = []
    have_git = bool(_git(root, "rev-parse", "--is-inside-work-tree"))

    # who references which state doc (for orphan detection)
    referenced = set()
    for a in adrs:
        referenced |= set(a.get("state_refs", []))
    for s in subs:
        if s.get("state_doc"):
            referenced.add(s["state_doc"])
    try:
        referenced |= set(_STATE_REF.findall(agents_file.read_text(encoding="utf-8")))
    except Exception:
        pass
    rd = docs_dir / "README.md"
    if rd.exists():
        referenced |= set(_STATE_REF.findall(rd.read_text(encoding="utf-8")))

    for name, d in state_docs.items():
        page = "state-" + name
        doc_rel = "docs/state/" + d["file"]
        code_paths = _code_paths(d["body_md"])
        missing = [p for p in code_paths if not (root / p).exists()]
        existing = [p for p in code_paths if (root / p).exists()]

        if missing:
            items.append({"sev": "high", "icon": "🔗", "tag": "断链", "page": page,
                          "title": "%s 引用的代码文件已不存在" % name,
                          "detail": "失效路径：" + "， ".join(missing[:4])})

        if have_git and existing:
            h = _git(root, "log", "-1", "--format=%H", "--", doc_rel)
            if h:
                cnt = _git(root, "rev-list", "--count", h + "..HEAD", "--", *existing)
                try:
                    n = int(cnt)
                except ValueError:
                    n = 0
                if n > 0:
                    items.append({"sev": "med", "icon": "⏳", "tag": "可能过期", "page": page,
                                  "title": "%s 定稿后，引用代码又改过 %d 次" % (name, n),
                                  "detail": "建议核对是否同步：" + "， ".join(existing[:4])})

        try:
            lines = (docs_dir / "state" / d["file"]).read_text(encoding="utf-8").count("\n") + 1
            if lines > 200:
                items.append({"sev": "low", "icon": "📏", "tag": "超长", "page": page,
                              "title": "%s 有 %d 行（>200，建议按职责拆分）" % (name, lines),
                              "detail": ""})
        except Exception:
            pass

        if name not in referenced:
            items.append({"sev": "low", "icon": "🏝", "tag": "孤立", "page": page,
                          "title": "%s 没有被任何 ADR / AGENTS 引用" % name,
                          "detail": "可能已废弃，或忘了从别处链接它"})

    today = _dt.date.today()
    dup_seen = set()
    for a in adrs:
        if a["status_class"] == "proposed" and a["date"]:
            try:
                days = (today - _dt.date.fromisoformat(a["date"])).days
                if days > 14:
                    items.append({"sev": "med", "icon": "🕗", "tag": "悬置", "page": a["anchor"],
                                  "title": "ADR-%s 仍是 Proposed（已 %d 天未落定）" % (a["num"], days),
                                  "detail": a["title"]})
            except ValueError:
                pass
        if a.get("dup_with") and a["num"] not in dup_seen:
            dup_seen.add(a["num"])
            items.append({"sev": "low", "icon": "⚠", "tag": "重号", "page": a["anchor"],
                          "title": "ADR-%s 与另一篇共用编号" % a["num"],
                          "detail": "； ".join(a["dup_with"])})

    sev_order = {"high": 0, "med": 1, "low": 2}
    items.sort(key=lambda x: (sev_order.get(x["sev"], 3), x["tag"]))

    recent = []
    if have_git:
        log = _git(root, "log", "--since=21.days", "--date=short",
                   "--pretty=%cd | %s", "--", "docs", "AGENTS.md")
        recent = [ln.strip() for ln in log.splitlines()[:12] if ln.strip()]

    return {"items": items, "recent": recent, "have_git": have_git,
            "counts": {s: sum(1 for it in items if it["sev"] == s) for s in ("high", "med", "low")}}
