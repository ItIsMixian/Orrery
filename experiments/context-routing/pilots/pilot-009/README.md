# Pilot 009：修正后的 Scope Acquisition 对照

Pilot 009 是 Pilot 008 首对正式运行停止后的新控制包。任务目标、完整冻结操作说明、P/S 入口 treatment、
Terra medium 配置和采纳门保持不变，只修正两类已证明的共同装置问题：

- 迁移 Oracle 按复合索引列顺序和可观察行为验收，不暗中要求任务未规定的索引名字或固定 State／Progress
  词形；
- Prompt 明确已安装 Skill 不属于允许输入，app-server 关闭 `skill_search`，完整事件 validator 继续拒绝
  任何仓库外读取。

三项任务改用 `PO-CR-033`–`035`，避免与 Pilot 008 R0 混淆。两组仍共享同一 9,109-byte 冻结说明，
每项 P/S Prompt 必须逐字节等长；唯一 treatment 是目标仓库 `AGENTS.md` 的线性 P 与任务优先 S。

确定性检查：

```powershell
python experiments/context-routing/pilots/pilot-009/operator/acceptance.py --self-test
python experiments/context-routing/pilots/pilot-009/run_pilot.py --dry-run
```

正式运行必须使用新的仓库外 `--output-root`。runner 按任务成对并行 P/S；任一侧装置无效时封存该对、
写入停止证据并且不再启动后续任务。Pilot 008 的 R0 证据保持只读，不会被本 Pilot 修补或重解释为
有效正式样本。
