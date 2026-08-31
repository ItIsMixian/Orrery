# Implementation Plan: Orrery v0.3.0 Final RC, Promotion and Publication

Status: Phase 0 revision-7 preview accepted; source freeze and fresh routed validation authorized; no RC task registered

Date: 2026-08-30

Governing decision: [ADR-0021](../../decisions/0021-v0-3-0-release-scope-default-matrix.md)

Approved Design: [v0.3.0 Release Scope and Default Matrix](../../design/v0-3-0-release-scope-default-matrix.md)

## Entry gates

- [ ] W7.3 includes ADR-0020 hierarchy, ADR-0022 pinned local ELK layout-only integration and ADR-0023 explicit frozen
  legacy recovery, has integrated State/Validation, reviewed vendor/license/provenance inventory and
  maintainer-approved final page; no silent engine fallback exists. Integration, inventory and routed evidence are
  complete; only the exact integrated page acceptance remains open.
- [x] CI7 acceptance gates/validation lease/no-repeat/predictive refusal has integrated State/Validation.
- [x] A4/U2.3 current central source and component versions are reconciled against final W7.3/CI7.
- [ ] Child receipts are current for exact integrated surfaces; the `f41b659...` receipts remain valid historical
  evidence but do not cover the real lightweight Personal/Relation Inbox composition blocker found on `807096d...`.
- [x] ADR-0021/default/distribution matrix remains unchanged.

Until all gates pass, do not register Final RC, modify public manifest/components/workflow, push a ref, create a tag or
build release assets.

## Phase 0 — clean integration and webpage acceptance

1. [x] Unique integrator merges accepted dependencies into a clean central descendant and reconciles State/Validation/
   DEVLOG/indexes additively.
2. [ ] Run CI7-selected integration Fast and Checkpoint once. The `f41b659...` run is preserved; after the revision-5
   product correction and maintainer preview acceptance, route the corrected exact source once without replaying
   unaffected child suites.
3. [ ] Start the exact integrated Unified page; maintainer accepts all primary pages at 1440×900 and 390×844, including
   global stop/rollback, zero overflow and zero console warning/error.
4. [ ] Bind acceptance to the source SHA. Any change after acceptance requires a new page review.

### 2026-08-30 central integration acceptance binding

The unique integrator merged W7.3 exact `44ea200d9dfa0107168ed49b8306393bbfccafa8` and CI7 exact
`111f4abc47b8122aee5469db4489ad6fb0dee75a` into the local integration line. The stable relevant source at
`f41b659720905367351ed11394754f4d7bb6b547` received one fresh Fast and one fresh Checkpoint receipt under CI7
fingerprint `0eea7fbe07a182de209d080dfa7c2c04a7c12956f801342ebf7c15b0a37aab7d`. Phase 0 remains open only for the
resulting documentation commit's exact-SHA Unified page acceptance.

- [x] Register Git-private Workstream `V0.3.0-central-integration-acceptance` on the primary integration worktree,
  primary `release-and-toolchain`, affected `test-coverage`, `documentation-system`, `project-structure`,
  `multi-worktree-collaboration` and `authority-meta-model`. It started at revision 1 and reached revision 4 through
  the bounded component/help/mapping corrections recorded in Validation.
- [x] Bind this Plan and the matching Final RC Validation from the exact committed task-description version. Expected
  writes are limited to central State/Validation/DEVLOG/index reconciliation, component inventory, and a narrow
  `scripts/ci/change-mapping.json` correction plus its existing CI fixture/test only if the integrated dry-run proves
  over-selection. No product feature or release input may be added in this Workstream.
- [x] Reconcile runtime component constants with the merged inventory: Core and Observatory pyproject/component
  metadata already declare 0.1.19, so the exact `packages/project-orrery-core/src/project_orrery_core/__init__.py` and
  `packages/project-orrery-observatory/src/project_orrery_observatory/__init__.py` version constants must also be
  0.1.19 before routing. This is inventory alignment only; no API/default/release change is authorized.
