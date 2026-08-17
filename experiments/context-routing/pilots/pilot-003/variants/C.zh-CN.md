# Variant C：选择性上下文与内容预算

可以先做只返回路径名的枚举。在任何仓库正文进入上下文前，先输出完整的 `CONTEXT MANIFEST` JSON：

```json
{
  "task_classification": "<类型与风险>",
  "retrieval_strategy": "none | single_file | multi_file",
  "initial_content_paths": [
    {"path": "<精确仓库相对路径>", "reason": "<读取理由>"}
  ],
  "expected_product_writes": ["<Prompt 允许路径>"],
  "expected_validation": ["<Prompt 验证命令>"],
  "expansion_conditions": ["<何时证据不足>"],
  "content_file_budget": 2
}
```

初始 Manifest 最多允许 2 个不同文件正文。优先使用标题定位、只返回文件名的搜索和有行号的局部读取。任何输出正文的搜索都消耗对应文件预算。

第一次产品写入前，再输出完整的 `SELECTED EVIDENCE` JSON 数组：

```json
[
  {"path": "<仓库相对路径>", "scope": "<行号或查询范围>", "fact": "<直接支撑修改的事实>"}
]
```

读取第三个文件、Manifest 外文件或扩大已选片段前，必须先输出与记录理由化 `[SCOPE EXPANSION]`。读取后补报属于协议违例。结束时把完整 Manifest 与 Selected Evidence 原样复制到 Agent 回执。

