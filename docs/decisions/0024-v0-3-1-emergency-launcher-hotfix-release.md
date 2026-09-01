# ADR-0024: Orrery v0.3.1 Emergency Launcher Hotfix Release

Status: Accepted

Date: 2026-08-31

Maintainer acceptance: accepted on 2026-08-31 with the instruction to publish as quickly as possible and not repeat
the v0.3.0 validation overhead.

Amends: [ADR-0021](0021-v0-3-0-release-scope-default-matrix.md)

Preserves: [ADR-0016](0016-unified-observatory-shell-and-single-local-entry.md)

## Context

Public v0.3.0 can flash many command windows on Windows because its hidden supervisor launches console-subsystem Git
children without an explicit no-window policy. Repeated normal launch also starts a second supervisor attempt instead
of reusing the healthy instance. The bounded fix exists as clean Worktree Candidate
`codex/windows-launcher-console-flash-hotfix@8f60facfaf15a531c085baf94d7207d068d29d9a`; product exact
`06a277de3e380f7c8a957d76cba60c29db0fd3e1` has focused tests and a terminal-instrumented Windows smoke.

Replacing the existing v0.3.0 assets would make one version and URL identify different bytes and would not update
already downloaded copies. A new patch is required, but repeating every v0.3.0 feature and runtime loop would delay
the corrective release without adding evidence for the narrow changed surface.

## Decision

1. The next public release is **v0.3.1**, scoped only to the Windows launcher fix, required version/manifest/package
   metadata and plain-language release/upgrade notes. DSH Store, the `orrery` alias, scheduler and every other deferred
   feature remain out of scope without a promised replacement version.
2. v0.3.0 tag, ZIP, checksum and asset URLs remain immutable. After v0.3.1 is public, prepend a prominent Windows
   launcher warning and v0.3.1 upgrade link to the v0.3.0 Release notes; do not delete or replace its assets.
3. Reuse the exact v0.3.0 Promotion evidence for unchanged surfaces and the exact hotfix child evidence for the
   changed surface. Do not replay A4, W7.3, CI7, browser, migration or unrelated feature suites.
4. The patch gate is deliberately short: one clean release-input commit, two quick exact-Git deterministic builds,
   one extracted-archive Windows launcher smoke without Computer Use, and one exact-SHA non-main Promotion using the
   existing required Windows/Ubuntu checks. Do not run a duplicate local full Candidate or a second Promotion on an
   unchanged SHA.
5. A non-green gate stops. Fix only the demonstrated cause on a new SHA; never rerun the same failed fingerprint merely
   to seek green. A green exact SHA proceeds directly through protected main, annotated v0.3.1 tag, asset publication,
   remote hash verification and the v0.3.0 warning.
6. The maintainer's acceptance authorizes that complete sequence without another pause between green gates. A new
   failure, scope expansion, asset mismatch or security boundary change still stops and returns to the maintainer.
7. Release notes lead with what users need to do and what was fixed. Internal component inventory and validation
   jargon stay in a short technical section, not the opening explanation.

## Consequences

- v0.3.1 becomes Latest; v0.3.0 remains downloadable historical evidence but is visibly discouraged on Windows.
- The patch does not pull previously deferred 0.3.1 feature ideas into this emergency release.
- Required exact-SHA Windows/Ubuntu branch protection remains intact; speed comes from eliminating duplicate local
  matrices and irrelevant suite replay, not from bypassing the final hosted gate.

## Mapping

- Approved Design: [v0.3.1 Launcher Hotfix Release](../design/v0-3-1-launcher-hotfix-release.md)
- Plan: [v0.3.1 Launcher Hotfix Release](../implementation/plans/2026-08-31-v0-3-1-launcher-hotfix-release.md)
- Validation: [v0.3.1 Launcher Hotfix Release](../validation/2026-08-31-v0-3-1-launcher-hotfix-release.md)
