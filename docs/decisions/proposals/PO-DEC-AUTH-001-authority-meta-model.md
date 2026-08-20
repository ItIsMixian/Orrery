# PO-DEC-AUTH-001: Authority Meta Model、语义一致性与复杂性边界

Status: Proposed

Date: 2026-08-21

Maintainer disposition: Approved for integration on 2026-08-21

Formal ADR: pending integration-time allocation

Would amend: [ADR-0001](../0001-project-orrery-self-hosting.md) Decision 1 and the self-hosting boundary

Would extend: [ADR-0004](../0004-platform-neutral-core-and-adapter-boundaries.md) conformance obligations without yet deciding the single implementation owner

Source discussion: [Authority Semantics、产品核心与复杂性边界](../../library/2026-08-20-authority-semantics-and-product-complexity-discussion.zh-CN.md)

> 本提案只包含维护者已经确认的 AUTH-2、AUTH-3、AUTH-5、AUTH-6、AUTH-7、AUTH-8，并采用 ADR compatibility audit 后的限定措辞。AUTH-1“产品核心定位”和 AUTH-4“Core 是唯一 semantics owner”不属于本提案，继续保持 pending。接受本提案不授权立即代码重构。

## Context

Project Orrery 已经使用 Seed、ADR、Design、Plan、State、Validation 和 Snapshot 区分项目知识角色，也通过 ADR-0004 分离 Core、CLI、Observatory 与 Adapter。但“这些角色是什么、每类 authority object 有什么 lifecycle、跨角色 claim 如何关联／失效／获得证据支持、哪些状态绝不能等同”的规则仍分布在 Markdown 原则、模板、脚本、Viewer 逻辑和 Agent 指令中。

Project Orrery 又在用自身协议管理自身，导致 Product Seed 与通用协议语义可能使用相同句子。如果不显式区分 meta semantics 与项目内容，既可能把 Project Orrery 的产品偏好误当成所有用户项目的 Seed，也可能让 CLI、Viewer、AI 和 coordinator 在不同事实作用域中各自解释一套规则。

需要新增一层概念上的 Authority Meta Model，定义角色与语义，但不增加作者文档类型、不覆盖项目 Seed 内容，也不提前决定最终 API 或代码所有权。

## Decision

### 1. 增加 Authority Meta Model 语义层

Orrery 的语义结构分为三层：

```text
Authority Meta Model
  roles / role lifecycles / claim dimensions / relations
  invariants / authority scopes / evidence semantics / model version
             ↓ interprets and validates; does not override project content
Project Authority Instance
  Product intent / Seed / ADR / Design / Plan / State / Validation / Snapshot
             ↓ describes and constrains
Implementation / configuration / assets / data / external state
```

Authority Meta Model 是 meta-schema／type system 和 authority interpreter：它定义 Seed、ADR、Design、Plan、State、Validation 和 Snapshot 各自是什么，各自 lifecycle 如何表达，跨角色 claim 如何关联、失效、被 evidence 支持，以及哪些作用域和状态词合法。“Meta”表示定义角色与解释规则，不表示它在具体项目内容上拥有高于 Seed 的决策权；项目自己的有效 Seed 仍约束该项目的 ADR 与 Design。

Meta Model 不是新增的作者文档类型。用户继续维护现有文档角色，Orrery 通过规范、解析与验证解释这些实例。

Authority Meta Model 必须具有可识别的语义版本，使消费者能够说明自己使用哪一版规则。它与文件格式／字段层面的 `document_schema` 概念不同；确切字段名、版本策略和兼容范围留给后续 Design。

### 2. 规范不变量、role lifecycle 与非线性 Authority Graph

下列不等式成为 Meta Model 的规范不变量：

- Accepted ≠ Implemented ≠ Validated
- planned ≠ current
- historical ≠ effective
- observed ≠ authoritative

ADR-0001 的完整链：

```text
Product intent → Seed → effective ADR → approved Design
→ implementation → State Docs → Validation → Snapshot
```

