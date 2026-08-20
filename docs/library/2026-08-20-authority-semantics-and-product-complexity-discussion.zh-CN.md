# 网页讨论摘录：Authority Semantics、产品核心与复杂性边界

Status: Discussion capture; non-authoritative

Captured: 2026-08-20

Source: 维护者提供的网页端讨论整理；未进行外部研究或源码复核

> 本记录保存产品认识与候选架构方向，不自行修改 Seed、ADR、Approved Design、State 或发布事实。若后续要把 Authority Model 提升为正式 Core 抽象，仍需通过适用的 ADR、Design、Plan 与 Validation。

## 1. Orrery 的产品核心

Orrery 最有辨识度的部分不是 AI Q&A、RAG 或 dashboard，而是它为项目知识规定了不同角色，并要求这些角色不能互相冒充：

```text
Intent
  ↓
Decision
  ↓
Plan
  ↓
Implementation
  ↓
State
  ↓
Validation
```

最核心的不变量是：

> **Accepted ≠ Implemented ≠ Validated**

同类区分还包括：

- planned ≠ current
- historical ≠ effective
- observed ≠ authoritative

Git 擅长回答“发生过什么”；Orrery 更希望回答：

- 现在什么算数？
- 为什么算数？
- 什么只是计划？
- 什么已经实现？
- 什么有证据证明？

这套权威角色与关系，是 Orrery 的核心 intellectual value。AI、检索、观测台和多 Agent 协调都应消费并投影它，而不应成为新的事实源。

## 2. 用户 Seed 与 Orrery Authority Semantics

用户项目里的 Seed 描述产品最根本的目标、价值和长期原则。例如游戏项目可以写：

- 玩家应该始终感到弱小；
- 光是一种资源；
- 怪物应该可学习但不可完全预测。

Orrery 自身还需要一层更高阶的 meta layer，描述 Orrery 解释和运行项目权威链的元规则，包括但不限于：

- Seed、ADR、Design、Plan、State、Validation、Snapshot 分别是什么；
- 各 authority object 自己的 lifecycle，以及不同角色的 claim 如何引用、约束、失效、被 supersede 或获得证据支持；
- accepted／implemented／validated 等状态词如何区分；
- historical／effective、planned／current、observed／authoritative 如何判定；
- Canonical／Candidate／Worktree／Local-only 等事实作用域如何影响结论；
- 哪类来源能构成事实、证据、批准或仅是派生投影；
- Viewer、AI、CLI 和 coordinator 在什么边界内消费和呈现同一套语义。

讨论中将它称为：

> **Orrery Authority Semantics / Authority Model**

关系可以表达为：

```text
Orrery Authority Meta Model
  roles / relations / invariants / scopes / evidence rules / model version
          ↓ interprets and validates
Project Authority Instance
  Seed / ADR / Design / Plan / State / Validation / Snapshot
          ↓ describes
Implementation / configuration / assets / data / external state
```

因此，“Orrery semantics 定义 Seed 是什么”只是一个例子，不是 Meta Model 的全部职责。它描述 Orrery 的整套 authority runtime semantics；用户定义自己的项目内容。Authority Model 不是又一种作者文档，而是解释、校验和约束现有文档角色及事实来源的领域语义。

维护者于 2026-08-21 进一步澄清：Meta Model 不应被缩窄为 Seed 类型说明，它应被理解为 Orrery 的 domain kernel／interpreter。该澄清已通过 ADR-0009 正式化，但尚未形成代码实现。

## 3. Self-hosting 为什么容易混淆两者

Project Orrery 正在使用 Orrery 管理自身：

```text
Orrery Protocol
      ↓ manages
Project Orrery Product
```

所以 Project Orrery 的 Product Seed 可能恰好包含 “Accepted does not mean implemented”，而同一句话又成为 Authority Semantics 的核心规则。

在自托管项目里：

```text
Product Seed
    ↓ motivates
Protocol semantic rule
```

两者可能高度重叠；普通用户项目通常不会有这种重叠。后续设计必须按职责而不是按字面相似度区分 Product Seed 与 Protocol semantics。

## 4. Domain／Authority Semantics 要解决的问题

抽离 semantics 的目的不是增加文档类型，而是防止不同组件分别实现一套 Orrery 规则。未来消费者可能包括：

- CLI
- Viewer／Static site
- AI Q&A
- Codex Skill 与其他 Agent integration
- Multi-Agent coordinator

