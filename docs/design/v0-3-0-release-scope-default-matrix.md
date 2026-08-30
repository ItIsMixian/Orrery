# Approved Design: Orrery v0.3.0 Release Scope and Default Matrix

Status: Approved

Date: 2026-08-30

Governing decision: [ADR-0021](../decisions/0021-v0-3-0-release-scope-default-matrix.md)

## Feature matrix

| Class | 0.3.0 surface | Required release expression |
|---|---|---|
| In | Unified Observatory, Authority/Rules, W7.3, CI7, Personal, Team opt-in, Maintenance Phase 0–2, Quick Remove, Orrery brand | Only after Canonical integration, exact Validation and final Candidate acceptance |
| 0.3.1 | DSH Store, `orrery` CLI alias, OS scheduler | Absent from assets/default/support list |
| Deferred | auto worktree delete, PyPI/wheels, independent Adapters, stable Authority API, D2, C2 | No promised version |
| Experimental | Harness JSON, Claude, DeepSeek, Team LAN/manual Host switch | source-only/unreleased, exact-scope wording |
| Unsupported | auto leader, cloud relay, remote execution/delete, Graph execution, Claude authenticated route | Explicitly shown as unsupported |

## Cohort defaults

| Cohort | Observatory | Authority/Rules | Allowed ordinary update | Explicit action |
|---|---|---|---|---|
| New empty | Unified | Model 1 / Rules 1 / migration-pending | create-only scaffold | project authority adoption |
| Brownfield | existing/legacy | missing/legacy preserved | missing files + allowlisted tools with backup | adoption and semantic migration |
| Orrery 0.2 | legacy | missing selectors preserved | offline tool upgrade | receipt-bound Unified/Model/Rules migration |
| Explicit 0.3 migration | Unified | exact supported selectors | compatible managed-tool update | rollback/future migration |
| Unknown/invalid/future | raw Markdown read-only | unsupported | compatibility report only | supported repair/migration first |

Every cohort preserves AGENTS, Seed, State, ADR, Design, Plan, Validation, credentials and generated/cache boundaries.
Unknown selectors fail before managed writes. Migration and restore bind exact before/after digests and reviewed receipt.

## Distribution and manifest

- Assets: `project-orrery-v0.3.0.zip` and `project-orrery-v0.3.0.sha256` only.
- Archive root remains `project-orrery/`; display brand is Orrery; stable CLI/package/import/protocol IDs remain
  `project-orrery`／`project_orrery_*`.
- Core/CLI/Observatory are embedded tracked source with exact component versions, not independent releases.
- The W7.3 Observatory Graph embeds the exact ADR-0022/GX2-reviewed local ELK.js runtime and license/provenance as
  tracked package input. No CDN, npm install or build-time download is part of installation or runtime.
- ADR-0023 retains the frozen handwritten geometry as an explicit local legacy engine. It shares Orrery's semantic
  input, is visibly labelled/manual-only and cannot activate automatically when ELK fails.
- Candidate manifest records project manifest format, document schema, Authority Model and Rules as four orthogonal
  default values with discrete support sets; it also binds exact source SHA, components, Adapters, cohorts, assets,
  URLs and release date.
- Current public 0.2 manifest and old repository URLs are replaced only in the reviewed 0.3 Candidate commit; historical
  v0.2 Git objects remain unchanged.

## Packaging

Builder input is `(exact commit, reviewed manifest blob, allowlist version, builder contract version)`. Entries come
from `git ls-tree`/`git cat-file`, are sorted POSIX paths under one root, and use fixed timestamp, Unix mode, creator,
empty extra/comment and `ZIP_STORED`. Symlink, duplicate/case collision, absolute/parent path and untracked input fail.
Entry receipt records path/OID/mode/size/hash plus archive hash.

Windows and Ubuntu Promotion compare source SHA, manifest hash, builder contract, entry receipt, ZIP and checksum. A
waiver is valid only with matching entries and explicit maintainer acceptance naming one exact Ubuntu run.

The entry receipt separately binds every vendored ELK runtime/license/provenance path and hash. Missing, extra,
untracked or hash-mismatched layout assets fail before archive creation.

## Runtime and upgrade portfolios

- Codex final ZIP: clean install, unique discovery, explicit/implicit invocation, Unified start/single URL/stop/restart,
  0.2 tool update, migration/rollback, dependency failure, uninstall/reinstall and author-file preservation.
- Harness JSON: final bundle Windows/Ubuntu subprocess request/failure/remove; `launch=false` remains explicit.
- New, brownfield, 0.2 tool update, 0.2 explicit migration, unknown/invalid, offline, old-tools/new-project and mixed
  component portfolios all fail closed and prove recovery.
- Final Unified Browser review covers all primary pages at desktop/mobile and binds maintainer acceptance to exact SHA.

## Validation ownership

Final RC consumes valid child receipts for A4, W7.3 and CI7. It runs one clean central Fast/Checkpoint after merge,
then Candidate, packaging, migration, final-runtime and cross-platform Promotion gates owned by RC. Manually listing
and replaying every child unittest suite is prohibited unless CI7 reports a stale/missing receipt for that exact
surface. Same-fingerprint retry follows CI7 no-repeat rules.

## Publication sequence

```text
accepted central dependencies
→ final webpage acceptance
→ manifest/archive freeze commit
→ local Candidate/runtime
→ non-main exact-SHA Windows+Ubuntu Promotion
→ same-SHA protected main
→ separately authorized annotated tag
→ tag rebuild/checksum
→ separately authorized GitHub Release
→ remote download hash verification
```

Any source change restarts from a new SHA. No stage may inherit an older SHA's result.
