# 实施计划：CI7 Validation Routing Precision & Total-Cost Diagnostics

Status: Amendment implemented; `290482f` Fast non-green / Checkpoint PASS recorded; diagnostic follow-up requires fresh central evidence

Date: 2026-08-29

Primary subsystem: `test-coverage`

Governing inputs:

- [Orrery 核心原则](../../core/principles.md)，尤其“验证强度必须与阶段和风险匹配”；
- [CI6 Local Validation Router Plan](2026-08-29-ci6-local-validation-router-tier-enforcement.md)；
- [Test Coverage State](../../state/test-coverage.md)。

## Why this is not a new ADR

CI7 不改变 Fast／Checkpoint／Candidate／Promotion 分别能证明什么，不允许高层级替代失败的低层级，不把
超时解释为通过，也不修改 15／90 秒预算、required checks、exact-SHA binding 或 main 推广门。它只修正
CI6 数据映射精度，并增加非权威成本诊断。因此现有 Seed 原则、CI6 contract 与 Implementation Plan 足以
约束本工作；如果未来要引入阶段替代、预算豁免或 ROI 强制准入门，必须另提 ADR。

## Problem

CI6 已阻止 feature task 直接把任意 unittest 套件冒充层级证据，但仍有两个成本缺口：

1. `observatory-ui` 等宽 surface 会让只修改 Graph 的任务选中无关 Maintenance real-Git fixture；W7.2.1
   的产品回归通过，但 Checkpoint 因无关 fixture 和 import/setup overhead 越过 90 秒。
2. 为了取得绿色 receipt，feature Agent 可能在原任务内继续优化测试夹具。最终测试变快，却额外消耗 Agent
   token、调试时间、重跑和维护复杂度；当前 receipt 只展示最终执行时间，不能判断优化是否回本。

## Non-negotiable boundaries

- Feature task 遇到超预算时只允许一次有界定位；必须保留非零失败 receipt、最慢 test IDs 与选择原因，
  不得在原任务中扩张为长期 CI 优化。
- 中央整合者先用 exact Git diff 重新路由，不继承过宽或失效的 Workstream expected-write glob。
- 同一无关瓶颈影响两个独立 Workstream 后，才建议建立独立 CI performance/routing Workstream；建议不自动
  创建任务，也不是合并授权。
- 不删除 assertion、不降低安全失败门、不把重型测试静默移出 Promotion、不提高预算来制造 PASS。
- 非关键成本与选择信息由 CLI／Harness receipt 生成，不要求 Agent 把它们写入自然语言上下文。

## Phase 1 — split generic Observatory surfaces

- [x] 将宽 `observatory-ui` 数据映射拆成稳定、可复用的 `observatory-shell`、`observatory-graph`、
  `observatory-maintenance` 与 `observatory-team-personal` surface；不得包含 task ID 或 branch 名。
- [x] 以实际 changed paths 为首要输入；Git-private subsystem 只在没有路径证据时保守 fallback。
- [x] expected writes 必须是精确文件或受支持的窄 glob；目录级宽声明生成 refusal／required metadata，不能扩大
  正式选择面。
- [x] Graph presentation 变化不选择 Maintenance Git fixture；Maintenance provider／Quick Remove 变化仍选择其
  当前安全门；Unified common security 变化选择所有受影响 consumer 的小型 adjacency。
- [x] 保持 Promotion inventory 每个 final unittest ID 恰好一次，完整 Windows／Ubuntu覆盖不变。

## Phase 2 — total validation cost diagnostics

- [x] 在 receipt 中增加纯诊断 `cost_diagnostics`，至少机械记录：selected test count、test runtime、router/setup
  wall time、rerun count、slow IDs、修改的 test/CI 文件数与行数、是否由独立 optimization Workstream 产生。
- [x] 可获得宿主 usage 时记录真实 Agent/tool usage；不可获得时写 `unknown`，不得估算或伪造 token。
- [x] 允许维护者提供 advisory `expected_future_runs`，CLI 计算简单 break-even 次数；该值不成为 PASS／FAIL、
  Authority、release 或自动任务创建依据。
- [x] Validation 同时报告测试节省和优化投入；只展示“最终快了多少”不能称为整体效率改进。

## Phase 3 — feature-task stop and central triage

- [x] over-budget receipt 明确区分：产品 test failure、router over-selection、fixture/runtime variance 与真正慢路径。
- [x] feature task 默认停止并回报；中央可选择重新路由、建立独立 CI task 或继续保持 blocked，不得要求功能
  Agent 自行追绿。
- [x] 第一次偶发超时只保留证据；同一瓶颈第二次影响独立 Workstream 时生成 advisory recurrence finding。
- [x] finding 只属于 Git-private／Validation 诊断，不自动形成 ADR、State、关系事实或执行任务。

## Validation portfolios

- W7.2 Graph-only diff：Fast／Checkpoint 不得选择 Maintenance real-Git fixture。
- U2.2 Maintenance diff：必须选择 Maintenance safety/checkpoint，但不得选择无关 Graph heavy journeys。
- Unified common-security diff：选择 bounded cross-consumer adjacency，并保持 15／90 秒预算。
- Mutation：路径缺失、重叠 mapping、过宽 expected writes、伪造 token usage、ROI 字段升级为 gate 均失败关闭。
- Promotion inventory／lanes／required checks／workflow text 与 CI6 前后完全等价。

## Completion and rollback

