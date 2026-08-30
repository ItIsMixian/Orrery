# 上下文路由研究 State

Updated: 2026-08-30
Authority: research state; no routing candidate is accepted product policy

## 当前事实

- 研究语料包含 24 个由真实 Git 提交重建的任务；详细实现位于 `experiments/context-routing/`。
- Pilot 001 因任务包与外部上下文污染而不能支持架构结论。
- Pilot 002 为固定阅读链额外开销提供方向性信号，但缺乏完整执行配置与独立内容读取证据。
- Pilot 003 完成 9 次 A/B/C 运行；原封存轮存在回执协议无效，随后修复 Harness 并做更小 B/C 对照。
- B/C 确认轮中 C 的总 input token 约比 B 高 75%，且没有达到高风险任务采纳门。
- Pilot 004 完成 3 个 holdout 任务 × B/H。v2 只读 Oracle 判定 B/H 均为 3/3 通过；H 总 input token 比 B 高 47%、平均耗时约高 15%，因此 H1 不采纳。
- H2 候选已经成文：把完整 Manifest、Selected Evidence、Agent receipt 和重复正式验证移出模型输出，只保留代理参数中的短扩张理由。
- 读取代理与两种独立验证链已实现：当前兼容基线使用完整 `codex exec --json` 事后拒绝未批准工具并交叉核验输出哈希；Hook Pre/Post 仅为可选增强。
- Windows Codex CLI 0.147.0 的十轮 smoke 没有产出 Hook audit；全部原始运行按 contaminated 封存且 manifest 可验证。既有第九轮 JSONL 可被新 validator 只读证明 1/1 合法代理读取。
- 原始证据现在有 R0/R1/R2 分层、四类保留期、seal/verify/status 和禁止公开字段规则；工具不会自动删除到期运行。
- Pilot 005 用两个新高风险任务启动 B/H2，但共同 Harness 存在命令包装、绝对路径、Git 历史和 Oracle 契约问题；四份 run 只作为 apparatus failure 保留。
- Pilot 006 修正共同装置后，B 与 H2 的候选和独立任务 Oracle 均为 2/2 通过。冻结 validator 对 CRLF→CRCRLF 产生两个访问假阴性；v3 只读复核在不改原始分类的前提下证明四个 run 的代理读取均有效。
- Pilot 006 聚合成本：H2 相对 B 的总 input +18.5%、cached input +24.7%、non-cached input -31.9%、output +22.5%、代理正文 +23.7%、Agent 时间 +7.2%。H2 没有达到“总 input 不高于 B”的预设门。
- Pilot 007 已完成 3 项任务 × P/B 六次运行；基线为 `f9cd508696280e41c933680f3b8c5090fe71cd9d`，模型为 `gpt-5.6-terra` / medium，六份 R0 manifest 全部有效且没有隐藏重试。
- Pilot 007 存在共同 formal-validation 分支冲突；`PO-CR-028-B` 另有 failed proxy command 和协议检查假阴性，因此不能作为完全干净的采纳因果对照。
- 只读语义复核后 P/B 任务质量同为 2/3。B 相对 P 的聚合 input +25.68%、output +23.56%、Agent 时间 +16.89%、代理正文 -6.95%，没有通过 input、output、时间或 15% 最小正文收益门。
- 用户已通过 ADR-0002 接受新的长期评测政策：后续采纳实验必须加入隔离的真实应用开发任务，滚动组合目标约为 60% 产品代码、20% 安全／迁移／跨模块、20% 文档／发布治理；三任务 Pilot 至少两项以可运行代码为主要交付物。
- Marglo／NextStep Seed_2 已被确认适合作为任务模式来源，但真实工作树、用户数据、凭据和未提交改动不得进入实验。
- Pilot 008 的 Skill Entry Router R 曾完成静态准备，但没有启动模型；其固定入口成本假设已在执行前退出当前 Pilot，历史文件和 Validation 保留且不冒充运行证据。
- 用户已通过 ADR-0005 接受新的主成本口径：从任务 Prompt 到首次允许产品 `fileChange` 启动前的累计 `input-to-scope-lock`；由 Harness 被动派生，不要求 Agent 输出 Manifest、Receipt、Selected Evidence 或访问总结。
- Pilot 008 当前比较共享同一 9,109-byte 完整 Skill 的 P/S：P 使用 598-byte 线性入口，S 使用 1,638-byte 任务路由入口；三项 P/S Prompt 分别完全等长为 11,708、11,705、11,666 bytes。
- app-server Scope analyzer 已实现首次写入边界、边界前最后累计 usage、单调性、thread／turn、允许路径和写前代理 proof 检查；合成 4-case self-test、passive 无 reason-code 代理、P/S 嵌套 preflight 和 dry-run 通过。
- 首次授权的 app-server compatibility smoke 使用当前桌面包 `codex-cli 0.148.0-alpha.15`，观察到同 turn
  三次单调累计 usage；但临时目录只复制了 CLI、遗漏同版本 code-mode host，Agent 无法启动读取工具，
  因而没有 `commandExecution` 或 `fileChange`。该运行按 contaminated 封存，不能判断目标顺序。
