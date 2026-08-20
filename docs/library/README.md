# Project Orrery research library

[English](#english) · [简体中文](#简体中文)

## English

This directory stores research notes, literature reviews, experiments, and design hypotheses for Project Orrery itself.

Material in this directory is **non-authoritative**. It may inform a proposal, benchmark, Design, or ADR, but it does not change the released Skill, the installation contract, or a target project's authority chain by itself.

### Notes

- [Task-centered context, provenance, and documentation overhead](2026-08-17-task-context-provenance-and-documentation-overhead.md) — evidence review and a proposed local benchmark for context routing, access receipts, documentation cost, and parallel development.
- [任务中心上下文、可追溯证据与文档开销](2026-08-17-task-context-provenance-and-documentation-overhead.zh-CN.md) — 中文版本。
- [Marglo as a real-development benchmark source](2026-08-19-marglo-benchmark-source-notes.zh-CN.md) — Chinese source notes on deriving isolated code, migration, security, and cross-module tasks without copying live data or worktree changes.
- [sivtr as a unified work-memory evidence layer](2026-08-19-sivtr-work-memory-source-notes.zh-CN.md) — Chinese source study of typed work records, stable refs, progressive retrieval, local-first boundaries, and the distinction between episodic evidence and authoritative project state.
- [OpenProgram](https://github.com/Fzkuji/OpenProgram) — unreviewed source lead suggested by the maintainer for possible future DAG and task-orchestration study; no source inspection, evidence claim, or adoption decision has been made.
- [Authority semantics, product core, and complexity boundaries](2026-08-20-authority-semantics-and-product-complexity-discussion.zh-CN.md) — maintainer-provided Chinese web-discussion capture distinguishing user Seed from Orrery's meta-level Authority Model, incremental semantic extraction from the Observatory, and user-facing versus internal research complexity.
- [Context-routing benchmark](../../experiments/context-routing/) — non-authoritative experiment infrastructure and Git-grounded historical task corpus.
- [Pilot 004 B/H holdout](../../experiments/context-routing/results/2026-08-18-pilot-004-bh-holdout-terra-medium.md) — both strategies passed the corrected independent acceptance surface; H was not adopted because it used 47% more input tokens overall.
- [Current research State](../state/context-routing-research.md) — the authoritative current-project summary derived from the non-authoritative evidence above.

## 简体中文

本目录保存 Project Orrery 自身的研究笔记、文献综述、实验方案与设计假设。

这里的材料均为**非权威资料**。它们可以推动提案、基准实验、Design 或 ADR，但不会自行改变已发布 Skill、安装契约或目标项目的权威链。

### 研究笔记

- [任务中心上下文、可追溯证据与文档开销](2026-08-17-task-context-provenance-and-documentation-overhead.zh-CN.md)——关于上下文路由、访问回执、文档成本与并行开发的证据综述及本地基准方案。
- [Task-centered context, provenance, and documentation overhead](2026-08-17-task-context-provenance-and-documentation-overhead.md)——英文版本。
- [Marglo 真实开发基准素材观察](2026-08-19-marglo-benchmark-source-notes.zh-CN.md)——提炼代码、迁移、安全与跨模块任务的模式，同时排除真实数据和活跃工作树。
- [sivtr 统一工作记忆层观察](2026-08-19-sivtr-work-memory-source-notes.zh-CN.md)——分析类型化工作记录、稳定引用、渐进检索、local-first 边界，以及情境证据与权威项目事实的区别。
- [OpenProgram](https://github.com/Fzkuji/OpenProgram)——维护者提供的未研究线索，未来可用于 DAG 与任务编排代码观察；当前没有打开源码、形成证据或作出采纳决定。
- [Authority Semantics、产品核心与复杂性边界讨论](2026-08-20-authority-semantics-and-product-complexity-discussion.zh-CN.md)——维护者提供的网页端讨论摘录，区分用户 Seed 与 Orrery meta-level Authority Model，并记录 Observatory 渐进拆分及用户复杂性隔离方向；当前没有直接升级为 ADR 或实现。
- [上下文路由基准](../../experiments/context-routing/)——非权威实验基础设施与可由 Git 复核的历史任务语料。
- [Pilot 004 B/H 留出任务结果](../../experiments/context-routing/results/2026-08-18-pilot-004-bh-holdout-terra-medium.md)——修正后的独立验收面上两种策略都通过；H 因总 input token 高 47% 而暂不采纳。
- [当前研究 State](../state/context-routing-research.md)——由上述非权威证据派生的项目当前事实摘要。
