# 跨会话交接

Updated: 2026-08-30

## 当前停止点

- 公开版本仍为 Orrery v0.2.0；tag 指向 `20fc95b`，ZIP／checksum 与历史 release manifest 不变。
- protected `origin/main` 已包含 SC1 exact `a9369ddeee0e74d4ddbe4bfc23a86b510d400457`；SC1 的产品 source baseline 为 `9ee831f`，只修改权威文档。
- CI5 exact `9ee831f` 的 Fast 与 Promotion 已完成：Promotion run `33235992711` 为 25/25 jobs PASS，双平台 required checks 均通过，Windows／Ubuntu 各聚合 390 tests／27 logical shards；同一 SHA 已进入 main。
- 当前本地 integrated Candidate 的未发布组件为 Core 0.1.18、CLI 0.1.22、Observatory 0.1.18；Harness JSON 为 0.1.2，其余 Adapter 为 0.1.1，支持状态仍为 `experimental`／`unreleased`。
- W1–W7、Personal／Team Observatory、workspace maintenance、LAN discovery／manual Host switch、relation execution 和只读 Graph 已进入 Canonical source。默认 docsite、公开模板、release manifest 和 v0.2.0 用户能力没有因此切换。
- R3 已把当前展示面收口为 Orrery；`project-orrery` 继续作为稳定 Skill／package／CLI／schema／协议及历史资产标识。R4/R5 未启动。
- SC1 已把权威入口、State、Plan 状态和 CI5 hosted evidence 对齐；Fast `33256438925`、Promotion `33256558285` 与 main Fast `33256757429` 均通过。该 source commit 没有执行物理 cleanup，Git-private session 状态也不升级为作者事实。
- 后续本机维护已归档并移除六个 `closed/superseded` worktree，只删除工作目录并保留 branch／commit；当前七个 registered worktree 中包含一个并发创建、未触碰的 `github-front-door-redesign`。
- 维护者已接受 ADR-0016／Unified Observatory Design：目标是一个可见 launcher、URL 与导航壳，内部 helper 可受管独立运行；现有 docsite 阅读、搜索、AI、作者信息架构和可识别视觉体验必须继承，U1 prototype 不是最终 UI。
- `codex/u1-u2-integration-baseline` 已按 W7.2.3 `30d44ff` → U2.2 `70e6ac9` 合流，联合 feature merge `0eaad30` 是供维护者复验的本地 integrated Candidate。联合 Fast 38/38 与真实 1440/390px 浏览器验收通过；44 项 Checkpoint 在既有 Maintenance fixture 上达到固定 90 秒预算，未虚报通过。它尚不等于 `origin/main`、默认切换或公开发布。
- ADR-0017 与 Approved Relation Capture Design 已接受。W7.3 Worktree Candidate `5fee848` 已实现 mechanical lineage、gate confirmation、integrator/absorbs 与 inbox，但尚未进入本地 integration；维护者已拒绝其 Graph UX，因此这些能力仍不能写成当前中央产品或发布能力。
- ADR-0018 与 Approved Authority-first Dispatch Design 已接受：U2.3 已完成，W7.3 已确认旧 scope revision；新的 Graph UX amendment 必须再次确认任务说明版本后才能恢复产品写入。自动 receipt 与 first-write enforcement 尚未实现。
- S0 `orrery-dispatch` 初始 source Candidate `9294902` 只包含 `SKILL.md`／`agents/openai.yaml`；首次 unmapped-path refusal 经任务说明 amendment 收口为 generic `release-packaging` mapping，Fast 44/44 与本地门通过。公共 v0.2.0／v0.3.0 与未来 S1 Conductor 状态未改变。
- PO enforcement local integration `8b73f26` 后，更新的 S0 两文件已安装到当前本机 `C:\Users\1\.codex\skills\orrery-dispatch`，source/installed hashes 一致。它仍未发布，不改变 release manifest／v0.3.0／S1 Conductor。
- A4 Candidate 与中央 authority-first 曾同时使用 `ADR-0018`。PO1 enforcement 已本地集成；当前线保留 authority-first `ADR-0018`，A4 已规范化为 `ADR-0019`，duplicate-number gate 与链接门通过。
- A4/U2.3 已本地合流：LF canonical inventory hash 解决 Windows CRLF 漂移，Fast 84/84、Checkpoint 89/89、Unified/Personal 25/25、A4/Adapter/wheel 15/15 及 390×844 Browser 通过。页面 help x=0/width=390、横向溢出 0、唯一功能 Ask Docs、console 0 warning/error；未 Promotion／push／public switch／release。

