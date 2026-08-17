# 当前进度

Updated: 2026-08-18

## 当前阶段

Project Orrery 0.2.0 是当前发布候选。`origin/main` 已包含其兼容协议与发布清单，但 GitHub 尚无 `v0.2.0` tag 或 Release；仓库工作树已完成自身文档系统集成和 Pilot 001–004 的状态归档，这些增量也尚未提交。

## 已完成

- [x] 通过 ADR-0001 正式采纳 Project Orrery 自托管权威链。
- [x] 建立真实 Agent／维护者入口、State、Validation、Snapshot 与开发日志。
- [x] 明确 `docs`、`experiments`、发布 Skill 和仓库外 benchmark 的职责。
- [x] 完成 Pilot 003 全量、修复后的 B/C 确认轮和 Pilot 004 B/H holdout。
- [x] Pilot 004 v1 Oracle apparatus failure 已保留，v2 只读复核已记录。
- [x] 修复 installer 会复制模板 `__pycache__`／`.pyc` 的问题。
- [x] 完成本地集成验证：28 项默认测试（27 通过、1 项按设计跳过）、启用动态 reader 后完整 28/28 通过、24 项 benchmark 语料与 6 份 run record 通过、文档站与本地链接检查通过。

## 当前结论

- Context Aperture H1 正确性与 B 持平、读取更克制，但总 input token 高 47%，未通过采纳门。
- 发布版 Skill 仍不强制 Context Manifest、Selected Evidence 或访问回执。
- 下一轮若继续，应先提出 H2 的成本假设与更小实验；不能直接重跑 H1。

## 待办

- [x] 人工审阅本次自托管、实验与产品修复 diff，并确定分层提交及首次发布方案。
- [ ] 按发布计划形成产品修复、研究证据、自托管、发布准备四个提交。
- [ ] 分支 CI 通过后快进 `main`，创建并验证首个 `v0.2.0` GitHub Release。
- [ ] 决定是否设计 H2，以及要削减的是 Prompt、Manifest、Selected Evidence 还是重复验证成本。
- [ ] 设计真正由 Harness 证明内容读取范围的最小代理实验。
- [ ] 在下一版发布前决定自托管改动、compatibility gate 候选与 installer 修复的发布范围。

## Blockers / risks

- 当前大量 `docs/`、`experiments/` 和测试资产仍是 Git 未跟踪文件；未提交前没有稳定版本历史。
- GitHub 当前没有任何 tag 或 Release；README 中指向 `v0.2.0` 的安装链接要等本轮发布完成后才会有效。
- 仓库外 benchmark 原始结果依赖本机保存，尚无长期保留／脱敏导出策略。
- Pilot 004 正式 validator 保留 exit 1，因为冻结的 v1 Oracle 存在假阳性；正确结论依赖 checksummed v2 只读复核。

## 下一里程碑

完成 [v0.2.0 首次公开发布计划](implementation/plans/2026-08-18-v0.2.0-first-public-release.md)，再在新的 Design/Plan 中决定 H2 是否值得进入下一轮实验。
