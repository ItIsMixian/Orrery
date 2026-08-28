# W7C-B Production Workstream Relation Graph Observatory Validation

Date: 2026-08-28

Status: PASS — Windows Worktree Candidate; no hosted Promotion

## Scope and exact inputs

- Parent/task base: `codex/w7a-dynamic-workstream-succession-contract@52e88b8e15788eb7b17161e61885e9198d29407c`.
- Visual input: `codex/w7c-a-workstream-graph-visual-prototype@a39f6a701ef39e6bb3eb3b7ec05a9b5dc7416ef1`.
- Provider: `project-orrery-core.workstream-relations`, provider schema 1.
- Core contracts: `workstream-relation-graph` schema 1 and `workstream-succession-plan` schema 1.
- Observatory projection: `workstream-relation-graph-observatory` schema 1; read-only, zero-network and root-only/default-off.

Both refs resolved to the required exact SHAs before the first product write. A Git-private
`W7C-B-production-workstream-relation-graph` session was registered with W7A as parent/task base. W7C-A was
imported additively after the compact Implementation Plan; its experiment fixture remains explicitly
provisional/non-authoritative.

## Product acceptance

- Production projection calls the W7A Core relation storage loader, graph builder and succession-plan builder.
  Browser code receives only the versioned payload and never inspects Git, Session records, branch names, paths or
  similarity.
- Succession, Dependency and Conflict lenses share one Core fact set. Active tips, multi-predecessor relations,
  collapsed history, Unknown/stale/proposed, confirmed conflicts, compare/suppress reasons, filters and node/edge
  inspector are present. lifecycle, runtime, evidence freshness, Scope, subsystem, visibility and observability
  remain independent; waiting/paused/blocked/failed are not styled as active.
- Unsupported/invalid provider or schema, missing relation root, invalid graph, dangling node/evidence, legacy
  Unknown, unsafe source link and Core/provider failure produce one empty Unavailable projection. The page and
  accessible list remain reachable; no partial graph is generated and error text is scrubbed.
- Navigable evidence is limited to validated repository-document anchors derived from Core `source_links`.
  Git-private, fixture, opaque and commit evidence remains non-navigable. No URL or command executes and no private
  absolute path, credential, prompt/answer/transcript, source body or unpushed diff is projected.
- Desktop uses inline SVG plus inspector and a keyboard-accessible relation ledger. At 390px the SVG becomes a
  non-interactive overview and the ledger becomes the primary single-column timeline. focus-visible,
  non-colour labels/line styles, reduced-motion and zero horizontal overflow are retained.
- The surface contains no apply, undo, close, delete, merge or remote-execution action. Team remains request-only.

## Fast and Checkpoint evidence

Commands and results:

```text
python -X utf8 -m unittest tests.test_workstream_relation_graph_observatory tests.test_workstream_graph_visual_prototype -v
PASS 13/13

node --check experiments/workstream-graph-visual-prototype/prototype.js
PASS

python -X utf8 scripts/ci/test_inventory.py
PASS 370 unique test IDs, 26 shards, 50 Fast tests

python -X utf8 scripts/ci/run_test_shard.py --profile fast --output <temp>
PASS 50/50

python -X utf8 -m unittest tests.test_workstream_relations tests.test_workstream_graph_visual_prototype tests.test_workstream_relation_graph_observatory tests.test_personal_observatory tests.test_team_observatory -v
PASS 45/45 in 148.582s

python -X utf8 scripts/ci/validate_ci.py --all
PASS

python -X utf8 scripts/ci/validate_repository_gates.py
PASS before final documentation sync; rerun below binds the final author tree

python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
PASS integrated candidate

python -X utf8 scripts/docsite/build_docsite.py --out <temp>/index.html
PASS 14 ADRs, 6 States, 7 subsystems, 140 documents before final Validation/index sync
```

Focused tests use the corrected real W7A provider against the current repository and the W7A compatibility fixture.
They explicitly cover waiting/paused/blocked/failed mapping, real missing relation-store zero-write behavior, three
lenses, multi-predecessor/active tips/history, Unknown/stale/proposed/confirmed conflict, fail-closed provider cases,
unsafe links, no frontend Git/session semantics, no external network, no author-document write, Personal/Team
adjacency, component version and CI inventory.

## Real in-app Chromium acceptance

The root-only page was built with the W7A corrected compatibility fixture solely for browser acceptance:

```text
python -X utf8 scripts/docsite/build_workstream_relation_graph.py --enable --synthetic-browser-fixture
http://127.0.0.1:54454/docs/_site/workstream-relations.html#workstream-relation-graph
```

- 1280px: selected all three lenses; verified CI2-late/W5E active tips, two-item collapsed history and expansion,
  W5E multi-predecessor dependencies, proposed/stale/Unknown, L3/direct confirmed conflict, compare/suppress rows,
  subsystem/runtime filters, node and edge keyboard selection, independent blocked axes and the safe Validation
  anchor. `scrollWidth=1265 < 1280`; accepted run reported zero console warnings/errors.
- 390×844: controls become one column, host search is hidden, inline SVG is a 116px overview and the accessible
  ledger is primary. Enter selected W5E→CI1 dependency; Space/Enter selected CI2-late→W5E confirmed conflict and
  populated exact reason codes. `scrollWidth=375 < 390`; no runtime exception was observed.
- Screenshots:
  `C:/Users/1/.codex/visualizations/2026/08/28/01a04813-0d09-7151-9620-03d04d2e57d6/w7c-b-browser/w7c-b-desktop-1280.png`,
  `.../w7c-b-mobile-390.png`, `.../w7c-b-mobile-390-ledger.png`.

## Page entry and default-off proof

`python scripts/docsite/build_workstream_relation_graph.py --enable` builds the root-only sibling. Without
`--enable` or `ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW=1`, the legacy renderer is byte-preserved. The Team server
injects the sibling only when that same explicit graph flag is enabled. A real repository with no relation storage
root renders Unavailable/Unknown and performs no write. The graph builder is absent from Observatory managed tools,
the public docsite/Skill template/release manifest remain unchanged, and v0.2.0 is unchanged.

## Known gaps and integration boundary

- W7B Candidate 已实现本机 discovery／plan／human-local confirmation／apply／recovery／receipt／undo；其
  apply/undo 通过隔离 Git fixture 验证，self-host 真实 relation store 仍只有 dry-run。W7C-B 不接线这些能力，
  不提供 apply／undo／close／delete 图形按钮；默认 UI 执行入口和公开发布也都尚未发生。
- No full Promotion, hosted Windows/Ubuntu exact-SHA checks, push, main integration, branch-protection change, tag or
  Release was performed.
- W7C-A import and W7C-B completion both touch shared project/documentation/test State, DEVLOG, Validation index and
  Implementation index. These were merged additively on this branch; the unique integrator must reconcile concurrent
  W7B or other Candidate edits without treating this Worktree State as Canonical.
