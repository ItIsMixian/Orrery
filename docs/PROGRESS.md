# 当前进度

Updated: 2026-08-28

## 当前阶段

Project Orrery v0.2.0 是当前公开版本；`origin/main` 已在其后集成平台中立 Core／CLI／Observatory、Codex／Harness JSON／Claude Code／DeepSeek Harness Adapter、Broker-only docsite、协作 Phase 0 contract，以及 Authority Meta Model M1／M2。所有后续能力仍是 Canonical source、`experimental`／`unreleased` 实现，没有形成新的公开 Release。

当前工作集中在五条相互独立的线路。详细历史进入 [DEVLOG](DEVLOG.md)，可复现证据进入 [Validation](validation/README.md)，这里仅保留当前控制面。

| 线路 | 当前状态 | 下一安全动作 |
|---|---|---|
| Authority Meta Model | 模型 1、Core evaluator、完整内部 CLI claims、root-only opt-in Observatory projection 与本地 release-candidate gate 已进入 Canonical source baseline；默认 production consumer 和公开 release 未切换 | 审阅 managed consumer 的 production switch 与回滚证据，再由维护者选择真实 SemVer／candidate manifest |
| 多 Workstream 协作 | W7D 非 `main` Integration Candidate 已组合 W7A succession contract、W7B 本机事务执行、CI2 分级测试与 W7C-B 只读关系图；Core 0.1.14／CLI 0.1.18／Observatory 0.1.9，修复 hosted preflight discovery 依赖后 inventory 为 376 IDs／27 shards／51 Fast／69 Checkpoint | 对修复后的非 `main` exact SHA 重跑 Windows／Ubuntu；双 PASS 后等待维护者授权 main fast-forward，self-host apply、默认 UI 执行入口与公开发布继续后置 |
| Context routing 研究 | C1 Oracle v0.2 无模型静态 controls 已通过；只有 Pilot 010 设计申请 readiness，没有运行授权或 treatment 采纳 | 由维护者决定是否注册 C2 设计任务；不得自动创建／运行 Pilot 010 |
| 平台与 Adapter | Claude／DeepSeek Adapter 0.1.0 均已实现但未发布；Claude 被认证阻断，DeepSeek 只有 rc.8／Windows／Core 0.1.0／CLI 0.1.1 wheel／指定模型和生命周期范围为 `verified` | Claude 只在另行授权且认证可用时继续；DeepSeek 后续工作转向独立发行与更多 runtime matrix，不外推当前证据 |
| 文档治理 | D1 已冻结内部只读 finding schema、11 条规则与 11 组正负 fixture；所有 finding 非权威且默认 advisory | 另行设计 D2 scanner／CLI；不自动修复、压缩 HANDOFF 或启用硬门 |

## 当前结论

- 公开事实仍以 v0.2.0 Release 为准；本地 Canonical 实现、runtime-verified 范围与 released 能力必须分别表达。
- Authority Model 1 已由 self-host 项目显式选择，但公开 v0.2.0 项目仍是 `legacy-unversioned`；普通工具升级不得替用户选择模型。
- Authority M2 的 `candidate_ready` 不等于 `release_ready`：缺少默认 managed consumer 的 production evidence 和维护者选择的实际发布版本。
- 多 Agent 候选已推进到 W7D：W7B 在隔离 Git fixture 中实现 discovery／plan／本机人类确认／apply／recovery／receipt／undo，W7C-B 只读图不接执行按钮，中央 Team 仍无执行权。真实 self-host apply、默认 UI 执行入口、真实多机、云 relay、多设备迁移和公开发布均未发生。
- Context-routing 的 H1、H2、B 和 S 均未通过各自采纳门；发布 Skill 不强制 Agent 生成 Context Manifest、Selected Evidence 或访问回执。
- Broker-only docsite 已统一模型调用入口，但同一 OS 用户下的本机托管只提供路由、缓存和预算门，不构成 Provider Key 的进程隔离。
- 文档治理与 Authority Meta Model 分层：治理 finding 只是非权威观察，长度／密度只触发人工审查，不能单独使文档失效或自动改写作者内容。

## 活动计划与待办

- [ ] [Authority Meta Model Plan](implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)：只推进 production consumer 采纳与实际 release 选择；在此之前不导出稳定 Core API，也不发布模型 1 支持声明。
- [ ] [W7D Integration Candidate Plan](implementation/plans/2026-08-28-w7d-w7-integration-candidate.md)：完成本地分级验证与只读图形验收后，冻结非 `main` exact SHA 并取得 Windows／Ubuntu required checks；双 PASS 仍只允许交给维护者决定 main fast-forward。
- [ ] [Context-routing 研究 State](state/context-routing-research.md)：C1 静态 controls 已完成；C2/Pilot 010 设计尚未获批，更没有模型运行授权。
- [ ] [平台 Phase 4](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)：DeepSeek 的精确 runtime 门已完成；Claude 的成功认证／模型路由仍未完成，两个 Adapter 的独立发行和更广矩阵均未开始。
- [ ] [文档治理 Plan](implementation/plans/2026-08-21-document-governance-and-audit.md)：D1 contract／fixture 已完成；下一步需另行批准 D2 只读 scanner／CLI，HANDOFF 专项压缩仍须人工复核。
- [ ] 跨平台 byte-for-byte archive 一致性和 benchmark R1 自动脱敏导出继续延期，不阻塞上述近期检查点。

