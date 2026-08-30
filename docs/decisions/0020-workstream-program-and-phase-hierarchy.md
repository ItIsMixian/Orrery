# ADR-0020: Workstream Program and Phase Hierarchy

Status: Accepted

Date: 2026-08-30

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0014](0014-dynamic-workstream-succession-contract.md),
[ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md)

## Context

Orrery currently records individual Workstream sessions, explicit task series and causal/ownership relations such as
`derived_from`, `depends_on` and `absorbs`. That is insufficient to represent a real development program whose tasks
branch into phases and substreams. In this repository, W5/W6/W7 are not arbitrary labels: they belong to one W
Workstream program, while W5, W6 and W7 are distinct phases. Some real chains cross non-W tasks such as CI1 or SH1.

Treating every W task as one linear series would invent order and causality. Treating W as a visual-only prefix would
discard a real project organization fact. Inferring membership from `display_prefix`, branch or title is also unsafe:
legacy records may be incomplete, renamed or independently created.

## Decision

1. **Program hierarchy is a first-class organizational fact.** Orrery adds versioned Workstream group definitions and
   memberships. Initial group kinds are `program` and `phase`; a phase has one parent program.
2. **Membership is not a relation edge.** Program/phase membership does not create `derived_from`, `depends_on`,
   `absorbs`, series order, lifecycle eligibility, closure, ownership transfer or validation gate effects.
3. **One primary group path in v1.** A Workstream may have zero or one primary ordered path such as
   `program:workstream-w → phase:workstream-w7`. Multi-program membership, tags and arbitrary group DAGs are future
   work.
4. **Membership is explicit.** `task_code`, `display_prefix`, title, branch name and numeric resemblance cannot create
   membership. They may be shown as evidence in a proposal, never treated as the deciding fact.
5. **Human authority.** Agent, task owner, parser or optional Conductor may propose a group definition or membership.
   A human project integrator confirms effective program/phase membership. Personal project owner is the default
   integrator; Team confirmation follows the existing verified-integrator boundary.
6. **Versioned append-only records.** Group create/amend/archive and membership propose/accept/reject/supersede use
   revision/CAS, actor, source links and Git-common-private append-only evidence. Existing author docs and relation
   history are not rewritten.
7. **Stable ID and display separation.** `group_id` is opaque and stable; human labels and task codes may change
   independently. Ordering is explicit within the parent group and cannot be derived from string sorting.
8. **Legacy stays Unknown.** Existing Workstreams without an accepted membership remain ungrouped/Unknown. Migration
   uses an explicit human-reviewed repair fixture; Orrery does not bulk-classify W/A/CI/U prefixes.
9. **Derived views may use hierarchy.** Observatory may group, filter, fold and lay out Workstreams by accepted group
   path. It must continue to draw the actual relation DAG independently and visibly distinguish group containment,
   series connectors and semantic edges.
10. **Controlled route bundling is presentation-only.** A derived graph may share a route trunk only for relations
    with the same type, direction, lifecycle/certainty, gate/style and common source or common target. The underlying
    edges, evidence and selection identities remain separate.
11. **Privacy and execution boundaries remain.** Personal is zero-network. Team may sync bounded group IDs, labels,
    revisions and membership metadata but not Prompt, transcript, source, diff, credentials or private evidence
    bodies. Group membership grants no execution or confirmation authority beyond this decision.
12. **Unknown extensions fail closed.** New group kinds, multiple primary programs, automatic prefix adoption or group
    membership that changes gates/ownership require a later ADR.

## Consequences

- W tasks can appear as one real program with W5/W6/W7 phase structure without fabricating a single linear W series.
- CI/SH/U tasks may remain outside the W program while real edges cross group boundaries.
- Core/CLI need group/membership contracts and human confirmation; Graph needs hierarchical containment and bounded
  route bundles. These are implementation requirements, not evidence that current W7.3 already supports them.
- Existing relation, authority, privacy, release and public/default boundaries remain unchanged.

## Mapping

- Approved Design: [Workstream program hierarchy and graph bundling](../design/workstream-program-hierarchy-and-graph-bundling.md)
- Implementation Plan: [W7.3 Workstream Relation Capture](../implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)
- Validation: [W7.3 Relation Capture & Confirmation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)
