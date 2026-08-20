# Context-routing Harness

This directory contains experimental apparatus, not released Skill behavior.

## Evidence modes

1. `codex-exec-jsonl-posthoc` is the current compatibility baseline. `context_read_proxy.py` returns marked UTF-8 slices; `validate_cli_events.py` rejects any unapproved command or unexpected item in the complete `codex exec --json` stream and cross-checks the returned slice hash.
2. `hook-pre-post` is an optional stronger layer. `hook_audit.py` can block unapproved local tools in `PreToolUse` and hash `PostToolUse.tool_response`, but Windows Codex CLI 0.147.0 did not execute project or inline Hooks in the 2026-08-18 non-interactive smoke runs. A run must never claim this mode unless the Hook audit log exists and validates.

Neither mode proves that the model attended to, understood, or relied on returned content. The JSONL mode is post-hoc rejection, not real-time prevention.

## Components

- `context_read_proxy.py`: safe repository-relative listing and UTF-8 line-slice reads; content responses are written as bytes so Windows TextIO cannot turn source CRLF into CRCRLF.
- `validate_cli_events.py`: independent JSONL command/output audit used by current pilots.
- `hook_audit.py` and `validate_access_audit.py`: optional Hook enforcement and cross-check.
- `seal_raw_evidence.py`: immutable manifest sealing, verification, and retention status.
- `run_hook_smoke.py`: micro-task used to probe the installed Codex CLI.
- `smoke_app_server_scope_ordering.py`: single-turn, repository-external compatibility probe for cumulative usage
  ordering before the first `fileChange`; on Windows it fails before creating output unless the CLI's same-version
  code-mode host, command runner, sandbox setup, and `rg` siblings are present.
- `raw-evidence-retention-policy.json`: classifications and default review periods.

## Local checks

```powershell
python -m unittest tests.test_context_routing_h2 -v
python experiments/context-routing/harness/smoke_app_server_scope_ordering.py --self-test
python experiments/context-routing/harness/validate_cli_events.py `
  --events <run>/_operator/events.jsonl `
  --proxy-log <run>/_operator/proxy-audit.jsonl `
  --policy <run>/_operator/access-policy.json
python experiments/context-routing/harness/seal_raw_evidence.py verify `
  --manifest <run>/raw-evidence-manifest.json
```

Raw runs belong outside the Git repository. Do not copy JSONL, provider output, isolated repositories, credentials, or absolute-path logs into `docs/`.

The first authorized app-server ordering attempt on 2026-08-19 is sealed as contaminated because a copied
`codex.exe` lacked its code-mode host and produced no command or file-change boundary. Do not use its final-turn
usage as a pre-write metric. The separately authorized Smoke 002 used same-version, hash-matched runtime siblings
and observed a token-usage update before the first product `fileChange`, so ordering is verified for
`codex-cli 0.148.0-alpha.15`. Its policy required zero pre-write proxy reads: it is ordering-only evidence, not a
formal P/S cost sample or independent content-delivery proof. Pilot 008 later integrated proxy proof, full event
validation, exact Scope analysis, formal validation, R0 sealing and paired fail-stop; its first pair exposed an
external Skill read and stopped. Pilot 009 completed six apparatus-valid formal runs with the same chain. See the
[Pilot 009 R2 result](../results/2026-08-19-pilot-009-ps-scope-terra-medium.md); this does not turn the Harness into
a general filesystem or attention boundary.

Pilot 006 exposed a legacy Windows stdout translation in a CRLF JSON file. The v3 proof extractor accepts only response forms whose SHA-256 matches the independently logged proxy hash: raw bytes, canonical LF, or the reversible CRCRLF form emitted by the old Windows TextIO path. It does not accept newline-insensitive prose comparison; a changed body still invalidates the run. Sealed raw runs remain immutable and any new interpretation must be a versioned read-only review.
