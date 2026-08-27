# Validation：W5C Team Observatory 信息架构

Date: 2026-08-27

Status: Worktree Candidate focused／adjacent／browser／structure PASS；未执行中央 Candidate 全仓门、远端 required checks、push、main merge 或 Release

Scope: `codex/w5c-team-observatory-ux`，base `6266a448a3c45345734478de9e26b7ab15ff52cd`。只重构 W5B Team 页面层级、文案和响应式布局；W5A Core／CLI、Team schema、权限、revision、TTL、request receipt、网络端点与 server 安全边界不变。Observatory Candidate 从 0.1.4 推进到 0.1.5，Core 0.1.9／CLI 0.1.13／Core API 1 不变。

## 人类信息架构

- 首屏先显示动态“现在的情况”，把 runtime、共享、成员、pending request、outbox 与 heartbeat 组合为一句人话结论和下一步说明。
- 主操作只保留启动本机服务、开始／暂停项目状态共享、采集本机状态与立即同步；按钮随真实状态改名并显示待同步数量。
- 主区域改为“成员与工作任务”，成员名与任务状态优先；Host、内部 ID、revision、Local-only 等机器字段降为次级说明或技术诊断。
- 请求区只突出等待本机确认的请求；已接受／拒绝请求进入默认折叠历史，并持续显示“确认只记录决定，不会自动执行”。
- Coordinator、Host、heartbeat、last-seen、outbox、创建测试请求、暂停连接与退出 Team Mode 进入“本机控制与技术诊断”。
- 若 `runtime_status=team-runtime-active` 但当前页面不拥有 server object，页面显示“其他本机协作服务登记”，禁用重复启动，并提供不绕过 Core ownership 的恢复说明；操作失败使用本地化、脱敏且具上下文的提示。

## Automated evidence

W5C static page contract：

```text
python -X utf8 -m unittest -v tests.test_team_observatory.TeamObservatoryTests.test_team_page_is_a_sibling_with_graphical_zero_network_onboarding
```

Result: 1/1 PASS。

W5A／W5C／component adjacent checkpoint：

```text
python -X utf8 -m unittest -v tests.test_team_observatory tests.test_collaboration_team tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection
```

Result: 最终 17/17 PASS，111.523s。覆盖 root-only、loopback、Host／Origin／cookie、body gate、secret redaction、enable/start/stop/disable、sharing/heartbeat、capture/sync、request-only receipt、capability、revision、TTL、zero-network default、特殊 runtime registration 文案与组件投影。中央 Candidate 的全仓门由后续唯一整合者执行。

Worktree checkpoint：

- integrated structure：PASS；Authority status `integrated candidate`，Authority Model 1 strict evaluation eligible；
- 隔离静态站：1,594 KB，123 docs，18 plans；
- Markdown：345 files／892 local links；只有 D1 冻结 positive fixture 的 1 个预期 missing target；
- `git diff --check`：PASS；只有三个既有 JSON／TOML 工作副本的 LF→CRLF 提示，没有 whitespace error；
- 根 `PROGRESS.md`／`HANDOFF.md`、默认 docsite、Skill template、managed-tool inventory、Core／CLI 与 server route 均未改动。

## Browser evidence

Browser: Codex in-app Chromium；只访问 W5C root-only loopback server。没有 DNS、公网或第三方请求。

验证路径：

1. Personal zero-network → 在本机启用 Team Mode → 启动本机协作服务；首屏从“尚未启动”切换为“本机状态已经准备好，目前还没有其他成员接入”。
2. 项目状态共享、采集与同步按钮显示真实 outbox 数量；heartbeat 关闭时解释 `Stale／Unknown` 是预期结果，不渲染成故障。
3. 创建两个本机测试请求，分别接受／拒绝；pending 数量回到 0，6 条历史记录进入默认折叠区，receipt 仍为 zero execution。
4. 初次桌面检查发现 Host 值在窄主栏中竖排；W5C 随后把 Host 完全下沉到技术诊断，并把 Local-only／revision 合并为任务次级说明，复验通过。
5. 真实非正常退出留下 stale runtime registration 时，页面不再把它称为“尚未启动”，而是显示其他本机服务登记并禁用重复 start；没有增加强制 kill、PID 控制或远程停机能力。

Viewport：

| Viewport | Result |
|---|---|
| Desktop 1280px | document `scrollWidth=1265 < 1280`；Team shell 约 699px；人话摘要、四项建议操作、成员任务、折叠请求历史和诊断入口可扫描；无横向溢出。 |
| Mobile 390×844 | document/body `scrollWidth=375 < 390`；Team shell 约 347px；状态信号两列、操作两列、任务单列，诊断入口保留；无横向溢出。 |

## Remaining boundaries

- W5C 不增加自动发现、真实其他设备、真实 LAN、云 relay、Host 迁移／选主、多设备、远程 shell／Agent／merge／delete 或自动请求执行。
- 启动页面在本机 37+ worktree 环境仍需约 2 分钟，因为 Personal/W3 projection 启动时逐项采集；本轮未引入缓存或渐进加载，后续应作为独立性能设计处理。
- 非正常终止 UI 进程可能留下 runtime registration；W5C 只提供可理解的检测与恢复说明，不绕过 Core-owned server object 或偷偷删除登记。
- 页面仍是 self-host root-only Candidate，不进入默认 docsite、发布模板、managed-tool 白名单或公开 v0.2.0。
