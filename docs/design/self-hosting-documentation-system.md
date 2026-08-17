# Project Orrery 自托管文档系统

Status: Approved
Governing ADR: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md)

## 目标

让本仓库成为 Project Orrery 权威模型的真实使用者，同时保持产品源码、项目文档、研究实验和本地原始运行数据之间的清晰边界。

## 阅读入口

| 读者 | 首选入口 | 路径 |
|---|---|---|
| Agent | 当前约束和事实定位 | `AGENTS.md → HANDOFF/PROGRESS → relevant State → implementation` |
| 维护者 | 当前阶段和演化原因 | `docs/README.md → PROGRESS → ADR/State/DEVLOG` |
| 用户 | 安装、使用和公开能力 | `README.md` / `README.zh-CN.md` |
| 研究者 | 实验假设、装置和结果 | `docs/library/ → experiments/context-routing/` |

这些入口不拥有平行事实；冲突时以有效 ADR、真实实现、State 与 Validation 为准。

## 存储边界

| 层 | 内容 | 权威性 |
|---|---|---|
| `skills/project-orrery/` | 发布 Skill、模板、迁移和更新工具 | 产品实现 |
| `docs/` | 原则、决定、当前状态、验证和交接 | 项目文档权威 |
| `experiments/` | 候选设计、Prompt、Harness、Oracle、可发布报告 | 非权威研究证据 |
| `project-orrery-benchmark/` | 隔离仓库、JSONL、回执和本地缓存 | 本地原始证据，不自动发布 |
| `scripts/docsite/` | 本仓库安装的观测台工具 | 自托管工具实现 |

## 同步规则

1. 产品行为变化：修改实现、State、PROGRESS、DEVLOG 和 Validation。
2. 研究实验完成：修改实验报告、研究 State、PROGRESS、DEVLOG、HANDOFF；必要时更新 Library 综述。
3. 长期产品约束变化：新增 ADR，再更新 Approved Design 和 Plan。
4. 发布：区分工作树已实现、仓库已提交和 GitHub 已发布三个状态。
5. Snapshots 只提供日期截面，不替代活动 State。

## 观测台

根 `scripts/docsite/` 从发布模板安装，读取本仓库权威 Markdown。`docs/_site/` 是生成物，不手工编辑。AI 问答与趋势雷达是可选投影，没有决策权。
