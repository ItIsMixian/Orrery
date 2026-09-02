# 文档系统 State

Updated: 2026-08-31

Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md) | [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md) | [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md) | [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md) | [ADR-0012](../decisions/0012-document-governance-and-information-lifecycle.md) | [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md) | [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md) | [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md) | [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md) | [ADR-0018](../decisions/0018-authority-first-workstream-dispatch.md) | [ADR-0019](../decisions/0019-portable-operating-rules-and-authority-route-preflight.md) | [ADR-0020](../decisions/0020-workstream-program-and-phase-hierarchy.md) | [ADR-0022](../decisions/0022-elkjs-workstream-graph-layout-engine.md) | [ADR-0023](../decisions/0023-explicit-legacy-graph-layout-fallback.md) | [ADR-0028](../decisions/0028-shell-first-observatory-and-incremental-graph-cache.md) | [ADR-0029](../decisions/0029-explicit-workstream-classification-and-dispatch-registration.md) | [ADR-0030](../decisions/0030-fast-candidate-freeze-and-asynchronous-validation.md)

## 当前事实

- Orrery 已用自身权威链管理本仓库。Agent 入口为根 `AGENTS.md`；维护者入口为 `docs/PROGRESS.md`、`docs/HANDOFF.md` 与本地 Observatory。
- ADR-0018 已把 authority-first 分发纳入权威链：首次任务和中途实质变更都必须先形成并提交 Plan／dated amendment 与 Pending Validation，必要时先完成 ADR／Approved Design；task transcript 只传 exact SHA／路径并不承担作者文档职责。U2.3 与 W7.3 是第一批按此规则补录的在途任务。
- S0 `orrery-dispatch` Skill Candidate 只把上述作者流程翻译为宿主操作：读取目标权威链、提交任务说明版本、发送 SHA／paths 并等待 scope acknowledgment。它不新增作者文档角色，不把 transcript 升级为事实，也不取代目标项目 `AGENTS.md`。
- PO1 已把 ADR-0007 的临时决策规则加入 `orrery-dispatch`：非唯一 integration worktree 使用 `PO-DEC-*` Proposed 文件，只有显式唯一整合者按当前 integration index 分配正式编号。repository gate 拒绝同一树内重复 numeric ADR；A4 已在本地 integration worktree 规范化为 ADR-0019。
- 更新后的 `orrery-dispatch` 已仅安装到当前本机 Codex home；安装副本与 source 两文件 hash 一致。该本机存在事实不产生项目决定、公共兼容或其他用户安装事实。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation、Snapshot、Library 与派生视图职责分离。Authority Meta Model 定义角色与语义；Product Seed 只约束 Orrery 自身目标。
- 文档事实显式区分 Canonical、Candidate、Worktree、Local-only、Historical 与 Unknown。普通功能分支只同步受影响 subsystem State／Plan／Validation／DEVLOG；根 PROGRESS／HANDOFF 由唯一整合者在合流阶段维护。
- PROGRESS 与 HANDOFF 是当前控制入口，不是历史总账。SC1 已把 CI5、R3、W7D 等 post-main 事实从 Candidate／pending 表述收口为 Canonical，并把历史运行细节留在 DEVLOG／Validation。
- ADR-0012 的 Documentation Governance Policy 已进入 Canonical source。D1 只实现内部 finding schema／registry 与 synthetic fixture；当前没有 `docs audit` scanner／CLI、acknowledge store、Observatory governance 页面或自动修复。
- Canonical 作者模板位于 Core package；Skill project-template 是 v0.2 兼容投影。Observatory tools 不属于作者事实，并由 component manifest 管理。
- 默认静态 docsite 从 Markdown 生成 `docs/_site/index.html`；生成物禁止手工编辑且不进入作者事实或发布包。
- AI Q&A、briefing、roadmap、milestones、radar、Authority projection、Personal／Team／Maintenance 与 Workstream Graph 都是派生视图。它们只能消费受约束输入并保留 source／scope／Unknown，不能创造 State、ADR、批准或 Validation。
- Authority shadow、diagnostic 与完整 projection 使用彼此独立的显式开关；默认 legacy build 保持。完整 M2.2 projection 仅由 root-only `build_authority_projection.py` 启用，失败关闭回无 claim 的 legacy 页面。
- Personal／Team／Maintenance／Graph 已作为 root-only/default-off sibling page 进入 Canonical source。U2.1 Candidate 的主视图用“交付／待确认的任务或历史状态／工作区清理建议”表达 Personal；Team 为 metadata-only/request-only，Maintenance 只显示当前资格与本机确认，Graph 只读消费完整且验证有效、hash-bound 的 native 或 legacy/archive relation evidence。
- ADR-0016 与 Approved Unified Observatory Design 已接受“一个用户入口／URL／导航壳、受管隐藏 helper”的目标。当前本地中央 Candidate 在现有 docsite 阅读、搜索、AI 与作者信息架构上，用一个连续 sidebar/scroll rail 组合中文 app 入口和可折叠项目文档树，并加入 A4 规则帮助、U2.3 活动任务、W7.3 关系待确认与 ELK 只读 Graph；Maintenance 使用密集有界队列和折叠技术详情。协议值只在技术详情显示，U1 synthetic prototype 仍不是 UI 规范，公开默认尚未切换。
- ADR-0028 已接受 Shell-first 启动与增量 Graph cache。U2.5 Phase A clean exact `6596a9f...` 已在独立
  Worktree 实现可导航 bootstrap shell、Graph 独立 lifecycle、Git-private validated cache、HEAD/session
  currentness 与 bounded shutdown；尚未本地整合。维护者已授权 Phase B 消费 accepted frozen W7.4 exact
  `fe75fc2...`，真实 Graph hydration preview 仍 Pending。
