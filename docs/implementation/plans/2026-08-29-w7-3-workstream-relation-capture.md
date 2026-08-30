# 实施计划：W7.3 Workstream Relation Capture & Confirmation

Status: Reopened for maintainer-required Graph UX correction; prior Candidate not accepted visually

Date: 2026-08-29

Governing ADR: [ADR-0017](../../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)

Approved Design: [Workstream relation capture and confirmation](../../design/workstream-relation-capture-and-confirmation.md)

Dispatch governance: [ADR-0018](../../decisions/0018-authority-first-workstream-dispatch.md)

## Goal

让 Workstream 在创建、后续衍生和集成时形成真实可审计的 relation DAG，而不是要求维护者事后手写关系或
让 Graph 从相似性猜测。W7.3 不实现可选 Conductor Skill，不新增远程执行，不允许 Agent 确认语义关系。

## Phase 0 — versioned contracts and fixtures

- [ ] 冻结 proposal/event/confirmation/role fixture 与 JSON schema；v1 relation 继续可读。
- [ ] 为 `depends_on.required_for` 冻结 implementation／validation／integration／release 四种 gate 及 legacy
  unknown 行为。
- [ ] 冻结 proposer/evidence/confirmer/role/revision/hash 字段和 path/size/count/symlink 安全门。
- [ ] 建立单人 owner、Team owner、多 integrator conflict、无 integrator、Agent spoof、legacy v1、cycle、
  late-CI fan-in 等正负组合。

## Phase 1 — automatic mechanical lineage

- [ ] Workstream registration/rebind 自动尝试 `derived_from`，仅接受 same-project exact OID 和本地 ancestry。
- [ ] 重复输入幂等；drift/non-ancestor/self/cycle/Unknown 失败关闭并返回 required metadata。
- [ ] append-only event 写入 Git-common-private store；作者树、package、Team sync 和外网零写入。
- [ ] Codex/Claude/DeepSeek/Harness Adapter 只提供 caller/platform provenance，不拥有确认权。

## Phase 2 — `depends_on` proposal and gate confirmation

- [ ] Core/CLI 支持 suggest/inspect/accept/change-gate/defer/reject；Agent 只能 suggest。
- [ ] implementation/validation 只接受 source task owner 的本机人类确认。
- [ ] integration/release 只接受人类 integrator 确认；central Team request 不能直接生效。
- [ ] gate-aware lifecycle eligibility 只消费 effective current relation，Unknown/proposed 不阻塞。
- [ ] Harness 从明确 Prompt/Plan/artifact/gate evidence 生成候选，不把 path overlap 自动升级为 dependency。

## Phase 3 — integrator and `absorbs`

- [ ] Personal project owner 成为默认 sole integrator；Agent/session 身份拒绝。
- [ ] Team owner 可显式 grant/revoke human integrator；无 integrator 时失败关闭。
- [ ] `absorbs` proposal 显示 target closure/Validation/scope，只有 integrator confirmation 产生 effective event。
- [ ] 多 integrator 使用 revision/CAS；冲突决定保持 pending，不 last-writer-win。

## Phase 4 — Observatory inbox and graph projection

- [ ] Personal/Team 增加“关系待确认”，显示原因、gate、证据与本机权限；中央仍 request-only。
- [ ] Graph 显示 effective/proposed 与 required_for，但不增加 confirm/apply/undo 按钮。
- [ ] 任务创建不经过 Orrery UI 时，Skill/CLI 在首次产品写入前完成注册；未登记任务显示 finding 而不伪造关系。
- [ ] 真实 self-host 以新 Integration Workstream 演示 fan-out/fan-in，不能回写旧历史意图。

## Validation and rollout

- Core/CLI schema、cycle、role spoof、CAS、legacy、privacy、zero-network 和 package exclusion tests；
- Codex/Harness JSON caller-provided registration evidence；Claude/DeepSeek 不继承其他平台结论；
- Personal/Team/Graph desktop/390px 浏览器验收；
- CI6 Fast/Checkpoint/Candidate 与 exact non-main SHA Windows/Ubuntu Promotion；
- main/public/release/default switch 另行授权。

实现后同步 Project Structure／Documentation System／Test Coverage State、独立 Validation、DEVLOG 和索引；
根 PROGRESS/HANDOFF 由唯一整合者维护。任何自动确认语义 dependency、多人投票或远程 confirmation 都不在
W7.3 范围。

## 2026-08-30 Maintainer Scope Amendment — Task Series, Status Taxonomy, Comparison vs Conflict

This amendment was authored centrally before W7.3 resumes the added implementation scope. It does not change
ADR-0017's human authority, relation types, DAG or privacy boundary. Series is display metadata; a semantic
predecessor creates only a proposal under the existing confirmation rules. Core comparison suggestions remain
derived/read-only and are no longer presented as confirmed conflicts.

### Task series and predecessor proposals

- [ ] Add versioned explicit `series_id`, `task_code`, `series_order` and optional
  `series_predecessor_workstream_id` (or versioned equivalent); never
  infer facts from `A3/A4`, `CI6/CI7` name prefixes.
