# Implementation Plan: Orrery v0.3.0 Final RC, Promotion and Publication

Status: Scope revision 9 Candidate/runtime PASS on `4556db3...`; second Promotion run authorized; GitHub Release withheld

Date: 2026-08-30

Governing decision: [ADR-0021](../../decisions/0021-v0-3-0-release-scope-default-matrix.md)

Approved Design: [v0.3.0 Release Scope and Default Matrix](../../design/v0-3-0-release-scope-default-matrix.md)

## Entry gates

- [x] W7.3 includes ADR-0020 hierarchy, ADR-0022 pinned local ELK layout-only integration and ADR-0023 explicit frozen
  legacy recovery, has integrated State/Validation, reviewed vendor/license/provenance inventory and
  maintainer-approved final page; no silent engine fallback exists. Integration, inventory and routed evidence are
  complete; only the exact integrated page acceptance remains open.
- [x] CI7 acceptance gates/validation lease/no-repeat/predictive refusal has integrated State/Validation.
- [x] A4/U2.3 current central source and component versions are reconciled against final W7.3/CI7.
- [x] Child and Phase 0 receipts are current for their exact product/mapping surfaces. Current Fast/Checkpoint bind
  `74afb9894aeee21c1131f3f8f3c70556563eba13`; final docs/page SHA remains a separate pending gate.
- [x] ADR-0021/default/distribution matrix remains unchanged.

Until all gates pass, do not register Final RC, modify public manifest/components/workflow, push a ref, create a tag or
build release assets.

## Phase 0 — clean integration and webpage acceptance

1. [x] Unique integrator merges accepted dependencies into a clean central descendant and reconciles State/Validation/
   DEVLOG/indexes additively.
2. [x] Run CI7-selected integration Fast and Checkpoint once on the final product/mapping fingerprint without replaying
   unaffected child suites. Current result is Fast 19/19 and Checkpoint 30/30 PASS on `74afb989...`.
3. [x] Start the exact integrated Unified page; maintainer accepts all primary pages at 1440×900 and 390×844, including
   global stop/rollback, zero overflow and zero console warning/error.
4. [x] Bind acceptance to source SHA `a2d7737802be66714ff88064820685de6e231e95`. Later product/page changes require
   a new review; the append-only task-description commit records this acceptance without pretending it was itself reviewed.

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
- [x] Commit the reconciled central evidence and rebuild the Unified page from that clean exact SHA. The maintainer
  accepted `a2d7737802be66714ff88064820685de6e231e95` at desktop/mobile sizes.

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

### 2026-08-31 scope revision 8 — precise relation capture and inbox validation routing

After source freeze, both Fast and Checkpoint dry runs refused before issuing a plan or loading tests. The first pair
found two new unittest IDs; their assertions were folded into existing owner tests so the final inventory does not
grow. The second pair then found exact `relation_inbox.py` unmapped. It also confirms the existing
`collaboration-maintenance` `workstream_*.py` glob would route a relation-capture-only correction through unrelated
slow workspace-maintenance evidence.

Revision 8 authorizes a data-only generic mapping correction, not a task-specific router branch:

- add exact `collaboration-relation-capture` for `workstream_relation_capture.py`, its v2 schema/fixture and existing
  `test_workstream_relation_capture.py`; remove only those exact items from `collaboration-maintenance` while leaving
  other collaboration, relation execution/graph/program and maintenance coverage unchanged;
- add exact `relation_inbox.py` to the existing `observatory-shell` surface because it is composed and secured by the
  single Unified shell; do not map it to Graph or Maintenance;
- move existing relation-capture test dependencies to the new surface. Keep every existing test ID; allow the existing
  `test_registration_auto_derived_from_is_exact_and_idempotent` owner at Fast/Checkpoint/Candidate/Promotion so the
  new supersession and mechanical-authority assertions receive direct evidence without adding a test;
- add versioned routing portfolios proving capture changes exclude the slow maintenance fixture and inbox changes
  select the existing Unified owner without Graph/Maintenance expansion;
