# ADR-0019: Portable Operating Rules 与 Authority Route Preflight

Status: Accepted

Date: 2026-08-30

Amends and extends: [ADR-0009](0009-authority-meta-model-and-semantic-conformance.md)

Clarifies: [ADR-0010](0010-core-owned-authority-evaluator.md), [ADR-0011](0011-authority-model-version-and-compatibility.md), [ADR-0012](0012-document-governance-and-information-lifecycle.md), [ADR-0004](0004-platform-neutral-core-and-adapter-boundaries.md)

Maintainer direction: A4 `Portable Meta Rules & Bootstrap Contract`, including the generalized Authority Route Preflight and Novelty/Absence Claim Gate, was approved for Candidate implementation on 2026-08-29. Acceptance of this ADR does not claim that the inventory, routing contract, consumers, adapters or release already exist.

Integration allocation: A4 Candidate `3d298a5c...` used provisional numeric identifier `ADR-0018` before integration.
The unique integrator allocated canonical local `ADR-0019` under ADR-0007/PO1, updating identifiers, links and the
portable-inventory digest without changing this decision's status or semantics.

## Context

ADR-0009/0010/0011, the Authority Meta Model State, the versioned fixture and the Core evaluator already constitute Orrery's meta-semantic layer. The missing product capability is not a new layer. The missing capability is reliable distribution and consumption of that existing layer by ordinary Skill bootstrap, retrieval routing, CLI/Harness inspection and user-facing projections.

Today the public v0.2.0 template contains three minimal Seed statements, while a generated target State placeholder cannot carry Orrery-wide operating rules. A Skill or Agent can therefore encounter wording about “通用原则”, “元规则”, “portable rules” or “why users cannot see this rule” and incorrectly infer from a local template that the semantic layer is absent. That failure generalizes beyond the meta-rule example: a low-authority template or local implementation fragment can be mistaken for project-wide evidence about whether a capability, decision, implementation, consumer or release exists.

The correction must preserve three boundaries:

1. Authority Meta Model remains the existing meta layer and Core remains its only deterministic semantics owner.
2. Portable Operating Rules are a versioned inventory/projection inside that layer, not a new target-project Seed or a copy of Orrery self-host State.
3. Target-project facts still come from the target's own AGENTS index, Seed, effective ADR/Design, implementation, State and Validation/release evidence.

## Decision

### 1. Extend the existing Authority Meta Model consumption surface

Orrery adds two versioned, related consumption contracts inside the existing Authority Meta Model:

- `orrery-operating-rules-v1`: a portable inventory of cross-project operating constraints distilled from governing Orrery semantics and safety contracts;
- `authority-route-preflight-v1`: a provider-neutral, deterministic route receipt for selecting the minimum governing evidence before a fact, novelty or absence claim.

Neither contract creates another authority layer, document role, evaluator owner or project fact store. ADR-0010 continues to make Core the only deterministic owner. CLI, Harness, Skill, Adapter and Observatory are collectors or projections.

### 2. Keep three kinds of content distinct

| Content | Responsibility | May it become a target-project Seed automatically? |
| --- | --- | --- |
| Orrery Portable Operating Rules | Cross-project bootstrap, authority interpretation, non-escalation and safe mutation constraints | No |
| Target-project Seed/State | The target's product intent and current facts | Only through the target's authored authority process |
| Orrery Product Seed/State | Orrery's own goals and current implementation/release facts | No; wording similarity does not cross the boundary |

Every operating-rule projection must state that it is not a target-project fact or Seed. The inventory may cite Orrery Product Seed as bounded source material, but it must distill portable constraints rather than copy Product Seed prose or current self-host facts.

### 3. Freeze a versioned portable operating-rules inventory

Core owns the canonical machine-readable inventory, schema, compatibility judgment and deterministic projection. Each rule has at least:

- stable rule ID and inventory/rule version;
- Chinese and English short descriptions or a stable message key;
- applicable stages and consumers;
- governing source links and source authority role;
- normative strength;
- mechanical-enforcement class;
- failure and Unknown behavior;
- an explicit `not-target-project-fact-or-seed` boundary.

The bounded v1 source inventory may distill cross-project constraints from the Orrery Product Seed, root AGENTS safety boundaries, ADR-0009/0011/0012 and the released Skill's installation/migration contract. It must exclude current component versions, current self-host State, project-specific goals, experiment conclusions and release-status facts.

