# 实施计划：W7.3 Workstream Relation Capture & Confirmation

Status: Implemented and locally validated Candidate; authority amendment acknowledged at `6315415075fb78b61d9a5bb835725bced0bc9ce1`

Date: 2026-08-29

Governing ADR: [ADR-0017](../../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)

Approved Design: [Workstream relation capture and confirmation](../../design/workstream-relation-capture-and-confirmation.md)

Dispatch governance: ADR-0018 at authority commit `6315415075fb78b61d9a5bb835725bced0bc9ce1`
(the integration branch must land that exact authority commit before this Candidate).

## Goal

让 Workstream 在创建、后续衍生和集成时形成真实可审计的 relation DAG，而不是要求维护者事后手写关系或
让 Graph 从相似性猜测。W7.3 不实现可选 Conductor Skill，不新增远程执行，不允许 Agent 确认语义关系。

## Phase 0 — versioned contracts and fixtures

- [x] 冻结 proposal/event/confirmation/role fixture 与 JSON schema；v1 relation 继续可读。
- [x] 为 `depends_on.required_for` 冻结 implementation／validation／integration／release 四种 gate 及 legacy
  unknown 行为。
- [x] 冻结 proposer/evidence/confirmer/role/revision/hash 字段和 path/size/count/symlink 安全门。
- [x] 建立单人 owner、Team owner、多 integrator conflict、无 integrator、Agent spoof、legacy v1、cycle、
  late-CI fan-in 等正负组合。

## Phase 1 — automatic mechanical lineage

- [x] Workstream registration/rebind 自动尝试 `derived_from`，仅接受 same-project exact OID 和本地 ancestry。
- [x] 重复输入幂等；drift/non-ancestor/self/cycle/Unknown 失败关闭并返回 required metadata。
- [x] append-only event 写入 Git-common-private store；作者树、package、Team sync 和外网零写入。
- [x] Codex/Claude/DeepSeek/Harness Adapter 只提供 caller/platform provenance，不拥有确认权。

## Phase 2 — `depends_on` proposal and gate confirmation

- [x] Core/CLI 支持 suggest/inspect/accept/change-gate/defer/reject；Agent 只能 suggest。
- [x] implementation/validation 只接受 source task owner 的本机人类确认。
- [x] integration/release 只接受人类 integrator 确认；central Team request 不能直接生效。
- [x] gate-aware lifecycle eligibility 只消费 effective current relation，Unknown/proposed 不阻塞。
- [x] Harness 从明确 Prompt/Plan/artifact/gate evidence 生成候选，不把 path overlap 自动升级为 dependency。

## Phase 3 — integrator and `absorbs`

- [x] Personal project owner 成为默认 sole integrator；Agent/session 身份拒绝。
- [x] Team owner 可显式 grant/revoke human integrator；无 integrator 时失败关闭。
- [x] `absorbs` proposal 显示 target closure/Validation/scope，只有 integrator confirmation 产生 effective event。
- [x] 多 integrator 使用 revision/CAS；冲突决定保持 pending，不 last-writer-win。

## Phase 4 — Observatory inbox and graph projection

- [x] Personal/Team 增加“关系待确认”，显示原因、gate、证据与本机权限；中央仍 request-only。
- [x] Graph 显示 effective/proposed 与 required_for，但不增加 confirm/apply/undo 按钮。
- [x] 任务创建不经过 Orrery UI 时，Skill/CLI 在首次产品写入前完成注册；未登记任务显示 finding 而不伪造关系。
- [x] 真实 self-host 以新 Integration Workstream 演示 fan-out/fan-in，不能回写旧历史意图。

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

- [x] Add versioned explicit `series_id`, `task_code`, `series_order` and optional
  `series_predecessor_workstream_id` (or versioned equivalent); never
  infer facts from `A3/A4`, `CI6/CI7` name prefixes.
- [x] Keep series grouping visually distinct from `derived_from`／`depends_on`／`absorbs` edges.
- [x] Explicit predecessor registration creates a proposal with suggested gate/evidence, never an effective edge.
- [x] Produce read-only self-host repair proposals for A3→A4 and CI6→CI7; maintainer confirmation selects the exact
  relation/gate before any effective event.

### User-facing status taxonomy

- [x] Replace the generic “待确认” collapse with deterministic Chinese states for active, human-confirmation pending,
  evidence/scope stale, historical, session missing/relation-only, unregistered and genuinely Unknown.
- [x] Keep raw lifecycle/runtime/evidence/scope axes in technical details; only actual human decision pending uses
  “等待人工确认”.

### Comparison versus conflict

- [x] Preserve conservative Core `compare_pairs` semantics but project them as amber comparison/review suggestions,
  not red conflicts.
- [x] Conflict lens contains only evidence-backed conflict facts (path/module/exclusive-resource/contract or explicit
  human finding), with location, impact and source.
- [x] No confirmed conflicts produces “当前没有已确认的任务冲突”.
- [x] Translate stale/unconfirmed/independent/post-fork reason codes into ordinary Chinese in a separate comparison
  queue; they must not create red Graph edges.
- [x] Version any changed projection/schema contract without rewriting v1 history.

### Acceptance

- [x] Real self-host shows A and CI series while unconfirmed predecessor links remain proposals.
- [x] Current compare suggestions and confirmed conflicts are completely separated.
- [x] 1440px/390px Graph and ledger preserve facts, keyboard/ARIA, zero overflow and read-only canvas.
- [x] Graph never confirms relations; local relation inbox remains the only confirmation UI.

Expected affected surfaces include relation capture Core/schema, registration/CLI/Harness, relation inbox,
presentation projection and their focused tests. If implementation requires a new relation kind or changes
confirmation authority, W7.3 must stop for a new ADR rather than expanding this Plan.
