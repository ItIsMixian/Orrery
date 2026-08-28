# Validation：W5D LAN collaboration Harness 与 stacked lineage

Date: 2026-08-27

Fact scope: Candidate `codex/w5d-lan-collaboration-harness`；基线 `codex/w6-workspace-maintenance@db78a7f58fdb853922766147a4bbad989ad3bc0e`

Governing authority: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)、[ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)、[Approved Design](../design/multi-worktree-collaboration-protocol.md)、[W5D Plan](../implementation/plans/2026-08-27-w5d-lan-collaboration-harness.md)

## 结论

W5D 的单机／CI 可复验闭环在 Windows Candidate 上通过：Personal 默认仍为 zero-network；discovery 与 Coordinator Host 必须分别由本机显式启动；发现包只含版本、opaque project fingerprint、opaque host/device hint、ephemeral endpoint／nonce／时间；join 需要 project 校验、一次性 proof、Host-local Admin 确认和成员 credential；Coordinator 只允许单 active generation 和手工 switch，不自动选主。双 clone runner 的 7 个阶段全部 PASS，产物脱敏且 `real_lan_validated=false`。

同一 checkpoint 修正 stacked lineage。Session／Scope Observation 记录 versioned parent＋exact task-base OID；显式 lineage 的 committed delta 从 task base 到 HEAD，其他 path source 不变。Overlap 只有在 parent chain、scope HEAD 与本地 Git ancestor proof 同时当前时才排除 inherited committed provenance；它不产生 resolved finding。Legacy、proof unavailable、scope drift、sibling 和 parent post-fork change 都保持 Unknown 或继续形成正常 finding。

这不是 Canonical／Release 或真实双机 LAN 验收；没有 push、main merge、tag、Release、云 relay、自动选主、远程执行、Phase 3 cleanup 或 Phase 4 scheduler。

## Lineage fixture 计数

Controlled W5C(base) → W6(stacked) → W5D(stacked) fixture：

| 口径 | Direct | Authority |
|---|---:|---:|
| legacy integration-base delta（修正前模拟） | 4 | 3 |
| exact task-base delta＋Git ancestor proof | 0 | 0 |

W5D 相对 task base 对 `chain/w6-only.txt` 与自有路径的真实提交仍出现在 Scope；W6 在 W5D fork 后再次修改同一路径会重新产生 Direct／L3；W5D 与同 base sibling 也继续产生 Direct／exclusive-resource L3。不存在 OID、非祖先 OID、错误 parent HEAD、lineage HEAD drift 分别失败关闭或投影 Unknown。Direct/L3 仍不可 acknowledge；W3 validation／candidate drift 仍阻断 Review Ready。

真实本机 W5D session 已显式绑定 `W6-workspace-maintenance@db78a7f58…`，但没有自动改写 W5C／W6 session。浏览器中的 explicit W5D→W6 chain 仍有 52 个 unique finding，来自 staged／unstaged／untracked／expected 等当前任务来源；W5C↔W6 的 70 个 current Direct 仍按 legacy 规则保守保留。中央整合时需显式 rebind／retire，不能由 branch 名推断或由 W5D 自动关闭。

## 自动验收

