# 跨会话交接

Updated: 2026-08-18

## 当前情况

- 根文档系统已依据 ADR-0001 完成自托管集成；`.project-orrery.json` 应保持 `authority_status: integrated`。
- GitHub 尚无稳定 tag／Release；`origin/main` 中的 `release-manifest.json` 把 v0.2.0 描述为稳定版候选，但它尚未真正发布。
- 当前自托管、实验和 installer 缓存排除修复都只存在于未提交工作树。
- 上下文路由证据集中在 `experiments/context-routing/`；大型原始输出位于 `D:\coding warehouse\project-orrery-benchmark`。
- Pilot 004 的 H1 未达到 token 采纳门，不能加入发布版 Skill。

## 风险与常见陷阱

- 不要把 v1 Oracle 的正式 validator exit 1 解读为六个候选实现失败；详见 Pilot 004 结果报告和 v2 复核。
- 不要为了“同步文档”把 JSONL、隔离仓库或本机路径批量复制进 `docs/`。
- 在 `v0.2.0` tag 与 GitHub Release 都成功前，不要把候选能力写成已发布能力。
- 运行 `py_compile` 会在模板目录产生被忽略的 `__pycache__`；installer 必须继续排除它们。
- `experiments/` 目前整体未跟踪；在任何清理或切分提交前先审阅 `git status`。

## 安全接续点

1. 阅读 `docs/PROGRESS.md` 和 `docs/state/context-routing-research.md`。
2. 运行自托管结构验证和完整测试，确认 Validation 仍匹配。
3. 按 [v0.2.0 首次公开发布计划](implementation/plans/2026-08-18-v0.2.0-first-public-release.md)分层提交、跑分支 CI、快进 main、打 tag 并验证 Release。
4. 发布完成后用独立文档提交记录远端事实，不要让 tag 前的候选状态长期留在 State。
5. 只有用户确认继续实验后，才新建 H2 Design 和新的 Pilot；不要改写已封存 Pilot 004 Prompt 或原始结果。
