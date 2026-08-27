# Validation：W4 health semantics / W5B Team Observatory

Date: 2026-08-27

Status: Candidate focused + adjacent checkpoint + browser PASS；未运行默认／动态全仓、远端 required checks 或 Promotion

Scope: `codex/w4-health-w5-ui`，base `31f04ff33592f71343983572ccbd16292c0d5920`。Phase A implementation `a900087`；Phase B implementation `b31e1d1`。本记录只证明当前 Candidate 的本机 Windows 行为，不证明 Canonical integration、公开 Release、真实多机／LAN 或云 relay。

## W4 health 修复

- Personal projection 保持 `derived-read-only`：W1–W3 finding、review、inventory、cleanup 与 closure 结论不被重判或改写。
- Delivery now 只包含具有 current session/evidence、lifecycle 为 active／review-pending 的 Workstream。只有 finding 双方都属于该集合的 Direct 才计入 current blocker。
- Reconciliation 单列 stale session、历史／stale-source finding、过期 review package 与当前未登记 Candidate；旧 W3/W4 session 显示 `needs closure / reconcile`。
- Workspace hygiene 单列 legacy-unmanaged、no-session、retained、Unknown 与 estimated reclaim；这些不计当前 Direct blocker。Unknown 按 delivery／reconciliation／hygiene 完整记账。
- Primary worktree 固定显示 `Protected canonical root`，不作为普通 Agent Workstream。当前 Candidate 无 session 时明确显示“未登记／无法判断交付资格”，不伪造 Review Ready。
- 第一屏固定为“交付状态／当前阻断／需要对账／工作区卫生”，Git OID、W3 slots、七类 inventory、cleanup action 与 receipt 继续下沉技术证据。

合成 fixture 使用 36-worktree-like 主比例（4 registered-active + 1 review-pending + 31 legacy-unmanaged），并加入 stale source sessions、37 个历史 Direct、1 个 current Direct、32 个 absent-session Unknown、Primary root、未登记 Candidate 与 retained evidence。断言 current blocker 为 1、历史 Direct 全部进入 reconciliation、Unknown 全部保留、legacy/no-session/retained/reclaim 与 current blocker 分离。fixture 不包含真实本机路径或真实快照。

## W5B 实现与安全边界

- `team_observatory.py` 在同一 Observatory 增加独立 Team sibling page；Team disabled 显示 Personal zero-network 的图形化 onboarding，并把 enable 与 start 分成两个动作。
- 页面只消费 Core `team-read-only-projection` 和 Git-private Team config；Member → Workstream、revision、TTL、presence、permission 与 request receipt 规则继续由 W5A Core 持有。
- 新 `serve_team_observatory.py` 是 root-only 动态入口，不改变默认 `build_docsite.py`／`serve.py`、managed-tool inventory、Skill template、installer、release manifest 或公开 v0.2.0。
- UI server 固定 `127.0.0.1`；LAN bind 不在页面首屏或 API。所有状态改变使用 POST，并要求合法 Host、精确 Origin、每次启动随机 HttpOnly／SameSite control cookie、16 KiB body 上限与 exact-field 校验。错误只返回类别，不回显异常路径或 private Team 内容。
- 页面／JSON 不返回 member credential token、Coordinator runtime control、API key 或 credential 字段；没有任意命令、路径、URL、shell 参数、源码正文、Prompt／回答／reasoning／transcript 或未 push diff 输入。
- Coordinator 只能由拥有其 server object 的 UI 进程 start／stop；正常关闭 UI 时 Core `stop_owned_coordinator_server` 停止 owned Coordinator、删除 runtime registration 并保留 Team config／本地事实。
- request create 只形成中央请求；accept／reject 先写本机 receipt，再更新 request 状态，始终 `execution_performed=false`。UI 没有 shell／Agent／merge／delete 实现。
- Team page 直接显示 Online／Offline／Stale-Unknown／Unknown／Unavailable；最后快照遵守 Core TTL，不自行判断实时在线。显示的 lifecycle 直接来自 Core projection，不把 Agent 自报映射成 Review Ready／Integrated。

## Automated evidence

Phase A focused + component checkpoint：

```text
python -X utf8 -m unittest tests.test_personal_observatory tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection -v
```

Result: 14/14 PASS，64.556s。

W5A/W5B focused：

```text
python -X utf8 -m unittest tests.test_team_observatory tests.test_collaboration_team -v
```

