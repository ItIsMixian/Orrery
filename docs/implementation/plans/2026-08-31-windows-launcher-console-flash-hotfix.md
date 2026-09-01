# Implementation Plan: Windows 启动器闪窗热修

Status: Approved for implementation; patch publication remains separately gated

Date: 2026-08-31

Governing decisions: [ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md),
[ADR-0021](../../decisions/0021-v0-3-0-release-scope-default-matrix.md)

Approved Design: [Unified Observatory Architecture & Shell](../../design/unified-observatory-architecture-and-shell.md)

## Why this is a hotfix

The public v0.3.0 Windows launcher starts the supervisor with `pythonw.exe`, but production paths reached while
building and refreshing the Unified Observatory create console-subsystem children without an explicit Windows
no-window policy. On a GUI-parent launch, repeated short-lived Git children can therefore appear as a rapid sequence
of command windows. A second launcher click also creates another hidden supervisor attempt before the existing
runtime guard rejects it.

This violates ADR-0016's existing headless-default and single-front-door contract. It is an implementation defect,
not a new product or security decision, so no new ADR is required. ADR-0021 keeps the published v0.3.0 tag and assets
immutable; any corrective publication must use a new patch release.

## Authorized implementation

1. Introduce one small cross-platform child-process policy owned by production code. On Windows, console-subsystem
   children started from Orrery's default headless runtime must use `CREATE_NO_WINDOW` (or the exact equivalent);
   non-Windows behavior remains unchanged. Apply it to every Git/helper subprocess reachable during Unified startup,
   page construction, refresh and shutdown—not to tests, CI workers or unrelated developer scripts.
2. Move the live-runtime check ahead of expensive Observatory construction. If the Git-private runtime identity binds
   an alive Orrery supervisor and its loopback health check succeeds, a normal launcher click opens that existing
   public URL once and exits successfully without starting another supervisor. A corrupt, stale or alive-but-unhealthy
   identity follows the existing fail-closed recovery/diagnostic contract; it must not be silently replaced.
3. Preserve explicit `--console` behavior: at most one visible supervisor console, normal error reporting, Ctrl+C
   shutdown and no additional child consoles. Preserve one public loopback URL, one browser open per successful
   launcher invocation and existing Git-private log/marker ownership.
4. Keep the root launchers and every released project-template copy byte/behavior compatible. Do not make author
   documents, credentials, caches, generated site output or Git-private runtime state release inputs.
5. Add only focused regression coverage for the Windows creation flags, existing-runtime reuse, stale/unhealthy
   refusal, console-mode preservation and root/template launcher parity. Reuse existing test owners where practical;
   do not create a broad new validation suite.

Expected product surfaces are limited to the shared production subprocess helper or wrappers, Unified runtime
supervision/launcher code, root/template launcher copies, the nearest existing launcher/Unified tests and—only if the
exact new path is otherwise unmapped—one generic CI path-mapping entry. The implementation Agent must inventory the
exact paths and register them in Git-private scope before its first product write.

## Explicitly out of scope

- changing Workstream, Authority, relation, Maintenance or graph semantics;
- UI redesign, new navigation, new network behavior or Team enablement;
- DSH Store, the `orrery` CLI alias, scheduler or automatic deletion;
- moving/reusing the v0.3.0 tag, replacing its ZIP/checksum or editing its immutable release assets;
- full Candidate/Promotion matrices during implementation;
- publishing a patch Release from the implementation task.

## Minimal validation sequence

1. Before editing, reproduce the call chain by inspection and record the exact production subprocess sites reached by
   default startup/refresh. Do not manufacture repeated visible windows as a test.
2. During iteration, run syntax/import checks and the smallest existing launcher/Unified owner tests that directly
   exercise changed behavior. No Fast, Checkpoint, Candidate or Promotion run is authorized in the edit loop.
3. On a clean Windows candidate, perform one bounded real launcher smoke: first click reaches HTTP 200 without child
   console flashes; second click reuses the same PID/port and creates no second supervisor; UI stop removes the exact
   marker and listener. Preserve logs and process observations in Validation.
4. The unique integrator reviews the diff and focused evidence. Only then may a separate patch-release scope select a
   version, run exact-SHA release-owned gates and request publication authorization.

## Completion boundary

Implementation is complete only when the focused contract and one real Windows launcher smoke pass on a clean exact
SHA, affected State/Validation/DEVLOG are synchronized, and the change is ready for integration. That state is not a
public patch release; publication remains a separate maintainer-authorized action.
