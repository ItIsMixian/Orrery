# 当前进度

Updated: 2026-08-31

## 当前阶段

Orrery v0.2.0 仍是当前公开版本。受保护的 `origin/main` 已包含 SC1 exact
`a9369ddeee0e74d4ddbe4bfc23a86b510d400457`；SC1 只收口文档，产品 source baseline
`9ee831f0d6f64306fe821f8c70229df54648d3eb` 已经包含平台中立
Core／CLI／Observatory、四个 Adapter、Broker-only docsite、Authority Meta Model M1／M2、
W1–W7 协作源、R3 品牌收口与 CI5 Promotion 优化。上述发布后能力仍为
`experimental`／`unreleased` 源码，不等于新的公开 Release。

| 线路 | 当前状态 | 下一安全动作 |
|---|---|---|
| Authority Meta Model | 模型 1、Core evaluator、内部 CLI claims、root-only opt-in projection 与本地 release-candidate gate 已进入 Canonical source；默认 production consumer、稳定公共 API 与公开模型 1 release 尚未发生 | 单独审阅 managed consumer switch／rollback，再由维护者选择真实 SemVer 与 candidate manifest |
| 多 Workstream 协作 | W1–W7 Canonical 基线与 ADR-0017 不变；W7.3 relation capture、program/phase/series projection、pinned ELK 与显式 legacy 后手已进入本地中央 Candidate | 只完成 exact-SHA Unified 整页验收；不在 Phase 0 重跑 feature suites |
| Unified Observatory | A4/U2.3/W7.3 已组合为本地 root-only/default-off Candidate：七入口导航、只读帮助/规则、轻量活动任务、关系待确认、密集维护和只读 Graph 共存；公开默认仍未切换 | 从干净 docs SHA 生成最终桌面/移动页面并由维护者接受，再注册 Final RC |
| Context routing 研究 | C1 Oracle v0.2 静态 controls 已通过；H1／H2／B／S 均未采纳 | 由维护者决定是否注册 C2 设计；不得自动创建或运行 Pilot 010 |
| 平台与 Adapter | Codex 精确范围和 DeepSeek rc.8 精确范围已有 runtime evidence；Claude 仍在认证前失败关闭；全部 Adapter 均未独立发布 | Claude 只在认证可用且另行授权时继续；其余工作转向发行设计或新的精确 runtime matrix |
| 文档治理 | D1 已冻结只读 finding contract、规则 registry 与 synthetic fixture；当前没有 `docs audit` 产品入口 | 维护者另行决定是否启动 D2 scanner／CLI；不自动改写 Markdown 或启用长度硬门 |

## 当前结论

