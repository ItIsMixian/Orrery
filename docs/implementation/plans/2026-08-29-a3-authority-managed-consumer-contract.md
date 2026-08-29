# 实施计划：A3 Authority Managed Consumer Contract

Status: Active Worktree Candidate

Date: 2026-08-29

Workstream: `A3-authority-managed-consumer-contract`

Baseline: protected `main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`

Governing ADRs: [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../../decisions/0011-authority-model-version-and-compatibility.md)

Approved Design: [Authority Meta Model](../../design/authority-meta-model.md)

Parent Plan: [Authority Meta Model 一致性基线与渐进提取](2026-08-21-authority-meta-model-conformance-and-extraction.md)

## 目标

在 M2.1 内部 observation bundle、Core evaluator 与 M2.2 root-only projection 之上，增加一个
provider-neutral、versioned、machine-readable 的 managed consumer 选择、就绪和回滚契约。契约供后续
U1 unified shell 消费，但本 Workstream 不启用默认 consumer、不修改统一 Observatory UI，也不选择或
发布任何 SemVer、manifest、installer default、release asset 或 Adapter support status。

## Contract boundary

- Core 是 selection／readiness／rollback 的唯一确定性 owner；输入只包含已经收集和 reconciliation 后的
  bindings／health observations，不包含 Markdown parser、Git provider、UI 或 Coordinator runtime 规则。
- CLI 只读收集 self-host manifest、M2.1 bundle 和 M2.2 projection，然后输出稳定 envelope 内的 A3
  contract；不暴露完整 normalized observations、文档 claims 或未经决定的公共 domain API。
- `legacy` 是默认 selection。`shadow`、`candidate-projection`、`enabled`、`rollback` 和派生的
  `unavailable` 必须独立表达；selection 与 active consumer 分开，不能把 opt-in Candidate 误报为默认启用。
- `enabled` 只接受维护者显式选择，并要求模型、snapshot、scope、visibility、component versions、source
  hash、reconciliation hash 和 safety invariants 全部 ready。AI／Coordinator 选择始终失败关闭。
- unsupported model 或 preflight 不可用产生 `unavailable`；显式 rollback、drift、collector／evaluator／
  projection failure 或 partial render 产生 `rollback`。两者 active consumer 都必须是逐字节 legacy。
- rollout 只能先 stage 完整 managed page、验证 exact binding 与完整 render，再原子替换；任何失败丢弃
  staged output 并保留 legacy。不得出现 partial claim 页面。
- rollback 是确定性本地计划：不写作者文档、不联网、不修改 release／manifest，只恢复既有 legacy bytes。

## Versioned schema and bindings

新增 `authority-managed-consumer-v1` schema／fixture。每个 inspect／readiness contract 绑定：

1. public `authority_model_version` 与内部 evaluator model ID；
2. exact repository snapshot、fact scope 和 ordered evidence visibility；
3. collector、evaluator 和 projection contract versions；
4. exact source-set expected／observed hashes；
5. exact reconciliation expected／observed hashes；
6. ordered readiness blockers、requested/effective selection 与 active consumer；
7. content-addressed rollout／rollback plan hash 和明确的 offline/no-author-write/no-release-mutation guarantees。

同输入必须产生逐字段相同结果和 plan hash。hash 或 version drift 不能被近似匹配、AI 解释或
Coordinator state 覆盖。

## 实现范围

- `packages/project-orrery-core/src/project_orrery_core/authority_consumer.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/authority-managed-consumer-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_consumer.py`
- `packages/project-orrery-cli/src/project_orrery_cli/__main__.py`
- `tests/fixtures/authority-meta-model/v1/managed-consumer.json`
- `tests/test_authority_managed_consumer.py`
- 本 Plan 与独立 A3 Validation

共享 Authority State、Test Coverage State、DEVLOG、Validation 索引、PROGRESS 和 HANDOFF 留给唯一中央
整合者重放。本分支不修改 README／assets、maintenance、Personal／Team server/navigation、start scripts、
统一 Observatory UI、公开 release inputs 或 Adapter manifests。

## 验收矩阵

| 场景 | 通过条件 |
|---|---|
| legacy／shadow／candidate／enabled | selection、active consumer、readiness 与 switch authorization 分离且默认 legacy |
| rollback／unavailable | 所有失败保留 legacy；rollback plan 无网络、作者写入、release mutation |
| unsupported model | Authority claims unavailable，不能猜测其他模型 |
| collector／evaluator／projection version drift | ordered blocker + deterministic rollback |
| source／reconciliation drift | exact hash mismatch 阻断，不能 partial commit |
| partial render／projection failure | staged output 丢弃，legacy bytes 保持 |
| Unknown／Local-only | 不能进入 enabled |
| AI／Coordinator escalation | 即使其他输入全 green 也不能改变 selection |
| determinism | 相同输入 contract 与 rollout／rollback plan hashes 完全相同 |
| compatibility | 默认 legacy build bytes／stats／release template／v0.2.0 inputs 不变 |

## Fast → Checkpoint

Fast 先运行 A3 focused tests 与相邻 Authority projection／CLI suites。Checkpoint 再运行 Authority focused、
CI contract、integrated structure、isolated default legacy build、isolated explicit projection build、Markdown
links、forbidden tracked-artifact／secret scan、`git diff --check` 和 diff boundary review。

本 Workstream 完成后只提交 Candidate branch，不 push `main`、不发布。维护者仍需另行决定是否将
`enabled` 作为真实 managed default，并由后续 release Workstream 选择实际 SemVer／candidate manifest。
