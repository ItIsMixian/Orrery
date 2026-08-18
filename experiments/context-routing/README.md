# Context-routing benchmark

> **Status:** research infrastructure; not part of the released Project Orrery Skill
> **Authority:** none; results may support a future ADR but do not change the current architecture

This benchmark is the first implementation step proposed by the [task-context and provenance research note](../../docs/library/2026-08-17-task-context-provenance-and-documentation-overhead.md). It compares context-routing strategies before Project Orrery adopts a Context Manifest, access receipts, or selective retrieval as a product requirement.

## What exists in this phase

- `corpus.json` contains reconstructed tasks grounded in real Project Orrery commits.
- `schemas/task-corpus.schema.json` documents the portable task format.
- `schemas/run-record.schema.json` documents run metadata and access events.
- `validate_benchmark.py` validates corpus structure, safe relative paths, Git references, reference diffs, and any captured run records without third-party packages.
- `runs/` contains local or publishable benchmark evidence with explicit provenance.
- `results/` contains evaluator comparisons and apparatus findings; a report is not an architecture decision.
- Pilot-003's runner freezes a Harness-authored `product-changes.json` for every run, including Git-untracked product files, and its checksummed operator-side security oracle tests failure ordering and secret-free persistence independently of Agent-authored tests.

The historical commit diff is a reproducible oracle for expected write paths. `curated_context_paths` are hypotheses about useful reads, not proof that every listed file is necessary or sufficient.

## Pilot history and next run

The root-level [pilot-001 instructions](START-PILOT.zh-CN.md), `prepare_pilot.ps1`, and `prompts/` files are frozen historical inputs. Do not reuse or edit them after collection.

Pilot 001 has been collected and independently checked at the repository boundary. Read the [comparison report](results/2026-08-17-po-cr-004-pilot-001.md) before reusing its prompts: the run exposed missing gold information and uncontrolled external Skill context, so it is not valid evidence for choosing a routing variant.

The corrected [pilot-002 packet](pilots/pilot-002/START.zh-CN.md) has now been run. All three variants produced accepted single-file results with matching Prompt and overlay hashes; see the [pilot-002 comparison](results/2026-08-17-po-cr-004-pilot-002.md). A reported seven content reads, while B and C each reported one. The result is a directional fixed-chain overhead signal, not an architecture decision: model-facing access remains self-reported and execution-profile metadata was not captured.

The [pilot-003 packet](pilots/pilot-003/START.zh-CN.md) implements that next apparatus step across three task categories and all A/B/C variants: a medium bilingual multi-file documentation task, a high-risk cross-module provider-settings task, and a high-risk credential-persistence task. It records the shared model, reasoning, permission, network, harness, and time-budget settings on the operator side; hashes the execution profile, schema, overlay, and full Prompt; requires structured pre-write Manifest and Selected Evidence receipts; synchronizes interventions across variants; and validates nine isolated one-commit repositories. A one-command local runner prepares, launches, captures Codex JSONL, resumes without hidden retries, seals, validates, and summarizes the nine runs.

A real GPT-5.6 Terra / medium run has now been collected; see the [pilot-003 report](results/2026-08-18-pilot-003-terra-medium.md). All nine Agents completed and their isolated repositories passed independent compile/tests, while the sealed run remained protocol-invalid because prompt revision v1 did not make the string-only `validation` receipt format salient enough. The result is useful directional evidence, not an architecture decision. It motivated the non-authoritative [Orrery Context Aperture candidate](designs/context-aperture-v0.1.zh-CN.md): selective initial evidence with reason-coded expansion and explicit quality gates. JSONL improves host-side provenance while model-facing content reads remain Agent self-report unless the harness exposes the exact content delivered to the model.

The repaired Harness has also completed a smaller [B/C confirmatory run](results/2026-08-18-pilot-003-bc-confirmatory-terra-medium.md) over the two high-risk tasks. The result did not pass the adoption gate: C reported fewer content reads but consumed about 75% more input tokens than B and failed independent acceptance on both tasks; B passed one of two. The sealed validator also revealed two overly rigid security-oracle assumptions, which were repaired and re-evaluated read-only without changing the raw repositories.

Pilot 004 has completed the three prospective B/H holdout tasks proposed in its [task design](pilots/pilot-004/TASK-DESIGN.zh-CN.md): recoverable credential revocation, trustworthy update-manifest caching, and a shared pre-upgrade compatibility gate. Read the [Pilot 004 report](results/2026-08-18-pilot-004-bh-holdout-terra-medium.md). The frozen v1 Oracle produced false positives and remains preserved as an apparatus failure; a read-only v2 review passed all six repositories. B and H both achieved 3/3 corrected acceptance, but H used 47% more input tokens overall and took about 15% longer, so H is not adopted. B remains the comparison baseline while a slimmer H2 is designed.

