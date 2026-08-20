# sivtr 统一工作记忆层观察

Date: 2026-08-19
Authority: Library；本文件记录外部项目观察与候选启发，不证明任何集成、策略或产品依赖已被采纳
Source: [`Ariestar/sivtr@4fae091`](https://github.com/Ariestar/sivtr/tree/4fae091561bb8cc144f99eee6f42fff737c5c2ce)

## 研究范围与证据状态

- 2026-08-19 固定读取 `main` 提交 `4fae091561bb8cc144f99eee6f42fff737c5c2ce`；该提交时间为
  `2026-08-19T13:51:18+08:00`，不能用来代表未来 `main`。
- 观察时最新公开 Release 是 [`v0.5.1`](https://github.com/Ariestar/sivtr/releases/tag/v0.5.1)；固定提交的
  `Cargo.toml` 与 `CHANGELOG.md` 已写 `0.6.0`，但 GitHub 尚无 `v0.6.0` tag／Release，因此本文只称其为
  工作树版本，不称为已发布版本。
- 阅读了 README、Agent 指令、Skill、MCP、统一 record／ref／WorkSet、provider registry、BM25／评估、
  local-first／remote、known issues 与相关源码。仓库为 Apache-2.0。
- 两次执行 `cargo test --workspace --locked` 都在进入项目测试前被本机 Windows 拒绝运行 Rust 依赖的
  build script（`os error 5`）；把 `target` 移到 D 盘仍相同。源码静态包含 659 个 `#[test]` 标记，但这
  不是通过数，本文不宣称固定提交测试通过。
- 仓库没有公开 `eval-snapshot.json`；检索文档报告的 1,328 records／22 queries 指标只能证明作者记录了
  一套方法与结果，不能仅凭公开仓库独立复算其 corpus／qrels。

## 它实际解决什么问题

`sivtr` 把终端命令与输出、多种 coding Agent 的本地 transcript、临时 pipe／run capture 归一化为一个
可搜索、可引用、可渐进展开的工作记忆空间。人类主要通过 TUI 浏览；Agent 通过只读 MCP 或 CLI 搜索、
筛选、定位和展开。它的主张不是“自动总结一切”，而是尽量回到可引用的原始工作事件。

这使它与 Project Orrery 的关注面相邻但不同：

| 维度 | sivtr | Project Orrery |
| --- | --- | --- |
| 主要对象 | 终端输出、Agent turn、工具调用／结果等情境性工作记忆 | Seed、ADR、Approved Design、Plan、State、Validation 等长期项目事实 |
| 最小单位 | `WorkRecord`／类型化 `WorkPart` | 权威文档、实现、验证记录中的事实单元 |
| 定位方式 | 稳定 `WorkRef`、WorkSet anchors、search／filter／nav／zoom | 入口索引、State 链、有效 ADR、活动 Plan 与真实实现 |
| 真值立场 | 历史 memory 是证据，仍须检查当前文件和测试 | 当前实现与外部状态是真值；文档层分工决定事实、理由、计划和证据 |
| 主要风险 | transcript 敏感信息、陈旧记忆、检索误召回、缓存／分享生命周期 | 权威层漂移、文档负担、发布态与工作树态混淆、派生视图越权 |

因此二者更像互补层：`sivtr` 回答“之前发生过什么、原输出在哪里”，Orrery 回答“当前什么是真的、为何
这样决定、下一步受什么约束”。历史 Agent 对话不能因为进入 memory 就升级为 State 或 ADR。

## 值得学习的实现模式

### 1. 类型化统一模型，而不是 provider-specific 文本拼盘

[`WorkRecord`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/crates/sivtr-core/src/record/model.rs)
把 terminal command 与 chat turn 放进同一 schema；`WorkPartData` 保留 Prompt、Command、User、Assistant、
ToolCall、ToolResult、Skill、Thinking、Output、Error 等类型。14 个 provider 由
[`AgentProviderSpec` registry](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/crates/sivtr-core/src/agents/mod.rs)
统一发现和实例化，公共检索面不手写 vendor 分支。

可借鉴点不是复制 provider 列表，而是让“来源适配”止于边界，后续选择、引用、过滤和展示共享一种模型。
这与 ADR-0004 的 Core／Adapter 边界方向一致。

### 2. `records + anchors` 支持真正的渐进披露

[`WorkSet`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/src/commands/memory/workset/mod.rs)
同时保存 materialized records 与当前 active anchors。search 找到候选，filter 缩小，nav 做确定性结构移动，
zoom 扩邻居，show 最后展开正文；中间结果可保存在 `@last`／`@name`。

这比“先把所有可能相关正文塞进 Prompt”更接近 Project Orrery 当前的 Scope Acquisition 研究目标。可以把
它抽象成候选实验概念：Harness 记录可寻址证据集合与活动锚点，Agent 只在需要时展开正文。但这只是启发，
不能据此修改 S treatment 或自动创建 Pilot 010。

### 3. 精确引用与证据纪律同时存在

[`WorkRef`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/crates/sivtr-core/src/record/refs.rs)
支持 `[origin:]source/session/record[/part]`；Skill 的核心规则是先窄搜、只展开最小上下文，并把 retrieved
memory 当作证据而非当前真值。只读
[`MCP server`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/src/mcp/server.rs)
只暴露 search／show／zoom／filter／status，Skill 负责“何时和怎样取证”，执行面与操作策略分开。

这与 Orrery 的“Agent 回执是自述、当前实现才证明现状”相容。若未来为 Observatory 增加外部证据适配，
应继续区分 `AuthorityRef` 与 `EvidenceRef`，不能把二者混成一种搜索命中。

### 4. 检索质量用冻结 corpus 与逐查询指标讨论

[`BM25` 实现](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/crates/sivtr-core/src/search/bm25.rs)
按类型化 WorkPart 做 passage retrieval，使用 CJK bigram、字段权重和确定性 tie-break；
[`eval`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/crates/sivtr-core/src/search/eval.rs)
输出 recall@k、precision@k、MRR、NDCG@k，并保留逐查询结果。文档还公开了无效尝试：recency fusion 会使
近期闲聊压过旧的真实命中，PRF 调参也曾降低 NDCG。

这类“固定数据、逐项失败分析、坏结果也保留”的态度值得借鉴。Orrery 的 Oracle 仍须更严格地区分行为、
数据安全、范围和事实链，不能把平均检索分数替代任务质量门。

### 5. Local-first 与远程权限模型有清楚轮廓

远程层采用 Device Daemon + Identity + Share + Grant + Mount；分享显式 opt-in、只读、邀请有期限，传输
使用 iroh。代码在授权后才查询 share root，并在出站前可执行脱敏。这个模型适合参考“另一个 workspace 的
证据如何被命名和挂载”，尤其是 `origin:body` 不改变本地 ref 主体的做法。

## 不能直接照搬的边界与反向样本

### 文档已经出现明显漂移

- [`AGENTS.md`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/AGENTS.md)
  声称是单一 Agent 指令源，但 Project／Stack／Commands 仍为空；
  [`CLAUDE.md`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/CLAUDE.md)
  又维护了大量独立架构与命令说明。
- 架构文档仍列出已经不存在的 `app.rs`、`buffer/`、`parse/`、`selection/` 等路径；Roadmap 中多项已落地
  功能仍标为未完成。
- `docs/retrieval-literature.md` 仍引用不存在的 `search/fusion.rs` 与 `FUSION_ENABLED`；`docs/retrieval-eval.md`
  的“已知限制”仍描述已经被 passage model 替代的头尾窗口。
- GitHub 的 [MCP contract 稳定化 issue #96](https://github.com/Ariestar/sivtr/issues/96) 仍开放，因此当前
  WorkRef／WorkSet MCP 表面适合研究，不宜视为稳定外部兼容契约。

这正说明“有很多好文档”不等于“有权威链”。Orrery 不应复制这些说明文本，而应学习如何让 State、当前
实现与生成索引保持可审计同步。

### 隐私与生命周期仍是高风险区

- [`redact.rs`](https://github.com/Ariestar/sivtr/blob/4fae091561bb8cc144f99eee6f42fff737c5c2ce/src/remote/redact.rs)
  明确说明 regex redaction 不是安全边界；Windows 本地 daemon token 文件权限也没有 Unix `0600` 等价保证。
- 保存 `@name` 时，WorkSet 会把完整 materialized records 写入 state 目录；解析缓存也把 transcript 派生的
  `WorkRecord` 写入 data-dir cache。这些副本能提高性能和复用性，但扩大了敏感数据保留面。
- Roadmap 把 retention／expiry／forget／purge、share audit、selective disclosure 和 provenance freshness
  仍列为未来工作。当前“local-first”不能被扩写成“不会复制敏感数据”或“已有完整遗忘机制”。
- [issue #130](https://github.com/Ariestar/sivtr/issues/130) 记录 TUI 搜索 corpus fingerprint 不包含标题／
  正文，内容变化而 ref 不变时可能返回陈旧缓存。这是稳定 ref 与 freshness 不能混为一谈的具体例子。

若 Orrery 将来读取此类 memory，必须由新的安全边界决定 opt-in、允许 source、最小返回、凭据／用户数据
排除、缓存位置、保留期、删除与审计；不能让观测台默认扫描或打包原始 transcript。

## 对 Project Orrery 的候选启发

以下均保持在 Library／实验候选层：

1. **双引用类型**：观测台或未来 Adapter 明确区分权威 `AuthorityRef` 与情境 `EvidenceRef`；任何摘要都要
   回链，且 EvidenceRef 不得直接更新 State。
2. **锚点式渐进披露**：在下一轮无模型 controls 中评估“候选集合 + 活动锚点 + 按需展开”，但继续由
   Harness 被动记录，不要求 Agent 写 Manifest／Receipt。
3. **可选 memory evidence adapter**：长期可研究从 `sivtr` CLI／MCP 只读获取验证输出或历史讨论，作为
   人工写 Validation／Handoff 的证据输入；它不是发布 Skill 的默认依赖，也不进入权威事实投影。
4. **检索评估纪律**：若 Observatory 以后新增全文／RAG，必须公开可发布的脱敏 corpus 契约、qrels／Oracle、
   per-query 失败和 freshness 规则；私有快照结果不能单独支撑产品声明。
5. **反向验证样本**：`sivtr` 的 Agent 入口、架构、Roadmap 与代码漂移适合作为文档一致性任务模式来源，
   但只能从固定提交构造最小脱敏 fixture，不能复制真实 transcript、缓存或用户目录。

## 当前结论

`sivtr` 最值得学习的不是“统一记忆”口号，而是类型化事件、稳定引用、WorkSet anchors、渐进披露、只读
Agent 接口和“memory 只是证据”的纪律。它也展示了 Orrery 试图解决的另一半问题：快速演化项目即使文档
很多，也会在入口、架构、Roadmap、发布态和实现态之间漂移。

当前不建议把 `sivtr` 设为 Project Orrery 依赖，也不修改发布 Skill、Observatory、Scope Router 或下一
Pilot。若用户未来接受具体集成方向，应先形成 ADR，明确权威／证据分层、隐私生命周期、Adapter 契约和
可复现验证门。
