# Validation：Codex Runtime E2E 安全停止

Date: 2026-08-21
Scope: ADR-0004 Implementation Plan Phase 2 的 Codex Adapter 发现、依赖失败关闭、升级与可恢复卸载；不含 Phase 3 或第二平台
Result: PARTIAL / STOP — 真实调用隔离门未通过，支持状态保持 `experimental`
Source: branch `codex/agent-platform-adapters`，baseline／HEAD／`main`／merge base 均为 `117acac9825b0ee93f0a98a8a64c8b82d13f56f6`

## 权威链与官方 runtime 依据

- 决策与设计：[ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)、
  [平台中立 Core 与 Adapter 架构](../design/platform-neutral-core-and-adapter-architecture.md)。
- 活动计划：[平台中立 Core 与 Agent／Harness Adapter](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)。
- OpenAI 官方 [Build skills](https://learn.chatgpt.com/docs/build-skills) 说明 Codex 会从 repo、user、admin
  与 system scope 发现 Skill；同名 Skill 不合并，两者都可能出现在 selector 中。
- OpenAI 官方 [Developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli) 说明
  `codex exec --ignore-user-config` 只跳过 `$CODEX_HOME/config.toml`，认证仍使用 `CODEX_HOME`；它没有声明会
  排除用户级 Skill。`--ephemeral` 只是不持久化 session rollout。
- 上述官方边界与本机无模型探针一致，因此没有把 `--ignore-user-config` 当成 Skill discovery 隔离开关。

## 精确环境

| 项目 | 值 |
|---|---|
| OS | Windows 11 Pro x64，`10.0.26200`，build 26200 |
| Python | 3.13.5 |
| Codex Desktop package | `26.818.2441.0` |
| Codex CLI runtime | `codex-cli 0.148.0-alpha.21` |
| 原 binary | `C:\Program Files\WindowsApps\OpenAI.Codex_26.818.2441.0_x64__2p2nqsd0c76g0\app\resources\codex.exe` |
| 实际执行副本 | `D:\coding warehouse\project-orrery-adapter-e2e-stage-a-20260821\runtime\codex.exe` |
| binary SHA-256 | `18fbf51f77adfc543c9d86c78c0a54553f89ba79236ed8b0a3c48e2a3b4f010e` |
| Adapter | `project-orrery-codex` 0.1.0，API 1，`experimental`，未发布 |
| Core / CLI | Core 0.1.0／API 1；CLI 0.1.0，均为未发布源码包 |
| Adapter CLI 约束 | distribution `project-orrery-cli`，`>=0.1.0,<0.2.0`，entrypoint `project-orrery` |
| 模型调用 | 0；没有读取或复制 token／登录凭据，没有发送项目内容到模型 |

WindowsApps 原路径不能由当前 shell 直接启动，因此 Stage A 只复制 runtime binary 及其同目录运行依赖到
D 盘隔离根；复制前后的 binary SHA-256 一致。所有 runtime 命令都使用该精确副本。

## Stage A：无模型隔离验证

隔离根为 `D:\coding warehouse\project-orrery-adapter-e2e-stage-a-20260821`。没有使用 API Key、登录态、
真实用户 Skill 目录或模型调用。

| 检查 | 结果 |
|---|---|
| 确定性打包 | PASS — 两次 6-entry ZIP 完全一致，SHA-256 `722be9460bc11c716cb5602ba1c655668a0c5db1a6b063833457e1038795a5da` |
| dry-run／安装／相同版本 KEEP | PASS — dry-run 零写入；实际安装与重复安装符合预期 |
| unknown directory | PASS — exit 2，目录内容不变 |
| 已识别旧 Adapter | PASS — 无 `--upgrade` 时拒绝；显式升级前完整备份 |
| 完整 v0.2 Skill | PASS — 无 `--upgrade` 时拒绝；显式升级前完整备份 |
| uninstall | PASS — 目录移入可恢复 trash，输出精确恢复路径 |
| discovery 边界 | PASS — backup／trash 均在 discovery root 外 |
| 作者文件 | PASS — 测试项目 `AGENTS.md` 哈希与 Git author tree 不变 |
| CLI 缺失 | PASS（直接 Adapter preflight）— exit 3，`code=cli_distribution_missing` |
| CLI entrypoint 缺失 | PASS（回归 fixture）— exit 3，`code=cli_entrypoint_missing` |
| CLI 版本 0.2.0 | PASS（直接 Adapter preflight）— exit 4，`code=cli_version_incompatible` |
| CLI 版本 0.1.0 | PASS（直接 Adapter preflight）— exit 0，并解析到 entrypoint |

为使自然语言依赖声明成为可重复执行的失败关闭边界，本轮新增
`adapters/codex/scripts/check_cli_dependency.py`，并把它列入 Adapter manifest。它只读取 Adapter manifest、
Python distribution metadata 与 `PATH`；不调用网络或旧实现。Stage A 的兼容 CLI 位于
`D:\coding warehouse\project-orrery-adapter-e2e-stage-a-20260821\cli-compatible-venv-system`。

## Stage B：真实 Codex runtime

### 发现与升级

- 在隔离 `CODEX_HOME`、隔离 HOME 和 repo discovery root 下，
  `codex debug prompt-input "Report discovery only."` exit 0；旧 Adapter 的模型可见目录中只有一个
  `project-orrery`，命中 Adapter 描述 1 次、旧 Skill 描述 0 次。原始 JSON prompt input SHA-256 为
  `5a9fb3b9e9847e5ad5c777b86c3a76875dc4cb1bbb883204ec6b31c73ca6b589`。
- 完整 v0.2 Skill 在升级前被同一 runtime 发现为唯一 `project-orrery`；命中旧 Skill 描述 1 次、Adapter
  描述 0 次，原始 JSON SHA-256 为 `9f2c38e1a1f2a9e05a2d6f3730ba9d0d5ca3b5e799f8eba66fbca6f931bd60bb`。
- v0.2 Skill 无显式 `--upgrade` 时 exit 2 且树摘要不变；显式升级的 40-file backup 摘要与升级前一致：
  `55f5673728014fb71931e3d3c169615ea7bcf20650e4b11b8c787b6d345b72a9`。
- 已识别旧 Adapter 的 5-file backup 摘要与升级前一致：
  `ab5fc8cd2f2ad10b673d000a2e775a0d9e14315de057acc20b8af8b52f44b029`。
- 升级后隔离 runtime 仍只发现一个 Adapter；backup 路径命中 0 次，模型可见 prompt text SHA-256 为
  `2ac237ed9da6e5f4b7682dadbe0509a4e1f1dbccdb2d4963a94209816d22d5ad`。

### 安全停止点

当 `CODEX_HOME=C:\Users\1\.codex` 以便原地使用真实登录态时，无模型 prompt-input 目录出现两个同名
`project-orrery`：

- `r8 = D:/coding warehouse/project-orrery-adapter-e2e-stage-b-20260821/runtime-repo/.agents/skills`
  对应新 Adapter 描述；
- `r0 = C:/Users/1/.codex/skills` 对应既有完整旧 Skill 描述。

目录中同名条目共 2 个，两种描述各命中 1 次；原始 JSON SHA-256 为
`03f4604825c3b5434518f241c074071eea55a91526d52fa39725d85c71338d35`。官方资料没有提供“保留该
`CODEX_HOME` 认证但排除其用户 Skill”的开关；把凭据复制到临时 `CODEX_HOME` 又违反本任务边界。因此在
任何 `codex exec` 之前停止，获准的 `gpt-5.6-terra`／medium turn 实际执行 0 次。

这意味着显式调用、适用时的隐式调用，以及由模型触发的 CLI 缺失／不兼容失败路径均没有真实 runtime
证据。Stage A 的直接 preflight 结果不能冒充模型实际调用。

### 可恢复卸载与重新发现

- 升级后的 6-file Adapter 摘要为
  `ffc7bba8b3b3c9e79aa0d68b7787ab7d4b6297008e4ebe41bb3c65e52e249b54`；uninstall 后 trash 摘要完全一致。
- trash 与 backup 均不在 `.agents/skills` 下。隔离 runtime 卸载后 `project-orrery`、Adapter 描述、旧 Skill
  描述、backup 和 trash 路径的命中数均为 0；prompt text SHA-256 为
  `52de0c5f08aa5097146d5c75e7e41172c446c119dfdbe99da96c7f2cb51f57b3`。
- 真实认证 home 下卸载后只剩既有旧 Skill：目录条目 1、Adapter 描述 0、旧 Skill 描述 1；prompt text
  SHA-256 为 `bd77482b96efc8437bea926949e6f9ab6373c1f8b5f826e87913a93a271a8d28`。
- runtime 测试仓库 HEAD 始终为 `d770a57cbea2b8cf45245e7b4c0dc7bb0a89fcb7`，Git tree 始终为
  `662b13b16f9e03d1d2b8131fc7e670baf912fab4`，`.agents/` 外 author status 为 0 项。

## 验证矩阵与门禁

| 必须路径 | 证据 | 结论 |
|---|---|---|
| runtime 发现 Adapter | 真实 binary `debug prompt-input`，唯一 repo Adapter | PASS |
| Adapter 路由到 CLI | 没有安全的真实登录态 discovery 隔离 | NOT RUN |
| CLI 缺失失败关闭 | Adapter preflight exit 3；没有模型触发证据 | PARTIAL |
| CLI 不兼容失败关闭 | Adapter preflight exit 4；没有模型触发证据 | PARTIAL |
| v0.2 只显式升级 | 拒绝后树不变，显式升级成功 | PASS |
| 升级前完整备份 | 文件数与树摘要一致 | PASS |
| 可恢复卸载 | trash 摘要一致并输出恢复路径 | PASS |
| backup／trash 不重复发现 | prompt-input 命中 0 次 | PASS |
| 作者文档不受影响 | HEAD／tree／author status 不变 | PASS |
| 卸载后不再发现 Adapter | 隔离 home 0 项；真实 home Adapter 描述 0 | PASS |
| 原用户环境 | 未安装、升级或卸载真实用户 Adapter；用户级 Skill 无测试期间写入 | PASS（任务作用域） |

`verified` 完整门仍缺真实显式调用、适用时的隐式调用，以及模型触发的缺失／不兼容失败路径。Adapter 与
runtime manifest 必须继续保持 `experimental`，`verified`／`evidence` 数组继续为空。该结论不改变
v0.2.0 已发布旧 Skill，也不代表新 Adapter 已发布。

## 最终仓库验证

| 命令／检查 | 结果 |
|---|---|
| `python -X utf8 -m unittest tests.test_codex_adapter -v` | PASS — 6/6 |
| `python -X utf8 -m unittest tests.test_project_orrery tests.test_codex_adapter -v` | PASS — 20 passed，2 expected skips |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated candidate |
| `python -X utf8 scripts/docsite/build_docsite.py --docs <absolute-docs> --agents <absolute-AGENTS> --out <D-drive-temp-html>` | PASS — 59 docs，879319 bytes；没有写 `docs/_site/index.html` |
| PowerShell Markdown local-link scan | PASS — 244 files，477 local links，0 missing |
| `git diff --check` | PASS |

隔离 HTML 位于
`D:\coding warehouse\project-orrery-adapter-e2e-stage-b-20260821\docsite-html\index.html`，SHA-256 为
`61abe511442b746824bdf0c78d9ce778b8d57d4940ec38187fa37eaaf39ddec9`。

## 外部状态与恢复

- 创建并保留两个 D 盘隔离证据根：`project-orrery-adapter-e2e-stage-a-20260821` 与
  `project-orrery-adapter-e2e-stage-b-20260821`；其中包含 runtime 副本、venv、fixture、backup 与 trash，
  便于复核和人工恢复。
- Stage A 首次本地 pip 安装产生的 3 个用户 pip cache leaf 已精确删除；源码包目录生成的 6 个未跟踪
  build／egg-info 目录也已精确删除。
- 没有写入 `C:\Users\1\.codex\skills` 或 `C:\Users\1\.agents\skills`，没有复制／读取登录凭据，
  没有创建模型 session。真实 `project-orrery` Skill 的 34 个文件在 Stage A 根创建后均无写入；
  `C:\Users\1\.agents\skills\project-orrery` 仍不存在。
- `debug prompt-input` 使用真实 `CODEX_HOME` 时可能刷新了普通 `models_cache.json`；Codex Desktop 的 SQLite、
  session 与 config 状态也在并发变化，未对这些共享运行态做字节级回滚。任务涉及的 Adapter／Skill／项目
  作者文件均已恢复或保持原状。
