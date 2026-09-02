# Validation: W7.4 Workstream History and Relation Decision UX

Status: Preview Accepted; Candidate Frozen; Validation Pending

Date: 2026-09-01

Authority baseline: `4ca857257114d938548292572ca3b75165928c67`

Product base: U2.4 Worktree Candidate `00b2eb4fa28a606cdb532c7938e46482950e8233`

## Rejected baseline and first preview

- the Git-common-private retired archive contained 37 unique Workstream identities while the relation provider exposed
  only 8 Graph nodes;
- the first W7.4 preview incorrectly treated the strict session-closure subset as the complete history inventory and
  projected only CI4, R1, R2, R3, W5D and W6;
- “展开全部历史” could not reveal those six zero-relation closed tasks;
- Personal relation cards led with relation enum/revision/raw IDs and machine rationale instead of an understandable
  question and consequence.

The maintainer rejected that preview because a retired archive record remains bounded migration input even when its
old session snapshot did not finish lifecycle closeout. ADR-0026 requires those fields to remain Unknown, not the task
identity to disappear.

## Complete bounded input reconciliation

| Quantity | Count | Meaning |
|---|---:|---|
| dated-v1 archive records | 37 | every regular `worktree.json` under the bounded retired-session archive root |
| valid archive envelopes | 37 | contract-valid session plus branch-slug and exact retirement-HEAD binding |
| unique Workstream identities | 37 | no duplicate identity in the bounded input |
| present after first migration | 6 | strict closed subset only |
| newly appended by revised migration | 31 | retirement identity retained; ambiguous closure fields explicitly Unknown |
| currently projected history identities | 37 | index, Core graph candidate set and expanded presentation agree |
| excluded bounded records | 0 | no dated-v1 record is silently dropped |

The first preview's nine quarantine results were W3-review-integration-cleanup, PO-W4-PERSONAL-OBSERVATORY,
CI6-local-validation-router-tier-enforcement, PO1-decision-allocation-enforcement, SC1-canonical-state-closeout,
W7.2.3-workstream-graph-density-correction, V0.3.1-launcher-hotfix-release and
W7.1-archived-session-relation-projection for branch/session-HEAD drift, plus CI3-fast-validation-dependency-fix for
lineage/session-HEAD drift. The revised migration validates the immutable archive envelope's exact retirement HEAD;
it does not require the still-existing branch to remain frozen at an older session snapshot.

The first preview's remaining 22 skips were W1.3, CI2-tiered-test-performance,
W7A-dynamic-workstream-succession-contract, W7B-succession-apply-undo-legacy-inference,
W7C-A-workstream-graph-visual-prototype, W7C-B-production-workstream-relation-graph,
W7D-w7-integration-candidate, A3-authority-managed-consumer-contract, A4-portable-meta-rules-bootstrap-contract,
CI5-promotion-throughput-optimization, CI7-validation-routing-precision-total-cost,
GX1-fireworks-graph-skill-evaluation, REL3-v0-3-0-release-scope-default-matrix, S0-orrery-dispatch-skill,
U1-unified-observatory-architecture, U2.2-unified-navigation-workspace-maintenance-ux,
U2.3-unified-navigation-live-task-visibility, W5C-team-observatory-ux, W5E-team-observatory-ui-closeout,
W7.3-integration-acceptance, W7.3-workstream-relation-capture-confirmation and
WINDOWS-LAUNCHER-CONSOLE-FLASH-HOTFIX. Each has a valid retirement envelope but an old non-closed session snapshot;
the revised record uses `closure.reason: unknown`, an archive-day time fallback and explicit `unknown_fields`.

One `V0.3.0-final-rc` session exists only under `retired-worktree-session-extras` at 126,892 bytes. It is explicitly
not a dated-v1 bounded archive record because it exceeds the 65,536-byte per-record limit and lives outside the
authorized archive root. It is recorded here as an excluded non-input observation, not silently counted as absent or
migrated. Bringing it into a later bounded contract would require separate authority.

## Git-private history migration previews and receipts

- zero-write migration preview hash: `633e286dce6155bf729fa551ebcab1fcb63616cd6e2030cc6da9db49abcb7d0a`;
- first candidates: 6; first quarantine: 9; first non-closed skips: 22;
- the hash-bound local append wrote six compact `closed-workstream-summary` records and one separate migration receipt;
- receipt inspection hash: `cf86b1d7642590dcca3b0093c93469e6757bb2ea9763feac1ffd9a4738464202`;
- receipt reports `history_snapshot_ready: true`, `archives_changed: false`, `relations_changed: false`;
- no archive, branch, commit, relation history, confirmation or evidence record was deleted or rewritten.
- revised zero-write preview hash: `81ff532124b27d36fc9ec17b3e724c928334f7db9f48e83aac4340c886af4e76`;
- revised preview: 37 total, 37 valid, 37 unique, 6 already present, 31 candidates, 0 excluded;
- the hash-bound revised append wrote 31 new summaries and one separate receipt; receipt inspection hash:
  `c6c07443c94b5e55093abb91dfd737be1fb1e9649cad320434e90a0735e86583`;
