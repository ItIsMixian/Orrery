# 实施计划：Pilot 009 修正后的 Scope Acquisition 对照

Status: Completed — six valid runs; cost gate passed; quality gate failed; S not adopted
Date: 2026-08-19
Governing ADRs: [ADR-0002](../../decisions/0002-real-development-benchmark-portfolio.md),
[ADR-0005](../../decisions/0005-prewrite-scope-acquisition-input.md)
Approved Design: [真实开发上下文路由基准](../../design/real-development-context-routing-benchmark.md)
Predecessor evidence: [Pilot 008 formal apparatus stop](../../validation/2026-08-19-pilot-008-formal-apparatus-stop.md)

## 目标

保持 Pilot 008 的真实任务目标、完整冻结说明、P/S 入口 treatment、Terra medium 配置和采纳门，
只修正首对正式样本已证明的共同装置问题，然后在新的仓库外证据根完成三对正式运行。

## 工作包

- [x] 分配新 Pilot 和任务 ID `PO-CR-033`–`035`，保留 Pilot 008 封存证据。
- [x] 让迁移 Oracle 按任务规定的索引列顺序、数据保留、幂等和未来版本拒绝验收，不要求隐藏名字。
- [x] 让 State／PROGRESS Oracle 按可观察语义验收，不要求任务未规定的固定词形。
- [x] 在共同 Prompt 中禁止用户目录已安装 Skill 输入，并关闭 app-server `skill_search`；全事件审计仍
  失败关闭地拒绝仓库外读取。
- [x] 通过 Oracle 自测、synthetic formal pipeline、P/S Prompt 等长和控制哈希 dry-run。
- [x] 通过仓库专项、完整、benchmark、结构、链接与 diff preflight。
- [x] 使用新外部输出根运行三对 P/S；六个 run 的装置和 Scope 全部有效并封存。
- [x] 验证全部 R0 manifest，生成 R2 结果并同步 State、PROGRESS、DEVLOG、HANDOFF。

## 完成出口

六个 run 的装置、Scope、formal validation 和 R0 全部有效；冻结成本门通过。冻结 Oracle 0/3 的自然
语言词形假阴性经只读复核后为 P/S 各 2/3，仍低于 3/3 质量门，因此 S 不采纳，发布 Skill 与模板不变。
下一轮先落实任务／Oracle v0.2 的分层 verdict、paraphrase 与 mutation controls，不自动补跑模型。
