# Approved Design: ELK.js Workstream Graph Layout and Orrery Rendering

Status: Approved

Date: 2026-08-30

Governing decision: [ADR-0022](../decisions/0022-elkjs-workstream-graph-layout-engine.md)

## Design brief

- **Purpose:** let maintainers scan authoritative task relationships without overlapping cards, detached relationship
  substitutes or unexplained nodes.
- **Context:** read-only dense analyst workspace inside the Unified Orrery Observatory.
- **Tone:** preserve the current restrained engineering visual system.
- **Differentiator:** Orrery chooses and explains every fact; ELK produces one deterministic compound layout for those
  exact facts; existing SVG renders the result.
- **Constraints:** zero-network Personal Mode, local self-contained distribution, Chinese UI, keyboard/ARIA, desktop
  and mobile, no new execution authority and no generic diagram-editor redesign.

## Ownership boundary

```text
Core / Observatory facts
→ Orrery lens + module/status + history + context projection
→ immutable LayoutInput with exact IDs and measured sizes
→ pinned local ELK.js
→ immutable LayoutResult with coordinates/ports/sections/labels
→ existing Orrery SVG/cards/inspector/ledger
```

Orrery owns both arrows around ELK. The input and output carry the same node/edge IDs; an ID-set mismatch rejects the
layout. ELK does not receive source text, Prompt/transcript, credentials, private evidence bodies or execution actions.

## Semantic projection before layout

### Module view

- `全部模块`: all lens-eligible full cards.
- Concrete module: full cards whose explicit primary subsystem equals the selected module.
- `显示受影响任务`: separate default-off layer for tasks explicitly listing the selected module in affected IDs.
- `显示关联上下文`: separate default-off one-hop semantic-neighbor layer from currently admitted full cards. Series
  display alone does not expand context. At most 12 external full cards are admitted; the remainder becomes one
  inspectable `+N 外部关联` boundary summary.
- Unknown/unregistered module facts remain in `未归属`; no view silently falls back to all modules.

Module/status uses intersection semantics. Every layer reports full-card, boundary and edge counts separately.

### Lens view

- Succession: accepted succession/absorbs behavior plus explicit series-display connectors and the accepted history
  contract.
- Dependency: `depends_on` endpoints only. Series connectors render only between already admitted endpoints; program,
  phase and active-tip membership cannot create singleton cards.
- Conflict: confirmed conflict endpoints only; comparison remains a separate default-off layer.

The exact node/edge ID set is frozen and hashed before ELK. The layout receipt repeats the input hash and counts.

## ELK graph model

- Root uses layered left-to-right layout, orthogonal routing, deterministic model order, separated connected components
  and explicit spacing derived from existing card dimensions.
- Cards are fixed-size leaf nodes. Their source/target ports are explicit and stable so arrow direction, hit targets
  and semantic route style remain Orrery-owned.
- W is a compound program node with W5/W6/W7 compound phase children. Membership is represented only by containment.
  CI/SH/U nodes remain outside while real cross-hierarchy edges connect normally.
- Edge labels are supplied with measured width/height. Returned label positions are used unchanged except for the root
  SVG translation. Invalid/missing label geometry becomes inspector-only text.
- ELK coordinates are immutable. Orrery may translate the whole root for padding and apply view zoom/pan, but cannot
  independently move nodes or rewrite edge sections.

The exact pinned options and ELK version are recorded in a product provenance file after GX2. Updating either changes
the layout contract and requires focused visual revalidation.

## Rendering preservation

The current Orrery DOM/SVG component owns:

- node card rect/text, status/dashed borders and task metadata;
- series/succession/dependency/comparison/conflict strokes and arrow markers;
- W/phase container header/background styling;
- selection/focus/dimming and the evidence inspector;
- zoom, pan, reset, fit and responsive ledger;
- dark/light variables and Chinese display vocabulary.

ELK-owned coordinates may alter whitespace and ordering, but no CSS token, typography scale, card information hierarchy
or interaction is changed merely to accommodate the engine. A visual snapshot compares representative cards and
controls against the accepted pre-ELK Orrery shell.

## Runtime and failure

- The reviewed ELK bytes are loaded locally. Static output embeds or references only packaged local bytes; dynamic
  serving sets no external URL.
- Layout is asynchronous and exposes loading state without shifting the surrounding shell. Selection/filter changes
  cancel or supersede stale results using an input revision/hash.
- Result validation checks ID equality, finite non-negative geometry, parent containment, node/container overlap,
  route/node intersection, label bounds and canvas extent before display.
- Missing asset, timeout, exception or invalid result fails to the same-fact accessible ledger and an explanatory
  `布局不可用` state. No custom geometry fallback, remote fetch or fabricated empty graph.

## Packaging and provenance

Product adoption vendors only the exact GX2-validated release artifacts needed by the chosen execution mode. The
package contains upstream URL/ref/version, SHA-256, size, license text and inclusion reason; component/release manifests
bind these files. Release builders include them through tracked Git inputs, and Windows/Ubuntu deterministic package
comparison covers their bytes.

No npm installation, CDN, build-time download or network availability is required for end users. Updating the vendor
asset is an explicit source change with new validation.

## Migration

1. Finish GX2 provenance and geometry report.
2. Preserve the current W7.3 dirty diff in recoverable Git-private evidence without discarding Core/capture work.
3. Separate semantic projection from geometry in the Graph presentation module.
4. Remove the custom Python/browser rank, pack, route and label algorithms.
5. Add the pinned local ELK adapter and existing-SVG renderer mapping.
6. Reapply the accepted W7.3 module/lens/history/program semantics as pre-layout ID-set tests.
7. Obtain focused Browser acceptance; only then run one routed Fast and one Checkpoint.

## Validation

- exact input/output ID-set and hash equality;
- primary-only module view, bounded affected/context layers and `未归属`;
- dependency endpoints only, no isolated program/series/active-tip nodes;
- W/W5/W6/W7 compound containment and real cross-hierarchy edges;
- zero floating labels, card/container overlap and edge-through-node for current self-host and stress fixtures;
- unchanged representative card/control/theme/inspector visual snapshots;
- selection, keyboard focus, reset/fit and stale-layout cancellation;
- 1440×900, 1280×800 and 390×844 Browser review;
- local-only asset, failure-to-ledger, package provenance/license and deterministic ZIP coverage.

