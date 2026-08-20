# Pilot 009 P/S Scope Acquisition run

Date: 2026-08-19
Result: six valid runs; cost gate passed; quality gate failed; S not adopted

## Scope and environment

- Runtime: `codex-cli 0.148.0-alpha.15` with hash-matched code-mode host, command runner, sandbox setup and `rg`.
- Model: `gpt-5.6-terra`, medium reasoning.
- External raw root:
  `D:\coding warehouse\project-orrery-benchmark\pilot-009-scope-20260819-142948`.
- P/S share the same 9,109-byte frozen Skill and byte-equal per-task Prompts; only repository `AGENTS.md` differs.
- app-server `skill_search` is disabled; the full event validator rejects external reads and unexpected tools.

## Preflight

| Check | Result |
|---|---|
| Pilot 009 Oracle self-test | PASS |
| Pilot 009 synthetic formal-pipeline dry-run | PASS |
| Context-routing focused tests | PASS, 20/20 |
| Default full repository tests | PASS, 61 total: 59 passed + 2 expected skips |
| Benchmark | PASS, 24 corpus tasks + 6 run records |
| Integrated structure and static build | PASS |
| Markdown local links | PASS, 227 files |
| `git diff --check` | PASS; two existing LF→CRLF requirements warnings only |

## Formal result

All six runs have `apparatus_valid: true`, exact Scope measurement, allowed first writes, passing formal repository
validation, complete proxy proofs and `decision_supporting` retention. P total pre-write input is 540,105; S is
446,904 (`S/P = 0.8274`). All frozen cost guards pass.

Frozen candidate quality is P/S 0/3. Read-only semantic review changes 033 and 035 on both sides from lexical false
negative to pass, leaving P/S 2/3. Both 034 implementations pass behavior/data probes but omit future-version rejection
from PROGRESS, so that failure remains. The required 3/3 quality gate fails; no product adoption follows.

Detailed metrics and the read-only review are in the
[Pilot 009 R2 result](../../experiments/context-routing/results/2026-08-19-pilot-009-ps-scope-terra-medium.md).

## Seal verification

All manifests verify with no failures: P runs 85/85 files each; S runs 88/88 files each. Original repositories,
events, stderr and absolute-path metadata remain outside Git. No sealed file was changed during review.

## Design consequence

The Harness path is ready for this runtime. The next limiting factor is task/Oracle design: behavior, data safety,
structured State and narrative consistency need separate verdicts, and prose controls must tolerate legitimate
paraphrase. The new research candidate is
[真实开发任务与 Oracle v0.2](../../experiments/context-routing/designs/real-development-task-oracle-v0.2.zh-CN.md).

## Final repository regression

After R2 and authority-chain synchronization, the default full suite again passed 61 total tests: 59 passed and
2 dynamic-dependency tests skipped by design. Benchmark validation remained 24 corpus tasks + 6 run records;
integrated structure/static build passed; 230 Markdown files had no missing local links; `git diff --check` passed
with only the same two LF→CRLF requirements warnings.
