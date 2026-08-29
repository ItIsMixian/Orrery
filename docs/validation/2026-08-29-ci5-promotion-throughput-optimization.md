# Validation: CI5 Promotion Throughput Optimization

Date: 2026-08-29

Status: Worktree Candidate local validation PASS; exact-SHA hosted Fast／Promotion pending

Fact scope: `codex/ci5-promotion-throughput`, based on Canonical
`main@a4b0ed333b1e1ad001610c74b77f6e09da639301`.

## Baseline diagnosis

CI4 exact-SHA Promotion run `33233029211` was 59/59 jobs PASS. Its 54 shard jobs consumed 39.1 aggregate
job-minutes: 15.0 minutes of test steps and 24.0 minutes of setup／checkout／install／verification／artifact overhead,
so overhead was 61.6%. Dependency installation alone consumed 11.7 minutes. The preceding three successful
Promotion runs recorded 62.4–63.6% overhead, confirming a structural orchestration cost rather than one slow run.

The clean CI4 Checkpoint baseline ran all 78 assertions successfully in 164.741828 seconds and therefore correctly
failed its unchanged 90-second budget. The single
`test_minimal_git_binding_rejections_and_state_axes_checkpoint` journey consumed 120.961576 seconds. It remains in
the complete `team-relations-execution` Promotion shard; only its duplicate non-Promotion Checkpoint execution was
removed.

## Implemented boundary

- Manifest schema 3 retains 27 logical Promotion shards and adds ten explicit physical lanes. Every shard belongs to
  exactly one lane; unknown, missing, duplicate and empty assignments fail closed; the 300-second W7B execution shard
  remains isolated.
- `run_test_lane.py` invokes the existing logical shard runner in a new Python subprocess for every member. It
  continues after a failed member, preserves every shard JSON, emits a separate lane receipt and returns nonzero when
  any member fails or lacks a valid result.
- Aggregate validation still proves every final unittest ID exactly once and now additionally requires all ten lane
  receipts with exact SHA／OS／manifest／ordered-shard bindings.
- Windows and Ubuntu lane/gate waves independently depend on the same preflight. Ten lanes per OS allow at most 20
  concurrent lane jobs. Required check names and OS-specific aggregate ownership are unchanged.
- Superseded Fast runs on the same source branch may cancel each other. Promotion runs are never cancellation-based
  reusable evidence.
- No product, component, Adapter, Authority, protocol, branch-protection, tag or Release behavior changed.

## Local evidence

| Check | Result |
| --- | --- |
| CI contract and mutation tests | 17/17 PASS |
| inventory／lane validation | 390 unique IDs／27 logical shards／10 lanes／57 Fast／81 Checkpoint; zero missing, duplicate or dead selector |
| `validate_ci.py --all` | PASS |
| final Fast profile | 57/57 PASS, 3.235952s／15s |
| first post-rebalance Checkpoint | 80/80 PASS, 41.697448s／90s |
| final Checkpoint attempts | 81/81 PASS at 42.806990s and 43.071302s／90s |
| real physical `lane-05` | 3/3 logical shards PASS; 360.367095s local Worktree measurement |
| integrated installation | PASS; `integrated_candidate`, Authority Model 1 supported |
| isolated docsite | PASS; 2,040 KB, 157 documents, 31 plans |
| repository gates | PASS; 667 paths／360 Markdown／1010 links, no forbidden artifacts |
| release package dry build | PASS; historical v0.2.0 ZIP and checksum emitted only to system temp |
| workflow YAML syntax | PASS for Fast and Promotion workflows |
| Python compile and `git diff --check` | PASS |

The real lane run produced three independent shard receipts plus one lane receipt. Local W3 fixture contention made
that run slower than historical hosted data; this does not alter shard budgets or justify retries. Hosted wall time
remains an advisory observation because runner queue and host load are external variables.

A complete local Promotion is intentionally not repeated: the new execution topology itself must be accepted by one
clean exact-SHA hosted Windows／Ubuntu run.

## Hosted acceptance and stop boundary

The final clean Candidate must first obtain independent Fast Windows／Ubuntu PASS. It must then be pushed to a frozen
non-`main` `promotion/**` ref and obtain all 25 expected Promotion jobs, both repository gates and required
`smoke-test (windows-latest)`／`smoke-test (ubuntu-latest)` PASS on the same exact SHA. Aggregation must still report
all 27 logical shards and every discovered test exactly once per OS.

Hosted evidence will report wall time, total shard/lane job-minutes, test-step time and overhead in the task receipt;
it will not create a docs-only successor SHA. Targets are no more than 27 total jobs, less than 30 lane job-minutes
and less than 45% lane-job overhead. Missing a performance target is evidence for follow-up, not permission to hide
a test failure, relax a safety budget or rerun until green.

This Workstream does not advance `main`, modify branch protection, select impact-based partial Promotion, publish a
Release or delete prior branches／worktrees／evidence.
