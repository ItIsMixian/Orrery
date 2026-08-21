# ADR-0012: 文档治理与信息生命周期

Status: Accepted

Date: 2026-08-21

Origin: approved by the maintainer after the 2026-08-21 current-entry compaction review

Amends: [ADR-0001](0001-project-orrery-self-hosting.md) Decision 2 and its synchronization rules

Clarifies: [ADR-0009](0009-authority-meta-model-and-semantic-conformance.md) without extending Authority Meta Model into workflow ownership

## Context

Project Orrery 已经通过 ADR-0001 区分 Seed、ADR、Design、Plan、State、Validation、Snapshot、DEVLOG 和阅读入口，也通过 ADR-0009 定义这些角色的权威语义。然而，角色定义本身不能阻止文档持续累积：根 `PROGRESS.md` 曾吸收早期 Pilot、平台阶段和完成史，Authority State 也曾保存逐检查点实现与 Validation 文件目录。内容大多正确，却让必读入口逐渐变成历史总账，增加人类与 Agent 的定位成本。

这次压缩修复了两个实例，但尚未回答长期问题：哪些文档面向当前控制，哪些保存历史；什么事件触发同步；什么时候应该链接、归档或拆分；机器能检查什么；谁有权决定改写。若没有稳定规则，入口会再次膨胀，而不同 Agent 也会各自发明清理标准。

## Decision

### 1. 增加 Documentation Governance Policy 运维层

Orrery 采用以下分层：

```text
Authority Meta Model
  定义 authority roles、claims、scopes、evidence 与 derived-view constraints
                ↓ constrains meaning
Documentation Governance Policy
  定义作者文档的更新、压缩、拆分、保留、交接与审查生命周期
                ↓ may be checked, never authored automatically
CLI / Harness / Observatory findings
  提供可复核的非权威观察，不创造项目事实或替作者改写文档
```

Documentation Governance 不是新的作者文档角色，也不规定项目整体如何运行。它只管理现有文档角色的信息生命周期。Authority Meta Model 继续回答“文档中的 claim 是什么意思”；治理规则回答“该 claim 应在什么入口维护、何时移出当前入口”。

### 2. 分开当前控制面与历史／证据面

- `AGENTS.md`：稳定的约束、路由与 subsystem 索引；不得成为项目摘要副本。
- `HANDOFF.md`：当前停止点、未决风险、恢复和安全接续；已解决的过程史应移入 DEVLOG／Validation。
- `PROGRESS.md`：活动线路、当前结论、未完成事项、阻塞、近期里程碑和下一动作；不得累计所有已完成工作。
- State Docs：当前事实、边界、能力、证据入口和已知缺口；不得保存逐日实现史或完整 Validation 目录。
- ADR：不可变的决策历史；后续只能 amend／supersede，不通过清理改写历史。
- Approved Design：当前获批规格；失效时显式标注 lifecycle 或由后续设计取代。
- Implementation Plan：准备如何实现及当前检查点；完成后保留历史，但不再占据当前控制入口。
- Validation：可复现证据记录，可以随实现累积，但由索引和 State 提供聚合入口。
- DEVLOG：追加式开发历史；Snapshot：带日期的阶段截面，均不替代 live State。
- Library／Backlog／Experiments：输入、候选和研究材料，不因被治理工具读取而获得决策权。

### 3. 采用事件驱动同步和唯一整合者规则

- 实现或验证完成时，同步受影响的 subsystem State、Validation 和 DEVLOG。
- 新的长期约束先形成 ADR，再进入 Approved Design 和活动 Plan。
- 功能分支让实现、验证和 subsystem State 同行；唯一整合者在合流时同步根 PROGRESS／HANDOFF。
- 停止点、阻塞或风险变化时更新 HANDOFF；风险关闭或里程碑完成时，从当前入口移除已解决叙述并保留历史链接。
- 发布时继续区分工作树实现、已提交、本地 Canonical、runtime verified 与公开 released。

