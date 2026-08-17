# PO-CR-004 首轮 A／B／C 测试操作说明

这是一轮低风险文档任务烟雾测试，目标是验证测试方法本身，而不是立刻决定 Project Orrery 的新架构。

## 测试任务

三组 Agent 接收相同任务：改善公开 README，让新用户能够从 GitHub 获得清晰、可复制的 Codex Skill 安装指令，同时保持现有采纳与安全边界。

唯一变量是上下文路由策略：

- A：固定强制阅读链；
- B：任务分类、Context Manifest 与带理由的范围扩展；
- C：B 加选择性检索、局部读取和上下文预算。

## 为什么不用普通 worktree

普通 worktree 会共享源仓库对象和引用，测试 Agent 仍有机会通过 `git log --all` 或其他引用看到后来提交的参考答案。准备脚本改用目标基线 commit 的归档快照，并为 A／B／C 分别初始化没有 remote、没有未来历史的独立 Git 仓库。

## 第一步：生成三个隔离仓库

在 Windows PowerShell 中运行：

```powershell
Set-Location -LiteralPath "D:\coding warehouse\project-orrery"

powershell -NoProfile -ExecutionPolicy Bypass `
  -File ".\experiments\context-routing\prepare_pilot.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-001"
```

`OutputRoot` 必须是尚不存在的新路径，并且必须位于 Project Orrery 源仓库之外。脚本不会覆盖现有目录。

成功后会得到：

```text
D:\coding warehouse\project-orrery-benchmark\pilot-001\PO-CR-004-A
D:\coding warehouse\project-orrery-benchmark\pilot-001\PO-CR-004-B
D:\coding warehouse\project-orrery-benchmark\pilot-001\PO-CR-004-C
```

## 第二步：建立三条全新对话

不要从当前对话分叉，也不要把当前聊天记录交给测试 Agent。

在 Codex 中分别新建三个任务：

| 新任务 | 工作目录 | 首条消息 |
|---|---|---|
| PO-CR-004-A | `...\PO-CR-004-A` | [prompts/PO-CR-004-A.zh-CN.md](prompts/PO-CR-004-A.zh-CN.md) 的正文 |
| PO-CR-004-B | `...\PO-CR-004-B` | [prompts/PO-CR-004-B.zh-CN.md](prompts/PO-CR-004-B.zh-CN.md) 的正文 |
| PO-CR-004-C | `...\PO-CR-004-C` | [prompts/PO-CR-004-C.zh-CN.md](prompts/PO-CR-004-C.zh-CN.md) 的正文 |

三条对话必须使用：

- 相同模型与 reasoning effort；
- 相同权限配置；
- 相同联网条件，首轮建议不联网；
- 相同时间与验证预算；
- 相同的用户补充信息。

最好在查看任何一组结果前就把三条任务都启动，避免后一个实验受到前一个结果影响。

## 测试期间不要做的事

- 不要向测试 Agent 提及参考 commit、标准改动路径或另外两组结果。
- 不要让测试 Agent读取本仓库的 `corpus.json`、研究笔记或提示词目录。
- 不要在 A 完成后根据结果改写 B／C 的任务描述。
- 如果某组提出澄清问题，应向三组补充完全相同的信息；无法统一时记录为实验偏差。
- 不要让任何一组提交、推送或联网查找当前 GitHub README。

## 第三步：完成后保留证据

每组 Agent 完成后，先保存它的最终回复，再在对应隔离仓库运行：

```powershell
git status --short
git diff --check
git diff -- README.md
```

不要立刻删除隔离仓库，也不要合并它们。把以下材料带回主测试对话：

1. A／B／C 三组最终回复；
2. 三组 `git status --short`；
3. 三组 `git diff --check`；
4. 三组 `git diff -- README.md`；
5. 若 Codex 界面能显示，记录各自耗时与 token；没有就保留 `null`，不要填成 0。

Agent 最终回复中的访问清单只能标记为 `agent` 自述。除非宿主工具另有真实访问日志，否则不能写成 `harness` 证据。

## 评估者最后才可以查看参考答案

三组全部冻结后，评估者才可以在 Project Orrery 源仓库查看历史参考提交：

```powershell
git show --stat 80b17bec84b763a356f54838771d6a9d91133800
git diff e0680523e4cacde2e8413188e04e801e9c2c1c81 80b17bec84b763a356f54838771d6a9d91133800 -- README.md
```

这些命令不得在 A／B／C 隔离仓库或测试对话中执行。

## 本轮通过标准

本轮主要判断实验装置是否可用：

- 三组都从相同基线开始；
- 三组都完成任务并通过 `git diff --check`；
- B／C 能清楚给出 Manifest、范围扩展与读取自述；
- 三组改动可以与同一个历史参考 diff 对照；
- 没有把 Agent 自述误当成独立访问证据。

单次任务的胜负不能直接形成架构 ADR。至少完成一批不同类别任务后，才分析正确率、上下文开销和文档负担。
