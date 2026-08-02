# Installation and upgrade contract

## Default scaffold

The installer copies missing template files only. It never overwrites an existing authored file, including `AGENTS.md`, documents under `docs/`, or viewer tooling.

## Tool upgrade

`--upgrade-tools` may replace only the viewer paths whitelisted in `install_project_orrery.py`. A matching path does not prove Orrery originally created that file. Before replacing a differing file, the installer copies the original into `.project-orrery-backup/<timestamp>/` under the target repository.

Authored project documents are never upgraded automatically. Schema evolution must be proposed as a migration and applied deliberately after reading the target repository's local instructions.

Installation has three distinct states: scaffold installed, authority migration pending, and authority integrated. The default template includes an unnumbered adoption proposal, not an accepted ADR. A target project chooses its own next ADR number and explicitly records adoption before claiming integration.

## Secrets and generated files

Do not package API keys, local AI configuration, caches, generated `docs/_site/`, virtual environments, or user-specific paths. The installed viewer reads provider configuration from environment variables, `ai-config.json`, `package.json`, or the OS keyring.

## Two-root and monorepo projects

Install Orrery in the documentation authority root. State Docs may link to implementation files outside that root with relative paths. Do not move or merge repositories merely to satisfy the template.
