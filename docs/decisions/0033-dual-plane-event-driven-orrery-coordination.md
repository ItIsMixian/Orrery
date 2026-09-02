# ADR-0033: Dual-plane, Event-driven Orrery Coordination

Status: Accepted

Date: 2026-09-02

Maintainer acceptance: accepted on 2026-09-02 after the maintainer reviewed the central/Worker operating flow,
approved event-driven quiet monitoring and role separation, and clarified that the two current Codex projects are an
intentional project-scoped context configuration rather than duplicate repositories.

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0018](0018-authority-first-workstream-dispatch.md)

Preserves: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md),
[ADR-0008](0008-local-first-team-coordination-and-cross-machine-metadata.md),
[ADR-0014](0014-dynamic-workstream-succession-contract.md),
[ADR-0030](0030-fast-candidate-freeze-and-asynchronous-validation.md)

Evidence snapshot: [Central Coordination Context and Latency Audit](../snapshots/2026-09-02-central-coordination-context-audit.md)

## Context

ADR-0018 made prompts transport rather than authority, and ADR-0030 separated Candidate freeze from expensive
validation. Neither decision implements the internal coordination loop: durable platform-task binding, quiet event
collection, a bounded current-control summary or separation between the maintainer's product discussion and execution
monitoring. This problem concerns communication and execution efficiency inside Orrery's coordination architecture;
it is not a Workstream DAG plugin feature.

In current self-host use, one long-lived central conversation manually filled that gap. It discussed product ideas,
wrote authority documents, dispatched and polled Workers, replayed task outputs, reviewed code and browser state, and
performed integration. Worker results could arrive during an unrelated maintainer discussion. Missing platform task
bindings and stale runtime state then forced the central conversation to rediscover or reconcile facts from multiple
sources.

## Decision

1. Orrery separates one human-facing entry into two logical planes:
   - the **Product and Decision plane** discusses intent, improves expression, explores options and authors accepted
     ADR/Design/Plan changes;
   - the **Execution Coordination plane** binds tasks, dispatches committed authority, consumes runtime events,
     exposes blockers and routes bounded integration requests.
2. The Product and Decision plane does not receive ordinary Worker messages, poll tasks or retain Worker command
   histories. The Execution plane does not invent product intent, approve decisions or become author authority.
3. Dispatch/resume returns after the task accepts the request or reports an immediate blocker. Monitoring is opt-in.
   Unchanged `running` state emits no repeated user-facing message.
4. Runtime transitions are deduplicated into an event inbox. Events arriving during an active maintainer discussion are
   queued rather than inserted into or steering that turn. Informational events remain quiet; attention events are
   shown after the turn or on request; critical safety signals may raise a visible alert but still do not impersonate
   user input.
5. Core defines a provider-neutral Local-only binding between `workstream_id`, worktree identity and an opaque platform
   session/task reference. Adapters declare capabilities such as `status`, `open`, `message`, `launch` or `rebind`;
   unsupported capabilities remain absent or Unknown.
6. Platform task execution status and Orrery Workstream lifecycle remain independent axes. `idle` or `archived` does
   not imply `closed`; `candidate-frozen` does not imply validated, integrated or cleanup-eligible.
7. The Execution plane exposes a regenerable, read-only control snapshot containing current task identity, exact HEAD,
   task-description revision, scope revision, lifecycle/runtime/validation axes, blockers and next relevant event. The
   ordinary active-task projection targets roughly 1–2 KiB and is otherwise bounded/paginated; it contains no Prompt,
   transcript, source/diff body or credential and has no decision authority.
8. Task inspection is progressive: summary/status and final receipt first, then one relevant turn, then one named
   command/output, with full history only as an explicit last resort. Historical tool output is never the default
   central read path.
9. Initial and amended task messages remain reference-only: task identity, code base when different, exact authority
   revision, required paths, execution configuration and hard safety boundary. Acceptance criteria belong in Plan and
   Pending Validation; review findings use bounded source-linked records rather than a second requirements copy.
10. Candidate freeze releases active write ownership while preserving the immutable historical scope and receipt.
    Reopening requires a new scope revision. ADR-0030 remains the semantic owner and W3.1 remains the implementation
    owner of this behavior.
11. Role-aware document entry is the intended direction: integrators/releases read global control entrances, while a
    bounded Worker reads universal safety rules plus its task authority and relevant State. The current `AGENTS.md`
    mandatory chain remains effective until a separately validated implementation proves that reduced routing
    preserves task quality; this ADR does not silently activate an unvalidated context treatment.
12. The current self-host keeps two Codex project records over the same repository as an intentional Local-only host
    profile: the project-scoped 1M configuration serves Product/Decision work, while implementation/Worker tasks use
    the execution project. This is deterministic host routing, not a Git split, DAG relation or public requirement.
    If the host later provides suitable per-session configuration, the two records may collapse without changing
    Orrery semantics.
13. The read-only Orrery DAG plugin is outside this decision's implementation scope. It may later consume the same
    derived status as any other view, but it is neither an owner, predecessor nor required delivery surface for the
    internal coordination changes.
14. Codex is the first host adapter, not a Core dependency. Claude Code, DeepSeek Harness and other providers implement
    only the capabilities their runtime can prove; no Codex thread field enters provider-neutral Core semantics.
15. Routine aggregation, deduplication and routing should be deterministic and model-free where possible. Model
    selection is a non-binding deployment recommendation rather than a product constraint. The maintainer may keep the
    Product/Decision central task at the highest available reasoning strength; no Orrery gate may lower or override
    that preference merely for efficiency.

## Consequences

- The maintainer can continue a product discussion without Worker events taking over the active turn.
- The central conversational context no longer needs to duplicate Worker execution context.
- A small derived snapshot adds schema/projection maintenance, but replaces repeated manual reconstruction and is never
  edited as a second truth store.
- Platform adapters require explicit capability work, but vendor-specific IDs and lifecycle differences remain out of
  Core.
- Existing tasks receive no new scope from this decision. A future implementation task identity remains unallocated
  until the maintainer explicitly names/registers it.
- Current public releases, default consumers, remote execution and Team permissions do not change.

## Mapping

- Approved Design: [Dual-plane Event-driven Orrery Coordination](../design/dual-plane-event-driven-orrery-coordination.md)
- Draft implementation decomposition: [Internal Coordination Efficiency](../implementation/plans/2026-09-02-internal-coordination-efficiency.md)
- Pending Validation: [Internal Coordination Efficiency](../validation/2026-09-02-internal-coordination-efficiency.md)
- Official Codex references: [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic),
  [App Server](https://learn.chatgpt.com/docs/app-server)
