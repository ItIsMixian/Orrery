# 当前进度

Updated: 2026-08-20

## 当前阶段

Project Orrery v0.2.0 已公开发布，Pilot 007 已封存且 B 不采纳。ADR-0005 把当前效率目标定义为从任务 Prompt 到首次允许产品写入前的累计 input；Harness 被动派生 Scope Lock，不要求 Agent 输出 Manifest 或回执。Pilot 008 的首对正式运行因 P 读取外部已安装 Skill 和共同 Oracle 假阴性而停止并封存。修正后的 Pilot 009 已完成三项 P/S、共六个 Terra medium run：装置、exact Scope、formal validation 和 R0 全部有效，S/P 聚合写前 input 为 `0.8274`，所有成本门通过；只读任务质量 P/S 均为 2/3，迁移任务共同遗漏 PROGRESS 的未来版本拒绝事实，因此 3/3 质量门失败，S 不采纳。下一步先落实分层任务／Oracle v0.2 的 paraphrase 与 mutation controls，不自动补跑模型。平台适配方向另由 ADR-0004 接受单仓库分包、canonical `AGENTS.md`、独立组件版本和真实 runtime 验证门；Phase 0、Phase 1 和 Phase 2 的仓库实现检查点已完成，当前工作树已有未发布 Core／CLI／Observatory 源码包、旧 Skill 兼容入口，以及可独立归档和可恢复安装的薄 Codex Adapter，但没有真实 Codex runtime E2E、独立组件发布或第二平台实现。ADR-0003 的凭据加固已由 ADR-0006 收敛为 Broker-only docsite：本机托管为默认，外部隔离只绑定 client token，直接 Provider UI／运行／Q&A CLI 入口均已移除并通过本地验证，但尚未提交或进入公开 v0.2.0。

2026-08-20 已把三个 Agent 交错留在共享 `main` 工作目录的成果先封存为不可变恢复提交，再在独立 integration worktree 中按研究、产品和权威状态拆分并合入。ADR-0007 已正式接受一任务一分支／worktree、三层事实作用域与干净集成规则；默认 59 passed + 2 expected skips、动态 61/61、结构／静态站／235 份 Markdown 本地链接验证通过。当前只完成人工采纳与恢复流程，自动 session、重叠检测、主 worktree 守卫和 integration CLI 仍未实现；改动尚未推送或发布。

## 已完成

