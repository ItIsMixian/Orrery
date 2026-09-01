# Validation: Windows 启动器闪窗热修

Status: Worktree Candidate validated; integration and patch publication pending

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

## Acceptance contract

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

PASS for the bounded Worktree Candidate contract on product exact
`06a277de3e380f7c8a957d76cba60c29db0fd3e1`. This is not Canonical integration, a patch Release, Candidate-stage
validation or Promotion evidence.

### Implemented surface

- `project_orrery_core.subprocess_policy.no_window_options()` is the shared production policy. Windows enabled calls
  return `CREATE_NO_WINDOW` (`134217728`); disabled and non-Windows calls return no creation flags. The policy is wired
  into the Git subprocess owners reached by Unified startup/page construction/refresh, while arbitrary validation
  commands remain outside the policy.
- normal headless startup checks the existing Git-private identity and loopback health before Unified page
  construction. A healthy live runtime reopens its exact public URL and exits; stale state still recovers and an
  alive-but-unhealthy or invalid identity fails closed. Explicit console legacy fallback does not suppress its inherited
  console.
- root and project-template `serve_orrery.py`／`docsite_insights.py` bytes remain equal. The managed runtime inventory
  includes the shared policy module; v0.3.0 release manifest, tag and assets remain unchanged.
- an opt-in `ORRERY_CHILD_POLICY_AUDIT_PATH` writes bounded local JSONL only when the validating caller explicitly sets
  it. Default production behavior performs no audit write. The smoke used a system-temporary path and removed it.

### Focused commands

- Python compile checks for every changed production Python file and both root/template copies — PASS.
- `python -X utf8 -m unittest tests.test_unified_observatory` — 16/16 PASS on exact `06a277d...`.
- `python -X utf8 -m unittest
  tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection` — 1/1
  PASS.
- `python -X utf8 -m unittest
  tests.test_project_orrery.ProjectOrreryTests.test_phase1_neutral_cli_matches_legacy_paths_and_preserves_authored_files`
  — 1/1 PASS.
- `git diff --check` — PASS. No Fast, Checkpoint, Candidate, Promotion or packaging matrix was run.

One earlier attempt to invoke a packaging-owned test correctly refused because the implementation worktree was dirty;
it did not load a release gate and is not counted as product evidence. A WMI process-start subscription and one long
PowerShell orchestration were also rejected before launching VBS; neither is counted as a smoke attempt.

### Bounded Windows launcher smoke

One terminal-instrumented normal-launch session ran against clean exact `06a277d...` on
`Windows-11-10.0.26200-SP0` with `C:\Users\1\anaconda3\pythonw.exe`:

1. first `Start Orrery.vbs` launch reached `/api/v1/health` with `status=ready`, supervisor PID `129012`, port `8765`
   and instance `59380f833c7b4b6e8270f03c37a4aab8`;
2. second normal VBS launch retained the same PID, port and instance, and health remained `ready`;
3. the exact new log slice contained one `runtime ready` and one `reusing healthy runtime`; there was no second ready
   event or marker replacement;
4. the opt-in audit recorded 760 policy evaluations from two launcher-process PIDs across 11 production callers
   (`serve_orrery`, docsite insights, active task projection, collaboration, review, Team, hierarchy and relation
   owners). Every record had `os_name=nt`, `enabled=true` and `creationflags=134217728`; invalid records: 0;
5. the same-origin stop endpoint returned 202 after the public root returned 200. The exact marker disappeared, PID
   `129012` exited, the audited reuse-helper PID `137368` was also absent, port `8765` stopped accepting connections
   and no matching supervisor remained.

This is auditable mechanical evidence for the Windows no-window flag and runtime reuse. Per maintainer instruction,
no desktop automation or foreground-window takeover was used. A human did not manually watch two double-clicks, so
the subjective statement “no visible flash was perceived” remains unclaimed and may be checked manually before patch
publication. The mechanical hotfix contract is complete; cross-platform release-owned gates remain a later scope.
