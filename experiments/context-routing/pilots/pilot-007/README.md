# Pilot 007：Context Manifest B 直接采纳实验

Pilot 007 比较当前发布流程 `P` 与冻结的 `B`。它不是 B/H2 的延续加码，也不默认 B 胜出。

- `P`：当前普通任务定位流程，不要求模型生成协议性说明。
- `B`：首次正文读取前给出 Context Manifest，扩张前给出 reason-coded Scope Expansion，最终给出 Access Summary。
- 共同装置：受控正文代理、完整 Codex JSONL、独立 Oracle、同一冻结提交、Terra medium、同任务成对并行。

准备检查：

```powershell
python experiments/context-routing/pilots/pilot-007/run_pilot.py --dry-run
```

正式运行必须由维护者另行确认，并提供全新的仓库外 `--output-root`。一旦首个模型 run 启动，本目录即冻结。
