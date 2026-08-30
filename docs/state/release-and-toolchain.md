# 发布与工具链 State

Updated: 2026-08-29

Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md), [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md), [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md)

## 当前公开发布

- Orrery v0.2.0 是唯一公开 Release。annotated tag 指向 `20fc95b`；ZIP SHA-256 为 `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`。
- 发布资产继续使用 `project-orrery-v0.2.0.zip`／`.sha256`；release manifest、bundled bridge 与 phase-0 fixture 保持冻结。
- v0.2.0 Skill 是当前唯一已发布集成。默认安装 create-only；`--upgrade-tools` 只处理白名单工具并先备份；作者文档、凭据、缓存和生成物不进入发布包。
- 当前展示品牌为 Orrery，但 `project-orrery` Skill／distribution／CLI、`project_orrery_*` imports、`.project-orrery.json`、v1 protocol IDs 与 backup/keyring/cache namespaces 不变。

## 当前 Canonical source

- protected `origin/main` 已包含 docs-only SC1 exact `a9369dd`；产品 source baseline `9ee831f` 不对应新 tag 或 Release。
- W7.2.3 Worktree Candidate 声明 Core 0.1.17、CLI 0.1.21、Observatory 0.1.16；Core／CLI 与关系 schema/facts 不变，Observatory 依次推进 Graph 可读性、渐进展开、画布交互、固定箭头／主题滚动条与紧凑组件间距。组件总状态为 `unreleased`，Core API／CLI JSON schema 仍为 1。
- Codex、Harness JSON、Claude Code 与 DeepSeek Harness Adapter source 均为 0.1.1、`experimental`／`unreleased`。每个 Adapter 有独立 manifest、归档、生命周期和 runtime evidence，不能互相外推。
- Codex verified evidence 只覆盖记录的 Windows 11 build 26200、`codex-cli 0.148.0-alpha.21`、Adapter/Core/CLI 0.1.0、模型和审批范围。
- DeepSeek verified evidence 只覆盖记录的 rc.8、Windows、Adapter 0.1.0、Core 0.1.0、CLI 0.1.1 wheel、`deepseek-official`／`deepseek-v4-flash` 与生命周期范围。
- Claude Code 2.1.87 只完成 Plugin／Skill 发现与认证前失败关闭；没有成功模型路由。Harness JSON 证明 subprocess JSON 合约，不证明第三方 Agent runtime 兼容。
- Authority Model 1 fixture/evaluator、内部 CLI bundle、migration／restore、root-only projection 与 local release-candidate gate 已进入 source；公开 manifest、standalone installer 和默认 managed Observatory 尚未声明或启用模型 1。
- Broker-only docsite、W1–W7 collaboration、Personal／Team／Maintenance／Graph root-only consumers 已进入 source，但没有进入默认 Skill template、managed-tool inventory 或 public release。
- Unified Observatory 已有本地 integrated baseline；U2.1 Worktree Candidate 在其上提供单一中文 app 导航、全局 stop、旧维护证据降级与 W7.1 legacy/archive graph 显示修复。仍没有默认/public launcher、managed-tool/public-template/installer transition 或 Release。

## CI 与推广门

- Fast workflow 为普通 push／PR 提供 `non-promotion-feedback`；Promotion 只接受冻结 candidate ref／exact SHA，并在 Windows／Ubuntu 执行完整 inventory。
- main branch protection 要求 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`，strict 且对管理员生效；PR 非必需，force-push 与 deletion 禁止。
- CI5 manifest schema 3 保留 27 个逻辑 shard，并映射为每 OS 十个物理 lane。每个 logical shard 仍在独立 Python 子进程中执行；aggregate 验证 lane receipt、exact SHA、OS、manifest、顺序与每个 final test ID 恰好一次。
- exact `9ee831f` 的 Fast run `33235942078` 与 Promotion run `33235992711` 已通过；Promotion 为 25/25 jobs、Windows／Ubuntu 各 390 tests／27 shards、required checks 双 PASS。十 lane 共 23.9 job-min，测试步骤 14.352 分钟，派生 overhead 约 40%。同一 SHA 随后 fast-forward 到 main，main Fast run `33236225082` 通过。
- CI5 不改变 branch protection、组件版本、发布 manifest、tag、Release 或测试覆盖范围；墙钟时间仍是 queue-dependent advisory 指标。

## 兼容与安全边界

- 旧 Skill wrapper 支持整个 0.3.x；最早到 0.4.0 才具备移除评审资格，且版本到达不自动删除。
- `orrery` PyPI 名称存在无关第三方项目；R4/R5 未授权创建同名 distribution/import。任何 alias 必须路由同一 canonical implementation，并在冲突时失败关闭。
- Authority migration/restore 只操作显式 receipt 绑定的项目 manifest；普通 scaffold／tool upgrade 不替已有项目选择模型。
- dynamic docsite 所有模型调用经过 Broker。Provider Key 只存 OS credential store；同用户本机 Broker 不等于秘密隔离。
- Team／relation／maintenance 的 Git-private state 不进入 wheel、Skill ZIP 或 release manifest。中央 Team 不能执行 shell、Agent、merge、apply 或 delete。

## 实现证据

- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`, `.github/workflows/release.yml`
- `packages/component-versions.json`, `packages/`
- `adapters/`, `scripts/package_*adapter.py`
- `.github/workflows/fast-validation.yml`, `.github/workflows/validate.yml`
- `scripts/ci/`, `tests/test_ci_validation.py`
- `scripts/docsite/build_unified_observatory.py`, `scripts/docsite/serve_orrery.py`
- [U2 Unified Observatory Validation](../validation/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 UX Acceptance Fixes Validation](../validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [W7.2 Graph Readability Validation](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [CI5 Validation](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)
- [Platform-neutral Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)

## 已知缺口

- 没有 Core／CLI／Observatory 独立公开发行物、多组件 release workflow、manifest v2 或公共支持矩阵。
- 维护者尚未选择下一 SemVer／candidate manifest；Authority `release_ready` 保持 false。
- Claude 认证后模型路由未完成；其他 Adapter／OS／runtime／模型范围不得继承已有 evidence。
- v0.2.0 archive 在 Windows／Linux 重建尚非 byte-for-byte 一致。
- Unified／Collaboration／Maintenance／Graph 没有默认 consumer 或 public release；self-host relation apply、真实双机与 scheduler 不受支持。
- R4 alias、R5 optional default transition 和最早 0.4.0 cleanup review 均未启动。
