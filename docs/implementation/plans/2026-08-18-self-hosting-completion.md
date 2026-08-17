# 实施计划：Project Orrery 自托管补全

Status: Completed
Date: 2026-08-18
Governing ADR: [ADR-0001](../../decisions/0001-project-orrery-self-hosting.md)
Approved Design: [自托管文档系统](../../design/self-hosting-documentation-system.md)

## 实施映射

- [x] 预演并非破坏式安装 scaffold；保留现有 Library 和 `.gitignore`。
- [x] 修复 installer 复制 `__pycache__`／`.pyc` 的模板污染问题并补测试。
- [x] 建立真实 `AGENTS.md`、Seed、ADR、Approved Design、State、PROGRESS、DEVLOG 与 HANDOFF。
- [x] 保持详细基准证据在 `experiments/`，把 Pilot 001–004 提炼进研究 State。
- [x] 建立可复现的自托管 Validation 与日期 Snapshot。
- [x] 生成并检查本地文档站。

## 实现目标

- `AGENTS.md`, `.project-orrery.json`, `docs/**`
- `scripts/docsite/**`, `start-docsite.bat`
- `skills/project-orrery/scripts/install_project_orrery.py`
- `tests/test_project_orrery.py`

## 验证

结果由 [2026-08-18 自托管基线验证](../../validation/2026-08-18-self-hosting-baseline.md) 接管；本清单本身不构成完成证据。
