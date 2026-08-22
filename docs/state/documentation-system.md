# 文档系统 State

Updated: 2026-08-22
Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md) | [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md) | [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md) | [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md) | [ADR-0012](../decisions/0012-document-governance-and-information-lifecycle.md)

## 当前事实

- Project Orrery 已在本仓库正式采纳自身权威链。
- Agent 入口是根 `AGENTS.md`；维护者入口是本目录 `README.md`、`PROGRESS.md` 与本地观测台。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation 和 Snapshot 已各有独立职责。
- ADR-0009 已把这些职责、各对象 lifecycle、独立 Decision／Implementation／Validation claim dimensions、fact scopes、evidence categories 和 derived-view constraints 正式定义为 Authority Meta Model；`docs/core/principles.md` 明确只是 Project Orrery Product Seed。
- 文档事实现在显式区分 Canonical（integration ref 已集成）、Candidate（功能分支 HEAD）和 Worktree（本地未提交）三个作用域；分支 State 只能陈述候选事实，不能冒充 canonical 当前状态。
- 根 `PROGRESS.md` 与 `HANDOFF.md` 是集成视角入口，不是历史总账：PROGRESS 只保留当前线路、未完成事项、阻塞和近期里程碑，完整演化与逐次证据分别进入 DEVLOG／Validation。普通功能分支应让代码、测试和 subsystem State 同行，并在合流时由唯一整合者同步全局入口，避免多个 Agent 持续争写同一份全局状态。
- ADR-0012 已进入本地 Canonical，并建立独立于 Authority Meta Model 的 Documentation Governance Policy：它按文档角色规定当前／历史边界、事件驱动同步、责任式拆分、soft review budget 和人工审查闭环。它不是新的作者文档类型，也不授权自动改写。
- 当前 self-host 文档已采用治理入口：PROGRESS／Authority State 完成首轮职责压缩；HANDOFF 因包含大量安全接续细节，被记录为后续人工 review candidate，尚未做专项压缩。
- ADR-0008 已接受默认 zero-network Personal Mode、手动开启 Team Mode、Local-only 元数据和中央只读／本机执行边界；这些目前只是有效设计约束，现有观测台还没有 Workstream 指挥台、Team 页签、成员或同步实现。
- 根观测台由模板 v0.2.0 安装；其输出 `docs/_site/index.html` 为可重建生成物。
- 未发布 Core 包现持有 canonical 作者文档模板；Skill 下的 project-template 是兼容投影，测试要求作者模板内容一致。Observatory 工具不属于作者事实，并由独立组件清单管理。
- 未发布 Codex Adapter 只把 Codex 调用路由到目标仓库根 `AGENTS.md` 和平台中立 CLI；它不携带 State、ADR、Validation、canonical 模板或项目摘要，因此没有形成第二套文档事实。
- AI 问答、项目简报、路线综合、里程碑和趋势雷达保持可选，且没有事实权威。Candidate 动态观测台已给这些输出附加不可由模型覆盖的 `derived-ai-view` 非权威 receipt；问答另有可见提示。Authority report 缺失时保留 `Unknown`，Candidate shadow 也只作为 `shadow-only` context，不会被 AI 输出升级成 State、ADR、批准或 Validation。
- Authority 诊断页面与 sidecar 分开 opt-in：`ORRERY_AUTHORITY_SHADOW_REPORT` 只生成可丢弃 report，`ORRERY_AUTHORITY_SHADOW_VIEW=1` 才显示只读诊断面板。面板显式标注非权威／未切换，只展示 comparison health、scope 和计数，不展示或创造项目 claims。
- 本地 Canonical baseline 通过 root-only `build_authority_projection.py` 增加第三个独立开关
  `ORRERY_AUTHORITY_PROJECTION_VIEW=1`：它把与 M2.1 bundle 精确 reconciliation 的 Core effective decision、
  role claims、Unknown、scope／visibility 和 source link 投影到 dashboard。开关缺省关闭，关闭即回到逐字节
  legacy 输出；失败不产生部分页面。原 `build_docsite.py` 与发布模板逐字节一致，root-only package-path
  injection 不进入 legacy module；发布 Skill 模板和默认 managed entry 均未切换。
