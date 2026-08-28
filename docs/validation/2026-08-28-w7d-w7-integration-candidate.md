# W7D W7 Integration Candidate Validation

Date: 2026-08-28

Fact scope: non-`main` Candidate `codex/w7d-w7-integration-candidate`

## Exact inputs and write gate

- Task base was verified as `codex/ci2-tiered-test-performance@8b635b18ece85d2d051adaf6961057b64011205c`.
- Additive sibling was verified as `codex/w7c-b-production-workstream-relation-graph@d411fd6e775d59332de37784cd781339d2835661`.
- Git ancestry was checked as W7A `52e88b8` → W7B `1160df4` → CI2 `8b635b1`; W7C-B remains a sibling of CI2.
- Both input worktrees were clean. W7C-A `a39f6a7` was not merged separately: its experiment and Validation trees compare byte-for-byte equal with the corresponding W7C-B trees.
- Before product writes, Git-private `W7D-w7-integration-candidate` was registered with primary subsystem `project-structure`, affected collaboration/documentation/release/test subsystems, CI2 as parent/task base, and implementation, shared State, manifest, Validation, root-entry and browser surfaces declared.

## Semantic integration

`d411fd6` was merged additively with `--no-ff` and no source branch rewrite. Conflicts in DEVLOG, Implementation/Validation indexes, four subsystem State Docs and `scripts/ci/test-shards.json` were resolved by preserving both input histories and reconciling their current facts. `packages/component-versions.json` resolves to Core 0.1.14, CLI 0.1.18, Observatory 0.1.9 and Core API 1.

The CI manifest remains schema 2. Fast remains capped at 15 seconds, Checkpoint at 90 seconds and the dedicated `team-relations-execution` Promotion shard at 300 seconds. The W7C-B dependency-light contracts are assigned to Fast and Checkpoint; both complete W7C modules occur once in the `team-observatory` Promotion shard. After the hosted preflight and aggregate-ordering regressions described below, mechanical inventory reports 377 unique test IDs, 27 shards, 51 Fast tests and 70 Checkpoint tests with no missing, duplicate or dead selector.

W7B is recorded as an implemented Candidate execution boundary: local discovery, planning, human confirmation, transaction apply, recovery, receipt and undo are covered in isolated Git fixtures. No self-host relation apply, default UI execution entry or public release occurred. The Workstream Graph exposes no apply, undo, close, delete or other execution control, and the central Team view remains request-only/read-only.

## Local verification before the stable integration commit

- Focused W7C contract: 13/13 PASS in 20.744 seconds.
- Initial Fast profile: 51/51 PASS in 2.132432 seconds, under the 15-second budget. After the final hosted repair, the same 51-test Fast profile passed again in 2.328416 seconds.
- Initial Checkpoint profile: 68/68 PASS in 81.201647 seconds, under the 90-second budget; no budget relaxation was made. The later preflight- and aggregate-ordering regressions are the 69th and 70th final Checkpoint selectors and passed in the focused CI contract; the full Checkpoint was not mechanically rerun.
- Final CI inventory and validator: PASS at 377 IDs／27 shards／51 Fast／70 Checkpoint.
- Component projection validator: PASS for Core 0.1.14／CLI 0.1.18／Observatory 0.1.9.
- Integrated installation validation passed with `authority_status=integrated_candidate`, Core 0.1.14, CLI 0.1.18 and Core API 1.
- Repository gates passed over 653 tracked/untracked paths, 349 Markdown files and 962 local links with no forbidden runtime/generated artifact.
- After the aggregate repair and current closeout documentation, the isolated docsite rebuilt to 1,951,461 bytes with 14 ADRs, 6 States, 7 subsystems, 2 snapshots, 147 documents, 28 plans and 7 Library entries.
- `node --check` passed for the visual prototype, and `git diff --check` passed after documentation integration.
- The dedicated W7B Promotion shard is intentionally deferred until the first stable integration commit and will be run exactly once; the closeout commit records that result without changing implementation or test selection afterward.

The complete local repository Promotion was not run. Hosted exact-SHA Windows and Ubuntu checks remain the cross-platform full gate.

## Real in-app Chromium acceptance

The root-only synthetic browser fixture was served from the generated sibling page and exercised in the real in-app Chromium runtime.

- Desktop at 1280×900: Succession／Dependency／Conflict lenses, subsystem/runtime filters, history expansion/collapse, node and edge inspector, Enter/Space keyboard operation and a repository-anchor safe link all worked. The Dependency inspector selected `rel-w5e-ci1-dependency`; the Conflict inspector selected the direct L3 CI2-late→W5E pair. `scrollWidth=1265` at `innerWidth=1280`, so horizontal overflow was absent.
- Mobile at 390×844: controls and accessible ledger reduced to one column, all three lenses remained available, Enter/Space opened edge and node inspection, and the W5E node kept its independent lifecycle/runtime/evidence/Scope axes. `scrollWidth=375` at `innerWidth=390`, so horizontal overflow was absent.
- Both sizes reported zero browser console warnings/errors and zero execution buttons. Safe links remained same-document repository anchors; opaque evidence was not made navigable.

