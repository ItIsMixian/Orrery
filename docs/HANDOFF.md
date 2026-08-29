# 跨会话交接

Updated: 2026-08-29

## 当前停止点

- 公开版本仍为 Orrery v0.2.0；tag 指向 `20fc95b`，ZIP／checksum 与历史 release manifest 不变。
- 当前 Canonical source 为 `origin/main@9ee831f0d6f64306fe821f8c70229df54648d3eb`，本地 main 与 origin/main 对齐。
- CI5 exact `9ee831f` 的 Fast 与 Promotion 已完成：Promotion run `33235992711` 为 25/25 jobs PASS，双平台 required checks 均通过，Windows／Ubuntu 各聚合 390 tests／27 logical shards；同一 SHA 已进入 main。
- 当前未发布组件为 Core 0.1.14、CLI 0.1.18、Observatory 0.1.9；四个 Adapter 均为 0.1.1 source，支持状态仍为 `experimental`／`unreleased`。
- W1–W7、Personal／Team Observatory、workspace maintenance、LAN discovery／manual Host switch、relation execution 和只读 Graph 已进入 Canonical source。默认 docsite、公开模板、release manifest 和 v0.2.0 用户能力没有因此切换。
- R3 已把当前展示面收口为 Orrery；`project-orrery` 继续作为稳定 Skill／package／CLI／schema／协议及历史资产标识。R4/R5 未启动。
- SC1 只负责把权威入口、State、Plan 状态和 CI5 hosted evidence 对齐；Git-private session 状态不升级为作者事实，物理 worktree／branch 删除不属于本次文档提交。

## 当前可继续的线路

1. **Collaboration self-host：** 对真实 self-host 仓库运行 relation／maintenance 的只读 inspect 与 dry-run，补齐旧 Workstream lifecycle／closure 证据。任何 apply、undo、remove-worktree 或成员本机动作仍逐次本机确认。
2. **Authority production consumer：** 单独评审 managed projection 的启用／回滚；之后再由维护者选择实际 SemVer／candidate manifest。两项不得在同一未经审阅的发布动作里一起关闭。
3. **Documentation D2：** 只有维护者批准后才实现 `docs audit` scanner／CLI；finding 继续 advisory、zero-network、无自动修复。
4. **Context C2：** C1 只满足设计申请条件。没有 Pilot 010 控制包、模型运行授权或 treatment 采纳。
5. **Platform：** Claude 仍缺成功认证／模型路由；DeepSeek 只保留 rc.8 精确验证范围。发行与新 runtime matrix 另立 Workstream。
6. **Workspace maintenance：** Phase 0–2 已在 source；Phase 3 自动 worktree removal 与 Phase 4 scheduler unsupported。

## 不得外推的边界

- Canonical source、runtime-verified scope 与 public release 是三种不同事实；main 上的实现不能写成 v0.2.0 已发布能力。
- W7B apply／undo 只在隔离 Git fixture 验证；真实 self-host 只有 read-only／dry-run，Graph 没有执行按钮，中央 Team 没有执行权。
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
2. 先运行 `git status`、`git worktree list` 和目标命令的只读 inspect；Git-private 快照不能替代作者 State。
3. 功能任务使用独立 branch＋worktree；主 worktree 只做唯一整合。
4. Candidate 先完成 Fast／Checkpoint／本地门，再把 exact SHA 推到非 main ref；只有 Windows／Ubuntu required checks 都通过后才能推广同一 SHA。
5. 发布、真实 relation apply、删除、凭据迁移、远端设置和模型实验都需要维护者分别授权。

详细历史见 [DEVLOG](DEVLOG.md)，逐次证据见 [Validation](validation/README.md)，研究结论见 [Context-routing State](state/context-routing-research.md)。
