# App-server Scope Ordering Smoke 001

Date: 2026-08-19
Result: contaminated apparatus run; ordering remains unavailable; no formal Pilot sample

> 后续状态：修正运行时后，单独授权的 [Smoke 002](2026-08-19-app-server-scope-ordering-smoke-002.md)
> 已在当前 CLI 上验证 usage／首次写入顺序。下文保留 Smoke 001 当时的原始结论，不作回写。

## 授权与范围

- 维护者只授权一次隔离 app-server 兼容性 smoke，不授权 Pilot 008 三对 P/S 正式样本。
- smoke 使用 `gpt-5.6-terra` / medium，在仓库外一次性 Git 仓库中要求 Agent 先读取
  `instruction.txt`，再用 `apply_patch` 将 `marker.txt` 从 `BEFORE` 改为 `AFTER`。
- 原始根为
  `D:\coding warehouse\project-orrery-benchmark\appserver-scope-smoke-20260819-130447`，没有进入 Git。

## 运行环境

- PATH 中的 Microsoft Store app execution alias 从工作区终端启动时返回 Windows access denied；未调用模型。
- 将桌面应用包内 `codex.exe` 复制到独立临时目录后，可执行版本为
  `codex-cli 0.148.0-alpha.15`。该二进制生成的 experimental JSON schema包含
  `initialize`、`thread/start`、`turn/start`、`thread/tokenUsage/updated`、`item/started:fileChange`
  和 `turn/completed`。
- 初次 smoke runner 只复制了 `codex.exe`，没有同时复制同版本
  `codex-code-mode-host.exe`。这是本次装置缺陷。

## 原始观测

| 观测 | 结果 |
|---|---|
| app-server server messages | 89 |
| `thread/tokenUsage/updated` | 3；同 turn 累计值单调 |
| 最终整轮累计 usage | input 58,541；cached input 48,384；output 300；该值不是 Scope Lock 指标 |
| `commandExecution` completed | 0 |
| `item/started:fileChange` | 0 |
| `marker.txt` | 保持 `BEFORE` |
| turn | protocol status `completed`，但 Agent 明确报告工具启动失败 |

事件与 stderr 一致：app-server 报告 code-mode host executable 不存在；Agent 两次进入模型响应，但无法
启动所需读取工具，因而没有命令或文件写入。虽然 usage 通知真实存在，缺少首次 `fileChange` 边界意味着
`input-to-scope-lock` 仍必须报告 `unavailable`，不能用最终 58,541 input 代替。

## 封存与修正

- 原始根按 `contaminated` 分类封存；`raw-evidence-manifest.json` 验证通过，36 个文件哈希有效，敏感度为
  `restricted`，到期日为 2026-09-18，工具不会自动删除。
- 同版本 `codex-code-mode-host.exe`、`codex-command-runner.exe`、
  `codex-windows-sandbox-setup.exe` 和 `rg.exe` 已复制到临时运行目录，但没有自动发起第二个模型 turn。
- smoke runner 现在会在创建输出根和调用模型前验证这些 Windows runtime sibling；新增 2-case 合成
  self-test，证明“usage 在首次写入前”可接受、“usage 只在首次写入后”会拒绝。

## 确定性回归

| 检查 | 结果 |
|---|---|
| smoke ordering self-test | PASS，2/2 |
| 上下文 Harness 专项 | PASS，18/18 |
| Pilot 008 `--dry-run` | PASS；smoke runner 已进入控制哈希 |
| Pilot 008 formal guard | PASS；仍在任何模型调用前返回非零 |
| 默认全仓 | PASS，52 项中 50 passed + 2 expected skips |
| benchmark validator | PASS，24 项 corpus、6 份既有 run record |
| integrated structure + static build | PASS |
| Markdown 本地链接与图片 | PASS，202 份 Markdown |
| `git diff --check` | PASS；仅有两份并行工作中既存 `requirements.txt` 的 LF→CRLF 提示 |

## 结论与下一步

本次运行不支持也不否定 app-server usage／fileChange 顺序能力。Pilot 配置继续保持
`scope_usage_ordering_verified: false`，正式执行继续失败关闭。若维护者希望完成兼容性判断，需要再次明确
授权一个已修正运行时的第二次隔离 smoke；它仍不是正式 P/S 样本。
