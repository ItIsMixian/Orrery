# 平台中立 Core 与 Agent／Harness Adapter 架构

Status: Approved
Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
Updated: 2026-08-21

## 目标与当前基线

目标是让 Project Orrery 的发布结构与平台中立定位一致，同时保留一套文档事实、canonical
模板和非破坏式迁移契约。

公开 v0.2.0 基线仍是：`skills/project-orrery/` 同时包含 Codex 入口、Python 工具、模板、
观测台和 release manifest，正式发布资产只有 Codex Skill。当前工作树已实现下述 Core／CLI／
Observatory 源码边界和 Codex Adapter，尚未实现 Harness Adapter、独立组件发行物或多组件发布；
因此目录图同时包含已实现与后续目标，精确当前事实以 State Docs 为准。

ADR-0009 已接受 Authority Meta Model 与 conformance 边界，但 AUTH-4“Core 是唯一 semantics implementation owner”仍未决定。当前表格中的 “Core 持有权威角色、schema” 继续表达 ADR-0004 的平台中立存储／合约边界，不应被扩读为 Meta Model API、parser ownership 或单一实现已经完成。

## 组件职责

| 组件 | 拥有 | 不拥有 |
|---|---|---|
| Core | 权威角色、schema、manifest 数据模型、迁移判定、非覆盖不变量、canonical 作者文档模板 | 平台目录、prompt 格式、审批 API、宿主安装 |
| CLI | `audit`、`scaffold`、`validate`、`check-update` 的人类与 JSON 接口 | 平台兼容性猜测、第二套迁移规则 |
| Observatory | 静态／动态派生阅读、搜索、健康信号和可选 AI | 项目事实和决策权 |
| Agent Adapter | 指令发现、调用提示、用户确认语义和平台 manifest | Core 模板、项目 State、通用安装逻辑 |
| Harness Adapter | 结构化请求／响应、稳定退出码、超时／取消和证据边界 | Agent 自述升级为独立审计证据 |
| 平台安装器 | Adapter 自身的安装、升级、备份和卸载 | 目标项目作者文档和 Observatory managed tools |
| 兼容性服务 | 组件范围、runtime 范围、支持状态与 Validation 引用 | 用单一版本号推断整体已升级 |

## 目标仓库结构

```text
packages/
  project-orrery-core/
    schema/
    templates/authority/
    migrations/
  project-orrery-cli/
  project-orrery-observatory/
adapters/
  codex/
  claude-code/
  deepseek-harness/
  harness-json/
packaging/
docs/
```

目录名可在实现计划中按 Python packaging 约束微调，但以下边界不可改变：

- canonical 作者文档模板只有一份；
- Observatory managed tools 与作者文档模板分别清点和升级；
- Adapter 只依赖 Core／CLI 公共合约；
- `docs/` 继续是 Project Orrery 自身唯一权威文档根。

## Agent 入口模型

`AGENTS.md` 是平台中立的 canonical Agent 入口，并继续承载当前仓库的读取顺序、硬边界和
`What / Truth / Dig` 路由。发布模板中的 “Codex state index” 命名在实施时改为中立名称。

若平台使用其他发现文件，Adapter 可创建薄入口，例如只包含：

1. 先读取根 `AGENTS.md`；
2. 遵守其权威链和本地边界；
3. 通过平台 Adapter 规定的方式调用 Orrery CLI。

薄入口不得复制项目当前状态、活动计划、ADR 内容或验证结论。既有同名作者文件默认不覆盖；
平台安装器必须先预演并由用户确认合并方式。

## Phase 4 平台映射

ADR-0013 将下一批真实平台固定为两个互相独立的 Adapter：

| 平台 | 官方扩展面 | 隔离 discovery／生命周期边界 | 分发前提 |
|---|---|---|---|
| Claude Code | Plugin 中的 `skills/project-orrery/SKILL.md` | 临时 `--plugin-dir`；持久测试使用独立 `CLAUDE_CONFIG_DIR` 与本地 marketplace | Claude marketplace 条目或等价受信分发源 |
| DeepSeek Harness | profile Plugin Bundle 注册 packaged Skill | 独立 `DSH_HOME`、专用 profile 与 `dsh plugin` | 可安装 npm／本地 package，且 runtime 版本满足 manifest |

