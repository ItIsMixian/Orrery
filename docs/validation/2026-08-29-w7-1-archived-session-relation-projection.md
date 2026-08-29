# W7.1 Archived Session Relation Projection Validation

Date: 2026-08-29

Status: implementation and bounded validation complete; central test-shard reconciliation and exact Candidate
promotion remain outside this branch

Fact scope: `codex/w7-1-archived-session-relation-projection`, created directly in the delegated worktree at exact
task base `f74397aeae860dd386c390f18d2dde6261ff530b`. No second worktree was created. This branch does not update root
PROGRESS/HANDOFF, subsystem State, DEVLOG, shared indexes, release surfaces or real Git-private archives.

## Registration and write boundary

Before the first author-file write, Git-private Workstream
`W7.1-archived-session-relation-projection` was registered with branch
`refs/heads/codex/w7-1-archived-session-relation-projection`, exact HEAD/task base/validated HEAD `f74397a…`,
`base_workstream_id=SH1-real-self-host-collaboration-acceptance`, and the four exact expected author paths used by
this task. The session SHA-256 was `465A1B6B35603A5170696812C8425B285F0E4093D7649C71CD63A7A33FC8097C`.

SH1's extant live session was bound to an older HEAD even though its branch tip was the required `f74397a…`.
Registration therefore preserved honest `lineage.status=parent-unverified-unknown`; it did not rewrite SH1 or claim
that a stale parent session had been mechanically verified. The branch session became stale after the expected
author writes and was not refreshed to manufacture a clean review boundary.

No archive, live session after registration, deleted worktree path, relation store during product loading, W7B
transaction, maintenance/cache state, Team state, network target, `main`, remote or release artifact was written.
The only author paths changed are the W7.1 Plan, this Validation, relation Core and its focused tests.
`scripts/ci/test-shards.json` remains byte-for-byte outside the branch diff.

## Archive resolver contract

Core now derives exactly one allowed root from local Git:
`$GIT_COMMON_DIR/orrery/retired-worktree-sessions/`. It accepts only the bounded dated-v1 layout
`YYYY-MM-DD/<branch-slug>-<8..40 hex HEAD prefix>/worktree.json`. The reader:

- uses fixed depth, deterministic sorted enumeration, at most 128 session files, 64 KiB per file and 4 MiB total;
- rejects unsafe date/entry names, traversal-shaped entries, extra depth/content, symlink/reparse paths,
  non-regular files, read-time identity/size drift, invalid UTF-8/JSON, unknown collaboration schema, malformed
  sessions, unresolved HEADs, branch-to-HEAD drift, entry-to-branch/HEAD drift and lineage-to-HEAD drift;
- reads no ordinary disk tree, arbitrary path, author document or network surface and never creates the archive
  root when it is absent;
- indexes only Workstream IDs explicitly referenced by native or live-legacy relations and missing from the live
  session set. Unreferenced history is counted but is not projected into Graph;
- gives a current live session unconditional precedence. Byte-identical and canonical-JSON-equivalent archives
  deduplicate deterministically; any distinct semantic records for one referenced Workstream produce one
  hash-bound Unknown endpoint instead of selecting by date, path or mtime;
- resolves only the proven retired lifecycle tuple `closed/offline/current/superseded`. The resolver index preserves
  exact HEAD, branch, declared Scope evidence, `origin=retired-session-archive`,
  `visibility=git-private-local-only` and `observability=retired-archive-local`;
- emits only `retired-session-archive:sha256:<semantic-hash>` or a safe conflict/unresolved hash. Neither Graph nor
  the resolver index exposes an absolute private archive path.

The version-1 relation graph protocol and its frozen schema/brand hash remain byte-for-byte unchanged. Its existing
node `origin` enum therefore continues to identify the projection mechanism as `legacy-session-projection`; the
archive-specific origin remains in the resolver index, while the graph's safe source evidence ID, visibility and
observability identify the archived endpoint and bind the full archived session semantics into `graph_hash`.
This avoids an unapproved protocol/release/A3 change while retaining the required provenance boundary.

Archive evidence is endpoint evidence only. Archived lineage never creates new edges; discovery explicitly excludes
the archive resolver, so an archive cannot become an apply/undo target. A closed/offline archived node is never an
active tip, Review Ready or realtime-online state, and the index exposes
`execution_supported=false`, `writes_performed=false`, `network_performed=false` and no destructive action.
Native records continue to replace matching legacy triples before graph construction. W7B execution/recovery code
and its transaction stores were not modified.

## SH1 finding closure

