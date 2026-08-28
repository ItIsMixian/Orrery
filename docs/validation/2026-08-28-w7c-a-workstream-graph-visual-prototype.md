# Validation：W7C-A Workstream Graph visual prototype

Date: 2026-08-28

Status: Worktree Candidate Fast／browser／repository／diff PASS；production Core wiring、Candidate/Promotion、push、main、tag 与 Release 未执行

Fact scope: `codex/w7c-a-workstream-graph-visual-prototype`，base `W5E-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

## 结论

W7C-A 在隔离 `experiments/workstream-graph-visual-prototype/` 建立可运行的无依赖 HTML／CSS／JS 原型。默认 Succession 只显示 active tip、继承主链、一层 same-base sibling 与一个三节点历史 cluster；Dependency 显示 W7C-B 的两个确认前驱和一个 Unknown；Conflict 显示一个带 path／validation evidence 的 synthetic `L3 / DIRECT` overlay，以及一个 proposed Semantic edge。节点、edge、history cluster、subsystem/status filter 与 inspector 可点击，SVG 项可由键盘 Enter／Space 选择；390px 下 SVG 降级提示，HTML ledger 成为单列主界面。

fixture 根级 `authority` 固定为 `provisional/non-authoritative`，所有 evidence kind 都是 synthetic／proposal／absence marker。这里的 `confirmed` 只表示合成场景内证据完整，不是生产项目 relation。原型没有导入 Core、读取真实 Workstream Session、连接 Team server 或写入默认 docsite／Skill／release surface。

## 产物

- `experiments/workstream-graph-visual-prototype/index.html`
- `experiments/workstream-graph-visual-prototype/styles.css`
- `experiments/workstream-graph-visual-prototype/prototype.js`
- `experiments/workstream-graph-visual-prototype/fixtures/workstream-graph.provisional.v1.json`
- `experiments/workstream-graph-visual-prototype/design-exploration.md`
- `tests/test_workstream_graph_visual_prototype.py`

## Fast → Checkpoint

- `python -X utf8 -m unittest tests.test_workstream_graph_visual_prototype -v`：6/6 PASS。
- `node --check experiments/workstream-graph-visual-prototype/prototype.js`：PASS。
- `python -X utf8 -m json.tool experiments/workstream-graph-visual-prototype/fixtures/workstream-graph.provisional.v1.json`：PASS。
- `python -X utf8 scripts/ci/validate_repository_gates.py`：PASS。
- `git diff --check`：PASS。

没有运行无关完整全仓、动态 docsite 或 Promotion；本任务按 Fast→Checkpoint 停止。

## 真实 in-app Chromium

Browser：Codex in-app Chromium；静态服务只绑定 `127.0.0.1:8127`。console warning/error 为 0，页面 script/link asset origin 只有 `http://127.0.0.1:8127`。

### Desktop 1280×720

- 初始 Succession 为 5 个显示节点／4 条边：history cluster、CI1、W5E、W7A sibling 与 W7C-A active tip；`document/body scrollWidth=1265＜1280`。
- Dependency 实际显示 `REQUIRED`、`REQUIRED`、`? UNKNOWN`，选择 `W7A → W7C-B` 后 inspector 展示 relation、certainty、direction、edge ID 与 synthetic evidence。
- Conflict 实际显示 `L3 / DIRECT` 与 `PROPOSED`；选择 confirmed edge 后 inspector 展示 `L3/direct`、synthetic path overlap 和 shared validation surface。
- Expand history 后显示节点从 5 增至 7，完整 `W5C → W6 → W5D → CI1 → W5E` 与 W7A／W7C-A 分叉可见。
- subsystem=`test-coverage`＋runtime=`active` 后只保留 W7A／W7C-A；Reset 恢复默认。SVG W7A 由键盘 Enter 选中并更新同一 inspector／live region。

### Mobile 390×844

- `document/body scrollWidth=375＜390`；filter 为两列，SVG 高 116px 且 pointer-events disabled，页面明确提示使用下方 mobile timeline。
- relation ledger 为 345.33px 单列；Dependency lens 在移动端点击后显示两个 confirmed predecessor 和一个 Unknown。
- 实际点击 ledger 的 `W7C-A → W7C-B` 后 selection kind 为 EDGE、inspector heading 正确、selected row ID 为 `dep-w7c-a-w7c-b`。

截图保存在 Codex visualizations 工作区而非 Git／发布包，并在任务交接中给出入口。

## W7A／W7C-B 边界

Design exploration 列出 W7A 需冻结的 stable identity、relation direction/kind、certainty/provenance、ordered multi-predecessor、evidence link、三状态轴、active tip、visibility/observability、cluster、ordering/version、failure 和 synthetic marker contract。W7C-B 仍需真实 Core projection、版本校验、安全 evidence link、Personal／Team visibility、provider fail-closed、生产测试和 Observatory/release 接线；本记录不把这些写成已实现。

提交前对 W7A Git-private status 的独立只读审计显示，两个 sibling Workstream 都声明写入 `docs/state/project-structure.md`、`docs/state/documentation-system.md`、`docs/state/test-coverage.md`、`docs/validation/README.md` 和 `docs/DEVLOG.md`，并共享 `git-diff-check` 验证面。该真实 Authority／validation overlap 必须由整合者合并；它没有进入 fixture、没有被页面读取，也不把页面 synthetic edge 升级为 Core finding。
