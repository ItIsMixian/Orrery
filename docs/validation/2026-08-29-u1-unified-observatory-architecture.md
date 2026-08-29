# U1 Unified Observatory Architecture & Shell Validation

Date: 2026-08-29

Status: PASS — Windows Worktree Candidate; no production switch or hosted Promotion

## Scope and exact baseline

- Branch: `codex/u1-unified-observatory-architecture`.
- Base: protected `main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`.
- Git-private session: `U1-unified-observatory-architecture`, registered before authored writes.
- Outputs: Proposed `PO-DEC-U1-unified-observatory-shell`, Proposed-for-approval Design, independent Plan/Validation
  and synthetic experiment only. Its formal ADR number is **unassigned**, reserved is **false**, and allocation is
  **integrator-only** after maintainer acceptance and integration.
- Maintainer accepted the architecture direction and production docsite inheritance boundary on 2026-08-29. This is
  Candidate-scope direction acceptance, not formal ADR/Design promotion; those remain integrator-only at integration.
- Explicitly unchanged: production servers/builders/UI modules, start scripts, public template, managed tools, release
  manifest, v0.2.0, root README/assets, root PROGRESS/HANDOFF and shared State/DEVLOG/indexes.

## Architecture evidence

The inventory was derived from the real current launch/server/builder/navigation code, including exact loopback port
selection, routes, Host/Origin checks, settings token, Team cookie scope, Coordinator/Broker ownership and shutdown.
The Proposed Design records both current and target ownership and keeps W6.1/A3 uncommitted details Worktree-only or
Unknown.

The clarified target separates the **single visible startup/UI contract** from the **internal runtime topology**.
Default Windows launch is headless, explicit debug shows at most one console, and diagnostics use a local
Git-private/runtime log. Broker, Team transport and other helpers may be in-process or hidden supervised capabilities;
their acceptance gates are parity, scoped security, health, unified shutdown and no orphan process/endpoint evidence.

Acceptance boundary alignment confirms that Unified Shell owns startup entry, URL, navigation, capability orchestration
and lifecycle—not a replacement document product. Current `build_docsite.py`／`serve.py` reading, search, AI Q&A,
author-document information architecture and recognizable visual experience are the production inheritance baseline.
Production implementation must reuse/adapt those consumers; its internal refactoring authority is limited to front
door, registration, supervision, route/security composition and lifecycle. A from-scratch rewrite or comprehensive
visual redesign requires a separate task and explicit maintainer approval.

## Synthetic prototype acceptance

The prototype remains dependency-light HTML/CSS/JS, offline, `synthetic-non-authoritative` and outside all
production/release inputs. It uses one responsive sidebar and stable navigation identities for Overview, Docs/Search,
Ask Docs, Authority, Personal, Team, Workstream Graph and Maintenance.

The prototype is an **architecture interaction study**, not a final docsite redesign or production UI specification.
Its layout and visual choices do not supersede the recognizable production docsite experience.

Real in-app Chromium acceptance covered the original interaction path and the affected topology clarification path:

- **1280×900 desktop:** one persistent sidebar, active navigation, dynamic→static→dynamic switching, static
  Provider/Team/Maintenance controls disabled, explicit Team opt-in, request-only permission copy, Authority
  Unavailable/error isolation, current cached + stale/Unknown Maintenance rows and synthetic fresh-preflight/receipt.
  Measured document `scrollWidth` was `1265` initially and `1280` on the Maintenance view, never greater than the
  `1280` viewport.
- **390×844 mobile:** the same sidebar becomes one keyboard/ARIA-labelled drawer; opening it changed
  `aria-expanded=false→true` and selecting a destination closed it. Team opt-in and Maintenance preflight remained
  single-column with no clipped actions. Measured document `scrollWidth=375 < 390`.
- **Focus/accessibility:** keyboard focus on the Maintenance cancel action had a visible solid `2px`
  `rgb(99, 211, 202)` outline. Semantic landmarks, exact button names, `aria-pressed`, `aria-current`, status live
  regions and reduced-motion behavior were exercised.
- **Console:** desktop and mobile warning/error log queries both returned an empty list after the complete interaction
  path.
- **Permission copy:** static explicitly says no server/cookie/control; Team explicitly says metadata-only and central
  request-only; Authority refuses inference; Quick Remove says branch/commit remain and performs no filesystem action.
- **Clarified desktop path, 1280×900:** top bar exposed `ONE VISIBLE URL`, `127.0.0.1 · helpers supervised` and
  `Default no console`; the overview separated `Headless default`, supervised helpers and Git-private diagnostics.
  Clicking diagnostics produced a synthetic local-only log notice. Static mode changed the label to
  `file: · no runtime`. Measured `scrollWidth=1265 < 1280`; console logs were empty.
