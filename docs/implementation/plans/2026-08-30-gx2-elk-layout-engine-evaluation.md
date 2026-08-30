# GX2 ELK Layout Engine Evaluation

Status: Approved isolated evaluation; no product adoption

Date: 2026-08-30

Governing sources: [ADR-0017](../../decisions/0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0020](../../decisions/0020-workstream-program-and-phase-hierarchy.md),
[W7.3 Plan](2026-08-29-w7-3-workstream-relation-capture.md)

Primary subsystem: `multi-worktree-collaboration`

Affected: `documentation-system`, `release-and-toolchain`, `test-coverage`

## Goal

Evaluate whether a pinned local ELK.js layout engine can replace only W7.3's handwritten node placement, compound
grouping, orthogonal routing and edge-label placement while preserving the existing Orrery frontend design and
authority semantics. This is research-before-adoption: no result modifies the product renderer, public package,
release manifest or accepted relation facts.

## Frontend preservation contract

- [ ] Reuse Orrery's existing card dimensions, typography, colors, semantic borders, legend, Chinese vocabulary,
  zoom/pan behavior, selection, inspector and dark/light tokens. ELK must not render UI or choose visual styles.
- [ ] ELK receives only layout input and returns node/container coordinates, ports, edge sections/bend points and
  label coordinates. Orrery continues to own filtering, graph semantics, DOM/SVG, accessibility and interaction.
- [ ] The evaluation may add an internal comparison switch inside the isolated artifact, but no new product control,
  framework, generic node-editor chrome or visual redesign is allowed.
- [ ] Existing frontend remains recognizable in a blind side-by-side comparison; acceptable visual differences are
  spatial arrangement, route geometry and compound-container bounds only.

## Isolation and dependency provenance

- [ ] Work only under `experiments/workstream-graph-elk-evaluation/` in the existing W7.3 worktree. Preserve every
  existing dirty W7.3 product file and do not edit `packages/`, `scripts/`, `tests/`, component manifests or release
  assets during this evaluation.
- [ ] Pin an exact released ELK.js source/ref, record package version, upstream URL, SHA-256, file size and license.
  Use a local `elk.bundled.js` copy for the experiment; no CDN, external request, model API or telemetry.
- [ ] The vendored experimental asset and generated HTML are not a production dependency or release asset. A later
  Accepted ADR, license/package review and explicit maintainer approval are required before product adoption.
- [ ] Use a bounded sanitized snapshot derived from the current self-host projection. Exclude absolute paths, Prompt,
  transcript, source/diff, credentials and raw Git-private evidence bodies.

## Semantic preprocessing fixtures

The layout engine must not decide which facts are visible. Freeze four Orrery-owned inputs before calling ELK:

1. **Succession overview:** effective succession plus explicit display-series edges using the current readable card
   styles and no inferred chronology.
2. **W compound view:** W program with W5/W6/W7 compound children, disconnected members retained in their confirmed
   phase, and real CI/SH/U cross-hierarchy relations. Membership creates containment only, never an edge.
3. **Project Structure module view:** full cards match `primary_subsystem_id == project-structure` only. Explicit
   affected-task context and semantic-neighbor context are separate default-off layers; context is one hop, does not
   expand through series membership, and shows at most 12 full external cards before using a `+N` boundary summary.
4. **Dependency view:** visible full nodes are exactly endpoints of scoped `depends_on` facts/proposals. Program,
   phase, active-tip or series membership cannot admit an isolated node; a series connector may render only when both
   of its endpoints are already admitted by dependency facts.

Record exact full-card IDs, boundary IDs and edge IDs for every fixture before layout. ELK output cannot change these
sets.

## ELK layout trial

- [ ] Use ELK layered layout left-to-right with orthogonal routing, explicit node sizes, fixed/ordered ports where
  required, edge-label dimensions, separated connected components and compound hierarchy/cross-hierarchy support.
- [ ] Provide W/W5/W6/W7 as compound graph structure. Do not convert membership into invisible edges, flatten W into
  unrelated components or force all members into one manual rectangle.
