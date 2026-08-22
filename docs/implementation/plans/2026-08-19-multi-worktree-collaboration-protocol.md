# 实施计划：多 worktree 协作协议

Status: Active

Date: 2026-08-19

Governing decisions:

- [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)
- [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../../design/multi-worktree-collaboration-protocol.md)

> ADR-0007 与 ADR-0008 已接受，本 Plan 进入完整活动状态。当前恢复与集成工作只证明人工隔离流程可行；完成清单不等于功能已经实现，State 只能记录已经验证的实际行为。

## 实施边界

### 包含

- Git worktree／clone 身份、事实作用域和私有 session 的平台中立数据模型。
- 创建／检查 Workstream worktree 的命令行入口，以及主 worktree 集成专用守卫。
- committed、staged、unstaged、untracked 和 expected-write 路径采集。
- Direct、Authority、Semantic、Unknown 四级重叠报告。
- 独立 integration worktree 中的 dry-run 合流和验证编排。
- 观测台上的 branch、OID、merge base、ahead／behind、dirty 与作用域投影。
- 临时决策 ID 到正式 ADR 编号的集成期检查与迁移。
- 由 Git／Harness／CLI 机械生成状态、范围与验证数据，并为 Agent 提供按需查询而不是固定上下文注入。
- 单人一级、多人按 Member 聚合的指挥台展示，以及与平台能力相匹配的独立执行层。

### 不包含

- 自动解决 merge 或语义冲突。
- 实时协同编辑、中央全局锁、未获本地 Node 主动上报的跨机器未 push 工作发现，或上传未 push 源码正文进行中央分析。
- 首版符号图、完整依赖图或通用 CI 平台适配器。
- 自动接受 ADR、自动把 Candidate State 升级为 canonical，或用 session 取代作者文档。
- 首版自动更新 integration ref；当前只生成 AI 辅助审查包并由人类执行合流。
- 富 Agent 接力、对话推理迁移和长期任务记忆；首版只实现最小 session checkpoint。
- 多专家 Agent 小队编排；独立 Skill／CLI 可以在未来消费本 Plan 提供的原语。
- 独立事故恢复子系统；继续使用 Git 恢复点和 Orrery 权威链。
- 当前其他分支上的 provider、broker、平台适配和 Pilot 008 工作；它们只可作为未来回归样本，不能被本 Plan 顺带合并。

## 首版交付顺序

1. **Personal foundation**：先完成 Phase 0、Phase 1 和 Phase 2 的本机 contract、worktree／session、subsystem mapping、Scope B、finding 与主目录守卫；默认无网络。
2. **Personal review loop**：再完成本地 Observatory 摘要、Review Ready、证据优先审查包、人工 integration dry-run 和保守清理，形成单成员多 Agent 完整闭环。
3. **Opt-in Team extension**：Personal 路径稳定后才启用 Member／capability、内置 LAN Host、Local-only telemetry、请求与跨成员 finding；Team 依赖不能回流成 Personal 启动成本。
4. **Self-host and release**：最后执行自托管迁移、兼容验证、公开说明和发布；未经真实证据不改变支持状态。

阶段编号描述架构依赖，不要求在一个发布中同时交付全部 Team Mode。

## 分阶段任务

### Phase 0 — 合约与隔离 fixture

- [x] 为 worktree identity、session、overlap finding 和 integration report 定义版本化 JSON schema。
- [x] 建立最小 Git fixture：干净主分支、两个 linked worktree、独立 clone、untracked 文件和未 push 分支。
- [x] 固定 integration ref 的配置键、默认值和 OID 解析规则。
- [x] 定义主 worktree 识别方法与显式维护者覆盖机制。
- [x] 在 schema 中保留 `member_id`、`host_id`、visibility 和 observability 字段；首版默认一个 Workstream 一个 active host，不提前实现多设备迁移。
- [x] 从 AGENTS／State 索引定义 stable subsystem registry 和 `primary_subsystem_id`、`affected_subsystem_ids`、`Unmapped`／project-wide 表达；registry 只投影现有权威文档，不自动创造 State。
- [x] 为 Member 基础身份和 Reviewer／Integrator／Admin capability 定义可组合权限 schema、bootstrap maintainer、授予／撤销审计与本地凭据失效规则。
- [x] 定义 `personal`／`team` project mode；默认 personal 使用隐式本地成员和全部本地 capability，且证明没有网络监听、发现、Coordinator、成员认证或团队同步依赖启动。

