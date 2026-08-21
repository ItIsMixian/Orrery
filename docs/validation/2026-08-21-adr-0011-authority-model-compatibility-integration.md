# 2026-08-21 ADR-0011 Authority Model compatibility integration

Status: Verified on Candidate integration branch

Scope: ADR-0011 formal integration, self-host model selection, neutral CLI read-only capability reporting and the internal Observatory status projection. This record does not validate a public release, an automatic migration command, or a managed docsite banner.

## Claims checked

- The accepted Gate B contract is now ADR-0011 and amends ADR-0009 without changing `manifest_format = 1` or `document_schema = 1`.
- The self-host project explicitly selects public Authority Model `1`; this is a repository decision, not an installer side effect.
- The neutral CLI consumes the Core compatibility judgment and exposes it in both human output and stable JSON. `eligible` is never presented as conformance `passed`.
- `legacy-unversioned` remains readable in relaxed validation but fails `--require-integrated`; unsupported and invalid selectors fail closed while preserving a read-only capability report.
- Authority shadow warnings remain structured JSON issues after the latest CLI protocol merge.
- The Observatory projection does not evaluate semantics. It converts an injected Core judgment into a display-neutral status signal and suppresses deterministic shadow evaluation when the capability is read-only.
- Legacy Observatory HTML and statistics remain unchanged for supported, legacy and evaluator-failure paths.

## Evidence

| Check | Observed result |
| --- | --- |
| `python -X utf8 -m unittest discover -s tests -p "test_authority*.py" -v` | Initial run exposed one expected stale 6-relation golden after ADR-0011; after updating the structural expectation, the full-suite run covered all 63 Authority tests without failure. |
| `python -X utf8 -m unittest discover -s tests -v` | 131 tests; 129 passed and 2 dynamic-dependency tests skipped by design. |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS; self-host reports Authority Model 1 as supported and strict-evaluation eligible. |
| `python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\\project-orrery-authority-gate-b-20260821.html"` | PASS; 1027 KB, 11 ADRs, 6 State Docs, 12 Plans and 72 rendered docs. |
| PowerShell local Markdown-link scan | PASS; 261 Markdown files, 572 local links, 0 missing targets. |
| Python compile of changed CLI/Observatory/test modules | PASS. |
| `git diff --check` | PASS; only the existing working-tree LF→CRLF notice for `.project-orrery.json`. |

## Boundaries retained

- No release manifest, installer default, scaffold template, public schema, stable Core export or component version changed.
- No semantic migration dry-run/apply command exists yet; ordinary tool upgrades still preserve an absent selector.
- The Observatory signal is package-internal and is not wired into `build_docsite.py` or `serve.py`.
- This branch is not yet `main`, pushed, tagged or released. Git integration remains separate from this Validation evidence.
