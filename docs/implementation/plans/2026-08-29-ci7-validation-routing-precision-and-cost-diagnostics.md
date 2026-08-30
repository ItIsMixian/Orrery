# 实施计划：CI7 Validation Routing Precision & Total-Cost Diagnostics

Status: Original Candidate `a520ebc` retained; reopened for maintainer-approved acceptance gates and validation leases

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

- [ ] 将宽 `observatory-ui` 数据映射拆成稳定、可复用的 `observatory-shell`、`observatory-graph`、
  `observatory-maintenance` 与 `observatory-team-personal` surface；不得包含 task ID 或 branch 名。
- [ ] 以实际 changed paths 为首要输入；Git-private subsystem 只在没有路径证据时保守 fallback。
- [ ] expected writes 必须是精确文件或受支持的窄 glob；目录级宽声明生成 refusal／required metadata，不能扩大
  正式选择面。
- [ ] Graph presentation 变化不选择 Maintenance Git fixture；Maintenance provider／Quick Remove 变化仍选择其
  当前安全门；Unified common security 变化选择所有受影响 consumer 的小型 adjacency。
- [ ] 保持 Promotion inventory 每个 final unittest ID 恰好一次，完整 Windows／Ubuntu覆盖不变。

## Phase 2 — total validation cost diagnostics

- [ ] 在 receipt 中增加纯诊断 `cost_diagnostics`，至少机械记录：selected test count、test runtime、router/setup
  wall time、rerun count、slow IDs、修改的 test/CI 文件数与行数、是否由独立 optimization Workstream 产生。
- [ ] 可获得宿主 usage 时记录真实 Agent/tool usage；不可获得时写 `unknown`，不得估算或伪造 token。
- [ ] 允许维护者提供 advisory `expected_future_runs`，CLI 计算简单 break-even 次数；该值不成为 PASS／FAIL、
  Authority、release 或自动任务创建依据。
- [ ] Validation 同时报告测试节省和优化投入；只展示“最终快了多少”不能称为整体效率改进。

## Phase 3 — feature-task stop and central triage

- [ ] over-budget receipt 明确区分：产品 test failure、router over-selection、fixture/runtime variance 与真正慢路径。
- [ ] feature task 默认停止并回报；中央可选择重新路由、建立独立 CI task 或继续保持 blocked，不得要求功能
  Agent 自行追绿。
- [ ] 第一次偶发超时只保留证据；同一瓶颈第二次影响独立 Workstream 时生成 advisory recurrence finding。
- [ ] finding 只属于 Git-private／Validation 诊断，不自动形成 ADR、State、关系事实或执行任务。

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

The original CI7 Candidate `a520ebc74a0846c148e73312ea2fbf2a32b4b08b` successfully split broad Observatory
surfaces and added total-cost diagnostics, but real W7.3 iteration still spent most of a 53-minute task on repeated
cross-module tests, full builds and unchanged-source retries before the maintainer accepted the UI. The maintainer
therefore approves mechanical phase/gate enforcement. This amendment preserves what Fast／Checkpoint／Candidate／
Promotion prove, their 15／90 second budgets, exact-SHA Promotion and required checks; it controls when a stage may
start and which evidence unlocks it.

This remains CI7 rather than a new ADR because it reuses current Workstream lifecycle, human authority, Git-private
receipts and CI6 stage semantics. If implementation needs Agent self-acceptance, remote authorization, stage
substitution, budget waiver or a change to release authority, stop for a new ADR.

### Acceptance policy v1

- [ ] Add an additive, versioned `acceptance_policy` with a composable `acceptance_gates` array. Do not use one
  mutually exclusive `acceptance_mode`; mixed tasks may require several gates.
- [ ] Each gate includes stable `id`, `kind`, `required_before`, `authority_role`, exact `contract_ref` path + blob OID,
  relevant surface IDs, status, evidence requirements and receipt reference. Initial kinds are
  `human_experience`, `contract`, `measurement`, `operation_authorization` and `platform_matrix`.
- [ ] Multiple gates use `all_of` only in v1. `any_of`, weighted voting and Agent-selected gate omission are not
  supported. Unknown kind/status remains Unknown and cannot unlock the requested stage.
- [ ] Gate status taxonomy is `proposed`／`ready`／`accepted`／`rejected`／`stale`／`unknown`. Human-experience and
  operation gates require the declared human role; Agent/session receipts cannot satisfy them. Contract,
  measurement and matrix gates may close mechanically only against a previously human-approved exact contract.
- [ ] Reuse the existing actor/role/revision/CAS/receipt envelope where compatible; do not create a second authority
  system or let validation receipts become ADR/State facts.

### Compatibility and receipt freshness

- [ ] Existing sessions without policy project as `legacy-unclassified` and retain current readable behavior during
  shadow rollout; no history bytes are rewritten and no bulk inference is allowed.