Canonical checkpoint（2026-08-22）：上述 Phase 0 项由独立分支提交 `4ae4f0a` 实现，通过
[专项 Validation](../../validation/2026-08-22-personal-collaboration-phase-0.md)后经干净整合进入本地
`main`。它仍未进入发布包或 Team 网络层；Phase 1–5 的未勾选项不因 schema 存在而视为实现。

### Phase 1 — 身份与 session

- [ ] 实现 `orrery worktree create` 的平台中立核心。
- [x] 实现 `orrery worktree status --json` 的平台中立只读核心与稳定 JSON envelope。
- [x] 把 session 写入 `git rev-parse --git-path orrery/worktree.json`，不写入作者工作树。
- [x] 当 branch、HEAD、integration OID 或 dirty fingerprint 改变时将陈旧 session 标出；重建只通过显式 session write 完成。
- [x] 验证 linked worktree 和独立 clone 都能产生一致的作用域字段。
- [x] 为 CLI 输出定义结构化、可按需展开的状态摘要；证明 Agent 无需生成或固定读取可机械派生的 Manifest／Receipt。
- [ ] 为 lifecycle phase、runtime condition、evidence freshness、closure reason 定义互不混淆的 schema 与合法转换；阶段回退和 Review Ready 撤销必须可解释。
- [ ] 定义 Adapter 的 launch／attach／rebind／message capability matrix，并覆盖 Orrery-first、Agent-first 自动 attach、首次写入守卫、无法 rebind 时新会话降级和 dirty 主 worktree 拒绝自动迁移。

Candidate checkpoint W1.1（2026-08-22）：实现提交 `6c5570d` 在独立分支
`codex/w1-1-personal-phase-1a` 完成上述五项最小 Phase 1A 闭环。Core 0.1.2 生成 branch／HEAD、
integration ref／OID、merge base、ahead／behind、dirty fingerprint 与计数；CLI 0.1.7 的
`worktree status` 保持只读，`worktree session write` 才显式原子写入 Git 私有路径。linked worktree／
独立 clone、stale reason、zero-network 和作者工作树不变均由
[专项 Validation](../../validation/2026-08-22-w1-1-personal-phase-1a.md)覆盖。该 Candidate 未实现
worktree create、主目录写入守卫、完整 lifecycle／attach／rebind、Scope/Finding、Observatory 或 Team runtime。

### Phase 2 — 范围采集与重叠检测

- [ ] 采集 merge base 至 HEAD 的 committed paths。
- [ ] 采集 staged、unstaged、untracked 与 session expected writes，保留路径来源。
- [ ] 从 Project Orrery 配置和文档索引识别 State、ADR、Design、Plan、Validation、PROGRESS、HANDOFF 等权威面。
- [ ] 输出 Direct、Authority、Semantic 和 Unknown findings；不把缺失远端证据解释为安全。
- [ ] 对凭据、release 和 schema migration 等独占资源提供可配置硬门禁。
- [ ] 实现 Scope Expansion B 策略：L0／L1 自动 revision，L2 本机确认，L3 本机拒绝；中央服务不能绕过本机门禁。
- [ ] 从实际／预期路径与 registry 派生 subsystem mapping；未预期跨 subsystem 触发 L2，Unmapped 保持显式，Shared subsystem 进入 Semantic 优先检查但不自动判冲突。
- [ ] 实现 Open／Acknowledged／Resolved／Stale finding lifecycle；Direct／L3 无豁免入口，Semantic／L2 的本机确认记录成员、理由、时间和 Scope Revision，并在范围／基线变化后失效。
- [ ] 将所有 Acknowledged L2 finding 和历史处置纳入人工集成审查包；Agent 自报和中央请求都不能直接改变 finding disposition。
- [ ] 为跨成员 L2 保存 per-member acknowledgement 和必需成员集合；单方确认只解锁其本地工作，整体以 `n/m` 投影，并在全员确认／解决／仲裁前阻止 Review Ready。

