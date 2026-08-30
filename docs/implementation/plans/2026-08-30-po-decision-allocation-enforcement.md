# PO1 Provisional Decision Allocation Enforcement

Status: Planned; authority scope frozen before implementation

Date: 2026-08-30

Governing ADRs: [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0018](../../decisions/0018-authority-first-workstream-dispatch.md)

Approved Designs: [Multi-worktree Collaboration Protocol](../../design/multi-worktree-collaboration-protocol.md), [Authority-first Workstream Dispatch](../../design/authority-first-workstream-dispatch.md)

Primary subsystem: `documentation-system`

Affected: `multi-worktree-collaboration`, `test-coverage`, `release-and-toolchain`

## Problem

ADR-0007 already requires non-integration branches to use stable `PO-DEC-<task-id>-<slug>` files under
`docs/decisions/proposals/`. A4 nevertheless allocated numeric `ADR-0018` inside an isolated Candidate. The central
integrator later inspected only its current tree, did not inventory the unintegrated A4 decision, and independently
allocated `ADR-0018` to authority-first dispatch.

The PO rule therefore existed as authority but was absent from the dispatch Skill and lacked even a merged-tree
duplicate-number gate. Branch isolation made the violation invisible until integration.

## Implementation

- [ ] Amend `orrery-dispatch` so any decision-bearing non-integration task uses a stable PO ID and `Status: Proposed`.
- [ ] Never infer integrator authority from a branch name. Numeric allocation is allowed only when the target
  authority explicitly identifies the current task/worktree as the unique integrator.
- [ ] Before allocating a numeric ADR, inspect the current integration decision index and pending PO sources; allocate
  the next free number only in the integration worktree, then update filename, metadata and all references together.
- [ ] Add a repository gate that rejects two current `docs/decisions/NNNN-*.md` files sharing one number. It does not
  scan peer worktrees or turn a Candidate number into a reservation service.
- [ ] Preserve the existing PO mechanism and schema; do not add a central network number service or rewrite accepted
  ADR history.

## A4 collision closeout

- [ ] Keep authority-first dispatch as canonical local `ADR-0018`, because it is already on the integration line and
  is referenced by U2.3/W7.3 task-description versions.
- [ ] When A4/U2.3 enters the integration worktree, rename A4 portable operating rules to `ADR-0019`, update every
  filename/link/index/governing reference atomically, and preserve A4 Candidate SHA `3d298a5c...` as provenance.
- [ ] Confirm the A4 decision content/status/semantics are byte-equivalent apart from identifier/link normalization.

## Validation

- current repository has one file per numeric ADR;
- synthetic duplicate numeric paths are rejected;
- proposal paths do not reserve or collide with numeric ADRs;
- `orrery-dispatch` explicitly routes non-integrator decisions to PO IDs;
- current repository/Fast/integrated-installation/Skill checks pass;
- no A4 product, U2.3 product, public release or remote state changes in PO1.
