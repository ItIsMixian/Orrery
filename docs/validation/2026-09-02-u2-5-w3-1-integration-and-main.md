# Validation: U2.5 + W3.1 Central Integration and Main Push

Status: Pending

Date: 2026-09-02

Plan: [U2.5 + W3.1 Central Integration and Main Push](../implementation/plans/2026-09-02-u2-5-w3-1-integration-and-main.md)

## Fixed inputs

- U2.5 `f28cf6d1dc9ebb6fbf58a73071c705a4339337d1`;
- W3.1 `2296853f5009ef7f5c1307452fbdd9a8f096c9c2`;
- local central task-description parent to be recorded after commit.

## Pending evidence

- clean ancestry-preserving integration and exact integrated SHA;
- bounded local structural/syntax result;
- non-main Promotion ref and GitHub Actions run;
- `smoke-test (windows-latest)` and `smoke-test (ubuntu-latest)` success on the exact SHA;
- identical protected-main SHA and clean local integration worktree;
- no tag, Release, asset, cleanup or child-suite replay.

## Result

Pending execution.

## 2026-09-02 first Promotion refusal

- integrated source `a25c52a99d089590697d3fe7a6c6a51cf3e2e496` was pushed to
  `promotion/u2-5-w3-1-integration`;
- Promotion run `33659299162` failed before test discovery/execution in exact-registry binding;
- the failure reported 12 unregistered new/renamed tests and one stale launcher test ID;
- no test failure, retry or protected-main push occurred on that SHA;
- the registry was updated with the exact discovered IDs, existing owner shards/stages/budgets, and the stale launcher
  ID was replaced rather than duplicated;
- JSON decode, `validate_ci.py --all` and `git diff --check` passed locally. A new SHA is required; the failed SHA will
  not be rerun.
