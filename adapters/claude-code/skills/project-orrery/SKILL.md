---
name: project-orrery
description: Route Project Orrery documentation-system work through the platform-neutral Project Orrery CLI while preserving the target repository's canonical AGENTS.md authority chain. Use when asked to scaffold, validate, audit, update, or maintain Project Orrery documentation.
---

# Project Orrery Claude Code Adapter

This is a thin Claude Code Plugin Skill. It requires the separately installed
`project-orrery` CLI declared in `adapter-manifest.json`; it does not contain
Project Orrery templates, schema, compatibility rules, or project facts.

## Route the task

1. Read the target repository's root `AGENTS.md` and follow its local reading
   order and safety boundaries before touching project files.
2. Before invoking the CLI, run
   `python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/check_cli_dependency.py"`.
   If the check exits nonzero, report its structured dependency error instead
   of falling back to copied templates or inferred rules.
3. Before the first product write, run `project-orrery worktree route --target
   <repo> --adapter-manifest "${CLAUDE_PLUGIN_ROOT}/adapter-manifest.json"
   --platform-session-id <current-session-id> --json`. If the runtime does not
   expose its session ID, stop with the returned continuation brief. When the
   route requires attach, run the corresponding `worktree session attach`
   command and rerun the route. Continue only when the route returns `allow`;
   never bypass dirty-primary recovery or silently rebind an existing session.
4. Use the CLI command that matches the request:
   - `project-orrery scaffold --target <repo> --title <title> --dry-run`
   - `project-orrery validate --target <repo>`
   - `project-orrery check-update --target <repo>`
5. Keep Plugin installation separate from target-project scaffolding,
   Observatory tool upgrades, and authored-document migration.
6. Never claim that an accepted decision is implemented, that an installed
   scaffold is integrated, or that Agent self-report proves files were read.

For established repositories, inspect existing documentation roles and review
the dry-run before any mutation. Never silently overwrite authored documents.
Only use `--upgrade-tools` when the user explicitly requests managed Observatory
updates and has reviewed the planned backups.

After implementation or validation work, update the authority layers required
by the target repository's own `AGENTS.md`. Do not create a parallel state
summary in Claude-specific files.
