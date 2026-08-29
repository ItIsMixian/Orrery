# Local validation mapping registry

`change-mapping.json` is the only policy data source used by `validate_change.py`. The router algorithm is generic:
it resolves Git changed paths and Git-private Workstream subsystem/expected-write scope, maps those inputs to generic
mapping IDs, then selects exact registered test IDs whose dependencies intersect the mapped surface and whose
`allowed_stages` contains the requested stage.

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

An unmapped changed path or expected-write declaration produces a non-evidence refusal receipt. Its
`required_metadata` explains that the missing path mapping and exact test dependency metadata must be added.

## Check a change

Run `python -X utf8 scripts/ci/validate_change.py --stage fast --dry-run --explain` first. The JSON explains
changed paths, Workstream scope, mapping IDs, selected exact tests and owner/tier/cost/dependency metadata. A dry run
is never tier evidence. Formal Fast/Checkpoint evidence exists only when `validate_change.py` or
`run_test_shard.py` emits a successful versioned receipt within budget.
