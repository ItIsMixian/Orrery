# Authority Meta Model State

Updated: 2026-08-21

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

Approved Design: [Authority Meta Model 语义设计](../design/authority-meta-model.md)

## 当前事实

- Project Orrery 已正式区分 Authority Meta Model、项目 Authority Instance 和 Implementation／external state。
- Meta Model 已规范角色、非线性 Authority Graph、独立 claim dimensions、Authority scopes、provider-neutral evidence categories、derived-view constraints 和 conformance 输入边界。
- `docs/core/principles.md` 仍是 Project Orrery Product Seed，不是通用 machine-readable Meta Model。
- 当前语义仍分布在 ADR、Design、模板、Python 工具、Viewer 和 Agent 指令中；Candidate 已有内部 lifecycle/relation collectors 与 Core evaluator，但尚无公共 parser／domain API 或稳定 Meta Model API。
- ADR-0011 已正式定义 project 顶层可选正整数 `authority_model_version`、release 默认值与离散支持集、legacy／unknown 失败关闭和显式语义迁移边界。self-host `.project-orrery.json` 已经维护者授权显式选择模型 `1`；当前公开 release manifest、installer 与新 scaffold 尚未投影该字段，旧项目继续是 `legacy-unversioned`。
- Candidate 分支已建立 `amm-fixture-v1` versioned conformance fixture：21 个案例冻结四项输入、独立 claim dimensions、lifecycle/relations、全部 fact scopes、evidence 能力边界、AI non-escalation、Snapshot 与 Coordinator 分离，以及 determinism/visibility comparison；专项测试为 9/9 通过。
- ADR-0010 已决定由平台中立 Core 持有唯一确定性 evaluator；Candidate 分支中的 `project_orrery_core.authority` 已能把 normalized observations 与四项 conformance 输入解释为 claims/relations/scope/evidence 边界，21 个 fixture case 的 shadow expectation 全部满足，额外输出均由 fixture policy 显式分类，专项为 14/14。
- Candidate CLI 已增加第一处真实 consumer 双轨：`authority_shadow.py` 保留原 validator 的 Accepted ADR／入口／pending／integrated 扫描为生产决定路径，同时把 Accepted ADR observation、精确 authority-input snapshot hash、显式 `Unknown` scope 与 revision-content visibility 送入 Core evaluator；差异只按 `parser-gap` 警告，不改变原退出码或 authority status。
- Candidate Observatory 包的未导出 parser shadow adapter 已覆盖 ADR lifecycle 和显式关系：它只把头部 `Amends:`／`Supersedes:` 与 `Status: Superseded by …` 规范化为 Core observations，后者会反转为“新 ADR supersedes 旧 ADR”；`Predecessor`、正文普通引用和 State 引用不进入规范关系。
- 真实仓库的 6 条 `Amends` 已与 Core relations 一致；合成测试也证明 supersede 会选出 effective decision、amend 会保留 base 与 amendment、缺少 ADR target 的显式关系会失败关闭。旧 build/serve 图谱没有切换，legacy `supersedes` 字段仍只表示 superseded-by target。
- Candidate Observatory 另有未导出的 role shadow adapter，按受控目录观察 Design／Plan／State／Validation：Design 只识别 Draft／Approved／Deprecated；Plan 只产生 `planned`，State 只产生 `current`，两者都不产生 implementation claim；Validation 只有精确 `Result: Passed/Failed` 或 `Outcome:` 才产生明确结果，文档存在、`Status:` 与自由文本保持 `Unknown`。
- Candidate Observatory 现有未导出的 runtime bridge：它先调用真实 legacy `render_site()`，再对同一 docs snapshot 运行 ADR 与 role shadow，返回独立 report；专项证明 HTML 字节、legacy stats 与失败路径均不被 experimental evaluator 改写。
- Candidate managed `build_docsite.py` 与 `serve.py` 已增加默认关闭的内部运行时接线：只有维护者显式设置 `ORRERY_AUTHORITY_SHADOW_REPORT` 才会调用该 bridge 并原子写入 disposable JSON sidecar；缺省运行继续精确走 legacy renderer，非法 scope、缺失 package、manifest／evaluator 或 sidecar 写入失败都不切换 HTML、stats 或服务启动权威。
- Candidate AI 派生视图已消费这一可选 sidecar 的压缩 context：Q&A、briefing、roadmap、milestones 与 radar 的成功／失败 JSON 都附带系统生成的 `derived-ai-view` 非权威 receipt，问答正文有可见说明，streaming response 有 view/status header。没有 report 时保持 `Unknown`／`unavailable`，只有 Candidate shadow 时保持 `shadow-only`；Local-only／Unknown 不得被推为 Canonical、源码事实、effective/current/implemented/validated。该边界阻止 AI 输出在系统中升级权威，不保证模型自然语言本身永不出错。
- 当前仓库 shadow 输入包含 7 个 Design、12 个 Plan、6 个 State 和 37 个 Validation；现有 Validation 的严格结果全部保持 `Unknown`，因此不会因旧自然语言记录误报验证通过。该结果只表示严格 collector 的 Candidate 输出，不否定各 Validation 正文中的人工证据。
- 当前 evaluator 是 experimental、fixture-bound 的 Candidate implementation：CLI 已有 Accepted ADR 运行时 shadow和只读 model capability report，Observatory 已完成包级 ADR lifecycle/relation/role、runtime bridge、内部 status signal、opt-in managed shadow sidecar 与 AI derived-view non-escalation；没有稳定顶层 API、默认启用的 managed Authority projection、consumer production switch、公开 release/installer projection 或发布实现，也不是 Canonical State 的实现声明。
- Gate B 已由 [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md) 解决。9-case `compatibility.json` 覆盖 field absent、public model 1、known unsupported、unknown newer、数值 gap、离散 model 3 和三类非法值，并冻结普通工具升级不得选择模型、manifest/document schema 不随首版模型变化。
- Candidate Core 内部 `authority_compatibility.py` 已实现 provider-neutral capability judgment：显式区分 `legacy-unversioned`、`supported`、`unsupported-known`、`unsupported-newer`、`unsupported-unknown` 与 `invalid`；不支持时只保留 read-only browsing，并禁止推导 effective/current/implemented/validated。`eligible` 只表示可进入严格 conformance 评估，不表示验证已经通过。
- Neutral CLI validator 已消费该 Core judgment，向人类与稳定 JSON 合约只读报告 `authority_model` capability：legacy 在普通验证中警告、在 `--require-integrated` 中失败；unsupported／invalid 始终失败关闭。顺带修复 Authority shadow 警告混入字符串、破坏 JSON issue contract 的缺陷。
- Candidate Core 内部 migration planner/materializer 与 neutral CLI 0.1.3 `migrate-authority-model` 已实现。dry-run 对 legacy→model 1 报告唯一 manifest 字段写入、备份范围与保持不变的 manifest/document schema；apply receipt 同时绑定源 manifest hash、目标模型与提议 manifest hash，过期／换目标会在备份前失败。真正 apply 先逐字节备份，再通过同目录临时文件原子替换；已选择 model 1 返回 no-op，invalid／unsupported／正交版本不兼容／没有显式跨版本路径的请求失败关闭。
- Candidate neutral CLI 0.1.4 `restore-authority-model` 已把迁移备份提升为显式恢复路径。它只接受当前项目 `.project-orrery-backup/authority-model/<generated>/.project-orrery.json` 下的普通文件，拒绝绝对路径、`..`、文件 symlink、目录形状漂移和解析后的根外路径；当前 manifest 必须使用受支持模型，备份必须是 legacy 或同一受支持模型，且除模型选择器外所有字段必须一致。
- restore dry-run receipt 绑定当前 manifest hash、规范化项目内备份路径与备份 hash；apply 前另把当前 bytes 保存到 `authority-model-restore` 撤销目录，再原子替换为精确备份 bytes。current／backup 任一变化、外部或过期备份、unsupported／invalid／正交版本和无关字段差异均在写入前失败关闭；no-op 不创建撤销备份，注入 replace failure 时当前文件不变且撤销备份保留。
- Candidate `amm-release-projection-v1` 已冻结 future release 的默认模型 1 + 离散 `[1]` 支持集、project manifest/schema 正交和旧项目不自动选择模型。Core `ReleaseContract` 拒绝缺失配对、默认值不在支持集、重复／非法支持集；project manifest v1 schema 允许但不要求正整数 `authority_model_version`。
- Core scaffold 只在 manifest 真正不存在／为空且 release 声明有效默认模型时写入该字段；已有 manifest 无论字段存在或缺失都保持原选择。隔离 `--upgrade-tools` 回归证明 legacy 缺字段不会被普通工具升级变成 model 1；当前 source/bundled v0.2.0 release contracts 继续不声明模型，不被本检查点改写。
- Candidate neutral CLI 0.1.5 `check-update` 已只读消费 future release 的默认值／离散支持集：显式 model 1 target 可直接通过，legacy、invalid 和 unsupported target 返回既有 migration-review 状态与原因；无 target 的 Skill-only 查询不推断项目迁移。v0.2.0 因没有模型声明而保持原更新判断，JSON response schema 未增加字段。
- Candidate Observatory runtime bridge 已增加 display-neutral 模型状态信号；supported 可继续 shadow，legacy／unsupported 只返回原 legacy HTML/stats 与只读警告，不运行确定性 Authority shadow。该信号可写入显式 opt-in sidecar，但尚未接入 managed 页面或服务 API。

