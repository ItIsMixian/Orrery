# 文档系统 State

Updated: 2026-08-30

Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md) | [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md) | [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md) | [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md) | [ADR-0012](../decisions/0012-document-governance-and-information-lifecycle.md) | [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md) | [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md) | [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md) | [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)

## 当前事实

- Orrery 已用自身权威链管理本仓库。Agent 入口为根 `AGENTS.md`；维护者入口为 `docs/PROGRESS.md`、`docs/HANDOFF.md` 与本地 Observatory。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation、Snapshot、Library 与派生视图职责分离。Authority Meta Model 定义角色与语义；Product Seed 只约束 Orrery 自身目标。
- 文档事实显式区分 Canonical、Candidate、Worktree、Local-only、Historical 与 Unknown。普通功能分支只同步受影响 subsystem State／Plan／Validation／DEVLOG；根 PROGRESS／HANDOFF 由唯一整合者在合流阶段维护。
- PROGRESS 与 HANDOFF 是当前控制入口，不是历史总账。SC1 已把 CI5、R3、W7D 等 post-main 事实从 Candidate／pending 表述收口为 Canonical，并把历史运行细节留在 DEVLOG／Validation。
- ADR-0012 的 Documentation Governance Policy 已进入 Canonical source。D1 只实现内部 finding schema／registry 与 synthetic fixture；当前没有 `docs audit` scanner／CLI、acknowledge store、Observatory governance 页面或自动修复。
- Canonical 作者模板位于 Core package；Skill project-template 是 v0.2 兼容投影。Observatory tools 不属于作者事实，并由 component manifest 管理。
- 默认静态 docsite 从 Markdown 生成 `docs/_site/index.html`；生成物禁止手工编辑且不进入作者事实或发布包。
- AI Q&A、briefing、roadmap、milestones、radar、Authority projection、Personal／Team／Maintenance 与 Workstream Graph 都是派生视图。它们只能消费受约束输入并保留 source／scope／Unknown，不能创造 State、ADR、批准或 Validation。
- Authority shadow、diagnostic 与完整 projection 使用彼此独立的显式开关；默认 legacy build 保持。完整 M2.2 projection 仅由 root-only `build_authority_projection.py` 启用，失败关闭回无 claim 的 legacy 页面。
- Personal／Team／Maintenance／Graph 已作为 root-only/default-off sibling page 进入 Canonical source。U2.1 Candidate 的主视图用“交付／待确认的任务或历史状态／工作区清理建议”表达 Personal；Team 为 metadata-only/request-only，Maintenance 只显示当前资格与本机确认，Graph 只读消费完整且验证有效、hash-bound 的 native 或 legacy/archive relation evidence。
- ADR-0016 与 Approved Unified Observatory Design 已接受“一个用户入口／URL／导航壳、受管隐藏 helper”的目标。U2.1 Candidate 在现有 docsite 阅读、搜索、AI 与作者文档树上只保留一组中文 app 导航，组合 Authority／Personal／Team／Graph／Maintenance；协议值只在技术详情显示，未暴露半成品语言切换。U1 synthetic prototype 仍不是 UI 规范，公开默认尚未切换。
- W7.2 Worktree Candidate 将真实只读 Graph 改为单一从左到右 DAG：固定可读卡片、中文 rank lane、工程图式实线／虚线／复合线、固定 10px 箭头、每链独立展开和收起、锚点式 `Ctrl + 滚轮` 缩放，以及默认关闭的画布内技术详情抽屉。dependency／conflict 只从各自真实端点建图；空 dependency 不再显示孤立 active tips。桌面以 88px rank 通道和 44px 独立链间隔显示主图并保留 1×1px 语义 ledger，390px 用同一事实／展开状态的普通任务关系列表替代微型图；文档根、侧栏、画布与详情滚动条共享深浅主题变量。
- Team 页面没有远程执行权；W7 Graph 没有 apply／undo／close／delete 按钮；Maintenance 不把建议或 receipt 升级成作者事实。
- ADR-0017 已接受 Git-private relation proposal／confirmation 的职责边界：Agent、Harness 与未来 Conductor 只能提出带来源和证据的建议；任务 owner 确认 implementation／validation gate，human integrator 确认 integration／release gate 与 `absorbs`。中央调度只是可选交互形态，不是权限来源；当前产品尚无 relation inbox 或这些确认入口。
- 动态 docsite 的模型调用统一经过 Broker。Provider 配置与凭据按端点绑定，同源 POST、body gate、预算、缓存和错误脱敏已实现；同用户本机 Broker 不宣称秘密隔离。
- 当前展示品牌为 Orrery；目标项目标题仍由模板 token 定制。历史 `Project Orrery` 与稳定 `project-orrery` 技术标识按 ADR-0015 保留。

