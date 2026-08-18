# 上下文路由研究 State

Updated: 2026-08-18
Authority: research state; no routing candidate is accepted product policy

## 当前事实

- 研究语料包含 24 个由真实 Git 提交重建的任务；详细实现位于 `experiments/context-routing/`。
- Pilot 001 因任务包与外部上下文污染而不能支持架构结论。
- Pilot 002 为固定阅读链额外开销提供方向性信号，但缺乏完整执行配置与独立内容读取证据。
- Pilot 003 完成 9 次 A/B/C 运行；原封存轮存在回执协议无效，随后修复 Harness 并做更小 B/C 对照。
- B/C 确认轮中 C 的总 input token 约比 B 高 75%，且没有达到高风险任务采纳门。
- Pilot 004 完成 3 个 holdout 任务 × B/H。v2 只读 Oracle 判定 B/H 均为 3/3 通过；H 总 input token 比 B 高 47%、平均耗时约高 15%，因此 H1 不采纳。
- H2 候选已经成文：把完整 Manifest、Selected Evidence、Agent receipt 和重复正式验证移出模型输出，只保留代理参数中的短扩张理由。
- 读取代理与两种独立验证链已实现：当前兼容基线使用完整 `codex exec --json` 事后拒绝未批准工具并交叉核验输出哈希；Hook Pre/Post 仅为可选增强。
- Windows Codex CLI 0.147.0 的十轮 smoke 没有产出 Hook audit；全部原始运行按 contaminated 封存且 manifest 可验证。既有第九轮 JSONL 可被新 validator 只读证明 1/1 合法代理读取。
- 原始证据现在有 R0/R1/R2 分层、四类保留期、seal/verify/status 和禁止公开字段规则；工具不会自动删除到期运行。
- Pilot 005 用两个新高风险任务启动 B/H2，但共同 Harness 存在命令包装、绝对路径、Git 历史和 Oracle 契约问题；四份 run 只作为 apparatus failure 保留。
- Pilot 006 修正共同装置后，B 与 H2 的候选和独立任务 Oracle 均为 2/2 通过。冻结 validator 对 CRLF→CRCRLF 产生两个访问假阴性；v3 只读复核在不改原始分类的前提下证明四个 run 的代理读取均有效。
- Pilot 006 聚合成本：H2 相对 B 的总 input +18.5%、cached input +24.7%、non-cached input -31.9%、output +22.5%、代理正文 +23.7%、Agent 时间 +7.2%。H2 没有达到“总 input 不高于 B”的预设门。
- Pilot 007 已准备但尚未运行。它把此前漂移的 B 冻结为“首次正文读取前 Context Manifest、扩张前 reason-coded Scope Expansion、最终 Access Summary、无 receipt 文件”，并直接与当前发布流程 P 对照。
- Pilot 007 基线固定为已推送的 `f9cd508696280e41c933680f3b8c5090fe71cd9d`，模型固定为 `gpt-5.6-terra` / medium；PO-CR-027／028／029 的独立 Oracle、自测和 baseline negative control 已通过 dry-run。

## 当前产品影响

- 发布版 Skill 不强制 Context Manifest、Selected Evidence 或 Access Receipt。
- B 只是实验基线，不是发布策略。
- Pilot 007 的 B 是采纳候选而非已采纳策略；准备控制包、通过 dry-run 或未来通过自动门都不会自动修改发布 Skill，仍需 R2 复核和维护者明确接受后才能新增 ADR。
- H1、Context Aperture v0.1 和 H2 都没有成为发布策略；H2 对照已结束且不采纳。受控读取代理与 validator 继续作为研究 Harness，不是普通用户要求。

## 证据

- [研究综述](../library/2026-08-17-task-context-provenance-and-documentation-overhead.zh-CN.md)
- [Pilot 003 报告](../../experiments/context-routing/results/2026-08-18-pilot-003-terra-medium.md)
- [B/C 确认轮](../../experiments/context-routing/results/2026-08-18-pilot-003-bc-confirmatory-terra-medium.md)
- [Pilot 004 B/H holdout](../../experiments/context-routing/results/2026-08-18-pilot-004-bh-holdout-terra-medium.md)
- [H2 候选](../../experiments/context-routing/designs/context-aperture-v0.2-h2.zh-CN.md)
- [读取证明设计](../../experiments/context-routing/designs/harness-content-read-proof-v0.1.zh-CN.md)
- [原始证据保留策略](../../experiments/context-routing/designs/raw-evidence-retention-v0.1.zh-CN.md)
- [装置验证](../validation/2026-08-18-h2-read-proof-apparatus.md)
- [Pilot 005 / 006 结果](../../experiments/context-routing/results/2026-08-18-pilot-005-006-bh2-terra-medium.md)
- [Pilot 005 / 006 验证](../validation/2026-08-18-pilot-005-006-bh2.md)
- [B 采纳候选](../../experiments/context-routing/designs/context-manifest-b-adoption-v0.1.zh-CN.md)
- [Pilot 007 实施计划](../implementation/plans/2026-08-18-context-manifest-b-adoption-experiment.md)
- [Pilot 007 准备验证](../validation/2026-08-18-pilot-007-preparation.md)

## 已知边界

- Agent receipt 仍是自述；新代理+JSONL 可在受控命令面证明返回切片哈希与模型侧命令输出一致，但不证明模型注意或理解。
- Pilot 004 冻结 v1 Oracle 存在假阳性；原 exit 1 必须与 v2 复核一起解读。
- token 统计受 Codex 缓存上下文和工具输出影响，不能只用“读取文件数”解释。
- JSONL 是事后审计；Hook 未工作时不能宣称直接读取已被执行前阻断。
- Pilot 006 样本只有两个高风险任务；它足以判定当前 H2 未达到冻结质量门，不足以支持普遍模型结论。
- Pilot 007 只有三项新任务；即使全部通过，也只能支持当前 Project Orrery、当前模型和当前受控 CLI 工具面下的受限采纳讨论。
