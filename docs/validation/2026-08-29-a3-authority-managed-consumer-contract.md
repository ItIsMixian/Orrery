# 2026-08-29 A3 Authority Managed Consumer Contract

Status: PASS — Worktree Candidate only

Date: 2026-08-29

Branch: `codex/a3-authority-managed-consumer-contract`

Baseline: protected `main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`

Workstream: Git-private `A3-authority-managed-consumer-contract`

Plan: [A3 Authority Managed Consumer Contract](../implementation/plans/2026-08-29-a3-authority-managed-consumer-contract.md)

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

Environment: Windows, Python 3.13.5, local filesystem/Git only; no publish, `main` push, external network,
user-level installation or release mutation.

## Validated contract

Core now owns the internal `authority-managed-consumer-v1` selection/readiness/rollback evaluator and bundled JSON
schema. Its input is provider-neutral and contains only exact conformance bindings and component health observations;
Markdown/Git collection, rendering and Coordinator runtime remain outside the evaluator.

The contract distinguishes:

| Requested/effective state | Current active consumer in A3 | Meaning |
|---|---|---|
| `legacy` | legacy | default; no managed rollout |
| `shadow` | legacy | collect/evaluate without a claim page |
| `candidate-projection` | legacy | opt-in Candidate projection; default remains legacy |
| `enabled` | legacy until a later apply receipt | rollout target is ready, not already applied |
| `rollback` | legacy | explicit or runtime failure recovery |
| `unavailable` | legacy | unsupported model, forbidden selector or unsafe preflight |

Every result binds public model version, internal evaluator model ID, repository snapshot, fact scope, ordered evidence
visibility, exact collector/evaluator/projection versions, expected/observed source hashes and expected/observed
reconciliation hashes. Content-addressed rollout and rollback plans bind the same `binding_hash`; identical inputs
produce identical contracts and plan hashes.

`enabled` readiness requires an exact supported model, Canonical scope, matching versions/hashes, complete render and
all non-escalation invariants. `Unknown`／Local-only cannot become enabled. AI／Coordinator selection and safety
escalation both fail closed even when every other input is green.

Collector/evaluator/projection failure, component version drift, source drift, reconciliation drift, partial render or
partial claims produce a deterministic rollback target. The plan requires complete-page-or-legacy atomicity; it never
permits a partial managed claim page. Rollback flags `writes_author_documents=false`, `network_required=false` and
`modifies_release=false`.

## CLI and U1 join contract

The unreleased unified source CLI adds:

```text
project-orrery authority-consumer inspect --target <root> --fact-scope <scope> --json
project-orrery authority-consumer readiness --target <root> --selection <state> \
  --selection-authority maintainer-explicit --fact-scope <scope> --json
```

Both use the existing stable CLI JSON envelope. `inspect` always requests `legacy` through `system-default`.
`readiness` returns only the bounded A3 contract, component health, blockers and deterministic plans; it explicitly
reports `normalized_observations_exposed=false` and does not return the M2.1 document／observation payload.

U1 may consume `contract_type`, `contract_hash`, `binding_hash`, `selection`, `readiness`, `rollout_plan` and
`rollback_plan`. `rollout_ready=true` means only that the exact enabled target passed A3 preflight;
`switch_authorized` remains false and `maintainer_enable_decision` remains pending. U1 must continue to show legacy as
current until a future maintainer-owned executor produces a separately designed exact-plan apply receipt. U1 must reject stale hashes, unexpected versions, non-ready selection,
AI／Coordinator authority and any plan whose offline/no-author-write/no-release guarantees differ. Execution failure
must discard staged managed output and follow the hash-bound rollback plan before rendering legacy.

A3 does not implement that executor or receipt, modify U1 shell/navigation, choose the default, or make a maintainer
enable decision.

## Verification evidence

| Check | Result |
|---|---|
| A3 focused contract/CLI tests | PASS — 7/7. |
| JSON Schema Draft 2020-12 check + healthy contract validation | PASS — schema valid and generated Core contract conforms. |
| A3 + M2.2 projection + AI derived-view adjacency | PASS — 25/25. |
| Authority M2.1/M2.2/compatibility adjacency | PASS; one existing Windows symlink-privilege skip where selected. |
| CI contract and inventory | PASS — 397 unique test IDs, 27 shards, 10 lanes; A3 assigned once to `authority-core`. |
| Fast profile | PASS — 64/64 in 3.939079s under the unchanged 15s budget. |
| Checkpoint profile | PASS — 88/88 in 27.003516s under the unchanged 90s budget. |
| Full repository suite with `ORRERY_TEST_BUILD=1` | PASS — 397 tests in 2508.583s; 3 existing environment skips. |
| Integrated structure | PASS — integrated candidate, Authority Model 1 supported and strict evaluation eligible. |
| Isolated legacy A/B + projection-disabled build | PASS — all three outputs byte-identical after a readiness inspection. |
| Isolated explicit projection build | PASS — projection `ready`, Candidate marker present, no production-switch marker. |
| repository links／forbidden gates | PASS — 676 paths, 364 Markdown files, 914 local links, no forbidden runtime/generated artifacts. |
| release/parallel-area diff boundary and `git diff --check` | PASS — no README/assets, maintenance, Personal/Team server/navigation, start script, unified UI, v0.2.0, release input or Adapter status change. |

After the full suite, final diff review tightened the nested JSON schema, changed enabled output to
`rollout_ready=true`／`switch_authorized=false`／maintainer decision pending, and bound observed collector/projection
versions to their running component constants. The A3 7/7 suite, Draft 2020-12 validation, CI contract,
integrated structure, isolated builds, repository gates and diff checks were rerun after those refinements.

The first adjacent command named a nonexistent AI test module and failed before product execution. It was corrected to
the real `tests.test_authority_ai_derived_view` module; the corrected focused run and full suite both passed. This
command-list error is not counted as product Validation.

## Frozen boundaries and remaining decision

- Current/public/default consumer remains legacy. A3 only evaluates a requested target and never applies it.
- M2.1 normalized observations remain an internal boundary; no stable top-level Core/domain parser API is exported.
- No next SemVer, candidate manifest, Release, installer default, release asset, component version or Adapter support
  status was selected or changed.
- The maintainer must separately decide whether to enable the managed consumer. That decision must precede any U1
  executor/apply receipt and remain separate from a later release/version decision.
- Promotion to `main` still requires the exact Candidate SHA on a non-main ref plus Windows/Ubuntu required-check PASS;
  this local Worktree Validation is not hosted Promotion evidence.

## Central integration replay checklist

The feature branch intentionally leaves shared documents untouched. After clean integration, the unique integrator
should replay only the resulting Canonical facts:

1. update `docs/state/authority-meta-model.md` with the managed consumer contract and remaining default-enable gap;
2. update `docs/state/test-coverage.md` with A3/CI coverage and exact integrated evidence;
3. append `docs/DEVLOG.md` and add this Validation to `docs/validation/README.md`;
4. update the parent Authority active Plan implementation mapping/checkpoint status;
5. update `AGENTS.md` Authority current-fact sentence if A3 enters Canonical source;
6. update root `docs/PROGRESS.md`／`docs/HANDOFF.md` only from the integration worktree and only if the global control
   point or risks changed.
