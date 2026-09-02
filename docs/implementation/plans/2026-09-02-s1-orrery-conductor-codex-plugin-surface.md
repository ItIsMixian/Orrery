# Implementation Plan: S1 Orrery Conductor Codex Plugin Surface

Status: Approved for implementation; live U2.5 binding and publication remain gated

Date: 2026-09-02

Task code: S1

Program path: explicitly absent — independent product repository

Task series: `orrery-coordination`; intended order `1`; explicit predecessor `S0-orrery-dispatch-skill`

Primary subsystem: `multi-worktree-collaboration`

Affected subsystems: `documentation-system`, `release-and-toolchain`

Governing decision: [ADR-0031](../../decisions/0031-read-only-codex-plugin-surface-for-orrery-conductor.md)

Approved Design: [Orrery Conductor Codex Plugin Surface](../../design/orrery-conductor-codex-plugin-surface.md)

## Objective

Create an independent, read-only Codex plugin that displays Orrery's existing Workstream DAG through a local MCP UI
surface without duplicating Graph facts, layout authority or orchestration permissions.

## Phase A — independent fixture-backed Codex compatibility

1. Work only in a separately assigned projectless directory named for `orrery-conductor`; initialize an independent
   Git repository and `codex/s1-codex-plugin` branch. Never create S1 inside the Project Orrery checkout/worktrees.
2. Read this exact external authority version before product writes and record its SHA in the new repository. Establish
   a minimal local authority/readme boundary without inventing historical implementation facts.
3. Use the supported Codex plugin scaffold to create `.codex-plugin/plugin.json`, a local MCP server, optional discovery
   Skill and one MCP UI resource. Preserve stable IDs from first commit.
4. Define a strict, sanitized adapter contract using a frozen fixture derived from the existing Orrery Graph delivery
   shape. Do not copy Git-private self-host data or depend on Project Orrery source imports.
5. Implement read-only status/snapshot/open-panel tools and render the existing DAG semantics in the MCP UI. Support
   bounded visible-panel refresh and atomic generation replacement; no hidden daemon.
6. Connect through a local development marketplace/profile without replacing or removing any installed plugin. Do not
   restart the app or change global plugin policy without an explicit user gate.
7. Produce a real Codex-hosted preview, then stop for maintainer inspection before broad tests.

## Phase B — gated live binding

After the unique integrator supplies an accepted exact U2.5 delivery-envelope Candidate, replace the fixture adapter
with loopback live binding while retaining fixture fallback for isolated development. Prove update/disconnect/stale
behavior without changing W7.4/U2.5 facts. Phase B is not authorized by a dirty or unaccepted U2.5 worktree.

## Focused post-preview validation

After explicit preview acceptance, run only manifest/schema/MCP lifecycle/UI-owner checks, zero-network negative
controls and clean-repository checks. Do not run Project Orrery Fast/Checkpoint/Candidate/Promotion or publish a
plugin/repository/release.

## Expected implementation surfaces in the new repository

- `.codex-plugin/plugin.json`;
- MCP server source and package metadata;
- MCP UI source/assets;
- optional discovery Skill;
- sanitized fixtures and focused tests;
- new-repository AGENTS/README/Design/Validation/DEVLOG as needed.

## Hard boundaries

- independent directory/repository; no product writes in `project-orrery` or its peer worktrees;
- reuse/adapt the Orrery Graph contract; no new fact selection, relation inference or layout authority;
- read-only Phase A: no task creation, dispatch, confirmation, validation trigger, merge or cleanup;
- no external network, private payloads, credentials, Computer Use or current-user input control;
- no app patching, global plugin replacement, remote repository, push, marketplace submission or release;
- live U2.5 binding waits for an accepted exact dependency.

## Completion definition

- a valid local Codex plugin can open a fixture-backed Orrery DAG UI inside the supported plugin surface;
- tools remain useful without UI and return bounded versioned JSON;
- full/compact and current/stale/unavailable states are understandable and read-only;
- closing the component stops refresh work;
- the maintainer accepts the preview;
- the branch is clean and no live/release capability is overclaimed.
