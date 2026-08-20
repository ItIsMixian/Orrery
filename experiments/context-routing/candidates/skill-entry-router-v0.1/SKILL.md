---
name: project-orrery
description: Maintain, audit, install, or migrate a traceable Project Orrery documentation system while keeping decisions, plans, implementation, current state, and validation distinct.
---

# Project Orrery

Keep one traceable fact chain without making every task carry every Orrery operation.

## Route before loading detail

- **Existing-project maintenance or audit:** obey the target `AGENTS.md`; read its mandatory entrances,
  relevant State Docs, effective ADRs only when reasons are needed, and the active Implementation Plan
  before implementation. Do not load install, release, migration, or viewer references unless the task
  actually crosses those boundaries.
- **New scaffold:** read [scaffold.md](references/scaffold.md).
- **Skill update, viewer upgrade, or compatibility work:** read
  [release-channel.md](references/release-channel.md) and
  [migration-contract.md](references/migration-contract.md).
- **Architecture explanation or document-schema migration:** read
  [architecture.md](references/architecture.md) and
  [migration-contract.md](references/migration-contract.md).
- **Run or configure the observatory:** read [viewer.md](references/viewer.md).

## Always preserve these boundaries

- Seed constrains durable principles; ADR records accepted choices and reasons; approved Design specifies
  them; Plan records intent; code/configuration/assets/external state are implementation truth; State Docs
  report current facts; Validation records reproducible evidence.
- `accepted` is not `implemented`; a worktree change is not a commit; a commit is not a release.
- Never bulk-overwrite authored `AGENTS.md` or `docs/`. Default installation creates missing files only;
  managed-tool upgrades require a reviewed dry run and backup.
- Never package credentials, `ai-config.json`, keyring contents, caches, `.port`, generated `docs/_site/`,
  virtual environments, or user-specific benchmark output.
- Dashboards, AI answers, summaries and radar are projections, not new project facts.

## Close maintenance work

Validate in proportion to the changed boundary and follow the target Plan/AGENTS commands. After real
implementation or validation, update affected State Docs and PROGRESS, append DEVLOG, and refresh HANDOFF
when the stopping point or risks changed. Report implementation, commit, push and release status separately.
