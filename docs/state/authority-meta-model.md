# Authority Meta Model State

Updated: 2026-08-21

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)

Approved Design: [Authority Meta Model 语义设计](../design/authority-meta-model.md)

## 当前事实

- Project Orrery 已正式区分 Authority Meta Model、项目 Authority Instance 和 Implementation／external state。
- Meta Model 已规范角色、非线性 Authority Graph、独立 claim dimensions、Authority scopes、provider-neutral evidence categories、derived-view constraints 和 conformance 输入边界。
- `docs/core/principles.md` 仍是 Project Orrery Product Seed，不是通用 machine-readable Meta Model。
- 当前语义仍分布在 ADR、Design、模板、Python 工具、Viewer 和 Agent 指令中；尚无独立 parser／domain object、公共 Meta Model API 或可声明的单一 implementation owner。
- 当前 project／release manifest 没有正式 `authority_model_version` 字段；ADR-0009 只要求语义必须可版本识别，具体 schema 与迁移尚未设计。
- Candidate 分支已建立 `amm-fixture-v1` versioned conformance fixture：21 个案例冻结四项输入、独立 claim dimensions、lifecycle/relations、全部 fact scopes、evidence 能力边界、AI non-escalation、Snapshot 与 Coordinator 分离，以及 determinism/visibility comparison；专项测试为 9/9 通过。
- ADR-0010 已决定由平台中立 Core 持有唯一确定性 evaluator；Candidate 分支中的 `project_orrery_core.authority` 已能把 normalized observations 与四项 conformance 输入解释为 claims/relations/scope/evidence 边界，21 个 fixture case 的 shadow expectation 全部满足，额外输出均由 fixture policy 显式分类，专项为 14/14。
- Candidate CLI 已增加第一处真实 consumer 双轨：`authority_shadow.py` 保留原 validator 的 Accepted ADR／入口／pending／integrated 扫描为生产决定路径，同时把 Accepted ADR observation、精确 authority-input snapshot hash、显式 `Unknown` scope 与 revision-content visibility 送入 Core evaluator；差异只按 `parser-gap` 警告，不改变原退出码或 authority status。
- 当前 evaluator 是 experimental、fixture-bound 的 Candidate implementation：CLI 也只完成 Accepted ADR 这一维的 shadow comparison；没有稳定顶层 API、consumer production switch、公开 schema/manifest 字段或发布实现，也不是 Canonical State 的实现声明。

## 当前边界

- Accepted ADR-0009 与 Approved Design 不等于 Authority Meta Model 已经代码化。
- AI Q&A、观测台和其他派生视图继续没有事实权威。
- AUTH-1 产品核心定位与 AUTH-4 单一 semantics owner 仍未决定。
- Decision Gate A 已由 ADR-0010 解决；Decision Gate B 仍未决定公开版本字段与兼容契约。
- 在 Gate B 通过前，不得提升 Core／document schema 版本、新增公开契约字段，或把 experimental module 宣称为稳定 API。

## 实现证据

- `docs/decisions/0009-authority-meta-model-and-semantic-conformance.md`
- `docs/design/authority-meta-model.md`
- `docs/core/principles.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/decisions/0004-platform-neutral-core-and-adapter-boundaries.md`
- `docs/decisions/0010-core-owned-authority-evaluator.md`
- `docs/implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md`（Candidate Plan；仅记录拟议路径与区域级盘点）
- `tests/fixtures/authority-meta-model/v1/conformance.json`（Candidate golden contract）
- `tests/test_authority_meta_model.py`
- `docs/validation/2026-08-21-authority-meta-model-fixture-baseline.md`
- `packages/project-orrery-core/src/project_orrery_core/authority.py`（Candidate experimental evaluator）
- `docs/validation/2026-08-21-authority-meta-model-core-shadow-evaluator.md`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_shadow.py`（Candidate CLI shadow adapter）
- `packages/project-orrery-cli/src/project_orrery_cli/validate.py`（legacy production path + warning-only comparison）
- `tests/test_authority_cli_shadow.py`
- `docs/validation/2026-08-21-authority-meta-model-cli-shadow.md`

## 已知缺口

- 没有机器可读 domain model、version manifest、parser contract 或 conformance CLI。
- 仅有区域级盘点；尚未形成逐函数／逐规则的 machine-readable inventory 或 drift 判定。
- CLI shadow 当前只比较 `accepted_adr`；`entrance_mapped`、`pending_marker` 与 `integrated` 仍被明确标为 legacy adoption heuristics，尚未进入 Meta Model evaluator。
- CLI 尚未解析完整 ADR lifecycle／supersede／amend、Implementation／State／Validation 或 evidence provenance；Observatory 也尚无双轨差异报告。
- 尚无 consumer production switch、公开语义版本字段、发布计划或 Canonical runtime Validation。
- Fixture 与 Core evaluator 目前只在 Candidate worktree 中；尚未经干净 integration worktree 合并为 Canonical baseline。
- Normalized observation collector/parser contract 尚未稳定；当前 evaluator 不读取作者 Markdown 或 Git/Harness 原始输出。
