# 项目结构 State

Updated: 2026-08-30

Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md), [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md), [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md), [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md), [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)

## 当前事实

- 单一 Git 仓库根为 `D:\coding warehouse\project-orrery`；protected `origin/main` 已包含 docs-only SC1 exact `a9369dd`，产品 source baseline 为 `9ee831f`。
- 项目作者权威根为 `AGENTS.md` 与 `docs/`；`.project-orrery.json` 选择 `authority_status: integrated` 和 `authority_model_version: 1`。
- 当前公开 v0.2.0 的发布源仍是 `skills/project-orrery/`。tag／ZIP／checksum／release manifest 指向历史发布提交 `20fc95b`，不随 main 上的实验源码改变。
- 未发布的平台中立源码位于 `packages/project-orrery-{core,cli,observatory}/`。W7.2 Worktree Candidate 在 exact U2.1 continuation baseline 上声明 Core 0.1.17、CLI 0.1.21、Observatory 0.1.16；Core API 为 1，组件总状态为 `unreleased`。
- 薄平台层位于 `adapters/{codex,harness-json,claude-code,deepseek-harness}/`，当前 source 版本均为 0.1.1、`experimental`／`unreleased`。Adapter 不拥有 canonical 作者模板、State、ADR 或 Authority 规则。
- 自托管观测台位于根 `scripts/docsite/`。integrated Candidate 新增 `Start Orrery.vbs`／`start-orrery.bat --console`、统一静态 builder 与单 loopback supervisor；Personal／Team／Maintenance／Workstream Graph 仍为 root-only/default-off consumer，没有进入默认发布模板或 v0.2.0 managed tools。
- ADR-0016 的生产 Unified Shell 已在 integrated Candidate 实现：一个用户可见 listener／URL／导航壳，Broker／Coordinator 等内部 capability 由 supervisor 隐藏管理；当前没有公开默认切换，`start-docsite.bat` 保持 whole-shell rollback。
- U2.1 Worktree Candidate 修复维护者拒绝的集成体验：只保留一个中文 app 导航并保留作者文档树；全页共享显式关闭服务入口；旧 Maintenance last-run 仅作历史警告；完整、valid、hash-bound 的 W7.1 legacy/archive graph 不再被 native root 缺失误挡。它没有创建 relation root、赋予 archive 执行权或放宽 Quick Remove 当前资格。
- W7.2 Worktree Candidate 只重构 Observatory Graph presentation：从左到右的确定性 rank、固定可读节点、按 connected component 对齐的工程图路线、按链双向展开／收起、三 lens 真实端点、画布内 inspector 与移动 relation ledger。关系由实线／虚线／复合线和固定视觉尺寸箭头表达，不在线路上覆盖文字；画布支持锚点式 `Ctrl + 滚轮` 缩放。rank 通道为 88px，独立链只保留 44px 分组空隙，不再插入整行空白；全站滚动条使用深浅主题适配。Core relation schema／facts、W7.1 archive 证据与执行边界未改。
- W7.1 integrated Candidate 只为 relation 已引用且 live endpoint 缺失的 Workstream 读取有界 Git-common-private retired-session archive，恢复 closed/offline/current/superseded 轴；archive 不进入 active tip、apply/undo、Review Ready 或执行面。
- W1–W7 协作源码已经进入 main：Git-private Workstream session、Scope/finding、review/integration/cleanup、Personal／Team projection、workspace maintenance、LAN discovery／manual Host switch、stacked lineage、relation event/graph、apply/undo/recovery contract 和只读 Graph consumer 均存在。
- ADR-0017 已接受后续 relation capture 规则：只有 exact-base／同项目／ancestry 可验证的 `derived_from` 可由 Core 自动写为有效事实；`depends_on` 必须标注 implementation／validation／integration／release gate，并由任务 owner 或 human integrator 确认；`absorbs` 只能由 human integrator 确认。Personal owner 默认是唯一 integrator，Team owner 可显式增加其他 human integrator。W7.3 尚未实现这些写入、角色与确认入口。
- CI5 将 27 个逻辑 Promotion shard 映射为每 OS 十个物理 lane；Fast 与 Promotion 分离，required check 名称保持不变。exact `9ee831f` 已通过 25-job 双平台 Promotion 并进入 main。
- 当前展示品牌为 Orrery。`project-orrery`、`project_orrery`、`.project-orrery.json`、v1 schema／receipt／hash domain 和 v0.2.0 资产继续作为稳定技术或历史标识。
- 非权威研究控制面位于 `experiments/context-routing/`；大型原始运行根为 `D:\coding warehouse\project-orrery-benchmark`，不属于 Git 仓库或发布包。

