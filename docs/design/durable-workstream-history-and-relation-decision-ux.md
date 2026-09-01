# Approved Design: Durable Workstream History and Relation Decision UX

Status: Approved

Date: 2026-09-01

Governing decision: [ADR-0026](../decisions/0026-durable-workstream-history-and-human-readable-relation-decisions.md)

## 1. User outcome

The Workstream experience must answer two ordinary questions:

1. “What work happened before, even if its worktree has been cleaned?”
2. “What exactly am I being asked to accept, and what changes if I accept it?”

Users are not expected to interpret raw Workstream IDs, relation revisions, Git-private storage labels or English
machine rationale to answer either question.

## 2. Durable history model

Core owns `workstream-history-index-v1` under the Git-common-private Orrery root. It is local, zero-network,
package-excluded and independent of linked-worktree paths. Team Mode may synchronize only its bounded safe metadata
under ADR-0008; it never synchronizes transcript, source/diff body, credentials or absolute paths.

Each current record contains:

```json
{
  "schema_version": 1,
  "contract_type": "closed-workstream-summary",
  "workstream_id": "W7.3-workstream-relation-capture-confirmation",
  "display": {"task_code": "W7.3", "label": "任务流与关系"},
  "classification": {
    "primary_subsystem_id": "multi-worktree-collaboration",
    "program_path": ["workstream-w", "workstream-w7"],
    "series_id": null,
    "series_order": null
  },
  "closure": {
    "lifecycle": "closed",
    "reason": "integrated",
    "closed_at": "2026-09-01T00:00:00Z",
    "final_head_oid": "<40-hex>",
    "branch_ref": "refs/heads/codex/..."
  },
  "references": {
    "validation_refs": [],
    "relation_ids": [],
    "source_evidence_ids": []
  },
  "visibility": "git-private-local-only",
  "revision": 1
}
```

The writer runs at verified integration/closure and before eligible worktree removal. It binds the exact session,
closure, HEAD and classification revisions, then writes one append-only record atomically. Drift, missing closure,
unknown ownership or unsafe source evidence fails closed and prevents automatic cleanup eligibility; it does not
fabricate a history record.

Legacy recovery reads valid retired sessions only as migration input. It creates a compact record with explicit
provenance and Unknown fields where proof is missing. It never truncates, rewrites or deletes the original archive.

## 3. Graph projection

The Graph provider receives two independent sets:

- live/current Workstreams and their real relations;
- closed history summaries, including tasks with zero relations.

Default display rules:

- current/unclosed tasks remain individual nodes;
- closed tasks are folded by accepted program → phase → series when available;
- ungrouped history is placed in one clearly named “其他历史任务” group;
- a collapsed group shows task count, time span and the number of retained relations, not a fake task node;
- expanding a group reveals every closed task in stable chronological/series order;
- edges between current and historical tasks remain visible at the group boundary and resolve to real endpoints when
  expanded;
- filters apply after history identity is loaded, so “all modules” and “expand all history” cannot silently omit
  unrelated closed tasks.

Historical records never become active tips, blockers, apply/undo targets, Review Ready tasks or execution surfaces.
When the history index is unavailable, the page says “历史索引不可用”; it must not represent an empty history as a
verified fact.

## 4. Relation-decision view model

Core/Observatory adapter exposes a deterministic decision presentation for each proposal:

```json
{
  "question": "CI7 在进入集成前，是否必须等待 CI6 完成？",
  "why_suggested": "CI7 注册时明确把 CI6 设为同系列前序任务。",
  "accept_effect": "接受后，CI7 在 CI6 完成前不能进入集成；开发仍可继续。",
  "reject_effect": "拒绝后，两项任务不会因这条建议形成依赖。",
  "evidence_note": "这是注册信息，不是从任务名称推断。",
  "decision_kind": "depends-on",
  "gate": "integration"
}
```

The wording is derived from validated relation type, direction, gate and evidence category. No LLM call is required
or allowed for decision semantics.

Primary card order:

1. one plain-language question;
2. why it was suggested;
3. “接受后” and “拒绝/暂缓后” consequences;
4. evidence limitation/Unknown warning;
5. actions in ordinary language;
6. collapsed “技术详情” containing IDs, revision, hashes, raw rationale and provenance.

Gate labels and consequences:

| Gate | User label | Acceptance consequence |
|---|---|---|
| `implementation` | 开始实现前 | source task cannot start implementation before target condition |
| `validation` | 开始验证前 | implementation may continue; validation waits |
| `integration` | 合入主线前 | branch work may continue; integration waits |
| `release` | 发布前 | integration may continue; release waits |

Changing a gate is presented as “改为在……前等待” and creates the existing append-only revision. Raw enum names are
technical detail only.

## 5. Authority and failure behavior

