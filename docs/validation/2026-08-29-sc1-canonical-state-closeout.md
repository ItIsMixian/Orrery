# Validation: SC1 Canonical State Closeout

Date: 2026-08-29

Status: Worktree Candidate local validation PASS; exact-SHA hosted acceptance pending

Fact scope: `codex/sc1-canonical-state-closeout`, based on clean
`main@9ee831f0d6f64306fe821f8c70229df54648d3eb`.

## Pre-write audit

- local `main`, `origin/main`, `origin/codex/ci5-promotion-throughput` and the frozen CI5 promotion ref resolved to
  `9ee831f0d6f64306fe821f8c70229df54648d3eb`; main was clean and 0/0 ahead/behind.
- GitHub Fast run `33235942078` and Promotion run `33235992711` succeeded on exact `9ee831f`; Promotion was
  25/25 jobs, with both required OS checks passing and each aggregate reporting 390 tests／27 shards.
- Promotion wall time was 3m56s. Twenty lane jobs consumed 23.9 job-minutes; lane test execution consumed
  14.352 minutes, yielding about 40% derived overhead.
- main branch protection remained strict, enforce-admins, and required
  `smoke-test (windows-latest)` plus `smoke-test (ubuntu-latest)`; force push and deletion remained disabled.
- public Release remained v0.2.0 with tag target `20fc95b` and historical asset/checksum names unchanged.
- all registered worktrees were clean. The pre-SC1 inventory exposed stale legacy session lifecycle and no native
  self-host relation events／active tips; this is local coordination evidence, not a source or release regression.

## Documentation reconciliation

- AGENTS and four affected State documents now describe the Canonical W1–W7／R3／CI5 source rather than historical
  Worktree Candidate scope.
- PROGRESS and HANDOFF were reduced to current control information; historical run detail remains linked through
  DEVLOG／Validation.
- CI5 Plan／Validation now record hosted completion and main integration. CI3, W5C, W5E, W6, W7D and R3 plan status
  no longer reports completed Promotion or Canonical integration as pending.
- the platform Plan now leaves Claude runtime verification open and marks the completed DeepSeek exact runtime gate;
  the collaboration Plan records implemented discovery/manual Host switch while retaining the real two-machine gap.
- no product code, component version, release manifest, branch protection, tag, Release or frozen historical input
  was changed.

## Candidate validation

| Check | Result |
|---|---|
| `python -X utf8 scripts/ci/validate_ci.py --all` | PASS |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS; integrated candidate, Authority Model 1 supported |
| `python -X utf8 scripts/ci/validate_repository_gates.py` | PASS; 669 paths／362 Markdown／907 local links／0 forbidden artifacts |
| isolated `build_docsite.py` | PASS; 1,901 KB／159 docs／32 plans |
| Fast profile | 57/57 PASS, 1.442897s／15s |
| `tests.test_project_orrery tests.test_ci_validation` | 33 run／31 PASS／2 expected dynamic-dependency skips |
| `git diff --check` | PASS |

Exact-SHA hosted Fast／Promotion remains pending. The Candidate must not enter main until both required OS checks
pass on the same non-main exact SHA.

## Residual boundary

SC1 does not claim that legacy private Workstream sessions have W3 `integrated` closure evidence. Physical worktree
or branch cleanup remains a separate locally confirmed action after a fresh read-only maintenance evaluation.