Result: 16/16 PASS，72.398s。后续扩大 HTTP body/security 断言后，`tests.test_team_observatory` 单独最终为 3/3 PASS，23.830s。

Frozen adjacent checkpoint：

```text
python -X utf8 -m unittest -v tests.test_team_observatory tests.test_collaboration_team tests.test_personal_observatory tests.test_collaboration_contract.CollaborationContractTests.test_personal_default_and_team_contract_never_start_network_runtime tests.test_collaboration_w3.CollaborationW3Tests.test_risk_policy_human_actions_and_ai_only_do_not_satisfy_review tests.test_collaboration_w3.CollaborationW3Tests.test_inventory_is_bounded_and_legacy_unknown_requires_explicit_adoption tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection
```

Result: 33/33 PASS，206.129s。覆盖 W4 health、W5B UI/server、完整 W5A、Personal zero-network、W3 human-review／bounded inventory 与 component version projection；没有运行默认或动态全仓。

一次较早 checkpoint 在 Team test 的最小 HTML fixture 缺少真实 `.nav-group` wrapper 时出现 2 个 fixture error，随后被主动中止，未计入通过证据。fixture 修复为真实结构后最终 checkpoint 全通过。Windows 对超限且服务端有意不读取的 HTTP body 可能返回 connection reset；最终测试同时要求小型 unknown-field 得到脱敏 400，并接受超限请求的 400 或连接级拒绝，不放宽 16 KiB 产品上限。

## Browser evidence

Browser: Codex in-app Chromium；root-only UI 首次构建后只通过 `127.0.0.1` 访问。没有 DNS／公网／外部服务请求。验收完成后 Team 被 disable，runtime registration 不存在，UI server 被停止，浏览器测试页关闭。

实际点击路径：

1. Personal → Team sibling navigation；首次发现 Team 是概览组第 4 项而被旧 `nth-child(n+4)` CSS 隐藏，Candidate 随后把该组设为 expanded，重建后 Team 导航可见。
2. disabled onboarding → Enable Team：确认仍为 `team-enabled-stopped`，没有 Coordinator。
3. Start Coordinator：确认 UI-owned `127.0.0.1` runtime；随后依次点击 heartbeat on、sharing off、sharing on。
4. Capture：outbox 从 0 → 1；Sync now：outbox 1 → 0，Member → Workstream 出现 `online / created / Local-only`，未显示 Review Ready／Integrated。
5. 连续创建两条固定 pause request；第一条 Accept locally，第二条 Reject locally。状态分别为 `accepted-locally`／`rejected-locally`，两者 `execution_performed=false`。
6. Stop Coordinator：Team config 保留且 runtime 变为 `team-enabled-stopped`；Disable Team：返回图形化 Personal zero-network onboarding。

Viewport／layout：

| Viewport | Result |
|---|---|
| Desktop 1280px | document `scrollWidth=1265`，Team sidebar entry visible，Personal/Team sibling switch、onboarding、toolbar、Member/Workstream 与 inbox 可扫描；无横向溢出。 |
| Mobile 390×844 | document/body `scrollWidth=375`，Team content `scrollWidth=331`；toolbar 自动换行，状态为两列，Member → Workstream 和 request 状态保留；无横向溢出。 |

真实 Personal snapshot 只作为 host-local browser evidence：37 个可见 worktree，0 current Direct blocker，60 reconciliation（4 stale session + 55 historical overlap + 1 unregistered Candidate），32 legacy／Unknown hygiene debt，33 Unknown 全部进入 hygiene。该快照没有提交为 fixture、State 项目事实或可移植产物。

## Remaining boundaries

- 自动发现、真实其他成员设备、真实多机／LAN 质量、跨 Coordinator 状态迁移、自动选主／leader election、云 relay、多设备迁移和完整成员管理 UX 未实现。
- UI 没有远程 shell／Agent／merge／delete、自动执行 request、自动 Review Ready／Integrated、自动 cleanup 或 LAN bind 控件。
- 当前 UI 是 self-host root-only Candidate，不在默认静态／动态 docsite、发布 Skill、installer、managed tools 或 v0.2.0。
- 本记录没有默认／动态全仓、Ubuntu、远端 exact-SHA checks、push、PR、main merge、tag 或 Release 证据；中央 Candidate／Promotion 仍需另行执行。
