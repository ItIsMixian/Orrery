# Pilot 008：Scope Acquisition 准备包

Pilot 008 保留原真实开发 fixture 与 Oracle，但在任何模型样本启动前改为比较线性入口 `P` 与任务优先
路由入口 `S`。

- `P`：共同完整 Skill + fixture 当前线性 `AGENTS.md`。
- `S`：相同完整 Skill + `variants/S-AGENTS.md` 任务路由入口；该 overlay 在模型启动前独立提交。
- 共同装置：脱敏应用 fixture、无 reason-code 的被动读取代理、独立 Oracle、相同模型与预算。
- 主指标：app-server 逐响应累计 usage 在首次允许产品 `fileChange` 启动前的最后快照。

旧 Skill Entry Router R 和 `variants/R.zh-CN.md` 作为未运行的历史准备材料保留，不再进入 Pilot 008
控制哈希、Prompt 或成本门。

本目录当前只允许准备和 dry-run：

```powershell
python experiments/context-routing/pilots/pilot-008/run_pilot.py --dry-run
```

当前 `--dry-run` 只验证静态装置。Smoke 001 因复制的 CLI 缺少同版本 code-mode host 而没有产生
`fileChange`，已按 contaminated 封存；使用哈希一致同版本 runtime sibling 的 Smoke 002 已证明
0.148.0-alpha.15 的逐响应 usage 先于首次产品写入。Smoke 002 允许 0 次写前代理读取，只是 ordering
兼容性证据，不是 P/S 成本样本，也没有内容交付 proof。正式路径继续失败关闭，直到 app-server
transport、代理 proof、仓库外 R0 封存与汇总全部接入；三对正式样本仍需另行确认，并必须使用新的
仓库外 `--output-root`。
