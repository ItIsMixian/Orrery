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
- 现有测试覆盖若干 authority invariants，但尚未形成跨 CLI／Viewer／AI／Coordinator 的统一 conformance fixture 套件。

## 当前边界

- Accepted ADR-0009 与 Approved Design 不等于 Authority Meta Model 已经代码化。
- AI Q&A、观测台和其他派生视图继续没有事实权威。
- AUTH-1 产品核心定位与 AUTH-4 单一 semantics owner 仍未决定。
- 未建立 Implementation Plan；下一次规划前不得以“落地 Meta Model”为名重构 Observatory 或提升 Core／document schema 版本。

## 实现证据

- `docs/decisions/0009-authority-meta-model-and-semantic-conformance.md`
- `docs/design/authority-meta-model.md`
- `docs/core/principles.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/decisions/0004-platform-neutral-core-and-adapter-boundaries.md`

## 已知缺口

- 没有机器可读 domain model、version manifest、parser contract 或 conformance CLI。
- 没有盘点各消费者中重复／漂移的 authority 判断。
- 没有 conformance fixture、迁移策略、发布计划或 runtime Validation。
- 没有决定 Meta Model 最终由哪个包拥有。
