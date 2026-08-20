# 跨会话交接

Updated: 2026-08-21

## 当前情况

- 根文档系统已依据 ADR-0001 完成自托管集成；`.project-orrery.json` 应保持 `authority_status: integrated`。
- Project Orrery v0.2.0 已公开发布：`main`、tag、Release、zip、checksum 和远端 manifest 均已核验。
- 自托管、实验、installer 缓存排除和 CI 完整历史修复已进入 Git 历史。
- 上下文路由证据集中在 `experiments/context-routing/`；大型原始输出位于 `D:\coding warehouse\project-orrery-benchmark`。
- Pilot 004 的 H1 未达到 token 采纳门，不能加入发布版 Skill。
- H2 候选、读取代理、JSONL 独立 validator、可选 Hook 和原始证据保留工具位于 `experiments/context-routing/`；研究层 `bb2c768`、权威状态层 `96bfd21` 和整合状态 `f9cd508` 已推送到公开 `origin/main`。没有新 Release。
- 10 份 CLI smoke 原始运行均在仓库外封存为 `contaminated`；manifest 10/10 可验证。既有 run `h2-hook-smoke-20260818-114907` 可被新 JSONL validator 只读判定为 1/1 内容读取证明，但不得回写或改分类。
- Pilot 005 四个 B/H2 run 因共同装置缺陷全部按 `contaminated` 封存；Pilot 006 修正共同 Harness 后完成相同两个任务。B/H2 均通过 2/2 任务验收。
- Pilot 006 的 PO-CR-026 两份冻结访问结果受 CRLF→CRCRLF 假阴性影响，原始分类仍为 `contaminated`；v3 只读复核证明四个 run 的访问均有效，且四份 manifest 始终有效。
- H2 相对 B 的总 input 高 18.5%，没有通过预设成本门，不采纳、不新增 ADR、不修改发布 Skill。R2 结论见 [Pilot 005 / 006 报告](../experiments/context-routing/results/2026-08-18-pilot-005-006-bh2-terra-medium.md)。
- `codex/b-adoption-pilot` 已完成 Pilot 007 六次运行。仓库外原始根为 `D:\coding warehouse\project-orrery-benchmark\pilot-007-20260818-143450`；六份 manifest 有效，不得回写、重分类或复制进 Git。
- Pilot 007 的共同 nested-branch formal-validation 缺陷使原 raw 0/3 对 0/3 不能直接解释；R2 语义复核为 P/B 均 2/3。B 的成本／收益门仍全部失败，因此不采纳、不新增 ADR。
- Pilot 008 原 P/R Skill Entry Router 只完成静态准备，没有运行模型；ADR-0005 已在执行前取代其固定入口成本假设，历史候选与 Validation 保留但不作为当前 treatment。
- Pilot 008 的正式 transport 已实现；首对迁移任务中 P 读取外部已安装 Skill 而 contaminated，P/S 又共同
  暴露冻结 Oracle 的索引名和自然语言词形假阴性。runner 停止后续任务，两份 R0 保持有效且只读。
- Pilot 009 保持完整 Skill、P/S 入口 treatment、任务目标和 Terra medium 配置，只修正上述装置问题。
  六次正式运行的 access audit、exact Scope、formal validation 和 R0 全部有效；外部原始根为
  `D:\coding warehouse\project-orrery-benchmark\pilot-009-scope-20260819-142948`。
- Pilot 009 的 S/P 聚合写前 input 为 `0.8274`，全部成本门通过；冻结 0/3 经只读语义复核为 P/S 2/3。
  两侧迁移实现行为正确，但 PROGRESS 都遗漏未来版本写前拒绝，3/3 质量门失败，因此 S 不采纳。
- 任务／Oracle v0.2 已作为研究候选成文：下一步先构造分层 verdict、公开结构化 State 字段、paraphrase
  和 mutation controls，不自动创建或运行 Pilot 010。
