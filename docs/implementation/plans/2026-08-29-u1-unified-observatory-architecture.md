# 实施计划：U1 Unified Observatory Architecture & Shell Design

Status: Architecture accepted and Phase 1 complete; production implementation not started

Date: 2026-08-29

Workstream: `U1-unified-observatory-architecture`

Branch/base: `codex/u1-unified-observatory-architecture` from protected
`main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`

Governing ADR: [ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md)

Approved Design: [Unified Observatory Architecture & Shell](../../design/unified-observatory-architecture-and-shell.md)

## Goal and boundary

U1 first freezes the architecture, consumer contract, join interfaces and non-authoritative interaction evidence for a
single Observatory shell. It does not merge production servers, change default navigation, enable Team/network,
implement Authority selection, alter Maintenance semantics, update start scripts, public templates, managed tools,
README/assets, release inputs or shared State/DEVLOG/indexes.

The production inheritance baseline is the existing `build_docsite.py`／`serve.py` document reader, search, AI Q&A,
author-document information architecture and recognizable visual experience. U1 does not authorize a from-scratch
docsite rewrite or comprehensive visual redesign; either requires a separate task and explicit maintainer approval.

## Phase 1 — architecture and synthetic evidence (this Workstream)

- [x] register a Git-private Workstream before authored writes;
- [x] inspect current docsite/Team servers, builders, navigation, route/cookie/Host/Origin/Broker/Coordinator ownership
  and shutdown behavior;
- [x] determine that a new ADR/amendment is required and draft temporary proposal
  `PO-DEC-U1-unified-observatory-shell` as Proposed only, without reserving a formal number;
- [x] draft a Proposed-for-approval Design covering runtime axes, public routes, internal topology, discovery,
  registration, supervised lifecycle, static fallback, isolation, rollback, versioning and public-template boundary;
- [x] freeze W6.1 and A3 join interfaces while keeping uncommitted/missing contract details Unknown;
- [x] design the final Windows one-click experience as headless-by-default, with an explicit one-console debug path and
  Git-private/runtime diagnostics, without editing launchers;
- [x] build a dependency-light synthetic prototype under `experiments/unified-observatory-shell/`;
- [x] verify desktop and 390px mobile navigation, mode boundary, Team opt-in, Authority Unavailable, maintenance
  cached/stale states, focus, overflow and console;
- [x] create independent U1 Validation; leave root PROGRESS/HANDOFF and shared State/DEVLOG/indexes untouched.
- [x] record maintainer acceptance of the architecture direction on 2026-08-29 while leaving the temporary proposal
  Proposed, its formal number unassigned/reserved=false and Design promotion integrator-only;
- [x] freeze the current docsite inheritance/non-redesign boundary and mark the prototype as an architecture
  interaction study rather than a final UI specification.

## Phase 2 — decision review and contract fixture (future)

- [x] maintainer accepted the architecture direction and production docsite inheritance boundary;
- [x] unique integrator assigned ADR-0016 and promoted the Design to Approved during integration;
- [x] reconcile committed W6.1/CI6 and A3 Candidate contracts in the U2 integration baseline;
- [ ] freeze machine-readable shell registration/route fixtures and negative collision/escalation cases;
- [ ] choose managed Broker topology (in-process or supervised helper) only after parity/security/lifecycle evidence;
- [ ] decide Team Coordinator/LAN transport topology while preserving Team opt-in and the single public UI URL;
- [ ] choose final server/supervisor/launcher names, hidden-launch mechanism, debug `--console` compatibility, runtime
  log location and compatibility duration.

## Phase 3 — root-only implementation (future independent Workstream)

- [ ] add one root-only public Observatory front door, supervisor and explicit consumer/helper registry behind an
  opt-in flag; do not assume one process or one internal listener;
- [ ] wrap/register/adapt the existing `build_docsite.py`／`serve.py` consumers; do not rewrite the docsite from scratch;
- [ ] compose docs/search/AI/Authority/Personal/Team/Graph/Maintenance without marker ownership conflicts while
  preserving author information architecture and the recognizable production docsite experience;
- [ ] centralize common security/lifecycle while preserving provider-specific authorization;
- [ ] prove normal exit, startup failure and supervisor crash leave no helper process, bound endpoint or stale ready marker;
- [ ] keep current default `serve.py` and public template byte behavior as rollback;
- [ ] add focused/adjacent/security/static/dynamic/browser tests and component version changes;
- [ ] synchronize affected subsystem State/Validation/DEVLOG through the unique integrator.

## Phase 4 — managed/public transition (future release choice)

- [ ] review root-only evidence and exact rollback before changing the preferred launcher;
- [ ] add a compatibility-forwarding `start-docsite.bat` only after entrypoint decision;
- [ ] separately update managed-tool/public-template/installer/release contracts;
- [ ] push exact Candidate to non-main ref, obtain required Windows/Ubuntu checks, then promote the same SHA;
- [ ] choose SemVer/manifest/tag/Release in a separate authorized release Workstream.

## Validation ladder for Phase 1

```text
node --check experiments/unified-observatory-shell/prototype.js
python -X utf8 -m unittest -v tests.test_personal_observatory tests.test_team_observatory tests.test_workstream_relation_graph_observatory
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out <isolated>/index.html
browser desktop + 390px mobile acceptance
git diff --check
```

Phase 1 does not run hosted Promotion, push main, tag, release or destructive maintenance.

## Clarification amendment short gate

The user-visible-entry/internal-topology clarification changes only the Proposed decision, Proposed Design, Plan,
Validation and synthetic prototype. It intentionally does not rerun the 196-second focused module suite:

```text
temporary proposal + forced-topology phrase alignment
node --check experiments/unified-observatory-shell/prototype.js
python -X utf8 scripts/docsite/build_docsite.py --out <isolated>/index.html
python -X utf8 scripts/ci/validate_repository_gates.py
browser affected desktop + 390px topology/diagnostics/static path
git diff --check
```

## Final acceptance-boundary amend short gate

This final narrow amend changes only Proposal/Design/Plan/Validation and the synthetic prototype notice. It does not
modify production docsite, launchers or other product source, and does not rerun the focused suite or Promotion:

```text
acceptance/inheritance/non-redesign phrase alignment
node --check experiments/unified-observatory-shell/prototype.js
python -X utf8 scripts/ci/validate_repository_gates.py
git diff --check
```
