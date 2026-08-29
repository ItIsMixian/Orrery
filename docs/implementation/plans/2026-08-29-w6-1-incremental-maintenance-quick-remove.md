# W6.1 Incremental Maintenance Cache + Quick Remove Implementation Plan

Date: 2026-08-29
Status: Candidate implemented and locally validated; shared documentation replay deferred to central integration
Workstream: `W6.1-incremental-maintenance-quick-remove`
Branch: `codex/w6-1-incremental-maintenance-quick-remove`
Base: protected `main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`
Governing decisions: [ADR-0007](../../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)
Parent plan: [Workspace Maintenance and scheduled cleanup](2026-08-27-workspace-maintenance-and-scheduled-cleanup.md)

## Scope

W6.1 makes the already implemented, locally confirmed Phase 2 flow responsive without changing its authority boundary.
It adds a Git-private incremental cache and a target-scoped Quick Remove path. It does not implement Phase 3 automatic
deletion, Phase 4 scheduling, branch deletion, Team-side execution, remote status checks or a public release switch.
No new ADR is required because removal remains a single locally confirmed `remove-worktree` action with every existing
cleanup gate revalidated immediately before execution.

## Expected writes and concurrent boundary

Implementation touches maintenance Core／v2 schema, CLI, Personal Maintenance rendering, root-only local control
server／launcher, focused tests, component versions and this Workstream's exclusive Plan／Validation. The concurrent
`codex/github-front-door-redesign` worktree has no Maintenance or root launcher changes, but it has uncommitted changes
in `README.md`, `README.zh-CN.md`, `docs/DEVLOG.md`, `docs/implementation/README.md`,
`docs/state/documentation-system.md`, `docs/validation/README.md` plus its own assets／Plan／Validation. W6.1 therefore
does not edit shared State／DEVLOG／indexes; the central integrator must merge the front door first, then replay those
W6.1 documentation projections on the resulting protected main.

## UI design brief

- Purpose: let a maintainer understand cached workspace health immediately and safely remove one registered linked
  worktree without waiting for an unrelated repository-wide scan.
- Context: dense local operational console, not a marketing surface.
- Tone: calm industrial control room, preserving Orrery's existing typography, dark/light tokens and information
  architecture.
- Differentiator: each target carries an explicit `current / stale / Unknown` cache rail, while the destructive flow
  repeatedly states “only remove the worktree; preserve branch and commit.”
- Constraints: semantic HTML, keyboard-visible controls, mobile width without horizontal overflow, reduced-motion
  support, loopback root-only serving, Personal zero-network and fixed JSON POST shapes.

## Implementation checkpoints

### A. Cache contract and incremental scan

- [x] Store versioned atomic entries below `$GIT_COMMON_DIR/orrery/maintenance/cache-v1/`.
- [x] Bind repository/worktree identity, registered path and git-dir, HEAD/branch, index/dirty/untracked/ignored
  fingerprint, session/closure/review hashes, integration OID, policy/schema/tool versions and scan timestamps.
- [x] Reuse unchanged entries; rescan only added, removed or fingerprint-changed worktrees.
- [x] On integration OID movement, recompute only ancestry/integration-dependent classifications.
- [x] Fail closed for missing, corrupt or unknown-version cache while retaining last-known state as stale/Unknown.
- [x] Keep full scans off HTTP request threads and expose progress/failure.

### B. Target-scoped Quick Remove

- [x] Accept only versioned maintenance item/worktree IDs or local authorization IDs.
- [x] Run fresh target-only preflight without full-project inventory.
- [x] Revalidate registered identity, exact path, HEAD/branch, clean/untracked/ignored, session/closure,
  integration/unique commits, process/path safety and authorization drift.
- [x] Archive the target Git-private session and verify its hash before `git worktree remove`.
- [x] Preserve branch/commit, invalidate only the target cache and registry summary, then schedule background refresh.
- [x] Never wait for GitHub CI or perform network I/O.

### C. Root-only control surface

- [x] Render cache state, last-known/stale/Unknown, background scan progress/failure and single-target confirmation.
- [x] Add `start-orrery-control.bat` to launch loopback-only root control and open the Maintenance page.
- [x] Keep Team authority absent from this entry; Team central remains cleanup-request only.

### D. Validation and authority synchronization

- [x] Prove cache hits avoid expensive full inventory/provider calls and cover all invalidation dimensions.
- [x] Cover corrupt/unknown cache, path aliases/8.3, reparse escape, ignored Unknown, unique commits, process use and
  post-authorization drift.
- [x] Remove only a temporary linked-worktree fixture and verify archive/registry/cache/branch/commit postconditions.
- [x] Preserve Host/Origin/cookie/body and fixed-POST security boundaries.
- [x] Measure cache hit, one-target incremental refresh and target preflight/removal without flaky hard timing gates.
- [x] Browser-verify desktop/mobile cache, stale/Unknown, confirmation and failure states with no console error or
  horizontal overflow.
- [ ] Replay affected State／DEVLOG／indexes after `github-front-door-redesign` integration; exclusive Validation is
  complete on this branch and root PROGRESS／HANDOFF remain untouched.

## Validation ladder

Fast runs focused cache/Core/UI tests during editing. Checkpoint adds adjacent W3/Personal/HTTP contracts and isolated
docsite build. Final Candidate runs CI contract, integrated structure, repository links/forbidden artifacts and
`git diff --check`. Promotion to protected main remains a later central-integration action on an exact pushed Candidate
SHA with Windows and Ubuntu required checks.
