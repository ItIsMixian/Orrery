# GX2 ELK Layout Engine Evaluation Validation

Date: 2026-08-30

Status: PASS — isolated ELK visual direction accepted for product wiring; product implementation/validation separate

Authority source: [GX2 Plan](../implementation/plans/2026-08-30-gx2-elk-layout-engine-evaluation.md)

Adoption decision: [ADR-0022](../decisions/0022-elkjs-workstream-graph-layout-engine.md)

## Required evidence

- exact task-description SHA and Git-private scope revision 11 acknowledgment;
- zero diff outside `experiments/workstream-graph-elk-evaluation/`;
- pinned ELK.js version/ref/upstream/hash/size/license and local-only loading evidence;
- sanitized self-host-derived fixture with no private path, Prompt/transcript, source/diff, credential or raw private
  evidence body;
- exact pre-layout full-card/boundary/edge ID sets for succession, W compound, Project Structure and dependency views;
- proof that ELK output changes coordinates/routes only and cannot change the Orrery-owned input fact sets;
- existing Orrery card CSS/tokens/typography/semantic styles and interaction preserved in the isolated SVG renderer;
- W/W5/W6/W7 compound structure with real cross-hierarchy edges and no membership-as-edge;
- Project Structure full cards are primary-only; affected and one-hop semantic context are separate, default-off and
  bounded, with no series-driven expansion to all nodes;
- dependency full nodes equal scoped `depends_on` endpoints and contain no program/series/active-tip singleton;
- ELK-returned edge-label coordinates or inspector-only fallback, with zero floating corner labels;
- machine-readable geometry report for overlaps, route/node intersections, crossings, stretch, bounds and timing;
- 1440×900, 1280×800 and 390×844 screenshots for all four fixtures, plus selection/inspector evidence;
- one initial layout plus at most one correction round; no routed Fast/Checkpoint/Promotion/release suite;
- concise reject/adopt-layout-only/further-study recommendation with dependency, license, bundle-size and integration
  tradeoffs.

No experiment artifact, dependency or result enters product source, State, release package or public/default behavior.
Only later maintainer acceptance plus a new ADR can authorize production adoption.

ADR-0023 now preserves the handwritten renderer as a future explicit legacy recovery engine and keeps product writes
blocked until the maintainer sees this GX2 page. This evaluation must stop at the preview/evidence handoff; it cannot
perform product integration under the GX2 scope.

## 2026-08-30 supervised preview acceptance gate

Before the coordinator may notify the maintainer, browser inspection—not a test workflow—must show:

- every desktop tab starts at 100%; no screenshot is auto-fit to 80/40/30%;
- W/W5/W6/W7 compound cards remain readable, inspector starts closed and external CI/SH/U endpoints are compact typed
  boundary stubs unless explicit context is requested;
- W compound has no visible crossing, floating label, edge-through-card or multi-screen detour;
- Project Structure primary-only, semantic-context-only and affected-only states are distinct; toggles are independent,
  bounded and never reproduce the all-node graph;
- dependency contains only `depends_on` endpoints and no isolated membership node;
- succession and dependency retain readable labels/routes;
- 390px uses the same-fact ledger rather than a scaled desktop graph;
- fresh 1440×900, 1280×800 and 390×844 screenshots plus local URL are returned to the coordinator;
- zero test commands/workflows and zero product/vendor/package/default writes occurred;
- exact task-description acknowledgment and Git-private scope revision 14 precede corrections.

This is a visual readiness gate only. It does not mark GX2, W7.3 or any product/release validation PASS.

## 2026-08-30 W phase small-multiple readiness gate

Central Browser review additionally requires:

- W view presents W5/W6/W7 as three readable phase panels inside one W workspace at 100%; no giant nested compound or
  automatic fit;
- each panel contains only its W full cards plus typed boundary stubs, uses ELK for its local layout and preserves exact
  relation/endpoint inspector identity;
- indirect external chains do not become page-spanning routes; only real direct cross-phase W edges may connect panels;
- no visible panel/card/label overlap, route crossing, route-through-card or multi-screen detour;
- inspector starts closed and phase/card typography matches the accepted Orrery trial styling;
- Project Structure affected-only uses bounded flat packing with `+N`, while semantic context remains off and unchanged;
- succession, dependency, primary-only, semantic-only and mobile views do not regress;
- no test command/workflow or product/vendor/package/default write occurs;
- exact task-description acknowledgment and Git-private scope revision 15 precede the correction.

The coordinator, not W7.3, decides whether the resulting view is ready to show the maintainer.

## Accepted isolated result

- Maintainer response: “感觉好像还不错，接线看看”.
- Accepted direction: existing Orrery visual tokens and interactions, ELK 0.11.0 geometry, W5/W6/W7 phase small
  multiples, typed external boundary stubs, primary-only module view, independent affected/semantic context,
  dependency endpoints only and mobile same-fact ledger.
- Exact provenance remains `elkjs@0.11.0`, bundle SHA-256
  `cbf61b0182e9085d36dcd5b392f57cc816273169ac40bde80b52b808444c5cf8`, EPL-2.0.
- Central browser inspection covered succession, W, Project Structure primary/semantic/affected, dependency and mobile;
  revision-15 passive diagnostics report zero W crossings, route-through-card and label/card overlap.
- No test command/workflow and no product/vendor/package/default write occurred during the accepted experiment.

This PASS approves product wiring only. It is not W7.3 product acceptance, Fast/Checkpoint evidence, Canonical
integration, default switch or release readiness.
