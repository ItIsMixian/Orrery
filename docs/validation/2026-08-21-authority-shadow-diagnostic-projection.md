# Validation: Authority shadow diagnostic projection

Date: 2026-08-21

Scope: Candidate worktree only; deterministic `docsite_insights.py` projection and managed `build_docsite.py` runtime wiring. This record does not claim a default Authority page, production switch, public API, release, or Canonical integration.

## Expected behavior

- With neither Authority environment switch, managed build/serve return the exact legacy HTML and stats.
- `ORRERY_AUTHORITY_SHADOW_REPORT=<path>` alone still writes only the disposable sidecar and returns the exact legacy HTML/stats.
- `ORRERY_AUTHORITY_SHADOW_VIEW=1` independently opts into a visible `authority-shadow-diagnostic` panel. The panel carries `data-authoritative=false` and `data-production-switched=false`.
- The diagnostic model exposes only comparison status, fact scope, model status and counts for differences, unresolved relations and Validation Unknown. It deliberately excludes claims, effective-decision payloads and relation bodies.
- Invalid／unavailable shadow results remain diagnostic `unavailable`; panel or report failures cannot become project facts.
- Root managed tools and Skill-template projections stay equivalent apart from the project-title placeholder.

## Evidence

Focused command:

```powershell
python -X utf8 -m unittest tests.test_authority_observatory_managed_shadow tests.test_authority_observatory_runtime_shadow tests.test_project_orrery -v
```

Result at the implementation checkpoint: 29 tests run, 27 passed and 2 dynamic-dependency tests skipped by design. The managed-entrypoint class now contains 6/6 cases; the three added cases prove explicit view-only injection, bounded health-count projection with effective claims excluded, and root/template parity.

Python compilation for root/template `build_docsite.py` and `docsite_insights.py` passed.

Final checks:

- full repository: 196 tests run, 194 passed and 2 dynamic-dependency tests skipped by design;
- integrated scaffold validation: passed with explicit Authority model 1 support;
- default static build: 11 ADR, 6 State, 7 subsystems, 2 snapshots, 80 classified docs, 12 plans and 6 library docs; output 1096 KB;
- Markdown local-link scan: 269 files／584 local links／0 missing targets;
- `git diff --check`: passed.

## Remaining boundary

- Both Authority switches are default-off, internal maintainer controls.
- The panel is a diagnostic observation of Candidate shadow behavior, not a project State or conformance certificate.
- Legacy dashboard KPIs, graph, badges, statistics and navigation remain production-owned by the legacy renderer.
- Full CLI claims, real Authority page semantics, consumer production switch, actual next-release model declaration and publication remain separate gates.
