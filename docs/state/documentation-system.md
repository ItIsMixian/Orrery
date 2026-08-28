# 文档系统 State

Updated: 2026-08-28
Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md) | [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md) | [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md) | [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md) | [ADR-0012](../decisions/0012-document-governance-and-information-lifecycle.md) | [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md)

## 当前事实

- Project Orrery 已在本仓库正式采纳自身权威链。
- Agent 入口是根 `AGENTS.md`；维护者入口是本目录 `README.md`、`PROGRESS.md` 与本地观测台。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation 和 Snapshot 已各有独立职责。
- ADR-0009 已把这些职责、各对象 lifecycle、独立 Decision／Implementation／Validation claim dimensions、fact scopes、evidence categories 和 derived-view constraints 正式定义为 Authority Meta Model；`docs/core/principles.md` 明确只是 Project Orrery Product Seed。
- 文档事实现在显式区分 Canonical（integration ref 已集成）、Candidate（功能分支 HEAD）和 Worktree（本地未提交）三个作用域；分支 State 只能陈述候选事实，不能冒充 canonical 当前状态。
- 根 `PROGRESS.md` 与 `HANDOFF.md` 是集成视角入口，不是历史总账：PROGRESS 只保留当前线路、未完成事项、阻塞和近期里程碑，完整演化与逐次证据分别进入 DEVLOG／Validation。普通功能分支应让代码、测试和 subsystem State 同行，并在合流时由唯一整合者同步全局入口，避免多个 Agent 持续争写同一份全局状态。
- ADR-0012 已进入本地 Canonical，并建立独立于 Authority Meta Model 的 Documentation Governance Policy：它按文档角色规定当前／历史边界、事件驱动同步、责任式拆分、soft review budget 和人工审查闭环。它不是新的作者文档类型，也不授权自动改写。
- 当前 self-host 文档已采用治理入口：PROGRESS／Authority State 完成首轮职责压缩；HANDOFF 因包含大量安全接续细节，被记录为后续人工 review candidate，尚未做专项压缩。
- ADR-0008 已接受默认 zero-network Personal Mode、手动开启 Team Mode、Local-only 元数据和中央只读／本机执行边界。最终候选包含显式 opt-in W4 Personal 指挥台和不进入作者工作树的 W5A Team 配置、Member／Host、metadata sync、只读聚合、请求与本机决定回执；只有 containing ref 为 main 时才是 Canonical。Team 页签与自动发现明确保持 next-phase。
- 根观测台由模板 v0.2.0 安装；其输出 `docs/_site/index.html` 为可重建生成物。
- 未发布 Core 包现持有 canonical 作者文档模板；Skill 下的 project-template 是兼容投影，测试要求作者模板内容一致。Observatory 工具不属于作者事实，并由独立组件清单管理。
- 未发布 Codex Adapter 只把 Codex 调用路由到目标仓库根 `AGENTS.md` 和平台中立 CLI；它不携带 State、ADR、Validation、canonical 模板或项目摘要，因此没有形成第二套文档事实。
- AI 问答、项目简报、路线综合、里程碑和趋势雷达保持可选，且没有事实权威。Candidate 动态观测台已给这些输出附加不可由模型覆盖的 `derived-ai-view` 非权威 receipt；问答另有可见提示。Authority report 缺失时保留 `Unknown`，Candidate shadow 也只作为 `shadow-only` context，不会被 AI 输出升级成 State、ADR、批准或 Validation。
- Authority 诊断页面与 sidecar 分开 opt-in：`ORRERY_AUTHORITY_SHADOW_REPORT` 只生成可丢弃 report，`ORRERY_AUTHORITY_SHADOW_VIEW=1` 才显示只读诊断面板。面板显式标注非权威／未切换，只展示 comparison health、scope 和计数，不展示或创造项目 claims。
- 本地 Canonical baseline 通过 root-only `build_authority_projection.py` 增加第三个独立开关
  `ORRERY_AUTHORITY_PROJECTION_VIEW=1`：它把与 M2.1 bundle 精确 reconciliation 的 Core effective decision、
  role claims、Unknown、scope／visibility 和 source link 投影到 dashboard。开关缺省关闭，关闭即回到逐字节
  legacy 输出；失败不产生部分页面。原 `build_docsite.py` 与发布模板逐字节一致，root-only package-path
  injection 不进入 legacy module；发布 Skill 模板和默认 managed entry 均未切换。
