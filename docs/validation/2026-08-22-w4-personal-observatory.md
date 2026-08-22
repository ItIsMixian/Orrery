# Validation：W4 Personal Observatory Worktree Candidate

Date: 2026-08-22
Status: Candidate validated

Governing decisions: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

Implementation Plan: [多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)

## Scope and fact boundary

- Worktree: `C:\Users\1\.codex\worktrees\da1c\project-orrery`
- Branch: `codex/w4-personal-observatory`
- Base: `main@ef488715dee369cbce81806f3040b4c0417d3eb8`
- Fact scope: uncommitted Worktree Candidate; no commit, push, PR, merge, tag or Release was authorized.
- W3 isolation: the real build passed `--exclude-branch codex/w3-review-integration-cleanup`. The shared Git worktree registry made the branch name/path visible, but the W4 collector did not open that worktree, its private session or implementation. Its card remains `Unavailable / excluded-worktree-contract-not-integrated / evidence Unknown`.

The Candidate adds an internal Observatory 0.1.1 projection and root-only opt-in builder. It delegates identity, Git status, lifecycle, Scope and overlap semantics to the already Canonical W1/W2 functions in `project_orrery_core.collaboration`; W4 only aggregates and escapes display data. The normal builder, local dynamic service, Authority projection, AI Q&A, Skill template, managed-tool inventory and public v0.2.0 behavior are unchanged.

## Product boundaries verified

- The projection reports `read_only=true`, `writes_performed=false`, `network_performed=false` and `team_runtime_enabled=false`.
- The Personal surface is a dedicated `page` sibling selected from the existing sidebar; it is not nested in or rendered on the overview dashboard. It has no forms, product action buttons, `onclick` handlers or `fetch` calls. Native `details` disclosure is the only W4 interaction.
- W3 review queue, integration eligibility and cleanup eligibility are optional display slots only. With no integrated W3 provider all three render `Unavailable / W3 not integrated`; W4 implements no W3 business decision.
- Missing session, inaccessible/excluded worktree and remote/unreported evidence remain Unknown／Unavailable. An empty local finding set is rendered as “No local finding; remote and unreported work remain Unknown”, never as zero global conflict.
- Lifecycle phase, runtime condition and evidence freshness render as three separate tracks. Agent-reported completion is not consumed as Review Ready, Integrated or Closed.
- The real snapshot contained 31 visible local worktrees and 32 W1/W2 findings, but only 2 worktrees had a session whose lifecycle had not reached `integrated`／`closed`; those 2 render as active Workstreams. The other 28 no-session worktrees and 1 excluded W3 worktree render in a collapsed local inventory. These counts are environment-local evidence, not Canonical project facts.
- The current presentation is question-first rather than schema-first: “项目现在怎么样／先看这些／谁在推进什么／影响到哪里” are the primary reading path. The current-focus sentence and four signals are deterministic renderings of W1/W2 fields. Trend remains `Unknown · 无历史快照`; delivery eligibility remains `Unavailable · W3 未集成`. Git OIDs, W3 slots, path evidence and inventory are contained in a collapsed technical-evidence section.

## Automated verification

| Command | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_personal_observatory -v` | PASS — 9/9 after the separate-page revision; W1/W2 reuse, no network/write, exclusion without worktree open, active／worktree-only／unavailable grouping, dashboard byte-content isolation, sidebar page navigation, Unknown/Unavailable, W3 fallback, read-only renderer, separated state tracks, HTML escaping, legacy fallback and mobile CSS. |
| `python -X utf8 -m unittest tests.test_personal_observatory tests.test_project_orrery tests.test_authority_observatory_projection tests.test_authority_observatory_managed_shadow tests.test_cli_wheel_installation -v` | PASS — 44 total, 42 PASS + 2 expected dynamic-dependency skips. |
| `python -X utf8 -m unittest discover -s tests -v` | PASS on the initial W4 Candidate before the separate-page presentation revision — 287 total, 282 PASS + 5 existing optional-dependency／Windows privilege skips; 742.628 s. |
| `ORRERY_TEST_BUILD=1; python -X utf8 -m unittest discover -s tests -v` | PASS on the initial W4 Candidate before the separate-page presentation revision — 287 total, 284 PASS + 3 Windows symlink privilege skips; 734.535 s. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid; Authority status `integrated candidate`, model 1 supported. |
| Legacy isolated docsite build | PASS after the human-brief revision — 1467 KB, 13 ADR, 6 State, 7 subsystem, 114 docs; output remained outside Git. |
| Personal + Authority explicit opt-in composition | PASS after the human-brief revision — 1505 KB; personal projection `ready`, Authority projection `composed`; W3 branch excluded before worktree read. |
| PowerShell local Markdown link scan | PASS — 336 Markdown files, 863 local links, zero unexpected missing; the single missing target is D1's frozen documentation-governance positive fixture. |
| High-confidence secret／release-forbidden tracked artifact scan | PASS — 0 secret files, 0 forbidden tracked artifacts. |
| `git diff --check` | PASS — no whitespace error; Git emitted only working-copy LF→CRLF notices for three existing JSON/TOML files. |

The focused collector test patches `socket.socket` to fail, builds two linked Workstreams through the existing W1 session writer, observes W2 Direct findings and compares all author-tree Git status before/after. A separate exclusion test raises if the excluded branch path is passed to `inspect_worktree_status`, proving that the isolation slot is not merely filtered after reading.

## Browser verification

Browser: Codex in-app Chromium via loopback-only `python -m http.server`; the temporary server was stopped after testing. The existing legacy page attempted its normal `/briefing` loopback request, which returned 404 under the static server; no external request or W4 Team transport was added.

| State／viewport | Result |
|---|---|
| Overview → Personal navigation | Overview initially contains no Personal panel. Clicking the sidebar entry selects `#personal-observatory`; dashboard display becomes `none`, Personal display becomes `block`, and DOM inspection confirms the two are sibling pages rather than nested content. |
| Real W1/W2 snapshot, 1440×1000 | First viewport contains the plain-language current focus, four project signals, all five priority explanations and both Workstream rows; 29 non-active worktrees and all W3/Git evidence remain collapsed. No form/action button; `scrollWidth=1425 < 1440`. |
| Workstream／technical evidence interaction | Native details opened for the first Workstream and the technical-evidence vault; the latter contains three W3 slots and the closed 29-row inventory. Workstream evidence exposes integration OID, merge base, HEAD, ahead/behind, capture time, worktree path, findings/ack and source-tagged Scope paths. |
| Narrow 390×844 | Brief signals form a 2×2 grid; Workstream summaries form a true two-column mobile grid; legacy search folds while theme remains visible. Workstream and technical evidence both open without overflow; final `scrollWidth=375 < 390`. |
| No Workstream／no local finding fixture | Visible “No active Workstream · Unknown”, “No local finding; remote and unreported work remain Unknown”, all W3 slots Unavailable and zero product buttons. |

Artifacts (outside Git):

- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4-legacy-docsite-final.html`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4-personal-observatory-human-brief.html`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4-personal-observatory-human-brief.json`

## Remaining boundaries

- W3 review／integration／cleanup Core and CLI remain absent from this branch. W4 neither copies nor predicts them.
- Team Mode, Member aggregation, Coordinator／LAN discovery, telemetry, requests, heartbeat and platform launch／rebind／message are not implemented.
- The Candidate is root-only and opt-in. It is not in the managed-tool inventory or public template and has no default production switch.
- This Windows Worktree evidence is not Canonical integration, cross-platform CI or release evidence. Candidate-first Windows／Ubuntu checks are required before any later main promotion.
