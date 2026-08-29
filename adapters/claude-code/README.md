# Orrery Claude Code Adapter

Status: `experimental` and unreleased. No Claude model-call range is currently
`verified`.

This directory is a native Claude Code Plugin. It contains one thin
`project-orrery` Skill and no Orrery templates, schema, migration rules,
Observatory implementation, or project facts.

## Prerequisites

- Claude Code `2.1.87` or later for the currently tested Plugin CLI surface.
- A separately installed `project-orrery-cli` satisfying the range in
  `adapter-manifest.json`.

The Skill runs `scripts/check_cli_dependency.py` before routing to the CLI.
Missing package metadata, a missing entrypoint, and incompatible versions fail
closed; the Adapter never falls back to copied legacy behavior.

## Validate and use without installing

```text
claude plugin validate adapters/claude-code
claude --plugin-dir adapters/claude-code
```

`--plugin-dir` is session-scoped. It is the preferred discovery path before any
persistent lifecycle test.

## Isolated persistent lifecycle

Set `CLAUDE_CONFIG_DIR` to a dedicated test directory that contains no copied
credentials, then use the bundled local marketplace:

```text
claude plugin marketplace add adapters/claude-code --scope user
claude plugin install project-orrery@project-orrery --scope user
claude plugin list --json
claude plugin update project-orrery@project-orrery --scope user
claude plugin uninstall project-orrery@project-orrery --scope user --keep-data
```

These commands manage only Claude's isolated Plugin state. Installing this
Adapter does not scaffold a target project or update its authored documents.
Using a real login or starting a model turn is a separate, explicitly authorized
validation stage.