- 动态观测台把 AI 服务设置入口放在顶栏、主题切换按钮左侧；静态 HTML 不注入设置入口，仍保持只读。
- 动态观测台的问答、仪表盘、趋势雷达、连接测试与独立 Q&A CLI 都只构造 Broker Provider；OpenAI、DeepSeek 和 Custom 只是上游注册项。项目 `ai-config.json` 的有效 Provider 恒为 `broker`。
- 默认本机托管 Broker 使用专用 Provider 凭据 namespace、client token、缓存、single-flight、模型白名单和预算门；一次“保存并启用”不强制额外测试请求。
- 本机托管只提供统一路由和成本控制，不隔离同一 OS 用户进程；只有在独立 OS 身份或等价外层隔离下运行外部 Broker 时才能隔离 Provider Key。
- 手动刷新、设置与问答写操作都要求同源 POST；旧查询参数 GET 不再触发模型调用。
- Canonical W1 Phase 0 已为 `AGENTS.md` 的七个 subsystem 区块增加显式稳定 ID。Core registry parser 只读取这些 ID 与已有 `docs/state/*.md` 链接；重复／保留 ID 或缺失 State Doc 失败关闭，并且不会因路径推断创建新 State。该 registry 是权威入口的机器投影，不是新的作者事实源。
- W1 Phase 1 把 Workstream session 保存为 Git 私有、可重建运行元数据，并由 CLI 从 Git 机械派生 branch／OID／dirty／scope、stale、lifecycle 与 routing 摘要；create／guard／route／attach 都不会自动改写 State、Plan、Validation 或根进度入口，也不要求 Agent 固定生成 Manifest／Receipt。
- W2 只写 Git-private control metadata：`scope-observation` 保留 committed／staged／unstaged／untracked／expected 来源；finding、acknowledgement 和历史处置是可重建协调记录，不成为新的 State／ADR／Validation。
- `worktree overlap` 与 `scope inspect` 保持只读；`scope refresh` 和 `finding acknowledge` 只在本机更新私有 session。L2 确认记录成员、理由、时间与 Scope Revision，Agent／中央来源被拒绝；缺失对端保持 Unknown／Unavailable。
- W3 Candidate 延续同一事实模型：review package、decision 与 closure record 只保存在 Git-private 管理区，是可审计的协调证据而非作者 State／ADR／Validation。package 先保存原始日志链接和结构化事实，再附可选的 `derived-non-authoritative` AI 摘要；摘要不能覆盖失败证据、满足人类 reviewer 计数或创造 Authority。
- W3 workspace inventory／cleanup bundle 仍是本地派生协调视图：Git metadata、private session／closure、项目允许根和显式候选是来源，Legacy unmanaged／Unknown 不因目录名、前缀或年龄升级成 Orrery 所有或可删事实。closure v2 与其 Git-private action-log 引用保留原路径、OID、review／Validation、分类、操作者及调用者自述动作；receipt 不能证明工具执行了删除，也不进入作者文档。
- W3 的 State alignment 只检查受影响实现与既有 subsystem State 是否同行，ADR alignment 检查临时 ID、正式编号冲突和引用；工具不会自动改写或编号作者文档。功能分支只同步受影响 subsystem State、Plan、Validation 与 DEVLOG，根 PROGRESS／HANDOFF 仍由唯一整合者处理。
- W4 Worktree Candidate 的 Personal Observatory 不解析作者文档来重新判断 Git／Scope／finding／Authority，也不重写 W3 review／integration／cleanup 规则。它作为总览仪表盘的 sibling page 由侧栏单独进入，总览本身不承载 Personal 内容。页面按人的阅读顺序呈现“项目现在怎么样／先看这些／谁在推进什么／影响到哪里”：首屏使用确定性本机计数与一句当前焦点，不把 OID、fact scope 或 finding 枚举当作主叙事；待审、阻断与可清理候选来自 W3 Core，raw package hash、OID、path、七类 inventory、closure／receipt 则下沉到默认折叠的技术证据。
- W4 通过 Workstream session 的 `review_package_id` 调用 W3 freshness／eligibility，而不是扫描目录猜审查队列；bounded inventory 只消费 W3 的 Git metadata／private session／closure／允许根／显式候选来源。四类 cleanup action 在页面只显示资格、授权与 `performed=false`，没有表单或执行入口。provider 缺失、失败、schema 不兼容或存在显式 excluded-worktree 隔离边界时，W1/W2 页面继续可用，W3 区域明确显示 Unavailable／Unknown；隔离边界下自动 W3 provider 不运行。远端、无 session 或不可访问证据也不表达为全局零冲突。
- W4 health Candidate 进一步把 Personal 首屏固定为“交付状态／当前阻断／需要对账／工作区卫生”。历史 Direct、stale session、absent-session Unknown 和 legacy inventory 不再累加成当前危急；只有双方 current 的 Direct 进入当前 blocker。当前 Candidate 无 session 时明确显示未登记／无法判断交付资格；Primary root 显示 protected canonical root。完整 Unknown 仍在对账或卫生层可追溯。
- W5B Candidate 在同一 Observatory 增加独立 Team sibling page。Team disabled 时显示 Personal zero-network、enable／serve 分离与 metadata-only/request-only 安全边界；启用后只投影 Core `team-read-only-projection`、Git-private config、Member → Workstream、presence 和 request receipt。动态入口为 root-only／loopback-only，默认／静态 docsite 不启动 socket，也没有把 Team UI 加入 managed-tool 白名单或公开模板。
- W5C Worktree Candidate 不改变上述投影来源，只把 Team sibling page 改为人类控制面：首先总结“现在怎样／下一步做什么”，再呈现成员与工作任务、待处理请求；handled request 与 Coordinator／Host／heartbeat／revision 等诊断默认折叠。派生页面仍没有权威或执行能力。
- W6 Worktree Candidate 增加独立“工作区维护” sibling page，投影 Git-private maintenance scan／queue／authorization／receipt、保护／Unknown 原因、共享策略和 branch 动作边界。静态 Personal 构建只读且按钮禁用；root-only loopback 动态入口才允许本机确认。页面不把建议、授权或 receipt 升级为 State／ADR／Validation，也不回写作者文档；Team 页只能发送 `cleanup` request，不能把中央决定变为 execute。
- W5D Worktree Candidate 在 Team sibling page 增加 discovery candidate、join confirmation、connection／reconnection 和 Coordinator generation／manual Host switch 状态；所有网络动作仍需本机显式触发，enable 本身不广播，页面不接收任意 URL／命令或执行请求。Personal sibling page 读取 Scope lineage summary，把显式 stacked chain 作为可折叠的派生视图显示 parent／task-base OID／inherited path 数和 chain 内 unique finding；Legacy／Unknown 不按 branch 名猜测，也不被伪装为 resolved finding。
- CI1 Worktree Candidate 的 inventory、timing result、aggregate receipt 与 Fast artifact 都是 machine-readable Validation evidence，不是 State／ADR／Promotion 事实。Fast 输出显式标注非 Promotion；只有冻结 exact SHA 的双平台 aggregator 与既有 required checks 能形成后续推广证据，且 hosted 性能目标仍须远端实测。
- W5E Worktree Candidate 只改变 Team 派生页面的信息层级：去除重复摘要，把四项状态与三个关键本机控制置顶，并以齿轮弹窗承载低频诊断。组合式接口草案继续位于 Library，Brownfield Migration 只进入 HANDOFF 接续约束；二者没有升级为 ADR、公共 API、Plan 已实施或 released 能力。
- W7A Worktree Candidate 的 relation record／graph／plan 与 Git-common-private event 都是协调控制面，不是作者 State／Plan／Validation。legacy `base_workstream_id/task_base_oid` 只读投影不会改写 session；graph source links 可以回到 Git-private／Validation 证据，但不得被 Observatory 或 AI 升级为项目权威。
- W7A Core graph 的 node 分开输出 lifecycle phase、runtime condition、evidence freshness、Scope、primary/affected subsystem、visibility、observability 与安全 source links；edge 输出 lifecycle/evidence/source links，pair plan 输出 active tips、Unknown 与 compare/suppress reason codes。Core 不输出颜色、坐标、布局、折叠或 UI 文案。W7C-B 的图形派生必须消费该 versioned graph，不能重新解释关系或隐藏保守 Unknown。
- W7C-A Worktree Candidate 的 `design-exploration.md` 与静态图原型共同位于隔离 `experiments/` 根；它们明确标为 provisional／non-authoritative，只列出 W7A 需要冻结的 consumer contract，不新增 ADR、Approved Design 或公共 schema。图与 accessible list 都从同一 synthetic fixture 派生，证据链接只能回到 fixture register，不能形成项目事实。
- W7C-B Worktree Candidate 将 W7C-A 视觉证据作为实验输入保留，但生产 sibling page 只投影 corrected W7A Core v1 graph／plan。页面的 Succession／Dependency／Conflict lens、折叠、筛选、SVG、ledger 与 inspector 都是 derived/read-only view；Unsupported/invalid schema、relation root absent、dangling evidence、legacy Unknown、unsafe link 或 provider failure 会清空全部 graph facts并显示 Unavailable/Unknown，不把局部数据升级为可信事实。