- [ ] Keep series grouping visually distinct from `derived_from`／`depends_on`／`absorbs` edges.
- [ ] Explicit predecessor registration creates a proposal with suggested gate/evidence, never an effective edge.
- [ ] Produce read-only self-host repair proposals for A3→A4 and CI6→CI7; maintainer confirmation selects the exact
  relation/gate before any effective event.

### User-facing status taxonomy

- [ ] Replace the generic “待确认” collapse with deterministic Chinese states for active, human-confirmation pending,
  evidence/scope stale, historical, session missing/relation-only, unregistered and genuinely Unknown.
- [ ] Keep raw lifecycle/runtime/evidence/scope axes in technical details; only actual human decision pending uses
  “等待人工确认”.

### Comparison versus conflict

- [ ] Preserve conservative Core `compare_pairs` semantics but project them as amber comparison/review suggestions,
  not red conflicts.
- [ ] Conflict lens contains only evidence-backed conflict facts (path/module/exclusive-resource/contract or explicit
  human finding), with location, impact and source.
- [ ] No confirmed conflicts produces “当前没有已确认的任务冲突”.
- [ ] Translate stale/unconfirmed/independent/post-fork reason codes into ordinary Chinese in a separate comparison
  queue; they must not create red Graph edges.
- [ ] Version any changed projection/schema contract without rewriting v1 history.

### Acceptance

- [ ] Real self-host shows A and CI series while unconfirmed predecessor links remain proposals.
- [ ] Current compare suggestions and confirmed conflicts are completely separated.
- [ ] 1440px/390px Graph and ledger preserve facts, keyboard/ARIA, zero overflow and read-only canvas.
- [ ] Graph never confirms relations; local relation inbox remains the only confirmation UI.

Expected affected surfaces include relation capture Core/schema, registration/CLI/Harness, relation inbox,
presentation projection and their focused tests. If implementation requires a new relation kind or changes
confirmation authority, W7.3 must stop for a new ADR rather than expanding this Plan.

## 2026-08-30 Maintainer Scope Amendment — Graph-native Relations, No Detached Substitutes

The prior W7.3 Candidate is rejected for Graph UX acceptance. It placed explicit task series in a detached card strip
and comparison suggestions in a large card ledger below the canvas. Those surfaces describe relationships outside the
graph while leaving the actual topology visually disconnected. Passing contract tests does not satisfy the requested
product behavior.

### Design brief

- **Purpose:** let a maintainer understand task lineage, explicit series progression, dependencies and confirmed
  conflicts from the topology itself.
- **Tone:** dense engineering/analyst workspace; graph-first, calm and legible.
- **Memorable interaction:** every visible relationship is a selectable connector inside the canvas, with its type and
  confidence readable from route style and inspector evidence.
- **Constraint:** existing read-only authority, Chinese UI, current Orrery visual tokens, keyboard/ARIA and mobile
  same-fact behavior remain. No ImageGen or decorative redesign.

### Graph-native series and relationship presentation

- [ ] Remove the standalone “任务系列” card strip. Explicit `series_id`／`series_order` metadata must create an actual
  graph-native series lane/group and ordered connector between adjacent tasks.
- [ ] A3→A4, CI6→CI7 and U1→U2→U2.2 must be visibly connected in the canvas without requiring the user to read a
  separate list. The connector is labelled/inspectable as “同系列演进（展示关系）”.
- [ ] A series connector is presentation-only: it cannot satisfy `derived_from`, confirm `depends_on`, block a gate,
  close a task or create an effective relation event. Its style must be distinct from succession, dependency and
  conflict edges.
- [ ] In the dependency lens, explicit predecessor proposals remain amber dashed directional edges with
  “等待人工确认”; A3→A4 and CI6→CI7 must appear in the same canvas. In other lenses, a subdued series connector keeps
  the structural relationship visible without changing semantic edge counts.
- [ ] Series lane headers may appear inside the canvas margin/swimlane, but no detached top card grid may substitute
  for nodes and connectors.

### Comparison and conflict information architecture

- [ ] Remove the always-expanded “需要比较／证据待刷新” card grid below the graph. Comparison suggestions become a
  compact default-collapsed inspector/drawer or an explicit default-off graph overlay.
- [ ] If comparison overlay is enabled, suggestions use thin neutral/amber dotted connectors, never red, and each
  connector selects a bounded evidence explanation. They remain non-authoritative and non-blocking.
- [ ] Conflict lens draws only confirmed conflict facts. Zero confirmed conflicts displays a clear empty canvas state
  and zero red relationship paths; comparison suggestions remain collapsed outside the conflict topology.
- [ ] With multiple confirmed conflicts, unrelated edges cannot share long coincident horizontal/vertical spines.
  Assign deterministic per-edge tracks, separate fan-out near endpoints, avoid node interiors and minimize crossings;
  crossings that remain must be visually distinguishable rather than rendered as one merged line.
- [ ] Remove or collapse any full-width technical/card ledger that pushes the graph below the fold. The first desktop
  viewport prioritizes controls plus usable topology.

### Acceptance

- [ ] Real self-host desktop screenshots show A3→A4 and CI6→CI7 inside the graph in succession-context and dependency
  views; no standalone series strip and no expanded comparison-card wall exist.
- [ ] Conflict lens with current self-host data has zero red edges and a visible “当前没有已确认的任务冲突” canvas
  state. A synthetic 4+ conflict fixture proves distinct tracks with no coincident unrelated path segments or
  node intersections.
