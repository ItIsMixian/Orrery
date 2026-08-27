# Validation：W6 Workspace Maintenance Phase 0–2

Date: 2026-08-27

Status: Worktree Candidate focused／adjacent／browser／structure／isolated-site／link／diff PASS；未执行中央 Candidate 全仓门、远端 required checks、push、main merge、tag 或 Release

Scope: `codex/w6-workspace-maintenance`，从 W5C `6dd508f0a416b9e1837460e9f1550c3243ac7ce2` 建立，并在首次产品写入前合入 `main@673e252fb8774a3a8a81da963d8d7acbdd78044b`。本轮只实现 Plan Phase 0–2；Core／CLI／Observatory Candidate 分别为 0.1.10／0.1.14／0.1.6，Core API 仍为 1。

## 实现边界

- `.project-orrery.json` 增加 strict `workspace_maintenance` v1 项目策略；缺字段、未知字段、未知版本或 `auto_remove_eligible_worktrees=true` 失败关闭。host preference 只存 Git-private，scheduler 固定 `unsupported-phase-4`。
- Core planner 直接调用 W3 `inventory_workspaces`／`compute_workspace_cleanup_eligibility`，不复制 clean、dirty、ignored、unique commit、closure／review／Validation 或路径安全规则。scan 只在 bounded source 内运行，支持 24h catch-up、integration／closed event、single-flight、debounce、hard timeout 与 interrupted recovery。
- queue item 绑定 selected workspace 的 exact resolved path、HEAD、branch、session phase、integration OID、closure／review hash、Validation refs hash、dirty/untracked/ignored 与 unique commit；全局 inventory hash保留为来源，但不会因 scan 自己写 Git-private metadata 而自我失效。
- `authorize` 只接受本机 human actor；`execute` 只接受 authorization ID，内部固定 `git worktree remove [--force only for allowlisted ignored] -- <registered-path>`。执行前重新计算 W3 eligibility 并检查 registry／lock／primary/path identity，漂移变 Stale；执行后验证 path、registry、branch、commit 与 receipt。
- local branch 只有 30 天 reminder，remote branch 保持 `unobserved-zero-network`；两者没有 execute。Team Coordinator 只有 `cleanup` request，request／accept／reject 均 `execution_performed=false`。没有任意 shell/path/URL、远程执行、branch 删除、后台自动删除或 OS scheduler 安装。

## Automated evidence

W6 focused：

```text
python -X utf8 -m unittest -v tests.test_workspace_maintenance
```

Result: 7/7 PASS，463.055s。覆盖 contract／policy／host preference、11-scenario corpus、CLI JSON、Personal zero-network、24h catch-up、event trace、debounce、single-flight、elapsed 与 hard timeout、interrupted scan、dirty drift、worktree lock/process-use、interrupted execute receipt、branch/path/shell/URL/AI authority 拒绝，以及真实临时 linked-worktree removal 后 path／registry absent、branch／commit retained 与 receipt。

W3 + Personal adjacent Checkpoint：

```text
python -X utf8 -m unittest -v tests.test_collaboration_w3 tests.test_personal_observatory
```

Result: 27/27 PASS，798.195s。W3 bounded inventory、Legacy／Unknown、recovery／reparse、dirty／untracked／ignored、unique commit、review／closure／Validation、四动作独立与旧 caller-attested receipt 语义保持不变；Personal 原健康页、W3 provider/fallback、静态只读与新 maintenance sibling page 通过。

Team + component adjacent：

```text
python -X utf8 -m unittest -v tests.test_team_observatory tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection
```

Result: 4/4 PASS，45.301s。`cleanup` Team request 进入本机 pending inbox且 `execution_performed=false`；loopback Host／Origin／cookie／body／secret gates、root-only 与组件版本投影通过。

Version／W1-W2 compatibility adjacent：

```text
python -X utf8 -m unittest -v tests.test_authority_model_migration tests.test_authority_model_restore tests.test_collaboration_contract
```

Result: 64/64 PASS，306.162s。组件版本断言、manifest migration／restore、Personal zero-network、worktree/session/route/lifecycle、schema bundle、Scope/Finding 与 L1–L3 hard gate 保持兼容。

