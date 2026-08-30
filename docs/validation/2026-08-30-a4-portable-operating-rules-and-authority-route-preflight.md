# A4 Portable Operating Rules & Authority Route Preflight Validation

Date: 2026-08-30

Status: Candidate validated locally; public/default release remains absent

Task base: `3fc7e7aacedafa8fbd20f9f79ddb8cf5784a0ef3`

Workstream: `A4-portable-meta-rules-bootstrap-contract`

## Scope

This record validates an extension of the existing Authority Meta Model, not a new semantic layer:

- Core-owned `orrery-operating-rules-v1` schema/inventory/projection and fail-closed compatibility;
- provider-neutral Authority Route Preflight, four independent claim axes and Novelty/Absence Claim Gate;
- CLI/Harness/Skill/Ask Docs consumer wiring without target-project writes or authority/release promotion;
- new-project two-layer explanation and brownfield create-only/upgrade non-overwrite behavior;
- existing Unified Observatory `authority` navigation as the only read-only UI carrier.

## Focused deterministic evidence

Command:

```text
python -X utf8 -m unittest tests.test_portable_operating_rules_and_authority_route tests.test_harness_json_adapter tests.test_unified_observatory -v
```

The first combined run found one test-language mismatch in the new-project two-layer assertion; the installed template already exposed the two distinct layers in English. The Candidate then made the user-facing layer names bilingual and retained the failure as development history. The final combined focused run passed `25/25` in `28.235s`. Unified/route-specific tests, the exact Skill projection, Ask Docs callback and static/dynamic Authority carrier were also exercised by CI6 below.

The generalized corpus contains 10 scenarios across 10 subsystem IDs and asserts evidence selection plus four-axis claim shapes. It covers the real A4 failure, accepted design without implementation, implemented but unreleased, old public/new Candidate, template-missing/Core-present, State Unknown, similar concept names, misleading low-authority material, host-hook uncertainty and non-adopted research. Mutation coverage includes semantic paraphrase, conflicting template, stale State, broken ADR link, unindexed concept, unknown registry schema, forged Agent assertion, unknown inventory version and tamper.

## Install and migration boundary

Harness tests create one clean project and one brownfield project. The clean project exposes `Orrery 工作规则` and `项目 Seed` as two layers. The brownfield fixture uses non-UTF-8 author Seed bytes plus custom State and AGENTS bytes; default scaffold and actual `--upgrade-tools` must preserve all three byte-for-byte.

Additional installation evidence:

- isolated wheel installation: `tests.test_cli_wheel_installation` passed `1/1` in the final `24.787s` run; the Core wheel contained both schemas and the canonical inventory, and the installed CLI returned an operating-rules inspect receipt;
- integrated installation validator: `validate_installation.py --target . --require-integrated` passed with `Authority status: integrated candidate` and Authority model `1`;
- Core inventory and Skill reference bytes were identical; missing, unknown-version and tampered copies failed closed to read-only/Unknown;
- a temporary release dry build succeeded and included `project-orrery/references/orrery-operating-rules-v1.json`, while excluding `.git`, generated `docs/_site`, `ai-config.json`, `.doccache` and `.port` data.

## Browser acceptance

An isolated current-worktree Unified server ran on `127.0.0.1:63204` and was stopped after acceptance. The central `127.0.0.1:63203` service was neither reused nor modified and remained listening after the A4 server stopped.

- At 1440×900, the existing eight-item app navigation contained exactly one `authority` identity, labelled `事实与规则`; no meta-rules/portable-rules sibling route existed. `项目原则` and `Orrery 工作规则` appeared in distinct source-labelled columns. The fact-status details were closed by default; opening a rule showed rule ID/version/source/enforcement/failure/Unknown. The Authority section contained zero buttons.
- At 390×844, the same two layers stacked inside a 344px content area. `documentElement.scrollWidth` was `380` for an inner width of `390`, so no horizontal overflow occurred. A fresh URL loaded all rule/status details closed by default, and the tool-rules ledger remained readable under progressive disclosure.
- Both viewports reported an empty warning/error console. The static carrier stayed read-only; the dynamic endpoint added no edit, approval, credential, network or execution surface.

## CI6 and repository gates

Pre-commit Candidate-content results:

- CI inventory/schema validator: PASS; 23 CI unit tests passed.
- CI6 Fast dry-run selected 84 tests with zero unknown paths; Fast passed `84/84` in `10.579391s` under the 15-second budget.
- CI6 Checkpoint dry-run selected 89 tests; Checkpoint passed `89/89` in `30.713138s` under the 90-second budget.
- repository gate inspected 736 tracked/untracked paths, 396 Markdown files and 1073 local links, with no forbidden runtime/generated artifact;
- `git diff --check` passed (line-ending conversion warnings only);
- full Promotion was intentionally not used as the development loop.

The clean committed Candidate is rerun through Fast and Checkpoint after commit so the handoff can report receipts bound to the exact final HEAD without a documentation/SHA self-reference cycle.

## Interpretation boundary

- Mechanically guaranteed in this Candidate: Core inventory validation/digest/compatibility, Core route evaluation and claim shape, CLI/Harness read-only receipts, root Unified Ask Docs callback, static/dynamic projection shape, installer non-overwrite tests.
- Agent best-effort: plain `SKILL.md` consumption where the host offers no verified pre-model hook.
- Hook-dependent: forcing every Codex/Claude/DeepSeek inference to receive a receipt before the model. No such cross-host guarantee is claimed here.
- Public/default/release remains absent: v0.2.0 tag, assets, checksum, manifest and default public consumer are unchanged.