理想依赖方向是：

```text
Markdown
   ↓
Parser
   ↓
Orrery Domain / Authority Model
   ↓
─────────────────────────────
CLI   Viewer   Agent   Coordinator
```

应避免：

- CLI 自己判断什么是有效 ADR；
- Viewer 再实现一次状态关系；
- AI Prompt 重新解释一套权威规则；
- Multi-Agent coordinator 又复制一套当前事实判定。

否则 accepted／implemented／validated、effective ADR、State 当前性等规则会在组件之间漂移。真正值得形成稳定 Core 抽象的是 Authority／domain semantics，而不只是因为某个 Python 文件过长。

维护者随后提供的外部复核进一步指出：Decision、Implementation 和 Validation 不应被压缩为 `planned → implemented → validated` 单一状态机。它们是独立但相关的 claim dimensions；Meta Model 只分别定义各 authority object 的 lifecycle，并描述跨角色 claim 与 evidence 的关系。

同一复核还收紧了三条边界：Authority scope 包含 Canonical／Candidate／Worktree／Local-only／Historical／Unknown，但不包含 Agent ownership、依赖等待和文件 lock；Evidence 规则描述 provider-neutral 类别而不绑定 GitHub Actions 等服务；Viewer／AI 受 derived-view semantic constraints 约束，但布局、颜色和输出章节不属于 Meta Model。

## 5. Observatory “偏 monolithic” 的含义

“偏 monolithic”不是说单体架构天然错误，而是目前若干职责仍集中在较大的文件中，例如：

- `build_docsite.py`
- `serve.py`
- `docsite_qa.py`

未来可能逐渐分离：

- parsing
- authority model
- project model
- rendering
- views
- AI
- server

讨论同时明确：现在不应为了模块化而进行大重构。更合理的做法是等待 stable abstraction 出现，再沿真实变化逐步提取。其中优先级最高的候选不是 UI，而是可被 CLI、Viewer、Agent 和 Coordinator 共同消费的 Authority／domain semantics。

## 6. Experiment infrastructure 与用户产品复杂性

Context-routing 研究产生的 benchmark Harness、Oracle、read proxy、JSONL audit、raw evidence sealing、Pilot 00x 和 retention mechanism，属于 Orrery 开发者的研发基础设施，不是普通用户必须理解的产品概念。

更合适的复杂性分层是：

### Layer 1 — User-facing protocol

用户需要理解：

- Seed
- Decision
- Plan
- State
- Validation
- 正常开发流程

### Layer 2 — Product machinery

用户通常不需要理解内部细节：

- installer／validator
- migration／compatibility
- docsite
- multi-Agent coordination machinery

### Layer 3 — Orrery development infrastructure

由 Orrery 维护者承担：

- benchmark／Oracle
- read proxy／JSONL audit
- experiment treatments
- raw evidence management

需要控制的不是仓库内部是否复杂，而是用户是否被迫承担这种复杂性。内部可以为了可靠性包含复杂研发装置，但默认用户体验必须保持轻量、渐进披露，并把开发者实验基础设施隔离在产品入口之外。

## 7. 当前讨论没有决定的事项

这份摘录没有直接决定：

- Authority Model 的最终 API、schema 或包路径；
- 是否新增正式 ADR 来命名该 Core 抽象；
- 现有 Parser、Observatory 或 AI 代码何时重构；
- 各消费者如何通过测试证明使用同一套 semantics；
- Experiment infrastructure 是否需要进一步拆仓或打包。

潜在的后续正式化路径是：先清点当前组件中重复的权威判定，再以行为测试冻结语义，只有在稳定边界出现后才提出 ADR／Approved Design 和渐进提取 Plan。

## 8. 原始摘录边界

维护者提供的原始文本最后停在：

> “甚至成熟产品经常是：为了：”

原始摘录在此中断。本记录不推测或补写其后内容；若维护者以后提供续文，应追加来源说明，而不是把推测写成原讨论结论。

## 9. 决策提炼

本讨论中的维护者判断已被拆分、审计并通过 [ADR-0009：Authority Meta Model、语义一致性与复杂性边界](../decisions/0009-authority-meta-model-and-semantic-conformance.md) 正式化。维护者接受了 AUTH-2／3／5／6／7／8 的限定版本；AUTH-1／4 继续 pending。本 Library 原文继续作为来源记录，不因提炼而获得决策权。
