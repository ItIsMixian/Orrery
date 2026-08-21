# Project Orrery adapters

Platform adapters contain only runtime discovery, invocation guidance, and
adapter lifecycle tooling. They depend on the platform-neutral Core and CLI;
they do not own or copy Project Orrery's canonical templates, compatibility
rules, or project facts.

Current adapters:

- `codex/`: experimental Codex Skill adapter. Its repository tests cover the
  artifact and installer lifecycle; one exact Windows runtime range is
  `verified`, while the Adapter distribution remains unreleased.
- `claude-code/`: experimental native Claude Code Plugin adapter with a bundled
  local marketplace for isolated lifecycle validation.
- `deepseek-harness/`: experimental DeepSeek Harness profile Plugin Bundle that
  registers one packaged Project Orrery Skill.
- `harness-json/`: experimental reference subprocess JSON Adapter. It validates
  the Core／CLI machine contract, not a third-party Agent runtime.
