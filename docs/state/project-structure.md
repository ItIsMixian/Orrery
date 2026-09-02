# 项目结构 State

Updated: 2026-09-01

Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md), [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md), [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md), [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md), [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md), [ADR-0018](../decisions/0018-authority-first-workstream-dispatch.md), [ADR-0019](../decisions/0019-portable-operating-rules-and-authority-route-preflight.md), [ADR-0020](../decisions/0020-workstream-program-and-phase-hierarchy.md), [ADR-0021](../decisions/0021-v0-3-0-release-scope-default-matrix.md), [ADR-0022](../decisions/0022-elkjs-workstream-graph-layout-engine.md), [ADR-0023](../decisions/0023-explicit-legacy-graph-layout-fallback.md), [ADR-0026](../decisions/0026-durable-workstream-history-and-human-readable-relation-decisions.md), [ADR-0027](../decisions/0027-retain-history-without-bulk-ui-and-recover-archived-lineage.md), [ADR-0028](../decisions/0028-shell-first-observatory-and-incremental-graph-cache.md), [ADR-0029](../decisions/0029-explicit-workstream-classification-and-dispatch-registration.md), [ADR-0030](../decisions/0030-fast-candidate-freeze-and-asynchronous-validation.md), [ADR-0031](../decisions/0031-read-only-codex-plugin-surface-for-orrery-conductor.md)

Additional governing amendment: [ADR-0032](../decisions/0032-codex-right-panel-primary-surface-for-orrery-conductor.md)

## 当前事实

- 单一 Git 仓库根为 `D:\coding warehouse\project-orrery`；protected `origin/main` 已包含 docs-only SC1 exact `a9369dd`，产品 source baseline 为 `9ee831f`。
- 项目作者权威根为 `AGENTS.md` 与 `docs/`；`.project-orrery.json` 选择 `authority_status: integrated` 和 `authority_model_version: 1`。
- ADR-0018 已将任务分发改为 authority-first：创建 Workstream 或追加实质范围前，中央协调者先提交 ADR／Design／Plan scope amendment／Pending Validation；任务消息只引用 exact SHA 和路径。U2.3、W7.3、CI7 与 v0.3.0 Phase 0 已按此流程登记/修订；旧 transcript 只保留为非权威 provenance。
- 当前公开 v0.2.0 的发布源仍是 `skills/project-orrery/`。tag／ZIP／checksum／release manifest 指向历史发布提交 `20fc95b`，不随 main 上的实验源码改变。
- `skills/orrery-dispatch/` 是 S0 独立两文件 source Candidate；它与安装／迁移／审计用的 `skills/project-orrery/` 分开，也不是未来独立 S1 Conductor repository。
- ADR-0031 已授权 S1 在独立 `orrery-conductor` repository 中实现只读 Codex plugin/MCP UI 兼容层。当前只有
  Project Orrery authority；外部 repository、实现、安装和 Release 尚未产生，live Graph binding 等待 accepted
  U2.5 delivery envelope。
- S1 Phase A 已在独立 repository 形成 clean `4e44d27...` 并安装本地开发插件，但其 inline conversation UI 被
  维护者拒绝。ADR-0032 现要求复用同一实现并以 Codex 既有 right Browser Panel 为主入口；修正版尚未实现。