表达权威依赖、典型成熟路径和阅读关系，不是所有项目变更都必须逐节点执行的强制 workflow。局部变更可以不新增 ADR／Plan，Validation 可以多次产生，后续 ADR 可以 amend／supersede 早期决定。

Meta Model 可以定义各类 authority object 自己的 lifecycle，例如 ADR 的 Proposed／Accepted／Rejected／Superseded，或 Design 的 Draft／Approved；但不得把 Decision、Implementation 和 Validation 压缩为同一个 feature 状态机。它们是相互关联但独立的 claim dimensions，例如：

```text
decision_status = accepted
implementation_claim = present
validation_evidence = failed
```

此时实现存在仍然是真实 claim，只是尚未证明满足要求。类似地，某实现后来被移除时，历史上的 implemented claim 仍可成立，而当前 State 已经不同。Meta Model 应描述这些 claim 如何被建立、限定作用域、失效、被 supersede 或获得 evidence 支持，不授权一个单值 `planned → implemented → validated` 状态机。

Authority scope semantics 只回答 claim 在哪个 revision／branch／worktree／visibility context 下有效，例如 Canonical、Candidate、Worktree、Local-only、Historical 和 Unknown。Agent ownership、任务等待关系、文件 lock 和调度队列属于 Coordinator runtime model，不进入 Authority Meta Model。

### 3. 同一输入边界下的一致性与 derived-view semantic constraints

Conformance 的一致性前提必须完整表达为：

```text
same authority_model_version
+ same repository snapshot
+ same fact scope
+ same evidence visibility
```

在这些输入相同时，CLI、Viewer、Coordinator 等确定性消费者对 effective／current／implemented／validated 等 Core-derived 状态必须一致。Canonical、Candidate、Worktree 或 Local-only 等输入不同可以得到不同结论，但消费者必须显示作用域、来源和不确定性，不能伪装成同一事实视图。

AI 自由文本不要求措辞、推理过程或自然语言结论完全一致；它只受以下 conformance 边界约束：

- 不能推翻、隐藏或升级 Authority Meta Model 给出的状态；
- 不能把 Unknown／Local-only／observed 写成 authoritative；
- 必须能回到 Core-derived 状态和原始证据链接；
- 不计作独立批准或验证证据。

这些是 derived-view semantic constraints，不是 UI／交互规范。Meta Model 不规定 Viewer 布局、颜色、删除线样式、CLI 文案或 AI summary 的 section 数量；它只规定消费者不能在语义上误报 effective、current、authoritative 或 validated。

### 4. 建立行为级 conformance fixtures

Meta Model 需要版本化 fixture／golden cases，至少覆盖：

- accepted 但未实现；
- implemented 但未验证；
- implementation present 且 Validation failed，二者必须同时保留；
- implementation 历史存在但当前已移除，历史 claim 与 current State 必须分离；
- superseded／amended ADR；
- Draft 与 Approved Design；
- Plan 与当前 State 分离；
- Canonical／Candidate／Worktree／Local-only 作用域；
- Authority scope 与 Coordinator ownership／lock 数据不得混型；
- Snapshot 不替代 live State；
- 派生 Viewer／AI 输出不能产生新事实；
- 相同输入下一致、不同可见性下显式分歧。

这些 fixture 验证语义行为，不要求所有消费者产生相同 UI、文案或自由文本。

Evidence 规则描述 provider-neutral 的证据类别和能力边界，例如 revision content evidence、reproducible executable validation、tool／runtime trace、human／Agent assertion 和 derived summary。具体 Git provider、CI 服务或 Harness 实现可以提供这些类别，但 Meta Model 不规定“只有 GitHub Actions 才算 Validation”等 implementation-specific 条件。

### 5. 渐进提取，不进行大爆炸式重构

接受 Meta Model 不等于立即拆分 `build_docsite.py`、`serve.py` 或 `docsite_qa.py`。先盘点重复判定、建立 golden／conformance tests，再沿稳定边界逐步提取 parsing、authority model 和 project model。

