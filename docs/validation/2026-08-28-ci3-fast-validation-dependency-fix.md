# CI3 Fast Validation Dependency Fix

Date: 2026-08-28

Status: Local Fast PASS; local Checkpoint assertions PASS but timing budget FAIL; exact-SHA hosted acceptance pending

Fact scope: `codex/ci3-fast-validation-dependency-fix`, task base
`codex/w7d-w7-integration-candidate@e2c049ebd6c6476eac8b9555e00edc046d673199`

## Baseline stop gate

- Local HEAD and both local/remote W7D candidate refs resolved to `e2c049ebd6c6476eac8b9555e00edc046d673199`;
  the author worktree was clean and `28f5fad` plus the W7D merge chain were ancestors.
- Promotion run `33195264226` on that exact SHA succeeded; required jobs `98931468856`
  (`smoke-test (windows-latest)`) and `98931688265` (`smoke-test (ubuntu-latest)`) both passed.
- Independent Fast run `33195264316` on the same SHA failed in jobs `98930666113` and `98930666372` before the
  Fast profile. Both logs show `validate_ci.py --all` final discovery importing docsite tests and failing with
  `ModuleNotFoundError: mistune`; the unconditional artifact step then failed because `fast-result.json` did not exist.

## Implemented contract

- Fast setup installs `wheel>=0.41,<1` plus the versioned docsite requirements before `validate_ci.py --all`, matching
  the already successful Promotion discovery environment on both platforms.
- Static validation requires the exact install command before contract validation. Unit mutation coverage rejects a
  reordered dependency block.
- A cross-platform Python step detects the timing result. Upload runs only when the file exists and retains
  `if-no-files-found: error`, so a genuine Fast result cannot silently disappear while an earlier failure has no
  misleading second artifact error.
- Fast still has no `ORRERY_TEST_BUILD`, Promotion required name, complete Promotion selector or widened budget.

## Local Fast to Checkpoint evidence

| Command / check | Result |
|---|---|
| `python -X utf8 -m unittest tests.test_ci_validation -v` | 13/13 PASS; final focused run 2.047s. |
| `python -X utf8 scripts/ci/test_inventory.py` | PASS; 379 unique IDs, 27 shards, 51 Fast, 72 Checkpoint. The two new CI regressions are auto-discovered; existing selectors are unchanged. |
| `python -X utf8 scripts/ci/validate_ci.py --all` | PASS. |
| `python -X utf8 scripts/ci/run_test_shard.py --profile fast ...` | 51/51 PASS in 2.323828s, below the unchanged 15s budget; `ORRERY_TEST_BUILD` absent. |
| `python -X utf8 scripts/ci/run_test_shard.py --profile checkpoint ...` | 72/72 assertions PASS, runner FAIL at 95.381843s > 90s. One bounded retry remained 72/72 but FAIL at 98.319724s. |

The two Checkpoint budget failures are retained. CI3 did not relax the 90-second budget, alter selectors or modify the
existing W7B/W7C implementation; the dominant timings were the pre-existing Git-backed W7B minimal/legacy tests.
No local W7B Promotion or complete repository Promotion was run.

## Repository checkpoint

- Integrated installation validation PASS: `authority_status=integrated candidate`, Authority Model 1 strict
  evaluation eligible.
- Repository gates PASS over 655 tracked/untracked paths, 351 Markdown files and 970 local links, with no forbidden
  runtime/generated artifact.
- Both workflow files parse as YAML; the changed Python files compile; `git diff --check` PASS.

Final hosted Fast and Promotion evidence is intentionally reported in the task receipt against the single committed
SHA, avoiding an unverifiable docs-only successor.
