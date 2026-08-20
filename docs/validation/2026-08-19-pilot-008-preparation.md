# Pilot 008 Skill Entry Router 准备验证

Date: 2026-08-19
Result: apparatus ready; no model runs; no adoption conclusion

> Historical preparation record. No model sample used this P/R packet. ADR-0005 later reframed Pilot 008 as
> a P/S Scope Acquisition experiment; see [the reframe validation](2026-08-19-pilot-008-scope-acquisition-reframe.md).

## 冻结候选与确定性成本

| 项目 | P | R | R/P |
|---|---:|---:|---:|
| Skill 正文字节 | 9,109 | 2,386 | 26.19% |
| PO-CR-030 Prompt 字节 | 11,983 | 5,353 | 44.67% |
| PO-CR-031 Prompt 字节 | 11,980 | 5,350 | 44.66% |
| PO-CR-032 Prompt 字节 | 11,941 | 5,311 | 44.48% |

这些是冻结文件与 Prompt 组成的确定性字节数，不是模型 token、质量或墙钟结论。P 已从活动发布源复制到
`pilot-008/controls/P-SKILL.md`，其链接的两份 reference 也一并冻结并进入控制哈希；并行写入一度使活动
文件换行字节与哈希漂移，Pilot 现在只校验冻结快照，不再依赖活动发布源。

## 装置验证

| 检查 | 结果 |
|---|---|
| Oracle self-test | PASS；3/3 baseline negative，3/3 positive control |
| 真实开发组成 | PASS；2 项代码／迁移，1 项事实链治理 |
| 隐私边界 | PASS；人工代码与数据，不复制真实工作树、数据库、凭据、缓存或未提交改动 |
| 嵌套 preflight | PASS；外层 `pilot-008-outer`，内层 `pilot-008-fixture`，无 `benchmark` 同名分支 |
| Pilot 008 `--dry-run` | PASS；Prompt、Skill、fixture、Oracle、Harness 和任务均进入控制哈希 |
| `python -m unittest tests.test_context_routing_h2 -v` | PASS，13/13 |
| 默认全仓 | PASS，稳定复跑 44 项中 42 passed + 2 expected skips |
| 并行写入竞态复核 | 首次复跑在发布模板被并行更新时瞬时失败；目标单测随即通过，文件稳定后的完整 44 项复跑通过 |
| 动态全仓 | 较早检查点为 41/42；Pilot 008 与动态设置通过，未完成的 docsite Broker 测试返回两个 HTTP 400；新增并行测试后未重跑动态模式 |
| benchmark validator | PASS，24 项历史 corpus、6 份既有 run record |
| integrated structure + static build | PASS |
| Markdown 本地链接 | PASS，169 份 Markdown；P 冻结 references 可解析 |
| `git diff --check` | PASS；另有并行 docsite requirements 的 LF→CRLF 警告，无 diff error |

## 边界声明

- 未运行 `gpt-5.6-terra` 或任何正式样本，没有仓库外 Pilot 008 输出根、R0 manifest 或 token 数据。
- R 仍是 `experiments/` 下的候选，不改变 `skills/project-orrery/`、v0.2.0 或当前产品政策。
- 较早的动态 Broker 失败属于并行的 docsite 凭据／Broker 工作树，不应伪装成 Pilot 008 失败；新增并行测试后
  没有重跑动态模式，因此当前只声明默认全仓通过，不声明动态全仓通过。
- 该历史 P/R 正式运行条件从未触发；当前执行入口和授权条件以 ADR-0005 及新的 P/S
  [Scope Acquisition 重构验证](2026-08-19-pilot-008-scope-acquisition-reframe.md)为准。
