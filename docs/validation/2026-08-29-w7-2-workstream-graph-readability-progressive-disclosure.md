# W7.2 Workstream Graph Readability & Progressive Disclosure Validation

Date: 2026-08-29

Status: PASS — implementation, real-browser acceptance and CI6 Fast/Checkpoint complete

## Scope and baseline

- Workstream: `W7.2-workstream-graph-readability-progressive-disclosure`.
- Exact continuation base: `codex/u1-u2-integration-baseline@ad9f0946a191b8810d99f70171318a4d5536c425`.
- The existing U2.1 branch was first confirmed clean at `02efa41a95e71b54f4ad0f7ef2c3071055bdb096`,
  then advanced only by `git merge --ff-only` to the exact continuation base. W7.2 was registered in Git-private
  state before the first W7.2 author write.
- A scope refresh bound the final expected-write set and dirty fingerprint. Because the U2.1 parent session no
  longer mechanically validated the refreshed private state, lineage honestly became `parent-unverified-unknown`;
  the exact Git ancestry/base above remains independently verified and no sibling session was rewritten.
- Authority: [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md),
  [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md) and the Approved
  [Unified Observatory Design](../design/unified-observatory-architecture-and-shell.md).
- Presentation-only boundary: Core 0.1.17 relation schema/facts and CLI 0.1.21 are byte-unchanged by this task;
  Observatory advances from 0.1.12 to unreleased 0.1.13.

## Layout and disclosure evidence

The Observatory maps recorded predecessor/dependency targets to the left and successor/dependent sources to the
right without changing Core fields. A deterministic longest-path ranker creates one stable horizontal direction,
Chinese rank lanes, 248×104px cards and 112px inter-rank routing space. Orthogonal routes own distinct label tracks;
the real graph has no visible-node overlap, label overlap, card text escape or route crossing through a non-endpoint
card. Cards keep a human prefix/name primary and place the bounded machine ID in secondary text, tooltip and the
technical inspector.

Succession, dependency and conflict are separate facts-first lenses. Succession may add active/current tips and
chain context. Dependency and conflict use only their real edge endpoints plus the hierarchy required to understand
those connected components. The real self-host has no explicit `depends_on` edge, so dependency renders zero nodes,
zero edges and `当前没有已登记的依赖关系`; a one-edge fixture renders exactly two endpoints, one orthogonal route,
one label and one arrow. Conflict visible IDs equal the union of the real conflict-pair endpoints and contain no
foreign edge class.

Default succession shows tips, direct predecessors and required siblings. Each chain's older ancestors become that
chain's own `更早历史 N 项` cluster. Expanding the real W5E chain replaces only its cluster with W5D; global
expand/collapse remain auxiliary and Reset restores the default collapsed set, succession lens, closed inspector and
100% zoom. The inspector is a closeable overlay, hidden by default; node and edge selection work with pointer or
Enter/Space. Desktop gives the graph all available content width and keeps the semantic ledger clipped to 1×1px
rather than producing a second visible page. At 390px the SVG tools are hidden and the same fact/expansion model is
rendered as an ordinary `任务关系列表` with human-readable `从谁 → 到谁` rows.

## Mechanical and focused regressions

The existing owner test IDs now cover:

- minimum card dimensions, visible-node bounding-box separation and contained text;
- orthogonal edge routes that do not enter non-endpoint cards, arrow markers and opaque labels;
- per-chain default cluster counts, single-chain expand/collapse, global expansion and Reset;
- empty dependency = zero isolated nodes, and one dependency = two endpoints plus one arrow;
- lens edge-type isolation and conflict endpoint equality;
- inspector hidden/closeable, keyboard/ARIA/focus/reduced-motion, and no network or execution API;
- desktop ledger visually clipped while its semantic DOM remains present; mobile ledger visible with the same
  current-lens fact IDs.

Focused command:

```text
python -X utf8 -m pytest -q tests/test_workstream_relation_graph_observatory.py tests/test_unified_observatory.py
PASS — 18/18

python -X utf8 -c "...WORKSTREAM_GRAPH_JS..." | node --check -
PASS
```

Formal CI6 evidence from the synchronized authored diff:

```text
python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run --explain
PASS — 38 mapped tests, no unknown path; dry-run is not evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425
PASS — 38/38, 2.504047s, evidence-eligible and inside the 15-second budget

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run --explain
PASS — 44 mapped tests, no unknown path; dry-run is not evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425
PASS — 44/44, 72.874628s, evidence-eligible and inside the 90-second budget
```

## Real self-host browser acceptance

The supervised root-only service was exercised in the in-app Chromium against the repository's real Git-private
projection, not a synthetic small graph. The first run contained 16 nodes/6 succession edges; a separately authorized
parallel Workstream appeared later through the same startup projection, and the final screenshot run contained 7
succession edges. W7.2 neither read nor wrote that parallel task. The changing count demonstrates facts-first
projection rather than a baked screenshot fixture.

At 1280×800 and 1440×900 the relation page uses the former blank table-of-contents slot, leaves the inspector closed,
keeps 100% readable cards, and allows internal horizontal/vertical scrolling instead of shrinking the graph. Default,
one-chain expanded, node inspector, edge inspector, dependency empty, conflict, zoom, fit and Reset were exercised.
At 390×844 the SVG graph is not visually rendered; the ranked ledger uses the same current-lens fact ID set and the
same W5D chain expansion, while node/edge drawers remain inside the viewport. All three viewport runs have no
document-level horizontal overflow and browser console warnings/errors are empty.

The frontend acceptance review covered hierarchy/read direction, typography/card proportion, edge contrast and
labels, component-state distinction beyond color, responsive substitution, focus/ARIA/reduced-motion, overflow and
drawer behavior. Local screenshots outside Git:

- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/w7-2/1280-default.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/w7-2/1280-one-chain-expanded.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/w7-2/1280-node-inspector.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/w7-2/1440-default.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/w7-2/390-ledger-ranks.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/w7-2/390-dependency-empty.png`

No Provider key, external network, real Team join, relation apply/undo, worktree deletion, merge or remote execution
was used. The service is explicitly stopped after final evidence and its listener/ready marker/helper are checked.

## Remaining boundary and integration order

- W7.1 archived evidence remains read-only and has no execution authority. W7.2 does not create relation roots,
  infer Unknown, edit facts, apply/undo/merge/delete or add remote execution.
- Static output still has no dynamic control. Team remains opt-in/request-only, Personal remains zero-network,
  Quick Remove remains local-confirmed, Authority/AI do not upgrade and `start-docsite.bat` remains rollback.
- Full Promotion, a non-main push, hosted Windows/Ubuntu required checks, main integration, default/public transition,
  release and root PROGRESS/HANDOFF synchronization remain the unique integrator's later work.
