# 多人／多 worktree 协作协议

Status: Approved for integration (Candidate scope)

Governing decisions:

- [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) — canonical isolation and fact-scope baseline
- [PO-DEC-WT-002](../decisions/proposals/PO-DEC-WT-002-local-first-team-coordination.md) — maintainer-approved candidate amendment for opt-in Team Mode and Local-only telemetry

Updated: 2026-08-20

## 首版体验总览

- 默认 Personal Mode：单成员、多 Agent、纯本地；Agent-first 习惯优先兼容，Orrery-first 是显式安全入口。
- 一个 Workstream 使用一个 branch + worktree 隔离，可由一个完整平台会话串行完成多个相关 Change Set，并通过 Scope Revision 扩张。
- Workstream 默认映射已有 subsystem State；Git／Harness／CLI 生成机械状态，Agent 上下文只接收最小目标、约束、异常和证据切片。
- Scope Expansion 使用 B 策略：L0／L1 自动，L2 本机确认，L3／Direct 硬阻断；finding、Review Ready、审查和清理均由可复核门禁驱动。
- 同一 Observatory 以轻量 Personal 首页为默认；Team Mode 手动开启后增加只读 Team 页签、内置局域网临时 Host、事件驱动的元数据同步和可叠加治理 capability。
- 中央不同步完整对话或源码正文，也不能远程执行；首版由人类 Integrator 合流，AI 只生成证据导航和风险摘要。
- 富 Agent 接力、自动集成、多专家小队、多设备、异地 relay／云 Coordinator 和中央源码语义分析明确延期。

## 问题

Project Orrery 当前把 State Docs 定义为“现在是什么”，但多人在不同分支、clone 或 linked worktree 中工作时，“现在”至少存在三种不同视角：集成分支已经提交的事实、功能分支的候选事实，以及尚未提交的本地工作副本。如果这些视角没有显式绑定到 commit 和 worktree，任一 Agent 都可能把局部状态误写成全局事实。

共享同一工作目录更加危险。两个 Agent 即使声称在处理不同任务，也会同时看到并修改同一份未提交文件、索引和生成物；Git 无法替它们区分文件所有权。

## 目标

1. 每个并发 Workstream 拥有独立分支、工作目录、索引和验证空间；一个会话可在其内完成多个相关 Change Set。
2. Canonical State、branch candidate state 与 dirty worktree state 不再混写。
3. 保持 Git 分支异步，不建立仓库级全局锁。
4. 在合流前发现文件、权威文档、依赖和验证层冲突。
5. 让协作元数据尽量由 Git 与工具生成，不要求每个小任务新增人工文档。
6. 同时支持同机 linked worktree 和不同机器的独立 clone。
7. 能由 Git、Harness 或 CLI 机械派生的非关键运行信息不进入 Agent 的常驻上下文；Agent 只接收完成当前判断所需的最小摘要，并按需查询细节。

## 非目标

- 不提供多人实时共同编辑。
- 不在成员未开启 Team Mode／分享、没有本地 Node 主动上报或证据不足时，宣称能够发现另一台机器上的未 push 工作；Local-only telemetry 也不等于源码或语义已验证。
- 不自动解决语义冲突或替维护者接受 ADR。
- 不把任务清单、仪表盘或冲突预测升级成新的事实源。
- 不要求所有平台启用 `extensions.worktreeConfig`；旧 Git 兼容性必须单独评估。
- 不在核心中编排“多专家 Agent 小队”；该能力由独立 Skill／CLI 按需调用 Orrery 的 worktree、session、scope 和 validation 原语。
- 首版不提供富 Agent 接力；只保留指挥台、故障续接和未来接力共同需要的最小 session checkpoint。
- 不建立独立事故恢复系统；当前以 Git 恢复点、Orrery 权威文档和 Validation 共同承担合理回退。
- 首版集成采用人工执行与 AI 辅助审查，不自动更新 integration ref；自动集成流水线属于后期体验。

## Git 事实基础

