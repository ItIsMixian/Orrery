# ADR-0018: Authority-first Workstream Dispatch

Status: Accepted

Date: 2026-08-30

Amends: [ADR-0007](0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0012](0012-document-governance-and-information-lifecycle.md)

## Context

Orrery previously allowed a central task to create an Agent task or append a large follow-up prompt before the changed
requirements entered the project's authority chain. The transcript is durable inside Codex, but it is not a project
Plan, is not indexed by the Observatory, is not guaranteed to be read by later Agents, and cannot prove what scope was
accepted. Asking the implementation Agent to reconstruct the Plan afterward reverses the intended authority order and
can lose critical decisions.

The maintainer requires the opposite order: author and commit the governing change first, then let the Agent read the
exact changed authority sources. A task prompt is transport, not authority.

## Decision

1. **Authority precedes dispatch.** Before creating a Workstream task, the unique coordinator/integrator writes the
   applicable ADR/amendment, Approved Design, Implementation Plan scope and Pending Validation acceptance contract,
   then commits them to an exact dispatch baseline.
2. **Prompts become references.** The task message contains only the task ID, exact authority commit, required source
   paths, execution configuration and hard safety boundary. It must not duplicate the full requirements.
3. **Agent acknowledgment precedes product writes.** The Agent reads the exact paths from the authority commit,
   verifies their hashes/status, registers the Git-private Workstream scope revision, and reports the selected sources
   before its first product write.
4. **Mid-flight changes use the same order.** A running Agent pauses at a safe boundary. The coordinator commits a
   Plan `Maintainer Scope Amendment` and Pending Validation changes first, then sends only the amendment commit and
   paths. The Agent incorporates or reads that exact commit, refreshes Git-private scope, and only then resumes.
5. **No new author-document role.** Implementation Plan, ADR/Design, Validation and State keep their existing roles.
   Git-private dispatch receipts reference their hashes; they do not replace them.
6. **Transcript is non-authoritative.** A prompt, Agent receipt or task summary cannot add requirements, approve a
   decision, change scope or prove validation unless the corresponding author source exists.
7. **Validation remains prospective then evidentiary.** Before implementation, Validation may contain a clearly
   labelled Pending acceptance contract. After execution it records actual reproducible results without rewriting the
   accepted scope history.
8. **Emergency correction still pauses first.** An urgent safety stop may be sent immediately, but no new
   implementation direction follows until the authority amendment is committed.
9. **Existing in-flight tasks are remediated, not rewritten.** U2.3 and W7.3 pause, receive the first authority-first
   amendment commit, update their scope revision and preserve previous transcript/Git history as non-authoritative
   provenance.

## Consequences

- Requirements become reviewable before code and survive task/archive/tool boundaries.
- Agent prompts become shorter and cannot silently diverge from Plan checklists.
- The coordinator must make a small author commit before dispatch or material scope change.
- Future Core/CLI automation may create versioned dispatch receipts, but the manual authority-first order takes effect
  immediately.

## Mapping

- Approved Design: [Authority-first Workstream Dispatch](../design/authority-first-workstream-dispatch.md)
- Plan: [Authority-first Workstream Dispatch](../implementation/plans/2026-08-30-authority-first-workstream-dispatch.md)
- Validation: [Authority-first Dispatch Decision Contract](../validation/2026-08-30-authority-first-workstream-dispatch.md)
