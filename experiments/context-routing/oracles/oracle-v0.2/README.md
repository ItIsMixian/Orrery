# Context-routing Oracle v0.2 static controls

Status: research apparatus; no model run and no product policy
Development task: `C1` (this is not an R0/R1/R2 evidence-layer label)

This package is the model-free readiness control for the
[task/Oracle v0.2 design](../../designs/real-development-task-oracle-v0.2.zh-CN.md). It is deliberately outside
`pilots/`: passing these controls does not create Pilot 010 or authorize a model sample.

The Oracle reports four independent layers:

1. `formal_validity` — public fixture shape, task identity and executable source form;
2. `semantic_quality` — public-call behavior, data safety, scope and prose consistency;
3. `state_future_version` — structured current State and the future-schema write-before-reject boundary;
4. `apparatus_contamination` — repository-boundary, unknown-tool and sealed-input evidence.

`apparatus_contamination` never rewrites the quality layers. A semantically correct candidate with an external read
is reported as `contaminated`, while its quality results remain visible.

The seven-file fixture exposes machine facts in `docs/state/application.facts.json`, validated against
`public-state.schema.json`. Natural-language checks use declared fact units with three positive paraphrases and two
contradictions per fact. Unknown wording becomes `manual_review_required`; it is not converted into a hidden lexical
failure. A missing or unknown required future-version narrative is also listed under
`state_future_version.omissions` for review. Behavior probes call the public API and inspect SQLite effects, so helper
names and index names are not part
of acceptance.

Run the controls without any provider credentials or model runtime:

```powershell
python experiments/context-routing/oracles/oracle-v0.2/oracle.py --verify-fixture
python experiments/context-routing/oracles/oracle-v0.2/oracle.py --self-test
```

The self-test covers baseline negatives, three paraphrase families, six contradiction cases, behavior/data/scope/
State mutations, an alternate SQLite index name, and apparatus contamination. It only creates temporary local Git
repositories and Python/SQLite processes.
