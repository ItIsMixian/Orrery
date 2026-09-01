# Validation: U2.4 Immediate Launcher Readiness

Status: Worktree Candidate validated; patch publication remains separate

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

PASS at Worktree Candidate scope. The public v0.3.1 archive is unchanged and still has the baseline delayed-entry
behavior; no Fast, Checkpoint, Candidate, Promotion or Release operation ran.

### Focused mechanical evidence

- Python compile covered both `serve_orrery.py` copies, the Graph adapter and the two focused owner modules.
- Existing owners remained at the same test IDs: Unified 16, Graph program-membership positive/negative 1 and
  root/template managed-runtime parity 1; 18/18 passed in 8.545 seconds.
- Root and project-template `serve_orrery.py` are byte-identical at SHA-256
  `34b08df42e0d6bb0721ecdb5bde3f9d2f6c3ee3170bae6fd07fd8c971aec1ec0`; `git diff --check` passed.
- `starting`, `ready` and `failed` health/page behavior, bounded polling with `/#overview` reload, sanitized failure
  projection, starting/ready reuse and starting/ready/failed stop are covered by the existing Unified owners.

### Real self-host lifecycle smoke

- The first pre-lazy-import implementation correctly exposed `starting` and reused one instance, but its first HTTP
  arrived at 3304 ms; this non-green result is retained. Moving existing runtime imports into the owned background
  worker corrected the front-door budget without changing Graph/Core work.
- Corrected cold start on port `18768`: root HTTP 200 and visible `starting` page at 701 ms; health was `starting`.
  The second normal launch exited 0 in 319 ms and preserved exact PID `58004`, port and instance ID.
- The same runtime became `ready`; the external poll observed the full page at 55.317 seconds. Git-private phase timing
  recorded listener `starting` at 74 ms, worker start at 75 ms and worker `ready` at 54.076 seconds total.
- Ready stop returned HTTP 202 and left no marker or listener; the owned process exited.
- A separate starting fixture on port `18769` returned the starting page at 544 ms. Stop returned HTTP 202 and left
  no marker, listener or matching Python process (`matching_processes=0`).
- The smoke used `--no-browser`; Computer Use, mouse/keyboard control and foreground desktop automation were not used.

## 2026-08-31 empty Graph projection blocker

- live provider: valid, 32 nodes, 12 `derived_from` edges, 9 program memberships;
- embedded page projection: `unavailable / invalid-provider`, 0 nodes/edges;
- direct exception: `Program membership path is invalid.`;
- exact mismatch: `W5D-lan-collaboration-harness → workstream-w/workstream-w5` references a Workstream outside the
  current graph node set; no other membership shape/group error was found.

Revision 2 passed. The adapter now omits only memberships whose Workstream is outside the graph node set. The existing
focused owner proves that omission adds no node/edge and that a malformed path for an in-graph node still returns
`unavailable / invalid-provider` with empty nodes/edges.

The single accepted self-host provider/projection run (`exec-a892b385-e8bf-4e82-955a-5f53301626c4`) observed 33 provider
nodes and 13 edges—the active U2.4 Git-private session adds one node/edge over the 32/12 baseline—and a `ready`
projection with 33 nodes, 20 honestly labelled effective/proposed/stale edges and
`placeholder_w5d=false`. No provider command was repeated after that evidence; Core relation/program stores,
memberships and confirmation authority were not modified.
