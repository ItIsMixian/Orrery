# U2.2 Unified Navigation & Workspace Maintenance UX

Date: 2026-08-29
Status: implemented and validated in isolated Candidate worktree
Workstream: `U2.2-unified-navigation-workspace-maintenance-ux`
Exact task base: `codex/u1-u2-integration-baseline@ad9f0946a191b8810d99f70171318a4d5536c425`
Governing decision: [ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md)
Approved design: [Unified Observatory architecture and shell](../../design/unified-observatory-architecture-and-shell.md)
Related plan: [Workspace Maintenance](2026-08-27-workspace-maintenance-and-scheduled-cleanup.md)

## Candidate scope

This Workstream responds to the third maintainer review of the integrated Unified Observatory Candidate. It changes
only presentation composition and bounded browser state. It does not change Maintenance Core eligibility, cache,
preflight, authorization, execution or receipt semantics; it does not enable automatic deletion, scheduler, network,
Team execution, Graph execution, Authority selection or AI permissions.

W7.2 Graph work remains parallel and isolated. This branch must not modify the Graph implementation, Graph tests,
Graph Plan/Validation or graph-specific CSS/JavaScript. Shared component versions, subsystem State, DEVLOG,
Validation index, PROGRESS and HANDOFF are integration-owned and intentionally excluded from this Candidate.

## Compact design brief

- **Purpose:** help a maintainer scan 15 or more registered worktrees, understand protection, refresh current evidence
  and discover safe local removal without translating machine protocol fields.
- **Context:** an operational documentation/control app for one local repository.
- **Tone:** dense analyst workspace within Orrery's existing calm, dark evidence-led visual system.
- **Differentiator:** one continuous navigation rail and one bounded maintenance queue whose first viewport answers
  “what needs attention, what can be removed, and why”.
- **Constraints:** generated HTML/CSS/JavaScript, no new dependency or image asset, Chinese-first primary UI,
  1280×800 / 1440×900 / 390×844, keyboard focus, ARIA, reduced motion, no page-level horizontal overflow.

## Implementation and acceptance

- [x] compose app destinations and the collapsible author-document tree inside one sidebar DOM and one scroll
  container, with one active-state system and no duplicate dashboard/document entry;
- [x] move “刷新工作区状态” into the Maintenance header action area and replace the full-width scan strip with a
  compact, no-layout-shift status;
- [x] replace long workspace cards with a dense row list, four filters, stable grouping and an 8-item page;
- [x] show workspace/task, display state, primary reason, recent evidence/activity and action in each row, while
  keeping paths, branches, raw reasons and protocol fields in row details;
- [x] preserve fresh target preflight and action-specific confirmation; only current eligible rows expose
  “安全删除” and zero-eligible state explains leading protection reasons;
- [x] collapse policy, thresholds, scheduler, branch/remote boundaries and operation history into bottom technical
  details; render legacy/history warnings as compact expandable banners;
- [x] keep mobile rows compact rather than converting the desktop table into tall cards;
- [x] add mechanical fixtures for 15 rows, paging, four filters, zero/non-zero eligible states, technical disclosure,
  continuous rail and header refresh placement;
- [x] verify the real self-host Maintenance status plus 1280×800, 1440×900 and 390×844 browser flows with zero
  console error/warning and no horizontal page overflow;
- [x] run CI6 Fast dry-run/Fast and Checkpoint dry-run/Checkpoint, then commit a clean Candidate without pushing main
  or publishing.

## Validation ladder

```text
python -X utf8 -m unittest -v tests.test_unified_observatory tests.test_workspace_maintenance
python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage fast --base ad9f0946a191b8810d99f70171318a4d5536c425
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425 --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base ad9f0946a191b8810d99f70171318a4d5536c425
real self-host browser: 1280×800, 1440×900 and 390×844
git diff --check
```

Full Candidate/Promotion, hosted Windows/Ubuntu checks, shared-file reconciliation, main promotion and release remain
central integration work.
