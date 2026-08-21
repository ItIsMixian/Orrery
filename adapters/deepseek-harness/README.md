# Project Orrery DeepSeek Harness Adapter

Status: `experimental` and unreleased. DeepSeek Harness is currently a developer
preview. Runtime compatibility is `verified` only for the exact rc.8, Windows,
Adapter, Core, CLI 0.1.1, provider/model, lifecycle, and failure-closure scope
recorded in the manifest. The Adapter distribution itself remains unreleased.

This directory is a native DeepSeek Harness profile Plugin Bundle. Its Cordis
plugin registers one immutable packaged `project-orrery` Skill with `ctx.skills`.
It does not bundle Project Orrery templates, schema, migration rules,
Observatory implementation, or project facts.

## Prerequisites

- `@deepseek-ai/dsh` in the version range declared by
  `adapter-manifest.json`.
- `pnpm` on `PATH`, because `dsh plugin` forwards package operations to pnpm.
- A separately installed compatible `project-orrery-cli`.

The Skill runs `scripts/check_cli_dependency.py` before routing to the CLI.
Missing package metadata, a missing entrypoint, and incompatible versions fail
closed.

## Isolated lifecycle

Set `DSH_HOME` to a dedicated directory that contains no copied credentials,
then install into a dedicated profile:

```text
dsh plugin --profile orrery-test add <adapter-directory-or-tarball>
dsh --profile orrery-test --dump-config
dsh plugin --profile orrery-test update project-orrery-deepseek-harness-adapter
dsh plugin --profile orrery-test remove project-orrery-deepseek-harness-adapter
```

Adding the package makes its `dsh.bundle.patch` join the profile's ordered Bundle
list. Restart a running profile after add, update, or remove. Installing this
Adapter does not scaffold or alter the target project.

Real headless model turns, real credentials, and real user profiles are a
separate, explicitly authorized validation stage.