### Phase 3 — 推测性集成与人工审查

- [ ] 实现 `orrery integrate --target <ref> --dry-run`，只在新建干净 integration worktree 中运行。
- [ ] 固定 target OID，计算 merge base 与 ahead／behind，并拒绝目标在运行期间静默漂移。
- [ ] 尝试 merge／rebase，运行 Workstream 声明的验证、受影响子系统验证与文档一致性检查。
- [ ] 验证 Candidate State 与推测性合流后的实现一致；失败时保留报告并停止进入人工审查队列。
- [ ] 检查临时决策 ID，计算正式 ADR 编号候选，并要求集成者确认重命名和引用更新。
- [ ] 生成包含 diff、重叠、验证、State 对齐和回退点的 AI 辅助审查包；首版由人类执行实际 merge，不自动更新 integration ref。
- [ ] 实现风险分级审查策略：personal 普通变更可自审，team 普通变更由 Integrator 审查，跨成员 L2／Authority／共享接口和高风险变更要求非作者 Reviewer；AI 不能满足人类审批计数。
- [ ] 将审查包绑定 candidate HEAD、target OID、Scope Revision 和 schema/hash，按证据／链接在前、AI 派生摘要在后的顺序生成，并拒绝失败证据被摘要隐藏。
- [ ] 实现 Approve／Request Changes／Hold／Reject 记录与失效规则；新提交、Scope／target／finding 变化或验证过期后旧批准变 Stale，Approve 只进入人工 Integrator 流程。
- [ ] 实现集成后清理资格报告：canonical ancestry、clean、独有 commit、untracked／ignored、closure record 和预计回收空间；默认只建议，本地成员确认后分别处理 worktree／local branch／remote branch。

### Phase 4 — 观测台与平台适配边界

- [ ] 在本地观测台页首显示当前 scope、branch、HEAD、integration OID、merge base、ahead／behind、dirty 和 untracked 数量。
- [ ] 展示其他本机可见 worktree 的重叠告警，并把远端不可见状态显示为 Unknown。
- [ ] 单人视图直接展示 Workstream／Agent；多人视图先按 Member 汇总再下钻到各自 Workstream，Host 只作为定位元数据。
- [ ] 默认只显示 Personal Mode 本地多 Agent 体验；用户按项目明确开启 Team Mode 后才加载成员、中央视图、局域网 Host／加入和同步设置。
- [ ] 在同一 Observatory 中实现项目状态、关注项、审查队列、活动 Workstream／subsystem 四区首页；卡片保持摘要，Scope／路径／日志／finding／review／cleanup 只在详情按需展开。
- [ ] Team Mode 只增加 Team 页签、Member 聚合、同步／请求／capability 视图；My Workstreams 保留本地执行动作，Team／他人卡片只能查看和发送请求。
- [ ] 把只读展示层与执行层分开；执行动作必须经过成员权限和平台 Adapter capability 检查。
- [ ] 中央指挥台允许所有已认证项目成员查看全员状态，但只能发送请求；成员本地指挥台必须对远程请求做明确确认后才执行。
- [ ] 按 capability 约束审查、合流、ADR 编号、canonical State 同步、成员和团队设置；验证 Admin／Integrator 也不能直接操作其他成员机器或绕过 L3。
- [ ] 中央同步层拒绝完整 Prompt／回答／transcript 和源文件正文，只接受版本化任务、Git、scope、验证、finding 与 last-seen 元数据。
- [ ] 未 push 工作显示为 `Local-only`；路径级证据不足以判断的语义关系保持 Unknown。已 push 源码继续由 Git 托管权限处理，不复制进 Orrery 协调存储。
- [ ] 在成员本地指挥台内置局域网 Coordinator Host 的启动、自动发现、成员验证、Host 确认和手工邀请地址回退；发现广播不能包含任务状态或源码元数据。
- [ ] 实现单 active Host 与手工 Host 切换；Host 离线不影响本地工作，新的 Host 按单调 revision 重新聚合在线成员状态。首版不做自动 leader election。
- [ ] 默认只在 Workstream／Scope、Agent 阶段、Git、验证或 finding 变化时经 debounce 后同步；提供立即同步，presence heartbeat 默认关闭并允许成员启用／调频／关闭。
- [ ] 对断连、突然掉线、Sharing off 和长期未更新分别投影 Offline、Stale／Unknown、Unavailable，不把最后快照当成实时事实。
- [ ] 分开展示 Workstream 生命周期、运行状况和证据新鲜度；不能把 Agent 自报的“完成”直接映射为 Review Ready、Integrated 或 Closed。
- [ ] 保持核心 Git 数据模型与 Codex、Claude Code、CI 或代码托管平台适配器分离。
- [ ] 所有状态投影只读，不回写 State、ADR 或 Plan。

