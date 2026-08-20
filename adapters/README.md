# Project Orrery adapters

Platform adapters contain only runtime discovery, invocation guidance, and
adapter lifecycle tooling. They depend on the platform-neutral Core and CLI;
they do not own or copy Project Orrery's canonical templates, compatibility
rules, or project facts.

Current adapters:

- `codex/`: experimental Codex Skill adapter. Its repository tests cover the
  artifact and installer lifecycle; real Codex runtime verification is still
  required before the adapter can be marked `verified`.
