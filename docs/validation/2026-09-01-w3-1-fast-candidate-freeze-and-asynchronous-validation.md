# Validation: W3.1 Fast Candidate Freeze and Asynchronous Validation

Status: Pending implementation; W7.4 manual adoption pending

Date: 2026-09-01

Plan: [W3.1 Fast Candidate Freeze and Asynchronous Validation](../implementation/plans/2026-09-01-w3-1-fast-candidate-freeze-and-asynchronous-validation.md)

## Baseline problem

An accepted W7.4 preview entered same-task post-acceptance checks and kept the implementation task active for multiple
minutes. This demonstrates that current closeout conflates Candidate freeze with validation. It does not prove a
worktree-removal performance problem; no physical cleanup ran.

## Pending W7.4 manual-adoption evidence

- exact accepted surface/relevant-tree fingerprint;
- time from resume to clean Candidate commit using structural checks only;
- `candidate-frozen / validation-pending` receipt;
- completed pre-stop test outputs retained only when a final exit code exists;
- no new unittest/Fast/Checkpoint/Candidate/Promotion command during freeze;
- worktree remains registered and no branch/commit/evidence is deleted.

## Pending W3.1 product evidence

- receipt schema positive/negative fixtures;
- zero-write dry-run and one-commit apply;
- acceptance-drift/unexpected-path/conflict/forbidden/parity/diff failures before commit;
- explicit proof that freeze does not import/invoke test runners, temporary Git fixtures, site/package builders or
  relation/history providers;
- `<30s` bounded real-Git freeze fixture and 60-second refusal boundary;
- immutable exact-SHA async validation PASS/FAIL and no-repeat behavior;
- status projections distinguish frozen-pending, validated, failed, closed and cleanup-eligible;
- no Candidate mutation, integration, deletion, external network or release action.

## Evidence boundaries

- a clean commit is not validation PASS;
- validation PASS is not integration, closure or cleanup authorization;
- an interrupted test without final exit code remains Unknown;
- moving validation off the interactive path does not remove or weaken it;
- manual W7.4 adoption validates the process shape, not W3.1 automation.

## Result

Pending. ADR/Design/Plan exist; no W3.1 task/worktree/product/receipt or asynchronous validator has been implemented.

## 2026-09-02 dispatch observation — schema gate

- W3.1 registered from task-description version `830619475258c0c257dea4ec162026c51ec29a0a` on its independent branch;
- its first scope refresh returned the expected L3 exclusive `schema-migration` hard gate for the two planned receipt
  schemas;
- the task stopped clean with no Candidate and no product changes;
- Plan revision 2 assigns only those strict schema resources to the unique integrator. W3.1 remains Pending until it
  imports the exact bootstrap, refreshes scope to allowed and implements the behavior.

This is blocker evidence, not implementation or validation PASS.

The unique integration branch subsequently added only the two approved strict JSON Schema resources at exact
`c142f325d643827c47ce14fb7a489ea1ff39a295`; JSON decode and Draft 2020-12 schema self-check passed. This removes the
bootstrap dependency but still proves no W3.1 command, receipt writer or validator behavior.

## 2026-09-02 resumption observation — frozen-peer overlap

- after importing the bootstrap, scope no longer failed on `schema-migration`;
- the original broad scope still produced direct/L3 findings against W7.4's frozen Graph, shared owner tests and
  task-local State/DEVLOG paths;
- no W3.1 product byte was written, and neither peer was closed, deleted or overwritten;
- Plan revision 3 limits the active implementation slice to new Core/CLI/CI infrastructure, one new focused owner and
  this Validation document. Projection and shared-document evidence remain Pending for a later common baseline.

The next admissible evidence is an allowed refreshed scope followed by implementation on only that disjoint slice.