根据 [Git worktree 官方文档](https://git-scm.com/docs/git-worktree)：

- linked worktree 共享对象库、普通 `refs/*` 和默认仓库配置；
- 每个 worktree 拥有独立 `HEAD`、索引、工作目录和大多数 pseudo refs；
- `$GIT_DIR` 在 linked worktree 中指向其私有管理目录，`$GIT_COMMON_DIR` 指向共享仓库；
- worktree 专属配置需要显式启用 `extensions.worktreeConfig`，且旧 Git 版本可能拒绝该仓库；
- worktree lock 只防止管理记录被 prune，不是协作写锁。

2026-08-19 本地烟雾验证在同一提交上建立 detached linked worktree：主工作区存在未提交改动时，新 worktree 保持干净；两者 `HEAD` 相同，但 `index` 和 `$GIT_DIR` 路径不同，`$GIT_COMMON_DIR` 相同。实验 worktree 已移除。

## 三层事实作用域

| 作用域 | 身份 | 可以声称什么 | 不可以声称什么 |
|---|---|---|---|
| Canonical | `integration_ref@commit`，通常为 `main@OID` | 已进入集成分支的项目当前事实 | 未合流分支或未提交工作的状态 |
| Candidate | `branch@HEAD` + `merge_base` | 当前功能分支在其提交上的候选实现与文档 | 已成为全项目事实或已发布 |
| Worktree | worktree id + `HEAD` + dirty fingerprint | 当前本地副本正在发生什么 | 其他 worktree、其他 clone 或项目全局状态 |

发布状态另以不可变 tag／release commit 表达；`main` 已实现也不自动等于已发布。

### 文档解释规则

- 在 `main` 上读取的 State Docs 是 Canonical State，但仍必须注明对应 commit。
- 在功能分支上读取的 State Docs 是该分支的 Candidate State。观测台必须显示分支、HEAD、merge base 和 dirty 状态，不能只显示文档正文。
- 未提交的 State 修改只属于 Worktree State。
- Accepted ADR 的效力也绑定 commit：只存在于功能分支的 ADR 不得被其他分支当作 canonical effective ADR；进入集成分支后才成为项目共享决定。
- 根 `PROGRESS.md` 与 `HANDOFF.md` 表达集成视角。普通功能分支不应为每个中间动作反复修改这两个全局入口；分支任务进度由 worktree session、Implementation Plan 或代码托管平台的任务／PR 承载，合流时再同步全局入口。

### 并发 ADR 编号

连续的 `ADR-NNNN` 是集成分支命名空间，不能由互相不可见的功能分支安全分配。两个分支都看到“下一个编号是 0003”时，可能各自创建不同的 `ADR-0003`；文件名冲突只是表面问题，更危险的是其他文档已经引用了两个含义不同的同号决定。

推荐规则：

1. 非集成分支先使用稳定的临时决策 ID，例如 `PO-DEC-<task-id>-<slug>`，文档放在 `docs/decisions/proposals/`，状态保持 Proposed。
2. 临时 ID 在分支生命周期内不变化，可安全被 Draft Design 和 Plan 引用。
3. 只有集成者在合流到最新 integration ref 时分配下一个正式 `ADR-NNNN`，随后统一重命名文件并更新引用。
4. 若历史分支已经预先使用数字编号，集成时必须检查冲突；未进入 integration ref 的编号不构成全局占位。
5. 已进入 integration ref 的 ADR 编号永不复用。

这避免引入一个所有人都必须实时访问的“ADR 号码锁”，也避免用未提交文件假装完成号码预留。

## 推荐工作模型

### 1. 分配

- 每个并发 Workstream 使用一个专属分支和一个专属 worktree 或 clone；Workstream 内可包含多个相关 Change Set。
- 主 worktree 保留给维护者／集成者；普通 Agent 不直接在其中实现任务。
- 同一分支不被多个 worktree 同时检出。多人共同任务通过独立子分支和集成分支协作。
- 创建 Workstream worktree 时固定并记录 `integration_ref`、起始 OID 和 merge base。

### 混合创建入口与平台能力

- 实际主流入口预计是 Agent-first：成员继续直接在 Codex、Claude 或其他平台创建新会话，本地 Adapter 检测项目、目录和 session，再连接已有 Workstream 或在首次产品写入前引导创建新的安全 Workstream。Orrery-first 的“从本地指挥台创建 Workstream 并启动 Agent”是逻辑上更安全的显式入口，但不能要求用户改变既有习惯后才能获得保护。
- Adapter 必须分别声明 `launch`、`attach`、`rebind` 和 `message` capability，不能假设所有平台都能把现有会话原地迁移到另一个 worktree。支持 rebind 时可以原地连接；只支持 launch 时创建位于正确 worktree 的新会话，并停止旧会话写入；都不支持时只创建 worktree 和 continuation brief，由用户手工打开。
- Agent-first 会话位于已注册 Workstream worktree 时自动 attach；位于干净、未注册的功能分支／worktree 时请求本机注册；位于主 worktree 且尚未写入时，在首次产品写入前阻断并提供创建／连接 Workstream；主 worktree 已经 dirty 时禁止自动迁移，进入恢复点、归属审阅和选择性转移流程。
- 中央指挥台只能发送“请创建／连接安全 Workstream”的请求，实际创建、迁移、停止旧会话或启动新会话仍由成员本地确认与执行。

### Workstream 与 subsystem State 的关系

- Git worktree 是物理隔离容器，不硬绑定单一模块；Workstream／Scope 承载模块语义。每个 Workstream 默认记录一个 `primary_subsystem_id` 和零个或多个 `affected_subsystem_ids`，允许真实的跨模块功能与项目级任务。
- subsystem registry 从现有 `AGENTS.md` 索引和 `docs/state/*.md` 派生稳定 ID、State Doc、已知路径模式、权威面和验证面。路径变化或展示名变化不应改变 subsystem identity。
- 创建或 attach 会话时，CLI 根据当前目录、expected writes、实际路径和 registry 提议模块映射；映射明确时自动使用，歧义时才请求成员选择，不把完整模块清单注入 Agent 上下文。
- 当前 Scope 触及新的已知 subsystem 时，按 Scope Expansion B 处理：若已在 affected 列表且无 finding 可继续；未预期跨模块默认进入 L2。无法映射时显示 `Unmapped`，提示关联现有 subsystem、标为一次性 project-wide scope，或提出候选 subsystem；工具不能凭路径自动创建新的权威 State。
- 同模块关系本身构成潜在 Semantic surface：两个 Workstream 即使没有路径重叠，只要共享 subsystem、接口或验证面，也要提高冲突检查优先级，但不能仅凭同模块直接宣称冲突。

### 2. Worktree Session

工具在 `git rev-parse --git-path orrery/worktree.json` 返回的位置维护本地 session。该路径位于每个 worktree 私有 `$GIT_DIR`，不进入提交，也不制造作者文档。

最小候选结构：

```json
{
  "schema": 1,
  "project_mode": "personal",
  "workstream_id": "PO-WT-001",
  "worktree_id": "local stable id",
  "member_id": "local-owner",
  "host_id": "host stable id",
  "platform_session": {
    "adapter": "codex",
    "session_id": "platform-specific id"
  },
  "branch": "codex/example",
  "head": "full commit oid",
  "integration_ref": "refs/heads/main",
  "integration_oid": "full commit oid",
  "merge_base": "full commit oid",
  "lifecycle_phase": "implementing",
  "runtime_condition": "active",
  "scope_revision": 1,
  "primary_subsystem_id": "project-structure",
  "affected_subsystem_ids": [],
  "expected_writes": ["path/or/pattern"],
  "governing_docs": ["docs/state/example.md"],
  "validation_surfaces": ["exact command"],
  "visibility": "worktree-local",
  "captured_at": "RFC 3339 timestamp"
}
```

Session 是可重建执行元数据，不是 State 或 Plan。它必须在 HEAD、分支或 dirty fingerprint 改变后被重新计算；Agent 自己填写的字段不能冒充独立证明。

### 上下文预算与控制面分工

- branch、HEAD、merge base、ahead／behind、dirty、tracked／untracked 路径、测试结果、时间戳和重叠 finding 由 Git、Harness 或 CLI 生成，不能要求 Agent 先阅读仓库再复述成 Manifest。
- CLI 输出结构化机器结果，观测台负责聚合展示；Agent 默认只接收目标、关键约束、当前冲突、异常和需要判断的证据切片。
- 详细路径、日志和历史通过 CLI 按需展开，不作为每轮 Prompt 的固定前缀。缺少必要证据时，Agent 可以请求扩张，但扩张本身由工具记录。
- Agent 可以提供意图、推理、不确定性和语义关系；这些内容不得替代 Git 写入事实、Harness 验证或 CLI 派生状态。

### Scope Expansion 的平衡策略

维护者已接受平衡策略 B：同子系统且无冲突的变化自动纳入当前 Scope Revision；跨子系统、权威文档、共享接口或与其他 Workstream 发生语义重叠时，在首次相关写入前暂停并请求确认；凭据、发布、schema migration、主 worktree 写入和 Direct conflict 由本机 Harness 硬阻断。

| 级别 | 条件 | 首版动作 |
|---|---|---|
| L0 范围内变化 | 目标、路径模式和验证面均未超出当前 Scope | Harness 静默记录 |
| L1 安全扩张 | 新增路径或 Change Set，但仍属同一子系统且没有 overlap finding | CLI 自动创建新 Scope Revision，指挥台提示但不打断 Agent |
| L2 协调扩张 | 跨子系统、Authority surface、共享接口／验证面或 Semantic overlap | 本机暂停相关写入，要求成员确认继续、协调或拆分 Workstream |
| L3 高风险扩张 | 凭据、发布、schema migration、主 worktree 或 Direct overlap | 本机硬阻断，必须显式解决后重新检查 |

只有新增意图、预期行为或无法机械推导的语义关系需要由用户／Agent 提供；实际路径、dirty 状态、验证面和 finding 由 CLI／Harness 派生。

### 3. 重叠检测

本机协调器可以枚举 `git worktree list --porcelain`，并对每个可访问 worktree 比较：

1. 从 merge base 到 HEAD 的已提交路径；
2. staged、unstaged 与 untracked 路径；
3. 两项任务声明的预期写入路径；
4. 共同适用的 State、ADR、Design 和 Validation；
5. 可选的符号、依赖或测试面。

告警等级建议为：

| 等级 | 条件 | 默认动作 |
|---|---|---|
| Direct | 同一路径已有或预期写入重叠 | 立即告警并要求协调 |
| Authority | 同一 State／ADR／全局入口可能被双方修改 | 指定唯一整合者 |
| Semantic | 不同文件共享接口、schema、迁移或测试面 | 运行推测性合流和专项测试 |
| Unknown | 另一任务未发布或 worktree 不可访问 | 明确显示不可观测，不声称无冲突 |

跨机器代码与集成证据仍只来自已经 push 的分支、PR／MR 和 CI。Team Mode 中，成员本地 Node 可以主动上报路径／模块、dirty、Validation 和 finding 等 `Local-only` telemetry；中央可以据此提示 Direct／Authority 候选，但未上传的源码正文和证据不足的 Semantic 关系仍是 Unknown。未开启分享、离线未上报或 Coordinator 不可见时，不得推断不存在冲突。

### Finding 生命周期与分级处置

- finding 使用 `Open`、`Acknowledged`、`Resolved` 和 `Stale` 状态。它是 session／协调控制面的派生记录，不升级为新的 State 或 ADR；每次 Scope Revision、integration base 或相关路径／验证面变化后重新计算。
- Direct／L3 finding 不可由成员或 Agent 豁免。相关写入保持阻断，直到重叠路径、独占资源、主 worktree 使用或高风险条件实际消失并由 CLI／Harness 复核为 Resolved。
- Semantic／L2 finding 允许成员在本地指挥台填写简短理由后继续。处置记录必须包含成员、时间、适用 Scope Revision 和理由；finding 保持可见、标为 Acknowledged，并强制进入最终 AI 辅助集成审查包。
- Agent 可以解释风险或建议处置，但不能自行批准 Acknowledged、Resolved 或任何豁免。中央指挥台只能发送协调请求，处置动作必须在成员本机确认。
- Acknowledged 不是永久忽略。Scope、基线、接口、验证面或冲突对端发生变化后，旧确认变为 Stale 并重新要求处置；工具检测到触发条件消失时可以建议 Resolved，但必须保留历史轨迹。
- 同一成员名下多个 Agent 产生的 Semantic／L2 finding，由该成员在本机确认即可覆盖自己负责的相关 Workstream。
- 跨成员 Semantic／L2 finding 为每个受影响成员维护独立 acknowledgement。成员确认自己负责的 Workstream 后可以继续本地开发，不必等待其他成员在线；整体 finding 在所有必需成员确认、Scope 调整消除重叠或未来权限矩阵规定的集成者完成仲裁前保持部分确认，相关 Workstream 不得进入 `Review Ready`。
- 部分确认在指挥台显示为 `Acknowledged n/m`，不能伪装为整体 Resolved。维护者／集成者的仲裁权限、超时和成员失联处理留给角色／权限矩阵决定。

### 4. 分支内工作

- 代码、配置、测试以及受影响的 subsystem State 在同一功能分支同行。
- 本文的“会话”指一个完整的平台会话／任务线程，例如从创建到结束的一个 Codex 新任务；它内部可以包含多轮用户消息、多次 Agent 行动、实现、验证和方向调整，不是一次消息往返。
- Workstream 是分支 + worktree 形成的 Git 隔离与协作单位，会话是当前驱动它的交互执行实例，Change Set 是其中可独立理解、提交或回退的一组功能变化。三者不强制一一对应。
- 一个会话可以在同一 Workstream 中串行完成多个相关 Change Set；会话对应的目标／功能集合允许变化，不要求“一个功能一个会话”或“一个功能一个 worktree”。每次扩大目标、预期写入或验证面时必须先刷新 session 并重新运行重叠检查。需要独立合并／回退、换负责人、跨入高风险资源或与活动任务发生冲突时再拆出新 Workstream；富 Agent 接力实现后，同一 Workstream 也可以由后续会话继续。
- State 只能描述该分支 HEAD／worktree 已经表现出的行为，不能提前写计划结果。
- 小任务不强制新增 Plan；跨模块、迁移、发布或长期任务使用 Implementation Plan。
- 临时工作进度默认留在本地 session 或 PR／任务记录，不写入 canonical `PROGRESS.md`。
- 需要把任务交给另一台机器且没有平台任务系统时，必须显式导出一个最小 handoff；其最终存储形式仍是开放选择。

### 5. 推测性合流

合流必须在独立、干净的 integration worktree 中执行：

1. fetch 并固定目标 integration OID；
2. 计算 merge base、ahead／behind 与路径重叠；
3. 在临时分支或 detached worktree 中尝试 merge／rebase；
4. 运行任务 Validation、受影响 subsystem 测试和文档一致性检查；
5. 检查 State 是否仍与合流后的实现一致；
6. 通过后才更新 integration ref；
7. 最后同步 canonical PROGRESS、HANDOFF、DEVLOG 与必要 Validation。

冲突检测先告警而非全局加锁。秘密、发布、schema migration 或明确声明的独占资源可以采用更严格的集成门。

## 观测台所需投影

观测台页首至少显示：

- 当前路径与 worktree id；
- branch／detached 状态；
- HEAD 和 integration OID；
- merge base、ahead／behind；
- clean／dirty 与未跟踪文件数量；
- 当前视图是 Canonical、Candidate 还是 Worktree；
- 其他可见 worktree 的直接／权威重叠告警。

这些数据全部从 Git、session 与验证结果派生，不写回权威文档。

### 展示层与执行层

- 单人多 Agent 时，展示层按 Project → Workstream／Agent 展开。
- 多人多 Agent 时，展示层按 Project → Member → Workstream／Agent 聚合；Host／设备作为底层定位元数据，默认不增加一个固定视觉层级。
- 展示层只投影 Git、Harness、CLI、session 与平台 Adapter 的可观察状态。中央指挥台是纯展示层：所有经过身份验证的项目成员都可以登录并查看所有成员的汇总状态，但不能直接创建、暂停、继续、终止或远程执行其他成员机器上的任何动作。
- 中央指挥台只能向成员发送操作请求；请求不是命令。真正的创建、暂停、继续、终止、scope 扩张批准、验证和集成准备都由成员自己的本地指挥台执行，并且远程请求必须在成员本机明确确认。
- 跨机器未 push 的工作不可由中央视图推断；最多显示成员上报的 telemetry，并与已 push Candidate 事实明确区分。

### 渐进式指挥台信息架构

Project Orrery 使用同一个 Observatory 承载文档阅读与项目指挥，不为 Team Mode 创建第二套应用。Personal Mode 默认首页保持轻量，只显示四个按优先级排列的区域：

1. 项目状态：canonical ref／HEAD、事实作用域、全局验证与风险摘要；
2. 需要关注：Waiting for User、Blocked、Failed、Stale／Unknown 和高等级 finding；
3. 审查队列：Review Ready、Request Changes、Hold 和等待人工集成的候选；
4. 活动 Workstreams 与 subsystem 活动概览：正在开发的会话卡片，以及各模块当前被哪些 Workstream 触及。

Workstream 卡片只显示名称、primary／affected subsystem、生命周期阶段、运行状况、Agent 平台／会话、branch／HEAD、dirty 摘要、Validation、finding 数量和 last activity。Scope Revision、具体路径、测试日志、finding 历史、审查包和清理资格通过详情页按需展开，避免把完整控制面再次塞回首页。

Team Mode 只在同一指挥台中增加 `Team` 页签：按 Member 聚合 Workstream、显示 Coordinator／同步状态、请求收件箱、跨成员 finding 和 capability 管理。`My Workstreams` 保留成员本地执行按钮；Team 页签以及其他成员卡片只允许查看和发送请求，不能出现会被误解为直接执行的按钮。Team Mode 未开启时，这些入口、网络状态和成员配置全部隐藏。

### 成员身份与可叠加 capability

所有经过验证的项目参与者都具有基础 `Member` 身份；Reviewer、Integrator 和 Admin 是可独立授予、可组合的 capability，不是互斥职位。项目维护者通常同时持有四者，普通开发者可以只有 Member。

| 身份／能力 | 首版权限边界 |
|---|---|
| Member | 查看全员状态；在成员本机创建和控制自己的 Agent／Workstream；确认自己负责的 L2；提交 Review Ready 候选 |
| Reviewer | 查看 AI 辅助审查包、评论、要求修改并给出审查结论；不能控制其他成员 Agent 或直接合流 |
| Integrator | 在干净 integration worktree 中执行人工合流、分配正式 ADR 编号、同步 canonical State，并按未来规则仲裁跨成员 L2；不能绕过 Direct／L3 |
| Admin | 邀请／移除成员、授予／撤销 capability、修改项目和局域网团队设置；不能因此获得成员机器远程执行权 |

- capability 只决定谁可以提出、批准或执行项目级流程，不改变中央只读、本地确认和成员机器隔离边界。
- capability 变更必须带 actor、时间、项目和前后值的审计记录；移除成员或撤销 capability 后，旧本地凭据／设备授权必须失效。
- Agent 不是项目成员身份，不能持有 Reviewer、Integrator 或 Admin capability；它只能在成员授权的本地会话中提出建议和生成候选证据。

### 默认 Personal Mode 与显式 Team Mode

- Project Orrery 默认运行在单成员多 Agent 的 `Personal Mode`：只有一个隐式本地成员，并默认持有 Member、Reviewer、Integrator、Admin；安全 worktree、Scope、冲突检测、状态投影和人工集成审查全部在本机工作。
- Personal Mode 不启动网络监听、局域网发现、Coordinator Host、成员认证、状态分享或 presence heartbeat，也不要求安装团队同步依赖。用户不启用团队功能时，不承担多人系统的配置、性能或安全成本。
- `Team Mode` 必须按项目由本地用户明确开启。开启后才生成／选择成员身份、配置项目加入边界，并允许启动／加入局域网 Host；中央同步和所有跨成员能力只在 Team Mode 中出现。
- 关闭 Team Mode 会停止发现、Host、状态上报和请求接收，但保留本地 Workstream、Git 历史、Validation 和权威文档；不能因为退出团队模式删除项目事实或本地工作。
- 两种模式共用同一 Workstream／session／finding schema，Team Mode 只是增加 Member 聚合、同步和治理 capability，不形成第二套项目权威。

### 风险分级的人类审查

- Personal Mode 的普通 L0／L1 变化允许同一成员同时作为作者、Reviewer 和 Integrator完成自审。
- Team Mode 的普通单 subsystem 变化由 Integrator 审查即可，非作者 Reviewer 可选；项目可以加严。
- 跨成员 L2、共享接口或 Authority surface 要求所有受影响成员完成 acknowledgement，并至少一名非作者 Reviewer 通过后才能进入集成。
- 发布、凭据、安全和 schema migration 等高风险候选必须由非作者 Reviewer 通过；相关 Direct／L3 条件必须先实际解决。项目可以要求 Reviewer 与 Integrator 职责分离。
- AI 只生成审查摘要、风险提示和证据导航，不计作人类 Reviewer，也不能满足独立审批人数。
- 项目策略可以提高审查要求，但不能降低 Direct／L3 硬门禁或把 Agent／AI 计作人类批准。

### AI 辅助的人工集成审查包

Workstream 满足 `Review Ready` 后，由 CLI／Harness 针对精确的 candidate HEAD、integration target OID、Scope Revision 和 review schema 生成不可混淆的审查包。审查包按“原始证据与链接在前、AI 摘要在后”排列，至少包含：

- 当前 Scope、Change Set 和受影响 subsystem 摘要；
- commit／diff 统计以及可回到原始 Git 证据的链接；
- 必需 Validation 的命令、结果、时间与证据新鲜度；
- Direct／Authority／Semantic／Unknown finding，及所有 L2 acknowledgement、理由和 `n/m` 状态；
- ADR／Approved Design／Candidate State 对齐结果；
- integration base 漂移、未 push／Local-only 和其他不可观察边界；
- AI 生成的风险摘要、遗漏候选和审阅导航，但明确标为派生建议。

人类审查动作只有 `Approve`、`Request Changes`、`Hold` 和 `Reject`。动作记录 reviewer、时间、candidate HEAD、target OID、审查包 hash 和可选意见；批准只对该精确组合有效。新 commit、Scope Revision、target 漂移、验证过期或 finding 变化会自动使旧批准 Stale，必须重新生成／审查。

AI 摘要没有批准权，不能隐藏失败证据、替代原始链接或计作 Reviewer。Approve 只允许候选进入 Integrator 的人工合流流程，不自动更新 integration ref；Request Changes 退回适当阶段，Hold 保留候选但暂停推进，Reject 必须保留可审计理由和回退入口。

### 集成后的保守清理

- 候选完成实际合流、集成验证和 canonical State 同步后，Workstream 标为 `Integrated`，但不立即删除 branch 或 linked worktree。CLI 先生成安全资格报告和预计可回收空间，本地指挥台只显示“可安全清理”建议。
- 默认清理由 Workstream 所属成员在本机确认。Team Mode 中 Integrator 或其他成员只能发送清理请求；中央和治理 capability 都不能直接删除成员本地目录。
- linked worktree 只有在 HEAD 已可追溯到 canonical integration、Git 状态 clean、没有独有 commit，并且不存在未确认的 untracked／ignored 路径时才可清理。已识别的可丢弃缓存可以通过显式 allowlist 排除，未知 ignored 文件继续阻断。
- 清理 worktree 前，把最小 closure record 写入共享 Git 私有管理区（不进入作者文档），记录 Workstream、final HEAD、integration commit、审查包、Validation、closure reason、清理者和时间。删除 worktree 不删除已集成 commit。
- branch 默认保留项目可配置的缓冲期，期满后只提示删除；只有确认已合流且没有独有 commit 时才可安全删除。本地 branch、远端 branch 和 worktree 是三个独立清理动作。
- 未集成、Rejected、Abandoned、dirty、含独有 commit 或含未知本地文件的 Workstream 永不自动清理。项目可以显式开启“集成后自动清理合格 clean worktree”，但默认关闭，且仍不能绕过资格检查。

### 中央同步的内容边界

- 不同步完整 Prompt、回答、推理过程或对话 transcript。中央只接收任务标题／摘要、成员、Workstream／session 标识、阶段、branch／HEAD、dirty 摘要、路径或模块级 scope、验证结果、finding、last-seen 和可观察性状态。
- 首版 Orrery 协调层不上传源文件正文。已经 push 的代码继续由现有 Git 托管权限控制；中央可以引用 branch、commit、PR 和 CI，但不额外复制一份源码。
- 未 push 代码在中央显示为 `Local-only`：允许成员本机上报 dirty／untracked 数量、规范化路径或模块摘要以及内容 hash，但不上传正文。中央可据此判断 Direct／Authority 路径重叠；缺少正文或依赖证据的 Semantic 关系必须显示为 Unknown，而不是绿色安全。
- 首版权限矩阵以上述 capability 为准：中央只读、成员本地控制、跨成员动作只能请求且必须本机确认。
- 数据模型从首版保留 `member_id` 与 `host_id`；多设备归属、设备迁移和同时在线策略尚未决定。默认一个 Workstream 同时只有一个 active host，避免设备问题阻塞当前单设备体验。

### Local-first 团队拓扑与同步策略

- “中央”是逻辑 Coordinator 角色，不要求常驻云服务器。首版由一名在线成员在自己的本地指挥台中启动临时 Coordinator Host；其他在线成员把状态 revision 直接同步给该 Host，中央网页由 Host 提供。
- 局域网团队模式必须内置：成员可以从本地指挥台启动 Host、自动发现同一局域网内的可加入项目并完成连接，不要求自行安装虚拟局域网、配置端口映射或部署云服务。自动发现只广播最小 endpoint／project fingerprint，不广播任务状态；加入仍要求经过验证的项目成员身份和 Host 侧确认。手工输入邀请地址作为发现失败时的回退。
- 同一时刻只认一个 active Coordinator Host。Host 离线时实时中央视图暂时不可用，各成员继续保留本地状态；另一成员可以手动启动新 Host，在线节点按 `member_id + host_id + workstream_id + revision` 重新发送最新状态。首版不实现自动 leader election。
- 异地网络不属于内置局域网首版的透明连接承诺；团队可自行使用虚拟局域网，后期再提供可选 rendezvous／relay 或常驻 Coordinator 部署。Orrery 的基础功能不能依赖这些外部服务。
- 同步默认事件驱动：Workstream／Scope、Agent 阶段、Git dirty／commit／push、验证和 finding 发生变化时，经 debounce／coalescing 后发送新 revision；空闲时不持续发送应用层 heartbeat，并提供“立即同步”。
- presence heartbeat 默认关闭，由成员主动开启并选择低频间隔。关闭时中央依据持久连接断开和 `last-seen` 展示状态；突然断网且无法确认离线时，在 TTL 后标为 `Stale／Unknown`，不能冒充实时状态。成员也可以完全关闭团队状态分享，此时中央明确显示 `Sharing off／Unavailable`。

### Workstream 双维度状态模型

Workstream 不使用一个混合了进度、连接和阻塞原因的扁平状态。观测台分别投影生命周期阶段、当前运行状况和证据新鲜度：

- 生命周期阶段：`Created → Investigating → Implementing → Validating → Review Ready → Integrated → Closed`。调查、实现和验证可以在失败或范围变化后回退；`Review Ready` 在基线漂移、验证过期或出现新 finding 时也必须撤销。
- 当前运行状况：`Active`、`Waiting for User`、`Paused`、`Blocked by Conflict`、`Failed`、`Offline` 或 `Stale／Unknown`。它表达当前能否继续，不改变生命周期事实。
- 证据新鲜度：记录 `last-seen`、最后 Git／Harness revision 和是否可独立复核；过期状态不能继续显示为实时事实。

`Review Ready` 只能由 CLI／Harness 门禁生成：至少存在候选 Change Set／commit，必需验证通过，worktree clean 或剩余文件已显式排除，没有未解决的 L3／Direct finding，L2 已有成员处置记录，必要 Candidate State 已对齐，并且 integration base 没有未经复核的漂移。Agent 只能提出进入审查的建议，不能自行宣布门禁通过。

`Integrated` 只在候选实际进入 canonical integration ref、集成验证通过且 canonical State 已同步后成立。代码完成但尚未合流时最多是 `Review Ready`；`Closed` 是后续行政终态，必须记录 integrated、abandoned 或 superseded 等 closure reason。

## 候选工具面

```text
orrery worktree create <workstream-id> --branch <branch> --from <integration-ref>
orrery worktree status [--json]
orrery worktree overlap [--all | --remote]
orrery integrate --target <integration-ref> --dry-run
orrery integrate --target <integration-ref> --validate
```

首版不需要实现完整符号图。路径重叠、权威文档重叠、merge-tree 和声明的验证面足以形成可测试基线。

## 验证场景

1. 主 worktree 有未提交文件时，新 linked worktree 必须保持 clean。
2. 两个 worktree 修改同一路径时产生 Direct 告警。
3. 两个分支修改不同文件但共享 schema／测试时产生 Semantic 告警。
4. Candidate State 不得在 canonical dashboard 中显示为已集成。
5. Team Mode 关闭／未上报时，另一机器的未 push 工作显示 Unknown；Team Mode 已上报时只显示 Local-only 元数据，并把未获代码证据的 Semantic 关系保留为 Unknown。
6. 推测性 merge 文本无冲突但测试失败时，集成必须停止。
7. worktree 含 untracked 文件时，重叠检测必须纳入这些路径。
8. 合流完成前，release 视图仍指向原 tag／release commit。
9. 两个分支同时提出决策时使用不同临时 ID；集成时按顺序获得唯一正式 ADR 编号并保持引用正确。

## 已确认的首版选择

1. 主 worktree 默认只供集成；工具在明确识别出普通实现任务误入主目录时应阻止写入，并给出创建独立 worktree 的恢复路径。
2. 分布式 branch handoff 优先复用平台 PR／Issue；没有平台能力时允许导出非权威的最小 Task Record，但首版不把它升级为新的文档层。
3. 首版不启用 `extensions.worktreeConfig`，使用私有 `$GIT_DIR/orrery/` session 保持兼容。
4. canonical integration ref 默认为 `main`，允许由项目配置覆盖，并在 session 中固定实际 ref 和 OID。
5. 第一版检测路径、权威文档和验证面；符号／依赖分析延后，在结果中诚实保留 Semantic／Unknown 边界。
6. 分支决策使用 `docs/decisions/proposals/` 和稳定临时 ID，只在集成时分配正式 ADR 编号。
7. 控制面信息遵循 CLI／Harness 优先和按需展开；不要求 Agent 生成可机械派生的非关键回执、清单或状态叙述。
8. 核心先建设安全并行、两级指挥台、冲突预警和多人多 Agent 汇总；富接力与自动集成延后，多专家小队由独立编排 Skill／CLI 承担。
9. Scope Expansion 使用平衡策略 B：L0／L1 自动记录，L2 本机请求确认，L3 本机硬阻断。
10. 中央指挥台只读且向所有已登录项目成员展示全员状态；它只能发送请求。成员本地指挥台拥有执行权，远程请求必须本机确认。
11. 中央不同步完整对话或源码正文；未 push 工作只同步最小状态／路径元数据并显式保留 Semantic Unknown。首版权限采用 Member + Reviewer／Integrator／Admin capability，多设备体验后续展开。
12. 首版内置零云依赖的局域网临时 Host、发现和加入流程；同一时刻只有一个 Host，切换由成员手动发起，异地 relay／常驻服务保持可选。
13. 状态同步默认事件驱动并合并短时间内重复事件；heartbeat 默认关闭且可由成员启用，断线不明时以 Stale／Unknown 表达。
14. Workstream 使用生命周期阶段 + 当前运行状况 + 证据新鲜度投影；Review Ready 与 Integrated 由 Git／Harness／State 条件决定，不接受 Agent 单方面自报。
15. 创建入口采用混合模式：Agent-first 是需要优先兼容的常见入口，Orrery-first 是显式安全入口；平台不能 rebind 时启动新会话，dirty 主 worktree 永不自动迁移。
16. Workstream 默认映射现有 subsystem State，可影响多个 subsystem；worktree 不与单一模块硬绑定，Unmapped／新模块只产生提示或候选提案，不自动生成权威 State。
17. Direct／L3 finding 必须解决且不可豁免；Semantic／L2 可由成员本机写明理由后继续，但保持 Acknowledged、随 Scope／基线变化失效并强制进入集成审查。Agent 无批准权。
18. 跨成员 L2 由每位受影响成员分别确认自己的 Workstream；单方确认后可继续本地工作，但全员确认／解决／仲裁前不得 Review Ready。跨成员确认不要求所有人同时在线。
19. 权限采用基础 Member + 可叠加 Reviewer／Integrator／Admin capability；任何 capability 都不赋予中央远程执行权，Integrator 不能绕过 Direct／L3，Agent 本身不能持有治理 capability。
20. 默认 Personal Mode 为单成员多 Agent、纯本地且不启动团队网络能力；Team Mode 必须按项目手动开启，并且关闭团队模式不影响本地事实与开发。
21. 人类审查按风险分级：个人普通变更可自审；跨成员／共享权威和高风险候选要求非作者 Reviewer；AI 不计作人类审批，项目只能加严不能削弱硬门禁。
22. Review Ready 自动生成绑定 candidate HEAD／target OID／Scope／schema 的证据优先审查包；人类只能 Approve／Request Changes／Hold／Reject，任何候选或证据变化都会使旧批准失效，AI 只提供无权威摘要。
23. 集成后默认只建议清理并展示空间，成员本机确认后才删除合格的 clean worktree；branch 延迟提示删除，dirty／独有 commit／未知本地文件和未集成状态禁止自动清理。
24. Personal 与 Team 使用同一 Observatory 渐进扩展：默认首页只有项目状态、关注项、审查队列、Workstream／subsystem 概览；详情按需展开，Team Mode 仅增加 Team 页签且不提供跨成员直接执行按钮。

ADR-0007 已在 2026-08-20 的集成工作中正式接受；维护者随后接受的 Team Mode 与 Local-only telemetry 方向记录在 PO-DEC-WT-002。当前分支中的扩展 Design 只有在集成者分配正式 ADR 编号并合流后才成为 canonical。现有实现仍只完成工作目录隔离、恢复与人工集成流程；私有 session、自动重叠检测、审查／清理命令和观测台投影均待实现，不能把设计获批误写为工具已经完成。
