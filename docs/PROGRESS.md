# 当前进度

Updated: 2026-08-29

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
| 多 Workstream 协作 | W1–W7、Personal／Team Observatory、maintenance、relation execution 与只读 Graph 已进入 Canonical source；默认页面仍不启用这些 root-only 控制面 | 先做 self-host read-only／dry-run 与 lifecycle/closure 对账；任何 apply、删除或成员本机执行仍逐次确认 |
| Unified Observatory | ADR-0016 与 Approved Design 已接受；U1 只完成架构／非权威原型，生产统一入口尚未实现 | 从包含 W6.1／CI6／A3 的独立整合基线启动 U2 root-only 生产实现，保留现有 docsite 体验且不切换公开默认 |
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
- `codex/u1-u2-integration-baseline` 已组合 W6.1／CI6、A3 与 Accepted U1 文档，作为 U2 的 Candidate 基线；它在 exact-SHA 双平台门和后续推广前不冒充 `origin/main` Canonical。

## 活动计划与待办

- [ ] [Authority Meta Model Plan](implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)：production consumer 与真实 release 选择仍未完成。
- [ ] [U1 Unified Observatory Plan](implementation/plans/2026-08-29-u1-unified-observatory-architecture.md)：架构已接受；U2 production shell、launcher、真实 consumer composition 与人工体验尚未完成。
- [ ] [多 Workstream 协作 Plan](implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)：Phase 5 self-host／发布未完成；真实多机、云 relay 与自动选主也不在当前支持范围。
- [ ] [Workspace Maintenance Plan](implementation/plans/2026-08-27-workspace-maintenance-and-scheduled-cleanup.md)：Phase 0–2 已进入 Canonical source；Phase 3 自动 worktree removal 与 Phase 4 scheduler 未开始。
- [ ] [Context-routing State](state/context-routing-research.md)：C2／Pilot 010 尚未获批。
- [ ] [平台 Plan](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)：Claude 成功认证／模型路由和所有组件独立发行仍未完成。
- [ ] [文档治理 Plan](implementation/plans/2026-08-21-document-governance-and-audit.md)：D2 scanner／CLI 尚未批准。
- [ ] [Rename／Compatibility Plan](implementation/plans/2026-08-28-orrery-rename-and-compatibility.md)：R3 已完成；R4 alias contract 与 R5 optional default transition 尚未启动。
- [ ] 跨平台 byte-for-byte archive 一致性、benchmark R1 自动脱敏导出与 Brownfield Adoption 研究继续延期。

## 最近完成

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