## 当前边界

- Accepted ADR-0009 与 Approved Design 不等于 Authority Meta Model 已经代码化。
- AI Q&A、观测台和其他派生视图继续没有事实权威。
- AUTH-1 产品核心定位仍未决定；AUTH-4 单一 deterministic evaluator owner 已由 ADR-0010 决定为平台中立 Core。
- Decision Gate A 已由 ADR-0010 解决；Decision Gate B 已由 ADR-0011 解决。
- Gate B 通过不等于发布实现完成：不得在缺少 manifest projection、显式 migration dry-run、旧项目与发布验证时改变 installer／release 默认值，也不得把 experimental module 宣称为稳定 API。

## 实现证据

- `docs/decisions/0009-authority-meta-model-and-semantic-conformance.md`
- `docs/design/authority-meta-model.md`
- `docs/core/principles.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/decisions/0004-platform-neutral-core-and-adapter-boundaries.md`
- `docs/decisions/0010-core-owned-authority-evaluator.md`
- `docs/decisions/0011-authority-model-version-and-compatibility.md`
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
- `packages/project-orrery-observatory/src/project_orrery_observatory/authority_shadow.py`（Candidate、未导出的 parser adapter）
- `tests/test_authority_observatory_shadow.py`
- `docs/validation/2026-08-21-authority-meta-model-observatory-parser-shadow.md`
- `docs/validation/2026-08-21-authority-meta-model-observatory-relation-shadow.md`
- `packages/project-orrery-observatory/src/project_orrery_observatory/authority_role_shadow.py`（Candidate、未导出的 role adapter）
- `packages/project-orrery-observatory/src/project_orrery_observatory/runtime_shadow.py`（Candidate、未导出的 runtime bridge）
- `tests/test_authority_observatory_roles_shadow.py`
- `tests/test_authority_observatory_runtime_shadow.py`
- `docs/validation/2026-08-21-authority-meta-model-observatory-role-shadow.md`
- `docs/validation/2026-08-21-authority-meta-model-observatory-runtime-shadow.md`
- `tests/fixtures/authority-meta-model/v1/compatibility.json`（Candidate compatibility golden contract）
- `packages/project-orrery-core/src/project_orrery_core/authority_compatibility.py`（Candidate internal capability judgment）
- `tests/test_authority_model_compatibility.py`
- `tests/test_authority_cli_compatibility.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/authority_model_status.py`（未导出的 status projection）
- `docs/validation/2026-08-21-authority-model-compatibility-candidate.md`
- `docs/validation/2026-08-21-adr-0011-authority-model-compatibility-integration.md`
- `packages/project-orrery-core/src/project_orrery_core/authority_migration.py`（Candidate internal、read-only planner）
- `packages/project-orrery-cli/src/project_orrery_cli/authority_migrate.py`（Candidate dry-run-only CLI）
- `tests/test_authority_model_migration.py`
- `docs/validation/2026-08-21-authority-model-migration-dry-run.md`
- `docs/validation/2026-08-21-authority-model-migration-apply.md`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_restore.py`（Candidate restore CLI）
- `tests/test_authority_model_restore.py`
- `docs/validation/2026-08-21-authority-model-restore.md`
- `tests/fixtures/authority-meta-model/v1/projection.json`
- `packages/project-orrery-core/src/project_orrery_core/manifests.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/project-manifest-v1.json`
- `tests/test_authority_model_projection.py`
- `docs/validation/2026-08-21-authority-model-release-projection.md`
- `packages/project-orrery-cli/src/project_orrery_cli/update.py`
- `tests/test_authority_update_compatibility.py`
- `docs/validation/2026-08-21-authority-model-update-compatibility.md`
- `tests/test_authority_observatory_managed_shadow.py`
- `docs/validation/2026-08-21-authority-model-managed-observatory-shadow.md`
- `scripts/docsite/docsite_qa.py` 与 `scripts/docsite/serve.py`（Candidate AI derived-view guard／receipt）
- `tests/test_authority_ai_derived_view.py`
- `docs/validation/2026-08-21-authority-ai-derived-view-constraints.md`

## 已知缺口

- 没有公共 machine-readable domain API、version manifest 或 conformance CLI；当前 parser 与 compatibility contracts 仅是 Candidate 内部测试边界。
- 仅有区域级盘点；尚未形成逐函数／逐规则的 machine-readable inventory 或 drift 判定。
- CLI shadow 当前只比较 `accepted_adr`；`entrance_mapped`、`pending_marker` 与 `integrated` 仍被明确标为 legacy adoption heuristics，尚未进入 Meta Model evaluator。
- CLI 尚未解析完整 ADR lifecycle／supersede／amend、Implementation／State／Validation 或 evidence provenance。
- Observatory lifecycle/relation/role shadow 与 runtime bridge 已有 opt-in managed sidecar 接线，但默认关闭且完全不进入 HTML／stats；`predecessors`、普通 ADR refs 与 State refs 仍明确属于 legacy graph/reference heuristics，页面 graph 尚未消费 Core effective-decision 或 role claim 结果。
- Role shadow 目前只解释文档角色与严格头部元数据，不验证 Validation 正文命令是否真正执行，也不从 State 自由文本推导 implementation present/absent。
- Runtime bridge 可由 Candidate package/test harness 或维护者显式环境开关调用；模板仅投影同一默认关闭的接线，在实际下一 release 与旧项目兼容完成独立验证前不默认启用，也不进入页面 authority projection。AI 已有非权威 context／receipt，但其语义仍受可见证据限制，不能替代确定性 evaluator 或人工审阅。
- Compatibility judgment 已接入 neutral CLI validator 的只读报告、`check-update` 的 future-release migration review 和 Candidate Observatory runtime bridge 的内部 status signal；future release/project projection contract 已进入 Core 与 fixture，但当前 v0.2.0 release manifest、standalone installer 和 managed Observatory banner 仍未声明模型。self-host 项目已显式选择模型 1，通用迁移已有 receipt-gated dry-run/apply/restore、精确备份与故障恢复证据；尚无实际下一 release 投影。
- 尚无 consumer production switch、公开 release／installer 模型投影或 Canonical runtime release Validation；Harness JSON Adapter v1 也尚未暴露迁移命令。
- Fixture 与 Core evaluator 目前只在 Candidate worktree 中；尚未经干净 integration worktree 合并为 Canonical baseline。
- Normalized observation collector/parser contract 尚未稳定；当前覆盖 ADR lifecycle、显式 amend/supersede 和四类文档 role metadata，但 evaluator 仍不读取作者 Markdown 或 Git/Harness 原始输出。
