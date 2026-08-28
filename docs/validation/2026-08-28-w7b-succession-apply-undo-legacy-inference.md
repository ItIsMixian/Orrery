# Validation：W7B Succession Apply／Undo／Legacy Inference

Date: 2026-08-28

Status: Windows isolated full-loop／Fast／Checkpoint Candidate PASS；self-host real apply、Ubuntu exact-SHA Promotion、main merge 与 W7C-B UI 未执行

Fact scope: `codex/w7b-succession-apply-undo-legacy-inference`, exact parent/task base
`codex/w7a-dynamic-workstream-succession-contract@52e88b8e15788eb7b17161e61885e9198d29407c`

## 结论

W7B 在 W7A 冻结的 append-only relation graph/record 与 Git-private Session 语义上实现真实本机执行层。
自动发现只消费 exact local Session、完整 Session 字节 hash、`task_base_oid`、HEAD、Git ancestry、Scope
hash 与 lineage；名称、路径、目录和时间相似度只产生 Unknown/rejected reason，不会激活关系。

Batch plan 绑定 project/graph/discovery/candidate/source+target Session/HEAD/Scope/actor/expiry。Apply 和 undo
同时要求 exact plan ID/hash、一次性随机 confirmation token 与同一 `human-local` actor；伪造、重放、过期、
跨项目或任意 evidence drift 都在产品写入前失败关闭。中央 request 或 Agent 自述没有可映射的 actor kind。

Transaction 使用 Git-common-private write-ahead journal。全部输入先预检，非 terminal journal 会让普通 graph
读取失败关闭；成功 receipt 保存 W7A event/transition evidence、实际 event hash、原/新 Session hash、HEAD、
lifecycle/runtime/evidence/Scope/closure、actor、confirmation 和 resulting graph hash。故障恢复只恢复 exact
Session 或追加 `cancelled`/`stale` compensation，不删除历史、worktree、branch、commit、Validation 或作者文档。

## 隔离全闭环

`tests/test_workstream_relation_execution.py` 每次在系统临时目录创建脱敏本地 Git fixture：
W5C → W6 → W5D，并从 W5D 派生 late CI1 与 W5E sibling；显式 `W5E depends_on CI1` 形成多 predecessor。
fixture 不含真实源码、凭据、网络或真实项目 Git-private state。

覆盖面：

- exact legacy lineage、legacy no-lineage Unknown、late CI、explicit dependency、多 predecessor 与 similarity reject；
- ancestor、non-ancestor、parent post-fork、sibling、Unknown 及 W7A compare/suppress 邻接；
- waiting-for-user、paused、blocked-by-conflict、failed 排除和 active 正例；
- exact one-confirmation binding、伪造、重放、过期、跨项目、Session/HEAD/Scope/graph drift；
- 多 operation batch、event 2 后故障注入、pending journal graph block、partial recovery、重复 apply；
- completed takeover 原子 `closed/paused/superseded` invariant；
- exact receipt undo、undo drift reject、原 Session 字节恢复、append-only 历史保留；
- CLI `discover|plan|inspect|apply|undo|receipt` JSON/人类 surface、stable nonzero Unknown/blocked；
- author tree status unchanged、socket connect trap、no worktree/branch/commit/Validation/author delete surface。

最终命令：

```text
python -X utf8 -m unittest tests.test_workstream_relation_execution -v
```

结果：9/9 PASS，921.066s；更早一轮 8 项执行测试为 7 PASS＋1 fixture
断言错误，原因是 no-lineage session 仍携带 `lineage` mapping 但 `base_workstream_id=null`；修正 Unknown
判定后原失败单项 1/1 PASS。该历史未冒充最终通过。

## Fast／W7A／CI1

- `python -X utf8 scripts/ci/run_test_shard.py --profile fast --output <temp>`：49/49 PASS，runner
  2.128s；明确为 `non-promotion-feedback`。
