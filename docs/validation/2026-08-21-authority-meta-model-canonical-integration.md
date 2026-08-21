# Authority Meta Model M1 本地 Canonical 集成

Date: 2026-08-21

Scope: 审阅并把 `codex/authority-meta-model-fixtures` 的 20 个 M1 提交以 fast-forward 方式集成到本地 `main`，随后同步全局 State／PROGRESS／HANDOFF／DEVLOG。该记录只证明本地 Git 集成和回归，不证明 push、发布或 production consumer switch。

## 集成前置条件

- Candidate 与本地 `main@2989582` 的 merge base 精确等于 `2989582`，Candidate 位于 main 之上且无反向提交。
- Candidate worktree 与主 worktree 均 clean；主 worktree 保持 integration-only。
- 审阅范围为 20 个提交、74 个路径、8646 additions／138 deletions。
- 安全复核确认迁移／恢复写入仅限项目根 `.project-orrery.json`、项目内生成备份和同目录原子替换；receipt 绑定 source／target／proposal 或 current／backup，外部路径、穿越和 symlink 逃逸失败关闭。
- 新增实现没有扩大 Provider 网络或凭据读取面；v0.2.0 release manifest、README、tag 和发布资产没有改写。

## Procedure and result

| Check | Result |
| --- | --- |
| `git merge --ff-only codex/authority-meta-model-fixtures` | PASS；本地 main 从 `2989582` 前进到 `e0f8ba7`，无 merge conflict 或内容重写。 |
| `python -X utf8 -m unittest discover -s tests -q` | PASS；196 项中 194 通过、2 项动态依赖按设计跳过。 |
| Authority 定向 12-module suite | PASS；120/120。 |
| `validate_installation.py --target . --require-integrated` | PASS；authority status 为 integrated candidate，模型 1 supported／eligible。 |
| `scripts/docsite/build_docsite.py` 写入临时输出 | PASS；1107 KB，11 ADR、6 State、7 subsystems、2 snapshots、81 classified docs、12 plans、6 library。 |
| PowerShell Markdown local-link scan | PASS；270 份 Markdown、590 个本地链接／图片、0 missing target。 |
| 根／发布模板投影审阅 | PASS；Authority 修改保持同步，`build_docsite.py`／`serve.py` 只有预期项目标题占位符差异。 |
| `git diff --check` | PASS。 |

## Accepted conclusion

- M1 fixture、experimental Core evaluator、模型兼容、显式 migrate／restore、CLI／Observatory shadow、AI non-escalation 与非权威诊断投影现在属于本地 Canonical Git baseline。
- `implemented` 仍不等于 `released` 或 `production-switched`：稳定 Core API、完整 CLI claims、正式 Observatory Authority projection、下一 release／installer 模型声明和发布验证仍未完成。
- 本轮没有 push、tag、GitHub Release、模型调用、Provider 请求或用户级 Skill 修改。
