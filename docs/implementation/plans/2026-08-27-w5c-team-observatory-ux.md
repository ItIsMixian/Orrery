# W5C Team Observatory 信息架构重构

Date: 2026-08-27
Status: Active Worktree Plan
Base: `6266a448a3c45345734478de9e26b7ab15ff52cd`
Governing decisions: [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)
Approved design: [Multi-worktree collaboration protocol](../../design/multi-worktree-collaboration-protocol.md)

## Design brief

- **Purpose:** 让第一次进入 Team Mode 的维护者在数秒内理解“现在发生了什么、是否需要处理、下一步做什么”，同时保留完整本机诊断。
- **Primary user:** 指挥一个或多个 Agent 的项目成员；不假设其理解 Coordinator、outbox、revision 或 TTL。
- **Tone:** 克制的运营指挥台；保留现有深色、高对比和硬分隔，不做营销式卡片墙。
- **Memorable idea:** 先给一句人话结论，再把协议字段逐层下沉。
- **Constraints:** 不修改 W5A Core 权限、revision、TTL、request receipt 或网络安全；不增加远程执行、LAN 控件或新依赖；桌面与 390px 移动端可用。

## Implementation

- [x] 顶部显示动态人话结论、团队人数、待处理请求和待同步项。
- [x] 把启动、共享、采集和同步组织为带上下文的建议操作。
- [x] 将 Member／Workstream 投影改成成员与任务语言，保留原始 ID 作为次级信息。
- [x] 请求区只突出待处理项，已处理请求进入折叠历史，并明确“确认不等于执行”。
- [x] Coordinator、Host、heartbeat、last-seen、revision 和测试请求下沉至本机控制与技术诊断。
- [x] 保留全部 POST、cookie、Host／Origin、body、secret 和 request-only 安全测试。
- [x] 运行 focused／adjacent 测试并完成桌面与移动端真实浏览器验收。

## State and evidence

- `docs/state/project-structure.md`
- `docs/state/documentation-system.md`
- `docs/state/release-and-toolchain.md`
- `docs/state/test-coverage.md`
- 新的 W5C Validation 与 DEVLOG 条目

本计划不修改根 `PROGRESS.md` 或 `HANDOFF.md`；它们只由后续唯一整合者更新。
