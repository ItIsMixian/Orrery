# Orrery Context Aperture v0.1（上下文光圈）

> 状态：候选设计，确认性 B/C 质量门未通过，尚未形成 ADR  
> 依据：pilot-001、pilot-002、pilot-003、B/C 确认轮与任务上下文研究笔记  
> 边界：不修改发布版 Skill，不宣称已经拥有精确文件访问审计

## 目标

让 Agent 先以完成任务所需的最小证据工作，同时在依赖、风险或验证结果表明证据不足时，有纪律地扩大上下文。它既不采用 A 的固定全文阅读链，也不把 C 的两个文件变成不可突破的硬上限。

核心原则是：**默认缩小，按证据扩张，先声明后读取，以验证决定是否继续扩大。**

## 四层光圈

1. **定位层**：读取路径、文件类型、标题、符号和 State 索引等元数据，不把整篇正文送入上下文。
2. **初始证据层**：通常读取 1–2 个最相关文件的必要片段；跨模块任务优先选择一个生产者和一个消费者。
3. **风险扩张层**：遇到直接依赖、权威规则、安全边界或冲突事实时，在读取前记录理由并扩大范围。
4. **验证反馈层**：测试、编译、diff 或验收检查失败时，根据失败证据重新打开光圈，而不是盲目枚举仓库。

初始预算只是光圈起点，不是总读取上限。任务可以扩张，但每次扩张都要留下原因。

## 标准工作流

```text
任务分类
  ↓
路径级定位（不读正文）
  ↓
Context Manifest（初始光圈）
  ↓
选择性读取 / 局部证据
  ↓
Selected Evidence（首次写入前）
  ↓
修改与验证
  ↓
失败？──是──> Scope Expansion ──> 补充证据 ──┐
  │                                          │
  否                                         └─重新验证
  ↓
Access Receipt + Validation
```

## Context Manifest v0.1

```json
{
  "task": {"kind": "cross_module", "risk": "high"},
  "retrievalStrategy": "multi_file",
  "initialEvidence": [
    {"path": "path/to/file.py", "scope": "symbol or line range", "reason": "direct implementation"}
  ],
  "authorityChecks": ["relevant AGENTS/State/ADR only when they constrain this task"],
  "expectedWrites": ["path/to/file.py"],
  "expectedValidation": ["exact command"],
  "initialBudget": {"contentFiles": 2, "preferPartialReads": true},
  "expansionConditions": [
    "direct dependency discovered",
    "security or persistence boundary not yet evidenced",
    "current facts conflict",
    "validation fails",
    "acceptance criterion cannot be proven"
  ]
}
```

Manifest 是检索计划，不是事实证明，也不是永久沙箱。路径枚举不计入正文预算；会输出正文的搜索应计入对应文件。

## 风险规则

| 任务 | 初始光圈 | 写入前最低证据 |
|---|---|---|
| 单文件文档 | 1 个文件 | 目标段落与必须保持的公开边界 |
| 多文件文档 | 1–2 个文件 | 两个入口的对应结构或共享权威来源 |
| 局部代码 | 1–2 个文件 | 目标实现与直接调用契约 |
| 跨模块代码 | 2 个文件起步 | 生产者、消费者以及必要时的共享抽象 |
| 安全／持久化 | 2 个文件起步 | secret source、sink、失败顺序与公开返回面 |
| 架构／迁移 | 相关 State + 有效 ADR 摘要起步 | 当前事实、有效约束与迁移目标 |

高风险任务不强制全文阅读固定七文件链，但必须回答“秘密从哪里来、可能到哪里去、失败时留下什么、对外暴露什么”。若两个初始文件不足，必须扩张。

## Scope Expansion

允许的理由码：

- `dependency-found`
- `missing-authority`
- `security-boundary`
- `conflicting-facts`
- `validation-failure`
- `acceptance-gap`

扩张记录必须在正文进入上下文之前产生，并包含路径、范围和理由。纯粹“可能有用”不能成为扩张理由。

## 证据与审计边界

- Context Manifest、Selected Evidence 和 Access Receipt 属于 Agent 自述。
- Codex JSONL 可以独立证明 Harness 发出了哪些工具／命令事件，但不能证明模型看到了文件中的哪些确切字节。
- Git 证明写入结果，不证明读取行为；并且普通 `git diff --name-only` 不包含未跟踪文件。
- 将来若需要强审计，应在文件工具与模型上下文之间加入受控读取代理，记录规范化路径、范围、内容哈希与返回字节数。

因此 v0.1 的目标是“可解释的检索纪律”，不是“不可绕过的访问控制”。

## 质量门

上下文更少不能自动获胜。候选策略必须同时满足：

1. 允许写入路径和未跟踪文件都被独立检查；
2. 任务指定的测试、编译、diff 与安全断言通过；
3. 高风险任务加入针对失败顺序、环境变量优先级、密钥脱敏和原子写入的专项测试；
4. 依赖召回、实现正确性和安全性不低于宽上下文基线；
5. 任何协议不合规都如实保留，不能在封存后改写回执。

## 建议落地顺序

1. 先把 v0.1 作为实验 overlay，不加入发布版 Skill。
2. **已完成实验设施：** benchmark 现在合并采集受跟踪与未跟踪产品文件，并为 validation 回执使用 v2 明确格式。
3. **已完成实验设施：** 操作者侧安全 Oracle 已覆盖环境变量 `hasKey`、凭据写入失败顺序、明文泄漏、异常脱敏与原子替换；它不依赖 Agent 自己选择测试范围。
4. **已完成确认性 B/C 对照，但未达到采纳门槛：** C 虽少自报一个正文读取文件，却比 B 多用约 75% input token，并在两个高风险任务中都被独立验收发现问题；B 也有一项环境凭据状态缺陷。当前不得提出采纳 ADR。

## 确认轮带来的修订

- “读取文件更少”没有自然转化为“token 更少”；`PO-CR-010-C` 产生了约三倍于 B 的命令事件，选择性策略本身仍可能诱发反复定位和缓存开销。
- C 的初始光圈不能替代高风险接受测试：它漏掉了凭据写入失败顺序，并在另一项任务中违反回执 schema。
- B 在本轮质量更好、开销更低，但仍未全胜；它只能作为下一轮比较基线，不能直接成为发布策略。
- 下一版候选应把 Manifest／回执格式更多交给 Harness 生成或机械校验，并在首次写入前显式验证 secret source、sink、失败顺序和公开状态。

详见 [B/C 确认轮报告](../results/2026-08-18-pilot-003-bc-confirmatory-terra-medium.md)。

下一轮没有重复旧任务。[pilot-004 holdout](../results/2026-08-18-pilot-004-bh-holdout-terra-medium.md) 已用三个新任务完成 B/H 对照，并将“必要扩张召回”和“不必要扩张克制”分开测量。修正后的独立验收中 B/H 都为 3/3，H 的读取行为也更克制；但 H 总 input token 比 B 高 47%，平均耗时高约 15%，未通过成本门。因此 H 不进入 ADR，下一步先拆解长 Manifest、Selected Evidence、重复验证与缓存口径，形成瘦身版 H2。

## 暂不决定

- 是否由 Harness 自动生成 Manifest，还是继续让 Agent 声明；
- 内容预算应按文件、字节、token 还是证据项计量；
- 精确读取审计是否值得引入文件代理的复杂度；
- 多人分支下 Manifest 如何绑定 commit、worktree 与 State 版本。