The slimmer [Context Aperture H2 candidate](designs/context-aperture-v0.2-h2.zh-CN.md) and its [content-read apparatus](harness/README.md) now exist. H2 removes model-authored Manifest, Selected Evidence, and receipt prose. The controlled read proxy marks exact UTF-8 slices, and an independent validator rejects any unapproved command or unexpected item in the complete `codex exec --json` stream before cross-checking output hashes. Hooks remain an optional real-time enforcement layer: ten Windows CLI 0.147.0 smoke attempts did not emit Hook audit events, so no current run may claim Hook enforcement. Pilot 005 preserved a shared apparatus failure; corrected Pilot 006 passed B and H2 on both new high-risk tasks. H2 still used 18.5% more total input tokens, 22.5% more output tokens, and 7.2% more Agent time, so it is not adopted. Read the [combined result](results/2026-08-18-pilot-005-006-bh2-terra-medium.md) and [validation](../../docs/validation/2026-08-18-pilot-005-006-bh2.md).

The next packet is [Pilot 007](pilots/pilot-007/README.md), a direct P/B adoption experiment. It freezes B as pre-read Context Manifest + reason-coded expansion + final Access Summary, keeps receipts out of the repository, and compares it with the current released process on three new tasks. The apparatus and baseline negative controls are prepared; model runs have not started.

## Current independent-access boundary

Project Orrery still does not provide a general filesystem security boundary. In controlled benchmark runs it can now independently prove that a proxy slice appeared in a captured CLI command output, while rejecting runs whose JSONL contains direct reads, unknown tools, missing outputs, or mismatched hashes. Therefore:

- an agent-authored list of files is classified as `agent` evidence, not independent observation;
- `manual` evidence is reviewable but not tool-generated;
- only validated `harness` or `tool_wrapper` events count as independently observed access in benchmark summaries;
- JSONL validation is post-hoc rejection, not real-time prevention;
- no run should claim Hook enforcement unless its Hook audit log independently validates.

This boundary prevents the experiment from extending a controlled-run result to ordinary Codex sessions, Hosted tools, attention, comprehension, or causal use of evidence.

## Variants

| Variant | Policy |
|---|---|
| `A` | Current fixed entry chain followed by ordinary search |
| `B` | Task classification, hierarchical localization, generated Context Manifest, and receipt capture |
| `C` | Variant B plus selective retrieval/compression and reason-coded scope expansion |

Variant B and C runs may initially be manual pilots. Their evidence origin must remain explicit.

## Validate the corpus

From the repository root:

```bash
python experiments/context-routing/validate_benchmark.py --repo-root .
```

The validator checks that each historical reference commit exists and that every `reference_changed_paths` entry appears in the corresponding Git diff.

To validate run records too, place JSON files under `experiments/context-routing/runs/` and rerun the same command. Files beginning with `_` are ignored.

## Replay a task

1. Select one task from `corpus.json`.
2. Create a disposable worktree at its `base_commit`.
3. Run one routing variant with the same task prompt, model family, permission profile, and validation budget used for the comparison runs.
4. Record events and metrics using `schemas/run-record.schema.json`.
5. Validate the run, then compare its resulting diff with `reference_changed_paths` and its outcome with the task's acceptance criteria.

Never run replay tasks in the maintainer's active worktree. Benchmark worktrees are disposable experiment surfaces, not release branches.

## Evidence levels

| `observed_by` | Meaning | Counts as independent access evidence? |
|---|---|---|
| `harness` | Emitted by the agent host at the tool/model boundary | Yes |
| `tool_wrapper` | Emitted by a controlled command or file-access wrapper | Yes, within the wrapper's coverage |
| `manual` | Entered by a human reviewer from visible evidence | No |
| `agent` | Reported by the model or agent itself | No |

Directory enumeration, search queries, and actual content reads use different event types. Seeing a path name is not equivalent to receiving its contents.

## Metrics

The run schema can record:

- task acceptance and validation status;
- token, time, and provider cost when available;
- enumerated, searched, and content-read file counts;
- irrelevant reads, necessary reads missed, and scope expansions;
- documents touched and documentation synchronization time;
- conflict warning delay and false-positive/false-negative counts.

Unknown values should remain `null`; they must not be replaced with zero.

## Decision gate

A future architecture ADR requires enough real runs to show that a candidate reduces context or documentation cost without a material regression in correctness, dependency coverage, or auditability. The planned corpus size is 20–30 tasks spanning local code, documentation, cross-module, security, release, CI, and architecture work.
