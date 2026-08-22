# 项目结构 State

Updated: 2026-08-22
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
- Codex Adapter 0.1.0 的发行支持状态仍为 `experimental`／未发布；其 runtime manifest 只对 Windows 11 build 26200、Codex Desktop 26.818.2441.0／`codex-cli 0.148.0-alpha.21`、Core／CLI 0.1.0 与已记录模型／审批组合标记 `verified`。
- 本地 Canonical source 已在平台中立 Core 0.1.1 冻结 `project-orrery-collaboration-v1`：worktree identity、Workstream session、Scope、overlap finding、integration report、subsystem registry、Member capability 和 project mode 共用一套 schema；CLI 0.1.6 提供只读 `collaboration-contract` 检查。W1.1 Candidate 以 Core／CLI 0.1.2／0.1.7 增加只读 `worktree status` 与显式 `worktree session write`；本 stacked W1.2 Candidate 进一步提升到 0.1.3／0.1.8，并增加 `worktree create` 与 primary-write preflight guard。
- `adapters/claude-code/` 与 `adapters/deepseek-harness/` 已形成 0.1.0、`experimental`／未发布的薄平台 Adapter；两者均只依赖平台中立 CLI，不拥有项目作者文档。Claude Code 已证明 Plugin／Skill 发现后在认证前失败关闭；DeepSeek Harness 只有 manifest 所列 rc.8／Windows／Core 0.1.0／CLI 0.1.1 wheel／模型与生命周期范围为 `verified`。

## 当前边界

- canonical 作者模板位于 Core 包；`skills/project-orrery/assets/project-template/` 是 v0.2 兼容投影，并由测试要求与 canonical 内容一致。
- Observatory 实现源码仍位于根 `scripts/docsite/`，组件包负责清点与版本化；Skill 模板通过显式标题 token 投影保持目标项目可定制。
- 旧 Skill 三个脚本路径现在是薄 wrapper；源码仓库调用新 CLI，单独分发 Skill 时回退到冻结的 v0.2 兼容实现。wrapper 保留至 `0.3.x`，最早在 `0.4.0` 移除。
- `adapters/codex/` 只包含 Codex 发现／调用元数据和 Adapter 生命周期安装器；它通过 manifest 引用 Core／CLI，不复制 canonical 作者模板、schema、兼容规则或项目状态。平台安装器只管理目标 skills 根下的 `project-orrery` Adapter 目录。
- `adapters/harness-json/` 不包含 `SKILL.md` 或平台发现文件；它拥有 versioned request／response schema、参数白名单、subprocess 边界和 timeout 分类，只调用 CLI 的 opt-in JSON，不读取作者文档来重新判定事实。
- `adapters/claude-code/` 使用原生 Plugin discovery；`adapters/deepseek-harness/` 使用 profile Cordis Plugin Bundle。两者有独立 manifest、打包器、生命周期和 runtime evidence，不共享对第三方平台兼容性的推断。
- `docs/_site/`、缓存、凭据和 benchmark 原始输出不是作者文档或发布资产。
- 自托管、实验和测试资产已进入 `main`；v0.2.0 tag／Release 指向发布提交 `20fc95b`，后续当前事实由 main 上的发布后文档继续维护。
- linked worktree 共享 Git 对象库和普通 refs，但拥有独立 HEAD、索引与工作目录。未提交文件仍只属于所在 Worktree scope。当前没有 ADR-0008 所设计的 Team Node／Coordinator，因此跨机器未 push 工作在实际产品中仍不可观察；未来 opt-in Team Mode 只能增加标注为 Local-only 的元数据，不会成为代码证据。
- Phase 0 配置固定在 `.project-orrery.json` 的 `collaboration.integration_ref`、`collaboration.primary_worktree` 和 `collaboration.project_mode`；integration ref 缺省为 `refs/heads/main`，只按本地 branch ref 解析精确 commit OID，不 fetch 或回退远端。主 worktree 缺省取 `git worktree list --porcelain` 的 main worktree，维护者覆盖必须是同一仓库已列出的绝对 worktree 路径。
- worktree 路径比较先收敛现有路径的真实绝对形式，再应用平台大小写规则；这让 Windows runner 的 8.3／长路径别名指向同一已列出 worktree，同时不允许不存在或跨仓库的 override 绕过检查。
- W1.1 Candidate 通过 `git rev-parse --git-path orrery/worktree.json` 定位每个 linked worktree／clone 的 Git 私有 session；原子写入不改变作者工作树状态。session 绑定 worktree ID、branch、HEAD、integration ref／OID、merge base 和 dirty fingerprint；只读 status 在任一绑定事实漂移后报告稳定 stale reason，不自动改写 session。
- W1.2 Candidate 的 `worktree create` 只使用配置的本地 integration ref，在创建前固定 commit OID，并以该 OID 建立新 branch + linked worktree；显式 `--path` 可选，缺省路径是源 worktree 同级的可预测名称。新 worktree 随后写入 Git-private `created` session；branch／path 碰撞在写入前拒绝，session 失败或 integration 漂移只回滚本操作创建的 clean worktree／branch。dirty primary worktree 的原状态不变，新 worktree 仍保持 clean。
- W1.2 Candidate 的 `worktree guard` 是只读 product-write preflight primitive：隔离 worktree 返回 allow；clean primary 与 dirty primary 均返回稳定 block reason 和非零退出码，dirty 只指向人工审阅／选择性转移，不执行自动迁移。Adapter 尚未强制调用该 guard，因此不能宣称任意 Agent 写入已被全局拦截。
- 根 `AGENTS.md` 的七个 subsystem 入口已有显式稳定 ID；Core registry 只投影这些入口链接的既有 State Docs，缺失 State 时失败关闭，`unmapped` 与 `project-wide` 只是 Scope 保留表达，不自动创建作者文档。

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
- `packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/collaboration_contract.py`
- `packages/project-orrery-cli/src/project_orrery_cli/worktree.py`
- `tests/fixtures/collaboration/git_fixture.py`
- `tests/test_collaboration_contract.py`

