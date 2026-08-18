# Context Manifest B 采纳实验实施计划

Status: apparatus prepared; model runs not started
Updated: 2026-08-18
Authority: implementation intent; does not change the released Skill

## 目标

用 Pilot 007 直接比较当前发布流程 `P` 与冻结的 Context Manifest `B`，决定 B 是否值得进入 Project Orrery 产品 ADR 讨论。实验不修改 `skills/project-orrery/`，不复用既有任务，也不把仓库外 R0 原始结果复制进 Git。

## 工作包

- [x] 将 B 冻结为 Manifest → reason-coded expansion → Access Summary，不生成 receipt 文件。
- [x] 固定当前流程 P 为对照，并让 P/B 共用相同代理、JSONL、Oracle、模型和预算。
- [x] 选择 PO-CR-027／028／029 三个新任务，覆盖 release、research security 和 public docs。
- [x] 在运行前冻结正确性、依赖召回、成本和最小收益门。
- [x] 为三项任务建立独立 Oracle、自测与 baseline negative control。
- [x] 完成控制包 dry-run 和仓库回归。
- [ ] 用 `gpt-5.6-terra` / medium 启动 3 对 P/B run；同任务成对并行，不隐藏重试。
- [ ] 封存 R0，生成 R1/R2，只读复核采纳门。
- [ ] 由维护者决定拒绝、继续补样本或接受；只有接受才新增 ADR。

准备证据见 [Pilot 007 准备验证](../../validation/2026-08-18-pilot-007-preparation.md)。

## 运行边界

- 基线必须保持 `f9cd508696280e41c933680f3b8c5090fe71cd9d`。
- 正式输出根使用新的仓库外目录，例如 `D:\coding warehouse\project-orrery-benchmark\pilot-007-<timestamp>`。
- 运行开始后不得修改 `pilot-007/`；装置修复进入 Pilot 008。
- 本计划的勾选只说明准备工作，不证明 B 已通过或已被采纳。

## 决策出口

- 未过任一硬门：记录不采纳，不创建采纳 ADR。
- 结果接近但样本不足：保持实验状态，设计新 holdout，不修改发布版 Skill。
- 全部通过：先生成 R2 评估并请求维护者明确接受；接受后才新增 ADR、Implementation Plan 和迁移说明。
