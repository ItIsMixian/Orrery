# ADR-0028: Shell-first Observatory and Incremental Workstream Graph Cache

Status: Accepted

Date: 2026-09-01

Maintainer acceptance: accepted on 2026-09-01 when the maintainer authorized development after rejecting the
full-page startup gate and repeated full Workstream Graph scans.

Amends: [ADR-0016](0016-unified-observatory-shell-and-single-local-entry.md)

Preserves: [ADR-0022](0022-elkjs-workstream-graph-layout-engine.md),
[ADR-0025](0025-two-explicit-windows-launchers.md),
[ADR-0027](0027-retain-history-without-bulk-ui-and-recover-archived-lineage.md)

## Context

U2.4 corrected the v0.3.1 cold-start failure by binding the loopback listener before the full Unified render and
showing a small startup page. That removed roughly 95 seconds of invisible waiting, but it did not satisfy the Unified
Shell contract. The browser is still replaced by a full-page `Orrery 正在启动` gate until every consumer finishes,
and the expensive Workstream Graph provider is still part of the whole-page render. The user cannot open documents,
search, Personal, Team or Maintenance while only Graph is slow.

The same implementation rebuilds the Graph provider during each cold start. The recorded U2.4 profile reached 751
child processes and spent most time in Workstream relation/history work, although the base document site completed in
about 2.5 seconds. A startup-only in-memory payload avoids request-time recomputation after the first build, but it is
discarded when the process stops and therefore is not an incremental cache.

ADR-0016 already says optional consumer failure must not disable the shell or other consumers. This amendment makes
that requirement concrete for startup and gives the Workstream Graph a derived, Git-private acceleration layer. It
does not change relation facts, W7.4 history recovery, ELK geometry or confirmation authority.

## Decision

1. **Shell readiness is independent from Graph readiness.** The dynamic Orrery shell, document reader/search and all
   non-Graph consumers that do not depend on Graph must become usable without waiting for the Workstream Graph
   provider or ELK. A slow, empty, stale or failed Graph is represented inside the existing Graph page only; it never
   replaces the whole application with a blocking startup page.
2. The listener may still bind first so concurrent launches reuse one PID/port/instance, but normal launch opens the
   browser against a navigation-capable shell rather than a global progress card. The maintained Windows target is a
   usable shell within three seconds. If the base shell is still assembling, `/` returns the same shell/navigation
   frame with page-local loading states, not a second startup product.
3. **Dynamic Graph activation is asynchronous and non-blocking.** The Graph route returns bounded state immediately
   and the existing Graph page hydrates when a projection becomes available. Successful refresh swaps one complete
   projection atomically; partial facts, partial HTML and partially laid-out geometry are never presented as current.
4. Observatory owns a versioned Git-private `workstream-graph-cache-v1` acceleration store. It contains only the
   sanitized semantic projection, source fingerprint/versions, generation and timestamps needed to validate reuse.
   It is excluded from author documents, packages, releases and Team synchronization, and it never becomes relation,
   history, closure or Validation authority.
5. A matching, compatible cache is served immediately without a full Graph provider run. A mismatched input
   fingerprint may be shown only as visibly stale/refreshing last-known data while one background refresh runs. An
   absent, corrupt or incompatible cache produces a Graph-local loading/unavailable state and one background rebuild;
   it does not block or fail the shell.
6. Graph inputs use a versioned bounded manifest owned by the existing providers: relation/capture events, task-series
   and program metadata, live Workstream session identities, durable history index/archived-lineage evidence,
   integration identity and the relevant provider/schema versions. Computing the startup fingerprint must not run
   full source, diff, ignored-file or per-worktree status scans. If currentness cannot be proven cheaply, the cache is
   marked stale/Unknown and refreshed in the background rather than called current.
7. Owners that append or atomically replace a Graph input emit a local invalidation/generation signal. A bounded
   metadata fingerprint remains the compatibility fallback for external/manual changes. Full Graph recomputation is
   allowed only for first use, incompatible/corrupt cache, proven input change, explicit local refresh or a missing
   owner signal detected by the bounded fallback—not mechanically on every launch.
8. Graph refresh is single-flight and cancellable. Stop during shell or Graph activation reclaims the worker,
   listener, marker and managed helpers. A failed refresh preserves an older valid projection as visibly stale with a
   sanitized reason; it never silently labels stale data current or erases the prior cache before atomic replacement.
9. Static mode remains a self-contained read-only build: it may perform one explicit Graph build and embed that
   projection, exposes no polling/control API and never depends on a runtime cache. Dynamic and static modes share the
   same Graph semantics and Orrery presentation.
10. W7.4 remains the owner of historical identity/lineage recovery, full-versus-compact Graph behavior and relation
    decision presentation. U2.5 may adapt the delivery boundary only after importing an accepted exact W7.4
    Candidate; it must not reimplement, infer, reduce or overwrite those facts or UI semantics.
11. The two launcher names, one supervisor, zero-network Personal default, Team opt-in/request-only boundary,
    same-origin mutation controls, explicit legacy rollback and pinned offline ELK contract remain unchanged.
12. This decision authorizes a local Worktree Candidate and maintainer preview only. It does not enable automatic
    cleanup, start W6.2, change a component/public version, push main, run Promotion or publish a release.

## Reasons

- A consumer-specific loading state matches the product model: Graph is one optional derived view, not a prerequisite
  for reading the project or using other local tools.
- A validated last-known projection makes repeated launches fast without pretending a cache is project authority.
- Event/generation invalidation handles normal Orrery writes cheaply, while a bounded metadata fingerprint prevents a
  missed event from becoming permanent stale state.
- Keeping the semantic projection atomic preserves ADR-0022's separation between Orrery facts and ELK geometry.
- Deferring Graph presentation wiring until the accepted W7.4 exact Candidate avoids replacing recovered historical
  relationships with an older branch implementation.

## Consequences

- `render_unified_site()` must be split so base shell composition and Graph projection are not one readiness unit.
- Runtime health must expose shell and per-consumer readiness separately; global `ready` can no longer mean “every
  optional consumer finished.”
- The Graph dynamic frontend needs a bounded hydration/status path while static builds retain embedded projection.
- A new Git-private cache contract, atomic writer, compatibility validator, invalidation hook and diagnostics are
  required. Cache deletion/rebuild remains safe because the cache has no authority.
- W7.4 and U2.5 can be separate Workstreams, but final Graph delivery wiring must consume the accepted W7.4 bytes and
  be reviewed for overlap before integration.

## Mapping

- Approved Design: [Shell-first Graph Activation and Incremental Cache](../design/unified-observatory-shell-first-graph-activation.md)
- Implementation Plan: [U2.5 Shell-first Graph Activation and Incremental Cache](../implementation/plans/2026-09-01-u2-5-shell-first-graph-activation-and-cache.md)
- Pending Validation: [U2.5 Shell-first Graph Activation and Incremental Cache](../validation/2026-09-01-u2-5-shell-first-graph-activation-and-cache.md)
