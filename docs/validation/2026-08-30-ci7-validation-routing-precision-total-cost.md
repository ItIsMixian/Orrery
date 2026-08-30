# Validation: CI7 Validation Routing Precision & Total-Cost Diagnostics

Date: 2026-08-30

Status: local Worktree Candidate PASS; clean exact-SHA hosted Promotion remains central integration work

Fact scope: `codex/ci7-validation-routing-precision-total-cost`, exact base
`3fc7e7aacedafa8fbd20f9f79ddb8cf5784a0ef3`. Implementation and validation used GPT-5.6 Sol with medium reasoning.
No A4.1/W7.3 worktree was read or written.

## Routing contract

- Actual changed paths are primary. Narrow expected writes are used only without an actual path; subsystem metadata
  is the final conservative fallback. Directory-wide `**`, unsafe declarations, unmapped paths and mapping overlap
  return non-evidence refusal receipts with required metadata.
- The former `observatory-ui` is split into provider-neutral `observatory-shell`, `observatory-graph`,
  `observatory-maintenance` and `observatory-team-personal`; production registry data contains no task or branch ID.
- Frozen portfolio result:

| Portfolio | CI6 before | CI7 after | Safety result |
| --- | --- | --- | --- |
| W7.2 Graph-only | `collaboration-maintenance` + `observatory-ui`; 23 Checkpoint | `observatory-graph`; 2 Checkpoint | Maintenance real-Git fixture changed from selected to absent |
| U2.2 Maintenance | coarse mixed UI/maintenance | four precise mappings; 22 Checkpoint | real-Git incremental/Quick Remove fixture remains selected |
| Unified common security | coarse all-UI | `observatory-shell`; 4 Fast | bounded Unified + Personal + Graph fail-closed adjacency |
| Authority/A4-class live paths | `authority-core` | `authority-core` | no unintegrated A4 file is required |

The before result was mechanically evaluated from the exact-base registry; after results used the same generic
selection algorithm and current integrated files. Missing/duplicate/overlap mapping, unknown path/dependency, broad
expected-write, forged usage and ROI-as-gate mutations fail closed.

## Receipt diagnostics

`cost_diagnostics` schema 1 is additive and explicitly `non-authoritative-advisory`. It records selected count, test
runtime, router/setup wall, reruns, slow IDs, changed test/CI files and lines, independent optimization Workstream,
optional future runs and simple break-even. Host agent-token/tool usage was unavailable and is exactly `Unknown`; no
token estimate was made. `gate_effect` is always `none`.

One real Fast sample selected 25 tests, ran them in 5.009717s, spent 3.620797s in router/setup, recorded zero reruns,
2 changed test files/155 changed lines and 4 changed CI files/724 changed lines. A maintainer-supplied diagnostic
example used 12s baseline, 30s optimization investment and 20 expected future runs: saving 6.990283s/run,
break-even 5 runs, projected net saving 109.805660s. Both the saving and the 30s investment are shown; this example
is not an ROI gate or forecast fact.

Over-budget diagnostics distinguish product failure, router over-selection, fixture/runtime variance and genuinely
slow paths. A Git-private counter permits one bounded feature-task triage attempt. A recurrence finding appears only
when the same fingerprint affects a second distinct Workstream; it creates no task, ADR, State or relation fact.

## Local evidence

| Check | Result |
| --- | --- |
| focused CI7 contract/portfolio | 5/5 PASS |
| complete `tests.test_ci_validation` | 25/25 PASS |
| `validate_ci.py --all` | PASS |
| routed Fast on final development tree | 42/42 PASS; 8.057895s / 15s |
| routed Checkpoint on final development tree | 42/42 PASS; 7.526136s / 90s |
| Promotion inventory | 421 exact final IDs, each once; 27 logical shards; 10 lanes; 92 Fast; 98 Checkpoint |
| workflow/manifest text against exact base | byte-equivalent; required checks and lane graph unchanged |
| complete local Promotion | intentionally not run as a development loop |

Repository structure, workflow/YAML/static contract, links/forbidden artifacts, secret boundaries and diff gates are
run again on the clean Candidate recorded in the task receipt. Fast/Checkpoint/Candidate/Promotion meaning, 15/90
second budgets, failure/timeout semantics, exact-SHA binding and Windows/Ubuntu required-check names are unchanged.

## Remaining central integration work

The central integrator must additively reconcile any newly integrated paths from parallel A4.1/W7.3 without making
their unintegrated files required here, refresh the Git-private session at the final commit, rerun clean Candidate
Fast/Checkpoint, push that exact non-main SHA and obtain both hosted required checks. This branch does not push,
promote main, change a component/public release, or edit root PROGRESS/HANDOFF.
