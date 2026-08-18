# 共同执行协议

你在隔离 Git 仓库中完成真实实现任务，不要只给建议。

## 内容访问边界

- 本任务包已经提供实验所需边界；不要读取 `AGENTS.md`、HANDOFF、PROGRESS、State 或 Implementation Plan，除非任务正文明确要求。
- 只用 `python .benchmark/context_read_proxy.py list` 枚举路径。
- 只用 `python .benchmark/context_read_proxy.py read --path <相对路径> --start <行> --end <行>` 获取仓库正文；读取必须逐条顺序执行。
- 前两个不同正文路径不需要 reason；从第三个不同路径起，以及扩大既有行范围时，在同一命令添加 `--reason <reason_code>`。
- reason code：`dependency-found`、`missing-authority`、`security-boundary`、`conflicting-facts`、`validation-failure`、`acceptance-gap`。
- 不得用 `Get-Content`、`type`、`cat`、`rg`、`git show`、`git diff`、临时脚本、MCP 或 Hosted tool 绕过代理读取正文。
- `.git`、`.benchmark`、`.codex`、外部路径、Git 历史和互联网都不是任务证据。

## 写入与验证

- 只能修改 RUN CONTRACT 列出的产品路径；不要修改 Prompt、Benchmark 或 Oracle。
- 使用编辑工具写入，不要用 shell 重写文件。
- 只运行 RUN CONTRACT 明列的快速反馈命令；正式验收由 Harness 独立执行。
- 不提交、不推送、不访问网络、不读取 Git 历史。
- 最终简要说明实现与快速反馈；不要创建访问回执、Manifest 文件或新的证明文档。
