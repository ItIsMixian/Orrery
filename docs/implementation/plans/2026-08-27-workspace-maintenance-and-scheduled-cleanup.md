# Workspace Maintenance 与定时清理实施计划

Date: 2026-08-27
Status: Phase 0–2 implemented in `codex/w6-workspace-maintenance` Candidate；Phase 3／4 未开始，Promotion 待中央验证
Suggested task code: W6（仅在正式注册实现任务时生效）
Governing decisions: [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)
Approved design: [Multi-worktree collaboration protocol — 集成后的保守清理](../../design/multi-worktree-collaboration-protocol.md#集成后的保守清理)
Motivating evidence: [2026-08-27 local worktree cleanup](../../validation/2026-08-27-local-worktree-cleanup.md)

## 1. 计划定位

本计划把现有 W3 `inventory`／`cleanup eligibility` 从人工诊断能力推进为本地 Workspace Maintenance 工作流，解决长期开发中 worktree、stale session、生成缓存和旧分支不断累积的问题。

它必须保持以下区分：

```text
定时发现 ≠ 自动删除
建议可清理 ≠ 已获授权
本机授权 ≠ 中央远程执行
worktree 删除 ≠ branch 删除 ≠ remote branch 删除
```

当前基线已经具备：

- bounded workspace inventory；
- registered active／review pending／integrated closed／legacy／generated／retained／Unknown 分类；
- 路径、Git identity、dirty、untracked／ignored、独有 commit、closure／review／Validation 与 target OID 检查；
- 四种互不隐含且默认 `performed=false` 的清理动作；
- Personal Observatory 的 delivery／reconciliation／hygiene 投影。

W6 Candidate 已实现 Git-private maintenance queue、action-specific remove-worktree 执行器和图形化本机确认；仍不存在后台自动删除或跨平台计划任务 Adapter。2026-08-27 的 38→2 worktree 清理仍是维护者授权的人工操作，不是产品实现证据。

## 2. 目标体验

维护者不需要等到页面堆满几十个 worktree 才手工排查。系统应当：

1. Workstream 完成实际集成／关闭后立即重新评估；
2. Observatory 启动时，如果最近一次成功扫描已经过期，则自动补查；
3. 达到数量或空间阈值时，在 Personal Observatory 显示可解释提醒；
4. 默认把合格项放进“可安全清理”队列，由成员在本机逐项或批量确认；
5. 删除前重新绑定 exact path、HEAD、integration OID、closure、dirty fingerprint 和 ignored set，任何漂移都使授权失效；
6. 删除后写 Git-private receipt 并验证目录、worktree registry 和 branch 状态；
7. 不把机械盘点清单塞入 Agent 上下文，只在任务需要时提供摘要和原始证据入口。

## 3. 非目标

- 首版不实现后台默认自动删除。
- 不扫描整个磁盘或凭目录前缀认领 Orrery 所有权。
- 不自动删除 dirty、未集成、Rejected／Abandoned、独有提交、未知 untracked／ignored、recovery、evidence、benchmark、credential 或 cache-boundary 工作区。
- 不把 worktree、local branch、remote branch 合并为一个“清理”按钮。
- 不让 Team 中央、Admin／Integrator capability 或远端 Agent 直接删除成员本地目录。
- 不通过 PID kill、任意 shell、任意路径或任意 URL 执行清理。
- 不把 maintenance receipt 升级为 State／ADR／Validation；它只是 Git-private 操作证据。
- 不在本计划中实现符号依赖分析、自动 integration 或 branch GC。

## 4. 默认策略

首版建议默认值：

| 项目 | 默认值 | 说明 |
|---|---:|---|
| Observatory 启动补查 | 开启 | 最近成功扫描超过 24 小时才运行 |
| Workstream integrated／closed 事件 | 开启 | debounce 后触发一次只读扫描 |
| worktree 数量提醒 | 8 | 超过时显示 maintenance 提醒，不删除 |
| 可回收空间提醒 | 500 MB | 只使用 bounded inventory 估算 |
| integrated worktree 缓冲期 | 7 天 | 到期后才进入建议队列 |
| local branch 删除提醒 | 30 天 | 只提醒；与 worktree 动作分离 |
| remote branch 删除 | 永不自动 | 首版不观察远端状态 |
| 自动移除 worktree | 关闭 | 只有项目显式 opt-in 后才能进入后续阶段 |
| heartbeat／云服务 | 不需要 | Personal Mode 本地运行 |

默认阈值属于项目可调策略，不是 Authority Meta Model 语义。

## 5. 配置与事实边界

### 项目级策略

项目共享、可审查的 guardrail 放在 `.project-orrery.json` 的版本化候选字段：

```json
{
  "collaboration": {
    "workspace_maintenance": {
      "policy_version": 1,
      "scan_on_observatory_start": true,
      "catch_up_after_hours": 24,
      "worktree_count_threshold": 8,
      "reclaim_threshold_mb": 500,
      "integrated_grace_days": 7,
      "local_branch_reminder_days": 30,
      "auto_remove_eligible_worktrees": false,
      "ignored_allowlist": [
        "**/__pycache__/**",
        "docs/_site/**"
      ]
    }
  }
}
```

实现前必须为字段建立 schema、迁移与 unknown-field 失败关闭；本示例不是当前已支持配置。

### 主机级偏好与运行记录

以下内容只属于本机，不进入作者文档或发布包：

```text
$GIT_COMMON_DIR/orrery/maintenance/
├─ host.json              # 本机是否允许补查／通知／可选系统 scheduler
├─ last-run.json          # 最近成功／失败／中断扫描
├─ queue/                 # 绑定 exact evidence 的建议项
├─ authorizations/        # 本机人类授权
└─ receipts/              # 执行与后置验证回执
```

这些记录不能证明代码行为已验证，也不能替代作者 Validation。

## 6. Maintenance contract

### Scan record

每次扫描至少绑定：

- repository／Git common-dir identity；
- integration ref 与 exact OID；
- inventory schema／content hash；
- 触发来源：`integration-event`、`closure-event`、`observatory-catch-up`、`manual` 或 `os-scheduler`；
- 扫描开始／结束时间、结果、超时与错误类别；
- worktree／分类／Unknown／estimated reclaim 计数；
- `writes_performed=false`、`network_performed=false`。

### Queue item

建议项必须绑定：

- exact resolved path 与 workspace ID；
- worktree HEAD、branch、integration OID；
- session／closure／review／Validation hashes；
- dirty fingerprint、untracked set、ignored set hash；
- action 类型，只能是四种既有动作之一；
- eligibility reasons、Unknown、生成时间与过期条件；
- grace-period 起点和最早可执行时间。

### Lifecycle

```text
Observed
  → Suggested
  → Awaiting local confirmation
  → Authorized
  → Executing
  → Verified | Failed

任何输入漂移：Suggested / Authorized → Stale → 重新扫描
```

Agent、中央请求或旧 receipt 不能把条目推进为 `Authorized`。

## 7. CLI 与 Core 边界

Core 扩展平台中立 maintenance planner，不复制 W3 eligibility：

```text
orrery maintenance policy show
orrery maintenance scan [--reason ...] [--json]
orrery maintenance queue [--json]
orrery maintenance inspect <item-id> [--json]
orrery maintenance authorize <item-id> --action remove-worktree
orrery maintenance execute <authorization-id>
orrery maintenance receipt <receipt-id>
orrery maintenance schedule status
```

职责：

- `scan` 组合现有 inventory／cleanup eligibility，默认零写入；
- `queue` 只写 Git-private 建议，不改变工作区；
- `authorize` 必须在成员本机执行并重新验证 evidence binding；
- `execute` 只接受 authorization ID，不接受任意路径／shell／URL；
- `execute` 每次只执行一种动作；remove-worktree 不隐含 branch 删除；
- `receipt` 记录工具实际退出码、前后 Git registry、路径存在性和 branch 保留状态；
- 任何 Unknown、race、path alias、reparse、process-use 或 evidence drift 都失败关闭。

今天使用的 legacy／stale session 人工归档路径不进入首版自动队列。缺少 closure/review 的目标继续要求明确的维护者辅助流程。

## 8. 触发与调度

### Phase 1 默认触发

- `integrate` 成功并同步 closure 后发出 maintenance event；
- Workstream 合法进入 `closed` 后发出 maintenance event；
- Observatory 启动读取 `last-run.json`，超过 24 小时则执行 catch-up scan；
- 多个事件在短时间内合并，任何时刻同一仓库最多一个 scan；
- scan 失败不影响开发、Git、Observatory 其他页面或 Team Mode。

### 可选系统 scheduler

真正“应用关闭时仍定时运行”留到后续 Adapter：

- Windows Task Scheduler；
- cron；
- systemd user timer；
- macOS launchd。

Adapter 只调用固定 `maintenance scan` 命令，不能传入任意 action 或删除路径。安装、更新和卸载 scheduler 都必须本机确认、可审计、可逆；首个版本不要求常驻 daemon。

## 9. Observatory 体验

Personal Observatory 增加“工作区维护”入口，而不是继续扩大健康总览：

1. **一句话状态：** 最近扫描时间、worktree 数量、可安全清理数量、预计空间；
2. **需要你确认：** 只显示当前仍 eligible 的 remove-worktree 建议；
3. **受保护／未知：** 按原因分组，默认折叠；
4. **策略设置：** 阈值、缓冲期、启动补查、可选 scheduler 状态；
5. **历史：** Git-private run／authorization／receipt，只显示摘要和原始链接；
6. **动作边界：** worktree、local branch、remote branch 分栏确认，禁止一个按钮连锁删除；
7. **Team Mode：** 其他成员和中央只能发送 maintenance request，不能触发本机 execute。

默认首页只显示提醒，不固定加载完整路径、ignored 清单或历史日志。

## 10. 实施阶段

### Phase 0 — Contract 与 fixture

- [x] 定义 maintenance policy、scan、queue、authorization、receipt schema；
- [x] 冻结 synthetic Git corpus：clean integrated、dirty、unique commit、untracked、allowlisted ignored、sensitive ignored、reparse escape、stale closure、process-use、recovery/evidence、missing path；
- [x] 为 project policy 与 host-private preference 建立迁移／兼容规则；
- [x] 明确现有 W3 inventory／cleanup schema 的复用边界；
- [x] CLI 实现 dependency-free `scan --json`，零删除。

### Phase 1 — Event／startup scan 与建议队列

- [x] 接入 integration／closure 事件和 Observatory 24h catch-up；
- [x] 实现 single-flight、debounce、timeout、interrupted run 与幂等 last-run；
- [x] 生成 evidence-bound suggestion queue；
- [x] Observatory 展示维护摘要、受保护／Unknown 原因和策略；
- [x] Phase 1 检查点默认没有自动执行，执行器仅在 Phase 2 本机授权路径可达。

### Phase 2 — 本机确认执行

- [x] 实现 authorization ID 与 action-specific execute；
- [x] 删除前完整重新验证，漂移使授权 Stale；
- [x] 只实现 `remove-worktree`；branch 动作继续只提示；
- [x] 执行后验证目录、registry、branch、receipt 与失败恢复；
- [x] Observatory 支持逐项／批量本机确认，但逐项生成独立 authorization／receipt；
- [x] Team request 只进入本机 inbox，不调用 execute。

### Phase 3 — 显式 opt-in 自动 worktree cleanup

- [ ] 只有项目策略与本机偏好双重开启才生效；
- [ ] 仅限有有效 integrated closure、通过缓冲期且全部资格门当前有效的 clean worktree；
- [ ] 每次执行前重复 Phase 2 preflight；
- [ ] 设置每轮最大删除数和空间上限；
- [ ] 失败立即停止本轮，不继续处理后续目标；
- [ ] 仍不自动删除任何 branch。

### Phase 4 — 跨平台 scheduler Adapter

- [ ] 先实现 Windows Task Scheduler Adapter，并验证安装／更新／暂停／卸载；
- [ ] 再实现 cron／systemd user timer／launchd；
- [ ] scheduler 只能运行固定 scan，不拥有 execute capability；
- [ ] 项目移动、CLI 版本变化或权限失效时失败关闭并提示修复；
- [ ] installer／release 适配与跨平台 matrix 通过后才进入公开支持声明。

## 11. Validation 矩阵

| 场景 | 必须结果 |
|---|---|
| Observatory 高频启动 | 24h 内不重复扫描；超过阈值只运行一次 |
| integration／closure 事件风暴 | debounce 后单次 scan；事件原因可追溯 |
| dirty／untracked／unknown ignored | 不进入授权队列 |
| allowlisted cache | 只在精确 pattern 下忽略；敏感名称永远阻断 |
| unique commit／未合流 | 禁止自动和人工 execute 建议 |
| branch 已 cherry-pick 但图不为祖先 | 不仅凭 ancestry 删除；必须由 closure／review／Validation 证明 |
| path alias／大小写／8.3 | 收敛到同一已登记 worktree，不能绕过边界 |
| symlink／reparse escape | 扫描可报告但 execute 失败关闭 |
| authorization 后 HEAD／target／dirty 漂移 | authorization 变 Stale，拒绝执行 |
| process 正在使用目标 | 拒绝执行并保留队列项 |
| execute 中断／崩溃 | receipt 为 interrupted／unknown；下次 scan 不冒充成功 |
| worktree remove 成功 | branch 和 commit 仍存在；registry/path 后置验证通过 |
| local branch／remote branch | 不因 worktree action 隐式删除 |
| Team 中央请求 | 只生成本机请求，`execution_performed=false` |
| Personal Mode | 零网络；scheduler 未显式安装时无后台进程 |
| OS scheduler | 只能调用 scan；不能构造任意命令、路径或 execute |
| maintenance docs | State 只写已实现事实，Plan 不被 Observatory 当作能力 |

Checkpoint 至少运行：

```text
python -X utf8 -m unittest -v tests.test_workspace_maintenance
python -X utf8 -m unittest -v tests.test_collaboration_w3 tests.test_personal_observatory
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out <isolated-output>
git diff --check
```

Candidate／Promotion 仍遵循全仓、本地站点／链接／安全门和 exact-SHA Windows／Ubuntu required checks。

## 12. State 与发布映射

实现阶段按实际完成范围更新：

- `docs/state/project-structure.md`：Git-private maintenance 目录、scheduler 与 worktree 事实；
- `docs/state/documentation-system.md`：Observatory 派生视图、作者事实不回写；
- `docs/state/release-and-toolchain.md`：CLI、scheduler Adapter、installer／release 状态；
- `docs/state/test-coverage.md`：fixture、race、安全和跨平台证据；
- `docs/validation/`：每个 Phase 的实际命令、环境、结果与残余边界；
- 由唯一整合者在合流时同步根 `PROGRESS.md`／`HANDOFF.md`／`DEVLOG.md`。

公开发布前还必须同步 Core／CLI／Observatory／Adapter 版本和兼容 manifest；未完成 Phase 4 不宣称“关闭应用后也会定时清理”。

## 13. ADR 边界

按本计划实现以下默认行为不需要新 ADR：

- 自动盘点、事件触发和启动补查；
- 默认建议队列；
- 本机逐项确认后移除严格合格 worktree；
- 项目显式 opt-in 的“集成后自动移除合格 clean worktree”；
- branch 与 worktree 动作继续分离。

出现以下任一变化必须先 amendment ADR-0007／0008：

- 默认开启后台自动删除；
- 允许中央／Agent／Admin 远程执行成员本机删除；
- 允许绕过 closure、dirty、unique commit、Unknown 或 ignored 安全门；
- 一个授权隐含 worktree、local branch、remote branch 多重删除；
- 上传源码正文、未 push diff、凭据或完整本机路径清单到中央服务。

## 14. 完成定义

本计划只有在以下条件全部满足后才可标记完成：

1. Phase 0–2 已形成可运行、可恢复、默认本机确认的完整维护闭环；
2. Personal Mode 默认仍零网络、无 scheduler、无自动删除；
3. 合格与不合格 fixture 都通过，race／中断／路径边界失败关闭；
4. Observatory 能解释为什么可以／不可以清理，而不是只显示数量；
5. worktree 删除后 branch／commit 和 Git-private receipt 可验证；
6. State、Validation、DEVLOG 与真实实现一致；
7. exact-SHA Windows／Ubuntu required checks 通过；
8. 维护者完成一次真实本机演练并明确接受。

Phase 3／4 可作为后续里程碑，不阻塞默认建议＋本机确认闭环的首次交付；但未实现时必须继续明确标为 unsupported。
