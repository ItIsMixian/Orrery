# ADR-0027: Retain History without Bulk UI and Recover Archived Lineage

Status: Accepted

Date: 2026-09-01

Maintainer acceptance: accepted on 2026-09-01 after rejecting two W7.4 previews that either flooded the relation
canvas with historical nodes or introduced a separate full-history directory while still failing to recover archived
relationships.

Amends: [ADR-0026](0026-durable-workstream-history-and-human-readable-relation-decisions.md)

Preserves: [ADR-0014](0014-dynamic-workstream-succession-contract.md),
[ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0020](0020-workstream-program-and-phase-hierarchy.md)

## Context

ADR-0026 correctly separated closed-task identity from the worktree directory, but its first implementation equated
retention with a new user-facing directory/list of all 37 archived tasks. That UI is not wanted. Worse, the
implementation judged most history “relation not registered” by looking primarily at the newer relation store.

Read-only inspection of the actual retired-session archive proves this is incomplete: 37 bounded records contain 33
`lineage` objects. Fourteen have `lineage.status=current`; at least eleven current source/target pairs resolve between
archived Workstreams and bind exact `base_workstream_id`, `task_base_oid` and `validated_head`. Examples include
W7B→W7A, W7C-B→W7A, W7A→W5E and W7D→CI2. These are existing mechanical session facts, not name inference.

The product must retain all history internally while projecting only evidence-backed relationships into the existing
Graph. It must not solve storage by adding another large history-management UI.

## Decision

1. **Retention and display are separate.** All bounded closed-task summaries remain stored independently of worktrees,
   but Orrery does not add a full-history directory, bulk card grid or second history application to the relation page.
2. **The existing Graph remains the only relationship surface.** It displays current tasks plus historical tasks that
   participate in a validated semantic relation or explicit series relation. Older connected chains may use the
   existing compact history folding; unconnected stored identities do not become canvas nodes by default.
3. **Archived session lineage is first-class recovery evidence.** Core evaluates archived `lineage` only when status,
   source/target identity, exact task-base OID, validated HEAD and Git ancestry/identity checks satisfy the existing
   mechanical `derived_from` contract. Valid records produce read-only historical projection edges with archived
   provenance; they do not rewrite the relation store.
4. **Unknown stays Unknown.** `legacy-unknown`, `parent-unverified-unknown`, missing targets, OID drift, cycles or
   unresolvable Git objects never create an edge. Names, task codes, prefixes, timestamps and visual order remain
   non-evidence.
5. **Explicit series evidence remains visible.** Accepted task-series predecessor/order metadata may draw the existing
   thin series connector for historical endpoints. Program/phase membership groups layout only and creates no edge.
6. **No new bulk history UI.** Stored identities remain available to Core/CLI/audit and future bounded queries, but
   W7.4 removes the new “完整历史目录”, bulk history cards and any control that injects all stored identities into ELK.
   Existing graph expansion means “expand connected relationship history”, not “display the archive inventory”.
7. **Relationship recovery is measurable.** Projection reports archived record counts, lineage status counts,
   accepted recovered edges and per-record rejection reasons in technical evidence, without exposing private paths or
   flooding the primary UI.
8. Human-readable relation decision cards from ADR-0026 remain required. This amendment changes history
   projection—not relation confirmation authority, gate semantics or decision explanation.
9. No archive/relation/branch/commit is deleted or rewritten. W6.2 remains blocked until the resulting history snapshot
   and relationship recovery are accepted and committed.

## Consequences

- The Graph regains real historical chains instead of showing a storage inventory.
- Closed tasks without relationship evidence are preserved without occupying the relationship canvas.
- Legacy session evidence can be used honestly without upgrading unknown lineage or mutating effective relation
  history.
- W7.4 must remove its newly added bulk history directory before acceptance.

## Mapping

- Amended Design: [Durable Workstream History and Relation Decision UX](../design/durable-workstream-history-and-relation-decision-ux.md#2026-09-01-revision-2--store-all-project-only-evidence-backed-relations)
- Amended Plan: [W7.4 Workstream History and Relation Decision UX](../implementation/plans/2026-09-01-w7-4-workstream-history-and-relation-decision-ux.md#2026-09-01-scope-revision-2--recover-archived-lineage-and-remove-bulk-history-ui)
- Pending Validation: [W7.4 Workstream History and Relation Decision UX](../validation/2026-09-01-w7-4-workstream-history-and-relation-decision-ux.md)
