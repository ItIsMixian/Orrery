# Validation：Codex Runtime E2E 完成

Date: 2026-08-21
Scope: ADR-0004 Implementation Plan Phase 2 的 Codex Adapter 真实发现、调用、依赖失败关闭、升级、可恢复卸载和环境恢复；不含 Phase 3、第二平台、多人协作或 Authority Meta Model
Result: PASS — 只有本文记录的 runtime 范围改为 `verified`；Adapter 发行状态仍为 `experimental`，Adapter、Core 与 CLI 均未发布
Source: branch `codex/agent-platform-adapters`，本次续验起始 HEAD `78fb42d26489c35667dd94af9ef1be72b79587f4`，merge base `main@117acac9825b0ee93f0a98a8a64c8b82d13f56f6`

## 权威链与前置证据

- 决策：[ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)。
- Approved Design：[平台中立 Core 与 Adapter 架构](../design/platform-neutral-core-and-adapter-architecture.md)。
- 活动 Plan：[平台中立 Core 与 Agent／Harness Adapter](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)。
- 仓库实现：[Phase 2 Codex Adapter](2026-08-19-platform-neutral-phase-2-codex-adapter.md)。
- Stage A、旧 Skill／旧 Adapter 升级、备份、首次卸载与同名污染发现：
  [Codex Runtime E2E 安全停止](2026-08-21-codex-runtime-e2e.md)。该记录保持当时的 PARTIAL 结论；
  本文只记录其后解除阻塞并补齐的真实调用证据。

当前 Codex 行为只依据 OpenAI 官方资料和精确 runtime 自带 help：

- [Build skills](https://learn.chatgpt.com/docs/build-skills) 定义 repo、user、admin 与 system discovery scope。
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) 定义
  `skills.config`、`path` 与 `enabled`。
- [Developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli) 定义
  `--ignore-user-config`、`--ephemeral`、`--json`、sandbox 与 inline `-c`。
