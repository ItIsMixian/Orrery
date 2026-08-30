# U2.3 Navigation & Live Task Visibility Validation

Date: 2026-08-30

Status: CANDIDATE — focused/product/repository evidence passes; formal Fast/Checkpoint remain ineligible on the inherited A4 CRLF inventory-digest defect, and the final mobile help-box correction still needs one central Browser replay

Authority source: exact authority commit `6315415075fb78b61d9a5bb835725bced0bc9ce1`, path `docs/implementation/plans/2026-08-30-u2-3-navigation-live-task-visibility.md` (merged by the central authority-first coordinator before this Candidate)

## Authority and scope binding

- Code base is exactly `3d298a5c408e4fff9cc2206c87a6cdde88f4c165`; implementation remained in the independent `codex/u2-3-unified-navigation-live-task-visibility` worktree.
- Authority amendment commit is `6315415075fb78b61d9a5bb835725bced0bc9ce1`. Before product writes resumed, `git show` verified the six requested sources with blobs `14d4e7d9`, `1de8da10`, `a2213bdf`, `5722379c`, `0170a411`, and `97da0ba8` respectively.
- Git-private Workstream `U2.3-unified-navigation-live-task-visibility` is registered with primary subsystem `documentation-system`, affected subsystems `project-structure`, `authority-meta-model`, `test-coverage`, and `release-and-toolchain`, exact expected writes, and scope revision 3.
- U2.3 did not modify A4.1-owned `authority_route.py`, operating-rules collector/schema/fixture/tests; W7.3-owned relation Core/schema/tests or Graph presentation modules; CI routing policy; or release proposals.

## Product evidence

- Unified app navigation has exactly seven entries in order: 项目总览、文档与搜索、个人工作台、团队协作、任务关系、工作区维护、路线与趋势. Ask Docs and Authority are absent from app navigation; Trends is absent from the author-document tree.
- The single floating `问文档` button remains the only Q&A entry. Overview describes that boundary and exposes no second Q&A capability card.
- A top-right `? 帮助` button opens one read-only ARIA dialog/popover. It separates 项目原则、Orrery 工作规则、事实解释状态; technical legacy/readiness/rollout/rollback detail is collapsed. Escape closes it and returns focus. No edit, approval, enable, migration, execution, credential, or network action was added; reduced-motion rules are present.
- Personal now consumes `orrery-active-task-projection-v1`: Git worktree registry plus bounded Git-common-private session JSON and the existing Maintenance cache. Initial collection does not run per-worktree status, read Scope/findings/source, or compute ignored/diff. A target-only detail request performs the existing Maintenance preflight for that task.
- A 20-worktree fixture covers four active sessions (`A4.1`, `W7.3`, `CI7`, `REL3`), stale cache, new session revision, broken session, missing worktree and protected primary root. Registered identity remains visible as `状态待刷新`; dynamic `/api/v1/personal/status` and `/api/v1/personal/tasks` observe revision changes without server restart. Main HTML and public JSON do not expose full local paths or raw findings.

## Measured self-host boundary

- Real projection discovered 22 registered worktrees: 21 current tasks, 1 protected primary root, 13 refresh-needed identities.
- It read 22 bounded session files totaling 104,370 bytes, made two registry/common-dir Git calls and one Maintenance cache snapshot, and performed zero startup source, Scope, ignored, diff, or per-worktree status reads.
- Wall time was 834.872 ms on this Windows self-host. Real Git-private identities included A4, W7.3, CI7, REL3 and U2.3; the fixture uses the requested `A4.1` name without rewriting real session identity.

## Automated validation

- `python -X utf8 -m unittest tests.test_unified_observatory tests.test_personal_observatory`: **25/25 PASS** in 65.730s after the final responsive-box patch.
- CI6 Fast dry-run and Checkpoint dry-run resolved all U2.3 paths with no unknown mapping. Formal Fast completed 28 tests with 26 PASS and two inherited A4 failures.
- Formal Checkpoint completed 102 tests in 54.588607s (within 90s), with 99 PASS and three A4-linked failures: the operating-rules inventory raw checkout digest is `e25bbe86…` while the frozen LF blob digest is `cec90a91…`; the loader error causes one downstream Ask Docs expectation failure. U2.3 does not own or modify that inventory/collector/test surface, and does not claim an evidence-eligible receipt.
- Integrated installation validation passed. Repository gates passed over 737 repository paths, 396 Markdown files and 1,074 links with no forbidden runtime/generated artifacts.
- Release dry build produced v0.2.0 ZIP/checksum in an isolated temporary directory. Its 41 entries contain no Git-private state, `.git`, `ai-config.json`, `.port`, generated `_site`, cache, `.env`, or `__pycache__` path.
- `git diff --check` passes apart from informational Windows LF/CRLF conversion warnings on existing JSON/TOML worktree files.

## Browser acceptance

- An isolated U2.3 server ran on `127.0.0.1:60413`; the central `127.0.0.1:60393` service was not stopped, reused or changed.
- In-app Chromium verified 1440×900 Overview/Personal, 1280×800 Trends, and 390×844 mobile Trends/drawer. All had document horizontal overflow 0; one sidebar/drawer, one floating Ask Docs entry, correct nav hierarchy, real A4/W7.3/CI7/REL3 visibility, hidden local paths, working task refresh/target detail, and no warning/error console entries.
- Desktop help verified the three layers, collapsed technical detail, ARIA labelling, close control, Escape and focus return. The first 390×844 measurement found the panel itself at x=-10 despite document overflow 0. CSS was corrected to an explicit border-box `left:0; right:0; width:100vw`, and the exact responsive rule is regression-tested.
- After rebuilding the isolated service, Browser policy rejected further interaction with the existing local tab. No bypass or alternate browser surface was used. Therefore the central integrator must replay the final 390×844 help screenshot/geometry check after merging A4.1, before treating Browser acceptance as complete.

## Integration boundary

- This is a clean non-main source Candidate only. No push, main update, tag, release, Team join, delete, Provider call or external network action occurred.
- Required merge/validation order is A4.1 first (repairs the strict evidence collector/digest baseline), then U2.3 and its Fast/Checkpoint/390px Browser replay, then W7.3 so its independently owned Graph series/status/compare-conflict semantics are reviewed against the final shell. CI7/REL3 remain independently owned.
