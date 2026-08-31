# Validation: CI7 Validation Routing Precision & Total-Cost Diagnostics

Date: 2026-08-30

Status: PASS (CI7 feature Candidate); Phase 0 revision-10 portfolio rollback and new-fingerprint evidence remain Pending

Fact scope: `codex/ci7-validation-routing-precision-total-cost`, exact base
`3fc7e7aacedafa8fbd20f9f79ddb8cf5784a0ef3`. Implementation and validation used GPT-5.6 Sol with medium reasoning.
No A4.1/W7.3 worktree was read or written.

Amendment authority is task-description commit `a67b8c61243ab6141fd7a94af4cc2d98cdf0c1e9`: Plan blob
`32428b78768b348a350a2554fbf0c98790ab33fe` and this Validation's pre-implementation expectation blob
`e0a9892b1eea99e84bdd93adcea10f4a0ab706d1`. Git-private binding scope revision 2 records those OIDs while the
repository branch continues from retained Candidate `a520ebc74a0846c148e73312ea2fbf2a32b4b08b`.

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

One pre-amendment diagnostic sample selected 25 tests, ran them in 5.009717s, spent 3.620797s in router/setup, recorded zero reruns,
2 changed test files/155 changed lines and 4 changed CI files/724 changed lines. A maintainer-supplied diagnostic
example used 12s baseline, 30s optimization investment and 20 expected future runs: saving 6.990283s/run,
break-even 5 runs, projected net saving 109.805660s. Both the saving and the 30s investment are shown; this example
is not an ROI gate or forecast fact.

Over-budget diagnostics distinguish product failure, router over-selection, fixture/runtime variance and genuinely
slow paths. A Git-private counter permits one bounded feature-task triage attempt. A recurrence finding appears only
when the same fingerprint affects a second distinct Workstream; it creates no task, ADR, State or relation fact.

## Acceptance and lease amendment

- `acceptance_policy` schema 1 uses `all_of` composable gates across five stable kinds. Human-experience and
  operation gates cannot be closed by Agent/session receipts; operation additionally requires action-time human
  authorization. Contract, measurement and platform matrix close mechanically only with prior human approval of the
  same exact contract. Unknown kind/status, missing role/revision/scope binding, Agent self-accept and forged
  contract/receipt/fingerprint all refuse.
- Relevant fingerprints cover contract blob, mapping registry and gate-owned source/test paths. Unrelated docs are
  stable; contract, relevant source, scope revision and declared authority role changes stale the receipt. Personal
  stays zero-network and Team emits only request-only bounded gate metadata.
- Git-private validation leases bind Workstream/scope/stage/fingerprint/exact IDs/count/p95/budget/receipt inputs and
  one run. Missing, forged, expired, consumed, wrong-stage and stale leases refuse before test loading. Success is
  idempotently reused; failure/timeout is `validation-cost-blocked` and an unchanged retry needs a request-bound human
  maintainer override.
- Iterating allows only non-evidence focused runs with 20-test/20-second/120-cumulative-second caps. Fast refuses
  count above 20 or p95 above 10 seconds; Checkpoint refuses single p95 above 30 or total above 60, including the
  synthetic 95-second Maintenance portfolio. These are preflight refusals, not changed 15/90 budgets or PASS.
- Versioned profiles cover UI experience, pre-approved deterministic contract, measurement, operation authorization,
  Windows/Ubuntu matrix and mixed all-of. Review packages are bounded to 3–5 representative cases plus negative
  cases. Integration accepts child receipt references and rejects child-owned gate replay.

Amendment assertions are intentionally folded into the existing CI7 final unittest ID, so the frozen Promotion
inventory remains 421 final IDs rather than growing merely to test the router. The first malformed PowerShell focused
invocation executed no target tests and is not counted green. Corrected focused policy/lease/p95/no-repeat stable sweep
is 16/16 PASS. On clean exact SHA `290482fe7cfc502fbd32f733629c5d619736b5f4`, the unique amended Fast was
invoked once and refused before test loading because the 42-test plan exceeded the predictive 20-test limit
(`fast-selected-count-exceeds-20`). It is non-green, was not retried and cannot be substituted by Checkpoint. The
unique amended Checkpoint used the same surface fingerprint and completed its one-run lease with 42/42 PASS in
16.417209s / 90s, evidence-eligible.

## Local evidence

