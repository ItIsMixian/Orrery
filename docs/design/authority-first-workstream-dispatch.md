# Authority-first Workstream Dispatch

Status: Approved

Date: 2026-08-30

Governing ADR: [ADR-0018](../decisions/0018-authority-first-workstream-dispatch.md)

## Contract

```text
Maintainer request
  → ADR/Design when required
  → Plan scope + Pending Validation
  → exact authority commit
  → Workstream creation / scope amendment notice
  → Agent reads exact diff and registers scope revision
  → implementation
  → Validation results + State
  → central integration and PROGRESS/HANDOFF
```

The dispatch contract uses existing author roles. Its machine-readable companion, when implemented, is Git-private and
contains only task ID, authority commit, selected paths/hashes, base SHA, scope revision, expected writes, validation
surfaces and Agent acknowledgment. It contains no Prompt body and has no decision authority.

## Initial dispatch

The authority commit must exist before `create_thread`. The created worktree starts from that exact commit whenever the
task's implementation base permits. If code must start from a different Candidate, the prompt identifies both the code
base and the authority commit; the Agent must import/read the authority-only diff before product writes.

The human-readable message is intentionally small:

```text
Execute <task-id> from code base <sha> using authority commit <sha>.
Read <Plan>, <governing ADR/Design>, and <Pending Validation>.
Verify hashes, register scope revision, then continue.
```

## Mid-flight amendment

1. send a stop-only message;
2. commit a dated `Maintainer Scope Amendment` to the existing Plan and update Pending Validation;
3. send only amendment SHA and paths;
4. Agent verifies the exact diff and updates Git-private expected writes/validation surfaces;
5. Agent resumes without treating the follow-up message as requirements.

Material permission, privacy, release or architecture changes still require an ADR/amendment before the Plan change.
Implementation details that remain within an accepted Design use only a Plan amendment.

## Failure behavior

- missing authority commit/path/hash: no product write;
- prompt text differs from Plan: Plan wins and the discrepancy is reported;
- amendment arrives while a command is atomic: finish the atomic command, then stop;
- dirty worktree cannot safely import amendment: preserve changes, read the exact sources out-of-tree, report the
  divergence and wait for an integration-safe method;
- transcript-only requirement: ignored as non-authoritative until committed.

## User-facing and release boundary

This process does not expose task prompts, source code, diffs or local credentials through Team Mode. It is an
authoring/coordination rule, not a new public document type or remote execution capability. Product automation and a
public Skill projection require their own implementation evidence.
