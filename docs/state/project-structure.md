# 项目结构 State

Updated: 2026-08-23
Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md), [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)

## 当前事实

- 单一 Git 仓库根：`D:\coding warehouse\project-orrery`。
- 并发协作当前人工采用“一个 Workstream = 一个分支 + 一个独立 linked worktree 或 clone”；一个平台会话可以在该 Workstream 中完成多个相关 Change Set。主 worktree 只供维护者集成。2026-08-20 已用独立 integration worktree 恢复并拆分三个共享工作目录任务，随后为 context-routing、platform／adapters 和 docsite／broker 分配三个干净 linked worktree，证明人工隔离与干净集成路径可行。
- 已发布 v0.2.0 产品源仍是 `skills/project-orrery/`；当前工作树包含未发布的 `packages/project-orrery-{core,cli,observatory}/` 源码边界、`adapters/codex/` 薄平台 Adapter，以及候选 `adapters/harness-json/` subprocess JSON 参考 Adapter。
- Core 持有 schema、manifest／兼容判定和 canonical 作者模板；CLI 组合 Core 与 Observatory；Observatory 持有 managed-tool 清单与模板投影规则。
- 项目文档权威根：`AGENTS.md` 与 `docs/`。
- `docs/state/authority-meta-model.md` 现作为 authority-semantics 子系统事实地图；它只报告规范与实现缺口，不是新的作者文档角色或机器 Meta Model 实现。
- 自托管观测台：根 `scripts/docsite/` 与 `start-docsite.bat`。
- 非权威研究控制面：`experiments/context-routing/`。
- 本地大型原始运行根：`D:\coding warehouse\project-orrery-benchmark`，不属于 Git 仓库。
- 原始运行由仓库内 `experiments/context-routing/harness/raw-evidence-retention-policy.json` 与 `seal_raw_evidence.py` 管理 manifest、校验和、分类和到期状态；工具不自动删除。
- 发布打包与 CI：旧 Skill 使用 `scripts/package_release.py`；未发布 Codex Adapter 使用 `scripts/package_codex_adapter.py`；现有 `.github/workflows/` 尚未发布多组件产物。
- self-host GitHub 的 main 推广采用 Candidate-first：exact SHA 必须先在非 main 分支通过 Windows／Ubuntu smoke checks，随后才允许快进 main。服务端 branch protection 对管理员生效，不要求 PR；workflow 排除普通 main push，避免同一 SHA 重复矩阵。该外部规则不是通用 Orrery 产品能力。
- Codex Adapter 当前源码版本为 0.1.1，发行支持状态仍为 `experimental`／未发布；其 runtime manifest 中的历史证据只对 Adapter 0.1.0、Windows 11 build 26200、Codex Desktop 26.818.2441.0／`codex-cli 0.148.0-alpha.21`、Core／CLI 0.1.0 与已记录模型／审批组合标记 `verified`，不自动覆盖 0.1.1。
- 最终候选将未发布 Core／CLI／Observatory 推进到 0.1.8／0.1.13／0.1.2：W1–W3 提供 Personal Scope/review/cleanup，W4 提供只读 Personal 指挥台，W5A 增加 Git-private Team 身份、严格 metadata envelope、event outbox、Member → Workstream 只读聚合、request-only 本机确认和显式启动的 loopback／LAN Coordinator foundation。Core API 仍为 1；只有 containing ref 为 main 时才是 Canonical，公开 v0.2.0 不变。
- `adapters/claude-code/` 与 `adapters/deepseek-harness/` 当前源码版本为 0.1.1、`experimental`／未发布的薄平台 Adapter；两者均只依赖平台中立 CLI，不拥有项目作者文档。现有真实 runtime evidence 仍精确绑定 Adapter 0.1.0：Claude Code 只证明 Plugin／Skill 发现后在认证前失败关闭；DeepSeek Harness 只有 manifest 所列 rc.8／Windows／Core 0.1.0／CLI 0.1.1 wheel／模型与生命周期范围为 `verified`。

## 当前边界

