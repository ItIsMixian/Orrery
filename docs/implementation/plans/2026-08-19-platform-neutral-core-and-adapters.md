# 实施计划：平台中立 Core 与 Agent／Harness Adapter

Status: Active
Date: 2026-08-19
Governing ADRs: [ADR-0004](../../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0013](../../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
Approved Design: [平台中立 Core 与 Adapter 架构](../../design/platform-neutral-core-and-adapter-architecture.md)

## 范围边界

本计划只负责把现有平台中立能力从单一 Codex Skill 发布单元中逐步抽取出来。它不实施
Pilot 008、不处理多人／多 worktree 协作、不修改 docsite 凭据／Broker 方案，也不在缺少
真实 runtime 证据时宣布第二平台兼容。

## Phase 0：基线、命名与耦合清单

- [x] 把当前 Skill 归档内容、CLI 行为、模板文件、managed tools 和 manifest 字段固化为基线清单。
- [x] 建立现有 installer／validator／update checker 的 golden fixture 和人类输出兼容断言。
- [x] 在公开文档中区分 Core／CLI 可移植、已发布 Adapter 和已验证 runtime 三种状态。
- [x] 将模板入口的 Codex 专属标题改为中立名称，但保持 `AGENTS.md` 路径和内容职责。

验收证据：基线清单、无实现漂移的回归测试、支持状态表；本阶段不改变发布产物结构。

回滚边界：仅回滚命名和新增测试，不修改目标项目或 v0.2.0 资产。

## Phase 1：抽取 Core、CLI 与 Observatory 边界

- [x] 建立 Core 包，集中 schema、manifest 模型、迁移判定和 canonical 作者文档模板。
- [x] 建立 CLI 包，让现有三个脚本变为兼容 wrapper 或 console entry point。
- [x] 将 Observatory 作为独立 managed-tool 组件清点和版本化。
- [x] 保持 create-only、`--upgrade-tools` 白名单、备份和 `authority_status` 语义不变。
- [x] 保留旧 `skills/project-orrery/scripts/` 路径，直到至少一个稳定迁移版本完成。

验收证据：新旧入口在隔离临时项目上产生等价动作与 manifest；既有作者文件不被覆盖。

回滚边界：旧脚本和模板仍可独立工作；不要求迁移已有目标项目。

## Phase 2：Codex 参考 Adapter

- [x] 将 `SKILL.md`、`agents/openai.yaml` 和 Codex 安装说明收敛到独立 Codex Adapter 产物。
- [x] Adapter 只引用 Core／CLI，不复制 canonical 模板或兼容规则。
- [x] 定义平台安装器的 dry-run、备份、卸载和既有文件冲突行为。
- [x] 在真实 Codex runtime 上验证发现、调用、失败路径、更新和卸载，并记录精确版本与 OS。
- [x] 只有上述证据完成后，才把对应范围标为 `verified`。

Phase 2 已完成。仓库 Adapter、独立归档器、CLI 失败关闭和临时目录生命周期测试均已实现；
2026-08-21 的后续真实 runtime 验证使用按路径禁用旧用户 Skill 的 per-run 配置，既保留真实登录态，
又把模型可见目录收敛为唯一 repo Adapter。精确 Windows／Codex／Adapter／Core／CLI／模型范围已覆盖
显式与隐式调用、缺失与不兼容失败关闭、旧 Skill 显式升级、完整备份、可恢复卸载、重新发现和作者
文件保留，因此只有该范围改为 `verified`。证据见
[Codex Runtime E2E 完成](../../validation/2026-08-21-codex-runtime-e2e-completion.md)；此前的
[安全停止](../../validation/2026-08-21-codex-runtime-e2e.md)继续保存首次发现同名污染的历史。
独立 CLI 发行物和 Adapter 仍未发布；本结论不启动 Phase 3。

验收证据：Codex Adapter 独立归档、checksum、实际 runtime Validation 和旧 Skill 升级路径。

回滚边界：可回退到兼容 Skill 归档；Core、CLI 和目标项目作者文档不回滚。

## Phase 3：不依赖 Codex 的 Harness／CLI 样例

- [x] 为 scaffold dry-run、validate 和 update checker 建立统一 JSON schema 与稳定退出码。
- [x] 实现最小 `harness-json` 参考 Adapter，使用 subprocess 或公共 Python API 调用 CLI。
- [x] 测试环境显式排除 `SKILL.md`、Codex 配置和真实 Agent runtime。
- [x] 覆盖成功、mixed toolchain、schema 不兼容、离线更新和目标文件保留路径。
- [x] 明确测试只证明 Core／CLI／Harness 合约，不证明模型读取或第三方平台兼容。

Phase 3 仓库实现检查点已在候选分支完成：CLI 0.1.1 为三个命令提供 opt-in response envelope，
JSON 模式使用稳定退出码 0／2／3／4／5／6／7；`adapters/harness-json/` 0.1.0 只接受白名单请求，
清理 Agent／Provider 环境变量，并直接启动 Python CLI subprocess。分支已 push；首轮 CI 暴露并修复
了 Linux 命令夹具错误，第二轮保留了无关 Windows 本机 HTTP 超时的失败证据，第三轮在同一提交
取得 Windows／Ubuntu 双 PASS。Phase 3 实现与跨 OS 验收已完成；Harness Adapter 发行状态仍是
`experimental`／`unreleased`，且不构成第三方 Agent runtime 兼容。Phase 4 仍需另行选择平台与计划。
证据见
[Phase 3 Harness JSON](../../validation/2026-08-21-platform-neutral-phase-3-harness-json.md)。

验收证据：机器可读 fixture、JSON schema 测试、跨 Windows／Ubuntu CLI CI。

回滚边界：JSON 保持 opt-in；既有人类输出和旧入口继续可用。

## Phase 4：Claude Code 与 DeepSeek Harness 真实适配

ADR-0013 已选择两个独立平台范围；任何一项完成都不能自动提升另一项。

### Phase 4A：Claude Code Plugin Adapter

- [x] 依据官方 Plugin／Skill／CLI 文档确认发现、隔离 home、marketplace 和生命周期边界。
- [x] 建立 `adapters/claude-code/` 薄 Plugin、manifest、CLI 失败关闭和确定性归档。
- [x] 使用本机精确 Claude Code runtime 在隔离 `CLAUDE_CONFIG_DIR` 中完成无模型 validate、发现、安装、
  更新、卸载和作者文件保留。
- [x] 经单独授权启动最少显式／隐式候选 turn；真实 runtime init 均发现 Plugin／Skill，但本机无登录态，
  在模型请求前以 `authentication_failed` 停止，0 token／0 cost。
- [ ] 经单独授权后，以最少真实 turn 验证显式／隐式调用和失败路径。
- [ ] 只有完整 runtime 证据门通过后，才把精确范围标为 `verified`。

### Phase 4B：DeepSeek Harness Profile Plugin Adapter

- [x] 依据官方架构、CLI、Skill registry 和 Plugin Bundle 文档确认扩展面与 profile 生命周期。
- [x] 建立 `adapters/deepseek-harness/` Bundle、packaged Skill、manifest、CLI 失败关闭和确定性 npm 产物。
- [x] 在 D 盘隔离 `DSH_HOME`／profile 中安装精确 developer-preview runtime，不读取或复制真实凭据；完成
  bundle composition、真实无模型 Skill discovery、更新、移除和作者文件保留。
- [x] 经单独授权启动最少 headless turn；显式 `/project-orrery` 已在真实 session 形成
  `skill-catalog`／`skill-invocation`，隐式候选形成 catalog，但两者因无 API Key 在模型请求处失败。
- [x] 经单独授权后，以最少 headless turn 验证显式／隐式调用和 CLI 缺失／不兼容失败路径；普通 wheel
  的 source-assets 定位失败随后已修复，并以非 editable wheel 真实复验通过。
- [ ] 只有完整 runtime 证据门通过后，才把精确范围标为 `verified`。

Stage A 只允许隔离目录、无真实 API Key、无模型调用；Stage B 写真实用户目录、使用真实登录态或发起
模型 turn 前必须在当前对话取得明确确认。

Phase 4A／4B 的 Stage A 已完成。Claude Code 2.1.87 通过官方 manifest validate、隔离
0.0.9→0.1.0 update、卸载后空安装列表与可恢复 cache；DeepSeek Harness 0.1.0-rc.8 在隔离
`DSH_HOME`／`DSH_AGENTS_HOME` 中通过真实 `ctx.skills` 唯一发现、body load、升级和移除后 0 项。
两者均为 0 模型调用，故 `verified` 数组保持为空。证据见
[Claude Code Stage A](../../validation/2026-08-21-claude-code-adapter-stage-a.md)与
[DeepSeek Harness Stage A](../../validation/2026-08-21-deepseek-harness-adapter-stage-a.md)。

Stage B 已获明确授权并执行安全的最少候选 turn。Claude Code 的真实 init 发现 inline Plugin、Skill 与
slash command，但本机 `loggedIn=false`；DeepSeek Harness 的真实 headless session 已形成 catalog 和
显式 Skill 注入，但本机没有 `DEEPSEEK_API_KEY`。两平台都在首个成功模型响应前失败，CLI 也未被模型
路由，故上方真实调用项仍未完成。证据见
[Claude Code Stage B 认证阻塞](../../validation/2026-08-21-claude-code-adapter-stage-b-auth-blocked.md)与
[DeepSeek Harness Stage B 凭据阻塞](../../validation/2026-08-21-deepseek-harness-adapter-stage-b-credential-blocked.md)。

2026-08-22 在用户配置真实 DeepSeek credential 后，DSH rc.8／`deepseek-official`／
`deepseek-v4-flash` 已完成显式 Skill 注入、隐式 `skill` tool load、editable CLI preflight／validate、CLI
distribution 缺失 exit 3、0.2.0 不兼容 exit 4，以及模型调用后的 remove／restore／final remove。普通 wheel
CLI 0.1.1 的 preflight 虽通过，`validate` 却在 target 检查前因找不到 source repository Observatory assets
崩溃；因此 verified 清单仍未完成。见
[DeepSeek Harness Stage B Runtime](../../validation/2026-08-22-deepseek-harness-adapter-stage-b-runtime.md)。

后续 wheel 修复让 Observatory build 从固定 component manifest 将九个 managed assets 嵌入 wheel，CLI
context 优先使用 `site-packages` assets、source checkout 才回退 monorepo。全新 wheel venv 的 scaffold／
validate 与真实 DeepSeek 显式 Adapter route 均 exit 0；原 wheel blocker 已关闭。证据见
[CLI Wheel Observatory Assets](../../validation/2026-08-22-cli-wheel-observatory-assets.md)。

验收证据：两个平台各自的 manifest、专项测试和独立 Validation。

回滚边界：任一 Adapter 可独立下架；Core／CLI 和其他 Adapter 不受影响。

## 预计实现目标

- `packages/project-orrery-core/**`
- `packages/project-orrery-cli/**`
- `packages/project-orrery-observatory/**`
- `adapters/codex/**`
- `adapters/claude-code/**`
- `adapters/deepseek-harness/**`
- `adapters/harness-json/**`
- `skills/project-orrery/**` 兼容 wrapper 与迁移入口
- `scripts/package_release.py`, `.github/workflows/**`
- `tests/test_project_orrery.py` 及新增 Core／CLI／Adapter 测试
- `README.md`, `README.zh-CN.md`, `docs/state/**`, `docs/validation/**`

实际目录可在 Phase 0 后按 Python packaging 约束细化，但不得改变 ADR-0004 的 canonical 模板、
薄 Adapter、独立版本和真实 runtime 验证边界。

## 完成条件

1. Core／CLI 可以在没有 Codex 文件和 runtime 的环境中安装、预演和验证目标项目。
2. Codex 产物只包含平台薄层与明确依赖，不再是通用能力的唯一物理边界。
3. v0.2.0 既有路径有可测试的兼容／迁移入口，作者文档未被批量覆盖。
4. manifest 能分别表达 Core、CLI、Observatory、Adapter 和 runtime 支持状态。
5. `verified` 条目全部链接真实 runtime Validation；未验证平台保持 `target` 或 `experimental`。
6. State、PROGRESS、DEVLOG、HANDOFF 与公开 README 准确区分 accepted、implemented、committed
   和 released。

各阶段完成结果由独立 Validation 接管；本计划清单本身不构成实现或兼容性证据。
