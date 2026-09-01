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
