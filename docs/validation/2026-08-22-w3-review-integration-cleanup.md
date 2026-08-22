# 2026-08-22 W3 Review / Integration / Cleanup Candidate

## Scope

- Worktree: `C:\Users\1\.codex\worktrees\3507\project-orrery`
- Branch: `codex/w3-review-integration-cleanup`
- Local base: `main@ef488715dee369cbce81806f3040b4c0417d3eb8`
- Candidate state: uncommitted Worktree changes; HEAD remains the base OID.
- Remote freshness boundary: `git fetch origin main` failed because the configured local proxy `127.0.0.1:7897` was unavailable. At task start, local `main`, local tracking `origin/main`, and HEAD were identical; this record does not claim a newer remote observation.

This Candidate implements only W3 Review / Integration / Cleanup, including the 2026-08-23 workspace-inventory cleanup-contract clarification. It reuses collaboration-v1, Workstream session, Scope, finding, acknowledgement and route-gate facts from Canonical W1/W2. It does not implement Observatory, Team Mode, a central service, LAN transport, telemetry, platform launch/rebind/message, automatic main updates, push, PR, tag, release, or user branch/worktree/directory deletion.

## Contract and safety checks

- `integrate --dry-run` pins target OID and candidate HEAD, creates a new disposable detached integration worktree, requires it to be clean, performs merge or rebase speculation, runs validation commands without a shell, records raw stdout/stderr, rechecks target drift, and removes only its own temporary worktree.
- Review packages live under common Git-private `orrery/reviews/`, put raw/structured evidence before an optional `derived-non-authoritative` AI summary, and bind target/candidate/Scope/finding/schema/validation hashes plus package content hash.
- State alignment requires affected implementation and subsystem State to move together. ADR alignment reports temporary IDs, formal-number collisions, missing references and Integrator-only numbering confirmation without rewriting author documents.
- Risk policy counts only human decisions; elevated/high changes require a non-author reviewer. Approve, Request Changes, Hold and Reject record action, actor, capability, reason, evidence, timestamp and invalidation conditions.
- Integration and cleanup are eligibility reports only. Closure is permitted only after a caller-provided final OID is already reachable from the selected local ref and is stored in Git-private `orrery/closures/`. No command merges main or deletes a user branch/worktree.
- Workspace inventory is bounded to Git worktree metadata, Git-private session/closure, optional project-config workspace roots and explicit user candidate paths. It never recursively discovers a disk or assumes same-prefix directories belong to Orrery. It reports seven conservative classifications, estimated size, Unknown, protections and recommendations.
- Legacy unmanaged/Unknown paths need explicit adopt/classify before eligibility. Active/pending tasks, evidence/benchmark retention, recovery/immutable paths, credential/cache boundaries, path escape/reparse points, foreign Git common dirs, dirty/untracked/ignored content, unique commits, missing review/Validation/closure and target drift fail closed.
- Remove worktree, delete local branch, delete remote branch and remove ordinary directory have independent authorization IDs, empty implication sets and `performed: false`. `cleanup-receipt` only records a caller-attested external action under the closure's Git-private action log; it performs no destructive action.

## Focused evidence

| Check | Result |
| --- | --- |
| `python -X utf8 -m unittest tests.test_collaboration_w3 -v` | PASS, 13/13 in 288.431 seconds, including candidate/Scope/finding/target/validation-set drift, Team Integrator policy and the inventory/cleanup negative matrix. |
| Collaboration schema/sample checks | PASS, 2/2. |
| Python compile checks for new Core/CLI/tests | PASS. |
| `python -m json.tool packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json` | PASS. |

The W3 suite includes positive and negative cases for stable JSON/exit codes, merge/rebase dry-run, dirty integration worktree, merge conflict, validation failure, Candidate State drift, missing and conflicting ADR handling, missing human review, AI-only rejection, four review actions, critical-input drift, cleanup invalidation, bounded legacy/unknown inventory, active task, benchmark/recovery retention, path escape/reparse, unique commits, unknown untracked/ignored, sensitive ignored files, independent authorization, zero-delete, Git-private evidence, Core zero-network behavior, and author worktree preservation.

## W3 checkpoint validation

| Command／procedure | Result |
| --- | --- |
| `python -X utf8 -m unittest -v tests.test_collaboration_contract tests.test_collaboration_w3 tests.test_authority_model_migration tests.test_authority_model_restore tests.test_codex_adapter` | PASS — 83/83 in 486.132 seconds; covers W1/W2 collaboration regression, all W3 inventory/cleanup safety paths, adjacent schema migration/restore and Codex adapter contracts. |
| Post-checkpoint closure-v2 conditional-schema focused rerun: schema bundle + closure cleanup + independent authorization/receipt | PASS — 3/3 in 53.790 seconds after the conditional required-field rule was placed on `closure-record`. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated candidate; Authority Model 1 supported and strict-evaluation eligible. |
| `python -X utf8 scripts/docsite/build_docsite.py --out C:\Users\1\AppData\Local\Temp\project-orrery-w3-final\index.html` | PASS — isolated `1495496`-byte site; tracked `docs/_site` remains absent. |
| PowerShell local Markdown-link scan over `rg --files -g '*.md'` | PASS — 336 Markdown files／859 local links; one expected synthetic missing target in the D1 positive fixture, zero unexpected missing. |
| High-confidence private-key／token scan and forbidden tracked-artifact inventory | PASS — zero secret matches; zero tracked `ai-config.json`, cache, `.port`, generated docsite, Python cache, keyring or external benchmark artifacts. |
| `git diff --check` | PASS for the final implementation and documentation diff. |

The validation policy was tightened for efficiency after implementation: W3 branch delivery uses the focused
and checkpoint evidence above. Default/dynamic full-repository, isolated docsite, complete link scan and the
Windows/Ubuntu exact-SHA matrix are the central integrator's one-time gates for the clean W3+W4 integration
candidate. The already completed local docsite/link/safety results remain supplemental evidence and were not
rerun after that policy change.

Before the policy change and before the inventory/cleanup-contract increment, a complete default repository run
passed 287 tests (282 passed, 5 existing optional-dependency／Windows privilege skips). A prior dynamic run also
predates the final validation-set freshness assertion and inventory increment. A later dynamic run was deliberately
interrupted when the policy changed; it had passed the then-current W1/W2 and W3 collaboration tests and was in
the context-routing tests, but has no full-suite conclusion. None of those earlier full-suite observations is
claimed for the current 0.1.7／0.1.12 Worktree Candidate; the 83-test checkpoint above is the current acceptance
evidence pending the central clean W3+W4 integration candidate.

## Known boundaries

- This is local Windows Candidate evidence, not a commit, Canonical integration, remote Windows/Ubuntu promotion result, release or support claim.
- The dry-run runner itself performs no fetch and Core review computation performs no network. User-declared validation executables remain caller-controlled external processes.
- Cleanup output is conservative advice. Remote-branch cleanup always requires external evidence and a separately authorized action.
- Existing historical worktrees/clones, screenshot/output directories and the repository-external benchmark were not independently inventoried or declared cleanup-eligible by this validation. Unknown remains Unknown until a bounded explicit candidate and policy are supplied.
- No closure for this Candidate was created because W3 was not actually integrated into main.
