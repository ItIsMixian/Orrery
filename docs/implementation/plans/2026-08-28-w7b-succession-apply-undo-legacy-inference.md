# 实施计划：W7B Succession Apply／Undo／Legacy Inference

Status: Completed; implementation is contained in Canonical W7/CI5 descendants

Date: 2026-08-28

Fact scope: Candidate `codex/w7b-succession-apply-undo-legacy-inference`, parent/task base
`codex/w7a-dynamic-workstream-succession-contract@52e88b8e15788eb7b17161e61885e9198d29407c`

Governing decision: [ADR-0014](../../decisions/0014-dynamic-workstream-succession-contract.md)

Approved Design: [Dynamic Workstream Succession Contract](../../design/dynamic-workstream-succession-contract.md)

## Goal and boundaries

Implement dependency-light, zero-network discovery/legacy inference, exact succession planning, one-local-confirmation
atomic batch apply, durable receipt inspection, and exact no-drift undo. Use only exact local Session, HEAD,
`task_base_oid`, Git ancestry, Scope and lineage evidence; names, directories, timestamps and path similarity never
establish a relation.

Real project state is read-only/dry-run only. Full apply/undo acceptance runs in an isolated temporary clone with a
sanitized W5C → W6 → W5D → CI1 → W5E topology. This Workstream does not delete any worktree, branch, commit,
Validation, relation history or author document; does not merge, push, tag, release, change branch protection, use
network, or add arbitrary shell/path/URL execution.

## Implementation sequence

1. Extend the Core contract with deterministic discovery candidates, exact hash-bound execution plans,
   confirmation tokens, apply/undo receipts, transaction journals and recovery inspection.
2. Implement fail-closed preflight and one atomic local transaction over append-only relation events plus
   Git-private predecessor Session transitions; preserve a verifiable recovery journal if an injected failure occurs.
3. Implement exact-receipt undo by appending `cancelled`/`stale` compensation and restoring predecessor Sessions only
   when current hash, HEAD and all state axes match the apply receipt.
4. Add CLI `relations discover|plan|inspect|apply|undo|receipt` human/JSON surfaces with stable nonzero blocked and
   Unknown exits; keep existing W7A commands compatible.
5. Add isolated fixtures/tests for explicit and legacy lineage, late CI, multiple predecessors, ancestry variants,
   runtime states, token forgery/replay/expiry/cross-project/drift, atomic failure/recovery, repeated apply, completed
   takeover invariants, undo/history preservation, deterministic receipts, zero network/delete and adjacency.
6. Run Fast then Checkpoint; update only affected subsystem State, Validation, DEVLOG and indexes. Leave root
   `PROGRESS.md` and `HANDOFF.md` to the unique integrator.

## Transaction and confirmation gates

- A plan binds project identity, graph/session/head/scope hashes, ordered operations, actor, expiry and plan hash.
- Confirmation is generated locally for that exact plan and actor, consumed once, and cannot be substituted by an
  Agent or central request.
- All inputs are re-read before the journal becomes write-capable. Each committed operation records before/after
  hashes; recovery either rolls back to zero effect or exposes a deterministic recoverable state that blocks graph
  use until repaired.
- Apply and undo append history; they never overwrite or delete relation events.

## Validation ladder

Fast runs the dependency-light execution contract plus the repository's existing non-Promotion feedback set. The
isolated full-loop execution suite and W7A relation suite establish the W7B/W7A product boundary before Checkpoint;
Checkpoint adds W1–W3, W5D/W6 adjacency, CI1 inventory/shards, integrated structure, isolated site/link gates,
author-tree and zero-network/no-delete assertions, and `git diff --check`. Full Promotion remains the central
integrator's later exact-SHA responsibility.

## Stop condition

Stop with a clean Candidate branch containing implementation, isolated acceptance evidence, real-project read-only
diagnostics, updated subsystem State/Validation/DEVLOG/indexes, and an explicit note that any real apply still needs
maintainer-local confirmation and central integration authorization.