- ADR-0029 已接受分类校准与未来 dispatch 显式登记。当前没有 `任务分类待确认` consumer、分类 envelope
  强制门或历史分类事件；W7.5 必须先展示证据来源和批次内容，维护者接受前保持零分类写入。
- ADR-0030 已把阻塞式 closeout 拆为快速 Candidate Freeze 与异步 Validation。冻结阶段只写最小 receipt/Pending
  指针；详细 Validation/State/DEVLOG 在异步结果或 integration 时事件驱动同步。W3.1 自动化尚未实现；中央
  `c142f32...` 只提供其 L3 所需的两份严格 receipt schema bootstrap。
- U2.3 local integrated Candidate 将 app rail 收敛为七个固定入口，把路线与趋势从作者文档树移入 app 区，并以唯一 floating Ask Docs 和顶栏只读帮助／系统状态面板替代独立问答／Authority 页面。Personal 使用 Git registry、Git-common-private 有界 session metadata 与现有 Maintenance cache 的轻量 active-task projection；启动不逐 worktree 读取源码、Scope、ignored 或 diff，重证据只在目标详情／刷新时读取。
- W7.2.3 integrated Candidate 将真实只读 Graph 改为单一从左到右 DAG：固定可读卡片、中文 rank lane、工程图式实线／虚线／复合线、固定 10px 箭头、每链独立展开和收起、锚点式 `Ctrl + 滚轮` 缩放，以及默认关闭的画布内技术详情抽屉。dependency／conflict 只从各自真实端点建图；空 dependency 不显示孤立 active tips。桌面以 88px rank 通道和 44px 独立链间隔显示主图并保留 1×1px 语义 ledger，390px 用同事实列表替代微型图；文档根、侧栏、画布与详情滚动条共享深浅主题变量。
- Team 页面没有远程执行权；W7 Graph 没有 apply／undo／close／delete 按钮；Maintenance 不把建议或 receipt 升级成作者事实。
- ADR-0017 的 Git-private relation proposal／confirmation 已进入本地中央 source。Unified Observatory 的 Personal／Team 页面增加“关系待确认”收件箱：Personal 仅在本机 human role capability 成立时显示 accept/change-gate/defer/reject，Team／central 始终 request-only；Graph 继续只读，只投影 effective／proposed 与 gate。
- Graph projection schema 2 将 program／phase／series 作为只读分组元数据，不把 membership 当因果边；主状态机械区分正在进行、等待人工确认、状态待刷新／证据过期、历史任务、缺少任务记录、未登记和关系证据不足。本地中央 Candidate 用固定本地 ELK 布局同一 semantic projection，桌面图与移动 ledger 保持同事实；Core `compare_pairs` 只作为默认关闭的黄色 comparison review，红色 conflict lens 只接受带 location／impact／source 的明确冲突证据。画布不含确认／应用／撤销动作。
- W7.4 Worktree Candidate 的 active history projection 已切换到 strict schema：37 条记录重新分类为 6 closed
  与 31 retired（12 implementing、18 validating、1 review-ready）；旧 37 条错误 closed-summary bytes 原位保全、
  不再被 reader 接受。关系页面已移除完整历史目录、bulk controls、
  identity-only cards 和目录入口；只投影具备语义 relation、明确 series 或严格 archived lineage 证据的任务。
  14 条 current lineage 中 11 条恢复，3 条因目标归档证据不足保持无边。索引不可用时明确写“历史索引不可用”，
  不把空白冒充已验证无历史。Relation Inbox 主卡改为 Core-owned 中文问题、建议原因、接受／拒绝后果与证据限制，
  raw IDs、revision、enum、rationale 和 provenance 只在“技术详情”中显示。维护者截图发现的 ELK 跨层级端口
  错误已按语义边界修正；随后又修复 history candidate blanket suppression，恢复四条显式 series 展示线。
  当前页面不再提供历史目录或 identity-only 画布入口。真实浏览器完整默认态随 Git-private U2.4/U2.5
  输入增量为 25 nodes／18 routes；已接受的 23 nodes／15 routes 逐项仍在，ELK ready 且 failure hidden。
  同画布 compact 为 15 nodes／8 routes／3 summaries，展开一组为 23／16／2，之后可恢复完整默认。
  full 模式的顶层 compound composition 使用 ELK box 而非会遗漏 nested-series 最终伸展范围的 rectpacking；
  绘制后按最终 SVG rect 执行全节点 pairwise overlap postcondition，非零即 failure、不得宣称 ELK ready。
  重启后的 full 与 compact 实测 overlap pairs 均为 0。
  页面同时把 lifecycle 与 organizational classification 分轴：provider 42 nodes 的 missing series／program-phase／
  both 为 33／35／27，strict history 37 records 的 missing series／program-phase 为 29／30；full 可见 25 nodes
  显示 17／21／14。缺失项明确标记“未登记”，不从 task code、名称、布局或 lineage 推断分类。