- Smoke 002 使用与当前桌面包逐文件哈希一致的完整 0.148.0-alpha.15 runtime。读取命令在 event 59
  完成，累计 usage 在 event 60 更新，首次 `fileChange` 在 event 62 启动；只修改 `marker.txt` 且 turn
  完成。ordering-only analyzer 得到 exact pre-write input 19,361、cached 9,984、non-cached 9,377。
- Smoke 002 原始根按 decision-supporting 封存且 manifest 39/39 有效；配置现可标记
  `scope_usage_ordering_verified: true`。该证据只验证事件顺序，没有要求或证明真实 proxy slice。
- Pilot 008 接入正式 app-server transport、完整事件 validator、proxy proof、Scope analyzer、正式验证、
  成对失败关闭和 R0 封存后启动首对迁移任务。P 直接读取仓库外已安装 Skill 而 contaminated；P/S 又
  共同暴露索引名和文档词形 Oracle 假阴性，runner 正确停止后续任务。两份 manifest 仍有效，该 Pilot
  不产生采纳比较。
- Pilot 009 保持相同任务目标、完整 Skill、P/S 入口 treatment、Terra medium 和采纳门，只修正已证明的
  外部 Skill 输入边界和 Oracle 问题。六个正式 run 的装置、exact Scope、formal validation 和 R0 全部
  有效；未出现仓库外读取。
- Pilot 009 聚合写前 input 为 P `540,105`、S `446,904`，S/P `0.8274`；写前 non-cached input、唯一
  slice bytes、完整 input、output 和 Agent seconds 比分别为 `0.8711`、`0.8126`、`0.9059`、`0.9453`、
  `0.9595`，所有冻结成本门通过。
- Pilot 009 冻结 Oracle 报告 P/S 0/3；只读语义复核确认 feedback 与事实对齐任务只是自然语言词形
  假阴性，P/S 真实质量均为 2/3。迁移任务行为与数据安全通过，但两侧 PROGRESS 都遗漏未来版本写前
  拒绝事实，维持失败。3/3 质量门未通过，S 不采纳。
- 开发任务 C1（不是 R0／R1／R2 evidence layer）的任务／Oracle v0.2 无模型静态控制包已实现：四层 verdict 独立区分形式有效性、语义质量、结构化
  State／未来版本遗漏和 apparatus contamination；公开 State schema、7 文件 checksummed fixture 与 20 个
  baseline／paraphrase／contradiction／mutation／manual-review／contamination cases 已通过。
- 静态包对每项自然语言事实覆盖三种 positive paraphrase 和两种 contradiction，并用公共 API、SQLite
  终态及 Git 范围检查阻断 guard 删除、索引列交换、未来版本检查后移、helper bypass、State omission 与
  越界写；索引改名保持 pass，未知措辞进入 `manual_review_required`。
- Oracle 层已具备申请 Pilot 010 设计的静态条件，但 Pilot 010 尚未创建、未运行；任务级 Prompt 等长、
  嵌套隔离、完整事件链、Scope pipeline 和目标 runtime 握手仍须在任何模型样本前单独冻结验证。
