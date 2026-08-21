# Authority Meta Model Observatory parser shadow

Date: 2026-08-21
Status: Candidate package-level shadow validated locally
Scope: `codex/authority-meta-model-fixtures`
Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)

## Validated claim

The platform-neutral Observatory package contains an internal, unexported shadow adapter that consumes the real
legacy `build_docsite.parse_adrs` result. It independently normalizes raw ADR status metadata, supplies the
experimental Core evaluator with an exact numbered-ADR snapshot, explicit `Unknown` scope and revision-content
visibility, then compares the Core decision lifecycle result with the legacy `status_class`.

The adapter is a package-level conformance harness, not a build-path migration. `build_docsite.py`, `serve.py`,
rendered badges, graphs, statistics and HTML remain unchanged. The Core evaluator is injected by the test caller,
so this checkpoint adds no public package dependency, top-level API, component manifest, template or release
contract.

## Verification

| Check | Result |
| --- | --- |
| `tests.test_authority_observatory_shadow` | PASS — 8/8 tests. |
| Combined Authority suites | PASS — Core 14 + CLI 6 + Observatory 8 = 28/28. |
| Legacy lifecycle coverage | PASS — Accepted, Accepted→Superseded, Superseded, Deprecated, Proposed, Design/Deferred and Other all dual-run consistently. |
| Current repository parser | PASS — every parsed numbered ADR matched the Core lifecycle shadow. |
| Exact input identity | PASS — numbered ADR bytes affect the SHA-256 snapshot; README, `0000` template and non-standard filenames do not. |
| Mismatch classification | PASS — forged legacy divergence is reported as `parser-gap` without switching production authority. |
| Relation boundary | PASS — predecessors, supersedes, ADR refs and State refs remain explicitly `legacy-only`; no graph heuristic is promoted into Core relations. |
| Public/runtime boundary | PASS — adapter is absent from the Observatory top-level API and build/serve sources are unchanged. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 89 tests run: 87 passed and 2 dynamic-dependency tests skipped as designed. |
| integrated structure validation | PASS — authority status remains `integrated candidate`. |
| static docsite build | PASS — 905 KB temporary output; 10 ADRs, 6 States, 12 Plans and 64 classified docs. |
| Markdown local-link scan | PASS — 251 tracked/untracked Markdown files, no missing local targets. |
| `git diff --check` | PASS — no whitespace errors. |

## Remaining boundary

- This is not an automatically executing Observatory runtime shadow. Build and serve paths still use only the
  legacy parser.
- ADR relation metadata, effective-decision graphs, Design/Plan/State/Validation claims and evidence provenance
  do not yet have an Observatory-to-Core parser contract.
- `docsite_insights.py` remains heuristic observation logic and has not entered shadow comparison.
- No template, manifest, public API, package dependency, version or release contract changed.
- Gate B remains open, and Candidate validation is not Canonical integration or release evidence.
