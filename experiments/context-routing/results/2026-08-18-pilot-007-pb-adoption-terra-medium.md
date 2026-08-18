# Pilot 007：P/B 直接采纳实验

Date: 2026-08-18
Model: `gpt-5.6-terra` / medium
Baseline: `f9cd508696280e41c933680f3b8c5090fe71cd9d`
Status: contaminated as a clean adoption experiment; B not adopted

## 结论

Pilot 007 不能支持采纳 B，也不能作为一轮完全干净的因果对照。六次 CLI 均最终 exit 0，六份 R0 manifest 全部有效，但存在两个运行前没有捕获的装置问题：

1. 六个候选仓库都运行了旧 Pilot 006 dry-run 测试；外层隔离分支已经叫 `benchmark`，嵌套 runner 再创建同名分支，导致正式测试统一失败。
2. `PO-CR-028-B` 先读取了尚不存在的预期新增文件，产生 failed proxy command；其后又给一个已覆盖行范围携带了冗余 `--reason`，而协议检查器把任意带 reason 的读取都误当成真实 expansion，形成额外协议假阴性。

因此 raw 的 P 0/3、B 0/3 不能直接当作候选实现质量。只读语义复核得到 P 2/3、B 2/3：两边在 028 均通过独立安全 Oracle；两边的 029 文档都解释了 PowerShell execution policy，只是 frozen Oracle 过度要求英文必须出现精确词形 `ExecutionPolicy`；两边的 027 则都没有按 POSIX 归档路径排序，Windows `Path` 排序出现 `README.md → DEVLOG.md`、`product-philosophy.md → PROGRESS.md`、`validate_installation.py → SKILL.md` 逆序，不能证明 Windows／Linux archive 顺序一致。

即使采用修正后的 2/3 对 2/3 质量判断，B 也没有任务收益，并同时越过 input、output、时间和最小正文节省门。因此保守决策是不采纳 B、不创建 ADR、不修改发布 Skill。若未来提出新候选，应进入 Pilot 008，不得改写或补跑本轮。

## 原始汇总

| Variant | Apparatus valid | Raw candidate pass | Input | Cached input | Non-cached input | Output | Proxy bytes | Agent seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P | 3/3 | 0/3 | 1,552,467 | 1,439,744 | 112,723 | 12,219 | 103,797 | 1,027.356 |
| B | 2/3 | 0/3 | 1,951,117 | 1,801,216 | 149,901 | 15,098 | 96,586 | 1,200.917 |

相对 P，B 的总 input 为 `+25.68%`，output `+23.56%`，Agent 时间 `+16.89%`，代理正文 `-6.95%`。冻结门分别要求 input 不高于 `+10%`、output 不高于 `+15%`、时间不高于 `+15%`，并至少节省 `15%` 代理正文或补回 P 漏掉的必要依赖；四项均未满足。

## 按任务复核

| Task | P | B | 只读判断 |
|---|---|---|---|
| PO-CR-027 | Oracle fail | Oracle fail | 两边真实遗漏跨平台大小写排序差异；维持 fail |
| PO-CR-028 | Oracle pass；formal 受共同缺陷影响 | Oracle pass；formal 受共同缺陷影响；访问装置无效 | 实现质量两边 pass，但 B run 不能计入干净对照 |
| PO-CR-029 | Frozen Oracle fail | Frozen Oracle fail | 两边语义满足 execution-policy 说明；固定词形检查是假阴性，修正为 pass |

六个 run 都产生 4 条相同的 CLI reconnect 事件并最终 exit 0。网络恢复是共同运行条件，不形成单边污染，但会限制绝对墙钟解释。

## 证据与不可改写边界

仓库外原始根：`D:\coding warehouse\project-orrery-benchmark\pilot-007-20260818-143450`

- `frozen-control.json`: `6f93ac0a1d6792bffe80d5159aeb0762d8981adb97b2684b17373b2db17249d7`
- `pilot-summary.json`: `d804a49b08a2c7eca10f4a74c119a8b8c885b5ec887207ad70b4ac1771dfede9`
- `pilot-summary.md`: `e5f04b4d0dfe5c56cd6057ae303783141b72966536469ada49fcce3cd822fc89`

R0 manifest SHA-256：

- `PO-CR-027-B`: `28c564365004157363047ef123713fa03f39da1a9ff9752e4f186c6cbf3f0fae`
- `PO-CR-027-P`: `86c3aa0c0a23336bb87c0a5730b3f31b790cfbee6c96ba04daf3f620210aefdc`
- `PO-CR-028-B`: `690269bf7cef7aae2129e54051e01b70b4510fdc4474f2e58148ffde047f2665`
- `PO-CR-028-P`: `21a8ad3ae7b80febafedeff391b65646d1977363b976c55465d8bfb3e4911e33`
- `PO-CR-029-B`: `8b7bdb82aeea28053291ecbd22a8dbcd9206704b99a847fb1a4f86a3f2e66e21`
- `PO-CR-029-P`: `f557ae93931f4fab3327764fb03943baef9b47642eb386fe296c1c5d8288c330`

R0 不回写、不重分类、不进入 Git。本文是 R2 结论；任何装置修复或新运行必须使用新的 Pilot 编号和输出根。
