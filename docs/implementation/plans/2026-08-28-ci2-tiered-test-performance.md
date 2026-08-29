# 实施计划：CI2 分级测试性能收口

Status: Completed; implementation is contained in Canonical W7/CI5 descendants

Date: 2026-08-28

Fact scope: Candidate `codex/ci2-tiered-test-performance`，parent/task base
`codex/w7b-succession-apply-undo-legacy-inference@1160df40e04e7c5ae83a6dc88164babad85fd36a`

Governing policy: [Product Seed](../../core/principles.md)、[CI1 tiered validation](2026-08-27-ci1-tiered-parallel-validation.md)、[W7B Plan](2026-08-28-w7b-succession-apply-undo-legacy-inference.md)

## Goal and non-goals

Preserve W7B's discovery／plan／confirmation／transaction／recovery／undo requirements while moving each claim to
the cheapest adequate validation layer. Daily feedback must not rebuild the full sanitized Git topology merely to
produce one aggregate pass count.

This Candidate does not weaken Promotion completeness, change required-check authority, modify branch protection,
merge or push, or treat cached/self-reported results as evidence. Any reusable result must remain bound to exact
source and test inputs; the initial implementation focuses on cheaper fixtures and explicit duration budgets rather
than introducing a persistent evidence cache.

## Test architecture

1. Keep schema, CLI surface, state-axis, hash-binding and rejection rules dependency-light where real Git behavior is
   not the claim under test.
2. Use minimal Git fixtures for ancestry, Git-private Session and path behavior. Do not route fixture setup through
   the full production `worktree create` acceptance path unless that path itself is the subject under test.
3. Retain at most two full sanitized W5C → W6 → W5D → CI1/W5E Promotion scenarios:
   - normal discovery → plan → apply → receipt → undo／CLI journey;
   - failure injection → blocked graph → recovery plus drift/replay rejection.
4. Fast remains non-Promotion and targets no more than 15 seconds locally. Checkpoint covers the changed subsystem and
   direct adjacency with a 90-second target. Full W7B isolation belongs only to Promotion and targets five minutes per
   platform.
5. Record per-test and per-shard durations. Budget violations must be visible and fail closed where the selected
   profile declares a hard budget; ordinary Checkpoint must never launch Promotion implicitly.

## Implementation sequence

1. Measure the existing W7B fixture construction and map every current assertion to dependency-light, minimal-Git or
   full-topology evidence.
2. Replace repeated heavyweight setup with a dedicated W7B topology builder that uses bounded raw local Git setup and
   Git-private Session writes; consolidate mutation journeys without hiding individual claim failures.
3. Extend CI1's manifest/runner contract with an explicit Checkpoint profile and profile budgets while retaining the
   exact once-only Promotion inventory.
4. Update tests, inventory/shards and subsystem documentation; run Fast, Checkpoint, then one optimized Promotion
   execution and compare against W7B's recorded 9/9 in 921.066 seconds.

## Acceptance

- W7B coverage remains explicit for legacy/late-CI/multi-predecessor discovery, ancestry variants, non-active states,
  exact confirmation rejection, atomic recovery, completed takeover, replay, receipt, undo, history, CLI, zero
  network and no-delete behavior.
- Full-topology construction count is at most two per Promotion run.
- Fast <= 15 seconds and Checkpoint <= 90 seconds on the local Windows Candidate host.
- Optimized W7B Promotion <= 300 seconds locally, or the Candidate stops with measured hotspots instead of claiming
  success.
- CI inventory remains complete and once-only; Fast/Checkpoint remain strict non-Promotion subsets.
- Only subsystem State, Validation, DEVLOG and indexes are updated; root PROGRESS/HANDOFF remain integrator-owned.

## Completed Candidate result

- W7B execution coverage is now four tests: one dependency-light Fast contract, one minimal-Git Checkpoint and two
  full sanitized Promotion journeys. The latter are the only tests that construct the complete W5C → W6 → W5D →
  CI1/W5E topology.
- The fixture no longer routes W7B setup through W1's production `worktree create` acceptance path. It uses bounded
  local `git worktree add` plus real Git-private Session writes, so W1 retains ownership of create/rollback behavior
  while W7B still exercises real ancestry, worktree metadata and transaction storage.
- Manifest schema 2 adds explicit Fast／Checkpoint roles and hard budgets. W7B has a dedicated
  `team-relations-execution` Promotion shard with a 300-second budget; Promotion inventory remains complete and
  once-only.
- Local Windows Worktree results: Fast 49/49 in 2.117s, Checkpoint 66/66 in 83.629s, optimized W7B Promotion 4/4 in
  264.738s. The old W7B run was 9/9 in 921.066s, so the full execution suite fell by about 71% while keeping the
  enumerated safety claims.
- These are local dirty-Worktree measurements bound to the recorded implementation state, not hosted exact-SHA
  Promotion evidence. Candidate-first Windows／Ubuntu execution remains an integration responsibility.