- [ ] Geometry assertions cover node overlap, edge-through-node, coincident path segments, arrow/label visibility and
  stable routing after filter/reset/fit.
- [ ] 1440×900, 1280×800 and 390×844 Browser acceptance verifies topology, inspector/overlay, keyboard focus,
  reduced-motion, zero document overflow and zero console warning/error.
- [ ] Continue the existing W7.3 branch/task and GPT-5.6 Sol medium implementation profile. Do not create W7.4, do not
  integrate CI7/REL3, and do not modify root PROGRESS/HANDOFF outside central integration.

This amendment changes presentation and explicit-series projection only. If implementation needs a new authoritative
relation kind or changes human confirmation authority, stop for a new ADR.

## 2026-08-30 Maintainer Scope Amendment — Readable Topology Re-layout after `05c83b`

The maintainer has rejected the second Graph implementation at exact W7.3 branch commit
`05c83b75723a9e6681c0885dd090606060cb696e`. The page now contains graph-native connectors, but the topology is still
not readable: the default view is reduced to 55%, unrelated relations form a shared vertical bus, labels sit on top
of routes, lane boundaries do not create a comprehensible reading order, and the permanently docked evidence panel
removes a large part of the usable canvas. Contract presence is not visual acceptance.

The isolated GX1 evaluation at `f5fd5afa3f9b133166495119080629a5be5f67b2` is accepted only as an implementation
aid. W7.3 must inspect these exact non-authoritative inputs with `git show`:

- `experiments/workstream-graph-skill-evaluation/evaluation.md`;
- `experiments/workstream-graph-skill-evaluation/fixture-a-relations.json`;
- `experiments/workstream-graph-skill-evaluation/fixture-b-conflicts.json`;
- `docs/validation/2026-08-30-gx1-fireworks-graph-skill-evaluation.md`.

The useful techniques are explicit lanes, separate ports/corridors, bridge/crossing detection, label clearance,
node spacing and route-stretch measurement. The third-party Skill/SVG/HTML is not a runtime dependency, relation
authority, product component or responsive implementation.

### Re-layout contract

- [ ] Rebuild node placement before repairing arrows. At desktop width, A3→A4, CI6→CI7 and U1→U2→U2.2 each occupy
  one aligned series row/lane with consistent node height and a clear left-to-right reading direction. A lane is a
  subtle in-canvas group, not nested boxes that mix unrelated series.
- [ ] Collapse historical chains by default into bounded in-canvas cluster nodes. Expanding one chain must re-layout
  only the affected component; it cannot introduce a full-height shared relation spine or force all current nodes to
  55% scale.
- [ ] The initial desktop/reset view is readable at 100%. `适合窗口` is an explicit action, not the default. If the
  topology cannot fit at readable size, reduce visible history or focus a component instead of shrinking text.
- [ ] The evidence inspector is closed by default. Selecting a node/edge opens an overlay/drawer that does not
  permanently recompute or compress the graph layout; Escape and the close control restore the same viewport.
- [ ] Succession view renders succession + subdued series only; dependency view renders dependency proposals +
  subdued series only; conflict view renders confirmed conflicts only. Comparison overlay remains default-off.
- [ ] Selecting an edge highlights its two endpoints and route while unrelated edges fade. A user must not have to
  follow every line simultaneously to understand one relation.

### Routing and typography contract

- [ ] Every visible relation owns a deterministic route and distinct endpoint ports. Unrelated edges may not share a
  collinear segment longer than 8px outside a 16px endpoint fan-out zone; several edges cannot merge into one
  vertical or horizontal bus.
- [ ] Default/current and synthetic 4+ conflict fixtures meet the GX1 showcase geometry target: zero node
  intersections, zero unmarked crossings/bridges, at most two bends per edge, route stretch ≤1.35, shortest segment
  ≥16px, node gap ≥40px and unrelated edge-label clearance ≥4px. If a fixture cannot meet this, move/collapse nodes
  before adding waypoints.
- [ ] Relation labels use ordinary Chinese, at most three short words in the canvas, offset 6–8px from the line and
  at least 10px from nodes. Full IDs, reason codes and evidence stay in the inspector. Labels cannot mask routes or
  stack on the same coordinate.
- [ ] Stroke and marker colors are one semantic pair: series is muted fine solid, succession is cyan solid,
  dependency is amber dashed, comparison is neutral/amber dotted and confirmed conflict alone is red. Arrowheads
  cannot use a different semantic color from their route.
- [ ] Canvas lanes, titles, legend and controls are obstacles in geometry checks. Routes cannot run through lane
  headings, node text or container borders.

### Responsive and acceptance contract

- [ ] At 390×844, render a dedicated top-to-bottom compact topology/focused chain with ≥12px primary text; do not
  scale the entire desktop canvas to a miniature image. Inspector becomes a dismissible sheet and the page has zero
  horizontal overflow.
- [ ] Browser evidence covers 1440×900, 1280×800 and 390×844 at initial load, reset, filter, fit, select, inspector
  open/close and history expand/collapse. Record visible scale, node/edge bounds, pairwise route overlap, crossings,
  bends, label clearance, focus/ARIA, document overflow and console warnings/errors.
