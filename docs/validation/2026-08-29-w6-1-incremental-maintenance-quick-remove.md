# W6.1 Incremental Maintenance Cache + Quick Remove Validation

Date: 2026-08-29
Branch: `codex/w6-1-incremental-maintenance-quick-remove`
Base: `d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`
Result: local Candidate PASS with one advisory performance gap and deferred shared-document projection

## Scope and authority boundary

- Cache and all maintenance evidence live below `$GIT_COMMON_DIR/orrery/maintenance/`; no cache, authorization,
  archive or receipt is tracked or packaged.
- The published, hash-locked `maintenance-v1.json` remains byte-for-byte unchanged. W6.1 introduces
  `maintenance-v2.json`; incompatible v1 queue／receipt state is reported stale-Unknown instead of blocking the page.
- Quick Remove accepts only a registered `workspace-*` ID, a `maintenance-item-*` ID or the existing local
  `maintenance-authorization-*` execution path. It exposes only `remove-worktree`; branch, commit and remote branch
  deletion remain false.
- Personal and the standalone control entry perform zero network I/O. The new entry binds only `127.0.0.1`, requires
  the root-only control cookie and exact Host／Origin／body shapes, and imports no Team authority.
- Phase 3 automatic deletion and Phase 4 scheduler remain unsupported and disabled.

## Cache and fail-closed evidence

`tests.test_workspace_maintenance.WorkspaceMaintenanceTests.test_scan_is_bounded_zero_network_debounced_single_flight_and_times_out`
proved:

- a cache-hit refresh reports three hits and `target_provider_scans == 0`;
- one dirty or clean reversion refreshes exactly one target;
- added and removed worktrees update only their entry／registry projection;
- integration movement performs one integration-sensitive provider read and two integration-only updates;
- session, policy, maintenance schema and tool version drift invalidate the required entries;
- corrupt and unknown-version current entries retain last-known evidence as stale or Unknown;
- timeout, interrupted scan and single-flight behavior remain fail closed.

Adjacent W3 tests retained the path and content gates for reparse escape, recovery boundaries, unique commits,
unknown untracked files and sensitive／unknown ignored paths. W6.1 tests additionally reject arbitrary paths, URLs,
shell strings and AI authority; detect dirty and post-authorization drift; reject locked／process-use targets; and
exercise exact registered path binding used to reject aliases including Windows 8.3 forms.

## Real temporary removal

The removal test creates and closes a linked worktree only inside a system temporary Git fixture. Before deletion it
archives the target worktree's Git-private `orrery/` tree, hashes source and archive, and requires exact equality.
After `git worktree remove` it proves:

- worktree path and Git registry record are absent;
- local branch remains present and resolves to the original target commit;
- commit object remains present;
- branch／remote branch deletion flags remain false;
- target current and last-known cache entries plus the registry summary are invalidated;
- background incremental refresh is scheduled and completes without blocking the deletion response.

No real user worktree was removed.

## Final validation ladder

| Command／surface | Result |
| --- | --- |
| `python -m unittest tests.test_workspace_maintenance tests.test_personal_observatory tests.test_team_observatory` | PASS — 24 tests in 549.237 s |
| focused W3 reparse／recovery and unique／ignored gates | PASS — 2 tests |
| affected version／brand／relation graph contracts | PASS |
| `python -X utf8 scripts/ci/validate_ci.py --all` | PASS |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated Candidate; Authority Model 1 strict eligible |
| `python -X utf8 scripts/ci/validate_repository_gates.py` | PASS — 676 paths, 365 Markdown files, 912 local links, no forbidden artifacts |
| isolated docsite build | PASS — `C:/Users/1/AppData/Local/Temp/orrery-w6-1-docsite.html` |
| `git diff --check` | PASS |

## Performance observations

Observed on the Windows fixture; timings are informational, not flaky test gates:

| Surface | Observation | Target | Result |
| --- | ---: | ---: | --- |
| cache-first page/status + render | median 553.374 ms; max 931.674 ms; 0 provider scans | < 1 s | PASS |
| one changed target, cache refresh core | 2492.473 ms; 1 provider scan, 2 cache hits | < 3 s | PASS |
| one changed target, entire scan persistence wall | 6087.436 ms | advisory | recorded |
| Quick Remove target preflight | 3421.809 ms | component observation | recorded |
| confirmed authorization + archive + removal | 2315.176 ms | component observation | recorded |
| target preflight + removal total | 5736.985 ms | < 5 s | advisory gap: +736.985 ms |

The implementation keeps the evidence gates rather than weakening them for the remaining Windows process-startup
variance. The HTTP request that starts a full refresh returns immediately and does not wait for these scan timings.

## Browser validation

Validated through the real loopback control server at the temporary fixture URL
`http://127.0.0.1:8765/control/maintenance`:

- 1440×1000 desktop: current, stale and Unknown cache states visible together; no horizontal overflow;
- 390×844 mobile: `scrollWidth 375 < innerWidth 390` after the standalone negative-margin fix;
- protected target shows explicit failure reasons;
- eligible target flow presents the repeated “only remove worktree; preserve branch/commit” boundary and the
  temporary fixture completes verified removal;
- background state renders independently; console warning／error list is empty in both viewports.

Screenshots:

- `C:/Users/1/.codex/visualizations/2026/08/29/01a04dfc-f956-7b72-9c99-85651ecbd6ef/w6-1-maintenance-desktop.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04dfc-f956-7b72-9c99-85651ecbd6ef/w6-1-maintenance-mobile.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04dfc-f956-7b72-9c99-85651ecbd6ef/w6-1-maintenance-mobile-cache.png`

## Concurrent shared-document boundary

`codex/github-front-door-redesign` currently owns uncommitted changes in `README.md`, `README.zh-CN.md`,
`docs/DEVLOG.md`, `docs/implementation/README.md`, `docs/state/documentation-system.md`,
`docs/validation/README.md` plus its own assets／Plan／Validation. W6.1 did not modify those files and did not modify
root `docs/PROGRESS.md` or `docs/HANDOFF.md`. Central integration order is: integrate the GitHub front door first,
rebase／replay W6.1 on the resulting protected main, then project W6.1 facts into affected State／DEVLOG／indexes.
