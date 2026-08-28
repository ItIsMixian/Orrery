# ADR-0014: 动态 Workstream 接续关系契约

Status: Accepted

Date: 2026-08-28

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](0008-local-first-team-coordination-and-cross-machine-metadata.md)

Origin: maintainer-approved W7A direction, based on `codex/w5e-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

## Context

ADR-0007／0008 和 W5D 已经能表达一个 Workstream 的显式 `base_workstream_id` 与精确
`task_base_oid`，但它们仍把关系附着在单个 worktree session 上。真实开发不会在项目开始时一次性
给出完整 DAG：后续任务、CI 专项、修复、接管与整合工作会在证据出现时追加。若只靠 branch 名、路径
相似度或旧 session，就会把 Git 来源、执行依赖与所有权转移混为一谈，并让已结束的祖先持续与其后继
制造重复 Direct finding。

关系需要成为共享 Git-private、可审计、可撤销且在 worktree 删除后仍存续的控制面；同时它仍不是作者
State、Plan、Validation 或新的调度权威。

## Decision

1. 项目不要求预先声明完整 Workstream DAG。关系在新 Workstream、依赖或接管事实出现时追加，类似
   Git commit 在创建时记录 parent；未知关系不得按名称、路径或时间猜测。
2. 首版只定义三种互不替代的关系：
   - `derived_from`：Git task-base／来源关系；
   - `depends_on`：执行依赖；
   - `absorbs`：责任与所有权转移。
3. 关系 lifecycle 为 `proposed`、`active`、`completed`、`cancelled`、`stale`。证据不足保持
   `proposed`／Unknown；证据漂移使有效关系变为 stale 候选，不能静默永久关闭。
4. 一个 Workstream 可有多个 predecessor，但同一时刻最多有一个非取消、非 stale 的
   `derived_from` 主要 Git task base。其他 predecessor 必须明确表达为 `depends_on` 或 `absorbs`。
5. 关系事件以 append-only 记录保存在 `$GIT_COMMON_DIR/orrery/workstream-relations/`。读取不得创建目录；
   写入不得覆盖历史事件。该区域不进入作者文档、发布包、默认模板或生成站点。
6. W7A 冻结 provider-neutral record／graph／discovery／apply／undo／legacy inference contract。自动发现和
   验证只产生 proposed plan；批量 apply 需要一次明确的本机 plan 确认，undo 追加补偿事件，不删除历史。
   W7A 只实现 proposed relation 的单条显式本机 append，不实施真实批量迁移。
7. 图验证必须拒绝自指、重复有效 edge、cycle、多个主要 Git parent、非法 OID 和被证明非祖先的
   `derived_from`。branch 名或路径相似度不是证据；无法读取 parent／OID／HEAD 时保持 Unknown。
8. `active tip` 是未被当前、证据充分的 active `derived_from`／`absorbs` 后继接管的活跃叶节点。
   只有 active tips 参与当前 Direct finding 的祖先／后继去重。parent 在 fork 后有独有提交、sibling、
   stale／Unknown、证据漂移、真实 L2/L3 与 exclusive resource 均不得被隐藏。
9. relation apply／undo 只追加关系事件。它不删除 worktree、branch、commit、Validation 或作者文档；
   删除仍由 W6 maintenance 的独立授权和重新验证负责。
10. Core 输出无布局意见的 versioned relation graph JSON：node／edge status、evidence、active tips、Unknown、
    source links 与冲突比较／抑制原因。Core 不输出颜色、坐标、动画或 UI 文案。
11. Observatory 只能消费 Core graph。W7C 可在此契约上实现 Succession／Dependency／Conflict 派生视图、
    active-tip 高亮、历史折叠、Unknown 虚线和可访问列表；W7A 不实现正式图形页面。
12. 本契约不是通用 DAG 调度器，不负责模型选择、任务排程、Agent 启停、自动执行、云资源或远程控制。

## Reasons

- append-only Git-common-private 事件兼顾 linked worktree 共享、删除后留痕与作者树零污染。
- 分开三种关系可防止 Git ancestor proof 被错误当成执行依赖或责任接管。
- proposed／Unknown 与 stale 能诚实表示分布式证据边界；显式 apply／undo 保留维护者控制。
- active-tip 去重只收敛重复祖先噪声，不削弱现有 Direct／L2／L3 安全门。
- 无布局 Core graph 允许 CLI、Observatory 和后续 Adapter 共享同一事实而不让 UI 反向拥有语义。

## Consequences

- 新关系必须带稳定 ID、方向、lifecycle、source links 和类型特定 evidence；`derived_from.task_base_oid`
  与 `absorbs.ownership_transfer_oid` 保持独立，缺失证据不能自动 active。
- 关系存储会长期保留事件，未来 W7B 需要 retention／compaction 设计时必须保持可审计历史。
- 旧 `base_workstream_id`／`task_base_oid` 只能投影为只读兼容 edge，不自动回写真实 session。
- Active-tip 计算需要精确 HEAD／task-base／ancestor 与 parent drift 证据；无法证明时比较保持开启。
- 图形展示与批量迁移分别属于 W7C／W7B，不能以 W7A schema 已存在宣称它们完成。

## Implementation and validation mapping

- Approved Design: [Dynamic Workstream Succession Contract](../design/dynamic-workstream-succession-contract.md)
- Implementation Plan: [2026-08-28 W7A Dynamic Workstream Succession Contract](../implementation/plans/2026-08-28-dynamic-workstream-succession-contract.md)
- State after implementation: `docs/state/project-structure.md`, `docs/state/documentation-system.md`,
  `docs/state/release-and-toolchain.md`, `docs/state/test-coverage.md`
- Validation: [W7A Validation](../validation/2026-08-28-dynamic-workstream-succession-contract.md)
