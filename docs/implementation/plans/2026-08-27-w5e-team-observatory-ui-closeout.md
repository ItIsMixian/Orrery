# W5E Team Observatory UI 收口

Date: 2026-08-27
Status: Active Worktree Plan
Base: `CI1-tiered-parallel-validation@67a2fe90f26ff5ded839c4d60fea23dfcd36ba13`
Governing decisions: [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)
Approved design: [Multi-worktree collaboration protocol](../../design/multi-worktree-collaboration-protocol.md)

## Design brief

- **Purpose:** 让维护者进入 Team Observatory 后先看到少量关键状态和三个持续可见的本机边界控制，不再重复阅读一段“现在的情况”。
- **Primary user:** 通过一个或多个 Agent 推进项目、但不需要理解 Coordinator／revision／TTL 内部字段的维护者。
- **Tone:** 克制、清晰的运营指挥台；沿用现有深色硬分隔系统，不新增营销式 badge 或重复摘要。
- **Memorable idea:** 四个关键状态紧贴页面标题，Team Mode／团队连接／在线状态始终可见；低频诊断通过一个小齿轮进入次级弹窗。
- **Constraints:** 不修改 Core Team 权限、discovery／join、revision、TTL、request receipt、Host／Origin／cookie／body 安全边界；不新增远程执行、任意命令／路径／URL 或依赖；桌面与 390px 移动端可用。

## Implementation

- [x] 删除标题右侧重复的共享边界 pill 和“现在的情况”摘要区。
- [x] 将团队连接、可见成员、待处理请求、待同步四个状态上移至标题后的首个扫描区。
- [x] 在非折叠区域持续显示 Team Mode、团队连接和在线状态控制，并保留显式退出 Team Mode。
- [x] 将 Host、内部 ID、revision、last-seen、测试请求、维护请求和隐私说明放入由小图标打开的本机设置／诊断弹窗。
- [x] 保留 discovery、sharing、capture、sync 的工作流语义和全部 Core／server 安全边界。
- [x] 把组合式接口与 Brownfield Migration 记录提交吸收到当前完整 Candidate，不升级为 ADR 或已实现能力。
- [x] 更新 Observatory Candidate 版本、专项测试、State、Validation 与 DEVLOG。
- [x] 完成 focused／adjacent／CI contract／结构／链接／diff，以及桌面与 390px 真实浏览器验收。

## State and evidence

- `docs/state/project-structure.md`
- `docs/state/documentation-system.md`
- `docs/state/release-and-toolchain.md`
- `docs/state/test-coverage.md`
- `docs/validation/2026-08-27-w5e-team-observatory-ui-closeout.md`
- `docs/DEVLOG.md`

本计划属于 W5E Candidate。它不证明 `main`、公开 v0.2.0、真实双机 LAN 或新接口已经发布。
