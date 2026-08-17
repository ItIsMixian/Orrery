# Pilot 004：B/H holdout 任务设计

> 状态：已执行并封存；结果见 `../../results/2026-08-18-pilot-004-bh-holdout-terra-medium.md`  
> 对照：B（现有 Manifest + 理由化扩张）vs H（Context Aperture 混合策略）  
> 基线候选：`ec0ec4a213275338ce34fe7219c5ad692bbcad81`；准备装置时必须重新校验

## 目的

这轮不再重复 `PO-CR-010/011`，也不直接把旧 C 政名为 H。三个主任务要分别回答：

1. H 面对安全边界时，能否读取足够的生产者／消费者证据并保持失败顺序正确；
2. H 面对真正局部的任务时，能否克制在单文件内，而不是为了“保险”枚举整个仓库；
3. H 初始两文件不够时，能否在写入前发现共享规则和第三个消费者，并留下有效扩张理由。

主轮为 3 个任务 × B/H，共 6 次模型调用。`PO-CR-015` 是保留任务，仅在主轮打平、Oracle 争议或局部任务样本不足时启用。

## 主任务矩阵

| 任务 | 风险／类型 | 正文需求形状 | 主要区分点 | 默认进入主轮 |
|---|---|---|---|---|
| `PO-CR-012` | high / security + cross-module | 两文件闭合 | 删除事务、真实失败、环境来源状态 | 是 |
| `PO-CR-013` | high / release，局部代码 | 单文件应足够 | 不必要扩张、缓存原子性、错误脱敏 | 是 |
| `PO-CR-014` | high / cross-module + compatibility | 初始两文件后必须扩张 | 共享规则发现、消费者召回、写入前扩张 | 是 |
| `PO-CR-015` | medium / local concurrency | 单文件应足够 | 并发写入、损坏恢复、克制检索 | 否，保留 |

## 每项任务的证据结构

### PO-CR-012：可恢复的凭据撤销

- Agent 允许修改：`_llm.py`、`serve.py`。
- 最小充分证据：凭据库删除边界与 HTTP 调用者；不应读取前端、README 或更新系统。
- 关键未知：凭据不存在、凭据库失败、旧明文配置、环境变量仍提供 Key 时，状态分别应该怎样变化。
- H 预期行为：初始选择两个文件即可闭合；首次写入前说明 secret source、destructive sink、失败后残留和公开状态。

### PO-CR-013：可信的更新清单缓存

- Agent 允许修改：`check_project_orrery_update.py`。
- 最小充分证据：该文件的 fetch、cache 和 manifest validation 路径。
- 关键未知：过大响应、无效 stale cache、原子替换失败、异常包含 URL query secret。
- H 预期行为：保持单文件光圈；只有发现真实外部规则缺失时才扩张。读取 installer、docsite 或文档正文应被判为疑似不必要扩张。

### PO-CR-014：升级前共享兼容性门

- Agent 允许修改：installer、update checker、validator，并可新增一个无 CLI 副作用的共享兼容性模块。
- 初始证据：installer 与 update checker。
- 必要扩张：发现 validator 的第三份兼容规则，以及 `release-manifest.json` 的实际范围契约后，必须在读取正文前声明 `dependency-found` 或 `missing-authority`。
- H 预期行为：不能把两文件预算当成硬上限；必须在首次产品写入前完成共享规则与全部消费者定位。

### PO-CR-015：并发安全的文档观测台缓存（保留）

- Agent 允许修改：`serve.py`。
- 最小充分证据：同文件内 `_load_cache`、`_save_cache` 与刷新线程。
- H 预期行为：保持单文件；以外部并发 Oracle 验证，不能通过阅读更多文件替代并发与失败注入测试。

## 防泄漏与防过拟合

1. Agent-facing 任务只描述用户可观察契约，不包含 Oracle 的函数名、注入点或断言顺序。
2. Operator Oracle、fixture 和 gold notes 不得进入隔离仓库；prepare 阶段必须从产品基线构建目标仓库，再在仓库外附加 Prompt。
3. 任务没有同仓库 reference patch。正确性以固定的独立 Oracle、允许写入路径和通用验证共同判定。
4. H treatment 必须在 Oracle 代码完成前冻结并 hash；不得看到某项失败后临时补一条只针对该任务的读取规则。
5. 每项任务的 B/H 使用相同模型、reasoning、权限、网络和时间预算，并按任务成对并行；任务顺序由 Harness 在运行前固定随机种子生成。
6. 原始仓库、回执和 JSONL 一经封存不可改写。Oracle 若有缺陷，只能记录 apparatus failure 并用新版本做事后只读复核。

## 计分与决策门

优先级从高到低：

1. 独立任务验收通过；
2. 协议／回执有效，且无越界写入；
3. 必要依赖召回与扩张时机正确；
4. 不必要正文读取和无理由扩张较少；
5. input token、命令事件与实际 Agent 时间较低。

H 只有同时满足以下条件才可进入 ADR 讨论：

- 任务通过数不低于 B，且不能在任何 high-risk 任务上形成 B 没有的安全回归；
- 0 次回执 schema 失败，0 次未声明的正文扩张；
- `PO-CR-014` 的必要消费者全部召回；`PO-CR-013` 不出现无证据的仓库级扩张；
- 三项合计 input token 不高于 B；若单项高出 25% 以上，必须有独立验收可证明的必要扩张收益；
- Harness Oracle 自身通过安全／失败注入 fixture 的正反例测试。

## 尚未实施

- H variant Prompt 与 schema；
- pilot-004 prepare／runner／validator；
- operator-only Oracle 与安全 fixture；
- 基线产品归档和 control-plane 剥离检查；
- 零模型 dry run。

完成以上装置并经人工审阅之前，不得启动这轮模型测试。
