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
