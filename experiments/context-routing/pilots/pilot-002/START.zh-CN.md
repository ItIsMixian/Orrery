# PO-CR-004 pilot 002：A／B／C 操作说明

pilot 002 修复了首轮试验暴露的三个问题：缺失验收所需的公开仓库身份、不同变体读取了不同版本的外部 Skill、以及“搜索输出正文是否算读取”定义不清。

本轮仍是实验装置验证，不会直接形成 ADR。

## 1. 生成隔离仓库和不可混写的 Prompt

在 Project Orrery 源仓库运行：

```powershell
Set-Location -LiteralPath "D:\coding warehouse\project-orrery"

powershell -NoProfile -ExecutionPolicy Bypass `
  -File ".\experiments\context-routing\pilots\pilot-002\prepare_pilot.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-002"
```

`OutputRoot` 必须尚不存在，并位于源仓库之外。脚本会产生：

```text
pilot-002\
├─ _operator\
│  ├─ PROMPT-A.zh-CN.md
│  ├─ PROMPT-B.zh-CN.md
│  ├─ PROMPT-C.zh-CN.md
│  └─ pilot-manifest.json
├─ PO-CR-004-A\
├─ PO-CR-004-B\
└─ PO-CR-004-C\
```

`pilot-manifest.json` 保存共同任务、每个完整 Prompt 的 SHA-256、各隔离仓库 HEAD 和允许的验证命令。不要编辑生成后的 Prompt；需要修正时应创建 pilot 003。

面向操作者的 Prompt 与 manifest 使用带 BOM 的 UTF-8，避免 Windows PowerShell 5 或本地文件查看器把中文误判为系统代码页。若预览仍出现乱码，不要复制或发送该文件，应先把运行判为装置故障。

## 2. 做外部上下文预检

准备器已经在三个仓库中提交同一份 `.codex/config.toml` 测试夹具，使用 `skills.config` 禁用 Project Orrery、OpenAI Docs 与 Skill Installer 的用户级副本。根据[官方 OpenAI 配置说明](https://developers.openai.com/codex/config-reference)，项目级配置只会在受信任项目中加载；因此打开隔离仓库时应确认客户端把它视为受信任项目，再开始任务。

`.codex/config.toml` 只属于 Harness overlay：Agent 可以在路径枚举中看见它，但不得读取或修改正文，也不得把它算作任务证据。其 SHA-256 记录在 `pilot-manifest.json`，三组必须相同。

如果当前宿主仍然加载了任何被禁用的外部 Skill 或系统文档，Prompt 要求 Agent 在写入前立即停止并返回 `RUN CONTAMINATED`。污染运行不得与其他变体比较，也不能通过“事后忘掉”恢复。

不要手工向任一 Agent 附加 Skill 文本、安装器说明、当前仓库 README、历史 diff 或本对话内容。

## 3. 同时建立三条全新任务

不要从当前任务分叉。分别把工作目录设置为匹配的隔离仓库，然后将对应 `PROMPT-*.zh-CN.md` 的**全部内容**作为首条消息发送：

| 任务 | 工作目录 | 发送内容 |
|---|---|---|
| A | `...\PO-CR-004-A` | `_operator\PROMPT-A.zh-CN.md` 全文 |
| B | `...\PO-CR-004-B` | `_operator\PROMPT-B.zh-CN.md` 全文 |
| C | `...\PO-CR-004-C` | `_operator\PROMPT-C.zh-CN.md` 全文 |

三条任务必须使用相同模型、reasoning effort、权限、联网状态和时间预算。最好在查看任何结果前全部启动。

记录下列运行元数据；界面没有提供的字段保留 `null`：

- 模型与 reasoning effort；
- 权限配置；
- `pilot-manifest.json` 中对应的 Prompt SHA-256；
- Agent 返回的 `started_at` 和 `ended_at`；
- token 与费用（若宿主显示）；
- 操作者追加的每条消息。若一组提出澄清，必须给三组相同回复，否则标记污染。

## 4. 冻结并收集结果

不要提交、推送、合并或删除隔离仓库。保存三组最终回复，然后由评估者在每个隔离仓库独立运行：

```powershell
git status --short
git diff --check
git diff --name-only
git diff -- README.md
python -m unittest discover -s tests -v
```

带回主评估任务的材料：

1. `_operator\pilot-manifest.json`；
2. A／B／C 最终回复；
3. 三组独立验证输出；
4. 三组实际 diff；
5. 运行元数据与操作者干预记录。

访问清单仍然只是 `agent` 自述。除非宿主或受控 wrapper 真正记录了模型边界上的内容读取，否则不能升级为 `harness` 证据。

## 5. 本轮有效性门槛

只有同时满足以下条件，pilot 002 才能作为一条可比较运行：

- 三组来自配置中同一个历史基线；
- 三组带有 SHA 相同的 Harness overlay，且项目配置实际生效；
- 三组收到相同共同任务事实，Prompt SHA 与 manifest 一致；
- `external_context_preflight` 为 `clean`；
- 没有未同步的操作者补充；
- B/C 的所有 Manifest 外正文读取都在读取前声明扩展；
- 三组使用相同验证命令；
- 评估者明确区分 Agent 自述与独立观察。

即使本轮有效，单个低风险 README 任务也不能决定架构。它只证明装置足以进入更广的任务批次。
