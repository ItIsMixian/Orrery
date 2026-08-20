# Pilot 008 formal apparatus stop

Date: 2026-08-19
Status: sealed apparatus finding; no adoption comparison

## Scope

Pilot 008 首次正式运行使用 Codex app-server 完成 `PO-CR-031` 的 P/S 配对。runner 在任一侧装置无效
时必须封存该对并停止后续任务；不得修补已使用的 Pilot 包或把污染样本计入采纳比较。

External evidence root:
`D:\coding warehouse\project-orrery-benchmark\pilot-008-scope-20260819-141008`

Runtime: `codex-cli 0.148.0-alpha.15`, GPT-5.6 Terra, medium reasoning.

## Result

- P 的 Scope measurement 本身为 exact：首次允许写入前累计 input `208,787`，其中 cached
  `158,976`、non-cached `49,811`；代理证明 7 个路径、4,394 unique slice bytes。
- S 的 Scope measurement 为 exact：写前 input `140,510`，其中 cached `77,824`、non-cached
  `62,686`；代理证明 5 个路径、3,192 unique slice bytes。
- P 完整事件审计发现直接读取仓库外
  `C:\Users\1\.codex\skills\project-orrery\SKILL.md`，因此 classified `contaminated`；S 的访问装置有效。
- 两侧都修改了四个允许路径，正式仓库测试通过。两侧实现都满足旧行保留、重复初始化、未来版本拒绝和
  `(status, snoozed_until)` 列顺序，但冻结 Oracle 暗中要求固定索引名
  `idx_feedback_status_snoozed`、固定 State 词形和任务 ID 词形，造成共同 false negative。
- runner 正确写入 `apparatus-stop.json`，未启动 `PO-CR-030` 或 `PO-CR-032`。

方向性 S/P 写前 input 比约 `0.673`，unique slice bytes 比约 `0.726`，但 P 已污染，因此这些数值只能
用于诊断，不能支持 treatment 决策或采纳。

## Evidence checks

```powershell
python experiments/context-routing/harness/seal_raw_evidence.py verify --manifest `
  D:\coding warehouse\project-orrery-benchmark\pilot-008-scope-20260819-141008\PO-CR-031-P\raw-evidence-manifest.json
python experiments/context-routing/harness/seal_raw_evidence.py verify --manifest `
  D:\coding warehouse\project-orrery-benchmark\pilot-008-scope-20260819-141008\PO-CR-031-S\raw-evidence-manifest.json
```

Both manifests remain valid: P `85/85` files, S `88/88` files.

## Disposition

Pilot 008 不产生 R2 采纳结论。任务目标和 treatment 保持不变，装置修正进入 Pilot 009：Oracle 改为
行为和语义验收，共同 Prompt 明确禁止已安装 Skill 输入，并关闭 app-server skill search。Pilot 008
原始证据保持 R0 只读。
