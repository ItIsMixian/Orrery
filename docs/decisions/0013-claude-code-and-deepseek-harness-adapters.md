# ADR-0013：选择 Claude Code 与 DeepSeek Harness 作为下一批平台 Adapter

Status: Accepted
Date: 2026-08-21
Amends: [ADR-0004](0004-platform-neutral-core-and-adapter-boundaries.md)

## Context

ADR-0004 建立了平台中立 Core／CLI／Adapter 边界，但有意没有选择第二个平台。Phase 0–3 已完成，
Codex 有一个精确 runtime 范围的 E2E 证据，Harness JSON 只证明 subprocess JSON 合约。项目现在需要
至少覆盖 Claude Code 和 DeepSeek Harness，且不能把参考 Harness、仓库单元测试或一个平台的证据
外推为另一个平台的兼容性。

官方扩展面不同：Claude Code 使用 Plugin 与其中的 Skill；DeepSeek Harness 使用 profile 中按顺序
组合的 Cordis Plugin Bundle，并可由插件注册 packaged Skill。两者都能保持薄入口、调用同一
`project-orrery` CLI，并在隔离 home／profile 中验证，而不复制 Core 模板或项目事实。

## Decision

1. ADR-0004 Phase 4 选择两个独立目标：Claude Code 和 DeepSeek Harness；顺序上先实现本机已有的
   Claude Code，再实现仍处于 developer preview 的 DeepSeek Harness。
2. Claude Code Adapter 是官方 Plugin：`.claude-plugin/plugin.json` 负责插件身份，
   `skills/project-orrery/SKILL.md` 负责发现与调用。开发验证优先使用 `--plugin-dir`；持久生命周期
   只通过隔离 `CLAUDE_CONFIG_DIR` 中的官方 marketplace／plugin 命令验证。
3. DeepSeek Harness Adapter 是 profile Plugin Bundle：`package.json` 声明 `dsh.bundle.patch`，
   `cordis.patch.yml` 挂载插件，插件向 `ctx.skills` 注册 packaged `project-orrery` Skill。安装、更新和
   移除使用隔离 `DSH_HOME` profile 下的 `dsh plugin` 命令。
4. 两个 Adapter 都只携带平台发现元数据、调用指令、CLI 依赖预检和自身 manifest；不得复制
   canonical 作者模板、schema、迁移规则、State 或 Validation 内容。
5. 两个平台分别从 `experimental` 开始，分别记录 Adapter、runtime、OS、Core／CLI、权限和模型范围。
   Claude Code、DeepSeek Harness 与 Codex 的 runtime evidence 互不继承。
6. 无模型 Stage A 必须覆盖确定性产物、结构验证、隔离安装／升级／卸载、CLI 缺失与不兼容失败关闭、
   backup／cache／profile 不污染作者项目。真实登录态、用户目录或模型 turn 属于 Stage B，必须另获
   明确授权。
7. DeepSeek Harness developer preview 的破坏性变化风险通过精确 runtime 版本门和失败关闭处理；
   在完整真实调用证据门通过前保持 `experimental`。

## Reasons

- Claude Code Plugin 和 DeepSeek profile Bundle 都是宿主官方支持的扩展面，不需要把临时文件复制成
  “伪 runtime 集成”。
- 独立 home／profile 允许先完成无凭据生命周期验证，并把模型调用与安装状态变化显式分开。
- packaged Skill 让 DeepSeek Adapter 能随 plugin 生命周期安装和移除，避免依赖散落的用户 Skill 文件。
- 两个平台共享 CLI 合约而不共享 runtime 结论，符合 ADR-0004 的证据粒度。

## Consequences

- 仓库增加 `adapters/claude-code/`、`adapters/deepseek-harness/`、各自打包器、专项测试和 Validation。
- Claude Code 的正式安装还需要 marketplace 分发面；DeepSeek Harness 的正式安装还需要可发布 npm
  产物。仓库内可安装实现不等于已发布。
- 在 Stage B 完成前，可以宣称 Adapter 已实现并通过隔离生命周期验证，但不能宣称真实模型调用已验证。
- 本决定不修改 Core／CLI API、不选择第三个平台、不改变多人协作或 Authority Meta Model。

## Implementation and validation mapping

- Approved Design: [平台中立 Core 与 Adapter 架构](../design/platform-neutral-core-and-adapter-architecture.md)
- Implementation Plan: [平台中立 Core 与 Agent／Harness Adapter](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)
- State Docs: [发布与工具链](../state/release-and-toolchain.md)、[测试覆盖](../state/test-coverage.md)、[项目结构](../state/project-structure.md)
- Validation: 各平台 Stage A／Stage B 分别建立独立记录
