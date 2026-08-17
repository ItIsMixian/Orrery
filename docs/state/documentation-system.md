# 文档系统 State

Updated: 2026-08-18
Governing ADR: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md)

## 当前事实

- Project Orrery 已在本仓库正式采纳自身权威链。
- Agent 入口是根 `AGENTS.md`；维护者入口是本目录 `README.md`、`PROGRESS.md` 与本地观测台。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation 和 Snapshot 已各有独立职责。
- 根观测台由模板 v0.2.0 安装；其输出 `docs/_site/index.html` 为可重建生成物。
- AI 问答、路线综合和趋势雷达保持可选，且没有事实权威。

## 同步状态

- Pilot 001–004 已在 Research State、DEVLOG、PROGRESS 和实验报告之间建立链接。
- 详细原始运行不复制进 Docs。
- 公开用户文档仍由 `README.md` 与 `README.zh-CN.md` 承担。

## 实现证据

- `AGENTS.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/design/self-hosting-documentation-system.md`
- `scripts/docsite/build_docsite.py`

## 已知缺口

- 当前观测台界面主要为中文，完整国际化仍未实施。
- 尚未建立自动检查 State 与实现链接是否过期的机制。
