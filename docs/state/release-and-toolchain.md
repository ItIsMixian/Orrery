# 发布与工具链 State

Updated: 2026-08-28

Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md)

## 当前事实

- Project Orrery v0.2.0 已通过 annotated tag 和 [GitHub Release](https://github.com/ItIsMixian/Orrery/releases/tag/v0.2.0)公开发布；tag 指向 `20fc95b`。
- 外部当前展示名和仓库入口已改为 Orrery／`ItIsMixian/Orrery`。Candidate 当前只同步根 README、
  self-host 更新入口、Adapter metadata 与当前链接；`project-orrery` 技术 ID、冻结 v0.2.0
  manifest/bridge、tag/asset 和历史权威记录保持不变。
- 正式 zip SHA-256 为 `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`，发布资产中的 checksum 已通过重新下载复核。
- Skill、目标工具链、项目 manifest 格式和文档 schema 分别版本化。
- 默认安装只创建缺失文件；`--upgrade-tools` 只处理白名单并先备份。
- installer 对 `__pycache__`、`.pyc`、`.pyo` 的排除，以及模板 `.venv/`／`venv/` 忽略规则已进入 v0.2.0。
- Pilot 004 中产生的共享 compatibility gate、凭据撤销和缓存实现都在隔离仓库中，不属于当前产品实现。
- 当前工作树的发布模板已把动态 docsite AI 设置入口移到顶栏并补充移动端收缩规则；该小优化尚未提交、打 tag 或进入公开 v0.2.0 资产。
- 当前工作树的发布模板已加入 ADR-0003 的 Provider 绑定、显式端点、同源刷新和可选确定性 Broker；Broker 已进入 managed-tool 白名单与安装验证，但这些未发布改动不回写 v0.2.0 资产。
- ADR-0006 进一步将未发布动态 docsite 收敛为 Broker-only：本机托管为默认，外部隔离只绑定 client token，图形、Q&A CLI 与 `set_key.py` 不再提供直接 Provider 运行入口。根工具与 Skill 模板已同步，仍未提交或发布。
- ADR-0004 已接受单仓库分包、canonical `AGENTS.md`、独立组件版本和真实 runtime 证据门；Phase 1 已在工作树建立 Core／CLI／Observatory 源码包，但 Codex Skill 仍是当前唯一发布集成，也没有第二平台兼容实现。
- ADR-0004 Phase 0 已完成：v0.2.0 的 36 个发布路径、8 个 managed tools、checksum、CLI 入口与 manifest 必需字段已进入机器可读基线；installer／validator／update checker 的人类输出有回归断言，模板 `AGENTS.md` 标题已中立化。
- 公开 README 当前把可直接运行但仍随 Skill 分发的 Core／CLI 路径、整体仍为 `experimental`／未发布但精确 runtime 范围为 `verified` 的 Codex Adapter，以及 `target` 其他平台分开表述；这不构成独立 Core／CLI 包发布，也不得把验证范围外推到其他 runtime 或 OS。
- 三个未发布组件初始版本均为 `0.1.0`；当前 W5E Worktree Candidate 为 Core 0.1.11／CLI 0.1.15／Observatory 0.1.8，Core API 仍为 1；仅 containing ref 为 main 时才是 Canonical。旧 Skill wrapper、managed-tool inventory 与冻结 v0.2 fallback 不变。
- 当前 W7A correction Worktree Candidate 为 Core 0.1.13／CLI 0.1.17／Observatory 0.1.8，Core API、relation schema version 与 CLI JSON envelope schema 仍为 1。`project-orrery relations graph|succession-plan` 只读加载修正后的多轴 Core graph；`relations propose` 只在本机显式调用时 append revision 1 proposed event。apply/undo 仅有 `execution_supported=false` 的 exact Session/receipt contract，该 CLI、schema 与版本尚未发布。
- 当前 W7B Worktree Candidate 为 Core 0.1.14／CLI 0.1.18／Observatory 0.1.8，Core API 与 CLI JSON envelope 仍为 1。新增 dependency-light `relations discover|plan|inspect|apply|undo|receipt` 与 execution schema v1；只有 exact local-human confirmation 可执行 Git-private batch transaction，Unknown/blocked 使用稳定非零退出。该变化没有加入 Adapter capability manifest、managed tools、Skill template、installer 或发布资产。
- Observatory 的 9 个当前 managed tools 由独立 component manifest 清点；根观测台与 Skill 模板之间的标题差异通过显式模板投影表达，不复制项目事实。
- 工作树的未发布 Codex Adapter 当前为 0.1.1：独立 manifest、`SKILL.md`、`agents/openai.yaml`、安装说明与平台安装器位于 `adapters/codex/`；它只声明 Core API 1 与 CLI `>=0.1.0,<0.2.0` 依赖，不包含 canonical 模板、schema 或兼容规则。既有 verified runtime evidence 仍绑定 0.1.0。
- `scripts/package_codex_adapter.py` 可生成固定条目顺序／时间／权限的独立 ZIP 和 SHA-256；平台安装器支持 dry-run、未知目录拒绝、旧 Skill／已识别 Adapter 整目录备份升级和移入可恢复回收目录的卸载。备份与回收目录位于 skills discovery 根之外，避免宿主重复发现旧 `SKILL.md`。
- Codex Adapter 现在包含确定性 CLI 依赖 preflight：它按 manifest 检查 `project-orrery-cli` distribution、`>=0.1.0,<0.2.0` 版本和 `project-orrery` entrypoint；缺失与不兼容均非零退出，不回退到旧 Skill 实现。
- 2026-08-21 使用 Windows 11 build 26200、Codex Desktop 26.818.2441.0／`codex-cli 0.148.0-alpha.21` 完成真实 binary E2E。首次检查因真实登录态同时发现 repo Adapter 与用户旧 Skill 而安全停止；后续使用 Codex `skills.config` 的 per-run 路径禁用项隔离旧 Skill，不复制凭据或修改用户 Skill 目录。模型可见目录只剩 repo Adapter，并以 `gpt-5.6-terra`／medium 完成显式与隐式路由、兼容 CLI 预检和 validate，以及 CLI distribution 缺失、0.2.0 不兼容时的失败关闭。
- 同一 E2E 还验证旧 v0.2 Skill 只有显式 `--upgrade` 才迁移、升级前整树备份、可恢复卸载、backup／trash 不重复发现、卸载后 Adapter 为 0 项、项目作者 tree 不变和用户旧 Skill 摘要不变。Adapter 0.1.0 的上述精确 runtime／OS／Core 0.1.0／CLI 0.1.0／模型与审批范围标记 `verified`，但 Adapter 发行支持状态继续为 `experimental`，证据见 [Codex Runtime E2E 完成](../validation/2026-08-21-codex-runtime-e2e-completion.md)。Adapter 与独立 Core／CLI 仍未发布；v0.2.0 旧 Skill 仍是唯一已发布集成。
- Phase 3 候选分支先把未发布 CLI 从 0.1.0 提升到 0.1.1：`scaffold`、`validate` 和 `check-update` 保留原人类输出，并新增 schema v1 opt-in JSON envelope。Authority migration 检查点把候选 CLI 依次推进到 0.1.2 dry-run、0.1.3 receipt-gated apply、0.1.4 scoped restore 和 0.1.5 future-release update compatibility；W1 Phase 0 又以 0.1.6 增加只读 `collaboration-contract`，W1.1 以 0.1.7 增加 `worktree status/session write`，W1.2 以 0.1.8 增加 `worktree create/guard`，W1.3 以 0.1.9 增加 lifecycle transition、Adapter route 与私有 attach，W2 以 0.1.10 增加 Scope/Finding，W3 以 0.1.11 增加 `integrate`／`review`，再以 0.1.12 扩展 `review inventory/cleanup/cleanup-receipt`；W5A Candidate 以 0.1.13 增加 `team` 命令族。既有 JSON envelope 与 update data schema 不变；失败关闭路径继续使用稳定非零 exit。Codex Adapter 的已验证历史仍精确绑定 CLI 0.1.0，不能因当前源码版本变化而改写。
- 未发布 `adapters/harness-json/` 当前为 0.1.1，是 subprocess JSON 参考 Adapter：只接受固定参数白名单，不加载 `SKILL.md`、Codex 配置／登录态或 Agent runtime，并清理常见 Agent／Provider 环境变量；其 workstream capability matrix 明确 launch／attach／rebind／message 全部关闭。原 0.1.0 在 Windows／Ubuntu CI 的跨 OS 验收事实保持不变，0.1.1 仍为 `experimental`／`unreleased`，不构成 Agent runtime 兼容声明。
- ADR-0013 的 Claude Code 与 DeepSeek Harness Adapter 当前源码版本为 0.1.1：各自有独立 manifest、确定性归档、CLI 依赖预检、隔离生命周期测试和 caller-provided session attach 声明，支持状态均为 `experimental`／`unreleased`。既有 runtime evidence 仍绑定 0.1.0；Claude Code 2.1.87 只证明 Plugin／Skill 发现及认证前失败关闭，DeepSeek Harness rc.8 的模型调用证据由单独 Validation 精确限定。
- 2026-08-22 经用户授权的 DeepSeek Harness rc.8 隔离运行已完成显式／隐式真实模型路由、CLI 缺失／不兼容失败关闭及 0→1→0 生命周期恢复；后续 wheel 修复又让普通非 editable CLI 0.1.1 从安装包加载 Observatory assets，并在真实显式 Adapter turn 中完成 preflight／validate。经干净整合与联合回归，只有精确 rc.8／Windows build 26200／Adapter 0.1.0／Core 0.1.0／CLI 0.1.1／`deepseek-official`／`deepseek-v4-flash` 及已记录生命周期范围进入 `runtime_compatibility.verified`；Adapter 发行仍为 `experimental`／`unreleased`。
- ADR-0011 已定义 Authority Model 的公开正整数版本与离散支持集。self-host project manifest 已显式选择模型 1，neutral CLI 0.1.13 Candidate 保留 0.1.5 的兼容报告、receipt-gated migration／restore 和只读 update 判断；实际 release manifest、standalone installer、当前 v0.2 scaffold 和发布资产仍未投影默认值或支持集，普通工具升级也不会补写字段。
- Candidate Core 已能验证 future release 的 `authority_model_version` 与 `compatibility.authority_model_versions.supported` 必须成对、默认值必须位于离散支持集；只有新项目会从这种 future contract 选择默认模型。已有 legacy manifest 在普通 scaffold／`--upgrade-tools` 下继续缺字段。当前 `skills/project-orrery/release-manifest.json` 和 bundled bridge 仍精确代表 v0.2.0、没有模型声明；因此 standalone v0.2 fallback、公开 zip/checksum 与发布事实均未改变。
- Canonical source baseline 已集成 `orrery-authority-release-candidate-gate-v1` 并进入公开 `origin/main`：候选 manifest 由维护者在仓库外显式提供，Gate 对 Authority Model `default=1`／`supported=[1]`、确定性离线 ZIP／checksum、standalone new／legacy、invalid／unsupported target、显式 migration／restore、self-host、secret／generated artifact 排除执行失败关闭验证。候选 manifest 只注入 staging archive，三份冻结 v0.2.0 历史输入保持不变；输出 receipt 始终区分 `candidate_ready` 与 `release_ready=false`。源码同步不等于 gate、模型 1 或下一版本已发布。
- Candidate 安装器在 release 真正声明 Authority support 时，会在任何读取／复制前拒绝 symlink、Windows reparse、目录或其他非普通 `.project-orrery.json`，并对 invalid／unsupported selector 零写入失败；public v0.2 manifest 未声明 support，因此冻结兼容行为不变。Gate 子进程只继承显式环境白名单并有 120 秒超时，解包阶段独立复核 traversal、大小写碰撞、symlink、禁用路径／文件和 plaintext credential pattern。
- Candidate managed Observatory source/template 已投影同一默认关闭的 Authority shadow sidecar 接线；它只在显式环境开关下运行，且 package／manifest／scope／写入失败不改变 legacy HTML 或 stats。该 Candidate 工具变化没有改写 v0.2.0 release manifest、归档、checksum、installer 默认值或公开支持状态。
- 同一 source/template 投影现已让 AI 派生视图消费压缩后的 shadow context，并在 JSON／正文／stream headers 标注非权威边界；缺省无 report 时失败关闭为 `Unknown`／`unavailable`。这仍是未发布 managed-tool 行为，不改变组件版本、v0.2.0 资产或公开支持声明。
- Candidate source/template 还投影了单独的 shadow diagnostic view 开关；report-only 与默认构建保持原 HTML，只有显式 view opt-in 才注入不含 claim payload 的诊断面板。该变化同样没有修改组件版本、release manifest、归档、installer 或 v0.2.0 事实。
- ADR-0007／ADR-0008 的 W1–W3 已进入 Canonical source：versioned contract、Git/config/subsystem/member/mode 解析、worktree create/status/guard/route、Git-private session、lifecycle、私有 attach、Scope/finding 与 acknowledgement 均可用；W3 复用这些 contract，提供 `integrate --dry-run`、证据优先 review package、四种人工 decision、integration eligibility、bounded workspace inventory、cleanup eligibility 与 Git-private closure/action receipt。默认 Personal Core 路径保持 zero-network，四类 cleanup 授权不互相隐含，所有实际 merge／push／删除都留给另行授权。当前平台均不声明 launch／rebind／message，且尚无宿主级任意写入拦截；Team runtime 仍是后续目标，用户级 Skill／公开 v0.2.0 资产没有变化。
- W4 Worktree Candidate 的 `build_personal_observatory.py` 是与 M2.2 类似的 root-only opt-in entry；关闭开关时逐字节返回既有 base renderer，开启后组合 W1/W2 Personal projection 与 Canonical W3 read-only provider，并可与显式 Authority Candidate projection 组合。W3 package freshness／risk／human approval／integration eligibility、bounded inventory、cleanup gate 与 closure／receipt 由 Core 或其稳定 Git-private bundle提供；W4 不实现判定或执行动作。该脚本不进入 Observatory managed-tool 白名单或 Skill template，不改变默认 build／serve、wheel managed assets、installer、release manifest、用户级 Skill 或公开 v0.2.0。
- W5A Candidate 在 W1–W3 contract 上增加 Team schema、Core、CLI 与 stdlib Coordinator。Personal 默认不导入或启动 listener；Team enable 只写 Git-private 配置，`serve` 才显式绑定 loopback，LAN wildcard/private bind 还要求本地开关。Coordinator 只读聚合和发送 request，不执行 shell／Agent／merge／delete；用户级 Skill与公开 v0.2.0 资产没有变化。
- W5B Candidate 增加 Core-owned in-process Coordinator stop 原语与独立 `serve_team_observatory.py`。root-only UI server 固定绑定 `127.0.0.1`，只接受同源／合法 Host／随机 HttpOnly control cookie 保护的固定 POST，限制 16 KiB body 并脱敏错误；关闭 UI 会停止它拥有的 Coordinator。Team page、动态入口与测试没有加入默认 `build_docsite.py`／`serve.py`、Observatory managed tools、Skill template、installer、release manifest 或公开 v0.2.0。
- W5C Candidate 只把 Observatory 提升到 0.1.5，并重排 Team page 的信息层级、状态文案、handled request archive 与 responsive layout；server route、POST action、cookie、body、network、Core／CLI contract 和发布清单均不变。
- W6 Candidate 增加 `orrery maintenance` dependency-free CLI、Core maintenance v1 contract 与 Personal Observatory 页面；发布版本分别提升到 Core 0.1.10／CLI 0.1.14／Observatory 0.1.6。CLI execute 只接受 authorization ID，scheduler status 固定 `unsupported-phase-4`；没有增加 daemon、Windows Task Scheduler／cron／systemd／launchd 安装器，也没有改动 Skill v0.2.0、managed-tool inventory、release manifest、tag 或 Release。
- W5D Candidate 增加 `team discovery-serve|discovery-scan|discovery-status`、candidate-aware join、`coordinator-switch-create|coordinator-switch-claim` 与 `worktree ... --base-workstream-id/--task-base-oid`。LAN acceptance runner／validator 是仓库工具，不进入公开 v0.2.0 包；它只在系统临时目录创建本地 clone，使用 controlled discovery＋loopback HTTP，并输出脱敏 checksum verdict。没有 push、tag、Release、云 relay、自动选主或 scheduler 变更。
- CI1 Worktree Candidate 增加 dependency-free unittest inventory／26-shard manifest、逐项 timing JSON runner、fail-closed aggregate 与 workflow static validator；Fast 对普通 push／PR 提供非 Promotion 反馈，Promotion 只接受显式 ref＋exact SHA 或 `promotion/**` 冻结分支。既有 branch-protection context 名不变，`release.yml` 的 tag 发布门不在本 Workstream 改写，且本 Candidate 没有调用 GitHub API、push、tag 或 Release。
- W5E Worktree Candidate 只将 Observatory 0.1.7 提升至 0.1.8：重排 Team 页面与本机设置弹窗，未修改 Core／CLI、Team server route、安全 POST、CI workflow、managed-tool inventory、Skill template、installer、release manifest、tag 或 Release。
- W7A 不修改 Observatory managed tools、Skill template、installer、release manifest、tag 或 Release。Git-common-private relation 文件不属于 package input；W7B apply/undo execution 与 W7C-B UI 均保持未实现。
- W7B 不修改 Observatory managed tools、Skill template、installer、release manifest、tag 或 Release。transaction/confirmation/receipt 与 relation event 均位于 Git common private state，不进入作者/发布 inventory；没有 push、main merge、branch protection、tag、Release 或网络调用。

## 实现证据

- `skills/project-orrery/scripts/install_project_orrery.py`
- `skills/project-orrery/scripts/validate_installation.py`
- `skills/project-orrery/scripts/check_project_orrery_update.py`
- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`
- `tests/fixtures/platform_neutral_phase0_baseline.json`
- `tests/test_project_orrery.py`
- `packages/component-versions.json`
- `packages/project-orrery-core/`
- `packages/project-orrery-cli/`
- `packages/project-orrery-observatory/`
- `adapters/codex/adapter-manifest.json`
- `adapters/codex/scripts/check_cli_dependency.py`
- `adapters/codex/scripts/install_adapter.py`
- `scripts/package_codex_adapter.py`
- `tests/test_codex_adapter.py`
- `adapters/harness-json/adapter-manifest.json`
- `adapters/harness-json/schemas/`
- `adapters/harness-json/run_harness.py`
- `adapters/claude-code/`
- `scripts/package_claude_code_adapter.py`
- `tests/test_claude_code_adapter.py`
- `adapters/deepseek-harness/`
- `scripts/package_deepseek_harness_adapter.py`
- `tests/test_deepseek_harness_adapter.py`
- `tests/test_harness_json_adapter.py`
- `packages/project-orrery-core/src/project_orrery_core/authority_migration.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_migrate.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_restore.py`
- `tests/test_authority_model_migration.py`
- `tests/test_authority_model_restore.py`
- `tests/fixtures/authority-meta-model/v1/projection.json`
- `tests/test_authority_model_projection.py`
- `tests/test_authority_update_compatibility.py`
- `packaging/authority-release-candidate-policy.json`
- `scripts/authority_release_candidate_gate.py`
- `tests/fixtures/authority-meta-model/v1/release-candidate-gate.json`
- `tests/test_authority_release_candidate_gate.py`
- `docs/validation/2026-08-21-m2-3-authority-release-candidate-gate.md`
- `packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json`
- `packages/project-orrery-core/src/project_orrery_core/collaboration.py`
- `packages/project-orrery-cli/src/project_orrery_cli/collaboration_contract.py`
- `packages/project-orrery-cli/src/project_orrery_cli/worktree.py`
- `tests/test_collaboration_contract.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/personal_observatory.py`
- `scripts/docsite/build_personal_observatory.py`
- `tests/test_personal_observatory.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/team_observatory.py`
- `scripts/docsite/serve_team_observatory.py`
- `tests/test_team_observatory.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/maintenance-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/maintenance.py`
- `tests/test_workspace_maintenance.py`
- `tests/test_collaboration_lineage.py`
- `tests/test_lan_collaboration_harness.py`
- `scripts/acceptance/run_lan_collaboration_acceptance.py`
- `scripts/acceptance/validate_lan_collaboration_acceptance.py`
- `scripts/ci/`
- `.github/workflows/fast-validation.yml`
- `.github/workflows/validate.yml`
- `tests/test_ci_validation.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/workstream-relations-v1.json`
- `packages/project-orrery-core/src/project_orrery_core/workstream_relations.py`
- `packages/project-orrery-core/src/project_orrery_core/workstream_relation_execution.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/workstream-relation-execution-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/workstream_relations.py`
- `tests/test_workstream_relations.py`
- `tests/test_workstream_relation_execution.py`

## 已知缺口

- v0.2.0 已发布；下一补丁需要修复 Windows／Linux ZIP 行尾和权限元数据差异，才能宣称跨平台 byte-for-byte 可重复打包。
- Phase 1 源码边界和 Phase 2 Codex Adapter 已实现，且一个精确 Windows／Codex 范围已通过真实 runtime E2E；其他 Codex 版本、OS、模型和审批模式仍未验证。Phase 3 Harness JSON 已通过同一提交的 Windows／Ubuntu CI，但这只验收平台中立 CLI／Harness 合约。Core／CLI 独立发行物、多组件发布流水线、manifest v2 和跨 runtime 支持矩阵仍未实现。
- self-host `main` 的服务端保护要求 exact commit 已通过 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`；维护者仍可直接快进已验证 SHA，不强制 PR。该规则保护 source integration，不选择发布版本、tag 或 Release。
- CI1 只在 Worktree scope 实现新检查拓扑；GitHub-hosted Fast ≤90s、Windows Promotion ≤4m、artifact upload/download 与既有 branch protection 接线仍需对冻结 exact SHA 做远端验证。未取得该证据前不得把本机投影写成 hosted 性能或 Canonical CI 事实。
- 当前 W5E Worktree Candidate 包含 W1–W3 review/cleanup、W4 Personal 指挥台、W5A Team foundation、W5E root-only Team UI、W6 maintenance、显式 LAN discovery/join/manual Host switch、stacked lineage 与 CI1。仍缺 Phase 3 自动 removal、Phase 4 scheduler Adapter、真实双机/LAN、自动选主、云 relay、多设备迁移、hosted CI1 性能证据与完整发行接线；Canonical 状态由 containing ref 决定，公开 v0.2.0 不变。
- W7B 的 relation execution 仅存在于源码 Worktree Candidate；未进入独立 wheel/release、Adapter capability manifest、默认 Observatory consumer 或 hosted Promotion。隔离本机 apply/undo 不能外推为 self-host 真实 migration、Ubuntu、跨设备或发布支持声明。
- Claude Code 尚未完成成功认证与模型调用；DeepSeek Harness 只有 manifest 中列出的 Adapter 0.1.0 精确 runtime 范围为 `verified`。两者均无公开分发或跨版本支持承诺，当前源码 Adapter 0.1.1／CLI 0.1.13 与其他 runtime／OS／模型不能继承旧验证结论。
- Authority Meta Model 已有 fixture-bound Core evaluator、内部兼容判断、neutral CLI `validate` capability report、receipt-gated migration apply/restore、future-release projection contract、`check-update` migration review 与本地 release-candidate gate，但没有维护者选定的实际下一 SemVer／source manifest、M2.2 consumer production evidence、稳定顶层 Core API、独立发行物、Harness Adapter 迁移命令、managed Observatory banner 或发布支持状态变化；v0.2.0 发布事实不变。