- [ ] Use `fireworks-tech-graph` only as a local design/geometry oracle and perform visual inspection after automated
  checks. At most two focused visual correction rounds may follow a stable implementation; tests alone cannot close
  this gate.
- [ ] The maintainer must accept a real self-host screenshot before W7.3 can return to completed/accepted state.
  `05c83b` and earlier Graph screenshots remain rejected evidence.

### Dispatch and safety

- Continue the existing W7.3 task/branch from exact `05c83b75723a9e6681c0885dd090606060cb696e`; do not create
  W7.4. Refresh Git-private scope to revision 4 after acknowledging the new task-description version.
- Use GPT-5.6 Sol with medium reasoning for implementation. Run focused Graph tests while iterating; run routed Fast
  and Checkpoint once after the visual layout stabilizes instead of repeatedly paying full checkpoint cost.
- Preserve relation capture Core/schema/CLI/Harness, human confirmation authority, inbox behavior and append-only
  history unless a focused regression proves a necessary compatibility fix. Do not integrate CI7/REL3, modify root
  PROGRESS/HANDOFF from the feature branch, push main, publish or change public/default behavior.

## 2026-08-30 Maintainer Scope Amendment — W Program Hierarchy & Controlled Bundling

Governing decision: [ADR-0020](../../decisions/0020-workstream-program-and-phase-hierarchy.md)

Approved Design: [Workstream program hierarchy and graph bundling](../../design/workstream-program-hierarchy-and-graph-bundling.md)

The maintainer clarified that W tasks share a real development-program structure. The previous re-layout contract
was too restrictive in two ways: it treated the absence of `series_id` as absence of all W organization, and it
prohibited useful same-semantics fan-out trunks. W is not one linear series, but it is one program with W5/W6/W7
phases. This amendment supersedes only the conflicting presentation constraints; ADR-0017 relation authority and the
remaining readable-topology requirements stay in force.

### Program hierarchy implementation

- [ ] Implement ADR-0020 group-definition and primary-membership contracts with program/phase hierarchy, opaque IDs,
  explicit order, revision/CAS, source links and human-integrator acceptance. Agent/task owner may propose only.
- [ ] Keep group membership orthogonal to series and semantic relations. Membership must not alter relation counts,
  active tips, gate eligibility, closure, ownership, review or validation state.
- [ ] Legacy records without accepted membership remain ungrouped/Unknown. Reject prefix/title/branch inference and
  W-looking negative fixtures.
- [ ] Add the Approved Design's exact self-host repair fixture for W/W5/W6/W7. It appends explicit metadata and keeps
  CI1/SH1 outside the W program while real edges may cross the program boundary.
- [ ] Project one continuous W program region with W5/W6/W7 phase lanes and independent folding. Do not connect all W
  tasks with a fake series; retain actual chains and cross-boundary relations.

### Controlled relation bundling

- [ ] Replace the blanket long-collinear-overlap prohibition with declared `route_bundle_id` semantics. Bundling is
  allowed only for identical relation type/direction/lifecycle/certainty/gate/style with a common source or target.
- [ ] Draw one owned trunk and separate endpoint branches. Branches use distinct ports/arrowheads and separate by
  ≥24px before the target. Mixed series/dependency/conflict/comparison/Unknown edges cannot share a bundle.
- [ ] Keep every underlying relation selectable and inspectable. Branch click selects one relation; trunk click opens
  a bounded relation list; selected relation highlights its trunk plus its branch without merging evidence.
- [ ] Geometry tests treat declared trunk overlap as valid and all undeclared coincident segments as failure. Nodes,
  headers, labels and controls remain hard obstacles.

### Selection correction

- [ ] Pointer selection brightens the existing semantic border and adds only a weak same-color glow. Remove the white
  outer selection rectangle. Dim unrelated graph content without hiding status or evidence.
- [ ] Preserve keyboard focus visibility with a non-white semantic accent and no layout shift. Inspector behavior and
  read-only authority remain unchanged.

### Acceptance and dispatch

- [ ] Desktop screenshots show a continuous W program with W5/W6/W7 substructure, actual CI1/SH1 cross-boundary
  chains and no fabricated W series edge.
- [ ] U1 same-type fan-out fixture demonstrates a shared succession trunk with visibly separated U2/A4/CI7 branches,
  distinct arrowheads and correct individual inspector identities.
- [ ] Existing A/CI/U series, dependency/conflict lens separation, 100% reset, inspector, mobile topology and geometry
  gates remain accepted only after a new maintainer screenshot review.
- [ ] The prior two visual correction rounds were performed under superseded grouping/bundle constraints. This
  amendment permits at most two focused visual correction rounds after the new hierarchy/bundle implementation.

Continue the same W7.3 task/worktree from `05c83b75723a9e6681c0885dd090606060cb696e`, preserving its current
uncommitted changes to the two Graph modules and focused test file. Refresh Git-private scope to revision 5 after
acknowledging the new task-description version. Use GPT-5.6 Sol medium. Do not run routed Fast/Checkpoint before the
maintainer accepts the new visual direction; do not create W7.4, integrate CI7/REL3, modify feature-branch root
PROGRESS/HANDOFF, push main, publish or change public/default behavior.

## 2026-08-30 Maintainer Scope Amendment — Partial-order Reading & Evidence-qualified History Folding

