# ADR-0021: Orrery v0.3.0 Release Scope, Defaults and Publication Authority

Status: Accepted

Date: 2026-08-30

Source proposal: `codex/rel3-v0-3-0-release-scope-default-matrix@ec2b09b447cd3cd2631c1ba94aac4c1e901476cc`

Related: [ADR-0011](0011-authority-model-version-and-compatibility.md),
[ADR-0015](0015-orrery-brand-and-compatibility-contract.md),
[ADR-0016](0016-unified-observatory-shell-and-single-local-entry.md),
[ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md),
[ADR-0020](0020-workstream-program-and-phase-hierarchy.md)

## Context

Orrery v0.2.0 remains the only public release. The source tree and local integration line contain substantially newer
Core/CLI/Observatory, Authority, Unified, collaboration and maintenance work, but source existence and local browser
acceptance do not define a public product. REL3 prepared a release scope/default/distribution proposal and the
maintainer accepted its six choices, with two corrections: W7.3 and CI7 use their latest accepted authority, and the
Final RC must consume child receipts rather than replay every child test suite.

## Decision

1. **Target version.** The next planned public version is `0.3.0`. This decision authorizes release preparation, not
   main/tag/asset/GitHub Release actions.
2. **Included scope.** Candidate inputs may include accepted Unified Observatory U2/W7.2, Authority Model 1/A3/A4,
   W7.3 relation capture plus ADR-0020 program hierarchy, CI7 routing/cost plus acceptance-gate/lease enforcement,
   Personal zero-network, Team project opt-in, Maintenance Phase 0–2 with human-confirmed Quick Remove and Orrery
   display branding. Every item still requires Canonical source and integrated Validation.
3. **Deferred to 0.3.1.** DSH Store distribution, `orrery` CLI alias and OS scheduler are excluded from 0.3.0.
4. **Deferred without promised version.** Automatic worktree deletion, PyPI/independent wheels, independent Adapter
   releases, stable public Authority API, D2 and C2 are not release blockers or hidden previews.
5. **Unsupported/experimental boundary.** Real dual-host auto-leader, cloud relay, remote shell/Agent/merge/delete,
   Graph execution and Claude authenticated route remain unsupported. Harness JSON, Claude, DeepSeek and Team LAN
   surfaces remain exact-scope experimental/source-only unless a later decision says otherwise.
6. **New project defaults.** A new empty 0.3 project uses Unified Observatory, Authority Model 1 and Rules 1, with
   `authority_status=migration_pending`; selector presence does not imply project adoption. Personal is zero-network,
   Team disabled, automatic deletion false and scheduler unsupported.
7. **Legacy/brownfield defaults.** Existing 0.2 and brownfield ordinary install/tool upgrade remains create-only and
   legacy by default, preserves missing semantic selectors and author bytes, and requires explicit inspect → dry-run
   → receipt-bound apply for Unified/Model 1/Rules 1 migration. Rollback preserves `start-docsite.bat` whole-shell
   fallback and exact receipt-bound semantic restore.
8. **Distribution.** The public unit is one self-contained `project-orrery-v0.3.0.zip` plus one ASCII/LF SHA-256 file.
   It embeds exact Candidate Core/CLI/Observatory tracked source, retains stable `project-orrery` technical IDs, and
   publishes no independent wheel, PyPI or Adapter asset.
9. **Runtime claims.** Final-archive Codex install/discover/invoke/start/stop/update/uninstall/reinstall evidence is a
   release blocker. Harness JSON reruns its bounded Windows/Ubuntu contract but remains experimental. Old runtime
   evidence does not transfer to new component versions; other Adapters remain source-only experimental.
10. **Deterministic packaging.** The builder consumes exact Git objects, fixed metadata and a versioned allowlist.
    Windows and Ubuntu should produce byte-identical archive/checksum/entry receipts. If not, release blocks unless
    the maintainer explicitly records a one-release canonical Ubuntu builder waiver after matching entry receipts.
11. **Evidence reuse.** Final RC validates child Candidate SHAs, current State/Validation and non-stale acceptance
    receipts. It runs only integration-, packaging-, runtime- and release-owned gates. It must not manually replay all
    A4/W7.3/CI7 suites after CI7 already proves their receipts valid.
12. **Authority separation.** Non-main Candidate push, protected-main promotion, annotated tag, immutable asset and
    GitHub Release are separate actions. GitHub Release requires a final explicit maintainer authorization after
    tag/archive/checksum evidence. Tag-trigger automation cannot call `gh release create` automatically.
13. **History.** `v0.2.0` tag object/target, frozen blobs, manifest, assets, notes, Validation and Snapshot remain
    immutable. Corrective publication after 0.3.0 uses a new patch version, never replaced assets or moved tags.

## Consequences

- W7.3 and CI7 are current entry blockers; Final RC cannot begin from parallel branch facts.
- Public manifest, component versions, release notes and archive bytes stay unchanged until a dedicated Final RC
  Workstream starts from a clean central descendant.
- The final workflow is deliberately heavy once, after acceptance; it is not part of feature iteration.

## Mapping

- Approved Design: [v0.3.0 Release Scope and Default Matrix](../design/v0-3-0-release-scope-default-matrix.md)
- Implementation Plan: [v0.3.0 Final RC and Promotion](../implementation/plans/2026-08-30-v0-3-0-release-candidate-and-promotion.md)
- Validation: [v0.3.0 Final RC and Promotion](../validation/2026-08-30-v0-3-0-final-rc-promotion.md)
