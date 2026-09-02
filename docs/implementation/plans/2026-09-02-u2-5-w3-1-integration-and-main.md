# Implementation Plan: U2.5 + W3.1 Central Integration and Main Push

Status: Approved for execution

Date: 2026-09-02

Maintainer authorization: integrate and push promptly; avoid redundant or broad local validation.

Inputs:

- U2.5 clean frozen Candidate `f28cf6d1dc9ebb6fbf58a73071c705a4339337d1`;
- W3.1 clean Candidate `2296853f5009ef7f5c1307452fbdd9a8f096c9c2`;
- W3.1 mechanically contains the exact U2.5 Candidate and current central authority ancestry.

## Objective

Integrate both Candidates into the unique local integration branch, push one exact non-main Promotion ref, and advance
protected `main` to the same SHA only after the required Windows and Ubuntu smoke checks pass.

## Short execution path

1. Commit this authority-only task-description version.
2. Merge W3.1 exact into `codex/u1-u2-integration-baseline`; because W3.1 contains U2.5, do not merge U2.5 separately.
3. Preserve additive authority/evidence history and make no new product change during integration.
4. Run only bounded local integration checks: ancestry, conflict-marker scan, Python syntax for changed owners, JSON
   schema decode and `git diff --check`. Reuse all child focused/runtime receipts; do not replay unittest suites, Fast,
   Checkpoint or local Candidate.
5. Push the exact integrated SHA to `promotion/u2-5-w3-1-integration`; use the repository-required Windows/Ubuntu
   Promotion checks as the sole broad validation.
6. If either required check fails, stop on the non-main ref and preserve the result. Do not retry unchanged SHA.
7. If both required checks pass, push the identical SHA to protected `main`. Do not create a tag, Release or asset.
8. Record exact run/SHA evidence and synchronize current State/PROGRESS/HANDOFF without replaying child checks.

## Hard boundaries

- no force push, history rewrite, tag, GitHub Release, package publication or worktree deletion;
- no new product behavior or scope expansion during integration;
- no broad local test replay;
- protected-main and exact-SHA dual-platform rules remain mandatory.

## Completion

The same exact integrated SHA is present on the Promotion ref and protected `main`, both required checks are green,
the integration worktree is clean, and release/publication state remains unchanged.