- [x] Keep the reviewed ELK files as Observatory package data, not root managed tools. Remove the four package-local
  `vendor/...` entries from exact
  `packages/project-orrery-observatory/src/project_orrery_observatory/component.json`; do not copy vendor bytes into
  the repository root or Skill project template, and do not alter package-data inclusion, hashes or provenance.
- [x] Preserve the A4/U2.3 help-surface vocabulary during W7.3 integration. Exact
  `packages/project-orrery-observatory/src/project_orrery_observatory/unified_observatory.py` must expose the existing
  “事实与规则” label inside the read-only help/status panel while keeping the standalone Authority navigation absent.
  This is copy reconciliation only; it adds no page, authority selection or action.
- [x] Create a Git-private human-experience gate receipt for the maintainer's accepted W7.3 product direction and this
  Phase 0 integration contract. The receipt grants validation entry only; it is not release operation authorization.
- [x] Run Fast and Checkpoint dry-run/explain first. A predictive or unknown-timing refusal is resolved or reported
  before any formal lease; dry runs do not count as stage evidence.
- [x] After the mapping/fingerprint is stable, issue exactly one Fast lease/run and exactly one Checkpoint lease/run.
  An unchanged non-green result is not retried or substituted. Record the receipts and total cost in the matching
  Validation.
- [ ] Commit the reconciled central evidence and rebuild the Unified page from that clean exact SHA. Final RC remains
  blocked until the maintainer accepts that SHA's desktop/mobile page.

Use the current root task as the unique integrator; do not create a separate Codex task for Phase 0. This Workstream
may not run Candidate/Promotion/release validation, modify public manifest/defaults/workflows, push, tag, publish or
perform a release operation.

### 2026-08-31 scope revision 5 — real lightweight composition blocker

Static page `807096d672f318335ae77c8f8fdbcc38c480f890` exposed a real integration failure before maintainer acceptance:
U2.3's `orrery-active-task-projection-v1` renders a semantic `<footer>` and no legacy `.po-foot`, while W7.3
`inject_relation_inbox()` still requires the old `.po-foot` marker. Relation Inbox quarantine then makes Personal
appear unavailable even though all seven navigation identities remain visible. The existing Unified runtime test
replaces the real lightweight renderer with a full Personal fixture, so its green composition assertion did not cover
this contract.

This is a compatibility bug inside already accepted ADR-0016/ADR-0017 behavior, not a new release, schema, authority or
security decision; no new ADR is required. Scope revision 5 authorizes only:

- `packages/project-orrery-observatory/src/project_orrery_observatory/relation_inbox.py`: replace the presentation-
  specific `.po-foot` anchor with a bounded stable Personal article boundary while preserving Personal local-only and
  Team request-only placement;
- `tests/test_unified_observatory.py`: make the composition contract cover the real lightweight Personal panel and
  retain two-inbox/no-action-in-Graph assertions;
- this Plan, matching Final RC/W7.3 Validation, affected State/PROGRESS/HANDOFF/DEVLOG/index records and generated
  external previews only.

Before the maintainer sees and accepts a corrected real page, only source editing, `git diff --check`, page generation,
DOM/layout/console inspection and local preview serving are allowed. Do not run unittest, pytest, focused suites,
Fast, Checkpoint, Candidate, Promotion or release commands. After preview acceptance, commit/freeze the exact source,
route one fresh Fast and one fresh Checkpoint under CI7, reconcile evidence, then rebuild the final docs SHA for the
binding page review.

### 2026-08-31 scope revision 6 — obsolete automatic Unknown lineage proposals

The revision-5 real preview proves the Personal/Team anchor correction works, but its relation inbox exposes seven
pending proposals. Four have different proposal IDs yet the same source, target and semantics:
`V0.3.0-central-integration-acceptance → U1-U2-integration-baseline`, `derived_from`, Unknown. Read-only inspection
traces them to earlier task-base changes: `auto_capture_derived_from()` hashes the exact base into a new proposal ID,
but never appends `superseded` to older tool-owned open proposals for the same endpoints. This inflates the actionable
count and makes stale mechanical observations look like four human decisions.