The maintainer clarified that “缩略” means structural folding of eligible old tasks, not low-zoom semantic hiding.
The invariant “right is newer” must be restored as a relation-backed partial-order reading contract rather than an
invented global timeline. This section refines ADR-0020 presentation only and does not add authority semantics.

### Horizontal ordering

- [ ] Interpret horizontal direction as **confirmed predecessor/history on the left → confirmed successor/current on
  the right**, not calendar time. Canvas/help text must say that unrelated tasks do not imply time order.
- [ ] Only effective/current `derived_from`, confirmed succession and explicit series predecessor/order may increase
  horizontal rank. `depends_on`, `absorbs`, program/phase membership, task code, display prefix, branch/title and
  filesystem timestamps cannot define old/new rank.
- [ ] Mutually unreachable/incomparable tasks occupy the same horizontal rank and stack vertically. Stable sorting is
  allowed only inside that rank; it cannot move an independent task into a later x-column and fabricate chronology.
- [ ] A current/rightmost tip is shown only when endpoint, scope and evidence are current. Unknown/stale records remain
  visibly non-current and cannot be forced right merely because they are active in memory.

### History eligibility and cluster semantics

- [ ] Default folding requires all of: closed/superseded/historical lifecycle; not active tip; current evidence and
  scope; no pending human confirmation; no Unknown/stale/conflict; no untransferred responsibility; and membership in
  one contiguous historical chain or a wholly completed phase.
- [ ] W5/W6 may collapse as completed phase clusters only when every included member meets eligibility. Branches that
  do not form one contiguous phase/chain remain separate clusters; age or left position alone cannot collect them.
- [ ] Cluster summary shows phase/chain label, member count, first/last endpoints, status summary and inbound/outbound
  external relation counts. Internal edges may hide, but every external edge redirects to a typed cluster boundary
  port and remains inspectable.
- [ ] Expanding a cluster restores exact member nodes/edges in place and preserves an anchor near the clicked cluster;
  it cannot recenter or globally rescale the canvas. Collapse/expand changes structure only, not facts or zoom.
- [ ] Tasks with pending confirmation, unresolved conflict, Unknown/stale evidence, active responsibility or current
  blocking role are never folded even if another task considers them historical.

### Deterministic layout pipeline

Apply exactly this order:

```text
accepted program/phase membership
→ history eligibility and contiguous cluster folding
→ confirmed partial-order rank
→ node placement
→ declared same-semantics route bundling
→ labels, arrowheads and selection projection
```

Bundling before folding or rank is invalid because it can create orphan trunks or routes through clusters.

### Zoom and acceptance

- [ ] Keep explicit zoom at 30%–200% and reset at 100%. Do not hide labels, evidence or nodes because of zoom level;
  a user-chosen 30% may be physically small but must represent the same facts.
- [ ] Space reduction comes from eligible history/phase folding and focused selection, never conditional semantic
  removal tied to scale.
- [ ] Tests cover independent same-rank tasks, false order from dependency/absorbs, stale/pending/non-transferred
  no-fold cases, contiguous versus branched clusters, external-edge redirection, anchor-preserving expansion and
  folding-before-bundling order.
- [ ] Browser evidence shows default folded W5/W6 plus expanded views at 100%, 30% and 200%, with identical fact
  counts after expansion, no overflow/console errors and no fabricated horizontal order.

Continue the current W7.3 implementation and preserve all current uncommitted changes. Refresh Git-private scope to
revision 6 after reading only this Plan amendment and its Validation section; do not reread older Skill/authority
materials. Use focused Graph/Core tests only, and keep routed Fast/Checkpoint blocked until maintainer screenshot
acceptance.

## 2026-08-30 Maintainer Correction — Component-local Rank & Two-dimensional Block Packing

The previous amendment's statement that mutually unreachable tasks share one rank was incorrectly interpreted across
the entire visible graph. That interpretation produced a tall global rank-0 column and full-height shared route buses.
This correction supersedes only that global-layout interpretation; the confirmed partial-order and evidence-qualified
history-folding semantics above remain unchanged.

### Rank scope and local layout

- [ ] Compute horizontal rank **locally**, never once for the whole visible graph. A rank domain is one
  relation-connected component, one explicit series lane, or one accepted program-phase lane. Every disconnected
  component has its own rank origin.
- [ ] Mutually unreachable tasks may share a rank and stack vertically only inside the same local domain. Independent
  components must not be collected at one global x coordinate merely because no semantic edge connects them.
- [ ] Explicit A/CI/U series remain compact left-to-right rows. W5/W6/W7 remain distinct program phase blocks, normally
  arranged top-to-bottom, while confirmed chains inside each phase read left-to-right.
- [ ] Program/phase/series containment controls block membership and presentation only; it still cannot fabricate a
  `derived_from`, `depends_on`, `absorbs`, conflict or chronology edge.

### Two-dimensional component packing

- [ ] Lay out each local domain first, measure its bounds, then pack independent component blocks into bounded
  two-dimensional rows/grid within the available viewport width. Use a subtle block header/boundary or sufficient
  gutter so side-by-side blocks read as spatial packing rather than chronology.
- [ ] The packer may use stable bounded rows or masonry, but it must not place every independent block in one global
  vertical column. Default 100% should use the first viewport in both dimensions before adding canvas height.
