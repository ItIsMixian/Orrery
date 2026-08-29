# 实施计划：W7D W7 Integration Candidate

Status: Completed; exact-SHA Promotion passed and verified descendants are contained in Canonical main

Date: 2026-08-28

Fact scope: Candidate `codex/w7d-w7-integration-candidate`, parent/task base
`codex/ci2-tiered-test-performance@8b635b18ece85d2d051adaf6961057b64011205c`

Additive sibling input: `codex/w7c-b-production-workstream-relation-graph@d411fd6e775d59332de37784cd781339d2835661`

Governing decision: [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md)

## Goal and hard boundaries

Integrate W7A/W7B/CI2 and the W7C-B production relation graph in one isolated Candidate while preserving each
subsystem's authority. W7C-A is already byte-identical inside W7C-B for its experiment assets and Validation and is
not merged separately.

The Candidate keeps W7B's local discovery／plan／human confirmation／transaction／recovery／receipt／undo contract and
W7C-B's root-only, default-off, read-only graph consumer. It does not perform a self-host relation apply, add graph
apply／undo／close／delete controls, grant central Team execution authority, merge or push `main`, change branch
protection, create a tag or publish a Release.

## Integration sequence

1. Verify exact refs, W7A→W7B→CI2 ancestry, sibling cleanliness and W7C-A absorption before product writes.
2. Register Git-private `W7D-w7-integration-candidate` with CI2 as exact parent/task base and declare implementation,
   shared State, CI manifest, Validation, root entry and browser acceptance surfaces.
3. Merge only W7C-B additively. Resolve DEVLOG, Implementation/Validation indexes, four subsystem State Docs,
   `packages/component-versions.json` and `scripts/ci/test-shards.json` semantically.
4. Preserve manifest schema 2, Fast 15 seconds, Checkpoint 90 seconds and the dedicated
   `team-relations-execution` Promotion shard at 300 seconds. Assign the W7C-B focused contract to Fast/Checkpoint
   and its full modules exactly once in Promotion; derive all counts from the inventory tool.
5. Verify Core 0.1.14, CLI 0.1.18 and Observatory 0.1.9 through the component contract. Correct W7C-B wording so
   W7B implementation is not confused with the still-absent self-host apply, default UI execution wiring or release.
6. Run focused, Fast, Checkpoint, one final local W7B Promotion, integrated structure, repository gates, isolated
   docsite and real in-app Chromium at 1280px and 390×844. Do not run the complete local repository Promotion merely
   for a unified count.
7. Freeze a clean Candidate, push that exact SHA only to a non-`main` promotion branch, and wait for both required
   hosted checks. Any fix produces a new exact SHA and new hosted run.

## Documentation sync

As the unique integrator, W7D updates the four affected State Docs, this Plan, independent Validation, indexes,
DEVLOG, PROGRESS and HANDOFF. Historical Candidate records remain intact; generated `docs/_site/index.html`, local
browser output and raw timing JSON remain outside Git.

## Stop condition

Stopped with a clean non-`main` Candidate whose exact pushed SHA passed both Windows and Ubuntu required checks.
Promotion to `main` remains a separate maintainer authorization.
