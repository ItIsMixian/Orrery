# Validation: CI6 Local Validation Router & Tier Enforcement

Date: 2026-08-29
Status: local Candidate PASS; Promotion-only suite intentionally not run
Fact scope: Worktree Candidate `codex/ci6-local-validation-router-tier-enforcement`, based on exact W6.1
`e28144d3bd000c00c9f96c8b2cb36979f42d287e`.

## Generic controls

- Machine inventory: 397 unique exact unittest IDs, 27 complete Promotion shards and ten complete physical lanes;
  81 global Fast and 82 global Checkpoint IDs. Every entry has owner surface/shard, allowed stages, cost class,
  budget, generic dependencies and a reason. The manifest contains no wildcard selector policy.
- Production `scripts/ci` Python/config/guide files contain no W6.1 task ID, source branch or fixed portfolio switch.
  The only 24-ID W6.1 list is test data in `tests/fixtures/ci-validation/change-portfolios-v1.json`.
- Synthetic docs-only, Authority/Core schema+CLI and collaboration/maintenance portfolios all route through the
  same Git path + Workstream subsystem/expected-write algorithm. Required tests were selected; Promotion-only
  forbidden IDs were absent; no portfolio required a Python algorithm change.
- Mutations for a newly discovered but unregistered test, duplicate exact entry, stale/dead ID, owner mismatch,
  unmapped path, Unknown dependency and heavy lower-stage admission all failed closed. The unmapped-path CLI case
  emitted `orrery-local-validation-refusal-v1`, `evidence_eligible=false`, and named the required
  `path_mappings` metadata.
- `scripts/ci/README.md` documents the normal extension cost: one exact test entry for a new test, and one reusable
  path mapping only for a genuinely new Adapter/release/UI surface. No per-task selector redesign is required.

## W6.1 regression case

- The original direct suite remains a fixture-only 24-ID regression portfolio. The schema/policy contract and pure
  maintenance renderer are lower-tier; 22 original heavy IDs remain Promotion-only and exactly-once. The
  new minimal Checkpoint helper is additional evidence rather than a replacement claim.
- The W6.1 synthetic diff selects fewer than all 24 IDs and excludes real linked-worktree deletion. Two focused W3
  cleanup adjacency IDs, full W3, real deletion/lock/recovery, remaining Personal and all Team server journeys stay
  Promotion-only and were not executed locally.
- Generic acceptance would fail if any production task/branch-specific branch were introduced; W6.1 does not own or
  alter the router algorithm.

## Local results

| Check | Result |
| --- | --- |
| focused generic portfolio/contract/mutation debug suite | 23/23 PASS in 8.784s; direct unittest, not tier evidence |
| prior formal routed Fast at `e5ee31c418fa4d2d81f3df792f683064a0a9c5d0` | 26/26 PASS in 8.882428s / 15s |
| prior formal routed Checkpoint at `e5ee31c418fa4d2d81f3df792f683064a0a9c5d0` | 27/27 PASS in 73.357672s / 90s |
| `validate_ci.py --all` | PASS |
| inventory validation | PASS; 397 IDs / 27 shards / 10 lanes |
| integrated structure | PASS; integrated Candidate, Authority Model 1 strict eligible |
| repository links/forbidden artifacts | PASS; 682 paths / 368 Markdown / 917 links |
| `git diff --check` | PASS; only a line-ending advisory for the manifest working copy |

Three earlier Checkpoint attempts failed closed inside the new test at 51.601s, 66.457s and 70.636s while aligning
the test with existing public trigger/signature/return-field contracts. None timed out, removed a worktree or produced
valid tier evidence. Their failure receipts remain Git-private history; only the final PASS may be cited.

One generic-registry Checkpoint at `dc27c2095926f024a315505bbbc84b3ab75711fa` timed out and failed closed after
92.134014s because seven unrelated Workstream-relation medium journeys shared the coarse collaboration dependency.
Their data-only `allowed_stages` metadata was corrected to Promotion; the revised current-diff Checkpoint contains
exactly one medium test, the minimal-Git incremental refresh plus target-only preflight helper.

## Receipt and reuse boundary

The routed receipts bind HEAD/base, dirty fingerprint, manifest/mapping-registry/inventory hashes, selected IDs, test
source, selector/dependency and relevant-tree hashes, stage/budget, OS/Python/environment, outcome/duration, slowest IDs and
runner errors. Dry-runs are explicitly `evidence_eligible=false`; missing, interrupted, timed-out, failed or
over-budget runs return nonzero.

Reuse status is `contract-refusal` v1, not implemented reuse. The key includes all required source/dependency/tree,
runtime, schema/runner/manifest/registry and environment dimensions. Security-sensitive CI or collaboration changes
and dirty mismatches independently refuse reuse; Unknown paths/dependencies refuse the selection itself, and
reuse is refused for multiple independent reasons. Promotion always remains a complete fresh run.

## Evidence limits and central handoff

No 549-second W6.1 module rerun, complete local Promotion, hosted matrix, push, main integration, tag, Release,
component-version change, branch-protection change or UI/product switch occurred. The central integrator must merge
after concurrent `A3`, `SH1`, `U1` and `github-front-door` ownership is reconciled, project shared State/DEVLOG/index
facts once, then freeze and push the exact non-main Candidate SHA for Windows/Ubuntu Promotion.
