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

## 2026-09-02 peer-only finding diagnosis

The revision-3 refresh persisted 21 direct/authority findings, but every finding named only W7.4 and U2.5; none named
W3.1. W3.1 therefore remained clean and correctly performed no product write. Plan revision 4 authorizes a focused
regression proving that unrelated peer conflicts remain visible in topology inspection without blocking a third,
disjoint Workstream's own scope refresh. Current-task conflicts must remain fail-closed.

Central bootstrap exact `33e48fbb8fa671d33c91cb1bd164fb038ab7e4c7` preserves full topology diagnostics and filters only the
per-Workstream refresh decision/session. The focused three-worktree regression completed 1/1 PASS in 19.308 seconds;
`git diff --check` passed. No broader suite, peer deletion, scope bypass or W3.1 product implementation occurred.

## 2026-09-02 revision-3 disjoint implementation evidence

Task authority and scope:

- imported exact task-description version `c0cab50e4d5c292ac42b2f08c351178ddb3d6a32`, which includes the narrow
  finding-isolation bootstrap at `33e48fbb8fa671d33c91cb1bd164fb038ab7e4c7`;
- rewrote the Git-private W3.1 session to the six revision-3 paths, then ran a normal full-local scope refresh;
- the first refresh reported `findings=[]` and the expected L2 local confirmation requirement; the confirmed refresh
  produced scope revision 5 with `allowed=true`, `local_work_allowed=true`, `findings=[]` and runtime `active`;
- no `--no-local-worktrees`, L3 override, peer deletion, fabricated lineage or peer product write was used.

Implemented disjoint behavior:

- Core loads and dependency-free validates the two centrally owned strict receipt schemas;
- `worktree freeze-candidate` supports explicit zero-write dry-run and apply, binds the accepted surface fingerprint to
  exact expected-path bytes, performs only bounded local structural checks, stages only expected paths, creates one
  commit and atomically writes its Git-private freeze receipt;
- the product freeze path invokes Git only: it imports or starts no unittest/pytest runner, temporary Git fixture,
  Fast/Checkpoint/Candidate/Promotion route, site/package build, browser replay or relation/history provider scan;
- the asynchronous adapter writes an exact-SHA Git-private request for the existing CI7 router and records an existing
  runner result without product writes. Exact PASS receipts are reused; unchanged failed Candidates refuse a new
  request or result record.

Focused owner command (the only test surface run):

`python -X utf8 -m unittest tests.test_candidate_freeze`

Final result: **7/7 PASS in 129.039 seconds**. The owner uses separate real-Git fixtures, so its aggregate runtime is
not the user-facing freeze latency. The bounded apply fixture asserted one commit, a clean worktree, an atomic receipt
and `elapsed_ms < 30000`; the injected clock asserted the 60-second pre-commit refusal. The same owner covered schema
positive/negative cases, zero-write dry-run, acceptance drift, unexpected paths, conflict markers, forbidden artifacts,
exact-copy parity, `git diff --check`, Git-only child-process instrumentation, exact-SHA request/PASS/FAIL immutability,
PASS reuse and failure no-repeat.

Static checks completed with final exit code 0:

- `py_compile` for the Core owner, CLI owner, asynchronous adapter and focused owner;
- `git diff --check`;
- CLI help parsing for `worktree freeze-candidate` and `candidate_validation.py {request,record}`.

This remains **partial W3.1 Candidate evidence**, not full completion. Personal/Graph/Maintenance projections, shared
owner tests, subsystem State/DEVLOG synchronization, W7.4 manual-adoption evidence and every
Fast/Checkpoint/Candidate/Promotion/publication gate remain Pending for the common integrated baseline defined by Plan
revision 3. No integration, push, release, closure, cleanup or worktree deletion occurred.

## 2026-09-02 deferred-projection resumption gate

- W3.1 infrastructure Candidate `6eab27964e22cb0e22b6ebb34ab175869a6505fc` remains clean and unchanged;
- U2.5 exact `f28cf6d1dc9ebb6fbf58a73071c705a4339337d1` is clean and frozen with validation Pending;
- the maintainer explicitly authorized W3.1 to resume its deferred projection phase from that common baseline;
- no projection implementation, focused evidence, integration or completion claim exists yet under revision 5.

## 2026-09-02 revision-5 deferred projection evidence

Authority and scope:

- losslessly imported task-description exact `7ca71c11bba59200479e633a1ffb52b15084482f` and U2.5 Candidate exact
  `f28cf6d1dc9ebb6fbf58a73071c705a4339337d1`; infrastructure exact
  `6eab27964e22cb0e22b6ebb34ab175869a6505fc` remains in ancestry;
- rewrote the Git-private expected-write/validation surface set, then ran the complete local-worktree scope guard;
- the first revision-8 refresh returned the expected L2 confirmation requirement with `findings=[]`; the Plan-revision-5
  confirmation produced scope revision 9 with `allowed=true`, `local_work_allowed=true`, `findings=[]` and no review block;
- did not use `--no-local-worktrees`, L3 acknowledgement, peer deletion, fabricated lineage, integration or cleanup.

Implemented projection:

- Core now reads only bounded regular Git-private receipt files (maximum 256 entries per ledger and 512 KiB per file),
  validates both strict central schemas and projects candidate, validation and closure as independent axes;
- Personal startup adds those axes and a visible status label while preserving two registry calls, one Maintenance cache
  snapshot, zero source/scope/diff reads, zero network and zero writes;
- Graph receives candidate lifecycle as supplemental provider metadata. It does not change Core graph/schema/hash, node
  or edge selection, active-tip calculation, relation/history authority, layout, or full/compact folding semantics;
- Maintenance inventory exposes the same axes and adds explicit pending/validated-but-open/failed reasons. Validation
  alone never changes cleanup eligibility; only the existing closure/integration/review gates can do that;
- missing legacy/new-format receipts remain `not-frozen` or Unknown rather than deriving a freeze fact from branch names,
  clean worktrees, prose or agent self-report.

Focused owners (the only automated test surfaces run):

- `python -X utf8 -m unittest tests.test_candidate_freeze` — **7/7 PASS in 210.238 seconds**;
- `python -X utf8 -m unittest tests.test_personal_observatory` — **14/14 PASS in 107.848 seconds**;
- `python -X utf8 -m unittest tests.test_workstream_relation_graph_observatory` — **12/12 PASS in 2.315 seconds**;
- `python -X utf8 -m unittest tests.test_workspace_maintenance` — **8/8 PASS in 468.904 seconds**.

Static checks and bounded live projection completed with exit code 0: changed Python files compiled, `git diff --check`
passed, Personal remained source/scope/diff-free, and the real local Graph projection remained `ready` with 28 nodes and
22 edges. U2.5 Shell/cache/delivery owners and their project-template copies were not edited. No Fast, Checkpoint,
Candidate, Promotion, push, release, worktree removal, branch deletion or network action occurred.

Result: W3.1 implementation and focused owner evidence are complete in this Worktree. This is not Canonical integration,
hosted validation, closure, cleanup authorization, Promotion or release evidence.
