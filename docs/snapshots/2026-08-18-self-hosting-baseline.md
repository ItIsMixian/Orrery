# Snapshot: Project Orrery self-hosting baseline

**Date:** 2026-08-18
**Assessment:** Integrated working-tree baseline; not yet a published release

## What this snapshot evaluates

This is the first dated assessment after Project Orrery adopted its own documentation architecture through [ADR-0001](../decisions/0001-project-orrery-self-hosting.md). It evaluates the effective principles, current State, implementation evidence, and context-routing research available on 2026-08-18.

## Stable facts

- No stable GitHub tag or Release exists yet. The release manifest on `origin/main` describes the first `v0.2.0` release candidate.
- The repository now has a real authority entrance (`AGENTS.md`), accepted self-hosting ADR, Approved Design, completed implementation plan, five State Docs, reproducible Validation, Progress, Devlog, and Handoff.
- `skills/project-orrery/` remains the released product source. Root `docs/` describes this repository; it does not replace the portable template.
- `experiments/context-routing/` and external raw benchmark repositories remain non-authoritative evidence surfaces.
- Pilot 004 matched B and H at 3/3 corrected acceptance, but H used 47% more input tokens and about 15% more time. H is not adopted; B is only the next experiment baseline.

## Evidence reviewed

- [Project structure State](../state/project-structure.md)
- [Documentation-system State](../state/documentation-system.md)
- [Context-routing research State](../state/context-routing-research.md)
- [Release and toolchain State](../state/release-and-toolchain.md)
- [Test-coverage State](../state/test-coverage.md)
- [Self-hosting validation](../validation/2026-08-18-self-hosting-baseline.md)

## Gaps and risks

- The self-hosting and Pilot 004 changes are still working-tree changes until reviewed and committed.
- Raw benchmark evidence lives outside the repository at a machine-local path and does not yet have a retention/export policy.
- Agent-reported content reads are not independent Harness evidence.
- The slimmer H2 policy and multi-worktree documentation protocol are backlog items, not accepted architecture.

## Assessment

The self-hosting authority chain is coherent enough to serve as Project Orrery's current documentation control plane. The product release surface and research surface remain correctly separated. The next safe action is to review the complete diff, preserve validation evidence, and decide the release boundary before committing or publishing.