- Marglo／NextStep Seed_2 是首批素材来源；只可提炼模式或从固定提交构造脱敏 fixture，不能在真实工作树运行，也不能复制用户数据、凭据、缓存或未提交改动。
- 工作树新增未发布的 docsite UI 小优化：动态页 AI 设置入口位于顶栏主题按钮左侧，根观测台与发布模板已同步；桌面／移动端浏览器验证、动态全仓 40/40、集成结构、静态站和 diff 检查通过。没有新增 ADR，也没有提交、推送或发布。
- ADR-0004 已接受平台中立 Core／CLI／Observatory／Adapter 的单仓库分包边界；Approved Design 与 Active Plan 已建立。Phase 0／1 和 Phase 2 仓库实现检查点已落地，但没有改变 v0.2.0 资产、实现第二平台或产生任何新的 runtime `verified` 证据。
- ADR-0004 Phase 0 已完成：v0.2.0 发布清单和三项 CLI 人类输出由 fixture／回归保护，模板 `AGENTS.md` 使用中立标题；README 将可移植 CLI、`experimental` Codex 和 `target` 其他平台明确分开。
- ADR-0004 Phase 1 已完成：`packages/*/src` 下建立 Core／CLI／Observatory 0.1.0 源码边界；旧 Skill 路径为薄 wrapper，单独 Skill 使用冻结 v0.2 fallback。12 项产品测试通过，2 个动态依赖测试按设计跳过。
- ADR-0004 Phase 2 仓库实现检查点已完成：`adapters/codex/` 是不含模板／schema／项目事实的薄 Adapter，`scripts/package_codex_adapter.py` 生成独立 ZIP／checksum，平台安装器的 dry-run、冲突拒绝、旧 Skill 备份迁移、升级与可恢复卸载在临时目录 5/5 通过。真实 Codex E2E 未执行，状态仍为 `experimental`。
- ADR-0003 的 docsite 凭据安全实现已在工作树完成：Provider／Base URL 绑定、显式端点、失败关闭、同源 POST、安全响应头、语料／Provider 缓存签名，以及可选确定性 Broker 的缓存、single-flight、模型与预算门均已同步到根工具和发布模板。它尚未提交、推送或发布。
- ADR-0006 已在工作树把上述可选 Broker 收敛为唯一 docsite 网关：设置页的 OpenAI／DeepSeek／Custom 只注册上游，默认本机托管自动启动，外部隔离只保存 client token；`set_key.py`、独立 Q&A CLI、仪表盘与测试路径都要求 Broker。动态产品专项 16/16、默认全仓 57 passed + 2 expected skips，尚未提交或发布。
- 已完成 `Ariestar/sivtr@4fae091` 固定提交的源码观察并写入 Library。当前结论是其 WorkRecord／WorkRef／WorkSet、渐进检索和只读 MCP 可作为情境证据层参考，但不能替代 Orrery 权威链；没有采纳依赖、Adapter、路由策略或新 Pilot。
- 三个 Agent 在同一 `main@96eee5a` 工作目录留下的交错改动已先封存到 `codex/recovery-shared-main-20260820@a87c5a4`，再在 `D:\coding warehouse\project-orrery-integration-20260820` 拆分为研究、产品、Library 和权威状态提交。恢复分支不可改写或删除。
- ADR-0007 已接受 Workstream 隔离、Canonical／Candidate／Worktree 作用域和干净集成规则；ADR-0008 又接受 default Personal Mode、opt-in Team Mode、Local-only telemetry 与中央只读／本机执行边界。两者都不证明自动化已经实现。完整动态回归仍为 61/61，默认 59 passed + 2 expected skips；本轮新增协作 Design 只做文档级验证，没有新 Release。
- 自动 session、overlap、主 worktree 守卫、`orrery integrate` 与观测台 scope banner 尚未实现。三个后续 Agent 必须各自进入新分配的 worktree，不能继续复用原共享目录。
- 已分配目录：context-routing 使用 `D:\coding warehouse\project-orrery-agent-context-routing`，platform／adapters 使用 `D:\coding warehouse\project-orrery-agent-platform-adapters`，docsite／broker 使用 `D:\coding warehouse\project-orrery-agent-docsite`。三者都是 clean linked worktree；尚未创建 session，开始新任务时再声明 expected writes 与 validation。
- 协作 Design 已完成产品层收敛：Agent-first／Orrery-first 混合入口、subsystem mapping、Scope B、finding／ack、双维度状态、风险审查包、人工集成、保守清理和 Personal／Team 渐进指挥台均已进入 Approved Design。下一步只做 Personal foundation Phase 0，不直接实现 Team 网络层。
- ADR-0009 已接受 Authority Meta Model 规范层并建立独立 State／Approved Design。它定义 role lifecycle、独立 claim dimensions、Authority scopes、provider-neutral evidence、derived-view constraints 和 conformance 输入；当前没有机器实现或 Plan，AUTH-1／AUTH-4 仍 pending。

## 风险与常见陷阱

