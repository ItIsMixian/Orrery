# ADR-0032: Codex Right Panel as the Primary Orrery Conductor Surface

Status: Accepted

Date: 2026-09-02

Maintainer acceptance: accepted on 2026-09-02 after rejecting S1's conversation-embedded DAG and identifying the
existing Codex right-panel toggle as the intended access pattern.

Amends: [ADR-0031](0031-read-only-codex-plugin-surface-for-orrery-conductor.md)

## Context

S1 Phase A correctly proved a read-only plugin/MCP UI, but MCP Apps UI is returned inside a conversation. The
maintainer instead wants the DAG available in Codex's existing right-side panel, opened and hidden through the same
top-right panel control used for pinned summaries and other Codex panels.

Official plugin documentation defines MCP UI as a component returned alongside the conversation. It does not expose a
supported API for registering a new native Codex toolbar icon or modifying application chrome.

## Decision

1. S1's primary Codex desktop presentation is a local read-only Browser Panel placed on the right. The existing Codex
   panel toggle is reused; S1 does not add a new native button.
2. The S1 compatibility layer exposes one bounded local panel URL/resource and, when the Codex host capability is
   available, asks the host to open it in the right panel. A plain clickable URL/resource remains the fallback.
3. Conversation-embedded MCP Apps UI remains a compatibility fallback only and must not be the default user flow.
4. The panel contains the DAG surface, not the full Observatory shell. It consumes the same versioned sanitized
   fixture/live envelope and does not duplicate fact selection or layout authority.
5. S1 must not patch Codex binaries, private application files or undocumented toolbar state. A dedicated new icon is
   out of scope unless OpenAI later publishes an extension point.
6. The panel performs bounded visible-only refresh and stops when closed. Personal zero-network, read-only authority
   and U2.5 live-binding gates remain unchanged.

## Consequences

- On the current Codex desktop host, the user gets the requested click-to-open right-side experience.
- Other MCP hosts can still use the inline component or resource link without inheriting Codex-specific assumptions.
- “Native right panel” means content hosted in Codex's existing panel container, not a custom first-class toolbar
  extension.

## Mapping

- Approved Design: [Orrery Conductor Codex Right Panel](../design/orrery-conductor-codex-right-panel.md)
- Amended Plan: [S1 Orrery Conductor Codex Plugin Surface](../implementation/plans/2026-09-02-s1-orrery-conductor-codex-plugin-surface.md)
- Pending Validation: [S1 Orrery Conductor Codex Plugin Surface](../validation/2026-09-02-s1-orrery-conductor-codex-plugin-surface.md)
- Official OpenAI documentation: [Add UI to an MCP server](https://developers.openai.com/plugins/build/chatgpt-ui)
