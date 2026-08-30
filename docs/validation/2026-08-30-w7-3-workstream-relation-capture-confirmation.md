# W7.3 Workstream Relation Capture & Confirmation Validation

Date: 2026-08-30

Status: PASS — Worktree Candidate implementation and local acceptance; exact-SHA Promotion remains for central integration

Authority sources:

- [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)
- [Approved Design](../design/workstream-relation-capture-and-confirmation.md)
- [W7.3 Plan and 2026-08-30 Scope Amendment](../implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)

## Fact scope and authority acknowledgment

- Candidate branch/worktree fact scope only; not Canonical, released, public or default-enabled.
- Exact code base: `codex/u1-u2-integration-baseline@3fc7e7aacedafa8fbd20f9f79ddb8cf5784a0ef3`.
- Exact authority commit: `6315415075fb78b61d9a5bb835725bced0bc9ce1`; its parent is the exact code base.
- The eight requested authority blobs were read and verified before resumed product writes; Git-private session scope
  revision 3 binds their exact blob OIDs and expected validation surfaces.
- This implementation record is separate from the docs-only
  [ADR-0017 decision contract](2026-08-29-w7-3-relation-capture-decision-contract.md).

## Expected evidence

- exact base and authority amendment commit acknowledgment;
- versioned proposal/confirmation/role/series contracts and compatibility;
- automatic exact-base lineage plus human-confirmed gate/absorbs paths;
- task-owner/integrator/CAS/spoof/stale/legacy/privacy negative matrix;
- A3→A4 and CI6→CI7 repair proposals without effective-history backfill;
- distinct task-series, status taxonomy, comparison suggestions and true-conflict projection;
- Personal/Team/inbox/Graph desktop/mobile browser acceptance;
- Fast/Checkpoint, repository/release/private-artifact/diff evidence.

## Command ledger

| Surface | Command/evidence | Result |
|---|---|---|
| Core/capture/schema | `python -X utf8 -m pytest tests/test_workstream_relation_capture.py tests/test_workstream_relation_graph_observatory.py tests/test_harness_json_adapter.py tests/test_unified_observatory.py -q` | PASS — 41/41, 256.04s |
| CLI/Harness | focused relation CLI test plus Harness JSON suggest/inspect/refusal matrix in the 41-test run | PASS |
| Observatory/Graph | `pytest tests/test_workstream_relation_graph_observatory.py -q` and bounded Unified fixture | PASS — final Graph 8/8; Unified 11/11 in 7.04s |
| Self-host | Core capture/provider projection for A/CI/U and new `W7.3-integration-acceptance` | PASS — details below |
| Browser | Browser skill at 1440×900 and 390×844 for Personal, Team and Graph | PASS — details below |
| CI6 | dry-run/explain, Fast and Checkpoint | PASS — Fast 90/90; Checkpoint 96/96 |
| Repository/release | repository gates, v0.2.0/Codex adapter dry builds and archive exclusion inspection | PASS |
| Hygiene | `git diff --check`; final clean Candidate verified after evidence commit | PASS |

## Results

### Contract, authority and compatibility

- Core 0.1.18, CLI 0.1.22, Observatory 0.1.17 and Harness JSON 0.1.2 are unreleased source versions. Codex,
  Claude Code and DeepSeek adapter versions remain 0.1.1; v0.2.0 manifest/tag/checksum bytes were not changed.
- `workstream-relation-capture-v2` freezes append-only proposal/event/confirmation/role/series records, revision/CAS,
  event hashes and bounded regular-file/path/count/size/symlink rules. Positive and negative fixtures cover Personal,
  Team, cycle, duplicate, stale, no-integrator, multi-integrator, spoof, remote request, legacy v1 and broken evidence.
- Registration/rebind only auto-captures `derived_from` after exact same-project OID and local ancestry verification.
  Drift/Unknown produces an explainable proposal/finding; no branch/title prefix becomes evidence.
- `depends_on` consumes explicit implementation/validation/integration/release gates. Only task owner may decide the
  first two and a human integrator the last two; `absorbs` is integrator-only and exposes closure, Validation, scope
  and unfinished responsibility. Proposed/deferred/Unknown and stale confirmation do not block lifecycle eligibility.
