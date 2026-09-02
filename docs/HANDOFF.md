# 跨会话交接

Updated: 2026-09-01

## 当前停止点

- W7.4 corrected preview 已接受并冻结为 clean exact
  `fe75fc238ebf876d8565cabda0c8e0f8cfb4cfdd`：strict history 为 6 closed／31 retired，11 条 recovered
  archived lineage，full 25 nodes／18 routes／0 overlaps，compact 15／8／0 overlaps。它诚实保持
  `candidate-frozen / validation-pending`，尚未整合、闭合或获得 cleanup authority。
- U2.5 Phase A clean exact `6596a9f8e0e79cf0e5bc76b8ae46b0f323056040` 已获维护者继续授权。Phase B 现在可
  精确导入上述 W7.4 Candidate，保留其全部历史／关系／full-compact 语义并生成 self-host preview；预览接受前
  仍禁止 unittest/Fast/Checkpoint/Candidate/Promotion。
- W3.1 已登记于独立分支，首轮因两个 receipt schema 属于中央独占 `schema-migration` 而正确停在 clean L3。
  中央已按 scope revision 2 在 exact `c142f325d643827c47ce14fb7a489ea1ff39a295` 完成严格两-schema bootstrap；
  W3.1 可精确导入、刷新 scope 后继续，schema 字段变更仍必须返回唯一整合者。
- W6.2 自动清理仍未分发。W7.4 已形成 accepted frozen history/lineage Candidate，但其 validation/整合、真实
  `history_snapshot_ready` 消费和 W6.2 自身任务说明仍是独立门；本轮不得把 W3.1/U2.5 的继续授权扩成自动清理。
- W7.4 再次暂停等待 task-description revision 2：维护者拒绝新“完整历史目录”和 bulk card grid，并指出原
  Graph 关系仍未找回。中央盘点为 37 records／33 lineage／14 current／至少 11 个 archived-to-archived exact
  pair；新范围要求删除 bulk UI、从 archived lineage 恢复可验证关系并保留 Unknown。接受前不得运行测试。
- G1、旧 U2 与 U2.4 worktree 已先保全 branch/commit/session 后退出 registry；scope peer findings 为零。剩余
  L3 来自 stale `main@d07e1a...` baseline。task-description revision 3 显式绑定实际本地 integration ref；
  W7.4 必须导入该配置并取得 allowed refresh 后才能继续。
- integration-ref 修正后唯一剩余 L3 是 W7.4 未跟踪 history schema。中央已拒绝其“任意 object＋全部 closed”
  草稿，并以 revision 4 bootstrap strict schema；W7.4 必须删除任务草稿、合入中央 schema，再刷新守卫。
- 维护者已接受 W7.4 恢复后的完整关系图；revision 5 只增加同画布 `折叠历史` 模式。默认完整图冻结，精简
  模式保留当前/待确认/Unknown/冲突与一跳历史上下文，只折叠更深的有证据历史子图；W6.2继续等待。
- U2.4 exact `00b2eb4fa28a606cdb532c7938e46482950e8233` 已按维护者指令进入当前本地 integration branch：
  归档布局恢复、即时 starting page 和两个 Windows 启动入口均已合入。合流产品树与 exact Candidate 一致，
  只做 compile/JSON/parity/diff 轻量检查，没有重跑 unittest。protected main、Promotion 和发布未发生；
  历史任务完整投影由独立 W7.4 持有。
- Orrery v0.3.1 已公开发布为 Latest Release；protected `main`、annotated tag、Release source 均绑定 exact
  `1d9223cb07b94674b58471e0c19addf748b16221`。Promotion run `33465321477` 与 tag workflow
  `33465760947` 全绿，远端 ZIP/checksum 哈希与 exact-Git build 一致。
- v0.3.1 已关闭 Windows 默认 launcher 的 Git console child 闪窗与重复 supervisor 启动：installed-project
  smoke 为 HTTP 200、同 PID/port/instance reuse、stop 202，随后 marker/listener/process 全部归零。
- v0.3.0 tag 仍为 exact `a0a728b...`，历史 ZIP/checksum assets 未替换；其 Release 正文顶部已添加严重
  Windows warning 和 v0.3.1 链接。v0.2.0 历史标识同样未改。
- 当前 integration worktree 正在把 authority revision `1776629...` 与已发布 release ancestry `1d9223c...`
  合并为 docs closeout；产品、tag、Release assets 与版本均不再改变。
