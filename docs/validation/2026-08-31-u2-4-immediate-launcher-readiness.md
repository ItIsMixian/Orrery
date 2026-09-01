# Validation: U2.4 Immediate Launcher Readiness

Status: Pending Validation

Date: 2026-08-31

Plan: [U2.4 Immediate Launcher Readiness](../implementation/plans/2026-08-31-u2-4-immediate-launcher-readiness.md)

## Baseline evidence

- normal `pythonw.exe` start: 23:37:41;
- runtime marker/ready log: 23:39:16;
- first browser GET: 23:39:17;
- eventual listener: `127.0.0.1:8765`, health `ready`, root HTTP 200;
- profile: 85.013 seconds, 751 subprocess calls, graph provider 63.991 seconds, base docs 2.561 seconds.

This proves the delayed-entry defect; it does not validate a correction.

## Pending acceptance

- first cold-start HTTP/loading page within 3 seconds;
- `starting`/`ready`/`failed` health semantics and one PID/port reuse;
- background render atomic activation and sanitized failure projection;
- stop reclamation in starting and ready states;
- preserved loopback/security/no-window/console/legacy behavior;
- root/template parity, focused owners and exact elapsed-time evidence;
- no Computer Use, full validation matrix or Release operation.

## Result

Pending. No product code has changed under this task-description version.

## 2026-08-31 empty Graph projection blocker

- live provider: valid, 32 nodes, 12 `derived_from` edges, 9 program memberships;
- embedded page projection: `unavailable / invalid-provider`, 0 nodes/edges;
- direct exception: `Program membership path is invalid.`;
- exact mismatch: `W5D-lan-collaboration-harness → workstream-w/workstream-w5` references a Workstream outside the
  current graph node set; no other membership shape/group error was found.

Revision 2 is Pending until the adapter omits only out-of-graph memberships, preserves in-graph negative controls and
the current self-host Graph renders the remaining honest relation facts without inventing W5D.
