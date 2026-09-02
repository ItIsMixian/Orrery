# Implementation Plan: W3.1 Fast Candidate Freeze and Asynchronous Validation

Status: Approved for implementation

Date: 2026-09-01

Task code: W3.1

Program path: explicitly absent — `classification-pending` because no accepted W3 phase group exists

Task series: `workstream-lifecycle`; intended order `31`; explicit predecessor `W3-review-integration-cleanup`

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

## 2026-09-02 scope revision 2 — integrator-owned receipt schema bootstrap

The initial W3.1 scope refresh correctly stopped at `L3 / schema-migration`: the approved Plan requires two new Core
receipt schemas, while all `schema/**` paths are exclusive to the unique integration worktree. W3.1 remained clean and
made no product write.

This revision authorizes the unique integrator to add strict, versioned
`candidate-freeze-receipt-v1.json` and `candidate-validation-receipt-v1.json` resources only. After the exact bootstrap
commit exists, W3.1 may:

1. import that exact bootstrap into its existing branch without rewriting either schema;
2. remove the two schema resource paths from task-owned expected writes and refresh its Git-private scope against the
   new task-description version;
3. resume the already approved Core loader/validator, CLI command, asynchronous handoff, projection and focused-owner
   implementation only after the exclusive schema finding is absent and scope is allowed;
4. return any required schema-field change to the unique integrator instead of bypassing or locally acknowledging L3.

The bootstrap does not implement freeze behavior, validation orchestration, integration, cleanup, push or release.
All original W3.1 safety and validation boundaries remain in force.

The unique integrator completed that strict two-file bootstrap at exact
`c142f325d643827c47ce14fb7a489ea1ff39a295`. W3.1 may consume it only through the import/scope-refresh sequence above.

## 2026-09-02 scope revision 3 — disjoint infrastructure first

After importing the schema bootstrap, W3.1 correctly found that its original broad projection/test/document write set
still overlapped the frozen W7.4 Candidate. A frozen validation-pending worktree must not be deleted or falsely closed
merely to free paths, and W3.1 must not overwrite its accepted Graph/history bytes.

W3.1 therefore resumes first on a disjoint infrastructure slice. Its current task-owned writes are limited to:

- `packages/project-orrery-core/src/project_orrery_core/candidate_freeze.py`;
- `packages/project-orrery-core/src/project_orrery_core/schema.py` only to load the two centrally owned schemas;
- `packages/project-orrery-cli/src/project_orrery_cli/worktree.py`;
- `scripts/ci/candidate_validation.py`;
- `tests/test_candidate_freeze.py`;
- its own Pending Validation document.

The Personal/Graph/Maintenance projection work, existing shared owner tests, subsystem State and DEVLOG updates are
deferred until W7.4/U2.5 provide a common integrated development baseline. This is sequencing, not removal from the
accepted design. W3.1 must rewrite its Git-private expected-write and validation-surface sets to this exact slice,
refresh scope, and resume product work only after all direct/L3 findings are retired. It must not import or edit W7.4
or U2.5 product bytes for this phase.

The disjoint Candidate may prove Core receipt validation, zero-write dry-run/one-commit apply, acceptance-drift and
structural refusals, the zero-validation freeze boundary, and immutable-SHA asynchronous PASS/FAIL/no-repeat behavior.
It cannot claim the deferred UI projections or full W3.1 completion.

## 2026-09-02 scope revision 4 — current-Workstream finding isolation bootstrap

The revision-3 disjoint scope was still blocked by direct findings whose `workstream_ids` contained only W7.4 and
U2.5. The current W3.1 Workstream touched none of those paths. `inspect_worktree_overlap` correctly reports the whole
local topology, but `refresh_workstream_scope` incorrectly fed every peer-to-peer finding into W3.1's own expansion
decision and session.

The unique integrator is authorized to make one narrow safety correction in Core collaboration scope handling and its
existing focused owner test:

1. keep full pairwise diagnostics in `inspect_worktree_overlap`;
2. before evaluating or persisting one Workstream's scope refresh, retain only findings whose `workstream_ids` include
   that current Workstream;
3. mechanically retire previously persisted peer-only findings from that Workstream session;
4. continue to fail closed for every direct, L3, authority, semantic or Unknown finding that actually involves the
   current Workstream.

After the exact bootstrap commit, W3.1 must import the new task-description version and refresh the revision-3
disjoint scope normally. `--no-local-worktrees`, L3 acknowledgement, peer deletion and fabricated lineage are not
authorized recovery mechanisms.

The unique integrator completed this narrow guard bootstrap at exact
`33e48fbb8fa671d33c91cb1bd164fb038ab7e4c7`. W3.1 must consume it through the normal exact task-description import and
scope refresh; it is not a blanket conflict override.
