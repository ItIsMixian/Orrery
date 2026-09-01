# Approved Design: Orrery v0.3.1 Launcher Hotfix Release

Status: Approved

Date: 2026-08-31

Governing decision: [ADR-0024](../decisions/0024-v0-3-1-emergency-launcher-hotfix-release.md)

## Release input

- Code base: `codex/windows-launcher-console-flash-hotfix@8f60facfaf15a531c085baf94d7207d068d29d9a`.
- Product implementation: `06a277de3e380f7c8a957d76cba60c29db0fd3e1`.
- Scope: shared Windows no-window child policy, healthy runtime reuse, root/template parity and release metadata only.
- Public version: `0.3.1`; Core and Observatory receive the next patch component versions because their shipped
  runtime changed. CLI and Adapter versions remain unchanged unless exact packaging contracts mechanically require a
  manifest-only reference update.

Public assets remain one `project-orrery-v0.3.1.zip` and one ASCII/LF `.sha256`, with the same archive root and stable
technical IDs as v0.3.0. Defaults, schemas, supported cohorts and unsupported/experimental boundaries do not change.

## Single-pass gate

| Step | Required evidence | Explicitly not repeated |
|---|---|---|
| Freeze | exact manifest/version/notes and clean SHA | feature suites, UI review |
| Local package | two exact-Git builds with identical ZIP/checksum/entry receipt | full Candidate matrix |
| Windows runtime | extracted archive starts, second launch reuses PID/port, stop cleans marker/process/listener | Computer Use, full Codex lifecycle portfolio |
| Hosted | one non-main exact-SHA Promotion; both named Windows/Ubuntu checks green | same-SHA rerun, per-lane retry |
| Publish | same SHA main/tag/assets, remote hashes, v0.3.0 warning/link | asset replacement, tag movement |

The existing Promotion workflow may still execute its complete registered inventory. That one hosted run is the
cross-platform branch-protection gate; the release task must not duplicate it locally.

## User-facing release copy

The opening text states: v0.3.1 fixes repeated Windows command-window flashes and duplicate-launch behavior; Windows
v0.3.0 users should upgrade. A short technical section may name `CREATE_NO_WINDOW`, runtime reuse and preserved
`--console` behavior. Do not lead with component internals, authority terminology or packaging mechanics.

The v0.3.0 page receives an additive warning only after v0.3.1 is remotely verified. Its existing body and assets stay
available below the warning.
