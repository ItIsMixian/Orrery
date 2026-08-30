# W7.2 Workstream Graph Readability & Progressive Disclosure

Status: W7.2 complete; W7.2.1/W7.2.2 implementation complete, local Checkpoint budget blocked

Date: 2026-08-29

Workstream: `W7.2-workstream-graph-readability-progressive-disclosure`

Branch/base: `codex/u2-1-unified-observatory-ux-acceptance-fixes` from exact integrated Candidate
`codex/u1-u2-integration-baseline@ad9f0946a191b8810d99f70171318a4d5536c425`.

Governing decisions: [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md) and
[ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md).

Approved Design: [Unified Observatory Architecture & Shell](../../design/unified-observatory-architecture-and-shell.md).

## Goal and boundary

Replace the rejected “fit every node into one viewport” graph presentation with a readable, single-direction,
progressively disclosed relation workspace. This is an Observatory presentation change only: consume the existing
hash-bound W7 Core graph and succession plan without changing Core relation schema, relation facts, archive authority,
apply/undo behavior or any execution capability.

## Compact design brief

- **Purpose:** let a maintainer trace why a current task exists, what directly precedes or blocks it, and which older
  evidence is hidden without decoding machine IDs or following crossing lines.
- **Context:** a dense operational evidence workspace inside the existing dark Orrery docsite; the real self-host graph
  is currently 16 nodes and 6 edges, so scrolling and progressive disclosure are legitimate, not defects.
- **Tone:** calm analyst workspace with visible lanes, strong causal direction and restrained technical detail.
- **Differentiator:** one left-to-right “earlier → direct predecessor/dependency → current” reading direction, with a
  separate clickable history cluster for each chain and the same expansion semantics in the mobile relation ledger.
- **Constraints:** generated HTML/CSS/vanilla JS, Chinese primary copy, 248×104px default cards, no external package or
  image asset, keyboard/ARIA/reduced-motion support, inspector closed by default, no page-level horizontal overflow,
  and no Core/domain-schema change.

## Layout and disclosure contract

1. Convert stored relation semantics to a display-only causal direction: for `derived_from`, `depends_on` and
   `absorbs`, the recorded target/predecessor is drawn on the left and the source/successor on the right. Core fields
   stay unchanged and remain visible in technical details.
2. Compute deterministic longest-path ranks over each selected lens. Render one vertical lane per rank, stable-sorted
   rows, 248×104px nodes, 112px inter-rank routing space and orthogonal left-to-right edge channels. Conflict pairs use
   the same left-to-right canvas direction without inventing causality.
3. Default each causal chain to its tip/current task, direct predecessors and required siblings. Older ancestors are
   represented by a chain-owned `更早历史 N 项` cluster. Expanding a cluster affects only that chain; global expand,
   collapse and reset are auxiliary controls.
4. Keep the graph at readable 100% scale by default and allow scroll/pan. Zoom, fit and reset are explicit. Fit has a
   readability floor and never becomes the default.
5. Keep technical evidence in a closed overlay drawer. Desktop uses the lane canvas; 390px uses a rank/chain ledger
   generated from the same visible fact IDs and expansion state.

## Implementation and acceptance

- [x] add display-only names/prefixes without changing the Core provider or schema;
- [x] implement deterministic horizontal ranks, lanes, fixed readable nodes and non-intersecting orthogonal routes;
- [x] isolate succession/dependency/conflict edges and give each lens its required route style and Chinese legend;
- [x] implement chain-local history clusters plus global expand/collapse and reset-to-default;
- [x] replace the permanent inspector column with a closeable overlay drawer;
- [x] add zoom, fit, reset and scroll/pan behavior without shrinking default text;
- [x] implement the 390px rank/chain relation ledger from the same visible graph model;
- [x] add mechanical layout/disclosure/lens/mobile parity regressions;
- [x] verify the real self-host graph at 1280×800, 1440×900 and 390×844;
- [x] synchronize affected State, W7.1/W7.2 Validation, DEVLOG and Validation index without editing root
  PROGRESS/HANDOFF.

## Validation ladder

```text
python -X utf8 -m unittest -v tests.test_workstream_relation_graph_observatory tests.test_unified_observatory
python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425
real browser: default / one-chain-expanded / node / edge / dependency / conflict / fit / reset
viewports: 1280×800, 1440×900, 390×844
git diff --check
```

Full Promotion, hosted Windows/Ubuntu checks, main integration, root PROGRESS/HANDOFF reconciliation and release remain
later work for the unique integrator.

## W7.2.1 maintainer correction

The maintainer's real-page review rejected line labels placed over routes, browser-focus rectangles around SVG paths,
surface-level folding and the lack of canvas-native zoom. The correction is registered as Git-private
`W7.2.1-workstream-graph-interaction-correction` from exact task base
`5523e6dcd8bac9eadc61fab95f7c85325bfcd383` and keeps the same presentation-only boundary.

- [x] remove text boxes from edge routes and encode relation class only through engineering line patterns plus arrows:
  solid cyan succession, dashed amber dependency and compound red conflict;
- [x] replace SVG path bounding-box focus with a focus treatment that follows the real route;
- [x] add viewport-anchored `Ctrl + wheel` zoom from 55% to 160%, while Reset returns to readable 100% and the canvas
  origin;
- [x] make every expanded upstream chain locally collapsible again in both the desktop graph and mobile ledger;
- [x] align connected components into stable left-to-right rows and reserve compact orthogonal routing only where a
  row change or longer span requires it;
- [x] keep the dependency lens facts-first: no explicit `depends_on` evidence means an explanatory zero-node empty
  state, not synthetic disconnected tasks;
- [x] move the inspector to a bounded in-canvas drawer and retain Escape, close-button and keyboard selection.

## W7.2.2 arrow and scrollbar visual integration

The maintainer's second real-page review found that SVG marker sizing was multiplying the conflict stroke width into
an oversized arrow and that native white scrollbars visually broke the dark analyst workspace. The correction is
registered as Git-private `W7.2.2-graph-arrow-scrollbar-visual-integration` from exact task base
`bff8ce6de1eed9b51e83a2e7cd92abc1297dddbe` and remains presentation-only.

- [x] render all relationship markers with fixed `userSpaceOnUse` 10×10 geometry instead of the SVG default
  stroke-width multiplier;
- [x] rebalance engineering routes to 3px default and 4px compound conflict lines without changing relation facts;
- [x] add shared low-contrast rounded scrollbar tokens for the document, sidebar, graph viewport and inspector;
- [x] give light mode its own root and descendant scrollbar palette, including the document-element scrollbar;
- [x] retain mobile ledger substitution, keyboard/ARIA semantics, read-only behavior and zero page-level horizontal
  overflow.