- 动态 docsite 的模型调用统一经过 Broker。Provider 配置与凭据按端点绑定，同源 POST、body gate、预算、缓存和错误脱敏已实现；同用户本机 Broker 不宣称秘密隔离。
- 当前展示品牌为 Orrery；目标项目标题仍由模板 token 定制。历史 `Project Orrery` 与稳定 `project-orrery` 技术标识按 ADR-0015 保留。
- A4 local integrated Candidate 不增加第九个一级导航；既有 `authority` 身份显示“事实与规则”，分栏投影目标项目 Seed 与 Core-owned Orrery 工作规则，legacy/managed/readiness 技术状态默认折叠。Ask Docs 在 root Unified 宿主中先消费 route receipt；Skill template 只能 advisory。

## 同步与生命周期规则

- 新建 Workstream 或追加实质范围前，先提交 authority baseline；Agent 必须在首次／恢复产品写入前读取 exact paths、确认 source revision 并更新 Git-private Scope。只有紧急 stop 可以先发送，后续实现方向仍须等待文档提交。
- 实现或验证完成后，同步受影响 State、Validation 与 DEVLOG；停止点或风险变化时同步 HANDOFF；当前线路改变时同步 PROGRESS。
- Preview acceptance 后的 Candidate Freeze 不要求先完成详细证据叙述；它只绑定接受指纹、结构检查与 exact
  commit。耗时验证完成后再同步完整证据，避免文档写作阻塞实现任务退出。
- Accepted ADR、Approved Design、Plan checklist、Agent 回执或 Git commit 都不能单独证明 implemented／validated／released。
- State 只保留当前事实与缺口；逐次命令、失败轮、性能数字和 exact SHA 进入 Validation／DEVLOG。
- Documentation finding 只是 `info`／`warning`／`review-required` observation；长度、密度和风格不能单独成为硬门。
- 观测台和 AI 只能展示或解释 source facts。缺失 provider、schema、scope、evidence 或 relation store 时必须显示 Unavailable／Unknown，而不是推断安全或完成。

## 实现证据

