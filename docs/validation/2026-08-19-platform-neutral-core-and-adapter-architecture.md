# Validation：平台中立 Core 与 Adapter 架构采纳

Date: 2026-08-19
Scope: ADR-0004、Approved Design、Implementation Plan、权威索引和当前 State 的文档一致性

## 预期行为

1. 用户确认的单仓库分包、canonical `AGENTS.md`、独立组件版本和真实 runtime 证据门进入 Accepted ADR。
2. Approved Design 明确 Core、CLI、Observatory、Agent Adapter、Harness Adapter、平台安装器和兼容性职责。
3. Active Plan 给出 Phase 0–4、验收证据和回滚边界，并显式排除 Pilot 008、多人／多 worktree 和 docsite 凭据实现。
4. State、PROGRESS、DEVLOG、HANDOFF 和文档索引不得把 accepted 写成 implemented 或 verified。
5. 新增本地 Markdown 链接全部可解析，现有 Project Orrery 结构仍被识别为 integrated candidate。

## 检查与结果

| 检查 | 结果 |
|---|---|
| 定向检查 ADR／Design／Plan 及入口中的 `ADR-0004` 链接 | PASS |
| PowerShell 解析三份新增架构文档的本地 Markdown 链接 | PASS — 全部目标存在 |
| `rg -n "[ \t]+$"` 检查三份新增文档 | PASS — 无尾随空白命中 |
| `git diff --check` 检查本轮涉及的已跟踪文档 | PASS |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid；authority 为 integrated candidate |

## 边界与已知缺口

- 本验证只证明决策链、索引和当前状态表述一致，不证明 Core／CLI 已抽取、Codex Adapter 已迁移或第二平台兼容。
- 没有运行静态站构建或完整测试，因为并行工作正在修改 docsite、凭据安全和 Pilot 008 相关文件；这些改动不属于本验证。
- 三份新增架构文档在验证时仍是未跟踪工作树文件；尾随空白和链接由独立只读检查覆盖，提交状态不由本记录宣称。
- 没有产生真实 Agent／Harness runtime E2E 证据，因此当前不能新增任何 `verified` 平台条目。

## Result

PASS：ADR-0004 的权威文档链已建立并通过文档级验证。实现状态仍为未开始，后续只能从
Implementation Plan 的 Phase 0 基线工作进入。
