# 2026-08-22 W1.3 Personal Phase 1C

Status: Candidate validated

Governing decisions: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

Implementation Plan: [2026-08-19 多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)

## Scope and fact boundary

W1.3 is the Phase 1C continuation stacked on W1.2. Implementation commit `8874f1a` is on
`codex/w1-3-personal-phase-1c`; its ancestry includes W1.2 `a5ba06428f1284b1d05636778c3e1a1a1e28dd66`
and W1.1 `e38589d`. Work ran in the independent Codex worktree
`C:\Users\1\.codex\worktrees\a3c2\project-orrery`; the Git main worktree remained
`D:\coding warehouse\project-orrery`. This task did not merge, push, tag or create a Release, and it did not
modify the user-level Skill.

The Candidate adds:

- Core 0.1.4 session fields for independent lifecycle phase, runtime condition, evidence freshness, closure reason,
  lifecycle revision and last transition; explicit transitions enforce a legal graph and require closure reasons;
- a read-only status projection that preserves the declared phase while deriving an effective phase; stale Git
  bindings or non-current review evidence revoke effective Review Ready to `validating` with stable reasons;
- fail-closed boundaries that reject Agent-initiated entry into Review Ready or Integrated until the executable
  review and integration gates planned for Phase 3 exist;
- a provider-neutral Adapter capability contract for launch／attach／rebind／message and stable read-only
  `worktree route` JSON, including clean／dirty primary blocks, absent／stale session handling, conditional
  caller-provided Agent-first attach and minimal continuation briefs;
- Git-private `worktree session attach`; rebind requires both explicit caller intent and an Adapter capability.
  All current Agent Adapters declare attach only, and Harness JSON declares no Agent runtime capability;
- Adapter 0.1.1 Skill routing that requires `worktree route` before the first product write, attaches when requested,
  and continues only after an allow result. This is an Adapter-instruction boundary, not a host-level interception
  of arbitrary writes.

All routing, lifecycle and attach behavior uses local Git／filesystem operations. `route` is read-only, attach writes
only `git rev-parse --git-path orrery/worktree.json`, and Personal Mode starts no network feature. Existing Codex,
Claude Code and DeepSeek runtime evidence remains bound to Adapter 0.1.0; this Candidate does not claim verified
runtime support for Adapter 0.1.1 or automatic platform launch／rebind.

## Verification evidence

Environment: Windows 11 build 26200, PowerShell, Python 3.13 and local Git.

| Command／procedure | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_collaboration_contract -v` | PASS — 22/22. |
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 260 total; 255 passed and 5 existing environment／optional-dependency skips. |
| `$env:ORRERY_TEST_BUILD='1'; python -X utf8 -m unittest discover -s tests -v` | PASS — 260 total; 257 passed and 3 existing Windows symlink-privilege skips; dynamic reader and Broker tests executed. |
| Lifecycle／route／attach Git fixtures with socket creation patched | PASS — legal graph, gate closure, effective Review Ready revocation, four manifests, stable CLI JSON／exit 5, private writes and zero-network Core paths covered. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated structure and Authority model eligibility preserved. |
| `python -X utf8 scripts/docsite/build_docsite.py --out $env:TEMP/project-orrery-w1-3-phase1c/project-orrery-w1-3-phase1c.html` | PASS — 1,411,564-byte isolated static build; tracked `docs/_site/index.html` unchanged. |
| PowerShell local Markdown-link scan over `rg --files -g '*.md'` | PASS — 301 Markdown files, 802 local links／images and 0 missing targets. |
| High-confidence private-key／token scan and forbidden tracked-artifact inventory | PASS — 0 secret matches; 0 `ai-config.json`／cache／`.port`／`docs/_site`／Python cache artifacts tracked. |
| `git diff --check` | PASS. |

## Remaining boundaries

- W2 remains reserved for Scope/Finding. W1.3 does not collect actual path scope, calculate overlap findings or
  implement acknowledgement policy.
- Review Ready and Integrated are deliberately unavailable without future executable gates. Speculative integration,
  review actions, cleanup, closure archive and automatic integration are not implemented.
- Current Adapters do not claim launch／rebind／message support and require a caller-provided platform session ID for
  attach. Their Skill instruction can guard Adapter-mediated work, but it cannot intercept arbitrary host or Agent
  writes outside the Adapter.
- No Observatory or Team Mode runtime is implemented. Personal Mode remains zero-network.
- Core 0.1.4, CLI 0.1.9 and Adapter 0.1.1 remain `unreleased`; public v0.2.0, the user-level Skill, release manifest and historical
  verified runtime scopes are unchanged. This Windows Candidate has no W1.3 cross-platform CI evidence.
