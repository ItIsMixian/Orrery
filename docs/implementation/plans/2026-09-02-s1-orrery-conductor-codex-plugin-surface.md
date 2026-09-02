# Implementation Plan: S1 Orrery Conductor Codex Plugin Surface

Status: Paused by maintainer; preserve local Candidates for a future native-sidebar extension point

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

## 2026-09-02 scope revision 2 — right-panel primary, inline fallback

The maintainer rejected the Phase A conversation-embedded component. Under ADR-0032, S1 must preserve its clean
`4e44d276ecb16a2acd6e750db243866a11e03961` foundation and change only the host presentation boundary:

1. reuse the existing fixture/schema/UI and expose it at one explicit loopback panel URL;
2. make the Codex-specific Skill/adapter open that URL in the host's right Browser Panel;
3. leave only a short status/link in the conversation and keep inline MCP UI as fallback, not default;
4. use the existing top-right panel toggle rather than attempting to add a new toolbar icon;
5. stop for a real right-panel preview before focused tests or live U2.5 binding.

No Codex binary/private-state patch, second renderer, external network, broad validation, publication or live-data
expansion is authorized.

## 2026-09-02 scope revision 3 — indefinite pause

The maintainer rejected both conversation-inline MCP UI and the right Browser Panel as insufficiently native, then
explicitly paused S1 as a whole. Preserve Phase A exact `4e44d276ecb16a2acd6e750db243866a11e03961` and right-panel
exact `3ac32ec77aa7dec60c63616c858550c3f5067b9a` in the independent repository. Stop the local preview listener and make
no further product, installation, live-binding, validation, publication or Codex-client work.

Future resumption requires a new maintainer decision and task-description version. The preferred trigger is a
supported Codex native sidebar/toolbar extension point; a separate App Server client is only a future option and is
not authorized by this pause record.