## 同步与生命周期规则

- 实现或验证完成后，同步受影响 State、Validation 与 DEVLOG；停止点或风险变化时同步 HANDOFF；当前线路改变时同步 PROGRESS。
- Accepted ADR、Approved Design、Plan checklist、Agent 回执或 Git commit 都不能单独证明 implemented／validated／released。
- State 只保留当前事实与缺口；逐次命令、失败轮、性能数字和 exact SHA 进入 Validation／DEVLOG。
- Documentation finding 只是 `info`／`warning`／`review-required` observation；长度、密度和风格不能单独成为硬门。
- 观测台和 AI 只能展示或解释 source facts。缺失 provider、schema、scope、evidence 或 relation store 时必须显示 Unavailable／Unknown，而不是推断安全或完成。

## 实现证据

- `AGENTS.md`, `docs/`, `.project-orrery.json`
- `packages/project-orrery-core/src/project_orrery_core/templates/`
- `packages/project-orrery-observatory/`
- `scripts/docsite/`
- `skills/project-orrery/assets/project-template/`
- `tests/test_project_orrery.py`
- `tests/test_documentation_governance_contract.py`
- `tests/test_personal_observatory.py`
- `tests/test_team_observatory.py`
- `tests/test_workspace_maintenance.py`
- `tests/test_workstream_relation_graph_observatory.py`
- `tests/test_unified_observatory.py`
- [Documentation Governance Plan](../implementation/plans/2026-08-21-document-governance-and-audit.md)
- [U2 Unified Observatory Plan](../implementation/plans/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 UX Acceptance Fixes Plan](../implementation/plans/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [W7.2 Graph Readability Plan](../implementation/plans/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [W7.2 Graph Readability Validation](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)

## 已知缺口

- D2 scanner／CLI、真实项目 soft-budget 配置、finding acknowledge／defer persistence、State／实现链接时效检查与自动修复均未实现。
- HANDOFF 已完成职责压缩，但没有自动治理工具；后续仍需人工确认安全边界的当前有效性。
- 完整国际化未实施，U2.1 只完成 zh-CN 主界面与集中 display vocabulary；没有完整英文模式。
- Authority 没有稳定公共 parser/domain API、默认 production projection 或公开模型 1 release。
- Personal／Team／Maintenance／Graph 尚未接入默认 docsite、Skill template 或公开 release。
- Unified Observatory 仍只是本地 root-only/default-off integrated Candidate；尚未进入默认 docsite、Skill template、managed-tool inventory、installer 或公开 Release。`start-docsite.bat`／`serve.py` 继续作为 legacy rollback 与当前公开兼容入口。
- Team 真实双机、云 relay、多设备、远程执行与 Graph 图形执行入口不存在。
- W7.3 relation capture inbox、gate-aware dependency confirmation、human integrator 管理与自动 mechanical `derived_from` 尚未实现；观测台仍只投影已经存在的关系证据。
- Brownfield Adoption 只有保守接入边界，没有研究结论、Approved Design 或 Implementation Plan。