- 已完成 `Ariestar/sivtr` 固定提交 `4fae091` 的外部源码观察：其类型化 WorkRecord／WorkRef、WorkSet
  anchors、渐进检索与只读 MCP 适合作为“情境证据层”参考，但不具备 Orrery 的权威事实职责。研究没有
  采纳依赖、Adapter、路由策略或新 Pilot；隐私生命周期、公开检索快照缺失和文档漂移仍是明确边界。
- GX1 在隔离 Candidate `f5fd5afa3f9b133166495119080629a5be5f67b2` 对固定
  `fireworks-tech-graph` Skill 做了两套本地关系图评测，结果为 8/12。其 lane／port／corridor／geometry
  技术可辅助 W7.3，静态 runtime、生成 SVG/HTML、移动缩放和关系语义均不采纳为产品或 Authority。

## 当前产品影响

- 发布版 Skill 不强制 Context Manifest、Selected Evidence 或 Access Receipt。
- B 只是实验基线，不是发布策略。
- Pilot 007 没有支持采纳 B；不新增产品 ADR、不修改发布 Skill。若未来仍研究显式 Manifest，应形成独立假设和新 Pilot，不能改写或补跑 Pilot 007／008。
- H1、Context Aperture v0.1 和 H2 都没有成为发布策略；H2 对照已结束且不采纳。受控读取代理与 validator 继续作为研究 Harness，不是普通用户要求。
- ADR-0002 与 ADR-0005 只约束研究设计，不改变当前发布 Skill，也不重新解释 Pilot 001–007。
- Pilot 009 的 S 仍只存在于 `experiments/`；成本方向信号不足以越过质量门。R 作为未运行历史候选保留，
  S 不进入发布 Skill 或模板，也不新增产品 ADR。
- Oracle v0.2 的公开 State schema 只属于研究 fixture，不是发布版 Skill／模板或通用 Authority Model 的
  新契约；静态 readiness 不构成模型运行授权或 treatment 采纳。

## 证据

