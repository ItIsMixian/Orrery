# 文档治理与信息生命周期

Status: Approved

Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0012](../decisions/0012-document-governance-and-information-lifecycle.md)

## 目标与边界

本设计规定 Project Orrery 作者文档怎样长期保持可读、可定位和可追溯。它不改变 Authority Meta Model 的 role／claim 语义，不增加新的权威文档类型，也不授权工具自动改写 Markdown。

```text
Authority semantics：什么算事实、证据和有效关系
                  ↓
Governance lifecycle：事实在哪个作者入口维护、何时归档或拆分
                  ↓
Read-only tooling：发现偏离并给出证据，由人决定是否处理
```

## 文档角色与保留周期

| 文档 | 当前职责 | 更新触发 | 移出／拆分规则 | 常见异味 |
|---|---|---|---|---|
| `AGENTS.md` | 强制约束、读取链、subsystem 路由 | 入口或硬边界变化 | 细节下沉 State／Design | 重复项目摘要、逐任务历史 |
| `HANDOFF.md` | 当前停止点、风险、恢复与安全接续 | 停止点或风险变化 | 已关闭事项移入 DEVLOG／Validation；不同 subsystem 风险可分入口 | 已解决警告长期保留、接续步骤过时 |
| `PROGRESS.md` | 活动线路、结论、待办、阻塞、近期里程碑 | 集成、里程碑、优先级变化 | 完成史移入 DEVLOG；长期线路链接到 Plan／State | 累计 `[x]` 清单、逐日流水账 |
| State | 当前能力、边界、证据入口、已知缺口 | 实现／外部状态／验证变化 | 过程史移入 DEVLOG；证据按能力聚合；职责分离时拆 subsystem | 完整测试目录、逐提交叙述、计划冒充事实 |
| ADR | 决定与原因 | 长期约束被接受 | 不删除；由后续 ADR amend／supersede | 实现状态写入 Decision |
| Approved Design | 获批规格与边界 | ADR 落成或规格调整 | 明确 lifecycle；新职责可拆 Design | 混入开发日志或临时探索 |
| Plan | 准备怎样实现、检查点和验收 | Design 获批、范围／状态变化 | 完成后保留但退出当前入口 | checklist 被当作实现证据 |
| Validation | 可复现证据与限制 | 验收或回归发生 | 可以累积；索引与 State 聚合定位 | 原始日志无边界复制、结论无命令／环境 |
| DEVLOG | 追加式演化历史 | 完成实现、验证、集成或重要纠偏 | 按日期保留，可在规模需要时按时期分卷 | 当前风险只存在历史中 |
| Snapshot | 带日期的原则／决定／状态／证据截面 | 阶段评估 | 永不替代 live State | 被当作当前事实入口 |
| Library／Backlog／Experiment | 研究、候选和未定方向 | 输入或实验变化 | 只有经采纳才进入 ADR／Design | 派生观点被当作决定 |

## 事件驱动同步矩阵

| 事件 | 必须审查 | 通常更新 | 不应自动更新 |
|---|---|---|---|
| 实现或配置变化 | 相关 State、测试需要 | 实现、State、Validation、DEVLOG | ADR，除非长期约束改变 |
| 验证完成／失败 | State claim 与已知缺口 | Validation、State、DEVLOG | Snapshot、公开能力声明 |
| ADR 接受／替代 | Design 与活动 Plan 是否一致 | ADR 索引、Design／Plan、State 的治理引用 | 实现状态 |
| 功能分支准备集成 | subsystem State、Validation、重叠 | 候选文件；整合者在合流时更新全局入口 | 其他 Agent 的根 PROGRESS／HANDOFF |
| 阻塞、风险或停止点变化 | 当前接续是否仍正确 | HANDOFF、必要时 PROGRESS | DEVLOG 中既有历史 |
| 里程碑完成 | 当前入口中已解决内容 | PROGRESS、DEVLOG、Validation；必要时 HANDOFF | 删除 ADR／Validation |
| 发布 | 实现、验证、版本与远端证据 | release State、公开文档、Validation、DEVLOG | 以本地 Candidate 冒充 released |

