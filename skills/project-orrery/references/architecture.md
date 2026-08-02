# Project Orrery architecture

## Authority chain

The primary chain is:

`Product intent -> Seed -> effective ADR -> approved Design -> implementation -> State Docs -> Validation -> Snapshot`

- Product intent describes the experience or outcome sought.
- Seed records principles that should not drift casually.
- ADR records what was decided and why. A later ADR may amend or supersede an earlier one.
- Design expands accepted decisions into a coherent specification. Draft design has no authority.
- Implementation Plan maps approved design and effective ADRs to tasks and validation. It is intent, not evidence.
- Implementation is the actual code, configuration, assets, data, or operations.
- State Docs describe what is true now and link to the implementation and governing ADRs.
- Validation records reproducible evidence.
- Snapshot evaluates the project at a date; it never replaces live state.

## Supporting inputs

- Backlog contains directions not yet accepted.
- Library contains research, references, examples, guides, and material indexes.
- AGENTS.md and HANDOFF.md are reader-specific navigation entrances, not competing truth stores.
- PROGRESS tracks current tasks and milestones.
- DEVLOG appends implementation and verification history.

## Invariants

1. `accepted` does not mean `implemented`.
2. Plans do not prove completion.
3. State Docs report actual behavior, including gaps and divergence.
4. An intentional change to a durable decision requires a new ADR; do not rewrite accepted history.
5. A Snapshot is a dated assessment, not a mutable status page.
6. Library material informs proposals but cannot silently constrain implementation.
