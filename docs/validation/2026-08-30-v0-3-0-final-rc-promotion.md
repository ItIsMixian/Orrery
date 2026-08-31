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
