# Installation and upgrade contract

## Default scaffold

The installer copies missing template files only. It never overwrites an existing authored file, including `AGENTS.md`, documents under `docs/`, or viewer tooling.

## Tool upgrade

`--upgrade-tools` may replace only the viewer paths whitelisted in `install_project_orrery.py`. A matching path does not prove Orrery originally created that file. Before replacing a differing file, the installer copies the original into `.project-orrery-backup/<timestamp>/` under the target repository.

Authored project documents are never upgraded automatically. Schema evolution must be proposed as a migration and applied deliberately after reading the target repository's local instructions.

Installation has three distinct states: scaffold installed, authority migration pending, and authority integrated. The default template includes an unnumbered adoption proposal, not an accepted ADR. A target project chooses its own next ADR number and explicitly records adoption before claiming integration.

## Secrets and generated files

Do not package API keys, local AI configuration, caches, generated `docs/_site/`, virtual environments, or user-specific paths. The installed viewer reads provider configuration from environment variables, `ai-config.json`, `package.json`, or the OS keyring.

The dynamic local observatory may configure an OpenAI-compatible provider through its graphical settings panel. API keys must be written only to the OS credential store and must never be returned to the browser or persisted in `ai-config.json`; only non-secret base URL and model choices belong in that gitignored file. Settings mutations are loopback-only and require the per-server-start settings token. The generated static reader is read-only and must not expose a credential-writing interface.

## Two-root and monorepo projects

Install Orrery in the documentation authority root. State Docs may link to implementation files outside that root with relative paths. Do not move or merge repositories merely to satisfy the template.

## Release and compatibility contract

Project Orrery versions four related surfaces independently:

| Surface | Recorded in | Meaning |
|---|---|---|
| Distributed Skill | `release-manifest.json:version` and `.project-orrery.json:installed_skill_version` | The agent workflow, installer, validator, and bundled release tools currently in use |
| Target toolchain | `.project-orrery.json:toolchain_version` | The managed reader files actually installed in the target repository |
| Project manifest | `.project-orrery.json:manifest_format` | The machine-readable installation metadata format |
| Document schema | `.project-orrery.json:document_schema` | The authority roles and authored-document contract understood by the release |

The legacy `.project-orrery.json:version` field remains as a compatibility alias for the Skill that last ran the installer. It must not be used to claim that a mixed target toolchain or authored document migration completed.

The stable release manifest declares the target manifest formats, document schemas, and earlier Skill versions that support a direct upgrade. Semantic Versioning describes release intent:

- Patch releases contain compatible fixes.
- Minor releases add backward-compatible capability.
- Major releases may require migration.

These categories do not override the declared compatibility ranges. The update checker must report `update_available_compatible`, `update_available_migration_required`, `installed_newer`, `current_incompatible`, or `unknown` instead of guessing.

Update checks are read-only, cache remote results for 24 hours by default, tolerate an unavailable network, and never install a release automatically. Users can also subscribe to tagged GitHub Releases. Public release archives contain the versioned Skill and a SHA-256 checksum; release tags, rather than the moving `main` branch, are the installation authority.

Updating the installed Skill and upgrading a target project are two separate approvals. A compatible Skill update is obtained and validated first. The target viewer then receives its own `--upgrade-tools --dry-run`, backup review, and explicit apply step. Authored documents are never bulk-migrated. If a document-schema change is required, write a project-specific migration plan and decision record before changing authority-bearing files.

Installations created by v0.1 predate the update checker. They require one deliberate bootstrap to v0.2 or later. The current validator recognizes the legacy project manifest, and the next safe installer run records all four version dimensions without treating that metadata upgrade as proof of document migration.
