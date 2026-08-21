# Authority Meta Model fixture baseline

Date: 2026-08-21
Status: Passed for Candidate fixture checkpoint
Scope: `codex/authority-meta-model-fixtures`, stacked on M1 commit `df9627e`
Governing ADR: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)

## Validated claim

The Candidate worktree contains a versioned, provider-neutral golden contract at
`tests/fixtures/authority-meta-model/v1/conformance.json`. It freezes conformance inputs and expected semantic
boundaries before Project Orrery chooses an implementation owner.

This evidence does not validate a production evaluator, parser, manifest/schema field, public API, CLI/docsite
migration, AI runtime response, release or Canonical integration.

## Coverage

- Four required inputs: model version, repository snapshot, fact scope and evidence visibility.
- Independent decision, implementation and validation claims, including failed validation without erasing implementation.
- Historical implementation versus current State, supersede/amend, Draft/Approved, Plan/State and Snapshot/live-State boundaries.
- Canonical, Candidate, Worktree, Local-only, Historical and Unknown scopes.
- Revision content, executable validation, tool trace, assertion and derived-AI evidence capability boundaries.
- AI non-escalation and explicit separation of fact scope from Coordinator owner/lock data.
- Same-input/same-output determinism and an explicit evidence-visibility difference comparison.

## Verification

| Check | Result |
| --- | --- |
| `python -X utf8 -m unittest tests.test_authority_meta_model -v` | PASS — 9/9 tests. |
| Fixture JSON parse and per-case contract | PASS — 21 cases, every case has the four required inputs. |
| Scope coverage | PASS — all six declared scopes are exercised; Coordinator is not a scope. |
| Comparison contract | PASS — equal inputs produce equal expected output; visibility-only difference is explicit. |
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 70 tests run, 2 dynamic dependency tests skipped by design. |
| `validate_installation.py --require-integrated` | PASS — scaffold structure valid; authority status is `integrated candidate`. |
| static docsite build to temporary output | PASS — 874 KB output; 9 ADRs, 6 States, 12 Plans and 61 classified docs. |
| Markdown local-link scan | PASS — 247 Markdown files, no missing local targets. |
| `git diff --check` | PASS — no tracked whitespace error before staging; staged fixture files are checked again before commit. |

## Remaining gates

- Gate A remains open: the fixture precedes and does not imply a Core, independent-package or multi-consumer owner.
- Gate B remains open: `amm-fixture-v1` is not a project/release manifest field and has no public upgrade/downgrade contract.
- Consumer behavior has not yet been shadow-compared against this fixture.

The unique integrator must merge this Candidate checkpoint before State can describe it as Canonical.
