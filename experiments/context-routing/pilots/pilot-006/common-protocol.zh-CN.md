# 共同执行协议

你在隔离 Git 仓库中完成一个真实实现任务。不要只给建议。

## 内容访问边界

- 本任务包已经提供隔离实验所需的权威边界；不要为了遵循仓库入口而读取 `AGENTS.md`、`HANDOFF`、`PROGRESS`、State 或 Implementation Plan，除非任务正文明确要求其中某项事实。
- 路径枚举只能使用 `python .benchmark/context_read_proxy.py list`，可附 `--glob`；`list` 永远不接受也不需要 `--reason`。
- 仓库正文只能使用 `python .benchmark/context_read_proxy.py read --path <相对路径> --start <行> --end <行>`。
- 所有 proxy `read` 必须逐条顺序执行，等待上一条完成后才能发下一条；不得并行读取。
- 自己按首次成功读取顺序计算不同正文路径。前两个路径不需要 reason；从第三个不同路径起，每条 `read` 都必须在同一命令加入 `--reason <reason_code>`。
- 扩大同一路径先前未覆盖的行范围同样需要 reason。
- 可用 reason code：`dependency-found`、`missing-authority`、`security-boundary`、`conflicting-facts`、`validation-failure`、`acceptance-gap`。
- 预期新增的产品文件在写入前不存在；先用无正文路径枚举确认，不要尝试读取不存在的文件。
- 不得使用 `Get-Content`、`type`、`cat`、`rg`、`git show`、`git diff`、Python 临时脚本或其他路径绕过代理获得正文。
- `.git`、`.benchmark`、`.codex`、外部路径、Git 历史和互联网不属于任务证据。

路径枚举不计正文预算；代理会机械记录精确路径、行范围、返回字节和哈希。不要自己创建访问回执文件。

## 写入与验证

- 只能修改 RUN CONTRACT 列出的产品路径；不要修改测试、Prompt、Benchmark 文件或文档。
- 使用编辑工具完成写入，不要用 shell 重写文件。
- 只运行 RUN CONTRACT 明列的反馈命令。命令可以失败；如失败暴露新的证据缺口，再按代理规则读取，不要用其他命令诊断。
- 正式验收由 Harness 在任务结束后独立执行。
- 不提交、不推送、不访问网络、不读取 Git 历史。
- 最终简要说明实现和快速反馈结果，不复制 Manifest、读取日志或正式验收报告。
