# U2.3 Unified Navigation, Help Surface & Live Task Visibility

Status: Implemented in the local integration Candidate; final central replay pending

Date: 2026-08-30

Code base: A4 Candidate `3d298a5c408e4fff9cc2206c87a6cdde88f4c165`

Primary subsystem: `documentation-system`

Affected: `project-structure`, `authority-meta-model`, `test-coverage`, `release-and-toolchain`

Dispatch governance: [ADR-0018](../../decisions/0018-authority-first-workstream-dispatch.md)

## Goal

Correct the final Unified Observatory information architecture and restore lightweight visibility of every registered
active Workstream without restoring a full scan of all worktrees at startup.

## Maintainer acceptance scope

- [x] App rail contains Project Overview, Docs & Search, Personal, Team, Workstreams, Maintenance and Routes & Trends.
- [x] Remove the standalone Ask Docs navigation item; the floating Ask Docs control is the only Q&A entry.
- [x] Move Routes & Trends from the project-document tree into the Orrery app rail.
- [x] Remove standalone Authority/Facts & Rules navigation. A top-right help/system-status control opens a read-only
  surface containing Project Principles, Orrery Operating Rules and collapsed fact-interpretation status.
- [x] Keep project documents in the author-document group only; preserve one sidebar and one scroll rail.
- [x] Replace Unified `include_local_worktrees=False` root-only Personal snapshot with a lightweight active-task
  projection from Git worktree registry plus bounded Git-common-private session metadata.
- [x] Use incremental Maintenance cache for workspace status; stale cache keeps task identity visible as “状态待刷新”.
- [x] Do not open every worktree's source, full Scope, ignored files or diff during startup. Heavy evidence is loaded
  only on explicit detail/refresh.
- [x] Dynamic status refresh notices new session revisions without restarting the whole service.
- [x] Personal main view shows task code/name, phase, runtime, primary subsystem and evidence freshness while hiding
  full local paths and raw findings by default.

## Non-goals and safety

- No Graph/series/compare/conflict changes; W7.3 owns them.
- No Authority route/evidence collector changes; A4.1 owns them.
- No Maintenance eligibility/Quick Remove, Team authority, AI provider, network or release/default changes.
- No Codex conversation/Prompt scraping; task truth comes only from Git/Orrery evidence.
- No worktree deletion, Team join or external network during tests.

## Validation

- 20-worktree/4-new-session fixture, stale cache, broken session, missing worktree and primary root;
- mechanical proof that startup does not perform the full status/Scope scan for every worktree;
- single app rail, no ask/authority nav, one floating Ask Docs, Trends in app layer, help surface read-only;
- dynamic session refresh and bounded technical detail;
- 1440×900, 1280×800 and 390×844 browser acceptance, zero page overflow and empty console warnings/errors;
- CI Fast/Checkpoint, repository/release/private-artifact/diff gates.

Implementation updates affected State, independent Validation and DEVLOG/index only. Root PROGRESS/HANDOFF are owned
by central integration.

## 2026-08-30 Maintainer Scope Amendment — Overview Ask Docs Label

- [x] Project Overview may display a non-interactive text line such as “问文档 · 入口位于右下角”.
- [x] The text has no link, button, route, click handler or capability action and cannot look like a second Ask Docs
  entry.
- [x] The floating lower-right “问文档” control remains the only functional Q&A entry; standalone navigation and
  Overview capability buttons remain forbidden.
- [x] Add a mechanical assertion for one functional Ask Docs entry plus the optional informational label.

This amendment changes only wording/presentation inside the accepted navigation model. It does not change AI provider,
network, permission, route or release boundaries and requires no new ADR.
