# Authority Meta Model State

Updated: 2026-08-21

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

Approved Design: [Authority Meta Model 语义设计](../design/authority-meta-model.md)

Active Plan: [一致性基线与渐进提取](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)

## 当前事实

- Project Orrery 已正式区分 Authority Meta Model、项目 Authority Instance 和 Implementation／external state。Meta Model 定义 authority roles、各对象 lifecycle、独立 claim dimensions、关系、事实作用域、provider-neutral evidence categories、derived-view constraints 和语义版本；它不是新的作者文档类型，也不覆盖项目自己的 Seed 内容。
- 规范不变量包括 `Accepted ≠ Implemented ≠ Validated`、`planned ≠ current`、`historical ≠ effective` 和 `observed ≠ authoritative`。Decision、Implementation 与 Validation 是相关但独立的 claim dimensions，不组成单一线性状态机。
- self-host 项目已在 `.project-orrery.json` 显式选择 `authority_model_version: 1`。当前公开 v0.2.0 release manifest、installer 与旧项目仍是 `legacy-unversioned`；普通工具升级不会替项目选择模型。
- Authority 实现代码已经进入本地 `main` 的 Canonical Git baseline，但其产品支持状态仍是 `experimental`／`unreleased`。Canonical source scope、runtime support status 与 public release status 必须分别表达。

| 层 | 当前能力 | 当前默认与边界 |
|---|---|---|
| Versioned semantics | `amm-fixture-v1` 冻结角色、claim、lifecycle／relation、scope、evidence、Snapshot／Coordinator 分离和 AI non-escalation 行为 | 模型 1 是目前唯一公开语义值；fixture ID 不是公共模型版本 |
| Core | 唯一确定性 evaluator 能解释 normalized observations；内部兼容判断、release contract、迁移／恢复规划与 materialization 已实现 | 尚无稳定公共 domain API；evaluator 不直接解析作者 Markdown、Git 或 Harness 原始输出 |
| CLI | 内部 `cli-authority-observations-v1` 能收集所有文档角色、source hash、repository snapshot、ADR lifecycle／relations、claims 与 evidence provenance；validator 和 update checker 可只读报告模型能力 | 仍嵌在 warning-only shadow／内部合约中；legacy adoption heuristics、退出码和普通升级行为没有切换 |
| Observatory | 包级 parser／relation／role shadow、runtime bridge、模型状态信号与 AI non-escalation receipt 已实现；M2.2 可投影完整 reconciled CLI bundle | 默认 legacy 页面不变；完整 Authority projection 仅由根 `build_authority_projection.py` 显式 opt-in，未进入发布模板或 managed production consumer |
| Migration／restore | receipt 绑定 source／target／proposal，项目内精确备份、原子替换、恢复撤销与 stale／symlink／traversal 失败关闭已有验证 | 只处理显式语义迁移；Harness JSON Adapter 尚未暴露迁移命令 |
| Release gate | M2.3 可验证维护者提供的模型 1 candidate manifest、确定性 staging archive、新建／legacy upgrade、迁移／恢复和安全边界 | gate 不选择版本，不改写 v0.2.0 历史资产；当前 `candidate_ready` 不等于 `release_ready` |

## 当前边界

- Accepted ADR-0009／0010／0011、已实现代码和已通过验证仍不等于默认 production consumer 已切换或模型 1 已公开发布。
- M2.2 的完整 projection 只存在于 root-only self-host 入口；legacy／unsupported model、collector／evaluator／source／reconciliation／render failure 都关闭回无 claim 的 legacy 页面。
- AI Q&A、briefing、roadmap、milestones 和 radar 只能消费受约束的派生 context，并保留 `Unknown`／Local-only；它们不能产生 State、ADR、批准或 Validation 事实。
- Validation 文档的存在、`Status:` 或自由文本不自动构成 executable evidence。严格 collector 无明确结构化证据时保持 `Unknown`，不否定文档中的人工陈述。
- Authority scope 只描述 claim 的 revision／branch／worktree／visibility context；Agent ownership、任务等待和文件 lock 属于 Coordinator runtime，不进入 Meta Model。
- AUTH-1“是否把 Authority／当前有效性正式声明为最主要产品核心”仍待维护者决定；AUTH-4 已由 ADR-0010 解决为平台中立 Core。

## 实现证据

- **规范与 fixture：** [Approved Design](../design/authority-meta-model.md), `tests/fixtures/authority-meta-model/v1/`
- **Core：** `packages/project-orrery-core/src/project_orrery_core/authority.py`, `authority_compatibility.py`, `authority_migration.py`, `manifests.py`
- **CLI：** `packages/project-orrery-cli/src/project_orrery_cli/authority_observations.py`, `authority_shadow.py`, `authority_migrate.py`, `authority_restore.py`, `validate.py`, `update.py`
- **Observatory：** `packages/project-orrery-observatory/src/project_orrery_observatory/authority_projection.py`, `authority_shadow.py`, `authority_role_shadow.py`, `runtime_shadow.py`, `authority_model_status.py`
- **Managed self-host integration：** `scripts/docsite/build_authority_projection.py`, `scripts/docsite/build_docsite.py`, `scripts/docsite/serve.py`, `scripts/docsite/docsite_qa.py`
- **Release gate：** `packaging/authority-release-candidate-policy.json`, `scripts/authority_release_candidate_gate.py`
- **项目选择：** `.project-orrery.json`

## 验证证据

- [M2 本地 Canonical 集成](../validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)——合并后的 Authority／全仓回归、默认 legacy build、显式 projection、release gate、链接与 diff。
- [M1 本地 Canonical 集成](../validation/2026-08-21-authority-meta-model-canonical-integration.md)——fixture、Core owner、兼容、迁移／恢复、shadow 与 AI non-escalation 的干净集成。
- [M2.1 CLI claims](../validation/2026-08-21-m2-1-authority-cli-claims.md), [M2.2 Observatory projection](../validation/2026-08-21-m2-2-observatory-authority-projection.md), [M2.3 release gate](../validation/2026-08-21-m2-3-authority-release-candidate-gate.md)——各检查点的独立证据。
- 其余逐能力记录见 [Validation 索引](../validation/README.md)；State 不重复保存逐次测试历史。

## 已知缺口

- 没有稳定、公共、machine-readable 的 parser／domain API 或通用 conformance CLI；normalized observation contract 仍是内部边界。
- 没有逐规则 machine-readable inventory、跨消费者 drift 检测或从真实 Markdown／Git／Harness 到 normalized observations 的稳定公共管线。
- M2.1 bundle 仍未成为公共 report，legacy `entrance_mapped`、`pending_marker`、`integrated` heuristics 和退出码没有迁移。
- 默认 managed Observatory、legacy graph／stats 和发布模板尚未消费 Core effective decision／role claims；M2.2 只有 root-only opt-in production-candidate 证据。
- 维护者尚未选择实际下一 SemVer／candidate manifest；公开 release／installer 仍未声明模型 1，M2.3 `release_ready` 保持 false。
- Harness JSON Adapter 未暴露 Authority migration／restore；没有 Canonical runtime release Validation 或稳定 API 兼容承诺。
