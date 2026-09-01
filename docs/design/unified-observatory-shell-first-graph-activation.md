# Unified Observatory Shell-first Graph Activation and Incremental Cache

Status: Approved

Date: 2026-09-01

Governing ADR: [ADR-0028](../decisions/0028-shell-first-observatory-and-incremental-graph-cache.md)

Maintainer approval: approved on 2026-09-01 for implementation as an independent U2.5 Workstream. Approval does not
claim that the cache, asynchronous delivery, W7.4 integration, validation, default transition or release exists.

## 1. User experience contract

Normal launch has one visible URL and one Orrery shell. Documents, search, Personal, Team, Maintenance and other
non-Graph pages remain navigable while Workstream Graph is loading or refreshing. The Graph page uses its existing
visual surface and one local state region:

| Graph state | User-visible behavior |
|---|---|
| `empty` | Graph-local loading state; the rest of Orrery is fully usable. |
| `cached-current` | Show the validated cached projection immediately; no full provider run on launch. |
| `cached-stale` / `refreshing` | Show last-known projection with a visible stale/refreshing marker; disable any wording that implies current evidence. |
| `ready` | Atomically replace the Graph-local projection and lay it out offscreen before display. |
| `failed` | Keep valid last-known data visibly stale when available; otherwise show the existing bounded unavailable/ledger state. |

The full-page U2.4 startup card is not the normal shell experience. A very short base-shell assembly phase may exist
internally, but `/` remains a navigation-capable shell and Graph never controls global readiness.

## 2. Runtime composition

Dynamic startup is separated into two pipelines:

```text
launcher
  -> bind/reuse one loopback supervisor identity
  -> compose and activate base shell (Graph slot only)
  -> open the public URL once
  -> load/validate Graph cache
  -> if needed, refresh Graph in one owned background worker
  -> atomically publish projection generation
  -> browser hydrates/re-lays out only the Graph slot
```

Base shell composition continues to reuse the existing docsite, Personal, Team, relation-inbox, Authority and
Maintenance consumers. The split must not create a second HTML application, route namespace, listener, browser page
or visual design.

Static builds follow a separate explicit path: build the complete read-only page once, embed Graph data and make no
runtime API request. A `file:` page must not display a fake dynamic refresh control.

## 3. Readiness model

Global runtime health and consumer readiness are independent:

```json
{
  "contract_type": "unified-observatory-health-v1",
  "status": "ready",
  "consumers": {
    "workstream-graph": {
      "status": "refreshing",
      "generation": 4,
      "cache_state": "cached-stale"
    }
  }
}
```

The existing top-level contract/version may be extended compatibly; a breaking shape requires an explicit version
change. `status=ready` means the shell is usable and safe, not that every optional consumer is current. Shell
integrity, route collision or unsafe capability escalation may still fail startup closed. A Graph provider/cache/layout
failure quarantines Graph only.

`GET /api/v1/workstreams/graph` is non-blocking and returns one bounded delivery envelope containing:

- delivery/cache state and generation;
- sanitized captured/refreshed timestamps;
- compatible provider/projection/cache versions;
- currentness/staleness reason codes;
- one complete semantic projection when available;
- `writes_author_documents=false`, `network_performed=false` and read-only authority markers.

The endpoint never starts a second refresh per request. An explicit local refresh, if exposed, uses the existing
same-origin cookie boundary and only requests background recomputation; it cannot alter relation facts.

## 4. Cache ownership and layout

The cache is stored beneath the repository Git-private Orrery namespace, for example:

```text
<git-common-private>/orrery/cache/workstream-graph-v1/
  current.json
  last-known.json
  invalidation.json
```

The implementation may choose equivalent exact filenames, but all entries must be regular bounded files, reject
links/traversal, validate exact fields and versions, and use temporary-file plus atomic replace. The last known valid
entry is retained until a new entry is fully validated and committed. Runtime logs may record timing/counts but not
private absolute paths, Prompt/answer/transcript, source/diff body or credentials.

`workstream-graph-cache-v1` contains only derived delivery data:

- cache contract/schema version;
- provider and projection schema versions;
- source manifest fingerprint and generation;
- semantic projection and its existing graph/projection hashes;
- created/refreshed timestamps and bounded diagnostics.