| Check | Result |
| --- | --- |
| focused CI7 acceptance/routing/lease stable sweep | 16/16 PASS |
| follow-up focused refusal/mapping contracts | 3/3 PASS; no formal stage invoked |
| `validate_ci.py --all` | PASS |
| unique routed Fast on `290482f` | predictive refusal before test loading; 42 > 20; non-green; no retry or substitution |
| unique routed Checkpoint on `290482f` | 42/42 PASS; 16.417209s / 90s; evidence-eligible |
| Promotion inventory | 421 exact final IDs, each once; 27 logical shards; 10 lanes; 92 Fast; 98 Checkpoint |
| repository/static/YAML/secret/diff gates | PASS on `290482f`; 726 paths, 394 Markdown files, 1046 links |
| workflow/manifest text against retained `a520ebc` | byte-equivalent; required checks and lane graph unchanged |
| complete local Promotion | intentionally not run as a development loop |

The `290482f` Checkpoint cost sample records selected count 42, test runtime 16.417209s, router wall 4.659261s,
runner setup/build 3.930978s, total setup/build 8.590239s, zero reruns, two changed test files / 511 lines and eight
changed CI files / 1003 lines. Host usage remains `Unknown`. A follow-up fixes refusal diagnostics so that a plan-known
predictive refusal also preserves selected count and change volume while runtime, runner setup/build and usage remain
`Unknown`; this does not retroactively rewrite the immutable `290482f` Fast receipt.

Fast/Checkpoint/Candidate/Promotion meaning, 15/90 second budgets, failure/timeout semantics, exact-SHA binding and
Windows/Ubuntu required-check names are unchanged. Because Fast is non-green, `290482f` is a clean Git Candidate but
is not an all-green validation Candidate.

## Central integration evidence

The clean CI7 Candidate is `111f4abc47b8122aee5469db4489ad6fb0dee75a`; central merge
`079de741aa13c338051f537650898633492f764e` combines it with W7.3. Dry-run reconciliation preserved every refusal:
unknown `observatory-ui`, four unregistered W7.3 IDs, timing-Unknown, 48-test and 22-test over-selection, and the old
fingerprint Checkpoint failure were all recorded before a new lease was issued. The old Fast green receipt is not
reused for the corrected mapping.

Current relevant source `f41b659720905367351ed11394754f4d7bb6b547` binds fingerprint
`0eea7fbe07a182de209d080dfa7c2c04a7c12956f801342ebf7c15b0a37aab7d`. Its unique Fast lease completed 3/3 PASS
in 0.804195s test runtime with 8.461413s total setup; its unique Checkpoint lease completed 4/4 PASS in 2.580301s
test runtime with 8.467307s total setup. Both are evidence-eligible and report zero reruns. The exact local receipts
are referenced by the v0.3.0 Final RC Validation and are not release artifacts.

This closes fresh central Fast/Checkpoint evidence, not Candidate or Promotion. The subsequent docs-only commit still
requires exact-SHA desktop/mobile Unified acceptance before Final RC registration. A later Final RC must run only
release-owned gates, then push an exact non-main SHA and obtain both hosted required checks; this local integration
does not promote main, change public manifest/defaults, tag or publish a Release.

## 2026-08-31 Phase 0 revision-8 mapping intake

Post-preview source introduces no new final unittest IDs after folding assertions into existing owners. Dry-run
correctly refuses exact unmapped `relation_inbox.py`; no lease or test loaded. Revision 8 may split relation capture
from the coarse maintenance surface and map inbox to Unified shell using generic paths plus data-only portfolios. It
must not change 15/90 budgets, stage authority, required-check names or Promotion inventory. Fresh Fast/Checkpoint
remain Pending until the corrected dry-run allows them.

Revision-8 real-window dry-run proves exact product paths are now mapped but Fast 25 exceeds the 20-test headroom and
the new Core owner timing is Unknown. The 3/4 mapping-only short window is not accepted as product evidence. Revision 9
uses one bounded non-evidence owner check and moves four existing Brand deep checks to Checkpoint while retaining two
Fast sentinels; no coverage, IDs, budgets or Promotion tests are removed.

Revision-9 formal Fast passed 20/20; Checkpoint failed only the hardcoded portfolio ID list, with 29 other methods
green. Updating that list expanded the next Fast plan to 41 through `ci-control`, so revision 10 removes the two new
examples and the list insertion while preserving the precise path mappings. This is a source correction and creates a
new fingerprint; the failed lease remains blocked and is never retried.
