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

## Central review correction preview

Product correction commit: `6f492b03e379e57adefcca1d476b80b8d9663574` on the existing U2.5 branch and six-path
scope. Phase B and W7.4-owned presentation/relation/history files remain untouched.

- The first real HTTP 200 arrived in 446 ms and contained `data-orrery-runtime-state="starting"`, the six-entry Orrery
  navigation and a Graph-local loading region. It did not contain the former full-page `Orrery 正在启动` card. A second
  normal launch while that same runtime was still starting reused the same URL and exited successfully in 510 ms.
- Input manifest schema 2 explicitly included the primary `.git/orrery/worktree.json`, three live worktree session
  records and a bounded hash over all three registered live worktree HEAD/ref identities. A real Git-private scope
  refresh changed the source fingerprint from `d0a8253...` to `4c07e4c...`; the product commit changed it again from
  `eb2bb12...` to `a78be36...` through the live HEAD identity.
- Launching after that HEAD change returned Graph `refreshing`, cache state `cached-stale`, reason
  `source-fingerprint-changed` and one provider run instead of `validated-cache-hit`.
- After one complete provider refresh, an unchanged restart returned `cached-current`, reason `validated-cache-hit`
  and `provider_runs_since_start: 0`.
- With a provider deliberately blocked, `close(timeout=0.2)` returned in 201 ms rather than waiting indefinitely.
  After the preview released the provider, the daemon worker was reclaimed and the current-cache hash remained
  unchanged, proving cancellation did not publish a new generation.
- A real runtime stopped while Graph was `refreshing` in 1.201 seconds; the marker and recorded PID were both gone.
  Graph activation, corpus activation and independent relation-capture workers now use bounded shutdown joins.
- Dynamic `GET /api/v1/workstreams/relations` returned an honest `loading` payload in 16 ms while background work was
  active; it no longer waits up to 45 seconds for the Graph provider.
- The correction used only Python syntax/import checks and local lifecycle previews. One discarded PowerShell preview
  command accidentally invoked a no-argument Python process because the function-local `$args` automatic variable
  shadowed its launch arguments; that exact process was terminated before the corrected preview, and it produced no
  product runtime marker or evidence.

This correction evidence addresses the central review findings but is still pre-acceptance worktree evidence. It does
not authorize or claim unittest, Fast, Checkpoint, Candidate, Promotion, W7.4 hydration or release validation.

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

Phase A and its central-review corrections are implemented and locally previewed. The task remains Pending because
Phase B has not produced or received maintainer acceptance for its self-host preview, W7.4 remains validation-pending,
and all post-acceptance mechanical evidence remains intentionally unrun.

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

Revision-3 refresh reduced the blocker to three imported State/DEVLOG paths against the clean frozen W7.4 ancestor.
Plan revision 4 requires an exact matching freeze receipt, Git ancestry and a clean peer before those inherited
findings can be excluded from U2.5's own refresh; topology diagnostics and every dirty/non-ancestor negative case remain
Pending focused evidence.

Central exact `4e64bbb88e2356c729bf69259a58ca96e0e44de3` passed the focused frozen-ancestor regression 1/1 in
25.511 seconds: full topology retained the conflict, descendant scope refresh proceeded, and one subsequent dirty peer
byte restored L3. No broader suite, U2.5 product write, peer closure or worktree removal ran.

## 2026-09-02 Phase B delivery-slice preview

- U2.5 imported task-description exact `e7c9478ad7d721a86e9b483d1dfd9ca5adbc9d8c`, including frozen-ancestor
  correction `4e64bbb88e2356c729bf69259a58ca96e0e44de3`. Full local-worktree scope refresh retained topology
  diagnostics, returned zero findings, and after the revision-4-authorized local L2 confirmation recorded scope
  revision 13 with both `allowed=true` and `local_work_allowed=true`.
- The expected-write set remained the seven revision-3 delivery paths with empty validation surfaces. No W7.4 Core
  relation/history, Graph presentation/adapter, shared mapping/test, State or DEVLOG path was edited.
- New `workstream_graph_delivery.py` maps a complete cached projection to one bounded browser generation containing the
  exact frozen W7.4 panel renderer, CSS, pinned local ELK bundle and presentation script. The dynamic endpoint adds this
  bundle only for a complete ready projection; cache authority and relation truth remain unchanged.
- The dynamic shell polls only while Graph is empty/refreshing, rejects older generations, lays out the new article
  offscreen and replaces only the Graph article after layout completes or exposes the existing W7.4 ledger/failure
  state. Compatible lens/mode/filter/expansion/selection/zoom/viewport state is carried into later generations.
- Python syntax/import checks passed for the root/template runtime and builder, cache owner and new delivery owner. A
  Node syntax parse of the emitted hydration JavaScript also passed. These were startup checks, not automated tests.
- A real self-host restart reached first HTTP in 491 ms and logged base-shell ready in 2.939 seconds. The unchanged
  generation-2 restart returned `cached-current`, `validated-cache-hit`, a complete browser delivery and
  `provider_runs_since_start: 0`.
- One explicit Git-private preview invalidation advanced generation 1 to 2. The running owner observed it without a
  duplicate worker, exposed `refreshing / cached-stale` with the prior complete delivery and exactly one provider run,
  then atomically published generation 2 after 13.564 seconds. The projection hash remained
  `a11409d0fe140194b5baf8a21e2de9cbccec1aee9b55dfd6f70d0ea77c24a200`.
- The delivered live projection retained 37 strict history records (6 closed / 31 retired), 11 recovered archived
  lineage edges and seven proposed relations. Its live topology now contains 28 nodes / 22 relations because newer
  registered tasks are real current inputs; this observation does not replace W7.4's accepted frozen 25/18 full and
  15/8 compact preview baselines.
- The preview remains running at `http://127.0.0.1:8765/` for maintainer inspection. No Computer Use, external network,
  unittest, Fast, Checkpoint, Candidate, Promotion, cleanup or release action ran. Full/compact visual parity and the
  atomic browser swap remain pending maintainer acceptance.

## 2026-09-02 acceptance-gate correction

The maintainer rejected full-page visual inspection as evidence for U2.5's internal cache/delivery behavior and
accepted a runtime-receipt-first gate. The task's recorded 491 ms first HTTP, 2.939 second usable shell, unchanged
`cached-current` restart with zero provider runs, single generation refresh and atomic publication are eligible inputs
to that receipt without rerun. Only bounded evidence for no page-wide blank/flash, semantic-layout preservation and
  stop-time cleanup remains to be completed before structural Candidate Freeze. No full-page subjective approval or
  broad automated tier is required.