- [ ] Repacking is deterministic and stable under selection, inspector open/close and reset. Selection cannot trigger
  a global column collapse, re-rank unrelated blocks or recenter the entire canvas.

### Block-scoped cross-routing

- [ ] A route bundle is scoped to one common endpoint **and** one source-block/destination-block pair. A declared
  same-semantics bundle must not span unrelated components or multiple program phases as one global trunk.
- [ ] When one endpoint targets multiple blocks/phases, split the routes into one bundle per target block/phase, or use
  dedicated boundary channels between that exact block pair. Cross-block routes enter/leave through block boundary
  ports and gutters, not through a full-height central bus.
- [ ] No overview route trunk may traverse unrelated series/program regions or collect unrelated edges merely because
  they share relation style. Local parallel segments remain separated enough to identify ports and arrowheads.

### Corrected deterministic pipeline

Apply exactly this order:

```text
accepted program/phase/series membership
→ eligible history folding
→ relation-connected component partition
→ component-local partial-order rank
→ local node layout
→ two-dimensional block packing
→ block-pair-scoped bundle routing
→ labels, arrowheads and selection projection
```

The earlier `membership → folding → global rank` reading is invalid. Rank before component partition or bundle before
block packing can recreate the rejected column and bus layout.

### Corrected acceptance and dispatch

- [ ] A fixture with at least four disconnected components produces at least two occupied block columns at 1440px and
  1280px; disconnected roots do not all share one global rank-0 x coordinate.
- [ ] A/CI/U series remain compact horizontal rows; W5/W6/W7 remain visibly distinct phase blocks; confirmed local
  chains still read left-to-right without implying order between neighboring blocks.
- [ ] No bundle crosses more than its declared source/destination block pair, and no global vertical trunk spans the
  series and program regions. Automated geometry evidence covers block overlap, route/card crossing and boundary-port
  routing without freezing incidental pixel coordinates.
- [ ] The maintainer must accept a real 100% screenshot showing multiple compact blocks/rows in the first viewport—not
  one tall column—before routed Fast/Checkpoint becomes eligible.

Continue the same W7.3 task/worktree and preserve all current uncommitted changes. Refresh Git-private scope to
revision 7 after reading only this correction and the matching Validation correction. Use GPT-5.6 Sol medium. Make the
smallest layout/routing correction needed; do not rerun routed Fast/Checkpoint before screenshot acceptance and do not
create W7.4, discard current work, integrate another branch, push, publish or change public/default behavior.

## 2026-08-30 Maintainer Correction — Module-scoped Graph Projection

The maintainer observed that selecting Documentation System, Context Routing Research, Authority Model or
Multi-worktree Collaboration still showed nearly the same task population. A module selector that only changes a
label, highlight or layout emphasis is not a module view. This correction uses ADR-0020's existing derived-view
filter permission and adds no authority or relation semantics.

### Strict module visibility

- [ ] `全部模块` is the only default option that projects the complete eligible graph. Selecting a concrete module
  applies a strict visibility predicate before history folding, component partition, rank or routing.
- [ ] A full task card is in scope only when the selected stable module ID equals its explicit primary subsystem or
  appears in its explicit affected-subsystem set. Display labels, task codes, branch/title text, series/program
  membership and relation proximity cannot infer module membership.
- [ ] Missing, Unknown or unregistered module metadata belongs to a separate `未归属` view. Unknown tasks must not be
  copied into every concrete module view.
- [ ] Module and runtime/status filters intersect. Selecting a module plus a status means `module AND status`, never a
  union that restores unrelated tasks.

### Cross-module context without graph flooding

- [ ] When an in-scope task has a visible relation to an out-of-scope task, retain the relation as a compact boundary
  endpoint/stub labelled with the external module and task identity. Do not render the out-of-scope task's full card,
  series lane, phase contents or unrelated neighbors.
- [ ] A group/series/program/phase container appears only when it contains at least one in-scope full task card. It
  projects only visible members plus required boundary stubs; container membership cannot pull every member into the
  selected module.
- [ ] An explicit `显示关联上下文` action may expand one-hop external full cards for inspection, but it is off by
  default, visibly marked as context, bounded to one hop and reset whenever the selected module changes.
- [ ] Boundary stubs preserve exact underlying edge identity and inspector evidence. They do not change relation
  counts, module facts, active tips, gates, history eligibility or execution authority.

### Pipeline and interaction

Apply module projection before layout:

```text
eligible task/relation facts
→ selected-module full-card predicate
→ bounded cross-module boundary stubs
→ eligible history folding
→ relation-connected component partition
→ component-local rank and local layout
→ two-dimensional block packing
→ block-pair bundle routing
```

- [ ] Changing modules recomputes visible nodes, containers, components, bounds and fit target while keeping reset at
  100%. It must not retain hidden-module nodes as layout obstacles or invisible route endpoints.
- [ ] The empty state names the selected module and says that no matching task evidence is available. It must not
  silently fall back to all modules.
- [ ] Visible counts and any summary/legend describe full cards separately from external boundary stubs.

### Acceptance and dispatch

- [ ] A fixture with disjoint Authority, Documentation, Context Routing and Multi-worktree tasks proves distinct node
  sets for all four concrete selections; a deliberately multi-module task appears only in its explicitly listed
  modules.