- CLI exposes bounded JSON `suggest/inspect/accept/change-gate/defer/reject`; Harness exposes only `suggest/inspect`.
  Neither path executes arbitrary shell, path or URL input, and central/remote/session/Agent callers cannot decide.

### Self-host facts

- Append-only series records explicitly group A3/A4 as Authority A, CI6/CI7 as CI and U1/U2/U2.2 as Unified U.
  A4→A3 and CI7→CI6 remain `integration` proposals. They are not effective history and did not come from name
  inference.
- A real linked worktree `W7.3-integration-acceptance` was created from exact implementation commit
  `84e1c0a1ac5fa306f834568c389651f69135af2b`. Its exact lineage automatically wrote native
  `derived_from(W7.3-integration-acceptance, W7.3-workstream-relation-capture-confirmation)`; a genuine CI6
  integration requirement remains proposal `w73-integration-requires-ci6`, not an effective dependency.
- Final read-only self-host projection is `ready`, 27 nodes／13 edges. The Integration workstream has one active
  mechanical `derived_from` and one proposed `depends_on(required_for=integration)`. Capture has 3 pending proposals,
  0 confirmed capture relations and 0 stale confirmations. Graph has 15 comparison suggestions and 0 confirmed
  conflicts; the two sets are disjoint. Projection reports `writes_performed=false` and `network_performed=false`.

### Status, comparison and conflict projection

- Projection schema 2 preserves raw axes while mapping cards to the frozen Chinese taxonomy: 正在进行、等待人工确认、
  状态待刷新／证据过期、历史任务、缺少任务记录、未登记、关系证据不足. “等待人工确认” is not a fallback.
- Task series use structured lanes/titles distinct from relation edges. Core v1 `compare_pairs` remains conservative,
  but Observatory consumes them as amber `comparison_suggestions`; red conflict facts require explicit
  location/impact/source. With no such fact the lens says “当前没有已确认的任务冲突”.

### Browser acceptance

- Browser skill used a separate local service at `127.0.0.1:63373`; it was stopped after acceptance. The central
  `127.0.0.1:63203` service was never stopped, reused or modified.
- At 1440×900 and 390×844, Personal showed the relation inbox and locally authorized actions; Team showed
  request-only with zero decision controls. Graph showed Authority/CI/Unified series, proposed gate edges, a separate
  comparison queue and an empty red conflict lens, with no confirm/apply/undo controls on the canvas.
- Both sizes had zero horizontal page overflow, keyboard/ARIA checks passed, mobile used the same-fact ledger, and
  console warning/error arrays were empty. No real remote/team/delete action ran.

### CI6 and repository gates

- Formal Fast: final 90/90 PASS in 10.488559s. Two immediately preceding post-self-host reruns hit the fixed 15s
  budget under local timing variance and remain failed evidence; the successful rerun changed no source or scope.
- The first two Checkpoint attempts reached the fixed 90s limit while the existing real-Git Workspace Maintenance
  fixture was still running; neither is claimed as PASS. Unified HTTP tests were then isolated from real self-host
  enumeration with a bounded synthetic relation fixture (production code unchanged). Formal Checkpoint rerun passed
  96/96 in 84.808322s, and the final current-diff rerun passed 96/96 in 78.812261s; the unchanged Maintenance test
  remained the dominant cost.
- `validate_ci.py --all` and repository gates passed; the latter reported 729 repository paths, 394 Markdown files,
  1054 local links and no forbidden runtime/generated artifact. Isolated `package_release.py` and
  `package_codex_adapter.py` dry builds succeeded; archive listings contain no Git-private capture/session state,
  generated site, `.port`, credentials or API configuration. The release listing's sole broad-pattern match was the
  intentional project-template `.gitignore` file, not a `.git` directory or private state. `git diff --check` passed.

### Remaining boundary and integration order

- This is not main, public, released or default-enabled. No full Promotion, push, tag, manifest rewrite, real
  dual-machine confirmation, cloud relay, scheduler, remote execution or historical effective dependency backfill
  was performed.
- Central integration must first land exact authority commit `6315415075fb78b61d9a5bb835725bced0bc9ce1`, then this
  W7.3 Candidate, reconcile only CI7's central test mapping, run Candidate/exact-SHA Windows+Ubuntu Promotion, and
  only then consider main. Root PROGRESS/HANDOFF remain central-integrator-owned.