- Human-readable copy never changes who may confirm.
- Unknown mechanical lineage exposes explanation plus defer/reject only; it has no Accept control.
- Actionable dependency proposals show Accept only when local role/CAS/evidence binding is currently valid.
- If Core cannot produce a complete question and consequence model, the card becomes non-actionable and asks for more
  evidence instead of falling back to raw technical controls.
- Request-only Team views may show the explanation but cannot execute the decision.
- Graph remains read-only; confirmation stays in Personal/Team inbox surfaces.

## 6. Compatibility and migration

Existing relation/series/program/archive schemas remain readable. `workstream-history-index-v1` is additive. Current
self-host valid retired sessions are eligible for a one-time, read-only preview of proposed history summaries; actual
write/apply is local, append-only and separately receipted. Current U2.4 archive repair remains provenance and is not
reclassified as W7.4 implementation evidence.

If a future release migrates existing projects, it must preserve customized author documents, keep Personal Mode
zero-network and exclude Git-private history from release archives.

## 7. Acceptance shape

Before broad automated tests, the maintainer sees one real self-host preview proving:

- cleaned closed tasks remain discoverable and are folded rather than missing or dumped into the active canvas;
- “expand all history” actually reveals them;
- at least one dependency and one Unknown lineage card are understandable without opening technical details;
- accepting a dependency clearly states its stage consequence, while Unknown lineage still cannot be accepted.

Only after this visual/semantic acceptance may focused Core/Observatory tests run. Fast, Checkpoint, Candidate,
Promotion and release remain separate later actions.

## 2026-09-01 revision 2 — store all, project only evidence-backed relations

[ADR-0027](../decisions/0027-retain-history-without-bulk-ui-and-recover-archived-lineage.md) supersedes the display
parts of sections 3 and 7 that required every stored closed task to be reachable through a new full-history UI.

- `workstream-history-index-v1` still retains every bounded closed identity independently of worktree cleanup.
- The relation page does not add a complete-history directory, bulk card grid or second history application.
- The existing Graph projects only current tasks and historical tasks connected by validated semantic or explicit
  series evidence. Connected old chains retain existing compact fold/expand behavior.
- Core evaluates archived session `lineage` as potential mechanical `derived_from` evidence using exact status,
  source/target, task-base OID, validated HEAD and Git checks. It does not require a newer relation-store record when
  the older session already contains valid mechanical evidence.
- Unverified/missing/drifted/cyclic lineage remains stored but creates no edge and no default canvas node.
- Technical diagnostics expose aggregate recovery/rejection counts and safe evidence references; they are not a new
  user-facing history list.
- The accepted preview must show recovered archived relationship chains in the original relation canvas and no bulk
  historical inventory UI.

### Historical identity is not closure

The history contract preserves the source session's observed lifecycle. A retired worktree with an `implementing`,
`validating`, `review-ready` or `integrated` session is recorded as `retired-session`; it is never rewritten as a
closed task. Only a source session whose lifecycle is exactly `closed` and has a valid closure reason becomes
`closed-workstream`. The schema keeps closure state, Git identity and lineage evidence as separate required objects.

## 2026-09-01 revision 4 — full relation and compact-history modes

The maintainer accepts the restored evidence-backed relation graph as the **full relation** baseline. Compact mode is
an alternate projection of the same Graph, not a new page, directory, list or source of facts.

### Modes

- `显示完整关系`: default; preserves the accepted full node/edge set, including all validated archived lineage,
  explicit series connectors and current pending proposals.
- `折叠历史`: preserves current/attention context while replacing deep, read-only historical subgraphs with compact
  summary nodes inside the same canvas.

### Nodes that compact mode must keep visible

- every non-historical/current task;
- every endpoint of a pending proposal, Unknown lineage, dependency, confirmed conflict or other item requiring human
  attention;
- the nearest one-hop historical predecessor/successor needed to explain each visible current/attention node;
- the selected/focused node and its directly connected evidence path.

### Fold eligibility

A node may fold only when it is historical/retired, non-executable, not awaiting a decision, not an Unknown/conflict
endpoint and deeper than one relationship hop from all protected visible nodes. Eligible nodes are folded by maximal
connected historical subgraph, never by task-name similarity. Accepted program/phase/series metadata may label or
partition a fold but may not invent an edge.

A fold summary is a presentation object, not a Workstream. It shows task count, retained relation counts/types and
entry/exit context. Every external connector remains traceable to its underlying edge. Branched historical subgraphs
retain distinct entry/exit ports rather than being flattened into a fake linear relation.

### Interaction

- clicking a fold summary expands only that historical subgraph in place; it does not open a new history UI;
- the expanded subgraph can be folded again without changing facts or other groups;
- switching global modes and local expansion uses an offscreen ELK result with an atomic canvas swap, avoiding a
  visible blank/flash and preserving zoom/anchor where practical;
- fully historical connected components remain as one compact summary each in compact mode rather than disappearing;
- identity-only records with no validated relation remain stored internally and are not introduced into either graph
  mode.
