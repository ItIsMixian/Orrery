# Authority Meta Model conformance fixtures

This directory freezes provider-neutral inputs and expected semantic results before Project Orrery chooses an
Authority Meta Model implementation owner.

`v1/conformance.json` is a Candidate golden contract, not a public manifest schema and not a runtime API. Its
internal fixture ID remains distinct from the public integer selected by ADR-0011. `v1/compatibility.json`
freezes legacy/supported/unsupported capability behavior, while `v1/projection.json` freezes the future-release
default + discrete support-set contract and the rule that ordinary upgrades preserve an existing missing field.
These Candidate fixtures do not rewrite the published v0.2.0 release manifest or constitute a new release.

`v1/cli-observation-contract.json` freezes the internal M2.1 CLI observation/claim bundle shape, deterministic
source hashing, relation normalization and non-escalation boundaries. It is a Candidate test contract rather than
a public CLI schema; release and installer exposure remain outside M2.1.

`v1/observatory-projection.json` freezes the M2.2 projection schema, its exact dependency on the M2.1 bundle,
role coverage, source-link requirement and independent opt-in rollback switch. The Observatory package consumes
an injected bundle and does not import CLI, so the existing CLI-to-Observatory package dependency stays acyclic.
It does not change the default managed reader or the release template.

The fixtures deliberately keep coordination runtime data separate from fact scopes and model
decision/implementation/validation as independent claim dimensions. Consumers may use these fixtures for
shadow comparisons, but passing the fixture tests does not make a consumer the normative semantics owner.