- all 31 legacy records preserve ambiguous closure reason/exact time as Unknown; eight bind a newer exact retirement
  HEAD than the stale session snapshot and disclose that difference in `unknown_fields`.

## Preview-only implementation observations

- Core inspection reports history index `ready`, 37 records, Git-common-private append-only storage and no execution
  capability;
- Graph provider reports 43 nodes and exactly 37 history candidates;
- default mechanical presentation folds all 37 into seven accepted phase/series/other groups with counts
  23 + 3 + 4 + 2 + 2 + 2 + 1; expanding `history:all` exposes 37/37 identities;
- folded and expanded legacy/mechanical geometry postconditions both report zero violations; this did not exercise
  the browser-side ELK compound hierarchy and was insufficient to establish ELK render readiness;
- Core supplies deterministic Chinese presentation for seven current proposals. The CI7→CI6 dependency explains the
  integration-stage wait and both accept/reject outcomes; three Unknown `derived_from` proposals set
  `accept_allowed: false` and state that human acceptance is unavailable;
- raw proposal ID, revision, raw endpoints, enum gate, rationale and evidence remain under `技术详情`.

These are implementation-start and render-readiness observations, not automated test or maintainer acceptance
evidence.

## Real self-host preview

- separate loopback service: `http://127.0.0.1:43741/#workstream-relation-graph`;
- the first revised loopback render returned HTTP 200 and the exact 37-record history notice, but maintainer
  inspection rejected it because ELK raised `UnsupportedGraphException`: an outer component edge referenced a leaf
  port nested inside a series compound. HTTP 200 and legacy/mechanical geometry therefore did not prove a usable
  ELK Graph;
- the correction keeps a series compound only when no semantic edge crosses its boundary. A series touched by a
  cross-group edge is presentation-flattened into the component level, so the outer edge and both explicit ports are
  owned by the same ELK hierarchy. No semantic edge was removed and no automatic legacy fallback was enabled;
- a fresh in-app browser run against the restarted loopback service verified both default folding and
  “展开全部历史”: `data-wg-engine=elk`, `data-wg-layout-ready=true`, failure panel hidden and no browser console errors.
  The expanded DOM contains exactly 37 history task cards while preserving the CI7 dependency and Unknown lineage
  decision explanations;
- maintainer inspection rejected that run because the 37 identities visually dominated the canvas while historical
  series relations were absent. The root cause was an old presentation rule that discarded every explicit series
  adjacency when either endpoint became a history candidate; W7.4 made 37 nodes historical and therefore activated
  that blanket suppression;
- the correction restores the four explicit metadata series routes A3→A4, CI6→CI7, U1→U2 and U2→U2.2. These remain
  presentation-only and do not become semantic succession, dependency or gate facts. The page now states the actual
  evidence boundary: 8 of 37 historical identities have a registered semantic relation or explicit series order;
  the other 29 are labelled “仅找回身份／关系未登记” rather than being presented as relationship recovery;
- fresh browser evidence after expansion reports 8 visible succession routes: four aggregated semantic succession
  routes plus four explicit series routes. The dependency lens reports five visible routes: three dependency
  proposals plus the two applicable series routes. Both lenses remain `data-wg-engine=elk`,
  `data-wg-layout-ready=true`, with zero console errors;
- default folding now retains every history identity touched by a visible relation or series route and folds only the
  29 identity-only records. The default succession canvas therefore already shows the same eight routes instead of
  hiding relation-backed tasks inside broad history clusters; expansion yields 37 cards, 29 explicit identity-only
  labels and the same eight evidence-backed/presentation-series routes;
- maintainer inspection rejected that expansion because 29 identity-only records still turned the relation canvas
  into a global task-list scatter. The `history:all` canvas expansion path has therefore been removed. “打开完整历史目录”
  now opens a separate seven-group directory covering all 37 identities; program／phase／series metadata only names
  directory groups and does not create a semantic relation;
- the default browser canvas now contains 16 nodes, including four compact identity-only directory entrances, and
  exactly eight routes. Opening the full directory exposes 37 items (8 relation-backed, 29 identity-only) without
  changing the 16-node／8-edge canvas. Clicking the “其他历史任务” graph entrance opens only that directory group;
  opening an identity-only task detail also leaves the canvas unchanged;
- the final preview was reloaded into the default collapsed state. It reports `data-wg-layout-ready=true`, the ELK
  status `ELK 0.11.0 · 1819×600`, failure panel hidden, directory closed and inspector closed;
