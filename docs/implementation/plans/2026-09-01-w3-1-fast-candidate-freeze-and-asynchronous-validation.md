# Implementation Plan: W3.1 Fast Candidate Freeze and Asynchronous Validation

Status: Approved for implementation

Date: 2026-09-01

Task code: W3.1

Program path: `workstream-w`

Primary subsystem: `multi-worktree-collaboration`

Affected subsystems: `test-coverage`, `documentation-system`

Governing decision: [ADR-0030](../../decisions/0030-fast-candidate-freeze-and-asynchronous-validation.md)

Approved Design: [Fast Candidate Freeze and Asynchronous Validation Closeout](../../design/fast-candidate-freeze-and-asynchronous-validation.md)

## Objective

Make accepted implementation tasks stop quickly by freezing one clean exact Candidate in under 30 seconds, while
moving time-consuming validation to an immutable-SHA asynchronous stage without weakening integration/release gates.

## Phase A — freeze contract and command

1. Register W3.1 on an independent branch/worktree from the exact task-description version. Acknowledge scope before
   product writes; do not modify active W7.4/U2.5/W7.5 product worktrees.
2. Add Core schema/validation for `candidate-freeze-receipt-v1` and the independent Candidate lifecycle states.
3. Implement CLI dry-run and apply for `worktree freeze-candidate` using existing session/scope/status/expected-write
   providers. Dry-run is zero-write; apply stages expected paths, creates one commit and atomically records the receipt.
4. Bind maintainer acceptance to an exact relevant-tree/surface fingerprint. Any changed product byte refuses freeze.
5. Implement only bounded structural checks from the Design. Instrument elapsed time and prove no test runner,
   temporary Git fixture, site/package build or provider scan is invoked.
6. Add Personal/maintenance status projection for `候选已冻结 · 等待验证` without granting closure or cleanup.

## Phase B — asynchronous validation handoff

7. Add `candidate-validation-receipt-v1` and an exact-SHA request/handoff adapter to the existing validation router.
   The validator has no product-write capability.
8. Reuse fresh exact-fingerprint receipts, otherwise select the existing authorized focused stage. Preserve CI7
   leases/budgets/no-repeat behavior.
9. Append PASS/FAIL status without modifying the Candidate. FAIL references and reopens the original task only after a
   new authority amendment; no automatic retry.
10. Update Personal/Graph projections to distinguish pending/validated/failed/closed and prove Maintenance still sees
    no cleanup eligibility before closure/history gates.

## W7.4 manual adoption

Before W3.1 automation is complete, the unique integrator applies ADR-0030 manually to the accepted W7.4 tree:

- stop additional post-acceptance test commands;
- preserve completed final-exit-code results and mark interrupted results Unknown;
- run only structural freeze checks;
- commit one clean exact Candidate with `validation-pending` status;
- stop W7.4; validation/integration follow asynchronously.

This manual adoption is process evidence for W3.1, not proof the command exists.

## Validation

Focused implementation evidence must include:

- synthetic accepted unchanged tree freezes/commits/receipts once;
- changed-after-acceptance, unexpected path, conflict, forbidden artifact, parity and diff failures stop before commit;
- freeze invokes zero tests and meets `<30s` in the bounded fixture;
- async PASS/FAIL cannot mutate Candidate and unchanged failure cannot rerun;
- status projections preserve pending vs validated vs closed vs cleanup-eligible distinctions;
- real W7.4 manual adoption timing/receipt is recorded separately.

Run focused owners during W3.1 development as appropriate; the user-facing freeze path itself must never run them.
Fast/Checkpoint/Candidate/Promotion and publication remain separate.

## Expected implementation surfaces

- Core collaboration/review/closure schemas and candidate-freeze owner;
- CLI Workstream freeze/status commands;
- CI7-compatible asynchronous validation handoff/receipt adapter;
- Personal/Graph/Maintenance status projection only;
- focused owner tests and W3.1 Validation/State/DEVLOG.

## Hard boundaries

- no weakening of exact-SHA validation, branch protection, Promotion or release policy;
- no tests/package/site/provider scans inside Candidate Freeze;
- no source/diff/transcript/credential persistence in receipts;
- no automatic retry, integration, task closure or worktree deletion;
- no modification of W7.4/U2.5/W7.5 product branches;
- no external network, scheduler, push/main/tag/release action.

## Completion definition

- accepted unchanged task can produce a clean exact Candidate and freeze receipt in under 30 seconds;
- implementation task stops at honest validation-pending state;
- validation runs independently against immutable SHA and cannot change source;
- PASS/FAIL/closed/cleanup states remain distinct;
- W7.4 manual adoption demonstrates the process without waiting on tests;
- focused W3.1 checks pass and the task branch is clean.