- [研究综述](../library/2026-08-17-task-context-provenance-and-documentation-overhead.zh-CN.md)
- [Pilot 003 报告](../../experiments/context-routing/results/2026-08-18-pilot-003-terra-medium.md)
- [B/C 确认轮](../../experiments/context-routing/results/2026-08-18-pilot-003-bc-confirmatory-terra-medium.md)
- [Pilot 004 B/H holdout](../../experiments/context-routing/results/2026-08-18-pilot-004-bh-holdout-terra-medium.md)
- [H2 候选](../../experiments/context-routing/designs/context-aperture-v0.2-h2.zh-CN.md)
- [读取证明设计](../../experiments/context-routing/designs/harness-content-read-proof-v0.1.zh-CN.md)
- [原始证据保留策略](../../experiments/context-routing/designs/raw-evidence-retention-v0.1.zh-CN.md)
- [装置验证](../validation/2026-08-18-h2-read-proof-apparatus.md)
- [Pilot 005 / 006 结果](../../experiments/context-routing/results/2026-08-18-pilot-005-006-bh2-terra-medium.md)
- [Pilot 005 / 006 验证](../validation/2026-08-18-pilot-005-006-bh2.md)
- [B 采纳候选](../../experiments/context-routing/designs/context-manifest-b-adoption-v0.1.zh-CN.md)
- [Pilot 007 实施计划](../implementation/plans/2026-08-18-context-manifest-b-adoption-experiment.md)
- [Pilot 007 准备验证](../validation/2026-08-18-pilot-007-preparation.md)
- [Pilot 007 R2 结果](../../experiments/context-routing/results/2026-08-18-pilot-007-pb-adoption-terra-medium.md)
- [Pilot 007 运行验证](../validation/2026-08-18-pilot-007-pb-adoption.md)
- [ADR-0002 真实开发任务组合](../decisions/0002-real-development-benchmark-portfolio.md)
- [ADR-0005 Scope Lock 前 input](../decisions/0005-prewrite-scope-acquisition-input.md)
- [真实开发基准 Approved Design](../design/real-development-context-routing-benchmark.md)
- [Marglo 素材观察](../library/2026-08-19-marglo-benchmark-source-notes.zh-CN.md)
- [Skill Entry Router R 候选](../../experiments/context-routing/designs/skill-entry-router-v0.1.zh-CN.md)
- [Pilot 008 历史 Skill Entry Router 实施计划](../implementation/plans/2026-08-19-skill-entry-router-pilot-008.md)
- [Pilot 008 历史准备验证](../validation/2026-08-19-pilot-008-preparation.md)
- [Scope Acquisition Router S 候选](../../experiments/context-routing/designs/scope-acquisition-router-v0.1.zh-CN.md)
- [Pilot 008 Scope Acquisition Plan](../implementation/plans/2026-08-19-scope-acquisition-pilot-008.md)
- [Pilot 008 Scope Acquisition 重构验证](../validation/2026-08-19-pilot-008-scope-acquisition-reframe.md)
- [App-server Scope Ordering Smoke 001](../validation/2026-08-19-app-server-scope-ordering-smoke-001.md)
- [App-server Scope Ordering Smoke 002](../validation/2026-08-19-app-server-scope-ordering-smoke-002.md)
- [Pilot 008 formal apparatus stop](../validation/2026-08-19-pilot-008-formal-apparatus-stop.md)
- [Pilot 009 Plan](../implementation/plans/2026-08-19-scope-acquisition-pilot-009.md)
- [Pilot 009 Validation](../validation/2026-08-19-pilot-009-ps-scope-run.md)
- [Pilot 009 R2 结果](../../experiments/context-routing/results/2026-08-19-pilot-009-ps-scope-terra-medium.md)
- [真实开发任务与 Oracle v0.2](../../experiments/context-routing/designs/real-development-task-oracle-v0.2.zh-CN.md)
- [C1 Oracle v0.2 静态结果](../../experiments/context-routing/results/2026-08-22-c1-oracle-v0.2-static-controls.md)
- [C1 Oracle v0.2 静态验证](../validation/2026-08-22-c1-context-routing-oracle-v0.2-static-controls.md)
- [sivtr 统一工作记忆层观察](../library/2026-08-19-sivtr-work-memory-source-notes.zh-CN.md)

## 已知边界

- Agent receipt 仍是自述；新代理+JSONL 可在受控命令面证明返回切片哈希与模型侧命令输出一致，但不证明模型注意或理解。
- Pilot 004 冻结 v1 Oracle 存在假阳性；原 exit 1 必须与 v2 复核一起解读。
- token 统计受 Codex 缓存上下文和工具输出影响，不能只用“读取文件数”解释。
- JSONL 是事后审计；Hook 未工作时不能宣称直接读取已被执行前阻断。
- Pilot 006 样本只有两个高风险任务；它足以判定当前 H2 未达到冻结质量门，不足以支持普遍模型结论。
- Pilot 007 只有三项新任务且存在共同装置缺陷；原始成本差异是反对采纳的风险信号，不是对所有模型／任务的普遍因果估计。
- 真实开发任务会增加 fixture 和 Oracle 成本；在独立 Plan、脱敏检查和嵌套 preflight 完成前，不得直接启动新 Pilot。
- Smoke 002 已证明当前 0.148.0-alpha.15 app-server 能在首次写入前提供同 turn 累计 usage；该能力仍可能
  随 Codex 版本变化，正式运行必须记录版本并先做 preflight。Smoke 未使用读取代理，不能替代正式 run 的
  proxy proof、允许路径和完整事件流验证。
- Pilot 009 只有三项任务和一个模型/runtime，且写前 input 中 cached token 占比很高；一致的成本下降是
  值得复测的方向信号，不是跨仓库普遍因果结论。自然语言 Oracle 的 lexical false negative 必须在后续
  Pilot 前由 paraphrase controls 阻断。
- Oracle v0.2 controls 只验证合成 feedback／SQLite／State 模式；未来 Pilot 的每个新任务仍必须拥有自己的
  positive／negative／mutation／paraphrase controls，不能把这 20 个通用 case 当作任务级 Oracle 已冻结。
