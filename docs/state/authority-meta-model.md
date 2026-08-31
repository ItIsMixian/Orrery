# Authority Meta Model State

Updated: 2026-08-30

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md), [ADR-0019](../decisions/0019-portable-operating-rules-and-authority-route-preflight.md)

Approved Design: [Authority Meta Model 语义设计](../design/authority-meta-model.md)

Active Plan: [A4 Portable Operating Rules 与 Authority Route Preflight](../implementation/plans/2026-08-30-a4-portable-operating-rules-and-authority-route-preflight.md)

## 当前事实

- Project Orrery 已正式区分 Authority Meta Model、项目 Authority Instance 和 Implementation／external state。Meta Model 定义 authority roles、各对象 lifecycle、独立 claim dimensions、关系、事实作用域、provider-neutral evidence categories、derived-view constraints 和语义版本；它不是新的作者文档类型，也不覆盖项目自己的 Seed 内容。
- 规范不变量包括 `Accepted ≠ Implemented ≠ Validated`、`planned ≠ current`、`historical ≠ effective` 和 `observed ≠ authoritative`。Decision、Implementation 与 Validation 是相关但独立的 claim dimensions，不组成单一线性状态机。
- self-host 项目已在 `.project-orrery.json` 显式选择 `authority_model_version: 1`。当前公开 v0.2.0 release manifest、installer 与旧项目仍是 `legacy-unversioned`；普通工具升级不会替项目选择模型。
- Authority 实现代码已经进入本地 `main` 的 Canonical Git baseline，但其产品支持状态仍是 `experimental`／`unreleased`。Canonical source scope、runtime support status 与 public release status 必须分别表达。
- A4 local integrated Candidate 扩展既有 Meta Model：Core 0.1.18 冻结 `orrery-operating-rules-v1` inventory 与 provider-neutral Authority Route Preflight；CLI 0.1.22／Harness JSON 0.1.2 提供只读 inspect／route receipt，Skill source 消费同版本投影。它没有创建第二个语义层或 evaluator owner。
- U2.3 Worktree Candidate 不改变 Authority Core、collector、schema、fixture 或 claim 语义；它只把 A4 的项目原则／Orrery 工作规则／事实解释状态投影移入顶栏只读帮助 surface，并将 legacy/hash/rollout/rollback 保持为默认折叠的技术注释。该 surface 没有编辑、批准、启用、迁移或执行权。
- route receipt 独立输出 semantic/decision、implementation、distribution/consumer 与 public/default/release 四轴；novelty/absence claim 只有在有界 negative-evidence receipt 完整时才可成立。已索引 governing source 存在时，“不存在／全新层”断言被拒绝。

| 层 | 当前能力 | 当前默认与边界 |
|---|---|---|
| Versioned semantics | `amm-fixture-v1` 冻结角色、claim、lifecycle／relation、scope、evidence、Snapshot／Coordinator 分离和 AI non-escalation 行为 | 模型 1 是目前唯一公开语义值；fixture ID 不是公共模型版本 |
| Core | 唯一确定性 evaluator 继续解释 normalized observations；新增 versioned portable rules inventory、兼容／tamper 失败关闭、concept registry route evaluator、四轴 receipt 与 absence gate | Core 不读取仓库 Markdown／Git；collector 属于 CLI/Adapter；未知规则版本不静默采用最新版 |
| CLI／Harness | `operating-rules inspect/route` 从 AGENTS index、State、effective ADR/Design、实现/分发/发布证据生成只读 receipt；Harness JSON 暴露相同 shape | 不写目标项目、不提升 Authority 或 Release；source contract 仍是未发布 Candidate |
| Skill／Host | Skill source 先读同版本 operating rules 再读目标项目 AGENTS/Seed/State；root Unified Ask Docs 在模型检索前实际调用 CLI/Core preflight | 纯 SKILL.md 只能 advisory；没有 verified pre-model hook 的 Codex/Claude/DeepSeek 宿主不能宣称强制 |
| Observatory | 既有 `authority` route 重构为“事实与规则”：项目原则、Orrery 工作规则和折叠的事实解释状态分层投影 | 无第二导航；静态只读，动态不新增编辑/批准/执行权；仍未成为公开默认 consumer |
| Migration／restore | receipt 绑定 source／target／proposal，项目内精确备份、原子替换、恢复撤销与 stale／symlink／traversal 失败关闭已有验证 | 只处理显式语义迁移；Harness JSON Adapter 尚未暴露迁移命令 |
| Release gate | M2.3 可验证维护者提供的模型 1 candidate manifest、确定性 staging archive、新建／legacy upgrade、迁移／恢复和安全边界 | gate 不选择版本，不改写 v0.2.0 历史资产；当前 `candidate_ready` 不等于 `release_ready` |

## 当前边界

