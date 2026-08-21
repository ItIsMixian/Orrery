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

- [2026-08-21 Authority Meta Model conformance and gradual extraction](plans/2026-08-21-authority-meta-model-conformance-and-extraction.md) — active Candidate Plan under ADR-0009/0010/0011; fixture、Core shadow、consumer shadow、compatibility 与 receipt-gated migration/restore 已形成检查点，release projection 和 production switch 仍待后续验证。
- [2026-08-19 multi-worktree collaboration protocol](plans/2026-08-19-multi-worktree-collaboration-protocol.md) — active under ADR-0007 and ADR-0008; Personal foundation precedes review/cleanup and opt-in Team Mode.
- [2026-08-18 self-hosting completion](plans/2026-08-18-self-hosting-completion.md) — completed migration plan; see its linked State and Validation records for current facts.
- [2026-08-18 v0.2.0 first public release](plans/2026-08-18-v0.2.0-first-public-release.md) — completed; records product, research, self-hosting, CI correction, tag, and release-state boundaries.
- [2026-08-19 docsite credential hardening](plans/2026-08-19-docsite-credential-hardening.md) — completed; implements ADR-0003 provider binding, fail-closed activation, local HTTP hardening, and an optional deterministic broker.
- [2026-08-19 platform-neutral Core and Agent/Harness Adapters](plans/2026-08-19-platform-neutral-core-and-adapters.md) — active; phases the Core/CLI extraction, Codex reference Adapter, non-Codex Harness sample, and later evidence-gated second-platform work.
- [2026-08-19 Pilot 008 Skill Entry Router](plans/2026-08-19-skill-entry-router-pilot-008.md) — preparation completed; freezes the compact Skill-entry candidate, real-development fixture, independent Oracle and nested preflight without running formal model samples.
- [2026-08-19 Broker-first docsite gateway](plans/2026-08-19-broker-first-docsite-gateway.md) — completed; removes direct Provider runtime paths and makes the managed or external Broker the only docsite model gateway.
- [2026-08-19 Pilot 008 Scope Acquisition reframe](plans/2026-08-19-scope-acquisition-pilot-008.md) — stopped after its first formal pair exposed an external Skill read and shared Oracle false negatives; its sealed samples are not adoption evidence.
- [2026-08-19 Pilot 009 corrected Scope Acquisition comparison](plans/2026-08-19-scope-acquisition-pilot-009.md) — completed; six valid runs passed all cost guards, while corrected quality stayed at 2/3 on both sides and S was not adopted.
