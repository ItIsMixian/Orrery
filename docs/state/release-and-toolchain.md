# 发布与工具链 State

Updated: 2026-08-31

Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md), [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md), [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md), [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md), [ADR-0018](../decisions/0018-authority-first-workstream-dispatch.md), [ADR-0019](../decisions/0019-portable-operating-rules-and-authority-route-preflight.md), [ADR-0021](../decisions/0021-v0-3-0-release-scope-default-matrix.md), [ADR-0022](../decisions/0022-elkjs-workstream-graph-layout-engine.md), [ADR-0023](../decisions/0023-explicit-legacy-graph-layout-fallback.md)

## 当前公开发布

- Orrery v0.2.0 是唯一公开 Release。annotated tag 指向 `20fc95b`；ZIP SHA-256 为 `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`。
- 发布资产继续使用 `project-orrery-v0.2.0.zip`／`.sha256`；release manifest、bundled bridge 与 phase-0 fixture 保持冻结。
- v0.2.0 Skill 是当前唯一已发布集成。默认安装 create-only；`--upgrade-tools` 只处理白名单工具并先备份；作者文档、凭据、缓存和生成物不进入发布包。
- 当前展示品牌为 Orrery，但 `project-orrery` Skill／distribution／CLI、`project_orrery_*` imports、`.project-orrery.json`、v1 protocol IDs 与 backup/keyring/cache namespaces 不变。
- ADR-0021 已接受 0.3.0 release/default/distribution contract：新项目 Unified/Model 1/Rules 1，旧项目 legacy
  until explicit migration，单一 self-contained ZIP + checksum，Codex final runtime blocker，tag/Release 分权。
  W7.3/CI7 本地中央合流与 routed Fast/Checkpoint 已完成；最终 exact-SHA 网页尚未接受，Final RC 未注册，
  public manifest/tag/assets 均仍为 0.2.0。
- ADR-0022 的 pinned local ELK.js layout-only engine、vendor/license/provenance 与产品接线已进入本地 source；
  它们尚未进入 final self-contained ZIP、deterministic receipt 或公开资产。
- ADR-0023 的 frozen legacy geometry 作为显式本地兼容后手保留且禁止自动回退；维护者已接受 W7.3 收口
  方向，最终整页 acceptance 仍与发布授权分离。

## 当前 Canonical source

- protected `origin/main` 已包含 docs-only SC1 exact `a9369dd`；产品 source baseline `9ee831f` 不对应新 tag 或 Release。
- A4/U2.3/W7.3 local integrated Candidate 声明 Core 0.1.19、CLI 0.1.22、Observatory 0.1.19；内部 relation capture schema 2 与 Graph projection schema 2 不变，组件总状态仍为 `unreleased`，Core API／CLI 顶层 JSON schema 仍为 1。Observatory 随包携带固定 `elkjs@0.11.0` bundle、EPL-2.0 license、package metadata 与 hash-bound provenance，运行时保持 zero-network。
- Codex、Claude Code 与 DeepSeek Harness Adapter source 保持 0.1.1；Harness JSON 因新增有界 relation `suggest`／`inspect` 请求推进到 0.1.2。各 Adapter 的 runtime evidence 继续不能互相外推，Harness 不获得 confirmation 权限。
- Codex verified evidence 只覆盖记录的 Windows 11 build 26200、`codex-cli 0.148.0-alpha.21`、Adapter/Core/CLI 0.1.0、模型和审批范围。
- DeepSeek verified evidence 只覆盖记录的 rc.8、Windows、Adapter 0.1.0、Core 0.1.0、CLI 0.1.1 wheel、`deepseek-official`／`deepseek-v4-flash` 与生命周期范围。
- Claude Code 2.1.87 只完成 Plugin／Skill 发现与认证前失败关闭；没有成功模型路由。Harness JSON 证明 subprocess JSON 合约，不证明第三方 Agent runtime 兼容。
- Authority Model 1 fixture/evaluator、内部 CLI bundle、migration／restore、root-only projection 与 local release-candidate gate 已进入 source；公开 manifest、standalone installer 和默认 managed Observatory 尚未声明或启用模型 1。
- Broker-only docsite、W1–W7 collaboration、Personal／Team／Maintenance／Graph root-only consumers 已进入 source，但没有进入默认 Skill template、managed-tool inventory 或 public release。
- Unified Observatory 当前本地中央 Candidate 组合 A4/U2.3/W7.3，提供单一连续中文导航、规则帮助、轻量活动任务、关系待确认、全局 stop、密集 Maintenance、旧证据降级与 pinned-ELK/legacy 同事实 Graph。仍没有默认/public launcher、managed-tool/public-template/installer transition 或 Release。
- S0 新增未发布 `skills/orrery-dispatch/` source Candidate，只包含 `SKILL.md` 与 `agents/openai.yaml`。它把 ADR-0018 的 authority handoff 投影为 Codex Skill 指令，面向用户称“任务说明版本”；没有 script／asset／reference／service／schema／network，也未进入当前 `project-orrery` Skill、installer、release manifest 或 v0.3.0 范围。
- PO1 在同一 `SKILL.md` 内补充 ADR-0007 PO allocation；仍无新 Skill 文件或发布资产。local integration `8b73f26` 后，两文件已按 SHA-256 一致性校验复制到当前本机 `C:\Users\1\.codex\skills\orrery-dispatch`，但没有进入 release manifest 或公共分发。
- U2.3 只更新 source Observatory 与 root self-host builder/server：发布 dry build 仍为冻结 v0.2.0 Skill archive，且排除 Git-private session、cache、凭据与生成站点。它没有修改 release manifest、proposal、tag、public/default consumer 或 CI routing policy。
- 发布源码中的 Skill 已携带 A4 inventory 投影与 bootstrap/preflight 指令，但 `release-manifest.json`、tag、ZIP、checksum 和 phase-0 fixture 未改；因此“source 分发已接线”与“公开 v0.2.0 已发布”分别为 present/absent。

