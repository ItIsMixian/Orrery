# 实施计划：Pilot 008 Skill Entry Router

Status: Completed — apparatus ready; no formal model runs authorized
Date: 2026-08-19
Governing ADR: [ADR-0002](../../decisions/0002-real-development-benchmark-portfolio.md)
Approved Design: [真实开发上下文路由基准](../../design/real-development-context-routing-benchmark.md)
Research candidate: [Skill Entry Router R v0.1](../../../experiments/context-routing/designs/skill-entry-router-v0.1.zh-CN.md)

## 目标

比较当前完整 Project Orrery Skill 入口 `P` 与精简、按操作路由的候选 `R`。本轮先完成
脱敏真实开发 fixture、独立 Oracle、控制包和真正嵌套的 preflight；不得修改发布 Skill，
不得在没有维护者再次确认时启动正式模型调用。

## 工作包

- [x] 冻结 P/R Skill 正文哈希、Prompt 组成、模型、推理强度和成本口径。
- [x] 构造不含真实用户数据的最小应用 fixture，并记录模式来源与脱敏边界。
- [x] 冻结两项代码任务和一项事实对齐任务，以及允许写入／受保护路径。
- [x] 建立行为优先的独立 Oracle、baseline negative control 与 positive control。
- [x] 修正 Pilot 007 的分支冲突路径，在真实外层 Git + 内层候选仓库中运行 preflight。
- [x] 增加 Pilot 008 dry-run 回归，不改变 Pilot 001–007 冻结控制包。
- [x] 运行专项、benchmark、结构、静态站、链接与 diff 验证。
- [x] 用 Validation、Research State、PROGRESS、DEVLOG 与 HANDOFF 记录“装置已准备／模型未运行”。

## 冻结门

R 只有在三项任务全部通过且不低于 P、必要依赖和受保护范围有效时，才进入成本判断。
固定 Skill 字节必须不高于 P 的 45%，完整 Prompt 至少下降 15%，总 input 不高于 P；output、
Agent 时间和代理正文均不得高于 P 的 105%。通过仍不自动采纳，必须先形成 R2 并由维护者接受。

## 验证出口

完成准备后写入 `docs/validation/2026-08-19-pilot-008-preparation.md`。正式运行使用新的仓库外
输出根，且开始前需再次获得用户确认。

## 完成结果

P 固定入口为 9,109 bytes，R 为 2,386 bytes（26.19%）；三项冻结 Prompt 的 R/P 字节比为
44.48%–44.67%。P 已冻结为 Pilot 内快照，避免活动发布源的并行写入改变基线。Oracle
negative/positive controls、外层 Git + 内层 fixture preflight 和 dry-run
均通过。没有启动 Codex 模型、没有产生 R0，也没有修改发布 Skill。验证见
[Pilot 008 准备验证](../../validation/2026-08-19-pilot-008-preparation.md)。

## 后续重构

本 Plan 的装置准备事实保留，但其固定 Skill 字节假设在任何模型样本启动前被 ADR-0005 取代。
Pilot 008 不得按本 Plan 的 P/R 成本门执行；活动工作见
[Scope Acquisition 重构 Plan](2026-08-19-scope-acquisition-pilot-008.md)。
