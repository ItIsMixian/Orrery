# 当前进度

Updated: 2026-08-21

## 当前阶段

Project Orrery v0.2.0 是当前公开版本；本地 `main` 已在其后集成平台中立 Core／CLI／Observatory、Codex 与 Harness JSON Adapter、Broker-only docsite、多人协作设计，以及 Authority Meta Model M1／M2。这些后续能力仍是本地 Canonical、`experimental`／`unreleased` 实现，没有形成新的公开 Release。

当前工作集中在四条相互独立的线路。详细历史进入 [DEVLOG](DEVLOG.md)，可复现证据进入 [Validation](validation/README.md)，这里仅保留当前控制面。

| 线路 | 当前状态 | 下一安全动作 |
|---|---|---|
| Authority Meta Model | 模型 1、Core evaluator、完整内部 CLI claims、root-only opt-in Observatory projection 与本地 release-candidate gate 已进入本地 Canonical baseline；默认 production consumer 和公开 release 未切换 | 审阅 managed consumer 的 production switch 与回滚证据，再由维护者选择真实 SemVer／candidate manifest |
| 多 Workstream 协作 | ADR-0007／0008 与 Approved Design 已接受；当前只有人工独立 worktree、唯一整合者和三层事实作用域 | 实现 Personal foundation Phase 0 的 machine contract；继续禁止在共享主目录并发开发 |
| Context routing 研究 | Pilot 009 的 P/S 装置与 Scope 证据有效，但质量门失败，没有策略获准进入发布 Skill | 不调用模型地完成 task／Oracle v0.2 的分层 verdict、结构化 State、paraphrase 与 mutation controls |
| 平台与 Adapter | Phase 0–3 已本地集成；Codex 精确 runtime 范围有 verified 证据，Harness JSON 有 Windows／Ubuntu CI；组件仍未独立发布 | 另行规划 Phase 4，并在明确授权后才选择第二个真实 Agent／Harness 平台 |

## 当前结论

- 公开事实仍以 v0.2.0 Release 为准；本地 Canonical 实现、runtime-verified 范围与 released 能力必须分别表达。
- Authority Model 1 已由 self-host 项目显式选择，但公开 v0.2.0 项目仍是 `legacy-unversioned`；普通工具升级不得替用户选择模型。
- Authority M2 的 `candidate_ready` 不等于 `release_ready`：缺少默认 managed consumer 的 production evidence 和维护者选择的实际发布版本。
- 多 Agent 目前具有可执行的人工安全工作法，但没有自动 session、主 worktree 守卫、重叠检测、review／integration CLI、Personal 指挥台或 Team telemetry。
- Context-routing 的 H1、H2、B 和 S 均未通过各自采纳门；发布 Skill 不强制 Agent 生成 Context Manifest、Selected Evidence 或访问回执。
- Broker-only docsite 已统一模型调用入口，但同一 OS 用户下的本机托管只提供路由、缓存和预算门，不构成 Provider Key 的进程隔离。

## 活动计划与待办

- [ ] [Authority Meta Model Plan](implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)：只推进 production consumer 采纳与实际 release 选择；在此之前不导出稳定 Core API，也不发布模型 1 支持声明。
- [ ] [多 Workstream 协作 Plan](implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)：先实现 Personal foundation Phase 0 的版本化 Workstream／session／scope／finding schema、subsystem registry、Git fixture、integration ref 与主 worktree 识别。
- [ ] [Context-routing 研究 State](state/context-routing-research.md)：完成 task／Oracle v0.2 的静态控制包，再决定是否申请新的 Terra medium 模型样本。
- [ ] 平台 Phase 4：等待单独计划和授权；Harness JSON 不冒充第二平台 runtime。
- [ ] 跨平台 byte-for-byte archive 一致性和 benchmark R1 自动脱敏导出继续延期，不阻塞上述三个近期检查点。

## Blockers / risks

- Authority：M2.2 只有 root-only opt-in 证据；M2.3 不会自动选择版本，`release_ready` 仍为 false。
- 协作：linked worktree 隔离索引和工作目录，但当前没有 OS 级路径沙箱；越界写入仍依赖工作目录纪律和整合审阅发现。
- Context routing：Pilot 009 只覆盖三个任务、一个模型和一个 runtime；成本方向不能替代 3/3 质量门。
- 发布：v0.2.0 ZIP checksum 有效，但 Windows／Linux 从同一 tag 重建仍非 byte-for-byte 一致。
- 凭据：Broker client token 仍能在模型白名单和预算内产生调用；同用户托管不能宣称秘密隔离。
- 研究证据：仓库外 raw evidence 已封存但没有自动 R1 导出器；不得把原始运行、凭据或本机路径批量复制进 Git。

## 最近完成

- [Authority M2 本地 Canonical 集成](validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)：M2.1／M2.2／M2.3 已通过独立 worktree 与干净集成，默认 production 和公开 release 保持不变。
- [Authority M1 本地 Canonical 集成](validation/2026-08-21-authority-meta-model-canonical-integration.md)：fixture、Core owner、兼容、迁移／恢复、shadow 与 AI non-escalation 已进入本地 baseline。
- [平台中立 Phase 3](validation/2026-08-21-platform-neutral-phase-3-harness-json.md)：Harness JSON 合约通过 Windows／Ubuntu CI，但仍为未发布参考 Adapter。
- [ADR-0008 协作 Design 集成](validation/2026-08-20-adr-0008-collaboration-design-integration.md)：Personal-first、Team opt-in 与 Local-only telemetry 边界已形成权威设计，尚无 runtime 实现。

## 下一里程碑

1. **Authority：** 明确 managed production consumer 的启用／回滚门，再由维护者选择实际 SemVer 和 candidate manifest。
2. **协作：** 完成 zero-network Personal foundation 的最小机器合约与 Git fixture；Team Mode 继续冻结。
3. **研究：** 在不调用模型的情况下证明新 Oracle 对 paraphrase、contradiction 与 mutation controls 的稳健性。
