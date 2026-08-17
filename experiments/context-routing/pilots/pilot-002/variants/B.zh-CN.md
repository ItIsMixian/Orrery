# Variant B：Context Manifest 与理由化扩展

可以先做只返回路径名的枚举。在任何仓库正文进入上下文前，先输出一份简短的 `CONTEXT MANIFEST`：

- 任务分类；
- 初始允许读取内容的精确文件列表，以及每个文件的理由；
- 预期写入路径；
- 预期验证；
- 触发范围扩展的条件。

随后只读取 Manifest 列出的文件内容。若搜索命令会打印列表外文件的正文，也必须先扩展。每次扩展都要在读取前输出：

```text
[SCOPE EXPANSION]
path: <仓库相对路径>
reason_code: missing-rule | missing-context | validation-failure | dependency-found
reason: <为什么当前证据不足>
```

外部路径和 Git 元数据不能通过扩展纳入。不要因为目录或文件存在就默认读取。