## 当前入口维护算法

维护者或整合者在事件发生后按以下顺序判断：

1. 这段信息是当前事实、当前动作、安全接续，还是历史／证据？
2. 它的权威角色和 fact scope 是什么？
3. 当前入口是否只需一句结论加权威链接，而不是复制完整证据？
4. 该信息的责任、更新节奏或所有者是否与现有文档不同？若是，拆分 subsystem／Design／Plan，而不是按字数机械切片。
5. 原入口中的旧内容是否已解决或失效？若是，确认历史去向后移出当前入口。

压缩必须保留有效安全边界、未决风险、当前计划链接和证据入口。任何无法确认的内容保持不动并产生 review finding。

## Soft budgets 与 finding contract

首版不把任何固定行数写成协议语义。项目可以配置 advisory threshold，工具也可以报告增长趋势、与同角色文档的相对异常和高密度信号。阈值命中只意味着“需要审查”，不等于文档错误。

只读 finding 至少包含：

| 字段 | 含义 |
|---|---|
| `finding_id` / `rule_id` | 稳定身份和产生规则 |
| `document` / `scope` | 文件与 Canonical／Candidate／Worktree 观察作用域 |
| `category` | role-boundary、current-history、evidence-duplication、staleness、link-integrity、metadata、growth 或 ownership |
| `severity` | `info`、`warning` 或 `review-required`；不是 Authority status |
| `observed` | 可复核的机器观察值，不含模型猜测 |
| `evidence` | 行、链接、hash 或 Git／工具元数据入口 |
| `suggested_destination` | 可选的人类处理建议，不是写入指令 |
| `generated_at` / `tool_version` | 生成时间和工具版本 |
| `uncertainty` | 证据不足时显式 Unknown |

建议的审计类别包括：当前入口积累完成史或关闭风险；State 混入 Plan／逐检查点历史；失活 Plan；必要链接断裂；结构化字段误用；并发 Workstream 争写全局入口；无职责变化却显著增长；证据链接过期或与 revision 不一致。

## 人工审查闭环

```text
audit observation → non-authoritative finding → maintainer/integrator review
       ├─ acknowledge / defer / tune soft budget
       └─ manually update or split authored documents → validation + synchronization
```

Finding 的确认状态属于治理运行数据，不得反向成为 ADR、State 或 Validation 成功。未来 Observatory 可以展示 finding 和确认状态，但不能提供无需本机确认的文档改写执行权。

## 安全、隐私与协作

- 审计默认 zero-network，只读取目标仓库允许的文档和 Git 元数据。
- 不同步完整 Prompt／回答／transcript、源码正文、未 push diff 或凭据。
- 功能分支只维护受影响 subsystem 文档；唯一整合者维护根入口。
- Local-only finding 必须标明设备／worktree 来源；无法跨机器证明的关系保持 Unknown。
- 自动修复、周期性后台重写和 LLM 自由文本替换均不在本设计范围。

## 兼容与渐进落地

现有 Markdown 无需迁移即可继续有效。第一阶段只让 Project Orrery 自身采纳规则；第二阶段建立只读 contract／fixture；第三阶段才考虑 Core／CLI audit 和 Observatory 投影；发布模板和 Adapter 更新必须经过独立 Validation 与发布选择。

## 验收标准

- ADR-0012、本文、活动 Plan、Documentation State 和索引互相可达。
- PROGRESS 继续只承担当前控制面；历史留在 DEVLOG／Validation。
- 当前实现没有自动文档改写、网络同步、公开模板或 release 变化。
- 后续工具的输出边界明确为 non-authoritative finding。
- 自托管结构、全仓测试、静态站和本地链接仍通过。
