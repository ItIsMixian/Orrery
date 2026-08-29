# ADR-0016: Unified Observatory Shell 与单一本地入口

Status: Accepted

Date: 2026-08-29

Maintainer acceptance: **accepted on 2026-08-29** for the Unified Shell architecture and the production docsite
inheritance boundary recorded below.

Amends: [ADR-0001](0001-project-orrery-self-hosting.md),
[ADR-0004](0004-platform-neutral-core-and-adapter-boundaries.md),
[ADR-0006](0006-broker-only-docsite-provider-gateway.md),
[ADR-0008](0008-local-first-team-coordination-and-cross-machine-metadata.md)

Preserves: [ADR-0009](0009-authority-meta-model-and-semantic-conformance.md),
[ADR-0014](0014-dynamic-workstream-succession-contract.md)

> Accepted 只约束后续设计与实现，不证明统一 Observatory 已经 implemented、validated、默认启用或发布。
> 当前 `start-docsite.bat`、`serve.py`、Team server、managed tools、公开 v0.2.0 与生产开关保持不变。

## Context

Canonical source 目前有一个默认动态 docsite、一个 root-only Team server，以及 Authority、Personal、
Maintenance、Workstream Graph 的多个 default-off builder／injector。它们共享部分 HTML，却没有一个正式
shell／consumer registration／visible-front-door／supervised-lifecycle contract：导航依赖字符串 marker 注入，
Team 与 docsite 分别拥有 HTTP server、安全 token 和 route namespace，Team UI 还可拥有 Coordinator
listener；managed Broker 也会额外绑定环回端口。

用户已经接受最终产品方向：Orrery 只有一个用户可见的本地启动入口、一个 Observatory UI/control URL 和
一个导航壳，默认不显示命令行窗口；显式 debug 模式最多显示一个控制台。在该壳中组合文档／搜索／AI、
Authority、Personal、Team、Workstream Graph 和 Workspace Maintenance，同时保持静态纯只读、动态
capability gating、Team 显式 opt-in、中央 request-only、derived view 无决策权和默认零网络。内部进程与
listener 拓扑是另一维度，可以按隔离需要存在，但不得变成第二个用户入口或第二个浏览器页面。

统一入口不等于重做文档产品。当前 production docsite 的文档阅读、搜索、AI 问答、作者文档信息架构和可识别
视觉体验是后续生产实现的继承基线。U1 的 synthetic prototype 只研究架构边界与交互编排，不是最终 UI 规范，
也不是全面视觉重设计提案。

这不是普通导航重排。它改变默认运行入口、HTTP ownership、managed Broker 的默认拓扑、root-only
consumer 装配和后续 public-template 边界，因此必须经过正式决策；只修改 README、builder 或启动脚本不足以
约束跨模块安全与回滚。

## Proposed decision

1. Orrery 采用一个版本化 **Unified Observatory Shell**。Shell 拥有唯一人类导航 identity、单一用户可见的
   `127.0.0.1` UI/control URL、公共安全 middleware、capability discovery、统一 supervisor lifecycle 和错误
   隔离；consumer 不再各自打开 sibling UI 页面或通过 HTML marker 竞争导航。
2. 默认 Windows 体验最终由一个可见的 **Start Orrery** 入口启动，并只打开一次浏览器；默认不显示命令行
   窗口。实现可以使用隐藏 supervisor／helper 进程。显式 debug launcher 或 `--console` 最多打开一个可见
   控制台。运行日志写入本机 Git-private／runtime log，并可从统一壳的诊断页面打开；不得写入作者事实或发布包。
   最终文件名与兼容方案由后续 Design review 决定。U1 首轮不修改任何真实启动脚本。
3. 静态模式继续是无服务、无 cookie、无动态控制的单文件只读读者。动态模式只向用户暴露一个 loopback
   UI/control URL；缺失、disabled、Unknown 或失败的 capability 显示 Unavailable，不从其他事实推断。
4. Personal Mode 仍是默认且 zero-network。Team Mode 仍按项目显式开启；中央页面只读／request-only，执行
   仍由成员本机确认。统一页面、共享 cookie 或共享 URL不得扩大 Team、Maintenance、Authority、Graph 或 AI
   的权限。
5. 默认 managed Broker 保留 ADR-0006 的 broker-only、凭据绑定、缓存、single-flight、模型白名单和预算门。
   Broker 可以实现为同进程 adapter，也可以实现为由 supervisor 启停的隐藏 helper／loopback endpoint；这是
   后续实现选择，不是本 proposal 的单进程决定。任何选择都必须通过行为 parity、凭据／endpoint 安全、认证、
   崩溃回收和无孤儿进程／端口验证。外部隔离 Broker 仍可作为显式依赖，且不拥有 Orrery UI URL。
6. Team 的用户可见 UI／control route 必须进入同一 Observatory URL。显式 Team Mode 所需的 Coordinator、LAN
   transport 或 discovery listener 可以作为受 supervisor 管理的内部 capability 存在；必须单独声明安全边界、
   保持 Team opt-in，并且不得打开第二个浏览器页面、要求用户分别启动或把 LAN transport 写成默认联网。