- CI5 exact SHA `9ee831f` 已完成 Fast 与 Promotion：Promotion run `33235992711` 为 25/25 jobs PASS，Windows／Ubuntu 均聚合 390 tests／27 logical shards；同一 SHA 已进入受保护 `main`。十 lane 合计 23.9 job-min，测试步骤 14.352 分钟，派生 overhead 约 40%，达到冻结目标。
- self-host branch protection 继续要求 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`，并对管理员生效。普通 `main` push 只运行 Fast，不重复 Promotion。
- Authority M2 的 `candidate_ready` 不等于 `release_ready`；公开 v0.2.0 manifest 仍不声明模型 1。
- 协作源码已经 Canonical，但真实 self-host relation store 仍缺正式 native event／closure；Graph 的 legacy session 投影与产品能力不能混写。
- 当前 display brand 为 Orrery；`project-orrery` Skill／distribution／CLI／schema／协议与 v0.2.0 资产继续作为稳定技术或历史标识保留。
- Broker-only docsite 统一模型入口，但同一 OS 用户下的本机 Broker 只提供路由、缓存和预算门，不构成 Provider Key 进程隔离。
- `codex/u1-u2-integration-baseline` 曾在联合 feature merge `0eaad30` 吸收 W7.2.3 `30d44ff` 与 U2.2 `70e6ac9`；该历史节点组件为 Core 0.1.17、CLI 0.1.21、Observatory 0.1.16。联合 Fast 38/38 与真实 1440/390px 浏览器验收通过；44 项 Checkpoint 在既有 Maintenance fixture 上达到固定 90 秒预算，未冒充通过。它仍只作为后续中央 Candidate 的历史 child evidence。
- ADR-0018 已接受 authority-first Workstream dispatch：U2.3 已按两次任务说明版本完成并本地集成，W7.3 也已确认其 scope revision；自动 receipt／first-write enforcement 尚未实现。
- ADR-0022 已接受 ELK.js 作为 Workstream Graph 唯一正常 layout/routing engine；它不改变现有 Orrery 前端或
  事实选择。GX2 provenance、W7.3 clean Candidate 与中央接线已完成，维护者接受的产品方向保持不变；
  公开 release/default 仍未发生。
- ADR-0023 保留 frozen、manual、visibly-labelled legacy engine 并禁止静默回退；W7.3 focused closeout 与
  中央 current fingerprint Fast/Checkpoint 已完成，最终整页接受由 v0.3.0 Phase 0 单独持有。
- S0 `orrery-dispatch` 两文件 source 与 PO enforcement 已进入本地 integration line并安装到当前本机 Codex home；标准 Skill 校验、generic routing 与本地门通过。它未发布，也不是 S1 Conductor 或宿主级 first-write enforcement。
- PO1 source Candidate `93ddfb7` 已进入本地 integration line：dispatch Skill 强制非整合任务使用 `PO-DEC-*`，repository gate 拒绝同树重复正式 ADR 编号；A4 已规范化为 ADR-0019。
- A4/U2.3 在合入 W7.3 前的 local integration 为 Core 0.1.18、CLI 0.1.22、Observatory 0.1.18、Harness JSON 0.1.2；其 Fast 84/84、Checkpoint 89/89、Unified/Personal 25/25 和 390px Browser 回执作为 child evidence 保留，仍不等于 public/default/release。
- 当前中央组件为 Core 0.1.19、CLI 0.1.22、Observatory 0.1.19、Harness JSON 0.1.2。W7.3 `44ea200` 与
  CI7 `111f4ab` 已合流；current fingerprint `0eea7f...` 在 `f41b659...` 上一次 Fast 3/3、一次 Checkpoint
  4/4 PASS，均 evidence-eligible、zero rerun。旧 fingerprint 的 Checkpoint failure 保留。

## 活动计划与待办

- [ ] [Orrery v0.3.0 Final RC and Promotion](implementation/plans/2026-08-30-v0-3-0-release-candidate-and-promotion.md)：revision-10 已恢复 20/30；Checkpoint 14.991s allowed，Fast 因 setup 9.320s + actual-path deep check 0.817s = 10.300s 拒绝。revision 11 只把该深检移到 Checkpoint，Fast 保留两个 mapping 哨兵，再对新 fingerprint dry-run。
- [x] [GX1 Fireworks Tech Graph Evaluation](implementation/plans/2026-08-30-gx1-fireworks-graph-skill-evaluation.md)：隔离 Candidate `f5fd5af` 得分 8/12；仅接受为 W7.3 设计/几何辅助和选择性重写输入，不采纳第三方 runtime。
- [x] [GX2 ELK Layout Engine Evaluation](implementation/plans/2026-08-30-gx2-elk-layout-engine-evaluation.md)：维护者接受 ELK 0.11.0、W phase small multiples、typed stubs、独立 context 与现有 Orrery 视觉方向用于产品接线；不等于产品/测试/Release PASS。
- [x] [PO1 Decision Allocation Enforcement](implementation/plans/2026-08-30-po-decision-allocation-enforcement.md)：dispatch Skill、duplicate-number gate 与 A4→ADR-0019 中央规范化均已完成。
- [x] [S0 Orrery Dispatch Skill](implementation/plans/2026-08-30-s0-orrery-dispatch-skill.md)：两文件 source Candidate 与 PO enforcement 已本地集成，并只安装到当前本机 Codex home；未进入发布包，S1 Conductor 仍是独立后续事项。
- [ ] [Authority-first Workstream Dispatch](implementation/plans/2026-08-30-authority-first-workstream-dispatch.md)：人工 authority-before-dispatch 契约生效；先完成 U2.3／W7.3 exact-SHA acknowledgment，再另立自动 receipt／first-write enforcement 产品阶段。
- [x] [U2.3 Navigation & Live Task Visibility](implementation/plans/2026-08-30-u2-3-navigation-live-task-visibility.md)：导航/help、轻量全活动任务、“问文档”说明和中央移动复验已完成并本地集成；Promotion/public/default 仍未发生。
- [x] [W7.3 Workstream Relation Capture](implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)：clean `44ea200`、中央 merge `ae90974`、pinned ELK inventory、focused/browser 与 current central Fast/Checkpoint 已完成；最终全页 acceptance 转由 v0.3.0 Phase 0 持有。
- [x] [CI7 Validation Routing Precision & Total-Cost Diagnostics](implementation/plans/2026-08-29-ci7-validation-routing-precision-and-cost-diagnostics.md)：clean `111f4ab` 与中央 current fingerprint fresh Fast 3/3、Checkpoint 4/4 已完成；旧 refusal/failure 均保留，Promotion 仍由 Final RC 持有。
- [ ] [U2.2／W7.2 联合验收](validation/2026-08-29-u2-2-w7-2-unified-observatory-joint-acceptance.md)：本地联合 Candidate 已就绪；等待维护者真实体验，之后再决定 exact-SHA Promotion。
- [ ] [Authority Meta Model Plan](implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)：production consumer 与真实 release 选择仍未完成。
- [ ] [U2.1 Unified Observatory UX Acceptance](implementation/plans/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)：基础体验返工已进入联合 Candidate；W7.2/U2.2 后的维护者复验、public/default transition 与 Release 尚未完成。
- [ ] [多 Workstream 协作 Plan](implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)：Phase 5 self-host／发布未完成；真实多机、云 relay 与自动选主也不在当前支持范围。
- [ ] [Workspace Maintenance Plan](implementation/plans/2026-08-27-workspace-maintenance-and-scheduled-cleanup.md)：Phase 0–2 已进入 Canonical source；Phase 3 自动 worktree removal 与 Phase 4 scheduler 未开始。
- [ ] [Context-routing State](state/context-routing-research.md)：C2／Pilot 010 尚未获批。
- [ ] [平台 Plan](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)：Claude 成功认证／模型路由和所有组件独立发行仍未完成。
- [ ] [文档治理 Plan](implementation/plans/2026-08-21-document-governance-and-audit.md)：D2 scanner／CLI 尚未批准。
- [ ] [Rename／Compatibility Plan](implementation/plans/2026-08-28-orrery-rename-and-compatibility.md)：R3 已完成；R4 alias contract 与 R5 optional default transition 尚未启动。
- [ ] 跨平台 byte-for-byte archive 一致性、benchmark R1 自动脱敏导出与 Brownfield Adoption 研究继续延期。

## 最近完成

- [U2.1 Unified Observatory UX Acceptance Fixes](validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)：单一中文导航、Maintenance历史兼容与Quick Remove可发现性、W7.1真实Graph、Host发现说明、全局关闭服务及Windows stale-PID恢复完成；clean Fast 38/38、Checkpoint 44/44和浏览器验收通过。
- [U2 Unified Observatory Production Integration](validation/2026-08-29-u2-unified-observatory-production-integration.md)：真实单 URL shell、headless/debug launcher、consumer registry、安全/lifecycle 与桌面/移动浏览器验收完成，现进入本地整合体验。
- [W7.1 Archived Session Relation Projection](validation/2026-08-29-w7-1-archived-session-relation-projection.md)：有界只读 archive resolver 恢复 W5D closed/offline/current/superseded 轴，不产生执行权。
- [SC1 Closed Worktree Removal](validation/2026-08-29-sc1-closed-worktree-removal.md)：归档并移除六个 clean／closed worktree，只删除目录且保留 branch／commit；并发创建的无关 worktree 未触碰。
- [CI5 Promotion Throughput Optimization](validation/2026-08-29-ci5-promotion-throughput-optimization.md)：`9ee831f` 的 Fast、25-job Promotion、双平台 required checks 与 main fast-forward 已完成。
- [CI4 opaque CLI token reliability](validation/2026-08-29-ci4-opaque-cli-token-argument-reliability.md)：`a4b0ed3` Fast 2/2、Promotion 59/59 双平台通过并进入 main。
- [R3 Orrery brand-only closeout](validation/2026-08-28-r3-orrery-brand-only-closeout.md)：当前展示面收口为 Orrery，稳定技术 ID 与历史资产保持不变。
- [W7D W7 Integration Candidate](validation/2026-08-28-w7d-w7-integration-candidate.md)：W7 relation execution 与只读 Graph 经 exact-SHA 双平台门进入后续 Canonical main。
- [CI3 Fast dependency fix](validation/2026-08-28-ci3-fast-validation-dependency-fix.md)：fresh-runner discovery／aggregate dependency 顺序已由后续 verified SHA 覆盖。

完整演化见 [DEVLOG](DEVLOG.md)，逐次可复现证据见 [Validation](validation/README.md)。

## 风险与阻塞

- linked worktree 提供独立 HEAD／index／目录，但没有 OS 级路径沙箱；越界写入仍依赖 guard、工作目录纪律和审查。
- 本机旧 Workstream session 缺少统一的 post-main closure 证据；在 closure／review 不完整时，maintenance 必须继续失败关闭，而不能仅凭 branch 已进入 main 自动删除。
- W7B 的 apply／undo 只在隔离 Git fixture 验证；self-host 真实项目没有 apply 记录，Graph 没有执行按钮，中央 Team 没有执行权。
- v0.2.0 ZIP checksum 有效，但同一 tag 的 Windows／Linux 重建尚非 byte-for-byte 一致。
- 仓库外原始研究证据没有自动 R1 脱敏导出器或异地备份；不得批量复制进 Git。

## 下一里程碑

1. 对 Canonical W7/W6 做真实 self-host read-only／dry-run，先补 lifecycle／closure 证据再讨论删除或自动化。
2. 选择 Authority managed consumer，或批准 D2／C2／Claude 其中一条独立线路；不得把多个发布／安全决策绑在一次未经审阅的切换中。
