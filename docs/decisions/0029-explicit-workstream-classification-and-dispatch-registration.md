# ADR-0029: Explicit Workstream Classification and Dispatch Registration

Status: Accepted

Date: 2026-09-01

Maintainer acceptance: accepted on 2026-09-01 after the maintainer confirmed that corrected lifecycle history did
not solve the remaining task-classification problem and instructed the coordinator to continue.

Amends: [ADR-0018](0018-authority-first-workstream-dispatch.md),
[ADR-0020](0020-workstream-program-and-phase-hierarchy.md)

Preserves: [ADR-0014](0014-dynamic-workstream-succession-contract.md),
[ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0027](0027-retain-history-without-bulk-ui-and-recover-archived-lineage.md)

## Context

W7.4 corrected one axis of history: the 37 bounded retired records now distinguish six verified
`closed-workstream` records from 31 `retired-session` records. That lifecycle correction does not classify work into
programs, phases or task series.

The current self-host provider exposes 42 Workstream nodes. Thirty-three lack task-series metadata, 35 lack accepted
program/phase membership and 27 lack both. The strict history index contains 37 records, of which 29 lack series and
30 lack program/phase. Primary subsystem is present, but the missing organizational axes leave related work visually
fragmented and make mechanical `derived_from` chains appear to be categories even though ancestry is not membership.

Existing metadata was added unevenly because older tasks predate authority-first dispatch and later task creation did
not consistently require an explicit classification envelope. Inferring `W7`, `CI` or `U` from a task name would make
the graph look tidier while manufacturing project facts. Classification therefore needs an explicit authority and a
bounded calibration workflow, not another layout heuristic.

## Decision

1. Workstream classification has independent axes:
   - required primary subsystem and explicit affected subsystems;
   - optional accepted program/phase membership;
   - optional accepted task-series identity/order/predecessor;
   - lifecycle/history state;
   - semantic/mechanical relations.
   No axis implies another.
2. New authority-first Workstream registration must provide a versioned classification envelope. Primary subsystem is
   required. Program/phase and series may be explicitly absent, but each absence carries a bounded reason such as
   `standalone-task`, `classification-pending` or `not-applicable`; omission is not silently treated as intentional.
3. Task code, display label, branch name, numerical prefix, creation time, visual order and `derived_from` ancestry are
   never classification authority. They may help a human find a task but cannot create program membership, series
   membership, order, predecessor, gate or relation.
4. Core owns validation and append-only classification events. `orrery-dispatch` transports the explicit envelope and
   refuses an incomplete registration; the Skill, transcript and Agent do not become classification authority.
5. Existing accepted program-membership and task-series events are mechanically retained without human replay.
   Missing historical classification is audited into proposals only when a bounded explicit source exists, such as a
   committed task Plan, recorded registration or earlier accepted classification event. A proposal cites that source
   and remains non-effective until confirmation.
6. Classification proposals use a human-readable local review surface. The maintainer can accept, change, defer,
   reject or deliberately keep a task unclassified. Related proposals may be presented as a batch, but every task's
   resulting event and evidence binding remain individually inspectable and CAS-protected.
7. A proposal with no explicit evidence cannot be accepted as an inferred fact. It stays `unclassified` with a reason;
   the UI does not invent a likely series or program from the name.
8. Confirmation authority is local human integrator/maintainer. Agents and central/request-only Team views may prepare
   or display bounded proposals but cannot confirm them. Personal Mode remains zero-network.
9. Accepted classification affects organization, filters, labels and ELK compound membership only. It creates no
   relation edge, dependency gate, active tip, closure, ownership, cleanup eligibility or execution authority.
10. Graph and history projections must expose lifecycle and organizational classification separately. Unregistered
    program/series axes display `未登记`/`未分类`; mechanical ancestry remains visibly a relation rather than a grouping.
11. W7.5 performs the one-time self-host calibration and adds future registration enforcement. It begins only from an
    accepted clean W7.4 Candidate so classification changes do not invalidate the layout acceptance baseline.
12. This decision authorizes a local Candidate and maintainer confirmation workflow only. It does not authorize
    automatic semantic classification, bulk silent acceptance, release/publication, W6.2 cleanup or U2.5 Phase B.

## Reasons

- Explicit absence is distinguishable from accidental omission.
- Human confirmation protects semantic project organization while still allowing mechanical recovery of existing
  explicit records.
- Keeping membership, lifecycle and relations orthogonal prevents a clean graph from becoming false project history.
- Enforcing the envelope at dispatch stops the backlog from growing after historical calibration.

## Consequences

- Core/CLI need a strict classification envelope, proposal/confirmation storage and bounded audit output.
- `orrery-dispatch` must include classification identity in registration references and refuse missing required fields.
- Personal Observatory needs a readable classification-review surface; Graph remains read-only.
- Existing unclassified tasks remain valid tasks. Calibration is additive and may deliberately leave records
  unclassified when evidence is insufficient.
- W7.4 remains the history/layout owner and must not absorb classification backfill.

## Mapping

- Approved Design: [Workstream Classification Calibration and Dispatch Registration](../design/workstream-classification-calibration-and-dispatch-registration.md)
- Implementation Plan: [W7.5 Workstream Classification Calibration](../implementation/plans/2026-09-01-w7-5-workstream-classification-calibration.md)
- Pending Validation: [W7.5 Workstream Classification Calibration](../validation/2026-09-01-w7-5-workstream-classification-calibration.md)
