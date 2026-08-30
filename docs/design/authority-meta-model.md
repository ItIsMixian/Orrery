# Authority Meta Model 语义设计

Status: Approved

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md), [ADR-0018](../decisions/0018-portable-operating-rules-and-authority-route-preflight.md)

Updated: 2026-08-30

## 目的

Authority Meta Model 是 Project Orrery 解释项目权威体系的规范语义层。它定义角色、各对象 lifecycle、跨角色 claim、事实作用域、证据类别、派生视图约束和语义版本，不是新的作者文档类型，也不决定用户项目的具体 Seed 内容。

它回答“怎样解释 Orrery 项目”，而不是包揽 Orrery 的全部运行行为。网络发现、任务调度、文件 lock、UI 布局、Broker 缓存和具体 CI provider 都由相应产品／技术 Design 管理。

## 三层模型

```text
Authority Meta Model
  roles / role lifecycles / claim dimensions / relations
  invariants / authority scopes / evidence semantics / model version
             ↓ interprets and validates; does not override project content
Project Authority Instance
  Product intent / Seed / ADR / Design / Plan / State / Validation / Snapshot
             ↓ describes and constrains
Implementation / configuration / assets / data / external state
```

“Meta”表示定义角色和解释规则，不表示其内容优先级高于项目 Seed。对某个具体项目而言，有效 Seed 仍约束其 ADR 与 Design。

## Authority roles

| Role | 语义职责 | 不证明什么 |
|---|---|---|
| Product intent | 期望产生的体验或结果 | 具体约束已经接受或实现 |
| Seed | 项目的长期目标、价值和原则 | 代码已经遵守这些原则 |
| ADR | 已决定什么、为什么，以及 amendment／supersession 历史 | 决定已经实现 |
| Design | 把有效决定展开为连贯规格；只有 Approved 才能约束 Plan | 实现已经完成 |
| Implementation Plan | 准备如何落地、验证和同步 State | 清单完成或实现存在 |
| Implementation | 实际代码、配置、资产、数据和外部运行状态 | 已满足 Design 或已验证 |
| State | 某个事实作用域下当前是什么，包括偏差与缺口 | 历史原因或未来计划 |
| Validation | 可复现证据支持或反驳哪些 claim | 自动把实现升级为符合所有意图 |
| Snapshot | 某个日期／版本的评估截面 | 替代 live State |

Library、Backlog、实验结果、AI 摘要和观测台卡片是输入或派生视图，不成为新的 authority role。

## Normative invariants

- Accepted ≠ Implemented ≠ Validated
- planned ≠ current
- historical ≠ effective
- observed ≠ authoritative
- derived view ≠ source of truth
- one reader projection ≠ a second fact store

## Role lifecycle 与独立 claim dimensions

各 authority object 可以有自己的 lifecycle，例如：

```text
ADR: Proposed → Accepted / Rejected → Superseded
Design: Draft → Approved → Deprecated
Review evidence: Current → Stale
```

Decision、Implementation 和 Validation 不组成单一 feature 状态机。它们是相关但独立的 claim dimensions：

```text
decision_status = accepted
implementation_claim = present
validation_evidence = failed
```

以上三个 claim 可以同时为真。Validation failed 不抹除 implementation exists；实现后来被移除也不抹除它在历史 revision 中曾存在。State 负责表达当前实现，Git／历史证据保留过去事实。

ADR-0001 的链表达 authority dependency、典型成熟路径和阅读方向，不要求每项变化逐节点执行。局部变化可以不需要 ADR／Plan，Validation 可以多次运行，后续 ADR 可以 amend／supersede 既有决定。

## Authority scopes

Authority scope 决定 claim 在什么 context 下有效：

| Scope | 含义 |
|---|---|
| Canonical | integration ref 已集成事实 |
| Candidate | 分支 HEAD 相对 merge base 的候选事实 |
| Worktree | 当前本地未提交事实 |
| Local-only | 成员主动上报但未形成跨机器代码证据的元数据 |
| Historical | 只在过去 revision／日期成立的事实 |
| Unknown | 证据不可见或不足，不能推导否定结论 |

Agent ownership、任务依赖、等待队列和文件 lock 属于 Coordinator runtime model，不是 Authority scope。

