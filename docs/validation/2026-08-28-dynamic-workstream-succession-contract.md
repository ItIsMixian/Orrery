# Validation：W7A Dynamic Workstream Succession Contract

Date: 2026-08-28

Status: correction checkpoint focused／Fast／adjacent／structure／site／link／diff PASS；hosted Promotion、main merge、W7B apply／undo execution 与 W7C-B 正式图形视图未执行

Fact scope: `codex/w7a-dynamic-workstream-succession-contract`，task base／parent lineage `W5E-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

## 结论

中央独立验收正确拒绝初始 Candidate `b6be68e55c149f43bbec420654b56855a4068a28`：旧
`_node_from_session()` 把 waiting-for-user、paused、blocked-by-conflict、failed 等状态映射为 active，node
contract 又把 lifecycle/runtime/evidence 压成 summary；旧 apply/undo 只有 relation event append，不能原子
标记或恢复 predecessor Session。本 correction 在同一 ADR-0014/Approved Design/Plan 下完成实装修正，没有
新建 ADR、改写 W7C-A、写真实 relation store 或批量改写 peer Session。

Core 现在分开输出 `session_state`、`lifecycle_phase`、`runtime_condition`、`evidence_freshness`、
`scope_status`、closure、primary/affected subsystem、visibility、observability 与安全 source links；summary
`status` 必须由这些轴确定，矛盾输入失败关闭。active tip 只接受 Session/evidence/Scope current、runtime
active、未结束 lifecycle 的普通节点与 review-ready/review-pending 正对照。

Active takeover 必须带 predecessor `paused` marker；completed takeover 要求 predecessor 已 exact
`closed/superseded` 或同一 atomic apply plan 完成该 transition，否则 graph invalid 并保留 compare reason。
Apply receipt 保存原/新 Session hash、HEAD 与全部状态轴；undo 绑定完整 exact receipt，只在无漂移时追加
补偿事件并恢复原 Session。W7A 仅冻结并验证 I/O shape，`execution_supported=false`，不执行迁移或删除。

## 修正前后真实只读图

- 修正前 `b6be68e`：8 nodes／6 legacy-projected edges，graph hash
  `52e9116554afa1de2573ae2a42d2377833464952db2e103501169bccedcdf9df`，错误 active tips 为
  `R1-orrery-rename-migration-audit`、`W5C-team-observatory-ux`、`W7A-dynamic-workstream-succession-contract`、
  `W7C-A-workstream-graph-visual-prototype`。其中 W5C/W7A/W7C-A 的真实 runtime 均为 waiting-for-user；R1
  虽 runtime active，但 evidence freshness 为 Unknown，亦不满足新 active eligibility。W6 的真实 runtime 为
  blocked-by-conflict，旧 summary 也曾把它伪装为 active，之后仅因 lineage folding 未出现在 tip 列表。
- 修正提交后 W7A Session closeout 的只读诊断：仍为 8 nodes／6 legacy edges、validation valid，唯一
  active tip 为
  `W5D-lan-collaboration-harness`。CI1/W5C/W5E/W7C-A 映射 inactive，W6 映射 blocked，R1 因 Unknown evidence
  失败关闭；W7A 自身以 current waiting-for-user 映射 inactive。这里没有把任何 predecessor 写成
  paused/closed/superseded，也没有声称 W7B apply 已执行。
- 原生 `$GIT_COMMON_DIR/orrery/workstream-relations/` 在修正前后均不存在；只读 graph 未创建它。
- 排除 W7A 自身后，7 个 peer Session exact-byte SHA-256 清单摘要修正前后同为
  `6eebe8c9414bfd804779380627ebe3e1d17d717dc89569747ff07afe3db89c8d`。真实
  W5C/W6/W5D/CI1/W5E/R1/W7C-A Session 未被本 correction 改写。

## 契约与实现证据

- Core `0.1.13`：versioned v1 record/graph/plan/apply-receipt/undo-receipt schema，独立 node 轴，exact
  OID/ancestor、self/duplicate/cycle/multi-primary-parent、completed predecessor closure、deterministic active
  tips 与 compare/suppress reason。
- CLI `0.1.17`：`relations graph`、`relations succession-plan`、显式本机 `relations propose`；稳定 JSON
  envelope 与 zero-network/no-auto-apply 边界不变。
- W7B freeze：one-local-confirmation、exact graph/discovery/event/Session hash/HEAD binding、
  `all-operations-or-none`、apply receipt、exact no-drift undo restore、preservation contract、
  `destructive_actions=[]`、`execution_supported=false`。
- W7C-B freeze：layout-neutral stable workstream/relation IDs、三条独立状态轴、subsystem、
  visibility/observability、edge lifecycle/evidence/source links、active tips、Unknown 与 compare/suppress reason。
  `tests/fixtures/workstream-relations/v1/w7c-consumer-compatibility.json` 明确标记
  `synthetic-non-authoritative`；它只读对照 W7C-A `a39f6a7` exploration，不复制 provisional schema/page。

## Fast 与 focused

- `python -X utf8 -m unittest tests.test_workstream_relations -v`：最终 15/15 PASS。
  覆盖原 relation 12 项语义，并新增 waiting/paused/blocked/failed/offline/stale-unknown 排除、active 与
  review-pending 正对照、矛盾 summary 拒绝、completed open predecessor fail-closed、closed/superseded 正例、
  atomic Session transition/apply receipt/exact undo no-drift、W7C consumer completeness 与 no-layout contract。
- Draft 2020-12：schema 自检及 record、graph、succession、discovery、apply plan、apply receipt、undo plan、
  undo receipt、legacy projection 共 9 类实际 Core payload PASS；另以 active predecessor Session-transition
  实例复核 apply/receipt/undo 三类复杂 shape PASS。外部 `jsonschema` 只用于验收，不进入 Core dependency。
- `scripts/ci/run_test_shard.py --profile fast`：48/48 PASS，1.595s；明确是 non-promotion feedback。
- `scripts/ci/test_inventory.py`：357 unique test IDs／26 shards／48 Fast PASS。
- `scripts/ci/validate_ci.py --all`：Fast role、Promotion completeness、exact-SHA binding、fail-closed gates PASS。
- schema、两个 fixture JSON parse 与 Core/CLI/test compile PASS；确定性 graph/CLI JSON 由 focused tests 覆盖。

## Checkpoint 邻接与结构

- W1/W2 collaboration contract 27、W5D lineage 2、CI1 contract 8、component projection 1：合计 38/38 PASS，
  172.982s。组件投影与相关断言已同步 Core/CLI 0.1.13/0.1.17。
- W3 stable CLI/exit-code 与 LAN basic contract 2/2 PASS；首次组合命令另有 2 个测试类名选择错误，未运行
  产品代码。改用真实类名后 Authority migration/restore dry-run 2/2 PASS，0.014s。
- W5D double-clone loopback runner 独占复核 1/1 PASS，10.425s。初始 W7A 验证中曾记录两次并发
  `ConnectionAborted`/timeout 后独占 PASS；本 correction 没有修改 LAN/Team transport，因此当前 PASS 与
  先前波动均不能表述为 relation 修复或 transport 稳定性变化。
- `validate_installation.py --require-integrated` PASS；repository gates PASS：632 repository paths、339
  Markdown、939 local links、无 forbidden/generated artifact。
- 隔离 docsite PASS：1,839,975 bytes，14 ADR／6 State／7 subsystem／2 Snapshot／138 docs／24 Plans／7
  Library；输出位于系统临时目录，未改 `docs/_site/index.html`。
- `git diff --check` PASS；未运行完整 Promotion。

## L2/L3 整合门

当前全部可见 worktree 的只读 overlap audit 为 510 active candidate findings：139 L2／371 L3，
`review_ready_blocked=true`、0 unavailable peer、`writes_performed=false`、`network_performed=false`。这些是
现有 Scope/authority/exclusive-resource 整合门，不是 relation graph validation 错误；W7A 没有批量
acknowledge、改写 peer Scope/Session 或用尚未执行的 W7B relation apply 隐藏它们。唯一整合者仍须在 clean
integration worktree 对 exact Candidate SHA 重新计算并按 W2/W3 路由处理。

## 未完成边界

- W7B 才可在新的 Approved Plan 下实现真实 discovery UX、一次本机确认、atomic batch apply/undo、receipt
  persistence、legacy materialization 与 retention/compaction；执行时必须复核 exact graph/Session/HEAD。
- W7C-B 才实现 Succession/Dependency/Conflict 三个派生视图、active-tip 高亮、历史折叠、Unknown 虚线与
  accessible list；Core 不拥有颜色、坐标、折叠或 UI 文案。
- relation apply/undo 永不授权 worktree/branch/commit/Validation/作者文档删除；删除继续由 W6 maintenance
  单独授权与重验。
- 推广仍需唯一整合者冻结 exact Candidate SHA、推到非 `main` 分支并取得 GitHub
  `smoke-test (windows-latest)`／`smoke-test (ubuntu-latest)` 双 PASS；本分支没有 push、main merge、tag 或
  Release。