Unknown, missing, malformed or tampered inventory versions fail closed to a read-only/Unknown capability result. Consumers must not silently choose the newest known inventory.

### 4. Add provider-neutral Authority Route Preflight

Before answering whether a capability, rule or decision exists, is implemented, is validated, is distributed, is public/default/released, or why a user cannot see it, a deterministic consumer must:

1. resolve one or more stable concept/subsystem IDs from a versioned concept registry and aliases;
2. follow the project AGENTS index to relevant State;
3. follow State to governing effective ADR/Approved Design;
4. select implementation, Validation, distribution/consumer and release evidence only as required by the query class;
5. exclude or explicitly mark lower-authority sources that cannot establish the requested claim;
6. preserve unresolved targets as Unknown.

Aliases are only entry points. Routing is owned by stable concept IDs, authority links and precedence. Classification uncertainty conservatively fans out to multiple related concepts, then converges by authority priority; it must not stop at the first matching template, README or code fragment.

The versioned route receipt contains at least:

- query class and registry/schema versions;
- selected concept IDs and confidence/ambiguity state;
- selected governing sources in authority order;
- excluded lower-authority sources and reasons;
- four independent claim dimensions;
- unresolved targets, Unknown reasons and bounded search scope;
- whether a novelty/absence claim is allowed, rejected or Unknown;
- a deterministic receipt hash.

The receipt selects evidence and claim shape. It does not replace the evidence, author prose or Core Authority evaluator.

### 5. Keep four claim axes independent

Route output must distinguish:

1. **semantic/decision existence** — whether the concept and governing decision/design exist;
2. **implementation** — whether implementation is present in the stated fact scope;
3. **distribution/consumer wiring** — whether the capability is actually delivered to the stated consumer;
4. **public/default/release** — whether it is public, default-enabled or released in the stated channel.

An axis is `present`, `absent` or `unknown` only when the selected evidence supports that value; otherwise it remains Unknown. “Not distributed” must not become “does not exist”. Accepted must not become implemented. Canonical source must not become public release.

### 6. Gate novelty and absence claims

Before a consumer says “new”, “not established”, “does not exist” or an equivalent absence claim, it must produce a bounded negative-evidence receipt recording:

- index/registry version;
- searched concept IDs;
- searched AGENTS/State/ADR/Design scope;
- unresolved or broken authority links;
- excluded lower-authority observations;
- the axes for which absence is actually supported.

If an indexed governing source exists, a semantic/decision absence claim is rejected. If the registry, State, link or evidence scope is incomplete, the claim is downgraded to Unknown with the missing target. A template omission, stale low-authority prose, missing consumer wiring or an Agent assertion cannot prove semantic absence.

### 7. Separate mechanical guarantees from advisory instructions

- Core can mechanically validate inventory/schema/hash, route precedence, claim shape, Unknown behavior and absence-gate receipts for normalized inputs.
- CLI/Harness can mechanically collect bounded repository evidence, invoke Core and emit versioned JSON without writing target files or promoting Authority/release status.
- Unified Observatory can mechanically consume the same projection and Ask Docs can invoke preflight before context selection; the page remains read-only.
- `SKILL.md` can direct an Agent to consume the versioned inventory and receipt before target AGENTS/Seed/State, but without a host pre-model hook that instruction is best-effort and must be labeled advisory.
- An Adapter may claim enforced pre-model input only when the exact host runtime exposes a verified hook. Unsupported hosts remain advisory; Adapter packaging alone does not strengthen the guarantee.

Skill wording, Core inventory, CLI/Harness output, template explanation and Observatory projection must be protected by drift tests. Projections may copy exact canonical bytes for Skill-only use, but they are generated/verified projections, not independent handwritten owners.

### 8. Preserve installation, migration and author ownership

Scaffold and migration remain create-only for authored documents. New projects receive a clear explanation that Orrery operating rules and the project's own Seed are different layers. Existing AGENTS, Seed and State files remain byte-for-byte preserved. `--upgrade-tools` continues to manage only its whitelist and cannot rewrite author Seed/State.

`scaffold installed`, `authority migration pending`, `authority integrated`, `consumer wired` and `public/released` remain separate facts. The route receipt or inventory presence cannot promote any of them.

The public v0.2.0 tag, manifest, archive, checksum and historical fixtures remain unchanged. A4 is source-only, unreleased and default-safe; it does not choose a future SemVer or enable a public/default consumer.

### 9. Add a read-only Unified Observatory projection

