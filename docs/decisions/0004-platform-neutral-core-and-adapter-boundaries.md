# ADR-0004：平台中立 Core 与 Agent／Harness Adapter 边界

Status: Accepted
Date: 2026-08-19
Amends: [ADR-0001](0001-project-orrery-self-hosting.md)

## Context

Project Orrery 的权威模型、Markdown 文档结构、Python 安装／验证脚本和本地观测台大部分不依赖
特定 Agent 平台，但 v0.2.0 的唯一正式发布单元仍是 `skills/project-orrery/` 下的 Codex
Skill。Core、CLI、模板、观测台、版本 manifest 和 Codex 入口目前被同一个归档一起发布。

这意味着 README 中的平台中立定位已经描述了产品本体和方向，却尚未形成可独立维护、安装、
版本化和验证的 Core／Adapter 产品边界。能够从其他 Harness 调用 Python 文件，也不等于已经
实现或验证对应平台集成。

需要在不复制 Seed、ADR、State、Validation 或模板事实的前提下，确定长期目录、发布、兼容性
和验证模型，并保留 v0.2.0 的非破坏式升级路径。

## Decision

1. 采用**单仓库、分包**结构。Project Orrery Core、CLI、Observatory、Agent Adapter、
   Harness Adapter 和平台安装器属于同一仓库内的独立职责与发布组件。
2. Core 保存平台中立的权威角色、schema、迁移规则、非覆盖不变量和 canonical 文档模板；
   Adapter 不得复制或派生第二套项目事实。
3. 根 `AGENTS.md` 继续作为平台中立的 canonical Agent 入口。平台若需要其他发现文件，
   对应 Adapter 只能生成指向 `AGENTS.md` 的薄入口，不得复制 Seed、ADR、State、Validation
   或项目状态摘要。
4. CLI 负责把 Core 暴露为可审计命令，并逐步提供稳定退出码和机器可读 JSON。Harness
   Adapter 通过该合约调用 Core／CLI，不解析易变的人类输出，也不把 Agent 自述当成独立证据。
5. 现有 Codex Skill 改造成参考 Agent Adapter。迁移期间保留旧 Skill 路径和兼容 shim；
   v0.2.0 已发布资产、checksum 和既有安装事实不回写。
6. Core、CLI、Observatory 和 Adapter 分别版本化；初期仍由同一仓库 tag 协调发布多个产物。
   同一 tag 不得被解释为所有目标项目、managed tools 或作者文档已经同步升级。
7. 兼容性至少分别表达：文档 schema、项目 manifest 格式、Core／Adapter API、CLI／Observatory
   版本、Adapter 版本以及目标 Agent／Harness runtime 版本。
8. 平台支持状态只允许使用：
   - `verified`：真实目标 runtime 的端到端发现、调用、失败路径和更新验证已有版本化证据；
   - `experimental`：已有可安装实现和有限验证，但运行时矩阵或生命周期尚不完整；
   - `target`：只有方向或设计，不构成兼容性声明。
9. Claude Code、Cursor、Gemini CLI 或其他第二平台不在本 ADR 中被选择，也不得因本 ADR 被宣称
   兼容。第二平台必须在可访问真实 runtime、安装边界和验证 Harness 后单独实施。
10. 平台 Adapter 安装器只管理宿主平台自身的 Adapter 文件和配置。目标项目的 scaffold、
    managed tools 升级和作者文档迁移仍是三个独立动作，并继续遵守 dry-run、白名单和备份契约。

## Reasons

- 单仓库能够复用一套 Core、模板和测试，比分仓更不容易产生事实漂移。
- 分包能让平台特定发现、权限和安装逻辑独立演进，避免继续把全部通用能力等同于 Codex Skill。
- 保留 `AGENTS.md` 作为 canonical 入口，可以支持不同平台的薄路由文件而不制造平行状态摘要。
- 真实 runtime 证据门能够区分“脚本可执行”“Adapter 已实现”和“平台兼容已验证”。
- 兼容 shim 和协调 tag 允许逐步迁移，而不要求一次性破坏 v0.2.0 安装路径。

## Consequences

- ADR-0001 对当前仓库事实和自托管边界仍然有效；其“`skills/project-orrery/` 是发布产品源”
  将在本 ADR 的 Implementation Plan 完成后演化为多组件发布结构。在此之前，当前 State 仍必须
  报告唯一发布源是现有 Skill。
- 后续 manifest 需要增加组件、Adapter API、runtime 和支持证据维度；这属于显式迁移，不能
  通过 README 或字段重命名暗中完成。
- CLI 的人类输出可以保留，但 Harness 自动化必须使用稳定 JSON／退出码合约。
- 每个 Adapter 都需要独立安装、卸载、兼容性和真实 runtime 验证；Adapter 数量增加会带来
  可见的测试矩阵成本。
- 在第二平台被真实实现和验证前，公开文档只能称其为 `target`。

## Implementation and validation mapping

- Approved Design: [平台中立 Core 与 Adapter 架构](../design/platform-neutral-core-and-adapter-architecture.md)
- Implementation Plan: [2026-08-19 平台中立 Core 与 Adapter](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)
- State Docs: [项目结构](../state/project-structure.md)、[发布与工具链](../state/release-and-toolchain.md)、[文档系统](../state/documentation-system.md)、[测试覆盖](../state/test-coverage.md)
- Validation: [平台中立 Core 与 Adapter 架构采纳](../validation/2026-08-19-platform-neutral-core-and-adapter-architecture.md)；各实现阶段完成后另写独立 Validation