- [ ] A cross-module relation fixture shows one full in-scope endpoint plus one compact external boundary stub by
  default, and only the explicit one-hop action may reveal the external full card.
- [ ] Browser screenshots for the four real self-host module selections visibly differ in task count and topology;
  none repeats the all-module graph, and module+status intersection, empty state and module switching remain stable at
  1440px, 1280px and 390px.
- [ ] Focused tests assert exact visible Workstream IDs, boundary-stub IDs, container membership and zero hidden-node
  influence on component/rank/bundle geometry; they do not rely only on dropdown text or CSS visibility.

Continue the same W7.3 task/worktree and preserve all current uncommitted changes. Refresh Git-private scope to
revision 8 after reading only this correction and the matching Validation correction. Use GPT-5.6 Sol medium and
apply it together with revision 7's layout correction. Do not rerun routed Fast/Checkpoint before maintainer visual
acceptance; do not create W7.4, discard work, push, publish or change public/default behavior.

## 2026-08-30 Maintainer Correction — Topology-first Soft Grouping & Local Crossing-free Routing

The maintainer rejected the revision-7 preview because it replaced the global single column with a single tall W
program tower. The implementation removed program members from normal connected-component packing, stacked every
phase by incrementing one vertical cursor, and then reconnected displaced endpoints with page-scale orthogonal lines.
Passing presence tests for phase boxes and edges did not establish a readable graph. This correction supersedes hard
program containment and broad block-pair routing while preserving ADR-0020 membership facts.

### Relation topology has placement priority

- [ ] After revision 8 module projection and eligible folding, partition by the **visible graph edges for the current
  lens**, including subdued explicit-series connectors. A connected component may contain tasks from several modules,
  programs or phases; all of its full endpoints and boundary stubs are laid out together as one topology unit.
- [ ] Program/phase/series membership may label, tint or order otherwise equivalent placements, but it must not remove
  a node from its relation-connected component, split related endpoints into distant containers, merge disconnected
  components or override crossing minimization.
- [ ] Lay out actual adjacency first: connected predecessor/successor endpoints occupy neighboring ranks whenever the
  partial order permits. Within a rank, use deterministic median/barycentric sweeps (or equivalent crossing
  minimization) over adjacent ranks before applying stable-ID tie breaking.
- [ ] Optimize in this order: zero node/container intersections → minimum edge crossings → short adjacent-endpoint
  routes → compact area → stable tie ordering. Compactness may not win over crossings or route length.

### W program is a soft overlay, not one enclosing tower

- [ ] Remove the single bounding rectangle that encloses every W program member. Render W membership as a lightweight
  repeated program label and phase-local header/hull attached to each local topology block; no empty rectangle may
  span disconnected W components.
- [ ] W5/W6/W7 phase order may sort local blocks, but it cannot force them into one vertical column. Disconnected phase
  components participate in the same two-dimensional packer as A/CI/U components.
- [ ] A phase containing three or more mutually incomparable visible tasks must use at least two desktop columns (or
  separate local component blocks); it cannot become a one-card-wide vertical rail. A genuine confirmed chain remains
  left-to-right rather than being wrapped into a fake grid.
- [ ] In the current self-host fixture, W5C/W5D/W5E and W7.1/W7.2.2/W7.2.3/W7.3-INT/W7.3 must not form one narrow
  vertical tower. CI1/SH1/U1 and their related W endpoints must be co-placed by their real connections, not separated
  to the bottom of a program box and joined by page-height lines.

### Local routing and fan-out only

- [ ] A declared bundle is only a short endpoint fan-out aid. Its shared trunk must remain inside the common
  endpoint's local rank gutter and end within 64px or one rank gap (whichever is smaller); after that, every branch
  owns a separate obstacle-avoiding route. `block-pair` identity alone never licenses a long shared spine.
- [ ] Route inside the owning topology component using node, label, group header/hull and existing route tracks as
  obstacles. A route cannot cross an unrelated component/phase interior or use the whitespace inside another block
  as a corridor.
- [ ] Reorder or repack nodes before accepting a crossing. The real self-host default view must have zero unmarked
  route/route crossings, zero route/card/header intersections and zero page-spanning vertical or horizontal trunks.
  If a synthetic graph cannot avoid a crossing, use an explicit bridge only after proving reordering and separate
  tracks cannot solve it.
- [ ] Existing route stretch, bend, segment and label-clearance requirements apply to every relation branch and trunk,
  including declared bundles; bundling does not exempt geometry gates.

### Corrected pipeline

```text
eligible facts
→ strict module full-card projection and boundary stubs
→ eligible history folding
→ visible-edge connected components across organizational boundaries
→ component-local partial-order rank
→ crossing-minimized in-rank ordering
→ local topology layout
→ two-dimensional component packing
→ soft program/phase overlays
→ short endpoint fan-out and obstacle-avoiding routes
→ labels and selection
```

Hard program containment before component partition is invalid because it creates the rejected W tower and forces
long cross-program routes.

### Acceptance and dispatch

- [ ] Geometry tests run against the actual self-host snapshot as well as synthetic fixtures. They assert zero
  route/route crossings, zero route/node/header/hull intersections, no trunk longer than the local fan-out limit, no
  one-column W tower and no program hull spanning disconnected components.