- **Clarified mobile path, 390×844:** the same visible-URL/supervisor copy remained present, the navigation drawer
  changed `aria-expanded=false→true→false`, and measured `scrollWidth=375 < 390`; console logs were empty.

Screenshots:

- `C:/Users/1/.codex/visualizations/2026/08/29/01a04e31-edc6-7381-b9ae-7a8e586e7ca3/u1-unified-observatory-shell/u1-desktop-visible-url-supervisor-1280.png`
- `C:/Users/1/.codex/visualizations/2026/08/29/01a04e31-edc6-7381-b9ae-7a8e586e7ca3/u1-unified-observatory-shell/u1-mobile-visible-url-supervisor-390.png`

## Commands and results

```text
temporary proposal identity / review-alignment check
PASS — proposal path/title/status present; formal number unassigned; reserved=false; integrator-only; legacy numbered
identity absent from the full worktree search

node --check experiments/unified-observatory-shell/prototype.js
PASS

python -X utf8 -m unittest -v tests.test_personal_observatory tests.test_team_observatory tests.test_workstream_relation_graph_observatory
PASS 24/24 in 196.400s

python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
PASS — integrated candidate; Authority Model 1 supported and strict-evaluation eligible

python -X utf8 scripts/docsite/build_docsite.py --out <visualization-root>/isolated-docsite/index.html
PASS — 15 formal ADRs, 6 State Docs, 7 subsystems, 163 classified docs, 33 Plans, 8 Library docs; the U1 temporary
proposal remains outside the formal ADR count

python -X utf8 scripts/ci/validate_repository_gates.py
PASS — 678 repository paths, 368 Markdown files, 921 local links, no forbidden runtime/generated artifacts

git diff --check
PASS
```

Clarification amendment short gates:

```text
temporary proposal + forced-topology phrase alignment
PASS — temporary ID/Proposed status unchanged; no mandatory single-process, internal-listener prohibition or forced
in-process Broker wording remains

node --check experiments/unified-observatory-shell/prototype.js
PASS

python -X utf8 scripts/docsite/build_docsite.py --out <visualization-root>/u1-topology-clarification-docsite/index.html
PASS — 15 formal ADRs, 6 State Docs, 7 subsystems, 163 classified docs, 33 Plans, 8 Library docs

python -X utf8 scripts/ci/validate_repository_gates.py
PASS — 678 repository paths, 368 Markdown files, 921 local links, no forbidden runtime/generated artifacts

browser affected desktop + 390px topology/diagnostics/static path
PASS — one visible URL, headless default, supervised helpers, local diagnostics, no overflow or console error

git diff --check
PASS
```

The 24-test focused module suite recorded above was not rerun for this documentation/synthetic-copy clarification, per
the user's instruction. Its earlier result remains evidence for the unchanged Personal/Team/Graph implementation.

Final acceptance-boundary amend short gates:

```text
acceptance/inheritance/non-redesign phrase alignment
PASS — maintainer direction acceptance is recorded; Proposed/unassigned/reserved=false/integrator-only boundaries and
production docsite reuse/non-redesign requirements are aligned across Proposal, Design, Plan, Validation and prototype

node --check experiments/unified-observatory-shell/prototype.js
PASS

python -X utf8 scripts/ci/validate_repository_gates.py
PASS — 678 repository paths, 368 Markdown files, 921 local links, no forbidden runtime/generated artifacts

git diff --check
PASS
```

The 196-second focused suite and Promotion were intentionally not rerun for this final narrow acceptance-boundary amend.

Focused/adjacent tests protect current Personal/Team/Graph contracts and default-off/zero-network behavior. The
isolated build proves U1 documents do not require a production server change. Browser evidence validates the synthetic
prototype only; it does not validate a unified production server that has not been implemented.

## Remaining boundaries

- Maintainer accepted the U1 architecture direction on 2026-08-29, but
  `PO-DEC-U1-unified-observatory-shell` remains Proposed; its formal ADR number is unassigned and not reserved. Only the
  unique integrator may allocate a formal number/update formal Status at integration. The Design remains Proposed for
  approval until integrator promotion.
- A3 currently provides only an uncommitted Worktree Plan; its machine contract remains unavailable.
- W6.1 current files are uncommitted Worktree State; its schema and provisional `/control/` routes are not U1 public
  contracts.
- No production server/supervisor/helper implementation, default launcher switch, component version bump, public
  template transition, hosted CI, push, main integration, tag or Release occurs in U1. Internal Broker/Team topology
  remains an implementation choice behind parity, security and lifecycle gates.
- U1 does not authorize a production docsite rewrite or comprehensive visual redesign. The synthetic study is not a
  UI specification; any such redesign requires a separate task and explicit maintainer approval.
