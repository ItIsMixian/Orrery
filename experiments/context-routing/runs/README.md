# Benchmark run records

Place real run records here using `../schemas/run-record.schema.json`.

- Keep unknown measurements as `null`.
- Mark every event with its real `observed_by` origin.
- Do not classify agent self-report as harness evidence.
- Do not publish secrets, repository excerpts, provider credentials, or machine-specific absolute paths.
- Prefix local templates or notes with `_` if they should be ignored by `validate_benchmark.py`.

Captured pilot records:

- `2026-08-17-po-cr-004-a-pilot-001.json`
- `2026-08-17-po-cr-004-b-pilot-001.json`
- `2026-08-17-po-cr-004-c-pilot-001.json`
- `2026-08-17-po-cr-004-a-pilot-002.json`
- `2026-08-17-po-cr-004-b-pilot-002.json`
- `2026-08-17-po-cr-004-c-pilot-002.json`

Original access events are Agent self-reports; only post-run evaluator events are independently observed by the listed tool wrapper. Pilot 001 records deliberately mark `apparatus_valid: false` because their comparison was confounded. Pilot 002 records use `apparatus_valid: null`: repository artifacts are controlled and correct, but model-facing reads and execution-profile equivalence were not independently established. Read the [pilot 001 comparison](../results/2026-08-17-po-cr-004-pilot-001.md) and [pilot 002 comparison](../results/2026-08-17-po-cr-004-pilot-002.md) before interpreting them.