## Blockers / risks

- Authority：M2.2 只有 root-only opt-in 证据；M2.3 不会自动选择版本，`release_ready` 仍为 false。
- 协作：linked worktree 隔离索引和工作目录，但当前没有 OS 级路径沙箱；越界写入仍依赖工作目录纪律和整合审阅发现。
- W7 Promotion：本地分级结果不能替代 exact-SHA hosted Windows／Ubuntu；双平台通过也不授权自动推进 `main`。
- W7 本机 timing：唯一一次 `team-relations-execution` 的 4/4 断言成功，但 311.803 秒超过 300 秒 hard budget，runner 结果保持 FAIL；预算/选择未改且没有重跑，必须由 hosted exact-SHA 结果继续判定。
- Context routing：Pilot 009 只覆盖三个任务、一个模型和一个 runtime；成本方向不能替代 3/3 质量门。
- 发布：v0.2.0 ZIP checksum 有效，但 Windows／Linux 从同一 tag 重建仍非 byte-for-byte 一致。
- 凭据：Broker client token 仍能在模型白名单和预算内产生调用；同用户托管不能宣称秘密隔离。
- 研究证据：仓库外 raw evidence 已封存但没有自动 R1 导出器；不得把原始运行、凭据或本机路径批量复制进 Git。

## 最近完成

- [W7D W7 Integration Candidate](validation/2026-08-28-w7d-w7-integration-candidate.md)：加法整合 CI2/W7B 与 W7C-B，保留 schema-2 分级预算、只读关系图和独立执行边界；exact-SHA hosted 结果与 main 授权边界在 Validation 中逐项记录。
- [W4 health／W5B Team Observatory 候选](validation/2026-08-27-w4-health-w5b-integration-candidate.md)：修复 36-worktree 健康误导，提供 loopback Team 图形流程；Core 0.1.9／CLI 0.1.13／Observatory 0.1.4，最终 exact-SHA 门仍待完成。
- [W4／W5A 联合候选](validation/2026-08-23-w4-w5-integration-candidate.md)：Core 0.1.8／CLI 0.1.13／Observatory 0.1.2，动态全仓 316 项通过，候选实现 SHA `2bc6207` 的 Ubuntu／Windows checks 通过；最终入口 SHA 仍须 Candidate-first 验证并等待维护者确认。
- [W3 Canonical 集成](validation/2026-08-23-w3-canonical-integration.md)：冻结 Core 0.1.7／CLI 0.1.12 的 review、integration、closure、workspace inventory 与 advisory cleanup contract；Promotion 仍以包含本记录的 exact SHA required checks 为准。
- [W2 Canonical 集成](validation/2026-08-22-w2-canonical-integration.md)：基于最新 main 增量吸收五来源 Scope/finding；exact SHA `21a2e1c` 已在 GitHub Actions `32570545138` 取得 Windows／Ubuntu 双 PASS，并由受保护 main 接受。
- [Candidate-first main promotion gate](validation/2026-08-22-candidate-first-main-promotion-gate.md)：Candidate `e4e4442` 先通过 Windows／Ubuntu，再由 strict/admin-enforced branch protection 允许快进 main；PR 非必需，main 不重复运行同一 SHA 的矩阵。
- [W1／D1／C1 Canonical 集成](validation/2026-08-22-w1-d1-c1-canonical-integration.md)：按 W1→D1→C1 吸收三个独立 Candidate，修复 C1 行尾冻结与 Windows session-path 测试别名；联合 273 项回归及 GitHub Actions `32564334514` Windows／Ubuntu 双 PASS。
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
2. **协作：** W7D exact-SHA Windows／Ubuntu 双 PASS 后交由维护者决定 main fast-forward；未经确认不推广 main，不把本机事务 fixture、loopback 或只读图证据外推为真实 self-host apply／LAN／中央执行。
3. **研究：** 决定是否批准 C2 的 Pilot 010 设计冻结；在此之前不运行模型。
4. **文档治理：** 决定是否批准 D2 只读 scanner／CLI；不实现自动修复或公开模板迁移。
5. **平台：** 在认证可用且另行授权后决定是否继续 Claude Stage B；DeepSeek 不再重复 rc.8 证据，后续只处理发行或新增 runtime matrix。