- modify only `scripts/ci/change-mapping.json` and
  `tests/fixtures/ci-validation/change-portfolios-v1.json`; `tests/test_ci_validation.py` may change only if the
  existing data-driven portfolio reader cannot consume the new entries.

No new product, schema, budget, stage meaning, required check or Promotion inventory is authorized. After the mapping
commit, rerun Fast/Checkpoint dry-run only. If timing is Unknown, use at most one CI7 bounded focused triage for the
exact owner before issuing formal leases; otherwise issue one fresh Fast and one fresh Checkpoint as already accepted.

### 2026-08-31 scope revision 9 — keep the real product window without Fast over-selection

Revision-8 mapping is committed at `6ffc305f7dec3fda129a142869f14bd5b9fb9afc`. Dry-run against the real pre-
implementation authority base `2aa1c61...` now has no unknown path or registry drift, but selects Fast 25 and
Checkpoint 31 under fingerprint `5bc31c...`. Fast refuses at count >20 and both stages refuse because the newly
expanded Core owner has no CI timing history. A shorter `cb3c6e4...` base selects only 3/4 mapping tests and is allowed,
but it omits the actual product surfaces; it is rejected as insufficient and must not be used for formal evidence.

Revision 9 preserves the real `2aa1c61...` validation window and authorizes only:

- one direct, non-evidence focused invocation of existing owner
  `test_workstream_relation_capture.WorkstreamRelationCaptureTests.test_registration_auto_derived_from_is_exact_and_idempotent`;
  it verifies the new Core body once but does not become Fast/Checkpoint evidence or a reusable receipt;
- return that owner to its prior Promotion-only stage after the focused check, so unknown timing does not force a broad
  formal run; Final RC Promotion still executes it on the release SHA;
- keep `test_current_brand_surfaces_use_orrery_and_current_repository` and
  `test_protocol_and_historical_hash_denylists_are_unchanged` as Fast brand sentinels; move the other four existing
  Brand contract tests to Checkpoint/Candidate/Promotion. No Brand test or coverage is removed;
- modify only `scripts/ci/change-mapping.json`; rerun real-window dry-run after commit. Expected selection is Fast 20
  and Checkpoint 30 with known timing. Budgets, stage meanings, final IDs, required checks and Promotion remain fixed.

If either new dry-run still refuses, stop and record it; do not issue a formal lease or repeat the focused owner.

### 2026-08-31 scope revision 10 — do not expand CI control to validate two data examples

The first revision-9 formal Fast completed 20/20 PASS. Its paired Checkpoint ran once and failed only because
`test_generic_router_selects_docs_authority_and_collaboration_portfolios` hardcodes the old portfolio ID sequence; the
other 29 methods passed in the 5.072s test runtime. The failed fingerprint is blocked and will not be retried.

The conditionally authorized one-line `tests/test_ci_validation.py` update fixed that assertion, but the next dry-run
mapped the whole file to `ci-control`: Fast 41 / predicted 23.297s refused; Checkpoint 51 / 27.988s allowed. No lease or
test ran on this new fingerprint. Adding two routing examples has therefore expanded validation more than the product
change itself.

Revision 10 authorizes rollback of only the two new portfolio objects and the one hardcoded-ID insertion so both files
return exactly to their pre-revision-8 bytes. The precise generic source mappings and Brand tier split remain. Current
mapping evidence will instead be:

- existing registry completeness/mutation/actual-path gates;
- real dry-run path explanations showing `workstream_relation_capture.py → collaboration-relation-capture` and
  `relation_inbox.py → observatory-shell`;
- absence of the slow Maintenance owner from selected IDs;
- final Promotion inventory retaining every relation-capture test.

No test or coverage item is deleted; only the two new data examples that caused broad `ci-control` selection are
withdrawn. After the rollback commit, real-base Fast/Checkpoint dry-run must return to the bounded product window
before any new policy receipt or formal lease is created.

### 2026-08-31 scope revision 11 — Fast setup leaves no room for the 0.817s mapping deep check

