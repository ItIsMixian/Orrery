# ADR-0023: Explicit Legacy Graph Layout Fallback and Preview-first Cutover

Status: Accepted

Date: 2026-08-30

Amends: [ADR-0022](0022-elkjs-workstream-graph-layout-engine.md)

Preserves: [ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0020](0020-workstream-program-and-phase-hierarchy.md),
[ADR-0021](0021-v0-3-0-release-scope-default-matrix.md)

## Context

ADR-0022 selected ELK.js for Workstream Graph layout/routing and required removal of the rejected handwritten geometry
instead of retaining two active implementations. The maintainer subsequently clarified two requirements:

1. the handwritten implementation should remain available as a recovery option if ELK proves unsuitable; and
2. the team must first inspect the isolated ELK output before any product integration, dependency write or default
   cutover.

Retaining a recovery path is different from silently falling back. The old renderer has known visual defects, so an
automatic switch would hide ELK failures and unexpectedly reintroduce rejected geometry. A bounded explicit legacy
mode preserves reversibility without pretending both engines are equally accepted.

## Decision

1. **Preserve a frozen legacy geometry engine.** The current handwritten node placement, packing, routing and label
   implementation is retained in a separately named compatibility module or recoverable source snapshot. It is not
   deleted during ELK integration.
2. **One semantic projection remains mandatory.** Orrery computes module/lens/history/context/program facts once and
   produces the same immutable LayoutInput for ELK and legacy engines. The legacy path cannot keep its old independent
   node-admission or filtering logic.
3. **No automatic geometry fallback.** ELK timeout, exception or invalid result first shows the same-fact accessible
   ledger and `ELK 布局不可用`. It may offer explicit `重试 ELK` and `使用旧版布局` actions; it cannot silently invoke
   legacy geometry.
4. **Legacy use is explicit and visible.** A local-only advanced/technical setting may select the legacy engine. The
   canvas displays `旧版兼容布局` while active and explains that geometry may be less readable. The choice grants no
   new facts, authority or network behavior.
5. **Legacy is frozen, not co-developed.** It receives compatibility/security fixes needed to consume the shared
   LayoutInput, but new layout features target ELK. Geometry parity is neither required nor claimed. Any material
   redesign of legacy layout requires separate approval.
6. **Preview before product cutover.** GX2 remains experiment-only. W7.3 may not vendor ELK into product, refactor the
   production engine interface, remove/move legacy code or change defaults until the maintainer reviews the GX2 page
   and explicitly accepts product integration.
7. **Post-acceptance default.** If the maintainer accepts the GX2 visual result and later product Candidate, ELK becomes
   the normal engine and legacy remains manual opt-in. Until then, no adoption decision is represented as implemented
   or default.
8. **Both paths are local and packaged deliberately.** A future v0.3.0 Candidate includes the pinned ELK bytes plus
   the frozen legacy module, their engine IDs and failure/selection contract. Neither path uses a CDN or remote data.
9. **Tests share facts, not coordinates.** Semantic tests prove both engines receive the same IDs. ELK Browser tests
   own primary geometry acceptance; legacy tests only prove bounded rendering, explicit labeling, no crash and no
   authority/fact divergence.

## Consequences

- The project retains a practical recovery path without letting bad geometry mask ELK failure.
- Product code carries two geometry engines but only one semantic projection and one normal default after acceptance.
- Bundle size and maintenance increase slightly; the legacy engine is intentionally frozen to bound this cost.
- GX2 visual review becomes a mandatory human gate before product integration, not merely supporting evidence.
- Silent fallback, two independent filters or an unlabeled legacy canvas violate this decision.

## Mapping

- Approved Design: [ELK Cutover and Explicit Legacy Fallback](../design/elkjs-cutover-and-explicit-legacy-fallback.md)
- Evaluation Plan: [GX2 ELK Layout Engine Evaluation](../implementation/plans/2026-08-30-gx2-elk-layout-engine-evaluation.md)
- Implementation Plan: [W7.3 Workstream Relation Capture](../implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)
- Validation: [W7.3 Workstream Relation Capture & Confirmation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)

