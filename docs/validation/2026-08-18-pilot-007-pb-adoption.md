# Pilot 007 P/B 采纳实验验证

Date: 2026-08-18
Result: run completed; adoption gate failed; shared apparatus defect recorded

## 已执行验证

| 检查 | 结果 |
|---|---|
| Pilot 007 frozen preflight / dry-run | PASS before execution |
| `gpt-5.6-terra` / medium P/B runs | 6/6 自然结束，均为 CLI exit 0；没有人为重试 |
| R0 `seal_raw_evidence.py verify` | 6/6 manifest valid，0 hash/size/unsealed-file failure |
| 完整 CLI JSONL / proxy 审计 | P 3/3 有效；B 2/3 有效；028-B 有 failed proxy command |
| Frozen task Oracle | 027 P/B fail；028 P/B pass；029 P/B fail |
| Frozen formal validation | 0/6；共同失败来自嵌套 Pilot 006 创建已存在的 `benchmark` 分支 |
| Frozen automated adoption gate | FAIL；correctness、apparatus、input、output、time、proxy-benefit 均未全部满足 |
| R2 semantic review | P 2/3、B 2/3；029 frozen Oracle 为固定词形假阴性，027 为真实跨平台顺序遗漏 |

## 仓库同步回归

在形成 R2、同步 State／Progress／Handoff／Devlog 与实验索引后，又执行了一轮只验证仓库一致性的回归：

| 检查 | 结果 |
|---|---|
| `python -m unittest tests.test_context_routing_h2 -v` | PASS，12/12 |
| `python -m unittest discover -s tests -v` | PASS，39 passed + 1 expected skip |
| `python experiments/context-routing/validate_benchmark.py --repo-root .` | PASS，24 个 corpus tasks、6 个 run records |
| `python -X utf8 scripts/docsite/build_docsite.py` | PASS，生成 `docs/_site/index.html` |
| `git diff --check` | PASS |

这组检查验证的是报告与项目文档同步后仓库仍然一致；它不改变冻结 Oracle、正式验证或自动采纳门的失败结果。

## 装置解释

正式验证失败不是六份实现共同破坏产品测试，而是测试套件中的 Pilot 006 dry-run 在外层实验分支名下产生冲突。该问题在运行前 dry-run 没有暴露，因为准备验证发生在 `codex/b-adoption-pilot`，正式候选则运行在名为 `benchmark` 的隔离分支。

`PO-CR-028-B` 的访问装置无效有两层原因：它先读取了不存在的新 exporter，形成真实 failed proxy command；协议检查器又把一个携带冗余 reason、但没有扩大已覆盖范围的读取误判为缺少 Scope Expansion。两者都保留在原始结果中，不做回写修正。

## 验证声明

- 本轮足以阻止 B 采纳：自动门失败，且修正后的任务质量没有优于 P。
- 由于共同装置缺陷，本轮不足以给出干净的 B 因果效应估计，也不应声称“B 已被科学证伪”。
- 不新增采纳 ADR，不修改 `skills/project-orrery/`。如继续，应建立 Pilot 008 并在启动前修正外层分支名、语义 Oracle 和 expansion/proxy 对齐。