## 同步状态

- Pilot 001–004 已在 Research State、DEVLOG、PROGRESS 和实验报告之间建立链接。
- 详细原始运行不复制进 Docs。
- 公开用户文档仍由 `README.md` 与 `README.zh-CN.md` 承担。

## 实现证据

- `AGENTS.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/design/self-hosting-documentation-system.md`
- `docs/design/document-governance-and-information-lifecycle.md`
- `docs/implementation/plans/2026-08-21-document-governance-and-audit.md`
- `scripts/docsite/build_docsite.py`
- `scripts/docsite/build_authority_projection.py`（root-only M2.2 opt-in projection）
- `scripts/docsite/serve.py`
- `scripts/docsite/_llm.py`
- `scripts/docsite/llm_broker.py`
- `docs/decisions/0006-broker-only-docsite-provider-gateway.md`
- `docs/validation/2026-08-19-broker-first-docsite-gateway.md`
- `adapters/codex/SKILL.md`
- `adapters/codex/adapter-manifest.json`
- `packages/project-orrery-core/src/project_orrery_core/collaboration.py`
- `packages/project-orrery-core/src/project_orrery_core/review.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json`
- `tests/test_collaboration_contract.py`
- `tests/test_collaboration_w3.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/personal_observatory.py`
- `scripts/docsite/build_personal_observatory.py`
- `tests/test_personal_observatory.py`
- `packages/project-orrery-core/src/project_orrery_core/team.py`
- `packages/project-orrery-cli/src/project_orrery_cli/team.py`
- `tests/test_collaboration_team.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/team_observatory.py`
- `scripts/docsite/serve_team_observatory.py`
- `tests/test_team_observatory.py`
- `packages/project-orrery-core/src/project_orrery_core/maintenance.py`
- `tests/test_workspace_maintenance.py`
- `tests/test_collaboration_lineage.py`
- `tests/test_lan_collaboration_harness.py`
- `docs/operations/lan-team-preflight.md`
- `docs/decisions/0014-dynamic-workstream-succession-contract.md`
- `docs/design/dynamic-workstream-succession-contract.md`
- `packages/project-orrery-core/src/project_orrery_core/workstream_relations.py`
- `packages/project-orrery-cli/src/project_orrery_cli/workstream_relations.py`
- `tests/test_workstream_relations.py`
- `scripts/ci/test_inventory.py`
- `scripts/ci/run_test_shard.py`
- `scripts/ci/aggregate_test_results.py`
- `docs/validation/2026-08-27-ci1-tiered-parallel-validation.md`
- `experiments/workstream-graph-visual-prototype/design-exploration.md`
- `experiments/workstream-graph-visual-prototype/fixtures/workstream-graph.provisional.v1.json`
- `docs/validation/2026-08-28-w7c-a-workstream-graph-visual-prototype.md`