## 已知缺口

- 已定义 R0 受限原始层、R1 脱敏可移植层和 R2 权威结论层；尚未实现自动 R1 导出器。
- H2／Harness／retention 研究资产已随 `bb2c768` 与 `96bfd21` 进入本地 `main`；远端 `origin/main` 尚未包含本轮提交。
- Pilot 005–009 的版本化控制包位于 `experiments/context-routing/pilots/`；已启动的控制包不可改写，
  修正使用新 Pilot。R0 原始运行只位于仓库外 `project-orrery-benchmark`，仓库内只保存 R2 结论与
  可复现控制面。
- 三个 Core／CLI／Observatory 组件目前只是未发布源码包，尚未形成独立 wheel 或多组件发布流水线。Codex Adapter 已能独立归档并完成一个精确 runtime 范围的 E2E，但尚未进入 release workflow；其他 runtime／OS 范围仍未验证。Harness JSON 已在同一候选提交通过 Windows／Ubuntu CI，但仍是 `experimental`／`unreleased` 参考 Adapter，尚未作为独立产物发布，也不构成第三方 Agent runtime 兼容证据。
- W1.2 Candidate 在 W1.1 上关闭手工 `worktree create` 与 primary-write preflight primitive；Adapter 强制 guard／launch／attach／rebind、完整 lifecycle、实际 Scope/path 采集、自动 overlap finding、integration/review/cleanup 命令、Observatory 投影与 Team 网络层仍未实现，不能宣称多 Agent 协调闭环已经完成。
- Claude Code／DeepSeek Harness Adapter 尚未公开发布；Claude 仍缺成功认证后的模型调用与 CLI 路由证据。DeepSeek 的精确 manifest 范围已验证，但不得外推到当前 Candidate CLI 0.1.8、其他版本、OS、Provider、模型或未来发行物。