- PO1 在不增加文件角色或号码服务的前提下，把 decision proposal/number allocation 边界投影进 dispatch Skill，并在 repository gate 检查当前树 numeric ADR 唯一性；它不扫描或锁定 peer Candidate 编号。
- 当前本机 Codex home 有一份从 local integration `8b73f26` 复制的 `orrery-dispatch` 两文件安装；该外部本机副本不属于 Git tree 或发布资产。
- 未发布的平台中立源码位于 `packages/project-orrery-{core,cli,observatory}/`。A4/U2.3/W7.3 local integrated Candidate 声明 Core 0.1.19、CLI 0.1.22、Observatory 0.1.19。Core API 为 1，组件总状态为 `unreleased`。
- 薄平台层位于 `adapters/{codex,harness-json,claude-code,deepseek-harness}/`；Harness JSON 0.1.2 同时提供 A4 inspect/route 与 W7.3 有界 relation suggest/inspect/decision 请求，其余 Adapter 为 0.1.1，均 `experimental`／`unreleased`。Adapter 不拥有 canonical 作者模板、State、ADR、route semantics 或 Authority 规则。
- 自托管观测台位于根 `scripts/docsite/`。本地 integrated Candidate 只保留 `Start Orrery.vbs`（隐藏控制台）与 `Start Orrery Console.bat`（单控制台）两个根启动入口、统一静态 builder 与单 loopback supervisor；Personal／Team／Maintenance／Workstream Graph 保持受管 consumer。
- ADR-0016／ADR-0025 的生产 Unified Shell 已在本地 integrated Candidate 实现：一个用户可见 listener／URL／导航壳，Broker／Coordinator 等内部 capability 由 supervisor 隐藏管理；legacy whole-shell rollback 改为内部 `serve_orrery.py --legacy`，不再作为第三个根启动文件。公开 v0.3.1 仍未切换到这组 U2.4 bytes。
- ADR-0028 已把 U2.5 注册为独立后续边界。Phase A clean `6596a9f...` 位于
  `codex/u2-5-shell-first-graph-cache` 独立 worktree，实现 Shell-first/cache 基础设施且未修改 W7.4-owned
  Graph presentation；当前 integration branch 未包含该产品。维护者已授权 Phase B 精确导入 accepted frozen
  W7.4 `fe75fc2...` 后继续，预览前仍无自动测试权限。
- ADR-0029 已接受显式 Workstream 分类与 dispatch 登记：当前 provider 42 nodes 中 33 无 series、35 无
  program/phase、27 两者皆无；strict history 37 records 中 29 无 series、30 无 program/phase。W7.5 尚未
  创建任务或写分类事件，现有缺口继续诚实显示为未登记且不得从名称/lineage推断。
- ADR-0030 已接受 fast Candidate freeze：实现任务在短结构检查/commit 后可停止为 validation-pending，耗时
  exact-SHA validation 独立运行。W7.4 已以 clean `fe75fc2...` 手工采用；`freeze-candidate` command/async
  orchestration 仍未实现。W3.1 已登记，中央 exact `c142f32...` 仅 bootstrap 两份严格 receipt schema；
  worktree removal 仍由 W6/W6.2 独立持有。
- U2.1 integrated Candidate 修复首轮体验：中文 app 导航、全页 stop、历史 Maintenance 证据降级和 W7.1 legacy/archive graph 显示；它没有创建 relation root、赋予 archive 执行权或放宽 Quick Remove 当前资格。
- W7.2.3 integrated Candidate 只重构 Observatory Graph presentation：从左到右的确定性 rank、固定可读节点、按 connected component 对齐的工程图路线、按链双向展开／收起、三 lens 真实端点、画布内 inspector 与移动 relation ledger。关系由实线／虚线／复合线和固定视觉尺寸箭头表达，不在线路上覆盖文字；画布支持锚点式 `Ctrl + 滚轮` 缩放。rank 通道为 88px，独立链只保留 44px 分组空隙；全站滚动条使用深浅主题适配。Core relation schema／facts、W7.1 archive 证据与执行边界未改。
- U2.2 integrated Candidate 把 app 入口和作者文档树组合进一个连续 sidebar/scroll rail，并把 Maintenance 改为 header refresh、四类筛选、8 行分页、折叠技术详情与仅 eligible 行可见的安全删除入口。它只改变展示和有界浏览器状态，不复制或改变 Core eligibility／preflight／authorization／receipt，也没有执行删除。
- U2.3 local integrated Candidate 的 Personal active-task projection 只读取共享 Git worktree registry、Git-common-private bounded session JSON 和 Maintenance cache；公开 HTML/JSON 隐藏本机完整路径与原始 finding，缺失／损坏／cache stale 的已登记任务保持身份可见并标为待刷新。Git-private 数据仍不进入作者文档、发布包或远程同步。
- W7.1 integrated Candidate 只为 relation 已引用且 live endpoint 缺失的 Workstream 读取有界 Git-common-private retired-session archive，恢复 closed/offline/current/superseded 轴；archive 不进入 active tip、apply/undo、Review Ready 或执行面。
- W7.4 accepted frozen `fe75fc2...` 已保存 37 个历史身份、移除 bulk history UI，并恢复 11 条可验证 archived
  lineage；full/compact 预览均为零重叠。它仍是 validation-pending Candidate，不是 Canonical、closed 或
  cleanup-ready。
