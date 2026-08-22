# C1 — Context-routing Oracle v0.2 static controls

Date: 2026-08-22
Result: PASS — Oracle static readiness; Pilot 010 not created or run
Development task: `C1` (not an R0/R1/R2 evidence-layer label)

## Scope

This validation covers development task C1: the research-only Oracle v0.2 package, public structured State fixture, layered verdict and
model-free control suite. It does not validate a model, routing treatment, Pilot 010 transport or new product policy.

The work ran in the independent `codex/context-routing-oracle-v0-2-static` worktree. Root `docs/PROGRESS.md` and
`docs/HANDOFF.md`, released Skill paths, Pilot 004–009 packets and external raw evidence remained unchanged.

## Static control evidence

```powershell
python -X utf8 experiments/context-routing/oracles/oracle-v0.2/oracle.py --verify-fixture
python -X utf8 experiments/context-routing/oracles/oracle-v0.2/oracle.py --self-test
python -X utf8 -m unittest tests.test_context_routing_oracle_v02 -v
```

- Fixture manifest: PASS, 7/7 files；公开 test discovery 为 4/4。
- Oracle self-test: PASS, 20/20 cases; 3 paraphrase positives, 6 contradictions, 6 semantic/State/scope mutations,
  one formal-invalid control, one unknown-wording manual review, one apparatus contamination and one baseline negative.
- Focused unit tests: PASS, 2/2.
- Self-test report explicitly records `model_calls: 0` and `pilot_created: false`.

## Layer behavior

- Missing public State fields fail `formal_validity`; a valid but stale/unknown current or future policy, or an
  unrecognized required future-version narrative, is reported under `state_future_version.omissions`.
- Public-call behavior, SQLite row/idempotence/index-column/future-version checks, Git scope and narrative facts remain
  separately visible under `semantic_quality`.
- Three declared paraphrases pass per fact family, two contradictions fail, and unknown wording requests manual review.
- An external-read control reports `overall_verdict: contaminated` without rewriting passing semantic/State layers.
- Renaming the SQLite index passes; swapping its columns fails. A correct unused helper cannot hide a broken public path.

## Repository validation

Final command evidence is recorded after the static package and authority-chain synchronization:

```powershell
python -X utf8 -m unittest tests.test_context_routing_oracle_v02 tests.test_context_routing_h2 tests.test_context_routing_benchmark -v
python -X utf8 -m unittest discover -s tests -v
python -X utf8 experiments/context-routing/pilots/pilot-004/operator/holdout_acceptance_v2.py --self-test
python -X utf8 experiments/context-routing/pilots/pilot-005/run_pilot.py --dry-run
python -X utf8 experiments/context-routing/pilots/pilot-006/run_pilot.py --dry-run
python -X utf8 experiments/context-routing/pilots/pilot-007/run_pilot.py --dry-run
python -X utf8 experiments/context-routing/pilots/pilot-008/run_pilot.py --dry-run
python -X utf8 experiments/context-routing/pilots/pilot-009/run_pilot.py --dry-run
python -X utf8 experiments/context-routing/validate_benchmark.py --repo-root .
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --docs <absolute-docs> --agents <absolute-AGENTS> --out <temp>/index.html
# PowerShell local-link scan over paths returned by: rg --files -g '*.md'
git diff --check
```

- Context-routing focused: PASS, 42/42 (C1 + H2/Scope + benchmark).
- Default full repository: PASS, 250 discovered；245 passed + 5 existing environment/optional-dependency skips.
- Frozen packets: Pilot 004 corrected read-only Oracle and Pilot 005–009 dry-runs PASS；Pilot 004–009 subdirectories
  have no Git diff.
- External frozen R0: PASS, 22/22 raw manifests from Pilot 005–009 verified read-only；Pilot 004 predates the R0
  manifest format and its frozen H hash is covered by the focused/full regression.
- Benchmark: PASS, 24 corpus tasks + 6 checked-in run records.
- Integrated structure: PASS；authority status `integrated candidate`，Authority Model 1 supported and strict-evaluation eligible.
- Isolated static site: PASS in a temporary output root；no repository `docs/_site` write or committed generated artifact.
- Markdown: PASS, 304 files／805 local links and images／0 missing targets.
- `git diff --check`: PASS.

The first isolated-site invocation supplied relative `--docs/--agents` paths and stopped before output because the
builder requires paths consistent with its absolute repository root. Re-running with resolved absolute paths passed;
no code, frozen input or repository-generated site was changed to accommodate the invocation error.

## Readiness and limits

Static readiness is **yes for requesting Pilot 010 design**. Run readiness is **no**: no Pilot 010 task IDs, packet,
Prompt, runtime profile or raw evidence root exists, and its task-specific launch gates have not been frozen. No model,
real user project, external raw copy, credential, cache, ADR, release Skill change, push, merge, tag or Release occurred.
