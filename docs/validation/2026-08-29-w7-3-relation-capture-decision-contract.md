# Validation：ADR-0017 Workstream Relation Capture Decision Contract

Date: 2026-08-29

Status: PASS — documentation decision/design/plan contract only; implementation not started

## Accepted scope

- exact-base mechanical `derived_from` may be appended automatically after same-project OID/ancestry validation;
- `depends_on` requires implementation／validation／integration／release gate and human-machine confirmation;
- task-local gates use human task owner; project gates and `absorbs` use human integrator;
- Personal owner is initial sole integrator; Team owner may explicitly add verified human integrators;
- central Agent/Conductor may propose and route, but never confirms project authority.

## Documentation checks

- ADR-0017 is Accepted and amends rather than rewrites ADR-0014/0008;
- accepted ADR amendment metadata is one-line parseable; the frozen repository relation test now includes ADR-0016
  and ADR-0017 without changing Authority runtime semantics;
- Approved Design separates proposal, evidence and confirmation and preserves append-only/private/Unknown boundaries;
- W7.3 Plan explicitly remains not started and maps schema、Core/CLI、role、inbox、Graph and validation phases;
- v1 depends_on without gate remains Unknown/unspecified; no historical bytes are silently migrated;
- no document claims CLI、Core、Observatory、Conductor、Team role grant or auto-derived event exists today.

## Non-implementation boundary

This validation proves link/status/semantic alignment only. It does not run product tests, mutate Git-private relation
state, assign roles, create a dependency, confirm an absorption, launch a Conductor, change public v0.2.0, push main,
tag or release. Implementation evidence must be produced by W7.3 on a separate branch/worktree.

## Local evidence

- routed Fast: 48/48 PASS in 1.774375s with AI provider disabled; selected surfaces were documentation and the frozen
  Authority amendment relation contract;
- Authority Observatory shadow: 15/15 PASS, including exact repository amendment relations for ADR-0016/0017;
- repository gate: 717 repository paths, 388 Markdown files, 1019 local links, no forbidden artifact;
- `git diff --check`: PASS.
