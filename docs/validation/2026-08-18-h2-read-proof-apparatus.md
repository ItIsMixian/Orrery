# 2026-08-18 H2 读取证明与原始证据装置验证

Status: apparatus prototype validated; formal B/H2 follow-up completed separately
Scope: Context Aperture H2 design, controlled read proxy, independent CLI-event audit, optional Hooks, raw-evidence sealing

## 结论

- H2 已形成可测试候选，但没有进入发布 Skill，也没有形成采纳 ADR。
- 当前可用的独立读取证据是 `codex-exec-jsonl-posthoc`：Harness 保存完整 `codex exec --json` 事件流，拒绝任何未批准命令／未知工具，并把命令输出中的代理请求标记与代理日志 SHA-256 交叉核验。
- `PreToolUse`／`PostToolUse` 保留为更强的实时阻断增强层；在 Windows、Codex CLI 0.147.0、`codex exec --ephemeral --json` 下，项目 Hook、显式 trusted 项目 Hook、绝对 Windows 命令和 CLI 内联 Hook 均未产生 Hook 事件，因此不能作为当前 Pilot 的必需依赖。
- 代理和 JSONL 能证明“某个切片出现在捕获的模型侧命令输出中”，不能证明模型注意、理解或使用了它。

## 验证环境

- Windows 11 Professional x64
- Codex CLI 0.147.0
- 模型：`gpt-5.6-terra`
- reasoning effort：`medium`
- 原始根：仓库外 `D:\coding warehouse\project-orrery-benchmark`
- 分支：`codex/context-aperture-h2`

## 执行与结果

### 无模型专项测试

```powershell
python -m unittest tests.test_context_routing_h2 -v
Get-ChildItem experiments/context-routing/harness -Filter *.py |
  ForEach-Object { python -m py_compile $_.FullName }
```

初始结果：7/7 通过，全部 Harness Python 文件编译通过。Pilot 005／006 后专项套件扩展为 11/11，新增 Windows CLI 包装／绝对写路径归一化、CRLF stdout 恢复与篡改拒绝，以及两版冻结控制包 dry-run。覆盖：

- 路径穿越与受限元数据拒绝；
- 初始两文件预算与 reason-coded 扩张；
- 精确范围、源哈希、返回哈希和 CRLF→LF 规范化；
- Hook allow/deny 与 PostToolUse 响应交叉验证；
- JSONL 合法代理读取通过，直接 `Get-Content` 和未知 MCP item 失败；
- 原始证据 seal/verify/status 与篡改检测。

### 全仓回归

```powershell
python -m unittest discover -s tests -v
$env:ORRERY_TEST_BUILD='1'; python -m unittest discover -s tests -v
python experiments/context-routing/validate_benchmark.py --repo-root .
python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build
python -X utf8 scripts/docsite/build_docsite.py
git diff --check
```

结果：默认 35 项中 34 通过、图形化 reader 动态测试按设计跳过；启用 `ORRERY_TEST_BUILD=1` 后 35/35 通过；24 项 corpus 与 6 份既有 run record 有效；integrated scaffold + static build 通过；文档站生成成功；Markdown 本地链接与 `git diff --check` 通过。

### 真实 CLI 兼容性探测

共保留 10 个一次性 smoke run，全部按 `contaminated` 分类封存，不隐藏重试、不覆盖失败。前四轮暴露参数／权限配置错误；第五至第九轮 Agent 均返回正确 sentinel，但没有 Hook audit；第十轮加载用户沙箱后，仓库外审计状态写入被 Windows sandbox 拒绝。

全部 10 份 `raw-evidence-manifest.json` 重新执行 `verify` 均为有效。运行 `h2-hook-smoke-20260818-114907` 的既有 JSONL 与代理日志经新 validator 只读复核：

```text
apparatus_valid: true
evidence_mode: codex-exec-jsonl-posthoc
content_reads_proved: 1 / 1
completed_command_count: 1
unapproved_commands: []
unexpected_item_types: []
invalid_output_proofs: []
```

该只读复核不会改写原 run 的 `contaminated` 分类；它只证明新 validator 可以从既有原始证据得出可复核结论。下一次正式 Pilot 必须从运行前声明该 evidence mode。

## 官方行为依据

- Codex 官方说明 `--json` 会捕获完整事件流，包含 command execution、file change、MCP call、web search、plan update 与 usage：<https://learn.chatgpt.com/docs/non-interactive-mode>
- 官方 Hooks 说明 Pre/Post 覆盖本地工具，但专用路径可能绕开默认 Hook，且 Hook 是 guardrail 而非完整边界：<https://learn.chatgpt.com/docs/hooks>
- 未信任项目会跳过项目 `.codex/` 的 config、hooks 和 rules：<https://learn.chatgpt.com/docs/config-file/config-reference>

## 后续状态

- 两个新任务和 B/H2 成对比较已经完成，见 [Pilot 005 / 006 验证](2026-08-18-pilot-005-006-bh2.md)。
- H2 正确性与 B 持平，但总 input token 高 18.5%，所以成本门明确失败，候选不采纳。
- JSONL 模式只做事后作废，无法像可用的 PreToolUse Hook 一样在读取发生前阻断。
- Hosted tools 和 CLI 未记录的专用路径不得进入本轮实验工具面。