- 动态观测台把 AI 服务设置入口放在顶栏、主题切换按钮左侧；静态 HTML 不注入设置入口，仍保持只读。
- 动态观测台的问答、仪表盘、趋势雷达、连接测试与独立 Q&A CLI 都只构造 Broker Provider；OpenAI、DeepSeek 和 Custom 只是上游注册项。项目 `ai-config.json` 的有效 Provider 恒为 `broker`。
- 默认本机托管 Broker 使用专用 Provider 凭据 namespace、client token、缓存、single-flight、模型白名单和预算门；一次“保存并启用”不强制额外测试请求。
- 本机托管只提供统一路由和成本控制，不隔离同一 OS 用户进程；只有在独立 OS 身份或等价外层隔离下运行外部 Broker 时才能隔离 Provider Key。
- 手动刷新、设置与问答写操作都要求同源 POST；旧查询参数 GET 不再触发模型调用。
- Canonical W1 Phase 0 已为 `AGENTS.md` 的七个 subsystem 区块增加显式稳定 ID。Core registry parser 只读取这些 ID 与已有 `docs/state/*.md` 链接；重复／保留 ID 或缺失 State Doc 失败关闭，并且不会因路径推断创建新 State。该 registry 是权威入口的机器投影，不是新的作者事实源。
- W1 Phase 1 把 Workstream session 保存为 Git 私有、可重建运行元数据，并由 CLI 从 Git 机械派生 branch／OID／dirty／scope、stale、lifecycle 与 routing 摘要；create／guard／route／attach 都不会自动改写 State、Plan、Validation 或根进度入口，也不要求 Agent 固定生成 Manifest／Receipt。

## 同步状态

- Pilot 001–004 已在 Research State、DEVLOG、PROGRESS 和实验报告之间建立链接。
- 详细原始运行不复制进 Docs。
- 公开用户文档仍由 `README.md` 与 `README.zh-CN.md` 承担。

## 实现证据

- `AGENTS.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/design/self-hosting-documentation-system.md`
- `docs/design/document-governance-and-information-lifecycle.md`
- `docs/implementation/plans/2026-08-21-document-governance-and-audit.md`
- `scripts/docsite/build_docsite.py`
- `scripts/docsite/build_authority_projection.py`（root-only M2.2 opt-in projection）
- `scripts/docsite/serve.py`
- `scripts/docsite/_llm.py`
- `scripts/docsite/llm_broker.py`
- `docs/decisions/0006-broker-only-docsite-provider-gateway.md`
- `docs/validation/2026-08-19-broker-first-docsite-gateway.md`
- `adapters/codex/SKILL.md`
- `adapters/codex/adapter-manifest.json`
- `packages/project-orrery-core/src/project_orrery_core/collaboration.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json`
- `tests/test_collaboration_contract.py`

## 已知缺口

- 当前观测台界面主要为中文，完整国际化仍未实施。
- D1 已建立内部 finding schema／registry、11 组合成 fixture 和 dependency-free contract validator；尚未实现 `docs audit` scanner／CLI、真实项目 advisory 配置位置与阈值、acknowledge／defer 持久化、State／实现链接时效检查或任何自动修复。该 Core contract 也未导出为稳定公共 API。
- W1 Phase 1 CLI 已能创建固定 integration OID 的 linked worktree、维护 Git-private session、执行 primary-write preflight、lifecycle transition、route 与 caller-provided attach；Adapter Skill 只在自身流程中要求这些检查，观测台尚未消费该合约，仍没有自动重叠报告、审查包、清理建议或 Team Mode runtime。
- Authority Meta Model 已有 Candidate fixture、experimental Core evaluator、self-host 模型选择、managed shadow sidecar／诊断面板与 AI non-escalation guard，但仍无稳定公共 parser／domain API、默认 Authority 页面 projection、consumer production switch 或公开 release 实现。
- M2.2 已有进入本地 Canonical baseline 的 root-only、显式 opt-in 完整 Authority projection，但没有改变上述默认／发布边界。
