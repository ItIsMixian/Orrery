# Validation：W3 Canonical 集成

Date: 2026-08-23
Scope: 在 W2 Canonical base 上吸收 W3 review／integration／closure／workspace inventory／cleanup eligibility，并同步全局入口；不包含 W4、真实 merge／delete、tag 或 Release
Status: Candidate validation in progress；只有当包含本记录的 exact SHA 位于 `main` 时 W3 才是 Canonical

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

最终 exact-SHA 的 W3 focused、动态全仓、integrated structure、隔离 docsite、Markdown link、安全／forbidden artifact、diff 与 Windows／Ubuntu Candidate-first 结果在本次集成完成后记录或由 GitHub exact-SHA checks 承载。