## Evidence semantics

Meta Model 描述 provider-neutral 的证据类别和能力边界：

| Evidence category | 可以支持 | 不能单独支持 |
|---|---|---|
| Revision content evidence | 某些 bytes／文件在某 revision 存在 | 模型读取、行为正确、当前仍有效 |
| Reproducible executable validation | 特定环境和命令下的可观察行为 | 超出范围的普遍正确性 |
| Tool／runtime trace | 某些工具事件发生、顺序和输出 | Agent 理解或未观测行为不存在 |
| Human／Agent assertion | 意图、解释、观察和不确定性 | 独立 authoritative fact |
| Derived summary／AI view | 导航、综合和风险候选 | primary evidence、批准或新项目事实 |

GitHub Actions、其他 CI、Git provider 或具体 Harness 都只是 evidence category 的实现，不由 Meta Model 指定为唯一合法 provider。

## Consumer conformance

一致性判断绑定完整输入：

```text
authority_model_version
+ repository snapshot
+ fact scope
+ evidence visibility
```

输入相同时，CLI、Viewer、Coordinator 等确定性消费者对 effective／current／implemented／validated 等 Core-derived 字段必须一致。输入作用域不同可以产生不同结果，但必须显示 scope、来源和 Unknown。

AI 自由文本不要求措辞一致，但必须：

- 不推翻、隐藏或升级 Meta Model 给出的状态；
- 不把 Unknown／Local-only／observed 写成 authoritative；
- 能链接回 Core-derived 字段和原始证据；
- 不计作 Reviewer、批准或独立 Validation。

这些是 derived-view semantic constraints，不是 UI 规范。颜色、布局、删除线和 summary section 数量由消费者 Design 决定。

## Core-owned evaluator boundary

ADR-0010 resolves AUTH-4: platform-neutral Core is the single deterministic semantics implementation owner.
The evaluator consumes pre-normalized observations plus the four conformance inputs. Markdown/Git/Harness
parsers, Coordinator runtime, UI projections and AI prose remain outside Core and must adapt into or consume the
Core result.

The first evaluator is experimental and fixture-bound. It may run in shadow mode but is not yet a stable
top-level Core API or manifest contract. Consumers must dual-run before switching, and an individual consumer
must be independently rollbackable.

## Meta Model version 与 document schema

Authority Meta Model 必须可版本识别。ADR-0011 将公开版本与内部 fixture 标识分离：项目在 `.project-orrery.json` 顶层用正整数 `authority_model_version` 选择语义模型，首版为 `1`；内部 conformance corpus 继续使用 `amm-fixture-v1`，不得把内部 ID 写入项目 manifest。

- `document_schema` 描述作者文档格式、字段和结构兼容性；
- `authority_model_version` 描述角色含义、claim／scope／evidence 解释规则。

格式可以不变而语义规则升级，语义规则也可以保持不变而文件格式迁移；二者不能用一个版本号替代。

消费者必须声明拥有 evaluator 与 conformance evidence 的离散模型支持集，不能用最小／最大区间填补未验证的版本。字段缺失表示 `legacy-unversioned`；未知、更新、已知但不受支持或非法版本均对确定性 Authority claim 失败关闭。原始 Markdown 仍可只读浏览，但 effective/current/implemented/validated 等结论保持 unavailable／Unknown。

普通安装、工具升级和 `--upgrade-tools` 不得选择或改写语义模型。语义迁移是单独的维护者决定，必须先提供只读 capability report 和 dry-run，再经备份、显式 apply、State 与 Validation 形成证据。模型 1 首次采用保持 `manifest_format = 1` 与 `document_schema = 1`；若将字段改成结构必填或改变公共 API，另行评审相应版本。

## Conformance fixture 最小覆盖

- accepted 但未实现；
- implementation present + Validation failed；
- implementation 历史存在但 current State 已移除；
- superseded／amended ADR；
- Draft／Approved Design；
- Plan 与 State 分离；
- Canonical／Candidate／Worktree／Local-only／Historical／Unknown；
- Snapshot 不替代 live State；
- Authority scope 与 Coordinator ownership／lock 不混型；
- 派生 Viewer／AI 不产生事实；
- 相同输入一致、不同可见性显式分歧。

