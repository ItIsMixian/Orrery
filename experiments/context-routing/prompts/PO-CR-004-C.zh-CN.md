# PO-CR-004-C 新对话首条消息

你正在一个专门用于 Project Orrery 基准实验的隔离 Git 仓库中。请完成下面的任务，不要只给建议。

## 共同任务

改善这个仓库的公开 `README.md`，让第一次接触 Project Orrery 的用户能够从 GitHub 获得一条清晰、可复制的 Codex Skill 安装指令。保持现有文档风格和已有的安全采纳边界；不要修改 Skill、脚本、测试或其他产品行为。

完成后运行适合本次文档修改的验证。不要提交、推送或访问互联网，也不要查看当前 HEAD 以外的 Git 历史、分支、标签、reflog 或对象。

## C：选择性上下文

你可以先枚举路径，但在读取文件内容前，必须先输出一份简短的 `CONTEXT MANIFEST`，其中包含：

- 任务分类；
- 对当前任务采用“不检索／单文件／多文件”哪一级上下文策略；
- 初始允许读取内容的文件列表，以及每个文件的理由；
- 上下文预算：初始最多读取 2 个文件的内容，优先使用标题搜索和局部片段；
- 预期写入路径与验证；
- 什么条件会触发范围扩展。

不要默认全文读取。先用标题、关键词或局部范围定位，只把与任务直接相关的证据纳入一个简短的 `SELECTED EVIDENCE` 摘要，再实施修改。

如果确实需要突破文件数量或读取范围，必须先输出：

```text
[SCOPE EXPANSION]
path: <路径或范围>
reason_code: missing-rule | missing-context | validation-failure | dependency-found
reason: <为什么当前证据不足>
```

再进行读取。

## 最终回复格式

先说明结果和验证，然后附上：

```text
BENCHMARK REPORT
variant: C
context_manifest:
selected_evidence:
enumerated_paths_or_patterns:
search_queries:
content_reads: 逐项写路径、full/partial 和读取范围
writes:
commands:
scope_expansions:
validation:
uncertainty:
```

访问清单属于 Agent 自述，不要声称它是 Harness 独立审计结果。
