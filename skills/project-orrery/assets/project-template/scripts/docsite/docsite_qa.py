#!/usr/bin/env python3
"""Question-answering over the project docs — the 'decision co-pilot' core.

Reuses the markdown parsers from build_docsite.py to build a corpus of
ADRs / state docs / snapshots / seed / classified project documents, then answers a natural-
language question in two LLM passes (via a generic OpenAI-compatible provider):

  1. retrieve : feed the LLM a catalog (id / kind / title / summary) and
                let it pick the most relevant docs (LLM-as-retriever).
  2. answer   : feed the full text of the picked docs and ask for a
                concise answer + the citation ids it actually relied on.

This module is import-friendly: a future local server can call
``build_corpus()`` + ``ask()`` directly. Run as a CLI to validate answer
quality first:

    # Register the managed or external Broker first
    python scripts/docsite/set_key.py
    python -X utf8 scripts/docsite/docsite_qa.py "为什么这样设计?"
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# make `_llm` + `build_docsite` (this dir) importable
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_HERE.parent))

import build_docsite as bd  # noqa: E402

try:  # make Chinese print correctly regardless of console codepage
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------------------------------------------------------------------------
# corpus
# ---------------------------------------------------------------------------

def _summary(text: str, n: int = 200) -> str:
    t = re.sub(r"[#*`>|]+", " ", text)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n]


def _parse_seed_chunks(docs_dir: Path):
    """Split the seed/constitution (docs/core/*.md) into per-## chunks."""
    core = docs_dir / "core"
    chunks = []
    if not core.exists():
        return chunks
    for f in sorted(core.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        # split on H2; keep heading with its body
        parts = re.split(r"(?m)^(##\s+.*)$", text)
        # parts: [pre, h1head, h1body, h2head, h2body, ...]; simpler: scan lines
        sections, cur_title, cur_buf = [], "Seed", []
        for ln in text.splitlines():
            if re.match(r"^##\s+", ln):
                if cur_buf:
                    sections.append((cur_title, "\n".join(cur_buf)))
                cur_title = re.sub(r"^##\s+", "", ln).strip()
                cur_buf = []
            else:
                cur_buf.append(ln)
        if cur_buf:
            sections.append((cur_title, "\n".join(cur_buf)))
        for i, (title, body) in enumerate(sections):
            if not body.strip():
                continue
            chunks.append({"id": "seed-%d" % i, "kind": "seed", "page": "lib-seed",
                           "title": "Seed · " + title, "text": body.strip()})
    return chunks


def build_corpus(docs_dir: Path, agents_file: Path):
    """Return a list of {id, kind, title, text, summary} from all docs."""
    adrs = bd.parse_adrs(docs_dir / "decisions")
    state_docs = bd.parse_state_docs(docs_dir / "state")
    snaps = bd.parse_snapshots(docs_dir / "snapshots") if (docs_dir / "snapshots").exists() else []
    library = bd.parse_library(docs_dir, _ROOT)
    bd.Resolver(adrs, state_docs, library)  # assigns a["anchor"]

    corpus = []
    for a in adrs:
        corpus.append({"id": a["anchor"], "kind": "ADR", "num": a["num"], "date": a["date"],
                       "path": "docs/decisions/" + a["file"],
                       "title": "ADR-%s %s [%s]" % (a["num"], a["title"], a["status"]),
                       "text": a["body_md"]})
    for name, d in state_docs.items():
        corpus.append({"id": "state-" + name, "kind": "state",
                       "path": "docs/state/" + d["file"],
                       "title": "state/%s — %s" % (name, d["title"]), "text": d["body_md"]})
    corpus.extend(_parse_seed_chunks(docs_dir))
    for s in snaps:
        corpus.append({"id": "snap-" + s["file"], "kind": "snapshot",
                       "title": s["title"], "text": s["body_md"]})
    for d in library:
        if d["family"] == "seed":
            continue
        corpus.append({"id": "lib-" + d["name"], "kind": d["family"],
                       "title": d["title"], "text": d["body_md"]})
    for c in corpus:
        c["summary"] = _summary(c["text"])
        c.setdefault("page", c["id"])  # jump target in the reader UI
    return corpus


# ---------------------------------------------------------------------------
# provider
# ---------------------------------------------------------------------------

def get_provider(*, require_broker=True):
    from _llm import make_provider
    p = make_provider(require_broker=require_broker)
    return p, p.name, "(Broker-only project configuration)"


# ---------------------------------------------------------------------------
# Authority-derived view boundary
# ---------------------------------------------------------------------------

_ROUTE_PREFLIGHT = None


def configure_authority_route_preflight(callback=None):
    """Install a host-owned deterministic preflight; ``None`` keeps Skill advisory.

    A plain SKILL.md cannot enforce a pre-model hook.  The root Unified
    Observatory configures this callback to the CLI/Core collector, while
    copied project templates remain honest best-effort consumers.
    """

    global _ROUTE_PREFLIGHT
    if callback is not None and not callable(callback):
        raise TypeError("authority route preflight must be callable or None")
    _ROUTE_PREFLIGHT = callback


def _authority_route_receipt(question: str):
    if _ROUTE_PREFLIGHT is None:
        return None
    try:
        value = _ROUTE_PREFLIGHT(question)
    except Exception as exc:  # noqa: BLE001
        return {
            "schema_version": 1,
            "contract_type": "authority-route-preflight-v1",
            "selection": {"concept_ids": [], "subsystem_ids": [], "ambiguous": True},
            "selected_governing_sources": [],
            "claim_dimensions": {},
            "novelty_absence_gate": {
                "status": "unknown", "absence_claim_allowed": False,
                "reason": "route-preflight-unavailable",
            },
            "negative_evidence": {"complete": False, "unresolved_targets": [str(exc)[:240]]},
        }
    return value if isinstance(value, dict) else None


def _route_selected_ids(receipt, by_id, maximum=6):
    if not isinstance(receipt, dict):
        return []
    by_path = {str(item.get("path", "")).replace("\\", "/"): item["id"] for item in by_id.values()}
    selected = []
    for source in receipt.get("selected_governing_sources", []):
        if not isinstance(source, dict):
            continue
        candidate = by_path.get(str(source.get("path", "")).replace("\\", "/"))
        if candidate and candidate not in selected:
            selected.append(candidate)
        if len(selected) == maximum:
            break
    return selected


def _route_system(system: str, route_receipt=None) -> str:
    if not isinstance(route_receipt, dict):
        return system
    bounded = {
        "contract_type": route_receipt.get("contract_type"),
        "query_class": (route_receipt.get("query") or {}).get("query_class"),
        "concept_ids": (route_receipt.get("selection") or {}).get("concept_ids", []),
        "claim_dimensions": route_receipt.get("claim_dimensions", {}),
        "novelty_absence_gate": route_receipt.get("novelty_absence_gate", {}),
    }
    return (
        system
        + "\n\n# Authority Route Preflight（Core/CLI 机械输入）\n"
        + json.dumps(bounded, ensure_ascii=False, sort_keys=True)
        + "\n四轴必须分别表达。distribution/public 为 absent 不等于 semantic 不存在；"
        "Accepted 不等于 implemented。absence_claim_allowed 不是 true 时，不得声称能力、规则或决定是新的／不存在；证据不足写 Unknown。"
    )

_AUTHORITY_DIMENSIONS = (
    "effective",
    "current",
    "implemented",
    "validated",
    "approved",
    "authoritative",
)
_DERIVED_NOTICE = (
    "> **AI 派生解释**：此回答不会创建、批准或验证项目事实；"
    "请以引用的权威文档、明确 scope 与 Validation 证据为准。\n\n"
)


def build_authority_context(runtime_report=None):
    """Project a runtime report into a small, non-authoritative AI constraint.

    This function only removes information and preserves uncertainty.  It does
    not evaluate Markdown or promote an Observatory shadow result to project
    authority.  Passing an already-normalized context is idempotent.
    """

    if (
        isinstance(runtime_report, dict)
        and runtime_report.get("context_schema")
        == "authority-derived-view-context-v1"
    ):
        scope = str(runtime_report.get("fact_scope") or "unknown")
        if scope not in (
            "canonical",
            "candidate",
            "worktree",
            "local-only",
            "historical",
            "unknown",
        ):
            scope = "unknown"
        deterministic_status = str(
            runtime_report.get("deterministic_status") or "unavailable"
        )
        if deterministic_status not in ("available", "shadow-only", "unavailable"):
            deterministic_status = "unavailable"
        must_not_infer = {
            "derived-view-is-authoritative",
            "summary-is-primary-evidence",
            "accepted-equals-implemented",
            "implemented-equals-validated",
        }
        must_not_infer.update(runtime_report.get("must_not_infer") or [])
        if deterministic_status != "available":
            must_not_infer.update(_AUTHORITY_DIMENSIONS)
        if scope in ("local-only", "unknown"):
            must_not_infer.update(("canonical", "source-code-content"))
        return {
            "context_schema": "authority-derived-view-context-v1",
            "view_type": "derived-ai-view",
            "authoritative": False,
            "creates_project_facts": False,
            "deterministic_status": deterministic_status,
            "authority_model_status": runtime_report.get(
                "authority_model_status", "unavailable"
            ),
            "authority_model_version": runtime_report.get(
                "authority_model_version"
            ),
            "fact_scope": scope,
            "shadow_status": runtime_report.get("shadow_status", "unavailable"),
            "must_not_infer": sorted(must_not_infer),
            "conformance_inputs": list(
                runtime_report.get("conformance_inputs") or []
            ),
        }

    model = runtime_report.get("authority_model", {}) if isinstance(runtime_report, dict) else {}
    shadow = runtime_report.get("shadow", {}) if isinstance(runtime_report, dict) else {}
    scope = str(shadow.get("fact_scope") or "unknown")
    shadow_status = str(shadow.get("status") or "unavailable")
    production_switched = bool(
        isinstance(runtime_report, dict)
        and runtime_report.get("production_behavior_switched") is True
    )
    model_read_only = model.get("read_only") is not False
    if production_switched and not model_read_only and shadow_status == "match":
        deterministic_status = "available"
    elif not model_read_only and shadow_status in ("match", "unknown", "mismatch"):
        deterministic_status = "shadow-only"
    else:
        deterministic_status = "unavailable"

    must_not_infer = {
        "derived-view-is-authoritative",
        "summary-is-primary-evidence",
        "accepted-equals-implemented",
        "implemented-equals-validated",
    }
    if deterministic_status != "available":
        must_not_infer.update(_AUTHORITY_DIMENSIONS)
    if scope in ("local-only", "unknown"):
        must_not_infer.update(("canonical", "source-code-content"))

    conformance_inputs = []
    for key in ("adr", "roles"):
        value = shadow.get(key, {}) if isinstance(shadow, dict) else {}
        candidate = value.get("conformance_input") if isinstance(value, dict) else None
        if isinstance(candidate, dict):
            conformance_inputs.append(
                {
                    "kind": key,
                    "repository_snapshot": candidate.get("repository_snapshot"),
                    "fact_scope": candidate.get("fact_scope"),
                    "evidence_visibility": list(candidate.get("evidence_visibility") or []),
                }
            )

    return {
        "context_schema": "authority-derived-view-context-v1",
        "view_type": "derived-ai-view",
        "authoritative": False,
        "creates_project_facts": False,
        "deterministic_status": deterministic_status,
        "authority_model_status": model.get("status", "unavailable"),
        "authority_model_version": model.get("selected_version"),
        "fact_scope": scope,
        "shadow_status": shadow_status,
        "must_not_infer": sorted(must_not_infer),
        "conformance_inputs": conformance_inputs,
    }


def _authority_system(system: str, authority_context=None) -> str:
    context = build_authority_context(authority_context)
    contract = {
        key: context[key]
        for key in (
            "view_type",
            "authoritative",
            "creates_project_facts",
            "deterministic_status",
            "authority_model_status",
            "authority_model_version",
            "fact_scope",
            "must_not_infer",
        )
    }
    return (
        system
        + "\n\n# Authority 派生视图约束\n"
        + json.dumps(contract, ensure_ascii=False, sort_keys=True)
        + "\n你的输出始终是 derived-ai-view，不是 State、ADR、批准或 Validation。"
        "不得把 must_not_infer 中的状态写成项目权威事实。引用原文时必须明确写成"
        "『该文档声称／记录』；证据不足时保留 Unknown，不得补全为否定或肯定。"
    )


def _derived_receipt(authority_context=None) -> dict:
    context = build_authority_context(authority_context)
    return {
        key: context[key]
        for key in (
            "context_schema",
            "view_type",
            "authoritative",
            "creates_project_facts",
            "deterministic_status",
            "authority_model_status",
            "authority_model_version",
            "fact_scope",
            "must_not_infer",
        )
    }


def _attach_derived_receipt(payload: dict, authority_context=None, route_receipt=None) -> dict:
    result = dict(payload)
    result["_authority"] = _derived_receipt(authority_context)
    if isinstance(route_receipt, dict):
        result["_route"] = route_receipt
    return result


def _derived_failure(error: str, authority_context=None, detail=None, route_receipt=None) -> dict:
    payload = {"error": error}
    if detail is not None:
        payload["detail"] = detail
    return _attach_derived_receipt(payload, authority_context, route_receipt)


# ---------------------------------------------------------------------------
# the two-stage ask
# ---------------------------------------------------------------------------

SEL_SYS = (
    "你是一个检索助手。下面给你一个项目的文档目录(每条含 id / 类型 / 标题 / 摘要)。"
    "根据用户的问题,挑出最相关的最多 6 篇文档,只返回它们的 id。"
    "尽量跨类型覆盖(ADR / state / seed / 快照都考虑),不要只盯着 seed;"
    "宁可多选一两篇相关的,也不要漏掉关键宪法/红线类文档。只输出 JSON。"
)
SEL_SCHEMA = {"type": "object", "properties": {
    "ids": {"type": "array", "items": {"type": "string"}}}, "required": ["ids"]}

ANS_SYS = (
    "你是这个项目的『决策顾问 / 项目记忆』。只依据【参考文档】回答用户的问题,"
    "用中文,简洁、准确、有条理。可以综合多篇。"
    "在 citations 里务必列出你实际依据的文档 id(来自参考文档的标题前缀)。"
    "如果参考文档不足以回答,直说『文档里没有明确答案』,不要编造。只输出 JSON。"
)
ANS_SCHEMA = {"type": "object", "properties": {
    "answer": {"type": "string"},
    "citations": {"type": "array", "items": {"type": "string"}}},
    "required": ["answer", "citations"]}


def ask(
    question: str,
    provider,
    corpus,
    per_doc_chars: int = 4000,
    verbose=False,
    authority_context=None,
):
    from _llm import LLMRequest

    by_id = {c["id"]: c for c in corpus}
    route_receipt = _authority_route_receipt(question)
    route_ids = _route_selected_ids(route_receipt, by_id)
    catalog = "\n".join("- %s [%s] %s :: %s" % (c["id"], c["kind"], c["title"], c["summary"])
                        for c in corpus)
    sel = provider.complete(LLMRequest(
        system=SEL_SYS,
        user="问题:%s\n\n# 文档目录\n%s" % (question, catalog),
        json_schema=SEL_SCHEMA, model_kind="intent", max_tokens=2500))
    if sel.get("parse_error") or sel.get("_provider_disabled"):
        return _derived_failure("retrieve failed", authority_context, sel, route_receipt)
    ids = list(route_ids)
    ids.extend(i for i in sel.get("ids", []) if i in by_id and i not in ids)
    ids = ids[:6]
    if not ids:
        ids = [c["id"] for c in corpus[:4]]  # fallback
    if verbose:
        print("  selected:", ", ".join(ids))

    refs = "\n\n".join("## [%s] %s\n%s" % (i, by_id[i]["title"], by_id[i]["text"][:per_doc_chars])
                       for i in ids)
    ans = provider.complete(LLMRequest(
        system=_route_system(_authority_system(ANS_SYS, authority_context), route_receipt),
        user="问题:%s\n\n# 参考文档\n%s" % (question, refs),
        json_schema=ANS_SCHEMA, model_kind="audit", max_tokens=4000))
    if ans.get("parse_error") or ans.get("_provider_disabled"):
        return _derived_failure("answer failed", authority_context, ans, route_receipt)
    raw = [c for c in ans.get("citations", []) if c in by_id] or ids
    cites, seen = [], set()
    for c in raw:
        pg = by_id[c]["page"]
        if pg in seen:
            continue
        seen.add(pg)
        cites.append({"id": c, "page": pg, "title": by_id[c]["title"]})
    return _attach_derived_receipt(
        {
            "answer": _DERIVED_NOTICE + ans.get("answer", "").strip(),
            "citations": cites,
            "retrieved": ids,
        },
        authority_context,
        route_receipt,
    )


# ---------------------------------------------------------------------------
# streaming answer (token-by-token) — reuses the provider's OpenAI client
# ---------------------------------------------------------------------------

ANS_STREAM_SYS = (
    "你是这个项目的『决策顾问 / 项目记忆』。只依据【参考文档】回答用户问题，"
    "用中文 markdown（可用 - 列表、**重点**、`代码` 等），简洁、准确、有条理，可综合多篇。"
    "如果参考文档不足以回答，直说『文档里没有明确答案』，不要编造。"
)


def ask_stream(provider, corpus, question, per_doc_chars=4000, authority_context=None):
    """Yield answer text deltas, then a trailing '\\n[[CITES]]<json>' line.

    Falls back to one chunk if the provider has no streaming OpenAI client
    (claude / ollama / rules)."""
    from _llm import LLMRequest
    by_id = {c["id"]: c for c in corpus}
    route_receipt = _authority_route_receipt(question)
    route_ids = _route_selected_ids(route_receipt, by_id)
    catalog = "\n".join("- %s [%s] %s :: %s" % (c["id"], c["kind"], c["title"], c["summary"])
                        for c in corpus)
    sel = provider.complete(LLMRequest(
        system=SEL_SYS, user="问题：%s\n\n# 文档目录\n%s" % (question, catalog),
        json_schema=SEL_SCHEMA, model_kind="intent", max_tokens=2500))
    ids = list(route_ids)
    ids.extend(i for i in (sel.get("ids", []) if isinstance(sel, dict) else []) if i in by_id and i not in ids)
    ids = ids[:6]
    if not ids:
        ids = [c["id"] for c in corpus[:4]]
    refs = "\n\n".join("## [%s] %s\n%s" % (i, by_id[i]["title"], by_id[i]["text"][:per_doc_chars])
                       for i in ids)
    cites, seen = [], set()
    for cid in ids:
        pg = by_id[cid]["page"]
        if pg in seen:
            continue
        seen.add(pg)
        cites.append({"id": cid, "page": pg, "title": by_id[cid]["title"]})

    client = getattr(provider, "client", None)
    model = getattr(provider, "audit_model", None)
    if client is None or not model:
        res = ask(question, provider, corpus, authority_context=authority_context)  # non-stream fallback
        yield res.get("answer", "") or res.get("error", "")
        yield "\n[[CITES]]" + json.dumps(res.get("citations", cites), ensure_ascii=False)
        return

    user = "问题：%s\n\n# 参考文档\n%s" % (question, refs)
    yield _DERIVED_NOTICE
    try:
        stream = client.chat.completions.create(
            model=model, max_tokens=4000, stream=True,
            messages=[{"role": "system", "content": _route_system(_authority_system(ANS_STREAM_SYS, authority_context), route_receipt)},
                      {"role": "user", "content": user}])
        for ch in stream:
            try:
                delta = ch.choices[0].delta.content or ""
            except Exception:
                delta = ""
            if delta:
                yield delta
    except Exception as e:  # noqa: BLE001
        yield "\n[[ERROR]] " + repr(e)
        return
    yield "\n[[CITES]]" + json.dumps(cites, ensure_ascii=False)


# ---------------------------------------------------------------------------
# project briefing — the human-facing "what's the state right now" narrative
# ---------------------------------------------------------------------------

_BRF_ITEM = {"type": "object",
             "properties": {"text": {"type": "string"},
                            "cites": {"type": "array", "items": {"type": "string"}}},
             "required": ["text", "cites"]}
BRF_SCHEMA = {"type": "object", "properties": {
    "now": _BRF_ITEM, "direction": _BRF_ITEM,
    "constraints": {"type": "array", "items": _BRF_ITEM},
    "open": {"type": "array", "items": _BRF_ITEM}},
    "required": ["now", "direction", "constraints", "open"]}

BRF_SYS = (
    "你是这个项目的资深维护者，正在用中文跟一个新接手的人（或未来的自己）做 5 分钟口头交接。"
    "依据给你的材料，生成一份『项目此刻态势』。要像人话、抓重点、有判断，不要机械罗列文档标题。\n"
    "每个结论都必须附 cites：这条依据了哪些文档，填它们的 id。"
    "id 只能用材料里方括号 [ ] 标注的那些，绝不要编造不存在的 id。\n"
    "只输出 JSON，字段：\n"
    "- now：{text: 2-3 句，项目是什么 + 现在处在什么阶段, cites:[id...]}\n"
    "- direction：{text: 2-3 句，把最近几个决策连起来看在做什么、往哪走（讲因果）, cites:[id...]}\n"
    "- constraints：[{text: 一句人话红线/原则, cites:[id...]}, ...]（3-6 条）\n"
    "- open：[{text: 一句待定/想做没做的方向, cites:[id...]}, ...]（2-5 条）"
)


def generate_briefing(provider, corpus, authority_context=None):
    """One LLM pass: turn the corpus into a human-facing status brief WITH citations."""
    from _llm import LLMRequest
    by_id = {c["id"]: c for c in corpus}
    adrs = [c for c in corpus if c["kind"] == "ADR"]
    states = [c for c in corpus if c["kind"] == "state"]
    seed = [c for c in corpus if c["kind"] == "seed"]
    backlog = [c for c in corpus if c["id"] == "lib-backlog"]

    adr_list = "\n".join("- [%s] %s" % (c["id"], c["title"]) for c in adrs)
    recent = "\n\n".join("## [%s] %s\n%s" % (c["id"], c["title"], c["text"][:700]) for c in adrs[-6:])
    state_lines = "\n".join("- [%s] %s：%s" % (c["id"], c["title"], c["summary"]) for c in states)
    seed_txt = ("\n".join(c["text"] for c in seed))[:2500]
    backlog_txt = backlog[0]["text"][:2500] if backlog else "（无 backlog）"
    user = ("说明：每段材料前 [方括号] 里是它的文档 id，引用时只用这些 id。\n\n"
            "# 项目宪法 seed（id：lib-seed）\n%s\n\n"
            "# 全部决策 ADR\n%s\n\n"
            "# 最近几个决策（摘要）\n%s\n\n"
            "# 各子系统现状\n%s\n\n"
            "# 待定想法 backlog（id：lib-backlog）\n%s"
            % (seed_txt, adr_list, recent, state_lines, backlog_txt))

    r = provider.complete(LLMRequest(system=_authority_system(BRF_SYS, authority_context), user=user, json_schema=BRF_SCHEMA,
                                     model_kind="audit", max_tokens=4500))
    if r.get("parse_error") or r.get("_provider_disabled"):
        return _derived_failure("briefing failed", authority_context, str(r)[:300])

    def resolve(cites):
        out, seen = [], set()
        for cid in (cites or []):
            c = by_id.get(cid)
            if not c:
                continue  # drop invented / unknown ids
            page = c.get("page", cid)
            if page in seen:
                continue
            seen.add(page)
            out.append({"page": page, "title": c["title"]})
        return out

    def item(x):
        if isinstance(x, dict):
            return {"text": x.get("text", ""), "cites": resolve(x.get("cites"))}
        return {"text": str(x), "cites": []}

    return _attach_derived_receipt(
        {"now": item(r.get("now")), "direction": item(r.get("direction")),
         "constraints": [item(x) for x in (r.get("constraints") or [])],
         "open": [item(x) for x in (r.get("open") or [])]},
        authority_context,
    )


# ---------------------------------------------------------------------------
# roadmap — "what to do" across week / month / quarter / year (trend radar A)
# ---------------------------------------------------------------------------

RM_SCHEMA = {"type": "object", "properties": {
    "week": {"type": "array", "items": _BRF_ITEM},
    "month": {"type": "array", "items": _BRF_ITEM},
    "quarter": {"type": "array", "items": _BRF_ITEM},
    "year": {"type": "array", "items": _BRF_ITEM}},
    "required": ["week", "month", "quarter", "year"]}

RM_SYS = (
    "你是这个项目的规划助手。依据材料，把『想做但还没做』的事按时间尺度归类：\n"
    "- week：一周内能动手的近期小项（小改进 / 收尾 / 低挂果）\n"
    "- month：一个月内的中期功能\n"
    "- quarter：一个季度的较大方向（需要设计、较复杂）\n"
    "- year：一年的愿景 / 远期方向\n"
    "每项一句话，务实、抓重点，不要编材料里没有的东西。每项附 cites（依据的文档 id，"
    "只能用材料里方括号 [ ] 标注的 id）。只输出 JSON。"
)


def generate_roadmap(provider, corpus, authority_context=None):
    from _llm import LLMRequest
    by_id = {c["id"]: c for c in corpus}
    adrs = [c for c in corpus if c["kind"] == "ADR"]
    seed = [c for c in corpus if c["kind"] == "seed"]
    snaps = [c for c in corpus if c["kind"] == "snapshot"]
    backlog = [c for c in corpus if c["id"] == "lib-backlog"]

    adr_list = "\n".join("- [%s] %s" % (c["id"], c["title"]) for c in adrs)
    seed_txt = ("\n".join(c["text"] for c in seed))[:2500]
    backlog_txt = backlog[0]["text"][:3000] if backlog else "（无 backlog）"
    snap_txt = ("\n\n".join("## [%s] %s\n%s" % (c["id"], c["title"], c["text"][:900]) for c in snaps))[:2500]
    user = ("说明：每段材料前 [方括号] 是它的文档 id，引用只用这些 id。\n\n"
            "# 待定想法 backlog（id：lib-backlog）\n%s\n\n"
            "# 项目宪法 seed 摘录（id：lib-seed，含 P0/P1/P2 分层与优先级）\n%s\n\n"
            "# 决策 ADR（标题+状态；Deferred / Design / Proposed 多为想做没落地）\n%s\n\n"
            "# 评估快照（含缺口清单）\n%s"
            % (backlog_txt, seed_txt, adr_list, snap_txt))

    r = provider.complete(LLMRequest(system=_authority_system(RM_SYS, authority_context), user=user, json_schema=RM_SCHEMA,
                                     model_kind="audit", max_tokens=6000))
    if r.get("parse_error") or r.get("_provider_disabled"):
        return _derived_failure("roadmap failed", authority_context, str(r)[:300])

    def resolve(cites):
        out, seen = [], set()
        for cid in (cites or []):
            c = by_id.get(cid)
            if not c:
                continue
            page = c.get("page", cid)
            if page in seen:
                continue
            seen.add(page)
            out.append({"page": page, "title": c["title"]})
        return out

    def item(x):
        if isinstance(x, dict):
            return {"text": x.get("text", ""), "cites": resolve(x.get("cites"))}
        return {"text": str(x), "cites": []}

    return _attach_derived_receipt(
        {k: [item(x) for x in (r.get(k) or [])] for k in ("week", "month", "quarter", "year")},
        authority_context,
    )


# ---------------------------------------------------------------------------
# milestones — the few CORE landmark changes, for the timeline (curated by LLM)
# ---------------------------------------------------------------------------

MS_SCHEMA = {"type": "object", "properties": {"milestones": {"type": "array", "items": {
    "type": "object", "properties": {
        "label": {"type": "string"}, "date": {"type": "string"},
        "cites": {"type": "array", "items": {"type": "string"}}},
    "required": ["label", "cites"]}}}, "required": ["milestones"]}

MS_SYS = (
    "你是这个项目的史官。从下面所有 ADR（标题 / 状态 / 日期）和 seed 里，挑出 6-8 个"
    "**最核心、最关键**的功能 / 架构里程碑（不是全部 ADR，只要真正重要的转折点）。每个：\n"
    "- label：一句话概括这个里程碑做成了什么（12-22 字，面向人、不要直接抄 ADR 标题）\n"
    "- cites：关联的 ADR id（1-2 个，只用材料里方括号 [ ] 的 id）\n"
    "按时间从早到晚排。只输出 JSON。"
)


def generate_milestones(provider, corpus, authority_context=None):
    from _llm import LLMRequest
    by_id = {c["id"]: c for c in corpus}
    adrs = [c for c in corpus if c["kind"] == "ADR"]
    seed = [c for c in corpus if c["kind"] == "seed"]
    adr_list = "\n".join("- [%s] %s（%s）" % (c["id"], c["title"], c.get("date") or "无日期") for c in adrs)
    seed_txt = ("\n".join(c["text"] for c in seed))[:1500]
    user = "# 所有 ADR\n%s\n\n# seed 摘录\n%s" % (adr_list, seed_txt)
    r = provider.complete(LLMRequest(system=_authority_system(MS_SYS, authority_context), user=user, json_schema=MS_SCHEMA,
                                     model_kind="audit", max_tokens=5000))
    if r.get("parse_error") or r.get("_provider_disabled"):
        return _derived_failure("milestones failed", authority_context, str(r)[:300])
    out = []
    for m in (r.get("milestones") or []):
        cites, date = [], m.get("date", "")
        for cid in (m.get("cites") or []):
            c = by_id.get(cid)
            if not c:
                continue
            cites.append({"page": c.get("page", cid), "title": c["title"]})
            if c.get("kind") == "ADR" and c.get("date"):
                date = c["date"]  # use the real ADR date for the axis
        out.append({"label": m.get("label", ""), "date": date, "cites": cites})
    out.sort(key=lambda x: x["date"] or "9999")
    return _attach_derived_receipt({"milestones": out}, authority_context)


# ---------------------------------------------------------------------------
# community radar — compare with open-source peers/trends (trend radar B, LIVE)
# ---------------------------------------------------------------------------

def _gh_search(keyword, token=None, n=5):
    import httpx
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "project-orrery"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = httpx.get("https://api.github.com/search/repositories",
                  params={"q": keyword, "sort": "stars", "order": "desc", "per_page": n},
                  headers=headers, timeout=15)
    r.raise_for_status()
    return r.json().get("items", [])


def _web_search(keyword, n=4):
    try:
        from ddgs import DDGS
        with DDGS() as d:
            return list(d.text(keyword, max_results=n))
    except Exception:
        return []


RADAR_KW_SYS = (
    "从项目定位提炼 3-5 个**英文**搜索词，用来在 GitHub 和网上找**同方向的开源竞品与技术趋势**"
    "（例：'local first knowledge base'、'developer documentation portal'、'project decision tracking'）。"
    "只输出 JSON {\"keywords\":[...]}。"
)
RADAR_EVAL_SYS = (
    "你是项目的竞品分析师。下面是本项目定位，以及从 GitHub / 网上抓回的同方向开源项目与趋势。请：\n"
    "- overview：2-3 句，这个方向的开源现状 + 本项目处在什么位置。\n"
    "- picks：挑 4-8 个最相关的项目，每个 {i: 项目编号, note: 一句话——它是什么 + 和本项目的关系/差异}。\n"
    "- takeaways：2-5 条，对本项目的启发 / 差距 / 可借鉴 / 差异化机会。\n"
    "**所有文字（overview / note / takeaways）一律用简体中文**；项目名与 URL 保留原文。\n"
    "只输出 JSON。i 只用材料里给的项目编号。"
)
_RADAR_EVAL_SCHEMA = {"type": "object", "properties": {
    "overview": {"type": "string"},
    "picks": {"type": "array", "items": {"type": "object", "properties": {
        "i": {"type": "integer"}, "note": {"type": "string"}}, "required": ["i", "note"]}},
    "takeaways": {"type": "array", "items": {"type": "string"}}},
    "required": ["overview", "picks", "takeaways"]}


def generate_radar(provider, corpus, github_token=None, extra_keywords=None, authority_context=None):
    from _llm import LLMRequest
    seed = [c for c in corpus if c["kind"] == "seed"]
    seed_txt = ("\n".join(c["text"] for c in seed))[:1800]

    kw = list(extra_keywords or [])
    try:
        kr = provider.complete(LLMRequest(
            system=_authority_system(RADAR_KW_SYS, authority_context), user="项目定位（seed 摘录）：\n" + seed_txt,
            json_schema={"type": "object", "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}}}, "required": ["keywords"]},
            model_kind="intent", max_tokens=1500))
        kw += [k for k in (kr.get("keywords") or []) if k not in kw]
    except Exception:
        pass
    kw = kw[:5] or ["open source project development tool"]

    repos, seen, errs = [], set(), []
    for k in kw[:4]:
        try:
            for it in _gh_search(k, github_token):
                fn = it.get("full_name")
                if not fn or fn in seen:
                    continue
                seen.add(fn)
                repos.append({"name": fn, "url": it.get("html_url"), "stars": it.get("stargazers_count", 0),
                              "desc": (it.get("description") or "")[:200],
                              "pushed": (it.get("pushed_at") or "")[:10], "topics": (it.get("topics") or [])[:5]})
        except Exception as e:  # noqa: BLE001
            errs.append("github '%s': %r" % (k, e))
    repos.sort(key=lambda r: -r["stars"])
    repos = repos[:14]

    web = []
    for k in kw[:2]:
        for w in _web_search(k):
            web.append({"title": w.get("title", ""), "url": w.get("href") or w.get("url", ""),
                        "snippet": (w.get("body") or "")[:200]})

    if not repos and not web:
        return _derived_failure(
            "联网取数失败（GitHub/web 都没拿到）："
            + ("；".join(errs)[:200] or "无结果"),
            authority_context,
        )

    repo_block = "\n".join("[%d] %s ⭐%d  %s  (%s)  pushed:%s"
                           % (i, r["name"], r["stars"], r["desc"], " ".join(r["topics"]), r["pushed"])
                           for i, r in enumerate(repos))
    web_block = "\n".join("- %s :: %s (%s)" % (w["title"], w["snippet"], w["url"]) for w in web[:6])
    er = provider.complete(LLMRequest(
        system=_authority_system(RADAR_EVAL_SYS, authority_context),
        user="# 本项目定位（seed 摘录）\n%s\n\n# GitHub 同方向项目（编号 [i]）\n%s\n\n# web 趋势片段\n%s"
             % (seed_txt, repo_block, web_block),
        json_schema=_RADAR_EVAL_SCHEMA, model_kind="audit", max_tokens=4000))
    if er.get("parse_error") or er.get("_provider_disabled"):
        return _derived_failure("radar eval failed", authority_context, str(er)[:300])

    comps = []
    for p in (er.get("picks") or []):
        i = p.get("i")
        if isinstance(i, int) and 0 <= i < len(repos):
            r = repos[i]
            comps.append({"name": r["name"], "url": r["url"], "stars": r["stars"], "note": p.get("note", "")})
    return _attach_derived_receipt(
        {"overview": er.get("overview", ""), "competitors": comps,
         "takeaways": er.get("takeaways") or [], "keywords": kw},
        authority_context,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    question = (os.environ.get("QA_Q") or " ".join(sys.argv[1:]).strip()
                or "为什么不让 agent 自己修改自己的 prompt?")
    docs_dir = _ROOT / "docs"
    agents_file = _ROOT / "AGENTS.md"

    corpus = build_corpus(docs_dir, agents_file)
    print("corpus: %d docs" % len(corpus))
    try:
        provider, pname, cfg_path = get_provider(require_broker=True)
    except Exception as e:
        print("FAILED to build provider:", repr(e))
        return
    print("provider: %s   (config: %s)" % (pname, cfg_path))
    print("Q:", question)
    print("-" * 60)
    try:
        res = ask(question, provider, corpus, verbose=True)
    except Exception as e:
        print("LLM call raised:", repr(e))
        return
    if res.get("error"):
        print("ERROR:", res["error"])
        print("detail:", str(res.get("detail"))[:400])
        return
    print("\nA:", res["answer"])
    print("\n引用:")
    for c in res["citations"]:
        print("  - [%s] %s" % (c["id"], c["title"]))


if __name__ == "__main__":
    main()
