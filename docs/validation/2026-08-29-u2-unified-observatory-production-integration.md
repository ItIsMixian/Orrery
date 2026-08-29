# U2 Unified Observatory Production Integration Validation

Date: 2026-08-29

Status: PASS — root-only Windows Worktree Candidate; no hosted Promotion or public/default transition

## Scope and exact baseline

- Branch: `codex/u2-unified-observatory-production-integration`.
- Base: `codex/u1-u2-integration-baseline@12f3bf53dfc768067a5a4048de63437313ed633a`.
- Git-private session: `U2-unified-observatory-production-integration`, registered before authored writes with the
  exact task base and honest parent-unverified Candidate lineage.
- Governing authority: Accepted [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md) and
  Approved [Unified Observatory Design](../design/unified-observatory-architecture-and-shell.md).
- Explicitly unchanged: root PROGRESS/HANDOFF, public v0.2.0, Skill template, managed-tool inventory, installer,
  release manifest, `start-docsite.bat`, tag, Release and main.

## Production Candidate evidence

The implementation reuses the real generated docsite HTML/CSS/JS and server-side reader/search/AI objects. It injects
a compact navigation group and overview into the existing visual shell instead of replacing the document product or
copying the U1 synthetic prototype. The dynamic front door exposes exactly one public loopback listener and URL;
Broker and Team Coordinator ownership stays hidden and supervised.

The versioned `unified-observatory-consumer-registration-v1` registry rejects duplicate routes, navigation identities,
consumer IDs, unknown privilege declarations and privilege escalation. Optional consumer failure is quarantined;
required consumer failure refuses the shell. Capability discovery contains status/reason/contract/route metadata but
not credentials, tokens or private paths.

Common API security rejects non-loopback Host, cross-origin or missing-Origin state changes, foreign cookies, stale
settings tokens, oversized/non-JSON bodies and unknown API routes. Team enablement remains project-level opt-in and
does not execute a request. Authority reads the A3 managed-consumer inspect plan and leaves legacy active because the
production switch is false. AI unavailability remains an AI/provider condition. Maintenance actions delegate to the
W6.1 provider, whose Quick Remove path still requires action-specific local confirmation and fresh target preflight.
The provider UI keeps its legacy Team suffixes by default, while the Unified registration supplies ADR-0016's
`/refresh` and `/remove-worktree` action paths. Unified actions skip the legacy Team page rebuild and poll the provider
status directly; this keeps background refresh non-blocking without moving cache or eligibility policy into the shell.

Static composition is a read-only file artifact: no Unified stop request, dynamic Team fetch or control cookie is
emitted. Dynamic runtime identity/log files live below the Git-private worktree area and are removed or retained as
appropriate: ready identity is removed at shutdown; the local aggregate log remains diagnostic evidence. A stale PID
identity is recovered; a live duplicate fails closed.

## Focused and CI6 evidence

```text
python -X utf8 -m unittest -v tests.test_unified_observatory
PASS — 11/11; final adjacent rerun below supersedes its timing

python -X utf8 -m unittest -v tests.test_unified_observatory tests.test_personal_observatory.PersonalObservatoryTests.test_workspace_maintenance_page_is_static_read_only_or_explicitly_host_local
PASS — 12/12 in 20.407s after final Maintenance route/non-blocking adapter correction

python -X utf8 scripts/ci/validate_ci.py --all
PASS — CI contract, inventory and data-only routing registry

python -X utf8 scripts/ci/validate_change.py --stage fast --base 12f3bf53dfc768067a5a4048de63437313ed633a --dry-run --explain
PASS as dry-run — mapped scope only, no unknown paths; dry-run is intentionally not evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage fast --base 12f3bf53dfc768067a5a4048de63437313ed633a
PASS — 49/49 selected tests; evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 12f3bf53dfc768067a5a4048de63437313ed633a --dry-run --explain
PASS as dry-run — 54 mapped tests, no unknown paths; dry-run intentionally not evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 12f3bf53dfc768067a5a4048de63437313ed633a
PASS — 54/54 selected tests; evidence-eligible; 90s budget not exceeded
```