- [ ] Feed relation labels to ELK as measured edge labels. If ELK does not return a valid label position, omit the
  canvas label and retain it in the inspector; never fall back to an arbitrary component corner.
- [ ] Render returned positions with Orrery-owned SVG elements. Do not post-process node coordinates or reroute edges
  with the rejected handwritten rank/packer/router.
- [ ] Capture layout execution time, output dimensions, node/container/label overlaps, route/node intersections,
  unmarked crossings, route stretch and external network requests.

## Artifacts and visual acceptance

- [ ] Produce one offline interactive HTML using existing Orrery visual tokens, the sanitized fixture JSON, a compact
  provenance manifest and a machine-readable geometry report.
- [ ] Capture 1440×900, 1280×800 and 390×844 screenshots for all four fixtures. Mobile may use Orrery's compact
  same-fact ledger if a full compound canvas is not readable; it must not scale desktop text into a thumbnail.
- [ ] Demonstrate edge/node selection and inspector opening without changing the layout footprint.
- [ ] Required visible outcomes: no floating labels; W members remain visibly grouped by program/phase; Project
  Structure context is not the all-node graph; dependency contains no isolated non-endpoint nodes; zero card/label/
  container overlap and no route through a node.
- [ ] Compare the ELK artifact with the rejected custom-renderer screenshot on the same semantic input. Do not compare
  different node/edge sets as if they were layout improvements.

## Cost and stopping rule

- Use only the experiment's semantic assertions, geometry report and Browser screenshots. Do not run routed Fast,
  Checkpoint, Promotion, release build or the full repository suite.
- Allow one initial configuration and at most one focused correction round. If the four visible defects remain, stop
  and reject ELK rather than beginning another open-ended tuning loop.
- Report asset size, local load/layout time, license/package implications and the expected production integration
  surface. Do not claim adoption, implementation or release readiness.

## Decision after evaluation

The maintainer chooses one of: reject; continue custom renderer; adopt ELK for layout/routing only; or request another
bounded architecture study. Production adoption requires a new ADR that defines the pinned dependency, local bundling,
single-source layout tests, fallback behavior, release/SBOM/license boundary and migration from the rejected custom
geometry path.

## 2026-08-30 maintainer adoption direction

[ADR-0022](../../decisions/0022-elkjs-workstream-graph-layout-engine.md) now selects ELK layout/routing-only adoption
while preserving the Orrery frontend. This supersedes the open decision menu above but does not waive GX2 evidence.
GX2 must pin and validate the exact release/ref/hash/size/license and four fixtures before W7.3 product dependency
writes. A failed capability or provenance gate blocks implementation and is reported as a conflict with ADR-0022;
the evaluator cannot silently choose a different engine or artifact.

[ADR-0023](../../decisions/0023-explicit-legacy-graph-layout-fallback.md) further requires preview-first cutover: GX2
must stop after presenting its offline page and evidence. The existing handwritten renderer remains untouched during
the experiment and is retained as a future explicit legacy recovery engine. No product integration may begin from the
GX2 task without a later maintainer acceptance and new exact task-description version.

## 2026-08-30 maintainer-supervised preview correction

The maintainer explicitly asked the coordinator to supervise GX2 until it produces a reasonably readable view, while
forbidding all test workflows before the maintainer confirms the view. The first artifact is not accepted: flat
succession/dependency are promising, but W compound auto-fits to 40%, Project Structure context auto-fits to 30% with
affected and semantic layers combined, the W layout retains one crossing/two stretched routes, and the correction
configuration crashes ELK 0.11.0.

### Render-only correction scope

- [ ] Allow up to two coordinator-reviewed preview iterations. Each iteration may edit only GX2 experiment HTML/CSS/JS,
  frozen fixture/provenance and screenshots. It cannot modify product files or select a new ELK artifact/version.
- [ ] Do not run `unittest`, `pytest`, focused test commands, geometry test scripts, Fast, Checkpoint, Promotion,
  release gates or any test workflow. Passive diagnostics calculated while the page renders may be displayed/read, but
  the iteration is driven by browser inspection rather than a test run.
