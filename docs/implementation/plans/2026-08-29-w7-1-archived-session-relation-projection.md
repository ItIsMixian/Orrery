# W7.1 Archived Session Relation Projection

Status: Completed

Date: 2026-08-29

Fact scope: `codex/w7-1-archived-session-relation-projection`, exact task base
`SH1-real-self-host-collaboration-acceptance@f74397aeae860dd386c390f18d2dde6261ff530b`.

Governing decisions:

- [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)
- [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)
- [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md)

Source finding: [SH1 Validation](../../validation/2026-08-29-sh1-real-self-host-collaboration-acceptance.md).

## Objective

Add a bounded, dependency-light, read-only Core resolver for the explicitly allowed dated v1 layout under
`$GIT_COMMON_DIR/orrery/retired-worktree-sessions/`. Use a retired session only when an existing native or legacy
relation references a Workstream whose live endpoint is absent. Restore the archived endpoint's exact closed,
offline, current, superseded, HEAD, branch and declared Scope axes without giving archive evidence runtime or
execution authority.

The CI1 → W5D SH1 finding is closed only when a synthetic equivalent restores W5D as a closed archived endpoint,
keeps the edge governed by its own current/stale evidence, and never turns archive presence into active-tip or
conflict suppression authority.

## Boundaries

- Keep Personal Mode zero-network and all archive reads zero-write. Do not create, repair, migrate or rewrite the
  archive, a Workstream session, relation history, worktree or author document during graph loading.
- Read only the exact Git-common-private archive root and its allowed dated-entry/worktree.json layout. Bound
  directory entries, files, depth, per-file bytes and aggregate bytes; reject symlink, reparse, traversal,
  non-regular, malformed, unknown-schema and inconsistent identity evidence.
- Live endpoints always win. Do not inject unreferenced historical Workstreams into the graph. Equivalent archive
  copies deduplicate deterministically; conflicting copies leave the referenced endpoint Unknown.
- Expose only a safe content-derived archive evidence ID/hash. Never expose an absolute private path to Core graph,
  Observatory or Team consumers.
- Archived nodes are permanently non-live: never active tips, Review Ready, online, discovery/apply/undo targets or
  execution-capable objects. W7B transaction, receipt, recovery and preservation behavior remains unchanged.
- Keep native relation records ahead of matching legacy projection and preserve deterministic graph hashing. When
  archive evidence changes graph content, its safe evidence hash participates in the graph hash.
- Do not modify W6.1 maintenance/cache, A3 Authority, U1, README/assets, default UI, release surfaces, real
  Git-private archives, root PROGRESS/HANDOFF, subsystem State, DEVLOG or shared indexes.
- `scripts/ci/test-shards.json` is explicitly outside this branch. The Validation/handoff will list every new test
  ID that the central integrator must register after CI6/A3 reconciliation.

## Implementation sequence

1. Add failing focused regressions for CI1 → archived W5D, live precedence, equivalent/conflicting duplicates,
   unreferenced exclusion, malformed/schema/identity errors, symlink/reparse/traversal/non-regular/oversize/limits,
   zero-write/zero-network and non-executable archive nodes.
2. Implement the bounded archive root resolver and deterministic Workstream index in Core. Keep unsafe input
   fail-closed and keep conflicts as hash-bound Unknown endpoints.
3. Join only relation-referenced, live-missing archived endpoints into the existing legacy node projection. Do not
   project archived lineage as new edges and do not enable archives in W7B discovery.
4. Keep the frozen relation graph v1 schema byte-for-byte stable. Preserve branch and
   `origin=retired-session-archive` in the resolver index; project only the existing node fields into Graph and use
   the safe archive evidence ID/hash to bind the full archived endpoint without widening the v1 protocol.
5. Run focused relation tests, dependency-light Fast/Checkpoint, CI static/integrated/repository/diff gates, then
   write the independent W7.1 Validation. Do not run the full long suite.

## Acceptance contract

- Exact live session beats any archive copy for the same Workstream.
- One relation-referenced missing endpoint resolves from one or more byte/semantic-equivalent valid archives.
- Conflicting valid archives do not select by path, date or mtime; the endpoint stays Unknown with a safe conflict
  evidence hash.
- Archive layout and content limits are deterministic across ordering and platform path spelling.
- CI1 → W5D restores W5D's true closure axes and branch/HEAD/Scope evidence while the edge remains independently
  current/stale and cannot suppress because the predecessor is archived closed/offline.
- Native relation-store precedence, W7B transaction/recovery, author-tree cleanliness, zero-network and graph hash
  determinism remain covered.

## Validation ladder

Focused:

```text
python -X utf8 -m unittest tests.test_workstream_relations -v
```

Checkpoint adds the repository Fast/Checkpoint profiles and the existing CI static, integrated installation,
repository/link/forbidden-artifact and diff gates. Full Promotion, hosted checks, main integration and release are
the central integrator's later responsibility on a separately frozen exact SHA.