- Accepted ADR-0009／0010／0011、已实现代码和已通过验证仍不等于默认 production consumer 已切换或模型 1 已公开发布。
- ADR-0019 为 Accepted，A4 source 为本地 integrated Candidate；两者都不能冒充公开 v0.2.0 已包含 portable rules 或所有宿主已有强制 Hook。
- M2.2 的完整 projection 只存在于 root-only self-host 入口；legacy／unsupported model、collector／evaluator／source／reconciliation／render failure 都关闭回无 claim 的 legacy 页面。
- AI Q&A、briefing、roadmap、milestones 和 radar 只能消费受约束的派生 context，并保留 `Unknown`／Local-only；它们不能产生 State、ADR、批准或 Validation 事实。
- Validation 文档的存在、`Status:` 或自由文本不自动构成 executable evidence。严格 collector 无明确结构化证据时保持 `Unknown`，不否定文档中的人工陈述。
- Authority scope 只描述 claim 的 revision／branch／worktree／visibility context；Agent ownership、任务等待和文件 lock 属于 Coordinator runtime，不进入 Meta Model。
- AUTH-1“是否把 Authority／当前有效性正式声明为最主要产品核心”仍待维护者决定；AUTH-4 已由 ADR-0010 解决为平台中立 Core。

## 实现证据

- **规范与 fixture：** [Approved Design](../design/authority-meta-model.md), `tests/fixtures/authority-meta-model/v1/`
- **Core：** `packages/project-orrery-core/src/project_orrery_core/authority.py`, `operating_rules.py`, `authority_route.py`, `data/orrery-operating-rules-v1.json`, `schema/`
- **CLI／Harness：** `packages/project-orrery-cli/src/project_orrery_cli/operating_rules.py`, `adapters/harness-json/`
- **Skill：** `skills/project-orrery/SKILL.md`, `skills/project-orrery/references/orrery-operating-rules-v1.json`
- **Observatory／Ask Docs：** `packages/project-orrery-observatory/src/project_orrery_observatory/fact_rules_projection.py`, `unified_observatory.py`, `scripts/docsite/docsite_qa.py`, `serve_orrery.py`
- **Managed self-host integration：** `scripts/docsite/build_authority_projection.py`, `scripts/docsite/build_docsite.py`, `scripts/docsite/serve.py`, `scripts/docsite/docsite_qa.py`
- **Release gate：** `packaging/authority-release-candidate-policy.json`, `scripts/authority_release_candidate_gate.py`
- **项目选择：** `.project-orrery.json`

## 验证证据

- [M2 本地 Canonical 集成](../validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)——合并后的 Authority／全仓回归、默认 legacy build、显式 projection、release gate、链接与 diff。
- [M1 本地 Canonical 集成](../validation/2026-08-21-authority-meta-model-canonical-integration.md)——fixture、Core owner、兼容、迁移／恢复、shadow 与 AI non-escalation 的干净集成。
- [M2.1 CLI claims](../validation/2026-08-21-m2-1-authority-cli-claims.md), [M2.2 Observatory projection](../validation/2026-08-21-m2-2-observatory-authority-projection.md), [M2.3 release gate](../validation/2026-08-21-m2-3-authority-release-candidate-gate.md)——各检查点的独立证据。
- 其余逐能力记录见 [Validation 索引](../validation/README.md)；State 不重复保存逐次测试历史。
- [A4 Portable Operating Rules 与 Authority Route Preflight](../validation/2026-08-30-a4-portable-operating-rules-and-authority-route-preflight.md)——inventory、route corpus、Skill/CLI/Harness/Ask Docs/UI、安装非覆盖与 Candidate 验证。
- [U2.3 Navigation & Live Task Visibility](../validation/2026-08-30-u2-3-navigation-live-task-visibility.md)——Authority 只读帮助 surface 与产品权限边界；未修改 Core 语义。

## 已知缺口

- A4 inventory、route receipt 与 CLI 仍是 source-only/unreleased；没有稳定公共 domain API 或公开兼容承诺。
- CLI collector 当前只覆盖有界 self-host index/State/ADR/Design/implementation/distribution/release 路径；任意第三方项目的通用 Markdown/Git collector 仍未成为稳定公共管线。
- M2.1 bundle 仍未成为公共 report，legacy `entrance_mapped`、`pending_marker`、`integrated` heuristics 和退出码没有迁移。
- root Unified Authority/Ask Docs 已消费 A4 projection/preflight；公开默认 docsite、v0.2.0 资产和所有 Agent 宿主仍未消费。
- v0.3.0 Worktree Candidate manifest 已选择 Authority Model 1 离散支持集，新项目 scaffold 会记录模型 1；
  公开 v0.2.0、既有项目和默认 public consumer 未改变，M2.3/public `release_ready` 仍为 false。
- Harness JSON Adapter 未暴露 Authority migration／restore；没有 Canonical runtime release Validation 或稳定 API 兼容承诺。
