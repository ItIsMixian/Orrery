# Dynamic Workstream Succession Contract

Status: Approved

Updated: 2026-08-28

Governing decisions: [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md),
[ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Fact scope: Candidate `codex/w7a-dynamic-workstream-succession-contract` based on
`codex/w5e-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

## 1. Contract boundary

W7A owns a provider-neutral relation control plane. It consumes exact Git/session evidence and emits deterministic
JSON. It does not schedule work, control Agents, mutate author documents, perform integration, or delete workspace
objects. The graph grows incrementally; no caller has to predict a complete DAG before work begins.

All contract objects use `schema_version: 1` and a distinct `contract_type`:

- `workstream-relation-record`
- `workstream-relation-graph`
- `workstream-succession-plan`
- `workstream-relation-discovery-plan`
- `workstream-relation-apply-plan`
- `workstream-relation-undo-plan`
- `workstream-legacy-relation-projection`

Unknown is data, not an exception or a green result. JSON arrays and diagnostics use deterministic ordering.

## 2. Relation direction and meaning

Every edge is directed `source_workstream_id → target_workstream_id`:

| type | source | target | may suppress ancestor/successor Direct pair |
|---|---|---|---|
| `derived_from` | new/forked Workstream | primary Git task-base Workstream | yes, only with current exact ancestry and no parent post-fork commits |
| `depends_on` | dependent Workstream | prerequisite Workstream | never |
| `absorbs` | active owner/successor | Workstream whose responsibility was transferred | yes, only with current explicit ownership-transfer evidence |

Multiple incoming semantic predecessors are valid. For each source, at most one `derived_from` edge may be
`proposed`, `active`, or `completed`; cancelled/stale history remains auditable but is not a second current parent.

## 3. Immutable event record

A relation event contains:

- stable `relation_id`, strictly increasing positive `revision`, immutable `event_id`, RFC 3339 `recorded_at`;
- type, source, target and lifecycle;
- `evidence` with exact optional `source_head_oid`, `target_head_oid`, type-specific `task_base_oid` or
  `ownership_transfer_oid`, head freshness,
  ancestry status, dependency/ownership-transfer status and parent unique-commit count;
- sorted `source_links` containing typed, repository-relative or opaque references without UI wording;
- `reason`, `actor.kind` (`human`, `tool`, `import`) and optional local actor ID;
- `origin` (`native`, `legacy-session-projection`, `discovery`) and `writes_performed`.

Lifecycle changes append a new full-state revision; prior files are never replaced. `cancelled` is explicit human/tool
withdrawal. `stale` means evidence no longer supports the earlier state. `completed` preserves history and no longer
represents a live takeover. W7A's write API creates revision 1 in `proposed` only.

## 4. Git-common-private storage

Native events live at:

```text
$GIT_COMMON_DIR/orrery/workstream-relations/<relation-id>/<revision>-<event-id>.json
```

The loader:

1. resolves the exact common Git directory locally without fetch or network;
2. returns an empty graph when the relation root is absent, without creating it;
3. rejects symlinks/reparse-like non-regular files, oversized files, malformed JSON, invalid records, duplicate
   revision/event IDs and revision gaps;
4. selects the highest revision as current while retaining ordered history metadata;
5. never reads author-document paths as relation truth.

The append API creates only its exact relation directory and a new file using exclusive creation. It refuses an
existing relation ID/revision and never edits sessions. Tests use isolated temporary repositories only.

## 5. Evidence and validation

Lexical OID validity requires exactly 40 hexadecimal characters. Repository validation additionally requires each
claimed commit to resolve to the same exact commit OID.

For `derived_from` to become evidence-confirmed active succession:

- source, target and task-base OIDs exist exactly;
- task base is an ancestor of source HEAD;
- recorded target HEAD equals task base;
- source and target head status are `current`;
- ancestry is `confirmed` and `target_unique_commits_after_base` is `0`.

If parent HEAD moved after the fork, ancestry is unavailable, or any binding drifts, the edge remains visible but is
stale/Unknown for suppression. Branch-name and path similarity never upgrade evidence.

For `absorbs`, suppression additionally requires current source/target heads, an exact
`ownership_transfer_oid`, explicit `ownership_transfer_status: confirmed`, and zero target commits after that
recorded transfer point. `task_base_oid` remains reserved for `derived_from`; `depends_on`
uses `dependency_status` for planning and never changes Git provenance or ownership.

Graph validation detects self edges, duplicate current `(type, source, target)` edges, multiple current
`derived_from` parents and directed cycles across non-cancelled/non-stale edges. Proposed edges participate in
structural checks but never suppress conflicts.

## 6. Nodes, active tips, and conflict pairs

Node input records workstream ID, lifecycle/runtime/evidence status, optional exact HEAD, source links and origin.
Missing node/session evidence produces an `unknown` node. A node is eligible as active only when runtime is active or
review-pending and evidence is current.

An effective active succession edge is an `active` `derived_from` or `absorbs` edge whose type-specific evidence is
confirmed. Active tips are eligible nodes that are not the target of such an edge. The deterministic succession plan
emits:

- `active_tip_workstream_ids`;
- `compare_pairs` for active tips, siblings, stale/Unknown edges, dependencies, parent post-fork drift and any pair
  carrying L2/L3/exclusive findings;
- `suppress_direct_pairs` only for a confirmed ancestor/successor chain with no unique parent commits and no
  independent L2/L3/exclusive reason;
- per-pair reason codes；对应 evidence／source links 保留在同一 versioned graph 的 node／edge 上。

This output advises the existing overlap consumer; it does not itself resolve or delete findings.

## 7. Discovery, apply, undo, and legacy compatibility

Discovery is read-only and may use exact local sessions, OIDs and ancestry. Inferred candidates always begin as
`proposed`; similarity-only candidates carry `insufficient-evidence` and cannot be activated.

An apply plan binds the graph hash, candidate event hashes and ordered append operations. It requires one explicit
local confirmation for that exact plan and returns a receipt; any drift invalidates the plan. An undo plan references
the apply receipt and appends `cancelled` or `stale` compensating events. Neither plan contains delete, merge, branch,
Validation or author-document operations. W7A freezes these I/O shapes but leaves batch execution to W7B.

Legacy sessions with `base_workstream_id` and `task_base_oid` project deterministically to read-only
`derived_from` edges. `lineage.status=current` plus exact evidence may project `active`; missing/drifted inputs project
`proposed`/Unknown or `stale`. Projection never writes relation storage or modifies the legacy session.

## 8. Observatory consumer boundary

W7C may render three derived views—Succession, Dependency and Conflict—but must consume the same Core graph and
pair plan. Core source links remain navigable evidence; node/edge lifecycle, Unknown and active tips stay machine
facts. Layout, colors, coordinates, dashed-line styling, labels and localization belong exclusively to Observatory.

## 9. Security and privacy

- Core and CLI are dependency-free and zero-network.
- Relation records may contain identifiers, OIDs, counts and typed source links, but not prompts, answers,
  transcripts, source/diff bodies, credentials or arbitrary shell commands.
- CLI accepts bounded values and repository-relative/opaque links; it never executes a link.
- Relation storage is excluded from release/package/docsite inventory by being inside Git common private state.
- Cleanup remains governed by W6 and cannot be implied by relation lifecycle or an apply/undo receipt.