## Worktree 与事实作用域

- 一个 Workstream 使用一个独立 branch＋linked worktree／clone；主 worktree只用于唯一整合。linked worktree 共享 Git object store 和 refs，但拥有独立 HEAD、index 与工作目录。
- Canonical／Candidate／Worktree／Local-only／Unknown 必须分别表达。Candidate HEAD 被 main 包含不自动产生 review package、closure record 或作者 Validation。
- Workstream session、review、closure、maintenance 与 relation transaction 存在 Git-private 区域；它们是协调证据，不进入作者文档或发布资产，也不能替代 State／ADR／Validation。
- 本机旧 session 的 lifecycle 可能落后于 Git ancestry。maintenance 在缺少 current closure／review／Validation 时必须保护目标；不得凭目录前缀、年龄或 branch 已进入 main 自动删除。
- `git worktree remove`、local branch delete、remote branch delete 和 ordinary-directory removal 是四种独立动作。当前产品只在本机人类确认后支持严格合格的 remove-worktree；branch 不随之删除。
- 2026-08-29 的 SC1 本机维护已归档并移除 W5D、CI4、R1、R2、R3、W6 六个 clean／closed worktree，只删除目录并保留全部 branch／commit。清理后为七个 registered worktree；并发创建的 `github-front-door-redesign` 及其余活动／待收口任务不在本轮范围。

## 结构与安全边界

- Core 持有 schema、manifest／兼容判断、Authority evaluator 与 canonical 作者模板；CLI 组合 Core 与 Observatory；Observatory 只负责派生投影。
- Skill project-template 是 canonical 作者模板的兼容投影；测试要求内容一致。旧 Skill 脚本是薄 wrapper，单独分发时回退冻结 v0.2 实现。
- Codex／Claude／DeepSeek Adapter 当前只声明 caller-provided attach；没有平台声明 launch／rebind／message。Adapter guard 不能阻止绕过 Adapter 的任意宿主写入。
- Team Mode 默认关闭；Personal 默认 zero-network。Team 只能同步版本化元数据，不能上传 Prompt／回答／transcript、源码正文、未 push diff 或成员凭据。
- W7B transaction 只写 Git-private confirmation／journal／receipt／compensation；真实 self-host 尚未执行 relation apply。Graph 只读，不提供 apply／undo／close／delete 按钮。
- Workspace Maintenance Phase 0–2 已实现；Phase 3 自动 worktree removal 和 Phase 4 OS scheduler 尚未实现。没有后台默认删除、daemon 或远程执行。

## 实现证据

- `.project-orrery.json`
- `packages/component-versions.json`
- `packages/project-orrery-core/`
- `packages/project-orrery-cli/`
- `packages/project-orrery-observatory/`
- `adapters/`
- `skills/project-orrery/`
- `scripts/docsite/`
- `scripts/ci/`, `.github/workflows/fast-validation.yml`, `.github/workflows/validate.yml`
- `tests/`
- [U2 Unified Observatory Validation](../validation/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 UX Acceptance Fixes Validation](../validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [W7.1 Archived Session Relation Projection](../validation/2026-08-29-w7-1-archived-session-relation-projection.md)
- [W7.2 Graph Readability](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [W7D Validation](../validation/2026-08-28-w7d-w7-integration-candidate.md)
- [CI5 Validation](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)

## 已知缺口

- Core／CLI／Observatory 尚无独立公开发行物、多组件 release pipeline 或 manifest v2。
- 默认 docsite／Skill template 尚未启用 Unified Observatory 或 Personal／Team／Maintenance／Graph；公开 v0.2.0 不包含这些能力。
- 没有真实双机 LAN、自动 Coordinator 选主、云 relay、多设备迁移或远程 shell／Agent／merge／delete。
- W7 relation store 没有 self-host native apply 记录；旧 session 到 post-main closure 的兼容收口仍需保守人工流程。
- W7.3 relation capture 尚未实现：当前没有 exact-base `derived_from` 自动写入、gate-aware `depends_on` proposal／confirmation、integrator registry／`absorbs` 确认或 Observatory relation inbox；现有 Graph 只能显示已有证据，因此仍可能稀疏。
- workspace maintenance 没有自动 removal 或 OS scheduler；关闭应用后不会定时执行。
- Claude Code 尚未完成认证后的真实模型路由；DeepSeek 与 Codex evidence 只覆盖各自记录的精确 runtime 范围。
- 自动 R1 脱敏导出器、跨平台 byte-for-byte archive 与 Brownfield Adoption 研究／Plan 均未实现。