- protected `origin/main` 已包含 SC1 exact `a9369ddeee0e74d4ddbe4bfc23a86b510d400457`；SC1 的产品 source baseline 为 `9ee831f`，只修改权威文档。
- CI5 exact `9ee831f` 的 Fast 与 Promotion 已完成：Promotion run `33235992711` 为 25/25 jobs PASS，双平台 required checks 均通过，Windows／Ubuntu 各聚合 390 tests／27 logical shards；同一 SHA 已进入 main。
- 当前本地 integrated Candidate 的未发布组件为 Core 0.1.19、CLI 0.1.22、Observatory 0.1.19；Harness JSON 为 0.1.2，其余 Adapter 为 0.1.1，支持状态仍为 `experimental`／`unreleased`。
- W1–W7、Personal／Team Observatory、workspace maintenance、LAN discovery／manual Host switch、relation execution 和只读 Graph 已进入 Canonical source。默认 docsite、公开模板、release manifest 和 v0.2.0 用户能力没有因此切换。
- R3 已把当前展示面收口为 Orrery；`project-orrery` 继续作为稳定 Skill／package／CLI／schema／协议及历史资产标识。R4/R5 未启动。
- SC1 已把权威入口、State、Plan 状态和 CI5 hosted evidence 对齐；Fast `33256438925`、Promotion `33256558285` 与 main Fast `33256757429` 均通过。该 source commit 没有执行物理 cleanup，Git-private session 状态也不升级为作者事实。
- 后续本机维护已归档并移除六个 `closed/superseded` worktree，只删除工作目录并保留 branch／commit；当前七个 registered worktree 中包含一个并发创建、未触碰的 `github-front-door-redesign`。
- 维护者已接受 ADR-0016／Unified Observatory Design：目标是一个可见 launcher、URL 与导航壳，内部 helper 可受管独立运行；现有 docsite 阅读、搜索、AI、作者信息架构和可识别视觉体验必须继承，U1 prototype 不是最终 UI。
- `codex/u1-u2-integration-baseline` 已按 W7.2.3 `30d44ff` → U2.2 `70e6ac9` 合流，联合 feature merge `0eaad30` 是供维护者复验的本地 integrated Candidate。联合 Fast 38/38 与真实 1440/390px 浏览器验收通过；44 项 Checkpoint 在既有 Maintenance fixture 上达到固定 90 秒预算，未虚报通过。它尚不等于 `origin/main`、默认切换或公开发布。
- ADR-0017 与 Approved Relation Capture Design 已接受。早期 Graph `05c83b` 因默认 55%、共享总线、标签
  重叠和 inspector 挤压被拒绝并已由 pinned-ELK Candidate supersede；它不再是当前中央实现。
- ADR-0020 与 Program/Bundle Design 已接受：W 是 program、W5/W6/W7 是 phase，membership 不是 series 或
  semantic edge；同类同向且共端点的 relation 只能在同一 block pair 内受控束线。旧 scope revision 5/6
  已被 pinned-ELK实现/验收 supersede。
- W7.3 revisions 7–10 的全局 rank、hard/soft program grouping、手写 packing/routing/label 页面均已被拒绝。
  ADR-0022 选择 ELK layout-only；ADR-0023 又保留手写 geometry 为 frozen/manual/visibly-labelled legacy 后手，
  禁止自动回退。Orrery 继续拥有事实选择与现有 SVG/frontend。
- ADR-0018 authority-first 继续生效：维护者接受的 W7.3 ELK 产品方向已形成 clean Candidate 并完成中央
  routed evidence；旧 `5fee848`/`05c83b` 回执只保留历史 provenance。自动 receipt／first-write enforcement
  尚未实现；Phase 0 exact-SHA 全页已经维护者接受。
- S0 `orrery-dispatch` 初始 source Candidate `9294902` 只包含 `SKILL.md`／`agents/openai.yaml`；首次 unmapped-path refusal 经任务说明 amendment 收口为 generic `release-packaging` mapping，Fast 44/44 与本地门通过。公共 v0.2.0／v0.3.0 与未来 S1 Conductor 状态未改变。
- PO enforcement local integration `8b73f26` 后，更新的 S0 两文件已安装到当前本机 `C:\Users\1\.codex\skills\orrery-dispatch`，source/installed hashes 一致。它仍未发布，不改变 release manifest／v0.3.0／S1 Conductor。
- A4 Candidate 与中央 authority-first 曾同时使用 `ADR-0018`。PO1 enforcement 已本地集成；当前线保留 authority-first `ADR-0018`，A4 已规范化为 `ADR-0019`，duplicate-number gate 与链接门通过。
- A4/U2.3 已本地合流：LF canonical inventory hash 解决 Windows CRLF 漂移，Fast 84/84、Checkpoint 89/89、Unified/Personal 25/25、A4/Adapter/wheel 15/15 及 390×844 Browser 通过。页面 help x=0/width=390、横向溢出 0、唯一功能 Ask Docs、console 0 warning/error；未 Promotion／push／public switch／release。
- CI7 clean `111f4ab` 已完成 mapping/cost、组合 acceptance gates、surface-bound receipt、validation lease 和
  no-repeat/predictive refusal，不修改 15/90 预算或发布 Authority。历史 `290482f` Fast refusal／Checkpoint
  PASS 与中央旧 fingerprint Checkpoint failure 均保留；current fingerprint `0eea7f...` 在 `f41b659...` 上
  fresh Fast 3/3、Checkpoint 4/4 PASS，均 evidence-eligible、zero rerun。