The root-only/default-off Unified Observatory keeps the existing single `authority` navigation identity and route as the only user-facing carrier. A4 must not add a ninth top-level navigation item, a separate meta-rules page, or a second semantics column. Instead, the current sparse Authority view becomes a progressively disclosed “事实与规则” composition containing target-project principles (from project documents), Orrery operating rules (from the versioned tool inventory), and fact-interpretation/managed-consumer status.

Primary UI uses ordinary Chinese and does not use the internal term “meta rules” as its title. Technical detail exposes rule ID, version, source, enforcement and Unknown/failure behavior. Managed/legacy/readiness details are collapsed by default.

The reusable projection cannot edit, approve or generate project facts. Static output remains read-only. Dynamic output adds no network, credential or execution authority and may expose operating-rules data only below the existing `/api/v1/authority` route family. Ask Docs uses the same route preflight before selecting authority context; a preflight failure preserves Unknown and cannot be bypassed by model prose.

### 10. Validate generalized routing, not keyword patches

The conformance corpus must include the real A4 failure and at least eight cross-subsystem scenarios covering design-only, implemented-but-unreleased, old released/new Candidate, template omission despite Core implementation, State Unknown, similar names, misleading lower-authority prose, multilingual/indirect queries and public/default distinctions.

Mutation and negative cases remove literal keywords while preserving semantics, inject conflicting templates, stale State, broken ADR links, unindexed concepts, unknown schemas and forged Agent assertions. Assertions bind selected evidence and four-axis claim shape, not a fixed natural-language answer.

## Correct A4 acceptance conclusion

For questions equivalent to “跨项目通用原则／元规则层／为什么 Skill 用户看不到当前 Seed/State 中的规则”, the indexed evidence must lead with Authority Meta Model State and ADR-0009, adding ADR-0011/0012 when compatibility or governance is needed. The four axes are:

- semantic/decision existence: present;
- implementation: present for the internal fixture/Core evaluator in the stated source scope;
- distribution/consumer wiring: absent or partial for ordinary Skill bootstrap before A4;
- public/default/release: absent for the new A4 capability.

Therefore the valid conclusion is “the Authority Meta Model already exists and has internal implementation; portable distribution and consumer wiring are missing.” “A new meta layer was discovered/created” is forbidden by the indexed governing sources.

## Rejected alternatives

### Create another meta-rules layer or evaluator

This would conflict with ADR-0009/0010, duplicate semantics ownership and make target Seed boundaries less clear.

### Copy Orrery Product Seed or self-host State into target projects

This would turn project-specific goals/current facts into universal rules and create silent author-document migration.

### Route only by a synonym list

Aliases cannot establish authority or distinguish similarly named concepts. Stable concept IDs, authority links, fan-out and precedence are required.

### Infer absence from templates, READMEs or local code

Those sources cannot establish project-wide semantic, decision, distribution or release absence. The Novelty/Absence Claim Gate must fail closed.

### Let Skill or Observatory own routing rules

That would create competing semantics owners. Both remain projections/consumers of Core contracts.

## Consequences

- Core gains a new internal, versioned inventory and route-preflight surface; it remains source-only and unreleased.
- CLI/Harness JSON gain bounded read-only inspect/capability output without author writes or status promotion.
- Skill-only distribution can still expose exact projected inventory bytes, while enforcement remains honestly advisory without a host hook.
- New scaffold explanations improve layer visibility, while brownfield author bytes remain untouched.
- The existing Authority view gains a discoverable read-only rules projection and preflight-aware Ask Docs context selection without a new page, navigation identity or execution authority.
- Component versions advance only for components whose unreleased source changes; release/tag/version selection remains a separate maintainer decision.

## Implementation and validation mapping

- Approved Design: [Authority Meta Model](../design/authority-meta-model.md), section “Portable Operating Rules 与 Authority Route Preflight”
- Implementation Plan: [A4 Portable Operating Rules & Authority Route Preflight](../implementation/plans/2026-08-30-a4-portable-operating-rules-and-authority-route-preflight.md)
- State Docs: [Authority Meta Model](../state/authority-meta-model.md), [Documentation System](../state/documentation-system.md), [Release and Toolchain](../state/release-and-toolchain.md), [Test Coverage](../state/test-coverage.md), [Project Structure](../state/project-structure.md)
- Validation: [A4 Portable Operating Rules & Authority Route Preflight](../validation/2026-08-30-a4-portable-operating-rules-and-authority-route-preflight.md)
