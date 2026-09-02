# Dual-plane Event-driven Orrery Coordination

Status: Approved

Date: 2026-09-02

Governing ADR: [ADR-0033](../decisions/0033-dual-plane-event-driven-orrery-coordination.md)

## 1. Role split

Orrery presents one conceptual front door while keeping two contexts separate:

| Plane | Owns | Does not own |
|---|---|---|
| Product and Decision | maintainer discussion, intent clarification, option analysis, ADR/Design/Plan authoring after acceptance | Worker monitoring, command logs, implementation debugging, ordinary task events |
| Execution Coordination | task/worktree binding, authority handoff, runtime event inbox, blocker routing, compact control projection | product intent, approval, source implementation, release authority |

An Integrator or Validator is a bounded phase/task, not a third permanent conversational memory. The Product plane may
remain the maintainer's normal entry. It promotes work to Execution only after explicit implementation intent and an
exact authority revision.

## 2. Control flow

```text
maintainer discussion
  -> Product/Decision plane
  -> accepted authority commit
  -> reference-only request
  -> Execution Conductor
  -> Worker in isolated worktree
  -> candidate/runtime event
  -> event inbox
  -> Validator / Integrator when gated
```

The reverse path is also bounded. Execution sends Product only a decision request containing the affected Workstream,
source-bound blocker, available choices and consequence summary. It never forwards a raw Worker transcript.

## 3. Focus lease and event inbox

An active maintainer turn holds a **focus lease**. Incoming Worker events are persisted to the Execution inbox and do
not call `turn/steer`, inject a user-visible message or replace the current topic.

| Event class | Examples | Delivery |
|---|---|---|
| informational | started, resumed, still-running heartbeat | quiet inbox; unchanged heartbeat deduplicated |
| milestone | candidate frozen, validated, integrated, completed | badge/inbox; summarize after the current turn or on request |
| attention | blocked, validation failed, approval required | queue while the focus lease is active; surface immediately after the turn |
| critical safety | credential exposure, destructive action pending, release integrity failure | visible alert; no automatic execution and no impersonated user input |

Each logical transition has a stable event key and monotonically increasing revision. Delivery acknowledgement prevents
the Product plane and Worker from narrating the same transition twice. A low-frequency mechanical reconciliation may
repair missed events without creating conversational polling turns.

## 4. Provider-neutral platform binding

The conceptual `platform-session-binding-v1` contains:

```json
{
  "schema_version": 1,
  "workstream_id": "W3.1-fast-candidate-freeze-asynchronous-validation",
  "worktree_id": "opaque-local-worktree-id",
  "adapter": "codex",
  "host_id": "local-host",
  "opaque_session_id": "provider-owned-id",
  "capabilities": ["status", "open", "message"],
  "observed_status": "active",
  "observed_at": "RFC3339",
  "visibility": "local-only"
}
```

Bindings store no Prompt, answer, transcript, source/diff body, credential or private path. One primary active binding
is expected per Workstream. Multiple active bindings produce an ambiguity finding; no task is automatically deleted.
A missing/archived platform task produces `execution-channel-missing` while preserving the Workstream and worktree.

Adapters translate the opaque ID and capability calls. Codex may support status/open/message; another provider may
support only attach or bounded run status. Missing capability is explicit, never emulated by guessing.

## 5. Independent status axes

The control projection never compresses these into one field:

- platform task: `active | idle | failed | archived | unavailable`;
- Workstream lifecycle: `implementing | review-ready | candidate-frozen | validating | closed | superseded`;
- runtime condition: `active | paused | waiting-for-user | blocked-by-conflict | offline | stale-unknown`;
- evidence freshness: `current | stale | unknown`;
- validation: `pending | running | passed | failed | unknown`;
- cleanup eligibility: separate W6/W6.2 judgment.

`candidate-frozen` clears active write claims but retains the bound historical scope and expected-write receipt. A
reopened implementation acquires a new scope revision; it does not mutate the frozen receipt.

## 6. Compact control snapshot

The snapshot is a derived response/cache, not authored Markdown. It is rebuilt from versioned Core/session evidence,
platform bindings and accepted receipts. Its ordinary four-to-eight-active-task view targets roughly 1–2 KiB; larger
sets use pagination or summary counts rather than silently truncating important blockers.

Required fields are generation/currentness, Workstream/task/worktree identity, exact authority and candidate revisions,
independent statuses, highest relevant blocker, attention requirement and next meaningful event. Every item links to
the source needed for expansion. Missing input makes the item stale/Unknown.

## 7. Progressive inspection

The central read path is:

1. control snapshot or task status;
2. final structured receipt/latest assistant conclusion;
3. one named turn associated with a blocker;
4. one named command/output or diff;
5. full history only by explicit diagnostic decision.

Summary state must not preload command output. `includeOutputs: true` is a targeted diagnostic option, not a monitoring
default. Full history remains available for recovery and audit without becoming permanent Product-plane context.

## 8. Reference-only dispatch

The transport shape is intentionally small:

```text
Execute <task> from code base <sha> using task-description <sha>.
Read <exact Plan/ADR/Design/Pending Validation paths>.
Use <model/runtime configuration>.
Preserve <hard safety boundary>.
Acknowledge revision and refresh local scope before product writes.
```

Material requirements or acceptance changes first update the authority sources. In-scope implementation defects use
source-linked review findings. Neither path duplicates a second checklist in the task message.

## 9. Role-aware document entry

The intended future entry matrix is:

| Role | Default authority input |
|---|---|
| Product/Decision | Seed, relevant State/ADR/Design and current product discussion |
| Worker cold start | universal safety, exact task Plan/Pending Validation, referenced State/ADR/Design, mechanical conflict summary |
| Worker resume | current checkpoint plus exact authority delta; expand when stale/Unknown |
| Integrator/release | full global entrances, candidate evidence, affected State and release policy |

This matrix is not active merely because the Design is approved. Current `AGENTS.md` remains the required entry until
a controlled implementation and task-quality evaluation supersede it. Previous failed routing treatments are not
reinterpreted as support for this design.

## 10. Current Codex host profile

The self-host profile intentionally uses two saved Codex projects over the same repository:

- a project-scoped 1M context configuration for Product/Decision discussion;
- an implementation project for Execution coordination, Workstreams, validation and integration tasks.

The mapping is Local-only and selected by role when creating a task. Sidebar grouping does not create a Workstream
relation. Both projects refer to the same repository authority and all concurrent implementation still uses separate
worktrees. If future Codex desktop versions expose suitable per-session context controls, this host profile may be
simplified without changing the provider-neutral contracts.

## 11. Model routing

Status collection, event deduplication, ID resolution and snapshot assembly are deterministic. A model is optional for
human-readable explanation. Product ideation and material architecture/integration decisions may use stronger
reasoning selected for that bounded judgment. The Conductor does not keep a highest-effort model active merely to wait.

## 12. Product and release boundary

ADR-0033 does not expand the current S1 right-panel task. S2 begins only after an exact task-description handoff and
must use independent worktrees/repositories for each owner. Personal remains zero-network; Team remains metadata-only
and request-only. No event grants task creation, relation confirmation, merge, cleanup, release or destructive authority.
