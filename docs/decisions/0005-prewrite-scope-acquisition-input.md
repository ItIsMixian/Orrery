# ADR-0005：上下文路由以首次产品写入前的范围确认成本为主指标

Status: Accepted
Date: 2026-08-19
Amends: [ADR-0002](0002-real-development-benchmark-portfolio.md)

## Context

ADR-0002 已要求后续上下文路由实验以隔离的真实应用开发任务为主，但既有 Pilot 仍主要报告完整
任务的总 input、output、墙钟和代理正文。完整任务成本混合了范围确认、实现、测试、失败重试和交接，
不能单独回答维护者最关心的问题：Agent 从收到人类指令开始，到确认要进入哪些实现文件、遵守哪些
约束并准备开始修改为止，Project Orrery 的入口与权威链给它造成了多少 input 压力。

此前候选还要求过 Context Manifest、Selected Evidence、Access Receipt 或扩张说明。这些自述会增加
Agent 的 input/output，改变被观察行为，而且不能独立证明模型实际读取或理解了正文。用户已经确认：
范围获取应由 Harness 被动观测，不要求 Agent 为实验额外生成 Manifest、回执或访问总结。

当前 `codex exec --json` 只在整轮结束时提供聚合 usage。它能报告完整任务成本，却不能把首次写入前
的 input 从后续实现成本中分离。本机 Codex app-server 协议另有逐上游响应更新的累计 token usage，
可与首次 `fileChange` 生命周期事件组合，但正式使用前仍需验证真实事件顺序和字段稳定性。

## Decision

1. 后续用于评价或采纳 Project Orrery 上下文路由策略的主成本指标，是从任务 Prompt 开始到首次产品
   文件写入启动之前的累计 input tokens，记为 `input-to-scope-lock`。首次产品 `fileChange` 的开始事件
   是可审计的 Scope Lock 近似边界，不宣称它证明模型主观上已经理解范围。
2. Scope Lock、边界前累计 usage、读取路径、代理切片与唯一正文量全部由 Harness 从工具／运行时事件
   派生。Agent 不输出或创建 Context Manifest、Scope Receipt、Selected Evidence、访问总结或其他
   仅为实验服务的协议文本。
3. Harness 同时记录边界前累计 input、cached input、non-cached input、output、唯一正文 bytes、读取路径
   数和读取顺序。完整任务总 input、output、墙钟与最终正文量继续作为护栏和诊断指标，但不是范围获取
   效率的替代品。
4. 只有运行时提供可验证的逐响应 usage，且 usage 更新与首次产品写入的事件顺序经过兼容性验证时，
   才能报告精确 `input-to-scope-lock`。若只能取得整轮聚合 usage，Harness 必须把分段 token 标记为
   `unavailable` 或有明确上下界的区间，不得用字节数或最终 token 伪装成精确值。
5. 成本下降不能补偿范围错误。候选必须先通过 ADR-0002 的行为、数据／安全、无关文件保护和事实链
   验收，并证明首次写入落在允许的产品范围；之后才比较 Scope Lock 前成本。
6. 真实开发任务组合、脱敏边界和独立 Oracle 继续由 ADR-0002 约束。既有 Pilot 001–007 不回写、
   不重分类；尚未运行模型的 Pilot 008 在正式执行前按本决定重构。
7. 本决定约束研究方法，不自动改变发布版 Skill、目标仓库模板或普通 Agent 工作流。任何候选只有通过
   预设质量门、形成 R2 并经维护者明确接受后，才可提出产品采纳 ADR。

## Reasons

- `input-to-scope-lock` 直接对应维护者体验到的“Agent 为确认实现范围付出了多少上下文成本”。
- 被动 Harness 观测避免协议本身制造额外 token，也避免把 Agent 自述当成访问证明。
- 将范围获取与实现阶段分开，能够区分“入口导航太重”与“任务本身实现困难”。
- 精确值必须建立在真实运行时事件上；承认不可观测比用估算制造虚假精度更可信。

## Consequences

- Pilot 008 不能沿用只输出整轮 usage 的 `codex exec --json` 正式执行路径。
- Harness 需要 app-server 事件分析器、单调 usage 检查、首次产品写入边界识别和兼容性 smoke。
- 研究报告会同时出现 Scope Lock 前指标和完整任务护栏，不能只引用最有利的一项。
- 候选路由设计应减少不相关权威层读取，而不是只缩短 Skill 文件或要求 Agent 写更多协议。

## Implementation and validation mapping

- Approved Design: [真实开发上下文路由基准](../design/real-development-context-routing-benchmark.md)
- Implementation Plan: [Pilot 008 Scope Acquisition 重构](../implementation/plans/2026-08-19-scope-acquisition-pilot-008.md)
- Corrected run Plan: [Pilot 009 Scope Acquisition](../implementation/plans/2026-08-19-scope-acquisition-pilot-009.md)
- State Docs: [上下文路由研究 State](../state/context-routing-research.md)
- Validation: [Pilot 008 apparatus stop](../validation/2026-08-19-pilot-008-formal-apparatus-stop.md)；
  [Pilot 009 formal run](../validation/2026-08-19-pilot-009-ps-scope-run.md)
