# 组合式集成接口草案

Date: 2026-08-27  
Status: Library note / non-authoritative

## 背景

Project Orrery 的核心候选定位是项目权威语义、事实追踪与可观测层，而不是通用长期记忆、人格记忆、向量数据库、Agent 自主执行器或通用多 Agent 调度平台。外部记忆系统、RAG／向量索引、Agent 平台、Harness 和专业 Skill 更适合作为可替换的上下游。

本笔记只记录一组待研究的组合式接口，不构成 ADR、Approved Design、公共 API、兼容承诺或 Implementation Plan。

## 四类候选接口

### 1. Context Export

按 Workstream、subsystem、fact scope 和上下文预算导出受约束的 Context Bundle。候选内容包括有效约束、当前 State、相关 ADR、证据引用、Unknown 和来源 hash。它帮助外部 Agent、Skill 或检索系统定位项目上下文，但不替代其自己的规划与检索实现。

### 2. Evidence Import

接收 Harness、CI、运行工具或外部系统提交的 Evidence Envelope。候选结构应保留 provider、revision、timestamp、artifact reference、reproducibility 和 evidence category。导入结果默认只是 observation／candidate evidence，不能自动改写 State、接受 ADR 或宣布 Validation 成立。

### 3. Runtime Identity Link

用最小身份引用把 Workstream 与外部 Agent 平台任务关联。现有 `platform_session` 是该方向的内部候选：保存 adapter 与平台 session ID，不保存 Prompt、回答、transcript、隐藏模型状态、源码正文、未 push diff 或执行凭据。身份绑定不等于 Orrery 已拥有 launch、message、rebind 或远程执行能力。

### 4. Specialist Skill Contract

让专业 Skill 消费有限 Context Bundle，并返回产物引用、影响范围、验证结果和不确定性。Orrery 不需要理解专业 Skill 内部的工具链；它只检查返回信息在权威模型中的角色和证据能力。

## 候选呈现层

接口不应只绑定某一种命令行或平台。可考虑按以下顺序渐进提供：

1. versioned JSON Schema／provider-neutral data model 作为稳定语义契约；
2. dependency-light CLI 与 stdin／stdout JSON 作为首个可审计参考传输；
3. 可选 Skill、Plugin、MCP、本地 HTTP 或语言 SDK 复用同一 Core 契约；
4. 特定生态 Adapter 独立版本化，不把其依赖倒灌进 Orrery Core。

## 必须保留的边界

- Core 在没有任何外部 Adapter 时仍应完整运行。
- Adapter 依赖 Orrery 的稳定契约；Core 不依赖某个特定 Skill、记忆产品、向量库或 Agent 平台。
- 外部记忆、相似度检索和 AI 总结只能提供候选上下文，不自动升级为权威项目事实。
- 默认不交换完整 Prompt／回答／transcript、源码正文、未 push diff、token 或凭据。
- CLI、Observatory、AI 和外部 consumer 可以解释和展示事实，但不能创造事实。
- `Accepted != Implemented != Validated`、fact scope、evidence provenance 和 Unknown 必须跨接口保留。

## 后续研究问题

- Context Bundle 的最小字段和上下文预算应如何表达？
- Evidence Envelope 的类别、去重、撤销和 stale 规则如何与 Authority Meta Model 对齐？
- 向量索引应如何消费 role、effective status、scope 和 source hash，而不形成第二套权威判定？
- `platform_session` 应在何种条件下进入稳定公共合约？
- 哪些能力只需要 CLI，哪些值得提供 MCP／SDK，如何避免多个 consumer 重复实现语义？
- 第三方 Adapter 的兼容等级、失败关闭规则和独立发布周期如何定义？

这些问题需要研究与小规模适配实验后，才决定是否形成 ADR、Approved Design 或 Implementation Plan。
