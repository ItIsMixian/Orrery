# GX2 ELK Layout Engine Evaluation

This directory is an isolated, non-production evaluation of `elkjs@0.11.0`. It does not modify or replace the
Orrery product renderer.

## Run locally

```powershell
python -m http.server 8766 --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/experiments/workstream-graph-elk-evaluation/` when serving from the repository root.

The page loads only local files. `fixture.json` is a bounded sanitized snapshot; `provenance.json` records the exact
ELK release, bundle hash, size and EPL-2.0 license. Browser-produced screenshots and `geometry-report.json` are
evaluation evidence only and are not release assets.

## Evaluation outcome

- Revision 14 keeps every desktop tab at 100%; `适合窗口` is explicit and mobile uses the same-fact ledger.
- W defaults to nine W full cards plus three typed CI/SH boundary stubs. External full cards require the explicit
  `显示外部完整卡片` action.
- Project Structure primary-only, semantic-only and affected-only states are independent; affected overflow remains a
  summary boundary rather than expanding the default view.
- The first supervised layout remains 1821×1383 with one passive crossing finding, so part of the W graph still spans
  more than one scroll region at 100%.
- The second and final supervised iteration tried ELK `box` only for containment containers, but ELK.js 0.11.0 rejects
  the required mixed-algorithm cross-hierarchy edges with `UnsupportedGraphException`. The page restores iteration 1.
- GX2 does **not** claim visual acceptance or product readiness. Product/vendor/package integration remains blocked
  pending maintainer review and a later exact task description.

### Revision 15 small multiples

- The W workspace now composes three independent ELK layouts: vertical W5, vertical W6 and wider W7. Every external
  CI/SH endpoint terminates at a typed stub inside the nearest phase panel; the seven original relation IDs remain
  unique and there is no top-level synthetic connector.
- At 100% the measured W workspace is 1878×844. Passive render diagnostics report nine full cards, four stubs, seven
  relations, zero crossings, zero route-through-card and zero label/card overlap.
- Project Structure affected-only uses flat ELK box packing at 774×1016 with 13 full cards and one `+N` boundary;
  semantic context remains off in that state.
- Fresh evidence is under `screenshots/revision-15/` and `small-multiple-preview-report.json`. These remain
  coordinator-review artifacts, not validation PASS evidence.

### Scope revision 16 product preview evidence

- The accepted GX2 direction is now wired into the real Unified Observatory Candidate. The product source and
  vendored runtime live under `packages/project-orrery-observatory/`; this experiment directory retains only review
  evidence and the earlier rejected/accepted geometry history.
- `screenshots/product-revision-16/` contains the real product page at 1440×900, 1280×800 and 390×844 for global
  succession, W phase small multiples, Project Structure primary/semantic/affected, dependency, explicit ELK
  failure and manual legacy mode. The additional mobile W ledger image shows the same-fact list rather than a second
  projection.
- `product-preview-report.json` binds the task-description version, product component version, local preview URLs,
  exact ELK hashes and the intentionally unrun test/release workflows.
- This is still `pending-maintainer-review`; it is not Validation PASS, integration acceptance or release evidence.
