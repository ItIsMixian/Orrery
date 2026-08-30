# U2.1 Unified Observatory UX Acceptance Fixes

Status: Complete; local Fast/Checkpoint and browser acceptance passed

Date: 2026-08-29

Workstream: `U2.1-unified-observatory-ux-acceptance-fixes`

Branch/base: `codex/u2-1-unified-observatory-ux-acceptance-fixes` from exact integrated Candidate
`codex/u1-u2-integration-baseline@4e2b5436d1744d8034011a34986df1eb6a04c9a4`.

Governing ADR: [ADR-0016](../../decisions/0016-unified-observatory-shell-and-single-local-entry.md)

Approved Design: [Unified Observatory Architecture & Shell](../../design/unified-observatory-architecture-and-shell.md)

## Goal and boundary

Repair the rejected U2 integrated Candidate as the real root-only/default-off product surface. Preserve the inherited
docsite information architecture and recognizable visual system while making the shell coherent, Chinese-first and
operationally honest. Do not change public v0.2.0, the default launcher transition, Team execution authority,
Authority/AI selection, Graph write authority, static controls, automatic deletion or the legacy rollback path.

## Compact design brief

- **Purpose:** let an Orrery maintainer understand and control one local Observatory without translating protocol
  vocabulary or choosing between duplicated navigation systems.
- **Context:** dense operational documentation/control app; existing dark docsite remains the design system.
- **Tone:** calm enterprise control room, compact and evidence-led rather than decorative.
- **Differentiator:** one stable Chinese app rail plus progressive disclosure: ordinary status and actions first,
  machine/schema/branch/Unknown vocabulary only under “技术详情”.
- **Constraints:** existing generated HTML/CSS/JS stack, 1280px and 390px acceptance, zero horizontal overflow,
  keyboard/focus basics, provider-owned action gates, no new dependency or image asset, no half-built language toggle.

## Implementation and acceptance

- [x] suppress duplicated Personal/Team/Graph/Maintenance entries from the legacy document navigation while retaining
  the author document tree;
- [x] centralize zh-CN display vocabulary and remove known English primary-view labels across Unified, Personal, Team,
  Workstreams and Maintenance;
- [x] degrade incompatible historical Maintenance evidence to Historical/Unknown without weakening current eligibility,
  and make Quick Remove discoverable for both zero and non-zero eligible counts;
- [x] accept complete validated hash-bound native or legacy/archive relation evidence independent of native-root
  presence, retain empty-evidence Unavailable, and serve a cached/bounded graph projection;
- [x] explain explicit LAN discovery and mark loopback/self results as local test/Host candidates;
- [x] provide one persistent global “关闭 Orrery 服务” control with confirmation and explicit disconnected state;
- [x] replace Personal reconciliation/hygiene terminology with ordinary Chinese and move protocol vocabulary to
  technical details;
- [x] add focused regression coverage and CI6 routing without executing deletion, external network, real Team join or
  provider credentials;
- [x] verify every primary page at 1280px and 390px with no horizontal overflow or browser console error;
- [x] synchronize U2/U2.1 Plan and Validation, affected State, DEVLOG and Validation index; leave root PROGRESS/HANDOFF
  untouched.

## Validation ladder

```text
python -X utf8 -m unittest -v <focused U2.1 tests>
python -X utf8 scripts/ci/validate_change.py --stage fast --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4 --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage fast --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4 --dry-run --explain
python -X utf8 scripts/ci/validate_change.py --stage checkpoint --base 4e2b5436d1744d8034011a34986df1eb6a04c9a4
real browser: Overview / Personal / Team / Workstreams / Maintenance at 1280px and 390px
git diff --check
```

Full Candidate/Promotion, hosted Windows/Ubuntu checks, central PROGRESS/HANDOFF reconciliation, main promotion and
release remain later integration work.