- [ ] New Workstreams created after opt-in enforcement must declare at least one gate. Migrating an active legacy
  task requires human-reviewed mapping; Agent suggestions remain non-authoritative.
- [ ] Bind acceptance to `surface_fingerprint`, not whole repository HEAD. The fingerprint covers exact contract blob,
  mapping registry version and relevant source/test paths; DEVLOG/Validation wording outside that surface cannot
  invalidate product acceptance.
- [ ] A relevant surface change, contract blob change, scope revision change or authority-role revocation makes the
  receipt stale. Unrelated branch commits do not.
- [ ] Personal remains zero-network and Team remains request-only. Team may project bounded gate metadata but cannot
  transmit Prompt, transcript, source, diff, credentials or raw private evidence.

### Validation lease and no-repeat enforcement

- [ ] `validate_change.py` issues a Git-private `validation_lease` only when required gates for the requested stage
  are satisfied. The lease binds Workstream ID, scope revision, stage, exact relevant fingerprint, allowed test IDs,
  selected count, predicted p95 cost, budget, receipt inputs and one run identity.
- [ ] Formal shard/lane runners refuse missing, stale, forged, stage-mismatched or over-budget leases before starting
  tests. Direct unittest remains local debugging only and cannot emit formal tier evidence.
- [ ] Same Workstream + surface fingerprint + stage may execute formally once. A previous receipt is returned for an
  unchanged request. Timeout/failure moves that stage to `validation-cost-blocked`; unchanged-source rerun requires a
  human-authorized override receipt, not a free-form Agent reason.
- [ ] In `iterating`, only mapping-owned focused tests are permitted: ≤20 selected tests, ≤20 seconds/run and ≤120
  cumulative seconds per scope revision before a new human review/contract transition. Human-experience tasks cannot
  run routed Fast/Checkpoint before an accepted experience receipt.
- [ ] Contract tasks may proceed without a second subjective pause when the exact contract was accepted before
  implementation and all machine evidence matches; operation gates still require action-time human authorization.

### Predictive budget refusal

- [ ] Maintain local, versioned timing summaries from valid receipts keyed by final test ID/environment. Unknown
  history is reported honestly and uses conservative selection; no model estimate becomes evidence.
- [ ] Refuse Fast before execution when selected count >20 or predicted p95 >10 seconds, preserving five seconds of
  budget headroom. Refuse Checkpoint when one test p95 >30 seconds or total predicted p95 >60 seconds; move such work
  to Candidate/Promotion or require a separate CI optimization decision instead of retrying.
- [ ] Router/setup/build time is included in prediction and cumulative Workstream cost. A test saving cannot be
  reported without the optimization, retry and setup cost already required by original CI7 diagnostics.
- [ ] Full docsite, real-Git multi-repository fixtures, package/release builds and cross-platform matrices are not part
  of UI/product iteration unless the accepted gate contract explicitly owns them.

### Profiles and review packages

- [ ] Provide versioned examples for UI experience, deterministic Core/CLI contract, measured performance, migration/
  deletion/release operation and platform matrix tasks. Profiles are data, never task-ID/branch switches.
- [ ] Each review package is bounded: user-visible purpose, invariants, 3–5 representative input/output or screenshots,
  negative cases, known gaps, exact contract/fingerprint and reproduction reference. Hundreds of raw test lines do
  not substitute for human-readable acceptance.
- [ ] Integration Workstream consumes valid child receipts and reruns only integration-owned gates. It cannot replay
  every child suite merely because aggregation occurred.

### Validation and rollout

- Shadow portfolios: legacy tasks unchanged; new policy emits diagnostics but no block.
- Enforced portfolios: visual task before/after human acceptance; pre-accepted Core contract; benchmark threshold;
  destructive operation authorization; Windows/Ubuntu matrix; mixed all-of task; unknown kind; stale receipt.
- Negative tests: Agent self-accept, missing role, forged contract/blob/fingerprint, unrelated doc change, relevant
  source change, duplicate run, timeout rerun, expired lease, direct heavy-run evidence claim and guard removal.
- Prove W7.3-style UI iteration selects only focused Graph tests before acceptance, then permits one Fast and one
  Checkpoint after the receipt. Prove a 95-second Maintenance fixture cannot enter a 90-second Checkpoint.
- Rollout order: shadow → new Workstreams required → explicit legacy adoption. Public/default/release activation and
  hosted enforcement remain separate maintainer decisions.

Continue the existing CI7 task/branch from clean `a520ebc74a0846c148e73312ea2fbf2a32b4b08b` using GPT-5.6 Sol
medium. Do not modify W7.3, CI7's root PROGRESS/HANDOFF, public release manifests, required check names or budgets.
During implementation use focused CI contract tests; run routed Fast/Checkpoint once only after the policy is stable.
