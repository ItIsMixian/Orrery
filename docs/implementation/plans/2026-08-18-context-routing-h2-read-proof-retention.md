# Context Aperture H2、读取证明与证据保留实施计划

Status: completed; H2 not adopted
Updated: 2026-08-18
Authority: implementation intent; does not change the released Skill

## 目标

把 Pilot 004 留下的三个问题作为一套研究设施处理：

1. 设计比 H1 更低开销的 Context Aperture H2；
2. 让 Harness 在受控本地工具面内独立记录实际返回给模型的内容切片；
3. 为仓库外原始 JSONL、Hook 日志、隔离仓库和 Oracle 输出建立可校验、可过期、可脱敏导出的保留规则。

本计划不修改 `skills/project-orrery/`，也不提出采纳 ADR。只有新候选通过预先定义的正确性、成本与审计质量门后，才能另行决定是否进入产品。

## 适用约束

- Seed 7：研究先于采纳。
- Seed 8：精确访问证明不能依赖 Agent 自述。
- Seed 9：新增协议必须证明收益覆盖维护和 token 成本。
- `docs/state/context-routing-research.md`：H1 正确性持平但总 input token 高 47%，不得直接重跑。
- `docs/state/project-structure.md`：大型原始运行继续位于仓库外，不批量复制进 `docs/`。

## 工作包

### WP1：H2 成本假设

- [x] 将长篇 `Context Manifest`、`Selected Evidence` 和 Agent 自写回执从模型职责移出。
- [x] 用读取代理的调用参数同时表达路径、范围和扩张理由。
- [x] 将正式验收继续留在 Harness，避免 Agent 为证明自己而重复执行完整质量门。
- [x] 建立无模型 fixture，并让代理／validator 直接报告返回正文和事件证据字节；正式 Prompt 成本留到新任务冻结时计算。
- [x] 选择 PO-CR-025／026 两个新任务做 B/H2 小样本，不复用 Pilot 004 holdout 作为“新任务”。

### WP2：最小内容读取代理

- [x] 实现受限路径枚举与 UTF-8 文本切片读取。
- [x] 每次返回前记录规范化路径、范围、源文件哈希、返回内容哈希和字节数。
- [x] 实现 `PreToolUse` 阻断和 `PostToolUse` 响应交叉核验，并以单元测试证明脚本语义；真实 Windows CLI 0.147.0 Hook 未触发，因此只作为可选增强。
- [x] 提供 `codex exec --json` 独立 validator：事后拒绝任何未批准命令／未知 item，并把命令输出与代理哈希交叉核验。
- [x] 明确证明范围只覆盖隔离 Harness 的受控本地工具面，不证明注意或理解。

### WP3：原始证据保留

- [x] 建立原始证据 manifest schema 与默认保留等级。
- [x] 实现 seal/verify/status；默认只报告过期，不自动删除。
- [x] 定义原始受限层、脱敏可移植层和仓库内结论层之间的单向派生关系。
- [x] 为本机绝对路径、凭据、源码正文和 Provider 内容设定禁止发布规则。

### WP4：验证与下一轮门槛

- [x] 单元测试覆盖路径穿越、符号链接、哈希、行范围、Hook 拦截、Hook 响应证明、JSONL 独立审计和 manifest 校验。
- [x] 在临时仓库运行不改产品的 Codex CLI 烟雾实验；确认 0.147.0 的 JSONL 格式可用于独立证明，同时记录非交互 Hook 未触发的兼容性缺口。
- [x] 运行现有 Project Orrery 测试和 benchmark validator，证明新设施没有改写封存证据。
- [x] 在装置阶段更新 State、PROGRESS、DEVLOG、HANDOFF，并在正式 Pilot 后再次同步完成结论。
- [x] 运行 Pilot 005 并保留共同装置失败；在 Pilot 006 修正共同 Harness 后完成 B/H2 确认轮。
- [x] 以 v3 规则只读复核 CRLF stdout 假阴性；原始 seal 和分类保持不变。
- [x] 按冻结成本门作出停止决定：H2 总 input 比 B 高 18.5%，不进入采纳讨论。

## H2 质量门

H2 只有同时满足以下条件才可进入采纳讨论：

1. 新任务独立验收正确性不低于 B；
2. 必要依赖召回和高风险失败顺序不低于 B；
3. 总 input token 不高于 B，且非缓存 input、模型输出、代理返回字节和墙钟时间分别报告；
4. 不再要求 Agent 复制完整 Manifest、Selected Evidence 或 Access Receipt；
5. 所有计入“内容读取”的事件均有 `tool_wrapper` 与完整 `codex exec --json` 命令输出交叉证据；Hook 可用时再增加 `PostToolUse` 证据；
6. 任何 JSONL 未覆盖路径、外部上下文、未知 item 或直接读取尝试都会使 apparatus 标记失效或污染，而不是降级为 Agent 自述。

## 停止条件

- 如果当前 Codex CLI 不能稳定在 `PostToolUse` 提供模型侧工具响应，使用完整 JSONL 事件流做事后独立证明；若 JSONL 也不能覆盖受控工具面，才停止强证明路线。
- 如果阻断策略妨碍正常编辑或验证，不扩大到通用产品功能；先把实验缩回只读 micro-task。
- 如果 H2 仍比 B 昂贵，不继续叠加更多回执格式；回到“固定入口 + Harness 外部验收”的更简单基线。

## 完成结论

停止条件已触发。B/H2 在两个新高风险任务上均通过 2/2 独立验收，但 H2 的总 input、output、代理正文和墙钟时间都高于 B。非缓存 input 的下降没有转化为总成本下降。发布 Skill 保持不变；研究 Harness 和封存规则继续保留，供未来形成不同假设时复用。