- [x] 通过 ADR-0001 正式采纳 Project Orrery 自托管权威链。
- [x] 建立真实 Agent／维护者入口、State、Validation、Snapshot 与开发日志。
- [x] 明确 `docs`、`experiments`、发布 Skill 和仓库外 benchmark 的职责。
- [x] 完成 Pilot 003 全量、修复后的 B/C 确认轮和 Pilot 004 B/H holdout。
- [x] Pilot 004 v1 Oracle apparatus failure 已保留，v2 只读复核已记录。
- [x] 修复 installer 会复制模板 `__pycache__`／`.pyc` 的问题。
- [x] 完成本地集成验证：28 项默认测试（27 通过、1 项按设计跳过）、启用动态 reader 后完整 28/28 通过、24 项 benchmark 语料与 6 份 run record 通过、文档站与本地链接检查通过。
- [x] 形成 Context Aperture H2 候选：取消 Agent 自写完整 Manifest、Selected Evidence 与 Access Receipt，改由 Harness 从任务配置和代理事件生成。
- [x] 实现受限读取代理、JSONL 独立审计、可选 Hook 增强、原始证据 seal/verify/status 与 7 项专项测试。
- [x] 完成 10 轮真实 CLI 兼容性探测并逐轮封存；全部 manifest 可验证，确认 Windows Codex CLI 0.147.0 的非交互 Hook 未触发，当前采用 JSONL 事后作废模式。
- [x] 完成全仓回归：默认 35 项中 34 通过、1 项按设计跳过；动态 reader 开启后 35/35 通过；benchmark、integrated build、文档站、链接与 diff 检查通过。
- [x] 冻结 PO-CR-025／026 两个新高风险任务及 B/H2 Prompt、Oracle、模型、执行配置和成本口径。
- [x] 保留 Pilot 005 的四个装置失败 run，并以修正后的 Pilot 006 完成 4 个正式运行；四份 raw manifest 均可验证。
- [x] 以 v3 规则只读复核 Windows CRLF stdout 假阴性；Pilot 006 四个运行的内容读取证明均有效，原始分类没有被改写。
- [x] 完成研究轮最终回归：默认 39 项中 38 通过、1 项按设计跳过；动态 reader 开启后 39/39 通过；24 项 corpus、6 份 run record、integrated static build、文档站、本地链接和 diff 检查通过。
- [x] 将 `bb2c768`、`96bfd21`、`f9cd508` 全部推送到公开 `origin/main`。
- [x] 冻结 Pilot 007 的 P/B treatment、三项新任务、独立 Oracle、Terra medium 配置和采纳门；baseline negative control 与 dry-run 通过，未启动模型调用。
- [x] 完成 Pilot 007 准备回归：专项 12/12、默认 39/40（1 skip）、动态 reader 40/40，corpus／run records、文档站、本地链接与 diff 检查通过。
- [x] 完成 Pilot 007 六次 Terra medium P/B 运行；所有 CLI 最终 exit 0，六份 R0 manifest 6/6 校验有效，没有隐藏重试。
- [x] 完成 Pilot 007 R2 只读复核：记录共同装置缺陷，将 029 的固定词形 Oracle 假阴性与 027 的真实跨平台排序遗漏分离，并按冻结成本门停止 B 采纳。
- [x] 通过 ADR-0002 采纳真实开发基准任务组合，并形成隔离、脱敏、任务比例与 Oracle 层级的 Approved Design。
- [x] 将动态 docsite 的 AI 服务设置入口移到顶栏主题按钮左侧，同步根观测台与发布模板，并完成桌面／移动端和全仓 40/40 回归；该 UI 小优化不新增 ADR、尚未发布。
- [x] 完成 Pilot 008 Skill Entry Router 历史准备：P 已冻结为 Pilot 内 9,109-byte 快照，R 为 2,386 bytes，三项 Prompt 降至 P 的约 44.5%–44.7%；3/3 negative、3/3 positive、嵌套 preflight、dry-run 和专项 13/13 通过。该 treatment 未运行模型，并在执行前由 ADR-0005 取代。
- [x] 完成 Pilot 008 Scope Acquisition 重构：P/S 共享 9,109-byte Skill，三项 Prompt 逐项等长；实现被动写前 usage analyzer、无 reason-code 代理模式、P/S 嵌套 preflight 和 formal fail-closed。分析器 4-case、上下文专项 17/17、默认全仓 49 passed + 2 expected skips、benchmark 与 integrated static build 通过，未运行模型。
- [x] 执行 App-server Scope Ordering Smoke 001：当前桌面包为 `codex-cli 0.148.0-alpha.15`，89 个服务端消息中有 3 次单调 usage 更新；因临时运行时遗漏 code-mode host，0 次命令、0 次 `fileChange`，按 contaminated 封存且 manifest 36/36 有效。修正后 smoke 自测 2/2、上下文专项 18/18、默认全仓 50 passed + 2 expected skips；该运行没有产生 Scope Lock 结论。
- [x] 执行修正后的 App-server Scope Ordering Smoke 002：同版本 runtime sibling 哈希一致；读取命令在事件 59 完成，写前累计 usage 在事件 60 到达，首次产品 `fileChange` 在事件 62 启动。独立 analyzer 报告 `input-to-scope-lock = 19,361`、`cached = 9,984`、`non-cached = 9,377`，测量链有效且顺序通过；原始根按 `decision_supporting` 封存，manifest 39/39 有效。该值仅是兼容性 smoke 的 ordering 指标，不是 P/S 成本结果，且本轮没有代理 proof。
- [x] 完成 Smoke 002 权威链与无模型回归：analyzer 4/4、ordering 2/2、上下文专项 18/18、默认全仓 57 passed + 2 expected skips、24 项 corpus、6 份 run record、integrated structure、docsite build、205 份 Markdown 链接与 diff 检查通过；Pilot 008 formal guard 继续生效。
- [x] 完成 Pilot 008 正式 transport 与首对运行：P/S Scope measurement 均 exact，但 P 的外部 Skill 读取
  使对照污染，共同迁移 Oracle 又暗中要求索引名和文档词形；两份 R0 有效，后续任务按设计停止。