- 当前 integration line 已由唯一 integrator 加入 strict `workstream-history-index-v1.json` schema bootstrap；它区分 `closed-workstream` 与未闭合的 `retired-session`，禁止任意 display/classification/reference 字段。W7.4 `fe75fc2...` 已消费该基线并实现 writer/consumer，但异步验证仍 Pending。
- W1–W7 协作源码已经进入 main：Git-private Workstream session、Scope/finding、review/integration/cleanup、Personal／Team projection、workspace maintenance、LAN discovery／manual Host switch、stacked lineage、relation event/graph、apply/undo/recovery contract 和只读 Graph consumer 均存在。
- W7.3 Candidate 已实现 ADR-0017 relation capture：versioned append-only Git-common-private proposal／confirmation／role／series store，exact same-project ancestry `derived_from` 自动写入，四类 gate `depends_on`、Integrator-only `absorbs`、Personal／Team human integrator CAS，以及 CLI／Harness suggest/inspect/decision 边界。Agent、session、remote central request 与旧 revision 均不能确认；旧 v1 无 gate 关系保持 Unknown。
- 当前 self-host 已显式登记 Authority A、CI、Unified U 系列，并保留 A4→A3、CI7→CI6 为待确认修复建议；没有从名称前缀推断或回写 effective 历史。另有真实 `W7.3-integration-acceptance` linked worktree 从 exact W7.3 implementation commit 自动形成 `derived_from`，对 CI6 的 integration gate 仍是非阻塞 proposal。
- 当前 Git-private capture 还保留四个同端点的 open automatic Unknown lineage proposals，来自 Phase 0
  task-base 历史变化；它们不是四个语义决定。scope revision 6 已获维护者授权，只通过 append-only
  `superseded` 事件保留一个 current proposal，不删除历史或自动确认关系。
- revision-6 self-host repair 已给三个旧 automatic Unknown proposals 追加 `superseded`，当前 pending 为一个
  Unknown lineage 加三个 distinct dependencies。现有 Core/UI 仍错误暴露 human Accept/gate 给
  `derived_from`；revision 7 Worktree correction 已恢复 Core-only mechanical authority，页面获维护者确认，
  source 已冻结并在 `74afb989...` 取得 Fast 19/19、Checkpoint 30/30；最终 docs-SHA `a2d7737...` 页面已接受。
- Graph projection 使用显式 program／phase／series metadata 组织任务，但 membership 绝不创建 relation、gate、closure 或 ownership。一个共享 semantic projection 同时供本地固定 `elkjs@0.11.0` 与显式手动 legacy engine 消费；ELK 是默认只读布局，失败时先显示同事实 ledger，不静默 fallback。comparison 保持默认关闭，冲突 lens 只消费有证据的确认冲突事实。
- CI5 将 27 个逻辑 Promotion shard 映射为每 OS 十个物理 lane；Fast 与 Promotion 分离，required check 名称保持不变。exact `9ee831f` 已通过 25-job 双平台 Promotion 并进入 main。
- 当前展示品牌为 Orrery。`project-orrery`、`project_orrery`、`.project-orrery.json`、v1 schema／receipt／hash domain 和 v0.2.0 资产继续作为稳定技术或历史标识。
- 非权威研究控制面位于 `experiments/context-routing/`；大型原始运行根为 `D:\coding warehouse\project-orrery-benchmark`，不属于 Git 仓库或发布包。

