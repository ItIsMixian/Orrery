# ADR-0026: Durable Workstream History and Human-readable Relation Decisions

Status: Accepted

Date: 2026-09-01

Maintainer acceptance: accepted on 2026-09-01 after rejecting a Graph that lost cleaned closed tasks and a Personal
relation inbox whose technical wording did not permit an informed accept/reject decision.

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0020](0020-workstream-program-and-phase-hierarchy.md)

## Context

The current archive resolver intentionally restores only closed Workstreams that are referenced by a live relation and
missing from the live session set. Removing a worktree therefore preserves branch/commit and some archived evidence,
but an unrelated closed task disappears from the Graph provider entirely. Existing “expand history” controls can only
expand historical nodes already supplied by the provider and cannot recover omitted tasks.

The Personal relation inbox also exposes relation type, revision, raw Workstream IDs, English machine rationale,
storage provenance and gate controls before it explains the actual decision. A maintainer cannot safely accept a
dependency merely from “阶段依赖 · revision 1” and `explicit task-series predecessor supplied by registration`.

Worktree lifecycle, task history and relation authority are different facts. Deleting an execution directory must not
delete or hide the historical task identity, and a confirmation UI must make the consequence understandable before it
offers an authoritative action.

## Decision

1. **Closed task history survives worktree removal.** Core owns a versioned, append-only, Git-common-private
   `workstream-history` index independent of any worktree directory. Removing a worktree never removes its history
   record, branch, commit, relation history or Validation references.
2. **History records are compact and bounded.** They retain Workstream ID, human label/task code, subsystem,
   program/phase/series membership, final branch/HEAD, lifecycle/closure time and reason, safe Validation/source refs,
   and relation IDs/status. They exclude Prompt, transcript, answer, source/diff body, credentials and absolute private
   paths.
3. **Full archives are evidence, not the history inventory.** Retired `worktree.json` files remain bounded fallback
   evidence. The history index determines which closed tasks exist. Valid legacy archives may be migrated into compact
   records without rewriting or deleting the archive; ambiguous fields remain Unknown.
4. **Graph includes current and historical task identity.** All current unclosed tasks remain individual nodes. Every
   closed history record remains reachable. Historical tasks default to compact program/phase/series groups and expand
   on demand; tasks without relations remain in history rather than disappearing. Historical nodes are permanently
   read-only and non-executable.
5. **Relation decisions use a Core-owned explanation model.** Every actionable proposal supplies deterministic,
   localized fields for: the question being asked, why it was suggested, the consequence of acceptance, the
   consequence of rejection/defer, and the evidence limitation. Observatory renders these fields; it does not invent
   semantics in JavaScript.
6. **Technical details are secondary.** Proposal ID, revision, raw Workstream IDs, machine rationale, evidence hashes,
   Git-private provenance and `local-only` labels appear under an explicit technical-details disclosure, not as the
   primary decision copy.
7. **Actions remain authority-safe.** `derived_from` remains mechanical and cannot gain a human Accept action when
   ancestry is Unknown. `depends_on` gate choices use plain-language stages and consequences, while Core/role/CAS
   rules continue to decide whether acceptance is allowed. Unclear evidence stays Unknown; understandable wording does
   not upgrade certainty.
8. **Classification belongs to Core.** Core owns history/category/relation explanation semantics. Observatory presents
   them, `orrery-dispatch` routes tasks, and Harnesses create/run sessions; neither a Skill nor a Harness may invent a
   second classification model.
9. Existing relation events, confirmations, archives and historical release assets remain immutable. This decision
   authorizes no automatic relation confirmation, deletion, branch cleanup, release or remote execution.

## Consequences

- Cleanup can remove execution containers without erasing project memory from Personal/Graph views.
- “Expand history” becomes a real data operation rather than a presentation toggle over an incomplete provider.
- Maintainers can decide relations from human consequences while retaining technical audit details when needed.
- Core, Observatory, cleanup preflight and task closure need a shared history contract; this is implemented by W7.4,
  not U2.4 or W6 Phase 5.

## Mapping

- Approved Design: [Durable Workstream History and Relation Decision UX](../design/durable-workstream-history-and-relation-decision-ux.md)
- Plan: [W7.4 Workstream History and Relation Decision UX](../implementation/plans/2026-09-01-w7-4-workstream-history-and-relation-decision-ux.md)
- Validation: [W7.4 Workstream History and Relation Decision UX](../validation/2026-09-01-w7-4-workstream-history-and-relation-decision-ux.md)
