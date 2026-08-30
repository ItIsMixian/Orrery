# Workstream Relation Capture & Confirmation

Status: Approved

Date: 2026-08-29

Governing ADR: [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)

## 1. Product model

Orrery captures relationships at three moments: task creation, late discovery/derivation and integration/ownership
transfer. The product separates proposal generation, tool evidence and human authority:

```text
Agent / Harness / Plan / optional Conductor
                   ↓ proposal + bounded evidence
          Git-private relation inbox
                   ↓ local human confirmation
       task owner or project integrator
                   ↓ append-only effective event
              Core relation graph
```

Graph、Personal、Team 和中央汇总只能消费该链，不能从布局、相似性或 Agent 文案反向创造 relation。

## 2. Relation and authority matrix

| Relation | Capture | Effective authority |
|---|---|---|
| `derived_from` | exact parent Workstream + task-base OID + verified ancestry | Core automatic mechanical event |
| `depends_on: implementation` | explicit intent、artifact owner、missing contract/tool evidence | source task owner |
| `depends_on: validation` | Validation requirement、missing fixture/gate、Harness failure | source task owner |
| `depends_on: integration` | integration plan、candidate intake、required reviewed SHA | human integrator |
| `depends_on: release` | manifest/release gate、platform/runtime evidence | human integrator |
| `absorbs` | takeover/merge/closure proposal | human integrator only |
| `conflict-pair` | Core overlap derivation | no confirmation; read-only derived view |

Agent rationale is `human-or-agent-assertion` observation. Mechanical evidence may make a proposal persuasive but does
not grant the Agent confirmation authority.

## 3. Proposal lifecycle

`proposed → evidence-updated → accepted | rejected | deferred-unknown | superseded`

- Every proposal binds proposal ID、source/target Workstream、relation type、suggested gate、proposer identity、
  fact scope、evidence references、created revision and exact endpoint heads when available.
- Gate edits create a new revision/event rather than rewriting the proposal.
- Acceptance records confirmer human member ID、role、local Host/project identity、decision time、evidence snapshot hash
  and resulting effective relation event ID.
- Rejection/defer records reason without deleting the proposal. Deferred/Unknown never blocks a lifecycle transition.
- Effective relation changes continue to use ADR-0014 apply/undo/recovery transaction boundaries.

## 4. Automatic `derived_from`

Automatic capture runs when a Workstream session is registered or rebound:

1. resolve `base_workstream_id` inside the same project identity;
2. verify `task_base_oid` exists and is the recorded parent/current accepted base allowed by policy;
3. verify exact ancestry and reject self/non-ancestor/cycle/drift;
4. append one idempotent mechanical relation event with Git evidence;
5. expose failure as Unknown/required metadata, never infer from branch names or task titles.

Re-running the same input is idempotent. A changed base produces a new proposal/rebind path, not silent replacement.

## 5. Human-machine `depends_on`

Proposal sources may include explicit user text, Plan metadata, required artifact ownership, imports/schema references,
Validation requirements or a Harness/tool failure. The inbox presents:

- “谁依赖谁”；
- `required_for` gate and plain-language consequence；
- evidence category and exact safe references；
- confidence is descriptive only, never an authority score；
- actions: accept, choose another gate, defer Unknown, reject.

Task-local confirmation prevents the source task from completing the named implementation/validation transition.
Project-gate confirmation affects integration/release eligibility and is ignored unless the confirmer had integrator
authority at the bound revision.

## 6. Late-derived work and fan-in

When a product Candidate exposes a later CI or migration task, the new task may mechanically derive from that
Candidate. Do not add a reverse dependency to the already-existing parent if it creates a cycle. A later Integration
Workstream represents fan-in:

```text
Integration Candidate ──derived_from──▶ Product Candidate
Integration Candidate ───depends_on───▶ CI fix
Integration Candidate ───depends_on───▶ Migration
```

The arrows use ADR-0014 source→target semantics: the Integration Workstream is the successor/dependent source and the
existing product/CI/migration Workstreams are its targets. The Core validator remains authoritative for edge direction
and cycle checks.

## 7. Integrator role without a central Agent

- Personal: local project owner is the initial sole integrator.
- Team: project owner remains the initial sole integrator and explicitly grants/revokes other human integrators.
- Multiple integrators use monotonic revision/CAS; conflicting decisions do not last-writer-win and remain pending.
- Optional Conductor may call proposal APIs and route inbox requests, but confirmation endpoints reject Agent/session
  identities and remote request-only callers.
- `platform_session` remains provenance for where work occurred, not a source of project authority.

## 8. Planned surfaces

- Core: proposal/event schema、mechanical derivation、gate-aware relation validation、role authorization.
- CLI/Harness JSON: `relations suggest|inspect|confirm|reject|defer` with bounded JSON receipts.
- Worktree registration: automatic derived-from attempt and explicit required metadata on failure.
- Personal/Team Observatory: “关系待确认” inbox and evidence inspector; central Team remains request-only.
- Graph: gate label and proposal/effective distinction; no confirmation or execution controls inside the graph canvas.

## 9. Compatibility and privacy

W7 v1 remains readable. v1 `depends_on` without gate is Unknown/unspecified and never silently converted. Proposal and
confirmation stores are Git-common-private, bounded, path-safe and package-excluded. Team metadata contains safe IDs,
gate/status/revision and evidence hashes only; no source body、Prompt、answer、transcript、diff or credential.
