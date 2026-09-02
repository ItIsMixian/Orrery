# Validation: S1 Orrery Conductor Codex Plugin Surface

Status: Pending implementation and maintainer preview

Date: 2026-09-02

Plan: [S1 Orrery Conductor Codex Plugin Surface](../implementation/plans/2026-09-02-s1-orrery-conductor-codex-plugin-surface.md)

## Accepted baseline

- Project Orrery owns an accepted Workstream Graph semantic/layout surface; S1 need not recreate task facts or ELK
  decisions.
- OpenAI documentation supports plugins containing Skills and MCP servers, with optional UI resources returned from
  MCP tools through the MCP Apps bridge.
- No `orrery-conductor` repository, Codex plugin, MCP server, UI component, local install or public release currently
  exists.

## Pending Phase A evidence

- independent Git repository and stable plugin identity;
- valid plugin/MCP/UI resource lifecycle in a local development profile;
- bounded read-only tools remain usable without rendered UI;
- fixture-backed full/compact DAG renders inside Codex with current/stale/unavailable states;
- visible-panel refresh is bounded and stops on close;
- zero external network and no private payload, mutation authority, Computer Use or plugin replacement;
- maintainer preview before broader tests.

## Pending Phase B evidence

- accepted exact U2.5 delivery-envelope dependency;
- explicit loopback project binding and compatible version refusal;
- live generation update without page-wide reload or fact/layout drift;
- disconnect and stale-last-known behavior.

## Result

Pending. Authority is accepted for an independent Phase A task; no repository, implementation, compatibility evidence,
installation or release is claimed.

## 2026-09-02 Phase A rejection and revised preview gate

Phase A exact `4e44d276ecb16a2acd6e750db243866a11e03961` proved the plugin/MCP fixture path, but the maintainer rejected
its conversation-embedded UI location. The next preview must render the same DAG in Codex's existing right Browser
Panel, hide/reopen through the host panel toggle and avoid a large inline conversation component. A custom toolbar icon
is neither claimed nor required. Existing Phase A manifest/handshake evidence may be reused without rerun.
