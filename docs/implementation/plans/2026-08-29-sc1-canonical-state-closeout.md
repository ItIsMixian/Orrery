# Implementation Plan: SC1 Canonical State Closeout

Status: Completed; exact-SHA Fast／Promotion passed and source integrated into protected main

Date: 2026-08-29

Fact scope: `codex/sc1-canonical-state-closeout`, based on clean Canonical
`main@9ee831f0d6f64306fe821f8c70229df54648d3eb`.

Governing authority: [Orrery Product Seed](../../core/principles.md),
[ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0012](../../decisions/0012-document-governance-and-information-lifecycle.md).

## Goal

Reconcile current authority entrances, subsystem State, active Plan status and CI5 hosted evidence with the
actual protected Canonical source. Remove completed-Candidate prose from current-state documents without rewriting
historical ADR／Validation／Snapshot／Pilot evidence.

## Scope

- update AGENTS, PROGRESS, HANDOFF and the four affected subsystem State documents;
- close CI5 hosted acceptance in its Plan／Validation and record the exact run metrics;
- correct stale completion status in CI3, W5C, W5E, W6, W7D and R3 plans;
- fix the Claude／DeepSeek Phase 4 checkbox inversion and mark already implemented W5D discovery/manual Host switch;
- append DEVLOG and refresh Implementation／Validation indexes;
- run dependency-light authority, CI, structure, links and diff checks before Candidate promotion.

## Explicit boundaries

- no product code, component version, release manifest, branch protection, tag or Release changes;
- no rewrite of historical Validation, ADR, Snapshot, frozen v0.2.0 or Pilot inputs;
- Git-private session retirement is local coordination maintenance, not author-document evidence;
- no worktree, local branch, remote branch or ordinary-directory deletion;
- no retroactive `integrated` lifecycle claim where W3 review／closure evidence was never created;
- public v0.2.0 remains the only released version.

## Acceptance

- current entrances agree on `origin/main@9ee831f`, CI5 completion and public v0.2.0 boundaries;
- State contains current source facts and known gaps, while per-run history remains linked through Validation／DEVLOG;
- active Plan inventory no longer reports completed R3／W5C／W5E／W7D／CI3／CI5 promotion as pending;
- Markdown local links, integrated installation, CI static contract, Fast profile and `git diff --check` pass;
- exact Candidate SHA passes non-main Fast and Promotion required Windows／Ubuntu checks before main integration.

## Handoff

After Canonical integration, run a fresh read-only Workstream／maintenance inventory. Any physical cleanup remains a
separate locally confirmed action and must preserve branches／commits unless separately authorized.

SC1 exact `a9369ddeee0e74d4ddbe4bfc23a86b510d400457` passed Fast `33256438925`, Promotion
`33256558285` (25/25 jobs) and main Fast `33256757429`, then entered protected main. This completion changes no
product code, release contract, tag or public release.
