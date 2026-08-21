# Authority Meta Model conformance fixtures

This directory freezes provider-neutral inputs and expected semantic results before Project Orrery chooses an
Authority Meta Model implementation owner.

`v1/conformance.json` is a Candidate golden contract, not a public manifest schema and not a runtime API. Its
`authority_model_version` exists only as one of the four required conformance inputs. Adding that field to a
project or release manifest remains behind Decision Gate B in the active Implementation Plan.

The fixtures deliberately keep coordination runtime data separate from fact scopes and model
decision/implementation/validation as independent claim dimensions. Consumers may use these fixtures for
shadow comparisons, but passing the fixture tests does not make a consumer the normative semantics owner.
