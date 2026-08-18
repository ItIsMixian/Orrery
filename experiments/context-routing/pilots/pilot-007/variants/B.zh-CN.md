# Variant B：冻结的 Context Manifest 协议

第一次读取仓库正文前，先输出：

```text
CONTEXT MANIFEST
task_class: <分类>
initial_reads:
- <路径> — <为什么需要>
expected_writes:
- <路径>
validation:
- <命令>
expansion_conditions:
- <什么证据缺口允许继续读>
```

之后只能先读 Manifest 的 `initial_reads`。读取新路径或扩大已读范围前，先输出：

```text
SCOPE EXPANSION
path: <路径>
reason_code: <共同协议允许的 reason code>
reason: <一句具体理由>
```

任务结束时在正常实现说明之后追加：

```text
ACCESS SUMMARY
content_reads: <实际读取路径及范围的简表>
scope_expansions: <扩张简表或 none>
```

这些文字是计划与解释，不替代 Harness 证据。不要创建 receipt、Manifest 或 Summary 文件。
