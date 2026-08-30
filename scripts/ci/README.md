# Local validation mapping registry

`change-mapping.json` is the only policy data source used by `validate_change.py`. The router algorithm is generic:
it resolves Git changed paths and Git-private Workstream subsystem/expected-write scope, maps those inputs to generic
mapping IDs, then selects exact registered test IDs whose dependencies intersect the mapped surface and whose
`allowed_stages` contains the requested stage.

CI7 keeps actual Git changed paths as the primary input. A Git-private subsystem is used only when neither actual
paths nor narrow expected writes are available. Expected writes never widen an actual-path selection: exact files
and a single wildcard in one basename are supported, while directory-wide `**`, trailing directories and generic
`*` declarations refuse formal evidence with required metadata. A path matching zero or multiple mappings also
fails closed.

## Add a test

Add exactly one entry to `tests` with all of these fields:

- `test_id`: the exact final unittest ID; wildcards are forbidden;
- `owner_surface` and `owner_shard`: the existing Promotion owner;
- `allowed_stages`: ordered subset of `fast`, `checkpoint`, `candidate`, ending with `promotion`;
- `cost_class` and `budget_seconds`;
- `dependencies`: one or more existing generic `path_mappings` IDs;
- `reason`: why those dependencies and that tier are adequate.

No selector or router-code change is needed. Discovery fails closed until the new exact ID is registered. Duplicate,
stale, wildcard, owner-mismatched, heavy lower-tier or Unknown-dependency entries are also rejected.

## Add a new surface

Only a genuinely new reusable surface needs one `path_mappings` data entry. Declare its stable ID, repository path
patterns, Orrery subsystem IDs, human-facing surfaces and security-risk flag. Then reference that ID from exact test
entries. Adapter, release and UI tasks use the same algorithm; they extend registry data rather than adding task,
branch or changed-path conditionals to Python.

Observatory routing uses provider-neutral `observatory-shell`, `observatory-graph`, `observatory-maintenance` and
`observatory-team-personal` surfaces. Graph-only paths do not select the Maintenance real-Git checkpoint. Maintenance
provider and Quick Remove paths retain that safety checkpoint. Common shell security selects only a small adjacency
declared on exact consumer tests.

An unmapped changed path or expected-write declaration produces a non-evidence refusal receipt. Its
`required_metadata` explains that the missing path mapping and exact test dependency metadata must be added.

## Check a change

Run `python -X utf8 scripts/ci/validate_change.py --stage fast --dry-run --explain` first. The JSON explains
changed paths, Workstream scope, mapping IDs, selected exact tests and owner/tier/cost/dependency metadata. A dry run
is never tier evidence. Formal Fast/Checkpoint evidence exists only when `validate_change.py` or
`run_test_shard.py` emits a successful versioned receipt within budget.

Every receipt adds versioned, non-authoritative `cost_diagnostics`: selected count, test runtime, router/setup wall,
Git-private mechanically counted reruns, slow IDs, changed test/CI file and line counts, independent optimization Workstream status and host usage.
Unavailable host usage is `Unknown`; token usage is never estimated or accepted from a selection plan. Optional
`--expected-future-runs`, `--baseline-test-runtime-seconds` and `--optimization-investment-seconds` produce a simple
break-even advisory. These values always have `gate_effect: none` and cannot affect PASS/FAIL, Authority, release or
automatic task creation.

An over-budget receipt classifies product failure, router over-selection, fixture/runtime variance or a genuinely
slow path. A feature task gets at most one `--bounded-triage` localization attempt and then reports centrally. The
same bottleneck produces a Git-private advisory recurrence finding only after two distinct Workstream IDs; it never
creates a task, ADR, State or relation fact.
