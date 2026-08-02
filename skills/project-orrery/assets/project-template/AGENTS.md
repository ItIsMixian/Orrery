# {{PROJECT_TITLE}}: Codex state index

This file is the mandatory entry point after a new session or context reset. It tells collaborators what to read first, where current facts live, and which boundaries must not be crossed.

## Read before touching files

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `docs/PROGRESS.md`
4. `docs/core/principles.md`
5. The relevant `docs/state/*.md`
6. Governing ADRs linked by the state document when the reason matters
7. An active `docs/implementation/plans/*.md` only when PROGRESS points to it
8. The actual code, assets, configuration, or operational state

## Documentation rules

- State Docs report current facts; ADRs preserve decisions and reasons.
- `accepted` does not mean `implemented`.
- Plans describe intended work and never count as implementation evidence.
- Update the relevant State Doc when subsystem behavior changes.
- Update `docs/PROGRESS.md` and append `docs/DEVLOG.md` after implementation or validation.
- Update `docs/HANDOFF.md` when pausing, handing off, or discovering a repeatable pitfall.
- Add an ADR for a durable cross-module constraint; amend or supersede earlier ADRs instead of rewriting accepted history.
- Never edit `docs/_site/index.html`; it is generated.

## project structure

**What**: Defines repository boundaries, documentation authority, and implementation locations.
**Truth**: `AGENTS.md`, `docs/PROGRESS.md`, `docs/HANDOFF.md`, and the actual repository tree.
**Dig**: [docs/state/project-structure.md](docs/state/project-structure.md) | governing ADR pending.

## test coverage

**What**: Records what validation protects documentation and implementation.
**Truth**: `docs/validation/`, automated test suites, and their latest reproducible results.
**Dig**: [docs/state/test-coverage.md](docs/state/test-coverage.md) | governing ADR pending.

## Add project-specific subsystems below

Use the same `What / Truth / Dig` triplet so Project Orrery can index them.
