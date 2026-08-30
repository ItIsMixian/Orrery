---
name: orrery-dispatch
description: Prepare and hand off new or materially rescoped Orrery-managed tasks from committed authority documents. Use when the user asks to start, split, assign, arrange, or materially change a task in an Orrery repository. Do not use for ordinary implementation that already has a current task-description version.
---

# Orrery Dispatch

Create a task reference, not a second copy of its requirements.

## Dispatch

1. Read the target repository's `AGENTS.md` and the authority sources it requires. If the authority chain is absent or
   not integrated, report that state instead of inventing project facts.
2. Require explicit user intent before creating a new task. Discussion, approval of a design direction, or “consider
   this later” does not authorize task creation.
3. For a new task, write the effective ADR and Approved Design when required, plus an Implementation Plan and Pending
   Validation. For a material mid-flight change, send only an immediate stop instruction, then write a dated Plan
   amendment and update Pending Validation. For a new decision outside the explicitly identified unique integration
   worktree, use a stable
   `PO-DEC-<task-id>-<slug>` proposal under `docs/decisions/proposals/`; do not allocate a numeric ADR. A branch name or
   locally observed “next number” does not grant integrator authority. The integrator allocates and relinks the next
   free numeric ADR against the current integration index.
4. Commit the authority-only change before task creation or resumption. Call this commit the **任务说明版本** in
   user-facing text; keep its full Git commit SHA in technical details.
5. Create or continue the task using the host's task tool when available. Preserve the target project's worktree,
   model and reasoning conventions.
6. Send only the task identity, code base when different, task-description version, exact authority paths, execution
   configuration and hard safety boundary. Do not repeat the requirements in the task message.
7. Require the implementation Agent to read the exact committed sources, preserve dirty work, acknowledge the source
   version and register or refresh its Git-private scope before first or resumed product writes.
8. Do not poll, wait on, or repeatedly read the task unless the user explicitly asks for monitoring.

If the host cannot create or message tasks, return the compact reference message for the user to send; do not invent
a task or claim dispatch succeeded.

## Boundaries

- Prompt, transcript, task summary and Agent receipt are transport or provenance, never project authority.
- A missing commit, missing path, stale scope or prompt/Plan mismatch stops product writes; the committed authority
  source wins.
- Do not approve semantic relations, merge, delete, release, change credentials or remote settings, or perform other
  user-gated actions.
- Do not implement the delegated product work or aggregate team state. This Skill is an authority handoff, not the
  Orrery Conductor.