- the service was started with `--no-browser --console`; no Computer Use or external network was used.

## Archived-lineage recovery correction

The maintainer rejected the separate complete-history directory because it recovered identities but still hid the
archived relationships that made those tasks meaningful. The correction removes the directory, bulk controls,
identity-only cards and phase／series／other directory entrances. All 37 records remain retained internally; only
tasks connected by semantic relation evidence or explicit accepted series metadata enter the browser projection.

| Archived lineage observation | Count | Result |
|---|---:|---|
| bounded records / unique identities | 37 / 37 | retained internally; no archive write or rewrite |
| `lineage.status=current` | 14 | exact endpoint, OID, Git ancestry and cycle checks attempted |
| recovered read-only `derived_from` edges | 11 | admitted to the relation graph |
| current lineage rejected | 3 | target archive missing or ambiguous; no edge generated |
| `legacy-unknown` / `parent-unverified-unknown` / absent | 13 / 6 / 4 | kept internally and edge-free |

Source retirement drift and target advancement after `task_base_oid` are exposed as stale/currentness diagnostics,
not treated as proof that lineage never existed. Each recovered edge binds safe hash-only archive evidence; archive
paths are not exposed. Candidate cycle detection found no cycle among the eleven admitted edges.

The restarted loopback preview reports `data-wg-engine=elk`, `data-wg-layout-ready=true`, status
`ELK 0.11.0 · 1954×1116`, a bound input hash, and a hidden failure panel. The DOM contains 23 rendered task cards and
15 rendered succession/series routes, with zero history-directory, history-item, bulk-expand or bulk-collapse
elements. All seven pending capture proposals remain in Git-private inspection; none was accepted, removed or
rewritten. Only syntax/import checks, read-only Core/provider inspection and live browser preview were used.

## Same-canvas compact-history preview

Scope revision 5 at task-description `590717889745ddd975b26b021f61dffcaf95c5d6` accepts the full relation graph
above as the frozen default and authorizes one alternate same-canvas presentation. Git-private scope refresh recorded
revision 5 against integration `4e56e3eb4fbb5596e5dcc2bddb48884d2056c041`, no active findings, L2 locally
confirmed and `local_work_allowed: true` before the new product write.

- the page opens in `显示完整关系`; the accepted 23-node／15-route baseline is preserved as an exact subset. Current
  Git-private U2.4/U2.5 inputs add two nodes and three routes, so the live canvas renders 25 nodes／18 routes without
  changing or removing any accepted endpoint pair; ELK is ready and the failure panel is hidden;
- `折叠历史` protects non-historical tasks, every pending/Unknown/dependency/conflict endpoint, selected context and
  one-hop historical context;
- only remaining deep read-only historical nodes enter maximal connected-subgraph summaries; with the additive
  U2.4/U2.5 inputs the initial compact projection contains 15 nodes, three summary nodes and eight externally rendered
  routes; fully historical components therefore remain represented instead of disappearing;
- one summary expands in place from 15 nodes／8 routes to 23 nodes／16 routes while the other two summaries remain
  folded; the expanded group exposes a `重新折叠` control;
- mode and local-fold changes keep the accepted SVG visible while the offscreen ELK result is computed, then replace
  it atomically; zoom stays unchanged and a proportional viewport anchor is restored where scrolling exists;
- no directory, secondary panel, card list, identity-only record or relation-state mutation was introduced.

This is preview evidence only. No unittest, Fast, Checkpoint, Candidate, Promotion or diff gate has run.

## Pending maintainer acceptance

- confirm the accepted full-relation canvas still opens by default and remains readable;
- inspect `折叠历史` and confirm every deep historical connected component remains represented by an in-canvas summary
  carrying task, relation-type and entry／exit counts;
- expand one summary in place, confirm its underlying relations return without a directory or secondary panel, and use
  `重新折叠` to restore the compact projection;
- confirm current, pending／Unknown and dependency／conflict context remains protected from compact folding.

## Strict history classification correction

The revision-4 central schema is now the only accepted active history-record shape. A fresh zero-write archive scan
recomputed, rather than hard-coded, these counts:

| Strict history classification | Count |
|---|---:|
| bounded / valid / unique archive records | 37 / 37 / 37 |
| `closed-workstream` | 6 |
| `retired-session` | 31 |
| retired lifecycle: implementing / validating / review-ready | 12 / 18 / 1 |
| excluded records | 0 |

The rejected draft's 37 `closed-workstream-summary` files remain byte-for-byte preserved under the old namespace;
their aggregate SHA-256 is `9ee7925d45440e8af294734802066bbd70b20cc1733c493682cca132ef1bd454` before and after repair.
The hash-bound strict preview `6ec42b950658856d0feac66dd52472ab37d0990c2651952d9e5583fea39dc7ce`
appended 37 strict records in a separate namespace and emitted an auditable rollback receipt. The receipt reports
`archives_changed: false`, `relations_changed: false`, `legacy_draft_changed: false` and
`history_snapshot_ready: true`.

