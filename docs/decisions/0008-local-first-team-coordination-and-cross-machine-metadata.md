# ADR-0008: Local-first Team Mode 与跨机器元数据可见性

Status: Accepted

Date: 2026-08-20

Origin: integrated from provisional decision `PO-DEC-WT-002`, approved by the maintainer on 2026-08-20

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md), especially Decision 11 and its cross-machine observability consequences

> 本 ADR 在独立 integration worktree 中基于最新 integration history 获得正式编号。原临时 ID 只保留为来源记录，不再作为有效决策标识。

## Context

ADR-0007 正确规定：另一台机器上未 push 的工作不能由 Git、PR 或 CI 自动发现，不能被表述为已验证的全局事实。后续产品讨论又确认了一个更窄、显式 opt-in 的 Team Mode：成员本机 Orrery Node 可以主动发送不含源码正文和完整对话的结构化状态元数据，使在线团队能够看到 `Local-only` 路径／模块、dirty 摘要、验证和冲突候选。

这种成员主动披露的 telemetry 不是 Git 代码证据，也不能证明未 push 内容的语义；但它确实成为 ADR-0007 原先没有允许的跨机器协调输入。因此不能只在 Design 中静默扩展，必须显式修订可见性、权限和默认部署边界。

## Decision

1. Project Orrery 默认使用单成员多 Agent 的 Personal Mode。默认不启动网络监听、局域网发现、成员认证、Coordinator、状态同步或 heartbeat；Team Mode 必须按项目由本地用户明确开启。
2. Team Mode 允许成员本地 Node 主动发送版本化、带来源的最小状态 envelope，包括成员／Host／Workstream／session 标识、branch／HEAD、Scope／subsystem、dirty／路径摘要、Validation、finding、revision 和 last-seen。
3. Team Mode 不同步完整 Prompt、回答、推理、conversation transcript、源码正文、未 push diff 或成员机器执行凭据。已经 push 的源码继续由 Git 托管权限控制，不复制到 Orrery 协调存储。
4. 对 ADR-0007 Decision 11 作窄修订：已经 push 的 Git／PR／CI 仍是跨机器代码与集成证据；成员主动上报的未 push 元数据可以作为 `Local-only` 协调输入，但必须标注为 member-local telemetry。未上报的工作以及缺少正文／依赖证据的语义关系仍为 Unknown。
5. “中央”是只读逻辑 Coordinator。首版由一个在线成员设备临时承载，局域网 Host／发现／加入内置且零云依赖；跨成员动作只能形成请求，实际执行必须由目标成员本地确认。
6. 局域网发现只公布最小 endpoint／project fingerprint，加入要求已验证项目成员身份和 Host 确认。异地 relay、常驻云 Coordinator 和多设备切换不属于首版默认体验。
7. 状态同步默认事件驱动并合并短时重复事件；应用层 heartbeat 默认关闭并由成员选择是否启用。突然断线或旧 telemetry 必须显示 Stale／Unknown。
8. 所有已验证项目成员都可查看 Team Mode 的全员状态。权限采用 Member 基础身份与 Reviewer／Integrator／Admin 可叠加 capability；任何 capability 都不授予中央远程执行权，Agent 本身不能持有治理 capability。
9. 人类审查按风险分级。AI 只生成无权威摘要；Direct／L3 不可豁免；跨成员 L2、共享 Authority／接口和高风险候选按 Design 要求独立人类确认／审查。

## Reasons

- Personal Mode 保持个人开发者的默认体验轻量，不为少数团队场景强制引入网络、成员或部署成本。
- 主动上报最小元数据可以在不上传源码正文的前提下发现路径／Authority 重叠，并诚实保留 Semantic Unknown。
- 临时本地 Host 满足局域网小团队，不把云服务器变成基本依赖。
- 中央只读和本机确认延续 ADR-0007 的隔离原则，避免状态可见性被误解为设备控制权。
- 通过正式 amendment 保持 ADR 与 Approved Design 一致，避免新体验暗中改变既有事实边界。

## Consequences

- Team Mode 需要独立的版本化 envelope、成员／Host 身份、revision、可见性标签和安全加入协议。
- `Local-only` 只表示某成员 Node 上报了元数据；它不等于代码已 push、中央已读取源码或 Harness 已独立验证语义。
- 未开启 Team Mode、关闭分享、成员离线或未上报的工作继续显示 Unknown／Unavailable。
- 中央视图可以比较路径、模块、Authority 和已声明验证面，但缺少必要证据时不得生成绿色 Semantic 结论。
- Team Mode 的实现与发布必须作为 Personal Mode 之后的可选扩展验证，不能使默认安装开始监听网络。

## Implementation and validation mapping

- Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)
- Implementation Plan: [2026-08-19 多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)
- State after implementation: `docs/state/project-structure.md`, `docs/state/documentation-system.md`, `docs/state/release-and-toolchain.md`, `docs/state/test-coverage.md`
- Validation: Personal Mode zero-network default; opt-in LAN Host/discovery/join; metadata-only envelopes; Local-only／Unknown projection; local confirmation; capability revocation; event-driven sync and stale handling
