# 发布与工具链 State

Updated: 2026-08-20

Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

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
- 公开 README 当前把可直接运行但仍随 Skill 分发的 Core／CLI 路径，与 `experimental` Codex 集成、`target` 其他平台分开表述；这不构成独立 Core 包或任何 runtime `verified` 证据。
- 三个未发布组件初始版本均为 `0.1.0`；Core API 为 1。旧 `skills/project-orrery/scripts/` 路径是薄 wrapper，并保留可独立运行的冻结 v0.2 fallback；保留承诺覆盖 `0.3.x`，最早 `0.4.0` 才可移除。
- Observatory 的 9 个当前 managed tools 由独立 component manifest 清点；根观测台与 Skill 模板之间的标题差异通过显式模板投影表达，不复制项目事实。
- 工作树新增未发布的 Codex Adapter 0.1.0：独立 manifest、`SKILL.md`、`agents/openai.yaml`、安装说明与平台安装器位于 `adapters/codex/`；它只声明 Core API 1 与 CLI `>=0.1.0,<0.2.0` 依赖，不包含 canonical 模板、schema 或兼容规则。
- `scripts/package_codex_adapter.py` 可生成固定条目顺序／时间／权限的独立 ZIP 和 SHA-256；平台安装器支持 dry-run、未知目录拒绝、旧 Skill／已识别 Adapter 整目录备份升级和移入可恢复回收目录的卸载。备份与回收目录位于 skills discovery 根之外，避免宿主重复发现旧 `SKILL.md`；所有生命周期验证只在临时目录完成。
- 新 Adapter 仍为 `experimental`：manifest 的 verified runtime 与 evidence 均为空，尚未安装到真实 Codex 用户目录，也没有真实发现、调用、失败、更新或卸载证据；v0.2.0 旧 Skill 继续是唯一已发布集成。
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
- `adapters/codex/scripts/install_adapter.py`
- `scripts/package_codex_adapter.py`
- `tests/test_codex_adapter.py`

## 已知缺口

- v0.2.0 已发布；下一补丁需要修复 Windows／Linux ZIP 行尾和权限元数据差异，才能宣称跨平台 byte-for-byte 可重复打包。
- Phase 1 源码边界和 Phase 2 的仓库内 Codex Adapter／生命周期产物已实现，但 Core／CLI 独立发行物、多组件发布流水线、manifest v2、Harness JSON 合约和 runtime 支持矩阵仍未实现；Codex Adapter 也尚未经过真实 runtime E2E。
- 多 Workstream 自动化尚无正式 schema、CLI、观测台投影、Team 网络面或 CI 门禁。当前仅能依靠 Git 原生命令、独立 worktree 和人工验证执行协议；默认安装没有因 ADR-0008 开始监听网络。
