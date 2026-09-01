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

## 2026-08-31 scope revision 2 — managed-runtime cardinality fixture

The first direct metadata run stopped after 1 PASS / 1 FAIL, before commit, packaging or any remote action. The
Observatory manifest correctly contains 104 managed-runtime entries because the accepted hotfix adds exactly
`project_orrery_core/subprocess_policy.py`; the same test already asserts that exact path is present but still freezes
the pre-hotfix total of 103.

Revision 2 authorizes only changing that existing `tests/test_project_orrery.py` cardinality expectation from 103 to
104. Preserve the explicit path assertion and every release-input edit already in the dirty task worktree. After the
new authority version is acknowledged and Git-private scope is refreshed, make the one-line correction, create a new
release-input commit/fingerprint, and run the same two direct metadata tests once. No other test expectation, product
code, Plan step or validation scope changes; the failed fingerprint is not retried.

## 2026-08-31 scope revision 3 — package orchestration parse correction

Release-input exact `41fcc0f751d694b7be873dbc6113ecbc00d0869a` passed both metadata tests. The first package
orchestration was rejected by the PowerShell parser before either builder started because a diagnostic string used
`$name:` instead of a delimited variable such as `${name}:`.

Revision 3 authorizes only correcting that external command text and executing the two-build package gate on unchanged
`41fcc0f...`. This is not a retry of a builder, package fingerprint or test: neither build process began and no output
directory was created. Do not modify repository files, rerun metadata tests or add another validation step.
