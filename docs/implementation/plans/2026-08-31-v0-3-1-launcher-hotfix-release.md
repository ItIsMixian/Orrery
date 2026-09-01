# Implementation Plan: Orrery v0.3.1 Launcher Hotfix Release

Status: Approved; execute immediately after task-description acknowledgment

Date: 2026-08-31

Governing decision: [ADR-0024](../../decisions/0024-v0-3-1-emergency-launcher-hotfix-release.md)

Approved Design: [v0.3.1 Launcher Hotfix Release](../../design/v0-3-1-launcher-hotfix-release.md)

## Execution

1. Start an isolated GPT-5.6 Sol medium release worktree from exact hotfix Candidate `8f60facfaf15a531c085baf94d7207d068d29d9a`.
   Read and acknowledge this task-description version, then register Git-private scope before writes.
2. Review the hotfix diff/Validation once. Change only public/component versions, manifest, package asset names,
   plain-language v0.3.1 notes and directly required release fixtures. Do not alter the hotfix behavior or add features.
3. Commit one clean release-input SHA. Run `git diff --check`, directly affected release metadata checks, two exact-Git
   builds, and one extracted Windows launcher start→reuse→stop smoke. Do not run Fast, Checkpoint, local Candidate,
   browser automation, Computer Use or unrelated runtime portfolios.
4. Push only `promotion/v0.3.1-rc` at that exact SHA and run the existing Promotion once. Wait for both named required
   checks. Do not retry an unchanged non-green SHA or run lanes manually.
5. If green, fast-forward the same SHA to protected main, create annotated tag `v0.3.1`, let the tag workflow verify
   its exact assets, then publish the GitHub Release and remotely verify ZIP/checksum hashes.
6. Edit the v0.3.0 Release notes by prepending a severe Windows launcher warning and link to v0.3.1. Do not modify its
   tag or assets. Record remote identities, then append release closeout State/Validation/DEVLOG in a later docs commit.

## Hard boundaries

- No DSH Store, CLI alias, scheduler, auto-delete, new UI, schema/default change or independent package release.
- No repeated A4/W7.3/CI7/feature suites and no full local release matrix.
- No Computer Use or foreground mouse/keyboard control.
- Any scope expansion, mismatched archive, security regression or non-green required check stops publication.

## Completion

Complete means v0.3.1 is the verified Latest Release, its remote assets match the exact tagged SHA, and v0.3.0 visibly
links Windows users to it while retaining immutable assets.