## CI 与推广门

- Fast workflow 为普通 push／PR 提供 `non-promotion-feedback`；Promotion 只接受冻结 candidate ref／exact SHA，并在 Windows／Ubuntu 执行完整 inventory。
- main branch protection 要求 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`，strict 且对管理员生效；PR 非必需，force-push 与 deletion 禁止。
- CI5 manifest schema 3 保留 27 个逻辑 shard，并映射为每 OS 十个物理 lane。每个 logical shard 仍在独立 Python 子进程中执行；aggregate 验证 lane receipt、exact SHA、OS、manifest、顺序与每个 final test ID 恰好一次。
- exact `9ee831f` 的 Fast run `33235942078` 与 Promotion run `33235992711` 已通过；Promotion 为 25/25 jobs、Windows／Ubuntu 各 390 tests／27 shards、required checks 双 PASS。十 lane 共 23.9 job-min，测试步骤 14.352 分钟，派生 overhead 约 40%。同一 SHA 随后 fast-forward 到 main，main Fast run `33236225082` 通过。
- CI5 不改变 branch protection、组件版本、发布 manifest、tag、Release 或测试覆盖范围；墙钟时间仍是 queue-dependent advisory 指标。
- CI7 Phase 0 current fingerprint `0eea7f...` 在 source `f41b659...` 上用 fresh one-run lease 完成 Fast 3/3
  与 Checkpoint 4/4 PASS，均 zero rerun；旧 fingerprint 的 Checkpoint failure 保留。此证据不等于 Candidate、
  Promotion 或 public release。
- `807096d...` 的 full-page build 在接受前发现 lightweight Personal/Relation Inbox composition blocker；
  revision 5 已恢复组合，revision 6 已收口同端点 automatic Unknown proposals，revision 7 正在恢复
  Core-only `derived_from` effective authority。维护者已接受修复预览；取得新 fingerprint 证据前，
  `f41b659...` receipts 仍不授权后续 source。
- revision-7 source 已冻结，但 fresh CI7 dry-run 因 unregistered temporary IDs／unmapped inbox 两次在测试加载
  前拒绝；IDs 已折叠，revision 8 只补 precise generic mapping。当前仍无 Final RC 或 release input。
- revision-8 mapping 已消除 unmapped path；真实产品窗口仍因 Fast 25 和一个 Unknown owner timing 拒绝。
  revision 9 保留真实窗口，以一次 focused owner + Brand 2-fast/4-checkpoint 分层收敛成本，不改变 release 门。
- revision-9 unique Fast 20/20 PASS；Checkpoint 因新增 portfolio 未同步 hardcoded list 而 29/30。修 list 后
  Fast 又因 ci-control 41 项拒绝。revision 10 撤回新增 examples/list，等待新 fingerprint；Final RC 仍未注册。
- revision-10 rollback fingerprint 的 Checkpoint 预测允许，Fast 仅因 setup+actual-path deep check 为 10.300s
  拒绝。revision 11 做单项 tier correction，不改变 release authority；仍无 Final RC。
- revision-11 product/mapping exact `74afb989...` 已通过 Fast 19/19 与 Checkpoint 30/30；下一安全动作仅是
  docs evidence commit + exact-SHA final page acceptance。Candidate/Promotion/public release 尚未开始。

## 兼容与安全边界

- 旧 Skill wrapper 支持整个 0.3.x；最早到 0.4.0 才具备移除评审资格，且版本到达不自动删除。
- `orrery` PyPI 名称存在无关第三方项目；R4/R5 未授权创建同名 distribution/import。任何 alias 必须路由同一 canonical implementation，并在冲突时失败关闭。
- Authority migration/restore 只操作显式 receipt 绑定的项目 manifest；普通 scaffold／tool upgrade 不替已有项目选择模型。
- dynamic docsite 所有模型调用经过 Broker。Provider Key 只存 OS credential store；同用户本机 Broker 不等于秘密隔离。
- Team／relation／maintenance 的 Git-private state 不进入 wheel、Skill ZIP 或 release manifest。中央 Team 不能执行 shell、Agent、merge、apply 或 delete。

## 实现证据

- `skills/project-orrery/release-manifest.json`
- `skills/orrery-dispatch/SKILL.md`, `skills/orrery-dispatch/agents/openai.yaml`
- `scripts/package_release.py`, `.github/workflows/release.yml`
- `packages/component-versions.json`, `packages/`
- `adapters/`, `scripts/package_*adapter.py`
- `.github/workflows/fast-validation.yml`, `.github/workflows/validate.yml`
- `scripts/ci/`, `tests/test_ci_validation.py`
- `scripts/docsite/build_unified_observatory.py`, `scripts/docsite/serve_orrery.py`
- [U2 Unified Observatory Validation](../validation/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 UX Acceptance Fixes Validation](../validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [U2.2／W7.2 Joint Acceptance](../validation/2026-08-29-u2-2-w7-2-unified-observatory-joint-acceptance.md)
- [U2.3 Navigation & Live Task Visibility](../validation/2026-08-30-u2-3-navigation-live-task-visibility.md)
- [W7.2 Graph Readability Validation](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [W7.3 Relation Capture & Confirmation Validation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)
- [CI5 Validation](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)
- [Platform-neutral Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)

## 已知缺口

- 没有 Core／CLI／Observatory 独立公开发行物、多组件 release workflow、manifest v2 或公共支持矩阵。
- 维护者尚未选择下一 SemVer／candidate manifest；Authority `release_ready` 保持 false。
- Claude 认证后模型路由未完成；其他 Adapter／OS／runtime／模型范围不得继承已有 evidence。
- v0.2.0 archive 在 Windows／Linux 重建尚非 byte-for-byte 一致。
- Unified／Collaboration／Maintenance／Graph／relation inbox 没有默认 consumer 或 public release；真实双机与 scheduler 不受支持。W7.3 只允许本机确认并将 effective relation 交给现有 lifecycle consumer，不提供中央 apply。
- R4 alias、R5 optional default transition 和最早 0.4.0 cleanup review 均未启动。
- `orrery-dispatch` 只在当前本机安装，尚未打包或发布；未来是否进入任何公开版本必须由独立 release Plan/Validation 决定。
- ELK.js vendor asset、license/provenance、package-data mapping 和 failure-to-ledger 已进入未发布本地 source；
  在 final ZIP／runtime／Promotion／publication evidence 完成前不得写成 v0.3.0 已公开包含。
