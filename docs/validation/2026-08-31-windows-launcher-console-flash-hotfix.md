# Validation: Windows 启动器闪窗热修

Status: Pending Validation

Date: 2026-08-31

Plan: [Windows 启动器闪窗热修](../implementation/plans/2026-08-31-windows-launcher-console-flash-hotfix.md)

## Observed defect

- The normal VBS entry launches `serve_orrery.py` through hidden `pythonw.exe`.
- Production startup/refresh paths contain multiple `subprocess.run(...)` Git calls and no shared
  `CREATE_NO_WINDOW`/`STARTUPINFO` policy.
- Git-private `unified.log` records ordinary single `runtime ready` events and one rejected duplicate supervisor,
  rather than an intentional restart loop.
- After the host reboot, no matching Orrery `pythonw`/`python`/`wscript`/`cmd` launcher process remained.

These observations support the diagnosis but do not validate a fix.

## Pending acceptance contract

### Focused mechanical evidence

- Windows headless subprocess options set the no-window flag for every production startup/refresh child site;
  POSIX options and process results remain unchanged.
- An alive, healthy marker causes normal launch to reuse the exact PID/port and avoids full construction plus a second
  supervisor. Stale identity recovery still works; alive-but-unhealthy identity fails closed with a useful log entry.
- `--console` retains one visible console and normal Ctrl+C shutdown without spawning child consoles.
- Root and released template launchers remain byte/behavior compatible.
- Existing launcher/Unified safety tests covering Host/Origin, loopback binding, stop, stale marker and no orphaned
  listener remain green when directly affected.

### One real Windows smoke

Record the exact candidate SHA, Windows version, Python executable and these observations from one bounded session:

1. first normal launch reaches `/api/v1/health` with no child command-window burst;
2. second normal launch keeps the first supervisor PID and port, opens/reuses the existing public URL and exits;
3. UI stop or console stop terminates the supervisor and removes only its matching runtime identity;
4. no matching Orrery supervisor/helper process or bound port remains.

### Validation cost boundary

Implementation iteration is limited to syntax/import checks and directly affected existing tests. Fast, Checkpoint,
Candidate, Promotion, packaging, tag and Release operations are not part of this task. A later patch-release task owns
the exact-SHA cross-platform and publication gates.

## Result

Pending. No product code has changed and no validation command has run under this task-description version.
