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
