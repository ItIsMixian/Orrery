# 多人／多 worktree 协作协议

Status: Approved

Governing ADR: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)

Evidence date: 2026-08-19

## 问题

Project Orrery 当前把 State Docs 定义为“现在是什么”，但多人在不同分支、clone 或 linked worktree 中工作时，“现在”至少存在三种不同视角：集成分支已经提交的事实、功能分支的候选事实，以及尚未提交的本地工作副本。如果这些视角没有显式绑定到 commit 和 worktree，任一 Agent 都可能把局部状态误写成全局事实。

共享同一工作目录更加危险。两个 Agent 即使声称在处理不同任务，也会同时看到并修改同一份未提交文件、索引和生成物；Git 无法替它们区分文件所有权。

## 目标

1. 一项并发任务拥有独立分支、工作目录、索引和验证空间。
2. Canonical State、branch candidate state 与 dirty worktree state 不再混写。
3. 保持 Git 分支异步，不建立仓库级全局锁。
4. 在合流前发现文件、权威文档、依赖和验证层冲突。
5. 让协作元数据尽量由 Git 与工具生成，不要求每个小任务新增人工文档。
6. 同时支持同机 linked worktree 和不同机器的独立 clone。

## 非目标

- 不提供多人实时共同编辑。
- 不宣称能够发现尚未提交、未推送且位于另一台机器上的工作。
- 不自动解决语义冲突或替维护者接受 ADR。
- 不把任务清单、仪表盘或冲突预测升级成新的事实源。
- 不要求所有平台启用 `extensions.worktreeConfig`；旧 Git 兼容性必须单独评估。

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

- 每个并发任务使用一个专属分支和一个专属 worktree 或 clone。
- 主 worktree 保留给维护者／集成者；普通 Agent 不直接在其中实现任务。
- 同一分支不被多个 worktree 同时检出。多人共同任务通过独立子分支和集成分支协作。
- 创建任务 worktree 时固定并记录 `integration_ref`、起始 OID 和 merge base。

### 2. Worktree Session

工具在 `git rev-parse --git-path orrery/worktree.json` 返回的位置维护本地 session。该路径位于每个 worktree 私有 `$GIT_DIR`，不进入提交，也不制造作者文档。

最小候选结构：

```json
{
  "schema": 1,
  "task_id": "PO-WT-001",
  "worktree_id": "local stable id",
  "branch": "codex/example",
  "head": "full commit oid",
  "integration_ref": "refs/remotes/origin/main",
  "integration_oid": "full commit oid",
  "merge_base": "full commit oid",
  "expected_writes": ["path/or/pattern"],
  "governing_docs": ["docs/state/example.md"],
  "validation": ["exact command"],
  "captured_at": "RFC 3339 timestamp"
}
```

Session 是可重建执行元数据，不是 State 或 Plan。它必须在 HEAD、分支或 dirty fingerprint 改变后被重新计算；Agent 自己填写的字段不能冒充独立证明。

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

跨机器时只能分析已经 push 的分支、PR／MR 元数据和 CI 证据。尚未 push 的另一台机器工作在技术上不可见，协议必须诚实暴露这一边界。

### 4. 分支内工作

- 代码、配置、测试以及受影响的 subsystem State 在同一功能分支同行。
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

## 候选工具面

```text
orrery worktree create <task-id> --branch <branch> --from <integration-ref>
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
5. 分支已提交但未 push 时，远端协调器必须显示 Unknown，而不是“无冲突”。
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

维护者已于 2026-08-19 同意上述方向，ADR-0007 已在 2026-08-20 的集成工作中正式接受。本 Design 现为 Approved Design。当前仅完成了工作目录隔离、恢复与人工集成流程；私有 session、自动重叠检测、集成命令和观测台作用域投影仍待实现，不能把协议获批误写为工具已经完成。
