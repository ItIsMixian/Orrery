# Architecture Decision Records

ADRs record what was decided and why. Accepted ADRs are immutable history; later ADRs may amend or supersede them.

Required metadata:

- `Status`: Proposed, Accepted, Deprecated, or Superseded by ADR-NNNN
- `Date`: YYYY-MM-DD
- `Amends` or `Supersedes` when applicable

Use `0000-template.md` as the starting point.

## Project Orrery decisions

- [ADR-0001: Project Orrery self-hosting](0001-project-orrery-self-hosting.md) — Accepted; establishes this repository's own documentation authority chain.
- [ADR-0002: Real-development benchmark portfolio](0002-real-development-benchmark-portfolio.md) — Accepted; requires future context-routing adoption studies to include isolated application-development tasks, not only documentation maintenance.
- [Adoption proposal](0000-orrery-adoption-proposal.md) — Superseded by ADR-0001; retained as migration history.

An accepted ADR constrains later Approved Design and implementation work. It does not prove that code or documents already implement the decision; current State and Validation provide that evidence.

## Pending integration proposals

These records use stable provisional IDs so concurrent branches do not compete for the next sequential ADR number. They are not effective ADRs until an integrator allocates `ADR-NNNN`, updates references, and merges them into the integration ref.

- [PO-DEC-WT-001: Multi-worktree collaboration and branch fact scopes](proposals/PO-DEC-WT-001-multi-worktree-collaboration.md) — maintainer approved for integration; still Proposed and non-canonical.
