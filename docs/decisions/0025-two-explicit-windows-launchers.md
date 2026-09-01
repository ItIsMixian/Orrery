# ADR-0025: Two Explicit Windows Launchers

Status: Accepted

Date: 2026-09-01

Maintainer acceptance: accepted on 2026-09-01 with the instruction that a project expose only two unambiguous Orrery
startup entries: one hidden-console launcher and one visible-console launcher.

Amends: [ADR-0016](0016-unified-observatory-shell-and-single-local-entry.md)

Preserves: [ADR-0015](0015-orrery-brand-and-compatibility-contract.md),
[ADR-0024](0024-v0-3-1-emergency-launcher-hotfix-release.md)

## Context

The current self-host root contains `Start Orrery.vbs`, `start-orrery.bat`, `start-orrery-control.bat` and the legacy
`start-docsite.bat`. The first two overlap because the batch file starts the hidden VBS path unless `--console` is
remembered, while the control launcher exposes a Maintenance-only server that the Unified shell has already absorbed.
Users cannot determine the intended entry from the filenames, and multiple launch surfaces can appear to represent
different Orrery products.

ADR-0016 already requires one normal hidden-console experience and at most one explicit debug console. The shipped
file surface must make that distinction visible instead of requiring an argument or architectural knowledge.

## Decision

1. A new project root exposes exactly two supported Orrery launch files:
   - `Start Orrery.vbs`: normal launch, no visible command window;
   - `Start Orrery Console.bat`: diagnostic launch, exactly one visible console.
2. Both launchers start or reuse the same Unified supervisor, PID, port, public URL and capability set. The console
   launcher is not a second Maintenance server or a different product mode.
3. `start-orrery.bat`, `start-orrery-control.bat` and root `start-docsite.bat` cease to be public root launchers in the
   next Candidate. Required control and legacy rollback behavior moves under `scripts/docsite/` or remains available
   through an explicit internal command; it is not presented beside the two user launchers.
4. Upgrade/removal may delete an old launcher only when it matches an Orrery-managed exact hash. A customized or
   unknown file is preserved and reported; no broad filename-based deletion is allowed.
5. Root source, project template, onboarding, component inventory and the next release manifest must agree on the two
   names. Historical v0.3.0/v0.3.1 tags, archives, checksums and release manifests remain immutable.

## Consequences

- Double-click behavior is evident from the filename and there is no separate public Maintenance launcher.
- Whole-shell rollback remains possible for maintainers, but is no longer a third root-level user entry.
- Renaming/removing managed launchers requires focused installer/migration coverage in the next release task; it does
  not authorize a release, tag or asset replacement under U2.4.

## Mapping

- Approved Design: [Unified Observatory Architecture & Shell](../design/unified-observatory-architecture-and-shell.md#2026-09-01-launcher-surface-amendment)
- Plan: [U2.4 Immediate Launcher Readiness](../implementation/plans/2026-08-31-u2-4-immediate-launcher-readiness.md)
- Validation: [U2.4 Immediate Launcher Readiness](../validation/2026-08-31-u2-4-immediate-launcher-readiness.md)
