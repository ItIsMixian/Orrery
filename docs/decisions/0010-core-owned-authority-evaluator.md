# ADR-0010: Core owns the deterministic Authority evaluator

Status: Accepted
Date: 2026-08-21
Amends: [ADR-0009](0009-authority-meta-model-and-semantic-conformance.md)

## Context

ADR-0009 deliberately left AUTH-4 unresolved until a versioned fixture/golden contract existed. The Candidate
`amm-fixture-v1` checkpoint now freezes the minimum semantics and proves that the owner decision can be made
without deriving it from an existing consumer or file layout.

Project Orrery needs one deterministic interpretation boundary so CLI, Observatory and platform Adapters do not
independently redefine decision/implementation/validation claims, fact scopes or evidence capabilities.

## Decision

Project Orrery Core owns the deterministic Authority Meta Model evaluator.

- Core evaluates pre-normalized repository observations under an explicit model version, repository snapshot,
  fact scope and evidence visibility.
- Markdown parsing, Git/Harness observation collection, presentation, AI prose and Coordinator runtime remain
  outside the evaluator. They adapt into or consume Core semantics.
- CLI, Observatory and platform Adapters must not become competing normative semantics owners.
- The first implementation remains experimental and fixture-bound. It is not exported as a top-level Core API,
  does not add a project/release manifest field and does not change `CORE_API_VERSION`.
- Unknown model versions, scopes, evidence categories and observation kinds fail closed until Gate B defines a
  public compatibility contract.

## Reasons

- Core is already the platform-neutral component for shared schemas, manifests, compatibility and authority
  templates, so it is the least platform-specific owner.
- A single evaluator prevents CLI, Viewer, AI and future Agent integrations from drifting while allowing their
  parsing and presentation to evolve independently.
- Keeping observation collection outside Core prevents Git providers, Harnesses, UI layouts or Coordinator locks
  from leaking into the Authority type system.
- Delaying the public API/version field preserves Gate B and avoids implying migration compatibility before it is
  designed and tested.

## Consequences

- The Core package may add an internal experimental evaluator and shadow tests against the versioned fixture.
- Consumers must dual-run and compare before switching production behavior; each migration remains independently
  reversible.
- Gate B is still required before exporting a stable API, adding `authority_model_version` to manifests, changing
  Core/document schema versions or publishing an upgrade/downgrade contract.
- AUTH-1 remains unresolved; choosing an implementation owner does not decide Orrery's marketing or product core.

## Implementation and validation mapping

- Approved Design: [Authority Meta Model](../design/authority-meta-model.md)
- Implementation Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)
- State Docs: [Authority Meta Model State](../state/authority-meta-model.md), [test coverage](../state/test-coverage.md)
- Validation: [Core shadow evaluator](../validation/2026-08-21-authority-meta-model-core-shadow-evaluator.md)