## 当前可继续的线路

1. **GX1 external graph Skill evaluation：** 在独立 branch/worktree 用真实关系与多冲突 fixture 评测 `fireworks-tech-graph`；不得修改 W7.3。完成后由维护者选择 replace／assist／selective merge／reject。
2. **S0 Orrery Dispatch Skill：** 两文件已在当前本机安装。后续只有独立 Release Plan 才能打包／发布它；不得把本机安装外推为其他用户可用，也不得扩成 S1 Conductor、自动 receipt 或首次写入阻断。
3. **PO1 decision allocation：** Skill PO 规则、duplicate-number gate、本机安装与 A4→ADR-0019 均已完成。
4. **Collaboration self-host：** 对真实 self-host 仓库运行 relation／maintenance 的只读 inspect 与 dry-run，补齐旧 Workstream lifecycle／closure 证据。任何 apply、undo、remove-worktree 或成员本机动作仍逐次本机确认。
5. **Authority production consumer：** 单独评审 managed projection 的启用／回滚；之后再由维护者选择实际 SemVer／candidate manifest。两项不得在同一未经审阅的发布动作里一起关闭。
6. **Documentation D2：** 只有维护者批准后才实现 `docs audit` scanner／CLI；finding 继续 advisory、zero-network、无自动修复。
7. **Context C2：** C1 只满足设计申请条件。没有 Pilot 010 控制包、模型运行授权或 treatment 采纳。
8. **Platform：** Claude 仍缺成功认证／模型路由；DeepSeek 只保留 rc.8 精确验证范围。发行与新 runtime matrix 另立 Workstream。
9. **Workspace maintenance：** Phase 0–2 已在 source；Phase 3 自动 worktree removal 与 Phase 4 scheduler unsupported。
10. **Unified Observatory Candidate：** W7.2.3 与 U2.2 联合页面已启动供维护者复验，包含单一连续侧栏、密集 Maintenance 队列和最终 Graph 交互／视觉修正；维护者接受后再冻结 exact-SHA Promotion Candidate，不切换 public template／managed tools／Release。完整英文模式仍未实现。
11. **W7.3 relation capture：** `5fee848` 的 Core/capture/authority evidence 保留，但维护者拒绝 Graph UX：独立系列卡片和图下 comparison card wall 不能替代图内关系，冲突线路不得重叠成共用脊柱。原 W7.3 任务按最新 Plan amendment 修正，未通过前不得中央集成。
12. **U2.3 shell closeout：** 已完成并本地集成；只读/zero-network/无全 worktree 重扫描边界保持。后续与 W7.3 合流后做最终整页体验和 Promotion，不单独继续 U2.3。

## 不得外推的边界

- Canonical source、runtime-verified scope 与 public release 是三种不同事实；main 上的实现不能写成 v0.2.0 已发布能力。
- W7B apply／undo 只在隔离 Git fixture 验证；真实 self-host 只有 read-only／dry-run，Graph 没有执行按钮，中央 Team 没有执行权。
- W7.1 只从有界 Git-common-private archive 恢复 relation 已引用的缺失 endpoint；archive 永不成为 active tip、apply/undo target、Review Ready 或实时执行面。
- linked worktree 不是 OS 沙箱；越界写入仍依赖 guard、工作目录纪律、Scope/finding 与人工审查。
- Team Mode 默认关闭；不得同步 Prompt、回答、transcript、源码正文、未 push diff 或成员凭据。Local-only 与 Unknown 必须保留。
- maintenance 不得凭目录名、年龄或“branch 已进 main”自动删除。没有 current closure／review／Validation evidence 时继续保护；worktree、local branch、remote branch 分别授权。
- Broker-only 统一路由不等于同用户进程秘密隔离；只有独立 OS 身份或等价边界下的外部 Broker 才能隔离 Provider Key。
- Authority projection、AI Q&A、briefing、roadmap、Graph 与 Observatory 都是派生视图，不能创建 State、ADR、批准或 Validation 事实。
- v0.2.0、ADR、Validation、Snapshot 与 Pilot 原始／冻结输入不得为统一品牌、修复行尾或收口文档而改写。