- [x] 完成 Pilot 009 三对 P/S 正式运行：6/6 装置与 Scope 有效、6/6 manifest 可验证；S/P 写前 input
  `0.8274` 且所有成本门通过。只读质量 P/S 均 2/3，未过 3/3 门，S 不采纳。
- [x] 形成真实开发任务／Oracle v0.2：分离行为、数据安全、范围、结构化 State 和叙事一致性 verdict，
  并要求 paraphrase、contradiction、mutation controls；当前只是研究候选。
- [x] 通过 ADR-0004 接受平台中立 Core／CLI／Observatory／Adapter 分包边界，并形成 Approved Design 与分阶段 Implementation Plan；当前发布实现仍是 Codex Skill。
- [x] 完成 ADR-0003：直接模式凭据按 Provider／Base URL 绑定并失败关闭，本地写操作改为同源 POST，旧刷新 GET 不再调用模型，可选 Broker 提供固定端点、去重缓存和预算门；根观测台、模板、安装器、测试与 Validation 已同步。
- [x] 完成 ADR-0006：默认托管与外部隔离两种模式都以 Broker 为唯一 docsite 调用通道；UI 只注册上游，`set_key.py` 和独立 Q&A CLI 也失败关闭到 Broker。动态产品专项 16/16、默认全仓 57 passed + 2 expected skips，integrated build 与模板投影通过。
- [x] 完成 ADR-0004 Phase 0：固化 v0.2.0 发布清单与 CLI 人类输出，模板入口改为中立标题，并在 README 将 CLI 可移植路径、`experimental` Codex 与 `target` 其他平台分开表述。
- [x] 完成 ADR-0004 Phase 1：建立 Core／CLI／Observatory 0.1.0 源码包、canonical 作者模板、schema／兼容模型、managed-tool 清单和旧 Skill wrapper／fallback，并验证新旧入口等价。
- [x] 完成 ADR-0004 Phase 2 仓库实现检查点：建立独立 Codex Adapter 0.1.0、组件／runtime manifest、确定性 ZIP／checksum 和只管理 Adapter 目录的 dry-run／备份升级／可恢复卸载；临时目录专项 5/5 通过，真实 runtime 验证仍待授权。
- [x] 完成 `Ariestar/sivtr@4fae091` 外部源码观察，区分其情境工作记忆层与 Orrery 权威事实层；记录 WorkRef／WorkSet 渐进披露、只读 MCP、检索评估、隐私生命周期和文档漂移启发。没有采纳依赖、Adapter、路由策略或新 Pilot。
- [x] 恢复共享工作目录中的三项并发成果：保留 `a87c5a4` 恢复提交，在独立 integration worktree 中形成研究、产品、Library 和权威状态提交，并将临时协作决策分配为 ADR-0007。
- [x] 完成 ADR-0007 人工采纳验证：冻结 Pilot 输入逐字节保留，默认／动态全仓、结构、静态站、Markdown 链接与 Git 检查通过。

## 当前结论

- Context Aperture H1 正确性与 B 持平、读取更克制，但总 input token 高 47%，未通过采纳门。
- 发布版 Skill 仍不强制 Context Manifest、Selected Evidence 或访问回执。
- H2 正确性与 B 持平，但总 input token 高 18.5%、output 高 22.5%、代理正文高 23.7%、墙钟高 7.2%；非缓存 input 低 31.9% 不足以抵消总成本，因此 H2 不采纳。
- 当前装置只证明受控命令输出与代理切片一致，不证明模型理解，也不提供实时阻断。
- Pilot 007 没有显示 B 的质量收益；B 相对 P 聚合 input +25.68%、output +23.56%、Agent 时间 +16.89%，代理正文仅 -6.95%，不满足采纳门。
- 共同装置缺陷意味着不能把本轮宣传为普遍“科学证伪 B”；项目层面的保守决定仍是不采纳、不继续给当前 B 增加协议。
- 后续研究以滚动组合覆盖真实产品代码、安全／迁移／跨模块和文档治理；代码任务先验收行为与安全，再验收必要的文档同步。
- Pilot 009 已证明正式 Harness 能在 6/6 run 精确统计 `input-to-scope-lock`；S 的聚合成本方向优于 P，
  但任务质量只有 2/3，因此不能由“成本门通过”推导“路由可采纳”。
