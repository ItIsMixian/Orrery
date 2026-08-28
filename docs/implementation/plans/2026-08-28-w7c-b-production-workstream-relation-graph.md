# 实施计划：W7C-B Production Workstream Relation Graph Observatory

Status: Completed Worktree Candidate

Date: 2026-08-28

Fact scope: `codex/w7c-b-production-workstream-relation-graph`, parent/task base
`W7A-dynamic-workstream-succession-contract@52e88b8e15788eb7b17161e61885e9198d29407c`

Visual input: `codex/w7c-a-workstream-graph-visual-prototype@a39f6a701ef39e6bb3eb3b7ec05a9b5dc7416ef1`
(provisional/non-authoritative)

Governing decision and design: [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md) |
[Dynamic Workstream Succession Contract](../../design/dynamic-workstream-succession-contract.md)

## Goal and boundaries

Ship a root-only, default-off Observatory sibling page that renders the W7A Core v1
`workstream-relation-graph` and `workstream-succession-plan` without recreating Git/session/relation semantics in
the browser. Keep the page read-only, zero-network and fail-closed. Preserve default docsite, Skill template,
managed-tool/release manifests and public v0.2.0 behavior.

W7C-B does not execute apply/undo, mutate relation/session stores or author documents, scan Git in the frontend,
control Agents, delete workspace objects, change Team authority, push, merge `main`, change protection, tag or
release. The sibling W7B Candidate already implements local discovery, exact planning, human-local confirmation,
apply/recovery/receipt/undo in isolated fixtures; it remains the only execution boundary, while self-host apply,
default UI execution wiring and public release have not occurred.

## Compact design brief

- **Purpose/user:** let a maintainer inspect succession, dependency and evidence-backed conflict while retaining
  exact Unknown/stale/proposed and compare/suppress explanations.
- **Context/tone:** dense analyst workspace with editorial restraint, adjacent to Personal/Team Observatory;
  quiet neutral surfaces, hard dividers and mono evidence details rather than dashboard cards.
- **Memorable interaction:** one fact set, three lenses; desktop uses inline SVG plus a persistent inspector, while
  390 px uses the same ordered facts as a vertical accessible ledger/timeline.
- **State system:** independent lifecycle, runtime, evidence freshness, Scope, subsystem, visibility and
  observability labels; waiting/paused/blocked/failed never receive active-tip treatment. Shape, text and line style
  redundantly encode state; focus-visible and reduced-motion are mandatory.
- **Constraints:** dependency-free projection, deterministic DOM/order, no horizontal overflow, safe Core-owned
  source links only, and a complete Unavailable/Unknown fallback that preserves page navigation and the list.

## Implementation phases

1. **Absorb the visual evidence additively.** Import W7C-A experiment assets and Validation from exact SHA
   `a39f6a7`; keep its fixture and fields explicitly provisional. Resolve shared State/DEVLOG/index content by
   addition without dropping W7A corrections.
2. **Freeze the Observatory consumer.** Add a versioned root-only provider that accepts only Core/CLI
   `workstream-relation-graph` plus `workstream-succession-plan`, validates provider/schema/version/root/node/edge/
   source-link integrity, and returns one all-or-unavailable projection. No browser Git/session inference.
3. **Build the sibling page.** Implement Succession/Dependency/Conflict lenses, deterministic active tips,
   consumer-side history folding, Unknown/stale/proposed/confirmed-conflict encodings, compare/suppress reasons,
   filters, keyboard selection, node/edge inspector and safe evidence navigation. Desktop uses inline SVG; mobile
   uses a ledger/timeline. Expose only via an explicit root-only script/flag.
4. **Protect adjacency and release boundaries.** Add corrected W7A real/provisional mapping, runtime-state,
   multi-predecessor, invalid/provider-failure/unsafe-link, zero-network/read-only and Personal/Team adjacency tests;
   bump only the unreleased Observatory component and CI1 inventory/shard declarations.
5. **Validate and document.** Run Fast during implementation, then one Checkpoint covering focused/adjacent tests,
   CI inventory/contract, repository structure, isolated docsite, local links and diff. Complete real in-app Chromium
   checks at 1280 px and 390 px with click, keyboard, console, overflow and screenshots. Update affected State,
   Validation, DEVLOG and indexes; do not edit root PROGRESS/HANDOFF.

## Fail-closed acceptance

- Unsupported/invalid provider, schema or version; missing relation root; dangling node/evidence; legacy Unknown;
  Core/provider failure; or unsafe source link produces no partially trusted graph.
- The page and accessible list remain reachable and label the projection `Unavailable`/`Unknown`, with diagnostics
  that expose no absolute Git-private path, credential, prompt/answer/transcript, source body or unpushed diff.
- No controls imply apply, undo, close, delete, merge or remote execution. Team remains central read-only/request-only.

## Validation ladder

- **Fast:** focused Observatory tests, JS syntax, provisional fixture boundary, corrected W7A mapping and direct
  failure cases.
- **Checkpoint:** W7A relation, W7C-A prototype, Personal/Team adjacency, CI inventory/contract, structure,
  isolated docsite, links, diff and in-app Chromium desktop/mobile acceptance.
- **Not run here:** full Promotion, hosted required checks, push, `main` merge, tag or Release.

## Documentation mapping

Completion updates `docs/state/{project-structure,documentation-system,release-and-toolchain,test-coverage}.md`,
`docs/validation/2026-08-28-w7c-b-production-workstream-relation-graph.md`, `docs/validation/README.md`,
`docs/implementation/README.md` and `docs/DEVLOG.md`. Shared State/DEVLOG/index edits remain Candidate-scope
integration conflicts for the unique integrator; root `docs/PROGRESS.md` and `docs/HANDOFF.md` stay untouched.

## Outcome

Implemented as Observatory 0.1.9 on the exact corrected W7A base and imported exact W7C-A visual evidence. The
root-only page consumes provider/graph/plan schema 1, fails closed as one projection, preserves independent state
axes and exposes no execution surface. Focused 13/13, Fast 50/50 and W7A/W7C-A/Personal/Team Checkpoint 45/45
passed; structure, CI contract, installation, isolated docsite, repository links and real 1280px/390px Chromium
acceptance passed. Hosted Promotion, push and main integration remain outside this plan; W7B execution is present
only in its sibling Candidate and is deliberately not wired into this read-only page.
