# ADR-0031: Read-only Codex Plugin Surface for Orrery Conductor

Status: Accepted

Date: 2026-09-02

Maintainer acceptance: accepted on 2026-09-02 when the maintainer authorized S1 to proceed in parallel as the Codex
compatibility layer for the existing Orrery Workstream DAG.

Amends: [ADR-0017](0017-workstream-relation-capture-and-confirmation-authority.md)

Preserves: [ADR-0022](0022-elkjs-workstream-graph-layout-engine.md),
[ADR-0028](0028-shell-first-observatory-and-incremental-graph-cache.md),
[ADR-0030](0030-fast-candidate-freeze-and-asynchronous-validation.md)

## Context

Orrery already owns the task/relation facts, historical projection, full/compact semantics and ELK layout contract.
The missing surface is a supported way to inspect that DAG inside Codex without opening the standalone Observatory.

Current OpenAI documentation describes plugins as installable packages that may contain Skills and an MCP server, and
allows selected MCP tools to return optional UI resources through the MCP Apps bridge. This provides a supported
compatibility boundary; it does not promise an arbitrary permanent native sidebar or authorize patching Codex itself.

## Decision

1. S1 is an independent product repository named `orrery-conductor`, not a new folder or Workstream implementation
   inside `project-orrery`.
2. S1 Phase A is a read-only Codex plugin composed of a valid plugin manifest, a local MCP server and an optional MCP
   UI resource. A small Skill may provide discoverability, but it does not own facts or orchestration authority.
3. The plugin consumes a versioned Orrery Workstream Graph delivery envelope. It does not rescan Git, infer relations,
   recreate history selection or fork the accepted layout semantics.
4. The first UI is rendered inside the supported conversation/plugin surface. It may refresh through bounded MCP Apps
   notifications or visible-panel polling; “live” means while that UI is mounted, not a hidden background daemon.
5. S1 may develop in parallel from a sanitized frozen fixture and exact contract. Live self-host binding waits for an
   accepted U2.5 delivery-envelope Candidate and must fail honestly when Orrery is absent, stale or incompatible.
6. Phase A is read-only: no task creation, dispatch, relation decision, merge, validation trigger, cleanup or remote
   execution. Those possible Conductor capabilities require later decisions and explicit user authority.
7. Personal use remains zero-network. The adapter may access only an explicitly selected project and loopback Orrery
   endpoint; no Prompt/transcript/source/diff body, credentials or private absolute path enters the UI payload.
8. Initial distribution is local development only. Public plugin submission, marketplace publication, remote repo
   creation and release are separate tasks.
9. S1 uses no Computer Use. Local Codex compatibility is proven through the supported plugin/MCP lifecycle and a
   maintainer-visible preview.

## Consequences

- W3.1 and U2.5 keep ownership of freeze/validation and Graph delivery; S1 owns only host compatibility.
- A fixture-backed Codex UI can advance immediately, while final live refresh remains dependency-gated.
- The first S1 milestone is not the full Orrery Conductor promised by the name; it is the safe read-only foundation.

## Mapping

- Approved Design: [Orrery Conductor Codex Plugin Surface](../design/orrery-conductor-codex-plugin-surface.md)
- Implementation Plan: [S1 Orrery Conductor Codex Plugin Surface](../implementation/plans/2026-09-02-s1-orrery-conductor-codex-plugin-surface.md)
- Pending Validation: [S1 Orrery Conductor Codex Plugin Surface](../validation/2026-09-02-s1-orrery-conductor-codex-plugin-surface.md)
- OpenAI documentation: [Build plugins](https://learn.chatgpt.com/docs/build-plugins),
  [Add UI to an MCP server](https://developers.openai.com/plugins/build/chatgpt-ui)
