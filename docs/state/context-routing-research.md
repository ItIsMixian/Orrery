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

## 当前产品影响

- 发布版 Skill 不强制 Context Manifest、Selected Evidence 或 Access Receipt。
- B 只是实验基线，不是发布策略。
- H1 和 Context Aperture v0.1 保持候选／研究状态；下一步只能是新 H2 设计或新的测量方法。

## 证据

- [研究综述](../library/2026-08-17-task-context-provenance-and-documentation-overhead.zh-CN.md)
- [Pilot 003 报告](../../experiments/context-routing/results/2026-08-18-pilot-003-terra-medium.md)
- [B/C 确认轮](../../experiments/context-routing/results/2026-08-18-pilot-003-bc-confirmatory-terra-medium.md)
- [Pilot 004 B/H holdout](../../experiments/context-routing/results/2026-08-18-pilot-004-bh-holdout-terra-medium.md)

## 已知边界

- Agent receipt 仍是自述；Codex JSONL 证明工具事件，但不证明模型看到的精确文件字节。
- Pilot 004 冻结 v1 Oracle 存在假阳性；原 exit 1 必须与 v2 复核一起解读。
- token 统计受 Codex 缓存上下文和工具输出影响，不能只用“读取文件数”解释。