After revision-10 rollback, real-base dry-run returns to Fast 20 / Checkpoint 30 under fingerprint `b7423560...`.
Checkpoint allows at predicted 14.991s. Fast still refuses at predicted 10.300s because router setup p95 is 9.320s
and `test_actual_paths_are_primary_broad_scope_refuses_and_overlap_fails_closed` alone is 0.817s; removing all other
tiny Fast tests would still leave the plan above 10 seconds.

Revision 11 may modify only `scripts/ci/change-mapping.json` to move that existing deep mapping/overlap check from
Fast to Checkpoint/Candidate/Promotion. Fast retains exact inventory-staleness and registry-mutation fail-closed
sentinels; Checkpoint retains all three plus the generic portfolio gate. No ID, assertion, budget, mapping, required
check or Promotion coverage changes. Expected new plan is Fast 19 below 10 seconds and Checkpoint 30; refusal stops
without a lease.

### 2026-08-31 revision-11 final Phase 0 routed evidence

Final product/mapping source `74afb9894aeee21c1131f3f8f3c70556563eba13`, base `2aa1c614...`, policy v6 and
fingerprint `4b4c56c5cef2998674712ef6bbb203e3defae7955b69f1561c93a05b97d6e06f` produced:

- Fast 19/19 PASS, 0.170343s test runtime, 9.038573s setup/build, zero reruns, evidence-eligible;
- Checkpoint 30/30 PASS, 7.119383s test runtime, 9.168959s setup/build, zero reruns, evidence-eligible.

The earlier revision-9 Fast PASS and Checkpoint failure remain historical; neither was reused. The direct Core focused
process has Unknown final status because its execution channel lost the exit code and was not rerun. Its exact owner
remains Promotion-only and will run in Final RC Promotion.

The next commit changes only author evidence records. It does not rewrite the product/mapping receipt SHA. Build the
Unified page from that clean docs SHA and obtain final desktop/mobile maintainer acceptance; Final RC registration
remains blocked until then. Final RC Candidate later validates the complete release-input SHA including these records.

### 2026-08-31 Phase 0 final page acceptance and Phase 1 dispatch

The maintainer explicitly accepted Unified page `http://127.0.0.1:8771/` generated from exact clean SHA
`a2d7737802be66714ff88064820685de6e231e95`. Browser evidence covered 1440×900 and 390×844: seven navigation
identities, no unavailable primary consumer, one Ask Docs button, one global stop, facts/rules help, two relation
inboxes, four pending proposals, lineage defer/reject only, three dependency gate cards, zero Team decision actions,
read-only Graph with no relation decisions, ledger/rollback controls, zero document horizontal overflow and empty
browser console. AI was disabled and server stderr was empty.

Phase 0 is complete. The task-description commit containing this paragraph is an append-only authority descendant of
the accepted page SHA; it is not misreported as a reviewed page. Final RC must perform its own final runtime/browser
gate on the release-input SHA.

Phase 1 may now register isolated Workstream `V0.3.0-final-rc`, branch `codex/v0-3-0-final-rc`, GPT-5.6 Sol medium,
primary `release-and-toolchain`, affected `documentation-system`, `test-coverage`, `project-structure`,
`authority-meta-model` and `multi-worktree-collaboration`, scope revision 1. Initial writes are limited to:

- `skills/project-orrery/release-manifest.json`;
- `scripts/package_release.py`;
- `.github/workflows/release.yml`;
- `packages/project-orrery-core/src/project_orrery_core/data/release-v0.3.0.json`;
- `docs/implementation/v0.3.0-onboarding.md` and `docs/implementation/v0.3.0-upgrade-rollback.md`;
- this Plan's matching Validation, affected subsystem State/DEVLOG/indexes;
- existing release/packaging tests and CI registry files only when dry-run proves the exact required change.

Before additional Skill assets, templates, launchers or package inventory are changed, the Final RC Agent must return
an exact self-contained archive inventory and request a dated scope amendment. Phase 1 may inspect/build locally but
may not push a ref, modify main, create a tag, create/upload assets or publish a GitHub Release. Those remain separate
Phase 3/4 maintainer authorizations.

