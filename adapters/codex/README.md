# Project Orrery Codex Adapter

Status: `experimental` and unreleased.

This directory is an independently packageable Codex Skill adapter. It carries
Codex discovery metadata and invocation guidance only. It does not bundle the
Project Orrery Core, CLI, canonical templates, Observatory, or compatibility
rules.

## Prerequisite

Install a compatible `project-orrery-cli` distribution first. The compatible
range and command name are declared in `adapter-manifest.json`. The Phase 1 CLI
is currently source-only, so this adapter is not yet a complete public install
path.

Before routing a task, the Adapter runs `scripts/check_cli_dependency.py` with
the same Python environment that supplies `project-orrery`. Missing package
metadata, a missing entrypoint, and versions outside the declared range fail
with a nonzero exit instead of falling back to legacy copied behavior.

## Preview and install

Codex discovers user skills from `$HOME/.agents/skills`. Preview an install
from a repository checkout by passing that parent directory explicitly:

```text
python adapters/codex/scripts/install_adapter.py --destination-root <skills-directory> --dry-run
python adapters/codex/scripts/install_adapter.py --destination-root <skills-directory>
```

An existing unknown `project-orrery` directory is never overwritten. A
recognized adapter or legacy v0.2 Skill can be migrated only with `--upgrade`;
the installer first moves the complete prior directory to a timestamped backup
next to, rather than inside, the Codex discovery root.

## Preview an upgrade or uninstall

```text
python adapters/codex/scripts/install_adapter.py --destination-root <skills-directory> --upgrade --dry-run
python adapters/codex/scripts/install_adapter.py --destination-root <skills-directory> --uninstall --dry-run
```

Uninstall is recoverable: the adapter directory is moved under a timestamped
trash directory next to the discovery root rather than deleted. Keeping backup
Skills outside that root prevents duplicate discovery. The installer manages
only the Codex adapter directory. It never scaffolds or upgrades a target
project.
