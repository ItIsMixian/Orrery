# Central Coordination Context and Latency Audit

Date: 2026-09-02

Scope: dated self-host evaluation; this Snapshot does not replace live State, Git-private Workstream sessions, Codex
task status or future Validation.

## Question

The maintainer reported that the long-lived central coordination task felt slow, repeatedly interrupted product
discussion and consumed excessive context while dispatching, monitoring and reviewing related Workstream tasks.

## Read-only observations

The audit inspected the most recent 30 central turns through bounded task metadata, current Codex task/project
metadata, Git worktree/session state and the authority documents required by the sampled W3.1 cold start. It did not
copy Prompt or transcript bodies into this Snapshot.

- 27 sampled central turns had completed. Their recorded mean duration was about 416 seconds.
- The sample contained 90 `wait_threads` calls totaling about 4,135 seconds, or 36.8% of completed-turn duration.
- It contained 15 `read_thread` calls; eight requested historical command/tool outputs rather than summary-only state.
- It contained 20 cross-task messages, two task creations and two central context-compaction events.
- W7.4 had accumulated 17 turns, 385 command records and seven context-compaction events in the inspected history.
- U2.5 had accumulated three turns, 142 command records and one context-compaction event.
- The early inspected W3.1 slice spent about 551 seconds and 27 command records on authority/scope bootstrap before a
  visible product file change.
- The 11 files read for that W3.1 entry path totaled 111,246 characters and 1,322 lines. Removing only a repeated
  `AGENTS.md` read plus global `HANDOFF`/`PROGRESS` from a non-integrator cold start would remove 36,193 characters,
  but this is an analytical counterfactual, not an adopted routing policy.
- At the observed checkpoint, W7.4 was described by author documents as `candidate-frozen / validation-pending`, while
  its Git-private session still advertised `implementing`, `blocked-by-conflict` and nine expected-write entries.
  This made historical authorization look like active write ownership.
- The four inspected live Workstream sessions had no platform task/session ID binding, so the central task recovered
  Codex thread identities from task listings or prior conversation state.
- Two saved Codex projects intentionally pointed at the same repository. The maintainer explained that the split is a
  current-host deployment workaround: the product/decision central project receives the project-scoped 1M context
  setting, while implementation Workstreams use the implementation project. This is Local-only configuration, not a
  duplicate repository or a public Orrery default.

## Interpretation

The dominant problem is not worktree isolation or exact-SHA authority. It is the use of one long-lived conversational
task as a manual substitute for a still-unimplemented internal coordination runtime. That task mixed product
discussion, authority authoring, dispatch, synchronous monitoring, transcript replay, code/browser review and
integration. Each scope
correction could therefore trigger another authority commit, message, import, read and scope refresh.

The lowest-risk improvements are to end dispatch turns promptly, suppress unchanged progress messages, retrieve
summary state before detailed task output, keep task notices reference-only and separate active write ownership from
historical scope. Role-aware document routing needs its own implementation and quality validation; prior
context-routing candidates did not pass adoption gates.

## Evidence limits

- Character counts and task/tool records are context-pressure indicators, not exact token billing.
- Task durations include waiting and tool execution and are not a controlled causal benchmark.
- Codex task/project metadata and Git-private sessions are Local-only observations, not author authority.
- The project-scoped desktop configuration constraint is maintainer-observed. Official Codex documentation confirms
  project-specific configuration as a supported layer, but does not establish a universal absence of every possible
  per-run override across CLI, IDE, App Server and future desktop versions.
- Any product adoption requires the ADR, Design, Plan and Validation gates linked from this Snapshot.

## Sources

- [ADR-0018](../decisions/0018-authority-first-workstream-dispatch.md)
- [ADR-0030](../decisions/0030-fast-candidate-freeze-and-asynchronous-validation.md)
- [Context-routing State](../state/context-routing-research.md)
- [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex App Server](https://learn.chatgpt.com/docs/app-server)
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