### 2026-08-31 Phase 1 scope revision 2 — archive inventory and self-contained scaffold blockers

`V0.3.0-final-rc` was registered in an isolated linked worktree on branch `codex/v0-3-0-final-rc`, with code base and
scope-revision-1 task-description version both at
`88d80df2a19c15ac0b9de3f439e20edf8ff0d7e8`. The Sol-medium Agent acknowledged the source, registered its
Git-private scope and returned without product writes, tests, packaging or remote operations.

Its proposed deterministic archive inventory contains 162 entries under root `project-orrery/`; the sorted path-list
SHA-256 is `26d6570585b3507880f83c652000bdcc857e7bac3ea59866f06ad40abdb0bf5c`. The baseline is the tracked
`skills/project-orrery/**` tree with that prefix removed, `packages/component-versions.json`, all tracked
Core/CLI/Observatory package blobs, the five tracked Harness JSON Adapter blobs and root `LICENSE`, plus the exact new
release-contract and Unified-template entries listed below. This accepts the inventory as revision-2 implementation
input only; it is not a built archive, entry receipt, Candidate PASS or release fact. Any materially different entry
set, archive root or source class requires another committed amendment before writing it.

Read-only inventory found three blockers inside the accepted ADR-0021 design:

1. CLI 0.1.22 still pins Core 0.1.18 even though the release Candidate inventory declares Core 0.1.19. The candidate
   must use one exact compatible component set and may not hide the mismatch in packaging.
2. The new-project launcher will call the projected `scripts/docsite/serve_orrery.py`, which imports embedded
   Core/CLI/Observatory source. A clean offline scaffold must therefore receive the exact tracked runtime source it
   needs; it may not depend on the repository checkout, a developer `PYTHONPATH`, network install, wheel/PyPI release
   or an unrelated machine package. Existing author documents remain create-only/preserved, and `--upgrade-tools`
   may update only the declared managed runtime/launcher allowlist after backup.
3. Phase 1 requires human release notes but had no authority path. The canonical author document is
   `docs/implementation/v0.3.0-release-notes.md`.

Scope revision 2 authorizes only these product/document surfaces:

- release contract/build/workflow: `skills/project-orrery/release-manifest.json`, `scripts/package_release.py`,
  `.github/workflows/release.yml`, `packages/project-orrery-core/src/project_orrery_core/data/release-v0.3.0.json`
  and `packages/project-orrery-core/src/project_orrery_core/manifests.py`;
- component/scaffold projection: `packages/project-orrery-cli/pyproject.toml`,
  `packages/project-orrery-cli/src/project_orrery_cli/context.py`,
  `packages/project-orrery-cli/src/project_orrery_cli/scaffold.py`, and
  `packages/project-orrery-observatory/src/project_orrery_observatory/component.json`;
- exact new managed template entries:
  `skills/project-orrery/assets/project-template/Start Orrery.vbs`,
  `skills/project-orrery/assets/project-template/start-orrery.bat`, and under
  `skills/project-orrery/assets/project-template/scripts/docsite/` the exact files
  `build_authority_projection.py`, `build_personal_observatory.py`, `build_unified_observatory.py`,
  `build_workstream_relation_graph.py`, `serve_orrery_control.py`, `serve_orrery.py` and
  `serve_team_observatory.py`;
- author guidance: `docs/implementation/v0.3.0-release-notes.md`,
  `docs/implementation/v0.3.0-onboarding.md` and `docs/implementation/v0.3.0-upgrade-rollback.md`;
- existing release/scaffold/runtime owners only as needed:
  `tests/test_project_orrery.py`, `tests/test_cli_wheel_installation.py`,
  `tests/test_authority_release_candidate_gate.py`, `tests/test_authority_update_compatibility.py`,
  `tests/test_unified_observatory.py`, `tests/test_brand_contract.py`,
  `tests/fixtures/platform_neutral_phase0_baseline.json`,
  `tests/fixtures/brand/orrery-brand-contract-v1.json`, and—only if CI7 dry-run proves a generic routing gap—
  `scripts/ci/change-mapping.json`, `tests/fixtures/ci-validation/change-portfolios-v1.json` and
  `tests/test_ci_validation.py`;
