# Pilot 007 B 采纳实验准备验证

Date: 2026-08-18
Scope: control packet only; no model runs and no adoption decision
Baseline under test: `f9cd508696280e41c933680f3b8c5090fe71cd9d`

## 结果

| 检查 | 结果 |
|---|---|
| `python experiments/context-routing/pilots/pilot-007/operator/acceptance.py --self-test` | PASS |
| `python experiments/context-routing/pilots/pilot-007/run_pilot.py --dry-run` | PASS；三项 baseline negative control 均按预期返回任务失败，Prompt 和控制哈希生成成功 |
| `python -m unittest tests.test_context_routing_h2 -v` | PASS；12/12 |
| `python -m unittest discover -s tests -v` | PASS；39/40，图形化动态 reader 按设计跳过 1 项 |
| `$env:ORRERY_TEST_BUILD='1'; python -m unittest discover -s tests -v` | PASS；40/40 |
| `python experiments/context-routing/validate_benchmark.py --repo-root .` | PASS；24 项 corpus、6 份既有 run record |
| `python -X utf8 scripts/docsite/build_docsite.py` | PASS；280 KB，23 篇索引文档、4 个 Plan |
| 本地 Markdown 链接扫描 | PASS |
| `git diff --check` | PASS |

## 验证含义

- Pilot 007 能从冻结 baseline 建立隔离副本，并证明三个新任务在未实现状态下不会被 Oracle 误判为通过。
- P/B Prompt、写入白名单、快速反馈命令、模型配置和采纳门均能由 runner 生成和哈希冻结。
- 本次验证不证明任一模型实现正确，也不证明 B 优于 P。只有正式六个 run、独立 R2 评估和维护者明确接受才能支持采纳 ADR。
