# Validation：W3 Canonical 集成

Date: 2026-08-23
Scope: 在 W2 Canonical base 上吸收 W3 review／integration／closure／workspace inventory／cleanup eligibility，并同步全局入口；不包含 W4、真实 merge／delete、tag 或 Release
Status: Local PASS；first remote matrix preserved，Windows alias fix candidate pending；只有当包含本记录的 exact SHA 位于 `main` 时 W3 才是 Canonical

## 输入

- Base：`main@ef488715dee369cbce81806f3040b4c0417d3eb8`；
- W3 source：`codex/w3-review-integration-cleanup@1aa3f32`；实现提交 `e807f4c`；
- 集成方式：两个提交按原顺序吸收，无代码或文档冲突；
- W4、分级验证文档分支、用户级 Skill、历史目录和仓库外 benchmark 均未进入本次 diff。

## 边界

- W3 只生成 review／integration／cleanup 证据和资格报告，不更新 `main`、不 push、不删除 worktree／branch／ordinary directory；
- workspace inventory 只读取受限来源；Legacy unmanaged／Unknown、benchmark／recovery、路径逃逸、独有提交和未知本地文件失败关闭；
- remove worktree、local branch、remote branch、ordinary directory 是四个独立授权，本实现全部保持 `performed: false`；
- 公开 v0.2.0、Adapter runtime compatibility、Observatory 默认入口和 Team Mode 均不改变。

## 验证

- W3 Candidate focused：13/13 PASS；W1/W2 + W3 + 邻接迁移／恢复／Codex Adapter checkpoint：83/83 PASS；
- 本地 integration candidate `c758827` 动态全仓：291 项，288 PASS + 3 个既有 Windows symlink privilege skips，746.154s；
- integrated structure：PASS；Authority status `integrated candidate`，模型 1 可严格评估；
- 隔离 docsite：`D:\coding warehouse\project-orrery-validation-w3-integration\index.html`，1,471 KB，115 docs；
- Markdown：337 files／862 local links；1 个 D1 positive fixture 预期 missing，0 unexpected missing；
- high-confidence private-key／token、forbidden tracked artifact 与 `git diff --check`：PASS；
- 最终文档提交不改变 W3 代码；包含本记录的 exact SHA 仍须先在非 main 分支取得 Windows／Ubuntu required checks，才可推广远端 main。

## 首次远端矩阵与修正

- Candidate `af65438` 的 GitHub Actions [`32583193534`](https://github.com/yw9299-stack/project-orrery/actions/runs/32583193534)：Ubuntu PASS（1m12s），Windows FAIL（8m00s）；
- Windows 产品测试已运行到结尾，失败为两个 fixture 断言把 `C:\Users\runneradmin` 与等价 `C:\Users\RUNNER~1` 当成不同路径：closure 原路径字面比较，以及 inventory active-entry 查找；
- Core 已使用 `abspath → realpath → normcase` 作为 workspace identity，本次只让测试使用相同 identity 比较，没有放宽 path boundary、cleanup blocker 或清理授权；
- 两个原失败用例修正后本地 2/2 PASS（65.562s）；必须在新 exact SHA 上重新取得 Windows／Ubuntu 双 PASS，首次失败运行不得重分类为通过。