## 复杂性与渐进提取

1. User-facing protocol：用户按需理解 Seed、Decision／ADR、Design／Plan、State、Validation、Snapshot；
2. Product machinery：installer、validator、migration、compatibility、docsite、multi-Agent coordination；
3. Orrery development infrastructure：benchmark、Oracle、read proxy、JSONL audit、实验 treatment、raw evidence。

内部复杂性通过渐进披露隔离，不永久禁止高级用户查看证据。能机械派生的信息交给 CLI／Harness，不进入固定 Agent 上下文。

接受本 Design 不授权大爆炸式重构。后续先盘点重复 semantics、冻结 golden／conformance cases，再沿稳定边界提取 parsing、authority model 和 project model。文件长度本身不是重构依据。

## Self-hosting 边界

Project Orrery Product Seed 可以启发 Meta Model，但两者职责不同。`docs/core/principles.md` 约束 Project Orrery 产品；ADR-0009 与本 Design 定义通用解释规则。文字重叠不把 Product Seed 自动变成 domain schema，也不把 Project Orrery 偏好注入用户 Seed。

## Portable Operating Rules 与 Authority Route Preflight

ADR-0018 不新增 Meta Model 层，而是在本 Design 已定义的同一语义层中增加两个普通消费者此前缺失的确定性消费面。

### A4a：`orrery-operating-rules-v1`

Core package 中只有一份 canonical JSON inventory。Schema 与 dependency-free parser 固定如下层次：

| 层 | 必需内容 | 边界 |
| --- | --- | --- |
| inventory envelope | contract/schema/inventory/version、Authority Model 版本、owner、hash domain、compatibility/failure policy | 未知/缺失/tamper 只返回 read-only/Unknown |
| portable rule | stable ID、rule version、message key、zh/en summary、stages、consumers、sources、strength、mechanical class、failure/Unknown、project-fact boundary | 不携带目标项目事实、Seed 或 Orrery 当前 State |
| portable concept seed | stable concept ID、aliases、authority source kinds 与 route hint | 只提供通用 bootstrap concept；不复制 self-host subsystem State |
| projection metadata | canonical digest、projection kind、writes/release/authority flags | Skill/CLI/Observatory 不可修改 owner 或升级状态 |

首版 inventory 从 Product Seed、AGENTS、ADR-0009/0011/0012 和 Skill migration/safety contract 中做有界提炼。跨项目规则包括：独立 claim dimensions、Unknown/作用域保留、派生视图非权威、create-only/no-overwrite、安装/迁移/集成/发布分离、持久决定经 ADR、证据与阶段匹配、秘密/生成物排除、未知版本失败关闭，以及 collaboration consumer 启用时的 Candidate/Canonical 隔离。组件版本、公开版本、当前工作流状态和实验结论不得进入 inventory。

Skill-only 投影可以打包与 canonical inventory 逐字节一致的 JSON。该副本由 drift test 证明为 exact projection；`SKILL.md` 不再手写另一份规则清单。

### A4b：`authority-route-preflight-v1`

Core 只接受 normalized concept registry、authority links、source observations 和 query intent；Markdown/AGENTS/Git/release 收集仍属于 CLI Adapter 边界。确定性路由顺序为：

```text
query intent
  -> alias entry / concept IDs (uncertain => bounded fan-out)
  -> AGENTS index link
  -> relevant State
  -> governing effective ADR / Approved Design
  -> requested implementation / Validation / distribution / release evidence
  -> four-axis claims + Unknown + novelty/absence decision
```

Concept registry 的每个 entry 至少包含 stable ID、subsystem ID、zh/en aliases、AGENTS/State links、governing ADR/Design links、implementation/distribution/release evidence hints 和 lifecycle。别名只负责召回；同名不同 concept 由 stable IDs、subsystem 与 authority link 区分。分类分数不足或并列时 fan-out，直到权威 source 收敛；低权威模板/README/Agent assertion 不可使搜索提前终止。

Route receipt 的 canonical shape 为：

```text
contract/schema/registry version + receipt hash
query class + normalized intent
selected concept IDs + ambiguity/fan-out
selected governing sources (authority order)
excluded lower-authority sources + reasons
claim dimensions:
  semantic_decision / implementation / distribution_consumer / public_default_release
negative-evidence scope + unresolved targets
novelty_absence_gate: allowed / rejected / unknown
writes=false / authority_promotion=false / release_promotion=false
```

