# 当前进度

Updated: 2026-08-22

## 当前阶段

Project Orrery v0.2.0 是当前公开版本；`origin/main` 已在其后集成平台中立 Core／CLI／Observatory、Codex／Harness JSON／Claude Code／DeepSeek Harness Adapter、Broker-only docsite、协作 Phase 0 contract，以及 Authority Meta Model M1／M2。所有后续能力仍是 Canonical source、`experimental`／`unreleased` 实现，没有形成新的公开 Release。

当前工作集中在五条相互独立的线路。详细历史进入 [DEVLOG](DEVLOG.md)，可复现证据进入 [Validation](validation/README.md)，这里仅保留当前控制面。

| 线路 | 当前状态 | 下一安全动作 |
|---|---|---|
| Authority Meta Model | 模型 1、Core evaluator、完整内部 CLI claims、root-only opt-in Observatory projection 与本地 release-candidate gate 已进入 Canonical source baseline；默认 production consumer 和公开 release 未切换 | 审阅 managed consumer 的 production switch 与回滚证据，再由维护者选择真实 SemVer／candidate manifest |
| 多 Workstream 协作 | ADR-0007／0008 与 Approved Design 已接受；Phase 0 schema、Git fixture、integration ref／主 worktree 解析、subsystem registry 与只读 CLI contract 已进入本地 Canonical source | 推进 Phase 1 的 worktree identity 与私有 session；继续禁止在共享主目录并发开发 |
| Context routing 研究 | Pilot 009 的 P/S 装置与 Scope 证据有效，但质量门失败，没有策略获准进入发布 Skill | 不调用模型地完成 task／Oracle v0.2 的分层 verdict、结构化 State、paraphrase 与 mutation controls |
| 平台与 Adapter | Claude／DeepSeek Adapter 0.1.0 均已实现但未发布；Claude 被认证阻断，DeepSeek 只有 rc.8／Windows／Core 0.1.0／CLI 0.1.1 wheel／指定模型和生命周期范围为 `verified` | Claude 只在另行授权且认证可用时继续；DeepSeek 后续工作转向独立发行与更多 runtime matrix，不外推当前证据 |
| 文档治理 | ADR-0012、Approved Design 与 self-host Phase 0 已进入 Canonical source，建立当前／历史边界、事件同步和 soft review 规则；尚无 audit runtime | 先冻结只读 finding contract／fixture；不增加自动改写 |

## 当前结论

- 公开事实仍以 v0.2.0 Release 为准；本地 Canonical 实现、runtime-verified 范围与 released 能力必须分别表达。
- Authority Model 1 已由 self-host 项目显式选择，但公开 v0.2.0 项目仍是 `legacy-unversioned`；普通工具升级不得替用户选择模型。
- Authority M2 的 `candidate_ready` 不等于 `release_ready`：缺少默认 managed consumer 的 production evidence 和维护者选择的实际发布版本。
- 多 Agent 已有 Phase 0 的机器可读 contract 与只读检查，但没有持久 session、主 worktree 守卫、重叠检测、review／integration CLI、Personal 指挥台或 Team telemetry。
- Context-routing 的 H1、H2、B 和 S 均未通过各自采纳门；发布 Skill 不强制 Agent 生成 Context Manifest、Selected Evidence 或访问回执。
- Broker-only docsite 已统一模型调用入口，但同一 OS 用户下的本机托管只提供路由、缓存和预算门，不构成 Provider Key 的进程隔离。
- 文档治理与 Authority Meta Model 分层：治理 finding 只是非权威观察，长度／密度只触发人工审查，不能单独使文档失效或自动改写作者内容。

## 活动计划与待办

- [ ] [Authority Meta Model Plan](implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)：只推进 production consumer 采纳与实际 release 选择；在此之前不导出稳定 Core API，也不发布模型 1 支持声明。
- [ ] [多 Workstream 协作 Plan](implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)：Phase 0 已完成；下一步只推进 Phase 1 的平台中立 worktree identity、私有 session 与安全 attach/rebind，不提前进入 Team 网络层。
- [ ] [Context-routing 研究 State](state/context-routing-research.md)：完成 task／Oracle v0.2 的静态控制包，再决定是否申请新的 Terra medium 模型样本。
- [ ] [平台 Phase 4](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)：DeepSeek 的精确 runtime 门已完成；Claude 的成功认证／模型路由仍未完成，两个 Adapter 的独立发行和更广矩阵均未开始。
- [ ] [文档治理 Plan](implementation/plans/2026-08-21-document-governance-and-audit.md)：Phase 0 文档规范完成后，下一步只设计 provider-neutral finding contract 与合成 fixture；HANDOFF 专项压缩须另行人工复核。
- [ ] 跨平台 byte-for-byte archive 一致性和 benchmark R1 自动脱敏导出继续延期，不阻塞上述近期检查点。