- Smoke 001 的最终 58,541 input 是无写入边界的整轮累计值，不是 `input-to-scope-lock`；不能用它估算或代替主指标。
- Smoke 002 的 19,361 input 是单个 ordering-only 兼容性 turn 的精确写前累计值，不是任一正式 P/S 样本，也不能支持路由收益结论；其 `minimum_prewrite_content_reads` 为 0，因此没有独立内容交付证明。
- 平台中立 Core／CLI／Observatory 源码边界已经实现，但 `implemented` 不等于 `released`：当前没有独立组件发布产物、Harness JSON Adapter、第二平台集成或可声明的第二平台 `verified` 证据。
- v0.2.0 CLI 仍随 Codex Skill 分发；源码 wrapper 调用新 CLI，独立 Skill 使用冻结 fallback。Codex 因缺少完整真实 runtime E2E 继续保持 `experimental`。
- Codex Adapter 已成为独立的未发布薄产物，但它只声明对 Core API 1 和 CLI `>=0.1.0,<0.2.0` 的依赖；Core／CLI 尚未发布，因此它不是新的完整公共安装路径，也没有改变 v0.2.0 发布事实。
- 动态 docsite 已没有直接 Provider 路径；默认同用户托管 Broker 只提供统一路由和成本门，只有在独立 OS 身份或等价边界中配置并运行外部 Broker，才能把 Provider Key 隔离出 docsite／Agent 身份。
- `sivtr` 可作为未来“情境证据来源”的研究对象，但不能替代 State／ADR／实现真值；任何可选 memory evidence Adapter 都需要新的权威／证据分层、隐私生命周期和可复现验证决定，当前不进入发布版或下一 Pilot。
- 多人／多 Agent 现在有可执行的人工安全工作法，但还不是自动协调系统：独立 worktree 能隔离写入，唯一整合者能对齐权威文档；工具目前不能自动证明 Agent 没有误入主目录、发现跨 worktree 语义重叠或观察另一台机器的未 push 工作。

## 待办

