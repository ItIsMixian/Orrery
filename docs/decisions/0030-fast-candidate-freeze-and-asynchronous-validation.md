# ADR-0030: Fast Candidate Freeze and Asynchronous Validation

Status: Accepted

Date: 2026-09-01

Maintainer acceptance: accepted on 2026-09-01 after the maintainer rejected multi-minute post-preview closeout and
required a simpler workflow.

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0018](0018-authority-first-workstream-dispatch.md)

Preserves: [ADR-0012](0012-document-governance-and-information-lifecycle.md),
[ADR-0021](0021-v0-3-0-release-scope-default-matrix.md)

## Context

Current feature tasks often keep the user waiting after a preview is accepted while the same task runs focused
unittests, creates temporary Git fixtures, updates evidence documents, performs parity/diff checks, commits and closes
its session. The checks may be valid, but combining them with the interactive close action makes “done” feel slow and
blurs four different facts: accepted experience, frozen source, validated source and closed/removed worktree.

A physical `git worktree remove` should take seconds once evidence already exists. Candidate freeze should also be a
short deterministic operation. Time-consuming validation still matters for integration and release, but it need not
hold the implementation task or block the maintainer from continuing other work.

## Decision

1. Orrery separates four states:
   - `preview-accepted`: human experience/semantic surface accepted for an exact relevant-tree fingerprint;
   - `candidate-frozen`: product writes stopped and one clean exact commit/receipt exists;
   - `validation-pending|validated|validation-failed`: asynchronous evidence bound to that exact commit;
   - `closed`: an explicit lifecycle outcome such as integrated, abandoned or superseded. Worktree removal is separate.
2. After preview acceptance, the blocking **Candidate Freeze** path targets under 30 seconds on the maintained host.
   It performs only bounded structural checks: authority/scope/current branch, expected paths, dirty/staged inventory,
   accepted-surface fingerprint, conflict markers, forbidden artifacts, `git diff --check`, required exact-copy parity
   and commit creation. It runs no unittest suite, temporary Git fixture, Fast/Checkpoint/Candidate/Promotion stage,
   package build, browser replay or relation/history rescan.
3. Syntax/import or other focused receipts already produced against the identical relevant-tree fingerprint may be
   attached without rerun. Missing evidence stays Pending; it does not block freeze or become PASS.
4. Any product/tree change after preview acceptance invalidates the acceptance fingerprint and refuses freeze. The task
   returns to iteration/preview instead of silently changing code during closeout.
5. Candidate Freeze writes a Git-private `candidate-freeze-receipt-v1` binding task-description version, workstream,
   accepted surface fingerprint, relevant tree hash, exact commit SHA, expected paths and checks performed. It contains
   no Prompt/transcript/source/diff body or credentials.
6. The implementation task becomes idle/stopped at `candidate-frozen + validation-pending`; it does not wait for long
   checks. Validation runs separately against the exact commit through an integration validator/CI lane or bounded
   follow-up task and may proceed while other non-conflicting work starts.
7. Asynchronous validation cannot modify the frozen commit. PASS appends an exact receipt; FAIL appends the failure and
   reopens the same implementation task from a new amendment/fingerprint. Unchanged failed runs are not retried.
8. Integration, protected main and release gates remain unchanged: a frozen but unvalidated Candidate cannot be
   promoted where current policy requires validation/Promotion.
9. Documentation closeout is also split. Freeze records a minimal Pending Validation update; detailed command output,
   final State/DEVLOG and global PROGRESS/HANDOFF reconciliation occur when validation/integration facts exist, not as
   repetitive blocking prose before the task can stop.
10. Worktree cleanup remains W6/W6.2-owned. Candidate freeze, validation PASS or branch containment does not authorize
    physical removal; cleanup consumes existing closure/history/safety evidence and performs no tests.
11. W7.4 adopts this process immediately through a dated Plan amendment. Its already-running grouped checks stop and
    remain non-evidence if no final exit code exists; the task freezes the accepted tree without starting new tests.
12. W3.1 may later implement one-command freeze/receipt and asynchronous validator orchestration. Manual adherence is
    effective now; automation, public release and scheduler remain separately validated.

## Reasons

- The user regains control immediately after accepting the result.
- Expensive checks retain their authority but move off the interactive critical path.
- Exact fingerprints prevent “accepted UI, changed source” drift.
- Distinct statuses stop Candidate, validation, closure and deletion from being conflated.

## Consequences

- Some Candidates will be clean and frozen while validation is Pending; all views must display that honestly.
- Downstream work may start from an accepted frozen Candidate when its own risk policy permits, but integration or
  destructive operations can still require validation.
- Existing validation routing/lease/no-repeat rules remain applicable to the asynchronous stage.
- Task closeout documents become shorter and event-driven.

## Mapping

- Approved Design: [Fast Candidate Freeze and Asynchronous Validation Closeout](../design/fast-candidate-freeze-and-asynchronous-validation.md)
- Implementation Plan: [W3.1 Fast Candidate Freeze and Asynchronous Validation](../implementation/plans/2026-09-01-w3-1-fast-candidate-freeze-and-asynchronous-validation.md)
- Pending Validation: [W3.1 Fast Candidate Freeze and Asynchronous Validation](../validation/2026-09-01-w3-1-fast-candidate-freeze-and-asynchronous-validation.md)