An earlier Fast attempt correctly failed a CI self-regression because all 11 new U2 tests entered the historical W6.1
Checkpoint portfolio and exceeded its `<24` selector bound. Four heavier composition/quarantine/lifecycle tests were
moved to Candidate/Promotion; the 23-test W6.1 checkpoint portfolio then passed its selector regression. This was a
mapping-budget correction, not a product assertion change. A prior attempt also refused evidence after writing its
receipt inside the worktree; those temporary files were deleted and the successful receipt is Git-private.

Final diff review also found two integration-only Maintenance defects before commit: the reused UI still called the
legacy `/scan`／`/quick-remove` suffixes, then provider action completion rebuilt the old Team page and blocked the
background response. The final adapter makes action suffix/reload behavior explicit, preserves the legacy defaults,
uses ADR-0016 routes in Unified, and tells `TeamUIState.perform` not to rebuild the unused legacy page. Focused tests
and real browser action were rerun after both corrections.

## Static and live runtime evidence

```text
python -X utf8 scripts/docsite/build_unified_observatory.py --enable --out <visualization-root>/u2-static-fast/index.html
PASS — isolated static artifact, eight navigation identities, no Unified dynamic control/Team fetch

python -X utf8 scripts/docsite/serve_orrery.py --console --no-browser --port 0
PASS — one URL at http://127.0.0.1:<ephemeral>/#overview; health reports single_visible_url=true
```

Live API checks returned root 200, eight consumer registrations, Maintenance ready, Authority legacy active with
production switch false, and Team status without enabling it. Missing Origin POST returned 403, wrong Host 421 and an
unknown API route 404. The normal stop endpoint returned 202 and exited zero in the lifecycle test. The browser run was
then interrupted through its explicit console path; the supervisor logged ownership release. In both cases the ready
marker, public listener and owned Python helper processes were absent afterward.

## Real browser acceptance

Real in-app Chromium exercised the real generated/supervised Candidate, not the U1 prototype:

- **1280x720 desktop:** overview used the existing dark docsite shell and author navigation. Search for
  `Unified Observatory` returned ADR-0016, the Approved Design and U1 Validation/Plan. Maintenance opened as a usable
  dynamic consumer. Workstream Graph preserved `Unavailable / Unknown` because the relation store was absent. With
  the real legacy provider initialization unavailable, Ask Docs registration and Overview both reported
  `unavailable · AI Provider is not safely enabled for this runtime` while Docs/Search stayed available.
- **Dynamic Maintenance action:** the real `后台增量扫描` button was visible/enabled, called
  `/api/v1/maintenance/refresh`, polled `/status`, re-enabled without a docsite rebuild and displayed the provider's
  current `failed` status honestly; the browser had no console error. No Quick Remove confirmation was accepted and no
  worktree/branch/commit was removed.
- **390x844 mobile:** the navigation toggle was visible and enabled; opening it produced a 330px drawer, selecting
  Docs closed the drawer and navigated to `#dashboard`.
- **Overflow:** desktop `scrollWidth=1280` at a 1280px viewport; mobile open drawer `scrollWidth=390` at 390px and
  closed Docs view `scrollWidth=375 < 390`.
- **Console:** error log count remained zero after search, dynamic consumer, Unavailable and responsive navigation
  interactions.
- **Shutdown:** after browser acceptance, port 54699 had no listener, the ready marker was absent and no
  `serve_orrery`／Team/Broker Python helper remained.

Screenshots:

- `C:/Users/1/.codex/visualizations/2026/08/29/01a04eb5-3000-71c3-b026-d31285953d07/u2-browser/desktop-overview.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04eb5-3000-71c3-b026-d31285953d07/u2-browser/mobile-nav-390.png`

## Remaining boundary

- This is a root-only/default-off Candidate. It does not make Unified Observatory the public/default experience.
- Full local Candidate and hosted exact-SHA Windows/Ubuntu Promotion were not run in this Workstream.
- Real dual-machine Team, automatic leader selection, cloud relay, remote execution, automatic worktree removal and OS
  scheduler remain unsupported.
- Public template, managed-tool inventory, installer, release manifest, SemVer/tag/Release and main promotion require a
  separate authorized transition after maintainer experience and integration.