ADR-0017 and its Approved Design already require append-only `superseded` proposal lifecycle and say a changed base
uses an explicit proposal/rebind path. Revision 6 implements that existing decision; it does not authorize a new ADR,
relation type, automatic semantic confirmation or destructive history rewrite. Exact behavior:

- before creating/reusing the current automatic Unknown `derived_from` proposal, append a `superseded` event to every
  other still-`proposed` `auto-derived-unknown-*` proposal with the same source/target whose proposer is exactly
  `tool:workstream-registration`;
- preserve all proposal files and revisions; never touch human/Agent/Harness/conductor proposals, accepted/deferred/
  rejected proposals or effective relations;
- leave exactly one current automatic Unknown proposal for one session input; repeating the same input performs zero
  writes. If a previously superseded task base becomes current again, create a new scope-bound generation instead of
  reopening terminal history;
- return the superseded proposal IDs in the local mechanical receipt without turning them into project authority;
- run one bounded self-host session refresh after implementation so the current inbox mechanically supersedes the
  three obsolete rows. It may not accept, defer or reject any proposal.

Authorized repository writes are the revision-5 files plus exact
`packages/project-orrery-core/src/project_orrery_core/workstream_relation_capture.py` and
`tests/test_workstream_relation_capture.py`, followed by the already-listed authority/evidence documents. The preview
gate remains unchanged: before the maintainer sees the repaired page, no unittest/pytest/focused/Fast/Checkpoint/
Candidate/Promotion/release command may run. The preview must show four pending proposals total—one current automatic
Unknown lineage proposal plus the three distinct existing dependency proposals—while Personal local confirmation,
Team request-only and Graph read-only boundaries remain unchanged.

### 2026-08-31 scope revision 7 — mechanical `derived_from` cannot be human-confirmed

The four-proposal mobile preview shows the remaining automatic Unknown `derived_from` card with “接受”, a dependency-
gate selector defaulting to “实现完成前”, and “更改阶段”. This violates ADR-0017: effective `derived_from` authority
belongs only to Core after exact ancestry verification, and only `depends_on` carries `required_for`. Existing Core
would let a local task owner reach `accept_proposal()` for `derived_from`; later evidence checks usually fail closed,
but the authority route and UI affordance are still wrong.

Revision 7 enforces the already accepted authority matrix without adding an ADR or schema version:

- `accept_proposal()` rejects every `derived_from` before role or evidence evaluation with an explicit mechanical-
  authority error; no human role can override ancestry;
- local capability remains sufficient to defer/reject an Unknown observation, but the Personal inbox renders only
  `暂缓／Unknown` and `拒绝` for `derived_from`; it renders no Accept, gate selector or change-gate action;
- `depends_on` and `absorbs` retain their existing authorized actions, Team remains request-only, and Graph remains
  action-free;
- Core and Unified regression contracts record the refusal/UI split, but no test command runs before the next real
  desktop/mobile preview.

Authorized paths remain the four revision-5/6 product/test files and the listed authority/evidence documents. The
preview gate now additionally requires one lineage card with two local actions, three dependency cards with their
existing gate controls, zero Team decision buttons, four total pending proposals and zero document horizontal
overflow.

### 2026-08-31 maintainer preview acceptance after revision 7

The maintainer explicitly confirmed the revision-7 page. This closes the pre-test preview gate only and authorizes the
unique integrator to commit/freeze the four product/test files, refresh the Git-private session to that exact SHA, run
CI7 Fast/Checkpoint dry-run/explain, and—only if the plans are allowed—issue one fresh lease/run for each stage.

Accepted preview facts are: seven navigation identities, no unavailable primary consumer, two inboxes, four pending
cards, one lineage card with only defer/reject and no select, three dependency cards with existing gate controls, zero
Team decision buttons, and zero document horizontal overflow at 1280×720 and 390×844. This acceptance is not the final
exact-SHA page gate, Candidate, Promotion or release authorization. No test ran before the confirmation.

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
