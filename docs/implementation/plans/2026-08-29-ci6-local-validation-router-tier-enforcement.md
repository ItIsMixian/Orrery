# CI6 Local Validation Router & Tier Enforcement Implementation Plan

Date: 2026-08-29
Status: Candidate implemented and locally validated; exact-SHA Promotion remains central integration work
Workstream: `CI6-local-validation-router-tier-enforcement`
Branch: `codex/ci6-local-validation-router-tier-enforcement`
Base/lineage: `W6.1-incremental-maintenance-quick-remove@e28144d3bd000c00c9f96c8b2cb36979f42d287e`
Governing policy: [Product Seed](../../core/principles.md), [Test Coverage State](../../state/test-coverage.md), [CI2 tiering](2026-08-28-ci2-tiered-test-performance.md), [CI5 throughput](2026-08-29-ci5-promotion-throughput-optimization.md), [W6.1 Plan](2026-08-29-w6-1-incremental-maintenance-quick-remove.md)

## Problem and boundary

CI Fast/Checkpoint/Promotion were effective, but a local Agent could run arbitrary `python -m unittest <modules>` and
describe the result as tier evidence without selector, budget or receipt enforcement. W6.1 exposed the consequence:
its direct 24-test maintenance/Personal/Team module run passed in 549.237 seconds, while the old seven maintenance
tests alone retained expensive real-Git topology, deletion, lock and recovery claims.

CI6 adds one repository-local Agent entry, `python scripts/ci/validate_change.py`, without changing product behavior,
W6.1 cache/Quick Remove semantics, component versions, workflows, required checks, branch protection or public release.
Direct unittest remains available for debugging but is not a Fast/Checkpoint completion receipt.

## Implemented architecture

1. Manifest schema 5 keeps only complete Promotion discovery, 27 logical shards and ten lanes. The separate
   machine-readable `scripts/ci/change-mapping.json` registry owns generic path/subsystem mappings, exact test
   ownership, allowed stages, cost classes, dependencies/reasons, stage budgets and the conservative reuse contract.
2. The router derives changed paths from Git, the exact base from an explicit ref or Git-private Workstream lineage,
   and primary/affected subsystem plus expected-write scope from the private session. Dry-run receipts explain
   path/scope → generic mapping → surface → final test ID → tier/cost/reason. Concrete changed or expected-write
   paths take precedence; Workstream subsystem metadata is the conservative fallback when no path scope exists.
3. The generated machine inventory gives every discovered final unittest ID exactly one owner surface/shard plus
   allowed stages, cost class, budget and dependency/adjacency reasons. Unregistered or stale IDs, duplicate
   ownership, unmapped paths, Unknown dependencies, incomplete Promotion and heavy lower-tier selection fail
   statically. Adding a test normally costs one exact registry entry; Adapter, release and UI surfaces extend by
   data-only mapping entries without changing router algorithms.
4. `run_test_shard.py` emits versioned receipts bound to exact HEAD/base, dirty fingerprint, manifest/inventory,
   selected IDs, test source, selector/dependency and relevant-tree hashes, OS/Python/environment, stage/budget,
   per-test outcomes/durations and runner errors. Timeout/interruption/missing result cannot become evidence.
5. Over-budget output records the five slowest IDs and directs heavy journeys to inventory-declared Promotion rather
   than allowing an ordinary specialized pass claim.
6. Reuse is intentionally `contract-refusal` v1. It computes the complete conservative key and rejects dirty,
   Unknown, changed-dependency and security-sensitive cases; no cached result is consumed or presented as evidence.

## Generic controls

- Production router/config/selector code has no task ID, branch name or fixed change-diff switch. A static mutation
  test scans every production CI Python/config/guide file for such switches.
- Synthetic docs-only, Authority/Core schema+CLI and collaboration/maintenance portfolios exercise the same
  path/subsystem/expected-write algorithm. Unregistered tests, duplicate entries, unmapped paths, Unknown
  dependencies, stale IDs and heavy lower-stage mutation all refuse formal evidence with missing-metadata guidance.
- The registry extension guide makes future Adapter/release/UI work a data maintenance operation; router code is
  changed only when the versioned generic contract itself changes.

## W6.1 regression portfolio

- Fast owns cache/schema/policy/fingerprint and pure maintenance rendering plus zero-network/static compatibility
  contracts. It creates no full maintenance topology.
- Checkpoint adds one new helper test that uses one real temporary Git fixture for one incremental refresh and one
  target-only Quick Remove preflight. It performs no deletion and keeps the 90-second budget.
- Promotion uniquely retains the original heavy cache invalidation, real linked-worktree removal, lock/recovery,
  CLI/live server and remaining Personal/Team journeys. Two W3 cleanup adjacency claims are also explicit
  Promotion-only inventory members.

This split is a test fixture regression portfolio only. No production router, manifest or mapping-registry branch
names W6.1, its Workstream, or its source branch.

The only W6.1 test-file change is
`tests/test_workspace_maintenance.py::test_minimal_git_incremental_refresh_and_target_preflight_checkpoint`; it adds a
tier-friendly helper without changing or deleting any existing assertion.

## Acceptance and integration

- W6.1 diff routing selects fewer than the complete original 24 tests at Fast and Checkpoint.
- Fast is below 15 seconds and Checkpoint below 90 seconds on the local Windows Candidate host.
- CI contract/mutation tests prove generic inventory completeness, data-only extensibility,
  required-check/workflow stability and Promotion-only regression coverage.
- Integrated structure, repository link/forbidden-artifact gate and `git diff --check` pass.
- No local full Promotion is run. Central integration must run the exact pushed Candidate SHA on Windows and Ubuntu
  before any promotion to `main`.

Shared State, DEVLOG, Implementation/Validation indexes, root PROGRESS and HANDOFF remain integrator-owned for this
concurrent line.
