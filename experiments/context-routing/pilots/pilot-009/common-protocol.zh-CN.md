# 共同执行协议

你在一次性隔离 Git 仓库中完成真实实现任务，不要只给建议。Prompt 已完整提供共同冻结操作说明；
随后按目标仓库 `AGENTS.md` 自然定位本地事实。不得发现、加载或读取用户目录中的任何已安装 Skill，
即使名称相同；冻结正文是本次唯一允许的 Skill 输入。

## 内容访问边界

- 只用 `python .benchmark/context_read_proxy.py list` 枚举路径。
- 只用 `python .benchmark/context_read_proxy.py read --path <相对路径> --start <行> --end <行>`
  获取仓库正文；读取必须逐条顺序执行。
- Harness 被动记录路径、切片和读取顺序；不要求你为扩大读取范围提供 reason code。
- 不得用 shell、Git 历史、临时脚本、MCP、Hosted tool 或互联网绕过代理读取正文。
- `.git`、`.benchmark`、外部路径和实验 operator 文件不是任务证据。

## 写入与验证

- 只能修改 RUN CONTRACT 列出的产品路径；保留所有预置无关文件。
- 使用编辑工具写入，不要用 shell 重写文件。
- 只在首次产品编辑之后逐条运行 RUN CONTRACT 明列的快速反馈；正式验收由 Harness 独立执行。
- 不提交、不推送、不访问网络。
- 最终只简要说明实现和快速反馈；不要输出或创建仅为实验服务的 Manifest、Receipt、访问总结或
  其他上下文协议。
