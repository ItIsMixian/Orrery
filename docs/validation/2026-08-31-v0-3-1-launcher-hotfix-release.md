# Validation: Orrery v0.3.1 Launcher Hotfix Release

Status: Pending Validation

Date: 2026-08-31

Plan: [v0.3.1 Launcher Hotfix Release](../implementation/plans/2026-08-31-v0-3-1-launcher-hotfix-release.md)

## Required evidence — one pass each

- [ ] exact hotfix Candidate `8f60fac...` and product `06a277d...` reviewed without additional product scope;
- [ ] version/manifest/notes identify v0.3.1 and exclude alias/scheduler/DSH/auto-delete;
- [ ] two exact-Git builds produce identical entry receipt, ZIP and checksum;
- [ ] extracted Windows archive reaches HTTP 200, second normal launch reuses PID/port, and stop leaves no marker,
  process or listener; no Computer Use is invoked;
- [ ] one exact non-main Promotion run yields both required Windows/Ubuntu checks green;
- [ ] protected main, annotated tag and Release assets all bind the same exact SHA;
- [ ] remote ZIP/checksum verification passes;
- [ ] v0.3.0 assets remain unchanged and its Release notes visibly direct Windows users to v0.3.1.

## Cost/refusal record

Record wall time and every command/run once. Do not list or replay unrelated child suites. An unchanged failure is not
retried; record the failed identity and stop for a new exact-SHA correction.

## Result

Pending. No v0.3.1 manifest, tag, asset or remote Release exists under this task-description version.