- ADR-0021 已接受 REL3 六项选择并纳入最新 W7.3/CI7 scope：0.3.0 使用单一 self-contained ZIP，新项目
  Unified/Model 1/Rules 1，旧项目显式迁移，Codex final runtime blocker，byte-identical 默认门，main/tag/Release
  分权。Final RC 已在独立 Sol-medium worktree 注册；DSH/alias/scheduler 明确延期 0.3.1。
- W7.3 clean `44ea200` 已通过 focused closeout，中央 merge 为 `ae90974`；CI7 clean `111f4ab` 的中央合流为
  `079de74`。`f41b659` 的唯一正式 Fast/Checkpoint 保留，但 `807096d...` 实页在接受前暴露 lightweight
  Personal/Relation Inbox 锚点不兼容。revision 5 预览已恢复组合；同页的四个同端点 automatic Unknown
  lineage proposals 已由 revision 6 append-only supersession 收敛为一个。lineage 卡仍错误显示 Accept/gate，
  revision 7 已恢复 Core-only effective authority；维护者确认修复页，现在只允许冻结 source 和 fresh CI7
  route，不得手工重放 child suites。source `15f013b` 保持 421 final IDs；两次 dry-run 均在 test loading 前
  拒绝，revision 8 已补 precise mapping。真实窗口当前 25/31 + one Unknown；3/4 mapping-only 窗口被拒绝，
  revision 9 以 one focused owner 和 Brand tiering 收口到 20/30。Fast 20/20 PASS；Checkpoint 因 hardcoded
  portfolio list 29/30。修 list 后 Fast 41 拒绝，revision 10 撤回新增 examples/list；新窗口 20/30 中 Fast
  又因 setup+actual-path 为 10.300s 拒绝。revision 11 最终 `74afb989...` Fast 19/19、Checkpoint 30/30 PASS；
  `a2d7737...` final page 已接受，Phase 0 COMPLETE。

## 当前可继续的线路

- **当前并行控制：W3.1 + U2.5 Phase B。** 两者保留原独立 task series/worktree。W3.1 消费中央 receipt-schema
  bootstrap 后实现快速冻结/异步验证；U2.5 消费 accepted frozen W7.4 exact Candidate 后完成 Graph 动态接线。
  W7.4 validation、W7.5 分类和 W6.2 cleanup 仍是独立后续门，不得混入这两个任务。

1. **GX1 external graph Skill evaluation：** `f5fd5af` 已完成 8/12；维护者选择 assist／selective reimplementation，第三方 runtime／SVG／HTML 不进入产品。
2. **GX2 ELK layout evaluation：** 隔离视觉方向已获维护者接受并冻结 exact provenance；不再继续修改实验。
3. **S0 Orrery Dispatch Skill：** 两文件已在当前本机安装。后续只有独立 Release Plan 才能打包／发布它；不得把本机安装外推为其他用户可用，也不得扩成 S1 Conductor、自动 receipt 或首次写入阻断。
4. **PO1 decision allocation：** Skill PO 规则、duplicate-number gate、本机安装与 A4→ADR-0019 均已完成。
5. **Collaboration self-host：** 对真实 self-host 仓库运行 relation／maintenance 的只读 inspect 与 dry-run，补齐旧 Workstream lifecycle／closure 证据。任何 apply、undo、remove-worktree 或成员本机动作仍逐次本机确认。
6. **Authority production consumer：** 单独评审 managed projection 的启用／回滚；之后再由维护者选择实际 SemVer／candidate manifest。两项不得在同一未经审阅的发布动作里一起关闭。
7. **Documentation D2：** 只有维护者批准后才实现 `docs audit` scanner／CLI；finding 继续 advisory、zero-network、无自动修复。
8. **Context C2：** C1 只满足设计申请条件。没有 Pilot 010 控制包、模型运行授权或 treatment 采纳。
9. **Platform：** Claude 仍缺成功认证／模型路由；DeepSeek 只保留 rc.8 精确验证范围。发行与新 runtime matrix 另立 Workstream。
10. **Workspace maintenance：** Phase 0–2 已在 source；Phase 3 自动 worktree removal 与 Phase 4 scheduler unsupported。
11. **Unified Observatory Candidate：** A4/U2.3/W7.3 已在本地中央 source 组合为单一连续侧栏、规则帮助、轻量活动任务、关系待确认、密集 Maintenance 和最终 Graph；`a2d7737...` 的 1440/390 exact page 已接受。下一步由 Final RC 投影 public template／managed runtime 并验证 final archive，不直接切换 Release。完整英文模式仍未实现。
12. **W7.3 relation capture：** pinned ELK、shared projection、W phase small multiples、显式 legacy、clean
    `44ea200`、中央 merge `ae90974` 与 current routed Fast/Checkpoint 均已完成。W7.3 不再单独跑 feature
    suites；最终整页 gate 已由 v0.3.0 Phase 0 完成。
