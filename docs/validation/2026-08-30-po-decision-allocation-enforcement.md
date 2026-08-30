# PO1 Provisional Decision Allocation Enforcement Validation

Date: 2026-08-30

Status: PASS — enforcement and A4 integration allocation complete locally

Authority source: [PO1 Plan](../implementation/plans/2026-08-30-po-decision-allocation-enforcement.md)

## Evidence

- Task-description version `da348b980b8b31e94073b0140edc030b67d22182`; independent
  `codex/po1-decision-allocation-enforcement` worktree with Git-private scope.
- ADR-0007 and the Approved Collaboration Design already contain the PO rule; the failure was missing dispatch/gate
  enforcement, not a missing authority decision.
- `orrery-dispatch` now requires `PO-DEC-<task-id>-<slug>` outside the explicitly identified unique integration
  worktree and rejects branch-name／locally observed next-number authority.
- repository gate ignores `0000` templates/history and proposal paths, accepts unique current ADRs, and rejects a
  synthetic duplicate `0018` pair with a deterministic error.
- No task-ID/branch conditional, network allocator, new schema or peer-worktree scan was added.

## Reproducible checks

```text
skill-creator quick_validate skills/orrery-dispatch
Skill is valid!

validate_adr_number_allocations(unique + proposal + 0000 fixture)
PASS unique/proposal/0000 fixture; duplicate 0018 rejected

python -X utf8 scripts/ci/validate_repository_gates.py
PASS current tree: unique numeric ADRs and existing repository gates

python -X utf8 scripts/ci/validate_change.py --stage fast --base HEAD --dry-run
DRY-RUN fast: 44 tests / 15-second budget

python -X utf8 scripts/ci/validate_change.py --stage fast --base HEAD
PASS local-fast-evidence: 44/44 within the fixed 15-second budget

python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
PASS integrated Candidate / Authority Model 1 supported
```

A4/U2.3 local integration preserves authority-first as ADR-0018 and allocates portable operating rules as ADR-0019.
The old A4 Candidate SHA remains provenance; current-tree duplicate-number and link gates validate the integrated form.