It does not contain a second relation store, rewrite archived sessions, invent closure, or confirm a proposal. Removing
the cache is always a performance reset, never loss of project history.

## 5. Input manifest and invalidation

The source manifest is deterministic and bounded. It identifies only inputs already owned by the relation/history
providers:

- effective/proposed relation and relation-capture event stores;
- task-series and program/phase metadata;
- live Workstream session identity records relevant to Graph;
- the durable W7.4 history index and bounded archived-lineage records;
- configured integration ref plus the exact OID required by the provider;
- provider, projection, history and cache schema versions.

Normal invalidation is event/generation driven. Writers append or atomically update a small Git-private invalidation
record after their own successful write. U2.5 exposes that hook for later W6.2 cleanup/history-snapshot work but does
not implement cleanup.

At startup, a compatibility fallback hashes/stat-checks only the bounded metadata/input files and integration identity.
It must not call full `git status`, enumerate source/diff/ignored files, or invoke the heavy relation provider across
every registered worktree. If an input cannot be checked safely or cheaply, reuse is `stale/unknown`, never current.

A full Graph refresh runs when and only when:

1. no valid cache exists;
2. cache/provider/projection/history versions are incompatible;
3. the invalidation generation or bounded source fingerprint changed;
4. the maintainer explicitly requests refresh; or
5. the previous refresh failed before any valid cache was produced.

Unchanged restarts reuse the exact validated generation and do not invoke the full Graph provider.

## 6. Frontend hydration

Dynamic base HTML includes the existing Graph navigation identity, controls/legend shell, accessible ledger container
and a JSON-free loading region. It does not embed a stale projection as if it were current. Browser code fetches the
delivery envelope, ignores older generations, constructs the same semantic model used by the accepted W7.4 page and
runs pinned local ELK offscreen before one DOM/SVG swap.

Full/compact mode, local history-summary expansion, selected relation, zoom anchor and reduced-motion behavior remain
owned by W7.4. A refresh preserves compatible local view state where possible; missing identities are dropped safely.
The frontend never performs relation inference or cache currentness decisions.

Polling is bounded and active only while the Graph route reports `empty` or `refreshing`. Ready/current generations do
not continue polling. Stop/unload does not become cleanup or relation authority.

## 7. Failure and security behavior

- Cache parse/version/hash failure quarantines the cache and schedules one refresh; it does not fail the shell.
- Provider failure leaves a last-known projection visibly stale or the existing unavailable/ledger state.
- ELK failure leaves the same semantic ledger and `布局不可用`; no automatic legacy fallback occurs.
- Stop cancels/drains the single Graph worker and then applies the existing supervisor shutdown order.
- Personal remains zero-network; Graph cache/refresh performs no external network and never enters Team metadata.
- All returned errors are sanitized and bounded; no absolute private paths or raw exception trace reach the browser.

## 8. W7.4 integration boundary

U2.5 may implement the shell/cache owner on disjoint runtime files immediately. It must not edit or freeze these
W7.4-owned presentation/relation surfaces until an accepted, clean W7.4 exact Candidate is available and imported:

- `workstream_graph_presentation.py`;
- `workstream_relation_graph.py`;
- `build_workstream_relation_graph.py`;
- relation/history provider files changed by W7.4;
- the shared validation mapping entries for those paths.

After import, U2.5 adapts delivery only. The accepted full graph remains default, compact mode retains W7.4's exact
visibility rules, all recovered lineage/pending/Unknown evidence remains present, and no bulk history UI is added.

## 9. Compatibility and rollout

- `Start Orrery.vbs` and `Start Orrery Console.bat` remain the only root launchers and reuse one runtime identity.
- `serve_orrery.py --legacy` remains the explicit whole-shell rollback.
- Root and project-template managed runtime/build files remain byte-equivalent where the release contract requires it.
- Existing static builders and tests may use an explicit eager Graph mode; dynamic default uses asynchronous delivery.
- U2.5 is a local Candidate only. Public template/version/manifest/Promotion/release work requires a separate accepted
  release task after maintainer preview and focused validation.
