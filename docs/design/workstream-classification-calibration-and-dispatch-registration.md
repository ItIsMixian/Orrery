# Workstream Classification Calibration and Dispatch Registration

Status: Approved

Date: 2026-09-01

Governing ADR: [ADR-0029](../decisions/0029-explicit-workstream-classification-and-dispatch-registration.md)

Maintainer approval: approved on 2026-09-01 for an independent W7.5 task after W7.4 produces an accepted clean
Candidate. Approval does not claim that classification has been calibrated or future dispatch enforcement exists.

## 1. Classification model

Classification is a set of independent fields, not one inferred category:

```json
{
  "schema_version": 1,
  "contract_type": "workstream-classification-envelope-v1",
  "workstream_id": "U2.5-shell-first-graph-activation-cache",
  "primary_subsystem_id": "documentation-system",
  "affected_subsystem_ids": ["release-and-toolchain", "test-coverage"],
  "program_path": null,
  "program_absence_reason": "not-applicable",
  "series": {
    "series_id": "unified-u",
    "task_code": "U2.5",
    "series_order": 25,
    "predecessor_workstream_id": "U2.4-immediate-launcher-readiness"
  },
  "series_absence_reason": null
}
```

Rules:

- primary subsystem is required and must resolve to the project subsystem registry;
- affected subsystems are sorted, unique and never replace primary ownership;
- program path is either one accepted program/phase path or explicit absence with reason;
- series is either one exact series record or explicit absence with reason;
- task code is display/series metadata, not an identity parser;
- predecessor is explicit series ordering only and does not create a dependency or `derived_from` edge.

Lifecycle fields (`closed`, `retired-session`, `implementing`, and similar) are not part of this envelope. Relation
records are referenced only to prove that classification did not create or remove them.

## 2. Authority and persistence

Core owns three contracts:

1. classification envelope validation at Workstream registration;
2. append-only classification proposal/decision events with expected revision/CAS;
3. a read-only audit joining registered Workstreams, accepted hierarchy/series events and explicit absence reasons.

Existing `workstream-program-hierarchy-v1` and task-series event stores remain the effective membership owners. W7.5
may add a small classification-review ledger or extend these stores through versioned events, but it cannot duplicate
effective membership in Observatory or dispatch code.

Accepted classification events are Git-common-private, local-only, bounded and excluded from packages/releases.
They retain source links and actor authority. Reject/defer/change actions append revisions; no historical event is
deleted or rewritten.

## 3. Historical audit and proposal rules

The audit starts from the real W7.4 provider and strict history index. Its initial baseline is:

| Inventory | Total | Missing series | Missing program/phase | Missing both |
|---|---:|---:|---:|---:|
| Core Graph provider | 42 | 33 | 35 | 27 |
| strict history records | 37 | 29 | 30 | not yet normalized |
| accepted W7.4 full projection | 25 | 17 | 21 | 14 |

The implementation must recompute rather than hard-code these counts.

Evidence classes:

- `existing-effective-event`: mechanically retained; no confirmation replay;
- `explicit-committed-task-authority`: may create a proposal citing exact commit/blob/path;
- `explicit-session-registration`: may create a proposal when the recorded fields are complete and source-bound;
- `conflicting-explicit-evidence`: non-actionable until the conflict is explained/resolved;
- `no-explicit-evidence`: unclassified; no proposal that can be accepted.

Task names, prefixes, branch names and ancestry can be shown as search context only. The proposal builder contains
negative controls proving these inputs alone produce no suggested classification.

## 4. Human-readable review

Personal Observatory adds one bounded `任务分类待确认` surface. It is separate from relation confirmation because
classification has no gate or causal effect.

Primary presentation order:

1. plain-language question: “是否把 U2.4 归入 Unified Observatory 系列？”;
2. proposed program/phase and/or series values;
3. why the proposal exists, with human-readable source title;
4. effect: organization/filter/layout only; explicitly no relation/cleanup effect;
5. evidence limitation/conflict warning;
6. actions: `接受分类`, `调整分类`, `暂缓`, `保持未分类`;
7. collapsed technical details containing IDs, exact refs, revisions and hashes.

Batch review groups proposals only when the proposed values and authority/evidence class match. The maintainer sees
every included task before acceptance, can remove/edit individual items and receives one result per task. A batch is
not an opaque “accept all suggestions” action.

Unknown/no-evidence items appear in an informational unclassified inventory, not as accepting cards.

## 5. Future dispatch enforcement

Authority-first task creation becomes:

```text
committed Plan/Validation
  -> explicit classification envelope
  -> Core validate/register
  -> Git-private scope refresh
  -> product writes
```

`orrery-dispatch` sends the task identity, task-description version, authority paths, execution configuration, safety
boundary and exact classification envelope. It refuses to claim registration when primary subsystem or absence
reasons are missing. It does not independently decide a series/program or parse task names.

Existing tasks remain readable when their envelope predates v1. They appear as `classification-pending` and enter the
audit; they are not silently rejected or auto-migrated.

## 6. Graph and history consumption

- Graph groups only effective accepted program/phase/series metadata.
- Unclassified nodes remain visible and explicitly labelled; a presentation-only `未分类` bucket may aid navigation
  but is not emitted as program membership.
- `derived_from`, `depends_on`, `absorbs`, conflict and series connectors retain their own semantics.
- Classification changes invalidate U2.5 Graph cache through the existing owner hook once U2.5 Phase B integrates;
  W7.5 does not implement hydration or cache policy.
- W7.4 full/compact node admission, history lifecycle, zero-overlap and ELK geometry remain unchanged.

## 7. Safety and failure behavior

- Personal Mode remains zero-network and local-confirmation only.
- Central/Team may request classification review but cannot apply it.
- Missing or conflicting evidence stays unclassified; no AI or Agent override.
- Classification cannot make a worktree cleanup-eligible, close a task, satisfy a gate or approve a relation.
- Invalid store/schema/CAS state fails closed without rewriting existing events.
- No program/series event is written during the initial preview. The maintainer first accepts the review model and
  proposed batch contents.

## 8. Delivery boundary

W7.5 starts from the accepted clean W7.4 exact Candidate. Phase A is read-only audit/proposal and real UI preview.
After maintainer acceptance, Phase B may apply only the explicitly accepted classification events and add future
dispatch enforcement. Focused checks follow; broader validation, integration, publication and release remain separate.
