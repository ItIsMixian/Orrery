# Harness 内容读取证明 v0.1

> 状态：最小实验设计，不是通用安全沙箱
> 目标：证明在隔离 benchmark 的受控本地工具面内，某个仓库内容切片确实作为工具响应返回给模型

## 可证明链

当前兼容基线的一次有效读取产生三份互相引用的证据：

1. 读取代理：在输出前记录规范化路径、行范围、源文件 SHA-256、返回正文 SHA-256 和字节数；
2. `codex exec --json`：保留命令执行、模型可见的 `aggregated_output`、文件变化、MCP/Hosted tool item 和最终 usage；
3. 独立 validator：拒绝不属于代理或 post-write 白名单的命令、未知 item、未完成命令和未批准写入，再从 `aggregated_output` 提取代理请求标记。raw、LF 规范形式或旧 Windows TextIO 的可逆 CRCRLF 恢复形式都必须命中代理日志独立记录的同一个 SHA-256；正文篡改不能通过“忽略换行”被宽松接受。

Validator 只有在代理规范化哈希与 JSONL 命令输出哈希一致、请求 ID 唯一且完整事件流没有未批准工具时，才生成 `observed_by: tool_wrapper` 的 `content_read`。这是事后作废机制，不是实时阻断。

若当前 Codex 环境实际产生 Hook 日志，可额外启用增强链：`PreToolUse` 在执行前阻断直接读取，`PostToolUse` 对 `tool_response` 做第二份交叉证明。没有日志时不得声称 Hook 模式生效。

## 为什么使用 Hooks

当前官方 Codex 文档说明：

- `PreToolUse` 可观察并阻断 shell、`apply_patch`、MCP 和多数本地 function tool；
- `PostToolUse` 的输入含正常送给模型的 `tool_response`；
- `codex exec --json` 输出包含 command execution、file change、MCP call 与 token usage 的 JSONL 事件。

来源：

- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/non-interactive-mode

同一文档也明确提醒，某些专用工具路径可以绕过默认 Hook 路径，因此 Hooks 应视为 guardrail，而非完整 enforcement boundary。实验报告必须保留这个限定。

## 隔离条件

- 使用 `codex exec --ephemeral --json --ignore-user-config`；
- 不启用 web search；不注册非实验 MCP；
- 代理脚本和策略由 Harness 复制并校验；Hooks 仅在真实烟雾测试证明已执行时启用；
- Agent 的产品工作区不能写入仓库外原始审计目录；
- JSONL validator 只接受代理枚举/读取、显式 post-write 白名单验证命令与预期写入；Hook 可用时使用同一策略实时阻断；
- 任何未知工具、直接正文命令或外部上下文使 apparatus 失败，不回退成“相信 Agent 回执”。

## 事件字段

每次代理读取至少记录：

```json
{
  "request_id": "uuid",
  "operation": "read",
  "path": "repository/relative/path.py",
  "start_line": 10,
  "end_line": 40,
  "reason_code": "dependency-found",
  "source_sha256": "...",
  "returned_sha256": "...",
  "returned_bytes": 1234,
  "observed_by": "tool_wrapper"
}
```

原始正文不复制进审计日志；正文仍存在 Codex 原始 JSONL/tool response 中，并按受限原始证据策略保存。

## 威胁与边界

- **能证明：** 代理从哪个提交工作树读取了什么范围、返回了多少 UTF-8 字节，以及该内容块出现在完整 CLI JSONL 记录的命令输出中；Hook 可用时还可证明它出现在 `PostToolUse.tool_response`。
- **不能证明：** 模型是否注意、理解或后来依赖了这些字节。
- **不能覆盖：** Hosted tools、未走默认 Hook 的专用工具、宿主在会话开始前注入的固定系统/开发者上下文。
- **不是权限隔离：** Hook、Agent 与本地 Harness 当前可能仍属同一 OS 用户；强对抗场景需要独立进程身份或容器边界。
- **避免循环论证：** Agent 自写 receipt 仅可作为诊断，不参与 `content_read` 强证据判定。

## 最小实验顺序

1. 无模型单元测试：路径穿越、范围、哈希、Hook allow/deny、响应交叉核验；
2. 临时仓库 micro-task：只读取带 sentinel 的文件并回答，不修改产品；当前 JSONL 兼容链已经由只读复核证明可工作，Hook 仍属可选增强；
3. 写入 micro-task：读取一个文件、通过 `apply_patch` 修改允许路径、执行白名单验证；
4. 新 B/H2 成对任务：只有前三步稳定后才运行。
