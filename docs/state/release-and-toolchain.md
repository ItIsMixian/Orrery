# 发布与工具链 State

Updated: 2026-08-21

Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

## 当前事实

- Project Orrery v0.2.0 已通过 annotated tag 和 [GitHub Release](https://github.com/yw9299-stack/project-orrery/releases/tag/v0.2.0)公开发布；tag 指向 `20fc95b`。
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
- 三个未发布组件初始版本均为 `0.1.0`；Core API 为 1。旧 `skills/project-orrery/scripts/` 路径是薄 wrapper，并保留可独立运行的冻结 v0.2 fallback；保留承诺覆盖 `0.3.x`，最早 `0.4.0` 才可移除。
- Observatory 的 9 个当前 managed tools 由独立 component manifest 清点；根观测台与 Skill 模板之间的标题差异通过显式模板投影表达，不复制项目事实。
- 工作树新增未发布的 Codex Adapter 0.1.0：独立 manifest、`SKILL.md`、`agents/openai.yaml`、安装说明与平台安装器位于 `adapters/codex/`；它只声明 Core API 1 与 CLI `>=0.1.0,<0.2.0` 依赖，不包含 canonical 模板、schema 或兼容规则。
- `scripts/package_codex_adapter.py` 可生成固定条目顺序／时间／权限的独立 ZIP 和 SHA-256；平台安装器支持 dry-run、未知目录拒绝、旧 Skill／已识别 Adapter 整目录备份升级和移入可恢复回收目录的卸载。备份与回收目录位于 skills discovery 根之外，避免宿主重复发现旧 `SKILL.md`。
- Codex Adapter 现在包含确定性 CLI 依赖 preflight：它按 manifest 检查 `project-orrery-cli` distribution、`>=0.1.0,<0.2.0` 版本和 `project-orrery` entrypoint；缺失与不兼容均非零退出，不回退到旧 Skill 实现。
- 2026-08-21 使用 Windows 11 build 26200、Codex Desktop 26.818.2441.0／`codex-cli 0.148.0-alpha.21` 完成真实 binary E2E。首次检查因真实登录态同时发现 repo Adapter 与用户旧 Skill 而安全停止；后续使用 Codex `skills.config` 的 per-run 路径禁用项隔离旧 Skill，不复制凭据或修改用户 Skill 目录。模型可见目录只剩 repo Adapter，并以 `gpt-5.6-terra`／medium 完成显式与隐式路由、兼容 CLI 预检和 validate，以及 CLI distribution 缺失、0.2.0 不兼容时的失败关闭。
- 同一 E2E 还验证旧 v0.2 Skill 只有显式 `--upgrade` 才迁移、升级前整树备份、可恢复卸载、backup／trash 不重复发现、卸载后 Adapter 为 0 项、项目作者 tree 不变和用户旧 Skill 摘要不变。Adapter 0.1.0 的上述精确 runtime／OS／Core 0.1.0／CLI 0.1.0／模型与审批范围标记 `verified`，但 Adapter 发行支持状态继续为 `experimental`，证据见 [Codex Runtime E2E 完成](../validation/2026-08-21-codex-runtime-e2e-completion.md)。Adapter 与独立 Core／CLI 仍未发布；v0.2.0 旧 Skill 仍是唯一已发布集成。
- Phase 3 候选分支先把未发布 CLI 从 0.1.0 提升到 0.1.1：`scaffold`、`validate` 和 `check-update` 保留原人类输出，并新增 schema v1 opt-in JSON envelope。Authority migration 检查点把候选 CLI 依次推进到 0.1.2 dry-run、0.1.3 receipt-gated apply、0.1.4 scoped restore 和 0.1.5 future-release update compatibility；JSON 模式继续稳定区分成功、非法请求、操作失败、验证失败、兼容失败、离线更新不可用和超时，update data schema 未增加字段。Codex Adapter 的已验证历史仍精确绑定 CLI 0.1.0，不能因当前源码版本变化而改写。
- 未发布 `adapters/harness-json/` 0.1.0 是 subprocess JSON 参考 Adapter：只接受固定参数白名单，不加载 `SKILL.md`、Codex 配置／登录态或 Agent runtime，并清理常见 Agent／Provider 环境变量。它在 Windows 候选工作树通过 dry-run、临时安装、validate、mixed toolchain、schema 不兼容、离线更新和作者文件保留；首轮 CI 暴露的 Unix 命令夹具错误已在 `c30acab` 修复。第三轮 CI `32441505867` 在同一 `4a006fe` 提交取得 Windows／Ubuntu 双 PASS，Phase 3 跨 OS 验收完成。支持状态仍为 `experimental`／`unreleased`，不构成第三方平台兼容声明。
- ADR-0011 已定义 Authority Model 的公开正整数版本与离散支持集。self-host project manifest 已显式选择模型 1，neutral CLI 0.1.5 候选源码可报告兼容能力，通过 review receipt、精确备份与原子替换显式采用 model 1，可从项目内匹配备份执行带撤销备份的恢复，并在 future release 声明模型时只读判断更新是否需要 migration review；实际 component/release manifest、standalone installer、当前 v0.2 scaffold 和发布资产仍未投影默认值或支持集，普通工具升级也不会补写字段。
- Candidate Core 已能验证 future release 的 `authority_model_version` 与 `compatibility.authority_model_versions.supported` 必须成对、默认值必须位于离散支持集；只有新项目会从这种 future contract 选择默认模型。已有 legacy manifest 在普通 scaffold／`--upgrade-tools` 下继续缺字段。当前 `skills/project-orrery/release-manifest.json` 和 bundled bridge 仍精确代表 v0.2.0、没有模型声明；因此 standalone v0.2 fallback、公开 zip/checksum 与发布事实均未改变。
- ADR-0007／ADR-0008 的多人协作协议已经进入权威链，但 `orrery worktree create/status/overlap`、review／cleanup 和 `orrery integrate` 仍只是 Approved Design 中的目标工具面；当前 CLI、Observatory、Skill 和发布资产都没有这些命令或 Personal／Team Mode，也没有升级版本或发布新产物。

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
- `tests/test_harness_json_adapter.py`
- `packages/project-orrery-core/src/project_orrery_core/authority_migration.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_migrate.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_restore.py`
- `tests/test_authority_model_migration.py`
- `tests/test_authority_model_restore.py`
- `tests/fixtures/authority-meta-model/v1/projection.json`
- `tests/test_authority_model_projection.py`
- `tests/test_authority_update_compatibility.py`

## 已知缺口

- v0.2.0 已发布；下一补丁需要修复 Windows／Linux ZIP 行尾和权限元数据差异，才能宣称跨平台 byte-for-byte 可重复打包。
- Phase 1 源码边界和 Phase 2 Codex Adapter 已实现，且一个精确 Windows／Codex 范围已通过真实 runtime E2E；其他 Codex 版本、OS、模型和审批模式仍未验证。Phase 3 Harness JSON 已通过同一提交的 Windows／Ubuntu CI，但这只验收平台中立 CLI／Harness 合约。Core／CLI 独立发行物、多组件发布流水线、manifest v2 和跨 runtime 支持矩阵仍未实现。
- 多 Workstream 自动化尚无正式 schema、CLI、观测台投影、Team 网络面或 CI 门禁。当前仅能依靠 Git 原生命令、独立 worktree 和人工验证执行协议；默认安装没有因 ADR-0008 开始监听网络。
- Authority Meta Model 已有 fixture-bound Core evaluator、内部兼容判断、neutral CLI `validate` capability report、receipt-gated migration apply/restore、future-release projection contract 和 `check-update` migration review，但没有实际下一 release manifest、稳定顶层 Core API、独立发行物、Harness Adapter 迁移命令、managed Observatory banner 或发布支持状态变化；v0.2.0 发布事实不变。
