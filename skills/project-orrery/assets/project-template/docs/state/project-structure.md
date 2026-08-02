# Project structure state

Updated: {{TODAY}}
Governing ADRs: pending project adoption

## Current truth

- Repository root: `.`
- Proposed documentation authority: `AGENTS.md` and `docs/`; integration is not yet accepted
- Local reader tooling: `scripts/docsite/`
- Generated site: `docs/_site/index.html`

## Implementation evidence

- `AGENTS.md`
- `scripts/docsite/build_docsite.py`
- `start-docsite.bat`

## Validation evidence

- Run `python -X utf8 scripts/docsite/build_docsite.py`.

## Known gaps

- Replace this generic map with the project's real repository boundaries.
- Adopt or amend the authority model through the project's own ADR process.