- `AGENTS.md`, `docs/`, `.project-orrery.json`
- `packages/project-orrery-core/src/project_orrery_core/templates/`
- `packages/project-orrery-observatory/`
- `scripts/docsite/`
- `skills/project-orrery/assets/project-template/`
- `tests/test_project_orrery.py`
- `tests/test_documentation_governance_contract.py`
- `tests/test_personal_observatory.py`
- `tests/test_team_observatory.py`
- `tests/test_workspace_maintenance.py`
- `tests/test_workstream_relation_graph_observatory.py`
- `tests/test_unified_observatory.py`
- `tests/test_portable_operating_rules_and_authority_route.py`
- [Documentation Governance Plan](../implementation/plans/2026-08-21-document-governance-and-audit.md)
- [U2 Unified Observatory Plan](../implementation/plans/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 UX Acceptance Fixes Plan](../implementation/plans/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [U2.2 Navigation & Maintenance Plan](../implementation/plans/2026-08-29-u2-2-unified-navigation-workspace-maintenance-ux.md)
- [U2.3 Navigation & Live Task Visibility Validation](../validation/2026-08-30-u2-3-navigation-live-task-visibility.md)
- [W7.2 Graph Readability Plan](../implementation/plans/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [U2.2／W7.2 Joint Acceptance](../validation/2026-08-29-u2-2-w7-2-unified-observatory-joint-acceptance.md)
- [W7.2 Graph Readability Validation](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [Authority-first Dispatch Plan](../implementation/plans/2026-08-30-authority-first-workstream-dispatch.md)
- [Authority-first Dispatch Contract](../validation/2026-08-30-authority-first-workstream-dispatch.md)
- [S0 Orrery Dispatch Skill Validation](../validation/2026-08-30-s0-orrery-dispatch-skill.md)
- [PO1 Decision Allocation Validation](../validation/2026-08-30-po-decision-allocation-enforcement.md)
- [W7.3 Relation Capture & Confirmation Validation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)

## 已知缺口

- 本地中央 v0.3.0 Candidate 新增 release notes、onboarding 与 upgrade/rollback 三份作者指南；它们只说明
  create-only、managed backup、offline runtime 和 publication 分权，不产生 release 或 Validation PASS。

- D2 scanner／CLI、真实项目 soft-budget 配置、finding acknowledge／defer persistence、State／实现链接时效检查与自动修复均未实现。
- HANDOFF 已完成职责压缩，但没有自动治理工具；后续仍需人工确认安全边界的当前有效性。
- 完整国际化未实施，U2.1 只完成 zh-CN 主界面与集中 display vocabulary；没有完整英文模式。
- Authority portable inventory/route 已作为 A4 source Candidate 接线，但没有稳定公共 parser/domain API、默认 production projection、通用宿主 Hook 或公开模型 1 release。
- Personal／Team／Maintenance／Graph 尚未接入默认 docsite、Skill template 或公开 release。
- W7.4 root-only self-host preview 的首版六条历史、ELK 跨层级端口错误、历史 series 线缺失、37 卡散点和
  后续独立历史目录均先后被维护者拒绝。当前 Worktree 已恢复 11 条严格归档 lineage 和显式系列线，删除所有
  bulk-history UI；真实浏览器为 ELK ready、failure hidden，该完整关系基线已获维护者接受。
- 维护者已接受上述完整关系图作为冻结默认。W7.4 revision 5 在同一画布新增 `显示完整关系`／`折叠历史`；
  compact 只折叠深层只读历史连通子图，保留 current、attention、pending、Unknown、dependency、conflict、selected
  与一跳历史上下文。摘要保留底层关系数／类型和真实 entry/exit，点击原地展开并可重新折叠；无新目录或列表。
  公开默认、Team 同步、cleanup 自动门与任何 Release
  均未改变。
- Unified Observatory 仍只是本地 root-only/default-off integrated Candidate；尚未进入默认 docsite、Skill template、managed-tool inventory、installer 或公开 Release。`start-docsite.bat`／`serve.py` 继续作为 legacy rollback 与当前公开兼容入口。
- 当前 integration branch 仍是 U2.4 的全页启动卡；U2.5 Phase A 产品只存在于 clean Worktree Candidate
  `6596a9f...`，未接入 integration/public runtime。Phase B Graph hydration、post-acceptance focused tests 与
  publication evidence 均不存在。
- Team 真实双机、云 relay、多设备、远程执行与 Graph 图形执行入口不存在。
- authority-first 的自动 dispatch receipt、scope revision CAS、CLI acknowledge 与宿主首次写入阻断尚未实现；当前只有已接受且人工执行的作者流程契约。
- `orrery-dispatch` 已在当前本机安装但未发布；它只能指导宿主遵守流程，不能机械阻断绕过 Skill 的写入，也不能外推为其他主机可用。
- W7.3 relation capture 已进入 root-only/default-off 本地中央 Candidate，exact page `a2d7737...` 已由维护者接受；没有 public/default consumer、远程 confirmation、中央执行或真实双机验收。public template 与 final-archive runtime 现在由独立 Final RC 持有。
- `807096d...` 的真实静态构建暴露 U2.3 lightweight Personal 与 W7.3 Relation Inbox 的锚点不兼容：导航仍在，
  但 Personal 被 quarantine。scope revision 5 已先登记，修复页面由维护者预览前禁止运行测试流程。
- revision-5 动态预览已恢复 Personal/Team inbox placement，但显示四个同端点 automatic Unknown lineage
  proposals。revision 6 修 Core append-only supersession，而不是在 UI 中隐藏重复；维护者看修复页前仍禁测试。
- revision-6 新服务已把 pending 收敛为四条，但 lineage 卡片仍显示不适用的 Accept/gate 控件。revision 7
  保留人类 defer/reject，同时把 effective `derived_from` 恢复为 Core-only；真实 1280/390 页面已获维护者
  确认，product/mapping source 已取得 current Fast/Checkpoint；最终 docs exact-SHA `a2d7737...` 已接受。
- Brownfield Adoption 只有保守接入边界，没有研究结论、Approved Design 或 Implementation Plan。
