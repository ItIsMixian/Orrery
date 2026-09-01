# Implementation Plan: U2.5 Shell-first Graph Activation and Incremental Cache

Status: Approved for implementation; W7.4 presentation wiring and automated validation remain gated

Date: 2026-09-01

Task code: U2.5

Task series: `unified-u`; task code `U2.5`; intended series order `25`; explicit predecessor `U2.4`

Primary subsystem: `documentation-system`

Affected subsystems: `release-and-toolchain`, `test-coverage`

Governing decision: [ADR-0028](../../decisions/0028-shell-first-observatory-and-incremental-graph-cache.md)

Approved Design: [Shell-first Graph Activation and Incremental Cache](../../design/unified-observatory-shell-first-graph-activation.md)

Predecessor implementation: U2.4 exact `00b2eb4fa28a606cdb532c7938e46482950e8233`, locally integrated by merge
`27480f54ff0e69a9463651cf4138254e02e5083d`. These are local Candidate/integration facts, not public v0.3.1 bytes.

Presentation dependency: W7.4 has an accepted full-graph preview but its compact mode and product branch are not yet
accepted/committed. U2.5 may begin on disjoint shell/cache infrastructure, but final Graph hydration must wait for an
accepted clean W7.4 exact Candidate and import it without replacing relation/history/UI semantics.

## Objective

Make Orrery usable as soon as its base shell is ready while Workstream Graph loads independently, and make unchanged
restarts reuse a validated Git-private Graph projection instead of repeating the full relation/history scan.

## Authorized implementation

### Phase A — disjoint shell and cache infrastructure

1. Register U2.5 on an independent branch/worktree from the exact task-description version, bind the existing
   `unified-u` task series and explicit U2.4 predecessor without inventing a program/phase membership, acknowledge the
   authority paths and refresh Git-private scope before product writes.
2. Record a zero-write baseline for base-shell time, Graph provider time/subprocess count, first HTTP, first usable
   shell and two unchanged consecutive launches. Do not use Computer Use or run a test suite.
3. Split dynamic Unified composition into a base-shell path and a Graph activation path. Static builds retain explicit
   eager Graph projection. Dynamic `/` and non-Graph APIs become usable without Graph readiness.
4. Add the versioned Git-private Graph cache owner, strict validator, bounded input manifest/fingerprint, atomic current
   and last-known writes, generation invalidation and single-flight background refresh.
5. Extend runtime health/capability state so shell readiness and Graph readiness are reported separately. Preserve one
   PID/port/URL, same-origin controls, sanitized diagnostics, no-window policy, console mode and deterministic stop.
6. Keep root/project-template runtime and builder copies equivalent. Do not change launcher names or add an entry.

Phase A may change only disjoint runtime/cache surfaces. It must not modify W7.4-owned Graph presentation/relation
files, shared Graph mapping entries or W7.4 documents while that worktree is dirty.

### Phase B — consume the accepted W7.4 Graph

7. Stop before Phase B and report the exact W7.4 dependency. Resume only after the unique integrator supplies an
   accepted clean W7.4 Candidate/import SHA and scope refresh remains allowed.
8. Adapt the accepted W7.4 dynamic Graph page to hydrate a complete delivery generation from the non-blocking endpoint.
   Preserve full default mode, compact history rules, local expansion, all recovered lineage, rejected diagnostics,
   series lines, pending proposals, zoom behavior and pinned offline ELK/explicit-legacy boundaries.
9. Render ELK/layout offscreen and atomically replace only the Graph region. Poll only while empty/refreshing and ignore
   old generations; preserve compatible local selection/mode/zoom state.
10. Wire Graph/history/relation/session writers to the invalidation hook only at their existing successful atomic-write
    boundaries. Do not add inference, confirmation, cleanup or a second source of relation truth.
11. Produce a real self-host preview using the accepted W7.4 graph. Stop for maintainer inspection before any unittest,
    Fast, Checkpoint, Candidate or Promotion command.

## Preview acceptance checks

The maintainer must be able to verify, without Computer Use:

1. normal launch enters the Orrery shell rather than the full-page startup card;
2. documents/search/Personal/Team/Maintenance remain usable while only Graph shows a local loading state;
3. first uncached Graph eventually becomes ready without a page-wide reload or visual flash;
4. an unchanged restart shows the validated cached Graph immediately and records zero full Graph provider runs;
5. one bounded input change marks the prior view stale/refreshing and produces exactly one atomic refresh;
6. full and compact W7.4 modes still show the same accepted relationships and history rules;
7. stopping during refresh leaves no worker, listener, marker or helper.

Before this acceptance, syntax/import checks required to start the preview are allowed; automated test suites are not.

## Focused post-acceptance validation

After explicit maintainer acceptance, run only the existing affected owners plus bounded new assertions folded into
those owners:

- base shell is usable while the Graph provider is deliberately blocked;
- unchanged second launch validates/reuses cache with zero provider recomputation;
- changed generation/fingerprint triggers one single-flight refresh;
- corrupt/incompatible cache is quarantined without blocking the shell;
- failed refresh retains valid last-known data as stale and exposes no private path;
- static build remains embedded/read-only with no dynamic fetch;
- root/project-template parity, Python/JavaScript syntax and `git diff --check`.

Do not run Fast, Checkpoint, Candidate, Promotion or a release matrix unless a later explicit task amendment authorizes
it. Do not repeat unchanged evidence.

## Expected implementation surfaces

- `scripts/docsite/serve_orrery.py` and its project-template copy;
- `scripts/docsite/build_unified_observatory.py` and its project-template copy;
- a versioned cache/delivery owner under `packages/project-orrery-observatory/src/project_orrery_observatory/`;
- existing Unified owner tests after preview acceptance;
- W7.4 Graph presentation/adapter and focused Graph owner only in Phase B after exact dependency import;
- `scripts/ci/change-mapping.json` only after both task diffs are reconciled by the unique integrator;
- subsystem State, this Validation and DEVLOG in the task branch. Root PROGRESS/HANDOFF remain integrator-owned.

## Hard boundaries

- preserve every W7.4 history identity, archived-lineage edge/rejection, pending proposal and relation authority;
- cache is derived acceleration only: no relation/history/closure/Validation facts and no Team synchronization;
- no full source/diff/ignored/per-worktree status scan on unchanged startup;
- no second listener/browser page/launcher, no external network and no Computer Use;
- no automatic cleanup, worktree/branch/archive deletion or W6.2 implementation;
- no component/public version, manifest, protected main, push, tag, asset, Promotion or Release operation;
- preserve dirty peer work and do not edit W7.4-owned surfaces before the exact dependency gate.

## Completion definition

- shell and non-Graph pages are usable within the maintained three-second target without waiting for Graph;
- Graph has an honest local loading/current/stale/refreshing/failed lifecycle and updates atomically;
- unchanged restart reuses a compatible cache and performs zero full Graph provider runs;
- a proven input change schedules exactly one refresh, and failure/corruption does not block the shell or lose the
  last-known valid projection;
- accepted W7.4 full/compact behavior and evidence counts are unchanged after delivery wiring;
- maintainer preview is accepted, focused post-acceptance checks pass and the task branch is clean;
- no integration, release or public capability is claimed.
