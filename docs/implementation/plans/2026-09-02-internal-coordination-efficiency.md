# Implementation Planning Record: Internal Coordination Efficiency

Status: Design-backed decomposition; task identity and implementation not authorized

Date: 2026-09-02

Task identity, program/series classification and repository owner: pending explicit maintainer allocation

Primary subsystem: `multi-worktree-collaboration`

Affected subsystems: `documentation-system`, `release-and-toolchain`, `context-routing-research`, `test-coverage`

Governing decision: [ADR-0033](../../decisions/0033-dual-plane-event-driven-orrery-coordination.md)

Approved Design: [Dual-plane Event-driven Orrery Coordination](../../design/dual-plane-event-driven-orrery-coordination.md)

## Objective

Replace the long-lived conversational coordination loop with provider-neutral platform binding, an event inbox and a
bounded control snapshot, while keeping product discussion, authority, Worker execution, validation and integration
separate.

## Ownership before dispatch

- The maintainer must decide whether each implementation slice belongs to Project Orrery, `orrery-dispatch`, a host
  coordination runtime/Adapter or another explicitly named repository.
- The read-only Orrery DAG plugin is not a predecessor, owner or required delivery surface.
- The unique integrator must select exact code/authority baselines for every chosen repository.
- Any Core schema path must be bootstrapped by its permitted owner before a non-integrator task writes it.
- Existing Workstream ownership and accepted Candidates must be reconciled so the new work does not claim their files
  or semantics.
- A dated scope revision must list exact expected writes and validation surfaces before any task/worktree is created.

No task code, task/worktree, repository mutation or product write is authorized by this planning record.

## Phase A — contracts and projection

1. Freeze provider-neutral binding, event and control-snapshot schemas without embedding Codex-specific fields.
2. Reuse existing independent Workstream lifecycle, runtime, freshness, validation and cleanup axes.
3. Make Candidate freeze release active write ownership while retaining immutable historical scope; consume W3.1's
   accepted contract rather than implementing a competing owner.
4. Build a deterministic bounded control projection with source links, generation/currentness and Unknown behavior.
5. Detect duplicate active platform bindings and missing/archived execution channels without automatic deletion,
   closure or reassignment.

## Phase B — host coordination runtime and Codex Adapter

6. In the maintainer-selected host coordination owner, add a Codex adapter over documented App Server
   task/status/turn events and current task APIs. Do not assume the read-only DAG plugin repository owns this runtime.
7. Deduplicate unchanged status and emit one logical event per transition.
8. Implement the focus lease: events queue while Product/Decision is in an active turn and never steer or inject user
   input into that discussion.
9. Expose quiet/milestone/attention/critical delivery classes in the existing right-panel surface. Closing the panel
   stops visible refresh, while the bounded local event store remains recoverable without a model daemon.
10. Resolve `workstream_id` to the opaque Codex task ID for open/message operations only when the binding declares the
    required capability.

## Phase C — authority transport and operating policy

11. Generate reference-only initial/resume messages from committed authority and reject a second acceptance checklist.
12. Make summary/final receipt the default inspection route; detailed turn/command/history retrieval requires an
    explicit escalation reason and bounded target.
13. End dispatch turns after acceptance/immediate blocker. Monitoring remains an explicit user choice; unchanged
    running state produces no commentary.
14. Configure the self-host role mapping so Product/Decision uses the dedicated project-scoped 1M project and
    Execution/Workers use the implementation project. Persist only Local-only opaque project references.

## Phase D — role-aware context evaluation

15. Design a new controlled context-routing treatment; do not reuse or reinterpret failed H1/H2/B/S results.
16. Compare the current mandatory entry against role-aware Worker cold-start/resume and Integrator entry on a frozen
    task portfolio with exact pre-write usage and task-quality Oracles.
17. Amend `AGENTS.md` and templates only if the treatment meets its quality and safety gates. Otherwise keep the
    current mandatory chain and ship the coordination gains independently.

## Phase E — additional host adapters

18. Extend the opaque binding/capability contract to Claude Code and DeepSeek Harness only after their real runtimes
    prove status/open/message/attach behavior individually.
19. Unsupported capabilities remain absent/Unknown; no adapter inherits Codex evidence.

## Validation

- deterministic binding, duplicate/orphan and stale-currentness fixtures;
- event deduplication, ordering, reconnect and missed-event reconciliation;
- focus-lease proof that Worker events cannot interrupt an active Product turn;
- bounded snapshot size/pagination and no private payload controls;
- reference-only transport and progressive inspection negative tests;
- Candidate-frozen active-ownership release without validation/closure escalation;
- current two-project self-host routing without treating sidebar membership as DAG evidence;
- provider capability fallback and zero-network Personal behavior;
- controlled before/after context and latency evaluation before any `AGENTS.md` routing switch.

## Hard boundaries

- no Prompt, response, transcript, source/diff body, credential or private path in binding/events/snapshot;
- no background model polling and no Worker event inserted as user input;
- no new decision, approval, relation, validation, merge, cleanup or release authority in derived state;
- no automatic task deletion, closure, rebind, retry, merge, main/tag/push or publication;
- no scope expansion of any current task, including the read-only DAG plugin and active Project Orrery Workstreams;
- no public/default switch or cross-provider support claim without independent evidence.

## Completion definition

- the maintainer can discuss product intent without Worker event interruption;
- Execution resolves Workstream/task/worktree identity without conversational memory;
- ordinary monitoring consumes a bounded current snapshot and emits no unchanged narration;
- blockers and milestones are delivered once with source links and correct priority;
- Candidate, validation, closure and cleanup axes remain independent;
- task messages are reference-only and detailed task output is retrieved only on demand;
- the role-aware context treatment either passes its frozen quality gates or remains unadopted;
- Codex evidence is not generalized to Claude or DeepSeek without adapter-specific Validation.
