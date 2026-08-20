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
- [ADR-0003: Provider-bound credentials and optional local broker](0003-provider-bound-credentials-and-optional-local-broker.md) — Accepted; fails closed on endpoint drift and separates standard keyring storage from optional process-isolated Provider keys.
- [ADR-0004: Platform-neutral Core and Agent/Harness Adapter boundaries](0004-platform-neutral-core-and-adapter-boundaries.md) — Accepted; adopts single-repository component packages, a canonical neutral Agent entrance, independent component versions, and evidence-gated runtime support.
- [ADR-0005: Pre-write scope-acquisition input](0005-prewrite-scope-acquisition-input.md) — Accepted; makes cumulative input before the first product write the primary routing-cost metric and requires passive Harness measurement without Agent manifests or receipts.
- [ADR-0006: Broker-only docsite Provider gateway](0006-broker-only-docsite-provider-gateway.md) — Accepted; makes Broker the only dynamic docsite model-call path while separating default same-user cost control from external OS-identity isolation.
- [Adoption proposal](0000-orrery-adoption-proposal.md) — Superseded by ADR-0001; retained as migration history.

An accepted ADR constrains later Approved Design and implementation work. It does not prove that code or documents already implement the decision; current State and Validation provide that evidence.

## Pending integration proposals

These records use stable provisional IDs so concurrent branches do not compete for the next sequential ADR number. They are not effective ADRs until an integrator allocates `ADR-NNNN`, updates references, and merges them into the integration ref.

- [PO-DEC-WT-001: Multi-worktree collaboration and branch fact scopes](proposals/PO-DEC-WT-001-multi-worktree-collaboration.md) — maintainer approved for integration; still Proposed and non-canonical.
