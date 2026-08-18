# Context Manifest B 采纳实验实施计划

Status: completed; Pilot 007 contaminated and B not adopted
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
- [x] 用 `gpt-5.6-terra` / medium 启动 3 对 P/B run；同任务成对并行，没有隐藏重试。
- [x] 封存 6 份 R0，以 pilot summary 作为 R1 聚合，并生成 R2 只读复核。
- [x] 按冻结门停止采纳：B 成本／收益门失败，且 Pilot 007 有共同装置缺陷；不新增 ADR。

准备证据见 [Pilot 007 准备验证](../../validation/2026-08-18-pilot-007-preparation.md)。
完成证据见 [Pilot 007 运行验证](../../validation/2026-08-18-pilot-007-pb-adoption.md)与 [R2 结果](../../../experiments/context-routing/results/2026-08-18-pilot-007-pb-adoption-terra-medium.md)。

## 运行边界

- 基线必须保持 `f9cd508696280e41c933680f3b8c5090fe71cd9d`。
- 正式输出根使用新的仓库外目录，例如 `D:\coding warehouse\project-orrery-benchmark\pilot-007-<timestamp>`。
- 运行开始后不得修改 `pilot-007/`；装置修复进入 Pilot 008。
- 本计划的勾选只说明准备工作，不证明 B 已通过或已被采纳。

## 完成结论

六份 R0 manifest 均有效，但共同 formal-validation 分支冲突使本轮不能作为完全干净的采纳实验。只读复核后 P/B 任务质量同为 2/3；B 聚合 input、output、时间均超过门槛，只减少 6.95% 代理正文，未达到 15% 最小收益。B 不采纳，发布 Skill 保持不变；任何后续修复进入 Pilot 008。

## 决策出口

- 未过任一硬门：记录不采纳，不创建采纳 ADR。
- 结果接近但样本不足：保持实验状态，设计新 holdout，不修改发布版 Skill。
- 全部通过：先生成 R2 评估并请求维护者明确接受；接受后才新增 ADR、Implementation Plan 和迁移说明。