同步的目标是保持当前入口可用，不要求每次变更复制所有事实到所有文档。

### 4. 链接证据，不复制证据

State 与入口文档应按能力或责任聚合少量权威实现／Validation 入口。原始日志、逐命令输出、测试矩阵和按日期的过程说明留在 Validation、DEVLOG、实验结果或仓库外证据根。只有当一段文本本身是当前事实或必要安全边界时，才应直接保留在当前入口。

### 5. 拆分依据是职责，不是硬字数

文档应在职责、更新节奏、所有者或读者路径明显分离时拆分。行数、字符数、链接密度、完成项数量和增长趋势只能作为 soft budget／review signal；它们不是 Authority 语义，也不能单独使文档无效、阻塞发布或授权自动改写。

### 6. 未来工具只生成非权威 finding

后续可以实现 provider-neutral、zero-network 的只读 `docs audit` 能力，检查角色越界、当前／历史混合、证据重复、过期入口、失活 Plan、断链、结构化字段误用、增长趋势和并发所有权冲突。

工具输出必须：

- 标明规则、来源、作用域、观察值和不确定性；
- 默认不上传 Prompt、回答、transcript、源码正文或成员凭据；
- 不直接修改作者文档、不自动关闭 finding、不把 warning 升级为 ADR／State／Validation；
- 由维护者或整合者选择 acknowledge、defer、修复或调整项目级 soft budget。

长度类 finding 默认不构成 CI 硬失败。结构破坏、断裂的权威链接或安全边界违规可以由后续 Approved Design 单独定义为失败条件。

### 7. 渐进采纳

本 ADR 首先约束 Project Orrery 自托管文档。首个实现检查点是建立治理 Design／Plan、同步当前 State 和记录文档级 Validation；不在同一变更中实现 CLI、Observatory 面板、自动迁移或公开模板升级。发布版采纳需要后续实现证据和单独发布决策。

## Reasons

- 当前入口需要保持小而可导航，但不能以删除历史或隐藏证据换取简短。
- 软预算能暴露积累趋势，同时避免把排版偏好误当成项目事实。
- 事件驱动同步比周期性重写更贴近真实变更，也减少多 Agent 争写全局文件。
- 只读 finding 保留人类判断和作者所有权，并符合 derived views 不得创造事实的既有边界。
- 将治理与 Meta Model 分开，可以避免 authority semantics 吞入任务调度、UI 或文档编辑策略。

## Consequences

- 新会话应先读短入口和相关 State，不再把 PROGRESS／HANDOFF 当作完整历史。
- 文档维护包含“移出当前入口并留下链接”，不再只意味着追加文本。
- HANDOFF 等现有长文档可以被标记为 review candidate，但必须人工确认安全接续信息后才能压缩。
- 后续 audit 工具需要稳定 finding contract、可配置 soft budgets、负向测试和非权威显示边界。
- 当前公开 v0.2.0、发布 Skill、模板和 runtime 行为不因本 ADR 自动变化。

## Rejected alternatives

- **只依赖作者自觉：** 已经出现入口膨胀，无法形成跨 Agent 一致维护。
- **固定字数并在 CI 强制失败：** 会诱导机械拆文档，也无法判断职责是否清晰。
- **让 AI 自动摘要并覆盖原文：** 会破坏作者所有权和可追溯证据，派生文本也可能被误认成事实。
- **把所有规则写进 Authority Meta Model：** 会把事实语义和运维工作流混为一层。

## Implementation and validation mapping

- Approved Design: [文档治理与信息生命周期](../design/document-governance-and-information-lifecycle.md)
- Implementation Plan: [2026-08-21 文档治理与只读审计](../implementation/plans/2026-08-21-document-governance-and-audit.md)
- State Docs: [文档系统 State](../state/documentation-system.md)
- Validation: [2026-08-21 文档治理采纳](../validation/2026-08-21-document-governance-adoption.md)
