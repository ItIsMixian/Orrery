# 原始实验证据保留策略 v0.1

> 状态：候选研究策略；尚未形成项目级 ADR
> 原则：原始证据留在仓库外，仓库只保存可复核的脱敏派生物与结论

## 三层证据

### R0：受限原始层

位置：仓库外 benchmark 根。包含 Codex JSONL、stderr、Hook 日志、代理日志、隔离仓库、Oracle 输出和产品 diff。

- 默认敏感等级：`restricted`；
- 文件以相对路径、大小和 SHA-256 写入 `raw-evidence-manifest.json`；
- sealing 后不原地改写；只读复核产生新派生文件并引用原 manifest；
- 禁止提交 Git、附加到公开 Release 或复制进 `docs/`。

### R1：脱敏可移植层

位置：`experiments/context-routing/runs/`、`results/`，或将来的私有归档。

只允许包含：任务/Prompt/overlay 哈希、模型与执行配置、相对路径、事件统计、内容哈希、返回字节数、验证结果、脱敏 diff 摘要和操作者结论。不得包含凭据、本机绝对路径、完整源码正文、Provider 隐藏内容或用户聊天历史。

### R2：权威结论层

位置：State、Validation、Snapshot、ADR。

这里只记录当前研究事实、质量门和决定；不得把 R0 的存在误写成产品已实现精确审计。

## 默认保留期

| 分类 | 默认期限 | 到期动作 |
|---|---:|---|
| `contaminated` | 30 天 | 先确认已有 apparatus failure 摘要，再允许人工删除 |
| `exploratory` | 90 天 | 确认 R1 派生物和校验存在，再允许人工删除 |
| `decision_supporting` | 365 天 | ADR 被替代且复核窗口结束后人工复查 |
| `release_supporting` | 不自动到期 | 发布仍受支持时保留；必须人工变更分类 |

工具默认只报告 `active / due / expired`，不自动删除。删除属于单独的破坏性维护操作，必须由维护者明确触发并记录删除清单。

## Manifest 最低字段

- schema version、pilot/run ID、分类、敏感等级；
- 创建时间、到期时间、源仓库 commit、apparatus 版本；
- 每个文件的相对路径、字节数、SHA-256；
- R1 派生物路径与哈希（若存在）；
- sealing 工具版本和验证结果。

Manifest 不保存原始根的绝对路径，移动整个 run 目录后仍应可验证。

## 脱敏出口门

R0 导出到 R1 前至少检查：

1. Windows 和 POSIX 绝对路径；
2. API key、Bearer token、Cookie、credential-store 内容；
3. 源码正文、Prompt 中未授权的用户数据与工具响应全文；
4. Git remote、用户名、设备名和临时目录；
5. 每个派生文件可回到 R0 manifest 的哈希或生成记录。

自动扫描只能作为下限；存在源码正文或异常栈时仍需人工审阅。

## 与 H2 的关系

读取代理只在 R0 保存完整 Hook/tool 证据；进入 R1 的读取事件只保留相对路径、范围、哈希和字节数。这样可以证明实验统计没有凭空生成，同时不会为了审计把整个代码上下文再复制进 Git。
