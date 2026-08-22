# 跨会话交接

Updated: 2026-08-22

## 当前情况

- 根文档系统已依据 ADR-0001 完成自托管集成；`.project-orrery.json` 应保持 `authority_status: integrated`。
- Project Orrery v0.2.0 已公开发布：`main`、tag、Release、zip、checksum 和远端 manifest 均已核验。
- 2026-08-21 的本地 Canonical 集成已在 `main@42aebae` 同步至公开 `origin/main`；本地动态 231 项与远端 GitHub Actions `32492830151` 的 Windows／Ubuntu 矩阵通过。该同步没有创建 tag、Release 或新的公开支持声明。
- 2026-08-22 的 W1、Claude／DeepSeek Adapter、wheel assets 修复与精确 DeepSeek compatibility 已同步至 `origin/main@000111d`。首次 matrix `32500503338` 为 Ubuntu PASS／Windows FAIL；修复 Windows 8.3 worktree alias 与显式 wheel 测试依赖后，GitHub Actions `32554191374` Windows／Ubuntu 双 PASS。没有创建 tag 或 Release。
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
- C1 已完成 Oracle v0.2 无模型静态 controls：分层 verdict、公开结构化 State fixture、paraphrase／contradiction／mutation 与 contamination controls 均通过。它只允许申请 Pilot 010 设计；C2 未注册，Pilot 010 未创建／运行，也没有模型授权。
- Marglo／NextStep Seed_2 是首批素材来源；只可提炼模式或从固定提交构造脱敏 fixture，不能在真实工作树运行，也不能复制用户数据、凭据、缓存或未提交改动。
- 未发布的 docsite UI 小优化已随 `1cad1ac` 进入 `origin/main`：动态页 AI 设置入口位于顶栏主题按钮左侧，根观测台与发布模板已同步；桌面／移动端浏览器验证、动态全仓 40/40、集成结构、静态站和 diff 检查通过。没有新增 ADR 或 Release。
- ADR-0004 已接受平台中立 Core／CLI／Observatory／Adapter 的单仓库分包边界；Approved Design 与 Active Plan 已建立。Phase 0／1／2 已落地，精确 Windows／Codex runtime 范围已有 `verified` E2E；这没有改变 v0.2.0 资产、发布独立组件或实现第二平台。
- ADR-0004 Phase 0 已完成：v0.2.0 发布清单和三项 CLI 人类输出由 fixture／回归保护，模板 `AGENTS.md` 使用中立标题；README 将可移植 CLI、`experimental` Codex 和 `target` 其他平台明确分开。
- ADR-0004 Phase 1 已完成：`packages/*/src` 下建立 Core／CLI／Observatory 0.1.0 源码边界；旧 Skill 路径为薄 wrapper，单独 Skill 使用冻结 v0.2 fallback。12 项产品测试通过，2 个动态依赖测试按设计跳过。
- ADR-0004 Phase 2 已完成：`adapters/codex/` 是不含模板／schema／项目事实的薄 Adapter；真实 `codex-cli 0.148.0-alpha.21` 在 Windows 11 build 26200 上通过唯一发现、显式／隐式调用、CLI 缺失／不兼容失败关闭、旧 Skill／Adapter 升级、完整备份、可恢复卸载、重新发现和环境恢复。只有该 runtime compatibility 为 `verified`；Adapter 发行仍为 `experimental` 且未发布。
- ADR-0004 Phase 3 已完成并进入 `origin/main`：CLI 0.1.1 的 opt-in JSON 合约、稳定退出码与 `adapters/harness-json/` 0.1.0 已通过隔离生命周期测试。首轮 CI 暴露并修复 Unix CLI 命令夹具；run 30 与最终 HEAD `02c4a6b` 的 run 31 均在 Windows／Ubuntu 双 PASS。Harness 仍为 `experimental`／`unreleased`，不证明模型读取或第三方 Agent runtime 兼容。
- ADR-0003 的 docsite 凭据安全实现已随 `1cad1ac` 进入 `origin/main`：Provider／Base URL 绑定、显式端点、失败关闭、同源 POST、安全响应头、语料／Provider 缓存签名，以及可选确定性 Broker 的缓存、single-flight、模型与预算门均已同步到根工具和发布模板。它仍未形成新 Release。
- ADR-0006 已在 `origin/main` 把上述可选 Broker 收敛为唯一 docsite 网关：设置页的 OpenAI／DeepSeek／Custom 只注册上游，默认本机托管自动启动，外部隔离只保存 client token；`set_key.py`、独立 Q&A CLI、仪表盘与测试路径都要求 Broker。动态产品专项 16/16、默认全仓 57 passed + 2 expected skips；支持状态仍是未发布。
- 已完成 `Ariestar/sivtr@4fae091` 固定提交的源码观察并写入 Library。当前结论是其 WorkRecord／WorkRef／WorkSet、渐进检索和只读 MCP 可作为情境证据层参考，但不能替代 Orrery 权威链；没有采纳依赖、Adapter、路由策略或新 Pilot。
- 三个 Agent 在同一 `main@96eee5a` 工作目录留下的交错改动已先封存到 `codex/recovery-shared-main-20260820@a87c5a4`，再在 `D:\coding warehouse\project-orrery-integration-20260820` 拆分为研究、产品、Library 和权威状态提交。恢复分支不可改写或删除。
- ADR-0007 已接受 Workstream 隔离、Canonical／Candidate／Worktree 作用域和干净集成规则；ADR-0008 又接受 default Personal Mode、opt-in Team Mode、Local-only telemetry 与中央只读／本机执行边界。两者都不证明自动化已经实现。完整动态回归仍为 61/61，默认 59 passed + 2 expected skips；本轮新增协作 Design 只做文档级验证，没有新 Release。
- 协作 W1/W2 已进入 `origin/main` 的 Canonical source：worktree/session、五来源 Scope、四类 finding、Scope Expansion B、本机 acknowledgement 与 route gate 均可用；W2 exact SHA `21a2e1c` 已由 GitHub Actions `32570545138` 的 Windows／Ubuntu双 PASS 验证。Review／integration／cleanup、Observatory 和 Team runtime 仍未实现；后续 Agent 仍必须各自进入独立 worktree。
- 已分配目录：context-routing 使用 `D:\coding warehouse\project-orrery-agent-context-routing`，platform／adapters 使用 `D:\coding warehouse\project-orrery-agent-platform-adapters`，docsite／broker 使用 `D:\coding warehouse\project-orrery-agent-docsite`。三者都是 clean linked worktree；尚未创建 session，开始新任务时再声明 expected writes 与 validation。
- 协作 Design 已完成产品层收敛，W1/W2 已实现 identity/session/Scope/finding 基础；下一步只进入 W3 review/integration/cleanup，不直接实现 W4/W5。
- ADR-0009／0010／0011 与活动 Plan 已把 Authority Meta Model 推进到 `origin/main` 的 experimental M2 source baseline：M1 的 fixture／Core／兼容／迁移基础上，M2.1 完整内部 CLI claims、M2.2 root-only opt-in Observatory projection 和 M2.3 release-candidate gate 均已通过独立 worktree验证、干净集成与双平台 CI。AUTH-4 已解决为平台中立 Core；AUTH-1 仍 pending。当前仍无稳定公共 domain API、默认 production projection、维护者选定的下一 SemVer／manifest 或公开模型 1 release。
- ADR-0013 已将 Claude Code 与 DeepSeek Harness 选为相互独立的 Phase 4 Adapter。源码候选均为 0.1.0、`experimental`／`unreleased`；Claude Code 2.1.87 只证明 Plugin／Skill 发现后认证前失败关闭。DeepSeek Harness 只有 rc.8／Windows build 26200／Adapter 0.1.0／Core 0.1.0／CLI 0.1.1 wheel／`deepseek-official`／`deepseek-v4-flash` 与 manifest 所列生命周期范围为 `verified`。
- W1 和第二平台 Adapter 已经独立 worktree、干净整合、普通 wheel 复验和双平台 CI 进入 `origin/main`；旧 P3 分支占用的 ADR-0010 已重编号为 ADR-0013，Authority ADR-0010／0011／0012 保持不变。当前没有 tag、Release 或 Adapter 独立发行。
- W1.1／W1.2／W1.3、D1 与 C1 已按 W1→D1→C1 顺序进入 `origin/main`；本地联合 273 项回归通过，C1 fixture 行尾冻结为 LF。首次远端 `32564000587` 为 Ubuntu PASS／Windows FAIL；修复 session-path 短／长路径断言后，`32564334514` Windows／Ubuntu 双 PASS。没有创建 Pilot 010、tag 或 Release。
- self-host GitHub main 已启用 Candidate-first branch protection：exact SHA 必须先在非 main 分支通过 Windows／Ubuntu checks，管理员也不能绕过；PR 不强制，main push 不重复运行同一 SHA。首次门禁验证使用 Candidate `e4e4442` 与 run `32566445483`。

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
- 不要把精确 Windows／Codex runtime 的 `verified` 证据外推到其他 runtime、OS、模型或审批模式，也不要把它写成 Adapter／Core／CLI 已发布。未来真实用户目录操作仍需逐次明确授权。
- 不要把默认同用户托管 Broker 宣称为进程隔离。它统一路由、缓存和预算门，但只有外部 Broker 确实运行在独立 OS 身份或等价外层边界下时才隔离 Provider Key；client token 仍能在预算内发起调用。
- 旧共享 keyring 槽不会被启动流程读取或自动迁移；用户重新保存当前 Provider Key 时会写入绑定槽并清理旧槽。若旧 Key 曾进入不受信任进程或测试上下文，轮换仍是 Provider 侧动作，代码无法替代。
- 不要把 `sivtr` README／Roadmap 或私有 retrieval snapshot 指标写成独立验证事实：其公开仓库没有评估快照，固定提交的完整 Rust 测试在本机因 build-script `os error 5` 未进入测试阶段，且 Agent 入口、架构、Roadmap 与实现存在漂移。任何 transcript 读取还必须先解决缓存副本、保留／删除、脱敏和 Windows daemon token 权限边界。
- 不要为了通过 `git diff --check` 删除冻结 Pilot fixture 的 EOF 空行；Pilot 008／009 对这些文件做逐字节 SHA-256 校验。2026-08-20 首次集成回归已实际捕获该问题，正确修复是从恢复提交还原原始字节，不是更新冻结哈希。
- 不要把 ADR-0007／ADR-0008 Accepted 或人工 worktree 验证写成自动协调已实现。当前产品没有 Team Node；未来已上报的未 push 元数据只能显示 Local-only，未上报内容和证据不足的语义关系继续为 Unknown。
- 不要把 M2 进入本地 `main` 写成已经发布或生产切换。完整 CLI bundle 仍是内部 contract，M2.2 projection 只由 root-only 开关启用，M2.3 gate 的 `release_ready` 仍为 false；公开 v0.2.0、standalone installer 和默认 managed Observatory 没有被改写。也不要因这些检查点大拆 `build_docsite.py`／`serve.py`／`docsite_qa.py`。
- 不要把 ADR-0012 Accepted 写成 `docs audit` 已实现。当前只有治理规范、自托管入口和活动 Plan；soft budget／finding／acknowledge／Observatory／模板发布都未实现。HANDOFF 本身是首个专项 review candidate，但压缩前必须人工确认本节安全边界的当前有效性。

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
7. Context-routing 接续先读取 [C1 Validation](validation/2026-08-22-c1-context-routing-oracle-v0.2-static-controls.md)与[静态结果](../experiments/context-routing/results/2026-08-22-c1-oracle-v0.2-static-controls.md)。只有维护者另行批准 C2 后才能冻结 Pilot 010 设计；Pilot 010 尚未创建，也没有模型运行授权。
8. 平台适配工作先读取 [ADR-0004](decisions/0004-platform-neutral-core-and-adapter-boundaries.md)、[ADR-0013](decisions/0013-claude-code-and-deepseek-harness-adapters.md)、[Implementation Plan](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)、[DeepSeek Wheel Validation](validation/2026-08-22-cli-wheel-observatory-assets.md)和[跨平台 CI 修复](validation/2026-08-22-deepseek-w1-windows-ci-fix.md)。DeepSeek 精确 runtime 门已完成但发行仍未发布；Claude 继续受认证与另行授权约束。
9. docsite 安全接续先读取 [ADR-0003](decisions/0003-provider-bound-credentials-and-optional-local-broker.md)、[ADR-0006](decisions/0006-broker-only-docsite-provider-gateway.md)、[Broker-first Design](design/broker-first-docsite-provider-gateway.md)和[Validation](validation/2026-08-19-broker-first-docsite-gateway.md)；公开 v0.2.0 尚不包含这些工作树改动。
10. 若继续研究外部工作记忆层，先读取 [sivtr 观察](library/2026-08-19-sivtr-work-memory-source-notes.zh-CN.md)；除非用户明确接受新的 ADR／Plan，不安装 sivtr、不扫描真实 transcript、不修改 Scope Router，也不自动创建 Pilot 010。
11. 多人协作先读取 [ADR-0007](decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)、[活动 Plan](implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)和 [W2 Validation](validation/2026-08-22-w2-scope-finding.md)。W3 只在独立 worktree 中继续，根 `PROGRESS`／`HANDOFF` 由整合者同步。
12. Team／telemetry 相关工作还必须读取 [ADR-0008](decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)与[Design 收敛 Validation](validation/2026-08-20-multi-worktree-collaboration-design-consolidation.md)；默认 Personal Mode 不得监听网络，Team extension 不得先于 Personal foundation。
13. Authority semantics 工作必须读取 [ADR-0009](decisions/0009-authority-meta-model-and-semantic-conformance.md)、[ADR-0010](decisions/0010-core-owned-authority-evaluator.md)、[ADR-0011](decisions/0011-authority-model-version-and-compatibility.md)、[活动 Plan](implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)、[State](state/authority-meta-model.md)和[M2 integration Validation](validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)。下一步先单独审阅 managed production consumer／rollback，再由维护者另行选择实际 SemVer／candidate manifest；不得把两项阻塞在同一未经审阅的发布动作中关闭。
14. 文档治理工作先读取 [ADR-0012](decisions/0012-document-governance-and-information-lifecycle.md)、[D1 Validation](validation/2026-08-22-d1-document-governance-finding-contract.md)和[Documentation State](state/documentation-system.md)。D2 scanner／CLI 尚未批准；不得自动清理 HANDOFF、把 finding 设为权威硬门或修改公开模板。
