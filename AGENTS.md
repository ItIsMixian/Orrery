# Project Orrery：Agent 状态索引

这是新会话或上下文重置后的强制入口。Project Orrery 正在用自身权威模型管理发布 Skill、文档观测台和上下文路由研究。

## 接触文件前必须阅读

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `docs/PROGRESS.md`
4. `docs/core/principles.md`
5. 与任务相关的 `docs/state/*.md`
6. State 链接的有效 ADR（只在需要理解理由时）
7. PROGRESS 指向的活动 Implementation Plan
8. 最后读取真实代码、配置、资产、实验报告或外部运行状态

## 权威规则

- State Docs 只写当前事实；ADR 保存决定与原因；Plan 只写准备怎样做。
- `accepted` 不等于 `implemented`；工作树实现不等于已提交，已提交不等于已发布。
- `docs/library/`、`docs/backlog.md` 和 `experiments/` 没有决策权。实验通过质量门并经用户接受后才可形成 ADR。
- 每次完成实现或验证，同步 State、Validation、DEVLOG；由唯一整合者按当前线路同步 PROGRESS，停止点或风险变化时同步 HANDOFF。当前入口只保留当前控制信息，历史通过链接进入 DEVLOG／Validation。
- `docs/_site/index.html` 是生成物，禁止手工编辑。

## 硬边界

- 默认安装不能覆盖现有作者文档；`--upgrade-tools` 只能操作白名单工具并先备份。
- API Key、`ai-config.json`、keyring、缓存、`.port`、生成站点和本机原始 benchmark 不能进入发布包。
- 仪表盘、AI 问答、摘要、RAG 和趋势雷达只能投影权威文档，不能产生项目事实。
- Git 只证明写入；Agent 回执只属于自述。没有 Harness／工具边界证据时，不得宣称已精确审计模型读取内容。
- 大型原始实验根 `D:\coding warehouse\project-orrery-benchmark` 不自动进入 Git；可发布结论必须提炼到 `experiments/context-routing/results/`。
- 修改发布契约、文档架构或跨模块安全边界时必须新增 ADR，不得只改 README。
- 并发 Workstream 必须各自使用独立分支和 linked worktree／clone；主 worktree 只用于集成。不得让两个 Agent 共享同一工作目录或把 Candidate／Worktree State 表述为 canonical。
- 普通功能分支不持续改写根 `docs/PROGRESS.md` 与 `docs/HANDOFF.md`；受影响的 subsystem State、实现和验证在分支同行，由唯一整合者在干净 integration worktree 中同步全局入口。
- 协作功能默认必须保持 zero-network Personal Mode；Team Mode 只能由用户按项目显式开启。中央视图只读且只能发送请求，任何执行必须由成员本机确认。
- Team Mode 不得同步完整 Prompt／回答／transcript、源码正文、未 push diff 或成员执行凭据；Local-only telemetry 必须标注来源，证据不足的语义关系保持 Unknown。

## project structure

**ID**: `project-structure`

**What**: 管理发布 Skill、根文档、实验控制面、自托管观测台和外部原始运行之间的边界。
**Truth**: 当前仓库树、`.project-orrery.json`、`docs/PROGRESS.md`。
**Dig**: [项目结构 State](docs/state/project-structure.md) | [ADR-0001](docs/decisions/0001-project-orrery-self-hosting.md) | [ADR-0007](docs/decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](docs/decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)。

## documentation system

**ID**: `documentation-system`

**What**: 管理权威链、人类／Agent 阅读入口、作者文档生命周期、同步义务和观测台投影。
**Truth**: `AGENTS.md`, `docs/`, 根 `scripts/docsite/`。
**Dig**: [文档系统 State](docs/state/documentation-system.md) | [自托管 Design](docs/design/self-hosting-documentation-system.md) | [治理 ADR-0012](docs/decisions/0012-document-governance-and-information-lifecycle.md) | [治理 Design](docs/design/document-governance-and-information-lifecycle.md) | [活动 Plan](docs/implementation/plans/2026-08-21-document-governance-and-audit.md)。

## authority semantics

**ID**: `authority-meta-model`

**What**: 定义 Orrery 解释项目权威体系的 Meta Model：authority roles、各对象 lifecycle、独立 claim dimensions、fact scopes、evidence categories、derived-view constraints 和 conformance 输入边界。
**Truth**: [Authority Meta Model State](docs/state/authority-meta-model.md)；本地 Canonical baseline 已有 versioned fixture、experimental Core evaluator、完整内部 CLI claim bundle、root-only opt-in Observatory projection 和本地 release-candidate gate；仍无稳定公共 domain API、默认 production switch 或公开模型 1 release。
**Dig**: [ADR-0009](docs/decisions/0009-authority-meta-model-and-semantic-conformance.md) | [ADR-0010](docs/decisions/0010-core-owned-authority-evaluator.md) | [ADR-0011](docs/decisions/0011-authority-model-version-and-compatibility.md) | [Approved Design](docs/design/authority-meta-model.md) | [来源讨论](docs/library/2026-08-20-authority-semantics-and-product-complexity-discussion.zh-CN.md)。

## released skill and compatibility

**ID**: `release-and-toolchain`

**What**: 平台中立 Core／CLI／Observatory、Codex Skill 兼容入口和发布兼容契约。
**Truth**: `packages/`, `adapters/codex/`, `skills/project-orrery/`, `scripts/package_release.py`, `scripts/package_codex_adapter.py`, `.github/workflows/`。
**Dig**: [发布与工具链 State](docs/state/release-and-toolchain.md) | [ADR-0004](docs/decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [Approved Design](docs/design/platform-neutral-core-and-adapter-architecture.md)。

## multi-worktree collaboration

**ID**: `multi-worktree-collaboration`

**What**: 管理并发 Agent 的分支／worktree 隔离、Canonical／Candidate／Worktree 事实作用域、重叠审阅和干净集成。
**Truth**: Git branch／HEAD／worktree 状态、`docs/state/project-structure.md`、`docs/state/documentation-system.md`；当前只实现人工隔离与集成流程，自动 session、overlap 与 integration 命令尚未实现。
**Dig**: [项目结构 State](docs/state/project-structure.md) | [协作协议](docs/design/multi-worktree-collaboration-protocol.md) | [ADR-0007](docs/decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](docs/decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md) | [活动 Plan](docs/implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)。

## context-routing research

**ID**: `context-routing-research`

**What**: 测量 Agent 文档负担、上下文路由、访问证据与 Harness 验收。
**Truth**: `experiments/context-routing/` 与仓库外封存输出；当前没有任何实验策略进入发布版 Skill。
**Dig**: [研究 State](docs/state/context-routing-research.md) | [研究综述](docs/library/2026-08-17-task-context-provenance-and-documentation-overhead.zh-CN.md) | [ADR-0002](docs/decisions/0002-real-development-benchmark-portfolio.md) | [ADR-0005](docs/decisions/0005-prewrite-scope-acquisition-input.md)。

## test coverage

**ID**: `test-coverage`

**What**: 保护安装、升级、发布、文档站、凭据边界和实验 Harness。
**Truth**: `tests/`, `.github/workflows/`, `docs/validation/`。
**Dig**: [测试覆盖 State](docs/state/test-coverage.md)。
