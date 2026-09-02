# Validation: U2.5 Shell-first Graph Activation and Incremental Cache

Status: Phase A implementation preview ready; maintainer acceptance and Phase B remain pending

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

## Phase A worktree preview evidence

- Workstream `U2.5-shell-first-graph-activation-cache` was registered from exact authority SHA
  `4e56e3eb4fbb5596e5dcc2bddb48884d2056c041` on independent branch
  `codex/u2-5-shell-first-graph-cache`; its Git-private series binding is `unified-u`, order `25`, with explicit
  predecessor `U2.4-immediate-launcher-readiness`.
- The zero-write task baseline reached the listener in 141 ms, but the complete dynamic shell remained blocked for
  29.605 seconds on the first launch and 28.575 seconds on an unchanged second launch. An isolated Graph provider run
  took 15.681 seconds and created 132 child processes.
- The Phase A preview reached the listener in 137 ms and published the usable base shell in 2.908 seconds. Deferred
  document-corpus activation completed 232 ms later without extending shell readiness.
- The unchanged preview restart reported Graph `cached-current`, cache generation `0`, reason
  `validated-cache-hit` and `provider_runs_since_start: 0`; the validated cached projection contained 7 nodes and 7
  edges. The prior uncached preview completed one background provider run and atomically published generation `0`.
- Runtime health reported the shell and `consumers.workstream-graph` independently. The local stop endpoint returned
  `stopping`, then removed the runtime marker and terminated the recorded PID.
- Only the Phase A runtime/builder copies and the Git-private cache/delivery owner were changed. No W7.4 presentation,
  relation or history surface was modified, and no external network or Computer Use was used.
- Python syntax/import checks needed to start the preview passed for the five changed runtime/cache files and both
  runtime imports. No unittest, Fast, Checkpoint, Candidate, Promotion or release command has run.

This evidence is a local worktree preview, not maintainer acceptance or post-acceptance validation. The cached payload
was produced from the current pre-W7.4 presentation baseline and cannot satisfy the accepted-W7.4 parity checks.

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

Phase A is implemented and locally previewed. The task remains Pending because the maintainer has not accepted the
preview, the unique integrator has not supplied an accepted clean W7.4 exact Candidate/import SHA, Phase B has not
started, and all post-acceptance mechanical evidence remains intentionally unrun.
