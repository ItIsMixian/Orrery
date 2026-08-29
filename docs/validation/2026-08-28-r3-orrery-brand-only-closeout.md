# R3 Orrery Brand-only Closeout Validation

Date: 2026-08-28

Status: Worktree Candidate implementation and local validation complete; exact-SHA hosted Promotion pending

## Scope and provenance

- Base: clean `main@1e67d4ac7f18e11459417ff4e04eef0ce065b28b`.
- Branch／Workstream: `codex/r3-orrery-brand-only-closeout`／Git-private `R3-orrery-brand-only-closeout`.
- Governing authority: Accepted [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md), Approved [Design](../design/orrery-rename-and-compatibility-contract.md), active [R3–R5 Plan](../implementation/plans/2026-08-28-orrery-rename-and-compatibility.md).
- Fact scope: this record validates a Worktree Candidate only. It does not claim `main`, Canonical, Release or hosted exact-SHA success.

## Mechanical brand contract

`tests/fixtures/brand/orrery-brand-contract-v1.json` classifies every R3 write before modification:

- current brand allowlist: current README／AGENTS／Product Seed／documentation entry and State surfaces; default root docsite, Personal／Team／Graph／Broker display surfaces; safe Skill／Adapter display metadata; golden/UI tests and the R3 authority chain;
- stable technical denylist: `.project-orrery.json` with `name=project-orrery`, `project-orrery-{core,cli,observatory}` distributions, `project_orrery_*` imports, canonical Skill／Plugin／Adapter IDs, existing CLI entrypoint and credential/cache/backup/trash namespaces;
- protocol denylist: schema `$id`, `contract_type`, hash／receipt domains, Authority/API/model versions, Workstream/review/closure/receipt IDs, `ORRERY_*` and `X-Orrery-*`;
- historical denylist: prior ADR／Validation／Snapshot／completed or stopped Plan／DEVLOG paragraphs, experiments and Pilot fixtures, v0.2.0 tag／Release／ZIP／checksum／manifest／bridge／baseline;
- immutable evidence: eight schema SHA-256 values plus ADR-0015, Approved Design, phase-0 baseline, public manifest, Core v0.2 data and published ZIP hash `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`.

The first new Release asset rule remains `project-orrery-*`. R3 does not select a SemVer or build a release.

## Implemented current display surfaces

- README titles／first screen／current install links and human entry docs now consistently present Orrery; current GitHub links use `ItIsMixian/Orrery`.
- Default self-host title is `Orrery · Documentation`; Personal, Team and Workstream Graph inherit it. Broker and optional AI presentation use Orrery as the current human display.
- Skill／Codex／Claude Code／DeepSeek／Harness JSON display names and descriptions use Orrery where the field is display-only. Machine identity fields remain unchanged. Harness JSON v1 schema titles and response error messages remain untouched because clients can observe them through the protocol. No alias or second full implementation was added.
- The target-project projection still uses the `PROJECT_TITLE_PY` title token rather than a hard-coded product brand; a non-Orrery `Atlas Control` golden exercises this boundary.
- One real mobile defect was corrected: the default 390px top bar no longer forces horizontal overflow. The root and project-template CSS remain projected together.

Historical occurrences such as the published “Project Orrery v0.2.0” fact remain untouched. This is not a repository-wide string-zeroing exercise.

## Browser acceptance

Real in-app Chromium loaded isolated generated default, Personal and Graph pages plus the root-only loopback Team server.

| Surface | 1280px | 390×844 | Safety observation |
| --- | --- | --- | --- |
| Default documentation | `Orrery · Documentation`; overflow 0 | same; overflow 0 | generated static read-only surface |
| Personal | same; overflow 0 | same; overflow 0 | `readOnly=true`, `DERIVED READ ONLY`, `ZERO EXTERNAL NETWORK` |
| Team | same; overflow 0 | same; overflow 0 | `authority=derived-read-only`, no forms; settings remained local |
| Workstream Graph | same; overflow 0 | same; overflow 0 | `authority=synthetic-non-authoritative`, `readOnly=true`, no apply/delete/form surface |

All four surfaces reported zero console warning/error entries. Graph Dependency evidence remained exact and its inspector continued to state “No apply · undo · close · delete · merge · remote execution.” No browser interaction mutated project or Team state.

The public repository and its description were inspected read-only at `https://github.com/ItIsMixian/Orrery`; no GitHub setting was changed.

## Reproducible local results

| Command / check | Result |
| --- | --- |
| `python -m unittest tests.test_brand_contract tests.test_personal_observatory tests.test_workstream_relation_graph_observatory -v` | 27/27 PASS |
| relevant product combination: brand, project, Codex／Harness JSON／Claude／DeepSeek, Personal／Team／Graph | 64 tests PASS + 2 expected dynamic-dependency skips; 167.159s |
| `python scripts/ci/test_inventory.py` | PASS; 385 IDs, 27 shards, 57 Fast, 78 Checkpoint |
| `python scripts/ci/validate_ci.py --all` | PASS |
| `python scripts/ci/run_test_shard.py --profile fast ...` | 57/57 PASS; 2.980794s / 15s |
| `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS |
| isolated `python scripts/docsite/build_docsite.py --out ...` | PASS; 2,007 KB, 154 documents |
| `python scripts/ci/validate_repository_gates.py` | PASS; 663 paths, 357 Markdown, 1001 links, no forbidden artifacts |
| `git diff --check` | PASS |

The complete local Promotion was intentionally not run. Hosted Windows／Ubuntu `smoke-test` evidence must bind the final clean exact Candidate SHA on a non-main ref.

## Retained boundaries and next gate

- No push, merge to `main`, GitHub settings／branch protection, tag, Release, archive, checksum or SemVer change occurred.
- No local root, Codex Saved Project, Codex data root, keyring, cache, backup or user project migration occurred.
- R4 aliases and R5 optional defaults have not started.
- The unique integrator must push the exact Candidate SHA to a non-main ref, obtain both required Windows／Ubuntu checks for that SHA, and only then decide whether to promote it to `main` and synchronize the root PROGRESS/HANDOFF.
