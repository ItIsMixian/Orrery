# Project Orrery adoption proposal

Status: Superseded by ADR-0001
Date: 2026-08-18

This generated proposal was fulfilled and superseded by [ADR-0001](0001-project-orrery-self-hosting.md). It remains only to demonstrate the migration-safe scaffold contract.

1. Audit the repository's existing documentation authority and ADR numbering.
2. Map existing documents to Seed, ADR, Design, Plan, State, Validation, Snapshot, Library, or operational entrances.
3. Choose the next available ADR number.
4. Write a project-specific ADR that records what is adopted, what remains unchanged, and how migration will be validated.
5. Update the real `AGENTS.md`, `PROGRESS.md`, and subsystem State Docs.

Copy the structure below into the project-specific ADR only after approval.

## Context

Ideas, decisions, plans, implementation facts, and assessments currently risk being treated as interchangeable prose.

## Proposed decision

Adopt the authority chain in `docs/README.md`. Effective ADRs constrain approved Design and implementation. State Docs describe actual behavior. Validation proves claims. Snapshots provide dated evaluations.

## Proposed consequences

- Accepted ADRs are not rewritten to hide later changes.
- Plans cannot mark a feature implemented.
- State Docs link to real implementation and validation evidence.
