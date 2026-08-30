# GX1 Fireworks Tech Graph Evaluation

Status: Completed on isolated Candidate `f5fd5afa3f9b133166495119080629a5be5f67b2`; accepted as W7.3 assistance/selective technique only

Date: 2026-08-30

Governing sources: [ADR-0017](../../decisions/0017-workstream-relation-capture-and-confirmation-authority.md), [W7.3 Graph UX Amendment](2026-08-29-w7-3-workstream-relation-capture.md#2026-08-30-maintainer-scope-amendment--graph-native-relations-no-detached-substitutes)

Primary subsystem: `context-routing-research`

Affected: `documentation-system`, `multi-worktree-collaboration`, `test-coverage`

## Goal

Evaluate the external `fireworks-tech-graph` Agent Skill against Orrery's real graph-native relation requirements in
an isolated branch before deciding whether it should replace layout logic, assist W7.3 design/validation, contribute
selected geometry techniques, or be rejected.

## Isolation and provenance

- [ ] Create independent branch/worktree `codex/gx1-fireworks-graph-skill-evaluation` from this exact task-description
  version; do not modify W7.3, central product code, release manifests or public assets.
- [ ] Install the GitHub Skill only into the current local Agent skills directory, record repository/ref/content hash,
  inspect its `SKILL.md` and required architecture/quality references before executing scripts.
- [ ] Treat the Skill, generated diagrams and scores as non-authoritative experiment evidence. They cannot create
  Orrery relation facts or approve W7.3.
- [ ] Use only local files and local rendering. Do not follow sponsorship links, upload project data, call external
  model APIs, load CDN assets or enable motion/GIF dependencies.

## Evaluation fixtures

### Fixture A — graph-native task relations

- A3→A4 and CI6→CI7 as ordered series plus pending dependency connectors;
- U1→U2→U2.2 as ordered series with a separate stale succession fact;
- distinct styles/legend for series, succession, dependency and conflict;
- no detached series card strip and no comparison card wall;
- at least one selected-edge evidence inspector and dense Orrery-style dark presentation.

### Fixture B — conflict routing stress

- at least eight nodes and four confirmed conflict pairs with shared sources/targets plus unrelated crossings;
- every conflict connector is graph-native, selectable and label/legend identifiable;
- unrelated edges do not share long coincident path segments, cross node interiors or lose arrow direction;
- comparison suggestions are default-hidden or non-red and visually distinct from confirmed conflicts.

## Required artifacts

- [ ] Versioned semantic input/spec for both fixtures.
- [ ] Validated SVG and offline HTML for both fixtures; PNG/browser screenshots when the Skill supports them locally.
- [ ] Machine-readable geometry/validation reports and a concise provenance manifest.
- [ ] Evaluation record mapping every Orrery acceptance requirement to artifact evidence or failure.
- [ ] No generated artifact enters `docs/` authority roles or release/package surfaces.

## Decision rubric

Each category scores 0–2; any semantic safety zero prevents adoption.

| Category | 0 | 1 | 2 |
|---|---|---|---|
| Relationship semantics | wrong/missing | correct but external text required | correct in-canvas encoding |
| Layout/routing | overlap/through-node | readable with manual repair | validator-backed clean routing |
| Information hierarchy | detached card substitute | mixed graph/list | graph-first, secondary inspector only |
| Orrery fit | incompatible | useful reference | directly transferable geometry/IR |
| Reproducibility | subjective only | screenshot evidence | deterministic spec + validator + screenshot |
| Integration cost | requires frontend rewrite | bounded adapter/spike | no runtime dependency or small isolated helper |

Decision outcomes:

- **replace-layout candidate:** ≥10/12, no zero, and reusable runtime/IR with acceptable license/package boundary;
- **assist W7.3:** ≥7/12, no semantic-safety zero, useful as prototype/geometry oracle but not runtime;
- **selective merge:** individual validated routing/geometry techniques can be reimplemented without importing the
  whole Skill/runtime;
- **reject:** lower score, misleading semantics, non-reproducible output or excessive integration cost.

## Validation and stopping condition

- run the external Skill's doctor/validation/render checks only after reviewing their exact local commands;
- independently inspect SVG path/node intersections, coincident segments, labels, arrows and viewport containment;
- Browser-check desktop and mobile outputs with zero overflow/console error;
- stop after two focused correction rounds if the best objective geometry score does not improve;
- report actual result without modifying or resuming W7.3. A later maintainer decision controls any W7.3 amendment.

## Result accepted by maintainer

- Exact GX1 Candidate: `codex/gx1-fireworks-graph-skill-evaluation@f5fd5afa3f9b133166495119080629a5be5f67b2`.
- Score: 8/12, no semantic-safety zero.
- Decision: assist W7.3 and selectively reimplement lane/port/corridor/geometry techniques; do not replace Orrery's
  runtime graph and do not import the third-party Skill/SVG/HTML as a product dependency.
- The maintainer subsequently requested a new W7.3 readable-topology amendment. That amendment, not the GX1
  experiment transcript or generated output, is the product authority.
