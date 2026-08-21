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
- [ADR-0007: Multi-worktree collaboration and branch fact scopes](0007-multi-worktree-collaboration-and-branch-fact-scopes.md) — Accepted; separates Canonical, Candidate, and Worktree facts and requires one branch plus one isolated worktree or clone per concurrent task.
- [ADR-0008: Local-first Team Mode and cross-machine metadata visibility](0008-local-first-team-coordination-and-cross-machine-metadata.md) — Accepted; amends ADR-0007 so opt-in Local-only telemetry can coordinate unpushed work without becoming code evidence, while Personal Mode remains zero-network by default.
- [ADR-0009: Authority Meta Model and semantic conformance](0009-authority-meta-model-and-semantic-conformance.md) — Accepted; distinguishes protocol meta-rules from project Seed content and defines non-linear claim dimensions, authority scopes, provider-neutral evidence and consumer conformance without authorizing a code refactor.
- [ADR-0010: Core-owned deterministic Authority evaluator](0010-core-owned-authority-evaluator.md) — Accepted; resolves AUTH-4 by assigning deterministic semantics to platform-neutral Core while keeping parsing, projections, AI and Coordinator runtime outside the evaluator and preserving Gate B.
- [Adoption proposal](0000-orrery-adoption-proposal.md) — Superseded by ADR-0001; retained as migration history.

An accepted ADR constrains later Approved Design and implementation work. It does not prove that code or documents already implement the decision; current State and Validation provide that evidence.

## Pending integration proposals

- [PO-DEC-AUTH-002: Authority Model 公开版本与兼容契约](proposals/PO-DEC-AUTH-002-authority-model-version-and-compatibility.md) — Proposed; freezes the Gate B field, legacy/unsupported behavior, version matrix and explicit migration boundary without changing manifests or runtime behavior.

Concurrent branches use stable IDs under `docs/decisions/proposals/` until the maintainer accepts a proposal and an integrator allocates the next canonical ADR number.
