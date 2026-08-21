# 2026-08-22 Personal collaboration Phase 0

Status: Candidate validated

Governing decisions: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

Implementation Plan: [2026-08-19 多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)

## Scope and fact boundary

This record covers W1 Personal Core／CLI Phase 0 only. The implementation commit is `4ae4f0a` on
`codex/w1-personal-core-contract`, created in the independent linked worktree
`C:\Users\1\.codex\worktrees\beb5\project-orrery` from baseline `8df974f`.
The worktree was not the Git main worktree; the main worktree was
`D:\coding warehouse\project-orrery`. Both initially pointed to the same OID and the W1 worktree was clean.

The Candidate adds:

- one provider-neutral `project-orrery-collaboration-v1` schema bundle for worktree identity, Workstream
  session, Scope, overlap finding, integration report, subsystem registry, human Member capability and
  project mode contracts;
- dependency-free Core validation and read-only Git/config inspection;
- `.project-orrery.json` keys `collaboration.integration_ref`, `collaboration.primary_worktree` and
  `collaboration.project_mode`; the integration ref defaults to `refs/heads/main`, resolves only a local
  branch to a full commit OID, and never fetches or infers a remote fallback;
- default Git main-worktree recognition plus an absolute-path maintainer override that must match a listed
  worktree;
- explicit stable IDs in the self-host `AGENTS.md` subsystem index, with registry projection limited to
  existing State Docs and reserved `unmapped`／`project-wide` Scope expressions;
- human Member plus composable Reviewer／Integrator／Admin capability, bootstrap maintainer, audited
  grant／revoke/removal and monotonic local credential invalidation;
- Personal／Team mode contract parsing. Personal is the default implicit local member with all local
  capabilities and no listener, discovery, Coordinator, member authentication, sync or heartbeat. Team is
  contract-only in this phase and starts no network runtime;
- a read-only CLI 0.1.6 `collaboration-contract` entry. Core is 0.1.1; Core API remains 1.

This is Candidate implementation, not Canonical integration, release, tag, push, installed-Skill update,
Team networking, persistent session, overlap computation, worktree guard or integration execution.

## First failures and corrections

| Checkpoint | Result | Correction |
|---|---|---|
| Initial focused test before implementation | Expected failure: `ModuleNotFoundError: project_orrery_core.collaboration` | Implemented the Core schema/parser and CLI entry against the frozen test contract. |
| First focused run after implementation | 7 passed, 2 failed: CLI subprocess omitted the existing Observatory source dependency; default Git status collapsed `untracked/same-path.txt` to `untracked/` | Added the existing Observatory source path to the subprocess fixture and required `--untracked-files=all`; product rules were not relaxed. |
| Corrected focused run | 10/10 passed | No remaining focused failure. |
| First staged diff check | Found one blank line at EOF in the new synthetic fixture | Removed the new-file-only whitespace and amended the implementation commit; no frozen experiment bytes were touched. |

## Final evidence

Environment: Windows 11 build 26200, PowerShell, Python 3.13, Git available locally. No model, Provider,
remote Git operation or external network service was used.

| Command／procedure | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_collaboration_contract -v` | PASS — 10/10. |
| `python -X utf8 -m unittest tests.test_collaboration_contract tests.test_project_orrery tests.test_harness_json_adapter tests.test_authority_model_migration tests.test_authority_model_restore -v` | PASS — 69 total; 67 passed and 2 existing optional dynamic-dependency skips. |
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 241 total; 236 passed and 5 skipped. Three skips were existing Windows symlink-privilege cases; two were existing optional reader／Broker dependencies. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold structure valid; authority status `integrated candidate`; model 1 eligible. |
| `python -X utf8 scripts/docsite/build_docsite.py --out C:\Users\1\AppData\Local\Temp\project-orrery-w1-phase0-final-head-20260822.html` | PASS — clean Candidate HEAD produced an isolated 1227 KB output; 12 ADR, 6 State, 7 subsystem, 2 Snapshot, 94 docs, 16 Plan and 6 Library. `docs/_site/index.html` was not edited. |
| PowerShell local Markdown-link scan over `rg --files -g '*.md'` | PASS — 284 Markdown files, 696 local links／images, 0 missing targets. |
| `git diff --check` | PASS after correcting the new fixture EOF whitespace and again after the Candidate documentation update. |

The zero-network negative test patches Python socket creation while constructing both default Personal and
explicit Team contracts, and asserts every runtime network boundary is false with an empty active-feature
list. The CLI implementation uses only local file and read-only Git subprocess inspection; it contains no
listener, discovery, Coordinator, authentication or synchronization runtime. This is a code-path test, not a
packet-capture claim.

## Dependencies and remaining boundaries

- W2 Scope/Finding must consume this schema and registry to implement committed／staged／unstaged／untracked／
  expected-write collection, Scope B revisions and Direct／Authority／Semantic／Unknown computation. Schema
  existence does not produce findings.
- W3 Review/Cleanup depends on exact candidate/target OIDs, finding lifecycle, capability audit and integration
  report binding; this phase does not implement review decisions, speculative integration or deletion.
- W4 Observatory may project the read-only contract later, but currently consumes none of it and must preserve
  Candidate／Worktree scope labels.
- W5 Team Mode remains frozen. `member_id`, `host_id`, visibility and observability are reserved, one session has
  one `active_host_id`, and no multi-device migration, Coordinator, discovery, sync, credentials or remote
  execution exists.
- Public v0.2.0, release manifests, tags, GitHub Release, installed Skill and user configuration are unchanged.

Within this bounded Phase 0 scope, the Candidate is ready for integration review after the documentation commit
and final clean-worktree verification. It is not itself Canonical or Released.
