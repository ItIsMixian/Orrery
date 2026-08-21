# 实施计划：M2.1 完整 CLI Authority observations／claims

Status: Worktree Candidate validated; integration pending

Date: 2026-08-21

Branch: `codex/m2-1-authority-claims`

Governing ADRs: [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../../decisions/0011-authority-model-version-and-compatibility.md)

Approved Design: [Authority Meta Model](../../design/authority-meta-model.md)

Parent Plan: [Authority Meta Model conformance and gradual extraction](2026-08-21-authority-meta-model-conformance-and-extraction.md)

State: [Authority Meta Model State](../../state/authority-meta-model.md)

## 目标

把 M1 中只比较 `accepted_adr` 的 CLI shadow 扩展为可审阅、可重复的 repository-level
Authority observation contract。CLI 必须确定性地观察 ADR lifecycle 与显式 amendment／supersession、
Design／Plan／State／Validation／Snapshot 角色，并把每条 claim 连接到精确 source、内容摘要、
fact scope 与 evidence category，再交给 Core evaluator 解释。

本检查点冻结的是内部 Candidate 输入／输出契约和验证证据，不是稳定公共 API，也不切换 legacy CLI
的 authority status、退出码或安装／发布行为。

## 硬边界

- Core 继续只解释 pre-normalized observations；Markdown 路径选择和解析留在 CLI adapter。
- 不从 State 自由文本或文件存在推导 implementation present／absent。
- Validation 文档中的自述结果必须保留来源与证据类别；没有可复现执行证据时不得升级为
  `validated`。
- `Predecessor`、正文普通 ADR 引用、State 引用和文件名相似性不成为 normative relation。
- 缺失 relation target、冲突 metadata、未知 lifecycle／scope／evidence 必须显式 Unknown 或失败关闭。
- legacy adoption heuristics（entrance mapping、pending marker、integrated candidate）继续是 production
  path；M2.1 只能报告 shadow difference，不能改变其结果。
- 不修改 Observatory 页面／runtime、managed projection、release manifest、installer、模板、
  `CORE_API_VERSION` 或组件公开支持声明；这些分别属于 M2.2／M2.3。

## Candidate contract

CLI collector 输出版本化的内部 bundle：

1. 精确 repository snapshot hash；
2. 每个可见 authority source 的相对路径、role、subject、内容 SHA-256 与 normalized observations；
3. Core 返回的 per-source claims、relations、scope 与 `must_not_infer`；
4. repository-level decision graph／effective-decision 结果；
5. unresolved relation、Unknown、parser failure 与 legacy-only heuristic 清单；
6. evidence provenance，明确区分 revision content、executable validation、trace、assertion 与 derived view。

同一 bytes、model、scope 和 visibility 必须产生逐值相同的 bundle。改变任一可见 authority source
必须改变 snapshot。非 authority 文档、README 与模板不得污染输入。

## 实现步骤

1. 在 CLI 包新增内部 repository collector，统一路径选择、header metadata、source identity 与 hash。
2. 覆盖 Seed、ADR、Design、Plan、State、Validation 和 Snapshot；保持 Implementation 为外部真值，
   没有结构化证据时不制造 observation。
3. 扩展 Core 内部 evaluator 的 observation validation／provenance 处理，同时保持 M1 fixture 输出兼容，
   且不导出顶层公共 API。
4. 让 `authority_shadow.py` 生成完整 Candidate bundle；旧 Accepted-ADR comparison 与 validator 行为保持。
5. 增加 fixture／专项测试，覆盖 lifecycle、relations、role claims、evidence visibility、Unknown、
   deterministic hash、非权威引用隔离和 legacy rollback。
6. 运行 Authority 专项、产品回归、全仓测试、集成结构、静态站、Markdown link 与 diff 检查。
7. 只同步本 subsystem State、Validation 与索引；根 `PROGRESS`／`HANDOFF`／`DEVLOG` 留给唯一整合者。

## 主要路径

- `packages/project-orrery-core/src/project_orrery_core/authority.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_observations.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_shadow.py`
- `packages/project-orrery-cli/src/project_orrery_cli/validate.py`
- `tests/fixtures/authority-meta-model/v1/cli-observation-contract.json`
- `tests/test_authority_cli_claims.py`
- `tests/test_authority_cli_shadow.py`
- `docs/state/authority-meta-model.md`
- `docs/state/test-coverage.md`
- `docs/validation/2026-08-21-m2-1-authority-cli-claims.md`

## 验收门

- fixture 与临时 repository 均证明完整 role/claim 覆盖和 deterministic output；
- explicit amend/supersede 方向、missing target 和 effective decision 与 Core 一致；
- Plan／State 不产生 implementation claim；Validation assertion 不冒充 executable evidence；
- legacy CLI 的文本／JSON status、退出码和 `integrated candidate` 判定保持兼容；
- shadow 失败或差异继续 warning-only 且可独立回滚；
- 默认 Observatory HTML、stats、managed runtime 与发布文件零修改；
- 完整验证通过后，本检查点最多称为 M2.1 Candidate validated，不称为 production-switched、released
  或 stable public API。
