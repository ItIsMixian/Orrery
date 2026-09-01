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

## 2026-08-31 scope revision 4 — include the shipped subprocess policy in archive inventory

The first actual exact-Git builder on `41fcc0f...` failed closed before archive creation: the tracked tree contains
`project-orrery/packages/project-orrery-core/src/project_orrery_core/subprocess_policy.py`, but the v0.3.1 archive
allowlist omitted it. The second build did not start and no remote action occurred.

Revision 4 authorizes only adding that exact path to the sorted v0.3.1 `archive_paths`, updating `archive_entries`
from 163 to 164, recomputing the path-list SHA-256, keeping the Core `release-v0.3.1.json` mirror byte-equivalent, and
changing the existing release-package count expectation from 163 to 164. Do not change any other allowlist member,
product file, version or test. Commit a new release-input SHA; then run the two-build gate in fresh temporary roots.
The failed `41fcc0f...` package identity is not retried, and no separate metadata or package test is added locally.

## 2026-08-31 scope revision 5 — install the Skill archive before launcher smoke

The two-build gate passed on `6a018319a52537b541cf0285bc45f529253f818b`; ZIP, checksum and full receipt are
byte-identical. The first runtime command then treated the extracted Skill root as an installed project and looked for
root `scripts/docsite/serve_orrery.py`. The file is correctly projected only after the bundled installer creates a
target project. Python failed before supervisor start; no marker, listener or process was created.

Revision 5 authorizes only corrected external runtime orchestration using the already verified ZIP: extract to a fresh
root, run its `project-orrery/scripts/install_project_orrery.py` into a fresh target, initialize/commit that isolated
target as a local Git repository, then execute the target's normal headless start→reuse→stop smoke. Do not rebuild,
modify repository files, run a test suite or reuse the failed target directory. Continue to Promotion only if this
single installed-project smoke is green.

## 2026-08-31 scope revision 6 — register the five existing hotfix tests

The installed-project runtime gate passed on `6a018319...`. Promotion run `33464068810` then failed in preflight before
any test lane because final discovery contains five hotfix tests absent from the exact registry. Required checks failed
closed from the missing inventory; no main/tag/Release action occurred.

Revision 6 authorizes only adding these existing IDs to `scripts/ci/change-mapping.json`:

- `test_unified_observatory.UnifiedLifecycleAndLauncherTests.test_child_policy_audit_is_explicit_bounded_and_records_windows_flags`
- `test_unified_observatory.UnifiedLifecycleAndLauncherTests.test_live_healthy_identity_reuses_exact_loopback_runtime`
- `test_unified_observatory.UnifiedLifecycleAndLauncherTests.test_normal_main_reuses_before_render_and_console_legacy_keeps_console`
- `test_unified_observatory.UnifiedLifecycleAndLauncherTests.test_production_child_policy_is_windows_only_and_explicitly_disableable`
- `test_unified_observatory.UnifiedLifecycleAndLauncherTests.test_unified_startup_and_refresh_git_sites_use_shared_child_policy`

Each entry uses owner surface `Packaging/Adapters/docsite`, shard `packaging-project`, allowed stage `promotion` only,
cost class `low`, budget 15 seconds, dependency `observatory-shell`, and a narrow launcher-hotfix reason. Do not add or
modify tests, budgets, lanes, existing entries or path mappings.

Commit a new SHA, run `python scripts/ci/validate_ci.py --all` once as registry/inventory preflight without loading test
suites, then perform the already-established two-build and installed-project runtime gates once on that exact SHA.
Only after those pass may `promotion/v0.3.1-rc` fast-forward and trigger one new Promotion. Run `33464068810` and SHA
`6a018319...` are not retried.

## 2026-08-31 scope revision 7 — close the six exact Promotion failures

Promotion run `33464450752` passed preflight and both repository gates on exact
`606dafc282eda6fd499a28e4701c3dc9174873fe`, then failed in lanes 03/05/09 on both platforms. Downloaded lane
artifacts reduce the result to six unique failing test IDs and three bounded causes:

1. four existing assertions still freeze Core/Observatory `0.1.19` although the v0.3.1 release input declares
   `0.1.20` (`test_collaboration_contract.py` twice, `test_collaboration_w3.py` once and
   `test_workstream_relation_graph_observatory.py` once with two values);
2. `test_project_orrery.py` uses `0.3.1` as a synthetic newer compatible release, which is now equal to the installed
   version and correctly returns `up_to_date`; the synthetic version/tag must become `0.3.2`;
3. the opt-in audit helper constructs `Path(...)` after its Linux test temporarily sets `os.name="nt"`; this makes
   `pathlib` choose unsupported `WindowsPath`. Use the already platform-bound `os.path.basename` for caller names and
   built-in `open(target, ...)` for the audit file, preserving the same JSONL contract and fail-closed `OSError` path.

Revision 7 authorizes only those exact edits in
`packages/project-orrery-core/src/project_orrery_core/subprocess_policy.py`,
`tests/test_project_orrery.py`, `tests/test_collaboration_contract.py`, `tests/test_collaboration_w3.py`, and
`tests/test_workstream_relation_graph_observatory.py`. Do not change versions, manifests, product behavior outside the
audit write implementation, test IDs, registry, budgets or workflows.

Commit a new SHA and run only the six previously failing IDs once locally. If green, perform two exact-Git builds and
one installed-project runtime smoke on that SHA, then fast-forward the promotion ref and run one new Promotion. Do not
replay successful lanes, the complete local suite, SHA `606dafc...` or run `33464450752`.
