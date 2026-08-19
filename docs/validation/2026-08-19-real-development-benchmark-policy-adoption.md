# 真实开发基准政策采纳验证

Date: 2026-08-19
Status: passed

## 验证目标

确认用户接受的真实开发任务组合已经进入正确的权威层，同时没有被误写成已实现的 Pilot、fixture 或发布 Skill 行为。

## 结构检查

- ADR-0002 记录长期决定、理由、后果和实施边界。
- Approved Design 定义任务比例、验收层级、隔离与隐私要求。
- Library 保存 Marglo 来源观察，不取得事实权威。
- Research State、Progress、Handoff 与 Devlog 只描述“政策已接受、实施未开始”。
- 发布 Skill 和既有冻结 Pilot 不应发生修改。

## 仓库回归

| 检查 | 结果 |
|---|---|
| `python -m unittest discover -s tests -v` | PASS，39 passed + 1 expected skip |
| `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS |
| `python experiments/context-routing/validate_benchmark.py --repo-root .` | PASS，24 个 corpus tasks、6 个 run records |
| `python -X utf8 scripts/docsite/build_docsite.py` | PASS，识别 2 个 ADR、5 个 State、28 份文档和 4 份 Library 资料 |
| 本地 Markdown 相对链接扫描 | PASS，12 个变更 Markdown 文件 |
| `git diff --check` | PASS |

验证证明 ADR、Design、Library 与当前状态入口已保持结构一致。它不证明 fixture、Oracle、Implementation Plan 或 Pilot 008 已经存在；这些仍是后续实施工作。
