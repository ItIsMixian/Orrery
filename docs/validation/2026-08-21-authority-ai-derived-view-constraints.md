# Validation: Authority AI derived-view constraints

Date: 2026-08-21

Scope: Candidate worktree only; managed `docsite_qa.py`／`serve.py` and their Skill-template projection. This record does not claim that model prose is always correct, that AI creates project facts, that the deterministic evaluator is a public API, or that an Authority production switch／release has occurred.

## Expected behavior

- Q&A, briefing, roadmap, milestones and radar remain `derived-ai-view`; success and failure JSON carry a system-generated receipt with `authoritative=false` and `creates_project_facts=false`.
- A missing runtime report becomes `Unknown`／`unavailable`; a Candidate shadow remains `shadow-only`. Local-only／Unknown input cannot be promoted to Canonical, source-code content, effective, current, implemented or validated.
- The model cannot override the reserved receipt, and citations absent from the selected corpus are discarded.
- Q&A includes a visible Chinese derived-view notice; streaming responses additionally expose `X-Orrery-View-Type` and `X-Orrery-Authority-Status`.
- Root managed tools and the released-Skill project template remain the same compatibility projection. No v0.2.0 artifact or public support status is rewritten.

## Evidence

Focused tests:

```powershell
python -X utf8 -m unittest tests.test_authority_ai_derived_view tests.test_authority_observatory_managed_shadow -v
```

Result: 9/9 passed. The six new cases cover Unknown defaults, Local-only shadow context, malicious prebuilt-context／authority-receipt spoofing, invented citations, guarded generated/failure payloads, template projection and managed server context/header wiring. The three existing managed-shadow cases continue to protect the exact legacy render and failure isolation.

Full repository regression:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Result: 193 tests run, 191 passed and 2 dynamic-dependency tests skipped by design.

Additional checks passed:

- Python compilation for root/template `docsite_qa.py` and `serve.py`;
- integrated scaffold validation with explicit Authority model 1 support;
- default static docsite build: 11 ADR, 6 State, 7 subsystems, 2 snapshots, 79 classified docs, 12 plans and 6 library docs; output 1088 KB;
- root/template projection assertions and `git diff --check`;
- Markdown local-link scan: 268 files／582 local links／0 missing targets.

## What the tests do not prove

Prompt constraints and visible labels cannot guarantee that a generative model never writes an incorrect sentence. This checkpoint instead proves the enforceable boundary: generated prose, including a deliberately overclaiming test response, cannot overwrite the system receipt, invent a resolvable citation, or become State／ADR／approval／Validation through this API. Human review and deterministic evidence remain required.

## Remaining boundary

- The Authority sidecar remains opt-in and default-off; without it, AI retains an explicit unavailable context.
- No AI output is written back into authoritative Markdown.
- Page-level Authority projection, `docsite_insights.py` migration, full CLI claims, consumer production switches, actual next-release model declaration and release publication remain separate gates.
