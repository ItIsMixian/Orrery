# Validation: W7.4 Workstream History and Relation Decision UX

Status: Pending Validation; maintainer preview required before automated tests

Date: 2026-09-01

Plan: [W7.4 Workstream History and Relation Decision UX](../implementation/plans/2026-09-01-w7-4-workstream-history-and-relation-decision-ux.md)

## Rejected baseline

- the current accepted-preview page shows only live or relation-connected archived tasks; cleaned closed tasks without
  relation endpoints are absent even when their session/archive evidence still exists;
- “expand all history” cannot reveal records omitted by the provider;
- Personal relation cards lead with `阶段依赖 · revision 1`, raw Workstream IDs, English machine rationale and
  Git-private provenance;
- the card offers Accept/change-gate/defer/reject without first explaining the actual question or the consequence of
  acceptance, so the maintainer cannot make an informed decision.

## Pending maintainer acceptance

- current, historical and Unknown counts are explained and match the complete bounded input set;
- closed zero-relation tasks remain discoverable after worktree cleanup and are folded by real classification;
- expanding all history reveals every bounded historical task without placing all of them in the default active view;
- a dependency card states in Chinese who waits for whom, at which stage, why it was suggested and what acceptance
  changes;
- an Unknown lineage card states why it cannot be verified and provides no Accept action;
- raw IDs, revision, hashes, rationale and local-only provenance are available only under technical details;
- no action changes relation authority, certainty or lifecycle merely because the wording improved.

## Test boundary

No unittest, Fast, Checkpoint, Candidate, Promotion or release evidence is permitted before the maintainer accepts the
real self-host preview. After acceptance, only focused history/relation/Observatory owners, parity and
`git diff --check` are initially in scope.

## Result

Pending. No W7.4 product implementation or validation evidence exists under this task-description version.

## 2026-09-01 preview rejection 3 — identity storage is not relation recovery

Status: Rejected by maintainer; scope revision 2 Pending

- the preview added a new “完整历史目录” and bulk card grid that the maintainer did not request;
- the original relation canvas still showed only a small subset of historical relationships;
- the implementation labelled many tasks “关系未登记” after consulting the newer relation store, but central
  inspection proves 33/37 archived sessions retain lineage objects and at least 11 current archived pairs bind exact
  source/target/task-base/validated-head evidence;
- identity-only storage and relationship projection were therefore conflated in both directions.

The next preview is acceptable only when the bulk history UI is absent, valid archived lineage relationships are
recovered into the existing Graph, invalid/Unknown lineage stays edge-free with technical reasons, and no archive or
relation history is rewritten. Automated tests remain forbidden before that preview is accepted.

## 2026-09-01 scope-baseline correction — Pending

- obsolete peer worktrees were preserved and removed from the registry; refreshed peer findings became zero;
- scope still failed L3 because `refs/heads/main@d07e1a15...` was not the actual local integration baseline;
- `.project-orrery.json` now explicitly selects `refs/heads/codex/u1-u2-integration-baseline` under the existing
  ADR-0007 configuration contract;
- W7.4 must import the exact correction and obtain an allowed scope refresh before product writes resume;
- no test, product write, main update, push or release is accepted as evidence under the stale baseline.

## 2026-09-01 strict schema bootstrap — Pending

- the task-owned schema draft was not accepted or committed;
- central archive facts are 6 closed, 12 implementing, 18 validating and 1 review-ready session;
- the integrator bootstrap schema forbids arbitrary properties and separates historical record kind, observed
  lifecycle, closure reason, Git identity, lineage and bounded references;
- W7.4 must merge the exact central schema commit and obtain an allowed scope refresh before resuming product work;
- no schema weakening, test or product completion is accepted before that gate.
