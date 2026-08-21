# Authority Meta Model Core shadow evaluator

Date: 2026-08-21
Status: Candidate implementation validated locally
Scope: `codex/authority-meta-model-fixtures`
Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)

## Validated claim

Platform-neutral Core contains an experimental deterministic evaluator for pre-normalized Authority observations.
It satisfies every expected claim/relation/prohibition in `amm-fixture-v1`, produces equal output for equal inputs,
responds explicitly to evidence visibility and fails closed on unsupported inputs.

The evaluator does not parse Markdown, collect Git/Harness evidence, alter manifests/schema, export a stable
top-level Core API, switch CLI/docsite behavior, call a model or implement Coordinator runtime.

## Verification

| Check | Result |
| --- | --- |
| Authority fixture/evaluator专项 | PASS — 14/14 tests. |
| All golden expectations | PASS — all 21 fixture cases satisfied in shadow comparison. |
| Shadow difference classification | PASS — every extra claim/prohibition is declared and exercised by fixture policy; no unclassified relation or Coordinator output. |
| Determinism / visibility | PASS — equal inputs produce equal result; hidden validation becomes explicit `unknown`. |
| Fail-closed boundary | PASS — unknown model version, scope, evidence category and observation kind are rejected. |
| Public-contract boundary | PASS — evaluator is not exported by `project_orrery_core.__init__`; manifests and API versions unchanged. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 75 tests discovered; process exited successfully. |
| integrated structure validation | PASS — authority status remains `integrated candidate`. |
| static docsite build | PASS — 887 KB temporary output; 10 ADRs, 6 States, 12 Plans and 62 classified docs. |
| Markdown local-link scan | PASS — 249 Markdown files, no missing local targets. |
| tracked/staged diff checks | PASS — no whitespace errors; exactly 11 authorized implementation, test and authority-document paths. |

## Remaining boundary

- No CLI or Observatory consumer has dual-run against real repository parsing yet.
- The evaluator accepts normalized observations; parser/collector contracts remain to be designed through shadow evidence.
- Gate B remains open. There is no public `authority_model_version` field, stable API or upgrade/downgrade promise.
- Candidate validation is not Canonical integration or release evidence.