- `python -X utf8 -m unittest tests.test_workstream_relations -v`：15/15 PASS，19.791s；保留 W7A
  three-relation、active-tip、completed predecessor、exact Git、post-fork/sibling、Unknown/L3、W7C consumer
  与 old builder compatibility。
- `python -X utf8 scripts/ci/test_inventory.py`：366 unique test IDs／26 shards／49 Fast，0 missing／duplicate。
- `python -X utf8 scripts/ci/validate_ci.py --all`：Fast role、Promotion completeness、exact-SHA binding 与
  fail-closed gates PASS。完整 W7B suite 只进入一个 `team-lan-core` Promotion shard；Fast 只运行 0.004s 的
  schema/CLI/no-delete dependency-light contract，避免把约十分钟隔离 Git loop 当普通 push latency。

## self-host 真实项目只读 dry-run

命令：

```text
python -X utf8 -m project_orrery_cli relations discover --target . \
  --recorded-at 2026-08-28T12:00:00Z --json
```

候选提交前、W7B Git-private Session 仍绑定 task-base HEAD 的快照结果为确定性非零 exit 5／warning：
8 proposed candidates、2 Unknown、0 similarity hints，graph hash
`5436d99493dc8f9bdba63ca25e9fb3a08467382ffff2f9ab59e842c235e12063`，discovery ID
`execution-discovery-b3d97812e1fcb193cbea4966`。前后 native relation store 均不存在，author status 完全一致，
`writes_performed=false`。候选提交后按要求把 W7B Session 刷新到 exact Candidate HEAD，因此 graph/session hash
按 evidence binding 正常变化；最终回执另报告该只读快照。没有生成 confirmation、journal、receipt，未改写任何
真实 peer Session。

## Checkpoint 与边界

Checkpoint 没有机械运行完整 Promotion；相邻面与结构门结果为：

- `python -X utf8 -m unittest tests.test_collaboration_contract -v`：27/27 PASS，141.443s；覆盖 W1/W2
  Session、Scope、zero-network 与 fail-closed 基础契约。
- `python -X utf8 -m unittest tests.test_collaboration_w3 -v`：13/13 PASS，345.620s；覆盖 review、closure、
  cleanup 独立授权与 zero-delete 邻接。
- `python -X utf8 -m unittest tests.test_collaboration_lineage -v`：2/2 PASS，52.096s；覆盖 W5C → W6 →
  W5D exact parent/lineage。
- `python -X utf8 -m unittest tests.test_ci_validation -v`：8/8 PASS，1.674s；覆盖 CI1 inventory、shards、
  exact-SHA 与聚合失败关闭。
- `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --json`：
  PASS，`integrated_candidate`，Core `0.1.14`／CLI `0.1.18`／Core API `1`。
- `python -X utf8 scripts/ci/validate_repository_gates.py`：PASS，637 repository paths、341 Markdown、943
  local links，无 forbidden runtime/generated artifact。
- `python -X utf8 -m py_compile ...` 与 `git diff --check`：PASS。
- `python -X utf8 scripts/docsite/build_docsite.py --docs <absolute docs> --agents <absolute AGENTS.md>
  --out <system temp>`：PASS，隔离生成 1,863,795-byte HTML；14 ADR、6 State、7 subsystem、2 snapshot、
  140 docs、25 plans、7 library，未改写 `docs/_site/`。首次用相对 `--docs` 的调用因构建器无法将相对路径
  映射到绝对 repository root 而失败，临时输出为空；改用绝对输入后通过，失败尝试未写仓库且未冒充通过。

本 Candidate 没有 push、main merge、branch-protection 变更、tag、Release 或网络调用。self-host 真实 apply
仍需维护者在成员本机针对当时 exact plan 单次确认，并需中央整合者另行授权；当前 dry-run 不能替代该授权。
Ubuntu 与 hosted exact-SHA required checks 仍由中央 Candidate-first Promotion 执行。
