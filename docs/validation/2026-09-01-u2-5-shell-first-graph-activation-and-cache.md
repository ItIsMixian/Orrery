# Validation: U2.5 Shell-first Graph Activation and Incremental Cache

Status: Pending implementation and maintainer preview

Date: 2026-09-01

Plan: [U2.5 Shell-first Graph Activation and Incremental Cache](../implementation/plans/2026-09-01-u2-5-shell-first-graph-activation-and-cache.md)

## Baseline evidence

- Public v0.3.1 opens no usable page until the complete Unified render finishes; the recorded self-host delay was
  roughly 95 seconds.
- U2.4 local Candidate binds a startup page in 701 ms and completes the full page after 55.317 seconds, but the browser
  remains globally blocked by `Orrery 正在启动` during that interval.
- The U2.4 profile recorded 751 child processes, about 63.991 seconds in the Graph provider and about 2.561 seconds in
  the base docsite.
- Dynamic `GET /api/v1/workstreams/graph` currently serves an in-memory `startup-cached-projection` only after the full
  render. The payload is discarded on stop, and the next cold start recomputes the Graph.
- W7.4 Graph/history product work is currently dirty and uncommitted; U2.5 has no accepted exact presentation
  dependency yet. This record must not treat that worktree as Canonical or a clean Candidate.

These observations prove the gap. They do not prove any correction.

## Pending maintainer preview

- one shell/URL with no full-page Graph startup gate;
- non-Graph navigation usable while Graph alone is loading;
- Graph-local empty/current/stale/refreshing/failed states and atomic visual swap;
- unchanged restart uses a validated Git-private cache with zero full provider runs;
- one bounded input change creates exactly one refresh and visibly stale last-known data until completion;
- accepted W7.4 full/compact semantics and evidence remain unchanged;
- stop during refresh reclaims runtime/worker state;
- no Computer Use, external network, automated test suite or release operation before acceptance.

## Pending focused mechanical evidence after preview acceptance

- existing Unified lifecycle/delivery owner assertions;
- existing Graph owner assertions affected by dynamic hydration;
- cache schema/fingerprint/atomic-write/corruption/single-flight negative controls;
- static eager-build and dynamic lazy-delivery separation;
- root/project-template parity, syntax checks and `git diff --check`;
- exact commands, elapsed times, provider invocation counts, cache generation/hash and clean Candidate SHA.

## Evidence boundaries

- A fast listener or shell skeleton alone does not prove the non-Graph product is usable.
- A cache hit does not prove relation/history facts are current unless the versioned input fingerprint matches.
- Cached/stale presentation is a derived view, not relation, closure, Validation or cleanup authority.
- Synthetic fixtures do not replace a real self-host preview using the accepted W7.4 graph.
- Focused local evidence does not authorize Fast, Checkpoint, Candidate, Promotion, main, version, tag, asset or Release.

## Result

Pending. No product implementation or automated validation is claimed by this task-description version.

## 2026-09-02 Phase B resumption gate

- Phase A is present as clean exact `6596a9f8e0e79cf0e5bc76b8ae46b0f323056040`; its task-owned evidence remains
  limited to syntax/import and real lifecycle preview observations, not an automated test PASS;
- the maintainer has authorized continuation;
- the accepted W7.4 dependency is frozen at exact `fe75fc238ebf876d8565cabda0c8e0f8cfb4cfdd` with validation Pending;
- U2.5 may import that exact Candidate and build the Phase B preview, but validation, integration and release claims
  remain blocked by their existing gates.

The next evidence is the real Phase B self-host preview. Automated suites remain forbidden before that preview is
accepted.

## 2026-09-02 Phase B scope diagnosis

- exact W7.4 Candidate import completed as merge `78b9c759e9f9628a64a7e6e9be381a2ac3b79eb5` with no Phase B product edit;
- the subsequent full-local refresh stopped at L3 because imported W7.4 paths appeared as committed on both branches,
  including paths U2.5 did not intend to edit;
- U2.5 remained clean and did not use `--no-local-worktrees` or acknowledge L3;
- Plan revision 3 preserves real expected-write conflicts while authorizing a disjoint delivery slice and exact shared
  commit deduplication in scope evidence.

This is blocker evidence only. The next admissible U2.5 evidence is an allowed full-local refresh followed by its first
legal delivery-slice product write.

Central exact `da923ff8ff1d411f8b42032886fae5d0a853fd8a` now removes only identical `committed_last_oid` material before
pairwise comparison. A focused two-worktree regression proved shared import plus one writer remains allowed, while two
expected writers still return L3; together with the peer-only isolation regression, 2/2 tests passed in 47.143 seconds.
No broader suite or U2.5 product write ran.
