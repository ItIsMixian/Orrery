# Validation: Orrery v0.3.0 Final RC and Promotion

Date: 2026-08-30

Status: PENDING — release decision accepted; dependencies and Final RC not complete

Authority: [ADR-0021](../decisions/0021-v0-3-0-release-scope-default-matrix.md) and
[Final RC Plan](../implementation/plans/2026-08-30-v0-3-0-release-candidate-and-promotion.md)

## Required evidence

- W7.3/CI7/A4/U2.3 exact integrated SHAs, current State/Validation and non-stale acceptance receipts;
- maintainer final Unified page acceptance bound to exact central source SHA;
- real 0.3.0 manifest with exact versions/defaults/support sets/assets/URLs/date and no placeholders/local/private data;
- immutable v0.2 tag target and frozen historical object/hash checks;
- exact-Git-object builder, entry receipt and repeated-build equality;
- new/brownfield/0.2/migration/restore/offline/unknown/mixed portfolios;
- final ZIP Codex runtime and Harness JSON Windows/Ubuntu bounded evidence;
- non-main exact-SHA Windows/Ubuntu Promotion and both required checks;
- same-SHA main, separately authorized annotated tag, tag rebuild/checksum;
- separate GitHub Release authorization and remote asset download/hash verification.

## Test-cost boundary

Final RC must consume valid child receipts and run only integration/release-owned gates. It cannot replay every child
suite by default. CI7 controls stale-surface selection, same-fingerprint no-repeat and predictive refusal. This
Validation records actual wall/setup/runtime cost and any explicit packaging waiver.

No public manifest, main, tag, asset or Release fact is PASS until the exact evidence is recorded here.

## Phase 0 central integration acceptance — pending evidence

Current local merge facts before formal validation:

- W7.3 focused Candidate: `44ea200d9dfa0107168ed49b8306393bbfccafa8`;
- W7.3 central merge: `ae909741edc8b72d004c8701d96fd3a810e0540c`;
- CI7 Candidate: `111f4abc47b8122aee5469db4489ad6fb0dee75a`;
- combined local integration merge: `079de741aa13c338051f537650898633492f764e`.

The combined worktree is clean and low-cost syntax/JSON/diff checks passed during conflict resolution. These checks
are not routed Fast/Checkpoint evidence. Required next evidence is a versioned Git-private Phase 0 Workstream and
human gate receipt, stable Fast/Checkpoint dry-run plans, one formal receipt for each stage, additive State/Validation/
DEVLOG reconciliation, and final desktop/mobile review of the resulting clean exact SHA. Candidate/Promotion,
manifest/package/runtime, push/main/tag/Release and publication remain out of scope.

Initial runtime inspection found Core and Observatory `__version__` still at 0.1.18 while their merged pyproject,
component and root inventory declare 0.1.19. Scope revision 2 must authorize the two exact `__init__.py` writes and
record their alignment before CI7 computes the stable integrated fingerprint. No routed stage has started.

Scope revision 2 alignment is complete: a direct source import reports Core 0.1.19, CLI 0.1.22 and Observatory
0.1.19, exactly matching `packages/component-versions.json`; `git diff --check` is clean. This is a component inventory
check, not routed stage evidence.

The first Fast and Checkpoint dry runs both refused before a selection plan because two merged W7.3 registry entries
still depended on removed surface ID `observatory-ui`. No lease was issued and no test loaded. The router inventory
build also invoked the locally configured briefing/roadmap/milestone Provider; that was an unintended dry-run setup
cost, not test evidence. Subsequent dry runs set `DOCSITE_AI_ENABLED=0`.

The registry correction maps the Graph-native series/conflict test and the promotion-only Chinese status taxonomy
test to exact provider-neutral `observatory-graph`; it does not restore broad `test_workstream*.py` or Maintenance
dependencies. Phase 0 lineage must also rebind from the pre-merge source to task base `86a4660`, because this
Workstream consumes the W7.3/CI7 child receipts and validates only integration-owned reconciliation after the merge.

After the exact lineage rebind, the second Fast/Checkpoint dry-run pair refused before plan creation because final
unittest discovery contained four W7.3 IDs missing from the registry. No lease or test run occurred. The registry now
adds the two program-hierarchy IDs as promotion-only `collaboration-maintenance` evidence and the two pure Graph IDs
as low-cost `observatory-graph` evidence. It does not add broad Workstream globs or Graph→Maintenance dependencies.

A five-method non-formal integration probe then produced two Harness PASS results, two Unified loader errors caused by
an incorrect test class name (the targets did not run), and one real component-boundary failure. The failure showed
that W7.3 had listed package-local `vendor/...` files as root `managed_tools`; that contract would require nonexistent
root/Skill-template duplicates even though the Graph correctly reads the package vendor directory. Scope revision 3
must remove only those four manifest entries while preserving the package bytes and package-data configuration.

After that correction, the exact component-boundary test and Unified host/origin/cookie safety test pass. The
corrected Unified composition method runs but fails because the merged help panel omits the intended literal
“事实与规则”; project principles and operating-rule content remain present. Scope revision 4 may restore that label
in the existing help heading only. The two Harness PASS methods and already-green component/security methods are not
rerun unchanged.