完成需要 CI contract、data-only mapping mutation、Fast/Checkpoint portfolios、完整 inventory、repository gates
和 exact-SHA hosted Promotion。回滚只恢复 CI7 registry／diagnostic字段；CI6 runner、现有预算、Promotion 与
required checks 继续可用。实现后同步 [Test Coverage State](../../state/test-coverage.md)、独立 Validation、
DEVLOG 与索引；根 PROGRESS/HANDOFF 由唯一整合者维护。

## 2026-08-30 Maintainer Scope Amendment — Composable Acceptance Gates & Validation Leases

Original Candidate `a520ebc74a0846c148e73312ea2fbf2a32b4b08b` 的 routing/cost 能力保留。维护者根据
真实 UI Workstream 的重复跨模块测试成本，批准机械化 phase/gate enforcement。该扩展不改变各 stage 的证明
含义、15／90 秒预算、exact-SHA Promotion 或 required checks；它只控制何时可进入 stage 以及哪类 evidence
可以解锁。Agent self-acceptance、remote authorization、stage substitution、budget waiver 与 public/default
activation 仍不在授权内。

### Acceptance policy v1

- [x] 提供 additive/versioned `acceptance_policy` 与可组合 `acceptance_gates`；v1 只支持 `all_of`，不使用互斥
  `acceptance_mode`、`any_of`、weighted voting 或 Agent-selected omission。
- [x] 每个 gate 固定 stable ID、kind、`required_before`、authority role、exact contract path/blob OID、surface IDs、
  status、evidence requirements 与 hashed receipt ref；五类为 `human_experience`、`contract`、`measurement`、
  `operation_authorization`、`platform_matrix`。
- [x] status taxonomy 为 proposed／ready／accepted／rejected／stale／unknown；Unknown kind/status 不解锁。
  Experience/operation 只认声明 role 的 human receipt，operation 还要求 action-time authorization；机械
  contract/measurement/matrix 必须携带此前 human-approved exact contract。
- [x] actor/role/revision/scope-CAS/receipt envelope 复用现有权威边界；validation receipt 不成为 ADR/State facts。

### Compatibility, freshness and privacy

- [x] 无 policy 的现有 session 以 `legacy-unclassified` shadow 兼容，不重写历史；human-authorized enforcement
  record 可要求 activation 之后的新 Workstream 至少声明一个 gate，legacy adoption 必须显式 human-reviewed。
- [x] acceptance 绑定 relevant `surface_fingerprint`：exact contract blob、mapping registry 与相关 source/test path；
  无关文档不使其 stale，contract／surface／scope／authority-role 改变会拒绝旧 receipt。
- [x] Personal 保持 zero-network；Team 只投影 bounded gate metadata 与 request-only capability，不发送 Prompt、
  transcript、source、diff、credential 或 raw private evidence。

### Validation lease and no-repeat enforcement

- [x] router 只在 gates 满足且 predictive preflight 允许时签发 Git-private `validation_lease`，绑定 Workstream、
  scope、stage、fingerprint、exact allowed test IDs/count、p95、固定 budget、receipt inputs 与 one-run identity。
- [x] routed shard runner 在加载测试前拒绝 missing／forged／stale／expired／consumed／wrong-stage／budget-mismatch
  lease；opt-in Promotion lane 只接受 integration-owned lease。Direct unittest 仍只是 local debugging。
- [x] 同 Workstream+scope+surface+stage 一次正式运行；成功的 unchanged request 返回 prior receipt。失败／timeout
  进入 `validation-cost-blocked`，只有绑定 request/revision/CAS 的 human maintainer override 可重跑。
- [x] `iterating` 只允许 non-evidence focused stage，≤20 tests、≤20s/run、≤120 cumulative seconds/scope；
  experience gate 未 accepted 前不能进入 Fast/Checkpoint。

### Predictive cost, profiles and integration

- [x] valid receipt 驱动 Git-private per-test/environment p95 summary；unknown history 如实为 Unknown 并在 enforcement
  下保守拒绝。Fast 在 count>20 或 total p95>10s 时 preflight refusal；Checkpoint 在 single>30s 或 total>60s
  时 refusal，不改变 15／90 秒 stage budget。
- [x] prediction 与 cumulative cost 包含 router、runner setup/build、run、retry/optimization cost；节省与投入仍
  同时展示，且不成为 ROI gate。
- [x] 提供 UI experience、deterministic contract、measurement、migration/deletion/release operation、platform
  matrix 与 mixed all-of 的 versioned data profiles；review package 限 purpose/invariants、3–5 representative
  cases、negative cases、known gaps、contract/fingerprint 与 reproduction ref。
- [x] Integration 只消费 child receipt refs 并重跑 integration-owned gates；child gate replay 失败关闭。完整
  docsite、real-Git multi-repository、package/release build 与 matrix 不进入无关 UI iteration。

### Validation and rollout

- [x] focused contract 覆盖 legacy shadow、human/mechanical authority、mixed all-of、five kinds、freshness、Team
  privacy、lease lifecycle/no-repeat/override、predictive limits、95 秒 Maintenance、integration replay 与 guard。
- [x] policy 稳定后只运行一次 routed Fast 和一次 routed Checkpoint；Fast 对 42>20 在 test loading 前 refusal，
  Checkpoint 42/42 PASS；同 fingerprint 未重试，Checkpoint 未替代 Fast。
- [x] clean Candidate 的 repository/static/diff gates 与 Promotion inventory/lane/required-check 等价已记录到
  Validation；完整 Promotion 不作为本地开发循环。
- [ ] hosted/public enforcement 继续为独立维护者决定；中央整合后 push exact non-main SHA 并取得 Windows／
  Ubuntu required checks，根 PROGRESS/HANDOFF 只由唯一整合者更新。
