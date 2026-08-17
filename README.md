<div align="center">

# Project Orrery

**A traceable documentation system and local project observatory for long-lived software repositories.**

[English](README.md) · [简体中文](README.zh-CN.md)

[![Validate Project Orrery](https://github.com/yw9299-stack/project-orrery/actions/workflows/validate.yml/badge.svg)](https://github.com/yw9299-stack/project-orrery/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](skills/project-orrery/SKILL.md)

</div>

Project Orrery is repository-scale project memory for humans and software agents. It turns local Markdown into a living project observatory where product intent, architectural decisions, implementation plans, current state, and validation evidence stay connected without being mistaken for the same kind of truth.

It is distributed as a portable [Codex skill](skills/project-orrery/) with a safe project scaffold and a local documentation viewer. It is designed for solo maintainers, teams, and multiple agents working across sessions—especially when the reason behind a change must remain readable long after the original conversation has disappeared.

## Why Project Orrery

Project Orrery began with two practical requirements:

1. **Preserve intent.** An agent should be able to follow a human's long-term product direction and recover what was decided, what conflict caused the decision, and why a later change replaced it.
2. **Preserve readability.** A maintainer or a new agent should be able to understand what the project is doing now without reconstructing it from old chats, scattered files, or commit archaeology.

Git records versions extremely well, but it does not explain which document is a proposal, which decision is still effective, whether an approved design actually shipped, or what evidence proves the current state. In an AI-assisted repository, that ambiguity compounds quickly: more files are produced, stale alternatives survive, and a future agent may confidently read the wrong source.

The same problem becomes a coordination problem in teams. Project Orrery gives contributors stable, typed places for proposals, decisions, plans, state, and evidence so parallel work can converge on shared project memory instead of producing competing narratives.

Project Orrery gives each kind of knowledge a distinct role:

![Project Orrery documentation architecture](docs/assets/document-architecture.en.svg)

The governing rule is simple: **accepted does not mean implemented, and planned does not mean proven.**

### A project protocol, not a giant LLM wiki

Project Orrery is primarily an authority and maintenance protocol for the repository and its agent harness. AI Q&A, synthesis, and retrieval are optional reading layers; they do not decide what is true and never replace the source documents.

For small and medium repositories, typed Markdown, stable reading entrances, explicit links, and direct search preserve more context than prematurely chunking everything into embeddings. Larger repositories can add full-text, vector, or RAG indexes when scale justifies them, while keeping those indexes derived and replaceable. The authority chain remains readable without a model, an external database, or a hosted service.

## What it provides

- **A traceable authority model** — Seed principles, append-only ADR history, approved design, implementation plans, factual State Docs, validation records, and dated snapshots.
- **A safe adoption workflow** — dry-run support, create-only default scaffolding, explicit migration status, and no silent claim that a repository has adopted Orrery's authority model.
- **Non-destructive upgrades** — managed viewer files can be refreshed from a strict allowlist; changed files are backed up before replacement.
- **A local documentation observatory** — searchable single-file reader, typed navigation, document-health signals, and project handoff views.
- **Optional intelligence features** — AI-assisted Q&A and synthesis, plus a GitHub trend radar. Core documentation remains usable without them.
- **Human-and-agent project memory** — clear entrances for maintainers and agents without creating a second, competing source of truth.
- **Team-safe documentation surfaces** — parallel contributors write into distinct roles, reducing accidental conflict between proposals, decisions, plans, and actual state.

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

#### Configure optional AI features

Open **Ask Docs** in the local observatory and select the settings button. The graphical panel supports OpenAI, DeepSeek, and custom OpenAI-compatible providers. It can configure the base URL, default model, optional intent and audit models, and an API key.

- API keys are written to the operating system credential store and are never returned to the browser or saved in `ai-config.json`.
- Non-secret provider and model settings are saved to the target project's gitignored `ai-config.json`.
- **Test connection** sends a minimal model request and may incur a small provider charge.
- The generated static reader at `docs/_site/index.html` is read-only and cannot store credentials.
- For headless or terminal workflows, use `python scripts/docsite/set_key.py`.

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

The static reader and authority model work without an AI provider. AI-assisted Q&A, roadmap synthesis, and milestone views require provider configuration supplied by the target project. The dynamic local observatory provides a graphical settings panel; secrets remain in the operating system credential store. The trend radar can use GitHub Search and, optionally, web search.

The observatory runs locally by default. Project Orrery does not include a hosted service, telemetry collector, or bundled credentials. Review your provider and network configuration before enabling optional online features.

## Current status

Project Orrery is in an early public release. The migration contract, installer safety rules, isolated smoke tests, static build, graphical AI provider configuration, and Windows/Linux CI are operational. The current reader interface is Chinese-first, while repository content may use any language; broader viewer localization is planned separately from this bilingual project documentation.

## Contributing

Issues and pull requests are welcome. Please keep changes portable, avoid project-specific assumptions, and preserve the non-destructive migration contract.

Run the local smoke tests before opening a pull request:

```bash
python -m unittest discover -s tests -v
```

After installing the template's reader dependencies, set `ORRERY_TEST_BUILD=1` to include the static site build. GitHub Actions runs this full path on Windows and Ubuntu.

## License

Project Orrery is released under the [MIT License](LICENSE).
