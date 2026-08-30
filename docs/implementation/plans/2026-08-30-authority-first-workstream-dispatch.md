# Implementation Plan: Authority-first Workstream Dispatch

Status: Manual process active; product automation planned

Date: 2026-08-30

Governing ADR: [ADR-0018](../../decisions/0018-authority-first-workstream-dispatch.md)

Approved Design: [Authority-first Workstream Dispatch](../../design/authority-first-workstream-dispatch.md)

## Immediate manual adoption

- [x] Freeze the rule that transcript text is not implementation authority.
- [x] Pause U2.3 and W7.3 before further scope expansion.
- [x] Author U2.3 Plan/Pending Validation and W7.3 Scope Amendment/Pending Validation centrally.
- [ ] Commit one exact authority baseline and send only its SHA/paths to the paused Agents.
- [ ] Each Agent acknowledges source hashes and refreshes Git-private scope before continuing.
- [ ] Central integration verifies implemented diff against the committed checklist, not the original prompt.

## Product automation

- [ ] Add a versioned Git-private dispatch receipt referencing authority paths/hashes, code base, scope revision,
  expected writes and validation surfaces.
- [ ] Add CLI inspect/acknowledge operations with no arbitrary file write or remote execution.
- [ ] Teach Workstream registration to refuse first product write when a required dispatch receipt is missing/stale.
- [ ] Add mid-flight amendment CAS/staleness and preserve prior revisions append-only.
- [ ] Project a compact read-only dispatch provenance in Personal/Team technical details without Prompt content.
- [ ] Add Codex/Harness adapter evidence; unsupported hosts remain advisory.

## Validation

- initial dispatch cannot occur before authority commit;
- transcript-only scope is rejected;
- prompt/Plan mismatch fails closed;
- mid-flight change pauses until exact amendment acknowledgment;
- dirty worktree preservation and out-of-tree authority read;
- ADR-required change cannot be smuggled through Plan-only amendment;
- Team sync excludes Prompt/body/source/diff/credentials;
- normal implementation/Validation/State/PROGRESS lifecycle remains unchanged.

Root PROGRESS/HANDOFF describe the manual adoption now; public/release support waits for the automation Candidate.
