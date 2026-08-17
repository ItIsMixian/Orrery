# Pilot 003 B/C 确认轮 — GPT-5.6 Terra / medium

> 状态：四次执行已封存；正式 validator 返回 1；完成事后 Oracle 复核  
> 权威：仅研究证据，不修改发布版 Skill，也不形成 ADR

## 实验范围

- 模型：`gpt-5.6-terra`
- reasoning effort：`medium`
- 任务：`PO-CR-010`、`PO-CR-011`
- 变体：B、C，共四次独立运行，每次只执行一次
- 任务工具联网：禁用
- 原始证据：`D:\coding warehouse\project-orrery-benchmark\pilot-003-bc-confirmatory-terra-medium-r1`
- Harness 选择：checksummed manifest 明确记录两项任务与 B/C；其余五组不属于本实验，而非缺失运行

四个 Agent 进程都以退出码 0 完成，产生回执和预期产品变更，并通过任务内的 compile、unit tests 与 `git diff --check`。两组都经历 WebSocket 超时并回退 HTTP，因此时间和 token 含明显网络／会话噪声。

## 开销

| 变体 | 完成 | 平均 Agent 秒数 | 平均自报正文读取 | Input tokens | Cached input | Output tokens |
|---|---:|---:|---:|---:|---:|---:|
| B | 2 | 339 | 3.0 | 643,443 | 581,376 | 14,544 |
| C | 2 | 374 | 2.0 | 1,123,807 | 1,033,728 | 16,142 |

C 自报正文读取比 B 少 33%，但 input token 多约 75%，output token 多约 11%。差异主要来自 `PO-CR-010`：C 使用 723,370 input token，B 使用 279,202；JSONL 中 C 的 command execution item 为 30 个，B 为 10 个。这个结果否定了“少读一个文件就必然减少整体上下文成本”的简单假设。

| 运行 | Agent 秒数 | Harness events | Input tokens | 自报正文读取 |
|---|---:|---:|---:|---:|
| `PO-CR-010-B` | 334 | 27 | 279,202 | 3 |
| `PO-CR-010-C` | 419 | 52 | 723,370 | 2 |
| `PO-CR-011-B` | 344 | 45 | 364,241 | 3 |
| `PO-CR-011-C` | 328 | 41 | 400,437 | 2 |

## 独立质量验收

封存时的 validator 正确保留了所有失败，但其中混合了产品缺陷、协议缺陷和 Oracle 自身缺陷：

1. 原 Oracle 只识别同一函数中的 `store_key → save_config`，因此误判了 `010-B` 在 HTTP handler 中先存凭据、再调用 `save_settings` 的分层实现。
2. 原 Oracle 用位置参数调用 `save_config(dict)`，因此无法测试 `011-B` 合法的 keyword-only API；更严重的是，后两个异常路径测试把这个 `TypeError` 误当成预期失败。

Oracle 随后增加了调用签名适配、分层持久化调用识别和稳定检查名称。修复版 SHA-256 为 `eca27cedc32fb63751e0c5e5b4aa6b9f0429fe48d4e7d13e28f916f20dd93d0f`。它只读复核已封存仓库，未修改原始结果：

| 运行 | 修复后独立验收 | 结论 |
|---|---|---|
| `PO-CR-010-B` | 通过 | 凭据先于项目配置持久化，公开状态和错误脱敏通过 |
| `PO-CR-010-C` | 失败 | `save_config` 先写非敏感 JSON，再调用 `store_key`；凭据库失败会留下部分保存 |
| `PO-CR-011-B` | 失败 | 保存后的返回状态忽略环境变量凭据，可能错误返回 `hasKey=false` |
| `PO-CR-011-C` | 失败 | 同样丢失环境变量派生的 `hasKey` 状态 |

此外，`PO-CR-011-C` 的回执使用 schema 未定义的 `target_scope=product` 和 `agent-receipt`，导致写入事件无法计入 contracted product/receipt writes。这是协议合规失败，不是产品代码错误，但仍必须计入变体质量。

## 结论

本轮不支持采纳当前 C 策略：

- B 在两项高风险任务中通过一项，C 两项都未通过独立验收；
- C 没有表现出预期的 token 优势，反而更昂贵；
- C 还多出一次回执 schema 失败；
- B 自身也未全胜，不能直接升级为正式路由策略。

因此 [Orrery Context Aperture v0.1](../designs/context-aperture-v0.1.zh-CN.md) 继续保持候选／实验状态。下一步应先机械生成或预校验 Manifest 与回执，并把高风险 source/sink/failure-order/public-status 检查前移，再用更大且未被当前提示反复调试过的任务集比较。样本只有两项、任务已被多轮使用、网络回退明显，所以本报告只否决“现在就采纳”，不证明 B 在所有项目任务上普遍优于 C。