每个 claim dimension 是 `present|absent|unknown`，并绑定 source IDs、fact scope 和 reason codes。一个轴的 evidence 不向另一个轴传播。State 过期、ADR 断链、unindexed concept、未知 schema 或伪造 Agent assertion都保留 Unknown/需补索引；模板缺失只会成为 excluded observation。

### Collector、Core 与消费者边界

| 路径 | 机械保证 | 不保证 |
| --- | --- | --- |
| Core inventory/route API | schema/hash/version、route precedence、receipt shape、four-axis non-escalation、absence gate | Markdown/Git 内容已被完整发现 |
| CLI/Harness | bounded project collector、Core invocation、JSON receipt、zero-write | Agent 一定使用 receipt |
| Unified Observatory | 同一 projection、Ask Docs preflight、只读页面和 Unknown guard | 模型自由文本绝不出错 |
| Skill | bootstrap 顺序与 exact inventory projection | 无 host hook 时不能阻止 Agent 跳过 |
| Host Adapter | 只有 runtime-verified pre-model hook 才能声称 enforced | discovery/install 本身不等于 pre-model enforcement |

### Bootstrap 顺序

支持 A4 的 Agent 在 scaffold、audit、maintenance 或 authority existence 查询前：

1. 读取 Skill 指向的 exact `orrery-operating-rules-v1` inventory；
2. 对 existence/implementation/distribution/release/visibility/novelty 查询运行 Authority Route Preflight；
3. 再读取目标项目 AGENTS、相关 State、governing ADR/Design 和实际 implementation/evidence；
4. 分四轴回答并保留 Unknown。

目标项目 Seed 继续由目标作者维护。新 scaffold 的 AGENTS/Seed 只解释两层关系并指向工具 inventory；brownfield upgrade 不改写这些文件。

### Unified Observatory 设计 brief

- Purpose：让维护者在同一个只读 `authority` 视图中区分“Orrery 如何工作”和“本项目相信/当前是什么”。
- Context：现有 dense analyst workspace，不改变 Unified Observatory 信息架构与视觉系统。
- Tone：克制、工程化、中文优先；普通说明在主视图，machine IDs/versions/source/enforcement 放入技术详情。
- Differentiator：不新增导航；把现有“权威状态”重构为普通用户可理解的“事实与规则”组合视图，其中项目原则、Orrery 工作规则和事实解释状态清楚分层，使用可扫描 ledger 而非重复栏目或营销卡片网格。
- Constraints：root-only/default-off、静态/动态都只读、零新增网络/凭据/执行权、1440×900 与 390×844 无横向溢出、console 无 error/warning、reduced-motion 保持。

现有 `authority` 页面只消费 Core projection，并继续作为唯一 sidebar identity。用户可见标题不直接使用内部术语“元规则”；managed/legacy/readiness 和 rule IDs 默认进入折叠技术详情。动态 `/api/v1/authority/operating-rules` 只返回启动时校验后的只读 payload；Ask Docs preflight 也消费相同 Core receipt，不能由模型生成或修改 route result。

### Conformance corpus

Corpus 以 normalized registries/observations 验证路由，不把自托管当前事实放入 portable inventory。至少包含 A4 真实失败及八个跨 subsystem 场景：design-only、implemented/unreleased、old public/new Candidate、template missing/Core present、State Unknown、similar names、misleading lower-authority document、zh/en/indirect query、以及 public/default 与 source scope 分离。Mutation cases 去除字面关键词、注入冲突模板/过期 State/断链 ADR/unindexed concept/unknown schema/forged assertion。

断言固定 selected evidence IDs、excluded sources、four-axis shape、Unknown/reason 与 absence gate，不固定 Agent 最终自然语言。

## 明确未决定

- AUTH-1：Authority 是否是最主要的产品核心；
- 最终 Python API、JSON schema、package path 和类型设计；
- 解析器／Observatory 拆分顺序；
- document schema／Core API 升级与发布版本。

这些内容留给下一次对话的 Plan／后续决策。本 Design 当前只把已接受的 Meta semantics 规范落地。