- this Plan, matching Validation, affected subsystem State, PROGRESS, HANDOFF, DEVLOG and existing indexes.

The embedded package trees and Harness JSON files are builder inputs from exact committed Git objects, not permission
to edit every included blob. The builder must fail on untracked/dirty source, symlink, duplicate/case-collision,
absolute/parent path, missing/extra inventory or private/generated inputs; it must emit a deterministic entry receipt
and the single ZIP/checksum pair required by ADR-0021. DSH Store, `orrery` alias, scheduler, automatic deletion,
PyPI/wheels, independent Adapter releases and any new remote/default authority remain excluded.

Before the first resumed product write, the Agent must read this committed revision, acknowledge its exact SHA and
refresh `V0.3.0-final-rc` to Git-private scope revision 2. After implementation, CI7 dry-run/explain precedes any
formal test lease; child feature suites are not manually replayed. Scope revision 2 still authorizes no push, main
mutation, tag, asset upload or GitHub Release.

### 2026-08-31 scope revision 3 — central integration and single Candidate path

The unique integrator selected only the three release-input product commits from `codex/v0-3-0-final-rc` and applied
them on top of task-description version `17bb70ba861c8f1f4be18fa11863e3cac7fc5c87`; it did not merge the task's
stale global-entry documentation commit. Central commits are `e677c73`, `68ab9be` and `552378b`. A subsequent
`git diff --check` found one trailing blank line in the new VBS launcher, fixed in exact product baseline
`ef145180ff3a093b65c5b293148783155e77bacb`. The central worktree is clean.

The task branch records two byte-identical builds and one repository-external offline scaffold/validator/launcher
probe on its earlier exact `56f4aca4a4a9120a1bd292cf17d8669f86061457`. Those hashes remain branch-scoped
historical evidence: the central launcher byte and commit ancestry changed, so none may be reused as exact Candidate
evidence. Central must rebuild from the later frozen Candidate SHA.

CI7 dry-run/explain on the task branch eliminated unknown paths but conservatively refused Fast 75 (>20 and Unknown
timing) and Checkpoint 81 (Unknown timing) before issuing a lease or loading a test. The only bounded Focused request
also refused before test loading because the session had entered `validating`; it was not retried. This is a release-
wide selection, not permission to weaken Fast/Checkpoint budgets, split the same set into manual batches or replay
unaffected child suites.

Scope revision 3 authorizes the existing Sol-medium `V0.3.0-final-rc` task to:

1. incorporate the new central task-description commit into its existing branch without rewriting or deleting its
   prior commits, resolve documentation in favor of the central Plan/PROGRESS/HANDOFF plus the additive branch build
   record, and refresh Git-private scope revision 3 before the first merge-resolution write;
2. make no new product change; its release-input tree must equal central product baseline `ef145180...` for every
   non-authority path before validation;
3. run exactly one CI7 Candidate dry-run/explain against explicit base `17bb70b...` and task phase `candidate`;
4. only if that exact plan is allowed, issue one Candidate lease/run, then perform one two-root deterministic build
   comparison and one repository-external offline new-project scaffold/validate/Unified-import portfolio on the same
   frozen SHA;
5. if Candidate dry-run refuses, or any Candidate/build/runtime gate is non-green, stop and record the result without
   retry, human-override receipt, smaller substitute base, hand-written test list or additional product fix.

Authorized writes are merge/reconciliation of the already listed scope-revision-2 surfaces plus this Plan, matching
Validation, affected State, PROGRESS, HANDOFF, DEVLOG and indexes. No new code/test/fixture/mapping behavior is
authorized. A needed product or routing correction requires another committed amendment. Scope revision 3 still
forbids push, main mutation, tag, asset upload and GitHub Release.

### 2026-08-31 scope revision 4 — Candidate dry-run semantics clarification

