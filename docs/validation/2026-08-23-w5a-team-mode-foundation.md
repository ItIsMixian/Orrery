# Validation：W5A opt-in Team Mode foundation

Date: 2026-08-23

Scope: `codex/w5-team-foundation` Candidate；Core／CLI Team 配置、身份、metadata transport、loopback Coordinator、只读聚合与 request-only 本机确认。不包含 Observatory／docsite、自动发现、W5 UI、云 relay、多设备迁移、自动选主、push、main integration 或 Release。

Status: Candidate focused + adjacent checkpoint PASS；中央 integration candidate 的默认／动态全仓与 Windows／Ubuntu exact-SHA required checks 尚未运行。

## 输入与版本

- worktree：`D:\coding warehouse\project-orrery-w5-team-foundation`
- branch：`codex/w5-team-foundation`
- base：`main@7932a9c01efb2e5125da1962873e67383982d98c`
- implementation commit：`ac0f4eb`（Core 0.1.8／CLI 0.1.13；Observatory 0.1.0 不变）
- Python：本机 CPython；实现只依赖标准库与既有 Core，不引入云服务或团队同步依赖

## 实现边界

- Team 配置、member credential、Coordinator state、outbox 与 request decision receipt 位于 Git-private `orrery/team/`；默认没有该配置时为 `personal-zero-network`。
- `team enable` 只写本机配置，不打开 socket；只有显式 `team serve` 才启动 Coordinator。默认 bind 为 loopback；wildcard／private LAN bind 还要求本地 `allow_lan_bind`。
- 手工 invite／join 校验项目 fingerprint、指定 member、一次性 invite 与 Host-local Admin 确认。非成员不能读取 projection 或发布状态。自动发现明确返回 `unsupported-next-phase`，没有伪装完成。
- envelope 固定为 v1、上限 64 KiB、严格 exact-field 与递归 forbidden-field 门；只包含 Member／Host／Workstream lifecycle/runtime/evidence freshness、Git ref/OID/ahead-behind/dirty count、Scope/path summary、finding／validation／review summary和 last-seen。Prompt、回答、reasoning、transcript、源码／文件正文、未 push diff、凭据／token／API key 等字段失败关闭。
- outbox 按 member + Workstream + event kind 合并重复事件；`sync-now` 提供立即发送。revision 必须单调递增，旧／重复 revision 被拒绝；每个 Member 只有一个手工选择的 active Host，不做 leader election。
- heartbeat 默认关闭；关闭时新鲜快照也只投影 presence `unknown`，TTL 后为 `stale-unknown`。显式 heartbeat 才可投影 `online`；sharing off 为 `unavailable`。
- Coordinator projection 固定 Member → Workstream 两级，Host 只是定位 metadata；projection 标为 `derived-read-only` 且 `execution_capability=false`。
- 中央只能创建 request。接受／拒绝前先写成员本机 Git-private receipt；中央记录 `execution_performed=false`。实现没有 shell、Agent、merge、delete 或远程动作入口。
- capability grant/revoke 复用 W1 Member contract 并提升 credential epoch；旧 credential 立即失效。Admin／Integrator 不获得远程执行权，也不能改变 W2 Direct／L3 或 W3 人审规则。

## Focused 验证

命令：

```text
python -m unittest tests.test_collaboration_team -v
```

结果：13/13 PASS，80.844s。覆盖 Personal 零监听、enable/disable、loopback 与 LAN bind gate、认证／Host 确认、非成员拒绝、禁止字段／大 payload、event coalescing、revision rollback、Host 切换、heartbeat off/on、TTL、request-only/local receipt/no execution、capability revoke、zero external network 和稳定 CLI JSON。

网络测试只绑定 `127.0.0.1`；DNS 名和公网 IP 在 `urlopen` 前失败关闭，没有调用外部服务。

## Adjacent checkpoint

首次 checkpoint 命令选择了两个不存在的 unittest class 名；22 个实际产品用例通过，2 个 loader selection error。该轮不记作 PASS，也不把 loader error 解释为产品失败。随后用正确 class 名补跑缺失用例。

```text
python -m unittest tests.test_collaboration_team tests.test_collaboration_contract.CollaborationContractTests.test_schema_bundle_freezes_all_phase_zero_contracts tests.test_collaboration_contract.CollaborationContractTests.test_personal_default_and_team_contract_never_start_network_runtime tests.test_collaboration_contract.CollaborationContractTests.test_member_capabilities_are_composable_audited_and_revoke_local_credentials tests.test_collaboration_contract.CollaborationContractTests.test_w2_cross_member_ack_progress_stales_on_scope_change_and_resolves_mechanically tests.test_collaboration_contract.CollaborationContractTests.test_worktree_cli_has_stable_json_and_explicit_private_write tests.test_collaboration_w3.CollaborationW3Tests.test_risk_policy_human_actions_and_ai_only_do_not_satisfy_review tests.test_collaboration_w3.CollaborationW3Tests.test_cli_json_and_exit_codes_are_stable_without_main_or_cleanup_mutation tests.test_authority_model_migration.AuthorityModelMigrationTests.test_dry_run_reports_change_and_does_not_write tests.test_authority_model_restore.AuthorityModelRestoreTests.test_dry_run_reports_exact_restore_without_writing tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection tests.test_codex_adapter.CodexAdapterTests.test_adapter_is_thin_versioned_and_has_scoped_runtime_evidence -v
```

结果：22 个实际用例 PASS；2 个 loader selection error，原因是正确 class 名分别为 `AuthorityModelMigrationCliTests`／`AuthorityModelRestoreCliTests`。

```text
python -m unittest tests.test_authority_model_migration.AuthorityModelMigrationCliTests.test_dry_run_reports_change_and_does_not_write tests.test_authority_model_restore.AuthorityModelRestoreCliTests.test_dry_run_reports_exact_restore_without_writing -v
```

结果：2/2 PASS，0.013s。合并解释为 focused + adjacent checkpoint 的 24 个实际产品用例全部通过；没有运行默认／动态全仓。

## 结构与安全 checkpoint

```text
python -m compileall -q packages/project-orrery-core/src packages/project-orrery-cli/src tests/test_collaboration_team.py
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
git diff --check
```

结果：PASS；结构 validator 报告 `Authority status: integrated candidate`、Authority Model 1 supported／strict eligible。未运行或修改 docsite。

只读 changed-path gate 确认 `scripts/docsite/`、`packages/project-orrery-observatory/` 与发布模板 docsite 变更为 0；修正过宽、会误命中 `task-centered` 的初始 `sk-` regex 后，高置信 private-key／OpenAI-like／GitHub token pattern 为 0；`git diff --check` PASS。

PowerShell 本地 Markdown link scan：338 个 Markdown、864 个本地链接、1 个 D1 `broken-link-positive.md` 预期 missing fixture、0 unexpected missing。

## 待中央 integration candidate

- 默认／动态全仓、隔离 docsite build 与 Windows／Ubuntu exact-SHA required checks由唯一整合者在 W4/W5 联合 integration candidate 上统一运行。
- 没有真实多机、真实 LAN 广播、云 relay 或外部服务证据；不得从 loopback 测试外推这些支持。
