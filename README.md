<div align="center">

# Project Orrery

**A traceable documentation system and local project observatory for long-lived software repositories.**

[English](README.md) · [简体中文](README.zh-CN.md)

[![Validate Project Orrery](https://github.com/yw9299-stack/project-orrery/actions/workflows/validate.yml/badge.svg)](https://github.com/yw9299-stack/project-orrery/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](skills/project-orrery/SKILL.md)

</div>

Project Orrery turns repository-local Markdown into a living project observatory. It keeps product principles, architectural decisions, implementation plans, current state, and validation evidence connected without pretending they are the same kind of truth.

It is distributed as a portable [Codex skill](skills/project-orrery/) with a safe project scaffold and a local documentation viewer. It is designed for teams and agents working on repositories where decisions outlive individual sessions and documentation drift is expensive.

## Why Project Orrery

Conventional documentation folders often mix proposals, decisions, plans, and current behavior. Over time, an accepted design is mistaken for shipped code, a completed checklist becomes the only evidence, or an agent starts from an outdated handoff.

Project Orrery gives each kind of knowledge a distinct role:

```text
Product intent -> Seed -> effective ADR -> approved Design -> Implementation Plan
                                  |                        |
                                  +----> implementation <--+
                                               |
                                           State Docs
                                               |
                                           Validation
                                               |
                                            Snapshot
```

The governing rule is simple: **accepted does not mean implemented, and planned does not mean proven.**

## What it provides

- **A traceable authority model** — Seed principles, append-only ADR history, approved design, implementation plans, factual State Docs, validation records, and dated snapshots.
- **A safe adoption workflow** — dry-run support, create-only default scaffolding, explicit migration status, and no silent claim that a repository has adopted Orrery's authority model.
- **Non-destructive upgrades** — managed viewer files can be refreshed from a strict allowlist; changed files are backed up before replacement.
- **A local documentation observatory** — searchable single-file reader, typed navigation, document-health signals, and project handoff views.
- **Optional intelligence features** — AI-assisted Q&A and synthesis, plus a GitHub trend radar. Core documentation remains usable without them.
- **Agent-friendly project memory** — clear entrances for agents and maintainers without creating a second, competing source of truth.

## Quick start

### 1. Install the Codex skill

Ask Codex:

> Install Project Orrery from https://github.com/yw9299-stack/project-orrery/tree/main/skills/project-orrery

The skill becomes available on the next turn. You can also copy [`skills/project-orrery`](skills/project-orrery/) into your Codex skills directory manually.

### 2. Audit and scaffold a repository

Open the target repository and ask Codex:

> Use Project Orrery to audit this repository. Show me the dry run before scaffolding the documentation observatory.

For direct command-line use:

```bash
git clone https://github.com/yw9299-stack/project-orrery.git
python project-orrery/skills/project-orrery/scripts/install_project_orrery.py \
  --target /path/to/project \
  --title "My Project" \
  --dry-run
```

Review every `CREATE`, `SKIP`, `UPGRADE`, and mixed-toolchain warning, then rerun without `--dry-run`.

### 3. Validate the installation

The first validation has no third-party dependencies:

```bash
python project-orrery/skills/project-orrery/scripts/validate_installation.py \
  --target /path/to/project
```

Installing the scaffold is not the same as adopting its authority model. Use `--require-integrated` only after the target repository has accepted its own adoption ADR and updated its real agent entrance, progress source, and State Docs.

### 4. Run the local observatory

From the target repository:

```bash
python -m pip install -r scripts/docsite/requirements.txt
python -X utf8 scripts/docsite/serve.py
```

On Windows, `start-docsite.bat` provides the same entry point. The server binds to the loopback interface and opens an available port from `8765` to `8784`.

To validate the static reader as well:

```bash
python project-orrery/skills/project-orrery/scripts/validate_installation.py \
  --target /path/to/project \
  --build
```

## Adoption and upgrade safety

Project Orrery is intentionally conservative around existing repositories.

- The default installer creates missing files only.
- Existing authored documentation is never overwritten by scaffolding.
- The generated adoption document is an unnumbered proposal, not an accepted ADR.
- `--upgrade-tools` may replace only allowlisted viewer files and creates a timestamped backup first.
- API keys, local AI configuration, caches, generated sites, virtual environments, and machine-specific paths must not be published with the skill.
- Monorepos and multi-root projects should install Orrery in their documentation authority root; implementation does not need to be moved to fit the template.

Read the complete [architecture](skills/project-orrery/references/architecture.md) and [migration contract](skills/project-orrery/references/migration-contract.md) before integrating an established documentation system.

## Repository layout

| Path | Purpose |
|---|---|
| [`skills/project-orrery/SKILL.md`](skills/project-orrery/SKILL.md) | Codex skill entry and operating rules |
| [`skills/project-orrery/scripts/`](skills/project-orrery/scripts/) | Safe installer and installation validator |
| [`skills/project-orrery/assets/project-template/`](skills/project-orrery/assets/project-template/) | Portable documentation scaffold and local reader |
| [`skills/project-orrery/references/`](skills/project-orrery/references/) | Authority architecture and migration contract |
| [`tests/`](tests/) | Isolated installation and upgrade smoke tests |
| [`.github/workflows/validate.yml`](.github/workflows/validate.yml) | Windows and Linux continuous validation |

## Optional features and privacy

The static reader and authority model work without an AI provider. AI-assisted Q&A, roadmap synthesis, and milestone views require provider configuration supplied by the target project. The trend radar can use GitHub Search and, optionally, web search.

The observatory runs locally by default. Project Orrery does not include a hosted service, telemetry collector, or bundled credentials. Review your provider and network configuration before enabling optional online features.

## Current status

Project Orrery is in an early public release. The migration contract, installer safety rules, isolated smoke tests, static build, and Windows/Linux CI are operational. The current reader interface is Chinese-first, while repository content may use any language; broader viewer localization is planned separately from this bilingual project documentation.

## Contributing

Issues and pull requests are welcome. Please keep changes portable, avoid project-specific assumptions, and preserve the non-destructive migration contract.

Run the local smoke tests before opening a pull request:

```bash
python -m unittest discover -s tests -v
```

After installing the template's reader dependencies, set `ORRERY_TEST_BUILD=1` to include the static site build. GitHub Actions runs this full path on Windows and Ubuntu.

## License

Project Orrery is released under the [MIT License](LICENSE).