The scope-revision-3 task completed one Candidate dry-run on clean merge `0f82d565...`, selected 81 tests and then
stopped because it interpreted `successful=false`, `evidence_eligible=false` and the embedded reuse refusal as a
Candidate-plan refusal. Read-only inspection of the versioned router proves that interpretation wrong:

- `_dry_receipt()` always emits `outcome=dry-run`, `successful=false` and `evidence_eligible=false` because a preview
  cannot itself be test evidence;
- the command returned exit 0, `runner_errors=[]`, acceptance `decision=shadow-allow` and timing
  `decision=allow` with no timing refusal reason;
- the plan's reuse block describes whether a prior receipt may be reused. Candidate/high-risk reuse remains refused by
  contract, but this command did not request `--reuse` and the refusal does not block a fresh Candidate run.

Therefore the existing dry-run is the single allowed preview required by scope revision 3; do not rerun it. Scope
revision 4 authorizes the same Sol-medium task to appenditively correct its branch State/Validation/DEVLOG
classification, refresh Git-private scope revision 4, freeze the resulting clean exact SHA and issue exactly one fresh
Candidate lease/run for the already selected 81 tests. No router, mapping, test, product or budget change is
authorized. If Candidate is green, continue the already-authorized two-root deterministic build and external offline
new-project portfolio on that same SHA. A non-green Candidate/build/runtime result stops without retry or substitute
evidence. Push, main, tag, asset upload and GitHub Release remain forbidden at this scope.

### 2026-08-31 scope revision 5 — stale release portfolio expectation

The unique formal Candidate on exact `ac44630c84afc84d887a63bd43541e41ecc0a38c` executed all 81 selected tests
once in 12.061400s. Eighty passed; the only failure was
`test_generic_router_selects_docs_authority_and_collaboration_portfolios`, whose hardcoded ordered fixture-ID list
still begins with `docs-only` and omits the already-versioned `release-candidate-packaging` object. The production
registry, generic portfolio fixture and selection plan all contain the new ID as intended. The receipt is non-green,
not evidence-eligible and will never be retried on the same fingerprint.

Scope revision 5 authorizes only `tests/test_ci_validation.py` to add exact `release-candidate-packaging` at the start
of that existing expected ID list, plus the usual Plan/Validation/State/PROGRESS/HANDOFF/DEVLOG/index reconciliation.
No assertion, portfolio object, mapping, router, product, budget or selected-test inventory may otherwise change.
After the one-line correction and a clean commit, run one Candidate dry-run on the new fingerprint; only if allowed,
run one fresh Candidate. Green then resumes the scope-revision-4 same-SHA build/offline gates. Any other non-green
result stops without retry. Push/main/tag/assets/Release remain forbidden.

Scope revision 5 completed on exact `ba2305555e30ee34c88bd7622d13aa8d02930fb8`: the new-fingerprint Candidate,
two-root deterministic build and external offline new-project portfolio are green. These results close only the
bounded local gates authorized above; Phase 2's remaining migration/runtime matrix and all Promotion/publication
authority remain open.

### 2026-08-31 scope revision 6 — final runtime, Promotion, main and tag authorization

The maintainer instructed the coordinator to continue without stopping until the final publication action is next.
This is action-time authorization for all intermediate gates below, while explicitly withholding GitHub Release
creation/upload. Exact frozen Candidate is `ba2305555e30ee34c88bd7622d13aa8d02930fb8`; later evidence-only authority
commits are not substituted for it.

Before any remote mutation, the existing Sol-medium Final RC task may run the remaining Phase 2 runtime matrix from
the exact Candidate archive only:

- bounded real Codex install/discovery/explicit-and-implicit invocation, Unified start/stop/restart, 0.2 update,
  migration/rollback, dependency failure, uninstall/reinstall and author-file preservation;
- Harness JSON Windows request/failure/remove with `launch=false`, no Provider secret exposure and no source-checkout
  dependency; Ubuntu execution remains owned by exact-SHA Promotion;
