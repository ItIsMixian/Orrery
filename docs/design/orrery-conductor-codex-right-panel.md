# Orrery Conductor Codex Right Panel

Status: Approved

Date: 2026-09-02

Governing ADR: [ADR-0032](../decisions/0032-codex-right-panel-primary-surface-for-orrery-conductor.md)

## Primary flow

```text
user opens Orrery DAG
  -> S1 returns/starts an explicit loopback panel URL
  -> Codex host opens that URL in the existing right Browser Panel
  -> top-right panel toggle hides/reopens the panel
```

The conversation receives only a short status/link, never the full DAG component by default.

## Panel contract

- one responsive, read-only DAG document without the Observatory navigation shell;
- same full/compact, current/stale/unavailable and Unknown semantics as the S1 envelope;
- no prompt/transcript content and no task/relation/cleanup controls;
- bounded polling or notification only while visible;
- deterministic stop and an honest disconnected state when the local source is unavailable.

The existing MCP server may host the panel route or supervise a small loopback companion. It must reuse the Phase A
schema, fixture and UI code rather than create a second renderer.

## Host compatibility

On Codex desktop, the S1 Skill/adapter uses the available host panel-opening capability with right placement. That
capability is Codex-specific and must be isolated behind an adapter. A host without it receives the same local URL or
inline MCP UI fallback.

S1 cannot register a new native toolbar item through the documented plugin manifest. It must not edit Codex internals
to imitate one.

## Preview gate

The maintainer preview passes when the graph appears in the right panel, the existing top-right control can hide and
restore it, the conversation contains no large embedded graph, and closing the panel stops refresh work. Only focused
manifest/server/panel checks may follow acceptance.
