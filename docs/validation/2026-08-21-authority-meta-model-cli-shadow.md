# Authority Meta Model CLI shadow comparison

Date: 2026-08-21
Status: Candidate implementation validated locally
Scope: `codex/authority-meta-model-fixtures`
Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md)
Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)

## Validated claim

The platform-neutral CLI now runs one bounded Authority comparison against real repository inputs. The legacy
validator remains the production decision path for Accepted ADR, authoring entrances, migration markers,
`integrated candidate` status and exit codes. In parallel, the shadow adapter normalizes only the Accepted ADR
observation, identifies the exact visible input set with a content hash, declares fact scope as `Unknown`, and
compares the Core evaluator result.

Matching output is silent. A mismatch is classified as `parser-gap` and emitted as a warning that explicitly says
the legacy CLI remains authoritative. Evaluator failure also degrades to a warning. No shadow result can change
the validator's status or exit code in this checkpoint.

## Verification

| Check | Result |
| --- | --- |
| `tests.test_authority_cli_shadow` | PASS — 6/6 tests. |
| Legacy production heuristic | PASS — Accepted ADR, entrance mapping, pending marker and integrated result are preserved. |
| Real-input shadow match | PASS — the fixture repository produces the same Accepted ADR result without a production switch. |
| Exact input identity | PASS — `AGENTS.md`, `docs/PROGRESS.md` and numbered ADR bytes contribute to a deterministic SHA-256 snapshot id. |
| Mismatch/failure behavior | PASS — forged disagreement is `parser-gap`; mismatch or evaluator failure produces a warning and leaves legacy status/exit behavior unchanged. |
| Scope/evidence boundary | PASS — CLI cannot infer Canonical/Candidate/Worktree safely, so the shadow input stays `Unknown` with revision-content visibility. |
| Existing product contract | PASS — `tests.test_project_orrery` ran 16 tests: 14 passed and 2 dynamic-dependency tests skipped as designed. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 81 tests run: 79 passed and 2 dynamic-dependency tests skipped as designed. |
| integrated structure validation | PASS — authority status remains `integrated candidate`. |
| static docsite build | PASS — 897 KB temporary output; 10 ADRs, 6 States, 12 Plans and 63 classified docs. |
| Markdown local-link scan | PASS — 250 tracked/untracked Markdown files, no missing local targets. |
| `git diff --check` | PASS — no whitespace errors. |

## Remaining boundary

- Only the Accepted ADR boolean is compared. Entrance mapping, pending markers and integrated adoption remain
  explicitly classified as legacy-only heuristics.
- The CLI does not yet normalize ADR lifecycle, supersede/amend relations, Design/Plan/Implementation/State/
  Validation claims, evidence provenance or an authoritative fact scope.
- No public CLI switch or machine-readable report is added; production behavior has not migrated.
- Observatory parsing/insights and AI derived views have not entered shadow mode.
- Gate B remains open. There is no public `authority_model_version`, stable API, compatibility promise or release.
- Candidate validation is not Canonical integration or release evidence.