### Phase 5 — 自托管迁移与发布

- [ ] 先在 Project Orrery 自身的隔离 fixture 和真实 linked worktree 上试用。
- [ ] 验证 shared Git private closure archive 在移除 linked worktree 后仍可读取，且不进入作者文档或发布资产。
- [ ] 通过 Validation 后更新 State Docs、PROGRESS、HANDOFF 和 DEVLOG。
- [ ] 同步 skill／通用 agent 模板、安装器、迁移合约和中英文公开说明。
- [ ] 完成向后兼容检查、包验证和发布说明；未经验证不提升版本或 tag。

## 预期实现目标

具体文件名由 Phase 0 的接口设计确定。平台中立组件是新实现的权威目标；现有 Skill 路径只作为兼容 wrapper／投影，预计影响：

- `packages/project-orrery-core/`：identity、session、scope、subsystem、finding、review、cleanup 和 project-mode schema／规则。
- `packages/project-orrery-cli/`：worktree、status、overlap、review、integrate dry-run 和 cleanup 命令编排。
- `packages/project-orrery-observatory/` 与根 `scripts/docsite/`：Personal／Team 投影、详情、请求和本地 Host UI／runtime 边界。
- `adapters/`：Codex、Claude 或其他平台的 launch／attach／rebind／message capability；不复制 Core 规则。
- `skills/project-orrery/`：当前发布兼容入口和工具投影，不能成为第二套 canonical 实现。
- `tests/`：平台中立单元／集成测试与 Git fixture。
- `docs/state/`、`docs/validation/`：完成后的当前事实和独立证据。

不得在实现开始前仅凭本 Plan 将上述目标写成 State 当前事实。

## Validation 矩阵

