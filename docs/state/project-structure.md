# 项目结构 State

Updated: 2026-08-29

Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md), [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md), [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md)

## 当前事实

- 单一 Git 仓库根为 `D:\coding warehouse\project-orrery`；protected `origin/main` 已包含 docs-only SC1 exact `a9369dd`，产品 source baseline 为 `9ee831f`。
- 项目作者权威根为 `AGENTS.md` 与 `docs/`；`.project-orrery.json` 选择 `authority_status: integrated` 和 `authority_model_version: 1`。
- 当前公开 v0.2.0 的发布源仍是 `skills/project-orrery/`。tag／ZIP／checksum／release manifest 指向历史发布提交 `20fc95b`，不随 main 上的实验源码改变。
- 未发布的平台中立源码位于 `packages/project-orrery-{core,cli,observatory}/`。当前版本为 Core 0.1.14、CLI 0.1.18、Observatory 0.1.9，Core API 为 1，组件总状态为 `unreleased`。
- 薄平台层位于 `adapters/{codex,harness-json,claude-code,deepseek-harness}/`，当前 source 版本均为 0.1.1、`experimental`／`unreleased`。Adapter 不拥有 canonical 作者模板、State、ADR 或 Authority 规则。
- 自托管观测台位于根 `scripts/docsite/` 与 `start-docsite.bat`。Personal／Team／Maintenance／Workstream Graph 均为 root-only 或 default-off source consumer，没有进入默认发布模板或 v0.2.0 managed tools。
- W1–W7 协作源码已经进入 main：Git-private Workstream session、Scope/finding、review/integration/cleanup、Personal／Team projection、workspace maintenance、LAN discovery／manual Host switch、stacked lineage、relation event/graph、apply/undo/recovery contract 和只读 Graph consumer 均存在。
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
- [W7D Validation](../validation/2026-08-28-w7d-w7-integration-candidate.md)
- [CI5 Validation](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)

## 已知缺口

- Core／CLI／Observatory 尚无独立公开发行物、多组件 release pipeline 或 manifest v2。
- 默认 docsite／Skill template 尚未启用 Personal／Team／Maintenance／Graph；公开 v0.2.0 不包含这些能力。
- 没有真实双机 LAN、自动 Coordinator 选主、云 relay、多设备迁移或远程 shell／Agent／merge／delete。
- W7 relation store 没有 self-host native apply 记录；旧 session 到 post-main closure 的兼容收口仍需保守人工流程。
- workspace maintenance 没有自动 removal 或 OS scheduler；关闭应用后不会定时执行。
- Claude Code 尚未完成认证后的真实模型路由；DeepSeek 与 Codex evidence 只覆盖各自记录的精确 runtime 范围。
- 自动 R1 脱敏导出器、跨平台 byte-for-byte archive 与 Brownfield Adoption 研究／Plan 均未实现。
