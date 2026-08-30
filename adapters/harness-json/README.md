# Orrery Harness JSON Adapter

This unreleased reference Adapter proves the platform-neutral CLI boundary without loading an Agent Skill or runtime.
It accepts a versioned JSON request, invokes `project_orrery_cli` as a subprocess with `--json`, validates the common
response envelope, and returns the CLI exit code unchanged.

Supported commands are `operating-rules-inspect`, `authority-route-preflight`, `scaffold`, `validate`, and `check-update`. The first two are bounded read-only Authority Meta Model consumption surfaces: they cannot write target files, promote Authority status, select a release, or turn missing evidence into absence. Requests cannot provide arbitrary CLI arguments;
each command has a fixed allowlist in `schemas/request-v1.schema.json`. Responses follow
`schemas/response-v1.schema.json` and always contain the schema version, command, Core/CLI versions, result category,
exit code, command data, warnings, and errors.

Example from a source checkout:

```powershell
python -X utf8 adapters/harness-json/run_harness.py `
  --request request.json `
  --python-path packages/project-orrery-core/src `
  --python-path packages/project-orrery-observatory/src `
  --python-path packages/project-orrery-cli/src
```

The Adapter removes Codex/Agent configuration variables and common Provider API-key variables from the child
environment. It invokes the selected Python interpreter directly and never searches for or loads `SKILL.md`, Codex
configuration, login state, or an Agent runtime. Update checks can use the network unless the request specifies
`"offline": true`; deterministic tests use a local manifest file or an empty isolated cache.

`experimental` here means the reference subprocess contract exists and is tested. It does not mean any third-party
Agent platform is supported, and it does not upgrade Core, CLI, or Adapter components to `released`.
