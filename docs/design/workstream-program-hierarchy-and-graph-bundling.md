# Approved Design: Workstream Program Hierarchy and Graph Bundling

Status: Approved

Date: 2026-08-30

Governing decision: [ADR-0020](../decisions/0020-workstream-program-and-phase-hierarchy.md)

## Goals

- represent real program/phase membership without inventing relation edges;
- keep W tasks visually continuous while preserving their actual branching chains;
- allow same-semantics fan-out/fan-in to share a readable route trunk;
- preserve individual edge evidence, hit targets and inspector identity;
- migrate current self-host data explicitly rather than parsing prefixes.

## Non-goals

- no scheduler, epic tracker, roadmap authority or automatic project planning;
- no multi-program membership or arbitrary group DAG in v1;
- no change to `derived_from`／`depends_on`／`absorbs`, series or confirmation authority;
- no grouping inferred from title, branch, `display_prefix` or task-code text;
- no public/default/release transition.

## Contracts

### Group definition

```json
{
  "schema_version": 1,
  "group_id": "workstream-w7",
  "group_kind": "phase",
  "parent_group_id": "workstream-w",
  "display_label": "W7 · 任务关系与集成",
  "order": 7,
  "lifecycle": "active",
  "revision": 1,
  "actor": {"kind": "human", "role": "integrator"},
  "source_links": []
}
```

`program` requires no parent. `phase` requires one current program parent. IDs are opaque; labels and order are
explicit. Duplicate ID, cycle, missing parent, stale revision and non-integrator acceptance fail closed.

### Membership

```json
{
  "schema_version": 1,
  "membership_id": "membership-w73",
  "workstream_id": "W7.3-workstream-relation-capture-confirmation",
  "group_path": ["workstream-w", "workstream-w7"],
  "lifecycle": "active",
  "revision": 1,
  "actor": {"kind": "human", "role": "integrator"},
  "source_links": []
}
```

The path must resolve root-to-leaf against current definitions. Only one active primary membership exists per
Workstream in v1. Membership is orthogonal to subsystem, series, relation, lifecycle and validation state.

## Current self-host repair fixture

The maintainer accepts this explicit organizational structure as a migration input, not a prefix inference rule:

| Program path | Exact current members |
|---|---|
| `workstream-w / workstream-w5` | `W5C-team-observatory-ux`, `W5D-lan-collaboration-harness`, `W5E-team-observatory-ui-closeout` |
| `workstream-w / workstream-w6` | `W6.1-incremental-maintenance-quick-remove` |
| `workstream-w / workstream-w7` | `W7.1-archived-session-relation-projection`, `W7.2.2-graph-arrow-scrollbar-visual-integration`, `W7.2.3-workstream-graph-density-correction`, `W7.3-workstream-relation-capture-confirmation`, `W7.3-integration-acceptance` |

Program `workstream-w` is labelled `W · 多 Workstream 协作`; phase labels are W5 Team collaboration, W6 Workspace
maintenance and W7 Relations/integration. CI1 and SH1 remain outside the W program even when real relations connect
them to W members. Missing or additional W-looking records remain ungrouped until explicitly accepted.

The fixture is versioned and human-reviewable. Applying it appends group/membership records; it never rewrites the
legacy session bytes or relation history.

## Graph projection

- One subtle outer W program region contains W5/W6/W7 phase lanes. Phase lanes may fold independently.
- Nodes keep current status/series styling. Group containment uses header/background only and creates no connector.
- Actual relation edges cross phase/program boundaries normally. CI1/SH1 appear outside the W region when their edges
  connect to W tasks.
- Series lanes remain a separate presentation layer inside a phase. A node may belong to a program phase and a series;
  these facts are not interchangeable.
- On mobile, the W program becomes a program header with phase accordions and focused chains; it is not a shrunken
  desktop canvas.

## Controlled route bundles

A `route_bundle_id` may be derived only when every member edge has:

- identical `relation_type`, direction, lifecycle, certainty, required gate and semantic style;
- one common source or one common target;
- current endpoint/scope evidence and no conflict/comparison/series mixing.

The bundle draws one shared trunk and separate branches. Branches must leave the trunk before the target clearance
zone, use distinct target ports and preserve visible arrowheads. The trunk has no individual relation label; an
optional compact badge may show type/count, such as `接续 ×3`.

Underlying relations remain individual DOM/data records. Clicking a branch selects one relation. Clicking a shared
trunk opens a bounded bundle list; selecting a relation highlights the trunk plus only its branch. A bundle cannot
merge evidence, gate status or inspector identities.

Geometry rules:

- declared bundle overlap is allowed only along its owned trunk;
- undeclared collinear overlap remains invalid;
- no trunk/branch may cross node interiors, lane headers, labels or controls;
- branches have ≥24px visual separation before their target and distinct arrowhead coordinates;
- mixed semantic colors/dashes are never bundled;
- simple node re-layout remains preferred over unnecessary bends.

## Selection and accessibility

- Pointer selection brightens the node's existing semantic stroke and adds a low-opacity same-color glow; it does not
  add a white outer rectangle.
- Unrelated nodes/edges dim slightly. Selected edge branches and endpoints remain fully visible.
- Keyboard `:focus-visible` uses the same semantic accent with a distinct non-white focus treatment that meets the
  current accessibility contract.
- Inspector open/close does not recompute or compress the graph layout.

## Authority and privacy

Group and membership proposals may originate from Agent, task owner, import fixture or optional Conductor. Only a
human integrator accepts them. Program metadata is Git-common-private; Team projection is bounded metadata only.
Observatory remains read-only for the graph and cannot accept membership from the canvas.

## Validation

- schema/duplicate/cycle/parent/path/revision/CAS/human-role and legacy Unknown fixtures;
- exact self-host W repair fixture plus negative W-prefix lookalikes;
- membership does not change relation counts, active tips, gates, closure or series;
- graph W/W5/W6/W7 containment with CI1/SH1 cross-boundary edges;
- same-source and same-target bundle fixtures, mixed-semantics refusal, branch hit testing and inspector identity;
- semantic selection/focus styling and desktop/mobile Browser review;
- focused Graph/Core tests during iteration; routed Fast/Checkpoint only after maintainer visual acceptance.
