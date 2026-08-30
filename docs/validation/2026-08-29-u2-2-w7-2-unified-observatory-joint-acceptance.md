# U2.2／W7.2 Unified Observatory Joint Acceptance Candidate

Date: 2026-08-29

Status: READY FOR MAINTAINER LOCAL ACCEPTANCE — combined Fast and browser PASS; combined Checkpoint budget timeout

## Scope and exact integration

- Integration branch: `codex/u1-u2-integration-baseline`.
- Integration base: `6166d1537f3118f9b74b9dbf2ff110f79a9d7bb3`.
- W7.2.3 source: `codex/u2-1-unified-observatory-ux-acceptance-fixes@30d44ffa051bbd0e108e5c634beaa01942baefe5`.
- U2.2 source: `codex/u2-2-unified-navigation-workspace-maintenance-ux@70e6ac96cdc405414a6a5989a4e541cc9f801c70`.
- Combined feature merge: `0eaad3050563cccc9c5eeb1d77cec743d3e29a99`.
- Components: Core 0.1.17, CLI 0.1.21, Observatory 0.1.16; all remain `unreleased`.

The unique integrator merged W7.2.3 first, then U2.2. Their product file sets did not overlap: W7.2 owns Graph
presentation and shared docsite scrollbar styling; U2.2 owns Unified navigation composition and Maintenance
presentation. Central CI7／ADR-0017 additions and W7.2 touched DEVLOG／State／Validation index additively; only DEVLOG
and the Validation index required manual additive conflict resolution. No Core relation, Maintenance eligibility,
authorization, receipt, Team execution or release contract was changed by the merge.

## Combined behavior

- One continuous sidebar contains app destinations and the collapsible project-document tree; there is one sidebar
  DOM, one scroll rail and one selected-state system.
- Maintenance uses a header-level `刷新工作区状态`, compact 8-row pages, four filters, bounded row details and folded
  policy/history evidence. Only Core-eligible rows can expose `安全删除`; no deletion was performed.
- Workstream Graph uses readable left-to-right ranks, fixed-size cards, engineering line patterns, fixed-size arrows,
  chain-local history disclosure, canvas zoom and an in-canvas details drawer. Desktop hides the duplicate visual
  ledger while retaining semantic DOM; 390px uses the ordinary relation list.
- Dependency/conflict lenses remain facts-first. The real self-host currently has no explicit `depends_on`, so the
  dependency lens displays zero nodes/edges and a Chinese explanation rather than synthetic current tasks.

## Local validation

Formal routing from the clean pre-integration base selected 38 Fast and 44 Checkpoint tests with zero unknown paths.

```text
python -X utf8 scripts/ci/validate_change.py --stage fast --base 6166d1537f3118f9b74b9dbf2ff110f79a9d7bb3
PASS — 38/38 in 3.098898s, evidence-eligible

python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 6166d1537f3118f9b74b9dbf2ff110f79a9d7bb3
TIMEOUT — fixed 90.0s outer budget while the existing
test_minimal_git_incremental_refresh_and_target_preflight_checkpoint was still running
```

No assertion failure preceded the timeout. U2.2 independently passed its 40/40 Checkpoint in 81.130677s; W7.2.1–3
did not modify Maintenance semantics or that slow fixture, and their focused Graph／Unified, JavaScript, Fast and
browser evidence remains valid. This combined record does not turn those isolated receipts into a combined
evidence-eligible Checkpoint PASS; CI7 remains responsible for later routing/cost correction.

The synchronized closeout diff reran routed Fast 38/38 in 3.648712s, repository gate over 723 repository paths／393
Markdown files／1040 local links, and `git diff --check`; all passed. Full Candidate／Promotion and hosted
Windows／Ubuntu checks are intentionally not part of the maintainer experience loop.

## Real browser acceptance

The combined branch was served through one supervised loopback URL with AI disabled. Browser checks used the actual
self-host Git-private projections, not a synthetic screenshot fixture.

- 1440×900 overview: one continuous sidebar and one visible URL.
- 1440×900 Maintenance: 16 worktrees, 9 need attention, 0 safe removals and 7 protected; refresh and several dense
  rows fit in the first viewport.
- 1440×900 Graph: 14 visible nodes, 7 succession edges, 100% readable scale, closed inspector and a desktop semantic
  ledger clipped to 1×1px.
- Dependency lens: 0 nodes, 0 edges, `当前没有已登记的依赖关系` and no synthetic filler.
- 390×844 Graph: normal `任务关系列表` from the same current-lens facts; controls remain usable.
- 390×844 Maintenance: summary, refresh, filters, pager and compact rows remain usable.
- Document-level horizontal overflow was zero at both viewports; console warning/error count was zero.

The local candidate remains open for maintainer experience. Closing the browser tab does not imply service shutdown;
the explicit `关闭 Orrery 服务` control remains the supported shutdown path.

## Remaining authority boundary

- This is a local root-only/default-off integrated Candidate, not `origin/main`, public/default behavior or v0.2.0.
- Maintainer acceptance is still required before freezing a non-main exact Promotion candidate.
- After acceptance, the exact clean SHA must pass Candidate/Promotion and both hosted required checks before any main
  promotion. Public template, managed tools, installer, SemVer/tag/Release and default launcher remain separate
  decisions.
- Real dual-host Team, automatic leader selection, cloud relay, remote execution, automatic worktree deletion and OS
  scheduler remain unsupported.
