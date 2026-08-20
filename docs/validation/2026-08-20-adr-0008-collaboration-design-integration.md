# 2026-08-20 ADR-0008 协作 Design 集成验证

Status: Passed for local integration

Integration base: `51379c14f290535d79a37f4d8773f9f804abfa9f`

Candidate: `codex/agent-context-routing@022d51a53d90465729f172596a77aeae3dba823b`

Governing decisions:

- [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md)
- [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), allocated during this integration from provisional `PO-DEC-WT-002`

## Scope

This record validates the documentation-only integration of the consolidated multi-Workstream collaboration model. It covers formal ADR allocation, authority links, Approved Design, active Plan, current State boundaries and generated observatory structure. It does not validate any session, overlap, review, cleanup, LAN or Team Mode implementation.

## Integration actions

- Merged the single candidate documentation commit into an independent clean integration worktree with `--no-ff --no-commit`.
- Allocated ADR-0008 without rewriting ADR-0007, and updated all provisional references.
- Kept default Personal Mode, opt-in Team Mode, central read-only／local execution and metadata-only synchronization as effective constraints while State continues to report those tools as unimplemented.
- Synchronized `AGENTS.md`, State Docs, PROGRESS, HANDOFF, DEVLOG and indexes at the integration point.
- Preserved the candidate Design consolidation Validation and added this separate integration evidence instead of rewriting implementation history.

## Validation results

| Check | Result |
|---|---|
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid; integration branch correctly reported as `integrated candidate` before local main fast-forward |
| `python -X utf8 scripts/docsite/build_docsite.py --out %TEMP%\project-orrery-adr-0008-integration-20260820.html` | PASS — 775 KB; 8 ADR、5 State、6 subsystem、2 Snapshot、55 docs、11 Plan、5 Library |
| PowerShell local Markdown-link scan | PASS — 238 Markdown files、441 local links、0 missing targets |
| `git diff --check` | PASS |
| Provisional-reference scan | PASS — no active path or authority reference remains to the former proposal; historical origin mentions are retained intentionally |

After committing this merge, local `main` must be fast-forwarded and re-run dependency-free structure validation before handoff. That post-commit check is reported in the task handoff rather than retroactively changing this evidence table.

## Known boundaries

- No product code, release artifact, runtime support status, network listener or user configuration changed.
- No unit／runtime／model test was required for the documentation-only merge; later implementation phases have their own Validation matrix.
- The local integration does not push `origin/main`, create a tag or publish a release.