- [x] 人工审阅本次自托管、实验与产品修复 diff，并确定分层提交及首次发布方案。
- [x] 按发布计划形成产品修复、研究证据、自托管、发布准备提交，并补充浅克隆 CI 修复。
- [x] 分支与 `main` 双平台 CI 通过，首个 [`v0.2.0` GitHub Release](https://github.com/yw9299-stack/project-orrery/releases/tag/v0.2.0) 已创建并验证。
- [x] 设计 H2，优先削减 Agent 生成的 Manifest、Selected Evidence、Receipt 和重复验证叙述。
- [x] 设计并实现由 Harness 证明内容读取范围的最小代理／JSONL 实验。
- [x] 冻结两个全新任务、B/H2 Prompt、Oracle、执行配置与成本口径。
- [x] 运行小规模 B/H2 对照，并按正确性、必要依赖召回、input token、代理字节和墙钟时间决定是否继续；结论为不采纳 H2。
- [x] 审阅并提交 H2 研究设施、Pilot 005／006 控制包和 R2 结论；研究层提交为 `bb2c768`，仓库外 R0 原始输出未进入 Git。
- [x] 将研究分支以 `--ff-only` 快进合并到本地 `main`；`main` 已包含 `bb2c768` 与 `96bfd21`，本轮不发布新 Skill 版本。
- [x] 将本轮全部提交推送到 `origin/main`；远端 `main` 与本地推送点一致。
- [x] 准备 Pilot 007 B 采纳实验及独立 Oracle，不执行正式模型样本。
- [x] 运行 Pilot 007 的 3 对 P/B 样本并生成 R2；结论为装置受污染且 B 成本／收益门失败，不采纳。
- [ ] 跨平台 byte-for-byte 可重复打包暂不进入本阶段；v0.2.0 已发布资产的 checksum 仍有效。
- [x] 为真实开发基准建立独立 Plan、脱敏 fixture、独立 Oracle、positive/negative controls 和嵌套 preflight。
- [x] 将 app-server 事件协议、代理 proof、R0 封存与汇总接入正式 transport，并在 Pilot 008／009 运行中
  验证成对失败关闭与六次完整证据链。
- [ ] 按任务／Oracle v0.2 为下一 Pilot 构造公开结构化 State 字段、分层 verdict、paraphrase 与 mutation
  controls；完成静态装置后再决定是否授权新模型样本。
- [x] 按[平台中立 Core 与 Adapter Implementation Plan](implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)完成 Phase 0 基线、命名和兼容测试。
- [x] 采用 `packages/*/src` 布局，Core／CLI／Observatory 初始未发布版本为 0.1.0；旧 Skill wrapper 保留至 0.3.x，最早 0.4.0 移除。
- [x] 建立 Codex Adapter 独立产物与安装／卸载边界：未知目录拒绝、已识别旧 Skill／Adapter 先备份再升级、卸载移入可恢复回收目录；Adapter 只声明外部 CLI 依赖。
- [x] 完成 Broker-first docsite gateway：所有 API 入口统一经 Broker 注册，默认托管不强制连接测试，外部模式只接收 client token；根／模板、README 和 Validation 已同步。
- [ ] 在明确授权后，把独立 CLI 与 Adapter 安装到隔离的真实 Codex 用户技能位置，记录精确 runtime／OS 的发现、调用、失败、更新和卸载 E2E；完成前保持 `experimental`，且不发布组件。
- [ ] 按 ADR-0007 活动 Plan 实现 Phase 0：版本化 worktree identity／session／overlap schema、Git fixture、integration ref 解析和主 worktree 识别；在此之前继续人工创建独立 worktree。

## Blockers / risks

- 仓库外 benchmark 已有 manifest、保留分类和脱敏边界，但尚无自动 R1 导出器；到期只报告，不自动删除。
- Pilot 004 正式 validator 保留 exit 1，因为冻结的 v1 Oracle 存在假阳性；正确结论依赖 checksummed v2 只读复核。
- v0.2.0 的 GitHub 资产和 checksum 一致，但 Windows 与 Ubuntu 从同一 tag 本地打包得到的 zip 字节不同；已确认条目集合一致，差异来自行尾与权限元数据，列入下一补丁。
- Windows Codex CLI 0.147.0 的 `codex exec` 未执行项目或会话内联 Hook；当前 JSONL 模式只能事后判废，不能执行前阻断。
- Pilot 006 只有两个高风险任务，足以否决当前 H2 的预设成本门，不足以推导所有模型和任务的普遍规律。
- Pilot 007 的外层 `benchmark` 分支会使嵌套 Pilot 006 dry-run 创建同名分支失败；任何未来 Pilot 必须在启动前用不同外层分支名覆盖该路径。
- Pilot 007 frozen Oracle 对 029 过度要求英文精确词形 `ExecutionPolicy`；R2 已修正语义判断，但没有回写原始 Oracle 或 raw summary。
- Pilot 009 frozen Oracle 对 033／035 仍存在自然语言固定词形假阴性；R2 只读复核为 P/S 2/3，没有
  回写 0/3 raw summary。下一 Oracle 必须用 paraphrase controls 在模型运行前发现这类问题。
- Marglo 来源仓库包含活跃工作树和潜在用户数据；未来只能从固定提交或显式白名单构造脱敏 fixture，不能直接复制当前工作目录。
- Broker client token 仍具有受模型白名单和每日预算约束的消费能力；同用户运行 Broker 只能减少重复调用和限制开销，不能宣称 Provider Key 已隔离。
- 当前多 worktree 规则没有强制执行器；若 Agent 仍在 `D:\coding warehouse\project-orrery` 共享主目录工作，Git 不会替项目区分所有权。恢复分支不可删除，功能 Agent 必须切换到分配的独立目录。

## 下一里程碑

上下文路由线路的下一安全里程碑是不调用模型地把任务／Oracle v0.2 变成新 Pilot 控制包：公开所有 exact
字段契约、分离五层 verdict，并用 paraphrase／contradiction／mutation controls 证明 Oracle。Pilot 009 的
成本方向信号可以作为继续研究的理由，但 S 在 3/3 质量门和维护者明确接受前不得进入发布 Skill 或模板。

平台适配线路的下一安全里程碑是 ADR-0004 Phase 2 的真实 Codex runtime E2E。仓库内产物和生命周期测试已就绪，但实际安装会改变用户技能目录并可能需要重启／新会话，因此必须先获得明确授权；在此之前保持 `experimental`，也不得宣称第二平台兼容。

多人协作线路的下一安全里程碑是 ADR-0007 Phase 0 的最小机器合约和 Git fixture；在任何自动命令完成前，继续使用一任务一个独立 worktree、主目录只集成、唯一整合者同步全局 State 的人工协议。
