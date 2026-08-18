# Pilot 005 / 006 B/H2 对照结果

> Date: 2026-08-18
> Model: `gpt-5.6-terra` / `medium`
> Baseline: Project Orrery v0.2.0, `20fc95be7b9616fa2de90fc1ffe33b35d5c3f3fd`
> Product authority: none; this report does not change the released Skill

## 结论

Pilot 005 是装置失败，只用于解释为什么需要 Pilot 006。Pilot 006 在两个新高风险任务上让 B 与 H2 都通过了 2/2 独立验收；经 v3 只读访问复核，四个运行也都满足受控读取证据要求。

H2 仍不采纳。相对 B，H2 的非缓存 input 降低 31.9%、固定 Prompt 降低 2.9%，但总 input 增加 18.5%、output 增加 22.5%、代理正文增加 23.7%、Agent 墙钟增加 7.2%。这违反了预先冻结的“总 input token 不高于 B”质量门。发布 Skill、AGENTS 模板和文档权威链保持不变，也不新增 ADR。

## 任务

| Task | Risk | Goal |
|---|---|---|
| PO-CR-025 | high | 阻止 installer 通过符号链接／junction 把受管文件写出目标根 |
| PO-CR-026 | high | 为 installer、validator 与 release manifest 建立共享的版本化 managed-tools 契约 |

任务、B/H2 Prompt、Oracle、模型、reasoning effort、baseline 和成本口径均在运行前冻结。两种变体具有相同写入权限与正式验收，差异只在路由协议。

## Pilot 005：保留的装置失败

四个 run 全部按 `contaminated` 封存。共同装置问题包括：

- Windows CLI 将允许命令包装为 `pwsh -Command`，v1 validator 未归一化；
- file-change 事件报告绝对路径，策略使用仓库相对路径；
- 归档式隔离仓库缺少正式测试所需 Git 历史；
- PO-CR-026 的冻结 Oracle 对契约键名存在歧义；
- 已批准但失败的快速验证命令被错误归入“访问装置失败”。

因此 Pilot 005 的 token、读取量和候选失败不能用于比较 B/H2。原始结果未重分类、未覆盖、未删除。

## Pilot 006：修正后的确认轮

### 原始封存状态

- PO-CR-025-B 与 PO-CR-025-H2：原始装置、协议、正式验证和任务 Oracle 均通过。
- PO-CR-026-B 与 PO-CR-026-H2：任务 Oracle、协议和正式验证通过；冻结 validator 因 Windows 文本 stdout 把 CRLF 翻译为 CRCRLF而各报一个哈希假阴性，所以原始分类保持 `contaminated`。
- 四份 `raw-evidence-manifest.json` 在后续复核前后均通过校验：文件数分别为 211、211、213、213。

### v3 只读访问复核

复核没有向封存目录写文件，也没有更改原分类。它同时要求：

1. 代理日志声明的 `returned_sha256` 与模型侧输出元数据一致；
2. 捕获正文的 raw、LF 规范形式或可逆的 Windows 文本 stdout 恢复形式之一与该独立哈希一致；
3. 未出现未批准命令、未知 item、失败代理读取、意外写入、缺失或重复证明。

复核版本：

- `validate_cli_events.py`: `f4d4abd924efa06b337c308b70012a7daa7117ccefa9f3eb92a151b95971d4e9`
- `hook_audit.py`: `d4b23b5d79c2b6587b114cb770f068a7437fa8ad40acc759d48e66ea0cb091f5`

| Run | Corrected access | Reads proved | Proxy bytes | Acceptance |
|---|---:|---:|---:|---:|
| PO-CR-025-B | pass | 1/1 | 7,388 | pass |
| PO-CR-025-H2 | pass | 2/2 | 12,716 | pass |
| PO-CR-026-B | pass | 3/3 | 15,092 | pass |
| PO-CR-026-H2 | pass | 3/3 | 15,092 | pass |

失败的已批准 post-write 快速验证仍记录在复核输出中，但不伪装成访问越界；正式 Harness 验收是候选正确性的权威证据。

## 聚合成本

| Metric | B | H2 | H2 vs B |
|---|---:|---:|---:|
| Corrected acceptance | 2/2 | 2/2 | equal |
| Total input tokens | 851,194 | 1,008,927 | +18.5% |
| Cached input tokens | 759,040 | 946,176 | +24.7% |
| Non-cached input tokens | 92,154 | 62,751 | -31.9% |
| Output tokens | 11,417 | 13,985 | +22.5% |
| Reasoning output tokens | 3,416 | 4,426 | +29.6% |
| Prompt bytes | 9,965 | 9,675 | -2.9% |
| Proxy returned bytes | 22,480 | 27,808 | +23.7% |
| Agent seconds | 705.479 | 755.930 | +7.2% |

H2 确实把一部分非缓存协议成本移出了模型输入，但没有降低总上下文成本；缓存 input 的增加淹没了这项收益。样本只有两个高风险任务，因此本报告只否决“当前 H2 已达到采纳门”，不声称对所有模型或任务类型存在普遍定律。

## 决定

- 不采纳 H2，不创建 ADR，不修改发布 Skill。
- 停止为 H2 叠加更多模型回执格式。
- 保留受控读取代理、独立 JSONL validator、原始证据封存和 CRLF 回归测试，作为研究 Harness，而不是普通用户运行时要求。
- 后续路线回到更简单的“固定入口／任务定位 + Harness 外部专项验收”，若再提出候选，必须形成新的假设和新 Pilot。

## 原始证据边界

R0 原始根位于 `D:\coding warehouse\project-orrery-benchmark`：

- `pilot-005-bh2-terra-medium-r1`
- `pilot-006-bh2-terra-medium-r1`

原始 JSONL、隔离仓库和 Provider 输出不进入 Git。本文件是 R2 结论；它引用校验和状态和聚合指标，不替代 R0。