Claude Plugin 使用宿主原生 install／update／uninstall；DeepSeek Bundle 使用 pnpm-backed
`dsh plugin add/update/remove`。Adapter 自身的备份、缓存和 profile 状态必须留在隔离宿主根，不能进入
目标项目或被当作作者文档。两者在真实模型调用前都必须先证明 CLI 依赖缺失／不兼容时失败关闭。

## CLI 与 Harness 合约

CLI 保留可读文本输出，并为自动化提供 opt-in JSON。机器合约至少包括：

- `schema_version`、命令名和 Core／CLI 版本；
- 统一结果类别、稳定退出码、warning 与 error code；
- dry-run 的 `create`、`keep`、`skip`、`upgrade`、`backup` 动作；
- target manifest、document schema、toolchain 和迁移要求；
- 不在错误字符串中泄露凭据、绝对缓存位置或无关环境状态。

参考 Harness 必须能在完全不加载 `SKILL.md`、Codex 配置或 Codex runtime 的测试环境中完成
scaffold dry-run、安装到临时目录、validate、兼容性失败分类和清理。该样例证明 CLI／Harness
边界，不证明任何第三方 Agent 平台兼容。

## 组件与兼容性版本

兼容 manifest 的下一格式至少表达：

| 维度 | 含义 |
|---|---|
| `document_schema` | Seed、ADR、Design、Plan、State、Validation 等作者文档职责 |
| `project_manifest_format` | `.project-orrery.json` 的机器可读格式 |
| `core_api_version` | CLI、Observatory 和 Adapter 可依赖的 Core 接口 |
| `cli_version` | 命令、JSON schema 和退出码实现 |
| `observatory_version` | 目标项目内 managed viewer 工具版本 |
| `adapter_version` | 单个平台 Adapter 的实现版本 |
| runtime compatibility | 平台名、实际测试版本、OS、范围策略和验证日期 |

现有 `installed_skill_version` 和 v1 release manifest 在迁移期继续可读。新字段不能被回填为
已经验证的事实；未知 runtime 必须是 `target` 或 `experimental`，不能默认为 `verified`。

## 支持状态与验证门

### verified

必须有真实 runtime 的版本化 Validation，覆盖：发现 Adapter、读取 canonical 入口、调用
CLI、dry-run、错误路径、更新／卸载，以及未覆盖作者文档。状态绑定具体 Adapter 版本、runtime
版本和 OS；超出已声明范围时不得外推。

### experimental

已有可安装 Adapter，且至少有可重复 smoke test；但真实 runtime 版本、权限模式、更新或
跨 OS 矩阵仍不完整。安装入口必须显式展示实验状态。

### target

只存在方向、issue 或设计占位。没有正式安装产物，不显示兼容徽章，不写“支持”。

## 安装和更新边界

更新顺序保持分离：

1. 获取并验证目标版本的 Core／CLI 或 Adapter 产物；
2. 平台安装器预演 Adapter 自身的安装／升级；
3. CLI 单独预演目标项目 scaffold 或 managed tools 升级；
4. 作者文档 schema 变化通过项目级迁移计划处理，永不批量覆盖。

初期使用同一 Git tag 协调组件发布，但每个产物保留自己的版本和兼容范围。发布流水线必须能
单独验证 Core、CLI、Observatory 和 Codex Adapter 内容，且不能把实验 Adapter 混入稳定产物。

## 迁移与回滚

- 先建立现有行为的 golden tests，再抽取 Core；旧脚本路径保留兼容 shim。
- 先新增 JSON 合约，不删除现有人类输出。
- Codex Adapter 只有在新产物通过实际 runtime 验证后才接管参考集成身份。
- 任一 Adapter 可独立下架或回滚，不要求回滚 Core 或改写目标项目文档。
- v0.2.0 归档和 checksum 保持不可变；迁移只影响后续版本。

## 非目标

- 除 ADR-0013 已选择的 Claude Code 与 DeepSeek Harness 外，本设计不选择其他 Agent 平台。
- 不实现或推广 Pilot 001–008 的上下文路由候选。
- 不解决多人／多 worktree 状态合并。
- 不改变 docsite 凭据、Broker 或 Provider 安全设计。
- 不承诺跨 Windows／Linux byte-for-byte 可重复归档；该问题继续单独处理。
