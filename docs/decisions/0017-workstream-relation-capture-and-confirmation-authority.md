# ADR-0017: Workstream 关系采集、阶段 Gate 与确认权限

Status: Accepted

Date: 2026-08-29

Amends: [ADR-0014](0014-dynamic-workstream-succession-contract.md), [ADR-0008](0008-local-first-team-coordination-and-cross-machine-metadata.md)

Preserves: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0016](0016-unified-observatory-shell-and-single-local-entry.md)

> 维护者已接受本 ADR 的关系采集与确认模型。Accepted 不证明 relation proposal、stage gate、角色确认、
> CLI、Observatory inbox 或 Conductor Adapter 已实现；当前 W7 v1 行为和公开 v0.2.0 均保持不变。

## Context

ADR-0014 定义了 `derived_from`、`depends_on`、`absorbs`、append-only relation event、DAG/cycle 验证和
只读 Graph，但当前 self-host 关系事实仍很稀疏：工作流主要登记机械 lineage，极少在创建、衍生和集成时
采集语义依赖或责任接管。Graph 可以呈现复杂 DAG，却不能创造未记录的关系。

“是否依赖”也不是一个简单的开始前布尔值。任务可能可以并行实现，却在 validation、integration 或 release
阶段才被另一任务阻塞。人类通常不能预先知道所有依赖；Agent 推理又不能独立升级为项目事实。同时，本项目
当前使用的“中央调度对话”只是维护者工作方式，不是 Orrery Core 可以假设的权威角色。

## Decision

1. **机械 `derived_from` 自动写入。** 新 Workstream 明确绑定 `base_workstream_id`、exact `task_base_oid`，
   且 Core 能本地验证目标存在、OID 一致和合法 ancestry 时，Orrery 自动追加 effective `derived_from` event；
   不需要人类重复确认。任一条件 Unknown／drift／non-ancestor 时只保留 proposal/Unknown，不猜测来源。
2. **`depends_on` 必须声明 gate。** 新版有效依赖必须包含 `required_for`：`implementation`、`validation`、
   `integration` 或 `release`。它表示缺少目标 Workstream 时源任务在哪个阶段不能完成，不意味着所有依赖都
   阻止任务开始。
3. **`depends_on` 采用人机共同确认。** Agent、Harness、Plan parser、CLI 或可选 Conductor 可以提出建议并
   附证据；Agent 自述只能作为 observation。只有人类确认产生 effective relation event。
4. **确认权限按 gate 分级。** `implementation`／`validation` 属于 task-local gate，由源 Workstream 的人类
   task owner 确认；`integration`／`release` 属于 project gate，由具备 `integrator` 权限的人类确认。
5. **确认界面必须解释后果。** proposal 至少显示 source/target、建议 gate、为什么依赖、证据类别、缺失目标
   会阻止什么，以及 Accept／change gate／defer Unknown／reject 选项。不能只让人回答裸问题“是否依赖”。
6. **`absorbs` 始终由人类 integrator 确认。** Agent、task owner 或 Harness 可以提议；子任务 Agent、普通
   reviewer 和中央只读视图不能确认责任接管。确认前必须显示目标 closure/Validation、接管范围与未完成责任。
7. **Personal Mode 的默认角色。** 本机项目 owner 默认是唯一人类 `integrator`，同时可以作为其 Workstream
   的 task owner。Agent/session 本身不继承该权限。
8. **Team Mode 的默认角色。** 显式启用 Team Mode 后，项目 owner 默认仍是唯一 integrator；owner 可以手工
   增加其他已验证项目成员为 integrator。没有有效 integrator 时，project-gate `depends_on` 和 `absorbs`
   保持 Proposed/Unknown 并失败关闭。
9. **中央 Agent 不是权威角色。** Orrery Core 只认识 versioned human member/role/confirmation evidence，
   不假设存在“中央调度对话”。可选 Orrery Conductor Skill/Adapter 只能创建任务、聚合状态和提交关系建议；
   它不能确认 `absorbs` 或 project-level dependency。
10. **关系建议与决定 append-only。** Proposal、evidence attachment、gate change、accept、reject、supersede
    都是 Git-common-private append-only event；不得原地覆盖历史建议或伪造早期意图。
11. **现有 DAG 约束继续生效。** 所有 effective relation 必须通过重复、self-edge、cycle、stale endpoint 与
    scope/evidence 门；不能为了表示“后续 CI 修复”建立反向 edge 导致环。需要 fan-in 时新建 Integration
    Workstream：它从一个主要 Git 来源 `derived_from`，再 `depends_on` 其他交付。
12. **v1 兼容失败关闭。** W7 v1 relation 继续可读。缺少 `required_for` 的历史 `depends_on` 投影为
    `unknown/unspecified`，不自动选择 gate，也不能产生新的强制阻断；W7.3 采用 versioned proposal/relation
    schema 与显式迁移，不静默重写历史 bytes。
13. **派生冲突不变。** path/module/validation/exclusive-resource overlap 继续形成只读 `conflict-pair`；相似性或
    overlap 可以建议 `depends_on`，但不能自动创建语义关系。
14. **本地优先与隐私不变。** Proposal/confirmation 默认只存在 Git-private 本地状态；Team 只同步允许的
    版本化元数据，不同步 Prompt、回答、transcript、源码正文、未 push diff、凭据或原始私有证据正文。

## Consequences

- 新任务从可验证父任务创建时会自然形成 `derived_from` 图，不再依赖 Agent 记得手写 lineage。
- `depends_on` Graph 可以表达“实现可并行、集成才等待”等真实关系，而不把所有依赖误写为 start blocker。
- Personal 与 Team 用户不需要复制本项目的中央对话模式；确认权来自人类角色和本机证据。
- Core/CLI 需要 relation proposal lifecycle、gate-aware eligibility、role-bound confirmation 与 v1/v2 兼容；
  Observatory 需要关系待确认 inbox。上述实现进入 W7.3，不由本 ADR 冒充完成。
- 如果未来允许 Agent 自动确认语义依赖、改变 integrator 权限、引入多人投票或远程确认，必须新增 ADR。

## Mapping

- Approved Design: [Workstream relation capture and confirmation](../design/workstream-relation-capture-and-confirmation.md)
- Implementation Plan: [W7.3 relation capture](../implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)
- Validation: [ADR-0017 decision contract](../validation/2026-08-29-w7-3-relation-capture-decision-contract.md)
