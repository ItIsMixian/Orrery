# 实施计划：W5D 局域网协作闭环与验收 Harness

Status: Completed; implementation is contained in Canonical W7/CI5 descendants

Date: 2026-08-27

Fact scope: Candidate `codex/w5d-lan-collaboration-harness@db78a7f`

Governing decisions:

- [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)
- [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../../design/multi-worktree-collaboration-protocol.md)

Parent Plan: [多 worktree 协作协议](2026-08-19-multi-worktree-collaboration-protocol.md)

## 目标与边界

本 Workstream 在真实双机验收前，完成可由单机和 CI 可靠复验的 LAN discovery、完整 join、单 active Host／手工切换、事件驱动重连与双成员隔离 Harness。默认 Personal Mode 必须继续 zero-network；Team enable 只准备本地状态，discovery 与 Host 启动各自需要本机显式动作并可完全停止。

冻结 W5D checkpoint 前同时修正 stacked Workstream lineage：显式记录父 Workstream 与创建任务时的精确父 HEAD，以该 task base 计算后继 committed delta，并只从父子／祖先链 overlap 中排除已被精确 base 包含的继承变化。缺少 lineage 的历史 session 保持 Legacy／Unknown；不得按 branch 名猜测关系，也不得把继承路径伪装成“已解决冲突”。

只传输版本化最小元数据。发现提示不授予成员资格；中央与其他成员只读／request-only，所有执行继续要求目标成员本机确认。若实现需要自动选主、云 relay、远程执行、源码／diff／对话同步或改变 W6 maintenance executor 的 process-use 语义，本 Workstream 停止并请求维护者决定。

## 实施阶段

1. **协议与安全原语**：冻结 discovery／invite／join／Host epoch schema；实现最小发现包、project fingerprint、短期 nonce、一次性挑战、Host-local Admin 确认、成员 credential epoch，以及 spoof／replay／跨项目／过期／未确认失败关闭。
2. **受控 transport 与 Host 生命周期**：实现默认关闭、可注入的 discovery transport；提供 loopback／受控虚拟 transport、单 active Host、手工 switch、旧 Host 拒绝新 revision、单调 revision 聚合、断线本地无影响和 TTL Stale／Unknown。
3. **Observatory 控制面**：在人类可读 Team 页面增加发现状态、候选 Host、join 确认、连接／重连和手工 Host switch；保留 root-only 本机控制、固定动作、request-only 与本机确认边界。
4. **隔离 Harness 与 runner**：用两个独立临时 clone／identity／credential／runtime 模拟两台设备，覆盖发现、加入、同步、断线、TTL、重连、Host switch、request-only 与 capability revoke；runner 使用固定参数、零真实凭据、临时目录和 loopback／受控 transport，输出脱敏 manifest、阶段结果、校验和与 machine-readable verdict。
5. **验收说明与权威同步**：补未来真实双机 preflight／runbook；原始运行只写仓库外临时根，仓库只保留 fixture／validator、提炼 Validation、受影响 subsystem State 与 DEVLOG，不改根 PROGRESS／HANDOFF。
6. **Stacked lineage 契约与作用域**：为 session／Scope Observation 增加版本化 `base_workstream_id`＋`task_base_oid` 绑定；创建时验证 OID 存在且是当前 HEAD 祖先；lineage current 时从 `task_base_oid..HEAD` 计算 committed delta，staged／unstaged／untracked／expected 保持当前任务来源，缺失输入标为 Legacy／Unknown。
7. **Lineage-aware overlap 与 Personal 投影**：只在显式、当前、可追溯的祖先链上折叠 inherited committed provenance；父任务在 child fork 后对同一路径的新提交继续形成 finding，siblings／legacy 正常比较。Personal Observatory 显示 chain、base OID 和 unique current finding 数，不生成继承型 resolved finding，不改变 L2/L3、exclusive resource、acknowledgement 或 Review Ready 门。
8. **Synthetic chain 回归**：构造 W5C(base) → W6(stacked) → W5D(stacked)，记录修正前后 fixture 计数；覆盖纯继承 0 Direct／Authority blocker、child 新增、parent fork 后同路径变化、非法／不存在／非祖先 base，以及 lineage 输入漂移失效。

## 验证策略

- Fast：协议／schema、发现泄漏门、join 失败路径、revision／TTL／Host switch、Personal zero-network 和定向 UI 测试。
- Lineage Fast：session／Scope schema、task-base ancestor gate、committed delta、祖先／后继与 sibling 对照、post-fork parent 变化、legacy／drift Unknown、L2/L3／exclusive／ack／Review Ready 不回退。
- Checkpoint：双成员隔离 runner、Windows 路径与 POSIX／Ubuntu 兼容路径、结构验证、隔离静态站、Markdown 链接、安全扫描和 `git diff --check`。
- 浏览器：真实 in-app Chromium 点击桌面与 390px 移动端的 discovery、候选选择、join 确认、连接／重连和 Host switch 状态。
- Candidate／Promotion：留给整合者在冻结 exact SHA 上运行默认／动态全仓与 Windows／Ubuntu required checks；本分支不 push、不更新 main、不创建 tag 或 Release。

网络测试不得访问公网或 DNS；只能绑定 loopback 或使用可注入受控 transport。Validation 必须明确本轮没有真实双机／真实 LAN 证据。
