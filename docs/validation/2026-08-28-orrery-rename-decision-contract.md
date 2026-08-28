# Validation: Orrery Rename Decision and Compatibility Contract

Date: 2026-08-28

Fact scope: Worktree Candidate `codex/r2-orrery-rename-decision-contract`, based on clean
`main@2037cab7a46ae048147115c3c317f8d542a8cee9`

## Scope

Validate a documentation-only R2 candidate: additive R1 provenance, reproducible current-main naming inventory,
external read-only identity facts, ADR/Design/Plan/Library/State/index linkage and repository documentation gates.
The initial pass validated the proposed decision package; this closeout also records maintainer acceptance of ADR-0015
and approval of its Design. It does not claim R3 implementation, package/runtime compatibility, main integration or
release.

## Baseline and provenance review

- `git status --short --branch` was clean before branch creation; detached HEAD and local `main` both resolved to
  `2037cab7a46ae048147115c3c317f8d542a8cee9`.
- R1 `f991befb3854bc7603b85e243c24cc4b2fb7a0e9` differs from its W5E base only by its Library audit and Library
  index. It is not merged into main. R2 retained its method/history as attributed input and did not cherry-pick it.
- Git-private session registration recorded the R2 branch, exact integration/merge-base OID, primary/affected
  subsystems, expected writes and validation surfaces before the first authored-file write.

## Maintainer acceptance closeout

- The maintainer accepted ADR-0015 and approved the companion Design on 2026-08-28. The Implementation Plan now
  releases R3 to a separately registered Workstream; R3, R4 and R5 remain unimplemented.
- R4's `orrery` CLI alias default is an explicit opt-in, collision-checked thin launcher to one canonical
  implementation. Host integrations change display name only unless that host independently proves safe alias
  discovery, upgrade and uninstall.
- The first new Orrery Release retains stable `project-orrery-*` archive/asset filenames while displaying the Orrery
  brand. Any later filename change remains an evidence-triggered review.
- Local root/Saved Project maintenance may be separately authorized after R3 passes exact-SHA gates and enters main;
  it does not wait for R4/R5. Codex application-data relocation to D: remains a later independent Workstream.
- Acceptance/approval changes decision authority only. No package, schema, CLI, Skill, Adapter, local path, Saved
  Project, Codex data, GitHub setting, tag or Release was changed by this closeout.

## Reproducible current-main inventory

Commands used `git ls-files` and `git grep -I ... 2037cab7 --`; each `git grep -o` output line is one occurrence and
the filename is the second colon-delimited field when an explicit tree-ish is supplied.

| Pattern | Occurrences | Files | R1 delta |
|---|---:|---:|---:|
| tracked paths | 655 | n/a | +33 |
| `Project Orrery` | 399 | 223 | +5／+5 |
| `Project-Orrery` | 2 | 2 | 0／0 |
| `project-orrery` | 1,372 | 298 | +50／+10 |
| `project_orrery` | 462 | 147 | +36／+7 |
| standalone `Orrery` | 242 | 79 | +20／+10 |
| `ORRERY_` | 194 | 67 | +9／+6 |
| `.project-orrery` | 171 | 75 | +2／+1 |

Frozen roots remained `Project Orrery` 163/92, `project-orrery` 528/136 and `project_orrery` 104/53. Path
inventory was 122 slug paths and 80 Python-namespace paths. Fourteen schema `$id` values contain the old slug;
72 `contract_type` occurrences across 22 files produce 46 distinct values. These are preservation inputs, not a
zero-count target.

## External read-only evidence

- GitHub REST GET reported `ItIsMixian/Orrery`, default `main`, and the current repository description.
- HEAD to the old repository URL returned 301 to `https://github.com/ItIsMixian/Orrery`.
- GitHub Release GET for v0.2.0 reported the historical ZIP/checksum asset names; local annotated tag dereferenced to
  `20fc95be7b9616fa2de90fc1ffe33b35d5c3f3fd` and ZIP digest remained
  `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`.
- PyPI JSON GET reported unrelated `orrery` 0.1.1 and its MVC/observer summary.
- All requests were GET/HEAD. No remote mutation, push, tag, Release or settings call occurred.

## Documentation and repository gates

Initial proposal authored-file pass:

| Command | Result |
|---|---|
| `python -X utf8 scripts/ci/validate_repository_gates.py` | PASS: 660 tracked/untracked paths, 356 Markdown files, 995 local links, no forbidden runtime/generated artifacts |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS: integrated candidate, Authority Model 1 supported/strict eligible |
| `python -X utf8 -m unittest tests.test_project_orrery -v` | PASS: 16 run, 14 pass, 2 dynamic-dependency skips by design |
| `python -X utf8 scripts/ci/run_test_shard.py --profile fast --output <system-temp>` | PASS: 51/51 in 2.574525s under 15s; inventory `d95b3062…`, manifest `0b191bc2…` |
| `git diff --check` | PASS |
| changed-path boundary | PASS: only `docs/**`; no diff in PROGRESS/HANDOFF, package/schema/CLI/Skill/Adapter/workflow/scripts/tests/project manifest |

The first integrated-validator pass correctly rejected a literal project-title template token quoted in the Library
audit as unresolved. The prose was changed to describe the token without embedding template syntax; the final
validator and link gate then passed. No generated `docs/_site/` artifact was written.

The Fast profile includes Authority non-escalation, v0.2 frozen hash, documentation governance, phase-0 published
inventory and component projection checks. A full Checkpoint/Promotion suite was not run because R2 changes authored
documentation only and does not implement R3 or runtime behavior.

## Acceptance closeout gates

The acceptance revision was validated against the same R2 Worktree Candidate without changing runtime inputs:

| Command | Result |
|---|---|
| `python -X utf8 scripts/ci/validate_repository_gates.py` | PASS: 660 tracked/untracked paths, 356 Markdown files, 998 local links, no forbidden runtime/generated artifacts |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS: integrated candidate, Authority Model 1 supported/strict eligible |
| `python -X utf8 -m unittest tests.test_project_orrery -v` | PASS: 16 run, 14 pass, 2 dynamic-dependency skips by design |
| `python -X utf8 scripts/ci/run_test_shard.py --profile fast --output <system-temp>` | PASS: 51/51 in 2.681523s under 15s; inventory `d95b3062…`, manifest `0b191bc2…` |
| `git diff --check` | PASS |
| changed-path boundary | PASS: 13 docs-only paths; root PROGRESS/HANDOFF and all package/schema/CLI/Skill/Adapter/code/remote surfaces unchanged |

The Fast profile includes the Authority, documentation-governance, v0.2 frozen-contract and component projection
checks affected by changing an ADR from Proposed to Accepted. No full Checkpoint or Promotion run was necessary for
this documentation-only acceptance closeout; R3 must obtain its own exact-SHA Promotion evidence when implemented.

## Known limits

- External observations are point-in-time facts from 2026-08-28 and do not reserve future registry/CLI names.
- ADR-0015 is Accepted and the Design is Approved, but R3 is only ready to start in a separate Workstream and remains
  unimplemented. R4/R5 and both local-maintenance tasks remain separately gated.
- No CLI/Skill/Adapter/package/schema/runtime behavior was changed or tested by this Validation.
