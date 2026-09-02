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

## 2026-09-02 second Promotion result

- corrected registry source `01a3e9ac80f96b610deb1353d09b546ac5c8a4c8` was pushed to the same non-main
  Promotion ref;
- Promotion run `33659625925` passed exact-SHA preflight and then failed closed in repository packaging gates and five
  logical test lanes on both operating systems;
- the failures were integration drift at already-accepted boundaries: the two-launcher/new-module package inventory,
  installed-runtime inventory, immutable Authority v1 compatibility, fixture Git identity, lazy Graph test setup,
  exact-blob overlap expectations, ADR relation inventory and machine-list stderr expectation;
- the SHA was not retried and protected `main` was not updated;
- correction remains limited to compatibility/inventory and stale test expectations. U2.5/W3.1 product semantics,
  public tags, Release assets and publication state are unchanged.

## Corrected integration candidate evidence

- Candidate Freeze owner suite passed 7/7 after the shared Git fixture gained repository-local author identity;
- the exact failed lineage, LAN harness, ADR relation inventory, machine inventory and immutable brand/schema checks
  each passed after stale integration expectations were reconciled;
- the six runnable failed packaging/installation methods passed, including fresh install/build and the deterministic
  170-entry archive; the AI-settings method remained locally skipped because optional dynamic dependencies were not
  requested, and will run in Promotion as before;
- the lazy Graph delivery API fixture and the explicit two-launcher contract each passed their focused rerun;
- `validate_ci.py --all`, `git diff --check`, manifest/core projection equality and all 111 managed-runtime path checks
  passed. No Fast, Checkpoint or local Candidate suite was run.

## 2026-09-02 third Promotion result

- exact candidate `effc5a252b5a96c067f586d3f91173857afe4ef4` entered Promotion run `33679435608`;
- exact-SHA preflight and the Ubuntu repository/package gate passed; completed Ubuntu lanes other than lane-03 were
  green when the remaining run was cancelled;
- lane-03 had one stale assertion that expected the starting shell to force `#overview`, while accepted U2.5 preserves
  the user's current hash with `location.replace('/'+location.hash)`;
- the run was cancelled once that sole failing fingerprint was available, avoiding unnecessary completion of an
  already non-green SHA. It will not be retried and `main` was not updated.
- the exact close/reclaim method then passed locally after its same stale block was aligned with current-hash
  navigation and the bounded 1500 ms polling backoff.
