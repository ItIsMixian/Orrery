# SH1 Real Self-host Collaboration Acceptance

Status: Complete

Date: 2026-08-29

Fact scope: `codex/sh1-real-self-host-collaboration-acceptance`, based on protected
`main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`.

Governing decisions:

- [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)
- [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)
- [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md)

Parent plan: [Multi-worktree Collaboration Protocol](2026-08-19-multi-worktree-collaboration-protocol.md),
Phase 5 self-host acceptance.

## Objective

Validate the Canonical W1–W7 collaboration source against Orrery's real self-host Git repository and
Git-private coordination state. Keep real-project operations read-only or dry-run, keep synthetic evidence
separate, and record exact Git, session, relation and maintenance hashes without upgrading local telemetry into
authoritative project facts.

## Boundaries

- Use only the existing Codex-created linked worktree. Do not create a second SH1 worktree.
- Register `SH1-real-self-host-collaboration-acceptance` before the first authored-file write.
- Do not modify root `docs/PROGRESS.md`／`docs/HANDOFF.md`, shared subsystem State, `docs/DEVLOG.md`, or shared
  indexes on this ordinary feature branch.
- Do not modify README/assets, maintenance Core／UI／cache, Authority consumer／UI, or unified Observatory product
  files owned by W6.1, github-front-door-redesign, A3 or U1.
- Do not run real relation apply／undo／recovery, maintenance authorization／execution, worktree removal, branch
  deletion, Team remote action, author-document writeback, network action, release, or main promotion.
- Give the full maintenance scan one explicit bounded attempt of at most 25 seconds. Treat timeout or performance
  findings as W6.1-adjacent evidence; do not repeatedly rerun the expensive scan.
- Never infer a Workstream relationship from branch names, worktree paths, age or path similarity. Preserve
  missing explicit evidence as Unknown.

## Evidence tracks

### Real self-host read-only evidence

- Bind the baseline to exact HEAD, integration OID, merge base, registered worktree inventory and clean/dirty
  fingerprints.
- Hash every live `worktree.json` used in a conclusion and hash the relation store, archived sessions and relevant
  maintenance status inputs as bounded file manifests.
- Inspect current worktree/session status, Scope/finding output, native and legacy relation graph, succession plan,
  active tips, relation transaction state, pending recovery and maintenance status/queue.
- Reconcile active, stale, closed/superseded and Unknown as independent axes. Check that archived sessions and
  removed worktree paths remain distinguishable from live registered worktrees.
- Use `integrate`, relation and maintenance commands only where their selected mode is mechanically read-only or
  dry-run. Record exit codes and expected fail-closed results without changing Git-private destructive state.

### Synthetic evidence

- Reuse existing committed W1–W7 suites for deterministic behavior that cannot safely be exercised against the
  self-host repository.
- Add an SH1-owned test or fixture only when it captures a missing, stable acceptance contract or a minimal product
  defect reproduction outside concurrent Workstream write sets.
- If a defect overlaps W6.1/A3/U1 or the front-door redesign, stop implementation and record the exact finding for
  central integration rather than editing the overlapping product surface.

## Validation ladder

1. **Fast:** SH1-owned focused tests, directly affected collaboration contracts, and `git diff --check`.
2. **Checkpoint:** repository CI contract, integrated installation structure and affected W1–W7 read-only suites
   within their frozen budgets.
3. **Repository gates:** integrated structure, isolated docsite when authored docs change, Markdown links,
   forbidden-artifact checks and final diff review.
4. **Candidate boundary:** bind all results to the final SH1 commit. This task does not push a Promotion ref, run
   hosted required checks, update main, publish, or claim release acceptance.

Interrupted commands, missing exit codes, or outputs without their required `Ran`／`OK` evidence do not count as
passes. Real self-host evidence and synthetic fixture evidence remain separate in the Validation record.

## Deliverables

- [x] Git-private Workstream registration on the exact protected-main baseline.
- [x] Real self-host read-only evidence bundle and exact hashes.
- [x] One bounded full maintenance scan outcome, with no repeated long run.
- [x] Product-finding overlap stop: no fixture/test was added because its required CI inventory path is in A3's write set.
- [x] [SH1 Validation](../../validation/2026-08-29-sh1-real-self-host-collaboration-acceptance.md).
- [x] Fast → Checkpoint and repository-gate evidence on the completed authored tree.
- [x] Non-main Candidate handoff prepared with findings, W6.1 boundary and central integration advice; exact final
  commit is reported outside this self-referential Plan.
