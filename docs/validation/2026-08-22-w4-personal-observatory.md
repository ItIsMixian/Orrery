# Validation：W4 Personal Observatory Worktree Candidate

Date: 2026-08-22—2026-08-23
Status: Candidate validated

Governing decisions: [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md)

Approved Design: [多人／多 worktree 协作协议](../design/multi-worktree-collaboration-protocol.md)

Implementation Plan: [多 worktree 协作协议](../implementation/plans/2026-08-19-multi-worktree-collaboration-protocol.md)

## Scope and fact boundary

- Worktree: `C:\Users\1\.codex\worktrees\da1c\project-orrery`
- Branch: `codex/w4-personal-observatory`
- W4A base/freeze: `main@ef488715dee369cbce81806f3040b4c0417d3eb8` → local commit `335f10a04e566935da234b19f86cbd280c936e18`.
- Canonical W3 base: `main@7932a9c01efb2e5125da1962873e67383982d98c`; exact merge commit `9ab852281bb64a9aa97c9ae021a5376c6e9907f9` preserves W4A history.
- W4B implementation: local commit `2b9b55643bbb616bfff57be7f4380433dcf81927`.
- Excluded-worktree isolation fix: local commit `e5a198e722f28b8b2d84b1806110a0a448c85d73`; an explicit exclusion prevents the automatic W3 provider from running and returns `IsolationBoundary / Unavailable`.
- Fact scope: committed local Worktree Candidate; local commit was authorized, but no push, PR, main merge, tag, Release or W5 work was authorized.
- W3 boundary: W4A previously excluded the parallel W3 branch before reading it. W4B does not open the old W3 worktree and only consumes the Core／CLI／Git-private contracts present in Canonical main.

The Candidate now contains Observatory 0.1.2 and the root-only opt-in builder. It delegates identity, Git status, lifecycle, Scope and overlap semantics to W1/W2, and review freshness／risk／human approval／integration eligibility／workspace inventory／cleanup eligibility to W3 Core. Closure and action receipt files are consumed only through the W3 inventory/closure bundle and remain evidence, not execution proof. The normal builder, local dynamic service, Authority projection, AI Q&A, Skill template, managed-tool inventory and public v0.2.0 behavior are unchanged.

## Product boundaries verified

- The projection reports `read_only=true`, `writes_performed=false`, `network_performed=false` and `team_runtime_enabled=false`.
- The Personal surface is a dedicated `page` sibling selected from the existing sidebar; it is not nested in or rendered on the overview dashboard. It has no forms, product action buttons, `onclick` handlers or `fetch` calls. Native `details` disclosure is the only W4 interaction.
- W3 review queue is discovered only from bound Workstream `review_package_id` values; W4 calls W3 package loader, freshness and integration eligibility instead of scanning paths or reproducing risk/approval rules. Target OID、candidate HEAD、Scope binding、blockers and human approval counts come from those bundles.
- Workspace inventory is the W3 bounded seven-class report. W4 does not infer ownership or cleanup from directory name, prefix or age. Only entries whose Core `recommended_action` is `evaluate-cleanup-eligibility` are passed to the W3 cleanup gate; four actions stay independent and automatic projection requires `authorized=false`、`performed=false`、`implies_actions=[]`.
- Missing/failed/incompatible W3 providers render Unavailable／Unknown while the W1/W2 W4A page remains available. An absent review package is an empty local queue, not a fabricated approval or integration conclusion.
- Closure and caller-attested action receipts expose their evidence bindings. Neither a closure nor `performed=true` inside a caller-attested receipt is rendered as proof that Orrery deleted a path or branch.
- Missing session, inaccessible/excluded worktree and remote/unreported evidence remain Unknown／Unavailable. An empty local finding set is rendered as “No local finding; remote and unreported work remain Unknown”, never as zero global conflict.
- Lifecycle phase, runtime condition and evidence freshness render as three separate tracks. Agent-reported completion is not consumed as Review Ready, Integrated or Closed.
- The final real snapshot contained 34 visible local worktrees and 35 W1/W2 findings, but only 2 worktrees had a session whose lifecycle had not reached `integrated`／`closed`; those 2 render as active Workstreams. The other 32 worktrees render in a collapsed local inventory. These counts are environment-local evidence, not Canonical project facts.
- The current presentation is question-first rather than schema-first: “项目现在怎么样／先看这些／谁在推进什么／影响到哪里” are the primary reading path. The current-focus sentence and four signals are deterministic renderings of W1/W2 fields. Trend remains `Unknown · 无历史快照`; delivery eligibility now reflects W3 Core or explicitly says no bound review package／provider unavailable. Git OIDs, package hashes, path evidence, seven-class inventory, cleanup actions and closure receipts remain in collapsed technical evidence.

## Automated verification