- [ ] A topology fixture with cross-phase and cross-program edges proves related endpoints remain in one local
  component while organizational labels remain readable and do not create edges.
- [ ] The default 100% desktop screenshot must show several balanced topology blocks, short local connectors and
  readable W phase labels. A full-height capture that requires tracing lines across multiple screen heights is a
  failure even if every endpoint is technically connected.
- [ ] Focused unit/geometry tests are necessary but cannot close this gate. Present the new real 1440px/1280px page to
  the maintainer before any routed Fast/Checkpoint.

Continue the same W7.3 task/worktree and preserve every current uncommitted file. Refresh Git-private scope to
revision 9 after reading only this correction and the matching Validation correction. Use GPT-5.6 Sol medium and
implement revisions 8 and 9 together. Replace the hard program-stack algorithm rather than tuning its spacing. Do not
create W7.4, discard work, integrate another branch, push, publish or run routed Fast/Checkpoint before maintainer
visual acceptance.

## 2026-08-30 Maintainer Correction — Single-pass Occupied-bounds Packing

The maintainer rejected the revision-9 preview because nodes, repeated W7 phase decorations and route corridors were
stacked on top of one another. Inspection found a concrete implementation defect: the code measured and packed blocks,
then performed a second coordinate mutation that expanded rank columns without remeasuring or moving following
blocks. Phase rectangles were also regenerated per node after packing, outside the measured block bounds. This is a
layout-pipeline failure, not a spacing or theme defect.

### Frontend layout brief

- **Purpose:** scan real task relations without tracing through overlapping cards, group boxes or routes.
- **Context/tone:** dense analyst workspace using the existing Orrery tokens and card typography.
- **Memorable behavior:** every topology component is one collision-free measured object; organizational membership is
  readable inside that object but never changes its final footprint after packing.
- **Constraint:** no ImageGen, decorative redesign, new runtime dependency or loss of keyboard/mobile/read-only
  behavior.

### One canonical placement pass

- [ ] Delete or replace the superseded hard-program placement and every post-pack x/y rewrite. A node's local
  coordinates, rank order and decoration geometry must be final before its component is measured.
- [ ] Each component produces one immutable local layout record containing `node_rects`, allocated header/badge rects,
  reserved route gutters and `occupied_bounds`. `occupied_bounds` is the union of all of these plus the required
  component gutter; raw node bounds alone are not packable bounds.
- [ ] The global packer operates only on immutable `occupied_bounds`, assigns one translation per component and applies
  that same translation to nodes, decorations, ports and route-gutter anchors. After translation, no element may
  change component-relative x/y. A layout change restarts measure → pack; it cannot patch coordinates in place.
- [ ] Canvas width/height, fit target and scroll extent are computed from final occupied bounds after all translations,
  never from an earlier placement pass.

### Remove overlapping group decoration

- [ ] Default overview renders no SVG rectangle enclosing a program or phase and no per-node phase hull. Replace W
  containment boxes with either one measured 22–28px component header (`W › W7`) or a compact membership label inside
  the existing task-card metadata line.
- [ ] If several same-phase tasks share one component, render at most one allocated component header. If they are in
  separate components, each component may repeat the label inside its own occupied bounds; identical labels cannot
  share coordinates or overlap another component.
- [ ] Series/program/phase highlight on focus may tint existing cards/connectors, but cannot add an unmeasured overlay,
  resize a block, cover text or create a new nested rectangle after packing.

### Route-corridor reservation

- [ ] Route planning starts only after final component translation. The local layout reserves rank gutters and edge
  fan-out channels inside `occupied_bounds`; routes may not escape into a neighboring component's packed rectangle.
- [ ] If obstacle routing needs more space than reserved, enlarge that component's local occupied bounds and rerun the
  global pack exactly once before rendering. Never draw first and discover overlap from the screenshot.
- [ ] Relation labels receive measured rectangles and participate in the same collision check. Labels cannot be placed
  by midpoint alone when that point intersects another route, node, header or label.

### Mechanical postconditions before preview

- [ ] Before generating another maintainer preview, focused tests and the real self-host model must assert pairwise
  intersection area `0` for every full node card, component occupied bound and measured header/label rect; distinct
  component bounds retain at least the declared block gap.
- [ ] Assert every node, header, label, port and route segment is contained by its owning component bounds (except the
  exact arrowhead allowance) and every final coordinate is non-negative and within canvas bounds.
- [ ] Assert one placement/translation per component, no post-pack node-coordinate mutation, no duplicate phase
  decoration at the same coordinate and no superseded hard-program layout path in the shipped source.
- [ ] The current real self-host 100% geometry must report zero node overlap, zero decoration/card overlap, zero
  component-bound overlap, zero route/card/label intersections and zero unmarked route crossings before a screenshot
  is shown. A screenshot is review evidence, not the first collision detector.

Continue the same W7.3 task/worktree and preserve every dirty file. Refresh Git-private scope to revision 10 after
reading only this correction and the matching Validation correction. Use GPT-5.6 Sol medium and retain revisions 8/9.
Implement the single immutable layout pipeline and mechanical postconditions before rebuilding the preview. Do not
create W7.4, discard work, push, publish or run routed Fast/Checkpoint before maintainer visual acceptance.