- any temporary user-scope installation must have an exact recoverable backup and restore the pre-run state;
  credentials are neither copied nor inspected. A safe isolation failure is non-green, not permission to weaken the
  runtime claim.

No code/test/manifest/archive change is authorized. A runtime failure stops for a new SHA or explicit scope decision;
no unchanged retry or partial-runtime substitution is allowed. If the runtime matrix is green, the unique integrator
is authorized to:

1. push only exact Candidate `ba230555...` to `refs/heads/promotion/v0.3.0-rc`, verify remote equality and allow the
   existing Promotion workflow to run once;
2. require both `smoke-test (windows-latest)` and `smoke-test (ubuntu-latest)` plus exact inventory/package receipts
   on that SHA; any non-green run stops without force-push or same-SHA replay;
3. after both required checks pass, fast-forward protected `main` to the same SHA and verify remote equality;
4. create and push one annotated `v0.3.0` tag targeting the same SHA, wait for its read-only verification workflow,
   rebuild the ZIP/checksum/entry receipt from the immutable tag and compare identities;
5. stop before `gh release create`, Release asset upload or any equivalent GitHub Release mutation, and present the
   complete evidence/known-limitations package to the maintainer.

The existing `v0.2.0` tag/assets remain immutable. No force update, tag move/reuse, branch deletion, credential
change, Provider call, PyPI/wheel publication or independent Adapter release is authorized.

### 2026-08-31 scope revision 7 — pre-runtime PowerShell variable correction

The first scope-revision-6 runtime orchestration stopped before its first installation/discovery/Codex subprocess
because PowerShell treats local `$home` as the read-only built-in `$HOME`. The external root contains only the
extracted exact archive; no user-scope install, Provider call, credential/config read or user-state mutation occurred.
The failed command is preserved and is not rerun unchanged.

Scope revision 7 authorizes only a new external orchestration command that replaces the local `$home` identifier with
a task-specific non-system variable such as `$runtimeHome`. It may not assign or repurpose `$HOME`, `$home` or
`$CODEX_HOME`. No repository file, Candidate byte, test, manifest, archive or runtime expectation may change. After
refreshing Git-private scope revision 7, execute the complete scope-revision-6 Codex/Harness matrix once from the
existing exact archive. A new non-green result stops without retry; green resumes the already-authorized Promotion
sequence. GitHub Release remains withheld.

### 2026-08-31 scope revision 8 — extracted release-root runtime resolution

The coordinator completed the corrected external runtime orchestration through the first real product blocker.
Exact archive identity remained 162 entries and ZIP SHA-256 `7a0cf3dd...`. On Codex CLI 0.151.0-alpha.7.2 with
GPT-5.6 Sol medium, isolated repo discovery exposed exactly one candidate Skill; explicit invocation correctly failed
closed on `--require-integrated` for a migration-pending scaffold, while implicit invocation selected the Skill and
ordinary validation returned 0. Unified twice completed start→HTTP 200→stop/restart; v0.2 tool upgrade backed up all
eight replaced tools and preserved the custom author-file hash; migration/apply/receipt-bound restore, dependency
failure, and recoverable Skill discovery 1→0→1 all behaved as designed without changing the real user Skill.

The bounded Harness invalid-argv request returned exit 2 and leaked no environment sentinel. The normal final-bundle
validate request returned `cli_protocol_error` because its CLI subprocess crashed before JSON: from extracted root
`project-orrery/packages/...`, `observatory_asset_root()` only searches package-local wheel assets or managed tools at
the repository root. The final archive stores those tools under `assets/project-template/`; consequently direct
embedded-source `repository_context()` cannot bind the Observatory asset root or release runtime root. This is a real
self-contained runtime defect; Promotion remains blocked.

Scope revision 8 authorizes only:

- `packages/project-orrery-observatory/src/project_orrery_observatory/inventory.py`: recognize an extracted release
  root only when its `release-manifest.json`, `packages/component-versions.json` and complete
  `assets/project-template/` managed inventory all agree; preserve existing wheel and source-checkout resolution;