| Command | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_personal_observatory -v` | W4B PASS after the exclusion guard — 12/12 in 99.481 s, including a real W3 Core review package consumed by W4, bounded inventory, four-action separation, receipt non-inference, provider/schema fallback, zero-network/read-only and all W4A presentation boundaries. |
| `python -X utf8 -m unittest tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection -v` | PASS — Observatory 0.1.2 package/component/root version projection agrees. |
| Earlier W4A affected-product checkpoint | PASS — 44 total, 42 PASS + 2 expected dynamic-dependency skips before the W3 projection was added. It was not rerun during the W4B UI loop. |
| Earlier W4A default／dynamic full-repository runs | PASS on the initial W4A Candidate before the separate-page revision — default 282 PASS + 5 skips; dynamic 284 PASS + 3 Windows privilege skips. They were not rerun for W4B; the central joint Candidate owns the final full suite. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid; Authority status `integrated candidate`, model 1 supported. |
| Legacy isolated docsite build | PASS — 1506 KB, 13 ADR, 6 State, 7 subsystem, 116 docs; output remained outside Git. |
| Personal + Authority explicit opt-in composition | PASS — 1653 KB; personal projection `ready`, Authority projection `composed`; explicit W3 exclusion produced `IsolationBoundary / Unavailable` without running the automatic provider. |
| PowerShell local Markdown link scan | PASS — 336 Markdown files, 863 local links, zero unexpected missing; the single missing target is D1's frozen documentation-governance positive fixture. |
| High-confidence secret／release-forbidden tracked artifact scan | PASS — 0 secret files, 0 forbidden tracked artifacts. |
| `git diff --check` | PASS — no whitespace error; Git emitted only working-copy LF→CRLF notices for three existing JSON/TOML files. |

The focused collector tests patch `socket.socket`／`socket.create_connection` to fail, compare author-tree Git status before/after, and use W3 Core itself to generate a real review package before W4 consumes its freshness、risk、approval、eligibility and binding. The exclusion regression makes both `inspect_worktree_status` and the automatic W3 provider fail if either crosses the explicit boundary; the final 12/12 run includes that guard. One implementation-agent collaboration combination run was stopped after roughly ten minutes because it exceeded the approved Fast scope; it is recorded as interrupted and was not rerun or counted as passing evidence.

The first W4B diagnostic static build exposed that the W1/W2 exclusion guarded the worktree collector but did not yet suppress the newly added automatic W3 provider. That build was rejected as evidence and overwritten. Commit `e5a198e` added the provider-level isolation guard; the final real build and browser evidence below were generated only after that fix.

## Browser verification

Browser: Codex in-app Chromium via loopback-only `python -m http.server`; the temporary server was stopped after testing. The existing legacy page attempted its normal `/briefing` loopback request, which returned 404 under the static server; no external request or W4 Team transport was added.

| State／viewport | Result |
|---|---|
| Overview → Personal navigation | Overview initially contains no Personal panel. Clicking the sidebar entry selects `#personal-observatory`; dashboard display becomes `none`, Personal display becomes `block`, and DOM inspection confirms the two are sibling pages rather than nested content. |
| Final real W1/W2 snapshot, desktop | Dedicated Personal page contains the plain-language current focus, four project signals, five priority explanations and two active Workstream rows; 32 other worktrees and all Git evidence remain collapsed. Explicit old-W3 exclusion renders W3 Unavailable and the old W3 branch is absent from the active Workstream text. No form, product button or external anchor; `scrollWidth=1265`, equal to viewport width. |
| Representative stable W3 bundle, desktop | Native details expose one pending/current review package, elevated risk, approval 0/1, Core blocker, target/candidate/Scope binding, all seven inventory classes, protection/Unknown/4.0 KB estimate, and all four actions with independent `eligible` plus `authorized=false`／`performed=false`／`implies=[]`. Receipt text says caller-attested and `deletion inferred=false`. |
| Narrow 390×844 | Representative W3 page keeps the project signals in a 2×2 grid. Technical vault and both evidence records remain interactive; `clientWidth=scrollWidth=375`, with no form or product action button. |
| Provider failure／old-schema fallback | The W1/W2 human briefing remains present while all three W3 slots say `UNAVAILABLE` and `Unknown`; no form, action button or horizontal overflow. No-Workstream／no-finding behavior remains covered by the focused fixture. |

Artifacts (outside Git):

- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4b-legacy-docsite.html`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4b-personal-observatory-real.html`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4b-personal-observatory-real.json`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4b-personal-observatory-representative.html`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4b-personal-observatory-representative.json`
- `C:\Users\1\.codex\visualizations\2026\08\22\01a0294f-ab89-7f33-a6ee-d3273a04f18c\w4b-personal-observatory-provider-fallback.html`

## Remaining boundaries

- W3 review／integration／cleanup Core and CLI are present only because Canonical main was merged. W4 consumes them read-only and neither copies nor executes their policy.
- Team Mode, Member aggregation, Coordinator／LAN discovery, telemetry, requests, heartbeat and platform launch／rebind／message are not implemented.
- The Candidate is root-only and opt-in. It is not in the managed-tool inventory or public template and has no default production switch.
- This Windows Worktree evidence is not Canonical integration, cross-platform CI or release evidence. Candidate-first Windows／Ubuntu checks are required before any later main promotion.
