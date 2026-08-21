# Validation：Claude Code Adapter Stage B 认证阻塞

Date: 2026-08-21
Scope: 经用户明确授权后的真实 Claude Code runtime 初始化、Plugin／Skill 目录发现，以及显式／隐式候选 turn 的认证边界；不含成功模型请求、CLI 路由、发布或 `verified` 提升
Result: PARTIAL PASS / BLOCKED — runtime 真实发现 Adapter，但本机没有 Claude Code 可用登录态，两个候选 turn 均在模型请求前失败
Source: branch `codex/claude-deepseek-adapters`，baseline `main@2989582d106e1bc36307a30427c8ba5f1dfb91c2`

## 权威链与官方依据

- [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
- [Approved Design](../design/platform-neutral-core-and-adapter-architecture.md)
- [Implementation Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)
- [Stage A](2026-08-21-claude-code-adapter-stage-a.md)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code Skills](https://code.claude.com/docs/en/slash-commands)

官方资料允许 Claude Pro／Max／Team／Enterprise、Claude Console 预付 credits 或受支持云提供方认证。
免费 Claude 聊天账号本身不构成本次机器上的可用 Claude Code runtime 认证。

## 精确环境

| 维度 | 值 |
|---|---|
| OS | Windows 11 Pro x64 `10.0.26200`，build 26200 |
| Claude Code | `2.1.87` |
| binary | `C:\Users\1\.local\bin\claude.exe` |
| binary SHA-256 | `c722ff8836e7a90b5c62fd5cb6549887dc314e7e8d9551c01df1718d9198ecdf` |
| Adapter | `project-orrery-claude-code` 0.1.0 |
| 声明的 Core／CLI | Core 0.1.0／CLI 0.1.1，均未发布；CLI 要求 `>=0.1.1,<0.2.0` |
| 本机 CLI distribution／entrypoint | 均缺失 |
| 认证状态 | `claude auth status` exit 1；`loggedIn=false`、`authMethod=none`、`apiProvider=firstParty` |

认证检查只投影上述非敏感字段，没有输出邮箱、token、组织 ID 或凭据内容。

## 真实 runtime 证据

显式候选根为 `D:\orrery-stage-b-claude-noauth-20260821-003`，隐式候选根为
`D:\orrery-stage-b-claude-noauth-20260821-004`。两次均把 `CLAUDE_CONFIG_DIR` 指向全新隔离根，移除
Anthropic Key／token 环境变量，以 `--plugin-dir` 直接加载工作树 Adapter，并使用 `plan` 权限与最多一个
turn；未写 `C:\Users\1\.claude` 或用户 Skill／Plugin 目录。

两次 `system/init` 都给出相同发现事实：

- `claude_code_version=2.1.87`，目标模型目录值为 `claude-sonnet-4-6`；
- `plugins` 含唯一 inline `project-orrery` Plugin；
- `skills` 与 `slash_commands` 均含 `project-orrery:project-orrery`；
- `apiKeySource=none`。

显式输入使用 `/project-orrery:project-orrery ...`，隐式输入只描述 Orrery audit／validate 任务。两者随后
都返回 `authentication_failed`／`Not logged in · Please run /login`，进程 exit 1；`duration_api_ms=0`、
输入／输出 token 均为 0、`total_cost_usd=0`。因此真实 Plugin／Skill 目录发现已经成立，但请求没有到达
模型，不能证明显式 Skill 内容注入、模型自动选择、CLI preflight 或 CLI 路由。

## 门禁结论

仓库收尾回归为两个 Adapter 专项 6/6、默认全仓 74 项中 72 passed／2 expected skips；integrated
structure、隔离静态 docsite、256 份 Markdown／552 个本地链接和 `git diff --check` 全部通过。

本轮没有模型调用，也没有修改真实用户配置。要继续，用户必须先在 Claude Code 中建立官方支持的认证
方式；若使用 Claude Console，还必须有可用预付 credits。完成认证后仍需重跑最少显式／隐式 turn、
兼容 CLI 路由及 CLI 缺失／不兼容的模型侧失败关闭。

证据门不完整，`runtime_compatibility.verified` 保持空数组，支持状态保持
`experimental`／`unreleased`。
