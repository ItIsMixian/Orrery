# 2026-08-22 W2 Scope / Finding

Status: Candidate validated

Governing decisions: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

Implementation Plan: [2026-08-19 多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)

## Scope and fact boundary

W2 was implemented in the independent Codex worktree
`C:\Users\1\.codex\worktrees\58da\project-orrery` on branch `codex/w2-scope-finding`, from
the starting `origin/main@193b3bab78e61eeebfa05e314fb0eb12b98ecd15`. The implementation commit is
`de5152efc3193db50f85b20e95dad46491909c07`.

The Candidate extends the existing collaboration-v1 contract, private Workstream session, subsystem registry,
worktree status/create/guard/route and caller-provided attach. It does not create a parallel rule set. Core 0.1.5
and CLI 0.1.10 add:

- one `scope-observation` over merge-base→HEAD committed, staged, unstaged, file-level untracked and session
  expected-write paths, preserving every source on each path;
- Authority classification for Seed, ADR, Design, Plan, State, Validation, AGENTS, PROGRESS, HANDOFF and DEVLOG;
- registry-derived subsystem mapping from explicit `AGENTS.md` Truth paths and existing authority links, while
  preserving `unmapped`／`project-wide` and treating shared subsystem alone only as Semantic priority;
- Direct／Authority／Semantic／Unknown finding, stable Scope/finding fingerprints, Open／Acknowledged／Resolved／
  Stale lifecycle, local-human-only L2 acknowledgement and cross-member `n/m` projection;
- Scope Expansion B: L0 record, L1 automatic revision, L2 local member confirmation with reason and revision,
  and L3 failure closure; central/Agent acknowledgement sources are rejected;
- default configurable exclusive resources for credentials, release and schema migration, plus Adapter-route
  failure closure for Direct／L3 and locally unacknowledged L2;
- read-only `worktree overlap` and `worktree scope inspect`, Git-private `scope refresh` and
  `finding acknowledge`; supplied peer-scope files are metadata contracts only and no Team transport exists.

Acknowledged L2 and retired finding history remain in the private session as mandatory future W3 review-package
inputs. W2 does not generate a review package or implement Review Ready, integration, cleanup, Observatory,
Coordinator／LAN／Team runtime, automatic merge or automatic remediation.

## Verification evidence

Environment: Windows 11 build 26200, PowerShell, Python 3.13 and local Git. Socket creation／connection is patched
to fail in focused Core paths; CLI results also report `network_performed: false`.

| Command／procedure | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_collaboration_contract -v` | PASS — 27/27 after adding five W2 cases; all W1 Phase 0／1 cases remain green. |
| W2 five-test focused selection | PASS — source collection, four finding kinds, L1/L2/L3, cross-member lifecycle and CLI zero-network cases all pass. |
| `python -X utf8 -m unittest tests.test_project_orrery tests.test_codex_adapter tests.test_claude_code_adapter tests.test_deepseek_harness_adapter tests.test_harness_json_adapter tests.test_authority_model_migration tests.test_authority_model_restore -v` | PASS — 71 total; 69 passed and 2 existing dynamic-dependency skips. |
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 278 total; 273 passed and 5 existing environment／optional-dependency skips. |
| `$env:ORRERY_TEST_BUILD='1'; python -X utf8 -m unittest discover -s tests -v` | PASS — 278 total; 275 passed and 3 Windows symlink-privilege skips. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated candidate; Authority Model 1 supported and strict-evaluation eligible. |
| `python -X utf8 scripts/docsite/build_docsite.py --out C:\Users\1\AppData\Local\Temp\project-orrery-w2-scope-finding-20260822-final\index.html` | PASS — isolated 1431 KB site; tracked `docs/_site/index.html` remains absent／unchanged. |
| PowerShell local Markdown-link scan | PASS — 333 Markdown files／851 local links; one expected synthetic missing target in the D1 positive fixture, zero unexpected missing. |
| High-confidence secret scan and release-policy forbidden tracked-artifact inventory | PASS — zero high-confidence secret matches and zero forbidden tracked artifacts. |
| `git diff --check` | PASS for the final implementation and documentation diff. |

One intermediate default-suite run was discarded because `docs/state/test-coverage.md` changed while its
Observatory render-stability tests were in flight, producing seven expected before／after snapshot mismatches.
The repository was then held static and the complete default suite reran to the PASS result above.

The Git fixture uses two linked worktrees plus an independent clone and writes only temporary repositories.
W2 assertions include pattern-style W1 expected writes ending in `/`, NUL-safe Git name-status collection,
source provenance, same-path tracked／untracked overlap, Authority overlap, shared validation Semantic overlap,
sharing-off Unknown, custom exclusive-resource configuration, L2 local confirmation and an L3 route block.

Cross-member coverage records `Acknowledged 1/2`, keeps Review Ready blocked, then reaches `2/2`; a Scope
fingerprint change retires the old acknowledgement as Stale and opens a new revision, while disappearance of the
condition mechanically produces Resolved. Direct／L3 acknowledgement and central-request acknowledgement both
fail closed.

During final validation, `origin/main` advanced by two Candidate-first promotion-gate commits to `6e1f9cb`.
The W2 branch therefore ended one commit ahead and two commits behind that moving ref before this Validation
commit. The upstream delta changes CI and authority documentation, not W2 implementation paths; its shared
DEVLOG／Plan／State／Validation-index edits must still be additively reconciled by the unique integrator.

## Remaining boundaries

- This is a Worktree／Candidate result, not Canonical integration, push, cross-platform CI or release evidence.
- The newer Canonical promotion rule requires the exact final Candidate SHA to be pushed to a non-main branch
  and pass both GitHub Windows／Ubuntu smoke checks before main promotion. This task explicitly forbids push, so
  the Candidate is ready for integrator pickup but not yet eligible for main promotion.
- W3 review／integration／cleanup, closure archive, actual Review Ready transition and AI-assisted review package
  are not implemented.
- No Observatory or Team runtime exists. Personal Mode remains zero-network; peer-scope file consumption is a
  local contract boundary, not sync or transport.
- Adapter route is a Skill／CLI preflight, not host-level interception of arbitrary writes. Current Adapters still
  do not claim launch／rebind／message support.
- Core 0.1.5 and CLI 0.1.10 remain `unreleased`; public v0.2.0, user-level Skill, release manifest, tag and Release
  are unchanged, and historical Adapter 0.1.0 runtime evidence does not transfer to this Candidate.
