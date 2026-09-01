# Implementation Plan: W7.4 Workstream History and Relation Decision UX

Status: Approved for implementation; visual/semantic preview precedes automated validation

Date: 2026-09-01

Task code: W7.4

Program path: `workstream-w / workstream-w7`

Governing decision: [ADR-0026](../../decisions/0026-durable-workstream-history-and-human-readable-relation-decisions.md)

Approved Design: [Durable Workstream History and Relation Decision UX](../../design/durable-workstream-history-and-relation-decision-ux.md)

Observed product base: U2.4 Worktree Candidate
`00b2eb4fa28a606cdb532c7938e46482950e8233`; this is a Candidate dependency, not Canonical/main fact.

## Objective

Make closed Workstreams survive worktree cleanup as usable project history and make every relation confirmation
understandable before the maintainer can act. This is one W7 task because both failures arise from the same Workstream
history/relation provider and its Personal/Graph projections. Workspace deletion policy remains W6 and launcher/runtime
behavior remains U2.4.

## Authorized implementation

1. Register W7.4 in an independent branch/worktree from the exact observed U2.4 Candidate, bind the explicitly approved
   `workstream-w/workstream-w7` classification in its scope, and acknowledge the exact task-description version before
   product writes. Do not fabricate a human membership event; if the current store needs a separate integrator action,
   leave a bounded proposal for local confirmation.
2. Add Core `workstream-history-index-v1` contracts, validation and append-only atomic storage independent of worktree
   paths. Provide verified closure snapshot and read-only legacy archive migration preview/apply boundaries.
3. Expose a bounded `history_snapshot_ready` result that a later W6 task can require before automatic cleanup. Do not
   change current W6 eligibility or implement automatic deletion in this task.
4. Extend the relation/Graph provider to include all bounded closed history summaries, including zero-relation tasks.
   Default-fold them by accepted program/phase/series and keep “其他历史任务” for ungrouped records.
5. Make expand/collapse/filter behavior operate on the complete history identity set. Preserve real relations,
   historical non-execution and ELK/explicit-legacy boundaries.
6. Add a deterministic Core-owned relation decision presentation model and replace the current technical-first inbox
   cards with question/reason/accept-effect/reject-effect/evidence-warning/actions/technical-details order.
7. Keep `derived_from` Unknown non-accepting, keep task-owner/integrator/CAS authority unchanged, and make incomplete
   explanations non-actionable rather than falling back to raw controls.
8. Maintain root/project-template behavior parity where the affected Observatory code is shipped. Update subsystem
   State, this Validation and DEVLOG in the task branch; do not rewrite root PROGRESS/HANDOFF there.

## Preview-first sequence

1. Read current live/archive/history inputs and record a zero-write baseline showing which closed tasks are omitted.
2. Implement the smallest complete history/provider/decision-view path.
3. Render the real self-host page on a separate local loopback preview without Computer Use.
4. Stop and ask the maintainer to inspect history folding/expansion and the dependency/Unknown decision cards.
5. Before that acceptance, do not run unittest suites, Fast, Checkpoint, Candidate or Promotion. Syntax/import checks
   needed to start the preview are allowed but are not acceptance evidence.
6. After maintainer acceptance, run only the focused Core/Observatory owners plus root/template parity and
   `git diff --check`. Broader validation and publication require a later explicit instruction.

## Expected implementation surfaces

- `packages/project-orrery-core/src/project_orrery_core/` history, relation and schema owners;
- `packages/project-orrery-observatory/src/project_orrery_observatory/` Graph and relation-inbox projections;
- root/project-template docsite adapters only where parity requires them;
- focused Workstream relation/history/Observatory tests after visual acceptance;
- `docs/state/project-structure.md`, `docs/state/documentation-system.md`, this Validation and `docs/DEVLOG.md`.

## Hard boundaries

- no deletion, branch cleanup, archive rewrite/truncation or existing relation-history rewrite;
- no automatic relation confirmation, prefix/name inference or AI-generated decision semantics;
- no Prompt/transcript/source/diff/credential/private-path persistence or Team synchronization;
- no Computer Use, external network, release/version/tag/asset/main/push operation;
- no Fast/Checkpoint/full matrix before maintainer acceptance;
- U2.4 remains a separate Candidate dependency and W6 Phase 5 remains a separate cleanup task.

## Completion definition

- every bounded closed self-host task is present in the history index and reachable from Graph history, including
  tasks with no relation edges;
- default Graph remains readable through history folding and expansion reveals the full historical set;
- the maintainer can explain the decision and consequence of each sampled card without opening technical details;
- Unknown lineage cannot be accepted and dependency authority/gates/CAS remain unchanged;
- focused post-acceptance checks pass and the task branch is clean;
- no integration, release or public capability is claimed.

