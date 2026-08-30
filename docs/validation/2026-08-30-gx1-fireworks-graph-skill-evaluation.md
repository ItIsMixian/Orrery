# GX1 Fireworks Tech Graph Evaluation Validation

Date: 2026-08-30

Status: PASS on isolated Candidate `f5fd5afa3f9b133166495119080629a5be5f67b2`; product adoption limited to assistance/selective reimplementation

Authority source: [GX1 Plan](../implementation/plans/2026-08-30-gx1-fireworks-graph-skill-evaluation.md)

## Expected evidence

- exact task-description version, branch/worktree and Git-private Scope;
- installed Skill repository/ref/hash, license and reviewed local dependency/command boundary;
- Fixture A/B semantic specs and generated SVG/offline HTML artifacts;
- external Skill validation plus independent geometry and Browser checks;
- 0–12 rubric with per-category evidence;
- explicit replace-layout／assist／selective-merge／reject recommendation;
- zero W7.3/product/release/public/remote diff.

## Accepted result

- Exact authority/base: `bfc3e6da2972b00dc6f6c0eab4c2cf9bd342be72`; isolated branch
  `codex/gx1-fireworks-graph-skill-evaluation`; final Candidate
  `f5fd5afa3f9b133166495119080629a5be5f67b2`.
- Pinned Skill ref: `e9c7a9351dee5861707a7ec5560248bf5e7b84b5`, package 1.2.0, MIT, installed-tree
  manifest `b41e66615d0b02e0998057a50426fe1bf6128ca863e30765a0925c95e257b3a6`.
- Fixture A: 9 nodes／7 edges／0 bridges; Fixture B: 10 nodes／8 edges／1 explicit bridge. Final SVGs passed
  semantic, XML, marker, geometry and declared composition gates.
- Browser desktop and 390px had zero document overflow/external asset/console warning/error, but mobile text was
  unreadable without zoom. Exported HTML had no edge selection or dynamic inspector.
- Rubric: semantics 2, layout 1, hierarchy 2, Orrery fit 1, reproducibility 2, integration cost 0 = **8/12**.
- Focused artifact contract passed 4/4; exact-Candidate routed Fast passed 49/49 and repository gates passed. The exact
  commands, render reports and non-authoritative fixtures remain inspectable with
  `git show f5fd5afa3f9b133166495119080629a5be5f67b2:<path>`.

Decision: the experiment may guide W7.3 lane layout, port/corridor assignment, crossing/bridge checks, spacing and
route metrics. It cannot create relation facts, replace the interactive runtime, satisfy mobile UX, enter a release
package or prove W7.3 acceptance.
