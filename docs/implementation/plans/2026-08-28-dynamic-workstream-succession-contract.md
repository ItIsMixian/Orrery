# 实施计划：W7A Dynamic Workstream Succession Contract

Status: Active Candidate Plan

Date: 2026-08-28

Fact scope: Candidate `codex/w7a-dynamic-workstream-succession-contract`, task base
`W5E-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

Governing decisions: [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md),
[ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [Dynamic Workstream Succession Contract](../../design/dynamic-workstream-succession-contract.md)

## Goal and stop boundaries

Implement the provider-neutral v1 record/graph/plan contract, dependency-free validation and deterministic CLI
projection. Preserve Personal zero-network, Git-private storage, existing W5D lineage, W6 cleanup and CI1 promotion
boundaries.

W7A does not batch migrate real W5C/W6/W5D/CI1/W5E sessions, execute apply/undo, build the W7C graph page, schedule
tasks, control Agents, delete worktrees/branches, push, merge main, change branch protection, tag or release.

## Implementation phases

1. **Contract and fixture**
   - Add Core schema v1 for relation event, graph, succession/discovery/apply/undo plans and legacy projection.
   - Add a sanitized W5C → W6 → W5D → CI1 → W5E-shaped synthetic fixture including a later CI task.
   - Freeze relation direction, lifecycle, exact OID evidence, source-link and no-layout/no-delete invariants.
2. **Core validation and projection**
   - Validate self/duplicate/cycle/multiple Git parent, type-specific evidence and deterministic ordering.
   - Resolve exact local OIDs/ancestry without network; retain proposed/Unknown on insufficient evidence.
   - Compute deterministic active tips and compare/suppress pair reasons without hiding sibling, parent post-fork,
     stale/Unknown, L2/L3 or exclusive findings.
   - Project legacy `base_workstream_id/task_base_oid` sessions read-only.
3. **Storage and CLI**
   - Implement read-only `$GIT_COMMON_DIR/orrery/workstream-relations/` loading with absent-root zero-write behavior.
   - Add stable `relations graph` and `relations succession-plan` JSON envelopes.
   - Permit only explicit local `relations propose` append for revision 1; do not use it on real project relations.
   - Freeze W7B discovery/apply/undo I/O builders with `writes_performed=false`.
4. **Version and CI inventory**
   - Raise unreleased Core/CLI component versions while keeping Core API and JSON envelope version stable.
   - Add W7A tests to CI1 Fast and exactly one Promotion shard; update inventory expectations mechanically.
5. **Checkpoint and authority sync**
   - Run schema/validator/fixture/CLI/CI inventory Fast checks first.
   - Run W1/W2/W5D/CI1 adjacency, structure, isolated site, Markdown links and diff at Checkpoint.
   - Update affected subsystem State, independent Validation, DEVLOG and indexes; do not edit root
     `docs/PROGRESS.md` or `docs/HANDOFF.md` on this feature branch.

## Required tests

- active successor while predecessor is still running;
- a new CI-class task absent from the original Plan;
- multiple predecessors, one primary Git parent;
- cycle, self-edge and duplicate edge rejection;
- branch/path similarity does not create evidence;
- exact Git ancestor and nonexistent/non-ancestor OID handling;
- parent post-fork unique commit and sibling comparison;
- stale HEAD/Scope, Unknown parent and deterministic active tips;
- append-only, no author-document write, no network and deterministic JSON;
- legacy `base_workstream_id/task_base_oid` read-only projection;
- W7B apply/undo/legacy inference contract contains no delete/execute operations;
- W7C graph JSON contains node/edge status, evidence, active tips, Unknown and source links, but no layout/color/UI text.

## Validation ladder

Fast:

```text
python -X utf8 -m unittest tests.test_workstream_relations -v
python -X utf8 scripts/ci/test_inventory.py
python -X utf8 scripts/ci/validate_ci.py --all
```

Checkpoint adds collaboration lineage/contract adjacency, CI1 tests, integrated structure, isolated static site,
Markdown local links, compile/JSON validation and `git diff --check`. Candidate/Promotion remain the unique
integrator's later responsibility on a frozen exact SHA.

## W7B/W7C handoff

- W7B owns real discovery UX, one-confirmation batch apply, append-only transition/undo execution, legacy migration
  policy and any retention/compaction proposal.
- W7C owns Succession/Dependency/Conflict rendering, active-tip highlighting, historical folding, Unknown styling and
  accessible list fallback; it must not reimplement Core semantics.
- Any request to execute migration against real W5C/W6/W5D/CI1/W5E sessions, delete workspace objects or change the
  graph contract requires a new reviewed Plan/ADR as applicable.
