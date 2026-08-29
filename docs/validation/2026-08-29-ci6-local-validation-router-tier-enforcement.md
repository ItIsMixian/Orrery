# Validation: CI6 Local Validation Router & Tier Enforcement

Date: 2026-08-29
Status: local Candidate PASS; Promotion-only suite intentionally not run
Fact scope: Worktree Candidate `codex/ci6-local-validation-router-tier-enforcement`, based on exact W6.1
`e28144d3bd000c00c9f96c8b2cb36979f42d287e`.

## Inventory and selection evidence

- Machine inventory: 395 unique final unittest IDs, 27 complete Promotion shards and ten complete physical lanes;
  79 global Fast and 87 global Checkpoint IDs. Every entry has owner surface/shard, allowed stages, cost class,
  budget and dependency/adjacency reasons.
- W6.1 original direct suite is frozen as a 24-ID claim set. The schema/policy contract and pure maintenance renderer
  are lower-tier; 22 original heavy IDs remain Promotion-only and exactly-once. The new minimal Checkpoint helper is
  additional evidence rather than a replacement claim.
- Two focused W3 cleanup adjacency IDs remain Promotion-only. Full W3, real deletion/lock/recovery, remaining
  Personal and all Team server journeys were not executed locally.
- Dry-run against `d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2..HEAD` selected 26 Fast IDs and 27
  Checkpoint IDs. Neither selection contained
  `test_remove_worktree_executor_preserves_branch_commit_and_receipt` or the complete original 24-item suite.

## Local results

| Check | Result |
| --- | --- |
| focused CI contract/mutation debug suite | 21/21 PASS in 6.393s; direct unittest, not tier evidence |
| formal routed Fast | 26/26 PASS in 8.677261s / 15s |
| formal routed Checkpoint | 27/27 PASS in 71.288271s / 90s |
| `validate_ci.py --all` | PASS |
| inventory validation | PASS; 395 IDs / 27 shards / 10 lanes |
| integrated structure | PASS; integrated Candidate, Authority Model 1 strict eligible |
| repository links/forbidden artifacts | PASS; 677 paths / 365 Markdown / 912 links |
| `git diff --check` | PASS; only a line-ending advisory for the JSON working copy |

Three earlier Checkpoint attempts failed closed inside the new test at 51.601s, 66.457s and 70.636s while aligning
the test with existing public trigger/signature/return-field contracts. None timed out, removed a worktree or produced
valid tier evidence. Their failure receipts remain Git-private history; only the final PASS may be cited.

## Receipt and reuse boundary

The routed receipts bind HEAD/base, dirty fingerprint, manifest/inventory, selected IDs, test source,
selector/dependency and relevant-tree hashes, stage/budget, OS/Python/environment, outcome/duration, slowest IDs and
runner errors. Dry-runs are explicitly `evidence_eligible=false`; missing, interrupted, timed-out, failed or
over-budget runs return nonzero.

Reuse status is `contract-refusal` v1, not implemented reuse. The key includes all required source/dependency/tree,
runtime, schema/runner/manifest and environment dimensions. The W6.1/CI6 diff is dirty and security-sensitive, so
reuse is refused for multiple independent reasons. Promotion always remains a complete fresh run.

## Evidence limits and central handoff

No 549-second W6.1 module rerun, complete local Promotion, hosted matrix, push, main integration, tag, Release,
component-version change, branch-protection change or UI/product switch occurred. The central integrator must merge
after concurrent `A3`, `SH1`, `U1` and `github-front-door` ownership is reconciled, project shared State/DEVLOG/index
facts once, then freeze and push the exact non-main Candidate SHA for Windows/Ubuntu Promotion.
