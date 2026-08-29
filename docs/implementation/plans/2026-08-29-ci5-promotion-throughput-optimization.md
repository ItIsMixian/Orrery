# Implementation Plan: CI5 Promotion Throughput Optimization

Status: Completed; exact-SHA hosted acceptance passed and source integrated into Canonical main

Date: 2026-08-29

Fact scope: Worktree `codex/ci5-promotion-throughput`, based on Canonical
`main@a4b0ed333b1e1ad001610c74b77f6e09da639301` after CI4 exact-SHA Fast and Promotion acceptance.

Governing authority: [Orrery Product Seed](../../core/principles.md), especially principle 11;
[Test Coverage State](../../state/test-coverage.md); [CI2 tiered performance](2026-08-28-ci2-tiered-test-performance.md);
[CI3 Fast dependency fix](2026-08-28-ci3-fast-validation-dependency-fix.md).

## Problem and measured baseline

CI4 Promotion run `33233029211` completed successfully with 386 unique unittest IDs, 27 logical shards,
Windows／Ubuntu required checks and 59 total jobs. The run consumed 41.5 aggregate job-minutes and 8.3 wall-clock
minutes. Across its 54 shard jobs, test execution consumed 15.0 minutes while checkout, Python setup, dependency
installation, exact-SHA verification and artifact handling consumed 24.0 minutes, or 61.6% of shard-job time.
Dependency installation alone consumed 11.7 minutes. The preceding three successful runs showed the same structural
overhead at 62.4–63.6%, so this is not a single-run anomaly.

The CI4 Checkpoint baseline executed all 78 selected assertions successfully but failed its unchanged 90-second hard
budget at 164.741828 seconds. One Promotion-owned minimal Git binding journey consumed 120.961576 seconds; the other
77 Checkpoint tests consumed about 44 seconds. The correct repair is to restore the staged feedback boundary, not to
raise the budget or remove the journey from Promotion.

## Invariants

CI5 must preserve:

- every discovered final unittest ID exactly once per Promotion OS;
- the 27 logical shard identities, surfaces, selectors and per-shard budgets;
- exact non-`main` Candidate SHA binding;
- Windows and Ubuntu execution with `ORRERY_TEST_BUILD=1`;
- fail-closed aggregation for missing, duplicate, extra, failed, cancelled or drifted evidence;
- required check names `smoke-test (windows-latest)` and `smoke-test (ubuntu-latest)`;
- the 15-second Fast and 90-second Checkpoint hard budgets;
- the 300-second `team-relations-execution` Promotion budget;
- repository structure, docsite, links／forbidden artifacts, package and diff gates.

CI5 does not introduce impact-based partial Promotion, cross-SHA result reuse, nightly-only safety coverage, product
changes, component version changes, branch-protection changes, tags or Releases. Those would require a separate
decision after this no-coverage-loss optimization is measured.

## Implementation

1. Upgrade the internal shard manifest with an explicit physical Promotion lane map. Every logical shard must belong
   to exactly one lane; every lane must be non-empty; `team-relations-execution` remains alone. Ten deterministic
   lanes are based on the maximum observed shard duration across the last four successful Promotion runs.
2. Add a batch lane runner that invokes the existing shard runner in a fresh Python subprocess for every logical
   shard. It must continue after a failed shard, retain each independent shard result, emit a lane receipt, and return
   nonzero if any shard fails or lacks a result. Logical budget and evidence semantics remain owned by the existing
   shard runner.
3. Change Promotion matrices from 27 shard jobs per OS to ten lane jobs per OS. Each lane performs checkout and
   dependency installation once, uploads all constituent shard results, and leaves aggregate validation at the
   logical-shard/test-ID level.
4. Allow Windows and Ubuntu lanes and repository gates to start independently after the same successful preflight.
   Their required aggregate jobs remain OS-specific and unchanged in name.
5. Add cancellation only for superseded non-Promotion Fast runs on the same source branch, and exclude frozen
   `promotion/**` pushes after the same SHA has passed ordinary-branch Fast. Promotion runs remain uncancelled evidence
   attempts and execute the complete inventory.
6. Remove only
   `test_minimal_git_binding_rejections_and_state_axes_checkpoint` from the Checkpoint selector. It remains in the
   dedicated complete Promotion shard. Do not change the Checkpoint budget.
7. Extend dependency-free static validation and mutation tests for manifest lanes, lane completeness, subprocess
   isolation, continue-and-fail behavior, workflow parallelism, artifact collection and unchanged required checks.

## Initial lane packing

- `lane-01`: `team-relations-execution`
- `lane-02`: `context-benchmark`, `team-lan-harness`
- `lane-03`: `w3-a`, `packaging-project`
- `lane-04`: `team-lan-core`, `workspace-observatory`, `workspace-cli`
- `lane-05`: `w3-c`, `team-ui-server`, `release-restore`
- `lane-06`: `workspace-queue`, `workspace-action`, `release-migrate`
- `lane-07`: `w3-b`, `context-oracle`, `workspace-scan`
- `lane-08`: `context-harness`, `packaging-adapters`, `team-personal-b`
- `lane-09`: `w1-w2-b`, `authority-core`, `team-personal-a`
- `lane-10`: `w1-w2-a`, `workspace-remove`, `team-personal-c`, `workspace-contract`

The first lane is deliberately heavy and isolated. The other nine had estimated worst observed test-step sums of
85–90 seconds before per-job setup. These estimates are planning inputs, not authority facts or runtime guarantees.

## Acceptance

- focused CI contract and mutation tests pass;
- inventory reports the complete CI5-base test set, 27 logical shards and 10 complete lanes with zero missing,
  duplicate or dead selector;
- Fast remains within 15 seconds;
- Checkpoint passes twice within 90 seconds without budget relaxation;
- integrated installation, repository gates and `git diff --check` pass;
- one clean non-`main` exact SHA obtains Fast Windows／Ubuntu PASS and Promotion Windows／Ubuntu required PASS;
- hosted evidence records total jobs, wall time, shard-job test time and setup overhead. Targets are no more than 27
  total jobs, less than 30 shard job-minutes and less than 45% shard-job overhead; hosted queue-dependent wall time is
  advisory and must not be turned into a flaky hard gate.

After implementation, update Test Coverage State, Validation, DEVLOG and indexes on this Workstream. Root
PROGRESS/HANDOFF remain for the later unique integrator and are not continuously rewritten here.

## Completion

Exact SHA `9ee831f0d6f64306fe821f8c70229df54648d3eb` passed Fast run `33235942078` and
Promotion run `33235992711`. Promotion completed 25/25 jobs; both required OS aggregates passed with
390 tests across 27 logical shards. The 20 lane jobs consumed 23.9 job-minutes, with 14.352 minutes in
lane test execution and about 40% derived overhead. The same SHA was then fast-forwarded to protected
`main`; main Fast run `33236225082` passed. No tag or Release was created.
