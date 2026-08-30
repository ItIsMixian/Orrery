# ADR-0022: ELK.js as the Workstream Graph Layout Engine

Status: Accepted

Date: 2026-08-30

Amends: [ADR-0020](0020-workstream-program-and-phase-hierarchy.md)

Preserves: [ADR-0016](0016-unified-observatory-shell-and-single-local-entry.md),
[ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0021](0021-v0-3-0-release-scope-default-matrix.md)

## Context

W7.3 retained valid relation capture, authority and inbox work, but its Graph presentation repeatedly failed visual
acceptance. The current implementation duplicates handwritten rank, component packing, orthogonal routing and label
placement in Python and Browser JavaScript. Successive fixes for global rank, program containment, module filtering,
route bundles and post-pack bounds displaced rather than removed defects: single columns, W towers, route crossings,
overlap, floating labels, over-expanded module context and unrelated dependency nodes.

These failures mix two different responsibilities. Orrery must decide which facts, nodes, groups and edges are visible;
layout software should compute geometry for that already-frozen graph. Continuing to grow the custom geometry code
would preserve two competing implementations and make screenshots the first collision detector.

The maintainer has selected ELK.js for the layout/routing layer while explicitly preserving the current Orrery frontend
design.

## Decision

1. **ELK.js becomes the sole product geometry engine for Workstream Graph.** It computes compound-container sizes,
   node coordinates, ports, orthogonal edge sections/bend points and edge-label positions. The rejected handwritten
   Python and Browser layout/routing algorithms are removed rather than retained as a fallback.
2. **Orrery keeps semantic ownership.** Core/Observatory preprocessing determines lens, module/status filters, history
   folding, boundary stubs, program/phase membership, series display, relation identity and evidence before ELK is
   called. ELK output cannot add/remove facts, infer relations or change authority.
3. **Orrery keeps rendering and design ownership.** Existing SVG cards, typography, colors, semantic borders, legend,
   Chinese copy, zoom/pan, selection, inspector, themes, keyboard behavior and mobile same-fact projection remain.
   ELK is not adopted as a UI/diagram framework and introduces no generic node-editor chrome.
4. **Module views are primary-first.** A concrete module's default full cards match only explicit
   `primary_subsystem_id`. Explicit affected-task context and semantic-neighbor context are separate default-off layers.
   Semantic context is one hop, excludes series-only expansion and is bounded; overflow is represented by a summary
   boundary node, never by silently returning the all-node graph.
5. **Lens admission is relation-specific.** Dependency full nodes are exactly endpoints of scoped `depends_on`
   facts/proposals. Program/phase, active-tip or series membership cannot add an isolated dependency node. A subdued
   series connector is allowed only when both endpoints are already admitted by dependency facts. Conflict follows
   confirmed conflict endpoints; succession follows its accepted relation/series contract.
6. **Program/phase uses compound hierarchy.** W, W5, W6 and W7 are supplied as compound containers with explicit
   membership and real cross-hierarchy edges. Membership creates containment only. It neither fabricates an edge nor
   forces disconnected members into a manually positioned tower.
7. **Labels fail closed.** Edge labels are measured inputs to ELK and use returned coordinates. A missing/invalid label
   coordinate omits the canvas label and keeps the text in the inspector; it never falls back to a component corner.
8. **Pinned, offline and self-contained.** The first implementation pins the exact released ELK.js artifact validated
   by GX2, stores its upstream/ref/version/SHA-256/size/license provenance, and packages only local reviewed bytes. No
   CDN or runtime network request is allowed. The v0.3.0 self-contained ZIP includes the required asset and license.
9. **One geometry source.** Python tests validate semantic input and serialized ELK contracts; Browser/JavaScript tests
   validate the actual ELK output. Python must not reimplement ELK placement or routing for parity assertions.
10. **Deterministic bounded execution.** Inputs use stable IDs/order, pinned options and fixed seeds/model-order rules.
    Layout runs asynchronously with a bounded failure/timeout path. Failure shows the existing accessible relation
    ledger plus `布局不可用`; it does not run the rejected custom renderer or present stale geometry as current.
11. **Adoption is evidence-gated.** GX2 must first record the exact asset/provenance and demonstrate the four rejected
    cases. W7.3 then integrates the same pinned engine, preserves Core/capture changes, replaces only presentation
    geometry, and returns to maintainer Browser acceptance before Fast/Checkpoint or release work.

## Consequences

- The frontend remains recognizably Orrery; only spatial arrangement and route geometry are delegated.
- Compound groups, cross-hierarchy edges, ports, orthogonal routing, crossing minimization and edge labels use one
  mature engine instead of continuing custom heuristics.
- The repository gains a reviewed vendored JavaScript dependency, provenance/license/SBOM obligations and additional
  release bytes. These are accepted tradeoffs for replacing the failed dual geometry implementation.
- A missing engine can reduce Graph to the accessible ledger but cannot affect relation facts, confirmation authority,
  Team privacy, execution permissions or other Observatory pages.
- Replacing ELK, restoring custom geometry, using a CDN or allowing layout output to select facts requires a later ADR.

## Mapping

- Approved Design: [ELK.js Workstream Graph Layout and Orrery Rendering](../design/elkjs-workstream-graph-layout-and-rendering.md)
- Evaluation Plan: [GX2 ELK Layout Engine Evaluation](../implementation/plans/2026-08-30-gx2-elk-layout-engine-evaluation.md)
- Implementation Plan: [W7.3 Workstream Relation Capture](../implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)
- Validation: [W7.3 Workstream Relation Capture & Confirmation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)

