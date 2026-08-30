# 实施计划：U2 Unified Observatory Production Integration

Status: Implementation and root-only Candidate checkpoint complete

Date: 2026-08-29

Workstream: `U2-unified-observatory-production-integration`

Branch/base: `codex/u2-unified-observatory-production-integration` from
`codex/u1-u2-integration-baseline@12f3bf53dfc768067a5a4048de63437313ed633a`

Governing ADR: [ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md)

Approved Design: [Unified Observatory Architecture & Shell](../../design/unified-observatory-architecture-and-shell.md)

## Goal and boundary

U2 implements the first real root-only, default-off Unified Observatory Candidate. It adapts the existing
`build_docsite.py`／`serve.py` document reader, search, AI, author-document information architecture and recognizable
visual style, then composes Authority, Personal, Team, Workstream Graph and Workspace Maintenance behind one loopback
URL and one navigation shell.

This Workstream does not change public v0.2.0, the Skill template, managed-tool inventory, installer, release manifest,
tag, Release, protected main or the public/default launcher. `start-docsite.bat` remains the whole-shell legacy
rollback. Team remains project opt-in and request-only; Personal remains zero-network; Authority and Maintenance remain
provider-owned capabilities whose domain policy is not copied into the shell.

## Implementation

- [x] register the Git-private Workstream before authored writes and bind the exact task base;
- [x] freeze a versioned consumer registration and capability-discovery contract with route/identity/privilege
  collision rejection, optional per-consumer quarantine and required-consumer whole-shell failure;
- [x] add a static root-only builder that keeps dynamic controls, cookies and server state absent;
- [x] add one dynamic loopback front door that composes the legacy docsite reader/search/AI surface and existing
  Authority A3, Personal, Team, Graph and W6.1 Maintenance consumers;
- [x] centralize only common Host/Origin/cookie/token/API/lifecycle boundaries while delegating Team/Maintenance actions
  to their existing provider-owned control object;
- [x] supervise in-process Broker/Coordinator/helper ownership, write local diagnostics and ready identity under the
  Git-private worktree runtime, reject a live duplicate and recover stale identity on the next start;
- [x] add `Start Orrery.vbs` as the headless default candidate entry and `start-orrery.bat --console` as the one-console
  diagnostic path, leaving `start-docsite.bat` untouched;
- [x] bump only the unreleased Observatory component from 0.1.10 to 0.1.11 and register focused CI6 tests;
- [x] validate one visible URL, security/non-escalation/static/lifecycle/rollback contracts and real desktop/mobile UI;
- [x] synchronize affected subsystem State, Validation, Validation index and DEVLOG without editing root
  PROGRESS/HANDOFF.

## Validation ladder

```text
python -X utf8 scripts/ci/validate_change.py --stage fast --base 12f3bf53dfc768067a5a4048de63437313ed633a --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage fast --base 12f3bf53dfc768067a5a4048de63437313ed633a
python -X utf8 scripts/docsite/build_unified_observatory.py --enable --out <isolated>/index.html
python -X utf8 scripts/docsite/serve_orrery.py --console --no-browser --port 0
real in-app Chromium: 1280px desktop + 390x844 mobile
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 12f3bf53dfc768067a5a4048de63437313ed633a
git diff --check
```

The full local Candidate and hosted exact-SHA Windows/Ubuntu Promotion are integration-stage work. U2 does not run the
historical full Promotion suite as its development loop and does not push main or publish.

## Future transition

- [x] maintainer manually experienced the root-only integrated Candidate and rejected its duplicated navigation,
  mixed-language primary UI and misleading/degraded runtime states;
- [x] U2.1 repairs those acceptance defects on the exact U2/W7.1 integrated baseline; see
  [U2.1 Plan](2026-08-29-u2-1-unified-observatory-ux-acceptance-fixes.md);
- [ ] unique integrator reconciles Candidate lineage and root PROGRESS/HANDOFF in a clean integration worktree;
- [ ] exact Candidate SHA is pushed to a non-main ref and obtains both required hosted checks;
- [ ] public/default launcher, managed-tool/template/installer/release changes are separately authorized and versioned.
