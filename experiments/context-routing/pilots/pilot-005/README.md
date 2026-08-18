# Pilot 005：B/H2 配对实验

本轮用两个从未进入既有 Pilot 的 holdout 任务比较：

- `B`：保留模型撰写的 Context Manifest、扩张叙述和最终访问摘要；
- `H2`：相同受控读取代理、相同两文件初始预算，但 Manifest、读取回执和正式验收全部由 Harness 生成。

两种变体都只能通过 `.benchmark/context_read_proxy.py` 获取仓库正文。完整 `codex exec --json` 由独立 validator 事后检查；任何直接读取命令、未知 item、未批准写入或代理哈希不匹配都会污染该 run。

任务、Prompt、Oracle 和执行配置必须在模型运行前冻结。原始输出位于仓库外，不进入 Git。
