# 2026-08-28 CI2 分级测试性能收口

Scope: Worktree Candidate `codex/ci2-tiered-test-performance`，parent/task base
`codex/w7b-succession-apply-undo-legacy-inference@1160df40e04e7c5ae83a6dc88164babad85fd36a`。

## Why

W7B 的原始最终模块为 9/9 PASS，但耗时 921.066 秒。静态审计证明九个测试共建立九套 fixture；每套又经
W1 的完整生产 `create_worktree` 接受路径建立 sanitized relation topology。该重复验证与 W7B 的
transaction／undo claim 不成比例，且普通 Checkpoint 不应为统一计数重跑完整 Promotion。

## Implemented test boundary

- dependency-light Fast：schema、CLI surface、no-delete／no-network source contract，不创建 Git fixture；
- minimal-Git Checkpoint：W5C→W5D→W5E，验证真实 Session／HEAD／Scope binding、四种非 active state、
  confirmation 伪造、Session drift、expiry 与 cross-project 拒绝；
- full Promotion journey A：完整 W5C→W6→W5D→CI1/W5E，覆盖 legacy/no-lineage、similarity reject、late CI、
  sibling/post-fork、CLI plan/apply/receipt/undo、completed predecessor、replay、history、author clean 与 zero network；
- full Promotion journey B：同一完整拓扑覆盖 multi-operation failure、blocked graph、journal recovery、补偿历史、
  post-recovery apply 与 undo drift 拒绝。

W7B fixture 使用 bounded local `git worktree add` 建立所需拓扑，再写真实 Git-private Session。W1 的
production create/rollback acceptance 继续由 W1 tests 独立拥有；本次没有用 mock 替代 W7B 所声称的真实
Git ancestry、private storage 或 transaction behavior。

## Results

```text
python -X utf8 -m unittest tests.test_ci_validation -v
9/9 PASS, 1.725s

python -X utf8 scripts/ci/test_inventory.py
362 unique IDs / 27 Promotion shards / 49 Fast / 66 Checkpoint

python -X utf8 scripts/ci/validate_ci.py --all
PASS

python -X utf8 scripts/ci/run_test_shard.py --profile fast --output <temp>
49/49 PASS, 2.116887s <= 15s

python -X utf8 scripts/ci/run_test_shard.py --profile checkpoint --output <temp>
66/66 PASS, 83.628564s <= 90s

python -X utf8 scripts/ci/run_test_shard.py --shard team-relations-execution --output <temp>
4/4 PASS, 264.737873s <= 300s
```

The optimized W7B Promotion duration is 656.328 seconds lower than the recorded 921.066-second baseline, about a
71% reduction. The runner fails the selected profile/shard if its declared hard budget is exceeded.

## Evidence limits

- Results are local Windows Worktree measurements. The JSON runner records the current Git HEAD, but this run occurred
  before Candidate closeout while tracked changes were present; it is not represented as a clean exact-SHA Promotion.
- No complete repository Promotion, hosted Windows/Ubuntu matrix, push, main merge, branch-protection change, tag or
  Release occurred.
- Promotion completeness and required-check authority are unchanged. A central integrator must still freeze and push
  the exact Candidate SHA before hosted evidence can become Canonical.
- This Candidate does not implement cross-SHA result reuse or a persistent evidence cache; it removes the immediate
  repeated-topology cost without introducing stale-pass risk.