Read-only Core inspection after the repair still reports 11 recovered archived-lineage edges and the same rejection
classes: 13 legacy Unknown, 6 parent-unverified Unknown, and 3 current records whose target archive is missing or
ambiguous. The real browser preview proves all accepted 23 nodes and 15 routes remain present in the current additive
25-node／18-route full graph. It also proves compact 15／8／3, one-group expanded 23／16／2, and a final return to the
full default with ELK ready and the failure panel hidden.

No unittest suite, Fast, Checkpoint, Candidate, Promotion, push, main, tag, release or publication action has run for
W7.4. Focused tests and `git diff --check` remain blocked until the maintainer accepts this preview.

## Full-mode compound packing overlap correction

Central browser inspection found one real final-SVG overlap in the otherwise complete 25-node full graph:
`CI7-validation-routing-precision-total-cost` at `(715,260,224,96)` intersected
`U1-U2-integration-baseline` at `(664,245,224,96)` by `173×81` pixels. Compact mode had zero overlap, isolating the
defect to full-mode compound composition rather than relation facts or history folding.

The full layout previously nested eligible series inside separately laid-out connected-component compounds and then
used top-level ELK rectpacking. The packed component envelope did not contain the final nested-series leaf extent, so
an independent component could be placed inside that leaked extent. The correction keeps the same ELK-produced
component/series geometry but uses the ELK box algorithm for the top-level compound boundary composition. There is no
node-ID condition, coordinate nudge, node omission or relation suppression.

A render-level postcondition now reads every final visible `.wg-node > rect` in SVG coordinates and computes all
pairwise positive-area intersections. Any nonzero result throws before `data-wg-layout-ready=true`; the failure panel
shows the affected pair instead of presenting an overlapping canvas as ELK ready.

Real restarted loopback evidence at `http://127.0.0.1:43741/#workstream-relation-graph`:

| Mode | Nodes | Routes | Fold summaries | Final SVG overlap pairs | Result |
|---|---:|---:|---:|---:|---|
| full default | 25 | 18 | 0 | 0 | ELK `1954×1292`, ready, failure hidden |
| compact | 15 | 8 | 3 | 0 | ELK `1488×836`, ready, failure hidden |

An independent browser-side rectangle scan agrees with the in-product postcondition in both modes. In the corrected
full geometry CI7 is `(1004,228,224,96)` and U1 integration baseline is `(32,637,224,96)`. The browser was returned to
the full default. Only Python syntax/import, read-only DOM geometry and browser preview were used; no automated
validation or release gate was started.

## Lifecycle and organizational-classification separation

The strict lifecycle correction does not imply complete organizational classification. The real provider inventory
is retained without inference:

| Inventory | Total | Missing task series | Missing program/phase | Missing both |
|---|---:|---:|---:|---:|
| Core Graph provider | 42 | 33 | 35 | 27 |
| strict history records | 37 | 29 | 30 | — |
| current full browser projection | 25 | 17 | 21 | 14 |

The provider exports this diagnostic as explicit-metadata-only with both name inference and lineage inference false.
The mast states that lifecycle and organizational classification are independent; cards missing both accepted axes
show `组织分类未登记`, and the node inspector shows `未登记` independently for program, phase, series and task code.
The engine diagnostic exposes the current full-visible counts even while compact mode is selected.

No program membership or task-series event was written. `derived_from` remains a relation only and is not used as a
series or synthetic group. Under the same sparse classification input, full remains 25 nodes／18 routes／0 overlaps and
compact remains 15 nodes／8 routes／3 summaries／0 overlaps; the browser was returned to full default.

## Candidate freeze — validation pending

The maintainer accepted the corrected full/compact preview on 2026-09-01. Task-description
`c08a9b23bc63fdfae3e621d74598efe3ab0c1542` revision 6 adopts ADR-0030 and freezes the accepted W7.4 tree without
running another test, browser, provider, build or routed validation command. The accepted product bytes were not
changed during freeze; only required root/project-template exact-copy parity and this Pending Validation state were
completed.

Completed post-acceptance commands with final exit codes are retained as prior evidence: Core relation/capture/program
owners 36/36, Graph Observatory 11/11 and Unified Observatory 16/16 exited zero. A component-boundary follow-up did
not complete successfully because this worktree lacks root `start-orrery.bat`; it was not repaired or rerun under the
freeze amendment. These receipts do not change the Candidate status to validated.

The frozen Candidate remains `validation-pending`: no Fast, Checkpoint, Candidate validation, Promotion, integration,
push, release, closure or cleanup claim is made. Exact-SHA asynchronous validation must consume the freeze result and
record PASS or FAIL separately.
