# Validation: Orrery v0.3.1 Launcher Hotfix Release

Status: Pending Validation

Date: 2026-08-31

Plan: [v0.3.1 Launcher Hotfix Release](../implementation/plans/2026-08-31-v0-3-1-launcher-hotfix-release.md)

## Required evidence — one pass each

- [ ] exact hotfix Candidate `8f60fac...` and product `06a277d...` reviewed without additional product scope;
- [ ] version/manifest/notes identify v0.3.1 and exclude alias/scheduler/DSH/auto-delete;
- [ ] two exact-Git builds produce identical entry receipt, ZIP and checksum;
- [ ] extracted Windows archive reaches HTTP 200, second normal launch reuses PID/port, and stop leaves no marker,
  process or listener; no Computer Use is invoked;
- [ ] one exact non-main Promotion run yields both required Windows/Ubuntu checks green;
- [ ] protected main, annotated tag and Release assets all bind the same exact SHA;
- [ ] remote ZIP/checksum verification passes;
- [ ] v0.3.0 assets remain unchanged and its Release notes visibly direct Windows users to v0.3.1.

## Cost/refusal record

Record wall time and every command/run once. Do not list or replay unrelated child suites. An unchanged failure is not
retried; record the failed identity and stop for a new exact-SHA correction.

## Result

Pending. No v0.3.1 manifest, tag, asset or remote Release exists under this task-description version.

## 2026-08-31 revision-1 metadata stop and revision-2 acceptance

The first release worktree metadata invocation completed one test and failed one:

- PASS: frozen v0.2 contracts remain historical;
- FAIL: `test_phase1_component_boundaries_and_compatibility_projection` expected 103 managed-runtime entries while
  the inspected manifest contains 104 and explicitly includes the new hotfix `subprocess_policy.py` path.

No commit, package, Promotion, tag, Release or v0.3.0 remote edit occurred. Revision 2 may correct only the stale
cardinality to 104 and run the same two tests once on a new fingerprint. All later evidence remains Pending.

## 2026-08-31 revision-2 PASS and package command parse stop

Release-input `41fcc0f751d694b7be873dbc6113ecbc00d0869a` completed the two direct metadata tests 2/2 PASS.
The subsequent PowerShell package command failed parsing at `$name:` before either exact-Git builder started. No
package output, remote action or repository change occurred. Revision 3 may correct only the external interpolation
syntax and continue the two-build gate on the same release-input SHA; no metadata test is repeated.

## 2026-08-31 first actual builder refusal

The corrected orchestration started the first builder on `41fcc0f...`; it failed before archive creation with
`missing=[]` and one extra tracked path: the accepted hotfix `subprocess_policy.py`. The v0.3.1 manifest and its Core
mirror both contain 163 paths and omit that shipped module. The second build, runtime, push and every remote stage did
not start. Revision 4 may add only that path, update the count/hash/mirror and its existing 163-count test expectation,
then execute the two-build gate once on a new release-input SHA.

## 2026-08-31 package PASS and uninstalled-root runtime stop

Exact `6a018319a52537b541cf0285bc45f529253f818b` produced two byte-identical packages. ZIP SHA-256 is
`e5a4fa548db0a091b3d359ce7d16d6e3ef1d211f75560aaea3c5283df5f1b6e5`. The first runtime command did not
run an installer and therefore searched for an installed-project launcher under the extracted Skill root; Python
returned file-not-found before supervisor startup. No marker, process, listener, push or remote action occurred.
Revision 5 may install that exact archive into a fresh isolated Git target and run the one authorized launcher smoke;
package evidence is retained and not repeated.
