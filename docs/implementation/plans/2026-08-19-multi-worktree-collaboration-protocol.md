# 实施计划：多 worktree 协作协议

Status: Active

Date: 2026-08-19

Governing ADR: [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)

Approved Design: [多人／多 worktree 协作协议](../../design/multi-worktree-collaboration-protocol.md)

> ADR-0007 已接受，本 Plan 进入活动状态。当前恢复与集成工作只证明人工隔离流程可行；完成清单仍不等于功能已经实现，State 只能记录已经验证的实际行为。

## 实施边界

### 包含

- Git worktree／clone 身份、事实作用域和私有 session 的平台中立数据模型。
- 创建／检查任务 worktree 的命令行入口，以及主 worktree 集成专用守卫。
- committed、staged、unstaged、untracked 和 expected-write 路径采集。
- Direct、Authority、Semantic、Unknown 四级重叠报告。
- 独立 integration worktree 中的 dry-run 合流和验证编排。
- 观测台上的 branch、OID、merge base、ahead／behind、dirty 与作用域投影。
- 临时决策 ID 到正式 ADR 编号的集成期检查与迁移。

### 不包含

- 自动解决 merge 或语义冲突。
- 实时协同编辑、中央全局锁或跨机器未 push 工作发现。
- 首版符号图、完整依赖图或通用 CI 平台适配器。
- 自动接受 ADR、自动把 Candidate State 升级为 canonical，或用 session 取代作者文档。
- 当前其他分支上的 provider、broker、平台适配和 Pilot 008 工作；它们只可作为未来回归样本，不能被本 Plan 顺带合并。

## 分阶段任务

### Phase 0 — 合约与隔离 fixture

- [ ] 为 worktree identity、session、overlap finding 和 integration report 定义版本化 JSON schema。
- [ ] 建立最小 Git fixture：干净主分支、两个 linked worktree、独立 clone、untracked 文件和未 push 分支。
- [ ] 固定 integration ref 的配置键、默认值和 OID 解析规则。
- [ ] 定义主 worktree 识别方法与显式维护者覆盖机制。

### Phase 1 — 身份与 session

- [ ] 实现 `orrery worktree create` 和 `orrery worktree status --json` 的平台中立核心。
- [ ] 把 session 写入 `git rev-parse --git-path orrery/worktree.json`，不写入作者工作树。
- [ ] 当 branch、HEAD、integration OID 或 dirty fingerprint 改变时将陈旧 session 标出或重建。
- [ ] 验证 linked worktree 和独立 clone 都能产生一致的作用域字段。

### Phase 2 — 范围采集与重叠检测

- [ ] 采集 merge base 至 HEAD 的 committed paths。
- [ ] 采集 staged、unstaged、untracked 与 session expected writes，保留路径来源。
- [ ] 从 Project Orrery 配置和文档索引识别 State、ADR、Design、Plan、Validation、PROGRESS、HANDOFF 等权威面。
- [ ] 输出 Direct、Authority、Semantic 和 Unknown findings；不把缺失远端证据解释为安全。
- [ ] 对凭据、release 和 schema migration 等独占资源提供可配置硬门禁。

### Phase 3 — 推测性集成

- [ ] 实现 `orrery integrate --target <ref> --dry-run`，只在新建干净 integration worktree 中运行。
- [ ] 固定 target OID，计算 merge base 与 ahead／behind，并拒绝目标在运行期间静默漂移。
- [ ] 尝试 merge／rebase，运行任务验证、受影响子系统验证与文档一致性检查。
- [ ] 验证 Candidate State 与合流后实现一致；失败时保留报告并停止更新 integration ref。
- [ ] 检查临时决策 ID，计算正式 ADR 编号候选，并要求集成者确认重命名和引用更新。

### Phase 4 — 观测台与平台适配边界

- [ ] 在本地观测台页首显示当前 scope、branch、HEAD、integration OID、merge base、ahead／behind、dirty 和 untracked 数量。
- [ ] 展示其他本机可见 worktree 的重叠告警，并把远端不可见状态显示为 Unknown。
- [ ] 保持核心 Git 数据模型与 Codex、Claude Code、CI 或代码托管平台适配器分离。
- [ ] 所有状态投影只读，不回写 State、ADR 或 Plan。

### Phase 5 — 自托管迁移与发布

- [ ] 先在 Project Orrery 自身的隔离 fixture 和真实 linked worktree 上试用。
- [ ] 通过 Validation 后更新 State Docs、PROGRESS、HANDOFF 和 DEVLOG。
- [ ] 同步 skill／通用 agent 模板、安装器、迁移合约和中英文公开说明。
- [ ] 完成向后兼容检查、包验证和发布说明；未经验证不提升版本或 tag。

## 预期实现目标

具体文件名由 Phase 0 的接口设计确定，预计影响：

- `skills/project-orrery/scripts/`：Git identity、session、overlap 和 integration 核心。
- `skills/project-orrery/assets/project-template/`：配置与 Agent 入口中的协作边界。
- `scripts/docsite/`：只读 scope banner 和 overlap 投影。
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
| 远端分支未 push 或 worktree 不可访问 | 产生 Unknown，不显示为零冲突 |
| Candidate State 打开观测台 | 明确显示 Candidate／Worktree 作用域，不出现在 canonical 视图中 |
| 纯文本 merge 成功但测试失败 | integration ref 不更新，报告保留失败证据 |
| 两分支同时创建决策 | 使用不同临时 ID；集成时获得唯一连续 ADR 编号并更新所有引用 |
| integration target 在验证中漂移 | 操作失败或要求基于新 OID 重跑 |
| 旧配置／无 worktreeConfig | 功能降级可解释，仓库仍可由支持的 Git 版本打开 |

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
