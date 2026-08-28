# Validation：W7A Dynamic Workstream Succession Contract

Date: 2026-08-28
Status: Worktree Candidate focused／adjacent／structure／site／link／diff PASS；hosted Promotion、main merge、W7B apply／undo 与 W7C 正式图形视图未执行
Fact scope: `codex/w7a-dynamic-workstream-succession-contract`，task base／parent lineage `W5E-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

## 结论

W7A 形成 ADR-0014、Approved Design 与紧凑 Implementation Plan，并实现 provider-neutral `workstream-relations/v1` record／graph／plan schema、dependency-free Core validator、Git-common-private append-only store、legacy lineage 只读投影和稳定 JSON CLI。关系只包含 `derived_from`、`depends_on`、`absorbs`；生命周期只包含 `proposed`、`active`、`completed`、`cancelled`、`stale`。Git task base、语义依赖和所有权转移保持正交，多个 predecessor 可以共存，但每个 successor 最多一个 active exact-Git primary parent。

Core 只把 evidence-current、exact-OID 且满足本机 ancestry／task-base 规则的 active `derived_from`／`absorbs` succession 用于 active-tip 折叠；`depends_on` 永不折叠 predecessor。active succession 只消除 ancestor／successor 自身的 Direct pair，sibling、fork 后独有提交、stale／Unknown 和真实 L2／L3 pair constraints 继续保留。证据不足、分支名或路径相似度只产生 proposed／Unknown，不能升级为事实。

共享记录位于 `$GIT_COMMON_DIR/orrery/workstream-relations/<relation-id>/<revision>-<event-id>.json`，不进入作者文档、release package 或生成站点。真实仓库只执行只读加载；唯一 relation 写测试位于隔离临时 Git 仓库，且证明 linked worktree 删除后记录仍存续。真实 W5C／W6／W5D／CI1／W5E Session 没有被批量改写。

## 契约与实现证据

- Core `0.1.12`：versioned schema、record／graph／plan builders、self／duplicate／cycle／multi-primary-parent 检查、独立的 exact `task_base_oid`／`ownership_transfer_oid`、ancestor／stale evidence 规则、deterministic active-tip 与 pair comparison。
- CLI `0.1.16`：`relations graph`、`relations succession-plan` 和显式本机 `relations propose`；沿用稳定 JSON envelope，并保持无网络、无自动 apply。
- W7B freeze：discovery／apply／undo plan 输入输出携带 exact graph hash、一次本机确认 binding、append-only event operation、typed receipt output、全为 `true` 的 preservation contract、`destructive_actions=[]` 与 `execution_supported=false`。
- W7C freeze：layout-neutral node／edge status、evidence、active tips、Unknown、source links 和 comparison pairs；Core 不输出颜色、坐标、折叠布局或 UI 文案。
- CI1 inventory：354 unique test IDs、26 shards、45 Fast；W7A schema／validator／fixture／CLI selectors 纳入 Fast，完整模块纳入 `team-lan-core`。

## 自动验证

- `python -X utf8 -m unittest tests.test_workstream_relations -v`：12/12 PASS，12.573s。覆盖运行中后继、原 Plan 未列出的 CI 类任务、多 predecessor、cycle、自指、duplicate edge、相似度不足、exact Git ancestor／ownership transfer、fork 后独有提交、sibling、stale HEAD／Scope、Unknown parent、active tips、append-only／no-author-doc／no-network、deterministic JSON、legacy projection 和 W7B／W7C freeze。
- Draft 2020-12 schema conformance：relation record、graph、succession／discovery／apply／undo plan 与 legacy projection 共 7 类实际 Core payload PASS；外部 validator 只用于验收，不进入 Core 依赖。
- 当前真实仓库只读 load：8 nodes／6 legacy-projected edges，graph valid，缺省读取没有创建 native relation store；输出只记录计数，未转录私有 Session 内容。
- `python -X utf8 scripts/ci/test_inventory.py`：PASS；354 unique test IDs、26 shards、45 Fast。
- `python -X utf8 scripts/ci/validate_ci.py --all`：PASS。
- schema／synthetic fixture JSON parse 与 Core／CLI compile：PASS。
- `tests.test_ci_validation` 与 component-version projection：9/9 PASS，1.180s。
- W1／W2 邻接：`tests.test_collaboration_contract` 首轮 27 项中 25 PASS，2 项只因预期版本仍为旧 Core／CLI；同步版本契约后精确重跑 2/2 PASS。未借此宣称整组重新执行。
- W3／Authority 邻接：稳定 CLI JSON／exit-code 用例 PASS；migration／restore dry-run 精确用例 2/2 PASS，0.019s。
- W5D lineage 2/2 PASS；LAN 合并运行中两个基础 contract PASS，double-clone runner 因本机 loopback `ConnectionAborted`／timeout 失败；并发重试仍 timeout，随后单独重跑 exact double-clone runner 1/1 PASS，84.521s。该记录保留本机并发／端口时序波动，不把它表述成 W7A 修复。
- 提交后只读本机 overlap audit 覆盖当前全部注册 worktree：509 active candidate findings（139 L2／370 L3），`review_ready_blocked=true`，且 `writes_performed=false`／`network_performed=false`。这些是尚未经过 W7B relation apply／active-tip 消歧的并行 Scope 整合门，不是 W7A graph validation 失败；唯一整合者仍须在 clean integration worktree 重新计算、审阅并按现有 L2/L3 路由处理，W7A 不在本分支批量 acknowledge 或改写 peer Session。
- `skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`：PASS。
- `scripts/ci/validate_repository_gates.py`：PASS。
- 隔离 `build_docsite.py`：PASS；1,832,086 bytes，14 ADR／6 State／7 subsystem／2 Snapshot／138 docs／24 Plans／7 Library；输出只写系统临时目录并在核对后删除，未改 `docs/_site/index.html`。
- Markdown local links 与 forbidden/generated-artifact 检查由 repository gate 覆盖；`git diff --check`：PASS。

## Synthetic fixture 边界

`tests/fixtures/workstream-relations/v1/succession-chain.json` 使用脱敏的 W5C → W6 → W5D → CI1 → W5E 形状；task IDs、OID 和 scope 都是合成值，不声称对应真实 Git 历史。临时仓库测试创建独立 commits／branches／linked worktree，只写其自身 `$GIT_COMMON_DIR`，不触碰本仓库私有 relation store。

## 未完成边界

- W7B 才可在新的 Approved Plan 下实现 automatic discovery、一次本机确认、batch apply／undo 和 legacy materialization；W7A 只冻结数据契约与显式 proposed append。
- W7C 才实现 Succession／Dependency／Conflict 三个派生视图、active-tip 高亮、历史折叠、Unknown 虚线和 accessible list；W7A 不提供正式图形页面或布局意见。
- relation apply 永不授权 worktree／branch／Validation／commit 删除；删除继续由 W6 maintenance 单独授权。
- 这不是通用 DAG scheduler，不负责模型选择、任务排程、Agent 启停、自动执行或云资源。
- 推广仍需唯一整合者冻结 exact Candidate SHA、推到非 `main` 分支并取得 GitHub `smoke-test (windows-latest)`／`smoke-test (ubuntu-latest)` 双 PASS；本分支没有 push、main merge、tag 或 Release。
