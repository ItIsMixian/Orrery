# Authority-first Workstream Dispatch Decision Contract

Date: 2026-08-30

Status: PASS — documentation/process contract; product automation not implemented

## Proven boundary

- The maintainer accepted authority-before-dispatch and rejected transcript-first scope distribution.
- ADR-0018, Approved Design and the Plan use existing ADR/Design/Plan/Validation/State roles.
- U2.3 and W7.3 task-specific scope is authored in repository documents before their next implementation step.
- A prompt remains provenance/transport and is not listed as a governing project source.
- No task content, code, release manifest, public Skill, remote setting or GitHub state changed in this decision record.

## Not yet proven

- automatic dispatch receipt generation or first-write enforcement;
- host-level prevention of transcript-only instructions;
- cross-platform Adapter support;
- public Skill/release behavior.

Those claims require the later product automation phase and independent Validation.

## Reproducible checks

```text
python -X utf8 scripts/ci/validate_change.py --stage fast --base HEAD
PASS local-fast-evidence fast: 17/17 tests within the fixed 15-second budget

python -X utf8 scripts/ci/validate_repository_gates.py
PASS repository gates: 730 paths, 400 Markdown files, 1076 local links, no forbidden artifacts

python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
Project Orrery scaffold structure valid; authority status integrated candidate; authority model 1 supported
```

The final authority commit is recorded by Git after these checks; no hosted Promotion claim is made for this docs-only
process baseline.
