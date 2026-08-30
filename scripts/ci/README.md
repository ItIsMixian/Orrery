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
`run_test_shard.py` emits a successful versioned receipt within budget. Direct unittest remains local debugging and
cannot emit formal tier evidence.

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

## Acceptance policy and validation leases

`acceptance_policy` schema 1 is additive. It declares a stable Workstream/scope binding, `all_of` composition and
one or more gates. Each gate has an ID, one of `human_experience`, `contract`, `measurement`,
`operation_authorization` or `platform_matrix`, a `required_before` stage, authority role, exact contract path plus
blob OID, relevant stable surface IDs, status, evidence requirements and a hashed receipt reference. V1 does not
support `any_of`, weighted voting, gate omission or an `acceptance_mode` shortcut.

Human-experience and operation gates require a human receipt for the declared role; operation authorization must be
action-time. Contract, measurement and matrix receipts may be mechanical only when they carry the matching prior
human approval of the exact contract. Unknown kinds/statuses, Agent acceptance, missing role/CAS fields, forged
contract/receipt/fingerprint and stale scope all remain Unknown or refused. The bounded Team projection exposes
only gate metadata and request-only capability; Personal remains zero-network and no evidence body, Prompt,
transcript, source, diff or credential is projected.

Sessions without policy are `legacy-unclassified` during shadow rollout. A human-authorized Git-private enforcement
record may require gates for Workstreams created after activation; active legacy adoption remains explicit and
human-reviewed. `acceptance-profiles-v1.json` provides data-only examples for UI experience, deterministic contract,
measurement, migration/deletion/release authorization, platform matrix and mixed all-of work.

An enforced formal request receives one Git-private `orrery-validation-lease-v1`. The lease binds Workstream, scope
revision, requested stage, relevant surface fingerprint, exact allowed test IDs/count, local p95 prediction, fixed
stage budget, receipt inputs and one run identity. The shard runner consumes it before loading tests. Missing,
forged, stale, expired, consumed, stage-mismatched or budget-mismatched leases fail closed. An unchanged completed
request returns its prior receipt. Failure or timeout becomes `validation-cost-blocked`; the same source cannot rerun
without a versioned human maintainer override bound to that request.

In `iterating`, only the non-evidence `focused` stage is allowed: at most 20 mapped tests, 20 seconds per run and 120
cumulative seconds per Workstream scope revision. Human-experience work cannot reach Fast/Checkpoint until accepted.
Fast preflight refuses more than 20 tests or predicted p95 above 10 seconds. Checkpoint refuses a single-test p95
above 30 seconds or total p95 above 60 seconds. Unknown timing history is reported honestly and refuses conservatively
under enforcement. Git-private summaries are updated only from valid receipts and include router plus runner
setup/build cost. These predictive limits preserve the fixed 15/90 second stage budgets; they are not waivers or
stage substitution.

Review packages remain bounded to purpose, invariants, three to five representative cases, negative cases, known
gaps, exact contract/fingerprint and reproduction reference. Integration may consume child receipt references but
reruns only integration-owned gates; replaying child-owned gates is a contract error. Hosted/public enforcement is a
separate maintainer decision, so existing workflow text and required-check names remain unchanged.
