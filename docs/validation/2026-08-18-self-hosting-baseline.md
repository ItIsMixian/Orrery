# Validation: Project Orrery self-hosting baseline

**Date:** 2026-08-18
**Scope:** Root documentation authority chain, installed observatory, installer cache filtering, experiment synchronization, and repository regression tests

## Expected behavior

1. The root repository is recognized as an integrated Project Orrery installation.
2. The generated reader includes ADR, State, Snapshot, Plan, Library, and current-project entry documents without editing generated HTML by hand.
3. The installer never copies `__pycache__`, `.pyc`, or `.pyo` artifacts from its embedded template.
4. Existing product tests and context-routing benchmark tests remain green.
5. Local secrets, generated reader output, and machine caches stay outside Git.

## Commands and results

| Command | Result |
|---|---|
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target .` | PASS — scaffold valid; authority detected as an integrated candidate |
| `python -X utf8 scripts/docsite/build_docsite.py` | PASS — generated `docs/_site/index.html`; final category counts are recorded below |
| `python -m unittest discover -s tests -v` | PASS — 28 tests ran; 27 passed and the opt-in dynamic-reader test was skipped |
| `$env:ORRERY_TEST_BUILD='1'; python -m unittest discover -s tests -v` | PASS — all 28 tests passed with the dynamic reader path enabled |
| `python -X utf8 experiments/context-routing/validate_benchmark.py --repo-root .` | PASS — 24-task corpus and 6 working-tree run records valid |
| PowerShell local Markdown-link scan over all repository `.md` files | PASS — no missing local link target |
| `git diff --check` | PASS — no whitespace error; Git emitted only the existing LF-to-CRLF working-copy warning for `.gitignore` |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build` | PASS — scaffold valid, static build valid, authority detected as integrated candidate |

Final reader build: `200 KB`; `1` effective ADR, `5` State Docs, `5` subsystem cards, `1` Snapshot, `17` indexed documents, `1` Plan, and `3` Library documents.

## Independent evidence boundaries

- Unit tests and validators mechanically inspect files and outputs within their documented scope.
- Pilot results remain experiment evidence. Agent access receipts do not become independent content-read audit merely because this validation links to them.
- Pilot 004's frozen v1 Oracle exit code remains an apparatus failure; the corrected v2 read-only assessment is identified separately in the result report.

## Known gaps

- No dynamic browser interaction test is included in this baseline.
- The machine-local raw benchmark repository is referenced, not packaged into this documentation tree.
- Publication, tag creation, and remote CI are outside this local validation.

## Result

PASS. The manifest may remain `authority_status: integrated`. This result proves the local repository baseline described above; it does not claim that the working tree has been committed, released, or validated by remote CI.
