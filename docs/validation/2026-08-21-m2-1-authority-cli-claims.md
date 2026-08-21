# M2.1 完整 CLI Authority observations／claims

Date: 2026-08-21

Status: Worktree Candidate validated locally; integration pending

Scope: `codex/m2-1-authority-claims` at a linked worktree created from local `main@65ef774`. This record validates only the M2.1 internal CLI observation/claim contract. It does not validate M2.2, M2.3, a production consumer switch, a stable public API or a release.

Governing ADRs: [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

Plan: [M2.1 complete CLI Authority observations/claims](../implementation/plans/2026-08-21-m2-1-authority-cli-claims.md)

## Validated claims

- `cli-authority-observations-v1` deterministically selects authored Seed, numbered ADR, Design, Plan, State, Validation and Snapshot sources while excluding README, templates and unrelated Library files.
- Every document record retains repository-relative source, exact content SHA-256, normalized observation, Core claims, `must_not_infer` and evidence provenance. The repository input hash changes with any visible source bytes.
- ADR lifecycle and explicit `Amends`／`Supersedes` metadata are normalized; `Status: Superseded by ADR-N` is inverted into the normative replacement direction. Missing targets make the decision graph `Unknown`; duplicate IDs, contradictory metadata, self-relations and source symlinks fail closed.
- Seed, Design, Plan, State and Snapshot remain separate roles. Plan／State presence does not create an implementation claim.
- A Validation header reporting Passed／Failed is only a human／Agent assertion unless reproducible executable evidence is independently visible. It cannot create `validation_evidence=passed` or a `validated` conclusion.
- The complete bundle remains embedded in the existing warning-only CLI shadow. Legacy Accepted-ADR／entrance／pending／integrated behavior, human/JSON status and exit codes remain the production path.

## Self-host observation

The Candidate collector observed 1 Seed, 11 ADR, 7 Design, 13 Plan, 6 State, 46 Validation and 2 Snapshot documents in this worktree after this record was added. Seven explicit amendment relations resolved without a missing target. All 46 current Validation records remained `Unknown` because none uses the new exact machine-evidence input contract; this does not negate their authored evidence, but prevents the parser from inventing executable proof.

## Verification

| Check | Result |
| --- | --- |
| `tests.test_authority_cli_claims` | PASS — 10 executed tests; 1 real-symlink test skipped on Windows because the process lacks symlink privilege. |
| `python -X utf8 -m unittest discover -s tests -p 'test_authority_*.py' -q` | PASS — 139 tests; 1 Windows symlink privilege skip. |
| `python -X utf8 -m unittest discover -s tests -q` | PASS — 207 tests: 204 passed and 3 skipped (2 existing dynamic-dependency skips and 1 Windows symlink-privilege skip). |
| integrated structure validation | PASS — `integrated candidate`, Authority Model 1 supported／eligible. |
| static docsite build | PASS — temporary output 1125 KB; 11 ADR, 6 State, 7 subsystems, 2 snapshots, 83 classified docs, 13 plans and 6 library docs. |
| Markdown local-link scan | PASS — 272 Markdown files, 601 local links/images and 0 missing targets. |
| `git diff --check` | PASS after final State／Validation synchronization. |

## Remaining boundary

- The contract is internal and Candidate-only; it is not exported from the top-level CLI package and adds no command or stable JSON field.
- `fact_scope` defaults to `Unknown`; M2.1 does not infer Canonical/Candidate/Worktree from Git or coordinator state.
- No State prose, source tree or Git/Harness raw output is parsed into implementation claims. A future structured implementation/evidence adapter needs its own contract and validation.
- Existing Observatory collectors still have their M1 shadow behavior. Reconciliation and formal page projection belong to M2.2 and have not started.
- Release manifest, installer, new scaffold defaults, public model support and production switching belong to M2.3 and remain untouched.
