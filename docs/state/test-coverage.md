# 测试覆盖 State

Updated: 2026-08-29

## 当前验证体系

- 验证分为 `Fast → Checkpoint → Candidate → Promotion`。Fast 只提供局部反馈；Checkpoint 证明 Workstream checkpoint；Candidate 运行完整本地门；Promotion 绑定 non-main exact SHA、规定 OS 和 required checks。
- Fast 使用 15 秒预算；Checkpoint 使用 90 秒预算；完整 Promotion 保留每个 final unittest ID、动态 build、结构／docsite／链接／发布包／diff gate 与安全预算。
- CI6 integration baseline inventory 为 404 unique unittest IDs、27 logical shards、10 physical lanes/OS、88 Fast、89 Checkpoint；U2 登记后为 415，U2.1 将四组新断言折叠进既有 owner test IDs，registry inventory 保持 415。`team-relations-execution` 保持独立 300 秒 Promotion 预算。
- CI6 新增 repo-local `scripts/ci/validate_change.py`，从 Git diff、Git-private Workstream subsystem／expected writes 与版本化 mapping registry 自动选择 exact test IDs，并生成绑定 HEAD/base/dirty fingerprint/registry 的 tier receipt。直接 `unittest` 仍可调试，但不能声明正式 Fast／Checkpoint 证据。
- lane runner 为每个 logical shard 启动独立 Python 子进程，保留原 shard result 并生成 lane receipt；失败、缺失、重复、extra、manifest/SHA/OS/order drift 或取消均使 aggregate 失败关闭。
- required check 名称仍为 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`；main branch protection strict 且 enforce-admins。

## 当前通过证据

- CI5 本地 contract/mutation 17/17 PASS；inventory 为 390／27／10／57／81，无 missing、duplicate 或 dead selector。
- CI5 本地 Fast 57/57 为 3.235952s；最终两次 Checkpoint 均为 81/81，42.806990s／43.071302s，预算未调高。120.961576s 的真实 Git journey 只保留在 Promotion。
- exact SHA `9ee831f0d6f64306fe821f8c70229df54648d3eb` 的 Fast run `33235942078` 成功；Promotion run `33235992711` 为 25/25 jobs PASS，Windows／Ubuntu required checks 双 PASS，各自聚合 390 tests／27 shards。
- CI5 hosted wall time 为 3m56s；20 个 lane jobs 共 23.9 job-min，lane 内测试步骤共 14.352 分钟，派生 setup/checkout/install/artifact overhead 约 40%，满足 `<30 lane job-min` 与 `<45%` 的 advisory 目标。
- 同一 exact SHA 已进入 main，main Fast run `33236225082` 成功。该证据关闭 CI5 hosted acceptance，不创建新 Release。
- SC1 开始前本地主工作树 clean；`validate_ci.py --all`、integrated structure、Fast 57/57 与 `git diff --check` 均通过。
- W6.1／CI6／A3 整合时保留 CI6 schema-5 manifest，并把 A3 七个低成本 Authority consumer tests 登记进 data-only mapping registry；CI contract 与 A3 7/7 专项通过。Hosted exact-SHA Promotion 仍由整合候选单独取得。
- U2 Unified Observatory focused 11/11 与最终 adjacent 12/12 PASS；CI6 final Fast 根据当前 diff 选择 49 项并 49/49 PASS，final Checkpoint 选择 54 项并 54/54 PASS（evidence-eligible，未超预算）。真实动态单 URL、静态无控制、Host／Origin／cookie／token、Team／Authority／AI／Maintenance 不升级、helper/marker 回收和 desktop/390px browser 均有独立证据。
- U2.1 新增 legacy Maintenance/current refresh、legacy/archive graph/empty refusal、startup-cached graph endpoint 与全局 stop 资源回收四组断言，并折叠进既有 owner test IDs；registry byte-for-byte 不变，不扩大历史 W6.1 `<24` Checkpoint selector。focused 五套 47/47、折叠后 exact methods 5/5、Unified 11/11；最终 CI6 Fast 选择 38 项、Checkpoint 选择 44 项，均 evidence-eligible PASS，详见 U2.1 Validation。
- W7.1 的四个 archived-session 安全回归已登记为 `team-lan-core` Promotion-only medium evidence，不进入 Fast／Checkpoint；其分支 focused 19/19、exact Fast 57/57、Checkpoint 85/85 及真实 self-host read-only graph 均通过，最终整合 Candidate 仍需 Promotion 重放。
- W7.2 将布局、折叠、lens 端点、inspector 与 desktop/mobile ledger 断言折叠进既有 Workstream Graph owner IDs，CI inventory／registry 不变。focused Graph＋Unified 18/18 与 JS syntax PASS；真实 self-host 1280×800、1440×900、390×844 无页面横向溢出或 console warning/error。最终 CI6 Fast／Checkpoint receipt 见 W7.2 Validation。

## 覆盖面

- `tests/test_project_orrery.py`：安装、非覆盖升级、发布包、更新兼容、凭据与模板投影。
- Authority suites：fixture/evaluator、compatibility、projection、migration/restore、AI non-escalation 与 release-candidate gate。
- Adapter suites：Codex、Harness JSON、Claude Code、DeepSeek Harness 的薄层、归档、依赖失败与生命周期。
- Collaboration suites：W1/W2 session／Scope／finding、W3 review/integration/cleanup、Personal／Team、LAN harness、lineage、maintenance、relation graph 与 apply/undo/recovery contract。
- Unified Observatory suite：versioned registration/discovery、collision/escalation fail-closed、quarantine、static boundary、single-URL runtime、HTTP security、consumer non-escalation、helper lifecycle 与 legacy rollback。
- Documentation governance suite：provider-neutral finding schema、11 类正负 synthetic fixture、soft-budget advisory 与零写入／零网络边界。
- Context-routing suites：24-task corpus、Pilot 002–009 frozen control packages、读取代理、JSONL audit、retention、Oracle v0.2 与 contamination/failure controls。
- Repository gates：integrated installation、isolated docsite、Markdown links、forbidden artifacts、release dry build、workflow/static contract、secret boundary 与 `git diff --check`。

## 证据解释边界

- GitHub Promotion 证明 exact source SHA 在指定 runner 上通过，不证明公开发布、其他 runtime、真实多机或模型自然语言正确。
- Agent receipt 只属于自述；JSONL 是事后审计。没有可工作的实时 Hook 阻断，不能宣称直接读取被执行前拦截。
- synthetic Git fixture、loopback HTTP 和 in-app Chromium 分别证明确定性 contract／本机 transport／页面行为，不外推为真实双机 LAN、远端执行或生产可靠性。
- 合法 skip／expected failure 保留原语义；被中断、没有 `Ran`／`OK` 或缺少 exit code 的命令不算通过。
- 历史失败轮保留在 Validation／GitHub Actions；后继 exact SHA 通过不改写原失败事实。

## 验证证据入口

- [Validation 索引](../validation/README.md)
- [U2 Unified Observatory Production Integration](../validation/2026-08-29-u2-unified-observatory-production-integration.md)
- [U2.1 Unified Observatory UX Acceptance Fixes](../validation/2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md)
- [W7.1 Archived Session Relation Projection](../validation/2026-08-29-w7-1-archived-session-relation-projection.md)
- [W7.2 Workstream Graph Readability](../validation/2026-08-29-w7-2-workstream-graph-readability-progressive-disclosure.md)
- [CI5 Promotion Throughput Optimization](../validation/2026-08-29-ci5-promotion-throughput-optimization.md)
- [CI4 opaque token reliability](../validation/2026-08-29-ci4-opaque-cli-token-argument-reliability.md)
- [R3 brand-only closeout](../validation/2026-08-28-r3-orrery-brand-only-closeout.md)
- [W7D integration](../validation/2026-08-28-w7d-w7-integration-candidate.md)
- [Authority M2 integration](../validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)
- [W1/D1/C1 integration](../validation/2026-08-22-w1-d1-c1-canonical-integration.md)
- [Context-routing State](context-routing-research.md)

## 已知缺口

- 动态图形 reader 依赖测试默认可跳过；高风险 UI／HTTP 改动仍需显式动态与浏览器验证。
- CI6 已有保守自动影响分析；Fast／Checkpoint evidence reuse 当前只实现 versioned refusal contract，跨 SHA Promotion reuse 与远端 runner cache 仍不存在。
- Context-routing 没有实时 Hook、自动 R1 脱敏导出或异地 raw evidence backup。
- v0.2.0 archive 尚无 Windows／Linux byte-for-byte 一致性门。
- Claude 认证后真实模型路由、真实双机 LAN、self-host relation apply、自动 worktree removal 与 OS scheduler 没有验收证据。
- Unified Observatory／Authority 没有默认 production consumer 或公开 release evidence；Documentation D2 scanner／CLI 尚未实现。