7. Core／CLI／Observatory／Adapter 边界保持 ADR-0004：Core 拥有确定性语义与 versioned contracts，
   Observatory consumer 只投影，shell 只编排。consumer registration 不允许复制 Authority、Maintenance、
   Team 或 Workstream relation 规则。
8. Authority 页面只消费 A3 或其后续被接受的 managed-consumer contract。Shell 不选择模型、不把 Candidate
   projection 升为 enabled、不把 AI／Coordinator 输入当成 Authority，也不允许 partial Authority render。
9. Maintenance 页面只消费 W6.1 或其后续 versioned cache／Quick Remove contract。Shell 不复制 eligibility、
   cache invalidation 或 remove-worktree preflight；所有 destructive action 继续绑定 action-specific 本机确认并
   在执行前重新验证。
10. Shell、API、consumer registration 和 navigation identity 独立版本化。用户可见 UI/control URL 与内部
    进程／listener topology 分开建模。可选 consumer/helper 的失败只隔离该 capability；shell、文档和其他
    consumer 继续可用。route collision、unsafe capability escalation 或 shell 自身完整性失败则启动失败关闭。
    正常关闭、崩溃恢复和启动失败都由 supervisor 统一收口，不得残留 helper 进程、端口或误导性 ready 状态。
11. 统一 shell 是派生／控制入口，不是第二套项目事实。AI、telemetry、cache、Team envelope、maintenance
    receipt、Authority projection 和 Workstream Graph 均保留自身 source／scope／Unknown，并不得写作者
    State、ADR、批准或 Validation。
12. public template、managed-tool inventory、installer、release manifest、v0.2.0 和真实默认开关不由本 proposal
    自动改变。后续进入公共默认前必须有 Approved Design、独立实现、版本／迁移／回滚证据、exact-SHA 双平台
    required checks 和单独的发布选择。
13. 生产实现必须优先复用或适配现有 `build_docsite.py`／`serve.py` consumer，不从零重写文档站。允许的内部
    重构只限统一 front door、consumer registration、supervision、public routes、安全 middleware 与 lifecycle；
    文档阅读、搜索、AI 问答、作者文档信息架构和可识别视觉体验继续作为继承基线。synthetic prototype 不得被
    当作最终 docsite UI 规范，也不得借 U1 默认推进全面视觉重设计。任何全面视觉重设计必须另立任务并单独取得
    维护者批准。

## Reasons

- 单一可见前门消除用户需要理解多个端口、窗口、导航和启动顺序的负担，同时不牺牲必要的内部隔离。
- 显式 consumer contract 让 W6.1、A3、Team 与 Graph 继续拥有各自语义，shell 只组合 readiness 与页面。
- 静态／动态共用 navigation identity，使离线读者不会被迫运行控制服务，同时动态 capability 可诚实降级。
- 允许 Broker／Team transport 采用经过验证的内部拓扑，使实现可以在部署简单性与凭据／故障隔离之间取舍。
- 默认零控制台、显式单控制台 debug 与统一 runtime log，兼顾普通启动体验和可诊断性。
- 继承现有 docsite consumer 与可识别体验，降低重写风险并保持文档工作流连续性。
- per-consumer quarantine 和全壳 legacy rollback 使迁移可以分阶段，不把多个高风险开关绑定到一次发布。

## Consequences

- 当前 `serve.py`、`serve_team_observatory.py` 和 root-only builders 需要后续重构为一个可见 front door、明确
  consumer registry、supervisor lifecycle 与公共 security middleware；U1 不决定必须合并为单进程。
- managed Broker 的 in-process 与 supervised-helper 方案都必须证明 cache／budget／endpoint／credential
  parity、安全边界、诊断与关闭行为；本 proposal 不预选其内部拓扑。
- Team Coordinator 的 UI route 必须由统一 front door 呈现；其 transport/listener 可以保留为受管内部能力，
  但缺少安全、opt-in 或 lifecycle contract 时 Team capability 必须保持 Unavailable。
- 后续 Windows 实现需要选择无控制台默认 launcher、单控制台 debug 入口、Git-private runtime log 位置和安全
  的“打开诊断日志”交互，并验证崩溃后没有遗留 helper。
- 后续实现以 adapter/front-door integration 连接现有 `build_docsite.py`／`serve.py` consumer；除统一入口必需的
  registration、route/security 与 lifecycle 改造外，不获得重写 docsite 或全面改变其信息架构／视觉体验的授权。
- consumer 与 shell 需要兼容矩阵和 contract tests；导航 marker 注入最终要迁移为显式 registration。
- 在后续生产实现通过独立验收与默认切换前，现有 default docsite 与各 root-only sibling entry 保持不变；
  synthetic prototype 可直接删除，不产生迁移或作者事实回滚。

## Mapping

- Approved Design: [Unified Observatory Architecture & Shell](../design/unified-observatory-architecture-and-shell.md)
- Implementation Plan: [U1 Unified Observatory Architecture](../implementation/plans/2026-08-29-u1-unified-observatory-architecture.md)
- Validation: [U1 architecture and prototype](../validation/2026-08-29-u1-unified-observatory-architecture.md)
- Non-authoritative prototype: `experiments/unified-observatory-shell/`
