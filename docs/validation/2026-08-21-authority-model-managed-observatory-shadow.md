# Validation: Authority Model managed Observatory shadow

Date: 2026-08-21

Scope: Candidate worktree only; managed `build_docsite.py`／`serve.py` opt-in shadow wiring. This record does not claim a production projection, stable API, release, push, or Canonical integration.

## Expected behavior

- With no opt-in environment variable, managed build and serve use the exact legacy renderer path.
- `ORRERY_AUTHORITY_SHADOW_REPORT=<path>` may dual-run the internal Core evaluator and atomically write a disposable JSON report.
- The report declares `production_behavior_switched=false`, an explicit fact scope and model capability.
- Invalid scope, missing package, invalid manifest, evaluator failure, or sidecar write failure cannot change the returned HTML, legacy stats, or service startup authority.
- The Skill project template remains the compatibility projection of the same managed source; this does not modify the historical v0.2.0 release asset.

## Evidence

Focused command:

```powershell
python -X utf8 -m unittest tests.test_authority_observatory_runtime_shadow tests.test_authority_observatory_managed_shadow tests.test_project_orrery -v
```

Result at the implementation checkpoint: 26 tests run, 24 passed and 2 dynamic-dependency tests skipped by design.

The three new managed-entrypoint cases prove:

1. default runtime returns byte-identical legacy HTML and equal stats with no report;
2. explicit Candidate-scope shadow writes `authority-shadow-report-v1` while preserving those same bytes and stats;
3. a Coordinator-like invalid scope yields `AuthorityEvaluationError` only inside the shadow report while legacy output remains intact.

Python compilation of both self-hosted and template `build_docsite.py`／`serve.py` also passed.

Full repository regression:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Result: 187 tests run, 185 passed and 2 dynamic-dependency tests skipped by design. Integrated scaffold validation, a default static build, `git diff --check` and the focused product/projection suite also passed.

## Remaining boundary

- The sidecar is an internal maintainer diagnostic and is default-off.
- No Authority result is rendered into HTML, dashboard, insights, AI corpus, or service API.
- The Core evaluator and bridge remain non-top-level Candidate APIs.
- Actual production switch, public model declaration in the next release, old-project runtime validation and release publication remain separate gates.