- 不要把 v1 Oracle 的正式 validator exit 1 解读为六个候选实现失败；详见 Pilot 004 结果报告和 v2 复核。
- 不要为了“同步文档”把 JSONL、隔离仓库或本机路径批量复制进 `docs/`。
- v0.2.0 资产 checksum 有效，但跨 Windows／Linux 重建尚非 byte-for-byte 相同；不要宣称跨平台可重复打包已经解决。
- 运行 `py_compile` 会在模板目录产生被忽略的 `__pycache__`；installer 必须继续排除它们。
- H2 新增文件已进入本地 `main`；不要误删 Pilot 控制包，也不要把仓库外 raw run 复制回仓库。
- 不要声称 Windows CLI Hook 已工作：0.147.0 下项目 Hooks、trusted 覆盖、绝对 `commandWindows` 和 CLI 内联 Hooks 都未产生日志。当前正式候选证据模式是 `codex-exec-jsonl-posthoc`。
- JSONL 模式是完整事件流上的事后作废，不是实时权限边界；任何 MCP／Hosted／未知 item、直接读取命令或输出哈希不匹配都必须使 run 失败。
- 原始 run sealing 后不得增补文件或“修正”分类；派生复核进入新 R1／Validation 文件并引用原 run。
- 读取代理已改为直接写 UTF-8 bytes；不要恢复为 Windows TextIO 输出，否则 CRLF 会再次变成 CRCRLF。兼容旧 run 的恢复形式仍必须命中代理独立 SHA-256，不能接受无哈希的换行宽松比较。
- Pilot 007／008／009 都已冻结；不要修复 raw summary、frozen Oracle、协议检查或候选仓库后再冒充
  同一轮结果。任何新任务或 Oracle 必须使用新 Pilot ID 和外部输出根。
- 未来 runner 的外层隔离分支不能再命名为 `benchmark`，否则既有 Pilot 006 dry-run 会在嵌套 clone 中创建同名分支失败。
- Pilot 009 已观察到 S 的写前 input 低于 P，但不能把成本门通过写成“S 已采纳”：质量门失败，样本只有
  三项、一个模型和一个 runtime。
- 不要把 Smoke 001 的最终 58,541 input 写成 Scope Lock input；该 turn 没有首次写入边界，唯一有效分类是 apparatus-contaminated／measurement unavailable。
- 不要把 Smoke 002 的写前 19,361 input 写成 P/S 路由成本或收益；它只验证当前 CLI 的事件顺序，策略允许 0 次写前代理读取，因此没有内容交付 proof。
- 不要因 Pilot 009 的成本方向信号直接修改发布 `skills/project-orrery/SKILL.md` 或模板；S 仍是
  experiments 候选且本轮明确不采纳。
- 不要把工作树中的 Core 源码分包写成“独立组件已发布”或“其他 Agent 平台已兼容”；当前公开发布源和唯一发布集成仍是 `skills/project-orrery/` 下的 Codex Skill。
- 不要把仓库内 Codex Adapter 的归档／临时目录测试写成真实 runtime 兼容证据；在没有明确授权前，不要安装、升级或卸载维护者真实用户技能目录中的 `project-orrery`。
- 不要把默认同用户托管 Broker 宣称为进程隔离。它统一路由、缓存和预算门，但只有外部 Broker 确实运行在独立 OS 身份或等价外层边界下时才隔离 Provider Key；client token 仍能在预算内发起调用。
- 旧共享 keyring 槽不会被启动流程读取或自动迁移；用户重新保存当前 Provider Key 时会写入绑定槽并清理旧槽。若旧 Key 曾进入不受信任进程或测试上下文，轮换仍是 Provider 侧动作，代码无法替代。
- 不要把 `sivtr` README／Roadmap 或私有 retrieval snapshot 指标写成独立验证事实：其公开仓库没有评估快照，固定提交的完整 Rust 测试在本机因 build-script `os error 5` 未进入测试阶段，且 Agent 入口、架构、Roadmap 与实现存在漂移。任何 transcript 读取还必须先解决缓存副本、保留／删除、脱敏和 Windows daemon token 权限边界。
- 不要为了通过 `git diff --check` 删除冻结 Pilot fixture 的 EOF 空行；Pilot 008／009 对这些文件做逐字节 SHA-256 校验。2026-08-20 首次集成回归已实际捕获该问题，正确修复是从恢复提交还原原始字节，不是更新冻结哈希。
- 不要把 ADR-0007／ADR-0008 Accepted 或人工 worktree 验证写成自动协调已实现。当前产品没有 Team Node；未来已上报的未 push 元数据只能显示 Local-only，未上报内容和证据不足的语义关系继续为 Unknown。
- 不要把 ADR-0009 Accepted 写成 Meta Model 已经存在于 Core。当前只是规范落地；没有 parser／domain API、语义版本字段或 conformance fixture，也没有授权拆分 `build_docsite.py`／`serve.py`／`docsite_qa.py`。