## Worktree 与事实作用域

- 一个 Workstream 使用一个独立 branch＋linked worktree／clone；主 worktree只用于唯一整合。linked worktree 共享 Git object store 和 refs，但拥有独立 HEAD、index 与工作目录。
- 当前本地整合阶段在 `.project-orrery.json` 显式选择 `refs/heads/codex/u1-u2-integration-baseline`，避免仍以旧 local `main` 计算 scope/merge base。该覆盖只属于本地 integration line；任何 protected-main/Promotion 候选必须先恢复 `refs/heads/main` 并重新绑定 exact SHA。
- `V0.3.0-final-rc` 已从 exact `88d80df...` 注册到独立 `codex/v0-3-0-final-rc` branch/worktree；scope revision 1
  仅完成只读 archive inventory 后停写。中央任务说明 revision 2 提交并由该 Workstream 刷新 scope 前，不能
  写产品、运行测试或把 Candidate/Worktree 状态称为 public release。
- release-input 产品提交已由唯一整合者选择性落到中央 `ef145180...`，没有合并任务分支的旧全局入口文档。
  任务分支和中央分支都保留；后续必须非破坏地汇合并由唯一整合者收口 State/PROGRESS/HANDOFF。
- Canonical／Candidate／Worktree／Local-only／Unknown 必须分别表达。Candidate HEAD 被 main 包含不自动产生 review package、closure record 或作者 Validation。
- Workstream session、review、closure、maintenance 与 relation transaction 存在 Git-private 区域；它们是协调证据，不进入作者文档或发布资产，也不能替代 State／ADR／Validation。
- 本机旧 session 的 lifecycle 可能落后于 Git ancestry。maintenance 在缺少 current closure／review／Validation 时必须保护目标；不得凭目录前缀、年龄或 branch 已进入 main 自动删除。
- `git worktree remove`、local branch delete、remote branch delete 和 ordinary-directory removal 是四种独立动作。当前产品只在本机人类确认后支持严格合格的 remove-worktree；branch 不随之删除。
- 2026-08-29 的 SC1 本机维护已归档并移除 W5D、CI4、R1、R2、R3、W6 六个 clean／closed worktree，只删除目录并保留全部 branch／commit。清理后为七个 registered worktree；并发创建的 `github-front-door-redesign` 及其余活动／待收口任务不在本轮范围。

## 结构与安全边界

- Core 持有 schema、manifest／兼容判断、Authority evaluator 与 canonical 作者模板；CLI 组合 Core 与 Observatory；Observatory 只负责派生投影。
- `orrery-operating-rules-v1` 的唯一 machine-readable owner 位于 Core `data/`，Skill `references/` 是 exact bytes 投影；CLI 收集仓库证据，Harness/Skill/Observatory 只消费，不成为第二个 evaluator 或 route owner。
- Skill project-template 是 canonical 作者模板的兼容投影；测试要求内容一致。旧 Skill 脚本是薄 wrapper，单独分发时回退冻结 v0.2 实现。
- Codex／Claude／DeepSeek Adapter 当前只声明 caller-provided attach；没有平台声明 launch／rebind／message。Adapter guard 不能阻止绕过 Adapter 的任意宿主写入。
- Team Mode 默认关闭；Personal 默认 zero-network。Team 只能同步版本化元数据，不能上传 Prompt／回答／transcript、源码正文、未 push diff 或成员凭据。
- W7B transaction 只写 Git-private confirmation／journal／receipt／compensation；真实 self-host 尚未执行 relation apply。Graph 只读，不提供 apply／undo／close／delete 按钮。
- Workspace Maintenance Phase 0–2 已实现；Phase 3 自动 worktree removal 和 Phase 4 OS scheduler 尚未实现。没有后台默认删除、daemon 或远程执行。
- authority-first 当前是作者流程硬边界；自动 Git-private dispatch receipt、CLI acknowledgment 和首次写入阻断尚未实现，不能把人工遵守写成宿主级强制执行。
- fast Candidate freeze 当前也是人工流程；没有命令或 scheduler。冻结不等于 validated、closed、integrated
  或 cleanup-eligible。

