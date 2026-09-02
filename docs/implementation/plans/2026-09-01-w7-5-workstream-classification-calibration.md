# Implementation Plan: W7.5 Workstream Classification Calibration

Status: Approved for implementation after accepted clean W7.4 Candidate

Date: 2026-09-01

Task code: W7.5

Program path: `workstream-w / workstream-w7`

Task series: `w7-integration`; intended order `3`; explicit predecessor `W7.4-workstream-history-relation-decision-ux`

Primary subsystem: `multi-worktree-collaboration`

Affected subsystems: `documentation-system`, `release-and-toolchain`, `test-coverage`

Governing decision: [ADR-0029](../../decisions/0029-explicit-workstream-classification-and-dispatch-registration.md)

Approved Design: [Workstream Classification Calibration and Dispatch Registration](../../design/workstream-classification-calibration-and-dispatch-registration.md)

## Objective

Calibrate missing self-host program/phase and task-series metadata through evidence-bound human decisions, then make
future authority-first task registration explicit enough that accidental unclassified tasks stop accumulating.

## Dependency gate

Do not create or start product work until the unique integrator provides the accepted frozen clean W7.4 exact
Candidate. W7.5 Phase A may begin while that Candidate's asynchronous validation is pending, but W7.5 integration and
classification apply cannot outrun required W7.4 validation. The lifecycle split, 11 recovered archived-lineage edges,
full/compact zero-overlap geometry and classification diagnostics are immutable inputs to W7.5, not work to redo.

## Phase A — read-only audit and review preview

1. Register W7.5 on an independent branch/worktree from the exact task-description version and exact W7.4 dependency.
   Bind the explicit W7 program/series classification above, acknowledge authority paths and refresh scope before writes.
2. Recompute classification coverage for live/provider/history/full-visible inventories. Record primary/affected,
   program/phase, series/order/predecessor, explicit absence reasons and evidence classes independently.
3. Mechanically retain existing effective events. Build proposals only from explicit committed task authority or
   complete source-bound session registration. Produce negative controls for name/code/branch/time/ancestry inference.
4. Implement a deterministic Core/CLI audit and proposal model with bounded counts, source links, conflict reasons,
   read-only/no-write/no-network flags and exact revisions.
5. Add the Personal `任务分类待确认` preview with plain questions, effects, evidence limits, individual adjustment and
   transparent batch composition. Unknown/no-evidence items have no Accept action.
6. Keep Graph read-only. It may display current accepted classification diagnostics and explicit unclassified labels,
   but Phase A writes no program/series event and changes no Graph facts/geometry.
7. Start a real local preview and stop for maintainer inspection before any unittest/Fast/Checkpoint/Candidate/Promotion.
   Syntax/import checks needed to render the preview are allowed.

## Maintainer preview acceptance

The maintainer can:

- distinguish lifecycle state from program/series classification;
- understand why each actionable proposal exists without opening technical details;
- inspect every task in a proposed batch and remove/change individual entries;
- deliberately keep a task unclassified;
- verify that no-evidence/name-only candidates cannot be accepted;
- verify that accepting classification is described as organization-only with no relation/cleanup effect.

## Phase B — confirmed events and future registration enforcement

8. Apply only maintainer-accepted classifications through append-only, CAS-protected local events and per-task receipts.
   Preserve rejected/deferred/changed history and all prior effective events.
9. Recompute provider/history/Graph coverage and prove accepted metadata appears while untouched tasks remain
   unclassified. Relation IDs/counts, lifecycle counts and W7.4 full/compact admission/geometry remain unchanged.
10. Add Core/CLI classification-envelope validation to Workstream registration. Primary subsystem and explicit
    program/series values or absence reasons are required for new authority-first tasks.
11. Update source `orrery-dispatch` to transport the envelope and refuse incomplete registration without deciding
    classification itself. Do not install/publish the changed Skill outside the repository in this task.
12. After Phase B preview acceptance, run only focused classification/Core/CLI/Personal owners, negative inference
    controls, affected dispatch structure checks, Graph non-effect checks and `git diff --check`. Broader tiers remain
    separately authorized.

## Expected implementation surfaces

- Core collaboration/program-hierarchy/task-series classification contracts and storage;
- CLI Workstream registration/audit/proposal/decision commands;
- Personal Observatory classification-review projection;
- `skills/orrery-dispatch/` source instructions/config only where the validated envelope is transported;
- focused existing owner tests after preview acceptance;
- affected subsystem State, W7.5 Validation and DEVLOG in the task branch.

Root PROGRESS/HANDOFF remain unique-integrator owned. W7.4 Graph geometry/presentation and U2.5 runtime/cache files are
outside W7.5 expected writes.

## Hard boundaries

- no classification inference from names, codes, prefixes, branches, timestamps, visual order or lineage;
- no automatic/bulk silent confirmation, AI classification or Agent confirmation authority;
- no relation/gate/closure/active-tip/ownership/cleanup effects from classification;
- no rewrite/delete of prior program/series/history/relation/session evidence;
- no external network, Computer Use, W6.2 cleanup, U2.5 hydration, release/version/tag/asset/main/push operation;
- no automated test stage before the corresponding maintainer preview acceptance.

## Completion definition

- the real coverage inventory is reproducible and explicit missing/absence states are distinguishable;
- every applied historical classification is bound to explicit evidence and maintainer confirmation;
- name-only/no-evidence inputs produce no effective classification;
- future registrations cannot accidentally omit primary or program/series absence decisions;
- classification changes do not change lifecycle or relation facts and W7.4 remains zero-overlap;
- focused post-acceptance checks pass and the task branch is clean;
- no integration, public installation or release is claimed.
