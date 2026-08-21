---
name: project-orrery
description: Route Project Orrery documentation-system work through the platform-neutral Project Orrery CLI while preserving the target repository's canonical AGENTS.md authority chain. Use when asked to scaffold, validate, audit, update, or maintain Project Orrery documentation.
---

# Project Orrery Codex Adapter

This is a thin Codex adapter. It requires the separately installed
`project-orrery` CLI declared in `adapter-manifest.json`; it does not contain
Project Orrery templates, schema, compatibility rules, or project facts.

## Route the task

1. Read the target repository's root `AGENTS.md` and follow its local reading
   order and safety boundaries before touching project files.
2. Before invoking the CLI, run this Adapter's
   `scripts/check_cli_dependency.py` with the Python interpreter that resolves
   `project-orrery`. If the check exits nonzero, report its dependency error
   instead of falling back to copied templates or inferred rules.
3. Use the CLI command that matches the request:
   - `project-orrery scaffold --target <repo> --title <title> --dry-run`
   - `project-orrery validate --target <repo>`
   - `project-orrery check-update --target <repo>`
4. Keep adapter installation separate from target-project scaffolding,
   Observatory tool upgrades, and authored-document migration.
5. Never claim that an accepted decision is implemented, that an installed
   scaffold is integrated, or that Agent self-report proves files were read.

For established repositories, inspect existing documentation roles and review
the dry-run before any mutation. Never silently overwrite authored documents.
Only use `--upgrade-tools` when the user explicitly asks to update managed
Observatory files and has reviewed the planned backups.

After implementation or validation work, update the authority layers required
by the target repository's own `AGENTS.md`. Do not create a parallel state
summary in Codex-specific files.
