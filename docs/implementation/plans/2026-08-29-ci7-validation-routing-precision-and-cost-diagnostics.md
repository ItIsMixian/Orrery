# 实施计划：CI7 Validation Routing Precision & Total-Cost Diagnostics

Status: Worktree Candidate implemented and locally validated; exact-SHA hosted Promotion remains central integration work

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

本分支已完成本地 contract／mutation、portfolio、正式 routed Fast／Checkpoint 与 repository gates；完整
Promotion 不作为开发循环运行。唯一剩余验收是中央整合后冻结并 push clean exact SHA，再取得 Windows／Ubuntu
required checks。该剩余项不改变本 Candidate 已实现的数据契约，也不授权本分支 push、main 或 release。
