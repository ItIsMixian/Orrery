# Scope Acquisition Router S v0.1

Status: proposed research candidate; not accepted product policy
Date: 2026-08-19
Governing research boundaries: [ADR-0002](../../../docs/decisions/0002-real-development-benchmark-portfolio.md),
[ADR-0005](../../../docs/decisions/0005-prewrite-scope-acquisition-input.md)

## 问题

维护者关心的不是 Project Orrery Skill 文件单独有多短，而是 Agent 收到真实开发指令后，为定位相关
子模块、当前 State、必要决定、实现源和测试，直到准备首次产品写入为止累计消耗了多少 input。

线性入口会让每项任务先读 HANDOFF、PROGRESS、Seed 和 State，再进入实现。对一个边界清晰的子模块
修复，这些全局入口中的一部分只在交接、冲突或长期理由出现时才有价值。单纯缩短 Skill 固定 Prompt
无法证明 Agent 更快锁定实现范围，完整任务总 token 又会混入实现、测试和返工。

## 对照定义

- `P`：完整冻结 Skill + 当前 fixture 的线性 `AGENTS.md`，按固定顺序读取全局入口后再进入相关 State
  与实现。
- `S`：使用相同完整冻结 Skill，只把目标仓库 `AGENTS.md` 替换为任务优先的模块路由索引。入口直接
  指向模块 State、实现和测试；HANDOFF、PROGRESS、Seed、ADR 与 Plan 仅在任务类型、冲突、风险或
  事实同步确实需要时深入。

两组使用相同任务 Prompt、Skill 正文、fixture 代码、Oracle、模型、推理强度和工具边界。这样首先
隔离“项目入口路由”对 Scope Acquisition 的影响；旧 Skill Entry Router R 作为独立研究草案保留，
不再是 Pilot 008 的 treatment。

## 被动测量

Agent 不输出 Manifest、Scope Receipt、Selected Evidence、Access Summary 或扩张回执。Harness 从
app-server JSON-RPC 事件流与代理日志中派生：

1. 找到首个允许产品路径的 `item/started` + `fileChange`；
2. 取该事件之前同一 thread／turn 的最后一份单调 `thread/tokenUsage/updated.total`；
3. 报告 Scope Lock 前累计 input、cached input、non-cached input、output 和 reasoning output；
4. 以写入前已完成代理命令中的独立哈希 proof 统计读取切片、唯一路径和唯一正文 bytes；
5. 继续报告整轮 usage、墙钟、最终正文和 Oracle，防止把成本转移到实现阶段。

若没有逐响应 usage、首次写入事件、同 turn 对齐或已验证事件顺序，精确分段指标必须为
`unavailable`，该 run 不得支持采纳。

## Pilot 008 假设与冻结门

只有 S 三项任务全部通过、质量不低于 P、没有 P-only 高风险成功、首次写入都在允许范围且六个 run
的 Scope Lock 测量有效，才进入成本判断。

- S 聚合 `input-to-scope-lock` 不高于 P 的 85%；
- 任一高风险任务的 S/P 写前 input 不高于 105%；
- S 聚合写前 non-cached input 不高于 P；
- S 写前唯一正文 bytes 不高于 P 的 105%，并分别报告读取路径与层级；
- S 完整任务 input、output、Agent 时间和代理正文不高于 P 的 105%；
- 没有通过漏读数据／安全约束、错误扩大范围或省略必要事实同步换取下降。

通过自动门仍不等于采纳。正式运行后必须生成 R2，由维护者明确接受，再决定是否提出产品 ADR。

## 当前装置边界

本机 Codex app-server schema 暴露逐响应累计 usage 和 `fileChange` 生命周期事件；旧
`codex exec --json` 只暴露整轮 usage。Smoke 002 已在 `codex-cli 0.148.0-alpha.15` 上证明 usage 更新
确实先于首次产品写入事件，并要求每次正式运行以精确版本兼容 preflight 失败关闭。该 smoke 的
策略允许 0 次写前代理读取，只证明 ordering，不证明内容交付；正式 app-server transport、代理
proof、R0 封存与汇总仍需实现，缺少其中任一项的正式 run 都必须把分段指标标为 `unavailable`。
