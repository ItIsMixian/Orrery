# Validation：DeepSeek Harness Adapter Stage B 真实模型 Runtime

Date: 2026-08-22
Scope: DeepSeek Harness 真实 provider／model、显式与隐式 Skill 调用、CLI 路由、CLI 缺失／不兼容失败关闭、可恢复卸载和环境恢复；不含公开发布、跨 OS 或普通 wheel 缺陷修复
Result: PASS WITH BLOCKER — Adapter 的真实模型调用链与生命周期通过，但普通 wheel 安装的 CLI 0.1.1 无法定位 Observatory source assets，故支持状态保持 `experimental`，`verified` 仍为空
Source: branch `codex/claude-deepseek-adapters`；runtime 从 `209cfc341a25f7797be3e3033298e731eb2e7566` 开始，最终 evidence manifest 归档见下列 checksum；原 baseline `main@2989582d106e1bc36307a30427c8ba5f1dfb91c2`

## 权威链与集成边界

- [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)
- [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
- [Approved Design](../design/platform-neutral-core-and-adapter-architecture.md)
- [Implementation Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)
- [Stage A](2026-08-21-deepseek-harness-adapter-stage-a.md)
- [Stage B credential blocker](2026-08-21-deepseek-harness-adapter-stage-b-credential-blocked.md)

本 Validation 的原始运行属于功能分支 Worktree scope。执行时本地 `main` 已推进到 `8df974f`，并已把
ADR-0010／0011／0012 分配给 Authority／治理工作；干净集成时已将该分支较早创建的 Phase 4
`ADR-0010` 重编号为 ADR-0013，并重新核对主线 State。原始运行范围没有因编号修复而扩大。

## 精确环境

| 维度 | 值 |
|---|---|
| OS | Windows 11 Pro x64 `10.0.26200`，build 26200 |
| Node／pnpm／Python | Node 22.17.0；pnpm 11.19.0；Python 3.13.5 |
| DeepSeek Harness | `@deepseek-ai/dsh 0.1.0-rc.8` |
| entrypoint | `D:\coding\Deepseek Harness\node_modules\@deepseek-ai\dsh\lib\bin.js` |
| entrypoint SHA-256 | `c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62` |
| provider／model | `deepseek-official`／`deepseek-v4-flash`；context window 1,000,000 |
| Adapter | `project-orrery-deepseek-harness-adapter` 0.1.0 |
| 最终 Adapter TGZ SHA-256 | `25593035c774da3380228209cd8b6243906c2b7e888218fa7e88dfe87d4e22c8`；两次归档 byte-identical |
| Core／CLI | Core 0.1.0／CLI 0.1.1；CLI 要求 `>=0.1.1,<0.2.0` |
| 权限与范围 | 隔离 headless profile；作者 fixture 只读；telemetry disabled |

用户 GUI 的 launcher 只读解析出真实 `DSH_HOME=D:\coding\DeepseekHarnessProfile` 和
`DSH_AGENTS_HOME=D:\coding\DeepseekHarnessAgents`。测试没有把 Adapter 安装进该 profile，也没有复制
`.credentials.yaml`；只把 `DEEPSEEK_API_KEY` 读入每个模型子进程的内存，结束时立即移除。真实 credential、
settings、launcher 的前后 SHA-256 相等，GUI 进程持续运行。

## 隔离装置

主证据根为 `D:\orrery-stage-b-dsh-auth-20260821-001`：

- `author-project.zip` 是分支提交的 `git archive`，解压后 424 个作者文件用于只读 target；
- `dsh-home`／`agents-home`／pnpm store／npm cache 均位于证据根；
- `cli-venv2` 是普通 wheel 安装的 CLI 0.1.1；
- `cli-venv3-editable` 是同一提交、同一版本的未发布源码 editable 安装；
- `incompatible-overlay` 只把 distribution metadata 显式投影为 0.2.0；
- session 为 DSH 自身的 `session.jsonl.zstd`，没有复制完整 transcript 进 Git。

第一次普通 venv 因缺 setuptools build backend 在 metadata 阶段失败，未启动模型；第二个 venv使用本机
已有 setuptools 成功构建 wheel。pip 为三个本地 Project Orrery wheel 写入用户 pip cache；这些文件不含
凭据，但因测试前不存在性未记录，没有擅自删除，故“用户外部状态完全恢复”门不宣称通过。

## 六个真实模型 turn

| Run | 触发 | 关键独立证据 | 结果 |
|---|---|---|---|
| 1 | 显式 `/project-orrery`，普通 wheel CLI | `skill-catalog` + `skill-invocation`；preflight exit 0；真实 `pwsh` CLI call | `validate` 在读取 target 前抛出 `cannot locate Project Orrery source repository for Observatory assets`；headless 正常报告失败原因 |
| 2 | 显式 `/project-orrery`，editable CLI | catalog + invocation；preflight 与 validate 各调用一次 | preflight exit 0；`validate` exit 0，`integrated candidate` |
| 3 | 无 slash 的适用任务 | 第一条模型工具调用为 `skill({"name":"project-orrery"})`，随后读取权威入口 | 隐式 Skill load、preflight exit 0、validate exit 0 |
| 4 | 显式，CLI 不在 PATH／metadata | 只有一次 preflight tool call | exit 3，`cli_distribution_missing`；无 fallback、无 validate |
| 5 | 显式，metadata 0.2.0 | 模型观察 manifest／preflight，只有一次 preflight 执行 | exit 4，`cli_version_incompatible`；无 fallback、无 validate |
| 6 | 最终 evidence manifest 归档，显式 editable route | 最终 TGZ 重新安装；preflight 与 validate 各调用一次 | 两者均 exit 0；随后最终 remove／probe 为 0 项 |

六个模型 turn 都由 session 事件记录 `request/context`、`assistant/message`、tool call/result 和
`turn/end`。聚合 usage 为 input 70,680、output 17,984、cache-read 451,456、reasoning 11,800 tokens；
四个卸载 probe session 为 0 模型 token。Provider 账单金额不由 DSH session 提供，本 Validation 不推断费用。

Run 3 的模型工具序列独立证明隐式选择：先调用 `skill` 加载 `project-orrery`，再读取 `AGENTS.md`、
HANDOFF、PROGRESS、principles 与相关 State，最后运行 dependency preflight 和 CLI validate。该证据只证明
这些记录在 DSH session 中，不把模型自然语言回执单独当作读取审计。

## 生命周期、作者文件与恢复

- 最终 Adapter TGZ 安装进隔离 `headless` profile，profile manifest 与 composed config 均识别 Bundle。
- 五个 turn 后执行 remove，修正后的真实 `ctx.skills` probe 返回 0 项／`get()` 空。
- 同一 discovery root 外的 TGZ 重新 `add` 后 probe 唯一发现 `project-orrery`、provider
  `project-orrery`；再次 remove 后最终 probe 又返回 0 项，profile dependency 与 Bundle 均为空。
- `author-project.zip` 与运行后 tree 比较为 expected 424、actual 424、missing 0、unexpected 0、changed 0。
- 真实 GUI profile、credential、settings、launcher 和进程不变；没有写用户 Agent Skill 根。

## verified 门禁判断

仓库收尾验证：

- `python -X utf8 -m unittest tests.test_deepseek_harness_adapter -v`：3/3 passed；
- 产品／全部 Adapter 组合：34 项中 32 passed、2 expected skips；
- `python -X utf8 -m unittest discover -s tests -v`：74 项中 72 passed、2 expected skips；
- integrated structure：PASS；静态 docsite 构建到
  `D:\orrery-docsite-deepseek-stage-b-runtime-20260822-001\index.html`：PASS；
- 257 份 Markdown／561 个本地链接／0 missing；secret pattern scan 与 `git diff --check`：PASS；
- `docs/_site/index.html` 未创建或修改。

真实 discovery、显式／隐式模型调用、CLI 缺失／不兼容失败关闭、安装、恢复安装、卸载、卸载后 0 项、
作者文件保护和真实 DSH 环境不变均已有可复现证据。但是普通 wheel 安装的兼容 CLI 0.1.1 仍无法执行
`validate`，成功路由只在未发布 editable source 安装中成立；此外用户 pip cache 有新增本地 wheel，功能
分支也尚未与当前 main 的 ADR／CLI 演进完成集成。

因此本轮不把 `runtime_compatibility.verified` 从空数组提升，Adapter distribution 继续
`experimental`／`unreleased`。下一步应在独立 CLI Workstream 修复 wheel 的 source-assets 定位并回归，
然后在同步当前 main、重编号 Candidate ADR 后，以最终归档补跑最少成功／失败矩阵。
