# A4 Portable Operating Rules & Authority Route Preflight

Status: Candidate implemented and validated; awaiting central integration

Date: 2026-08-30

Exact task base: `codex/u1-u2-integration-baseline@3fc7e7aacedafa8fbd20f9f79ddb8cf5784a0ef3`

Workstream: Git-private `A4-portable-meta-rules-bootstrap-contract`

Governing ADRs: [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../../decisions/0011-authority-model-version-and-compatibility.md), [ADR-0012](../../decisions/0012-document-governance-and-information-lifecycle.md), [ADR-0018](../../decisions/0018-portable-operating-rules-and-authority-route-preflight.md)

Approved Design: [Authority Meta Model](../../design/authority-meta-model.md), section “Portable Operating Rules 与 Authority Route Preflight”

Primary subsystem: `authority-meta-model`

Affected subsystems: `documentation-system`, `release-and-toolchain`, `test-coverage`, `project-structure`

## Goal and non-goals

Deliver the last-mile distribution and consumption guarantees for the existing Authority Meta Model. A4 does not create a new meta layer or evaluator owner, copy Orrery self-host State into target projects, change v0.2.0 history, choose a public SemVer, switch a default consumer, publish a release, or push `main`.

The work is split into two dependent checkpoints so a synonym patch cannot be mistaken for completion.

## A4a — portable inventory and consumer wiring

- [x] Add dependency-free `orrery-operating-rules-v1` schema, canonical Core inventory, parser/hash/compatibility judgment and read-only projection.
- [x] Distill only cross-project rules; reject current State, project goals, component/release facts and experiment conclusions.
- [x] Fail missing, unknown, malformed and tampered inventory to read-only/Unknown; never choose latest implicitly.
- [x] Add bounded CLI inspect/capability JSON with no writes or Authority/release promotion.
- [x] Add exact Skill-only JSON projection and update `SKILL.md` bootstrap order; protect byte-for-byte drift against Core.
- [x] Explain the Orrery-rules/project-Seed distinction in canonical new-project templates and exact Skill template projection.
- [x] Preserve brownfield AGENTS/Seed/State bytes under install and `--upgrade-tools`; preserve migration-pending/integrated separation.
- [x] Reuse the existing single `authority` navigation/route and turn it into a “事实与规则” composition: project principles, Orrery operating-rules ledger, and collapsed interpretation/readiness details. Do not add a ninth sidebar item or an independent meta-rules page; keep any dynamic data endpoint under `/api/v1/authority`.

## A4b — Authority Route Preflight and absence gate

- [x] Add provider-neutral normalized concept registry/source observation/intent input and `authority-route-preflight-v1` receipt in Core.
- [x] Emit query class, selected concepts, governing sources, excluded lower-authority sources, four axes, Unknown/reasons, negative-evidence scope and deterministic hash.
- [x] Implement conservative alias recall, ambiguity fan-out, authority precedence and stable concept IDs without keyword-only conclusions.
- [x] Refuse semantic absence when indexed governing sources exist; downgrade incomplete registry/State/ADR/evidence searches to Unknown.
- [x] Add a bounded CLI repository collector that follows AGENTS → State → governing ADR/Design → requested evidence and never infers project-wide state from templates/local code.
- [x] Expose inspect through Harness JSON with a fixed argument allowlist and unchanged common envelope guarantees.
- [x] Make Observatory Ask Docs call preflight before authority context selection; preflight failure must preserve Unknown and may not be overridden by model prose.
- [x] Label Skill-only use as advisory; report Adapter enforcement only for a runtime-verified pre-model hook.

## Version and release boundaries

- [x] Advance Core/CLI/Observatory and the modified Harness Adapter source versions only for actual unreleased changes.
- [x] Keep `CORE_API_VERSION`, CLI/Harness common envelope schema and public v0.2.0 manifest/tag/checksum/history unchanged; the additive route receipt has its own internal schema version.
- [x] Keep all new consumers source-only, unreleased, root-only/default-off or explicitly invoked.
- [x] Confirm package exclusions for credentials, caches, Git-private workstream state, generated site and local browser artifacts.

## Conformance and negative matrix

- [x] A4 real failure: Meta Model/ADR/evaluator present, ordinary Skill distribution wiring missing, public A4 release absent.
- [x] Existing Approved Design but no implementation.
- [x] Implementation present but no public release.
- [x] Old public version released while new Candidate remains unreleased.
- [x] Template lacks a capability but Core implementation exists.
- [x] Relevant State explicitly reports Unknown.
- [x] Similar names map to different stable concepts.
- [x] Misleading template/README/Agent assertion conflicts with governing State/ADR.
- [x] Chinese, English and indirect phrasing converge on the same concept/claim shape.
- [x] Mutation: remove literal alias keywords while preserving intent.
- [x] Negative: stale State, broken ADR link, unindexed concept, unknown schema/inventory, forged Agent assertion, missing/tampered inventory.
- [x] Assert selected/excluded evidence and four-axis claims; do not assert one fixed natural-language answer.

## Installation, static/dynamic and browser validation

- [x] Dependency-free focused schema/fixture/Core/CLI/Skill/Harness/Observatory tests.
- [x] Temporary new-project scaffold dry-run/install/validate and layer-discovery checks.
- [x] Brownfield install and `--upgrade-tools` dry-run/apply checks with custom Seed byte-for-byte preservation.
- [x] Skill-only inspect and missing-Core fallback remain advisory/read-only without inventing claims.
- [x] Static Unified build separates project principles/rules/status inside the existing Authority view and has no dynamic controls; dynamic endpoint/Ask Docs preflight are read-only and zero new network authority.
- [x] Real browser 1440×900 and 390×844: project Seed vs Orrery rules visibly distinct, no horizontal overflow, core navigation/details work, console error/warning empty.
- [x] Do not stop, reuse or mutate the central `http://127.0.0.1:63203` acceptance service; the isolated `63204` process was stopped after acceptance while `63203` remained listening.

## Repository and CI6 gates

- [x] `scripts/ci/validate_change.py --tier fast --dry-run`
- [x] `scripts/ci/validate_change.py --tier fast`
- [x] `scripts/ci/validate_change.py --tier checkpoint --dry-run`
- [x] `scripts/ci/validate_change.py --tier checkpoint`
- [x] Integrated installation/links/docsite/repository gates.
- [x] Release dry build and package content/exclusion checks.
- [x] Secret/generated-artifact boundary and `git diff --check`.
- [x] Do not run full Promotion as the development loop; no push/main/release operation is authorized.

## Documentation synchronization and handoff

- [x] Update Authority Meta Model, Documentation System, Release/Toolchain, Test Coverage and Project Structure State with Candidate facts and remaining public/default gaps.
- [x] Record reproducible commands/results in A4 Validation, append DEVLOG and update the Validation/ADR/Plan indexes.
- [x] Do not modify root `docs/PROGRESS.md` or `docs/HANDOFF.md`; the central integrator owns those entrances.
- [x] Commit a clean Candidate and report exact HEAD, source component versions, CI6 Fast/Checkpoint receipts, browser/install/package evidence, unreleased/default-safe boundary and integration order.
- [x] Final receipt separately states mechanical guarantees, Agent/Skill best-effort behavior and host-hook-dependent enforcement.
