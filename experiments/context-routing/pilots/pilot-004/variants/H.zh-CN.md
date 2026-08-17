# Variant H：风险驱动的 Context Aperture

可以先做只返回路径名的枚举。在任何仓库正文进入上下文前，先输出完整的 `CONTEXT MANIFEST` JSON：

```json
{
  "task_classification": "<类型与风险>",
  "retrieval_strategy": "single_file | bounded_multi_file | dependency_expansion",
  "initial_content_paths": [
    {"path": "<精确仓库相对路径>", "reason": "<读取理由>"}
  ],
  "expected_product_writes": ["<Prompt 允许路径>"],
  "expected_validation": ["<Prompt 验证命令>"],
  "expansion_conditions": ["<何时证据不足>"],
  "content_file_budget": 2
}
```

初始 Manifest 最多允许 2 个不同文件正文。预算是初始光圈，不是硬上限：如果安全边界、共享依赖或验收失败证明证据不足，必须先声明扩张，再读取必要正文。路径枚举本身不消耗正文预算。

第一次产品写入前，输出完整的 `SELECTED EVIDENCE` JSON 数组。高风险任务还必须在其中覆盖：输入或状态来源、产生副作用的 sink、失败顺序、公开状态，以及尚未闭合的风险／证据缺口。

```json
[
  {"path": "<仓库相对路径>", "scope": "<行号或查询范围>", "fact": "<直接支撑修改或安全顺序的事实>"}
]
```

读取第三个文件、Manifest 外文件或扩大已选片段前，必须先输出并在回执中记录：

```text
[SCOPE EXPANSION]
path: <仓库相对路径>
reason_code: dependency-found | missing-authority | security-boundary | conflicting-facts | validation-failure | acceptance-gap
reason: <为什么当前证据不足，以及读取此处将关闭什么缺口>
```

不得在访问后补报。验证失败如果暴露证据缺口，必须重新打开光圈并记录扩张；不能只反复修补当前文件。结束前使用 `python -m json.tool .benchmark/agent-receipt.json` 检查 JSON 可解析，并逐项确认：`pilot_id`、`prompt_revision`、`task_id`、`variant` 精确匹配；`target_scope` 只能是 `repository`、`query` 或 `command`；所有产品写入和回执写入都有事件；所有 Manifest 外正文读取都有更早的 `scope_expand` 事件。