## 已知缺口

- 当前观测台界面主要为中文，完整国际化仍未实施。
- D1 已建立内部 finding schema／registry、11 组合成 fixture 和 dependency-free contract validator；尚未实现 `docs audit` scanner／CLI、真实项目 advisory 配置位置与阈值、acknowledge／defer 持久化、State／实现链接时效检查或任何自动修复。该 Core contract 也未导出为稳定公共 API。
- W3 已实现证据优先审查与清理资格；当前 W5D Worktree Candidate 在 W4 health／W5C UI／W6 maintenance 上增加显式 LAN discovery、join、manual Host switch 与 lineage chain 投影。默认 docsite／发布模板不加载动态 Team／Maintenance；Phase 3 自动删除、Phase 4 scheduler、富成员管理、真实双机/LAN、自动选主与云 relay 仍未实现，当前事实作用域由 containing ref 决定。
- W7A 尚未实现 W7B 的真实自动发现／migration／本机确认 apply／undo；W7C-B 也不提供任何执行按钮。中央 Team 视图保持 request-only，未来本机确认接线必须在 W7B 完成后另行评审。
- W7C-A 仍只验证 synthetic visual consumer；W7C-B 已实现真实 Core consumer、safe source-link projection、Unknown／Local-only 保留、provider/schema fail-closed 与 Observatory 信息架构，但当前仍是本地 Worktree Candidate，未进入默认 docsite、Skill template、managed tools、release manifest、hosted Promotion 或公开 v0.2.0。
- Authority Meta Model 已有 Candidate fixture、experimental Core evaluator、self-host 模型选择、managed shadow sidecar／诊断面板与 AI non-escalation guard，但仍无稳定公共 parser／domain API、默认 Authority 页面 projection、consumer production switch 或公开 release 实现。
- M2.2 已有进入本地 Canonical baseline 的 root-only、显式 opt-in 完整 Authority projection，但没有改变上述默认／发布边界。
