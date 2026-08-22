# 2026-08-22 W1.2 Personal Phase 1B

Status: Candidate validated

Governing decisions: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

Implementation Plan: [2026-08-19 多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)

## Scope and fact boundary

W1.2 is a Phase 1B continuation stacked on the unintegrated W1.1 Candidate. Implementation commit `ebf9b75`
is on `codex/w1-2-personal-phase-1b`; its ancestry is W1.1 `e38589d`, based on
`main@606e2c8`. Work ran in the independent Codex worktree
`C:\Users\1\.codex\worktrees\a3c2\project-orrery`; the Git main worktree remained
`D:\coding warehouse\project-orrery`. This task did not merge, push, tag or create a Release.

The Candidate adds:

- Core 0.1.3 `create_worktree`, which resolves only the configured local integration ref, pins its exact commit
  OID, creates a short local branch and linked worktree from that OID, then initializes a `created` session at
  the target worktree's Git-private path;
- preflight rejection for invalid／existing branches, existing target paths, missing parent directories, invalid
  subsystem scope and `--from` values that differ from the configured integration ref;
- conservative rollback of only the clean branch／worktree created by the current operation when private session
  initialization fails or the integration ref drifts; incomplete rollback is reported rather than force-deleting;
- Core's read-only primary-write guard and CLI 0.1.8 `project-orrery worktree guard`, with stable allow／block
  reasons and exit 5 for a blocked product-write preflight;
- CLI `project-orrery worktree create <workstream-id> --branch <branch> [--path <path>]
  [--from <integration-ref>] --primary-subsystem-id <id>` with the existing stable JSON envelope.

Creating from a dirty primary worktree does not move or rewrite its author changes. The linked worktree begins
clean with a distinct `$GIT_DIR`, shared `$GIT_COMMON_DIR`, pinned HEAD and current private session. All Core／CLI
paths are local Git／filesystem operations; Personal Mode starts no listener, discovery, Coordinator, member auth,
heartbeat or synchronization runtime.

## Verification evidence

Environment: Windows 11 build 26200, PowerShell, Python 3.13 and local Git.

| Command／procedure | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_collaboration_contract -v` | PASS — 18/18. |
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 256 total; 251 passed and 5 existing environment／optional-dependency skips. |
| `$env:ORRERY_TEST_BUILD='1'; python -X utf8 -m unittest discover -s tests -v` | PASS — 256 total; 253 passed and 3 existing Windows symlink-privilege skips; dynamic reader and Broker tests executed. |
| Dirty primary → Core create → linked worktree status／session／guard | PASS — primary porcelain bytes unchanged; target clean, non-primary, exact integration HEAD, current `created` session and guard allow. |
| Branch／path collision, injected session failure and integration drift fixtures | PASS — collisions wrote nothing; failure/drift removed the operation-owned worktree and branch without force deletion. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated structure and Authority model eligibility preserved. |
| `python -X utf8 scripts/docsite/build_docsite.py --out $env:TEMP/project-orrery-w1-2-phase1b/project-orrery-w1-2-phase1b.html` | PASS — 1,397,893-byte isolated static build; tracked `docs/_site/index.html` unchanged. |
| PowerShell local Markdown-link scan over `rg --files -g '*.md'` | PASS — 300 Markdown files, 796 local links／images and 0 missing targets. |
| High-confidence private-key／token scan and forbidden tracked-artifact inventory | PASS — 0 secret matches; 0 `ai-config.json`／cache／`.port`／`docs/_site`／Python cache artifacts tracked. |
| `git diff --check` | PASS. |

The focused suite patches Python socket creation during Core status／guard／create paths, proving W1.2 does not
open a network socket. The subprocess CLI fixture checks stable command names, Core／CLI versions, JSON status,
warning structure and exit codes. Existing W1.1 coverage continues to prove linked worktree and independent clone
status／session behavior and stale reasons.

## Remaining boundaries

- The guard is a platform-neutral preflight primitive; no Adapter yet enforces it before every Agent product write.
  Launch／attach／rebind／message capability, automatic attach and dirty-main selective transfer remain unimplemented.
- W2 remains reserved for Scope/Finding. W1.2 does not collect path overlap, calculate findings or implement Scope
  Expansion B beyond validating the initial subsystem fields used to create the private session.
- No lifecycle transition engine, review, speculative integration, cleanup, closure archive, Observatory projection
  or Team runtime is implemented. Personal Mode remains zero-network.
- Core／CLI remain `unreleased`; public v0.2.0, the user-level Skill, release manifest and verified Adapter runtime
  scopes are unchanged. This Windows Candidate has no W1.2 cross-platform CI evidence.
