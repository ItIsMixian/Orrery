# Architecture Decision Records

ADRs record what was decided and why. Accepted ADRs are immutable history; later ADRs may amend or supersede them.

Required metadata:

- `Status`: Proposed, Accepted, Deprecated, or Superseded by ADR-NNNN
- `Date`: YYYY-MM-DD
- `Amends` or `Supersedes` when applicable

Use `0000-template.md` as the starting point.

## Project Orrery decisions

- [ADR-0026: Durable Workstream History and Human-readable Relation Decisions](0026-durable-workstream-history-and-human-readable-relation-decisions.md) — Accepted; closed task identity survives worktree removal in a compact Core-owned history index, Graph history includes zero-relation tasks, and actionable relation cards must explain the question and consequences before exposing controls.
- [ADR-0025: Two Explicit Windows Launchers](0025-two-explicit-windows-launchers.md) — Accepted; the next Candidate exposes only `Start Orrery.vbs` for hidden-console launch and `Start Orrery Console.bat` for one-console diagnostics, while internalizing redundant control/legacy helpers and preserving historical release assets.
- [ADR-0024: Orrery v0.3.1 Emergency Launcher Hotfix Release](0024-v0-3-1-emergency-launcher-hotfix-release.md) — Accepted; ships only the Windows launcher correction through one short exact-SHA patch gate, preserves v0.3.0 assets and moves alias/scheduler/DSH out of the emergency release.
- [ADR-0023: Explicit Legacy Graph Layout Fallback and Preview-first Cutover](0023-explicit-legacy-graph-layout-fallback.md) — Accepted; preserves the handwritten renderer as a frozen, visibly labeled manual recovery engine, forbids silent fallback and blocks ELK product integration until the maintainer first accepts the isolated GX2 page.
- [ADR-0022: ELK.js as the Workstream Graph Layout Engine](0022-elkjs-workstream-graph-layout-engine.md) — Accepted and amended by ADR-0023; selects pinned local ELK layout-only while Orrery retains fact selection and existing SVG/frontend design.
- [ADR-0021: Orrery v0.3.0 Release Scope, Defaults and Publication Authority](0021-v0-3-0-release-scope-default-matrix.md) — Accepted; selects the 0.3.0 feature/default/distribution matrix, one self-contained ZIP, exact-SHA deterministic Promotion and separate main/tag/Release authority while deferring DSH/alias/scheduler to 0.3.1.
- [ADR-0020: Workstream Program and Phase Hierarchy](0020-workstream-program-and-phase-hierarchy.md) — Accepted; adds explicit human-confirmed program/phase membership separate from series and causal relations, plus presentation-only controlled route bundling without gate or execution effects.
- [ADR-0019: Portable operating rules and Authority Route Preflight](0019-portable-operating-rules-and-authority-route-preflight.md) — Accepted; amends/extends ADR-0009 with a versioned portable-rules inventory, provider-neutral fact-route receipt, four independent claim axes and novelty/absence gate while preserving Core as the sole semantics owner and keeping all consumers read-only/unreleased.
- [ADR-0018: Authority-first Workstream Dispatch](0018-authority-first-workstream-dispatch.md) — Accepted; requires the authority commit to precede task creation or material scope amendment, reduces task messages to exact SHA/path references and makes transcript-only requirements non-authoritative.
- [ADR-0017: Workstream relation capture, stage gates and confirmation authority](0017-workstream-relation-capture-and-confirmation-authority.md) — Accepted; permits future automatic recording of mechanically verified `derived_from`, adds four `depends_on` gates with task-owner/integrator confirmation, restricts `absorbs` to human integrators and makes central Conductor proposal-only; W7.3 is not implemented.
- [ADR-0016: Unified Observatory Shell and single local entry](0016-unified-observatory-shell-and-single-local-entry.md) — Accepted; gives users one visible launcher, URL and navigation shell while allowing supervised hidden helpers, preserving the existing docsite experience and keeping static, Team, Authority and destructive-action boundaries independent.
- [ADR-0015: Orrery brand and compatibility contract](0015-orrery-brand-and-compatibility-contract.md) — Accepted; separates the Orrery display brand from stable technical/protocol identities, fixes the R4 thin-alias and first-new-release asset defaults, preserves v0.2.0 history and the full 0.3.x compatibility window, and blocks Python `orrery` namespace takeover.
- [ADR-0014: Dynamic Workstream Succession Contract](0014-dynamic-workstream-succession-contract.md) — Accepted; adds incremental `derived_from`／`depends_on`／`absorbs` relations, append-only Git-common-private evidence, reversible lifecycle and conservative active-tip conflict semantics without creating a scheduler or deletion authority.
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
- [ADR-0011: Authority Model public version and compatibility contract](0011-authority-model-version-and-compatibility.md) — Accepted; resolves Gate B with a positive-integer project selector, discrete consumer support sets, fail-closed legacy/unknown behavior and explicit semantic migration separate from ordinary tool upgrades.
- [ADR-0012: Documentation governance and information lifecycle](0012-document-governance-and-information-lifecycle.md) — Accepted; separates current control surfaces from history, adopts event-driven synchronization and soft review budgets, and limits future tooling to non-authoritative read-only findings.
- [ADR-0013: Claude Code and DeepSeek Harness Adapters](0013-claude-code-and-deepseek-harness-adapters.md) — Accepted; selects two independent Phase 4 platform Adapter ranges and requires isolated lifecycle evidence before separately authorized model-call validation.
- [Adoption proposal](0000-orrery-adoption-proposal.md) — Superseded by ADR-0001; retained as migration history.

An accepted ADR constrains later Approved Design and implementation work. It does not prove that code or documents already implement the decision; current State and Validation provide that evidence.

## Pending integration proposals

- No active proposal is awaiting maintainer review; ADR-0018–0026 are Accepted. ADR-0024 carries the maintainer's
  explicit request to proceed through the green v0.3.1 publication sequence without another pause.
- `PO-DEC-AUTH-002` was integrated as ADR-0011.
- `PO-DEC-REL-003` at REL3 exact `ec2b09b` was accepted and normalized into ADR-0021 plus the current Approved Design/blocked Final RC Plan.

Concurrent branches use stable IDs under `docs/decisions/proposals/` until the maintainer accepts a proposal and an integrator allocates the next canonical ADR number.
