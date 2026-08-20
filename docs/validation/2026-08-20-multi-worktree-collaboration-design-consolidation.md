# 2026-08-20 多 Workstream 协作 Design 收敛验证

Status: Passed and integrated

Scope: `codex/agent-context-routing` candidate documentation relative to local `main@51379c1`

Governing decisions:

- [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)
- [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), allocated from provisional `PO-DEC-WT-002` during integration

## Purpose

This validation closes the product-level discussion for safe parallel Agent development, progressive Personal／Team command-center UX, conflict handling, human review and conservative cleanup. It verifies documentation authority and structure only; it does not claim that session, overlap, Team Mode, review or cleanup tooling is implemented.

## Authority and consistency review

The review found and corrected these material issues:

1. ADR-0007 limited cross-machine coordination inputs to pushed Git／PR／CI evidence, while later accepted Team Mode discussion allowed opt-in unpushed path-level telemetry. The candidate recorded this as PO-DEC-WT-002; integration allocated ADR-0008 as an explicit amendment and did not rewrite ADR-0007.
2. Ambiguous “one task = one worktree” wording was replaced with Workstream as the isolation unit, platform session as the interaction instance and Change Set as a feature／commit grouping.
3. The private session example was updated from a stale `task_id` skeleton to project mode, Workstream／member／Host／platform session, lifecycle, Scope Revision, subsystem and visibility fields.
4. Cross-machine wording now distinguishes pushed code evidence, voluntarily reported `Local-only` telemetry and genuinely Unknown work／semantics.
5. The Plan implementation targets now use platform-neutral Core／CLI／Observatory／Adapter packages; the published Skill remains a compatibility projection rather than a second canonical implementation.
6. Delivery order now completes zero-network Personal foundation and local review／cleanup before opt-in Team Mode, preventing team dependencies from becoming default personal cost.
7. A concise first-release experience summary was added to the existing Approved Design instead of creating a duplicate product-summary document.

## Validation results

| Check | Result |
|---|---|
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid; candidate authority correctly reported as `integrated candidate` |
| `python -X utf8 scripts/docsite/build_docsite.py --out %TEMP%\project-orrery-collaboration-design-20260820.html` | PASS — 753 KB; 7 ADR、5 State、6 subsystem、2 Snapshot、54 docs、11 Plan、5 Library |
| PowerShell local Markdown-link scan | PASS — 237 Markdown files、429 local links、0 missing targets |
| `git diff --check` | PASS |
| Authority review | PASS — canonical ADR remains immutable; provisional amendment, Candidate Design and Candidate Plan are mutually linked |

## Known boundaries

- ADR-0008 is now canonical, but `accepted` still does not mean the Personal／Team tooling is implemented.
- Current State continues to report only manual worktree isolation／recovery. No State, support status or release claim was upgraded by this documentation review.
- No runtime, networking, platform Adapter or model test was run; those require later implementation-specific Validation.
- No merge into local `main`, remote push, tag or release is part of this record.