## One-time local W7B Promotion

The stable implementation merge commit is `2a5d5d4d0065324e9453f0a0522fbc92011a6186`. The dedicated shard was run exactly once on that clean commit:

```text
python -X utf8 scripts/ci/run_test_shard.py --shard team-relations-execution --output <temp>
4/4 test outcomes: success
runner verdict: FAIL — 311.803221s > 300s hard budget
```

Per-test timings were 0.002979s, 88.452008s, 162.034236s and 61.313722s. The corresponding CI2 record was 0.003037s, 77.326388s, 135.184251s and 52.223925s, total 264.737873s. The three Git-backed journeys slowed by 14.4%, 19.9% and 17.4% in the later run. `git diff 8b635b1..2a5d5d4` is empty for the execution test, Core/CLI implementation and shard runner; W7C-B does not alter this path. This is therefore retained as a local timing-budget miss rather than rewritten as a product assertion failure.

The 300-second budget and four-test selection were not changed, and the local Promotion was not rerun. Hosted exact-SHA Windows/Ubuntu execution is the next independent measurement; if either required check fails, a new Candidate commit and new hosted run are required.

## Remote Promotion closeout

Initial exact Candidate `b7d2df6a94d496a6d7aa2225024f737314cb62e6` was pushed to `promotion/w7d-w7-integration-candidate`. GitHub Actions run `33192497123` failed in preflight before any Promotion matrix test: `validate_ci.py --all` performs final unittest discovery, but the preflight job had not installed the docsite requirements, so Ubuntu could not import `mistune`.

The repair installs the same requirements (and wheel) before exact-SHA binding/inventory validation, and extends the CI validator plus a focused regression to require that ordering. Focused CI contract 10/10, final inventory/validator and Fast 51/51 pass locally. The first hosted failure remains evidence; a new exact SHA must run both required checks.

Repaired exact Candidate `25a94aa82ddfa63eddf804eb92632aa1676d6a58` reached the full matrix in GitHub Actions run `33192808364`. Its hosted W7B `team-relations-execution` shard passed on Windows in 2m36s and Ubuntu in 20s, independently satisfying the unchanged 300-second budget. Required checks still failed because independent sharding exposed three latent contracts:

- W7C-B's corrected-W7A test read self-host Git-private sessions, which do not exist in a clean runner; both OSes failed `team-ui-server`.
- Authority shard isolation exposed an un-preloaded lazy `_llm` sibling import and a stale expected amendment map that omitted ADR-0014; both OSes failed `authority-core`.
- Three maintenance tests compared Windows path spellings directly even though production normalizes real paths; Windows workspace action/queue/remove failed, while the corresponding Ubuntu shards passed.

The next repair uses the committed synthetic/non-authoritative compatibility provider for W7C state-axis assertions while retaining a separate real missing-store zero-write test; preloads the local `_llm` contract and adds ADR-0014 to the expected Core relation map; and applies the same `realpath`/`normcase` comparison semantics to test workspace selection. Local repair evidence is workspace path-sensitive 3/3 in 256.957s, `team-ui-server` 16/16 in 39.547s and `authority-core` 127/127 in 44.340s with one existing Windows symlink-privilege skip.

Exact Candidate `d9f55b5bd71634be23a54fe2fc50d107881de930` ran as GitHub Actions `33193955085`. Every Windows and Ubuntu Promotion shard, both repository gates and the dedicated W7B shard passed; hosted W7B was 2m32s on Windows and 31s on Ubuntu. The two required aggregate jobs nevertheless failed after downloading all 27 shard artifacts because aggregate-time final unittest discovery again ran without the docsite requirements and could not import `mistune`. This is an aggregate-job setup defect, not a shard or product-test failure.

The repair installs wheel plus the docsite requirements in both aggregate jobs before artifact inventory aggregation, enables the same dependency cache and extends `validate_ci.py` with a two-platform ordering contract and focused regression. It does not change manifest budgets, selectors, product execution authority or relation UI. The added regression accounts for the final 377/27/51/70 inventory. A new exact SHA must run both required checks.

The final repaired Candidate SHA and hosted run/check results are reported after execution. A green non-`main` Candidate remains only ready for maintainer-authorized main fast-forward; this task does not merge main, create a tag/Release, change branch protection or delete any branch, worktree, commit or Validation.
