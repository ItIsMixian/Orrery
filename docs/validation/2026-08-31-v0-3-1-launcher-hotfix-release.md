# Validation: Orrery v0.3.1 Launcher Hotfix Release

Status: Validated

Date: 2026-08-31

Plan: [v0.3.1 Launcher Hotfix Release](../implementation/plans/2026-08-31-v0-3-1-launcher-hotfix-release.md)

## Required evidence — one pass each

- [x] exact hotfix Candidate `8f60fac...` and product `06a277d...` reviewed without additional product scope;
- [x] version/manifest/notes identify v0.3.1 and exclude alias/scheduler/DSH/auto-delete;
- [x] two exact-Git builds produce identical entry receipt, ZIP and checksum;
- [x] extracted Windows archive reaches HTTP 200, second normal launch reuses PID/port, and stop leaves no marker,
  process or listener; no Computer Use is invoked;
- [x] one exact non-main Promotion run yields both required Windows/Ubuntu checks green;
- [x] protected main, annotated tag and Release assets all bind the same exact SHA;
- [x] remote ZIP/checksum verification passes;
- [x] v0.3.0 assets remain unchanged and its Release notes visibly direct Windows users to v0.3.1.

## Cost/refusal record

Record wall time and every command/run once. Do not list or replay unrelated child suites. An unchanged failure is not
retried; record the failed identity and stop for a new exact-SHA correction.

## Result

PASS. Orrery v0.3.1 is the verified Latest Release. Product/tag source exact
`1d9223cb07b94674b58471e0c19addf748b16221`; Promotion run `33465321477` and tag workflow run `33465760947`
are green. Remote ZIP/checksum hashes match the exact-Git build, and v0.3.0 retains its original tag/assets while
visibly directing Windows users to v0.3.1.

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

## 2026-08-31 runtime PASS and Promotion preflight refusal

The installed-project smoke on `6a018319...` passed: HTTP 200, second launch reused PID `167716` and port `8765`,
stop returned 202, and marker/listener/matching processes all reached zero. Promotion run `33464068810` stopped in
inventory preflight: exactly five existing hotfix test IDs were unregistered. No matrix lane ran; both required checks
failed closed and no publication action occurred.

Revision 6 may add only those five IDs with the exact common ownership/stage/cost/dependency metadata in the Plan,
run one local registry self-check, then create package/runtime evidence and one Promotion on a new SHA. The failed run
and old SHA are preserved and not retried.

## 2026-08-31 Promotion lane failure set

Exact `606dafc...` passed registry preflight, Windows/Ubuntu repository gates, local two-build and installed-project
runtime gates. Run `33464450752` then failed in lanes 03/05/09. Downloaded Windows/Ubuntu artifacts identify six unique
test IDs: one update-checker fixture, three collaboration version fixtures, one Graph component-version fixture and
the cross-platform child-policy audit. The five newly registered hotfix tests were discovered and four passed on both
platforms; only the audit-path implementation failed on Linux under its explicit Windows simulation.

Revision 7 may apply only the exact three-cause correction in the Plan, execute those six IDs once on a new SHA, and
then recreate package/runtime/Promotion evidence. No main/tag/Release or v0.3.0 edit occurred; the old run is immutable
and not retried.

## 2026-09-01 final release evidence

- revision-7 correction commit: `1d9223cb07b94674b58471e0c19addf748b16221`;
- exact six-ID run: 6/6 PASS in 54.037 seconds, once;
- deterministic build: two fresh 164-entry roots produced ZIP
  `2970fc208d529022b0ac33c2b6a35e9874ef87fa90d67bd0dafb52fc5d2b6445`, checksum-file
  `1650f51f76b8f24362aeb6929eb0ebac6166b7e20239d400c085d9bd3b440e78` and receipt
  `926f98a489be29570b1a144bdd6ee7fd15f19f4d3de5fe22644d4f86e11c4ba9` byte-identically;
- installed-project runtime: HTTP 200; second launch reused PID `212636`, port `8765` and instance
  `f6438cedcca648b1a625078316fef2c0`; second exit 0; stop 202; marker/listener/PID/matching process all zero;
- exact non-main Promotion: run `33465321477` PASS, including both named required checks;
- protected main and annotated `v0.3.1`: exact `1d9223c...`; tag workflow `33465760947` PASS;
- GitHub Release: `https://github.com/ItIsMixian/Orrery/releases/tag/v0.3.1`, non-draft/non-prerelease;
- remote re-download: ZIP and checksum-file hashes match the deterministic build; checksum content declares the
  same ZIP hash;
- v0.3.0: annotated tag remains exact `a0a728b1f096650e475a1327d29973f2a1f9e267`; asset digests remain
  `sha256:12a7061227cd2f9137dc2923716523059fbc8b528df8b1c7a8cdd8283d7d2385` (ZIP) and
  `sha256:599b416d5b03a74665e1e9c5864b4902ab13ba9037956d3ef04919a45737e011` (checksum file); only the Release
  body gained the Windows warning/link.

No Computer Use, retry of an unchanged non-green SHA, full local suite, manual lane replay, DSH/alias/scheduler/
auto-delete scope or historical asset replacement occurred.