- [ ] Default every desktop tab to 100%. `适合窗口` remains explicit; screenshots cannot auto-fit text to 80/40/30%.
  Scrollable canvas is preferable to unreadable scaling.
- [ ] W compound default full cards are W members inside W/W5/W6/W7 containers. CI/SH/U cross-hierarchy endpoints use
  compact typed boundary stubs by default and preserve exact relation identity; full external cards require an explicit
  context action. This must reduce long routes without deleting or inventing edges.
- [ ] W compound opens with inspector closed. Phase containers and cards are readable at 100%; no unmarked crossing,
  route-through-node, floating label or multi-screen route remains in the coordinator screenshot.
- [ ] Project Structure default remains primary-only. Produce a separate **semantic-context-only** screenshot with
  affected context off; the two checkboxes never activate one another. Affected context, when shown separately, stays
  bounded and uses a `+N` summary rather than forcing auto-fit.
- [ ] Dependency continues to contain only scoped `depends_on` endpoints, with no program/series/active-tip singleton.
  Succession and dependency must not regress while correcting W/context.
- [ ] Mobile continues using the readable same-fact ledger; no desktop canvas thumbnail.

### Supervision handoff

After each preview, report the local URL and fresh 1440×900, 1280×800 and 390×844 screenshots without claiming PASS.
The coordinator inspects them and either sends one focused correction or declares the view ready for the maintainer.
Do not notify the maintainer directly from W7.3 and do not begin product integration.

Continue the same task/worktree, preserve all existing dirty/product/legacy files and refresh Git-private scope to
revision 14 after reading this amendment plus the matching Validation section. Use GPT-5.6 Sol medium. The no-test and
experiment-only boundaries override earlier GX2 validation commands until the maintainer confirms the view.

## 2026-08-30 coordinator correction — W phase small multiples

Central browser inspection accepts the direction of succession, dependency, Project Structure primary-only and
semantic-context-only views, but rejects the remaining W compound geometry. One 1821×1383 nested compound still places
content far to the right, requires several scroll regions and retains a crossing/long routes. Further option tuning of
that single compound has already crashed ELK 0.11.0 and must stop.

### W view composition

- [ ] Replace the one giant nested W compound with one W program workspace containing three visible phase panels:
  W5, W6 and W7. These are presentation small multiples backed by the same accepted membership, not new facts or edges.
- [ ] Each phase panel runs ELK independently for its own W member full cards, real intra-phase edges and compact typed
  boundary stubs for every external CI/SH/U endpoint. An external relation terminates at the nearest panel boundary;
  inspector identity preserves its exact original endpoint/relation.
- [ ] A real direct cross-phase W relation, if present, uses an explicit top-level connector between phase ports. Do not
  route indirect chains through full external cards across all panels and do not duplicate a semantic edge.
- [ ] Arrange the three measured phase panels as readable desktop small multiples at 100% (for example W5/W6 compact
  and W7 wider according to content). Cards keep existing size; no global auto-fit, tiny compound thumbnail or
  multi-screen detour.
- [ ] W program/phase headers remain subtle containment labels. Inspector starts closed. No panel/card/label overlap,
  route crossing or route-through-card is acceptable in the coordinator screenshot.

### Flat affected context

- [ ] Project Structure affected-only has no semantic edges in the fixture, so use ELK box/rectangle packing for that
  flat layer instead of a 2190px single column. Keep the `+N` summary and 100% cards. This flat layout is independent
  from compound cross-hierarchy configuration and must not re-enable semantic context.

### Handoff

Preserve succession, dependency, primary-only, semantic-only and mobile behavior already inspected centrally. Generate
fresh 1440×900, 1280×800 and 390×844 screenshots for W and affected-only plus unchanged-reference screenshots for the
other views. Do not run any test command/workflow. Refresh Git-private scope to revision 15 after reading this section
and the matching Validation gate. This is one further render-only coordinator correction; product/legacy files remain
untouched.
