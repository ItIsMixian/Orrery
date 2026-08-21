# Authority Meta Model State

Updated: 2026-08-21

Governing ADR: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md)

Approved Design: [Authority Meta Model 语义设计](../design/authority-meta-model.md)

## 当前事实

- Project Orrery 已正式区分 Authority Meta Model、项目 Authority Instance 和 Implementation／external state。
- Meta Model 已规范角色、非线性 Authority Graph、独立 claim dimensions、Authority scopes、provider-neutral evidence categories、derived-view constraints 和 conformance 输入边界。
- `docs/core/principles.md` 仍是 Project Orrery Product Seed，不是通用 machine-readable Meta Model。
- 当前语义仍分布在 ADR、Design、模板、Python 工具、Viewer 和 Agent 指令中；尚无独立 parser／domain object、公共 Meta Model API 或可声明的单一 implementation owner。
- 当前 project／release manifest 没有正式 `authority_model_version` 字段；ADR-0009 只要求语义必须可版本识别，具体 schema 与迁移尚未设计。
- Candidate 分支已建立 `amm-fixture-v1` versioned conformance fixture：21 个案例冻结四项输入、独立 claim dimensions、lifecycle/relations、全部 fact scopes、evidence 能力边界、AI non-escalation、Snapshot 与 Coordinator 分离，以及 determinism/visibility comparison；专项测试为 9/9 通过。
- 当前 Candidate 分支已形成区域级重复语义盘点与渐进提取计划；fixture 是 Gate A 前的共享 golden contract，不是 evaluator、consumer migration、公开 schema/API 或发布实现，也不是 Canonical State 的实现声明。

## 当前边界

- Accepted ADR-0009 与 Approved Design 不等于 Authority Meta Model 已经代码化。
- AI Q&A、观测台和其他派生视图继续没有事实权威。
- AUTH-1 产品核心定位与 AUTH-4 单一 semantics owner 仍未决定。
- 已完成 Candidate Plan 的 fixture-first checkpoint；Decision Gate A 仍未决定 implementation owner，Decision Gate B 仍未决定公开版本字段与兼容契约。
- 在 Gate A／B 通过前，不得以“落地 Meta Model”为名重构 Observatory、提升 Core／document schema 版本，或新增公开契约字段。

## 实现证据

- `docs/decisions/0009-authority-meta-model-and-semantic-conformance.md`
- `docs/design/authority-meta-model.md`
- `docs/core/principles.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/decisions/0004-platform-neutral-core-and-adapter-boundaries.md`
- `docs/implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md`（Candidate Plan；仅记录拟议路径与区域级盘点）
- `tests/fixtures/authority-meta-model/v1/conformance.json`（Candidate golden contract）
- `tests/test_authority_meta_model.py`
- `docs/validation/2026-08-21-authority-meta-model-fixture-baseline.md`

## 已知缺口

- 没有机器可读 domain model、version manifest、parser contract 或 conformance CLI。
- 仅有区域级盘点；尚未形成逐函数／逐规则的 machine-readable inventory 或 drift 判定。
- 尚无 Authority Meta Model evaluator、shadow comparison、consumer migration、公开语义版本字段、发布计划或 runtime Validation。
- Fixture 目前只在 Candidate worktree 中，是 test-only contract；尚未经干净 integration worktree 合并为 Canonical baseline。
- 没有决定 Meta Model 最终由哪个包拥有。
