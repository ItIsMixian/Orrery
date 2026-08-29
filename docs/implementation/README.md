# Implementation

Plans live under `docs/implementation/plans/` and describe how an approved design will be implemented.

Every active plan should map:

1. Applicable effective ADRs
2. Approved Design sections
3. Concrete implementation targets
4. Validation commands or review criteria
5. State Docs that must change

A completed checklist is not evidence by itself; implementation, validation, and State Docs take over after delivery.

## Plans

- [2026-08-29 U2 Unified Observatory Production Integration](plans/2026-08-29-u2-unified-observatory-production-integration.md) — root-only/default-off production Candidate complete and integrated for maintainer experience; public/default transition remains separate.
- [2026-08-29 W7.1 Archived Session Relation Projection](plans/2026-08-29-w7-1-archived-session-relation-projection.md) — bounded read-only retired-session resolver restores referenced closed Workstream axes without creating discovery or execution authority.
- [2026-08-29 SH1 Real Self-host Collaboration Acceptance](plans/2026-08-29-sh1-real-self-host-collaboration-acceptance.md) — read-only self-host evidence that motivated W7.1; no real relation apply or destructive action.
- [2026-08-29 U1 Unified Observatory Architecture & Shell](plans/2026-08-29-u1-unified-observatory-architecture.md) — architecture phase complete under Accepted ADR-0016 and Approved Design; production U2 implementation, default transition and release remain separate work.
- [2026-08-29 CI6 Local Validation Router & Tier Enforcement](plans/2026-08-29-ci6-local-validation-router-tier-enforcement.md) — adds the repo-local change router, exact test registry, tier receipts and W6.1 cost separation without weakening Promotion coverage.
- [2026-08-29 W6.1 Incremental Maintenance & Quick Remove](plans/2026-08-29-w6-1-incremental-maintenance-quick-remove.md) — committed maintenance-v2 cache, background refresh and target-scoped Quick Remove Candidate consumed by the U2 integration baseline.
- [2026-08-29 A3 Authority Managed Consumer Contract](plans/2026-08-29-a3-authority-managed-consumer-contract.md) — versioned deterministic Authority consumer selection/readiness/rollback contract; no production consumer switch.
- [2026-08-29 SC1 Canonical State Closeout](plans/2026-08-29-sc1-canonical-state-closeout.md) — completed docs-only reconciliation; exact `a9369dd` passed Fast/Promotion and entered protected main without product, release or physical cleanup changes.
- [2026-08-29 CI5 Promotion Throughput Optimization](plans/2026-08-29-ci5-promotion-throughput-optimization.md) — completed no-coverage-loss CI optimization; exact `9ee831f` passed 25/25 hosted jobs and entered Canonical main while preserving 27 logical shards and required checks.
- [2026-08-28 Orrery Rename and Compatibility R3–R5](plans/2026-08-28-orrery-rename-and-compatibility.md) — active under Accepted ADR-0015; R3 is complete in Canonical main, while R4/R5 remain future independent Workstreams preserving Python identity and frozen v0.2.0 evidence.
- [2026-08-28 CI3 Fast Validation Dependency Fix](plans/2026-08-28-ci3-fast-validation-dependency-fix.md) — completed and contained in Canonical main; protects fresh-runner dependency order and conditional timing artifact upload without changing Fast or Promotion authority.
- [2026-08-28 W7D W7 Integration Candidate](plans/2026-08-28-w7d-w7-integration-candidate.md) — completed; CI2/W7B and W7C-B entered Canonical descendants with tiered budgets, read-only graph authority and separate execution boundaries intact.
- [2026-08-28 CI2 tiered test performance](plans/2026-08-28-ci2-tiered-test-performance.md) — completed and contained in Canonical descendants; preserves W7B coverage while reducing full-topology construction and adding explicit Fast／Checkpoint／W7B budgets.
- [2026-08-28 W7B Succession Apply／Undo／Legacy Inference](plans/2026-08-28-w7b-succession-apply-undo-legacy-inference.md) — completed and contained in Canonical descendants; provides exact local discovery, confirmation-bound transaction／recovery, append-only receipt/undo and self-host read-only diagnostics.
- [2026-08-28 W7C-B Production Workstream Relation Graph Observatory](plans/2026-08-28-w7c-b-production-workstream-relation-graph.md) — completed and contained in Canonical descendants; provides the root-only/default-off Core v1 graph consumer and three read-only lenses without a graphic execution surface.
- [2026-08-28 W7A Dynamic Workstream Succession Contract](plans/2026-08-28-dynamic-workstream-succession-contract.md) — completed and contained in Canonical descendants; defines the v1 relation record/graph/plan schema, Git-common-private boundary and read-only graph/succession CLI.
- [2026-08-27 W5E Team Observatory UI closeout](plans/2026-08-27-w5e-team-observatory-ui-closeout.md) — completed and contained in Canonical descendants; removes redundant Team summaries and moves low-frequency diagnostics into a secondary dialog without changing authority.
- [2026-08-27 Workspace Maintenance and scheduled cleanup](plans/2026-08-27-workspace-maintenance-and-scheduled-cleanup.md) — Phase 0–2 are contained in Canonical main; opt-in automatic worktree removal and cross-platform scheduler Adapters remain future phases.
- [2026-08-27 W5C Team Observatory information architecture](plans/2026-08-27-w5c-team-observatory-ux.md) — completed and contained in Canonical descendants; turns the W5B protocol surface into a human-readable Team view without changing Team authority.
- [2026-08-21 documentation governance and read-only audit](plans/2026-08-21-document-governance-and-audit.md) — active under ADR-0012; Phase 0 self-host governance and D1 internal finding contract／synthetic fixtures are complete as Candidate work, while scanner／CLI, Observatory and release adoption remain future phases.
- [2026-08-21 M2.2 Observatory Authority Candidate projection](plans/2026-08-21-m2-2-observatory-authority-projection.md) — completed and locally integrated; consumes the M2.1 bundle under an explicit root-only opt-in while preserving the legacy default and independent rollback.
- [2026-08-21 M2.3 Authority Model 1 release/installer candidate gate](plans/2026-08-21-m2-3-authority-release-candidate-gate.md) — completed and locally integrated; validates maintainer-supplied release inputs without selecting a public SemVer, changing v0.2.0 history or claiming release readiness.
- [2026-08-21 M2.1 complete CLI Authority observations/claims](plans/2026-08-21-m2-1-authority-cli-claims.md) — completed and locally integrated; provides deterministic lifecycle, relation, role and evidence-provenance claims while leaving legacy CLI behavior unchanged.
- [2026-08-21 Authority Meta Model conformance and gradual extraction](plans/2026-08-21-authority-meta-model-conformance-and-extraction.md) — active Plan under ADR-0009/0010/0011; fixture、Core evaluator、consumer shadow、compatibility、receipt-gated migration/restore 与 root-only projection 已进入 source，实际 release 和 production switch 仍待后续验证。
- [2026-08-19 multi-worktree collaboration protocol](plans/2026-08-19-multi-worktree-collaboration-protocol.md) — active under ADR-0007 and ADR-0008; Personal foundation precedes review/cleanup and opt-in Team Mode.
- [2026-08-18 self-hosting completion](plans/2026-08-18-self-hosting-completion.md) — completed migration plan; see its linked State and Validation records for current facts.
- [2026-08-18 v0.2.0 first public release](plans/2026-08-18-v0.2.0-first-public-release.md) — completed; records product, research, self-hosting, CI correction, tag, and release-state boundaries.
- [2026-08-19 docsite credential hardening](plans/2026-08-19-docsite-credential-hardening.md) — completed; implements ADR-0003 provider binding, fail-closed activation, local HTTP hardening, and an optional deterministic broker.
- [2026-08-19 platform-neutral Core and Agent/Harness Adapters](plans/2026-08-19-platform-neutral-core-and-adapters.md) — active; phases the Core/CLI extraction, Codex reference Adapter, non-Codex Harness sample, and later evidence-gated second-platform work.
- [2026-08-19 Pilot 008 Skill Entry Router](plans/2026-08-19-skill-entry-router-pilot-008.md) — preparation completed; freezes the compact Skill-entry candidate, real-development fixture, independent Oracle and nested preflight without running formal model samples.
- [2026-08-19 Broker-first docsite gateway](plans/2026-08-19-broker-first-docsite-gateway.md) — completed; removes direct Provider runtime paths and makes the managed or external Broker the only docsite model gateway.
- [2026-08-19 Pilot 008 Scope Acquisition reframe](plans/2026-08-19-scope-acquisition-pilot-008.md) — stopped after its first formal pair exposed an external Skill read and shared Oracle false negatives; its sealed samples are not adoption evidence.
- [2026-08-19 Pilot 009 corrected Scope Acquisition comparison](plans/2026-08-19-scope-acquisition-pilot-009.md) — completed; six valid runs passed all cost guards, while corrected quality stayed at 2/3 on both sides and S was not adopted.