UI、server 与 AI 的模块化只在出现可验证边界时进行；文件长度本身不是重构授权。现有兼容入口、v0.2.0 资产和 State 实现事实保持不变。

### 6. 三层复杂性与渐进披露

Project Orrery 区分：

1. User-facing protocol：Seed、Decision／ADR、Design／Plan、State、Validation、Snapshot 与正常开发流程；
2. Product machinery：installer、validator、migration、compatibility、docsite 与 multi-Agent coordination；
3. Orrery development infrastructure：benchmark、Oracle、read proxy、JSONL audit、experiment treatment 与 raw evidence management。

内部实现和研发装置可以复杂，但普通用户默认只承担完成目标所需的最小协议。这里的“隐藏内部复杂性”表示渐进披露，而不是永久禁止用户查看 Design、Snapshot、高级 Validation 或工具证据。机器可派生信息由 CLI／Harness 处理，实验结构不进入常规用户入口或固定 Agent 上下文。

### 7. Self-hosting 中分离 Product Seed 与 Meta Model

Project Orrery Product Seed 可以启发 Authority Meta Model，两者也可能使用相同句子，但职责不同：

- Product Seed 约束 Project Orrery 这个产品想成为什么；
- Authority Meta Model 约束所有采用 Orrery 的项目如何解释文档角色、事实作用域和证据。

自托管文档和实现不得仅凭文字重合就把 Product Seed 当成可执行 domain schema，也不得让 Project Orrery 当前产品偏好自动成为所有目标项目的 Seed 内容。

## Related judgments still pending

本提案不决定：

- **AUTH-1**：是否将 Authority／当前有效性判断正式声明为 Project Orrery 最主要的产品核心；
- **AUTH-4**：平台中立 Core 是否成为唯一 semantics implementation owner，以及所有消费者必须通过哪个公共 API／CLI 合约使用它。

接受 Meta Model 与 conformance 边界，不等于提前接受这两项产品／代码所有权判断。

## Explicitly unresolved

- Authority Model 的最终 Python API、JSON schema、package path 和类型设计；
- `authority_model_version` 的具体字段、兼容范围和迁移机制；
- Parser、Observatory 或 AI 代码的拆分顺序；
- 是否以及何时改变公共 document schema／Core API version；
- Context-routing experiment infrastructure 是否拆仓；
- 任何立即代码重构、支持状态变化或发布版本。

这些内容必须在后续 Draft／Approved Design、Implementation Plan 和 Validation 中逐步决定。

## Consequences

- ADR-0001 Decision 1 获得“非强制线性 workflow”的正式解释，self-hosting Seed 与通用 semantics 的职责被分开。
- ADR-0004 的消费者与兼容模型增加 Meta Model 版本和 conformance 义务，但本提案尚不决定单一代码所有者。
- 后续组件新增 authority judgment 时必须声明使用的 Meta Model 版本、事实作用域和证据可见性。
- Observatory 重构由 conformance evidence 驱动，短期可以继续保留 monolithic 文件。
- User-facing 文档和默认入口继续隔离实验 Harness 复杂性，同时允许高级用户按需深入证据。

## Confirmation record

维护者于 2026-08-21 接受：

- AUTH-2，采用“meta 定义角色但不覆盖项目 Seed 内容”的限定；
- AUTH-3，明确 ADR-0001 的箭头链不是强制线性 workflow；各对象 lifecycle 与 Decision／Implementation／Validation 独立 claim dimensions 分开建模；
- AUTH-5，采用相同模型版本／快照／事实作用域／证据可见性的 conformance 前提，并限制 AI 不得越权；
- AUTH-6，先测试与盘点，再渐进提取；
- AUTH-7，三层复杂性与渐进披露；
- AUTH-8，self-hosting 中 Product Seed 与 Meta Model 职责分离。

AUTH-1 与 AUTH-4 继续 pending。正式 ADR 编号只在最新 integration history 上分配。
