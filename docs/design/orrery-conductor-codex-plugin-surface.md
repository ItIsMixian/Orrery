# Orrery Conductor Codex Plugin Surface

Status: Approved

Date: 2026-09-02

Governing ADR: [ADR-0031](../decisions/0031-read-only-codex-plugin-surface-for-orrery-conductor.md)

## 1. Product boundary

S1 makes the accepted Orrery DAG inspectable inside Codex. It is an adapter, not a second Graph product:

```text
Codex plugin UI
  -> local MCP tool/resource
  -> S1 envelope adapter
  -> explicit loopback Orrery Graph delivery contract
  -> existing sanitized semantic projection and layout semantics
```

The standalone Observatory remains valid. S1 does not copy its document shell, navigation, task authority or cleanup
controls into Codex.

## 2. Repository and package shape

The independent `orrery-conductor` repository contains:

- `.codex-plugin/plugin.json` with stable identity and local-development metadata;
- a local MCP server exposing bounded read-only status/snapshot/open-panel tools;
- one MCP UI resource for the DAG panel;
- an optional discovery Skill that invokes those tools without duplicating requirements;
- sanitized contract fixtures and focused compatibility checks;
- repository-local authority, README and license/provenance records.

The implementation should use the supported plugin scaffold and MCP Apps conventions rather than modifying Codex
installation files by hand.

## 3. MCP contract

The minimum tools are conceptually:

- `orrery_graph_status`: report explicit project binding, compatibility and current/stale/unavailable state;
- `orrery_graph_snapshot`: return one bounded sanitized delivery generation;
- `orrery_graph_open`: return the UI resource bound to that generation.

Tool names may be normalized during implementation, but the server remains useful when a host cannot render UI. No
tool mutates Orrery or launches tasks.

## 4. UI and live refresh

The UI consumes only the delivery envelope and preserves Orrery's full/compact visibility, relation types, historical
status, Unknown semantics, zoom behavior and pinned offline layout boundary. It renders inside the host-provided MCP UI
iframe and communicates through the MCP Apps bridge.

While visible, it may subscribe to generation notifications or poll at a bounded interval. It ignores older
generations and atomically swaps a complete layout. Closing the component stops refresh activity. A missing live
endpoint shows an honest disconnected/fixture-development state; it never scans disks or starts Orrery implicitly.

## 5. Parallel development boundary

Phase A can proceed with a frozen sanitized contract fixture and therefore shares no implementation path with W3.1 or
U2.5. Phase B may bind to live data only after the unique integrator supplies an accepted exact U2.5 delivery-envelope
Candidate. S1 must adapt to that contract instead of importing U2.5 source files.

## 6. Security and privacy

- loopback-only, explicit-project binding and zero external network by default;
- no Prompt, answer, transcript, source body, diff body, credential or full private path in MCP/UI payloads;
- read-only tools and no shell/merge/relation/cleanup authority;
- bounded payload, sanitized errors, schema/version refusal and no silent stale-as-current display;
- no Computer Use or mouse/keyboard control.

## 7. Acceptance surface

The first maintainer preview must show a recognizable Orrery DAG inside Codex, preserve full/compact facts from the
fixture, expose disconnected/stale/current states clearly and close without leaving a polling worker. Manifest/syntax
checks needed to open the preview are allowed; broader automated validation follows preview acceptance.
