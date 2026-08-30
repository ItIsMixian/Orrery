# Approved Design: ELK Cutover and Explicit Legacy Fallback

Status: Approved

Date: 2026-08-30

Governing decision: [ADR-0023](../decisions/0023-explicit-legacy-graph-layout-fallback.md)

Extends: [ELK.js Workstream Graph Layout and Orrery Rendering](elkjs-workstream-graph-layout-and-rendering.md)

## Engine interface

Both engines consume one Orrery-owned immutable contract:

```text
GraphProjection
  node IDs / edge IDs / compound membership
  measured node + edge-label sizes
  semantic styles / ports / input hash / revision
        │
        ├── ElkLayoutEngine.layout(input)
        └── LegacyLayoutEngine.layout(input)
                  ↓
LayoutResult
  same IDs / engine ID / input hash / coordinates / sections / labels / diagnostics
```

The engine adapter rejects added/missing IDs, stale revisions, non-finite geometry and result/input hash mismatch before
rendering. Engine selection never changes GraphProjection.

## Evaluation and cutover sequence

1. GX2 renders the local ELK experiment only; W7.3 product files remain untouched.
2. The maintainer reviews succession, W compound, Project Structure and dependency at desktop/mobile.
3. If rejected, product integration remains blocked and the current source is unchanged.
4. If accepted, the coordinator submits a new exact task-description version authorizing product integration.
5. W7.3 extracts the current custom geometry behind `LegacyLayoutEngine`, implements the shared projection and pinned
   `ElkLayoutEngine`, then presents a product Candidate.
6. Only after product visual acceptance may ELK become the normal engine and routed Fast/Checkpoint run once.

ADR-0022 acceptance alone does not skip steps 2 or 4.

## Legacy-mode behavior

- The technical settings/help panel contains the engine choice; it is not a new primary navigation page or prominent
  ordinary-user control.
- Normal post-acceptance value is `ELK`. `旧版兼容布局` is selected only by an explicit local action.
- ELK failure shows ledger/error first. The user may retry or explicitly select legacy; no timer or exception handler
  switches engines automatically.
- Legacy mode displays a persistent compact label and its diagnostics identify the legacy engine.
- The selection is local, contains no project fact and is never synchronized through Team Mode.
- Reset resets graph view state but does not silently alter the explicitly chosen engine.

## Frozen legacy boundary

The legacy engine keeps only geometry code. Module/lens/status/context admission, W membership, history folding,
relation identity and edge styling move to the shared GraphProjection. Legacy compatibility changes may adapt ports or
input schema and prevent crashes, but cannot grow a second semantic model or claim ELK geometry acceptance.

The old implementation remains recoverable in source history and the named module. Rejected screenshot behavior is
documented rather than erased. Removal would require a later ADR and evidence that the recovery path no longer has
value.

## Validation

- GX2 page shown before any product diff;
- exact equal input IDs/hashes for ELK and legacy engines;
- explicit engine selection and persistent legacy label;
- ELK error remains ledger-first with no automatic fallback;
- legacy renders boundedly without crashing or changing facts;
- ELK retains primary geometry/browser acceptance ownership;
- both engines are zero-network and intentionally included/excluded by the reviewed package manifest;
- desktop/mobile help/settings accessibility and no new top-level navigation.

