# Design

Design documents turn accepted direction into coherent specifications. Mark each design `Draft` or `Approved` and link the governing ADRs.

Draft Design may explore options. Only Approved Design can constrain an Implementation Plan.

## Approved designs

- [Self-hosting documentation system](self-hosting-documentation-system.md) — the reader paths, storage boundaries, and synchronization rules governed by ADR-0001.
- [Real-development context-routing benchmark](real-development-context-routing-benchmark.md) — isolated application-development task mix, Oracle hierarchy, fixture boundaries, and passive pre-write Scope Acquisition measurement governed by ADR-0002 and ADR-0005.
- [Docsite credential isolation and local broker](docsite-credential-isolation-and-broker.md) — provider binding, fail-closed activation, local HTTP hardening, and the optional deterministic broker governed by ADR-0003.
- [Platform-neutral Core and Adapter architecture](platform-neutral-core-and-adapter-architecture.md) — component responsibilities, canonical Agent entrance, compatibility model, support states, and migration boundaries governed by ADR-0004.
- [Broker-first docsite Provider gateway](broker-first-docsite-provider-gateway.md) — Broker-only runtime, managed default, external isolation and explicit migration governed by ADR-0006.
