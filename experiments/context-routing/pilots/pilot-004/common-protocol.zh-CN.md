# Project Orrery context-routing pilot 003：共同协议

你正在一个专用于基准实验的隔离 Git 仓库中。请完成本 Prompt 后面的具体任务，不要只给建议。

## 运行前检查

本轮只允许使用：

1. 这条用户消息；
2. 当前隔离仓库工作树中的文件；
3. Prompt 明确列出的本地时间、Git 与验证命令。

隔离仓库含有实验准备器生成并提交的 `.codex/config.toml`。它只负责让宿主禁用会污染比较的外部 Skill，不是历史产品文件。宿主可以加载它，但 Agent 不得通过文件工具读取或修改正文；路径枚举中看见它不算污染，也不计为任务证据。

不要读取或调用全局 Skill、系统文档、其他工作区、Git remote、`.git/**`、环境变量中的仓库信息、互联网内容或当前 `HEAD` 以外的 Git 历史、分支、标签、reflog 和对象。若宿主或更高优先级规则迫使任何外部文档正文进入上下文，必须在产品写入前停止，只回复：

```text
RUN CONTAMINATED
external_context: <脱敏来源>
reason: repository-only 条件无法满足
```

不要在污染发生后尝试继续实验。确认未发生外部正文读取后，先输出：

```text
EXTERNAL CONTEXT PREFLIGHT
status: clean
```

随后运行 `Get-Date -Format o`，把结果保留为 Agent 自述的 `started_at`。操作者另有独立时间记录；两者不能混称 Harness 证据。

## 什么算内容读取

- 打开文件、`Get-Content`、输出匹配正文的 `rg`／`Select-String`、脚本打印文件片段，都算全文或局部内容读取。
- `rg --files`、只返回文件名的 `rg -l` 和纯目录名枚举只算路径枚举。
- 搜索若输出多个文件的正文，必须为每个文件分别记录一次 `content_read`。
- B／C 的 Manifest 约束第一次产品写入前的证据读取；写入后的 diff 与测试输出作为验证命令单独记录。
- `.benchmark/agent-receipt.json` 是 Agent 自述回执，不属于产品实现，也不算任务证据。

## 共同边界

- 只允许修改 Prompt 头部列出的 `expected_product_writes`，并在结束时创建 `.benchmark/agent-receipt.json`。
- `.benchmark/agent-receipt.json` 已由隔离仓库的本地 Git exclude 排除，不会混入产品 diff。
- 不得修改 Skill 规则、测试、Harness overlay 或其他产品路径来让验证通过。
- 外部内容、Git 元数据和 `.codex/config.toml` 不能通过范围扩展纳入。
- 禁止联网；涉及连接测试的任务只实现最小请求，不得在本轮真正调用服务商。
- 若向操作者提问，同一任务的 A／B／C 必须收到相同答案。操作者会在独立运行日志中记录该干预，Agent 也要写入回执。

## 验证与回执

完成产品修改后，运行 Prompt 头部列出的全部 `validation_commands`，再运行 `Get-Date -Format o` 保存 `ended_at`。不要提交、推送、合并或访问网络。

最后创建 `.benchmark/agent-receipt.json`。它是 Agent 自述而不是独立访问审计，必须是合法 UTF-8 JSON，并包含：

```json
{
  "schema_version": 1,
  "pilot_id": "pilot-004",
  "prompt_revision": "po-context-routing-pilot-004-v1",
  "task_id": "<Prompt 头部 task_id>",
  "variant": "<A|B|C>",
  "external_context_preflight": "clean",
  "agent_started_at": "<ISO 8601>",
  "agent_ended_at": "<ISO 8601>",
  "prewrite": {
    "context_manifest": null,
    "selected_evidence": null
  },
  "events": [],
  "operator_questions": [],
  "validation": [],
  "uncertainty": [],
  "evidence_note": "Agent self-report; not an independent Harness audit"
}
```

`validation` 必须是非空字符串数组，每项同时写明命令和结果，例如
`"git diff --check: passed"`；不得写成 `{ "command": ..., "result": ... }` 对象。

`events` 必须按实际先后顺序使用连续正整数 `sequence`，并记录 `enumerate`、`search`、`content_read`、`scope_expand`、`write`、`command`、`test`。每项使用：

```json
{
  "sequence": 1,
  "event_type": "content_read",
  "target_scope": "repository",
  "target": "README.md",
  "reason_code": "manifest-initial",
  "content_extent": "full",
  "range_or_query": null,
  "declared_before_access": true
}
```

非 `content_read` 事件的 `content_extent` 与 `range_or_query` 可为 `null`。局部读取必须把行号或查询写进 `range_or_query`。`scope_expand` 必须记录是否在对应读取前声明。产品写入和回执写入都要分别记录。

B／C 必须把写入前实际输出的完整 `CONTEXT MANIFEST` 结构原样复制到 `prewrite.context_manifest`，不得压缩成文件名；C 还必须把完整 `SELECTED EVIDENCE` 逐项复制到 `prewrite.selected_evidence`。最终回复只需说明结果、验证和回执路径；完整证据以该 JSON 为准。