## Context-routing 冻结结论

- H1、H2、B 与 S 均未通过各自采纳门；发布 Skill 不强制 Context Manifest、Selected Evidence 或 Access Receipt。
- Pilot 007／008／009 已冻结，原始 R0 位于 `D:\coding warehouse\project-orrery-benchmark`。不得回写、重分类或复制进 Git。
- Pilot 009 的 S/P 写前 input 比为 `0.8274`，但 P/S 质量均为 2/3，S 不采纳。新工作必须使用新 Pilot ID、独立外部输出根与任务级 Oracle controls。
- JSONL 是完整事件流上的事后审计，不是实时权限阻断；Agent receipt 仍只是自述。精确读取证明继续要求受控代理／Harness 证据。

## 发布与兼容边界

- v0.2.0 release asset 继续使用 `project-orrery-v0.2.0.*`，checksum 为历史事实；首个新 Release 也必须遵守 ADR-0015 的稳定技术 ID 契约。
- Core／CLI／Observatory 尚未形成独立公开 wheel/release；Codex、Claude、DeepSeek、Harness JSON Adapter 均未独立发布。
- Codex verified evidence 只覆盖记录的 Windows／runtime／Adapter 0.1.0／Core 0.1.0／CLI 0.1.0 范围；DeepSeek 只覆盖记录的 rc.8／Windows／Adapter 0.1.0／Core 0.1.0／CLI 0.1.1 wheel／模型范围。
- v0.2.0 ZIP 在不同 OS 重建尚非 byte-for-byte 相同；不要宣称跨平台可重复打包已经解决。

## 未来交接（未启动）

- **S1 Orrery Conductor Skill：** 目标为独立仓库 `ItIsMixian/orrery-conductor`。尚无仓库、实现或 Release；后续必须另开 S1。正式开发使用独立任务＋worktree，subagent 只做当前任务内部的有界工作。
- **Brownfield Adoption：** 目前只有保守迁移契约，区分 `scaffold installed`、`authority migration pending` 与 `authority integrated`。尚无研究结论或 Implementation Plan；不得批量覆盖作者文档或补造历史理由。
- **R4/R5：** alias contract 与 optional default transition 未启动；`orrery` PyPI 名称存在第三方冲突，不能擅自创建同名 distribution/import。

## 安全接续顺序

1. 读取 `AGENTS.md`、`PROGRESS.md`、任务相关 State 与活动 Plan。
2. 新建任务或追加实质范围时，先提交 ADR／Design／Plan amendment／Pending Validation 的 exact authority baseline；任务消息只传 SHA／paths，Agent 确认 scope revision 后才写产品。
3. 先运行 `git status`、`git worktree list` 和目标命令的只读 inspect；Git-private 快照不能替代作者 State。
4. 功能任务使用独立 branch＋worktree；主 worktree 只做唯一整合。
5. Candidate 先完成 Fast／Checkpoint／本地门，再把 exact SHA 推到非 main ref；只有 Windows／Ubuntu required checks 都通过后才能推广同一 SHA。
6. 发布、真实 relation apply、删除、凭据迁移、远端设置和模型实验都需要维护者分别授权。

详细历史见 [DEVLOG](DEVLOG.md)，逐次证据见 [Validation](validation/README.md)，研究结论见 [Context-routing State](state/context-routing-research.md)。
