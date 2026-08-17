---
name: project-orrery
description: Install, migrate, audit, and maintain a traceable Markdown project documentation system with Seed principles, ADRs, approved Design, Implementation Plans, State Docs, Validation, Snapshots, handoff/progress records, a local static reader, optional AI Q&A, and GitHub trend radar. Use when a user asks to create or upgrade a project docs architecture, package a living documentation portal, distinguish decisions from current implementation facts, repair a drifting ADR/state/plan system, or add the Project Orrery observatory to an existing repository.
---

# Project Orrery

Build a living project observatory without confusing ideas, decisions, plans, implementation, and evidence.

## Select the operation

- **New repository or missing docs system:** scaffold Project Orrery.
- **Existing docs system:** audit local instructions and map existing files before installing anything.
- **Viewer-only refresh:** use the managed tool upgrade; do not replace authored docs.
- **Documentation maintenance:** follow the target repository's `AGENTS.md`, then update the correct authority layer.
- **Architecture explanation or migration:** read [architecture.md](references/architecture.md) and [migration-contract.md](references/migration-contract.md).

## Check the release channel

For an installed target, tell the user that the Skill is checking the stable release manifest, then run the cached checker before maintenance, migration, or viewer upgrades unless the user requested an offline-only workflow:

`python <skill>/scripts/check_project_orrery_update.py --target <repo>`

Use `--offline` when network access is unavailable or undesired. The checker is read-only, uses a 24-hour cache by default, and must not block ordinary documentation work merely because the release service is unavailable.

- `up_to_date`: continue with the installed Skill.
- `update_available_compatible`: show the tagged release and explain that updating the Skill is separate from upgrading the target viewer. Do not install either silently.
- `update_available_migration_required`: stop automatic upgrading and read the tagged migration notes against the target's manifest and authored documents.
- `installed_newer`: preserve the installed version and do not downgrade unless the user explicitly requests it.
- `current_incompatible`: do not mutate the target; obtain a compatible Skill or write an explicit migration plan.
- `unknown`: report that compatibility could not be verified, then continue only with work that does not depend on a new release.

Treat `release-manifest.json` as the machine-readable release contract. The distributed Skill version, installed target toolchain version, project-manifest format, and document schema are separate dimensions. Semantic Versioning communicates release intent; direct compatibility is decided by the manifest's declared ranges.

To update the installed Skill, fetch the exact tagged release into a temporary location, verify the packaged SHA-256 checksum when using a release archive, validate the new Skill, compare any local modifications, and back up the current Skill directory. Replace it only after user confirmation. A repository Skill installer may refuse to overwrite an existing destination; never delete the old Skill first or update from a moving `main` branch.

## Scaffold safely

1. Inspect the repository root, `AGENTS.md`, existing docs directories, and worktree status.
2. Identify the documentation authority root. In monorepos or two-root projects, do not move implementation merely to fit the template.
3. Treat the repository's existing `AGENTS.md` and progress source as authoritative throughout migration. Copying Orrery files is not formal adoption.
4. Preview the operation:

   `python <skill>/scripts/install_project_orrery.py --target <repo> --title "<project>" --dry-run`

5. Review every `SKIP`, `UPGRADE`, and mixed-toolchain warning. Default scaffolding creates missing files only.
6. Install:

   `python <skill>/scripts/install_project_orrery.py --target <repo> --title "<project>"`

7. For an existing repository, inventory its ADR numbering and document roles, then write a project-specific adoption ADR. The generated adoption proposal is not accepted and uses no real ADR number.
8. Update the real `AGENTS.md`, `PROGRESS`, and State Docs. Only then may the project call the authority chain integrated.
9. Customize generated placeholders from real repository evidence. Never claim an implementation exists because the scaffold mentions it.
10. First run dependency-free structure validation:

   `python <skill>/scripts/validate_installation.py --target <repo>`

11. Install viewer dependencies only when the user wants to run the site:

   `python -m pip install -r <repo>/scripts/docsite/requirements.txt`

12. Then validate the static build:

   `python <skill>/scripts/validate_installation.py --target <repo> --build`

## Upgrade viewer tooling

Run the installer with `--upgrade-tools`. It may replace only the viewer paths on Orrery's upgrade whitelist under `scripts/docsite/` and `start-docsite.bat`; it backs up differing copies under `.project-orrery-backup/<timestamp>/` first. A matching path does not prove Orrery originally created the file, so review the dry run and backup location.

Never bulk-overwrite `AGENTS.md` or authored files under `docs/`. Migrate those semantically, one authority layer at a time.

After installing a compatible tagged Skill, preview the target-toolchain update separately:

`python <new-skill>/scripts/install_project_orrery.py --target <repo> --upgrade-tools --dry-run`

Review the version dimensions in `.project-orrery.json` and every backup path before removing `--dry-run`. A current Skill does not imply that the target viewer or document schema has already been upgraded.

## Maintain the authority chain

- Put immutable product constraints in Seed principles.
- Record durable choices and reasons in a new ADR. Amend or supersede earlier ADRs instead of rewriting history.
- Expand accepted choices in Approved Design.
- Map effective ADRs, approved design, implementation targets, validation, and State Doc updates in an Implementation Plan.
- Treat code, assets, configuration, data, and external state as the implementation truth.
- Describe only current behavior in State Docs, including divergence and known gaps.
- Record reproducible evidence under Validation.
- Use Snapshots only for dated evaluation.
- Keep research and examples in Library until a decision promotes them.

After implementation or validation, update `PROGRESS`, append `DEVLOG`, update affected State Docs, and refresh `HANDOFF` when the stopping point or risks changed.

## Run the observatory

- Windows: `<repo>/start-docsite.bat`
- Cross-platform: `python -X utf8 <repo>/scripts/docsite/serve.py`
- Static build only: `python -X utf8 <repo>/scripts/docsite/build_docsite.py`

The AI and radar features are optional. In the dynamic local observatory, open Ask Docs and use its settings button to configure OpenAI, DeepSeek, or another OpenAI-compatible provider. Store API keys only in the OS credential store; the panel saves non-secret base URL and model choices in the gitignored project-root `ai-config.json`. `python scripts/docsite/set_key.py` remains the terminal fallback. Testing a connection sends a minimal model request and may incur a small provider charge. The static `docs/_site/index.html` reader is read-only and cannot configure credentials.

Never package API keys, `ai-config.json`, keyring contents, `.doccache.json`, `.port`, or generated `docs/_site/` into the skill or a public repository.

## Verify before handoff

1. Run dependency-free validation, then `validate_installation.py --build` after installing requirements.
2. Use `--require-integrated` only after the target project has accepted an adoption ADR and updated its real entrances.
3. Confirm the generated site contains ADR, State, Library, and supporting document sections.
4. Confirm existing authored files were not silently overwritten.
5. Report scaffold status and authority-integration status separately, followed by created, skipped, upgraded, backed-up, and still-placeholder content.
