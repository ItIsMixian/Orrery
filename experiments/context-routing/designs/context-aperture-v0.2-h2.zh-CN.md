# Orrery Context Aperture H2（瘦身候选）

> 状态：已完成 Pilot 005／006；未通过成本门，不采纳、不形成 ADR
> 前身：Context Aperture v0.1 / Pilot 004 H1
> 产品影响：无；发布版 Skill 保持 v0.2.0 行为

## 问题

H1 在 Pilot 004 中保持了与 B 相同的 3/3 正确性，并减少了自报正文读取，但总 input token 高 47%、平均耗时高约 15%。最明显的可删成本不是“必要源码”，而是模型反复生成和复制：

- 完整 `Context Manifest`；
- 首次写入前的 `Selected Evidence`；
- 最终 Agent receipt；
- 与 Harness 正式验收重复的完整验证叙述。

H2 的假设是：**把声明和审计结构交给 Harness/读取工具机械生成，让模型只为真实扩张提供一个短理由码，可以保留 H1 的检索克制，同时消除大部分协议性 token。**

## H2 工作流

```text
Harness 注入任务事实（允许写入、正式验收、初始预算）
  ↓
Agent 通过代理枚举路径（不返回正文）
  ↓
Agent 通过代理读取 1–2 个切片
  ↓
代理自动记录路径、范围、哈希、字节与顺序
  ↓
需要更多证据？──是──> 调用代理时附一个 reason_code
  ↓
Agent 修改产品
  ↓
Agent 只运行必要的快速反馈；Harness 执行正式验收
  ↓
Harness 从 JSONL + 代理日志生成 Manifest / Receipt；Hook 可用时增加实时阻断
```

## 与 H1 的差异

| 项目 | H1 | H2 |
|---|---|---|
| Manifest | Agent 输出完整 JSON 并复制到回执 | Harness 从任务配置和前两次代理读取生成 |
| Selected Evidence | Agent 输出事实数组 | 取消；路径、范围和返回哈希由代理记录 |
| 扩张理由 | 多行声明 | 代理参数中的短 `reason_code` |
| Access Receipt | Agent 创建 JSON | Harness 汇总 Hook、代理和 JSONL |
| 正式验证 | Agent 执行并叙述，Harness 再验收 | Agent 只做快速反馈；Harness 独立完成质量门 |
| 读取证据 | 主要为 Agent 自述 | 受控工具面内为 `tool_wrapper + codex exec JSONL`；Hook 是可选增强 |

## 初始光圈

- 初始正文预算仍是最多 2 个不同文件，但预算由代理按事件自动计算。
- 路径枚举不计正文预算。
- 第三个文件、扩大既有范围或搜索返回正文时，调用必须包含以下理由之一：
  - `dependency-found`
  - `missing-authority`
  - `security-boundary`
  - `conflicting-facts`
  - `validation-failure`
  - `acceptance-gap`
- 代理拒绝缺理由的扩张；Agent 不需要额外输出解释段落。

## 高风险任务

H2 不要求模型生成长篇安全摘要。任务 Prompt 只保留四个问题作为思考约束：source、sink、failure order、public state。是否满足这些约束由任务专用 Harness Oracle 验收；访问日志只证明模型获得了哪些候选证据，不冒充安全正确性证明。

## 成本口径

下一轮必须分别报告：

- `input_tokens`；
- `cached_input_tokens`；
- `input_tokens - cached_input_tokens`；
- `output_tokens` 与 reasoning output；
- 代理返回正文的 UTF-8 字节数；
- 固定 Prompt/overlay 字节数；
- Agent 墙钟时间与 Harness 验收时间。

“读取文件更少”不能替代这些成本口径。

## 不作出的承诺

- H2 不证明模型理解、记住或依据了返回内容。
- H2 默认拒绝出现 Hosted/MCP/未知 item 的运行；官方说明中可能绕过默认 Hook 或 JSONL 的专用路径不属于实验工具面。
- H2 不进入发布 Skill，除非新任务质量门通过且用户接受后续 ADR。
- H2 不要求普通用户安装监控层；读取代理首先只是 benchmark apparatus。

## 实验结果

两个新高风险任务上，B 与 H2 均通过 2/2 独立验收；经 v3 只读复核，四个 Pilot 006 run 的访问证据也全部有效。H2 相对 B 的非缓存 input 下降 31.9%，但总 input 增加 18.5%、output 增加 22.5%、代理正文增加 23.7%、Agent 时间增加 7.2%。

因此本设计触发停止条件：不继续叠加更多 H2 回执格式，不进入发布 Skill。完整说明见 [Pilot 005 / 006 结果](../results/2026-08-18-pilot-005-006-bh2-terra-medium.md)。