## 2026-09-01 scope revision 2 — recover archived lineage and remove bulk history UI

The maintainer rejected the second and third previews. Restoring 37 identities was necessary storage work, but the
implementation still failed the product objective: it either dumped identity-only tasks into ELK or introduced a new
“完整历史目录” card grid while the original Graph still lacked most historical relations.

Central read-only evidence for this revision is fixed:

- 37 bounded retired-session records;
- 33 records with a `lineage` object;
- lineage status counts: 14 `current`, 13 `legacy-unknown`, 6 `parent-unverified-unknown`, 4 absent;
- at least 11 `current` archived source/target pairs resolve inside the bounded archive and bind exact task-base and
  validated-head OIDs. The implementation must recompute and validate this count rather than hard-code it.

This revision authorizes W7.4 to:

1. remove the newly introduced complete-history directory, bulk historical cards and `history:all` archive-dump path;
2. retain the full underlying history index without presenting it as a new user-facing application;
3. extend the existing legacy/archive relation resolver so valid archived `lineage.status=current` records can produce
   read-only historical `derived_from` projection edges after exact endpoint/OID/Git/cycle validation;
4. preserve current relation-store/capture proposals and explicit task-series connectors, deduplicating equivalent
   archived/native edges deterministically without suppressing distinct evidence;
5. keep legacy/unverified/missing/drifted lineage as Unknown with a technical rejection reason and no invented edge;
6. keep only evidence-connected historical tasks in the relation canvas, using existing connected-history folding;
7. update the real self-host preview to prove the recoverable archived chains are visible in the original Graph, the
   bulk history UI is absent and current decision-card improvements remain;
8. stop again for maintainer inspection before any unittest/Fast/Checkpoint/Candidate/Promotion stage.

This revision does not authorize rewriting archive/session/relation bytes, synthesizing relations from names or
timestamps, adding another history UI, changing confirmation authority, or starting W6.2.

Revision-2 completion supersedes the earlier bullets requiring zero-relation tasks to be reachable from Graph UI.
Those identities must remain stored, but they need not be rendered.

## 2026-09-01 scope revision 3 — bind the actual local integration ref

After the obsolete G1/U2/U2.4 registered worktrees were preserved and retired, scope refresh reported zero active
peer findings but still returned `L3 / Allowed: no`. The remaining cause was a stale project baseline: the session
resolved `refs/heads/main@d07e1a15...`, while the unique local integration worktree is
`refs/heads/codex/u1-u2-integration-baseline@208ae29...`. Consequently, already integrated U2.4 release/schema paths
were misclassified as new W7.4 expansion.

ADR-0007 already permits a project override of the default integration ref. Revision 3 authorizes:

1. the self-host `.project-orrery.json` to bind `collaboration.integration_ref` to
   `refs/heads/codex/u1-u2-integration-baseline` for this local integration phase;
2. W7.4 to import that exact one-file configuration correction as a separate bootstrap commit while preserving all
   existing dirty product work, then rerun scope refresh;
3. product writes to resume only if the refreshed guard returns allowed against the actual integration ref;
4. the future protected-main/Promotion task to restore the public/default integration ref to `refs/heads/main` before
   any push to main or release packaging.

This is a baseline correction, not an L3 bypass. It does not authorize ignoring peer findings, changing branch
protection, pushing the local integration branch or starting W6.2.

## 2026-09-01 scope revision 4 — integrator-owned strict history schema bootstrap

With the actual integration ref configured, scope refresh had zero peer findings but correctly retained an exclusive
`schema-migration` L3 for the untracked W7.4 schema Candidate. Central review rejected that draft because
`display`／`classification`／`references` allowed arbitrary objects and every archive was forced to lifecycle
`closed`. The real bounded archive contains only 6 closed sessions; the other 31 are 12 implementing, 18 validating
and 1 review-ready session.

The unique integrator now owns the strict `workstream-history-index-v1.json` bootstrap. Revision 4 authorizes W7.4 to:

1. verify its untracked schema is not committed, remove that task-owned draft after preserving any relevant design
   intent already captured in code, and merge the exact central schema-bootstrap commit;
2. preserve observed lifecycle honestly through `closed-workstream` versus `retired-session` records;
3. rerun scope refresh against an integration baseline that already owns the schema;
4. resume product writes only when the exclusive schema path is absent from W7.4's diff and the guard returns allowed.

W7.4 must not loosen the strict central schema or reintroduce arbitrary objects to fit existing code. Any required
schema amendment returns to the unique integrator before product writes continue.
