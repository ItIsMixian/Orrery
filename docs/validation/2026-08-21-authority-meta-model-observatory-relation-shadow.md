# Authority Meta Model Observatory relation shadow

Date: 2026-08-21
Status: Candidate relation contract validated locally
Scope: `codex/authority-meta-model-fixtures`
Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)
Predecessor validation: [Observatory parser shadow](2026-08-21-authority-meta-model-observatory-parser-shadow.md)

## Validated claim

The internal Observatory shadow adapter now defines a narrow relation-observation contract in addition to its
ADR lifecycle comparison. It reads only explicit ADR header metadata (`Amends:` and `Supersedes:`), plus the
legacy `Status: Superseded by ADR-N` encoding. The latter is inverted into the normative direction
`ADR-N supersedes the older ADR` before the observations enter the experimental Core evaluator.

The resulting Core relations and effective-decision claims are Candidate shadow evidence. They do not replace
the legacy graph, change rendered pages or add a public parser/API contract. `Predecessor`, ordinary Markdown
references and State references remain legacy-only navigation inputs and cannot silently become normative
amend/supersede relations.

## Verification

| Check | Result |
| --- | --- |
| `tests.test_authority_observatory_shadow` | PASS — 15/15 tests. |
| Combined Authority suites | PASS — Core 14 + CLI 6 + Observatory 15 = 35/35. |
| Explicit supersede | PASS — accepted replacement supersedes the older ADR and becomes the single effective decision. |
| Legacy direction inversion | PASS — `Status: Superseded by ADR-N` becomes `ADR-N supersedes current ADR`; the old legacy field remains identifiable as superseded-by. |
| Explicit amend | PASS — base decision and accepted amendment both remain effective. |
| Real repository metadata | PASS — six current `Amends` headers produce the expected Core relations with no unresolved target. |
| Relation isolation | PASS — `Predecessor`, body refs and State refs do not enter Core relations. |
| Missing target | PASS — a superseded-by target outside the visible snapshot remains `Unknown` and creates no effective-decision claim. |
| Fail-closed metadata | PASS — an explicit relation header without an ADR target raises `AuthorityRelationParseError`. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 96 tests run: 94 passed and 2 dynamic-dependency tests skipped as designed. |
| integrated structure validation | PASS — authority status remains `integrated candidate`. |
| static docsite build | PASS — 913 KB temporary output; 10 ADRs, 6 States, 12 Plans and 65 classified docs. |
| Markdown local-link scan | PASS — 252 Markdown files and 513 local links, no missing target. |
| `git diff --check` | PASS — no whitespace errors. |

## Remaining boundary

- `build_docsite.py`, `serve.py`, badges, graph edges and HTML remain unchanged and continue using the legacy
  parser/projection.
- The internal relation collector is not exported as a top-level Observatory API and adds no public package
  dependency, manifest field or version promise.
- `Clarifies`, `Predecessor`, ordinary refs, State refs, Design/Plan/State/Validation claims and evidence
  provenance are outside this checkpoint.
- Gate B remains open. Candidate validation is not Canonical integration, production-switch or release evidence.
