# 测试覆盖 State

Updated: 2026-08-31

## 当前验证体系

- 验证分为 `Fast → Checkpoint → Candidate → Promotion`。Fast 只提供局部反馈；Checkpoint 证明 Workstream checkpoint；Candidate 运行完整本地门；Promotion 绑定 non-main exact SHA、规定 OS 和 required checks。
- Fast 使用 15 秒预算；Checkpoint 使用 90 秒预算；完整 Promotion 保留每个 final unittest ID、动态 build、结构／docsite／链接／发布包／diff gate 与安全预算。
- CI6 integration baseline inventory 为 404 unique unittest IDs、27 logical shards、10 physical lanes/OS、88 Fast、89 Checkpoint；U2 登记后为 415，U2.1 将四组新断言折叠进既有 owner test IDs，registry inventory 保持 415。`team-relations-execution` 保持独立 300 秒 Promotion 预算。
- CI6 新增 repo-local `scripts/ci/validate_change.py`，从 Git diff、Git-private Workstream subsystem／expected writes 与版本化 mapping registry 自动选择 exact test IDs，并生成绑定 HEAD/base/dirty fingerprint/registry 的 tier receipt。直接 `unittest` 仍可调试，但不能声明正式 Fast／Checkpoint 证据。
- CI7 Worktree Candidate 将宽 Observatory mapping 拆为 `observatory-shell`／`observatory-graph`／`observatory-maintenance`／`observatory-team-personal`；actual Git paths 优先，宽 expected-write 与路径重叠失败关闭，subsystem 只在无路径证据时保守 fallback。receipt 追加非权威 `cost_diagnostics`、四类 over-budget 诊断、单次 feature triage 与第二独立 Workstream recurrence advisory；这些字段不参与 PASS/FAIL、Authority、release 或自动任务。
- CI7 maintainer amendment 当前新增 versioned composable `all_of` acceptance gates（experience／contract／measurement／operation／matrix）、exact contract/blob + relevant-surface fingerprint、legacy shadow/new-task opt-in/explicit adoption、human-only experience/operation authority 与 mechanical evidence 的 prior human contract approval。Personal 仍 zero-network；Team 只投影 request-only bounded metadata。
- Opt-in routed validation 现由 one-run Git-private lease 绑定 Workstream/scope/stage/fingerprint/exact IDs/p95/budget/receipt inputs；runner 在加载测试前拒绝 missing/forged/stale/expired/consumed/wrong-stage lease。unchanged success 返回 prior receipt；failure/timeout 为 `validation-cost-blocked`，无 human override 不可重跑。iterating 只有 non-evidence focused（20 tests／20s／120s per scope）；Fast/Checkpoint predictive headroom 为 20 IDs/10s 与 single 30s/total 60s，未修改原 15／90 秒预算。
- lane runner 为每个 logical shard 启动独立 Python 子进程，保留原 shard result 并生成 lane receipt；失败、缺失、重复、extra、manifest/SHA/OS/order drift 或取消均使 aggregate 失败关闭。
- required check 名称仍为 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`；main branch protection strict 且 enforce-admins。

## 当前通过证据

- CI5 本地 contract/mutation 17/17 PASS；inventory 为 390／27／10／57／81，无 missing、duplicate 或 dead selector。
- CI5 本地 Fast 57/57 为 3.235952s；最终两次 Checkpoint 均为 81/81，42.806990s／43.071302s，预算未调高。120.961576s 的真实 Git journey 只保留在 Promotion。
- exact SHA `9ee831f0d6f64306fe821f8c70229df54648d3eb` 的 Fast run `33235942078` 成功；Promotion run `33235992711` 为 25/25 jobs PASS，Windows／Ubuntu required checks 双 PASS，各自聚合 390 tests／27 shards。
- CI5 hosted wall time 为 3m56s；20 个 lane jobs 共 23.9 job-min，lane 内测试步骤共 14.352 分钟，派生 setup/checkout/install/artifact overhead 约 40%，满足 `<30 lane job-min` 与 `<45%` 的 advisory 目标。
- 同一 exact SHA 已进入 main，main Fast run `33236225082` 成功。该证据关闭 CI5 hosted acceptance，不创建新 Release。
- SC1 开始前本地主工作树 clean；`validate_ci.py --all`、integrated structure、Fast 57/57 与 `git diff --check` 均通过。
- W6.1／CI6／A3 整合时保留 CI6 schema-5 manifest，并把 A3 七个低成本 Authority consumer tests 登记进 data-only mapping registry；CI contract 与 A3 7/7 专项通过。Hosted exact-SHA Promotion 仍由整合候选单独取得。
- U2 Unified Observatory focused 11/11 与最终 adjacent 12/12 PASS；CI6 final Fast 根据当前 diff 选择 49 项并 49/49 PASS，final Checkpoint 选择 54 项并 54/54 PASS（evidence-eligible，未超预算）。真实动态单 URL、静态无控制、Host／Origin／cookie／token、Team／Authority／AI／Maintenance 不升级、helper/marker 回收和 desktop/390px browser 均有独立证据。
- U2.1 新增 legacy Maintenance/current refresh、legacy/archive graph/empty refusal、startup-cached graph endpoint 与全局 stop 资源回收四组断言，并折叠进既有 owner test IDs；registry byte-for-byte 不变，不扩大历史 W6.1 `<24` Checkpoint selector。focused 五套 47/47、折叠后 exact methods 5/5、Unified 11/11；最终 CI6 Fast 选择 38 项、Checkpoint 选择 44 项，均 evidence-eligible PASS，详见 U2.1 Validation。
- W7.1 的四个 archived-session 安全回归已登记为 `team-lan-core` Promotion-only medium evidence，不进入 Fast／Checkpoint；其分支 focused 19/19、exact Fast 57/57、Checkpoint 85/85 及真实 self-host read-only graph 均通过，最终整合 Candidate 仍需 Promotion 重放。
- W7.2 将布局、折叠、lens 端点、inspector 与 desktop/mobile ledger 断言折叠进既有 Workstream Graph owner IDs，CI inventory／registry 不变。W7.2.1 覆盖 `Ctrl + wheel`、路径焦点、无线路标签、按链收起和 dependency 空态；W7.2.2 增加固定 marker 和全站主题 scrollbar；W7.2.3 固定 88px rank／44px component 间隔并拒绝 synthetic blank row。focused Graph＋Unified 18/18 与 JS syntax PASS；真实 self-host 桌面节点无重叠、边不穿框，390×844 无页面横向溢出，console error/warning 为空。最终 CI6 Fast／Checkpoint receipt 见 W7.2 Validation。
- U2.2 用既有 owner tests 固定单一连续侧栏、15-entry/8-row Maintenance 队列、四类筛选、eligible/zero-eligible、折叠 policy/history 和移动紧凑行；隔离 Fast 34/34、Checkpoint 40/40 与三档浏览器通过。与 W7.2.3 合流后，联合 Fast 38/38 与真实 1440/390px 页面通过；联合 Checkpoint 的 44 项在既有 Maintenance real-Git fixture 上达到固定 90 秒预算，因此未声明 evidence-eligible PASS。
- S0 `orrery-dispatch` 使用 `skill-creator` quick validator 检查 frontmatter、名称与 scaffold placeholder；文件 inventory 固定为 `SKILL.md`／`agents/openai.yaml` 两项。该结构门不证明宿主级 first-write enforcement、实际 task creation 或公开安装兼容性。
- S0 首轮 Fast dry-run 对未登记的新 Skill 路径失败关闭；任务说明 amendment 后只把 `skills/orrery-dispatch/**` 加入 generic `release-packaging` mapping。最终 dry-run 为 44 tests／0 unknown，正式 Fast 44/44 在 15 秒预算内通过；test IDs、budgets、stage authority 与 Promotion coverage 不变。
- PO1 扩展 repository gate：当前树 numeric ADR 编号必须唯一，`0000` 模板／历史和 `docs/decisions/proposals/` 不参与正式编号分配。函数级 synthetic fixture 验证 unique/proposal/0000 通过、duplicate `0018` 拒绝；没有新增 unittest ID 或改变 CI tier inventory。
- A4/U2.3 中央合流把 portable inventory 的 hash domain 固定为 LF canonical bytes，使 Windows CRLF/LF checkout 等价且额外内容仍判 tamper；A4/Adapter/wheel 15/15、Unified/Personal 25/25 通过。正式 routed Fast 84/84（9.470s/15s）与 Checkpoint 89/89（17.312s/90s）均 evidence-eligible；390×844 中央 Browser 为零横向溢出、help x=0/width=390、唯一功能 Ask Docs、0 console warning/error。
- W7.3 `5fee848` 的 Core/capture/permission suites 与原 Browser evidence 可保留；`05c83b` 虽增加图内 connector，
  维护者仍拒绝其 55% 默认缩放、共享关系总线、线标签重叠和常驻 inspector 挤压。后续门固定 100% readable
  reset、按 lens 分边、pairwise coincident/crossing/bend/stretch/segment/gap/label-clearance 几何指标、专用 390px
  topology 和真实截图人工验收；旧 PASS 不足以关闭 UI gate。GX1 `f5fd5af` 的 8/12 结果只提供几何参考。
- CI7 原 Candidate `a520ebc` 已缩窄 Observatory routing 并增加 total-cost diagnostics，但尚未阻止 Agent 在
  人类接受前运行正式层级或对同一 fingerprint 原样重跑。维护者已批准 additive acceptance policy v1：组合
  gates、surface fingerprint、Git-private validation lease、focused iteration 累计预算、predictive refusal 与
  timeout cost-blocked；15／90 秒预算和各层证据含义不变，产品实现仍 Pending。
- ADR-0020/W7.3 新门要求 program/phase schema、explicit self-host W repair、prefix negative controls、membership
  non-escalation、same-source/target bundle 与 mixed-semantics refusal、branch/trunk hit testing、semantic selection
  以及桌面/移动视觉验收；未通过前不得把 W grouping 或 route bundle 写成产品事实。
- ADR-0021 Final RC 只消费 current child receipts 并运行 integration/release-owned gates；默认手工重放全部
  A4/W7.3/CI7 suites 被禁止。RC 专属门是 manifest、migration/restore、deterministic package、final runtime、
  dual-platform Promotion 与 publication identity，且同 fingerprint 遵守 CI7 no-repeat。
- W7.3 registry 覆盖 relation schema/fixture、exact-base 幂等 lineage、cycle、role spoof、CAS、stale、legacy、privacy、zero-network、Harness bounded JSON、program/phase/series non-authority、status taxonomy、comparison/conflict 分离以及 pinned-ELK semantic/layout contract。revision-17 focused program/Graph suites为 13/13 PASS；JS byte-safe syntax、vendor inventory和组件版本清点 PASS。scope revision 18 的两条 exact `-whitespace` 属性、vendor SHA-256 与完整 staged diff check 均 PASS。
- W7.3 当前 total succession 自托管投影在桌面/移动均为 19 nodes／14 edges。Browser focused closeout 覆盖 1440×900 默认 100%／fit 46%／reset 100%、语义色 edge selection 与只读 inspector，以及 390×844 same-fact ledger；两端页面横向 overflow 为 0，console warning/error 为 0。中央 current fingerprint 已取得 Fast 3/3 与 Checkpoint 4/4 PASS；最终整页 acceptance 仍必须绑定后续 clean docs SHA。
- Final RC exact `76a6961...` 的 Candidate dry-run 为 100 IDs、0 unknown、timing allow；唯一 fresh lease
  `404cbf0e...` 完成 100/100 PASS（66.346133s、zero rerun）。两次 exact-Git package byte-identical，完整
  Windows final runtime PASS。Promotion run `33451288289` 的 36 个失败 ID 保留为旧 SHA 证据；新 SHA 尚待
  Windows/Ubuntu Promotion，不用本地重复全量 451 项。
- revision-18 exact `a0a728b...` 的 fresh Candidate 56/56（2.096941s）、双根 package 与完整 final runtime
  PASS；run `33454661325` 最后 5 个 ID 的本地 closure 为先 3/5、再只跑剩余 2/2 PASS。新 SHA 尚待 Promotion。
- 原始 `a520ebc` CI7 routing/cost 实现的 focused contract/portfolio 5/5、完整 `test_ci_validation` 25/25 与 CI contract PASS；当前 inventory 为 421 exact IDs／27 shards／10 lanes／92 Fast／98 Checkpoint。W7.2 Graph-only 从 CI6 的 `collaboration-maintenance + observatory-ui`／23 Checkpoint（含 Maintenance fixture）收敛为 `observatory-graph`／2（不含 fixture）；U2.2 Maintenance 为 22 项且保留真实 Git fixture；Unified security 为 4 项有界 adjacency。该 pre-amendment 开发树 routed Fast 42/42 为 8.057895s，Checkpoint 42/42 为 7.526136s；它们不替代下条 amendment exact-SHA 事实。
- Amendment assertions 并入现有 CI7 final test ID，因此 Promotion inventory 仍为 421 而不是通过增加 final IDs 扩张；focused policy/lease/p95/no-repeat stable sweep 16/16 PASS。exact `290482f` 唯一 Fast 对 42>20 在 test loading 前 predictive refusal，保持 non-green 且未重试／未由 Checkpoint 替代；唯一 Checkpoint 42/42 PASS（16.417209s/90s，evidence-eligible）。中央旧 fingerprint 的 Fast 3/3 PASS 与 Checkpoint 组合门 failure 均保留；修正后 current fingerprint `0eea7f...` 在 `f41b659...` 上以 fresh lease 完成 Fast 3/3（0.804195s test runtime）和 Checkpoint 4/4（2.580301s），均 evidence-eligible、zero rerun。

## 覆盖面

- `tests/test_project_orrery.py`：安装、非覆盖升级、发布包、更新兼容、凭据与模板投影。
- Authority suites：fixture/evaluator、compatibility、projection、migration/restore、AI non-escalation 与 release-candidate gate。
- Adapter suites：Codex、Harness JSON、Claude Code、DeepSeek Harness 的薄层、归档、依赖失败与生命周期。
- Collaboration suites：W1/W2 session／Scope／finding、W3 review/integration/cleanup、Personal／Team、LAN harness、lineage、maintenance、relation graph 与 apply/undo/recovery contract。
- Unified Observatory suite：versioned registration/discovery、collision/escalation fail-closed、quarantine、static boundary、single-URL runtime、HTTP security、consumer non-escalation、helper lifecycle 与 legacy rollback。
- Documentation governance suite：provider-neutral finding schema、11 类正负 synthetic fixture、soft-budget advisory 与零写入／零网络边界。
- A4 suite：Core inventory/schema/digest/unknown-version/tamper、Skill/Core/template drift、CLI/Harness receipt、10 个跨 subsystem 四轴 conformance 场景、route mutation/absence gate、Ask Docs preflight、new/brownfield byte preservation 与 Unified Authority static/dynamic projection。
- Context-routing suites：24-task corpus、Pilot 002–009 frozen control packages、读取代理、JSONL audit、retention、Oracle v0.2 与 contamination/failure controls。
- Repository gates：integrated installation、isolated docsite、Markdown links、forbidden artifacts、release dry build、workflow/static contract、secret boundary 与 `git diff --check`。

## 证据解释边界

- GitHub Promotion 证明 exact source SHA 在指定 runner 上通过，不证明公开发布、其他 runtime、真实多机或模型自然语言正确。
- Agent receipt 只属于自述；JSONL 是事后审计。没有可工作的实时 Hook 阻断，不能宣称直接读取被执行前拦截。
- synthetic Git fixture、loopback HTTP 和 in-app Chromium 分别证明确定性 contract／本机 transport／页面行为，不外推为真实双机 LAN、远端执行或生产可靠性。
- 合法 skip／expected failure 保留原语义；被中断、没有 `Ran`／`OK` 或缺少 exit code 的命令不算通过。
- 历史失败轮保留在 Validation／GitHub Actions；后继 exact SHA 通过不改写原失败事实。

## 验证证据入口

- [Validation 索引](../validation/README.md)
- [U2.2／W7.2 Joint Acceptance](../validation/2026-08-29-u2-2-w7-2-unified-observatory-joint-acceptance.md)
- [S0 Orrery Dispatch Skill](../validation/2026-08-30-s0-orrery-dispatch-skill.md)
- [PO1 Decision Allocation Enforcement](../validation/2026-08-30-po-decision-allocation-enforcement.md)
- [U2.3 Navigation & Live Task Visibility](../validation/2026-08-30-u2-3-navigation-live-task-visibility.md)
- [U2 Unified Observatory Production Integration](../validation/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 Unified Observatory UX Acceptance Fixes](../validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [W7.1 Archived Session Relation Projection](../validation/2026-08-29-w7-1-archived-session-relation-projection.md)
- [W7.2 Workstream Graph Readability](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [W7.3 Workstream Relation Capture & Confirmation](../validation/2026-08-30-w7-3-workstream-relation-capture-confirmation.md)
- [CI5 Promotion Throughput Optimization](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)
- [CI4 opaque token reliability](../validation/2026-08-29-ci4-opaque-cli-token-argument-reliability.md)
- [R3 brand-only closeout](../validation/2026-08-28-r3-orrery-brand-only-closeout.md)
- [W7D integration](../validation/2026-08-28-w7d-w7-integration-candidate.md)
- [Authority M2 integration](../validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)
- [W1/D1/C1 integration](../validation/2026-08-22-w1-d1-c1-canonical-integration.md)
- [Context-routing State](context-routing-research.md)

## 已知缺口

- v0.3.0 release-input Fast 75／Checkpoint 81 与 bounded Focused 均在测试加载前拒绝。后续 Candidate dry-run
  在 merge `0f82d565...` 上选择 81 tests，acceptance=`shadow-allow`、timing=`allow`、runner_errors=[]；
  `successful=false/evidence_eligible=false` 只是所有 dry-run 的固定非证据语义，reuse refusal 不阻止 fresh
  Candidate。scope revision 4 的 exact `ac44630...` Candidate 为 80/81；唯一 failure 是
  `test_ci_validation.py` 的 fixture-ID 期望漏掉已存在的 `release-candidate-packaging`。scope revision 5 只修
  这一行；新 fingerprint `f4530713...` 的 dry-run allowed，唯一 fresh Candidate 在 `ba230555...` 以 81/81
  PASS、zero rerun、evidence-eligible 完成。旧失败未重试、拆批或改写。
- corrected final runtime 的 Codex/Unified/upgrade/migration/dependency/Skill lifecycle 已通过，但 final ZIP
  direct Harness validate 在 CLI JSON 前因 extracted `assets/project-template/` 未被 runtime context 解析而
  non-green；invalid request 仍 exit 2。scope revision 8 exact `e120aaa...` 修复后 Candidate 36/36、双根
  package 与完整 final runtime 均 PASS；旧 `ba230555...` 结果未复用。
- exact `e120aaa...` Promotion run `33449930707` 在 test/lane 前失败：`test_inventory.py --lane-list` 的 stdout
  混入 docsite discovery 日志，导致 `$GITHUB_OUTPUT` invalid format；required checks 正确失败关闭。scope
  revision 9 只稳定 machine-list stdout 和 AI-disabled discovery，不改 inventory/lane/coverage。初始
  `14f771f...` Candidate 41/42 的 bare `_common` test-module collision 未重试；final `4556db3...` Candidate
  42/42 PASS，Promotion inventory 仍为 421 IDs。
- exact `4556db3...` Promotion run `33451288289` 完整记录每 OS 451 tests/27 shards/10 lanes，但 Ubuntu 33、
  Windows 36 个 ID non-green。修复 Candidate 为 `76a6961...`；在该 SHA 的新 Promotion 通过前不能宣称
  dual-platform 或 release-ready。

- 动态图形 reader 依赖测试默认可跳过；高风险 UI／HTTP 改动仍需显式动态与浏览器验证。
- CI7 clean Candidate 与 fresh central Fast/Checkpoint 已完成；exact non-main Windows／Ubuntu Promotion 仍待 Final RC。本地 cost diagnostics 只证明机械测量与 advisory 计算，不证明宿主 token usage、未来节省或整体 ROI。Hosted/public acceptance enforcement 未启用，仍须维护者另行决定。
- Unified runtime composition test 当前用 full Personal fixture 替代真实 U2.3 lightweight panel，因此没有覆盖
  Relation Inbox 对已移除 `.po-foot` 的依赖；`807096d...` 页面在人工 DOM 检查中发现该缺口。revision 5
  必须先改为真实轻量契约并给维护者看页，之后才允许 fresh routed validation。
- relation capture 现有 idempotence 只覆盖 same exact base，不覆盖 task-base A→B 时旧 automatic Unknown
  proposal 的 supersession。revision 6 增加 exact lifecycle regression；测试代码可先写，但维护者预览前不得执行。
- relation capture 还缺少“任何 human role 都不能接受 `derived_from`”的明确回归，Unified 也未断言 lineage
  卡片无 gate/accept。revision 7 已写入这两项契约且页面获维护者确认；测试尚未执行，下一步只走 CI7
  dry-run 和 current-fingerprint one-run leases。
- post-freeze 两组 dry-run 均在加载测试前失败关闭：先发现两个未登记新 ID，折叠后再发现
  `relation_inbox.py` unmapped。revision 8 不增 test ID，而是建立 exact relation-capture surface、把 inbox
  归入 Unified shell，并用 data-only portfolios 防止错误选择 slow Maintenance fixture。
- revision-8 real-window dry-run 已无 unmapped/registry drift，但 Fast 25 超 20，且 exact Core owner timing
  Unknown；mapping-only 3/4 窗口因漏掉产品而弃用。revision 9 只运行一次非证据 Core owner，并把四个现有
  Brand 深检移到 Checkpoint、保留两个 Fast 哨兵；预计 20/30，Promotion 覆盖不变。
- revision-9 Fast 20/20 PASS；Checkpoint 29/30，唯一 failure 是 hardcoded portfolio ID list。补一行后
  `test_ci_validation.py` 触发 ci-control，使新 dry-run Fast 41/23.297s 拒绝、Checkpoint 51/27.988s allowed。
  revision 10 撤回两条新 portfolio/一行 list，保留 precise mappings；失败 fingerprint 不重跑。
- revision-10 rollback 后为 20/30；Checkpoint 14.991s allowed，Fast 因 setup p95 9.320s + actual-path deep
  check 0.817s = 10.300s 拒绝。revision 11 只把该 existing test 移到 Checkpoint，Fast 仍有 inventory/mutation
  两个 mapping 哨兵；无 ID/预算/Promotion 变化。
- revision-11 final fingerprint `4b4c56c...` 在 `74afb989...` 上完成 Fast 19/19（0.170343s）与 Checkpoint
  30/30（7.119383s），均 evidence-eligible、zero rerun。旧 Fast green/Checkpoint failure 与后续 predictive
  refusals全部保留；direct Core focused exit code 丢失，结果保持 Unknown，exact owner 仍由 Promotion 执行。
- Phase 0 final page `a2d7737...` 在 1440×900/390×844 完成同事实 Browser review：零横向溢出、空 console、
  4 pending、lineage 无 Accept/gate、Team 0 actions、Graph 0 decision actions。Final RC runtime/Promotion 未运行。
- CI6 已有保守自动影响分析；Fast／Checkpoint evidence reuse 当前只实现 versioned refusal contract，跨 SHA Promotion reuse 与远端 runner cache 仍不存在。
- Context-routing 没有实时 Hook、自动 R1 脱敏导出或异地 raw evidence backup。
- v0.2.0 archive 尚无 Windows／Linux byte-for-byte 一致性门。
- Claude 认证后真实模型路由、真实双机 LAN、远程／中央 relation confirmation、自动 worktree removal 与 OS scheduler 没有验收证据。
- Unified Observatory／Authority 没有默认 production consumer 或公开 release evidence；Documentation D2 scanner／CLI 尚未实现。
- 纯 Skill 指令仍没有强制 pre-model hook；A4 只机械保证 Core/CLI/Harness 与 root Unified Ask Docs 路径，其他宿主保持 advisory/Unknown。
