# Variant B：Context Manifest 与理由化扩展

可以先做只返回路径名的枚举。在任何仓库正文进入上下文前，先输出完整的 `CONTEXT MANIFEST` JSON：

```json
{
  "task_classification": "<类型与风险>",
  "retrieval_strategy": null,
  "initial_content_paths": [
    {"path": "<精确仓库相对路径>", "reason": "<读取理由>"}
  ],
  "expected_product_writes": ["<Prompt 允许路径>"],
  "expected_validation": ["<Prompt 验证命令>"],
  "expansion_conditions": ["<何时证据不足>"],
  "content_file_budget": null
}
```

随后只读取 Manifest 列出的正文。若正文搜索或直接读取会让列表外文件内容进入上下文，必须先输出并记录：

```text
[SCOPE EXPANSION]
path: <仓库相对路径>
reason_code: missing-rule | missing-context | validation-failure | dependency-found
reason: <为什么当前证据不足>
```

外部路径和 Git 元数据不能扩展纳入。结束时把写入前输出的完整 Manifest 原样复制到 Agent 回执，不得只写文件名或摘要；`prewrite.selected_evidence` 可以为 `null`。

