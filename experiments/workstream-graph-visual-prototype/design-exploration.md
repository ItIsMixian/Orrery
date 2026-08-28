# W7C-A Workstream Graph visual exploration

Status: Worktree Candidate exploration; provisional and non-authoritative

Base: `W5E-team-observatory-ui-closeout@692d19b3945f0a950548399d67eadd76b4587688`

This exploration describes a runnable consumer prototype. It does not define a Core relation schema, add an ADR, or claim that the Observatory implements a production graph.

## Compact design brief

- **Purpose:** help a maintainer answer “what continued from what, what depends on what, and where is the evidence-backed conflict?” without reading a spaghetti graph.
- **Primary user:** a maintainer reviewing several concurrent Workstreams and needing to move from a compact overview to exact evidence.
- **Context:** a standalone derived-view prototype adjacent to, but not wired into, the Personal or Team Observatory.
- **Tone:** dense analyst workspace with editorial restraint—hard dividers, quiet neutral surfaces, mono evidence labels, and limited semantic color.
- **Memorable idea:** one stable graph viewport changes lens while the evidence inspector explains the selected node or edge; uncertain relations are visibly broken lines, never green paths.
- **Constraints:** dependency-free HTML/CSS/JS, inline SVG plus an HTML list fallback, 390 px mobile support, keyboard navigation, non-color encodings, reduced motion, and no production Core/session reads.

## Visual and interaction system

The layout uses a compact header, a three-button lens switch, subsystem/status filters, the graph viewport, and a persistent inspector. Succession is the initial lens. The active tip is marked with a double-ring target and the words `ACTIVE TIP`; historical nodes are compressed into one expandable cluster. A real sibling remains visible one level from the active chain.

Dependency mode rotates attention to multi-predecessor convergence. Conflict mode adds a cross-hatched red edge and explicit `L3 / DIRECT` text for the fixture-confirmed path overlap. Proposed and Unknown relations use broken lines plus `PROPOSED` or `? UNKNOWN` labels; color is only a redundant cue.

On widths at or below 640 px the inline SVG becomes secondary and the accessible HTML relation list becomes the primary vertical timeline. Node and edge rows remain buttons that update the same inspector. All controls have focus-visible treatment, and animation is disabled by `prefers-reduced-motion`.

## Fixture boundary

`fixtures/workstream-graph.provisional.v1.json` is intentionally synthetic. Its root `authority` value is `provisional/non-authoritative`; evidence URLs are local fragment markers and evidence kinds are prefixed with `synthetic-`, `agent-proposal`, or `absence-marker`. The fixture must not be parsed as a real Workstream Session, copied into Core tests as a canonical schema, or used to claim that a branch relationship exists.

The fixture covers the requested visual cases:

- succession chain `W5C → W6 → W5D → CI1 → W5E → W7C-A`;
- true same-base sibling `W7A` beside `W7C-A`;
- `W7C-B` with two confirmed synthetic dependency predecessors;
- one Unknown dependency and one proposed conflict edge;
- one confirmed synthetic Direct conflict with explicit path and validation-surface evidence.

“Confirmed” therefore means confirmed within the synthetic fixture, not confirmed as a production project fact.

## Provisional consumer fields

Every field below is a UI exploration input, not a public contract:

- fixture: `fixture_version`, `authority`, `purpose`, `default_active_tip_id`, `collapsed_history`;
- node: `id`, display labels, three status axes, subsystem tags, branch/ref summary, `is_active_tip`, evidence references;
- edge: `id`, `source`, `target`, `view`, `relation`, `certainty`, optional `severity`, evidence references;
- collapsed cluster: stable ID, ordered node IDs, summary, and provisional marker.

The prototype deliberately avoids importing the current internal collaboration schema or inventing a `relation_graph` production object.

## Consumer contract W7A needs to freeze

W7A should decide, with Core ownership, the minimum stable consumer contract before W7C-B can wire a real view:

1. stable relation and node identity, including whether identity survives branch rename or Workstream closure;
2. relation direction and kind vocabulary for succession, dependency, sibling/base sharing, and conflict;
3. certainty/provenance vocabulary that can preserve confirmed, proposed, and Unknown without collapsing them into booleans;
4. ordered predecessor semantics for multi-predecessor dependency and whether succession can have more than one predecessor;
5. evidence reference shape, source authority, availability, and safe link targets;
6. independent lifecycle, runtime-condition, and evidence-freshness axes for node filtering;
7. active-tip semantics, including whether there can be zero, one, or several tips per view/member;
8. subsystem/status tags and visibility/observability fields needed for Personal versus Team projections;
9. collapsed-history cluster semantics—consumer-generated grouping versus Core-provided aggregation, plus how hidden Unknown/conflict counts are surfaced;
10. deterministic ordering and compatibility/version behavior so desktop SVG and mobile list render the same facts;
11. fail-closed behavior for missing nodes, dangling evidence, unsupported relation kinds, or stale Local-only telemetry;
12. an explicit non-authoritative marker for synthetic/test fixtures that cannot be confused with production output.

## W7C-B production wiring left open

W7C-B would still need to consume the W7A-owned relation projection, validate its version, map safe evidence links, reconcile Personal/Team visibility, and integrate the view into the existing Observatory information architecture. It must also add production contract tests, provider-failure/Unknown behavior, security review for link targets, and release/version updates. None of that is implemented here.
