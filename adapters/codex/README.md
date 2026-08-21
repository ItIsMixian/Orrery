# Project Orrery Codex Adapter

Status: `experimental` and unreleased as an Adapter distribution;
runtime-`verified` only for the exact Codex/Windows scope recorded in
`adapter-manifest.json`.

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

## Isolate a same-name legacy Skill during runtime validation

When the authentication `CODEX_HOME` also contains the published legacy
`project-orrery` Skill, a repository Adapter and that user Skill are both
discoverable. Do not copy `auth.json` into a temporary home and do not treat an
ambiguous selector as Adapter evidence. Codex supports a per-run
`skills.config` disable override. On the verified `codex-cli
0.148.0-alpha.21` Windows runtime, the effective override used the resolved
legacy `SKILL.md` file path:

```text
codex exec --ignore-user-config -c 'skills.config=[{path="C:/Users/<user>/.codex/skills/project-orrery/SKILL.md",enabled=false}]' <other-verification-options> <prompt>
```

First compare `codex debug prompt-input` with and without the override. Proceed
only when the model-visible catalog contains exactly one `project-orrery`
entry and it is this Adapter. This path detail is scoped to the verified
runtime; re-check it when Codex changes.
