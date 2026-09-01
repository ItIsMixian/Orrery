# Implementation Plan: U2.4 Immediate Launcher Readiness

Status: Approved for implementation; patch publication remains separate

Date: 2026-08-31

Governing decision: [ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md)

Approved Design: [Unified Observatory Architecture & Shell](../../design/unified-observatory-architecture-and-shell.md)

## Observed failure

On the released v0.3.1 self-host repository, a normal Windows click started `pythonw.exe` at 23:37:41 but did not bind
the public runtime or open the page until 23:39:16–17. The page eventually returned HTTP 200; the user-visible failure
was roughly 95 seconds with no window, page, progress or error.

A read-only profile of the same render completed in 85.013 seconds and executed 751 child processes. The Workstream
graph provider consumed 63.991 seconds, relation graph/legacy projection 47.497/45.416 seconds and relation capture
32.131 seconds; the base document site consumed only 2.561 seconds. Current `serve_orrery.py` performs all rendering
before `_bind_server()`, `identity.ready()` and `webbrowser.open()`.

ADR-0016 already requires the public loopback URL to bind before per-consumer activation and requires consumers to
degrade independently. This task corrects the implementation order; it does not introduce a new architecture choice.

## Authorized implementation

1. Bind the public loopback listener and write one owned runtime identity before the heavy Unified render. A first
   normal launch must expose an HTTP page within 3 seconds on the maintained Windows host.
2. Serve a small Orrery-native startup page while state is `starting`. It states that project relationships are being
   assembled, polls the existing health endpoint with bounded intervals and automatically reloads `/#overview` once
   health becomes `ready`. It must not contain project facts, remote assets or a second UI design.
3. Extend the versioned health response to distinguish `starting`, `ready` and `failed`. A second normal launch during
   `starting` or `ready` reuses the exact PID/port and opens the same public URL; it never launches another supervisor.
4. Perform the existing `render_unified_site()` in one owned background worker. On success, atomically replace the boot
   page and consumer state. On failure, keep the local listener alive with a sanitized failure page/status, runtime-log
   location guidance and working stop route; do not expose traceback, absolute private paths or credentials in HTTP.
5. Keep stop idempotent during `starting`, `ready` and `failed`, reclaiming worker/listener/marker and managed Broker.
   Preserve `--console`, `--no-browser`, legacy rollback, loopback security and the v0.3.1 no-window child policy.
6. Keep root and project-template runtime copies byte/behavior equivalent. Add bounded startup phase timings to the
   Git-private log so future stalls can be diagnosed without desktop automation.

## Out of scope

- changing Workstream/relationship facts, reducing evidence, hiding graph failures or changing Team/Authority rights;
- optimizing all 751 Git calls in this task—the profile becomes input to a separate performance task after entry is usable;
- UI redesign, new external networking, Computer Use or foreground mouse/keyboard control;
- full Candidate/Promotion matrices, version bump, tag, asset or Release publication.

## Minimal validation

1. Syntax/import checks plus only the existing Unified lifecycle/launcher owners directly affected by the state change.
2. One real cold-start smoke on the current self-host topology, without Computer Use:
   - root HTTP 200 and visible `starting` page within 3 seconds;
   - second normal launch reuses the same PID/port while rendering is still active;
   - eventual `ready` exposes the full page and loading page reload contract;
   - stop during a separate starting fixture leaves no marker, listener, worker or matching process.
3. Root/template parity and `git diff --check`.

Do not run Fast, Checkpoint, Candidate or Promotion during implementation. Publication, if requested, receives a new
patch-release Plan after this Candidate is accepted.

## 2026-08-31 scope revision 2 — quarantine only out-of-graph program memberships

The delayed-start page eventually rendered, but its embedded Workstream Graph projection was
`status=unavailable / invalid-provider` while the live Core provider remained valid with 32 nodes and 12
`derived_from` edges. Direct projection reproduced `Program membership path is invalid.` The exact mismatch is one
explicit program membership for `W5D-lan-collaboration-harness`; that Workstream is not present in the current graph
node set. All four program/phase groups and the other eight memberships are structurally valid.

Revision 2 authorizes the Observatory adapter to ignore explicit program memberships whose Workstream is outside the
current relation graph node set, matching the existing task-series projection behavior. Duplicate memberships,
non-two-element paths and unresolved program/phase groups for nodes that are in the graph must still fail closed. Do
not create a placeholder W5D node, relation, membership, lifecycle fact or inferred group.

Add one focused regression proving an out-of-graph membership is omitted while the 32-node/12-edge provider remains
renderable, plus a negative control proving an invalid membership for an in-graph node still quarantines the Graph.
The current self-host page must project the existing edges with their honest proposed/stale labels instead of showing
an empty unavailable graph. Core relation/program stores and confirmation authority remain unchanged.

## 2026-09-01 scope revision 3 — restore archive boundary and reduce launcher surface

After local worktree cleanup, the running self-host page froze the Workstream Graph as Unavailable with
`archive session directory must contain exactly one worktree.json regular file`. Read-only inspection found 38 dated
archive entries; 13 entries created on 2026-09-01 contained a valid direct `worktree.json` plus unrelated
`ci-validation`, `runtime` or `task-bindings` directories. This violated the W7.1 dated-entry-v1 boundary. The same
running page retained a stale 20-worktree Maintenance snapshot although the Git registry now contains four worktrees.

This revision authorizes:

1. a reversible Git-private self-host repair that leaves every dated relation archive entry with exactly one direct
   `worktree.json` and moves all other preserved metadata into a separate Git-private extras namespace; no evidence
   bytes, branch, commit or author document may be deleted;
2. one direct self-host projection check after repair proving the relation provider/Graph is renderable from current
   live plus valid archived evidence, followed by one normal Unified refresh/restart so stale generated state is not
   presented as current;
3. implementation of [ADR-0025](../../decisions/0025-two-explicit-windows-launchers.md): the root and project template
   expose only `Start Orrery.vbs` (hidden console) and `Start Orrery Console.bat` (one console), both using the same
   Unified supervisor; `start-orrery.bat`, `start-orrery-control.bat` and root `start-docsite.bat` are not public root
   entries;
4. preservation of legacy/control behavior under `scripts/docsite/` only where still required for explicit recovery,
   with exact-hash managed migration for old root files deferred to the patch-release task;
5. a focused archive-layout regression, a focused two-launcher inventory/behavior check, root/template parity and
   `git diff --check` only. Do not start Fast, Checkpoint, Candidate, Promotion or release work before maintainer UI
   acceptance.

The archive reader remains bounded, zero-write and fail-closed for unsafe input. This revision does not authorize
invented relation facts, branch deletion, broad filesystem cleanup, version changes or publication.