- `python -m unittest tests.test_collaboration_contract -v`：27 项运行，26 PASS；唯一失败是 schema `$defs` 冻结集合尚未加入 `stacked_lineage`。同步期望后定向用例 PASS；其余 W1/W2 create／rollback、Scope Expansion L1/L2/L3、exclusive resource、ack、CLI 与 zero-network 全部通过。
- `python -m unittest tests.test_collaboration_lineage tests.test_collaboration_contract.CollaborationContractTests.test_schema_bundle_freezes_all_phase_zero_contracts tests.test_personal_observatory -v`：17/17 PASS，353.024s。
- `python -m unittest tests.test_lan_collaboration_harness tests.test_collaboration_team tests.test_team_observatory tests.test_collaboration_w3.CollaborationW3Tests.test_validation_failure_and_candidate_state_drift_block_review_ready tests.test_collaboration_w3.CollaborationW3Tests.test_package_stales_on_candidate_input_drift -v`：22/22 PASS，410.990s。
- `python scripts/acceptance/run_lan_collaboration_acceptance.py`：PASS；仓库外 raw leaf `project-orrery-w5d-acceptance-ct5y4u3h`，manifest SHA-256 `59fbdef57bf3ac776719e011fd32165dab818ea9c34c1ccbadc4c1916e11f7ad`，stage-results SHA-256 `d00f987cf75b7688ea2a67b5610a1d8ab402f3c5bc6092365005836e4e366d41`。
- `python scripts/acceptance/validate_lan_collaboration_acceptance.py <raw-root>`：3 个 sealed artifact 校验 PASS；manifest 为 Core 0.1.11／CLI 0.1.15、Windows、Python 3.13.5、2 members、controlled discovery＋loopback HTTP、零真实凭据、零外部网络、7 stages。
- `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`：integrated scaffold 结构 PASS。
- `python scripts/docsite/build_docsite.py --out <system-temp>/index.html`：最终隔离站点 1,729,016 bytes，13 ADR、6 State、7 subsystem、130 docs、21 Plans；未写 `docs/_site/index.html`。
- 作者文档链接检查：159 份 Markdown、798 个本地链接、0 missing。全仓扫描唯一 missing 是 D1 明确保留的 `broken-link-positive` synthetic fixture。
- `python -m json.tool .../collaboration-v1.json`、`compileall` 与 `git diff --check`：PASS。

## 浏览器验收

真实 in-app Chromium 对 root-only 动态 Observatory 完成：

- Team：1280px 与 390×844 均点击显式 discovery；发现候选只显示 opaque hint／loopback endpoint／untrusted；从独立临时 clone 发起 join 后，Host 页面显示 pending request 并由本机按钮确认；同步后显示两个成员、connected／monotonic aggregation、Coordinator generation 1；request accept 显示“本机接受（未执行）”。桌面 `1265 < 1280`，移动 `375 < 390`，无横向溢出。
- Personal lineage：1280px 显示 `Stacked chain`、W5D→W6、task base `db78a7f58`、24 inherited paths 和 chain 内 unique finding；Workstream DOM ID 保持原始稳定 ID，只在标题缩进。390×844 同样可见，`scrollWidth=375 < 390`。临时 viewport 已 reset，测试 tab 与本机 server 已关闭。

浏览器验收曾发现 owner credential epoch 变化后 re-enable 写回 epoch 1 的真实缺陷；Core 已改为签发当前 member epoch，并加入回归。浏览器提前关闭请求产生的预期 BrokenPipe／ConnectionReset 也由 root-only UI server 安静处理，不吞掉其他异常。

## 平台与未覆盖边界

- Windows 本机动态证据如上。当前主机的 WSL 没有可用 distro，Docker Linux engine 未运行，因此没有本地 Ubuntu 动态 PASS；新增测试由 `.github/workflows/validate.yml` 的 Windows／Ubuntu `python -m unittest discover -s tests -v` 路径发现，但 exact-SHA required checks 必须由中央 Candidate 后续执行。
- 所有网络测试只使用 injected controlled discovery 或 `127.0.0.1`；未访问公网或 DNS。真实双机、真实广播域、防火墙／多网卡、路由器隔离、睡眠恢复和真实 LAN Host switch 仍需按 [LAN preflight](../operations/lan-team-preflight.md) 验收。
- 远端最新 main fetch 因本机代理 `127.0.0.1:7897` 不可用而失败；本分支只核对了本地 `main@673e252` 与既定 W6 base，没有把远端不可达表述为最新远端已验证。
- Legacy session 不会自动迁移；parent session 不可见时显式 lineage 标为 `parent-unverified-unknown`，不会获得 inherited-path suppression。中央必须用 exact parent HEAD 显式重绑，不能清空 finding 或按 branch 相似度推断。
