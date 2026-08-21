# M2.2 Observatory Authority Candidate projection

Date: 2026-08-21

Status: Worktree Candidate validated locally; integration pending

Scope: `codex/m2-2-authority-observatory-projection` based on the validated M2.1 commit `db81691`.
This record covers only the root self-hosted Observatory Candidate projection. It does not validate M2.3,
the release template, installer, a default production switch, a stable public API or a release.

Plan: [M2.2 Observatory Authority Candidate projection](../implementation/plans/2026-08-21-m2-2-observatory-authority-projection.md)

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

## Validated design boundaries

- `project_orrery_observatory.authority_projection` consumes a caller-supplied M2.1 bundle and does not import
  `project_orrery_cli`; a subprocess import using only the Observatory source root verifies the package boundary.
- Root-only `build_authority_projection.py` is the managed integration layer that explicitly loads the CLI collector,
  then hands the complete bundle to Observatory. `build_docsite.py` remains byte-equivalent with the release template.
  This preserves the existing `CLI -> Observatory` dependency without a cycle and keeps Candidate source-path
  injection outside the legacy builder.
- `observatory-authority-projection-v1` validates the exact Authority Model, repository snapshot, fact scope and
  evidence visibility before exposing any Core-owned claim. It retains source path, source SHA-256, in-reader
  source link, relations, evidence provenance and `must_not_infer` for every document.
- Effective decisions come only from the M2.1 decision graph. Seed／ADR／Design／Plan／State／Validation／Snapshot
  claims come only from per-document Core results; legacy prose, insights and AI are not projection inputs.
- `ORRERY_AUTHORITY_PROJECTION_VIEW=1` is an independent maintainer opt-in. With the switch absent or disabled,
  returned HTML, stats and report behavior remain exactly legacy. Disabling it after use is the rollback path.
- legacy／unsupported model, invalid scope／visibility, collector error, source/provenance tampering,
  snapshot reconciliation drift or rendering failure returns the unmodified read-only legacy page and a bounded
  `unavailable` projection without partial claims.
- The release Skill template has no M2.2 Candidate entry. The existing root and template `build_docsite.py` remain
  byte-equivalent; only the additional root-only managed entry is withheld until M2.3／release integration is
  separately authorized and validated.

## Failed boundary check and correction

The first synchronized full-suite run reported 1 failure out of 219 tests, with 3 expected skips:
`test_phase1_neutral_cli_matches_legacy_paths_and_preserves_authored_files` detected that an earlier implementation
had placed the opt-in directly in root `build_docsite.py`, breaking its byte-equivalence with the release template.
No Authority semantic test failed, but the packaging boundary was invalid. The implementation was corrected by
restoring `build_docsite.py` unchanged and moving all CLI/Observatory source-path injection, collection, projection and
rendering into root-only `build_authority_projection.py`. A focused 19-test rerun, including the original failing
release-compatibility check, then passed. Final green results below are post-correction evidence.

## Verification

| Check | Result |
| --- | --- |
| pre-change Observatory baseline | PASS — 37 existing tests. |
| `tests.test_authority_observatory_projection` | PASS — 12/12. |
| focused projection + managed/runtime regression | PASS — 22/22 before the final negative-test additions; post-correction 19/19 including root/template parity and the original failing release-compatibility check. |
| Authority suite | PASS — 151 tests with 1 Windows symlink-privilege skip. |
| explicit self-host opt-in static build | PASS — root-only Candidate entry reported projection `ready`; 1220 KB, 11 ADR, 6 State, 7 subsystems, 2 snapshots, 85 classified docs and 14 plans; model/scope/source/effective/reconciliation markers present. |
| full repository suite | PASS — 219 tests, 3 expected skips. |
| integrated structure | PASS — integrated candidate, Authority Model 1 supported and strict evaluation eligible. |
| default static build | PASS — legacy builder 1146 KB with the same 11/6/7/2/85/14 counts; root/template parity test passed; disabling the Candidate switch produced the exact same SHA-256 as the legacy builder. |
| Markdown local links | PASS — 274 Markdown files, 614 local links, 0 missing targets. |
| `git diff --check` | PASS after final documentation synchronization. |

## Remaining boundary

- M2.2 is a Worktree Candidate and root self-host feature only. It is neither canonical nor released.
- The projection remains opt-in and embedded above the legacy dashboard; it does not change legacy stats, graph,
  AI receipts or the Authority shadow diagnostic.
- The M2.1 collector and M2.2 projection remain internal contracts rather than stable top-level APIs.
- Release manifest, installer, component/release versions, Skill template, public model support and default managed
  activation belong to M2.3 or final integration and were not modified here.
