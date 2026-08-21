# 2026-08-21 main acceptance and cross-platform CI

Result: Passed — source `main` only; no release

Date: 2026-08-21

Accepted source commit: `42aebae928554ea87e2412066062793ca8db5270`

Scope: the 38 local integration commits after public `origin/main@117acac`, plus the portable release-gate test correction discovered during remote acceptance.

## Local acceptance

- `ORRERY_TEST_BUILD=1 python -X utf8 -m unittest discover -s tests -v`: 231 tests passed; 3 real-symlink cases were skipped because the Windows process lacked symlink privilege.
- `validate_installation.py --target . --require-integrated --build`: passed; Authority status remained `integrated candidate`, model 1 was supported and eligible for strict evaluation.
- Default Observatory build was 1,232,344 bytes; explicit Authority projection was 1,318,502 bytes and reported `ready`. Rebuilding with the opt-in removed restored the exact default SHA-256 `E35EC47BC48C075596721989C2FC0DA11A212DFDF96D18FE6BE63F83E06CEB1C`.
- 282 tracked Markdown files contained 686 local links with 0 missing targets.
- The 126-file incoming range contained no binary or >1 MiB changed file. `ai-config.json`, `.doccache.json`, `.port`, `docs/_site`, `__pycache__`, `.pyc` and repository-external benchmark roots were not tracked. `git diff --check` passed.

## Remote acceptance discovery and correction

The first push at `95fa4e3` started [GitHub Actions run 32492265629](https://github.com/yw9299-stack/project-orrery/actions/runs/32492265629). Windows passed, but Ubuntu exposed one test-fixture defect:

- `test_cli_preserves_candidate_manifest_lexical_path` used `C:/reviewed/...` as though it were absolute on every OS;
- on POSIX, `pathlib.Path` correctly treated that value as relative, so the assertion observed a current-directory prefix;
- the product gate itself did not fail. The fixture was changed to a platform-native absolute path while preserving the security assertion that the candidate path must not be resolved through a symlink before gate preflight.

Focused reruns after the correction:

- Windows: 12 release-gate tests, 10 passed and 2 symlink-privilege cases skipped;
- Ubuntu WSL: 12/12 passed, including both real-symlink cases.

The broader WSL attempt was not accepted as full-suite evidence because that local environment lacked reader dependencies and could not access frozen Git objects through the mounted worktree. It is retained here as an apparatus limitation, not represented as a product regression.

The correction was committed as `42aebae` and pushed to `main`. [GitHub Actions run 32492830151](https://github.com/yw9299-stack/project-orrery/actions/runs/32492830151) then passed on both Ubuntu and Windows using clean clones and installed reader dependencies.

## Authority boundary

This acceptance proves the source branch is synchronized and cross-platform CI is green. It does **not** create a tag, GitHub Release, public model-1 support statement, stable Core API, managed Observatory production switch or new published artifact. Project Orrery v0.2.0 remains the current public release; post-v0.2 capabilities on `main` remain `experimental`／`unreleased` unless separately stated.
