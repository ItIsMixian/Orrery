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

- [2026-08-28 Orrery Rename and Compatibility R3–R5](plans/2026-08-28-orrery-rename-and-compatibility.md) — planned and blocked on ADR-0015 acceptance; separates brand-only closeout, compatible aliases and an optional package/CLI default transition while preserving Python identity and frozen v0.2.0 evidence.
- [2026-08-28 CI3 Fast Validation Dependency Fix](plans/2026-08-28-ci3-fast-validation-dependency-fix.md) — installs real Fast discovery dependencies before contract validation, mechanically protects ordering and conditionally uploads only an existing timing result without changing the 15-second Fast or Promotion contracts.
- [2026-08-28 W7D W7 Integration Candidate](plans/2026-08-28-w7d-w7-integration-candidate.md) — integrates CI2/W7B and W7C-B additively, preserves tiered budgets and read-only graph authority, and freezes the non-`main` exact-SHA Promotion handoff.
- [2026-08-28 CI2 tiered test performance](plans/2026-08-28-ci2-tiered-test-performance.md) — completed Worktree Candidate that preserves W7B coverage while reducing full-topology construction to two Promotion journeys and adds explicit Fast／Checkpoint／W7B hard budgets.
- [2026-08-28 W7B Succession Apply／Undo／Legacy Inference](plans/2026-08-28-w7b-succession-apply-undo-legacy-inference.md) — completed Candidate Plan for exact local discovery, confirmation-bound transaction／recovery, append-only receipt/undo and self-host read-only diagnostics.
- [2026-08-28 W7C-B Production Workstream Relation Graph Observatory](plans/2026-08-28-w7c-b-production-workstream-relation-graph.md) — completed Worktree Candidate for the root-only/default-off Core v1 graph consumer, three read-only lenses, fail-closed evidence projection and desktop/mobile browser acceptance; W7B execution and Promotion remain separate.
- [2026-08-28 W7A Dynamic Workstream Succession Contract](plans/2026-08-28-dynamic-workstream-succession-contract.md) — active Candidate Plan for the v1 relation record/graph/plan schema, dependency-free Core validation, Git-common-private read/append boundary, read-only graph/succession CLI and W7B/W7C handoff contracts.
- [2026-08-27 W5E Team Observatory UI closeout](plans/2026-08-27-w5e-team-observatory-ui-closeout.md) — active Worktree plan that removes redundant Team summaries, keeps Team Mode／connection／online controls visible, and moves low-frequency local diagnostics into a secondary dialog without changing Core or network authority.
- [2026-08-27 Workspace Maintenance and scheduled cleanup](plans/2026-08-27-workspace-maintenance-and-scheduled-cleanup.md) — proposed W6 Candidate Plan under ADR-0007/0008: event-driven and startup catch-up scans first, local confirmation execution second, explicit opt-in automatic worktree removal third, and cross-platform OS scheduler Adapters last.
- [2026-08-27 W5C Team Observatory information architecture](plans/2026-08-27-w5c-team-observatory-ux.md) — active Worktree plan that turns the verified W5B protocol surface into a human-readable team command view without changing Team authority, network, request-only or release boundaries.
- [2026-08-21 documentation governance and read-only audit](plans/2026-08-21-document-governance-and-audit.md) — active under ADR-0012; Phase 0 self-host governance and D1 internal finding contract／synthetic fixtures are complete as Candidate work, while scanner／CLI, Observatory and release adoption remain future phases.
- [2026-08-21 M2.2 Observatory Authority Candidate projection](plans/2026-08-21-m2-2-observatory-authority-projection.md) — completed and locally integrated; consumes the M2.1 bundle under an explicit root-only opt-in while preserving the legacy default and independent rollback.
- [2026-08-21 M2.3 Authority Model 1 release/installer candidate gate](plans/2026-08-21-m2-3-authority-release-candidate-gate.md) — completed and locally integrated; validates maintainer-supplied release inputs without selecting a public SemVer, changing v0.2.0 history or claiming release readiness.
- [2026-08-21 M2.1 complete CLI Authority observations/claims](plans/2026-08-21-m2-1-authority-cli-claims.md) — completed and locally integrated; provides deterministic lifecycle, relation, role and evidence-provenance claims while leaving legacy CLI behavior unchanged.
- [2026-08-21 Authority Meta Model conformance and gradual extraction](plans/2026-08-21-authority-meta-model-conformance-and-extraction.md) — active Candidate Plan under ADR-0009/0010/0011; fixture、Core shadow、consumer shadow、compatibility、receipt-gated migration/restore、future-release projection 与只读 update compatibility 已形成检查点，实际下一 release 和 production switch 仍待后续验证。
- [2026-08-19 multi-worktree collaboration protocol](plans/2026-08-19-multi-worktree-collaboration-protocol.md) — active under ADR-0007 and ADR-0008; Personal foundation precedes review/cleanup and opt-in Team Mode.
- [2026-08-18 self-hosting completion](plans/2026-08-18-self-hosting-completion.md) — completed migration plan; see its linked State and Validation records for current facts.
- [2026-08-18 v0.2.0 first public release](plans/2026-08-18-v0.2.0-first-public-release.md) — completed; records product, research, self-hosting, CI correction, tag, and release-state boundaries.
- [2026-08-19 docsite credential hardening](plans/2026-08-19-docsite-credential-hardening.md) — completed; implements ADR-0003 provider binding, fail-closed activation, local HTTP hardening, and an optional deterministic broker.
- [2026-08-19 platform-neutral Core and Agent/Harness Adapters](plans/2026-08-19-platform-neutral-core-and-adapters.md) — active; phases the Core/CLI extraction, Codex reference Adapter, non-Codex Harness sample, and later evidence-gated second-platform work.
- [2026-08-19 Pilot 008 Skill Entry Router](plans/2026-08-19-skill-entry-router-pilot-008.md) — preparation completed; freezes the compact Skill-entry candidate, real-development fixture, independent Oracle and nested preflight without running formal model samples.
- [2026-08-19 Broker-first docsite gateway](plans/2026-08-19-broker-first-docsite-gateway.md) — completed; removes direct Provider runtime paths and makes the managed or external Broker the only docsite model gateway.
- [2026-08-19 Pilot 008 Scope Acquisition reframe](plans/2026-08-19-scope-acquisition-pilot-008.md) — stopped after its first formal pair exposed an external Skill read and shared Oracle false negatives; its sealed samples are not adoption evidence.
- [2026-08-19 Pilot 009 corrected Scope Acquisition comparison](plans/2026-08-19-scope-acquisition-pilot-009.md) — completed; six valid runs passed all cost guards, while corrected quality stayed at 2/3 on both sides and S was not adopted.
