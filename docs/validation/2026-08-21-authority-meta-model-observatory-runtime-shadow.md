# Authority Meta Model Observatory runtime shadow

Date: 2026-08-21
Status: Candidate runtime bridge validated locally
Scope: `codex/authority-meta-model-fixtures`
Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)
Predecessor validation: [Observatory role shadow](2026-08-21-authority-meta-model-observatory-role-shadow.md)

## Validated claim

The Candidate Observatory package now has an internal runtime bridge that calls the real legacy
`build_docsite.render_site()` first and then evaluates the already validated ADR and document-role shadow
contracts against the same docs tree. It returns the original HTML and statistics unchanged, plus a separate
warning-only report containing the production fingerprint, explicit fact scope and both Core shadow results.

An experimental evaluator failure is isolated as `shadow.status = unavailable`; it does not suppress or alter
the legacy page. A legacy rendering failure still propagates because no production output exists in that case.

This is not managed-entrypoint adoption. `scripts/docsite/build_docsite.py`, `serve.py`, the compatibility
template and release projection remain unchanged because those paths require the Gate B compatibility decision.

## Verification

| Check | Result |
| --- | --- |
| `tests.test_authority_observatory_runtime_shadow` | PASS — 5/5 tests. |
| Combined Authority suites | PASS — Core 14 + CLI 6 + ADR Observatory 15 + role Observatory 9 + runtime bridge 5 = 49/49. |
| Real legacy render | PASS — dual-run page is byte-identical and legacy stats are equal. |
| Production fingerprint | PASS — report SHA-256 matches the returned HTML bytes. |
| Combined report | PASS — current ADR lifecycle/relations and 7 Design, 12 Plan, 6 State, 31 Validation documents are observed under explicit Unknown scope; all 31 strict Validation results remain Unknown. |
| Failure isolation | PASS — synthetic evaluator failure produces an unavailable shadow report while returning the unchanged legacy page/stats. |
| Managed tool boundary | PASS — no change to `build_docsite.py`, `serve.py`, component manifest, compatibility template or release contract. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 110 tests run: 108 passed and 2 dynamic-dependency tests skipped as designed. |
| integrated structure validation | PASS — authority status remains `integrated candidate`. |
| static docsite build | PASS — 930 KB temporary output; 10 ADRs, 6 States, 12 Plans and 67 classified docs. |
| Markdown local-link scan | PASS — 254 Markdown files and 525 local links, no missing target. |
| `git diff --check` | PASS — no whitespace errors. |

## Remaining boundary

- The bridge is not exported from the Observatory package and must be invoked explicitly by Candidate tests or
  development harnesses.
- No rendered badge, graph, statistic, HTML section, CLI result or AI corpus consumes the shadow report.
- Gate B must define public semantic version discovery and old/unknown project behavior before managed
  build/serve and scaffold/upgrade projection can adopt this runtime path.
- Candidate runtime validation is not Canonical integration, production-switch or release evidence.
