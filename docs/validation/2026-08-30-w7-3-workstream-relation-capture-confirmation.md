# W7.3 Workstream Relation Capture & Confirmation Validation

Date: 2026-08-30

Status: PENDING — implementation evidence not yet accepted

Authority sources:

- [ADR-0017](../decisions/0017-workstream-relation-capture-and-confirmation-authority.md)
- [Approved Design](../design/workstream-relation-capture-and-confirmation.md)
- [W7.3 Plan and 2026-08-30 Scope Amendment](../implementation/plans/2026-08-29-w7-3-workstream-relation-capture.md)

## Fact scope and authority acknowledgment

- Candidate branch/worktree fact scope only; not Canonical, released, public or default-enabled.
- Exact code base: `codex/u1-u2-integration-baseline@3fc7e7aacedafa8fbd20f9f79ddb8cf5784a0ef3`.
- Exact authority commit: `6315415075fb78b61d9a5bb835725bced0bc9ce1`; its parent is the exact code base.
- The eight requested authority blobs were read and verified before resumed product writes; Git-private session scope
  revision 3 binds their exact blob OIDs and expected validation surfaces.
- This implementation record is separate from the docs-only
  [ADR-0017 decision contract](2026-08-29-w7-3-relation-capture-decision-contract.md).

## Expected evidence

- exact base and authority amendment commit acknowledgment;
- versioned proposal/confirmation/role/series contracts and compatibility;
- automatic exact-base lineage plus human-confirmed gate/absorbs paths;
- task-owner/integrator/CAS/spoof/stale/legacy/privacy negative matrix;
- A3→A4 and CI6→CI7 repair proposals without effective-history backfill;
- distinct task-series, status taxonomy, comparison suggestions and true-conflict projection;
- Personal/Team/inbox/Graph desktop/mobile browser acceptance;
- Fast/Checkpoint, repository/release/private-artifact/diff evidence.

## Pending command ledger

| Surface | Command/evidence | Result |
|---|---|---|
| Core/capture/schema | `python -m pytest tests/test_workstream_relation_capture.py -q` | Pending |
| CLI/Harness | focused W7.3 CLI and Harness JSON tests | Pending |
| Observatory/Graph | focused Unified Observatory and Graph tests | Pending |
| Self-host | bounded inspect receipts for A/CI series, proposals and conflict/comparison separation | Pending |
| Browser | Browser skill at 1440×900 and 390×844 for Personal, Team and Graph | Pending |
| CI6 | dry-run, Fast and Checkpoint | Pending |
| Repository/release | repository gates, release dry build, secret/generated/private-state/package exclusion | Pending |
| Hygiene | `git diff --check` and clean exact Candidate | Pending |

## Results

Pending. No item becomes PASS until its exact implementation evidence is reproducible.
