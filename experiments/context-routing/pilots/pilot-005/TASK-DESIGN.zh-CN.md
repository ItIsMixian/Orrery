# Pilot 005：任务与质量门

Status: frozen before model execution

## 任务形状

| 任务 | 目标 | 最小充分证据假设 | 区分点 |
|---|---|---|---|
| PO-CR-025 | 安装目标链接防逃逸 | 安装器单文件，必要时第二份迁移契约 | H2 是否能保持局部光圈并通过真实文件系统失败注入 |
| PO-CR-026 | 共享 managed-tools 契约 | installer + validator，随后必须扩张到 release manifest | H2 是否在写前召回第三权威并用 reason code 扩张 |

两种变体使用同一个读取代理和同一个两文件初始预算。这个设计有意只隔离“模型生成协议文本”的成本：B 保留 Manifest／扩张叙述／Access Summary，H2 将它们移到 Harness。

## 质量门

1. 独立 Oracle 正确性与 failure order：H2 不低于 B；
2. apparatus 必须有效，所有正文读取均由代理+JSONL 交叉证明；
3. H2 的必要依赖召回不低于 B，且 PO-CR-025 不因保险而扩张到无关模块；
4. 四次运行分别报告 input、cached input、non-cached input、output、代理字节和墙钟时间；
5. 两项合计 H2 input token 不高于 B；
6. 任一直接读取、未知工具、越界写入、未封存原始证据或 Oracle apparatus error 会污染 run。

本轮只有四次模型调用：每项任务的 B/H2 同时启动，两个任务按固定顺序执行。失败不隐藏重试；需要修复装置时必须新建 pilot revision 和新的原始根。
