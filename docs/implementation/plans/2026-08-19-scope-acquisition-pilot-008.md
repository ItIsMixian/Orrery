# 实施计划：Pilot 008 Scope Acquisition 重构

Status: Stopped — first formal pair sealed; apparatus and Oracle defects require Pilot 009
Date: 2026-08-19
Governing ADRs: [ADR-0002](../../decisions/0002-real-development-benchmark-portfolio.md),
[ADR-0005](../../decisions/0005-prewrite-scope-acquisition-input.md)
Approved Design: [真实开发上下文路由基准](../../design/real-development-context-routing-benchmark.md)
Research candidate: [Scope Acquisition Router S v0.1](../../../experiments/context-routing/designs/scope-acquisition-router-v0.1.zh-CN.md)

## 目标

保留 Pilot 008 已通过控制的两项代码任务、一项事实对齐任务、脱敏 fixture、Oracle 和嵌套隔离，
把 treatment 从“缩短 Skill 固定入口”改为“线性项目入口 P 与任务优先入口 S”。Harness 被动统计
首次产品写入前累计 input；不要求 Agent 输出 Manifest 或回执。

## 工作包

- [x] 将 `input-to-scope-lock`、被动 Harness 和精确度边界写入 ADR-0005 与 Approved Design。
- [x] 实现 app-server 事件分析器：首次产品写入、边界前最后 usage、单调性、thread／turn 对齐和写前代理 proof。
- [x] 为精确值、缺失 usage、非单调 usage、错误写入路径和旧 `codex exec` 聚合流增加确定性测试。
- [x] 冻结 P 线性入口和 S 任务优先入口；两组共享同一完整 Skill、任务、fixture、模型和 Oracle。
- [x] 移除 Pilot 008 对固定 Skill 字节的主成本门，改为 Scope Lock 前 input 门和完整任务护栏。
- [x] 在 app-server transport 和真实事件顺序尚未验证时，让正式执行失败关闭；dry-run 只证明静态装置。
- [x] 运行 Oracle controls、嵌套 preflight、专项测试、benchmark、结构、静态站、链接与 diff 验证。
- [x] 同步 State、PROGRESS、DEVLOG、HANDOFF 和独立 Validation。

## 兼容性出口

确定性自测本身不证明真实 Codex app-server 的事件顺序；Smoke 002 已在当前版本上补足 ordering 证据。
开始三对 P/S 样本前，正式 transport 还必须验证：逐响应 usage 单调、对应模型调用的 usage 更新先于首次
`fileChange`、代理 proof 可与写前命令对齐、完整事件流可封存。任一条件失败时只记录 `unavailable`，
不回退到估算 token；装置完成后，模型样本仍需维护者另行确认。

- [x] Smoke 001 启动一个隔离 app-server turn 并封存原始事件；因复制的 CLI 缺少同版本 code-mode host，
  没有产生命令或 `fileChange`，按 `contaminated` 保留，不能判断顺序。
- [x] 将 Windows runtime sibling 检查和 2-case ordering self-test 加入 smoke runner。
- [x] 维护者再次确认后运行修正后的 Smoke 002；同版本 runtime 下 usage event 60 先于首次
  `fileChange` event 62，ordering-only analyzer 报告 exact，原始 manifest 39/39 有效。
- [x] 将 ordering capability 标记为 verified，并引用 Smoke 002 Validation 与原始 run id。
- [x] 实现 Pilot 008 正式 app-server transport、真实 proxy proof 对齐、R0 封存和成对失败关闭。
- [x] 启动首对 `PO-CR-031`；P 因仓库外已安装 Skill 读取而 contaminated，P/S 又共同暴露冻结 Oracle
  的索引名和文档词形假设，runner 按设计停止后续任务。
- [x] 保持两份 R0 证据只读，并把装置修正移入新 Pilot 009；Pilot 008 不产生采纳结论。

## 完成出口

Pilot 008 以装置停止完成，不产生 R2 采纳比较。修正后的正式样本使用 Pilot 009 和新的仓库外输出根；
即使自动门通过，仍需 R2 和维护者明确接受，才能讨论发布 Skill 或模板变化。