| 场景 | 必须证明 |
|---|---|
| 主 worktree dirty，新建 linked worktree | 新 worktree 保持 clean，索引和 `$GIT_DIR` 私有，`$GIT_COMMON_DIR` 共享 |
| 两任务修改相同 tracked／untracked 路径 | 产生 Direct finding，报告包含来源和双方 scope |
| 两任务修改同一 State／ADR／全局入口 | 产生 Authority finding，并要求唯一整合者 |
| 不同文件共享 schema／验证面 | 产生 Semantic finding或在推测性集成测试中失败，不宣称路径独立即安全 |
| Team Mode 未开启、未分享或 worktree 不可访问 | 产生 Unknown／Unavailable，不显示为零冲突 |
| Candidate State 打开观测台 | 明确显示 Candidate／Worktree 作用域，不出现在 canonical 视图中 |
| 纯文本 merge 成功但测试失败 | integration ref 不更新，报告保留失败证据 |
| 两分支同时创建决策 | 使用不同临时 ID；集成时获得唯一连续 ADR 编号并更新所有引用 |
| integration target 在验证中漂移 | 操作失败或要求基于新 OID 重跑 |
| 旧配置／无 worktreeConfig | 功能降级可解释，仓库仍可由支持的 Git 版本打开 |
| 同子系统无冲突的功能扩张 | 自动生成新 Scope Revision，不要求用户或 Agent 重写完整任务说明 |
| L2／L3 扩张 | L2 只能由成员本机确认；L3 在解决 finding 前保持阻断，中央请求不能越权 |
| 中央成员视图 | 任一已认证项目成员可查看全员状态，但不能直接操作其他成员 Agent |
| 未 push 本地工作 | 只显示 Local-only 元数据；不上传源码正文，Semantic 证据不足时显示 Unknown |
| 中央数据泄漏检查 | 不包含完整 Prompt、回答、transcript、源文件正文或成员本机执行凭据 |
| 同局域网零外部依赖 | 成员可内置启动／发现／加入临时 Host；不要求云服务器、虚拟局域网或手工端口配置 |
| 发现与加入安全 | 发现广播不含任务数据，非项目成员不能读取状态，加入需要验证与 Host 确认 |
| Host 离线与切换 | 本地工作不受影响；新 Host 手工启动后按 revision 聚合，不接受旧状态覆盖新状态 |
| 事件驱动同步 | 空闲时没有强制应用 heartbeat；变化事件经合并发送，立即同步可用，heartbeat 可选且可关闭 |
| 无 heartbeat 突然断线 | 超过 TTL 显示 Stale／Unknown，不把旧状态继续标成在线或当前事实 |
| 阶段与状况并存 | Implementing + Waiting、Validating + Offline 等组合可准确表达，不互相覆盖 |
| Review Ready 门禁 | commit、clean/exclusion、验证、L2/L3 finding、Candidate State 和 integration base 条件全部由工具核对；Agent 自报不能越过 |
| Review Ready 撤销 | 新 Scope、基线漂移、验证过期或新 finding 出现后自动退回适当阶段并保留原因 |
| Integrated 与 Closed | 只有进入 canonical ref 且集成验证／State 同步后标 Integrated；Closed 必须有明确 closure reason |
| Agent-first 已在 Workstream worktree | 自动 attach 现有 Workstream，不要求用户从指挥台重新创建会话 |
| Agent-first 误入 clean 主 worktree | 首次产品写入前阻断，并按 Adapter capability rebind 或启动新会话 |
| 主 worktree 已 dirty | 不自动迁移或覆盖；建立恢复边界后由人类／AI 辅助选择性转移 |
| 平台不支持 rebind | 正确 worktree 中的新会话获得最小 continuation brief，旧会话停止写入且不伪装为原地迁移 |
| subsystem 映射 | 默认关联现有 State module；多模块可表达，未预期跨模块触发 L2，Unmapped 不自动生成 State |
| Direct／L3 处置 | UI／CLI 不提供豁免；条件未实际消失时写入持续阻断，Agent 或中央请求不能越权 |
| Semantic／L2 处置 | 成员本机提供理由后可继续，finding 仍可见并进入集成审查；缺失理由或 Agent 自报不生效 |
| Acknowledgement 失效 | Scope Revision、integration base、接口／验证面或对端变化后变 Stale 并重新请求处置 |
| 同成员多 Agent L2 | 成员一次本机处置覆盖自己负责的相关 Workstream，记录仍按 finding／Scope 可追溯 |
| 跨成员部分确认 | 已确认成员可继续本地开发；中央显示 n/m，未全员确认时所有相关 Workstream 均不能 Review Ready |
| capability 可叠加 | 同一成员可组合 Member／Reviewer／Integrator／Admin，普通 Member 不会隐式获得审查、合流或管理权限 |
| 治理能力不等于远程执行 | Admin／Integrator 只能执行项目流程或发送请求，不能直接控制其他成员 Agent／shell，也不能豁免 Direct／L3 |
| capability 撤销 | 中央权限、邀请和旧设备／本地授权按审计记录失效，离线节点重连后不能继续使用旧 capability |
| Personal Mode 默认 | 初次使用只启用本地多 Agent／worktree 能力；没有端口监听、发现广播、团队凭据、状态上报或额外同步服务 |
| Team Mode 显式开启／关闭 | 只有本机确认后才启动团队能力；关闭后网络与同步停止，本地 Workstream／Git／Validation／文档完整保留 |
| 风险分级审查 | personal 普通变更可自审；跨成员／Authority／高风险候选强制非作者 Reviewer，AI 摘要不计入批准数 |
| 审查包完整性 | Scope、Change Set、subsystem、Git、Validation、finding／ack、ADR／State、漂移／Unknown 和原始链接均存在，AI 摘要位于证据之后 |
| 审查批准绑定 | Approve 绑定精确 HEAD／target OID／Scope／schema hash；任一输入变化后旧批准 Stale 且不能继续合流 |
| 四种审查动作 | Approve 只进入人工合流；Request Changes 回退、Hold 暂停、Reject 保留理由和回退入口；AI 不能触发任何动作 |
| 集成后安全清理 | 仅 clean、已合流、无独有 commit、无未知 untracked／ignored 的 worktree 可进入建议队列；默认必须成员本机确认 |
| 清理动作独立 | 移除 worktree、删除本地 branch、删除远端 branch 分别授权；任一动作不能暗中触发其他删除 |
| 不安全／未完成候选 | dirty、Rejected、Abandoned、未集成、独有 commit 或未知本地文件时自动清理始终失败关闭 |
| closure record | worktree 删除后仍可从 Git 私有管理区追溯 final HEAD、integration commit、review、Validation 和清理操作，且不污染作者文档／发布包 |
| Personal 首页信息密度 | 四个主区域和摘要卡能呈现需要关注／审查／活动状态，详细路径与日志不在首页固定加载或注入 Agent 上下文 |
| Team 渐进启用 | Personal Mode 看不到团队网络／成员负担；开启后同一 Observatory 增加 Team 页签，不出现第二套权威或重复任务数据 |
| 中央／本地按钮边界 | My Workstreams 可执行本地动作；Team 和其他成员卡片只有查看／请求，视觉与接口都不能误触发远程执行 |

最低验证命令将在实现时固化为仓库脚本；至少包括：

```text
python -m unittest discover -s tests -v
python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
git diff --check
```

此外必须使用 `python scripts/docsite/build_docsite.py --out <隔离的临时 HTML 路径>` 完成一次静态构建，并在 Validation 中记录实际路径和结果，不能手工改写 `docs/_site/index.html` 或虚构通过结果。

## State 与交接映射

实现和验证完成后更新：

- `docs/state/project-structure.md`：worktree／clone、主工作区和私有 session 的实际结构。
- `docs/state/documentation-system.md`：三层事实作用域与 candidate 文档呈现。
- `docs/state/release-and-toolchain.md`：命令行、兼容性和集成门禁。
- `docs/state/test-coverage.md`：fixture、overlap 和 integration 验证覆盖。
- `docs/PROGRESS.md`, `docs/HANDOFF.md`, `docs/DEVLOG.md`：只在合流阶段同步 canonical 进度、风险和历史。

若实施有意改变本提案的主 worktree、三层作用域、临时 ADR ID 或 clean integration worktree 规则，必须先新增或修订候选决策，不能只改代码或 Plan。
