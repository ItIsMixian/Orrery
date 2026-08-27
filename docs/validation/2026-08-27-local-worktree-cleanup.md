# Validation：本机历史 worktree 清理

Date: 2026-08-27

Status: Local workspace cleanup PASS；只删除 worktree 目录，不删除本地／远端 branch，不修改源码历史或发布状态

Scope: Project Orrery self-host 本机工作区。操作由维护者明确要求，在 W5C Worktree Candidate 中执行；本记录描述外部 Git／文件系统状态，不把本机清理外推为产品自动清理能力。

## 清理前审计

- Personal Observatory：38 worktrees、41 reconciliation、34 workspace hygiene；
- W3 inventory：34 legacy-unmanaged、3 registered-active、1 review-integration-pending；
- 第一批候选 31 个全部 tracked=0、untracked=0；ignored 内容只有 1,377 个 `__pycache__` 文件和 5 个 `docs/_site` 生成物；
- 敏感名称检查未发现 `.env`、`ai-config.json`、credential、secret、token、raw、benchmark 或 `.project-orrery-backup`；
- 没有其他进程引用候选路径；31 个目录约 117.1 MB；
- patch/ancestry 不作为删除 branch 的依据：部分 source branch 经 cherry-pick 集成，所有 branch 和 commit 均保留。

第一阶段明确保留：

- primary `D:\coding warehouse\project-orrery`；
- immutable recovery `D:\coding warehouse\project-orrery-integration-20260820`；
- final W4/W5 integration candidate `D:\coding warehouse\project-orrery-integration-w4-w5-20260823`；
- current W5C `D:\coding warehouse\project-orrery-w5c-team-observatory-ux`；
- 第一阶段还保留 3 个被 stale session 保护的历史任务，待单独归档。

## 第一阶段：legacy worktree removal

- 对 31 个目标逐项重新验证：路径必须属于 `D:\coding warehouse\` 或 `C:\Users\1\.codex\worktrees\`，必须仍是精确 registered worktree，必须不在 preserve 集合，tracked/untracked 必须为 0，ignored 只能命中 `__pycache__`／`docs/_site`，不得被进程引用；
- 使用 `git worktree remove --force <exact-path>` 只移除 worktree；没有执行 `git branch -d/-D`、remote delete 或普通递归目录删除；
- 删除后 38 → 7 worktrees，所有抽查的 source branch 仍存在；
- Personal Observatory 变为 7 worktrees、41 reconciliation、3 hygiene，说明目录债务已去除，但 stale coordination metadata 尚未收尾。

## 第二阶段：stale session retirement

三个旧 session 均为 clean worktree，但 session binding 已 stale：

| Workstream | Branch | Old phase | Stale reasons | Archived session SHA-256 |
|---|---|---|---|---|
| `W3-review-integration-cleanup` | `codex/w3-review-integration-cleanup` | implementing | head changed, integration OID changed | `FF9ECBACE391445D05BCB2FA873CC158DB924F74A1747A5C1C132B383FAF6F9F` |
| `W1.3` | `codex/w1-3-personal-phase-1c` | validating | integration OID changed | `D4A9772E7EE30C9387E07922F05B8E2B534C54C91AA392A76B38CD0F2AF152FC` |
| `PO-W4-PERSONAL-OBSERVATORY` | `codex/w4-personal-observatory` | implementing | head changed, integration OID changed | `CD0FFC251756B39F502A8380865E896D6DDA3EFCFD9B527169DC34EEF49F5049` |

- 现有 CLI 拒绝对 stale session 伪造正常 transition，因此没有把它们改写为 integrated／closed；
- 各 worktree Git-private `orrery/` 元数据先复制到 `.git/orrery/retired-worktree-sessions/2026-08-27/<branch>-<head>/`，复制前后 `worktree.json` SHA-256 相同；
- archive 位于 Git-private 区域，不进入作者文档、发布包或 Observatory 活动扫描；
- 归档后移除三个 worktree；branch 和 commit 继续保留。

## 第三阶段：移除可重建的保留目录

- 重新审计 recovery 与 final W4/W5 candidate：两者 tracked/untracked 为 0，ignored 只含 `__pycache__`／`docs/_site`，无外部进程引用；
- recovery 事实由保留分支 `codex/integrate-concurrent-work-20260820@117acac` 重建；final candidate 由 `codex/integrate-w4-w5-20260823@6266a44` 重建；
- 使用 `git worktree remove --force` 移除两个目录，继续保留 branch／commit；没有删除任何 recovery branch 或已通过 required checks 的 candidate ref。

## 最终状态

- 2 worktrees：primary 与 current W5C；
- W5C 正式登记为 `validating + waiting-for-user`，primary subsystem 为 `multi-worktree-collaboration`；
- Personal Observatory：1 current Workstream、0 current Direct、0 reconciliation、0 hygiene；
- startup 从 37+ worktree 环境约 2 分钟降低到 2 worktree 环境 30 秒以内；仍未实现缓存或增量采集；
- 没有删除 branch、remote ref、commit、源码正文、作者文档、凭据或原始 benchmark。

## Recovery boundary

- 被移除 worktree 的 tracked 内容可从保留 branch／commit 重建，包括 recovery 与 final candidate；
- 三个 stale session 的原始私有元数据可从上述 Git-private archive 只读恢复；
- `git worktree remove --force` 同时移除了各目录中的 ignored `__pycache__`／`docs/_site`，这些是可重建生成物，不在 Git 中恢复；
- 本操作不是 Orrery 自动 cleanup 的发布实现，不能据此宣称 W3 closure／eligibility gate 已自动批准这些目标。
