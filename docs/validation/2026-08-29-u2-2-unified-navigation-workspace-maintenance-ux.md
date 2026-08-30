# U2.2 Unified Navigation & Workspace Maintenance UX Validation

Date: 2026-08-29
Fact scope: isolated Candidate worktree
Exact task base: `codex/u1-u2-integration-baseline@ad9f0946a191b8810d99f70171318a4d5536c425`
Workstream: `U2.2-unified-navigation-workspace-maintenance-ux`
Result: PASS for implementation, mechanical regression, real self-host browser acceptance, CI6 Fast and CI6 Checkpoint

This evidence applies only to the U2.2 Candidate worktree. It is not Canonical, is not published, and does not claim
Promotion or hosted Windows/Ubuntu evidence.

## Implemented contract

- Unified app destinations and the author-document tree now share one `aside[data-unified-sidebar]`, one continuous
  `overflow-y:auto` rail and one selected-state system. The document tree is a collapsible group in that rail; it has
  no nested scroll container or second navigation background.
- Workspace Maintenance places `刷新工作区状态` in the page header action area with fixed-width compact live status.
  The previous full-width action strip is absent.
- Maintenance renders a stable, display-only grouping over Core results with four filters and an eight-row page. Main
  rows expose workspace/task, state, primary reason, recent evidence and action; protocol IDs, paths, branches, raw
  reasons and secondary evidence stay in row details.
- Only Core-eligible current rows render `安全删除`. The browser continues to call fresh target preflight and the
  action-specific confirmation before the existing quick-remove endpoint. Zero-eligible state explains that leading
  protection reasons are in technical details.
- Policy version/thresholds, scheduler status, branch and remote boundaries, authorization history and legacy details
  are folded by default. Mobile uses compact rows rather than one tall card per worktree.

No Maintenance Core eligibility, cache, preflight, authorization, execution or receipt semantics changed. No automatic
deletion, scheduler, Team/Graph/Authority/AI permission or network capability was added.

## Mechanical evidence

The updated fixtures verify:

- exactly one unified sidebar element and one sidebar scroll container, with app navigation before the project-document
  tree and no independent document-tree overflow;
- refresh control inside the Maintenance header, no `.mo-actions` scan row, compact live state and page size `8`;
- a 15-entry corpus with 10 attention, 2 eligible and 3 protected entries; the default view exposes only 8 entries,
  with correct `attention`, `eligible`, `protected` and `all` filters and paging;
- both 2-eligible and zero-eligible Quick Remove states; only eligible rows contain the action, while the fresh
  preflight and exact confirmation contract remain present;
- bottom technical policy details folded by default, machine fields confined to row details, compact history banner,
  native button semantics, ARIA state/live regions, focus-visible styles and reduced-motion handling.

Focused regression after updating the obsolete U2.1 copy assertions:

```text
python -X utf8 -m unittest -v \
  tests.test_unified_observatory.UnifiedRegistrationTests.test_static_shell_has_navigation_but_no_dynamic_control_script \
  tests.test_personal_observatory.PersonalObservatoryTests.test_workspace_maintenance_page_is_static_read_only_or_explicitly_host_local \
  tests.test_workspace_maintenance.WorkspaceMaintenanceTests.test_versioned_contract_policy_and_synthetic_corpus_are_fail_closed

Ran 3 tests in 0.356s — OK
```

## Real self-host browser acceptance

The current worktree was served over loopback with the source package paths. One real refresh completed and updated the
live Maintenance cache from 15 to 16 registered worktrees: 9 need attention, 0 are safe to remove, and 7 are protected.
No remove/preflight confirmation was triggered, no real deletion occurred, and no external provider or network was
used.

| Viewport | Evidence |
| --- | --- |
| 1280×800 | one continuous sidebar; header refresh and summary visible; multiple dense rows in the first viewport; page overflow `0` |
| 1440×900 | 8 bounded rows on page 1, 6 intersecting the first viewport; technical policy folded; page overflow `0` |
| 390×844 | filters, refresh and pager usable; 8 bounded rows; first row `147.625px`; page overflow `0` |
| 390×844 nav | one visible sidebar with `overflow-y:auto`; app and document groups both present; 0 nested scroll containers |

The four filters, two-page `all` view (8 + 8 after the live count reached 16), row technical disclosure, project-document
collapse, policy disclosure and mobile menu were exercised. Console error/warning count was zero. Local screenshots:

- `C:/Users/1/.codex/visualizations/2026/08/30/01a05029-d528-73f2-9c3f-119c7b6365a5/u2-2/maintenance-1280x800-final.png`
- `C:/Users/1/.codex/visualizations/2026/08/30/01a05029-d528-73f2-9c3f-119c7b6365a5/u2-2/maintenance-1440x900-final.png`
- `C:/Users/1/.codex/visualizations/2026/08/30/01a05029-d528-73f2-9c3f-119c7b6365a5/u2-2/maintenance-390x844-final.png`
- `C:/Users/1/.codex/visualizations/2026/08/30/01a05029-d528-73f2-9c3f-119c7b6365a5/u2-2/sidebar-390x844-final.png`

## CI6 evidence

```text
python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run
DRY-RUN fast: 34 selected tests

python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425
PASS local-fast-evidence fast: 34/34 tests in 2.767512s

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run
DRY-RUN checkpoint: 40 selected tests, 90.0s budget

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425
PASS local-checkpoint-evidence checkpoint: 40/40 tests in 81.130677s
```

The first Checkpoint attempt reached its 90-second budget while a stale self-host process was still running. The slow
fixture passed alone in 71.680s; after stopping that task-owned process, the unchanged suite passed inside budget as
recorded above. No failed attempt is reclassified as passing evidence.

## Parallel overlap and integration boundary

U2.2 intentionally did not modify `workstream_relation_graph.py`, Graph tests, the W7.2 Plan/Validation or graph-specific
CSS/JavaScript. It also did not modify root PROGRESS/HANDOFF, shared component versions, subsystem State, DEVLOG or the
Validation index.

W7.2's broad Observatory package scope overlaps U2.2 at the shell composition layer, especially
`unified_observatory.py`; its declared package scope also covers `personal_observatory.py`, although U2.2 made no Graph
behavioral change there. Central integration should apply W7.2 first, then U2.2 as the final shell/maintenance UX pass,
resolve shell changes additively, perform one shared component/State/DEVLOG/index update, and rerun combined
Fast/Checkpoint plus exact-Candidate hosted checks before any main promotion.
