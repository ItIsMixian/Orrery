# 当前进度

Updated: 2026-08-18

## 当前阶段

Project Orrery v0.2.0 已于 2026-08-18 完成首次公开发布。`main`、annotated tag、GitHub Release、zip、SHA-256 与远端 release manifest 均已核验；仓库自托管与 Pilot 001–004 证据也已进入 Git 历史。

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
- [x] 按发布计划形成产品修复、研究证据、自托管、发布准备提交，并补充浅克隆 CI 修复。
- [x] 分支与 `main` 双平台 CI 通过，首个 [`v0.2.0` GitHub Release](https://github.com/yw9299-stack/project-orrery/releases/tag/v0.2.0) 已创建并验证。
- [ ] 决定是否设计 H2，以及要削减的是 Prompt、Manifest、Selected Evidence 还是重复验证成本。
- [ ] 设计真正由 Harness 证明内容读取范围的最小代理实验。
- [ ] 修复 Windows／Linux 打包在行尾和 ZIP 权限元数据上的差异，恢复跨平台 byte-for-byte 可重复性。

## Blockers / risks

- 仓库外 benchmark 原始结果依赖本机保存，尚无长期保留／脱敏导出策略。
- Pilot 004 正式 validator 保留 exit 1，因为冻结的 v1 Oracle 存在假阳性；正确结论依赖 checksummed v2 只读复核。
- v0.2.0 的 GitHub 资产和 checksum 一致，但 Windows 与 Ubuntu 从同一 tag 本地打包得到的 zip 字节不同；已确认条目集合一致，差异来自行尾与权限元数据，列入下一补丁。

## 下一里程碑

回到上下文路由研究：先确定 H2 的成本削减假设与精确读取证明实验，再决定是否启动下一轮 Pilot。