Structure：

```text
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
```

Result: PASS；Authority status `integrated candidate`，Authority Model 1 strict evaluation eligible。

## Isolated site and link evidence

默认隔离静态站：

```text
python -X utf8 scripts/docsite/build_docsite.py --out <temporary-directory>/index.html
```

Result: PASS；最终文档集检查点为 1,661 KB，13 ADRs、6 States、7 subsystems、2 snapshots、128 docs、20 plans、6 library docs。

第一次把 `--out` 误传为目录，构建器按“输出文件”契约返回 `PermissionError`；该命令错误未计为通过。使用新临时目录内的 `index.html` 后重跑成功。

显式 Personal 隔离站：

```text
python -X utf8 scripts/docsite/build_personal_observatory.py --enable --out <temporary-directory>/index.html
```

Result: PASS；最终文档集检查点为 1,716 KB／128 docs，projection `ready`；输出包含 `workspace-maintenance`、`data-maintenance-control=false` 与无 scheduler 边界。

Markdown 本地链接在加入本 Validation 后为 350 files／899 local links；唯一 missing target 是 D1 冻结 positive fixture `tests/fixtures/documentation-governance/v1/corpus/broken-link-positive.md -> ../validation/missing-validation.md`，属于既有预期。`git diff --check` 最终无 whitespace error；JSON／TOML 只有既有 LF→CRLF 工作副本提示。

## Browser evidence

Browser: Codex in-app Chromium；只访问 root-only `http://127.0.0.1:<ephemeral>/team/`。没有 DNS、公网或第三方请求，没有启用 Team Mode。

Desktop 1280×720：

- 真实点击“工作区维护”导航，维护页面可见；两列主区约 `417px 280px`，document 无横向溢出。
- 真实点击“立即只读扫描”；等待页面从“正在执行本机维护步骤”重建为“本机控制可用”，按钮恢复 enabled。
- 后端 receipt 显示 scan `succeeded`、3 worktrees、0 suggestion、0 receipt、`network_performed=false`；worktree registry 仍保留 main、W6 与 W5C，未执行删除。

Mobile 390×844：

- reload 后 maintenance page 保持可见；主 grid 与 action boundary 均收敛为一个约 347px 列，document 无横向溢出。
- 真实点击“授权与执行历史”，`details.open=true`；只读 scan 按钮保持 enabled，批量授权因当前无 suggestion 正确 disabled。
- 截图人工检查确认保护／Unknown、策略、branch boundary 与历史区域可读。

## 开发中暴露并修正的问题

- 初版 authorization binding 把包含 primary `.git` 体积的全局 inventory hash 也纳入 evidence hash；scan 自身 Git-private 写入会使建议自我漂移。修正为保留 inventory hash 作为 provenance，只对 selected workspace 稳定事实计算 evidence hash。
- 初版 single-flight lock 没有 stale owner 信息；修正为写 PID／timestamp，只在确认 owner 不存活时回收，未知 lock 继续失败关闭。已持锁时不会把并行 scan 误记为 interrupted。
- 初版中断测试误替换全局 `subprocess.run`，连 preflight Git 读取也被中断；测试桩收窄到内部固定 remove-worktree 调用点，公共 Core API 未增加任意 executor。

## Remaining boundaries

- Phase 3／4 未实现：项目策略即使被篡改为自动删除也失败关闭；没有后台 daemon、Windows Task Scheduler、cron、systemd 或 launchd Adapter。
- 不删除 local／remote branch；remote 状态不联网观察。local reminder 只来自 verified worktree receipt 到期时间。
- preflight 主动识别 Git worktree lock；通用跨平台 PID／打开文件句柄扫描未实现。若其他进程占用只在固定 Git remove 失败与 postflight receipt 中呈现，不会绕过门或冒充成功。
- 动态 Maintenance UI 仍是 self-host root-only Candidate，不进入默认 docsite、Skill template、managed-tool inventory 或公开 v0.2.0。
- 本分支未执行动态全仓、Candidate/Promotion、exact-SHA Windows／Ubuntu required checks 或真实维护者接受演练；这些由唯一整合者在干净 integration worktree 完成。
