# App-server Scope Ordering Smoke 002

Date: 2026-08-19
Result: usage/fileChange ordering verified; formal Pilot transport still disabled

## 授权与范围

- 维护者授权修正 Smoke 001 的运行时问题，只运行一个隔离 app-server turn；没有授权 Pilot 008 三对 P/S
  正式样本。
- 使用 `gpt-5.6-terra` / medium、`approvalPolicy: never`、`workspace-write` 和 ephemeral thread。
- 仓库外原始根为
  `D:\coding warehouse\project-orrery-benchmark\appserver-scope-smoke-002-20260819-132227`。

## 运行时前置检查

临时目录中的以下文件与当前 Codex 桌面包逐文件 SHA-256 一致：

- `codex.exe`
- `codex-code-mode-host.exe`
- `codex-command-runner.exe`
- `codex-windows-sandbox-setup.exe`
- `rg.exe`

实际版本为 `codex-cli 0.148.0-alpha.15`。Smoke runner 的 2-case 合成自测通过；Smoke 001 的
contaminated manifest 仍为 36/36 有效；运行前 Pilot 配置保持未验证。

## 事件顺序

| 事件索引 | 事件 | 观测 |
|---:|---|---|
| 58 | `item/started:commandExecution` | 启动 `Get-Content -LiteralPath instruction.txt` |
| 59 | `item/completed:commandExecution` | 输出与冻结指令正文一致 |
| 60 | `thread/tokenUsage/updated` | input 19,361；cached 9,984；non-cached 9,377；output 99 |
| 62 | `item/started:fileChange` | 首次写入，只更新 `marker.txt` |
| 63 | `item/completed:fileChange` | `BEFORE` → `AFTER` |
| 65 | `thread/tokenUsage/updated` | 写入后的第二个累计快照 |
| 80 | `thread/tokenUsage/updated` | 最终 input 58,481；cached 48,384；output 189 |
| 84 | `turn/completed` | status `completed`，无 turn error |

同 thread／turn 的三份累计 usage 单调。首次产品 `fileChange` 启动前存在一份完整 usage 快照，且命令读取
已经完成；仓库最终只有 `marker.txt` 修改，正文严格为 `AFTER`，`git diff --check` 通过。

## 独立分析与精确度

`analyze_scope_acquisition.py` 使用 ordering-only policy 重新读取原始 `server-events.jsonl`，得到：

- `measurement_valid: true`
- `precision: exact`
- Scope Lock event index 62
- pre-write input 19,361
- pre-write cached input 9,984
- pre-write non-cached input 9,377
- pre-write output 99
- final input 58,481

该 policy 明确设置 `minimum_prewrite_content_reads: 0`，因此结论只验证 app-server usage／fileChange 的事件
顺序，不宣称独立证明了读取代理正文。正式 Pilot 仍必须要求真实 proxy proof、允许路径、完整事件流和 R0
封存全部有效。

app-server 启动期间仍有用户环境中无关 MCP 的 HTTP 502 startup noise；没有 code-mode host 启动错误，
这些 MCP 没有进入任务调用链。正式 transport 应把非实验 MCP 从运行配置中隔离或将其启动异常明确分类，
不能让它们影响 P/S 对照。

## 封存

- 原始根按 `decision_supporting` 分类封存。
- `raw-evidence-manifest.json` 验证通过，39 个文件哈希有效，敏感度为 `restricted`。
- 到期日为 2027-08-19；工具不会自动删除。
- 原始事件、stderr、绝对路径和一次性仓库不会进入 Git。

## 产品与执行影响

- `pilot-config.json` 的 `scope_usage_ordering_verified` 可以更新为 `true`，并引用本 Validation 和原始 run id。
- 这只解除 ordering 不确定性，不代表 S 被采纳，也不代表 Pilot 008 已可正式运行。
- 当前 Pilot runner 继续在任何模型调用前失败关闭，直到 app-server 正式 transport、proxy proof、R0 封存和
  汇总路径完成确定性实现；三对 P/S 样本仍需维护者另行确认。

## 仓库回归

权威链同步完成后执行的检查：

| 检查 | 结果 |
|---|---|
| Scope analyzer self-test | PASS，4/4 |
| App-server ordering self-test | PASS，2/2 |
| `tests.test_context_routing_h2` | PASS，18/18 |
| Pilot 008 `--dry-run` | PASS；更新后的配置与装置进入控制哈希 |
| Pilot 008 formal guard | PASS；在任何模型调用前以 formal transport 未实现为由失败关闭 |
| Smoke 001／002 raw manifest verify | PASS，36/36 与 39/39 |
| 默认全仓测试 | PASS，59 项中 57 通过、2 项动态依赖按设计跳过 |
| benchmark | PASS，24 项 corpus、6 份 run record |
| integrated structure／docsite build | PASS |
| Markdown 本地链接 | PASS，205 份 Markdown 无缺失目标 |
| `git diff --check` | PASS；仅报告两个既有 requirements 文件的 LF→CRLF 工作树提示 |

回归未启动新的模型 turn，也没有创建正式 P/S 输出根。
