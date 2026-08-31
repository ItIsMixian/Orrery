# Implementation Plan: Orrery v0.3.0 Final RC, Promotion and Publication

Status: Blocked on W7.3/CI7 Canonical integration and final webpage acceptance; no RC task registered

Date: 2026-08-30

Governing decision: [ADR-0021](../../decisions/0021-v0-3-0-release-scope-default-matrix.md)

Approved Design: [v0.3.0 Release Scope and Default Matrix](../../design/v0-3-0-release-scope-default-matrix.md)

## Entry gates

- [ ] W7.3 includes ADR-0020 hierarchy, ADR-0022 pinned local ELK layout-only integration and ADR-0023 explicit frozen
  legacy recovery, has integrated State/Validation, reviewed vendor/license/provenance inventory and
  maintainer-approved final page; no silent engine fallback exists.
- [ ] CI7 acceptance gates/validation lease/no-repeat/predictive refusal has integrated State/Validation.
- [ ] A4/U2.3 current central source and component versions are reconciled against final W7.3/CI7.
- [ ] Child receipts are current for exact integrated surfaces; stale/missing evidence is returned to the owning task.
- [ ] ADR-0021/default/distribution matrix remains unchanged.

Until all gates pass, do not register Final RC, modify public manifest/components/workflow, push a ref, create a tag or
build release assets.

## Phase 0 — clean integration and webpage acceptance

1. Unique integrator merges accepted dependencies into a clean central descendant and reconciles State/Validation/
   DEVLOG/indexes additively.
2. Run CI7-selected integration Fast and Checkpoint once. Do not manually replay child suites with current receipts.
3. Start the exact integrated Unified page; maintainer accepts all primary pages at 1440×900 and 390×844, including
   global stop/rollback, zero overflow and zero console warning/error.
4. Bind acceptance to the source SHA. Any change after acceptance requires a new page review.

### 2026-08-30 central integration acceptance binding

The unique integrator has merged W7.3 exact `44ea200d9dfa0107168ed49b8306393bbfccafa8` and CI7 exact
`111f4abc47b8122aee5469db4489ad6fb0dee75a` into the current local integration line. This does not satisfy Phase 0
until the merged source receives fresh CI7 evidence and exact-SHA webpage acceptance.

- [ ] Register Git-private Workstream `V0.3.0-central-integration-acceptance` on the primary integration worktree,
  primary `release-and-toolchain`, affected `test-coverage`, `documentation-system`, `project-structure`,
  `multi-worktree-collaboration` and `authority-meta-model`, scope revision 1.
- [ ] Bind this Plan and the matching Final RC Validation from the exact committed task-description version. Expected
  writes are limited to central State/Validation/DEVLOG/index reconciliation, component inventory, and a narrow
  `scripts/ci/change-mapping.json` correction plus its existing CI fixture/test only if the integrated dry-run proves
  over-selection. No product feature or release input may be added in this Workstream.
- [ ] Create a Git-private human-experience gate receipt for the maintainer's accepted W7.3 product direction and this
  Phase 0 integration contract. The receipt grants validation entry only; it is not release operation authorization.
- [ ] Run Fast and Checkpoint dry-run/explain first. A predictive or unknown-timing refusal is resolved or reported
  before any formal lease; dry runs do not count as stage evidence.
- [ ] After the mapping/fingerprint is stable, issue exactly one Fast lease/run and exactly one Checkpoint lease/run.
  An unchanged non-green result is not retried or substituted. Record the receipts and total cost in the matching
  Validation.
- [ ] Commit the reconciled central evidence and rebuild the Unified page from that clean exact SHA. Final RC remains
  blocked until the maintainer accepts that SHA's desktop/mobile page.

Use the current root task as the unique integrator; do not create a separate Codex task for Phase 0. This Workstream
may not run Candidate/Promotion/release validation, modify public manifest/defaults/workflows, push, tag, publish or
perform a release operation.

## Phase 1 — register Final RC and freeze inputs

1. Create an isolated Sol-medium Final RC Workstream from the accepted central SHA with precise expected writes.
2. Generate reviewed 0.3.0 candidate manifest, release notes, onboarding and 0.2/brownfield upgrade/rollback guide.
3. Implement exact-Git-object deterministic builder and entry receipt; split automatic tag verification from manual
   GitHub Release publication.
4. Commit release inputs. The resulting new SHA becomes the only local Candidate input.

## Phase 2 — local Candidate and final runtime

1. Run CI7 Candidate for the release-input SHA plus repository/install/secret/generated/private-state gates.
2. Build twice from the same Git objects in independent roots; compare entries and archive/checksum bytes.
3. Execute new/brownfield/0.2/migration/restore/offline/unknown/mixed portfolios from the final archive.
4. Execute final Codex runtime and Harness JSON Windows/Ubuntu bounded runtime portfolios.
5. Any fix creates a new commit and invalidates all prior Candidate/runtime evidence.

## Phase 3 — non-main exact-SHA Promotion

1. Freeze clean 40-char SHA and push only `promotion/v0.3.0-rc`; verify remote ref equality.
2. Run Windows/Ubuntu Promotion required checks and package builds on the same SHA.
3. Aggregate exact inventory and archive/checksum/entry receipts. Mismatch fails unless the maintainer explicitly
   grants the ADR-0021 one-release canonical-builder waiver.
4. A source fix requires a new SHA and complete Promotion rerun.

## Phase 4 — main, tag and release as separate actions

1. Request maintainer authorization for same-SHA protected-main fast-forward after both required checks PASS.
2. Separately request annotated `v0.3.0` tag authorization; verify immutable tag object/target and rebuild assets without
   creating GitHub Release.
3. Present tag/archive/checksum/runtime evidence and known limitations; separately request GitHub Release authorization.
4. Manual publisher revalidates main/tag/SHA/assets, creates Release, downloads remote assets and verifies checksum.
5. Submit a separate closeout commit syncing released State/Validation/PROGRESS/HANDOFF/DEVLOG/Snapshot without
   rewriting v0.2 history.

## RC-owned validation only

- central integration selection and receipt freshness;
- manifest/default/distribution consistency;
- exact-source archive/entry/checksum determinism;
- installation, migration, restore, offline and mixed-component portfolios;
- final Codex/Harness JSON runtime;
- dual-platform Promotion and publication identity.

Child Core/Graph/CI feature suites run again only when CI7 proves their receipt stale for a changed surface. Raw
manual unittest lists from the REL3 Draft are superseded by this ownership rule.

## Deferred and unsupported guard

Release archive, manifest, UI and notes must exclude DSH Store, `orrery` alias, scheduler, auto-delete, PyPI/wheels,
independent Adapter assets, D2/C2 and remote/auto-leader/cloud functionality. Experimental Adapter claims remain exact
and source-only.

## Rollback

- Before non-main push: amend and rerun local RC-owned gates.
- After non-main push: preserve failed evidence; use a new SHA/ref update and rerun Promotion.
- After main before tag: corrective reviewed commit; never reset protected main or claim release.
- After tag: never move/reuse tag; keep Release unpublished or issue a patch version.
- After Release: preserve 0.3.0 assets/checksum and ship a patch.
- User rollback: stop Unified, launch legacy `start-docsite.bat`, use exact migration restore receipt; no automatic
  delete or branch inference.