- canonical 作者模板位于 Core 包；`skills/project-orrery/assets/project-template/` 是 v0.2 兼容投影，并由测试要求与 canonical 内容一致。
- Observatory 实现源码仍位于根 `scripts/docsite/`，组件包负责清点与版本化；Skill 模板通过显式标题 token 投影保持目标项目可定制。
- 旧 Skill 三个脚本路径现在是薄 wrapper；源码仓库调用新 CLI，单独分发 Skill 时回退到冻结的 v0.2 兼容实现。wrapper 保留至 `0.3.x`，最早在 `0.4.0` 移除。
- `adapters/codex/` 只包含 Codex 发现／调用元数据和 Adapter 生命周期安装器；它通过 manifest 引用 Core／CLI，不复制 canonical 作者模板、schema、兼容规则或项目状态。平台安装器只管理目标 skills 根下的 `project-orrery` Adapter 目录。
- `adapters/harness-json/` 不包含 `SKILL.md` 或平台发现文件；它拥有 versioned request／response schema、参数白名单、subprocess 边界和 timeout 分类，只调用 CLI 的 opt-in JSON，不读取作者文档来重新判定事实。
- `adapters/claude-code/` 使用原生 Plugin discovery；`adapters/deepseek-harness/` 使用 profile Cordis Plugin Bundle。两者有独立 manifest、打包器、生命周期和 runtime evidence，不共享对第三方平台兼容性的推断。
- `docs/_site/`、缓存、凭据和 benchmark 原始输出不是作者文档或发布资产。
- 自托管、实验和测试资产已进入 `main`；v0.2.0 tag／Release 指向发布提交 `20fc95b`，后续当前事实由 main 上的发布后文档继续维护。
- linked worktree 共享 Git 对象库和普通 refs，但拥有独立 HEAD、索引与工作目录。未提交文件仍只属于所在 Worktree scope。W5A Candidate 只有用户本机显式 enable 后才能启动 Coordinator；中央只接受标注为 Local-only 的版本化元数据，不接收源码正文或未 push diff，也不把 telemetry 升级为代码证据。未启用、未分享、过期或证据不足继续投影 Unknown／Unavailable。
- Phase 0 配置固定在 `.project-orrery.json` 的 `collaboration.integration_ref`、`collaboration.primary_worktree` 和 `collaboration.project_mode`；integration ref 缺省为 `refs/heads/main`，只按本地 branch ref 解析精确 commit OID，不 fetch 或回退远端。主 worktree 缺省取 `git worktree list --porcelain` 的 main worktree，维护者覆盖必须是同一仓库已列出的绝对 worktree 路径。
- worktree 路径比较先收敛现有路径的真实绝对形式，再应用平台大小写规则；这让 Windows runner 的 8.3／长路径别名指向同一已列出 worktree，同时不允许不存在或跨仓库的 override 绕过检查。
- Phase 1 通过 `git rev-parse --git-path orrery/worktree.json` 定位每个 linked worktree／clone 的 Git 私有 session；原子写入不改变作者工作树。session 绑定 worktree ID、branch、HEAD、integration ref／OID、merge base 和 dirty fingerprint；只读 status 在绑定事实漂移后报告稳定 stale reason，不自动重写。
- `worktree create` 固定本地 integration OID 后建立 branch + linked worktree 与 `created` session；branch／path 碰撞预先拒绝，session failure／integration drift 只回滚本操作创建的 clean 对象。`worktree guard` 允许隔离 worktree，并对 clean／dirty primary 失败关闭且不自动迁移。
- lifecycle phase、runtime condition、evidence freshness 与 closure reason 独立保存；Git／review evidence 漂移会撤销有效 Review Ready。W3 Candidate 的 review／closure 操作会在关键绑定漂移时失败关闭，并只更新 Git-private session；它不自动把 Candidate 合入 main。
- Adapter capability contract 分离 launch／attach／rebind／message。Codex、Claude、DeepSeek 当前只声明 caller-provided attach，Harness JSON 全关闭；Adapter Skill 要求先走 route/guard，但不能拦截绕过 Adapter 的任意宿主写入，也不证明 platform runtime launch／rebind 支持。
- 根 `AGENTS.md` 的七个 subsystem 入口已有显式稳定 ID；Core registry 只投影这些入口链接的既有 State Docs，缺失 State 时失败关闭，`unmapped` 与 `project-wide` 只是 Scope 保留表达，不自动创建作者文档。
- W2 从 merge base→HEAD、staged、unstaged、untracked 与 session expected writes 生成同一 `scope-observation`，每条路径保留来源；registry 从 `AGENTS.md` Truth 路径与 authority links 派生 subsystem mapping。无法映射的路径保持 `Unmapped`，共享 subsystem 只提高 Semantic 优先级。
- Direct／Authority／Semantic／Unknown finding 与 Open／Acknowledged／Resolved／Stale 生命周期存放于 Git-private session。fingerprint 绑定 Scope revision、HEAD、integration OID、路径、验证面和对端；跨成员 L2 保存 required members 与逐成员确认，整体 `n/m` 未完成时阻止 Review Ready。
- Personal Mode 的 W2 collector、overlap、scope refresh 与 acknowledgement 都只执行本地 Git／文件系统操作；没有新增 listener、discovery、Coordinator、heartbeat 或 Team transport。凭据、release、schema migration 的默认独占路径可由项目配置收紧／替换，Direct／L3 以及未本机确认的 L2 已接入 Adapter route 并失败关闭。
- W3 Candidate 的 `integrate --dry-run` 固定 target OID 与 candidate HEAD，在新建、干净、一次性 integration worktree 中执行 merge／rebase 推测和声明验证；无论成功、冲突或验证失败都不更新 target ref，并核对作者 worktree 的 HEAD／status 前后不变。只有该工具创建的临时 worktree 会在运行后移除。
- review package 与 decision 保存在 common Git private `orrery/reviews/`，closure record 保存在 `orrery/closures/`。package 绑定 target OID、candidate HEAD、Scope revision/fingerprint、finding set、collaboration schema version/byte hash、validation set 与内容 hash；原始证据／结构化事实先于可选 AI 派生摘要，摘要没有 Authority。Approve／Request Changes／Hold／Reject 明确记录人类 actor、capability、reason、evidence、timestamp 与失效条件，AI actor 永不计入人审。
- integration eligibility 只计算当前 package、验证、风险策略和人类 decision 是否满足。workspace inventory 只枚举 Git 已登记 worktree、Git-private session／closure、`.project-orrery.json` 可选允许根与用户显式候选，不扫描磁盘或同前缀目录；输出七类分类、Unknown、保护原因和预计空间。无 session／closure 的历史 worktree／clone 维持 Legacy unmanaged／Unknown，未显式 adopt/classify 前只报告。
- cleanup eligibility 对选中目录验证允许根内的真实绝对路径、symlink/reparse escape、Git identity/common-dir、非 active、clean、未知 untracked／ignored、独有 commit、canonical ancestry／closure reason、review／Validation／closure 与新鲜 target OID。benchmark/raw evidence、recovery/immutable 与 credential/cache 通过显式策略或 Unknown fail-closed 保留；不按名称或时间自动删除。remove worktree、delete local branch、delete remote branch 与 remove ordinary directory 是四个独立授权，全部 `performed: false`；显式 Git-private action receipt 只记录调用者自述的外部动作。现有本机目录没有被本 Candidate 自动审计为可删。
- W4 Worktree Candidate 的 root-only `build_personal_observatory.py` 与 Observatory 内部 Personal projection 逐 worktree 调用 W1/W2 status／Scope／finding／lifecycle Core 合约，并正式消费 Canonical W3 的 review package freshness、risk、人类 approval、integration eligibility、bounded workspace inventory、cleanup eligibility、closure 与 action receipt bundle。W4 不复制这些判定：review／integration 只调用 W3 Core，inventory 七类、protection、Unknown 与预计空间来自 W3 bundle，只有 Core 标为 `evaluate-cleanup-eligibility` 的条目才继续调用 cleanup gate；四个 action 始终分别投影且自动采集保持 `authorized=false`、`performed=false`、`implies_actions=[]`。receipt 只显示 caller-attested evidence，不能证明删除已发生。
- W3 provider 缺失、失败或 schema 不兼容时，W4 整体页面仍保留 W1/W2 的 W4A 投影，W3 区域单独退回 Unavailable／Unknown；它不从目录名、前缀、年龄或页面状态自行推断 review、integration 或 cleanup 结论。
- 该 W4 Candidate 只生成显式 opt-in 的本地 HTML／可选 JSON 快照；默认 `build_docsite.py`、现有 loopback service、Authority projection、AI Q&A、发布模板与 v0.2.0 行为均未切换。投影声明 `read_only=true`、`writes_performed=false`、`network_performed=false`、`team_runtime_enabled=false`，没有 LAN／Coordinator／Member 同步或页面执行动作。