- [Authentication](https://learn.chatgpt.com/docs/auth) 与
  [environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables) 定义
  `CODEX_HOME` 的认证／配置边界。本验证没有复制或输出 `auth.json`、token 或 API Key。

## 精确验证范围

| 维度 | 值 |
|---|---|
| OS | Windows 11 Pro x64，`10.0.26200`，build 26200 |
| Python | 3.13.5；失败 fixture 使用 `C:\Users\1\anaconda3\python.exe` |
| Codex Desktop | `26.818.2441.0` |
| Codex CLI | `codex-cli 0.148.0-alpha.21` |
| runtime binary | `D:\coding warehouse\project-orrery-adapter-e2e-stage-a-20260821\runtime\codex.exe` |
| binary SHA-256 | `18fbf51f77adfc543c9d86c78c0a54553f89ba79236ed8b0a3c48e2a3b4f010e` |
| Adapter | `project-orrery-codex` 0.1.0，API 1 |
| Core／CLI | Core 0.1.0／API 1；CLI 0.1.0；均为未发布源码包 |
| CLI 约束 | distribution `project-orrery-cli`，`>=0.1.0,<0.2.0`，entrypoint `project-orrery` |
| 模型 | `gpt-5.6-terra`，reasoning effort `medium` |
| 执行模式 | `codex exec --approve-for-me --ignore-user-config --ignore-rules --ephemeral --json`；workspace-write 自动审批 |
| runtime repo | `D:\coding warehouse\project-orrery-adapter-e2e-stage-b-20260821\runtime-repo` |

其他 Codex 版本、OS、模型、审批／sandbox 模式和已发布独立 CLI 均不在 `verified` 范围。

## 同名 Skill 隔离修复

隔离 `CODEX_HOME` 的 keyring 与 `auto` 登录状态都为 `Not logged in`，因此不能在不复制凭据的情况下用
全新 home 发起真实 turn。保留 `CODEX_HOME=C:\Users\1\.codex` 时，不加覆盖的无模型
`codex debug prompt-input` 显示两个同名条目：repo Adapter 1 个、用户旧 Skill 1 个。

官方配置参考把 `skills.config.path` 描述为包含 `SKILL.md` 的 Skill 文件夹；在本次精确
`0.148.0-alpha.21` Windows runtime 中，文件夹路径覆盖仍保留两个条目，而指向解析后的
`SKILL.md` 文件路径才生效：

```text
-c 'skills.config=[{path="C:/Users/1/.codex/skills/project-orrery/SKILL.md",enabled=false}]'
```

无模型对照结果：不覆盖为 2 项（Adapter 1、旧 Skill 1）；文件夹路径覆盖仍为 2 项；文件路径覆盖为
1 项（Adapter 1、旧 Skill 0）。因此后续 turn 使用文件路径 per-run 覆盖。它没有写真实配置、没有改
用户 Skill 目录，也没有弱化 repo discovery。该文件路径行为只作为此 runtime 的实测差异记录，不能
外推到其他版本。

## 真实模型调用

所有 prompt 都限定为隔离 fixture、只读验证，不包含秘密或无关项目内容。`--ephemeral` 没有保存
session rollout。首次显式 turn 使用普通 workspace-write 时，Adapter 已被读取，但 Python 子进程在
启动前被 policy 拒绝，最终为 `preflight=blocked; validate=not-run`；该失败不计为通过。依据精确
runtime `codex exec --help`，后续使用 `--approve-for-me` 保持 workspace-write 自动审批边界。

| 路径 | 真实 runtime 证据 | 结果 |
|---|---|---|
| 显式调用 | prompt 明示 `$project-orrery`；模型先读取权威入口与 Adapter，再执行 preflight 和 validate | PASS — `PREFLIGHT_EXIT=0 VALIDATE_EXIT=0`；CLI 输出 `Authority status: migration pending`，没有把 scaffold 冒充正式采纳 |
| 隐式调用 | prompt 只要求验证 Project Orrery 文档系统，未点名 Skill；模型主动读取 repo Adapter | PASS — `dependency check: 0; validation: 0` |
| CLI distribution 缺失 | PATH 中无 `project-orrery`，Python metadata 无 distribution | PASS — `ERROR code=cli_distribution_missing distribution=project-orrery-cli`，模型明确 `validation was not run`，没有旧实现 fallback |
| CLI 版本不兼容 | fixture metadata 为 0.2.0，manifest 要求 `<0.2.0` | PASS — `ERROR code=cli_version_incompatible ... installed=0.2.0 required=>=0.1.0,<0.2.0`，模型明确 validation 未运行 |

失败 fixture 直接运行 Adapter preflight 的原始退出码分别为 3 和 4。Codex 的 PowerShell tool event 把
这两个非零子进程都标为 exit 1，而已处理失败的外层 `codex exec` 为 exit 0；结构化 Adapter error 与
“validation 未运行”才是模型路径的失败关闭证据，不能把外层进程 0 误写成依赖成功。

真实 turn 还产生两个与 Adapter 无关但已记录的 runtime warning：PowerShell shell snapshot 尚不支持；
现有 `deepseek-code/agents/openai.yaml` 有无效 UTF-8 metadata。两者没有改变本次命令结果或用户 Skill。

## 生命周期与重新发现

前置 Validation 已证明：

- unknown directory 拒绝；
- 完整 v0.2 Skill 和已识别旧 Adapter 都只有显式 `--upgrade` 才迁移；
- 升级前备份与原树文件数、摘要一致；backup 位于 discovery root 外；
- 项目作者 HEAD `d770a57cbea2b8cf45245e7b4c0dc7bb0a89fcb7` 与 tree
  `662b13b16f9e03d1d2b8131fc7e670baf912fab4` 不变。

补齐模型调用后再次对 repo Adapter 执行 recoverable uninstall：安装树与 trash 都为 6 文件，树摘要
均为 `f20564eced115ab6b47518ab63923684fef10f0d2e5fefd2fd0d17c3d3024e29`；恢复路径为：

```text
D:\coding warehouse\project-orrery-adapter-e2e-stage-b-20260821\runtime-repo\.agents\.project-orrery-adapter-trash\20260821T003638.180727Z\project-orrery
```

trash 不在 `.agents/skills` discovery root。卸载后：

- 不禁用用户旧 Skill时：`project-orrery` 1 项、Adapter 0、旧 Skill 1、trash 命中 0；prompt text SHA-256
  `bd77482b96efc8437bea926949e6f9ab6373c1f8b5f826e87913a93a271a8d28`。
- 使用同一 per-run 禁用项时：`project-orrery` 0 项、Adapter 0、旧 Skill 0、trash 命中 0；prompt text
  SHA-256 `f9b33fafda0a886a75a3522378d83622cf19877ac15646fc9769552c31e92d0a`。

真实用户旧 Skill 在 turn 前后均为 34 文件，树摘要
`4a8181352c449fa99b59786888742e2773a0e872696e14a98ce74047c8be32f7`，最新写入时间仍为
`2026-08-17T09:54:11.0057063Z`；`C:\Users\1\.agents\skills\project-orrery` 仍不存在。

首个真实 turn 在 runtime repo 产生未跟踪 PowerShell `ModuleAnalysisCache`。它已可恢复地移出作者树到：

```text
D:\coding warehouse\project-orrery-adapter-e2e-stage-c-fix-20260821\quarantine\runtime-repo-Microsoft-20260821T003041Z
```

恢复后 `.agents/` 外 author status 为 0，HEAD 与 tree 仍为上述固定值。

## verified 门禁决定

| 门禁 | 结论 |
|---|---|
| 精确 runtime／OS／Adapter／Core／CLI | PASS |
| 真实发现 | PASS — per-run 隔离后唯一 repo Adapter |
| 真实显式调用 | PASS |
| 真实隐式调用 | PASS |
| 明确失败路径 | PASS — distribution 缺失与版本不兼容均失败关闭 |
| 更新 | PASS — 旧 Skill／旧 Adapter 显式升级与完整备份 |
| 卸载／恢复 | PASS — recoverable trash、重新发现 0 项、恢复路径保留 |
| 作者文件与用户 Skill | PASS — 作者 tree 与用户旧 Skill 摘要不变 |
| Validation 链接 | PASS — 本文及前置安全停止记录 |

完整门通过，因此 Adapter 0.1.0 的 manifest 与组件投影只把 `runtime_compatibility` 的“精确验证
范围”改为 `verified`。Adapter distribution 的 `support_status` 继续为 `experimental`，因为独立 CLI
与公开安装路径尚未发布。`implemented != runtime-verified != released`：
`packages/component-versions.json` 顶层继续为 `unreleased`，没有 tag、Release、push、main merge 或
第二平台声明。

## 最终仓库验证

| 命令／检查 | 结果 |
|---|---|
| `python -X utf8 -m unittest tests.test_codex_adapter -v` | PASS — 6/6 |
| `python -X utf8 -m unittest tests.test_project_orrery tests.test_codex_adapter -v` | PASS — 20 passed，2 expected skips |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — `integrated candidate` |
| 两次 `python -X utf8 scripts/package_codex_adapter.py --check-adapter-version 0.1.0` | PASS — 两个 6-entry ZIP byte-identical，SHA-256 `3980d59639109c8e501d53618aeca225c783fbc064c52712ae12931de516e366` |
| 隔离 docsite build | PASS — 60 docs；输出只写 Stage C 隔离根 |
| Markdown 本地链接扫描 | PASS — 245 files，486 local links，0 missing |
| `git diff --check` | PASS |

隔离 HTML 位于
`D:\coding warehouse\project-orrery-adapter-e2e-stage-c-fix-20260821\docsite-html\index.html`；没有修改
`docs/_site/index.html`。最终归档与 checksum 位于同一 Stage C 根的 `package-a`／`package-b`。

## 外部状态清单

- 保留 Stage A、Stage B 与 Stage C 三个 D 盘隔离根，用于 runtime、venv、fixture、backup、trash 与
  可恢复 PowerShell cache 复核。
- 使用真实 `CODEX_HOME` 的既有登录态发起最少验证 turn；没有读取、复制或输出凭据，没有写真实
  `skills` 目录或 Codex 配置。
- `debug prompt-input`／模型目录加载可能刷新普通 Codex cache；`--ephemeral` 不持久化 rollout。
- repo Adapter 已从 runtime fixture 可恢复卸载；用户旧 Skill 和目标项目作者文件保持原状。
