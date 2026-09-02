# Design

Design documents turn accepted direction into coherent specifications. Mark each design `Draft` or `Approved` and link the governing ADRs.

Draft Design may explore options. Only Approved Design can constrain an Implementation Plan.

## Approved designs

- [Orrery Conductor Codex Right Panel](orrery-conductor-codex-right-panel.md) — makes Codex's existing right Browser Panel the primary S1 surface and retains inline MCP UI only as fallback, under ADR-0032.
- [Orrery Conductor Codex Plugin Surface](orrery-conductor-codex-plugin-surface.md) — independent read-only Codex plugin, local MCP server and MCP UI adapter over the existing Orrery DAG, under ADR-0031.
- [Fast Candidate Freeze and Asynchronous Validation Closeout](fast-candidate-freeze-and-asynchronous-validation.md) — sub-30-second structural freeze, honest validation-pending status and immutable-SHA asynchronous checks without weakening integration/release gates, under ADR-0030.
- [Workstream Classification Calibration and Dispatch Registration](workstream-classification-calibration-and-dispatch-registration.md) — evidence-bound human calibration for missing program/series metadata plus explicit future dispatch envelopes, without name inference or relation/lifecycle effects, under ADR-0029.
- [Unified Observatory Shell-first Graph Activation and Incremental Cache](unified-observatory-shell-first-graph-activation.md) — decouples usable shell readiness from Graph readiness and specifies a validated Git-private, event-invalidated, non-authoritative Graph cache under ADR-0028.
- [ELK Cutover and Explicit Legacy Fallback](elkjs-cutover-and-explicit-legacy-fallback.md) — preview-first cutover, one shared semantic projection, frozen/manual/visibly-labelled legacy recovery and no silent fallback under ADR-0023.
- [ELK.js Workstream Graph Layout and Orrery Rendering](elkjs-workstream-graph-layout-and-rendering.md) — pinned local ELK compound/orthogonal geometry with Orrery-owned facts, SVG/frontend, zero-network packaging and ledger failure path under ADR-0022, amended by ADR-0023.
- [Orrery v0.3.0 Release Scope and Default Matrix](v0-3-0-release-scope-default-matrix.md) — new/legacy cohort defaults, single self-contained ZIP, final runtime, deterministic packaging and split publication authority under ADR-0021.
- [Workstream Program Hierarchy & Graph Bundling](workstream-program-hierarchy-and-graph-bundling.md) — explicit program/phase membership, self-host W/W5/W6/W7 repair fixture and same-semantics route bundles under ADR-0020 without inventing relation edges.
- [Authority-first Workstream Dispatch](authority-first-workstream-dispatch.md) — authority commit before initial dispatch or mid-flight scope amendment, SHA/path-only task notices, pre-write Agent acknowledgment and non-authoritative transcripts under ADR-0018.
- [Workstream Relation Capture & Confirmation](workstream-relation-capture-and-confirmation.md) — automatic mechanical lineage, gate-aware dependency proposals, human task-owner/integrator authority, local-first inbox and optional proposal-only Conductor under ADR-0017.
- [Unified Observatory Architecture & Shell](unified-observatory-architecture-and-shell.md) — one visible launcher/URL/navigation identity with explicit consumer registration, supervised internal helpers, inherited docsite experience, static fallback, failure isolation and staged rollback under ADR-0016.
- [Orrery Rename and Compatibility Contract](orrery-rename-and-compatibility-contract.md) — approved under ADR-0015; maps brand, stable identifiers, explicit opt-in CLI thin alias, host-specific display/alias behavior, brownfield migration, first-release asset naming, privacy, rollback and R3–R5 gates without claiming implementation.
- [Dynamic Workstream Succession Contract](dynamic-workstream-succession-contract.md) — provider-neutral relation events, exact Git evidence, append-only common-private storage, active-tip conflict-pair policy and W7B/W7C consumer boundaries governed by ADR-0014.
- [Self-hosting documentation system](self-hosting-documentation-system.md) — the reader paths, storage boundaries, and synchronization rules governed by ADR-0001.
- [Real-development context-routing benchmark](real-development-context-routing-benchmark.md) — isolated application-development task mix, Oracle hierarchy, fixture boundaries, and passive pre-write Scope Acquisition measurement governed by ADR-0002 and ADR-0005.
- [Docsite credential isolation and local broker](docsite-credential-isolation-and-broker.md) — provider binding, fail-closed activation, local HTTP hardening, and the optional deterministic broker governed by ADR-0003.
- [Platform-neutral Core and Adapter architecture](platform-neutral-core-and-adapter-architecture.md) — component responsibilities, canonical Agent entrance, compatibility model, support states, migration boundaries, and Claude Code／DeepSeek Harness Phase 4 platform mapping governed by ADR-0004 and ADR-0010.
- [Broker-first docsite Provider gateway](broker-first-docsite-provider-gateway.md) — Broker-only runtime, managed default, external isolation and explicit migration governed by ADR-0006.
- [Multi-worktree collaboration protocol](multi-worktree-collaboration-protocol.md) — isolation and fact scopes under ADR-0007, amended by ADR-0008 with default Personal Mode, opt-in Team Mode, Local-only telemetry, review, cleanup, and progressive command-center UX.
- [Authority Meta Model semantics](authority-meta-model.md) — role lifecycles, independent claim dimensions, authority scopes, provider-neutral evidence, derived-view constraints and conformance boundaries governed by ADR-0009; no implementation owner or refactor Plan is selected yet.
- [Documentation governance and information lifecycle](document-governance-and-information-lifecycle.md) — current/history boundaries, event-driven synchronization, responsibility-based splitting, soft budgets and non-authoritative audit findings governed by ADR-0012.

## Draft designs

- No active Draft Design is registered.