The synthetic CI1 → W5D journey creates a live current CI1 lineage whose W5D worktree is removed while a valid
retired session remains. Graph loading restores W5D as
`session=current/lifecycle=closed/runtime=offline/evidence=current/scope=current/closure=superseded`, exact HEAD and
completed status. The resolver separately proves its exact archived branch.

The CI1 → W5D edge remains independently governed by current/stale endpoint evidence. It is not made effective or
suppressed merely because an archive exists; the succession plan retains no direct-pair suppression for the closed
predecessor. Changing a non-axis archived semantic field changes both the safe archive evidence hash and graph hash.
Discovery leaves the missing live parent Unknown, proving that archive evidence is not an execution candidate.

The same read-only resolver was exercised against this repository's real Git-private state without changing it.
The final resulting graph hash was `ff0d7c7617b4c1a60d51b112a136cac54c5e7513189e25e8c75560a478f63f5a`.
It restored real W5D HEAD `ae6913ee354511605ab9349244b1beaea913bfac`, branch
`refs/heads/codex/w5d-lan-collaboration-harness`, the closed/offline/current/superseded axes and safe evidence ID
`retired-session-archive:sha256:a7748e898d567b73e33fd332de9ebd8c76fbdb65f87f5d6bb7e783a6fdff5a07`.
CI1 → W5D remained stale/evidence-driven with no automatic suppression. The native relation store remained absent.

## Regression-first and focused validation

The first focused run was made before the resolver existed and failed at import of
`load_archived_session_index`; it is retained as the required red regression, not counted as a pass.

New exact unittest IDs:

1. `test_workstream_relations.WorkstreamRelationTests.test_archived_relation_endpoint_restores_closed_axes_and_binds_graph_hash`
2. `test_workstream_relations.WorkstreamRelationTests.test_archived_session_live_precedence_equivalent_duplicates_conflict_and_unreferenced`
3. `test_workstream_relations.WorkstreamRelationTests.test_archived_session_reader_rejects_malformed_unknown_inconsistent_and_unsafe_inputs`
4. `test_workstream_relations.WorkstreamRelationTests.test_archived_session_index_is_read_only_zero_network_and_has_no_execution_surface`

Final focused evidence:

- the four new IDs: 4/4 PASS in 37.809s;
- complete `tests.test_workstream_relations`: 19/19 PASS in 72.709s;
- existing W7B dependency-light execution/no-delete contract: 1/1 PASS in 0.004s;
- final Fast: 57/57 PASS in 3.432025s;
- final Checkpoint after fixture optimization: 85/85 PASS in 82.253570s under its 90s budget.

The first Checkpoint attempt had all 85 assertions pass but correctly failed the profile budget at 155.621773s.
After initial fixture reduction, one later run again passed all assertions but exceeded the budget at 96.985295s.
Redundant graph reconstruction and physical creation of 128 equivalent limit fixtures were then replaced with the
same contract assertions plus a patched production limit; the final bounded run above passed with useful margin.
No full long/Promotion suite was run.

## Static, integration and repository gates

- `python -X utf8 scripts/ci/validate_ci.py --all`: PASS;
- CI inventory: PASS at 394 unique test IDs, 27 shards, 10 lanes, 57 Fast and 85 Checkpoint tests;
- integrated structure: PASS as `integrated_candidate`, Core `0.1.14`, CLI `0.1.18`, Core API `1`;
- repository gates: PASS over 674 repository paths, 367 Markdown files and 918 local links, with no forbidden
  artifacts;
- Core/test `py_compile`: PASS; relation schema JSON decode: PASS;
- `git diff --check`: PASS.

One attempted graph-origin schema widening was correctly rejected by the frozen brand-hash Fast test. It was fully
reverted before the passing Fast/Checkpoint evidence above; the schema file is absent from the branch diff.

## Central replay and integration order

The current broad class selector discovers these four tests locally, which explains the inventory increase from 390
to 394, but this branch deliberately does not edit the shared shard manifest. The unique integrator should:

1. reconcile and land the current CI6 and A3 changes to `scripts/ci/test-shards.json` in the chosen clean integration
   worktree;
2. integrate W7.1 without taking any shared-manifest version from this branch;
3. register/replay the four exact IDs above once against the reconciled manifest, confirm the Fast/Checkpoint lane
   counts and budgets, and record the central receipt/index updates;
4. freeze the resulting exact Candidate SHA, push that SHA to a non-main branch, obtain both required hosted smoke
   checks, and only then consider promotion to protected `main`.

This branch does not push, publish, update `main`, claim hosted smoke evidence or claim canonical State.
