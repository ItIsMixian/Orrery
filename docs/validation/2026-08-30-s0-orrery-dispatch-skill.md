# S0 Orrery Dispatch Skill Validation

Date: 2026-08-30

Status: PASS — unreleased source Candidate only

Authority source: [S0 Plan](../implementation/plans/2026-08-30-s0-orrery-dispatch-skill.md)

## Implemented scope

- Initial task-description version: `8bb7e1fae26b63e811da84a8e18ffae0f20093fb`; validation-routing amendment:
  `b5bc33c3265733d13d2bc227a9777b07c615668d`, acknowledged before the mapping write.
- Workstream: `S0-orrery-dispatch-skill`, branch `codex/s0-orrery-dispatch-skill`, independent linked worktree.
- Inventory: `skills/orrery-dispatch/SKILL.md` and `skills/orrery-dispatch/agents/openai.yaml`; no other Skill resources.
- `SKILL.md` freezes authority-first new-task and mid-flight amendment handling, explicit task authorization, compact
  SHA/path handoff, scope acknowledgment and opt-in-only monitoring.
- `openai.yaml` provides display name, short description and a `$orrery-dispatch` default prompt; implicit invocation
  remains the platform default.

## Contract review

| Scenario | Required result | Evidence |
|---|---|---|
| User explicitly asks to arrange a new task | write and commit authority sources before task creation | Dispatch steps 2–6 |
| User only discusses an idea | do not create a task | Dispatch step 2 |
| Material change reaches an active task | stop-only, commit dated amendment, then send references | Dispatch step 3 |
| Authority commit/path is absent or prompt differs | stop product writes; committed authority wins | Boundaries |
| Target worktree is dirty | preserve dirty work and require exact-source acknowledgment | Dispatch step 7 |
| User did not request monitoring | do not wait/poll/read repeatedly | Dispatch step 8 |
| Relation/release/delete/merge action appears | no automatic approval or execution | Boundaries |

## Reproducible checks

```text
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/orrery-dispatch
Skill is valid!

python -X utf8 scripts/ci/validate_change.py --stage fast --base HEAD --dry-run
DRY-RUN fast: 44 tests; mappings ci-control/documentation/release-packaging; zero unknown paths

python -X utf8 scripts/ci/validate_change.py --stage fast --base HEAD
PASS local-fast-evidence fast: 44/44 tests within the fixed 15-second budget

python -X utf8 scripts/ci/validate_repository_gates.py
PASS repository gates: 734 paths, 403 Markdown files, 1087 local links, no forbidden artifacts

python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
Project Orrery scaffold valid; integrated candidate; Authority Model 1 supported

python -X utf8 scripts/ci/validate_ci.py --all
PASS CI contract: Fast/Promotion roles, exact-SHA binding and fail-closed gates

python -X utf8 scripts/package_release.py --output-dir <temporary-directory>
PASS release boundary: frozen v0.2.0 archive contains 40 entries and excludes orrery-dispatch
```

The first Fast dry-run refused both Skill paths and expected writes as unmapped. After the authority amendment, S0
scope revision 2 adds only `skills/orrery-dispatch/**` to the existing generic `release-packaging` mapping; no task ID,
branch condition, test ID, tier budget or Promotion contract changed.

Structural and repository validation do not prove host-level first-write enforcement or real task creation.

## Release boundary

The source Candidate is not installed, published or part of Orrery v0.3.0. It does not modify the current
`project-orrery` Skill or implement the future S1 Conductor.
