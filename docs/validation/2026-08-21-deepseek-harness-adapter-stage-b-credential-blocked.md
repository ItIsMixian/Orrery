# Validation：DeepSeek Harness Adapter Stage B 凭据阻塞

Date: 2026-08-21
Scope: 经用户明确授权后的真实 DeepSeek Harness headless Agent 生命周期、Skill catalog、显式注入、隐式候选目录和模型凭据失败边界；不含成功模型请求、CLI 路由、发布或 `verified` 提升
Result: PARTIAL PASS / BLOCKED — headless runtime 真实发现并显式注入 Adapter Skill，但本机没有 DeepSeek API Key，两个 turn 均在 provider 请求处失败
Source: branch `codex/claude-deepseek-adapters`，baseline `main@2989582d106e1bc36307a30427c8ba5f1dfb91c2`

## 权威链与官方依据

- [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
- [Approved Design](../design/platform-neutral-core-and-adapter-architecture.md)
- [Implementation Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)
- [Stage A](2026-08-21-deepseek-harness-adapter-stage-a.md)
- [DeepSeek Harness official repository](https://github.com/deepseek-ai/deepseek-harness)
- [CLI reference](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/reference/README.md)
- [Skill subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md)
- [Headless bundle](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/bundle/headless/README.md)

实现与判断继续绑定官方仓库提交 `141eb6fef83422698aef7a981029e843e8161534`。

## 精确环境

| 维度 | 值 |
|---|---|
| OS | Windows 11 Pro x64 `10.0.26200`，build 26200 |
| Node／pnpm | Node 22.17.0；pnpm 11.19.0 |
| DeepSeek Harness | `@deepseek-ai/dsh 0.1.0-rc.8` |
| entrypoint SHA-256 | `c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62` |
| Adapter | `project-orrery-deepseek-harness-adapter` 0.1.0 |
| Adapter TGZ SHA-256 | `6cab195ea26cc5fab0ebeeb5b6974718a6385df1c21023b46b5d16c0eb5b152b` |
| 声明的 Core／CLI | Core 0.1.0／CLI 0.1.1，均未发布；CLI 要求 `>=0.1.1,<0.2.0` |
| 本机 CLI distribution／entrypoint | 均缺失 |
| 凭据状态 | 继承环境无 `DEEPSEEK_API_KEY`；默认 `~/.dsh/.credentials.yaml`／`.env` 均不存在 |

凭据检查只验证变量名和文件是否存在，没有读取或输出任何 secret 值。

## 真实 headless Agent 证据

证据根为 `D:\orrery-stage-b-dsh-noauth-20260821-002`。`DSH_HOME`、`DSH_AGENTS_HOME`、pnpm store／home、
npm cache 和 telemetry 设置全部隔离在该 D 盘根内。真实 `dsh plugin --profile headless add` 安装最终 TGZ，
`--dump-config` 识别 `project-orrery-skill` 插件行。

第一轮输入以 `/project-orrery` 显式命名 Skill。压缩 session 共有 20 个事件；模型请求前已经持久化：

- `skill-catalog`，内容含 `project-orrery`；
- 独立 `skill-invocation`，内容含完整 `<skill_content>`；
- `request/header` 与 `request/context`。

随后 `assistant/chunk` 和 `turn/end` 记录
`MISSING_CREDENTIAL: llm-deepseek: no API key for provider route "deepseek-official"`，进程 exit 1。该证据证明
真实 Agent 生命周期中的目录发现和用户显式 Skill 注入，不证明模型已经处理 Skill 或调用 CLI。

第二轮只描述适用的 Orrery audit／validate 任务。19 个事件中仍有含 `project-orrery` 的
`skill-catalog`，没有 `skill-invocation`，随后同样 `MISSING_CREDENTIAL`／exit 1。这是正确的凭据前目录
状态；由于模型没有启动，不能把它表述为模型完成了隐式选择。

两个 session、profile、依赖和日志都位于隔离根。没有写 `C:\Users\1\.dsh`、
`C:\Users\1\.agents\skills` 或真实项目作者文件，也没有复制凭据。

## 门禁结论

仓库收尾回归为两个 Adapter 专项 6/6、默认全仓 74 项中 72 passed／2 expected skips；integrated
structure、隔离静态 docsite、256 份 Markdown／552 个本地链接和 `git diff --check` 全部通过。

本轮补齐了真实 headless catalog 和显式用户调用注入证据，也证明缺少 provider 凭据时明确失败；仍缺
成功模型请求、模型隐式选择、CLI 路由及模型观察到的 CLI 缺失／不兼容失败。用户需要在本机通过 DSH
官方 credentials service 或启动环境配置有效 `DEEPSEEK_API_KEY` 后才能继续；secret 不应粘贴进项目
或对话。

证据门不完整，`runtime_compatibility.verified` 保持空数组，支持状态保持
`experimental`／`unreleased`。
