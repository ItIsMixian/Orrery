# PO-DEC-WT-001: 多 worktree 协作与分支事实作用域

Status: Proposed

Date: 2026-08-19

Maintainer disposition: Approved for integration on 2026-08-19

Formal ADR: pending integration-time allocation

> 这是候选分支上的临时决策记录，不是 canonical ADR。只有集成者基于最新集成分支分配正式 `ADR-NNNN`、更新引用并合流后，它才成为全项目有效决定。

## Context

Project Orrery 已经区分原则、决策、实现、State 与验证，但多人同时在分支、linked worktree 或独立 clone 中开发时，“当前事实”不再只有一种：集成分支存在 canonical 事实，功能分支存在 candidate 事实，本地未提交工作还存在 worktree 事实。

若多个 Agent 共用一个工作目录，它们会同时看到相同的未提交文件、索引和生成物；Git 无法区分任务所有权。即使使用独立 worktree，并发分支仍可能同时修改相同路径、权威文档、接口或验证面。连续 ADR 编号也会在互不可见的分支中发生碰撞。

项目需要一种不依赖全局写锁、能在同机和跨机器场景中诚实表达可见范围，并在合流前暴露冲突的协作协议。

## Decision

1. 每项并发任务必须拥有独立分支，并使用独立 linked worktree 或独立 clone。主 worktree 默认只用于集成，不作为普通 Agent 的实现目录。
2. 项目事实分为三层：
   - Canonical：`integration_ref@commit` 上已经集成的事实；
   - Candidate：`branch@HEAD` 相对 merge base 的候选事实；
   - Worktree：当前工作目录中尚未提交的局部事实。
3. Project Orrery 的界面与机器报告必须显示当前 branch、HEAD、integration OID、merge base、ahead/behind、dirty 状态和事实作用域，不得把 Candidate 或 Worktree State 表述为 canonical。
4. 每个 linked worktree 的执行 session 存放在 `git rev-parse --git-path orrery/worktree.json` 所指向的私有 Git 管理路径中。它是可重建运行元数据，不进入仓库，也不成为新的权威文档。
5. 根 `PROGRESS.md` 和 `HANDOFF.md` 表达集成视角，普通功能分支不得为每个中间动作持续改写它们。与实现同行的 subsystem State 可以在功能分支中更新，但在合流前只属于 Candidate State。
6. 首版重叠检测覆盖：已提交、staged、unstaged、untracked 和预期写入路径；State／ADR／Design／全局入口等权威文档；声明的验证面。结果分为 Direct、Authority、Semantic 和 Unknown。Unknown 必须明确显示，不得伪装为“无冲突”。
7. 冲突检测默认告警和阻断集成验证，不建立仓库级全局写锁。凭据、发布、schema migration 等明确独占资源可以配置更严格的门禁。
8. 合流必须在独立且干净的 integration worktree 中推测性执行，固定目标 integration OID，运行 merge／rebase、相关测试、文档一致性和 State 对齐检查；全部通过后才能更新集成分支。
9. 非集成分支中的新决策使用 `docs/decisions/proposals/PO-DEC-<task-id>-<slug>.md` 形式的稳定临时 ID。只有集成者基于最新 integration ref 分配正式 `ADR-NNNN`，并在合流前统一更新文件名和引用。
10. 默认 integration ref 为 `main`，但允许项目配置覆盖。首版不要求启用 `extensions.worktreeConfig`，也不承诺符号级或完整依赖图分析。
11. 跨机器协调只把已经 push 的分支、平台任务／PR 元数据和 CI 证据视为可观察输入；另一台机器上未 push 的工作必须显示为不可观察边界。

## Reasons

- linked worktree 提供独立 HEAD、索引和工作目录，同时共享对象库与普通 refs，适合把并发任务的写入空间物理隔离。
- 三层事实作用域保留 Project Orrery “State 只描述当前事实”的原则，同时承认分布式开发没有单一的实时文件系统视图。
- Git 派生的 session 和状态投影能降低手工维护文档给 Agent 带来的上下文与同步负担。
- 告警加推测性合流比全局锁更适合异步开发；它允许真正独立的任务并行，同时在集成点集中验证语义关系。
- 临时决策 ID 避免分支争抢连续编号，也不需要中央号码服务。
- 暂不启用 worktree-specific Git config，减少对 Git 版本和仓库格式的兼容风险。

## Consequences

- 启动并发任务需要创建或选择独立 worktree／clone，不能把共享主目录当作默认工作区。
- 工具必须准确采集 untracked 文件、dirty 状态和 merge base；只看 commit diff 不足以判断重叠。
- Candidate Design、Plan 和 State 必须带作用域提示，集成后才可转为 canonical。
- 根进度文档的写冲突减少，但集成者承担在合流时同步 PROGRESS、HANDOFF、DEVLOG、State 和 Validation 的责任。
- 不同机器上的未 push 工作无法被自动发现；协议只能暴露 Unknown，不能消除这一分布式限制。
- 路径无重叠不等于语义无冲突；首版依靠声明的验证面和推测性合流弥补，符号／依赖分析留待后续研究。
- 正式 ADR 编号在集成时才确定，因此外部讨论和分支内引用必须先使用临时 ID。

## Implementation and validation mapping

- Candidate Approved Design: [多人／多 worktree 协作协议](../../design/multi-worktree-collaboration-protocol.md)
- Implementation Plan: [2026-08-19 多 worktree 协作协议](../../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)
- State Docs after implementation: `docs/state/project-structure.md`, `docs/state/documentation-system.md`, `docs/state/release-and-toolchain.md`, `docs/state/test-coverage.md`
- Validation: linked-worktree isolation, untracked-path detection, direct／authority／semantic／unknown overlap, candidate-scope rendering, provisional ADR allocation, and clean speculative integration scenarios defined by the Plan
