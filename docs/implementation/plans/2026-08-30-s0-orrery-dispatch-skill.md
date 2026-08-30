# S0 Orrery Dispatch Skill

Status: Planned; authority scope frozen before implementation

Date: 2026-08-30

Governing ADRs: [ADR-0018](../../decisions/0018-authority-first-workstream-dispatch.md), [ADR-0017](../../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)

Approved Design: [Authority-first Workstream Dispatch](../../design/authority-first-workstream-dispatch.md)

Primary subsystem: `release-and-toolchain`

Affected: `documentation-system`, `project-structure`, `test-coverage`

## Goal

Add a minimal `orrery-dispatch` Codex Skill that performs the authority handoff around task creation and material
rescoping. It is a thin host workflow over the target repository's existing authority chain, not a second authority
source and not the future full Orrery Conductor.

## Deliverables

- [ ] `skills/orrery-dispatch/SKILL.md` with a narrow trigger for starting, splitting, assigning or materially
  rescoping an Orrery-managed task.
- [ ] `skills/orrery-dispatch/agents/openai.yaml` with concise UI metadata and implicit invocation enabled.
- [ ] No scripts, references, assets, service, database, schema or network dependency in S0.

## Required workflow

- [ ] Read the target repository's `AGENTS.md`, current control entrances, relevant State and active Plan before
  dispatch work.
- [ ] Require explicit user intent before creating a new task; discussion or an idea alone does not authorize it.
- [ ] For a new task, author and commit the effective ADR／Approved Design／Plan／Pending Validation before task
  creation. For a material mid-flight change, send stop-only first, then commit a dated Plan amendment and Pending
  Validation before sending new direction.
- [ ] Present the authority commit to users as **任务说明版本**. Preserve the full Git commit SHA only in technical
  details and Agent-facing references.
- [ ] Send the implementation Agent only task identity, code base, task-description version, exact authority paths,
  execution configuration and hard safety boundary. Do not duplicate the requirements in the task message.
- [ ] Require source-version acknowledgment and Git-private scope revision before first/resumed product writes.
- [ ] Do not continuously wait, poll or reread the implementation task unless the user explicitly asks for monitoring.

## Hard boundaries

- The Skill cannot approve `depends_on`, `absorbs`, release, deletion, merge, credentials, remote settings or any
  other user-gated action.
- It cannot treat Prompt, transcript, task summary or Agent receipt as project authority.
- It does not implement product code, aggregate team state, schedule work, select an integrator or replace the
  project-specific `AGENTS.md`.
- It does not modify the current `project-orrery` install/migrate/audit Skill or claim the future S1 Conductor exists.
- It remains an unreleased source Candidate until an independent release plan includes it.

## Validation

- `skill-creator` quick validation passes for the new folder.
- Frontmatter description triggers only Orrery task dispatch/rescope requests.
- Manual scenarios cover new task, mid-flight amendment, idea-only refusal, missing authority commit, dirty worktree,
  prompt/Plan mismatch and user-requested versus unsolicited monitoring.
- Repository, integrated-installation, release/private-artifact and routed Fast gates pass.
- Diff contains only the two Skill files, one generic validation mapping update and required
  State／Validation／DEVLOG／index closeout.

Implementation updates Release & Toolchain／Documentation System／Project Structure State, independent Validation,
DEVLOG and indexes. Root PROGRESS／HANDOFF are updated only by the central integrator.

## 2026-08-30 Maintainer Scope Amendment — Validation Routing

The first routed Fast dry-run correctly refused `skills/orrery-dispatch/**` as an unmapped path. S0 remains paused
until this amendment is committed and acknowledged.

- [ ] Add `skills/orrery-dispatch/**` to the existing generic `release-packaging` path mapping in
  `scripts/ci/change-mapping.json`; do not add task-ID or branch-specific router logic.
- [ ] Refresh the Git-private Workstream scope revision before modifying the mapping.
- [ ] Re-run route dry-run and require zero unknown paths／expected writes, then run the selected formal tier.
- [ ] Keep the existing Fast／Checkpoint budgets, test IDs, stage authority and Promotion coverage unchanged.

This is validation metadata for an existing release/toolchain surface. It does not add a third Skill resource, change
the Skill behavior, authorize packaging or require a new ADR.