## Blockers / risks

- Authority：M2.2 只有 root-only opt-in 证据；M2.3 不会自动选择版本，`release_ready` 仍为 false。
- 协作：linked worktree 隔离索引和工作目录，但当前没有 OS 级路径沙箱；越界写入仍依赖工作目录纪律和整合审阅发现。
- Context routing：Pilot 009 只覆盖三个任务、一个模型和一个 runtime；成本方向不能替代 3/3 质量门。
- 发布：v0.2.0 ZIP checksum 有效，但 Windows／Linux 从同一 tag 重建仍非 byte-for-byte 一致。
- 凭据：Broker client token 仍能在模型白名单和预算内产生调用；同用户托管不能宣称秘密隔离。
- 研究证据：仓库外 raw evidence 已封存但没有自动 R1 导出器；不得把原始运行、凭据或本机路径批量复制进 Git。

## 最近完成

- [main 验收与跨平台 CI](validation/2026-08-21-main-acceptance-and-cross-platform-ci.md)：本地 231 项动态回归、integrated build、Authority 投影回滚、链接与发布边界通过；首次 Ubuntu 发现的 Windows 路径夹具已修正，最终 Windows／Ubuntu 双 PASS，未创建新 Release。
- [DeepSeek wheel runtime 与跨平台 CI](validation/2026-08-22-deepseek-w1-windows-ci-fix.md)：关闭普通 wheel assets 阻塞，精确 runtime 范围进入 `verified`；首次矩阵保留 Windows 失败证据，修复 8.3 路径与 wheel 测试依赖后，GitHub Actions `32554191374` Windows／Ubuntu 双 PASS。
- [W1 与第二平台 Adapter 本地集成](validation/2026-08-22-w1-and-second-platform-adapters-integration.md)：Phase 0 contract 与 Claude／DeepSeek Adapter 从独立 worktree 经干净整合吸收，旧 Phase 4 ADR-0010 重编号为 ADR-0013；后续 wheel Validation 与 CI 完成了 DeepSeek 精确门。
- [Authority M2 本地 Canonical 集成](validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)：M2.1／M2.2／M2.3 已通过独立 worktree 与干净集成，默认 production 和公开 release 保持不变。
- [Authority M1 本地 Canonical 集成](validation/2026-08-21-authority-meta-model-canonical-integration.md)：fixture、Core owner、兼容、迁移／恢复、shadow 与 AI non-escalation 已进入本地 baseline。
- [平台中立 Phase 3](validation/2026-08-21-platform-neutral-phase-3-harness-json.md)：Harness JSON 合约通过 Windows／Ubuntu CI，但仍为未发布参考 Adapter。
- [ADR-0008 协作 Design 集成](validation/2026-08-20-adr-0008-collaboration-design-integration.md)：Personal-first、Team opt-in 与 Local-only telemetry 边界已形成权威设计，尚无 runtime 实现。
- [当前状态入口压缩](validation/2026-08-21-current-state-entry-compaction.md)：PROGRESS 与 Authority State 已恢复为当前控制入口，并触发 ADR-0012 的长期治理设计。

## 下一里程碑

1. **Authority：** 明确 managed production consumer 的启用／回滚门，再由维护者选择实际 SemVer 和 candidate manifest。
2. **协作：** 进入 Personal Phase 1，完成 worktree identity 与私有 session 的最小写入闭环；Team Mode 继续冻结。
3. **研究：** 在不调用模型的情况下证明新 Oracle 对 paraphrase、contradiction 与 mutation controls 的稳健性。
4. **文档治理：** 完成 Phase 1 只读 finding contract／fixture 设计；不实现自动修复或公开模板迁移。
5. **平台：** 在认证可用且另行授权后决定是否继续 Claude Stage B；DeepSeek 不再重复 rc.8 证据，后续只处理发行或新增 runtime matrix。
