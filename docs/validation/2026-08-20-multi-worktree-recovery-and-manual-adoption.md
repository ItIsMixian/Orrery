# 2026-08-20 多 worktree 恢复与人工采纳验证

Status: Passed for manual adoption

Governing ADR: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

## 验证范围

本记录验证一次真实的共享工作目录恢复与人工集成过程，目标是证明：在多个 Agent 已经把未提交改动交错写入同一个 `main` 工作目录后，维护者仍能先保全原貌，再在独立 integration worktree 中审阅、拆分、合并和验证，而不覆盖原始恢复证据。

本记录不验证尚未实现的 worktree session、自动 untracked path 采集、Direct／Authority／Semantic／Unknown 重叠分类、观测台 scope banner 或 `orrery integrate` 命令。

## 恢复边界

- 原共享目录：`D:\coding warehouse\project-orrery`
- 恢复基线：`main@96eee5a3fea8d2bdd802c8ae28df721194833114`
- 恢复分支：`codex/recovery-shared-main-20260820`
- 不可变恢复提交：`a87c5a4361734953f6e490389377968eb2d52cbb`
- 恢复规模：198 个路径，15,726 insertions，1,050 deletions
- 恢复审阅：没有生成站点、缓存、凭据或其他禁止路径；没有 ≥2 MiB 的变更文件；秘密扫描没有发现真实凭据。

恢复分支没有被 reset、改写或删除。27 个文件原有的重复 EOF 空行也保留在该提交中，作为共享工作树原貌的一部分。

## 独立集成过程

- Integration worktree：`D:\coding warehouse\project-orrery-integration-20260820`
- Integration branch：`codex/integrate-concurrent-work-20260820`
- 研究／Harness：`a9bbdc6 research(context): preserve scope acquisition pilots`
- 平台 Core／Adapter 与 Broker docsite：`1cad1ac feat(platform): integrate core adapters and broker gateway`
- 外部工作记忆研究：`2aa1ee4 docs(research): record sivtr work-memory observations`
- 并行权威状态对齐：`4a17b77 docs(state): reconcile concurrent project facts`
- 协作协议合入：`c3cc477 merge: bring in multi-worktree collaboration protocol`
- 正式决策分配：临时 `PO-DEC-WT-001` 在最新集成历史上转为 ADR-0007。

集成初期曾只在 integration worktree 删除 27 个文件的重复 EOF 空行，没有回写恢复提交。首次默认回归因此正确失败：Pilot 008／009 的冻结 `fixture-source/AGENTS.md` 哈希从预期 `8d948831...` 变为 `3e30cfc5...`。维护者没有更新冻结哈希，而是从不可变恢复提交逐字节恢复全部 27 个文件；两个冻结输入随后恢复为预期 SHA-256，定向 dry-run 与完整回归通过。这次失败证明冻结实验输入必须优先于通用格式清理。协议分支、恢复分支和产品／研究拆分提交均保留独立历史。

## 结构结论

- 一项任务一个分支／worktree 的人工模型可用；共享对象库没有导致未提交工作目录或索引互相泄漏。
- `PROGRESS`、`HANDOFF`、`DEVLOG` 和跨子系统 State 的交错修改由唯一整合者集中对齐。
- `accepted` 仍不等于 `implemented`：ADR-0007 和 Approved Design 已进入权威链，但 Plan 的自动化阶段尚未完成。
- 跨机器未 push 工作仍不可观察；当前只能记录为 Unknown，不能声称不存在冲突。

## 回归验证

环境：Windows，Python 3，PowerShell；integration worktree 为 `D:\coding warehouse\project-orrery-integration-20260820`。

| 命令／检查 | 结果 |
|---|---|
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 61 项中 59 通过，2 项动态依赖按设计跳过 |
| `$env:ORRERY_TEST_BUILD='1'; python -X utf8 -m unittest discover -s tests -v` | PASS — 61/61 |
| Pilot 008／009 两项定向 apparatus dry-run | PASS — 恢复冻结输入后 2/2 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid，authority 为 integrated candidate |
| `python -X utf8 scripts/docsite/build_docsite.py --out %TEMP%\project-orrery-integration-20260820.html` | PASS — 691 KB；7 ADR、5 State、6 subsystem、2 Snapshot、53 docs、11 Plan、5 Library |
| PowerShell 本地 Markdown link scan | PASS — 235 个 Markdown 文件、420 个本地链接、0 个缺失目标 |
| `git diff --check` | 在最终文档提交后 PASS |

默认回归第一次运行的两项失败被保留在本记录中，不计作最终通过前的无效噪声：它直接发现了格式清理对冻结输入的破坏，并触发逐字节恢复，而不是修改测试或哈希来迎合当前工作树。

## 已知缺口

- 没有自动阻止 Agent 在主 worktree 实现任务。
- 没有私有 `$GIT_DIR/orrery/worktree.json` session。
- 没有机器可执行的 tracked／untracked／expected-write 重叠报告。
- 没有推测性 integration CLI 或观测台事实作用域投影。
- 本轮只更新本地 Git 历史；未经单独授权不推送 `origin/main` 或发布版本。
