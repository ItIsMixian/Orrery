# 实施计划：CI3 Fast Validation Dependency Fix

Status: Completed; hosted acceptance passed and implementation is contained in Canonical main

Date: 2026-08-28

Fact scope: Candidate `codex/ci3-fast-validation-dependency-fix`，parent/task base
`codex/w7d-w7-integration-candidate@e2c049ebd6c6476eac8b9555e00edc046d673199`

Governing authority: [Product Seed](../../core/principles.md)、[Test Coverage State](../../state/test-coverage.md)、
[Release and Toolchain State](../../state/release-and-toolchain.md)、[CI2 Plan](2026-08-28-ci2-tiered-test-performance.md)、
[W7D Plan](2026-08-28-w7d-w7-integration-candidate.md)

## Goal and boundaries

Make the independent Fast workflow deterministic on fresh Windows and Ubuntu runners by installing the real final
unittest discovery/import dependencies before `validate_ci.py --all`. Keep Fast non-Promotion, keep its 15-second
test budget and existing selectors, and suppress only the secondary missing-artifact error when a prior step prevents
`fast-result.json` from being created.

This task does not change Promotion selection, required-check names, `ORRERY_TEST_BUILD`, product/Authority semantics,
component versions, branch protection, `main`, tags or Releases.

## Implementation and acceptance

1. Reuse the exact pinned-range wheel plus versioned docsite requirements install already proven by Promotion, with
   pip caching declared separately from test execution.
2. Extend the dependency-free workflow validator and unit regression so the install command must precede Fast
   contract validation.
3. Detect `fast-result.json` with setup Python under `always()` and upload only when present. A Fast runner failure
   still fails the job and uploads its real result; a pre-run failure no longer creates a second artifact root cause.
4. Run focused CI contracts, inventory, `validate_ci.py --all`, Fast, one Checkpoint attempt plus one bounded retry,
   integrated structure, repository gates and diff. Do not run local W7B Promotion or full repository Promotion.
5. Freeze one clean non-`main` SHA and require both independent Fast jobs plus both Promotion required checks on that
   same SHA. Hosted results are reported in the task receipt rather than creating a docs-only SHA loop.
