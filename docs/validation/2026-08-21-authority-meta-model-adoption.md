# 2026-08-21 ADR-0009 Authority Meta Model 采纳验证

Status: Passed for documentation-level adoption

Integration base: `f3d717e2b05f1f7c6c7b44396fac3826bfd22a4f`

Candidate branch: `codex/agent-platform-adapters`

Governing ADR: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md)

Approved Design: [Authority Meta Model 语义设计](../design/authority-meta-model.md)

## Scope

This record validates the documentation-level adoption of Authority Meta Model semantics. It covers ADR allocation, Product Seed／Meta Model separation, role lifecycle versus independent claim dimensions, Authority scopes, provider-neutral evidence, derived-view constraints, conformance boundaries, State synchronization and documentation rendering.

It does not validate a parser, domain API, `authority_model_version` manifest field, Core ownership, Observatory refactor or runtime consumer conformance.

## Authority review

- ADR-0009 explicitly amends ADR-0001 Decision 1 so the arrow chain is an Authority Graph／typical maturation path rather than a mandatory linear workflow.
- ADR-0009 clarifies ADR-0004 conformance obligations without accepting AUTH-4 or claiming a single semantics implementation owner.
- Decision／Implementation／Validation remain independent claim dimensions; Validation failure does not erase implementation existence.
- Authority scope excludes Agent ownership, dependency queues and file locks, which remain coordinator runtime data.
- Evidence categories remain provider-neutral; derived views are constrained semantically without prescribing UI behavior.
- AUTH-1 and AUTH-4 remain explicitly unresolved.

## Validation results

| Check | Result |
|---|---|
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 61 tests: 59 passed, 2 dynamic-dependency tests skipped by design |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid; integration branch reported as `integrated candidate` before local main fast-forward |
| `python -X utf8 scripts/docsite/build_docsite.py --out %TEMP%\project-orrery-adr-0009-meta-model-20260821.html` | PASS — 841 KB; 9 ADR、6 State、7 subsystem、2 Snapshot、58 docs、11 Plan、6 Library |
| PowerShell local Markdown-link scan | PASS — 243 Markdown files、471 local links、0 missing targets |
| `git diff --check` | PASS |
| Provisional-reference scan | PASS — active references point to ADR-0009; historical `PO-DEC-AUTH-001` origin mentions are retained intentionally |

After committing and fast-forwarding local main, dependency-free structure validation and remote push ancestry must be rechecked before final handoff.

## Known boundaries

- No product code, template, manifest schema, support state or release artifact changed.
- No Implementation Plan was created; the next conversation starts with semantic duplication inventory and conformance planning.
- Local main push is part of the surrounding integration task, not evidence that a Meta Model runtime exists.