13. **U2.3 shell closeout：** 已完成、本地集成并进入 Phase 0 accepted page；只读/zero-network/无全 worktree 重扫描边界保持。后续只在 Final RC 做 public-template/final-archive runtime，不单独继续 U2.3。
14. **CI7 validation governance：** clean `111f4ab` 与 current fingerprint fresh Fast 3/3、Checkpoint 4/4
    已完成；旧 refusal/failure 不被覆盖。下一步不再重跑 Phase 0 formal stages，Promotion 留给 Final RC。
15. **v0.3.0 Final RC（历史已完成）：** `V0.3.0-final-rc` 已从 exact `88d80df...` 注册在独立 branch/worktree。revision 1
    只读返回 162-entry inventory（path-list SHA-256 `26d65705...`）并在零写入／零测试状态停下；中央 revision 2
    已授权并实现 CLI→Core 0.1.19 pin、自包含 offline scaffold runtime projection 与 canonical release notes。
    三个产品提交已选择性进入中央，中央 baseline 为 `ef145180...`；任务分支 75/81 CI7 dry-run 在加载测试前
    拒绝。Candidate preview 随后在 `0f82d565...` 选择 81 tests，acceptance/timing 均 allow，但任务误把固定
    dry-run non-evidence/reuse refusal 写成 run refusal。scope revision 5 只修 stale fixture-ID expectation；
    exact `ba230555...` 新 fingerprint Candidate 81/81、双根 package bytes 相同、external offline new-project
    portfolio PASS。scope revision 6 已授权 final runtime、exact non-main Promotion、同 SHA main 与 annotated
    tag；首个 runtime orchestration 在安装前因 `$home`/`$HOME` 变量冲突停止，用户状态未改变。scope revision
    7 corrected runtime 暴露 extracted asset/runtime root defect；scope revision 8 exact `e120aaa...` 已修复并
    完成 Candidate 36/36、双根 package、final ZIP Harness、真实 Codex、Unified、upgrade/migration/Skill lifecycle。
    Promotion run `33449930707` 在 lanes 前因 machine lane-list stdout 被 docsite 日志污染而失败关闭；run
    `33451288289` 完整执行但暴露 36 个集成漂移 ID；`33454661325` 将其缩到 5 个仍 non-green。scope revision
    18 exact `a0a728b...` 已完成 Candidate 56/56、双根 package、完整 final runtime 与 2-ID closure PASS；
    run `33456504779` 已双平台 PASS；同 SHA main/tag/GitHub Release 与远端资产验证随后完成。该线不再继续。

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

- v0.3.1 是当前 Latest Release；v0.3.0/v0.2.0 资产与 checksum 保持历史事实。所有后续 Release 继续遵守 ADR-0015 的稳定技术 ID 契约。
- Core／CLI／Observatory 尚未形成独立公开 wheel/release；Codex、Claude、DeepSeek、Harness JSON Adapter 均未独立发布。
- Codex verified evidence 只覆盖记录的 Windows／runtime／Adapter 0.1.0／Core 0.1.0／CLI 0.1.0 范围；DeepSeek 只覆盖记录的 rc.8／Windows／Adapter 0.1.0／Core 0.1.0／CLI 0.1.1 wheel／模型范围。
- v0.2.0 ZIP 在不同 OS 重建尚非 byte-for-byte 相同；不要宣称跨平台可重复打包已经解决。

## 未来交接（未启动）

- **S1 Orrery Conductor：** 独立 Phase A `4e44d27...` 的 inline MCP UI 已被维护者拒绝；ADR-0032/revision 2
  要求复用同一 fixture/server/UI，并以 Codex 既有 right Browser Panel 为主入口，inline 仅作回退。live binding
  等 accepted U2.5 exact envelope；新 toolbar icon、Codex patch、执行能力、remote repo 与 Release 均未授权。
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