## 实现证据

- `.project-orrery.json`
- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`
- `.github/workflows/validate.yml`, `.github/workflows/release.yml`
- `packages/component-versions.json`
- `packages/project-orrery-core/`
- `packages/project-orrery-cli/`
- `packages/project-orrery-observatory/`
- `adapters/codex/`
- `scripts/package_codex_adapter.py`
- `tests/test_codex_adapter.py`
- `adapters/harness-json/`
- `tests/test_harness_json_adapter.py`
- `adapters/claude-code/`
- `adapters/deepseek-harness/`
- `tests/test_claude_code_adapter.py`
- `tests/test_deepseek_harness_adapter.py`
- `packages/project-orrery-core/src/project_orrery_core/collaboration.py`
- `packages/project-orrery-core/src/project_orrery_core/review.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/collaboration_contract.py`
- `packages/project-orrery-cli/src/project_orrery_cli/integration.py`
- `packages/project-orrery-cli/src/project_orrery_cli/review.py`
- `packages/project-orrery-cli/src/project_orrery_cli/worktree.py`
- `tests/fixtures/collaboration/git_fixture.py`
- `tests/test_collaboration_contract.py`
- `tests/test_collaboration_w3.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/personal_observatory.py`（W4 Worktree Candidate）
- `scripts/docsite/build_personal_observatory.py`（root-only W4 opt-in entry）
- `tests/test_personal_observatory.py`
- `packages/project-orrery-core/src/project_orrery_core/team.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/team-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/team.py`
- `tests/test_collaboration_team.py`

## 已知缺口

- 已定义 R0 受限原始层、R1 脱敏可移植层和 R2 权威结论层；尚未实现自动 R1 导出器。
- H2／Harness／retention 研究资产已随 `bb2c768` 与 `96bfd21` 进入本地 `main`；远端 `origin/main` 尚未包含本轮提交。
- Pilot 005–009 的版本化控制包位于 `experiments/context-routing/pilots/`；已启动的控制包不可改写，
  修正使用新 Pilot。R0 原始运行只位于仓库外 `project-orrery-benchmark`，仓库内只保存 R2 结论与
  可复现控制面。
- 三个 Core／CLI／Observatory 组件目前只是未发布源码包，尚未形成独立 wheel 或多组件发布流水线。Codex Adapter 已能独立归档并完成一个精确 runtime 范围的 E2E，但尚未进入 release workflow；其他 runtime／OS 范围仍未验证。Harness JSON 已在同一候选提交通过 Windows／Ubuntu CI，但仍是 `experimental`／`unreleased` 参考 Adapter，尚未作为独立产物发布，也不构成第三方 Agent runtime 兼容证据。
- W3 source 已实现 review／integration／cleanup；W4/W5A 最终候选增加 Personal Observatory 和可运行 opt-in Team Core／CLI／loopback Coordinator。仍没有自动发现、自动 Coordinator 迁移／选主、云 relay、多设备迁移或 Team UI，且不执行远程 shell／Agent／merge／delete。Canonical 与 promotion 状态由 containing ref／exact-SHA checks 决定。
- Claude Code／DeepSeek Harness Adapter 尚未公开发布；DeepSeek 的精确 manifest 范围不得外推到当前源码 Adapter 0.1.1／CLI 0.1.13、其他版本、OS、Provider、模型或未来发行物。