## 安全接续点

1. 阅读 `docs/PROGRESS.md` 和 `docs/state/context-routing-research.md`。
2. 运行自托管结构验证和完整测试，确认 Validation 仍匹配。
3. 阅读 [H2 装置验证](validation/2026-08-18-h2-read-proof-apparatus.md)、[Pilot 005 / 006 验证](validation/2026-08-18-pilot-005-006-bh2.md)和活动 Implementation Plan。
4. Pilot 007 准备后的专项测试为 12/12；全仓默认 39/40（1 skip），动态 reader 开启后 40/40；benchmark、integrated build、文档站、本地链接与 diff 检查通过。若涉及既有 raw run，只可执行 verify／只读派生。
5. 阅读 [Pilot 007 R2 结果](../experiments/context-routing/results/2026-08-18-pilot-007-pb-adoption-terra-medium.md)和 [运行验证](validation/2026-08-18-pilot-007-pb-adoption.md)；不要只看 frozen raw 的 0/3。
6. 读取 [Pilot 008 apparatus stop](validation/2026-08-19-pilot-008-formal-apparatus-stop.md)、
   [Pilot 009 Validation](validation/2026-08-19-pilot-009-ps-scope-run.md)和
   [R2](../experiments/context-routing/results/2026-08-19-pilot-009-ps-scope-terra-medium.md)；raw 0/3 必须与
   只读 2/3 复核一起解释。
7. 下一步先按[任务／Oracle v0.2](../experiments/context-routing/designs/real-development-task-oracle-v0.2.zh-CN.md)
   建立无模型 controls。Pilot 010 尚未创建，也没有自动补跑授权。
8. 平台适配工作先读取 [ADR-0004](decisions/0004-platform-neutral-core-and-adapter-boundaries.md)、[Approved Design](design/platform-neutral-core-and-adapter-architecture.md)、[Implementation Plan](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)、[Phase 1 Validation](validation/2026-08-19-platform-neutral-phase-1-core-cli.md)和[Phase 2 仓库实现 Validation](validation/2026-08-19-platform-neutral-phase-2-codex-adapter.md)；下一步须经明确授权后才进行真实 Codex runtime E2E，不先选择第二平台或发布组件。
9. docsite 安全接续先读取 [ADR-0003](decisions/0003-provider-bound-credentials-and-optional-local-broker.md)、[ADR-0006](decisions/0006-broker-only-docsite-provider-gateway.md)、[Broker-first Design](design/broker-first-docsite-provider-gateway.md)和[Validation](validation/2026-08-19-broker-first-docsite-gateway.md)；公开 v0.2.0 尚不包含这些工作树改动。
10. 若继续研究外部工作记忆层，先读取 [sivtr 观察](library/2026-08-19-sivtr-work-memory-source-notes.zh-CN.md)；除非用户明确接受新的 ADR／Plan，不安装 sivtr、不扫描真实 transcript、不修改 Scope Router，也不自动创建 Pilot 010。
11. 多人协作先读取 [ADR-0007](decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)、[Approved Design](design/multi-worktree-collaboration-protocol.md)、[活动 Plan](implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)和[恢复 Validation](validation/2026-08-20-multi-worktree-recovery-and-manual-adoption.md)。后续任务只在独立 worktree 中继续，根 `PROGRESS`／`HANDOFF` 由整合者同步。
12. Team／telemetry 相关工作还必须读取 [ADR-0008](decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)与[Design 收敛 Validation](validation/2026-08-20-multi-worktree-collaboration-design-consolidation.md)；默认 Personal Mode 不得监听网络，Team extension 不得先于 Personal foundation。
13. Authority semantics 工作必须读取 [ADR-0009](decisions/0009-authority-meta-model-and-semantic-conformance.md)、[Approved Design](design/authority-meta-model.md)和[State](state/authority-meta-model.md)；下一次对话先做重复语义盘点与 conformance 设计，不直接进入重构。
