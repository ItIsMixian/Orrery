# Authority Meta Model Observatory role shadow

Date: 2026-08-21
Status: Candidate role contract validated locally
Scope: `codex/authority-meta-model-fixtures`
Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)
Predecessor validation: [Observatory relation shadow](2026-08-21-authority-meta-model-observatory-relation-shadow.md)

## Validated claim

The internal Observatory role shadow adapter now collects deterministic observations from the existing
Design, Implementation Plan, State and Validation directories. It hashes exactly those visible inputs and
sends one normalized role observation at a time into the experimental Core evaluator.

The contract is deliberately conservative. Design recognizes only Draft, Approved and Deprecated lifecycle
terms. A Plan produces `planned` and a State document produces `current`, but neither creates an
`implementation_claim`. A Validation file produces Passed or Failed only from an exact `Result:` or
`Outcome:` value. Document presence, `Status:` and free-form result prose remain `Unknown`; hiding
reproducible validation evidence also returns `Unknown`.

This is Candidate package-level shadow evidence. It does not rerun commands recorded in Validation, infer
implementation from State prose, change docsite rendering or establish a public parser/API contract.

## Verification

| Check | Result |
| --- | --- |
| `tests.test_authority_observatory_roles_shadow` | PASS — 9/9 tests. |
| Combined Authority suites | PASS — Core 14 + CLI 6 + ADR Observatory 15 + role Observatory 9 = 44/44. |
| Design lifecycle | PASS — Draft／Approved／Deprecated normalize; missing or unrelated values remain Unknown. |
| Plan／State independence | PASS — `planned` and `current` do not create an implementation claim. |
| Validation non-escalation | PASS — presence, `Status:` and mixed prose remain Unknown. |
| Explicit Validation result | PASS — exact Passed/Failed values normalize under executable-evidence visibility. |
| Hidden evidence | PASS — a decisive result returns Unknown when executable validation is not visible. |
| Fail-closed metadata | PASS — contradictory explicit Result/Outcome metadata raises `AuthorityRoleParseError`. |
| Repository inventory | PASS — 7 Design, 12 Plan, 6 State and 29 Validation documents observed; all 29 existing Validation results remain Unknown under the strict collector. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 105 tests run: 103 passed and 2 dynamic-dependency tests skipped as designed. |
| integrated structure validation | PASS — authority status remains `integrated candidate`. |
| static docsite build | PASS — 922 KB temporary output; 10 ADRs, 6 States, 12 Plans and 66 classified docs. |
| Markdown local-link scan | PASS — 253 Markdown files and 519 local links, no missing target. |
| `git diff --check` | PASS — no whitespace errors. |

## Remaining boundary

- `build_docsite.py`, `serve.py`, rendered badges, graphs, statistics and HTML remain unchanged and use the
  legacy family parser/projection.
- The adapter is not exported from the Observatory package and adds no public dependency, manifest field or
  version promise.
- A parsed Validation result is not proof that its command was rerun by this adapter. Executable replay,
  evidence provenance, State-body implementation claims, insights/projection and runtime wiring remain future
  checkpoints.
- Gate B remains open. Candidate validation is not Canonical integration, production-switch or release
  evidence.
