# U2.1 Unified Observatory UX Acceptance Fixes Validation

Date: 2026-08-29

Status: PASS — implementation, local CI6 Fast/Checkpoint and real-browser acceptance complete

## Scope and baseline

- Branch: `codex/u2-1-unified-observatory-ux-acceptance-fixes`.
- Exact task base: `codex/u1-u2-integration-baseline@4e2b5436d1744d8034011a34986df1eb6a04c9a4`.
- Git-private Workstream: `U2.1-unified-observatory-ux-acceptance-fixes`, registered before authored writes and
  refreshed to the exact changed/expected paths before formal CI6 evidence.
- Governing authority: accepted [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md)
  and Approved [Unified Observatory Design](../design/unified-observatory-architecture-and-shell.md).
- Explicitly unchanged: root PROGRESS/HANDOFF, public v0.2.0, default launcher, Skill template, managed tools,
  installer, release manifest, `start-docsite.bat`, main, tag and Release.

## Product evidence

The real Unified Candidate now has one Chinese application navigation group. The injected shell removes only the
legacy app-page links for Overview/Personal/Team/Graph/Maintenance and retains the author document tree. A centralized
display vocabulary covers the shell and the Personal/Team/Graph/Maintenance primary views; protocol values, branch,
schema and machine identifiers are kept under `技术详情`. No incomplete language switch is exposed.

Maintenance writes current runs to `last-run-v2.json` and treats an incompatible, byte-preserved `last-run.json` as a
historical warning. That warning does not fail current refresh and never changes current eligibility. The page always
shows Quick Remove and the safe count; zero eligible items have an explicit empty state, while an eligible fixture row
alone receives fresh preflight and action-specific confirmation. No real repository removal was executed.

The Workstream consumer accepts only complete, read-only, validation-valid and content-hash-bound native or
legacy/archive evidence. Native relation-root presence remains provenance rather than a display gate. Empty evidence
is still Unavailable; no synthetic node, relation root or archive execution authority is created. The self-host page
shows W7.1 archive/session evidence including referenced nodes/edges and a closed axis, and the dynamic endpoint serves
the startup-bound projection without request-time graph recomputation.

Team discovery is labelled `在局域网查找团队成员` and explains explicit click, project-fingerprint filtering,
untrusted candidates, target-Host confirmation and the no-auto-join/execute/source-upload boundary. Loopback/self is
labelled as a local test/local Host. The global `关闭 Orrery 服务` control is present on every app page; confirmation
calls the existing local stop endpoint, shows disconnection, and releases the listener, ready marker and owned helper.
Closing a tab does not imply service shutdown.

## Regression and safety evidence

Focused suites cover single navigation, Chinese primary copy, historical Maintenance downgrade/current refresh,
zero/non-zero Quick Remove discoverability, legacy/archive graph without a native root, empty graph refusal, cached
graph delivery, local-host discovery copy and full service reclamation. The tests use fixtures, memory and loopback;
they do not read a Provider key, access the external network, join a real Team or remove a real worktree.

Formal CI6 commands and final counts are recorded after the receipts complete:

```text
python -X utf8 scripts/ci/validate_change.py --stage fast --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4 --dry-run --explain
PASS — 38 mapped tests, no unknown path; dry-run is not evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage fast --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4
PASS — 38/38, evidence-eligible, within the 15-second budget

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4 --dry-run --explain
PASS — 44 mapped tests, no unknown path; dry-run is not evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4
PASS — 44/44, evidence-eligible, within the 90-second budget
```

The five focused suites first passed 47/47. After the four new assertions were folded into their owning existing test
IDs, the exact merged methods passed 5/5 and the full Unified suite passed 11/11. The registry inventory therefore
remains the inherited 415 IDs; U2.1 adds coverage without changing the versioned CI inventory or tier budgets.

The first Fast dry-run refused the original broad Session expectations `tests/` and
`packages/project-orrery-core/`. The same registered Workstream was refreshed to exact files/supported globs; the
next dry-run passed with no unknown path. This is intended CI6 failure closure, not product evidence.

The first formal Fast attempt ran 62 selected product/contract tests, but its embedded CI self-regression correctly
refused the receipt because four separately registered IDs expanded the historical W6.1 Checkpoint selector from 23
to 27 against its `<24` bound. The assertions were mechanically folded into the existing owning IDs and the registry
was restored byte-for-byte; no tier budget, selector bound or product behavior was changed.

An intermediate 44-test Checkpoint reached 94.144717 seconds because the Unified runtime class repeated the real
15-worktree relation scan already covered by the graph suite and browser acceptance. Its test-only setup now injects
the fixed synthetic relation provider through the same production projection path. The product startup/provider path
is unchanged; the following Checkpoint passed 44/44 in 63.303518 seconds. This preserves both the dynamic Unified and
real Git maintenance gates inside the existing budget.

## Real browser acceptance

Real in-app Chromium exercised the supervised self-host Candidate at 1280x800 and 390x844. Overview, Personal, Team,
Workstreams and Maintenance were each selected through the unified navigation at both viewports. Every page kept
document-level horizontal overflow at zero; mobile selection closed the drawer; console warnings/errors remained
zero. Maintenance refreshed the real local read-only status to current and displayed 15 registered worktrees, zero
safe removals and the principal protection reasons. No removal confirmation was accepted.

The global stop button was also exercised against the live server. The runtime logged the POST stop request and
`runtime stopped; helper ownership released`; the listener and ready marker were absent afterward. A new server was
started only to capture the final corrected Chinese shell and then stopped explicitly. This exercise also exposed a
Windows stale-process check that treated an exited process with a retained handle as live; `_pid_alive` now checks
`GetExitCodeProcess`, the stale identity recovery regression passes, and the final listener/marker/helper checks are
all empty.

Screenshots are local acceptance artifacts outside Git:

- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/u2-1/desktop-{overview,personal,team,workstreams,maintenance}.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04fb7-0d1c-7c62-8ff3-c98cf4316b83/u2-1/mobile-{overview,personal,team,workstreams,maintenance}.png`

## Remaining boundary and integration order

- This remains a local root-only/default-off Candidate; complete English mode and a public/default transition are not
  implemented.
- Team stays opt-in, metadata-only and request-only; real dual-host, auto leader, cloud relay and remote execution are
  unsupported. Graph stays read-only and archives have no execution authority. Quick Remove remains locally confirmed;
  automatic deletion and the OS scheduler remain unsupported.
- Static output has no control surface; `start-docsite.bat` remains the whole-shell rollback. Authority/AI selection and
  public Authority Model 1 release readiness do not change.
- The exact clean Candidate must next be pushed to a non-main ref, pass GitHub
  `smoke-test (windows-latest)` and `smoke-test (ubuntu-latest)`, then be integrated from a clean integration worktree.
  Only the unique integrator synchronizes root PROGRESS/HANDOFF and considers main promotion. This Workstream does not
  push, publish or run full Promotion as its development loop.
