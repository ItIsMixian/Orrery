# Validation：CI4 Opaque CLI Token Argument Reliability

Date: 2026-08-29

Status: Worktree Candidate local validation PASS；final exact-SHA hosted Fast／Promotion pending

Fact scope: `codex/ci4-opaque-cli-token-argument-reliability`, exact parent/task base
`codex/r3-orrery-brand-only-closeout@439c40fe5347689d8616cc057812d9a6438ca116`

## Root cause and bounded repair

R3 exact SHA `439c40fe5347689d8616cc057812d9a6438ca116` had Fast run `33231693802` PASS on
Windows and Ubuntu. Promotion run `33231693777` failed only in Ubuntu
`team-relations-execution`: `secrets.token_urlsafe(32)` validly produced an opaque confirmation token beginning with
`-`, while the test passed `"--confirmation-token", token` as two argv entries. `argparse` therefore treated the
value as an option and raised `argument --confirmation-token: expected one argument`. Windows passed because its
random token did not trigger that shape; it was not evidence that the invocation was reliable.

CI4 changes only current apply／undo CLI tests and usage examples to pass one argv entry:

```text
--confirmation-token=<opaque-token>
```

The token is never interpolated into a shell command. A new deterministic regression patches token generation at
the test boundary to return `-leading-dash-apply-token` and `-leading-dash-undo-token`, then executes the real CLI
apply and undo paths and validates committed receipts／append-only history. The original full topology test keeps
real random token generation but now uses the same safe argv form.

## Current-call audit and unchanged product contract

A repository audit excluded historical Validation／DEVLOG／Pilot／Library／Snapshot／completed Plan material. The
only active `--confirmation-token` call sites were the product parser declarations and this test's apply／undo argv.
No active documentation example required a change. Historical commands remain byte-preserved.

CI4 does not modify `secrets.token_urlsafe`, token entropy/hash/storage, schema, protocol, confirmation consumption,
transaction journal, receipt/undo semantics, Core/CLI parser, component versions, Adapter capability, release
manifest or v0.2.0. R3 brand tests prove current brand allowlist, stable Python／CLI／Skill／Adapter identity,
protocol/history hash denylist and first-release asset rule remain unchanged.

## Local validation

| Check | Result |
| --- | --- |
| deterministic leading-dash apply／undo method | 1/1 PASS, 48.112s |
| original full-topology CLI apply→receipt→undo flow | 1/1 PASS, 227.736s |
| `python -m unittest tests.test_workstream_relation_execution -v` | 5/5 PASS, 501.427s |
| `python -m unittest tests.test_workstream_relations -v` | 15/15 PASS, 30.959s |
| `python -m unittest tests.test_brand_contract -v` | 6/6 PASS |
| `python scripts/ci/test_inventory.py` | PASS; 386 IDs, 27 shards, 57 Fast, 78 Checkpoint |
| `python scripts/ci/validate_ci.py --all` | PASS |
| `python scripts/ci/run_test_shard.py --profile fast ...` | 57/57 PASS, 3.217789s／15s |
| integrated installation validator | PASS; `integrated_candidate`, Core 0.1.14／CLI 0.1.18／Core API 1 |
| isolated docsite build to a system-temp `index.html` | PASS; 2,068,862 bytes, 155 documents |
| repository gates | PASS; 664 paths, 358 Markdown, 1002 links, no forbidden artifacts |
| `git diff --check` | PASS |

The complete local Promotion was intentionally not repeated. The new test is mechanically collected by the
existing `test_workstream_relation_execution.*` selector in the 300-second `team-relations-execution` Promotion
shard, so inventory rises from 385 to 386 without changing shard count, budget, Fast or Checkpoint selections.
The first optional docsite invocation passed a directory rather than the builder's required output file and was
rejected with `PermissionError`; it wrote nothing to the repository. The corrected isolated file-target invocation
is the PASS recorded above.

## Final hosted gate and stop boundary

The clean Candidate must be pushed to `promotion/ci4-opaque-cli-token-reliability`. The same exact SHA must obtain
Fast Windows／Ubuntu PASS plus Promotion 59/59 jobs and both required `smoke-test` checks PASS. Any red result requires
a new SHA and a complete rerun. Hosted run/job evidence is reported in the task receipt rather than appended as a
docs-only commit.

CI4 does not merge `main`, change branch protection, tag or publish a Release, migrate directories or Codex data,
create the deferred S1 repository, delete history, or perform a real self-host relation apply.