- `packages/project-orrery-cli/src/project_orrery_cli/context.py`: when the resolved Observatory assets are the
  extracted `assets/project-template/`, bind `runtime_root` to that exact release root so managed runtime projection
  remains available;
- `tests/test_project_orrery.py`: extend an existing release-package owner to invoke the bundled Harness JSON validate
  request directly from an extracted archive, proving JSON exit 0 without checkout/wheel/PyPI or ambient package
  dependency; keep invalid-argv failure closure and source/wheel behavior unchanged;
- matching Plan/Validation/State/PROGRESS/HANDOFF/DEVLOG/index records and generic CI mapping only if dry-run finds an
  unmapped exact path.

No manifest/archive inventory/version/default/authority/UI/Adapter capability or test budget change is authorized.
After the fix, a new exact SHA requires one Candidate dry-run/run, two-root deterministic rebuild, external offline
portfolio and the full corrected final runtime matrix once. Any non-green result stops without retry. The previous
`ba230555...` evidence remains immutable history and cannot be promoted. Remote operations and GitHub Release remain
blocked until the new exact SHA is green.

Scope revision 8 completed on exact `e120aaae27f9f4e1b74c72c053dd2f6e72eed88b`. Candidate 36/36, two-root
package identity, offline scaffold, direct final-bundle Harness, real Codex explicit/implicit invocation, Unified
restart, v0.2 upgrade/migrate/restore, dependency failure and recoverable Skill lifecycle are green. The frozen SHA
is now eligible for the already-authorized `promotion/v0.3.0-rc` push; no later evidence-only commit may replace it.

### 2026-08-31 scope revision 9 — machine-only Promotion inventory output

Exact `e120aaa...` was pushed to `promotion/v0.3.0-rc` and remote equality was verified. Promotion run
`33449930707` failed in preflight before any lane or repository gate ran: `test_inventory.py --lane-list` imported the
test inventory, whose docsite modules printed `building reader…` and related lines before the JSON array. Workflow
command substitution wrote those lines to `$GITHUB_OUTPUT`, which rejected the multiline value as invalid format.
Both named smoke jobs then failed closed because no lane artifacts existed. The run is immutable and is not replayed.

One local diagnostic invocation omitted `DOCSITE_AI_ENABLED=0` and reached the configured `openai-compat` briefing/
roadmap/milestone path. It is not evidence and may have incurred Provider cost; all subsequent inventory commands must
disable AI before imports.

Scope revision 9 authorizes the unique integrator to modify only:

- `scripts/ci/test_inventory.py`: set the inventory process to AI-disabled before test discovery; for `--lane-list`
  and `--shard-list`, redirect incidental discovery stdout away from machine stdout so stdout is exactly one compact
  JSON array line; retain diagnostics on stderr and preserve normal `--output`/human summary behavior;
- `tests/test_ci_validation.py`: extend an existing CI control owner to prove list modes are parseable single-line JSON
  despite a synthetic incidental stdout emitter, while inventory IDs/order remain unchanged;
- matching Plan/Validation/State/PROGRESS/HANDOFF/DEVLOG/index records.

No workflow graph, test inventory, lane assignment, budget, product, release archive or required-check name may
change. The fix creates a new exact SHA: run one CI7 Candidate dry-run/run for the changed CI surface, rebuild twice
and prove release ZIP/checksum entries remain equivalent except source-bound receipt fields, then rerun the required
exact-SHA final runtime and update the existing promotion ref by fast-forward only. A new Promotion run is allowed
once; any non-green result stops without same-SHA replay. GitHub Release remains withheld.

Scope revision 9 completed on exact `4556db3a8b75e9b92e3e2cfe9d229273b203ab33`. The first fix SHA
`14f771f...` Candidate was 41/42 non-green because importing the inventory CLI in-process exposed a pre-existing bare
`_common` module-name collision; it was not retried. The final regression uses a subprocess black-box and object-bound
mock targets, preserving all 421 unittest IDs. Candidate 42/42, two-root package identity and the complete final
runtime matrix are green. The promotion ref may now fast-forward from `e120aaa...` to `4556db3...` exactly once.

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