## 实现证据

- `.project-orrery.json`
- `packages/component-versions.json`
- `packages/project-orrery-core/`
- `packages/project-orrery-cli/`
- `packages/project-orrery-observatory/`
- `adapters/`
- `skills/project-orrery/`
- `skills/orrery-dispatch/`
- `scripts/docsite/`
- `scripts/ci/`, `.github/workflows/fast-validation.yml`, `.github/workflows/validate.yml`
- `tests/`
- [U2 Unified Observatory Validation](../validation/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 UX Acceptance Fixes Validation](../validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [U2.2／W7.2 Joint Acceptance](../validation/2026-08-29-u2-2-w7-2-unified-observatory-joint-acceptance.md)
- [U2.3 Navigation & Live Task Visibility](../validation/2026-08-30-u2-3-navigation-live-task-visibility.md)
- [W7.1 Archived Session Relation Projection](../validation/2026-08-29-w7-1-archived-session-relation-projection.md)
- [W7.2 Graph Readability](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [W7.3 Relation Capture & Confirmation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)
- [W7D Validation](../validation/2026-08-28-w7d-w7-integration-candidate.md)
- [CI5 Validation](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)

## 已知缺口

- Core／CLI／Observatory 尚无独立公开发行物、多组件 release pipeline 或 manifest v2。
- 默认 docsite／Skill template 尚未启用 Unified Observatory 或 Personal／Team／Maintenance／Graph；公开 v0.2.0 不包含这些能力。
- 没有真实双机 LAN、自动 Coordinator 选主、云 relay、多设备迁移或远程 shell／Agent／merge／delete。
- W7 relation store 没有 self-host native apply 记录；旧 session 到 post-main closure 的兼容收口仍需保守人工流程。
- ADR-0018 的自动 dispatch receipt、scope revision CAS、Adapter acknowledgment evidence 和 first-write enforcement 尚未实现。
- S0 Skill 仅在当前本机安装、未发布，也没有任务状态聚合、scheduler、relation confirmation 或执行权限。
- W7.3 focused Candidate `44ea200` 已进入本地中央合流；CI7 current fingerprint `0eea7f...` 在 source
  `f41b659...` 上取得唯一 Fast 3/3 与 Checkpoint 4/4 PASS，均为 evidence-eligible、zero rerun。两份 exact
  vendored ELK bundle 仍保持同一 SHA-256，只有两条路径级 `-whitespace`。exact-SHA 最终整页验收、non-main
  Windows／Ubuntu Promotion 与 main／public／default 尚未发生。当前 self-host 三条 `depends_on` 仍只是待人工
  确认 proposal；没有把它们宣称为 effective dependency。
- workspace maintenance 没有自动 removal 或 OS scheduler；关闭应用后不会定时执行。
- 当前 integrated U2.4 runtime 仍用全页 startup gate；U2.5 Phase A cache/input currentness/per-consumer
  readiness 只在 `6596a9f...` Worktree preview 有机械证据，browser hydration 尚未实现或验证。
- 已有 accepted frozen W7.4 history/archived-lineage Candidate `fe75fc2...`，但其异步 validation、中央整合、
  closure 与 cleanup authorization 均未完成。
- Claude Code 尚未完成认证后的真实模型路由；DeepSeek 与 Codex evidence 只覆盖各自记录的精确 runtime 范围。
- 自动 R1 脱敏导出器、跨平台 byte-for-byte archive 与 Brownfield Adoption 研究／Plan 均未实现。
