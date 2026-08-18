# PO-CR-029：Windows Codex CLI 安装说明

改进公开中英文 README 的 Codex CLI 安装说明，面向 PowerShell 因 ExecutionPolicy 拒绝 `npm.ps1`、又希望减少 C 盘占用的 Windows 用户。

要求：

- 中英文分别成段，不混写。
- 给出可复制的 `npm.cmd` 安装方式，并展示把 npm prefix 和 cache 放在 `D:\Tools\Codex` 的示例。
- 不建议把系统 ExecutionPolicy 改成 `Unrestricted`、全局 `Bypass` 或关闭安全策略。
- 说明 Codex CLI 与桌面端可以并存；安装完成后用 `codex.cmd --version` 验证。
- 保留既有 Skill 安装和安全采纳边界。
